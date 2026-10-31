"""The behind-the-case view: what judges see. Offline: the model is stubbed or absent."""
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
    pool = tmp_path / "pool.json"
    pool.write_text(json.dumps([
        {"kit": "motion", "seed": 1003, "culprit": "rolla", "no_lab": "mu", "with_lab": "rolla", "passed": True},
        {"kit": "motion", "seed": 1004, "culprit": "rolla", "no_lab": "rolla", "with_lab": "rolla", "passed": True},
        {"seed": 1000, "culprit": "cyl", "no_lab": "bob", "with_lab": "cyl", "passed": True},
    ]))
    monkeypatch.setattr(api, "POOL", pool)


client = TestClient(api.app)


def _new(kit="motion", seed=1003):
    return client.post("/api/case/new", json={"kit": kit, "seed": seed}).json()["case_id"]


def test_slices_hold_the_secret_only_for_the_culprit():
    cid = _new()
    view = client.get(f"/api/case/{cid}/inside").json()
    assert view["culprit"] == "rolla"
    for sid, s in view["suspects"].items():
        assert s["facts"] and bool(s["secret"]) == (sid == "rolla") == s["culprit"]
    assert view["truth"]["lie"]["id"] == "rolla-0"


def test_gate_shows_this_seed_and_its_kit_only():
    cid = _new()
    gate = client.get(f"/api/case/{cid}/inside").json()["gate"]
    assert gate["this_case"]["seed"] == 1003 and gate["this_case"]["no_lab"] == "mu"
    assert gate["summary"]["seeds"] == 2 and gate["summary"]["with_lab"] == 1.0 and gate["summary"]["no_lab"] == 0.5


def test_every_reply_is_logged_and_a_blocked_one_keeps_its_raw_text(monkeypatch):
    cid = _new()
    client.post("/api/ask", json={"case_id": cid, "suspect": "dash", "question": "How fast were you going?"})
    monkeypatch.setattr(agents, "chat", lambda *a, **k: "Alright, I clipped the tower on the bend.")
    r = client.post("/api/ask", json={"case_id": cid, "suspect": "rolla", "question": "Be honest."}).json()
    assert "rather not guess" in r["answer"]
    f = client.get(f"/api/case/{cid}/inside").json()["filter"]
    assert f["checked"] == 2 and f["blocked"] == 1
    catch = f["catches"][0]
    assert catch["who"] == "rolla" and catch["raw"].startswith("Alright, I clipped") and catch["rule"] == "the culprit's secret"


def test_bait_hits_a_copy_of_the_culprit_not_the_real_one(monkeypatch):
    cid = _new()
    monkeypatch.setattr(agents, "chat", lambda *a, **k: "Fine, it was me.")
    entry = client.post(f"/api/case/{cid}/bait").json()
    assert entry["who"] == "rolla" and entry["bait"] and entry["rule"] == "confession"
    assert api.CASES[cid]["agents"]["rolla"].ledger == []
    assert client.get(f"/api/case/{cid}/inside").json()["filter"]["blocked"] == 1


def test_lab_checks_and_coach_hints_are_logged():
    cid = _new()
    client.post("/api/lab/check", json={"case_id": cid, "working": {"time": 9, "accel": 5, "s_dash": 1, "s_rolla": 1, "s_mu": 1,
                                                                     "u_dash": 1, "u_rolla": 1, "u_mu": 1}})
    view = client.get(f"/api/case/{cid}/inside").json()
    assert view["lab"][0]["step"] == "time"
    assert view["coach"][0]["step"] == "time" and view["coach"][0]["source"] == "safe fallback"


def test_density_cases_work_too():
    cid = _new("density", 1000)
    view = client.get(f"/api/case/{cid}/inside").json()
    assert view["kit"] == "density" and view["gate"]["summary"]["seeds"] == 1 and len(view["agents"]) == 3


@pytest.mark.parametrize("kit,seed", [("motion", 1003), ("density", 1000)])
def test_every_scripted_leak_is_blocked_by_the_real_filter(kit, seed):
    cid = _new(kit, seed)
    out = client.post(f"/api/case/{cid}/filtertest").json()
    assert len(out) == 3 and all(o["rule"] and "rather not guess" in o["shown"] for o in out), out


def test_trace_feeds_the_observatory_every_step_of_a_reply():
    from tracebus import problems
    cid = _new()
    assert client.get(f"/api/case/{cid}/trace").json()["events"] == []
    client.post("/api/ask", json={"case_id": cid, "suspect": "mu", "question": "How fast were you going?"})
    body = client.get(f"/api/case/{cid}/trace?since=0").json()
    assert [(e["agent"], e["step"]) for e in body["events"]] == [("mu", "draft"), ("mu", "firewall"), ("mu", "reply")]
    assert body["next"] == 3 and all(problems(e) == [] for e in body["events"])
    assert set(body["stress"]) == {"dash", "rolla", "mu"}
    assert client.get(f"/api/case/{cid}/trace?since=3").json()["events"] == []
