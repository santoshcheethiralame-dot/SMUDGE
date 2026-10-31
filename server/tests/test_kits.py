"""No model calls anywhere in here: the truth engine, the lab check, the present check
and the output filter are all plain code, so they are tested as plain code.

The contract tests run against every kit in the registry, so a new case is checked
the moment it is registered.  python -m pytest tests  (from server/)
"""
import re

import pytest

import agents
import kits
import llm
from truth import new_case, check_constraints, check_lab, present

SEEDS = range(1000, 1060)
KITS = list(kits.REGISTRY)


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    """Any accidental model call fails loudly instead of spending quota."""
    monkeypatch.setattr(llm, "PROVIDERS", [])
    monkeypatch.setattr(llm, "CACHE", tmp_path)


# --- contract: every kit ----------------------------------------------------

@pytest.mark.parametrize("kit", KITS)
def test_cases_replay_exactly_from_seed(kit):
    a, b = new_case(1234, kit), new_case(1234, kit)
    assert (a.culprit, a.hidden, a.public_facts, a.statements) == (b.culprit, b.hidden, b.public_facts, b.statements)


@pytest.mark.parametrize("kit", KITS)
def test_every_seed_has_exactly_one_breakable_lie(kit):
    for seed in SEEDS:
        c = new_case(seed, kit)
        assert check_constraints(c), seed
        lies = [x for v in c.statements.values() for x in v if x.get("contradicts")]
        assert len(lies) == 1 and lies[0]["id"].startswith(c.culprit + "-"), seed


@pytest.mark.parametrize("kit", KITS)
def test_statements_fit_on_one_line_of_the_testimony_panel(kit):
    for seed in SEEDS:
        for lines in new_case(seed, kit).statements.values():
            assert all(len(x["text"]) <= 90 for x in lines), [x["text"] for x in lines if len(x["text"]) > 90]


@pytest.mark.parametrize("kit", KITS)
def test_every_suspect_is_the_culprit_somewhere(kit):
    assert {new_case(s, kit).culprit for s in SEEDS} == set(kits.get(kit).suspects)


@pytest.mark.parametrize("kit", KITS)
def test_public_view_hides_the_answer(kit):
    for seed in SEEDS:
        c = new_case(seed, kit)
        pub = c.public()
        assert "culprit" not in pub and "hidden" not in pub
        assert not set(c.hidden) & set(pub)
        assert all(set(x) == {"id", "text"} for v in pub["statements"].values() for x in v)


@pytest.mark.parametrize("kit", KITS)
def test_correct_working_yields_the_evidence_that_breaks_the_lie(kit):
    k = kits.get(kit)
    for seed in SEEDS:
        c = new_case(seed, kit)
        out = check_lab(c, k.solution(c))
        assert out["ok"] and out["step"] is None, (seed, out)
        lie = next(x for v in c.statements.values() for x in v if x.get("contradicts"))
        assert out["evidence"] == lie["contradicts"]
        assert set(out["card"]) >= {"title", "line", "badge", "say"} and all(out["card"].values())
        assert present(c, lie["id"], out["evidence"]) == {"hit": True, "culprit": c.culprit, "close": False}


@pytest.mark.parametrize("kit", KITS)
def test_evidence_against_an_innocent_misses(kit):
    k = kits.get(kit)
    for seed in SEEDS:
        c = new_case(seed, kit)
        ev = check_lab(c, k.solution(c))["evidence"]
        for sid, lines in c.statements.items():
            if sid != c.culprit:
                assert not any(present(c, x["id"], ev)["hit"] for x in lines)
                assert not any(present(c, x["id"], ev)["close"] for x in lines)


@pytest.mark.parametrize("kit", KITS)
def test_the_culprits_true_lines_miss_but_count_as_close(kit):
    k = kits.get(kit)
    for seed in SEEDS:
        c = new_case(seed, kit)
        ev = check_lab(c, k.solution(c))["evidence"]
        for x in c.statements[c.culprit]:
            if not x.get("contradicts"):
                assert present(c, x["id"], ev) == {"hit": False, "culprit": None, "close": True}


