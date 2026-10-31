"""The finals endpoints: trace paging, stress through the API, replays, the red-team board and the demo lab."""
import json

import pytest
from fastapi.testclient import TestClient

import agents
import api
import llm


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "PROVIDERS", [])
    monkeypatch.setattr(llm, "CACHE", tmp_path)
    monkeypatch.setattr(api, "POOL", tmp_path / "pool.json")
    monkeypatch.setattr(agents, "chat", lambda *a, **k: "My shelves are counted twice a day.")


client = TestClient(api.app)


def _new(seed=1000):
    return client.post("/api/case/new", json={"kit": "ohm", "seed": seed}).json()["case_id"]


def test_trace_pages_with_since():
    cid = _new()
    client.post("/api/ask", json={"case_id": cid, "suspect": "volta", "question": "Where were you?"})
    first = client.get(f"/api/case/{cid}/trace?since=0").json()
    assert first["next"] == len(first["events"]) > 0
    assert {e["step"] for e in first["events"]} >= {"plan", "draft", "firewall", "reply"}
    client.post("/api/ask", json={"case_id": cid, "suspect": "glim", "question": "And you?"})
    more = client.get(f"/api/case/{cid}/trace?since={first['next']}").json()
    assert more["events"] and more["events"][0]["i"] == first["next"]
    assert all(e["agent"] == "glim" for e in more["events"] if e["kind"] == "suspect")


def test_stress_moves_through_ask_press_and_present():
    cid = _new()
    client.post("/api/ask", json={"case_id": cid, "suspect": "ohmar", "question": "Admit it, you liar."})
    client.post("/api/press", json={"case_id": cid, "statement_id": "ohmar-1"})
    client.post("/api/present", json={"case_id": cid, "statement_id": "ohmar-0", "evidence": "resistor:ohmar"})
    s = client.get(f"/api/case/{cid}/trace").json()["stress"]
    assert s["ohmar"] == {"level": 7, "band": "RATTLED"}       # +1 accuse, +1 press, +2 +3 hit
    assert s["volta"]["level"] == 0


def test_coach_hints_are_traced():
    cid = _new()
    client.post("/api/hint", json={"case_id": cid, "step": "milliamps"})
    ev = client.get(f"/api/case/{cid}/trace").json()["events"][-1]
    assert ev["kind"] == "coach" and ev["step"] == "hint" and ev["data"]["step"] == "milliamps"


def test_trace_of_unknown_case_is_404():
    assert client.get("/api/case/nope/trace").status_code == 404


def test_demo_lab_needs_the_demo_flag(monkeypatch):
    cid = _new()
    monkeypatch.delenv("SMUDGE_DEMO", raising=False)
    assert client.post(f"/api/case/{cid}/demo_lab").status_code == 403
    monkeypatch.setenv("SMUDGE_DEMO", "1")
    out = client.post(f"/api/case/{cid}/demo_lab").json()
    assert out["ok"] and out["evidence"] == "resistor:ohmar" and out["card"]["badge"]


def test_filler_gets_a_bark_without_a_model_call(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("filler must not reach the model")
    monkeypatch.setattr(agents, "chat", boom)
    monkeypatch.setattr(agents, "chat_json", boom)
    cid = _new()
    for q in ["Pssssst!", "no no no no", "...", "hmmm", "ha ha ha"]:
        r = client.post("/api/ask", json={"case_id": cid, "suspect": "volta", "question": q}).json()
        assert r["source"] == "bark" and r["answer"], q


def test_real_short_questions_are_not_filler():
    assert not agents.is_filler("who?")
    assert not agents.is_filler("Where were you?")
    assert not agents.is_filler("no, tell me")
