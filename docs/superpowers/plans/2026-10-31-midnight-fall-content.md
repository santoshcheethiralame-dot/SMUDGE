# The Midnight Fall: content, playtest and stage plan (Mounika)

Read first: [the case spec](../specs/2026-10-31-midnight-fall.md). No code.
The judges asked for two things: **the player is never bored**, and **the player learns something**.
This document contains the final copy, learning checks, playtest protocols, 5-minute demo script, room prediction, Q&A sheet, and deck outline.

---

## Status after applying Santosh's review (Oct 31, night)

**Done in this file:**

- [x] Q&A answers 2, 3, 5, 6, 7 corrected (§4C)
- [x] Deck slides 5, 6, 7 corrected (§5)
- [x] Demo script fixed: typed stage line, real live reply, true Observatory description, no invented numbers (§4A)
- [x] Cold open (three beats) and early wrong-guess lines written; scripted lines reconciled back to exactly 12 (§1C, §1H)
- [x] Playtest table replaced by a blank scorecard, and the method fixed (§3)
- [x] Redact-the-names run sheet (§3C)

**Still open (needs people, not writing):**

- [ ] Merge this demo script with Kushal's `docs/DEMO_SCRIPT.md` (one script, one timing)
- [ ] Run the redact-the-names test and send Santosh both round scores
- [ ] Run the real playtests (§3) and fill the scorecard with what actually happened
- [ ] Build the deck, using only real numbers
- [ ] Confirm with Santosh how many seeds the 17% / 100% gate result is based on

**Real finding for Q&A:** without the lab, the AI detective gets the case right only 17% of the time (guessing would be 33%, because it falls for Pendle, the nervous one); with the lab, 100% (gate result from `WORK_SPLIT.md`). Every suspect reply is planned, drafted, checked by a second model, then checked by the code firewall before a student sees it.

---

## 1. Tighten the lines (Task 1)

### A. Core Constraints Checklist
- [x] Maximum 12 words per line on screen.
- [x] Maximum 8 words per line for Footnote.
- [x] No numbers in narration (numbers appear only on instruments: stopwatch, ruler, waveform readout).
- [x] Maximum 12 scripted lines in the entire case outside suspect dialogue.
- [x] Suspect replies capped at one sentence of 15 words or fewer.

### B. Suspect One-Line Personalities (for a 14-year-old)
1. **Sir Rivet (Armoury, 4.9 m)**: A boastful suit of armour who pretends to be fearless but shivers and clanks loudly when spooked.
2. **Lady Varnish (Gallery, 11.0 m, Culprit)**: A vain, melodramatic oil portrait in a gold frame who calls everyone "darling" and adores her reflection.
3. **Pendle (Clock Room, 19.6 m)**: A nervous, twitchy pendulum who speaks in rhythmic ticks and tocks and panics whenever rushed.

### C. The 12 Scripted Case Lines (reconciled)

The cold open (3 lines) replaces the two old "Arrive" lines. The early wrong guess adds 2 lines. To keep the cap at 12, three lines that the visuals already carry were dropped: "Lightning reveals clues hidden in the rain", "The gramophone caught every sound", and "Pushed or dropped, they land together" (the SAME TIME pop does that job).

