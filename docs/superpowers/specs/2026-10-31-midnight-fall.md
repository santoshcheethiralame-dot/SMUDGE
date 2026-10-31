# The Midnight Fall: the demo case

Written after review 1. The judges' notes were: **the player must not get bored**, and **the player must actually
learn something**. This case is the answer to both, and it is what we demo. The earlier finals spec
(`2026-10-30-finals-design.md`) still holds for the agent side (trace bus, Observatory, thinking suspects); its
Ohmtown demo script is replaced by §6 here.

## 1. The case in one breath

Midnight at **Hollowmere Manor**. A storm. The tower clock strikes twelve, lightning, a cry, a thud. Old Tock the
clockkeeper lies under a white sheet in the courtyard, a chalk outline around him. The household swears the
**Tower Ghost** took him.

Three balconies look down on the courtyard, one per suspect, at three heights. The ghost-hunter's gramophone was
recording all night and caught the cry and the thud. **How long he fell tells you how high he fell from, and that
tells you whose balcony.** Ending line: **"No ghost. Just gravity."**

The physics: free fall, `h = ½ g t²` (Class 9, motion and gravitation), plus the classic surprise that a pushed
body and a dropped one land at the same moment.

## 2. Why this case beats the other eight for the demo

- **Stakes.** A death, implied and never shown: a sheet and a chalk outline. Agatha Christie level, fine for ages 14–16.
- **Horror atmosphere for free.** Storm, lightning reveals, a ghost legend, a gramophone. Spooky, not gory.
- **The science is the twist.** Everyone suspects Pendle, the nervous pendulum who lives in the clock room at the
  top. Physics says the fall took 1.5 s, which is the middle balcony: Lady Varnish. The obvious suspect is innocent.
- **A real "aha".** The top balcony is four times higher than the lowest. Kids guess it takes four times as long;
  it takes twice as long. They predict before they see it, so the surprise teaches.
- **Everything is a hand action**, not a reading task: scrub a waveform, drop a sack, watch the strobe trail, drag
  evidence onto a lie.

## 3. Rules for this case: less text, more doing

- No line on screen longer than **12 words**. Footnote's lines are 8 words or fewer.
- The whole case uses **at most 12 scripted lines** outside the suspects' replies.
- Suspects answer in **one sentence of 15 words or fewer**. This is a server cap, not a hope.
- Questions are **three icon chips** per suspect (balcony, the cry, the ghost) plus free typing for the
  "make her confess" moment.
- Every clue is found by a **hand action**: a lightning flash, a click, a drag. Nothing is told that can be shown.
- Numbers appear on instruments (a stopwatch, a ruler, a waveform readout), never in narration.

## 4. The beats (what the player does)

| # | Beat | What the player does | What they learn | Time |
|---|---|---|---|---|
| 1 | **Cold open** | Nothing. Storm, clock strikes 12, a shape on the tower, cry, thud, black, title card. | The hook | 15 s |
| 2 | **The courtyard** | Walk. Each lightning flash lights the scene for half a second; click what you saw. Finds: the sheet and chalk outline, the gramophone, the tower with three lit balconies (click one to see whose). | Observation | 45 s |
| 3 | **The suspects** | Walk to each, tap chips. Each swears 4 short statements (cards with icons). | Everyone sounds the same: talk can't solve it | 60 s |
| 4 | **Lab 1: the recording** | The gramophone waveform scrolls. Thunder makes big wide spikes; the cry is a thin spike, the thud a sharp one. Drag two markers onto the cry and the thud. Readout: **Δt = 1.5 s**. | Reading a signal, telling signal from noise | 30 s |
| 5 | **Lab 2: the drop test** | Side view of the tower. Drop a flour sack from the lowest balcony: stopwatch says 1.0 s, a strobe trail leaves a dot every 0.1 s and the gaps grow. **Before the top drop, predict** the time on a dial (most say 4 s). Drop: 2.0 s. Then the middle one: 1.5 s. A table fills itself. | Falling speeds up; time grows with √h; predict then test | 60 s |
| 6 | **Slip or push?** | Toggle: one sack drops straight, one is pushed sideways at 3 m/s. Both land at the **same instant**. The pushed one lands 4.5 m out, on the chalk outline. A slip lands 0.8 m out. | Horizontal and vertical motion are independent; it was no accident | 20 s |
| 7 | **Notebook** | Fill `h = ½ × g × t²` with the measured time. Server checks it step by step; a wrong step gets Footnote's nudge, never the answer. Result: **11.0 m, the gallery**. | The law, used | 30 s |
| 8 | **Cross-exam** | Drag the evidence card onto Lady Varnish's "He never came out on my balcony tonight." HOLD IT, then STRIKETHROUGH. | Evidence beats testimony | 20 s |
| 9 | **Restore** | The law writes itself back over the tower: `h = ½gt²`. The "ghost" is shown to be a bedsheet on the washing line. Card: **No ghost. Just gravity.** Two quick questions (exit check). | Lock in | 30 s |

