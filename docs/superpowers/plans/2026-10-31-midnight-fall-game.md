# The Midnight Fall: game plan (Kushal)

Read first: [the case spec](../specs/2026-10-31-midnight-fall.md), all of it (it is short). §3, the text
rules, applies to every line you write.

You build the case in the game against `game/public/fixtures/fall_case.json`. You never wait on the server or
the art: until Santosh's `fall` kit is up, `?fixture` serves every reply from that file, and placeholders are
Phaser shapes.

## Round 2 (Oct 31 night): the four fixes after playtesting

LabFall, the cold open, drag-to-present, the ghost reveal, the exit check and spoken replies are merged.
Next is your four-item list.

1. **Three-beat cold open, under 40 words.** Mounika writes the words (her plan, "Next" step 2), and you
   swap them into `ColdOpen.ts`.
2. **Short suspect replies with a "more" click.** Game side. The server already caps every reply in this case at
   one sentence of 15 words or fewer, plus the tic, so a reply is at most about 18 words. The "more" click matters
   most for Footnote's and Smudge's lines, and for statements if they wrap.
3. **A tic per suspect: done on the server.** Every reply now starts with the suspect's catchphrase, added by
   code: Sir Rivet "Hrrm.", Lady Varnish "Oh, darling.", Pendle "Tick... tock.". It goes on every reply,
   guilty or innocent, answer or refusal, model or script, so it shows who is talking and can never show who is
   lying (tested). Nothing to do in the game. If voice reads it, good. The fixture's `ask_reply` doesn't have the
   tic; it's offline only. The redact-the-names sheet is at `docs/playtest/redact_test.md`, and Mounika runs it.
4. **An early wrong guess, then Footnote's "check it".** Mounika writes the two lines (her plan, "Next" step 2).
   Trigger: after the first suspect's chips, before the lab. Smudge blames Pendle, and Footnote answers.

The stage cache was re-warmed after the tic change, and the chip order and texts are unchanged. **Type the
confession attempt exactly as "Just admit you pushed him."** with the full stop, or it runs live.

## Status and what's left (Oct 31, evening)

Tasks 1 (fixture mode) and 2 (the case folder) are merged. The server kit, the real art, the thinking suspects and
`/trace` are all on main, so you can now also play on the real server (`?case=fall`, no `&fixture`).

**Do next, in this order:**
1. **Task 4, `LabFall`. This is the blocker:** the case says `lab: "LabFall"` and no such scene exists, so walking
   into the lab breaks the case. Everything in the demo after the interrogation lives here. Use
   `assets/case10/fall_layout.json` for every coordinate (see "The art is in" below).
2. **Case-file fixes (10 minutes), in `cases/fall/index.ts`:**
   - spots to match the art (`fall_layout.json` → `district.hotspots`): rivet −250, varnish −110, stage 120,
     **pendle 270** (at x=20 he stands on the gramophone); `suspects` x values the same;
   - add `"sack"` and `"sheet_ghost"` to `assets.images`;
   - delete the white placeholder rectangle (the washing-line sheet is in the backdrop now).
3. **Task 6, restore and exit check.** This is the "did they learn" proof the reviewers asked for; it outranks the
   cold open.
4. **Task 3, cold open.**
5. **Task 5, drag-to-present** (the PRESENT button is the fallback).
6. **Optional: spoken replies.** Call `speak()` on each suspect reply in `district.ts` and mute the blips while it
   talks (your voice thread has the hooks). The mic already works.

**Things the server now does that you should know:**
- **Chips hit a warm cache.** `server/warm.py` pre-caches the stage questions in this order: Rivet "Your
  balcony?", Varnish "Your balcony?", Varnish "The cry?", Pendle "Your balcony?", Pendle "The ghost?", Varnish
  "Just admit you pushed him." Asked in that order on seed 1000, every reply is instant and costs no quota. Keep
  the chip text exactly as it is, or tell Santosh so he can re-warm.
