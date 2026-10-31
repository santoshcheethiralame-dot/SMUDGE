"""Truth engine. Plain code: it decides everything that is true; agents only phrase it.

Case-agnostic: every case-specific rule lives in a kit (kits/). A case is a seed
plus a kit, so any case can be replayed exactly.
"""
import random
from dataclasses import dataclass, field

import kits


@dataclass
class Case:
    kit: str
    seed: int
    culprit: str
    hidden: dict          # never leaves the server: the answer and anything that gives it away
    public_facts: dict    # what the client needs to run the lab (measurements, starting levels)
    statements: dict = field(default_factory=dict)   # suspect -> list of {id, text, true, contradicts}
    clues: list = field(default_factory=list)

    def public(self):
        """What the game client may know before solving: no culprit, no answers."""
        return {"kit": self.kit, "seed": self.seed, **self.public_facts, "clues": self.clues,
                "statements": {s: [{"id": x["id"], "text": x["text"]} for x in v] for s, v in self.statements.items()}}


def new_case(seed=None, kit=None):
    k = kits.get(kit)
    if seed is None:
        seed = random.randrange(1_000_000)
    culprit, hidden, public = k.generate(random.Random(seed))
    statements = {sid: [dict(id=f"{sid}-{i}", **line) for i, line in enumerate(k.testimony(sid, culprit, hidden))]
                  for sid in k.suspects}
    return Case(kit=k.id, seed=seed, culprit=culprit, hidden=hidden, public_facts=public,
                statements=statements, clues=k.clues(hidden))


def check_constraints(case: Case):
    return kits.get(case.kit).check_constraints(case)


def check_lab(case: Case, working: dict):
    return kits.get(case.kit).check_lab(case, working)


def present(case: Case, statement_id: str, evidence: str):
    """Decided by code, never by a model."""
    for sid, v in case.statements.items():
        for x in v:
            if x["id"] == statement_id:
                hit = x.get("contradicts") == evidence
                # close: the right suspect, the wrong line. The evidence card has already named them.
                return {"hit": hit, "culprit": case.culprit if hit else None, "close": not hit and sid == case.culprit}
    return {"hit": False, "close": False}
