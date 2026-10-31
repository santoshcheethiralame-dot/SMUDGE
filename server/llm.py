"""One chat() call for every agent: Groq first, Gemini as backup, disk cache.

Both providers speak the OpenAI chat-completions format, so one code path
serves both. If neither answers, chat() returns None and the caller falls
back to scripted lines, so the game never hangs on the network.
"""
import hashlib
import json
import os
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(__file__).resolve().parent / ".cache"
CACHE.mkdir(exist_ok=True)


def _load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()

GROQ = "https://api.groq.com/openai/v1/chat/completions"
# gpt-oss thinks first; its thinking tokens count against the budget, so keep it short and out of the reply
OSS = {"reasoning_effort": "low", "include_reasoning": False}
# Groq meters quota per model, so each extra model is more free quota. Tried in order; the first answer wins.
# The smaller models stand in for suspects and the coach only: as the gate's detective they misread lab results,
# so a provider without a "smart" model is skipped for that tier.
PROVIDERS = [
    dict(name="groq", key="GROQ_API_KEY", url=GROQ, extra=OSS,
         models={"fast": "openai/gpt-oss-20b", "talk": "openai/gpt-oss-120b", "smart": "openai/gpt-oss-120b"}),
    dict(name="groq-20b", key="GROQ_API_KEY", url=GROQ, extra=OSS,
         models={"fast": "openai/gpt-oss-20b", "talk": "openai/gpt-oss-20b"}),
    dict(name="groq-qwen", key="GROQ_API_KEY", url=GROQ, extra={"reasoning_effort": "none"},
         models={"fast": "qwen/qwen3.8-27b", "talk": "qwen/qwen3.8-27b"}),
    dict(name="gemini", key="GEMINI_API_KEY", url="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
         extra={"reasoning_effort": "low"},
         models={"fast": "gemini-flash-lite-latest", "talk": "gemini-flash-lite-latest", "smart": "gemini-flash-lite-latest"}),
]

_cooldown: dict[str, float] = {}
STATS = {"calls": 0, "cache_hits": 0, "failures": 0, "by_provider": {}}


def available():
    return [p["name"] for p in PROVIDERS if os.environ.get(p["key"])]


def _gone(p, tier):
    """Cooling down after a rate limit or error. Kept per model: a 429 on one model leaves the others free."""
    return _cooldown.get(f"{p['name']}:{p['models'][tier]}", 0) > time.time()


def _rest(p, tier, seconds):
    _cooldown[f"{p['name']}:{p['models'][tier]}"] = time.time() + seconds


def chat(messages, tier="fast", temperature=0.6, max_tokens=220, json_mode=False, seed_key="", patience=0.0, meta=None):
    """Return the assistant's text, or None if no provider could answer.
    patience: seconds to keep retrying through rate limits (batch jobs only; the game uses 0).
    meta: an optional dict filled with who answered: provider, model, cached, ms."""
    t0 = time.time()
    body = {"messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    h = hashlib.sha256(json.dumps([body, tier, seed_key, "v3"], sort_keys=True).encode()).hexdigest()[:24]
    cached = CACHE / f"{h}.json"
    if cached.exists():
        STATS["cache_hits"] += 1
        hit = json.loads(cached.read_text())
        if meta is not None:
            meta.update(provider=hit.get("provider"), model=_model(hit.get("provider"), tier), cached=True, ms=0)
        return hit["text"]

    deadline = time.time() + patience
    while True:
        text, provider = _try_providers(body, tier, cached)
        if text is not None or time.time() >= deadline:
            if meta is not None:
                meta.update(provider=provider, model=_model(provider, tier), cached=False, ms=round((time.time() - t0) * 1000))
            return text
        time.sleep(4.0)


def _model(provider, tier):
    p = next((p for p in PROVIDERS if p["name"] == provider), None)
    return p["models"].get(tier) if p else None


def _try_providers(body, tier, cached):
    for p in PROVIDERS:
        key = os.environ.get(p["key"])
        if not key or tier not in p["models"] or _gone(p, tier):
            continue
        try:
            payload = {**body, **p.get("extra", {}), "model": p["models"][tier]}
            payload["max_tokens"] = body["max_tokens"] + 1024
            r = httpx.post(p["url"], headers={"Authorization": f"Bearer {key}"},
                           json=payload, timeout=60.0 if tier == "smart" else 12.0)
            if r.status_code == 429:
                # a per-minute limit asks for seconds, the daily token cap for minutes: wait as long as it says
                try:
                    wait = float(r.headers.get("retry-after", 20))
                except ValueError:
                    wait = 20
                _rest(p, tier, max(20, wait))
                STATS["rate_limited"] = STATS.get("rate_limited", 0) + 1
                continue
            r.raise_for_status()
            choice = r.json()["choices"][0]
            text = (choice["message"]["content"] or "").translate(_ASCII)
            if choice.get("finish_reason") == "length" and not body.get("response_format"):
                text = _last_sentence(text)
            if not text.strip():
                raise ValueError("empty completion")
            STATS["calls"] += 1
            STATS["by_provider"][p["name"]] = STATS["by_provider"].get(p["name"], 0) + 1
            cached.write_text(json.dumps({"text": text, "provider": p["name"]}))
            return text, p["name"]
        except Exception:
            STATS["failures"] += 1
            _rest(p, tier, 5)
            continue
    return None, None


# the pixel font only has ASCII: fold typographic punctuation the models like to emit
_ASCII = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "‐": "-", "‑": "-",
                        "‒": "-", "–": "-", "—": " - ", "…": "...", " ": " ", " ": " "})


def _last_sentence(text):
    """A reply cut off by the token limit ends at its last complete sentence."""
    cut = max(text.rfind(c) for c in ".!?")
    return text[:cut + 1] if cut > 0 else ""


def chat_json(messages, **kw):
    text = chat(messages, json_mode=True, **kw)
    if text is None:
        return None
    text = text.strip().strip("`")
    if text.startswith("json"):
        text = text[4:]
    try:
        return json.loads(text)
    except Exception:
        start, end = text.find("{"), text.rfind("}")
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            return None
