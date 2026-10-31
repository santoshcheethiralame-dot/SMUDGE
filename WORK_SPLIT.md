# Finals: who does what

**Changed after review 1.** The judges asked that the player never gets bored and actually learns something.
The demo is now one new case, **The Midnight Fall**: a death at a haunted manor, solved with free fall
(`h = ½gt²`). It is short on text and long on hands-on play. The agent side (thinking suspects, firewall,
Observatory) stays and runs inside it.

Read [the case spec](docs/superpowers/specs/2026-10-31-midnight-fall.md) whoever you are. It is short.

## Where we are (updated Oct 31, evening)

**Done and on main:** the server side of the case (the `fall` kit, gated: with-lab 100%, no-lab 17%), all the
art in `game/public/assets/case10/`, suspects that plan, draft, critique and redraft every reply, stress, the live
`/trace` feed, the warm demo cache, and on Kushal's side the Observatory, the mic, fixture mode and the case folder.

**The blocker:** the case points at a `LabFall` scene that doesn't exist yet, so walking into the lab breaks it.
Everything below waits on that.

## Latest (Oct 31, late)

Each plan has a "Do next" or "Review and next steps" section at the top: read that first.
- **Kushal:** P0 is lining LabFall and the courtyard up with the art (`fall_layout.json`), then Mounika's lines,
  the "more" click, a production build with a preview proxy, and one merged demo script.
- **Mounika:** fix the Q&A facts and the demo script, write the cold-open and wrong-guess lines, run the
  redact-the-names test, then the real playtests. **The playtest table is a template: nobody quotes those numbers
  until real players produce them.**
- **Santosh:** tics, the redact sheet and the warm cache are done; next is the full rehearsal on the production build.

## What's left

| Who | What, in order | Plan |
|---|---|---|
| Kushal | 1. **`LabFall`** (the whole demo lives here) · 2. case-file fixes (10 min) · 3. restore + exit check · 4. cold open · 5. drag-to-present · 6. spoken replies (optional) | [game plan](docs/superpowers/plans/2026-10-31-midnight-fall-game.md), "Status and what's left" at the top |
| Mounika | 1. final lines (if not sent yet) · 2. the before-play learning check · 3. **playtests** as soon as the lab plays · 4. demo script, Q&A sheet, deck | [content plan](docs/superpowers/plans/2026-10-31-midnight-fall-content.md) |
| Santosh | first full run on the real server with Kushal's lab; rerun `server/warm.py` whenever the stage questions change; keep the server up for playtests | below |

Santosh's list:
1. ~~The `fall` kit, with tests; replies match the fixture; 15-word reply cap.~~ Done.
2. ~~Gate the kit; demo seed 1000 must pass.~~ Done: 6/6, with-lab 100%, no-lab 17%.
3. ~~Art.~~ Done, in `game/public/assets/case10/`.
4. ~~The thinking loop and stress, for the Observatory.~~ Done: live on `/trace`.
5. ~~Warm cache for the stage questions (`server/warm.py`) and a `demo_lab` safety net.~~ Done.
6. Full rehearsal on the real server once `LabFall` lands.

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
