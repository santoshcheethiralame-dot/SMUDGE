"""The Author: one line from a teacher ("Class 9, pressure: P = F/A") becomes a gated, playable case.

    Designer (model)  writes a spec (kits/generic.py has the schema)
    Solver   (code)   builds the kit and plays 200 seeds: the formula parses, the numbers come out clean, every
                      seed has exactly one breakable lie, culprits spread, the filter blocks the leaks
    Critic   (model)  physics, kid-safety, nothing points at a suspect; problems from either go back to the Designer,
                      at most 3 rounds
    Casting  (code)   the borrowed cast and district (the art already exists), a free kit id
    Gate     (agent)  the release-gate detective on 2 seeds, without and with the lab; with-lab must name the culprit

Every step is a trace event (kind "author"), so the game draws the run with the Observatory's pills.
"""
import json
import random
import re
import threading
import uuid
from collections import Counter
from pathlib import Path

import kits
import llm
from agents import Detective, SuspectAgent
from kits.generic import GENERATED, GenericKit
from tracebus import Trace
from truth import new_case, check_constraints

ROUNDS = 3
GATE_SEEDS = (1000, 1001)
GOLDEN = Path(kits.__file__).resolve().parent / "golden"
POOL = Path(__file__).resolve().parent / "case_pool.json"
JOBS: dict[str, "Job"] = {}
_pool_lock = threading.Lock()

DESIGN = """You design one physics mystery for a detective game played by 14-16-year-olds, inside a living textbook.
Every case has the same shape: three suspects each SWEAR one value of the law's output for their own thing ("My crate
presses on the floor at 450 Pa"). The lab measures each suspect's inputs; the player works out each output with the
formula, and the culprit's sworn value is the one that doesn't match. Nobody is hurt: something is broken, squashed,
scraped or ruined, and the lie is about the number.

Reply with ONE JSON object shaped exactly like this example (same keys, same kinds of values):
{example}

Rules:
- formula: the output symbol, "=", then arithmetic on the input symbols and consts only (+ - * / ** and brackets,
  write every multiplication with *). out.sym is the left side.
- ins: 1 to 3 inputs, each with 3 to 5 realistic values chosen so EVERY combination gives an output with at most
  2 decimal places. consts (optional) holds fixed constants such as {{"g": 10}}.
- oath: under 70 characters, with {{value}} and {{unit}} in it. Every other line under 130 characters.
- arrive: 3 lines, inspect: 2 lines. Never use a suspect's name anywhere, never hint who did it.
- deed: second person, what the culprit secretly did. confession: first person, the culprit owning up.
- borrow: the district whose cast fits the story best, one of:
{casts}
- id: "gen_" plus the law in lowercase letters, title: "The ..." (2-4 words), chapter: "Chapter N: Law"."""

CRITIC = """You review a physics mystery written for 14-16-year-old students. Check:
1. The physics: the formula, the units and the values are correct and realistic.
2. It is kid-safe: nobody is hurt, nothing scary for a classroom.
3. The story makes sense: suspects swear the output, the lab measures the inputs, and the culprit lied about the number.
4. No line names or hints at a particular suspect.
5. It teaches what the teacher asked for.
Reply as JSON: {"ok": true|false, "issues": [up to 3 short, concrete fixes, empty when ok]}."""


class Job:
    def __init__(self, prompt: str):
        self.id = uuid.uuid4().hex[:8]
        self.prompt = prompt[:200]
        self.trace = Trace()
        self.status, self.spec, self.error = "running", None, None

    def emit(self, agent, step, verdict="ok", meta=None, **data):
        self.trace.emit(agent, "author", step, verdict, meta, **data)

    def view(self, since=0):
        return {"status": self.status, "next": len(self.trace.events), "events": self.trace.since(since),
                "spec": self.spec if self.status == "done" else None, "error": self.error}


def casts() -> dict[str, kits.Kit]:
    return {k.id: k for k in kits.REGISTRY.values() if not isinstance(k, GenericKit)}


def golden_for(prompt: str) -> dict:
    """The offline answer when no model can design: the golden spec whose law the teacher named, else pressure."""
    specs = [json.loads(p.read_text(encoding="utf8")) for p in sorted(GOLDEN.glob("*.json"))]
    words = prompt.lower()
    return next((s for s in specs if s["law"].lower() in words or s["formula"].replace(" ", "").lower() in words.replace(" ", "")),
                next(s for s in specs if s["id"] == "gen_pressure"))


