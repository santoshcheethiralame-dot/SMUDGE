"""The redact-the-names test: can a player tell who is talking from the words alone?

    python redact_sheet.py          asks every Midnight Fall suspect the same questions (seed 1000, real models),
                                    then writes docs/playtest/redact_test.md and redact_key.md

Round A hides names, rooms, heights and tics: does each personality carry on its own? Round B keeps the tics. A tester
reads each line and writes R (Sir Rivet), V (Lady Varnish) or P (Pendle). Pass: 9 of 12 or better in round B.
The key is a separate file so the tester never sees it.
"""
import random
import re
from pathlib import Path

import kits
from agents import SuspectAgent
from stress import Stress
from tracebus import Trace
from truth import new_case

KIT, SEED = "fall", 1000
QUESTIONS = ["Your balcony?", "The cry?", "The ghost?", "Who do you think made Old Tock fall?"]
NUMBER = re.compile(r"\b(\d+(\.\d+)?|(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|nineteen|twenty)"
                    r"( point \w+)?)\b", re.I)
OUT = Path(__file__).resolve().parent.parent / "docs" / "playtest"


def redact(text, k, keep_tic):
    for s in k.suspects.values():
        if not keep_tic:
            text = text.replace(s["tic"], "").strip()
        for word in (s["name"], *s["name"].split(), s["room"], s["role"]):
            text = re.sub(rf"\b{re.escape(word)}\b", "▇▇▇", text, flags=re.I)
    return NUMBER.sub("▇▇▇", text)          # heights give the speaker away as surely as names do


if __name__ == "__main__":
    k = kits.get(KIT)
    case, trace = new_case(SEED, KIT), Trace()
    stress = Stress(k.suspects)
    agents = {sid: SuspectAgent(case, sid, trace=trace, stress=stress) for sid in k.suspects}
    lines = []
    for q in QUESTIONS:
        for sid in k.suspects:
            stress.asked(sid, q)
            lines.append((sid, q, agents[sid].ask(q, patience=120)["answer"]))
            print(sid, "->", lines[-1][2])
    tag = {"rivet": "R", "varnish": "V", "pendle": "P"}
    sheet = ["# The redact-the-names test", "",
             "For each line write who said it: **R** (Sir Rivet, the armour), **V** (Lady Varnish, the portrait) or "
             "**P** (Pendle, the pendulum). Names and rooms are blacked out. Don't look at the key until both rounds "
             "are done. About 10 minutes.", ""]
    key = ["# Redact test: the key", "", "Score each round out of 12. Round B passes at 9 or better. Round A shows "
           "whether the personalities carry without the tics; under 6 means the voices need work.", ""]
    for name, keep, seed in (("A (no tics)", False, 1), ("B (with tics)", True, 2)):
        order = lines[:]
        random.Random(seed).shuffle(order)
        sheet += [f"## Round {name}", "", "| # | Question | Reply | Who? |", "|---|---|---|---|"]
        sheet += [f"| {i} | {q} | {redact(a, k, keep)} | |" for i, (_, q, a) in enumerate(order, 1)]
        key += [f"## Round {name}", "", " ".join(f"{i}:{tag[sid]}" for i, (sid, _, _) in enumerate(order, 1)), ""]
        sheet.append("")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "redact_test.md").write_text("\n".join(sheet), encoding="utf8")
    (OUT / "redact_key.md").write_text("\n".join(key), encoding="utf8")
    print("wrote", OUT / "redact_test.md")
