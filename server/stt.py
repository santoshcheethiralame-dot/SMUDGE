"""Speech to text through Sarvam, called from the server so the key never reaches the browser.
Any failure raises SttError; the browser then falls back to its own on-device recognition."""
import os

import httpx

URL = "https://api.sarvam.ai/speech-to-text"
TIMEOUT = 6.0          # seconds; the stage can't wait longer than this on a mic press
MAX_BYTES = 2_000_000  # hold-to-talk clips are a few seconds; this is a generous ceiling


class SttError(Exception):
    def __init__(self, status: int, why: str):
        super().__init__(why)
        self.status, self.why = status, why


def available() -> bool:
    return bool(os.environ.get("SARVAM_API_KEY"))


def transcribe(audio: bytes, content_type: str = "audio/webm", client: httpx.Client | None = None) -> str:
    key = os.environ.get("SARVAM_API_KEY")
    if not key:
        raise SttError(503, "no SARVAM_API_KEY")
    if not audio:
        raise SttError(400, "empty audio")
    if len(audio) > MAX_BYTES:
        raise SttError(413, "audio too large")
    ext = "ogg" if "ogg" in content_type else "mp4" if "mp4" in content_type else "webm"
    try:
        c = client or httpx.Client(timeout=TIMEOUT)
        r = c.post(
            URL,
            headers={"api-subscription-key": key},
            files={"file": (f"clip.{ext}", audio, content_type.split(";")[0] or "audio/webm")},
            data={"model": "saaras:v4", "language_code": "en-IN"},
        )
    except httpx.HTTPError as e:
        raise SttError(502, f"sarvam unreachable: {type(e).__name__}")
    if r.status_code != 200:
        raise SttError(502, f"sarvam {r.status_code}")
    return (r.json().get("transcript") or "").strip()
