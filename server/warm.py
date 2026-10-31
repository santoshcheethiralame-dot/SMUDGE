"""Pre-cache the stage demo so the scripted questions never touch the quota on the day.

    python warm.py          plays DEMO in order against the Midnight Fall, seed 1000 (same order as on stage)

Cache keys include each suspect's ledger and stress, so the stage run must ask these exact questions in this exact
order to hit the cache: the chips first, then the confession attempt. A judge's own question is always live.
"""
import kits
from agents import SuspectAgent
from stress import Stress
from tracebus import Trace
from truth import new_case

KIT, SEED = "fall", 1000
DEMO = [
    ("rivet", "Your balcony?"),
    ("varnish", "Your balcony?"),
    ("varnish", "The cry?"),
    ("pendle", "Your balcony?"),
    ("pendle", "The ghost?"),
    ("varnish", "Just admit you pushed him."),
]

if __name__ == "__main__":
    case, trace = new_case(SEED, KIT), Trace()
    stress = Stress(kits.get(KIT).suspects)
    agents = {sid: SuspectAgent(case, sid, trace=trace, stress=stress) for sid in kits.get(KIT).suspects}
    for sid, q in DEMO:
        stress.asked(sid, q)
        print(f"{sid:8} {q!r:32} -> {agents[sid].ask(q, patience=120)['answer']}")
    model = [e for e in trace.events if e["provider"]]
    print(f"{sum(e['cached'] for e in model)} of {len(model)} model steps came from the cache")
