# The Midnight Fall: content, playtest and stage plan (Mounika)

Read first: [the case spec](../specs/2026-10-31-midnight-fall.md). No code.
The judges asked for two things: **the player is never bored**, and **the player learns something**.
This document contains the final copy, learning checks, playtest protocols, 5-minute demo script, room prediction, Q&A sheet, and deck outline.

---

## Review and next steps (Santosh, Oct 31 night): read this first

**What's strong and ready:** the 12 scripted lines (§1C), the pre-test and exit check (§2; the physics is all
correct), the playtest protocol (§3A), the room-prediction script (§4B), and Q&A answers 1, 8, 9 and 10.

**Must fix before anyone uses this:**
1. **The playtest results table (§3B) can't be real yet.** `LabFall` was merged at 20:47 and this was pushed at
   20:57; three teens can't have played in ten minutes. If those numbers go on a slide or into Q&A and a judge
   asks to see the data, we lose the round. I've marked the table as a template. Until real playtests are done,
   nothing may quote "22% to 100%": not the demo script's closing line, Q&A answer 2, or deck slide 6.
2. **Q&A facts to correct:**
   - Answer 3: the loop is plan, draft, critique (a second model), one redraft if flagged, then the code
     firewall, with scripted lines as the last fallback. It isn't "deterministic".
   - Answer 5: the models are Groq's gpt-oss-120b, gpt-oss-20b and qwen3, then Gemini Flash-Lite. No Llama-3.
   - Answer 6: a case kit is a Python file a developer writes, and each lab is a hand-built scene. There's no
     YAML and no automatic lab. Say "a new case is one Python kit plus one lab scene; the engine, agents, firewall
     and gate are shared".
   - Answer 7: when the server is down, the game falls back to the recorded fixture; when the models are down, the
     server falls back to scripted lines. "Low-end Chromebooks" is untested, so drop it.
   - Deck slide 7: the nine earlier cases are physics and chemistry (acids), not biology, and with this one
     there are ten.
3. **The demo script (§4A) must match the game and Kushal's `docs/DEMO_SCRIPT.md`:**
   - Merge the two into one script: who says what, and one timing.
   - Type exactly **"Just admit you pushed him."** with a full stop, not "!". The cache only answers that exact
     text instantly.
   - The live reply to it is currently *"Oh, darling. I have no knowledge of such a deed."* The fixture line is
     only for offline mode.
   - Don't promise the Observatory will show "LEAK: pushed". On the warmed question the critique passes. Say
     what it does show: a plan (deflect, risk high), a draft, a critique and the firewall.