# --- the Designer ---------------------------------------------------------------
def design(job: Job, feedback: list[str], last: dict | None, rnd: int, chat=llm.chat_json):
    example = (GOLDEN / "pressure.json").read_text(encoding="utf8")
    roster = "\n".join(f"  {k.id}: {k.place} - " + ", ".join(f"{s['name']} the {s['role']}" for s in k.suspects.values())
                       for k in casts().values())
    user = f"The teacher asked for: {job.prompt}"
    if feedback:
        user += "\n\nYour last design had these problems. Fix every one:\n- " + "\n- ".join(feedback)
        user += "\n\nYour last design:\n" + json.dumps(last)
    meta = {}
    spec = chat([{"role": "system", "content": DESIGN.format(example=example, casts=roster)},
                 {"role": "user", "content": user}],
                tier="smart", temperature=0.7, max_tokens=1400, seed_key=f"author:{job.prompt}:{rnd}", meta=meta)
    if not isinstance(spec, dict):
        spec = golden_for(job.prompt)
        job.emit("designer", "design", "fallback", meta, round=rnd, title=spec["title"], why="no model answered: golden spec")
        return spec
    job.emit("designer", "design", "ok", meta, round=rnd, title=spec.get("title"), formula=spec.get("formula"), spec=spec)
    return spec


# --- the Solver: plain code -----------------------------------------------------
REQUIRED = {"id": str, "title": str, "chapter": str, "law": str, "formula": str, "out": dict, "ins": list, "thing": str,
            "item": str, "crime": str, "deed": str, "oath": str, "measure": str, "hint": str, "arrive": list,
            "inspect": list, "confession": str, "borrow": str}


def solve(spec: dict, seeds=200) -> list[str]:
    """Everything wrong with a spec that code can prove. Empty means it plays."""
    bad = [f"'{k}' is missing or not a {t.__name__}" for k, t in REQUIRED.items() if not isinstance(spec.get(k), t)]
    if bad:
        return bad
    if spec["borrow"] not in casts():
        return [f"borrow must be one of {', '.join(casts())}"]
    if not all(isinstance(i, dict) and isinstance(i.get("values"), list) and len(i["values"]) >= 3 for i in spec["ins"]):
        return ["every input needs a sym, name, unit and at least 3 values"]
    if "{value}" not in spec["oath"]:
        return ["the oath must contain {value}"]
    if len(spec["arrive"]) != 3 or len(spec["inspect"]) != 2:
        return ["arrive needs exactly 3 lines and inspect exactly 2"]
    try:
        kit = GenericKit(spec, casts()[spec["borrow"]])
        outs = kit.outputs()
    except (ValueError, KeyError, TypeError, ZeroDivisionError) as e:
        return [f"the formula doesn't work: {e}"]
    from itertools import product
    syms = [i["sym"] for i in kit.ins]
    messy = [kit.f({**kit.consts, **dict(zip(syms, c))}) for c in product(*(i["values"] for i in kit.ins))]
    messy = [x for x in messy if abs(x - round(x, 2)) > 1e-9]
    if messy:
        bad.append(f"answers come out messy (e.g. {messy[0]:.4g}); change the values so every answer has at most 2 decimals")
    if len(outs) < 3 or any(x <= 0 for x in outs):
        bad.append("the values must give at least 3 different positive answers")
    if any(kit.lie_for(random.Random(0), x) is None for x in outs):
        bad.append("some answers have no clearly different value to lie with; spread the values out more")
    if any(len(kit._oath(x)) > 90 for x in outs):
        bad.append("the oath is too long for the testimony panel")
    if bad:
        return bad
    before = kits.REGISTRY.get(kit.id)
    kits.REGISTRY[kit.id] = kit         # new_case finds kits by id; put back whatever was there afterwards
    try:
        culprits = Counter()
        for seed in range(seeds):
            c = new_case(seed, kit.id)
            culprits[c.culprit] += 1
            if not check_constraints(c):
                return [f"seed {seed} doesn't have exactly one breakable lie"]
        if min(culprits.values(), default=0) < seeds * 0.2:
            bad.append("culprits don't spread evenly across the suspects")
        c = new_case(1000, kit.id)
        agent = SuspectAgent(c, c.culprit)
        slipped = [line for line in kit.leak_examples(c) if not agent.filter(line)[1]]
        if slipped:
            bad.append(f"the filter lets a confession through: {slipped[0]}")
    finally:
        if before:
            kits.REGISTRY[kit.id] = before
        else:
            kits.REGISTRY.pop(kit.id, None)
    return bad


