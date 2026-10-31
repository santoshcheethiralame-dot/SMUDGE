"""Case 9 specifics. The shared kit contract in test_kits.py also runs on this kit."""
from collections import Counter

import pytest

import agents
import kits
import llm
from truth import new_case, check_lab

K = kits.get("power")


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "PROVIDERS", [])
    monkeypatch.setattr(llm, "CACHE", tmp_path)


def test_lift_times_are_half_seconds_a_stopwatch_can_catch():
    for seed in range(4000, 4200):
        t = new_case(seed, "power").public_facts["seconds"]
        assert t * 2 == int(t * 2) and 3 <= t <= 15


def test_culprits_are_spread_evenly():
    counts = Counter(new_case(s, "power").culprit for s in range(5000, 5600))
    assert min(counts.values()) > 150


@pytest.mark.parametrize("field,mistake,step", [
    ("w", lambda w: w["m"] * w["h"], "gravity"),
    ("p", lambda w: w["w"] * w["t"], "times"),
    ("p", lambda w: w["t"] / w["w"], "flipped"),
])
def test_each_classic_mistake_gets_its_own_hint(field, mistake, step):
    c = new_case(4001, "power")
    w = K.solution(c)
    w[field] = mistake(w)
    out = check_lab(c, w)
    assert out["step"] == step and out["bad"] == [field]


@pytest.mark.parametrize("text", ["I winched the crate up the tower.", "My winch was running half the night.",
                                  "The lift took 12 seconds, I reckon.", "Must have been a 1200 W job."])
def test_culprit_cannot_give_it_away(text):
    c = next(new_case(s, "power") for s in range(4000, 4100) if new_case(s, "power").culprit == "cog")
    assert agents.SuspectAgent(c, "cog").filter(text)[1] is True


@pytest.mark.parametrize("text", ["My winch is the 400 W one. It was off all night.", "I never went near the clock tower lift.",
                                  "Hoist has an 800 W winch, mind."])
def test_denials_pass(text):
    c = next(new_case(s, "power") for s in range(4000, 4100) if new_case(s, "power").culprit == "cog")
    assert agents.SuspectAgent(c, "cog").filter(text)[1] is False
