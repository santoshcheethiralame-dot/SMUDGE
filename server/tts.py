"""Spoken replies through Sarvam text-to-speech, called from the server so the key never reaches the browser.
With no Sarvam key, free Microsoft neural voices (edge-tts) speak instead, one cast voice per character, cached
on disk so a rehearsed line plays at once. Any failure raises TtsError; the browser then uses its own voice."""
import asyncio
import base64
import hashlib
import os
import re
import shutil
import subprocess
from collections import OrderedDict
from pathlib import Path

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


# edge-tts casting: (voice, rate, pitch). Guides and the Midnight Fall cast are chosen by ear; everyone else gets a
# stable voice from the pool. Small rate/pitch nudges only: big ones make a neural voice sound synthetic.
CAST = {
    "smudge": ("en-US-BrianNeural", "+0%", "+0Hz"),
    "foot": ("en-US-AnaNeural", "+4%", "+0Hz"),
    "narrator": ("en-US-ChristopherNeural", "-6%", "-2Hz"),
    "baron": ("en-GB-RyanNeural", "-8%", "-8Hz"),
    "varnish": ("en-GB-SoniaNeural", "-4%", "+0Hz"),
    "rivet": ("en-IE-ConnorNeural", "-8%", "-6Hz"),
    "pendle": ("en-GB-ThomasNeural", "-10%", "-2Hz"),
}
NEURAL_POOL = ["en-US-EmmaNeural", "en-US-GuyNeural", "en-GB-LibbyNeural", "en-US-EricNeural", "en-AU-NatashaNeural",
               "en-US-RogerNeural", "en-IE-EmilyNeural", "en-US-SteffanNeural", "en-IN-NeerjaExpressiveNeural",
               "en-IN-PrabhatNeural", "en-US-MichelleNeural", "en-AU-WilliamMultilingualNeural"]
DISK = Path(__file__).resolve().parent / ".cache" / "tts"
# neural voices hold 0.5-0.9 s at every full stop, which sounds like dead air in a game; cap each pause near 0.16 s
# and speak 6% faster. ffmpeg missing or failing just leaves the clip as it came.
TIGHTEN = ("silenceremove=start_periods=1:start_threshold=-50dB:stop_periods=-1:stop_duration=0.16:"
           "stop_threshold=-45dB:stop_silence=0.16,atempo=1.06")


def tighten(audio: bytes) -> bytes:
    if not shutil.which("ffmpeg"):
        return audio
    try:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", "pipe:0", "-af", TIGHTEN,
                            "-c:a", "libmp3lame", "-b:a", "64k", "-f", "mp3", "pipe:1"],
                           input=audio, capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return audio
    return r.stdout if r.returncode == 0 and r.stdout else audio


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


def cast_for(who: str) -> tuple[str, str, str]:
    if who in CAST:
        return CAST[who]
    h = 7
    for ch in who:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return NEURAL_POOL[h % len(NEURAL_POOL)], "+0%", "+0Hz"


def _edge(text: str, voice: str, rate: str, pitch: str) -> bytes:
    import edge_tts

    async def run():
        out = b""
        async for chunk in edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).stream():
            if chunk["type"] == "audio":
                out += chunk["data"]
        return out
    return asyncio.run(asyncio.wait_for(run(), TIMEOUT))


def neural(who: str, text: str) -> bytes:
    """Free neural voices for when there is no Sarvam key. SMUDGE_NEURAL_TTS=0 turns them off."""
    if os.environ.get("SMUDGE_NEURAL_TTS", "1") == "0":
        raise TtsError(503, "no SARVAM_API_KEY and neural voices are off")
    voice, rate, pitch = cast_for(who)
    path = DISK / (hashlib.sha256(f"{voice}|{rate}|{pitch}|{text}|tight1".encode()).hexdigest()[:24] + ".mp3")
    if path.exists():
        return path.read_bytes()
    try:
        audio = _edge(pronounce(text), voice, rate, pitch)
    except ImportError:
        raise TtsError(503, "no SARVAM_API_KEY and edge-tts is not installed")
    except Exception as e:
        raise TtsError(502, f"neural voice failed: {type(e).__name__}")
    if not audio:
        raise TtsError(502, "neural voice sent no audio")
    audio = tighten(audio)
    DISK.mkdir(parents=True, exist_ok=True)
    path.write_bytes(audio)
    return audio


def synthesize(who: str, text: str, client: httpx.Client | None = None) -> bytes:
    text = text.strip()
    if not text:
        raise TtsError(400, "empty text")
    key = os.environ.get("SARVAM_API_KEY")
    if not key:
        return neural(who, text[:MAX_CHARS])
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