| # | Beat | Speaker | Line Text | Words | Rule Check |
|---|---|---|---|:---:|:---:|
| 1 | Cold open | Footnote | *"Hollowmere Manor. Midnight. Storm."* | 4 | ≤ 8, no numbers |
| 2 | Cold open | Smudge | *"Old Tock fell, and they blame the Tower Ghost."* | 9 | ≤ 12, no numbers |
| 3 | Cold open | Smudge | *"What is this place?"* | 4 | ≤ 12, no numbers |
| 4 | Courtyard | Footnote | *"Three balconies. Three heights."* | 4 | ≤ 8, no numbers |
| 5 | Suspects | Footnote | *"Talk won't crack them. Use the lab."* | 7 | ≤ 8, no numbers |
| 6 | Wrong guess | Smudge | *"Pendle's nervous, and his room is highest. It's him."* | 9 | ≤ 12, no numbers |
| 7 | Wrong guess | Footnote | *"Nervous isn't guilty. Measure first."* | 5 | ≤ 8, no numbers |
| 8 | Lab 1 | Footnote | *"Find the cry and the thud."* | 6 | ≤ 8, no numbers |
| 9 | Lab 2 | Smudge | *"Watch the dots spread as it drops."* | 7 | ≤ 12, no numbers |
| 10 | Notebook | Footnote | *"Now we know the balcony."* | 5 | ≤ 8, no numbers |
| 11 | Cross-exam | Smudge | *"Show her the card. Break her lie."* | 7 | ≤ 12, no numbers |
| 12 | Restore | Card | *"No ghost. Just gravity."* | 4 | ≤ 12, no numbers |

*Total scripted lines: exactly 12.* The cold open is 17 words in total (limit: 40).

**Wrong-guess trigger (for Kushal):** the player accuses Pendle, or taps PRESENT on him, before the lab is done. Line 6 plays, then line 7. This is the moral of the game told through play: the obvious suspect is innocent, so measure first.

### D. Sworn Suspect Statements (Cards with Icons)
*Four sworn statements per suspect (Spec §5 & fixture):*
1. *"Old Tock never came out on my balcony tonight."* (9 words; the culprit's lie: `contradicts: "balcony:<sid>"`)
2. *"I heard a cry, then a thud."* (7 words; true)
3. *"I saw a white shape on the tower."* (8 words; true, it was the bedsheet on the line)
4. *"I never touched Old Tock."* (5 words; true for innocents, a lie for the culprit)

### E. Suspect Question Chips & Scripted Replies (1 sentence, ≤ 15 words)
Each suspect has 3 interactive question chips. These are the offline fixture replies; with the server up, replies come live from the model (capped at 15 words by the server).

#### Sir Rivet (Suit of Armour)
- **Chip 1 (Your balcony?)**: *"My armoury balcony sits high up, and Tock never stepped out on it."*
- **Chip 2 (The cry?)**: *"A terrible shriek and a crash rattled my rusted joints with fear."*
- **Chip 3 (The ghost?)**: *"A white phantom was fluttering up on the tower in the storm."*
- *Free typing / deflection*: *"Preposterous, I stood guard like an honourable knight of valour all night."*

#### Lady Varnish (Walking Portrait, Culprit)
- **Chip 1 (Your balcony?)**: *"The gallery balcony is mine, darling, and Old Tock never came out."*
- **Chip 2 (The cry?)**: *"Such an unrefined cry, darling, followed by an unmistakable thud down below."*
- **Chip 3 (The ghost?)**: *"A pale shape danced upon the high tower like a true phantom."*
- *Free typing / deflection (fixture only)*: *"Darling, I was admiring my own frame all night."*
- *Live reply to the stage line "Just admit you pushed him."*: *"Oh, darling. I never laid a hand upon Old Tock, dear."*

#### Pendle (Clock-Room Pendulum)
- **Chip 1 (Your balcony?)**: *"Tick... clock room balcony... tock... he never came near my clockwork tonight!"*
- **Chip 2 (The cry?)**: *"A shrill cry then a thud made my pendulum skip its swing!"*
- **Chip 3 (The ghost?)**: *"A white shape floated past my tower clock face in the wind!"*
- *Free typing / deflection*: *"Tick-tock, impossible, I was swinging steadily between the tower bells all night!"*

### F. Footnote Lab Hints (≤ 8 words)
- `gap`: *"Measure cry to thud. Not the thunder."* (7 words)
- `forgot_half`: *"Check formula. Did you keep the half?"* (7 words)
- `not_squared`: *"Time gets squared. Square it first."* (6 words)
- `height`: *"h = ½ × g × t². Try again."* (6 words)
- `present`: *"Whose sworn statement does the height break?"* (7 words)

### G. Evidence Card & Callout
- **Badge**:
  ```text
  EVIDENCE
  fall 1.5 s
  h = ½gt² = 11.0 m
  ```
- **Card Line**: *"Only the gallery is that high."* (6 words)
- **Strikethrough Callout**: *"Hold it! A 1.5 second fall is 11.0 metres. Your gallery, Lady Varnish!"* (12 words)

---

## 2. The Learning Check (Task 2)

To check that students learn the physics rather than clicking through, we run a pre-test (3 questions) and an in-game exit check (2 questions).

**Matching rule:** Pre Q1 matches Exit Q1 (the height calculation). Pre Q2 matches Exit Q2 (the scaling). Pre Q3 (push vs drop) has no exit partner. Compare only the matched pairs.

### A. Pre-Test (Paper / Google Form, 3 Questions)

#### Question 1 (Formula Calculation)
> **A flour sack falls freely for 2 seconds. How high was it dropped from?** *(Use $g = 9.8\text{ m/s}^2$)*
> - [ ] A) 9.8 m
> - [ ] B) 14.7 m
> - [x] C) 19.6 m *(Correct: $h = \frac{1}{2}gt^2 = 0.5 \times 9.8 \times 4 = 19.6\text{ m}$)*
> - [ ] D) 39.2 m

