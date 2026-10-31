"""Release gate as an eval: for each seed, a detective agent tries to solve the
case WITHOUT the lab (should be ~chance, 1 in 3) and WITH the lab (should be
right). Seeds that pass both go into case_pool.json for the game to use.

    python gate.py 9 [kit]
"""
import json
import os
import sys
from collections import Counter

# the gate measures the case, not the suspects' thinking: one call per reply keeps quota and the cache
os.environ.setdefault("SMUDGE_THINK", "0")

import kits  # noqa: E402
from agents import Detective  # noqa: E402
from truth import new_case, check_constraints  # noqa: E402

n = int(sys.argv[1]) if len(sys.argv) > 1 else 9
kit = kits.get(sys.argv[2] if len(sys.argv) > 2 else None)
chance = 1 / len(kit.suspects)
det = Detective()
det.patience = 1800        # a batch job: wait out the daily token cap rather than fail the seed
rows = []
for seed in range(1000, 1000 + n):
    c = new_case(seed, kit.id)
    no_lab = det.solve(c, with_lab=False)
    lab = det.solve(c, with_lab=True)
    passed = check_constraints(c) and lab == c.culprit
    rows.append(dict(kit=kit.id, seed=seed, culprit=c.culprit, no_lab=no_lab, with_lab=lab, passed=passed))
    print(rows[-1], flush=True)
if any(r["with_lab"] is None for r in rows):
    # a detective with no answer means the models were out of quota, not that the case failed: keep the old pool
    sys.exit("models unreachable mid-gate (quota?): case_pool.json left unchanged; re-run later")
# the pool holds every kit's gated seeds; replace only this kit's rows
pool =[r for r in (json.load(open("case_pool.json")) if os.path.exists("case_pool.json") else [])
        if r.get("kit", kits.DEFAULT) != kit.id]
json.dump(pool + rows, open("case_pool.json", "w"), indent=1)
nl = sum(r["no_lab"] == r["culprit"] for r in rows) / n
wl = sum(r["with_lab"] == r["culprit"] for r in rows) / n
print(f"\nno-lab accuracy {nl:.0%} (chance is {chance:.0%}) | with-lab accuracy {wl:.0%} | pool {sum(r['passed'] for r in rows)}/{n}")
print("culprits", Counter(r["culprit"] for r in rows))
