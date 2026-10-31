"""Case 5 specifics. The shared kit contract in test_kits.py also runs on this kit."""
from collections import Counter

import pytest

import agents
import kits
import llm
from kits.refraction import SIN, material_for
from truth import new_case, check_lab

K = kits.get("refraction")


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "PROVIDERS", [])
    monkeypatch.setattr(llm, "CACHE", tmp_path)


def test_the_table_tells_every_material_apart():
    found = {material_for(SIN[60] / SIN[r]) for r in (41, 35, 29, 21)}
    assert found == {"ice", "glass", "sapphire", "diamond"}


def test_the_fake_is_cut_from_the_culprits_material():
    for seed in range(4000, 4200):
        c = new_case(seed, "refraction")
        m = material_for(SIN[60] / SIN[c.public_facts["r"]])
        assert K.suspects[c.culprit]["material"] == m != "diamond"


def test_culprits_are_spread_evenly():
    counts = Counter(new_case(s, "refraction").culprit for s in range(5000, 5600))
    assert min(counts.values()) > 150


@pytest.mark.parametrize("mistake,step", [(lambda w: w["i"] / w["r"], "angles"), (lambda w: w["sin_r"] / w["sin_i"], "flipped"),
                                          (lambda w: w["sin_i"] * w["sin_r"], "index")])
def test_each_classic_mistake_gets_its_own_hint(mistake, step):
    c = new_case(4001, "refraction")
    w = K.solution(c)
    w["n"] = mistake(w)
    out = check_lab(c, w)
    assert out["step"] == step and out["bad"] == ["n"]


def test_angles_in_place_of_sines_are_caught():
    c = new_case(4001, "refraction")
    w = {**K.solution(c), "sin_i": 60}
    assert check_lab(c, w)["step"] == "sine"


@pytest.mark.parametrize("text", ["I cut the fake lens from a spare block.", "A block of my ice has gone missing lately.",
                                  "The beam bends to 35 degrees."])
def test_culprit_cannot_give_it_away(text):
    c = next(new_case(s, "refraction") for s in range(4000, 4100) if new_case(s, "refraction").culprit == "frost")
    assert agents.SuspectAgent(c, "frost").filter(text)[1] is True


@pytest.mark.parametrize("text", ["Yes, I work ice. None of it is missing.", "I never touched the lighthouse lens.", "Pane works glass, mind."])
def test_denials_pass(text):
    c = next(new_case(s, "refraction") for s in range(4000, 4100) if new_case(s, "refraction").culprit == "frost")
    assert agents.SuspectAgent(c, "frost").filter(text)[1] is False
