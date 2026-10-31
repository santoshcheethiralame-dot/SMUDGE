"""The trace bus: every agent step becomes one event, which the Observatory draws and the gate replays.
The event shape is a contract with the game (docs/superpowers/specs/2026-10-30-finals-design.md §3.1)."""
import time

KINDS = {"suspect", "coach", "detective", "router", "redteam"}
STEPS = {"plan", "draft", "critique", "redraft", "firewall", "reply", "hint", "route", "accuse"}
VERDICTS = {"ok", "leak", "block", "skip", "pass", "fallback"}
PRIMARY = "groq"        # a step served by anything else (and not from the cache) also gets a router event

_TYPES = {"i": int, "t": (int, float), "agent": str, "kind": str, "step": str, "model": (str, type(None)),
          "provider": (str, type(None)), "ms": int, "tokens": int, "cached": bool, "verdict": str, "data": dict}


class Trace:
    def __init__(self):
        self.events: list[dict] = []

    def emit(self, agent, kind, step, verdict="ok", meta=None, **data):
        meta = meta or {}
        ev = {"i": len(self.events), "t": round(time.time(), 3), "agent": agent, "kind": kind, "step": step,
              "model": meta.get("model"), "provider": meta.get("provider"), "ms": int(meta.get("ms") or 0),
              "tokens": int(meta.get("tokens") or 0), "cached": bool(meta.get("cached")), "verdict": verdict, "data": data}
        self.events.append(ev)
        provider = meta.get("provider")
        if provider and provider != PRIMARY and not meta.get("cached") and kind != "router":
            self.emit("router", "router", "route", "fallback", tier=meta.get("tier"), served=provider)
        return ev

    def since(self, i: int):
        return self.events[max(0, i):]


def problems(ev: dict) -> list[str]:
    """What is wrong with one event, as readable strings. Empty when it meets the contract."""
    out = [f"{k}: missing or not {t}" for k, t in _TYPES.items() if not isinstance(ev.get(k), t)]
    out += [f"{name} {ev.get(name)!r} unknown" for name, ok in (("kind", KINDS), ("step", STEPS), ("verdict", VERDICTS))
            if ev.get(name) not in ok]
    return out
