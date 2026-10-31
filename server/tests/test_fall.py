"""Case 10 specifics. The shared kit contract in test_kits.py also runs on this kit."""
import json
from collections import Counter
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import agents
import api
import kits
import llm
from truth import new_case, check_lab

K = kits.get("fall")
FIXTURE = Path(__file__).resolve().parents[2] / "game" / "public" / "fixtures" / "fall_case.json"


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "PROVIDERS", [])
    monkeypatch.setattr(llm, "CACHE", tmp_path)
    monkeypatch.setattr(api, "POOL", tmp_path / "none.json")


def _case(culprit):
    return next(c for c in (new_case(s, "fall") for s in range(1000, 1100)) if c.culprit == culprit)


def test_culprits_are_spread_evenly():
    counts = Counter(new_case(s, "fall").culprit for s in range(5000, 5600))
    assert min(counts.values()) > 150


@pytest.mark.parametrize("height,step", [(22.05, "forgot_half"), (7.35, "not_squared"), (15.0, "height")])
def test_each_classic_mistake_gets_its_own_hint(height, step):
    c = _case("varnish")
    out = check_lab(c, {**K.solution(c), "height": height})
    assert out["step"] == step


def test_the_thunder_is_not_the_fall():
    c = _case("varnish")
    r = c.public_facts["recording"]
    assert check_lab(c, {"gap": r["thud_at"] - r["thunder_at"][0], "height": 11.0})["step"] == "gap"


def test_suspects_may_name_their_own_balcony_and_the_gossiped_one_only():
    a = agents.SuspectAgent(_case("pendle"), "rivet")
    assert a.filter("My armoury balcony is 4.9 m up.")[1] is False
    assert a.filter("Lady Varnish's gallery is 11.0 m up, mind.")[1] is False       # gossip: rivet knows varnish's
    assert a.filter("The clock room must be 19.6 m.")[1] is True
    assert a.filter("It took him 2 seconds to fall.")[1] is True


@pytest.mark.parametrize("text", ["Fine. I pushed him.", "He came out on my balcony, alright.", "He fell from my gallery."])
def test_culprit_cannot_give_it_away(text):
    assert agents.SuspectAgent(_case("varnish"), "varnish").filter(text)[1] is True


@pytest.mark.parametrize("text", ["He never came out on my balcony, darling.", "I never touched Old Tock."])
def test_culprit_can_still_deny(text):
    assert agents.SuspectAgent(_case("varnish"), "varnish").filter(text)[1] is False


def test_replies_are_capped_at_one_short_sentence():
    a = agents.SuspectAgent(_case("varnish"), "rivet")
    long = "I was polishing my helmet all night long in the armoury. Then the storm came and I hid under the stairs."
    assert a.filter(long)[0] == "Hrrm. I was polishing my helmet all night long in the armoury."
    assert "15 words" in a.system()


def test_the_game_fixture_is_what_the_server_says():
    fx = json.loads(FIXTURE.read_text(encoding="utf8"))
    c = TestClient(api.app)
    body = c.post("/api/case/new", json={"kit": "fall", "seed": 1000}).json()
    cid = body.pop("case_id")
    assert body == {k: v for k, v in fx["case_new"].items() if k != "case_id"}
    for key in ("lab_check_ok", "lab_check_wrong"):
        got = c.post("/api/lab/check", json={"case_id": cid, "working": fx[key]["request"]}).json()
        assert got == fx[key]["reply"], key
    got = c.post("/api/present", json={"case_id": cid, **fx["present_hit"]["request"]}).json()
    assert got == fx["present_hit"]["reply"]


def test_footnote_stays_short_in_the_low_text_case(monkeypatch):
    long = "*Remember: when you halve a value you must divide, not multiply. Did you double it instead of halving it?"
    monkeypatch.setattr(agents, "chat", lambda *a, **k: long)
    assert agents.Footnote().hint(K, "forgot_half") == K.hints["forgot_half"]
    monkeypatch.setattr(agents, "chat", lambda *a, **k: "*Look again at the half in your formula.")
    assert agents.Footnote().hint(K, "forgot_half") == "*Look again at the half in your formula."


@pytest.mark.parametrize("sid", list(K.suspects))
def test_a_tic_marks_who_is_talking_never_who_is_lying(sid):
    """Same tic whether this suspect is the culprit or not, on answers, refusals and scripted lines alike."""
    tic = K.suspects[sid]["tic"]
    for culprit in K.suspects:
        a = agents.SuspectAgent(_case(culprit), sid)
        assert a.filter("The rain is heavy tonight.")[0] == f"{tic} The rain is heavy tonight."
        assert a.filter("Fine. I pushed him.")[0].startswith(tic + " ")
        assert a.ask("Nice weather?")["answer"].startswith(tic + " ")


def test_a_tic_is_never_doubled():
    a = agents.SuspectAgent(_case("varnish"), "varnish")
    assert a.filter("Oh, darling, the gallery is lovely.")[0] == "Oh, darling. The gallery is lovely."
    assert a.filter("oh darling... I heard a cry.")[0] == "Oh, darling. I heard a cry."


def test_a_reply_that_opens_with_the_tic_keeps_its_words():
    a = agents.SuspectAgent(_case("varnish"), "varnish")
    said = "I heard a cry from high above, then a thud that shook every frame in the long hall downstairs."
    assert a.filter("Oh, darling. " + said)[0] == "Oh, darling. " + said
    assert a.filter("Oh, darling.")[0] == "Oh, darling. I couldn't say."


@pytest.mark.parametrize("text,blocked", [("My balcony is the gallery, eleven metres up.", False),
                                          ("My gallery balcony stands 11.0 m above the courtyard.", False),
                                          ("He came out on my balcony, briefly.", True),
                                          ("Old Tock stood on my balcony at midnight.", True),
                                          ("Tock never came out on my balcony.", False)])
def test_the_culprit_may_describe_her_balcony_but_not_put_him_on_it(text, blocked):
    assert agents.SuspectAgent(_case("varnish"), "varnish").filter(text)[1] is blocked
