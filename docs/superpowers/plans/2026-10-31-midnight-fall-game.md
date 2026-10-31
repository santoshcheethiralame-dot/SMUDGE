# The Midnight Fall: game plan (Kushal)

Read first: [the case spec](../specs/2026-10-31-midnight-fall.md), all of it (it is short). §3, the text
rules, applies to every line you write.

You build the case in the game against `game/public/fixtures/fall_case.json`. You never wait on the server or
the art: until Santosh's `fall` kit is up, `?fixture` serves every reply from that file, and placeholders are
Phaser shapes.

## Patterns to copy

| You are building | Copy the shape of |
|---|---|
| The case definition | `game/src/cases/motion/index.ts` (a `CaseDef`; dropping a folder in `src/cases/` registers it) |
| A bespoke lab with several steps | `game/src/scenes/LabMotion.ts` (`create()` awaits each step in turn, then `api.labCheck`, then the evidence card) |
| Cross-exam and restore | `CrossExam.ts`, `Restore.ts`: reuse them, change only what §4 beats 8–9 need |
| Footnote's hints | the `step` / `hint` handling in `LabMotion.notebook()` |

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