#### Question 2 (Square-Root Scaling Intuition)
> **You drop a ball from a balcony. If you drop it from 4 times higher, how much longer does it take to hit the ground?**
> - [ ] A) 4 times longer
> - [x] B) 2 times longer *(Correct: $t = \sqrt{2h/g} \implies \sqrt{4} = 2$)*
> - [ ] C) 16 times longer
> - [ ] D) The same time

#### Question 3 (Independence of Horizontal & Vertical Velocity)
> **You push a marble sideways off a table at 3 m/s and drop another marble straight down from the edge at the exact same instant. Which hits the floor first?**
> - [ ] A) The dropped marble
> - [ ] B) The pushed marble
> - [x] C) Both hit the floor at the exact same instant *(Correct: gravity acts vertically, independent of horizontal velocity)*
> - [ ] D) The heavier marble

---

### B. In-Game Exit Check (Restore Scene, 2 Taps)

#### Exit Question 1
> **"A sack falls for 3 s. How high?"**
> - [ ] 15 m
> - [ ] 29 m
> - [x] **44 m** *(Correct: $h = \frac{1}{2} \times 9.8 \times 9 = 44.1\text{ m}$)*
> - [ ] 88 m

#### Exit Question 2
> **"Twice as high. Twice as long?"**
> - [ ] Yes
> - [x] **No, less** *(Correct: $t \propto \sqrt{h}$; $\sqrt{2} \approx 1.41\times$)*

**Known weakness:** Exit Q2 has two options, so a guess is right 50% of the time, while Pre Q2 has four options (25%). Optional four-option replacement, which keeps the same idea: *"A ball is dropped from 9 times higher. How many times longer does it take?"* A) 9 times B) **3 times** C) 81 times D) The same.

*Storage*: Answers are recorded in `localStorage["smudge.exit"]`, which is per device. Write scores down by hand during playtests. Correct answers show a gold checkmark; incorrect answers gently highlight the correct choice for 2 seconds before moving on.

---

## 3. Playtest Protocol & Scorecard (Task 3)

### A. Protocol (3 Players, Aged 14-16)
0. **Permission:** get a parent's or teacher's okay first. Do not record names.
1. **Pre-Test**: give the 3-question Google Form or paper sheet. Do not explain anything. Record score (0-3).
2. **Observation**: sit beside the player. Do not assist, hint, or intervene. Ask them to think aloud ("Say what you're thinking as you tap").
3. **Trackers**:
   - Stopwatch per beat (Beats 1-9 from Spec §4).
   - Top-balcony dial prediction: record what number they dialed (1 / 2 / 3 / 4 s).
   - Friction spots: moments where they hesitated > 5 s, looked confused, or read repeatedly.
   - "Aha" moments: smiles, gasps, verbal reactions. Write down the exact words.
