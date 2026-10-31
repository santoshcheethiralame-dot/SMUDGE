# Author Lite: a case from one line (review 2)

Must-ship D cut to what fits in one day. A teacher types "Class 9, pressure: P = F/A"; agents write a case, code
proves it solvable, a detective agent gates it, and it is playable in the game straight away, on borrowed art.

## The one case shape every generated case uses

Each suspect swears one value of the law's OUTPUT for their own thing ("My crate pressed at 1200 Pa"). The lab
gives each suspect's INPUT measurements (force, area). The player computes the output for each; the culprit's
sworn value is the one the numbers say is impossible. Same shape as sound/heights, so the gate, filter and
cross-exam all work unchanged.

## Pieces

| Piece | File | What |
|---|---|---|
| Spec | `server/kits/generated/<id>.json` | the case as data (schema in `kits/generic.py`'s docstring) |
| GenericKit | `server/kits/generic.py` | a Kit built from a spec; formulas parsed with `ast`, never `eval`; loads every spec in `generated/` at start |
| Author | `server/author.py` | Designer (model, JSON spec) -> Solver (code, 200 seeds) -> Critic (model) -> redesign, at most 3 rounds -> Casting (code: borrowed cast and district) -> Gate (detective agent, 2 seeds, no-lab and with-lab) -> save |
| API | `server/api.py` | `POST /api/author {prompt}` -> `{job}`; `GET /api/author/{job}?since=` -> trace events, status, spec; `GET /api/kits/generated` -> specs |
| Game | `game/src/cases/generated.ts` | `fromSpec(spec)` builds a CaseDef on the borrowed case's art, notebook-only lab |
| Game | `game/src/systems/author.ts` | the panel: prompt box, agent lanes (reuses the Observatory pills), Play button |

Trace events use the Observatory contract (`tracebus.py`), with kind `author` and steps design/solve/critique/cast/gate.

## Cut on purpose

New art, map pins for generated cases, persistence of authored cases beyond the JSON file, more than one case shape.

## Pick-up notes

Golden specs (offline fallback and test fixtures) live in `server/kits/golden/`. Tests: `server/tests/test_generic.py`,
`server/tests/test_author.py` (fake model, offline). Each step is committed separately; `git log` shows how far it got.