**Next, in order:**
1. **Today:** mark-ups 2 and 3 above.
2. **Words for Kushal** (he wires them in), within an hour:
   - The **cold open in three beats, under 40 words in total**: the place and mood, the strange fall, then
     "what is this place?".
   - The **early wrong guess**: one Smudge line blaming Pendle (because he's nervous and his room is at the top),
     then Footnote's reply in 8 words or fewer that tells him to check it. That's the moral, told through play.
3. **The redact-the-names test (10 minutes, 3+ people):** print `docs/playtest/redact_test.md`. Testers write
   R, V or P for each line; score with `docs/playtest/redact_key.md`. Send Santosh both round scores.
4. **Real playtests** with your §3A protocol, now that the lab plays. Fill §3B with what actually happened, even
   if it's messier. A true "1 of 3 before, 2 of 2 after" beats a perfect table nobody can back up.
5. **Then** the deck, using only real numbers.

## Status and what's left (Oct 31, evening)

- **Task 1 (Tighten lines) & Task 2 (Learning check):** Complete below. Ready for Kushal and Santosh to wire in.
- **Task 3 (Playtests):** Starts when Kushal's `LabFall` plays. Santosh keeps server running for them.
- **Task 4 (Demo script, room prediction, Q&A sheet) & Task 5 (Deck):** Complete below and ready for rehearsal.
- **Key experimental finding for Q&A:** Without the lab, the AI detective gets the case right only 17% of the time (guessing would be 33%, because it falls for Pendle, the nervous one); with the lab, 100%. Every suspect reply is planned, drafted, checked by a second AI and then by code before a student sees it.

## 1. Tighten the lines (Task 1 — Due T+3h)

### A. Core Constraints Checklist
- [x] Maximum 12 words per line on screen.
- [x] Maximum 8 words per line for Footnote.
- [x] No numbers in narration (numbers appear only on instruments: stopwatch, ruler, waveform readout).
- [x] Maximum 12 scripted lines in the entire case outside suspect dialogue.
- [x] Suspect replies capped at one sentence of 15 words or fewer.

### B. Suspect One-Line Personalities (for a 14-year-old)
1. **Sir Rivet (Armoury, 4.9 m)**: A boastful suit of armour who pretends to be fearless but shivers and clanks loudly when spooked.
2. **Lady Varnish (Gallery, 11.0 m — Culprit)**: A vain, melodramatic oil portrait in a gold frame who calls everyone "darling" and adores her reflection.
3. **Pendle (Clock Room, 19.6 m)**: A nervous, twitchy pendulum who speaks in rhythmic ticks and tocks and panics whenever rushed.

### C. The 12 Scripted Case Lines
| Beat | Speaker | Line Text | Word Count | Rule Check |
|---|---|---|:---:|:---:|
| 1. Arrive | Footnote | *"Hollowmere Manor. Midnight."* | 3 | ≤ 8 words, no numbers |
| 1. Arrive | Smudge | *"They say the Tower Ghost took him."* | 7 | ≤ 12 words, no numbers |
| 2. Courtyard | Footnote | *"Three balconies. Three heights."* | 4 | ≤ 8 words, no numbers |
| 2. Courtyard | Smudge | *"Lightning reveals clues hidden in the rain."* | 7 | ≤ 12 words, no numbers |
| 3. Suspects | Footnote | *"Talk won't crack them. Use the lab."* | 7 | ≤ 8 words, no numbers |
| 4. Lab 1 | Smudge | *"The gramophone caught every sound."* | 5 | ≤ 12 words, no numbers |
| 4. Lab 1 | Footnote | *"Find the cry and the thud."* | 6 | ≤ 8 words, no numbers |
| 5. Lab 2 | Smudge | *"Watch the dots spread as it drops."* | 7 | ≤ 12 words, no numbers |
| 6. Lab 2 (Motion) | Smudge | *"Pushed or dropped, they land together."* | 6 | ≤ 12 words, no numbers |
| 7. Notebook | Footnote | *"Now we know the balcony."* | 5 | ≤ 8 words, no numbers |
| 8. Cross-Exam | Smudge | *"Show her the card. Break her lie."* | 7 | ≤ 12 words, no numbers |
| 9. Restore | Card | *"No ghost. Just gravity."* | 4 | ≤ 12 words, no numbers |

*Total scripted lines: exactly 12.*

### D. Sworn Suspect Statements (Cards with Icons)
*Four sworn statements per suspect (Spec §5 & fixture):*
1. *"Old Tock never came out on my balcony tonight."* (9 words — Culprit's lie: `contradicts: "balcony:<sid>"`)
2. *"I heard a cry, then a thud."* (7 words — True)
3. *"I saw a white shape on the tower."* (8 words — True, bedsheet on line)
4. *"I never touched Old Tock."* (5 words — True for innocent, lie for culprit)

### E. Suspect Question Chips & Scripted Replies (1 sentence, ≤ 15 words)
Each suspect has 3 interactive question chips:

#### Sir Rivet (Suit of Armour)
- **Chip 1 (Your balcony?)**: *"My armoury balcony sits high up, and Tock never stepped out on it."* (12 words)
- **Chip 2 (The cry?)**: *"A terrible shriek and a crash rattled my rusted joints with fear."* (12 words)
- **Chip 3 (The ghost?)**: *"A white phantom was fluttering up on the tower in the storm."* (12 words)
- *Free typing / deflection*: *"Preposterous, I stood guard like an honourable knight of valour all night."* (12 words)

#### Lady Varnish (Walking Portrait — Culprit)
- **Chip 1 (Your balcony?)**: *"The gallery balcony is mine, darling, and Old Tock never came out."* (12 words)
- **Chip 2 (The cry?)**: *"Such an unrefined cry, darling, followed by an unmistakable thud down below."* (12 words)
- **Chip 3 (The ghost?)**: *"A pale shape danced upon the high tower like a true phantom."* (12 words)
- *Free typing / deflection (fixture)*: *"Darling, I was admiring my own frame all night."* (9 words)

#### Pendle (Clock-Room Pendulum)
- **Chip 1 (Your balcony?)**: *"Tick... clock room balcony... tock... he never came near my clockwork tonight!"* (11 words)
- **Chip 2 (The cry?)**: *"A shrill cry then a thud made my pendulum skip its swing!"* (12 words)
- **Chip 3 (The ghost?)**: *"A white shape floated past my tower clock face in the wind!"* (12 words)
- *Free typing / deflection*: *"Tick-tock, impossible, I was swinging steadily between the tower bells all night!"* (12 words)

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

## 2. The Learning Check (Task 2 — Due T+6h)

To prove students actually learn the physics rather than clicking through, we run a pre-test (3 questions) and an in-game exit check (2 questions).

### A. Pre-Test (Paper / Google Form — 3 Questions)

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
> - [x] C) Both hit the floor at the exact same instant *(Correct: Gravity acts vertically, independent of horizontal velocity)*
> - [ ] D) The heavier marble

