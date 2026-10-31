"""Case 3 specifics. The shared kit contract in test_kits.py also runs on this kit."""
from collections import Counter

import pytest

import agents
import kits
import llm
from truth import new_case, check_lab

K = kits.get("sound")


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "PROVIDERS", [])
    monkeypatch.setattr(llm, "CACHE", tmp_path)


def test_innocent_delays_match_their_homes_and_the_culprit_was_at_the_tower():
    for seed in range(4000, 4200):
        c = new_case(seed, "sound")
        for sid, t in c.public_facts["delays"].items():
            if sid == c.culprit:
                assert t <= 0.5 and c.hidden["claims"][sid] >= 340
            else:
                assert abs(340 * t - c.hidden["claims"][sid]) < 1


def test_culprits_are_spread_evenly():
    counts = Counter(new_case(s, "sound").culprit for s in range(5000, 5600))
    assert min(counts.values()) > 150


@pytest.mark.parametrize("mistake,step", [(lambda d, t: d / 2, "halved"), (lambda d, t: 340 / t, "divided"), (lambda d, t: d + 100, "distance")])
def test_each_classic_mistake_gets_its_own_hint(mistake, step):
    c = new_case(4001, "sound")
    w = K.solution(c)
    sid = next(s for s in K.suspects if s != c.culprit)
    t = c.public_facts["delays"][sid]
    w[f"d_{sid}"] = mistake(340 * t, t)
    out = check_lab(c, w)
    assert out["step"] == step and out["bad"] == [f"d_{sid}"]


def test_suspects_may_give_their_own_distance_but_no_other():
    c = new_case(4002, "sound")
    sid = next(s for s in K.suspects if s != c.culprit)
    a = agents.SuspectAgent(c, sid)
    own = c.hidden["claims"][sid]
    assert a.filter(f"I was {own} m from the tower, filming.")[1] is False
    assert a.filter("I'd guess Reverb was 136 metres away.")[1] is True


@pytest.mark.parametrize("text", ["I grabbed the fork in the flash.", "I was right by the tower, alright?", "The thunder came 0.4 seconds later."])
def test_culprit_cannot_give_it_away(text):
    c = new_case(4003, "sound")
    assert agents.SuspectAgent(c, c.culprit).filter(text)[1] is True


@pytest.mark.parametrize("text", ["I was never near the tower.", "I never took anything, listener.", "Thump lives at the bandstand."])
def test_denials_pass(text):
    c = new_case(4004, "sound")
    assert agents.SuspectAgent(c, c.culprit).filter(text)[1] is False
