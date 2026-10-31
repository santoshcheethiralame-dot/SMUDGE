"""The Author pipeline, offline: a scripted model and a scripted detective, real Solver and Casting."""
import json

import pytest

import author
import kits
from tracebus import problems

SPEED = json.loads((author.GOLDEN / "speed.json").read_text(encoding="utf8"))


class Det:
    think = None

    def __init__(self, right=True):
        self.right = right

    def solve(self, case, with_lab):
        return case.culprit if with_lab and self.right else next(iter(kits.get(case.kit).suspects))


def fake_chat(designs, critic_ok=True):
    calls = iter(designs)

    def chat(messages, **kw):
        if messages[0]["content"].startswith("You review"):
            return {"ok": critic_ok, "issues": [] if critic_ok else ["too scary"]}
        return next(calls)
    return chat


@pytest.fixture(autouse=True)
def sandbox(monkeypatch, tmp_path):
    monkeypatch.setattr(author, "GENERATED", tmp_path / "generated")
    monkeypatch.setattr(author, "POOL", tmp_path / "pool.json")
    yield
    for k in [k for k in kits.REGISTRY if k.startswith("gen_speed_")]:
        kits.REGISTRY.pop(k)


def test_solver_problems_go_back_to_the_designer_and_the_fix_is_gated_and_saved(tmp_path):
    messy = {**SPEED, "ins": [{**SPEED["ins"][0]}, {**SPEED["ins"][1], "values": [3, 7, 9]}]}
    job = author.Job("Class 8, speed: v = d/t")
    author.run(job, chat=fake_chat([messy, SPEED]), detective=Det())
    assert job.status == "done", job.error
    steps = [(e["agent"], e["step"], e["verdict"]) for e in job.trace.events]
    assert steps[:2] == [("designer", "design", "ok"), ("solver", "solve", "block")]
    assert ("critic", "critique", "pass") in steps and ("casting", "cast", "ok") in steps
    assert sum(s == ("gate", "gate", "pass") for s in steps) == 4
    assert all(not problems(e) for e in job.trace.events)
    saved = json.loads((tmp_path / "generated" / f"{job.spec['id']}.json").read_text(encoding="utf8"))
    assert saved["formula"] == "v = d / t" and job.spec["id"] in kits.REGISTRY
    assert {r["kit"] for r in json.loads((tmp_path / "pool.json").read_text())} == {job.spec["id"]}


def test_the_critic_can_send_it_back_until_the_rounds_run_out():
    job = author.Job("speed")
    author.run(job, chat=fake_chat([SPEED] * 3, critic_ok=False), detective=Det())
    assert job.status == "failed" and "3 rounds" in job.error


def test_a_case_the_detective_cannot_solve_is_not_kept(tmp_path):
    job = author.Job("speed")
    author.run(job, chat=fake_chat([SPEED]), detective=Det(right=False))
    assert job.status == "failed" and not (tmp_path / "generated").exists()
    assert not any(k.startswith("gen_speed_") for k in kits.REGISTRY)


def test_no_model_means_the_golden_spec():
    job = author.Job("Class 9, pressure: P = F/A")
    spec = author.design(job, [], None, 1, chat=lambda *a, **k: None)
    assert spec["id"] == "gen_pressure" and job.trace.events[0]["verdict"] == "fallback"


def test_the_api_serves_jobs_and_authored_specs(monkeypatch):
    from fastapi.testclient import TestClient
    import api
    job = author.Job("speed")
    job.id = "j1"
    monkeypatch.setitem(author.JOBS, "j1", job)
    monkeypatch.setattr(author, "start", lambda prompt: job)
    client = TestClient(api.app)
    assert client.post("/api/author", json={"prompt": "speed"}).json() == {"job": "j1"}
    assert client.get("/api/author/j1").json()["status"] == "running"
    assert client.get("/api/author/nope").status_code == 404
    assert {"gen_pressure", "gen_speed"} <= {s["id"] for s in client.get("/api/kits/generated").json()}
