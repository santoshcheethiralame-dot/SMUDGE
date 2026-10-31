"""Case 6 specifics. The shared kit contract in test_kits.py also runs on this kit."""
from collections import Counter

import pytest

import agents
import kits
import llm
from truth import new_case, check_lab

K = kits.get("ohm")


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "PROVIDERS", [])
    monkeypatch.setattr(llm, "CACHE", tmp_path)


def test_readings_land_on_the_dial_marks():
    for seed in range(4000, 4200):
        p = new_case(seed, "ohm").public_facts
        assert p["volts"] in (5, 10) and p["milliamps"] % 50 == 0 and 50 <= p["milliamps"] <= 1000


def test_culprits_are_spread_evenly():
    counts = Counter(new_case(s, "ohm").culprit for s in range(5000, 5600))
    assert min(counts.values()) > 150


@pytest.mark.parametrize("field,mistake,step", [
    ("i", lambda w: w["ma"], "milliamps"),
    ("r", lambda w: w["v"] / w["ma"], "milliamps"),
    ("r", lambda w: w["i"] / w["v"], "flipped"),
    ("r", lambda w: w["v"] * w["i"], "multiplied"),
])
def test_each_classic_mistake_gets_its_own_hint(field, mistake, step):
    c = new_case(4001, "ohm")
    w = K.solution(c)
    w[field] = mistake(w)
    out = check_lab(c, w)
    assert out["step"] == step and out["bad"] == [field]


def test_suspects_may_name_their_own_stock_but_not_the_swapped_value():
    c = next(new_case(s, "ohm") for s in range(4000, 4100) if new_case(s, "ohm").culprit == "glim")
    a = agents.SuspectAgent(c, "volta")
    assert a.filter("My shop stocks 10 Ω resistors, sparky.")[1] is False
    assert a.filter("Ohmar sells 20 Ω ones, mind.")[1] is False           # gossip: Volta knows Ohmar's stock
    assert a.filter("Sounds like a 50 Ω part went in.")[1] is True        # but not Glim's, so that's a guess at the answer
    assert a.filter("I measured 5 volts across it.")[1] is True


@pytest.mark.parametrize("text", ["I swapped the resistor on the board.", "One of mine has gone missing.", "I was right by the board."])
def test_culprit_cannot_give_it_away(text):
    c = next(new_case(s, "ohm") for s in range(4000, 4100) if new_case(s, "ohm").culprit == "ohmar")
    assert agents.SuspectAgent(c, "ohmar").filter(text)[1] is True


@pytest.mark.parametrize("text", ["My shop stocks 20 Ω resistors. All still on the shelf.", "I never touched the Grand Light Board.",
                                  "None of my resistors are missing."])
def test_denials_pass(text):
    c = next(new_case(s, "ohm") for s in range(4000, 4100) if new_case(s, "ohm").culprit == "ohmar")
    assert agents.SuspectAgent(c, "ohmar").filter(text)[1] is False