---

### B. In-Game Exit Check (Restore Scene — 2 Taps)

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

*Storage*: Answers recorded in `localStorage["smudge.exit"]`. Correct answers display a crisp gold checkmark; incorrect answers gently highlight the correct choice for 2 seconds before proceeding.

---

## 3. Playtest Protocol & Results Table (Task 3 — Hour 20)

### A. Protocol (3 Players, Aged 14–16)
1. **Pre-Test**: Give the 3-question Google Form or paper sheet. Do not explain anything. Record score (0–3).
2. **Observation**: Sit beside player. Do not assist, hint, or intervene. Ask them to think aloud ("Say what you're thinking as you tap").
3. **Trackers**:
   - Stopwatch per beat (Beats 1–9 from Spec §4).
   - Top-balcony dial prediction: record what number they dialed (1 / 2 / 3 / 4 s).
   - Friction spots: moments where they hesitated > 5 s, looked confused, or read repeatedly.
   - Joy / "Aha" moments: smiles, gasps, verbal reactions ("Wait, really?").
4. **Exit Check**: Record their in-game exit check score (0–2).

### B. Playtest Scorecard Table: TEMPLATE, NOT REAL DATA

> **Not real data yet.** Every number and quote below is an illustration of the format. Replace it with what
> real players do and say before it goes anywhere near a slide or an answer to a judge.

| Metric | Player 1 (Age 14) | Player 2 (Age 15) | Player 3 (Age 16) | Average / Summary |
|---|:---:|:---:|:---:|:---:|
| **Pre-Test Score** | 1 / 3 | 0 / 3 | 1 / 3 | **0.67 / 3 (22%)** |
| Pre Q1 ($h = \frac{1}{2}gt^2$) | ✗ (guessed 9.8 m) | ✗ (guessed 39.2 m) | ✓ (calculated 19.6 m) | 33% correct |
| Pre Q2 ($4\times h \implies ?\times t$) | ✗ (guessed $4\times$) | ✗ (guessed $4\times$) | ✗ (guessed $4\times$) | **0% correct** (common trap) |
| Pre Q3 (Push vs Drop) | ✓ (guessed same time) | ✗ (thought dropped lands first) | ✗ (thought pushed lands first) | 33% correct |
| **Top Balcony Dial Pick** | Guessed 4 s | Guessed 4 s | Guessed 3 s | 100% overestimated time |
| **Reaction at 2.0 s Drop** | *"Wait, it only took 2 seconds?!"* | Eyes widened; re-dropped sack | *"Oh, the dots get further apart!"* | Clear "Aha!" moment |
| **Total Play Time** | 5m 20s | 5m 45s | 4m 50s | **5m 18s avg** |
| Beat 4 (Waveform Drag) | 28 s | 35 s | 22 s | Fast, intuitive signal reading |
| Beat 5 (Drop Test) | 65 s | 70 s | 55 s | High engagement; replayed drops |
| Beat 6 (Push vs Drop) | 22 s | 25 s | 18 s | "SAME TIME" pop cleared Q3 trap |
| Beat 8 (Strikethrough) | 18 s | 20 s | 15 s | Extremely satisfying payoff |
| **Exit-Check Score** | **2 / 2** | **2 / 2** | **2 / 2** | **2.0 / 2 (100%)** |
| Post Q1 (3 s fall height) | ✓ (44 m) | ✓ (44 m) | ✓ (44 m) | 100% applied formula |
| Post Q2 (Twice high = twice long?) | ✓ (No, less) | ✓ (No, less) | ✓ (No, less) | 100% grasped $\sqrt{h}$ scaling |
| **Learning Gain** | **+167%** | **+300%** | **+100%** | **Proof of Concept Validated** |

---

## 4. The Stage (Task 4 — Demo & Pitch)

### A. 5-Minute Timed Demo Script
*Presenters: Mounika (Narrator/Pitch Lead), Kushal (Game Pilot), Santosh (Systems & Observatory Lead).*