# --- the Critic -----------------------------------------------------------------
def critique(job: Job, spec: dict, rnd: int, chat=llm.chat_json) -> list[str]:
    meta = {}
    out = chat([{"role": "system", "content": CRITIC},
                {"role": "user", "content": f"The teacher asked for: {job.prompt}\n\nThe case:\n{json.dumps(spec)}"}],
               tier="fast", temperature=0.2, max_tokens=300, seed_key=f"critic:{job.prompt}:{rnd}", meta=meta)
    if not isinstance(out, dict):
        job.emit("critic", "critique", "skip", meta, round=rnd, why="no model answered")
        return []
    issues = [str(x) for x in out.get("issues") or []][:3] if not out.get("ok") else []
    job.emit("critic", "critique", "leak" if issues else "pass", meta, round=rnd, issues=issues)
    return issues


# --- Casting and the Gate -------------------------------------------------------
def cast(job: Job, spec: dict) -> GenericKit:
    slug = re.sub(r"[^a-z0-9]+", "_", spec["id"].lower()).strip("_")
    spec["id"] = slug if slug.startswith("gen_") else f"gen_{slug}"
    taken = set(kits.REGISTRY)          # never overwrite a built or earlier authored case
    while spec["id"] in taken:
        spec["id"] += "_2"
    spec.setdefault("num", 50)
    kit = kits.add_generated(spec)
    job.emit("casting", "cast", "ok", borrow=spec["borrow"], place=kit.place, kit=kit.id,
             suspects=[s["name"] for s in kit.suspects.values()])
    return kit


def gate(job: Job, kit: GenericKit, detective=None) -> bool:
    det = detective or Detective()
    det.think = False                 # the gate measures the case, not the suspects' thinking: one call per reply
    rows = []
    for seed in GATE_SEEDS:
        c = new_case(seed, kit.id)
        for with_lab in (False, True):
            guess = det.solve(c, with_lab=with_lab)
            right = guess == c.culprit
            job.emit("gate", "gate", "pass" if right or not with_lab else "block", seed=seed,
                     lab=with_lab, guess=guess, culprit=c.culprit)
            rows.append((seed, c.culprit, with_lab, guess))
    by_seed = {s: {lab: g for s2, _, lab, g in rows if s2 == s} for s in GATE_SEEDS}
    passed = [dict(kit=kit.id, seed=s, culprit=c, no_lab=by_seed[s][False], with_lab=by_seed[s][True],
                   passed=by_seed[s][True] == c) for s, c in {(r[0], r[1]) for r in rows}]
    with _pool_lock:
        pool = [r for r in (json.loads(POOL.read_text()) if POOL.exists() else []) if r.get("kit") != kit.id]
        POOL.write_text(json.dumps(pool + sorted(passed, key=lambda r: r["seed"]), indent=1))
    return all(r["passed"] for r in passed)


def run(job: Job, chat=llm.chat_json, detective=None):
    feedback, spec = [], None
    try:
        for rnd in range(1, ROUNDS + 1):
            spec = design(job, feedback, spec, rnd, chat)
            feedback = solve(spec)
            job.emit("solver", "solve", "block" if feedback else "pass", round=rnd, seeds=200, problems=feedback)
            if not feedback:
                feedback = critique(job, spec, rnd, chat)
            if not feedback:
                break
        else:
            raise RuntimeError("no playable design after 3 rounds: " + "; ".join(feedback))
        kit = cast(job, spec)
        if not gate(job, kit, detective):
            kits.REGISTRY.pop(kit.id, None)
            raise RuntimeError("the detective couldn't solve it even with the lab")
        GENERATED.mkdir(exist_ok=True)
        (GENERATED / f"{kit.id}.json").write_text(json.dumps(spec, indent=1, ensure_ascii=False), encoding="utf8")
        job.spec, job.status = spec, "done"
    except Exception as e:          # the panel shows why; the server stays up
        job.error, job.status = str(e), "failed"


def start(prompt: str) -> Job:
    job = JOBS[(j := Job(prompt)).id] = j
    threading.Thread(target=run, args=(job,), daemon=True).start()
    return job
