"""Sarvam speech-to-text route: mocked at the HTTP layer, so no key or network is needed."""
import httpx
import pytest
from fastapi.testclient import TestClient

import api
import stt

client = TestClient(api.app)


def _mock(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.fixture
def key(monkeypatch):
    monkeypatch.setenv("SARVAM_API_KEY", "test-key")


def test_transcribes_and_sends_key_only_to_sarvam(key):
    seen = {}

    def handler(req):
        seen["key"] = req.headers["api-subscription-key"]
        seen["url"] = str(req.url)
        return httpx.Response(200, json={"transcript": " where were you at midnight? "})

    assert stt.transcribe(b"audio", "audio/webm;codecs=opus", _mock(handler)) == "where were you at midnight?"
    assert seen == {"key": "test-key", "url": stt.URL}


def test_route_returns_text(key, monkeypatch):
    monkeypatch.setattr(stt, "transcribe", lambda audio, ct: "hello")
    r = client.post("/api/stt", content=b"abc", headers={"content-type": "audio/webm"})
    assert r.status_code == 200 and r.json() == {"text": "hello"}


def test_no_key_is_503_so_browser_falls_back(monkeypatch):
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    assert client.post("/api/stt", content=b"abc", headers={"content-type": "audio/webm"}).status_code == 503


def test_empty_audio_is_400(key):
    assert client.post("/api/stt", content=b"", headers={"content-type": "audio/webm"}).status_code == 400


def test_sarvam_error_and_timeout_are_502(key):
    with pytest.raises(stt.SttError) as e:
        stt.transcribe(b"a", client=_mock(lambda r: httpx.Response(429, json={})))
    assert e.value.status == 502

    def boom(r):
        raise httpx.ReadTimeout("slow")

    with pytest.raises(stt.SttError) as e:
        stt.transcribe(b"a", client=_mock(boom))
    assert e.value.status == 502
