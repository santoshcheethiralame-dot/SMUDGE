"""The suspects' loop: plan, draft, critique, redraft once, firewall. Offline: a fake router answers."""
import pytest

import agents
import llm
from stress import Stress
from tracebus import Trace, problems
from truth import new_case

LEAK = "Fine, I swapped the resistor."
SAFE = "My shelves are counted twice a day."


class Fake:
    """Stands in for agents.chat / agents.chat_json. Plans and critiques are told apart by their system prompt."""

    def __init__(self, plan=None, critique=None, drafts=(SAFE,), dead_fast=False):
        self.plan = plan if plan is not None else {"intent": "deflect", "risk": "high", "must_avoid": ["the swap"], "strategy": "stall"}
        self.critique = critique if critique is not None else {"leaks": False, "contradicts_ledger": False, "fix": ""}
        self.drafts, self.dead_fast, self.calls = list(drafts), dead_fast, []

    def _meta(self, meta, tier):
        if meta is not None:
            meta.update(provider="groq", model=f"fake-{tier}", cached=False, ms=7, tokens=11, tier=tier)

    def chat(self, messages, tier="fast", meta=None, **kw):
        self.calls.append(("draft", messages[0]["content"]))
        self._meta(meta, tier)
        return self.drafts.pop(0) if len(self.drafts) > 1 else self.drafts[0]

    def chat_json(self, messages, tier="fast", meta=None, **kw):
        kind = "critique" if "You check a reply" in messages[0]["content"] else "plan"
        self.calls.append((kind, messages[0]["content"]))
        if self.dead_fast:
            if meta is not None:
                meta.update(provider=None, model=None, cached=False, ms=3, tokens=0, tier=tier)
            return None
        self._meta(meta, tier)
        return dict(self.critique if kind == "critique" else self.plan)


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    monkeypatch.setattr(llm, "PROVIDERS", [])
    monkeypatch.setattr(llm, "CACHE", tmp_path)
    monkeypatch.delenv("SMUDGE_THINK", raising=False)


def _agent(monkeypatch, fake, sid="ohmar"):
    monkeypatch.setattr(agents, "chat", fake.chat)
    monkeypatch.setattr(agents, "chat_json", fake.chat_json)
    case = new_case(1000, "ohm")
    trace, stress = Trace(), Stress(["volta", "ohmar", "glim"])
    return agents.SuspectAgent(case, sid, trace=trace, stress=stress), trace, stress


def steps(trace):
    return [(e["step"], e["verdict"]) for e in trace.events if e["kind"] == "suspect"]


def test_full_loop_emits_every_step_in_order(monkeypatch):
    a, trace, _ = _agent(monkeypatch, Fake())
    assert a.ask("Where were you?")["answer"] == SAFE
    assert steps(trace) == [("plan", "ok"), ("draft", "ok"), ("critique", "ok"), ("firewall", "pass"), ("reply", "ok")]
    assert all(problems(e) == [] for e in trace.events)
    assert trace.events[0]["data"]["risk"] == "high" and trace.events[0]["data"]["stress"] == 0
    assert trace.events[0]["tokens"] == 11 and trace.events[0]["agent"] == "ohmar"


def test_a_leak_flagged_by_the_critique_gets_exactly_one_redraft(monkeypatch):
    fake = Fake(drafts=(LEAK, SAFE, "never used"), critique={"leaks": True, "contradicts_ledger": False, "fix": "Do not admit it."})
    a, trace, _ = _agent(monkeypatch, fake)
    assert a.ask("Admit it.")["answer"] == SAFE
    assert steps(trace) == [("plan", "ok"), ("draft", "ok"), ("critique", "leak"), ("redraft", "ok"), ("firewall", "pass"), ("reply", "ok")]
    assert "Do not admit it." in fake.calls[-1][1]
    assert [k for k, _ in fake.calls].count("critique") == 1


def test_low_risk_skips_the_critique(monkeypatch):
    a, trace, _ = _agent(monkeypatch, Fake(plan={"intent": "answer", "risk": "low", "must_avoid": [], "strategy": "chat"}))
    a.ask("Nice weather?")
    assert ("critique", "skip") in steps(trace)
    assert next(e for e in trace.events if e["step"] == "critique")["data"] == {"why": "low risk"}


def test_a_dead_fast_model_skips_plan_and_critique_but_still_replies(monkeypatch):
    a, trace, _ = _agent(monkeypatch, Fake(dead_fast=True))
    assert a.ask("Where were you?")["answer"] == SAFE
    assert steps(trace)[:3] == [("plan", "skip"), ("draft", "ok"), ("critique", "skip")]
    assert trace.events[0]["data"] == {"why": "no model"}


def test_the_firewall_still_blocks_after_the_loop(monkeypatch):
    fake = Fake(drafts=(LEAK,), critique={"leaks": False, "contradicts_ledger": False, "fix": ""})
    a, trace, _ = _agent(monkeypatch, fake)
    out = a.ask("Admit it.")
    assert "rather not guess" in out["answer"] and out["source"] == "llm+filtered"
    fw = next(e for e in trace.events if e["step"] == "firewall")
    assert fw["verdict"] == "block" and fw["data"]["rule"]


def test_think_off_makes_one_call(monkeypatch):
    monkeypatch.setenv("SMUDGE_THINK", "0")
    fake = Fake()
    a, trace, _ = _agent(monkeypatch, fake)
    a.ask("Where were you?")
    assert [k for k, _ in fake.calls] == ["draft"]
    assert steps(trace) == [("draft", "ok"), ("firewall", "pass"), ("reply", "ok")]


def test_no_model_at_all_falls_back_to_scripted_lines(monkeypatch):
    fake = Fake(dead_fast=True)
    fake.chat = lambda messages, tier="fast", meta=None, **kw: None
    a, trace, _ = _agent(monkeypatch, fake)
    out = a.ask("Where were you?")
    assert out["source"].startswith("script") and out["answer"]
    assert ("draft", "fallback") in steps(trace)


def test_stress_band_reaches_the_plan_and_the_draft(monkeypatch):
    fake = Fake()
    a, trace, stress = _agent(monkeypatch, fake)
    stress.level["ohmar"] = 6
    a.ask("Where were you?")
    plan_prompt = next(p for k, p in fake.calls if k == "plan")
    draft_prompt = next(p for k, p in fake.calls if k == "draft")
    assert "RATTLED" in plan_prompt and "short, defensive" in draft_prompt
    assert trace.events[0]["data"]["stress"] == 6


def test_calm_think_off_prompt_is_unchanged(monkeypatch):
    """The gate's cache (and old seeds) depend on the single-call prompt staying byte-for-byte the same."""
    monkeypatch.setenv("SMUDGE_THINK", "0")
    fake = Fake()
    a, _, _ = _agent(monkeypatch, fake)
    expected = a.system()              # read before asking: the reply joins the ledger, which is in the prompt
    a.ask("Where were you?")
    assert fake.calls[0][1] == expected
