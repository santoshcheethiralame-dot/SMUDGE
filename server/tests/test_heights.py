"""Case 4 specifics. The shared kit contract in test_kits.py also runs on this kit."""
from collections import Counter

import pytest

import agents
import kits
import llm
from truth import new_case, check_lab

K = kits.get("heights")


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "PROVIDERS", [])
    monkeypatch.setattr(llm, "CACHE", tmp_path)


def test_innocent_photos_show_the_noon_sun_and_the_culprits_a_lower_one():
    for seed in range(4000, 4300):
        c = new_case(seed, "heights")
        for sid in K.suspects:
            r = c.public_facts["heights"][sid] / c.public_facts["shadows"][sid]
            if sid != c.culprit:
                assert abs(r - 1.73) < 0.02
            else:
                assert abs(r - 1.0) < 0.02 or abs(r - 0.58) < 0.02


def test_shadows_have_one_decimal_and_fit_the_tape():
    for seed in range(4000, 4300):
        c = new_case(seed, "heights")
        for s in c.public_facts["shadows"].values():
            assert s == round(s, 1) and 3 <= s <= 22


def test_culprits_are_spread_evenly():
    counts = Counter(new_case(s, "heights").culprit for s in range(5000, 5600))
    assert min(counts.values()) > 150


@pytest.mark.parametrize("field,mistake,step", [("r", lambda h, s: s / h, "flipped"), ("r", lambda h, s: h * s, "ratio"),
                                                ("a", lambda h, s: 45 if abs(h / s - 1.73) < 0.05 else 60, "angle")])
def test_each_classic_mistake_gets_its_own_hint(field, mistake, step):
    c = new_case(4001, "heights")
    w = K.solution(c)
    sid = next(s for s in K.suspects if s != c.culprit)
    w[f"{field}_{sid}"] = mistake(c.public_facts["heights"][sid], c.public_facts["shadows"][sid])
    out = check_lab(c, w)
    assert out["step"] == step and out["bad"] == [f"{field}_{sid}"]


def test_suspects_may_give_their_own_height_but_no_other():
    c = new_case(4002, "heights")
    sid = next(s for s in K.suspects if s != c.culprit)
    a = agents.SuspectAgent(c, sid)
    own = c.public_facts["heights"][sid]
    assert a.filter(f"My landmark is {own} m tall.")[1] is False
    assert a.filter("The shadow was 18.0 metres long.")[1] is True


@pytest.mark.parametrize("text", ["I lifted the gnomon right off.", "I was in the plaza at noon, alright?",
                                  "My photo was taken earlier, at 4 pm.", "The sun was at 30 degrees."])
def test_culprit_cannot_give_it_away(text):
    c = new_case(4003, "heights")
    assert agents.SuspectAgent(c, c.culprit).filter(text)[1] is True


@pytest.mark.parametrize("text", ["I was never in the plaza.", "I never lifted anything, petal.", "My photo was taken at noon."])
def test_denials_pass(text):
    c = new_case(4004, "heights")
    assert agents.SuspectAgent(c, c.culprit).filter(text)[1] is False
