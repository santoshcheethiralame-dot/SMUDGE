"""The Observatory is built against the fixtures in game/public/fixtures; these tests keep them true to the contract."""
import json
from pathlib import Path

import pytest

from tracebus import Trace, problems

FIX = Path(__file__).resolve().parents[2] / "game" / "public" / "fixtures"


def test_trace_sample_matches_the_contract():
    body = json.loads((FIX / "trace_sample.json").read_text(encoding="utf8"))
    assert body["next"] == len(body["events"])
    for i, ev in enumerate(body["events"]):
        assert ev["i"] == i
        assert problems(ev) == [], (i, problems(ev))
    for s in body["stress"].values():
        assert 0 <= s["level"] <= 9 and s["band"] in {"CALM", "GUARDED", "RATTLED", "CORNERED"}
    seen = {(e["step"], e["verdict"]) for e in body["events"]}
    for want in [("critique", "leak"), ("redraft", "ok"), ("firewall", "block"), ("critique", "skip"), ("route", "fallback")]:
        assert want in seen, want


def test_redteam_sample_matches_the_contract():
    body = json.loads((FIX / "redteam_sample.json").read_text(encoding="utf8"))
    assert set(body["by_layer"]) == {"held", "critique", "firewall", "slipped"}
    assert sum(body["by_layer"].values()) == body["attacks"] == len(body["rows"])
    assert all(r["layer"] in body["by_layer"] for r in body["rows"])


def test_replay_sample_matches_the_contract():
    body = json.loads((FIX / "replay_sample.json").read_text(encoding="utf8"))
    dts = [e["dt"] for e in body["events"]]
    assert dts == sorted(dts) and dts[0] == 0
    assert all(problems({k: v for k, v in e.items() if k != "dt"}) == [] for e in body["events"])
    assert set(body["result"]) == {"no_lab", "with_lab"}


def test_emit_numbers_events_and_since_pages():
    t = Trace()
    t.emit("volta", "suspect", "plan", meta={"provider": "groq", "model": "m", "ms": 5, "tokens": 9, "cached": False}, risk="low")
    t.emit("volta", "suspect", "draft", text="hi")
    assert [e["i"] for e in t.events] == [0, 1]
    assert t.since(1) == [t.events[1]] and t.since(2) == []
    assert t.events[0]["data"] == {"risk": "low"} and t.events[1]["model"] is None
    assert all(problems(e) == [] for e in t.events)


def test_a_step_served_below_the_first_provider_adds_a_router_event():
    t = Trace()
    t.emit("glim", "suspect", "plan", meta={"provider": "groq-qwen", "model": "q", "tier": "fast"})
    t.emit("glim", "suspect", "draft", meta={"provider": "groq-qwen", "model": "q", "cached": True})
    assert [(e["step"], e["verdict"]) for e in t.events] == [("plan", "ok"), ("route", "fallback"), ("draft", "ok")]
    assert t.events[1]["data"] == {"tier": "fast", "served": "groq-qwen"}


@pytest.mark.parametrize("bad", [{"kind": "wizard"}, {"step": "dance"}, {"verdict": "maybe"}, {"ms": "fast"}])
def test_problems_names_what_is_wrong(bad):
    ev = Trace().emit("volta", "suspect", "plan")
    assert problems({**ev, **bad})


import llm


class _Resp:
    status_code = 200
    headers = {}

    def raise_for_status(self):
        pass

    def json(self):
        return {"choices": [{"message": {"content": "Hello there."}, "finish_reason": "stop"}], "usage": {"total_tokens": 321}}


def test_chat_reports_tokens_and_tier(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "CACHE", tmp_path)
    monkeypatch.setattr(llm, "PROVIDERS", [dict(name="groq", key="X_KEY", url="u", models={"fast": "m"})])
    monkeypatch.setenv("X_KEY", "k")
    monkeypatch.setattr(llm.httpx, "post", lambda *a, **k: _Resp())
    meta = {}
    assert llm.chat([{"role": "user", "content": "hi"}], tier="fast", meta=meta) == "Hello there."
    assert meta["tokens"] == 321 and meta["tier"] == "fast" and meta["provider"] == "groq"
    again = {}
    llm.chat([{"role": "user", "content": "hi"}], tier="fast", meta=again)
    assert again["cached"] is True and again["tokens"] == 0