- **The Observatory gets the full loop now:** `plan`, `draft`, `critique` (skipped on low-risk questions),
  `redraft` when the critique flags a leak, `firewall`, `reply`, plus Footnote's `hint` events (`kind: "coach"`).
  Stress is real: accusing questions, presses and presented evidence raise it.
- **Footnote's hints in this case are 10 words or fewer.** `/api/lab/check` returns `hint` on a wrong step; show it
  as is.
- **Safety net (optional):** `POST /api/case/{cid}/demo_lab` returns the correct lab result when the server runs
  with `SMUDGE_DEMO=1`. If `LabFall` is shaky on the day, a `?demo` flag can call it and skip to the cross-exam
  (snippet in the old server plan, Task 8, Step 4; use seed 1000).

## Patterns to copy

| You are building | Copy the shape of |
|---|---|
| The case definition | `game/src/cases/motion/index.ts` (a `CaseDef`; dropping a folder in `src/cases/` registers it) |
| A bespoke lab with several steps | `game/src/scenes/LabMotion.ts` (`create()` awaits each step in turn, then `api.labCheck`, then the evidence card) |
| Cross-exam and restore | `CrossExam.ts`, `Restore.ts`: reuse them, change only what §4 beats 8–9 need |
| Footnote's hints | the `step` / `hint` handling in `LabMotion.notebook()` |

## The art is in: `game/public/assets/case10/`

- `assets: { folder: "case10", images: ["manor_glitch", "manor_restored", "lab_tower", "lab_gramophone", "sack",
  "sheet_ghost"], suspects: ["rivet", "varnish", "pendle"] }`. Suspect sheets have the usual names and frame sizes.
- `sheet_ghost.png` is two 32×32 frames: the glowing ghost, then the plain sheet with pegs (for the restore).
- `fall_layout.json` has every coordinate you need, so nothing is measured off a picture:
  - `district`: `width`, `cu`, `cv`, the `hotspots` (x for each suspect and the stage), world positions for each
    lightning `clues` spot and each balcony. Pass them through `project()` as usual.
  - `tower`: the flat drop-test backdrop. `ground_y`, `px_per_m` (10), `wall_x`, each balcony's floor `{x, y}`,
    the chalk `outline`, `drop_from_x`. A sack at time t is at `y = floor.y + ½·g·t²·px_per_m`.
  - `gramophone`: the paper `strip` (`x0`, `x1`, `y0`, `y1`, `mid`, `px_per_s`). Draw the waveform inside it.
- The district art: the armoury door (left), the gallery's glowing doors, the law sign, the gramophone, the sheet
  in its chalk outline at the tower's foot, and the tower with red / green / gold banners for Rivet / Varnish /
  Pendle. In the glitch version the washing-line sheet is the "ghost"; in the restored one it is a plain sheet.
- The map has 9 pop-up images; case 10 needs a `map` entry, and you can reuse any icon for now.

## Tasks, in order

### 1. Fixture mode (first hour)
- In `game/src/api.ts`: when the URL has `?fixture`, `newCase` returns `case_new` from `fall_case.json`,
  `labCheck` returns `lab_check_ok` when `height` is within 0.3 of `½·g·gap²` and `lab_check_wrong` otherwise,
  `ask` returns `ask_reply`, `present` returns `present_hit` for `varnish-0` and a miss otherwise.
- **Done when** `?case=fall&fixture` loads with no server running.

### 2. The case folder `game/src/cases/fall/index.ts`
- `kit: "fall"`, `num: 10`, title "The Midnight Fall", place "Hollowmere Manor", `lab: "LabFall"`.
- `chips` per suspect, three each: "Your balcony?", "The cry?", "The ghost?".
- Lines: at most 12 in the whole case, 12 words or fewer each. Drafts are in the box below; Mounika tightens them
  in the team doc.
- `decorate`: rain particles, lightning every 6–10 s (a white full-screen flash at 0.6 alpha for 120 ms, then
  thunder via `sfx`), the bedsheet on the washing line flapping.