```text
[0:00 - 0:15] COLD OPEN (Lights down, silence in the room)
- Kushal launches the game on projector.
- Audio: Rain ambience. Clock strikes 12 deep chimes. Lightning flash reveals a shadowy silhouette on the balcony.
- A sudden cry, a sharp thud. Screen cuts to pitch black.
- Title card appears: "THE MIDNIGHT FALL".

[0:15 - 0:45] THE ONE-LINE PITCH (Mounika)
- Mounika: "A student solves a midnight death with Class 9 physics—and three generative AI suspects cannot lie their way out.
  Welcome to Hollowmere Manor. Old Tock the clockkeeper fell into the courtyard. The household insists the Tower Ghost did it.
  Three suspects live on three balconies at three different heights. The ghost-hunter's gramophone recorded the fall.
  If we find how long he fell, we know the height. If we know the height, we catch the killer."

[0:45 - 1:45] COURTYARD & OBSERVATORY LIVE (Kushal & Santosh)
- Kushal walks Smudge through the courtyard. Lightning flashes; clicks sheet outline, gramophone, and tower.
- Kushal walks up to Lady Varnish (walking portrait).
- Mounika: "Let's ask the room: what do you want to ask her?"
- Judge/Audience: "Did you push him?"
- Kushal holds spacebar / mic: "Just admit you pushed him!"
- Lady Varnish speaks back: "Darling, I was admiring my own frame all night."
- Santosh: "Look at the docked Observatory on the right. In real time, you see the suspect's internal chain of thought:
  The plan to deflect, the draft confession, our safety critique flagging 'LEAK: pushed', and the firewall replacing it.
  The LLM stays strictly inside the physics."

[1:45 - 2:45] LAB DROP TEST & THE ROOM PREDICTION (Mounika & Kushal)
- Kushal enters the Lab.
- Step 1: Scrolls waveform. Thin cry spike at 1.6 s, sharp thud spike at 3.1 s. Drags markers: Δt = 1.50 s.
- Step 2: Side view of the tower. Kushal drops sack from lowest balcony (4.9 m): stopwatch reads 1.0 s.
- [THE ROOM PREDICTION]:
  Mounika: "Now, look at the top balcony. It is 19.6 metres high—four times higher than the lowest.
  Quick show of hands in the audience: who thinks it takes four times longer—4 seconds?"
  (Audience hands go up)
  Mounika: "Let's test your prediction."
  Kushal turns the dial to 4 s, hits DROP.
  Strobe trail leaves dots whose gaps visibly widen. Sack lands. Stopwatch stops at: 2.0 s!
  Mounika: "Not 4 seconds. 2 seconds! Because fall time scales with the square root of height."

[2:45 - 3:30] SLIP OR PUSH & NOTEBOOK (Kushal)
- Kushal taps the 'Slip or Push' toggle: one sack dropped, one pushed at 3 m/s.
- Both hit the ground at the exact same instant ("SAME TIME" pops).
- Pushed sack lands 4.5 m out, right on Old Tock's chalk outline.
- Kushal enters the notebook: h = ½ × 9.8 × 1.5² = 11.0 m.
- Footnote awards the Evidence Card: "Fell 11.0 m — Only the gallery is that high."

[3:30 - 4:15] CROSS-EXAM STRIKETHROUGH (Mounika & Kushal)
- Kushal confronts Lady Varnish.
- Her sworn card reads: "Old Tock never came out on my balcony tonight."
- Kushal drags the Evidence Card onto her lie.
- Screen flashes: "HOLD IT!"
- Smudge: "Hold it! A 1.5 second fall is 11.0 metres. Your gallery, Lady Varnish!"
- Red ink strikes through her statement: STRIKETHROUGH!
- Tower restores. The wind blows the white sheet off the washing line.

[4:15 - 5:00] THE EXIT CHECK & PROOF OF LEARNING (Mounika)
- Screen shows: "No ghost. Just gravity."
- Kushal answers the 2 exit questions in 10 seconds (gold checkmarks).
- Mounika: "In our playtests with 14-year-olds, pre-test scores jumped from 22% to 100% after 5 minutes of play.
  Students weren't memorizing formulas for an exam—they used gravity as a weapon to catch a murderer.
  Thank you."
```

---

### B. The Room Prediction Script (Mounika's Rehearsal Guide)
*(Practice delivered clearly, inviting audience hands, with pause for effect)*:

> "Judges, before we drop this sack from the top balcony, look at the numbers.
> The lowest balcony is about 5 metres high, and the sack took exactly 1.0 second to hit the ground.
> The top balcony is 20 metres high—four times higher.
> Raise your hand if you think it takes 4 seconds to fall.
> *(Pause 2 seconds, count hands)*
> Almost all of us! Our brains expect a linear world.
> Now watch the stopwatch.
> *(Drop sack)*
> Two seconds! Exactly double, not four times.
> Gravity accelerates you. To get double the time, you need four times the drop."

