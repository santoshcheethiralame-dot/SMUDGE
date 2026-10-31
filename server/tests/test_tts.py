"""Sarvam text-to-speech route: mocked at the HTTP layer, so no key or network is needed."""
import base64

import httpx
import pytest
from fastapi.testclient import TestClient

import api
import tts

client = TestClient(api.app)


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "test-key")
    tts._cache.clear()


def _mock(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_synthesize_decodes_audio_and_caches():
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(200, json={"audios": [base64.b64encode(b"MP3DATA").decode()]})

    assert tts.synthesize("volta", "Hello there.", _mock(handler)) == b"MP3DATA"
    assert tts.synthesize("volta", "Hello there.", _mock(handler)) == b"MP3DATA"
    assert len(calls) == 1                                     # the repeat came from the cache
    assert calls[0].headers["api-subscription-key"] == "test-key"


def test_speakers_are_stable_and_guides_are_fixed():
    assert tts.speaker_for("volta") == tts.speaker_for("volta")
    assert tts.speaker_for("smudge") != tts.speaker_for("foot")


def test_route_returns_mp3(monkeypatch):
    monkeypatch.setattr(tts, "synthesize", lambda who, text: b"abc")
    r = client.post("/api/tts", json={"who": "volta", "text": "hi"})
    assert r.status_code == 200 and r.headers["content-type"] == "audio/mpeg" and r.content == b"abc"


def test_no_key_503_and_empty_400(monkeypatch):
    assert client.post("/api/tts", json={"who": "v", "text": "  "}).status_code == 400
    monkeypatch.delenv("SARVAM_API_KEY")
    monkeypatch.setenv("SMUDGE_NEURAL_TTS", "0")
    assert client.post("/api/tts", json={"who": "v", "text": "hi"}).status_code == 503


def test_no_key_speaks_with_a_cast_neural_voice_and_caches_on_disk(monkeypatch, tmp_path):
    monkeypatch.delenv("SARVAM_API_KEY")
    monkeypatch.setenv("SMUDGE_NEURAL_TTS", "1")
    monkeypatch.setattr(tts, "DISK", tmp_path)
    calls = []
    monkeypatch.setattr(tts, "_edge", lambda text, voice, rate, pitch: calls.append((text, voice)) or b"mp3")
    monkeypatch.setattr(tts, "tighten", lambda audio: audio)
    assert tts.synthesize("varnish", "Hrrm. Darling.") == b"mp3"
    assert tts.synthesize("varnish", "Hrrm. Darling.") == b"mp3"
    assert calls == [("Hmm. Darling.", "en-GB-SoniaNeural")]
    assert tts.cast_for("volta") == tts.cast_for("volta") and tts.cast_for("volta")[0] in tts.NEURAL_POOL


def test_neural_failure_is_502(monkeypatch, tmp_path):
    monkeypatch.delenv("SARVAM_API_KEY")
    monkeypatch.setenv("SMUDGE_NEURAL_TTS", "1")
    monkeypatch.setattr(tts, "DISK", tmp_path)

    def down(*a):
        raise OSError("offline")
    monkeypatch.setattr(tts, "_edge", down)
    with pytest.raises(tts.TtsError) as e:
        tts.synthesize("rivet", "hi")
    assert e.value.status == 502


def test_sarvam_failures_are_502():
    with pytest.raises(tts.TtsError) as e:
        tts.synthesize("v", "hi", _mock(lambda r: httpx.Response(500, json={})))
    assert e.value.status == 502

    def boom(r):
        raise httpx.ReadTimeout("slow")

    with pytest.raises(tts.TtsError):
        tts.synthesize("v", "hi", _mock(boom))
    with pytest.raises(tts.TtsError):
        tts.synthesize("v", "hi", _mock(lambda r: httpx.Response(200, json={})))


def test_noises_are_spelled_speakably():
    assert tts.pronounce("Hrrrrm. I was polishing my helmet.") == "Hmm. I was polishing my helmet."
    assert tts.pronounce("Pssssst! Over here.") == "Psst! Over here."
    assert tts.pronounce("Where were you?") == "Where were you?"


def test_tighten_keeps_the_clip_when_ffmpeg_fails(monkeypatch):
    monkeypatch.setattr(tts.shutil, "which", lambda name: None)
    assert tts.tighten(b"raw") == b"raw"
    monkeypatch.setattr(tts.shutil, "which", lambda name: "ffmpeg")
    assert tts.tighten(b"not an mp3") == b"not an mp3"