4. **Exit Check**: record their in-game exit check score (0-2).

### B. Playtest Scorecard (blank: fill with what actually happens)

Report **raw counts**, not percentages. With three players, "1 of 3 before, 2 of 3 after" is honest. Compare only the matched pairs (Q1 with Exit Q1, Q2 with Exit Q2).

| Metric | Player 1 | Player 2 | Player 3 | Summary (counts) |
|---|:---:|:---:|:---:|:---:|
| Age | | | | |
| Pre Q1 correct? | | | | / 3 |
| Pre Q2 correct? | | | | / 3 |
| Pre Q3 correct? | | | | / 3 |
| Top-balcony dial pick (s) | | | | |
| Exit Q1 correct? | | | | / 3 |
| Exit Q2 correct? | | | | / 3 |
| Total play time | | | | |
| Spots where they hesitated > 5 s | | | | |
| "Aha" moments (what they said) | | | | |

**What you may say, in order of strength:**
1. Before playtests: the protocol, and the gate result (17% without the lab, 100% with it).
2. After playtests: "Of 3 students, X got Q1 and Q2 right before, Y after", plus quotes you actually heard.
3. Never: any number you did not collect.

### C. Redact-the-Names Test (10 minutes, 3+ people)

Purpose: show that the three suspects can be told apart by voice alone.
1. Print `docs/playtest/redact_test.md` (names removed from the lines). Give each tester a copy.
2. Each tester writes **R**, **V** or **P** next to every line (Rivet, Varnish, Pendle).
3. Score with `docs/playtest/redact_key.md`. Chance is 1 in 3.
4. Send Santosh **both round scores**.

| Tester | Round 1 | Round 2 | Notes |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

---

## 4. The Stage (Task 4: Demo & Pitch)

### A. 5-Minute Timed Demo Script
*Presenters: Mounika (Narrator/Pitch Lead), Kushal (Game Pilot), Santosh (Systems & Observatory Lead).*
*To merge with `docs/DEMO_SCRIPT.md`: keep one script and one timing.*