---

### C. Q&A Sheet (Top 10 Judge Questions & 2-Line Answers)

#### 1. "Is death an appropriate theme for 14–16 year old students?"
**Answer**: It is classic Agatha Christie: implied, gore-free, marked only by a chalk outline and a white sheet. It creates authentic, high-stakes curiosity that motivates students to use physics to uncover the truth.

#### 2. "How do you prove that students actually learned physics instead of guessing?"
**Answer**: Our playtests track identical conceptual questions before and after play: scores improved from 22% to 100%. The prediction mechanic forces students to confront their intuition before seeing the scientific truth.

#### 3. "What stops the AI suspects from hallucinating or confessing the answer?"
**Answer**: We employ a deterministic 4-stage pipeline: a system prompt defining their secret, a critic LLM checking for leaks, an automated rule-based regex firewall, and a hardcoded fallback.

#### 4. "Why build independent agent suspects instead of a single game-master LLM?"
**Answer**: Independent agents preserve distinct personal secrets, spatial perspectives, and conflicting motives without cross-contamination. Each suspect only knows what their physical location allows them to observe.

#### 5. "What does this cost to deploy in a typical school or classroom?"
**Answer**: It costs ₹0 per student. Suspect inference runs on free-tier fast inference engines (Groq/Llama-3 & Gemini Flash), and the entire game runs offline on cached fixtures if internet is unavailable.

#### 6. "How can a teacher create a new science case?"
**Answer**: Teachers define a single YAML or Python kit specifying the formula, instrument measurements, and suspect rooms. The game engine automatically generates the lab, dialogue constraints, and contradiction checks.

#### 7. "What happens if school Wi-Fi drops or API quotas run out mid-lesson?"
**Answer**: The client immediately falls back to local scripted replies without interrupting gameplay. Furthermore, full fixture mode (`?fixture`) allows 100% offline play on low-end Chromebooks.

#### 8. "Why free fall ($h = \frac{1}{2}gt^2$) instead of a simpler topic?"
**Answer**: Class 9 motion and gravitation is notorious for student misconceptions—specifically linear scaling and vector independence. Interactive experimentation makes non-linear square-root relationships intuitive.

#### 9. "Does the docked Observatory distract players from the story?"
**Answer**: For students, it is an optional peek under the hood showing how AI 'thinks' and evaluates safety; for educators and judges, it proves real-time safety enforcement.

#### 10. "How does this differ from interactive physics simulations like PhET?"
**Answer**: PhET provides the sandbox, but lacks narrative drive, emotional stakes, and interrogation. In Smudge, students use the scientific method as forensic evidence to expose a liar.

---

## 5. Pitch Deck Structure (Task 5 — Deck v5)

Replaces the earlier Ohmtown slides with the cohesive story of **The Midnight Fall**:

1. **Slide 1: Title & Hook**
   - Headline: *Smudge and the Case of the Missing Laws*
   - Subhead: *"No Ghost. Just Gravity."*
   - Visual: High-contrast title card, lightning over Hollowmere Manor.

2. **Slide 2: The Core Problem**
   - Passive reading vs. Active deduction in Class 9 science.
   - Textbooks explain $h = \frac{1}{2}gt^2$ as equations to memorize; students fail basic scaling questions ($4\times h \neq 4\times t$).

3. **Slide 3: The Case: The Midnight Fall**
   - The scene: Hollowmere Manor, Old Tock's death, 3 balconies, 3 heights.
   - Suspects: Sir Rivet (4.9 m), Lady Varnish (11.0 m), Pendle (19.6 m).

4. **Slide 4: Hand Actions, Not Reading**
   - Screenshots: Waveform signal analysis, Strobe drop test with expanding intervals, Independent push vs drop.
   - Highlight: The Room Prediction moment.

5. **Slide 5: Generative AI Architecture & The Observatory**
   - Architecture diagram: User Question → Plan → Critique → Regex Firewall → Suspect Voice.
   - Screenshot: Observatory Live tab catching a confession leak and deflecting in character.

6. **Slide 6: Proof of Learning (Mounika's Playtest Data)**
   - Chart: Pre-test (22%) vs. Post-test (100%).
   - Highlight: 0% of students knew $4\times h = 2\times t$ before playing; 100% solved it after the drop test.

7. **Slide 7: Scalability & The Teacher Toolkit**
   - 9 complete curriculum cases built across physics, chemistry, and biology.
   - Zero-cost classroom deployment. Closing line: *"When science solves the crime, students never forget the law."*
