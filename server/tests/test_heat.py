"""Case 7 specifics. The shared kit contract in test_kits.py also runs on this kit."""
from collections import Counter

import pytest

import agents
import kits
import llm
from kits.heat import metal_for
from truth import new_case, check_lab

K = kits.get("heat")


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "PROVIDERS", [])
    monkeypatch.setattr(llm, "CACHE", tmp_path)


def test_whole_degree_readings_still_name_the_right_metal():
    for seed in range(4000, 4300):
        c = new_case(seed, "heat")
        p = c.public_facts
        cc = p["water_kg"] * 4200 * (p["t2"] - p["t1"]) / (p["block_kg"] * (100 - p["t2"]))
        assert metal_for(cc) == K.suspects[c.culprit]["metal"]
        assert p["t2"] == int(p["t2"]) and p["t2"] - p["t1"] >= 9


def test_culprits_are_spread_evenly():
    counts = Counter(new_case(s, "heat").culprit for s in range(5000, 5600))
    assert min(counts.values()) > 150


@pytest.mark.parametrize("field,mistake,step", [
    ("q", lambda w: w["mw"] * 4200 * w["t2"], "rise"),
    ("c", lambda w: w["q"] / (w["mb"] * w["t2"]), "drop"),
    ("c", lambda w: w["mb"] * (100 - w["t2"]) / w["q"], "flipped"),
])
def test_each_classic_mistake_gets_its_own_hint(field, mistake, step):
    c = new_case(4001, "heat")
    w = K.solution(c)
    w[field] = mistake(w)
    out = check_lab(c, w)
    assert out["step"] == step and out["bad"] == [field]


@pytest.mark.parametrize("text", ["I melted the lock with a hot block.", "A block of my copper has gone missing.",
                                  "The water rose 14 degrees, I'd say."])
def test_culprit_cannot_give_it_away(text):
    c = next(new_case(s, "heat") for s in range(4000, 4100) if new_case(s, "heat").culprit == "brewster")
    assert agents.SuspectAgent(c, "brewster").filter(text)[1] is True


@pytest.mark.parametrize("text", ["Yes, I work copper. Every block is accounted for.", "I never went near the bathhouse safe.",
                                  "Al works aluminium, mind."])
def test_denials_pass(text):
    c = next(new_case(s, "heat") for s in range(4000, 4100) if new_case(s, "heat").culprit == "brewster")
    assert agents.SuspectAgent(c, "brewster").filter(text)[1] is False
