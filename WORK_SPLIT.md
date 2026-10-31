# Finals: who does what

**Changed after review 1.** The judges asked that the player never gets bored and actually learns something.
The demo is now one new case, **The Midnight Fall**: a death at a haunted manor, solved with free fall
(`h = ½gt²`). It is short on text and long on hands-on play. The agent side (thinking suspects, firewall,
Observatory) stays and runs inside it.

Read [the case spec](docs/superpowers/specs/2026-10-31-midnight-fall.md) whoever you are. It is short.

## Your part

| Who | Plan | First thing to do |
|---|---|---|
| Santosh | below | The `fall` server kit, matching `game/public/fixtures/fall_case.json` |
| Kushal | [game plan](docs/superpowers/plans/2026-10-31-midnight-fall-game.md) | Task 1: `?fixture` mode, then the case folder and `LabFall` |
| Mounika | [content plan](docs/superpowers/plans/2026-10-31-midnight-fall-content.md) | Task 1: tighten the lines, due in 3 hours |

Santosh's list, in order:
1. ~~`server/kits/fall.py` with tests; replies match the fixture exactly; 15-word reply cap.~~ Done.
2. Gate the kit; demo seed 1000 must pass (culprit Lady Varnish).
3. Art through the pipeline: the manor courtyard, the two lab backdrops, three suspects, the sack and the sheet
   (spec §7).
4. From the [server plan](docs/superpowers/plans/2026-10-30-finals-server.md): the thinking loop and stress, for
   the Observatory.

## Milestones (hours from now)

| H+ | What must be true |
|---|---|
| 3 | Lines final; Kushal plays the courtyard on the fixture |
| 8 | `fall` kit live on the server; `LabFall` recording and drop test work |
| 14 | The whole case plays end to end on the real server |
| 18 | Art in; **first full rehearsal**; playtests start |
| 26 | **Feature freeze**; backup video recorded |
| 26+ | Bugs only, rehearsals, deck |

**Cut order** if a rehearsal shows we are behind: see spec §8. Never cut the prediction, the strobe trail or the
waveform.

## Getting started

1. Pull, then follow [docs/HANDOFF.md](docs/HANDOFF.md) §2 to run the server and the game. Ask Santosh for the two
   keys for `smudge/.env`; never commit that file. The new case runs without either one: `?case=fall&fixture`.
2. Before every commit: `cd server && python -m pytest tests -q` and `cd game && npx tsc --noEmit`, both green.
3. Push small commits, one feature each. The server and `art/` are Santosh's; `game/src` is Kushal's.
4. Something blocked or unclear? Say so in the team chat straight away rather than working around it.
