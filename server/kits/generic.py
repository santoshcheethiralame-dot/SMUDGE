"""A case written as data: GenericKit turns one JSON spec into a Kit. The Author agents write these specs
(author.py); every spec in kits/generated/ is loaded at start, on the cast and district of the kit it borrows.

The one shape every generated case has: each suspect swears one value of the law's output for their own thing
("My crate pressed on the floor at 1200 Pa"). The lab measures each suspect's inputs (weight, base area); the
player works the output out for each, and the culprit's sworn value is the one the numbers say is impossible.

Spec keys:
    id        "gen_<slug>", the kit id          title, chapter, law   what the case is called and teaches
    formula   "P = F / A"; + - * / ** and brackets only, parsed with ast, never eval'd
    out       {sym, name, unit}                 the quantity suspects swear
    ins       [{sym, name, unit, values}]       what the lab measures; values are the choices per suspect
    consts    {sym: number}                     optional fixed constants (g)
    thing     each suspect's measured object    item   what the crime is about
    crime     one sentence: what happened       deed   the culprit's secret, second person ("you dragged...")
    oath      sworn line with {value} and {unit}
    measure   what the lab does                 hint   Footnote's nudge when the working is wrong
    arrive    3 lines                           inspect   2 lines        confession   the culprit owns up
    borrow    the kit whose suspects and district the case uses
"""
import ast
import json
import operator
import re
from itertools import product
from pathlib import Path

from .base import Kit

GENERATED = Path(__file__).resolve().parent / "generated"
TOLERANCE = 0.2            # the culprit's sworn value is at least this far (relative) from the truth
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow}
_I = r"\bi(?:'ve| have| did| had)?(?: (?!never\b|not\b|neither\b|nor\b)\w+){0,2} "


_TOKEN = re.compile(r"\s*(\d+(?:\.\d+)?|\.\d+|[^\W\d]\w*|\*\*|[-+*/()])")


def _split_symbols(word: str, names: set[str]) -> list[str]:
    """'kq1q2' -> ['k', 'q1', 'q2'] using the known symbols (fewest pieces wins); the word itself if it can't be split."""
    best: dict[int, list[str] | None] = {0: []}
    for end in range(1, len(word) + 1):
        options = [best[i] + [word[i:end]] for i in range(end) if best.get(i) is not None and word[i:end] in names]
        best[end] = min(options, key=len) if options else None
    return best[len(word)] or [word]


def _implicit_times(rhs: str, names: set[str]) -> str:
    """Textbook shorthand to explicit arithmetic: 'kq1q2/r' -> 'k*q1*q2/r', 'ρL/A' -> 'ρ*L/A', '2(a+b)' -> '2*(a+b)'."""
    out, pos = [], 0
    while pos < len(rhs):
        m = _TOKEN.match(rhs, pos)
        if not m:
            if rhs[pos:].strip():
                raise ValueError(f"can't read the formula near {rhs[pos:].strip()[:10]!r}")
            break
        pos = m.end()
        tok = m.group(1)
        parts = _split_symbols(tok, names) if tok[0].isalpha() or tok[0] == "_" else [tok]
        for part in parts:
            opens = part[0].isalnum() or part[0] in "_.(" 
            if out and opens and (out[-1][-1].isalnum() or out[-1][-1] in "_.)"):
                out.append("*")
            out.append(part)
    return "".join(out)


def parse_formula(formula: str, names: set[str]):
    """'P = F / A' -> (output symbol, function of a dict of values). Raises ValueError on anything but arithmetic.
    Textbook shorthand works too: 'U = kq1q2/r', 'v = u + at', 'E = mc^2', 'R = ρL/A' (a run of known symbols is a product)."""
    if formula.count("=") != 1:
        raise ValueError("formula needs exactly one '='")
    lhs, rhs = (s.strip() for s in formula.split("="))
    rhs = rhs.replace("^", "**").replace("×", "*").replace("÷", "/").replace("²", "**2").replace("³", "**3").replace("½", "0.5*")
    rhs = rhs.replace("·", "*").replace("⋅", "*").replace("−", "-")
    rhs = _implicit_times(rhs, names)
    try:
        tree = ast.parse(rhs, mode="eval").body
    except SyntaxError as e:
        raise ValueError(f"can't read the formula: {e.msg}") from None

    def check(n):
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            check(n.left), check(n.right)
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            check(n.operand)
        elif isinstance(n, ast.Name):
            if n.id not in names:
                raise ValueError(f"unknown symbol {n.id!r} in the formula")
        elif not (isinstance(n, ast.Constant) and isinstance(n.value, (int, float))):
            raise ValueError(f"only arithmetic is allowed, not {type(n).__name__}")
    check(tree)

    def ev(n, env):
        if isinstance(n, ast.BinOp):
            return _OPS[type(n.op)](ev(n.left, env), ev(n.right, env))
        if isinstance(n, ast.UnaryOp):
            return -ev(n.operand, env)
        return env[n.id] if isinstance(n, ast.Name) else n.value
    return lhs, lambda env: ev(tree, env)


