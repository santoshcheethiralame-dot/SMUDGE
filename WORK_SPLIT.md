# Finals: who does what

We have 48 hours to the final round: a 5–10 minute live demo, then Q&A. The demo shows two things, both in
Ohmtown (`?case=ohm`, seed 1000):

1. **Interrogation in the glass box.** Suspects plan, draft and critique every reply before the firewall, live in
   the Observatory, spoken out loud. A judge tries to make the culprit confess.
2. **The gate, replayed.** The detective agent fails without the lab and wins with it, next to the red-team
   scoreboard.

The full design is [the finals spec](docs/superpowers/specs/2026-10-30-finals-design.md). Read §2 (the demo) and
§3 (the contract) whoever you are.

## Your part

| Who | Plan | First thing to do |
|---|---|---|
| Santosh | [server plan](docs/superpowers/plans/2026-10-30-finals-server.md) | Task 1: the contract fixtures, by T+2, so Kushal is unblocked |
| Kushal | [game plan](docs/superpowers/plans/2026-10-30-finals-game.md) | Task 1: the Observatory's Live tab, against the fixtures |
| Mounika | [content plan](docs/superpowers/plans/2026-10-30-finals-content.md) | Task 1: the red-team attack lines, due T+14 |

## Milestones

| T+ (hours) | What must be true |
|---|---|
| 2 | Contract locked; fixtures in `game/public/fixtures/` |
| 14 | Thinking suspects work end to end; attack lines in; voice started |
| 20–24 | **First full rehearsal** of the demo; decide cuts |
| 34 | **Feature freeze**; backup video recorded |
| 34–44 | Bugs only; three rehearsals; no gate or red-team runs |

**Cut order** if a rehearsal shows we are behind: thought bubbles → generated red-team variants → spoken replies
(keep the mic) → animated gate replay.

## Getting started

1. Clone, then follow [docs/HANDOFF.md](docs/HANDOFF.md) §2 to run the server and the game. Ask Santosh for the
   two keys for `smudge/.env`; never commit that file.
2. Before every commit: `cd server && python -m pytest tests -q` and `cd game && npx tsc --noEmit`, both green.
3. Pull before you start, push small commits, one feature each. Two people never edit the same file at the same
   time: the server is Santosh's, `game/src/systems/observatory.ts`, `inside.ts`, `voice.ts` and `ui.ts` are
   Kushal's.
4. Something blocked or unclear? Say so in the team chat straight away rather than working around it.
