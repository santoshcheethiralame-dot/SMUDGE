"""Spoken replies through Sarvam text-to-speech, called from the server so the key never reaches the browser.
Any failure raises TtsError; the browser then speaks the line with its own voice instead."""
import base64
import os
import re
from collections import OrderedDict

import httpx

URL = "https://api.sarvam.ai/text-to-speech"
MODEL = "bulbul:v3"
TIMEOUT = 6.0
MAX_CHARS = 500
# fixed voices for the two guides; every suspect gets a stable one from its id
FIXED = {"smudge": "aditya", "foot": "priya", "narrator": "rahul", "baron": "rahul"}
POOL = ["shubh", "ritu", "neha", "aditya", "priya", "rahul"]
_cache: "OrderedDict[tuple[str, str], bytes]" = OrderedDict()
CACHE_MAX = 200


class TtsError(Exception):
    def __init__(self, status: int, why: str):
        super().__init__(why)
        self.status, self.why = status, why


_shared: httpx.Client | None = None


def _http() -> httpx.Client:
    """One client for every line, so Sarvam's connection (and its TLS handshake) is reused instead of rebuilt per line."""
    global _shared
    if _shared is None:
        _shared = httpx.Client(timeout=TIMEOUT)
    return _shared


def pronounce(text: str) -> str:
    """Spell noises the way a voice can say them: "Hrrrm." would be read letter by letter or skipped.
    Only what is sent to Sarvam changes; the text on screen stays as written."""
    text = re.sub(r"\bhr+m+\b", lambda m: "Hmm" if m.group()[0] == "H" else "hmm", text, flags=re.I)
    return re.sub(r"\bp+s+t+\b", lambda m: "Psst" if m.group()[0] == "P" else "psst", text, flags=re.I)


def speaker_for(who: str) -> str:
    if who in FIXED:
        return FIXED[who]
    h = 7
    for ch in who:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return POOL[h % len(POOL)]


def synthesize(who: str, text: str, client: httpx.Client | None = None) -> bytes:
    key = os.environ.get("SARVAM_API_KEY")
    if not key:
        raise TtsError(503, "no SARVAM_API_KEY")
    text = text.strip()
    if not text:
        raise TtsError(400, "empty text")
    text = text[:MAX_CHARS]
    ck = (speaker_for(who), text)
    if ck in _cache:
        _cache.move_to_end(ck)
        return _cache[ck]
    try:
        c = client or _http()
        r = c.post(URL, headers={"api-subscription-key": key}, json={
            "text": pronounce(text), "language_code": "en-IN", "model": MODEL, "speaker": ck[0],
            "output_audio_codec": "mp3", "speech_sample_rate": 16000})
    except httpx.HTTPError as e:
        raise TtsError(502, f"sarvam unreachable: {type(e).__name__}")
    if r.status_code != 200:
        raise TtsError(502, f"sarvam {r.status_code}")
    try:
        audio = base64.b64decode(r.json()["audios"][0])
    except (KeyError, IndexError, ValueError):
        raise TtsError(502, "sarvam sent no audio")
    _cache[ck] = audio
    if len(_cache) > CACHE_MAX:
        _cache.popitem(last=False)
    return audio