@pytest.mark.parametrize("kit", KITS)
def test_every_wrong_step_has_a_safe_hint(kit):
    k = kits.get(kit)
    c = new_case(1000, kit)
    good = k.solution(c)
    for field in good:
        out = check_lab(c, {**good, field: good[field] + 7})
        assert not out["ok"] and out["step"] in k.hints, (field, out)
    for hint in k.hints.values():
        assert not any(re.search(rf"\b{w}\b", hint, re.I) for w in k.answer_words), hint


@pytest.mark.parametrize("kit", KITS)
def test_offline_fallback_answers_stay_in_character(kit):
    k = kits.get(kit)
    c = new_case(1000, kit)
    for sid in k.suspects:
        a = agents.SuspectAgent(c, sid)
        for q in k.detective_questions + ["Nice weather?"]:
            r = a.ask(q)
            assert r["source"] == "script" and r["answer"]


@pytest.mark.parametrize("kit", KITS)
def test_knowledge_slices_hold_the_secret_only_for_the_culprit(kit):
    k = kits.get(kit)
    for seed in list(SEEDS)[:12]:
        c = new_case(seed, kit)
        for sid in k.suspects:
            facts, secret = k.knowledge(c, sid)
            assert facts and bool(secret) == (sid == c.culprit)


# --- the output filter ----------------------------------------------------------

def _agent(guilty: bool):
    c = new_case(1003, "density")          # culprit: cyl (lead)
    return agents.SuspectAgent(c, "cyl" if guilty else "karat")


@pytest.mark.parametrize("text", [
    "I did swap the crown.", "I've only ever swapped the crown's look.", "The fake I made was lead.",
    "Fine, it was me.", "What if I had cast the fake? Silly.", "The crown is 158 g, I weighed it.",
])
def test_filter_blocks_confessions_and_numbers(text):
    out, filtered = _agent(guilty=True).filter(text)
    assert filtered and "rather not guess" in out


@pytest.mark.parametrize("text", [
    "I never swapped it, mate.", "I've never swapped or touched a crown.", "I didn't swap, make, cast or touch any fake.",
    "Aye, I keep lead in the weight box. None of it is missing.", "I made the rings myself.",
])
def test_filter_lets_denials_through(text):
    assert _agent(guilty=True).filter(text) == (text, False)


def test_culprit_cannot_admit_their_metal_is_missing():
    assert _agent(guilty=True).filter("Some of my lead has gone missing lately.")[1]


def test_innocents_cannot_accuse_as_fact():
    assert _agent(guilty=False).filter("Cyl is the thief, plain as day.")[1]


@pytest.mark.parametrize("guilty", [True, False])
def test_nobody_points_at_another_suspect(guilty):
    # only the culprit would want to deflect, so a guess at someone else is blocked for everyone
    a = _agent(guilty=guilty)
    other = next(s["name"] for sid, s in a.kit.suspects.items() if sid != a.sid)
    assert a.filter(f"Maybe {other} got a little too greedy.")[1]
    assert a.filter(f"I hear {other} sells plenty, not that I'm pointing any fingers!")[1]
    assert a.filter(f"{other} sells things too, everyone knows that.") == (f"{other} sells things too, everyone knows that.", False)


def test_stage_directions_are_stripped():
    assert _agent(guilty=False).filter("*polishes monocle* Exquisite question.") == ("Exquisite question.", False)


def test_an_reads_numbers_aloud():
    from kits.base import an
    assert [an(n) for n in (8, 8.7, 11, 18.0, 80, 800, 11000)] == ["an"] * 7
    assert [an(n) for n in (1, 10.4, 110, 180, 400, 1200)] == ["a"] * 6


def test_coach_hint_starts_with_one_asterisk(monkeypatch):
    import agents
    monkeypatch.setattr(agents, "chat", lambda *a, **kw: "* Detective, when did your clock start?")
    assert agents.Footnote().hint(kits.get("motion"), "time") == "*Detective, when did your clock start?"


def test_thousands_commas_are_read_as_one_number():
    # an innocent saying their own sworn 1020 m as "1,020 m" is not quoting someone else's 20 m
    for seed in range(1000, 1040):
        c = new_case(seed, "sound")
        sid = next(s for s in c.statements if s != c.culprit)
        claim = c.hidden["claims"][sid]
        if claim >= 1000:
            import agents
            a = agents.SuspectAgent(c, sid)
            text = f"I filmed it from home, {claim:,} m from the tower."
            assert a.filter(text) == (text, False)
            return
    pytest.skip("no seed with a four-digit claim")