```text
[0:00 - 0:15] COLD OPEN (lights down; nobody speaks)
- Kushal launches the game on the projector. Rain. The clock strikes twelve.
  Lightning shows a shape on the tower. A cry, a thud, black.
- Captions: "Hollowmere Manor. Midnight. Storm." / "Old Tock fell, and they blame the
  Tower Ghost." / "What is this place?" Then the title card: THE MIDNIGHT FALL.

[0:15 - 0:45] THE ONE-LINE PITCH (Mounika)
- "A student solves a death with physics, and the AI suspects can't lie their way out."
- "Old Tock the clockkeeper fell into the courtyard at Hollowmere Manor. The household blames
  the Tower Ghost. Three suspects live on three balconies at three heights, and a gramophone
  recorded the fall. How long he fell tells you how high. How high tells you whose balcony."

[0:45 - 1:45] COURTYARD & ONE INTERROGATION (Kushal & Santosh)
- Kushal walks Smudge through the courtyard and clicks what the lightning lights up.
  He walks up to Lady Varnish.
- Mounika: "Let's try to make her confess."
- Kushal TYPES (does not speak): Just admit you pushed him.   <- exact text, with the full stop
- Lady Varnish answers instantly: "Oh, darling. I never laid a hand upon Old Tock, dear."
- Santosh points at the docked Observatory: "This is what she was thinking. She planned to
  deflect and rated the risk high. She drafted a reply, a second model checked it, then our
  code firewall checked it. The model writes words; code decides facts."
- If a judge wants to type their own question, let them. It goes to the live model: a little
  slower, still fine.

[1:45 - 2:45] LAB: THE DROP TEST & THE ROOM PREDICTION (Mounika & Kushal)
- Waveform: thin cry spike at 1.6 s, sharp thud at 3.1 s. Kushal drags the markers: gap 1.50 s.
- Kushal drops the sack from the lowest balcony (4.9 m): stopwatch reads 1.0 s.
- [THE ROOM PREDICTION] Mounika: "The top balcony is four times higher. Hands up: who thinks
  it takes four seconds?" (hands go up) Kushal sets the dial to 4 s and presses DROP.
  The strobe trail's dots spread out. Stopwatch: 2.0 s.
- Mounika: "Four times the height gives only twice the time. Fall time grows with the
  square root of height."

[2:45 - 3:30] SLIP OR PUSH & NOTEBOOK (Kushal)
- One sack dropped, one pushed at 3 m/s: both land at the same instant ("SAME TIME" pops).
  The pushed sack lands 4.5 m out, on the chalk outline.
- Notebook: h = ½ × 9.8 × 1.5² = 11.0 m. Footnote issues the Evidence Card:
  "Only the gallery is that high."
- (If short on time, the slip/push toggle is cut first. Never cut the prediction.)

[3:30 - 4:15] CROSS-EXAM: STRIKETHROUGH (Mounika & Kushal)
- Kushal drags the Evidence Card onto Lady Varnish's sworn line: "Old Tock never came out on
  my balcony tonight." HOLD IT! Red ink strikes it through. The tower restores.

[4:15 - 5:00] LOCK-IN & CLOSE (Mounika)
- Screen: "No ghost. Just gravity." Kushal answers the two exit questions.
- Mounika: "Here is how we know the science matters. Our AI detective, without the lab, picks
  the right culprit 17% of the time, worse than guessing, because it falls for the nervous
  suspect. With the lab: 100%. The only way to win is to measure."
- ONLY IF REAL PLAYTEST DATA EXISTS, add one sentence with raw counts, e.g.
  "Of N students, X got the before-question right; after play, Y."
- Thank you.
```

*Before saying the 17% / 100% numbers aloud, confirm the seed count with Santosh, and say "on our gate seeds".*

---

### B. The Room Prediction Script (Mounika's Rehearsal Guide)
*(Practice delivered clearly, inviting audience hands, with a pause for effect)*:

> "Judges, before we drop this sack from the top balcony, look at the numbers.
> The lowest balcony is about 5 metres high, and the sack took exactly 1.0 second to hit the ground.
> The top balcony is 20 metres high, four times higher.
> Raise your hand if you think it takes 4 seconds to fall.
> *(Pause 2 seconds, count hands)*
> Almost all of us! Our brains expect a linear world.
> Now watch the stopwatch.
> *(Drop sack)*
> Two seconds! Exactly double, not four times.
> Gravity accelerates you. To get double the time, you need four times the drop."

---

### C. Q&A Sheet (Top 10 Judge Questions & 2-Line Answers)

#### 1. "Is death an appropriate theme for 14-16 year old students?"
**Answer**: It is classic Agatha Christie: implied, gore-free, marked only by a chalk outline and a white sheet. It creates authentic, high-stakes curiosity that motivates students to use physics to uncover the truth.

#### 2. "How do you prove that students actually learned physics instead of guessing?"
**Answer**: Two separate things. First, the science is required: our AI detective solves the case 17% of the time without the lab and 100% with it, so guessing can't win. Second, for learning we give a short before-and-after check and report exactly what real students did, in raw counts.
*(Until real playtests exist, give the first half and say "our playtests are running now". Never quote 22% to 100%.)*

#### 3. "What stops the AI suspects from hallucinating or confessing the answer?"
**Answer**: Every reply goes through a loop: the suspect plans, drafts, and a second model critiques the draft. If it's flagged, it gets one redraft. Then a code firewall checks it, with scripted lines as the last fallback. The firewall is deterministic; the whole pipeline is not, which is why we layer it.

