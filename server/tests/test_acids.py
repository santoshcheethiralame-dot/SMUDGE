"""Case 8 specifics. The shared kit contract in test_kits.py also runs on this kit."""
from collections import Counter

import pytest

import agents
import kits
import llm
from truth import new_case, check_lab

K = kits.get("acids")


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "PROVIDERS", [])
    monkeypatch.setattr(llm, "CACHE", tmp_path)


def test_the_fountain_never_matches_a_product_until_the_dilution_is_undone():
    for seed in range(4000, 4200):
        p = new_case(seed, "acids").public_facts
        assert p["fountain_ph"] not in p["products"].values()


def test_culprits_are_spread_evenly():
    counts = Counter(new_case(s, "acids").culprit for s in range(5000, 5600))
    assert min(counts.values()) > 150


@pytest.mark.parametrize("field,mistake,step", [
    ("factor", lambda w: w["poured"] / w["total"], "dilution"),
    ("shift", lambda w: w["factor"], "shift"),
    ("before", lambda w: w["ph"], "direction"),
])
def test_each_classic_mistake_gets_its_own_hint(field, mistake, step):
    c = new_case(4001, "acids")
    w = K.solution(c)
    w[field] = mistake(w)
    out = check_lab(c, w)
    assert out["step"] == step and out["bad"] == [field]


def test_stepping_the_wrong_way_is_caught():
    for seed in range(4000, 4030):
        c = new_case(seed, "acids")
        w = K.solution(c)
        w["before"] = w["ph"] + (w["ph"] - w["before"])
        assert check_lab(c, w)["step"] == "direction"


@pytest.mark.parametrize("text", ["I emptied my can into the fountain.", "I was by the fountain at midnight.", "It's about pH 9 in there."])
def test_culprit_cannot_give_it_away(text):
    c = next(new_case(s, "acids") for s in range(4000, 4100) if new_case(s, "acids").culprit == "bicarb")
    assert agents.SuspectAgent(c, "bicarb").filter(text)[1] is True


@pytest.mark.parametrize("text", ["I sell baking soda, always have.", "I never went near the Mayor's fountain.", "Sudsy sells soap flakes."])
def test_denials_pass(text):
    c = next(new_case(s, "acids") for s in range(4000, 4100) if new_case(s, "acids").culprit == "bicarb")
    assert agents.SuspectAgent(c, "bicarb").filter(text)[1] is False