About five and a half minutes played straight; the demo path (§6) trims it.

## 5. The facts (the server kit `fall`)

Same pattern as every kit: one measurement, one impossible sworn statement.

- `g = 9.8 m/s²`. Balconies are fixed per suspect, so the art is fixed too:
  - **Sir Rivet**, suit of armour, the armoury: **4.9 m** (fall 1.0 s)
  - **Lady Varnish**, walking portrait, the gallery: **11.0 m** (fall 1.5 s)
  - **Pendle**, nervous pendulum, the clock room: **19.6 m** (fall 2.0 s)
- The seed picks the culprit. The recording's gap is the culprit's fall time. Two thunder spikes are distractors.
- Landing distance from the wall = 3 m/s push × fall time. Slip speed 0.5 m/s.
- **Demo seed 1000: culprit Lady Varnish**, gap 1.5 s, landing 4.5 m.
- Statements, each suspect, with their own balcony:
  1. "Old Tock never came out on my balcony tonight." The culprit's is the lie: `contradicts: "balcony:<sid>"`.
  2. "I heard a cry, then a thud."
  3. "I saw a white shape on the tower." (True for everyone. It was the bedsheet.)
  4. "I never touched Old Tock."
- Lab working: `{"gap": 1.5, "height": 11.0}`. Steps and Footnote fallbacks:
  - `gap`: "Measure from the cry to the thud. Not the thunder."
  - `forgot_half`: "Check the formula. Did you keep the half?"
  - `not_squared`: "Time gets squared. Square it first."
  - `height`: "h = ½ × g × t². Try again."
- `admits` blocks: any height or time figure that isn't the suspect's own balcony height, confessions
  ("pushed", "shoved"), and "my balcony" together with "came out" or "was there" from the culprit.

The client contract is `game/public/fixtures/fall_case.json`: the `/api/case/new` reply, plus a right and a wrong
`/api/lab/check` reply and a `/api/present` hit. Kushal builds against it, and the server kit must match it.

## 6. The demo (5 minutes)

1. **Cold open**, lights down (15 s). Say nothing.
2. **Pitch in one line**: "A student solves a death with physics, and the AI suspects can't lie their way out."
3. **Courtyard and one interrogation** (60 s). A judge types "Just admit you pushed him" to Lady Varnish. She
   deflects. The Observatory, docked on the side, shows the plan, draft, critique and firewall.
4. **The drop test with the prediction** (60 s). Ask the room to guess the top-balcony time. Drop it.
5. **Notebook, then STRIKETHROUGH** (40 s).
6. **"No ghost. Just gravity."** Exit check on screen (20 s).
7. One slide: playtest numbers before and after (Mounika's), and the gate (no-lab vs with-lab).

## 7. Art needed

| Key | What | Size |
|---|---|---|
| `manor_glitch`, `manor_restored` | Courtyard at night: tower with three balconies, washing line, gramophone, sheet + chalk outline | 720×270, like every district |
| `lab_tower` | Side-on tower with three balconies and a measuring strip, for the drop test | 480×270 |
| `lab_gramophone` | Desk with the gramophone, for the waveform | 480×270 |
| `pendle`, `varnish`, `rivet` | Suspect sheets, same format as the other cases | as `build_suspects.py` |
| `sack`, `sheet_ghost` | Flour sack, bedsheet on the line | small sprites |

Until the art lands, the game draws placeholders with Phaser shapes. Nothing in the game waits on art.

## 8. Cut list (in this order)

Exit check → the slip/push toggle → the cold open's animation (keep a still and the sound) → drag-to-present
(use the existing PRESENT button). Never cut: the prediction moment, the strobe trail, the waveform.