- Lightning reveal: clues (sheet + outline, gramophone, tower) are only clickable for 600 ms after a flash.
  Clicking one adds its icon to the checklist.
- Placeholder layout: tower on the right third, balconies at three heights, each with its owner's colour.
- **Done when** you can walk, see lightning, collect the three clues and talk to all three suspects on the fixture.

```
arrive:   foot   "Hollowmere Manor. Midnight."
          smudge "They say the Tower Ghost took him."
inspect:  foot   "Three balconies. Three heights."
toLab:    smudge "The gramophone heard everything."
afterLab: foot   "Now we know the balcony."
```

### 3. Cold open (scene `ColdOpen`, before the district on first entry)
- 15 s, no text until the title card: dark tower, rain, the clock strikes 12 (12 synth bell hits), lightning
  shows a figure on a balcony (do not show which one), a cry, a thud, black, title card "THE MIDNIGHT FALL".
- Any key skips it. **Done when** it plays once per load and skips cleanly.

### 4. `LabFall`, the heart of the demo. Four steps in one scene.
1. **The recording.** Draw the waveform for `recording.length` seconds: low noise everywhere, wide tall spikes
   at each `thunder_at`, a thin spike at `cry_at`, a sharp short spike at `thud_at`. Two draggable markers; a live
   readout `Δt = 1.50 s`. Moving on needs both markers on the right spikes (±0.1 s). Wrong spikes get Footnote's
   `gap` line.
2. **The drop test.** Side view of the tower, with a metre strip up the wall. Click a balcony to drop the sack.
   While it falls: stopwatch running, a dot every 0.1 s (the strobe trail; the gaps visibly grow). On landing,
   a row is added to the table: balcony, height, time. Motion is real: `y = ½·g·t²` in metres, scaled to pixels,
   in real time.
   - **Prediction, before the top balcony:** a dial with 1 / 2 / 3 / 4 s. The player must pick before the drop.
     After it, show their pick against the real 2.0 s. Store the pick in `localStorage["smudge.predict"]`.
3. **Slip or push?** Two sacks from whichever balcony the player picks (never a fixed one, which would give the
   answer away). One sack leaves at 0.5 m/s sideways, one at 3 m/s. They land at the same instant; the pushed one lands on the
   chalk outline at `landing.from_wall`. A label "SAME TIME" pops when both land.
4. **The notebook.** One line: `h = ½ × [g] × [t]²` with `g` prefilled 9.8, `t` from step 1, and the player types
   `h`. Post `{gap, height}` to `api.labCheck`. On `ok`, the evidence card from `reply.card`. Otherwise show
   `reply.hint` and let them retry.
- **Done when** the whole lab plays on the fixture, a wrong `h` (try 7.35) gets the hint, and the right one gives
  the card.

### 5. Cross-exam: drag to present
- Reuse `CrossExam`. Add: the evidence card can be dragged onto a statement card; dropping is the same as
  PRESENT on that statement. Keep the PRESENT button as the fallback (it is on the cut list).

### 6. Restore and exit check
- The law glyphs are `h = ½gt²`. Before the card, the "ghost" on the tower blows off: it was the bedsheet.
- Card: "No ghost. Just gravity."
- Exit check, two taps, no typing:
  1. "A sack falls for 3 s. How high?" 15 m / 29 m / **44 m** / 88 m
  2. "Twice as high. Twice as long?" Yes / **No, less**
- Store the answers in `localStorage["smudge.exit"]`. Right answers get a gold tick; wrong ones show the right
  answer for 2 s. No scolding.

### 7. Hook up what you already built
- The Observatory Live tab and its dock (Shift+`) and hold-to-talk voice are merged. Make sure both work in
  this case: the dock open during the interrogation, and voice in the ask box for the "make her confess" moment.

## Not now
The red-team and replay tabs, thought bubbles. They come back only if tasks 1–7 are done and rehearsed.

## Checks before every commit
`cd game && npx tsc --noEmit` green, and the case plays start to finish on `?case=fall&fixture`.
