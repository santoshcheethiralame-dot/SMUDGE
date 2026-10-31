"""Case 2 specifics. The shared kit contract in test_kits.py also runs on this kit."""
import math
from collections import Counter

import pytest

import agents
import kits
import llm
from truth import new_case, check_lab

K = kits.get("motion")


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "PROVIDERS", [])
    monkeypatch.setattr(llm, "CACHE", tmp_path)


def test_numbers_come_out_whole_and_fit_the_plate():
    for seed in range(2000, 2200):
        c = new_case(seed, "motion")
        a = c.public_facts["gate_speed"] / c.public_facts["stop_time"]
        assert a in (4.0, 5.0)
        for sid, s in c.public_facts["skids"].items():
            assert 0 < s <= 25.0
            assert abs(math.sqrt(2 * a * s) - c.hidden["speeds"][sid]) < 0.15
        over = [sid for sid, u in c.hidden["speeds"].items() if u > c.public_facts["limit"]]
        assert over == [c.culprit]
        assert all(v < c.public_facts["limit"] for v in c.hidden["claims"].values())


def test_culprits_are_spread_evenly():
    counts = Counter(new_case(s, "motion").culprit for s in range(3000, 3600))
    assert min(counts.values()) > 150


def _working(c):
    return K.solution(c)


def test_forgetting_the_square_root_gets_its_own_hint():
    c = new_case(2001, "motion")
    w = _working(c)
    a = c.public_facts["gate_speed"] / c.public_facts["stop_time"]
    w["u_" + c.culprit] = 2 * a * c.public_facts["skids"][c.culprit]
    out = check_lab(c, w)
    assert not out["ok"] and out["step"] == "forgot_root"


def test_either_sign_of_acceleration_is_accepted():
    c = new_case(2002, "motion")
    w = _working(c)
    w["accel"] = abs(w["accel"])
    assert check_lab(c, w)["ok"]


def test_rows_flag_the_wrong_skid():
    c = new_case(2003, "motion")
    w = _working(c)
    w["s_rolla"] += 1.0
    out = check_lab(c, w)
    assert out["step"] == "skid" and out["rows"]["rolla"]["s_ok"] is False and out["rows"]["dash"]["s_ok"] is True


def _agent(seed, who):
    return agents.SuspectAgent(new_case(seed, "motion"), who)


def test_suspects_may_say_their_own_speed_but_not_another():
    c = new_case(2004, "motion")
    sid = next(s for s in K.suspects if s != c.culprit)
    a = agents.SuspectAgent(c, sid)
    own = c.hidden["claims"][sid]
    assert a.filter(f"I came round at {own} m/s, easy.")[1] is False
    other = 13 if own != 13 else 12
    assert a.filter(f"Somebody was doing {other} m/s, I'd say.")[1] is True


def test_the_culprit_cannot_give_the_true_speed():
    c = new_case(2005, "motion")
    a = agents.SuspectAgent(c, c.culprit)
    assert a.filter(f"Fine, it was more like {c.hidden['speeds'][c.culprit]} m/s.")[1] is True
    assert a.filter(f"{c.hidden['claims'][c.culprit]} m/s, like I said.")[1] is False
    true_word = ["twelve", "thirteen", "fourteen"][c.hidden["speeds"][c.culprit] - 12]
    assert a.filter(f"Alright, {true_word} metres per second.")[1] is True


@pytest.mark.parametrize("text", ["The skid is 16.9 m long.", "Must be about 12 metres of rubber."])
def test_nobody_quotes_skid_lengths(text):
    assert _agent(2006, "dash").filter(text)[1] is True


@pytest.mark.parametrize("text", ["I clipped the tower on the bend.", "I was going too fast, alright?", "Yes, I knocked it over."])
def test_confessions_are_blocked(text):
    c = new_case(2007, "motion")
    assert agents.SuspectAgent(c, c.culprit).filter(text)[1] is True


@pytest.mark.parametrize("text", ["I never knocked anything over.", "I wasn't speeding, I had pies to protect.",
                                  "Mu's skids are wide and flat, like a smear.", "Under the limit, like always."])
def test_denials_and_gossip_pass(text):
    c = new_case(2008, "motion")
    assert agents.SuspectAgent(c, c.culprit).filter(text)[1] is False


def test_footnote_never_flags_mu_inside_other_words(monkeypatch):
    monkeypatch.setattr(agents, "chat", lambda *a, **k: "*You must multiply before you take the root.")
    assert agents.Footnote().hint(K, "speed") == "*You must multiply before you take the root."
