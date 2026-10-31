"""Cases written as data: the formula parser and the GenericKit's own rules."""
import json
from pathlib import Path

import pytest

import kits
from kits.generic import parse_formula, GenericKit
from truth import new_case, check_lab

GOLDEN = [json.loads(p.read_text(encoding="utf8")) for p in sorted((Path(kits.__file__).parent / "golden").glob("*.json"))]


@pytest.mark.parametrize("formula,env,want", [("P = F / A", {"F": 900, "A": 2}, 450),
                                              ("h = 0.5 * g * t**2", {"g": 9.8, "t": 1.5}, 11.025),
                                              ("h = ½g*t²", {"g": 10, "t": 2}, 20)])
def test_formulas_compute(formula, env, want):
    assert parse_formula(formula, set(env))[1](env) == pytest.approx(want)


@pytest.mark.parametrize("formula", ["P = __import__('os').system('x')", "P = F.real", "P = [F][0]", "P = Q / A", "P F / A", "P = F /"])
def test_formulas_refuse_anything_but_arithmetic(formula):
    with pytest.raises(ValueError):
        parse_formula(formula, {"F", "A"})


def test_formula_must_give_the_sworn_quantity():
    spec = {**GOLDEN[0], "formula": "F = P * A", "ins": [{"sym": "P", "name": "p", "unit": "Pa", "values": [1]},
                                                         {"sym": "A", "name": "a", "unit": "m²", "values": [1]}]}
    with pytest.raises(ValueError):
        GenericKit(spec, kits.REGISTRY[spec["borrow"]])


@pytest.mark.parametrize("spec", GOLDEN, ids=lambda s: s["id"])
def test_culprits_spread_and_lies_are_far_from_the_truth(spec):
    from collections import Counter
    kit = kits.REGISTRY[spec["id"]]
    seen = Counter()
    for seed in range(200):
        c = new_case(seed, kit.id)
        seen[c.culprit] += 1
        true, claim = c.hidden["truth"][c.culprit], c.hidden["claims"][c.culprit]
        assert abs(true - claim) > 0.2 * true
    assert min(seen.values()) > 40


@pytest.mark.parametrize("spec", GOLDEN, ids=lambda s: s["id"])
def test_wrong_working_names_the_step(spec):
    kit = kits.REGISTRY[spec["id"]]
    c = new_case(7, kit.id)
    w = kit.solution(c)
    sid = next(iter(kit.suspects))
    sym = kit.ins[0]["sym"]
    assert check_lab(c, {**w, f"{sym}_{sid}": w[f"{sym}_{sid}"] + 50})["step"] == "read"
    assert check_lab(c, {**w, f"out_{sid}": w[f"out_{sid}"] * 3 + 1})["step"] == "formula"
    ok = check_lab(c, w)
    assert ok["ok"] and ok["evidence"] == f"out:{c.culprit}" and kit.suspects[c.culprit]["name"] in ok["card"]["title"]