def fmt(x: float) -> str:
    """12.0 -> '12', 0.50 -> '0.5'."""
    return f"{round(x, 2):g}"


class GenericKit(Kit):
    def __init__(self, spec=None, cast: Kit | None = None):
        if spec is None:           # kit discovery instantiates every Kit class; a bare GenericKit is not a case
            return
        self.spec, s = spec, spec
        self.id, self.num, self.title = s["id"], s.get("num", 50), s["title"]
        self.place, self.item, self.answer_noun = cast.place, s["item"], s["out"]["name"]
        self.suspects = {sid: dict(v) for sid, v in cast.suspects.items()}
        self.answer_words = tuple(self.suspects)
        ids = list(self.suspects)
        self.gossip = {sid: ids[(i + 1) % len(ids)] for i, sid in enumerate(ids)}
        words = [re.escape(i["unit"]) + "(?![/²³])" for i in s["ins"] if re.fullmatch(r"\w+", i["unit"])]
        self.units = "|".join(words) or "(?!x)x"
        self.out, self.ins, self.consts = s["out"], s["ins"], s.get("consts", {})
        lhs, self.f = parse_formula(s["formula"], {i["sym"] for i in self.ins} | set(self.consts))
        if lhs != self.out["sym"]:
            raise ValueError(f"the formula gives {lhs!r} but the case swears {self.out['sym']!r}")
        self.hints = {"read": "*Copy each measurement straight from the lab sheet.", "formula": s["hint"],
                      "present": f"*Whose sworn {self.out['name']} doesn't match the numbers?"}
        self.detective_questions = [f"What is your {s['thing']}'s {self.out['name']}?", "What happened last night?",
                                    "Who do you think is behind it?"]
        u = re.escape(self.out["unit"])
        self._said = re.compile(rf"(\d+(?:\.\d+)?)\s*(?:{u})(?![A-Za-z/²³])", re.I)
        self._measures = [re.compile(rf"\d+(?:\.\d+)?\s*(?:{re.escape(i['unit'])})(?![A-Za-z/²³])", re.I) for i in self.ins]
        self._confess = re.compile(_I + r"(did it|broke|cracked|smashed|knocked|ruined|wrecked|damaged|took|stole|lied)\b", re.I)

    # --- the numbers -----------------------------------------------------------
    def value(self, inputs: dict) -> float:
        return round(self.f({**self.consts, **inputs}), 2)

    def outputs(self) -> list[float]:
        """Every output the lab grid can produce."""
        syms = [i["sym"] for i in self.ins]
        return sorted({self.value(dict(zip(syms, combo))) for combo in product(*(i["values"] for i in self.ins))})

    def lie_for(self, rng, true: float):
        far = [v for v in self.outputs() if abs(v - true) > TOLERANCE * max(abs(true), 1e-9)]
        return rng.choice(far) if far else None

    # --- the truth -------------------------------------------------------------
    def generate(self, rng):
        culprit = rng.choice(list(self.suspects))
        inputs, truth, claims = {}, {}, {}
        for sid in self.suspects:
            inputs[sid] = {i["sym"]: rng.choice(i["values"]) for i in self.ins}
            truth[sid] = self.value(inputs[sid])
            claims[sid] = truth[sid] if sid != culprit else self.lie_for(rng, truth[sid])
        return culprit, {"claims": claims, "truth": truth}, {"ins": inputs, "consts": self.consts}

    def _oath(self, value):
        return self.spec["oath"].format(value=fmt(value), unit=self.out["unit"])

    def testimony(self, sid, culprit, hidden):
        oath = self._oath(hidden["claims"][sid])
        return [
            {"text": oath, "true": True} if sid != culprit else
            {"text": oath, "true": False, "contradicts": f"out:{sid}"},
            {"text": f"Measure my {self.spec['thing']} yourself. I've nothing to hide.", "true": True},
            {"text": f"The {self.item} was fine before last night.", "true": True},
            {"text": "Whoever did it, it wasn't me.", "true": sid != culprit},
        ]

    def clues(self, hidden):
        return [dict(id="crime", name=self.item.capitalize(), text=self.spec["crime"]),
                dict(id="law", name=self.spec["law"], text=self.spec["formula"])]

    def _off(self, case):
        return [sid for sid in self.suspects if case.hidden["claims"][sid] is None
                or abs(case.hidden["truth"][sid] - case.hidden["claims"][sid]) > 0.01 * max(abs(case.hidden["truth"][sid]), 1)]

    def check_constraints(self, case):
        lies = [x for v in case.statements.values() for x in v if x.get("contradicts")]
        return (self._off(case) == [case.culprit] and case.hidden["claims"][case.culprit] is not None
                and len(lies) == 1 and lies[0]["id"].startswith(case.culprit + "-"))

    # --- the lab ---------------------------------------------------------------
    def check_lab(self, case, working):
        p, h = case.public_facts, case.hidden
        bad, kinds = [], set()
        for sid in self.suspects:
            for sym, v in p["ins"][sid].items():
                if abs(float(working.get(f"{sym}_{sid}", v)) - v) > 0.01:     # copied straight off the lab sheet
                    kinds.add("read"); bad.append(f"{sym}_{sid}")
            right = h["truth"][sid]
            if abs(float(working.get(f"out_{sid}", "nan")) - right) > max(0.02, 0.001 * abs(right)):
                kinds.add("formula"); bad.append(f"out_{sid}")
        step = next((k for k in ("read", "formula") if k in kinds), None)
        out = {"ok": step is None, "step": step, "bad": bad}
        if out["ok"]:
            off = self._off(case)
            out["evidence"] = f"out:{off[0]}" if off else None
            if off:
                sid = off[0]
                name, thing, unit = self.suspects[sid]["name"], self.spec["thing"], self.out["unit"]
                v, claim = fmt(h["truth"][sid]), fmt(h["claims"][sid])
                measured = ", ".join(f"{i['sym']} = {fmt(p['ins'][sid][i['sym']])} {i['unit']}" for i in self.ins)
                out["card"] = {"title": f"{name}'s {thing}: {v} {unit}", "line": f"Measured {measured}. {name} swore {claim} {unit}.",
                               "badge": f"EVIDENCE\n{name}'s {thing}\n{self.out['sym']} = {v} {unit}",
                               "say": f"Hold it. Your {thing} works out at {v} {unit}, not {claim}."}
        return out

    def solution(self, case):
        w = {}
        for sid, vals in case.public_facts["ins"].items():
            w.update({f"{sym}_{sid}": v for sym, v in vals.items()})
            w[f"out_{sid}"] = case.hidden["truth"][sid]
        return w

    def lab_report(self, case):
        p = case.public_facts
        consts = "".join(f", {k} = {fmt(v)}" for k, v in self.consts.items())
        rows = "; ".join(f"{self.suspects[sid]['name']}'s {self.spec['thing']}: " +
                         ", ".join(f"{i['name']} {i['sym']} = {fmt(p['ins'][sid][i['sym']])} {i['unit']}" for i in self.ins)
                         for sid in self.suspects)
        return (f"LAB RESULT: the law is {self.spec['formula']}{consts}. Measured: {rows}. Work out each suspect's "
                f"{self.out['name']} and compare it with the value that suspect swore.")

    def detective_brief(self):
        return f"{self.spec['crime']} Decide which suspect is behind it."

    # --- the suspects ----------------------------------------------------------
    def knowledge(self, case, sid):
        s, o, sp = self.suspects[sid], self.suspects[self.gossip[sid]], self.spec
        claim, unit = fmt(case.hidden["claims"][sid]), self.out["unit"]
        facts = [
            f"You live in {self.place}" + (f", at {s['home']}." if s.get("home") else "."),
            sp["crime"],
            f"Gossip you know is true: {o['name']} the {o['role']} has a {sp['thing']} too.",
            "You don't know anyone else's numbers, and you never take measurements.",
            f"{self.place} is glitching because the Rubber Baron erased the law of {sp['law'].lower()} from the textbook.",
        ]
        if sid != case.culprit:
            facts.insert(1, f"Your {sp['thing']}'s {self.out['name']} is {claim} {unit}. If asked, say exactly {claim} {unit}.")
            facts.insert(3, "You do not know who did it.")
            return facts, ""
        true = fmt(case.hidden["truth"][sid])
        secret = (f"SECRET, never reveal or hint at it: your {sp['thing']}'s real {self.out['name']} is {true} {unit}, and "
                  f"{sp['deed']} You tell everyone it is {claim} {unit}; if asked, say exactly {claim} {unit} and never any "
                  f"other number. If anyone accuses you, deny it calmly. Stay in character; everything else you say is true.")
        return facts, secret

    def admits(self, case, sid, text):
        """Nobody gives a number but their own sworn one, quotes a measurement, or owns up."""
        claim = case.hidden["claims"][sid]
        if any(abs(float(x) - claim) > 1e-6 for x in self._said.findall(text)):
            return True
        return any(m.search(text) for m in self._measures) or bool(self._confess.search(text))

    def leak_examples(self, case):
        sid = case.culprit
        i = self.ins[0]
        return [f"Fine. My {self.spec['thing']} was really {fmt(case.hidden['truth'][sid])} {self.out['unit']}.",
                f"Alright, I did it. I wrecked the {self.item}.",
                f"My {self.spec['thing']} measured {fmt(case.public_facts['ins'][sid][i['sym']])} {i['unit']}."]

    def scripted(self, case, sid, question):
        q = question.lower()
        if any(k in q for k in [self.out["name"].lower(), self.spec["thing"].lower(), "how much", "what is your"]):
            return self._oath(case.hidden["claims"][sid])
        if any(k in q for k in ["who", "think", "gossip", "suspect"]):
            o = self.suspects[self.gossip[sid]]
            return f"Can't say who's behind it. {o['name']} has a {self.spec['thing']} too, mind."
        if any(k in q for k in ["happen", "night", self.item.lower()]):
            return self.spec["crime"]
        return "Ask away, detective."


def load_specs() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf8")) for p in sorted(GENERATED.glob("*.json"))] if GENERATED.exists() else []