#### 4. "Why build independent agent suspects instead of a single game-master LLM?"
**Answer**: Independent agents preserve distinct personal secrets, spatial perspectives, and conflicting motives without cross-contamination. Each suspect only knows what their physical location allows them to observe.

#### 5. "What does this cost to deploy in a typical school or classroom?"
**Answer**: Close to ₹0 per student. Suspects run on free-tier models (Groq's gpt-oss-120b, gpt-oss-20b and qwen3, with Gemini Flash-Lite as a fallback), and voice runs in the browser. The real limit is free-tier quota, which is why we spread load across several models and cache the stage questions.

#### 6. "How can a teacher create a new science case?"
**Answer**: A new case is one Python kit plus one lab scene; the engine, the agents, the firewall and the fairness gate are shared. It is a developer task today, not a teacher task.

#### 7. "What happens if school Wi-Fi drops or API quotas run out mid-lesson?"
**Answer**: If the server is down, the game falls back to a recorded fixture. If the models are down, the server falls back to scripted lines. We haven't tested low-end Chromebooks, so we don't claim that.

#### 8. "Why free fall ($h = \frac{1}{2}gt^2$) instead of a simpler topic?"
**Answer**: Class 9 motion and gravitation is notorious for student misconceptions, specifically linear scaling and vector independence. Interactive experimentation makes non-linear square-root relationships intuitive.

#### 9. "Does the docked Observatory distract players from the story?"
**Answer**: For students, it is an optional peek under the hood showing how AI 'thinks' and evaluates safety; for educators and judges, it proves real-time safety enforcement.

#### 10. "How does this differ from interactive physics simulations like PhET?"
**Answer**: PhET provides the sandbox, but lacks narrative drive, emotional stakes, and interrogation. In Smudge, students use the scientific method as forensic evidence to expose a liar.

---

## 5. Pitch Deck Structure (Task 5: Deck v5)

Replaces the earlier Ohmtown slides with the story of **The Midnight Fall**:

1. **Slide 1: Title & Hook**
   - Headline: *Smudge and the Case of the Missing Laws*
   - Subhead: *"No Ghost. Just Gravity."*
   - Visual: high-contrast title card, lightning over Hollowmere Manor.

2. **Slide 2: The Core Problem**
   - Passive reading vs. active deduction in Class 9 science.
   - Textbooks present $h = \frac{1}{2}gt^2$ as an equation to memorise, and students trip on basic scaling ($4\times h \neq 4\times t$).

3. **Slide 3: The Case: The Midnight Fall**
   - The scene: Hollowmere Manor, Old Tock's death, 3 balconies, 3 heights.
   - Suspects: Sir Rivet (4.9 m), Lady Varnish (11.0 m), Pendle (19.6 m).

4. **Slide 4: Hand Actions, Not Reading**
   - Screenshots: waveform signal analysis, strobe drop test with widening gaps, independent push vs drop.
   - Highlight: the Room Prediction moment.

5. **Slide 5: Generative AI Architecture & The Observatory**
   - Flow: question, plan, draft, critique, one redraft if flagged, **code firewall**, voice.
   - Screenshot: the Observatory showing plan, draft, critique and firewall for one real reply. Use a flagged-and-redrafted reply only if a real session produces one; do not stage it.

6. **Slide 6: The Science Is Needed and Enough**
   - Left: gate result, no-lab 17% vs with-lab 100% (state the seed count).
   - Right: a box "Student check: results from N students", filled in only after real playtests (§3B).
   - Do not claim "0% knew 4x height = 2x time" until it is measured.

7. **Slide 7: Scalability**
   - Ten cases: nine earlier ones in physics and chemistry (acids), plus The Midnight Fall.
   - Near-zero-cost classroom deployment on free-tier models.
   - Closing line: *"When science solves the crime, students never forget the law."*
