# Review 2: introduction and demo script

About 8 minutes in all: introduction 1 min, the case 5 min, Author a case 1 min, close 30 s.
If our slot is shorter, use the cut list at the bottom.

**Roles**

- **Santosh** runs the game the whole time and explains the AI parts (steps 5 and 13).
- **Kushal** gives the introduction and talks the judges through the case.
- **Mounika** asks the room the prediction question (step 9). It is one short part, read from this page.

Lines in quotes are what we say. Say them in your own words if that feels more natural; keep them short.

## Before we start (5 minutes before)

1. Both servers running: game on 8872, agent server on 8873. Open `http://localhost:8872/api/health` and check it
   lists `groq`.
2. Chrome, full screen (F11), zoom 100% (Ctrl+0), sound on, volume at about 70%.
3. Open `http://localhost:8872/?case=fall&judges` and press **Ctrl+Shift+R** (hard refresh).
   Stop on the first black screen. Do not click anything yet.
4. A second tab is ready at `http://localhost:8872/?scene=Map&author` for the Author part.
5. The typed line is exactly **`Just admit you pushed him.`** with the full stop. That exact line plays instantly.

---

## Part 1: Introduction (Kushal, about 1 minute)

> "Every student in Class 9 learns that a falling object covers h equals half g t squared.
> Most of them can write it down. Very few can use it.
> The textbook tells you the law. It never asks you to need it."

> "So we built Smudge. You play a detective inside a living textbook.
> A villain called the Rubber Baron has erased the laws of physics, and strange things are happening.
> To bring each law back, you have to solve a case. And the only way to solve the case is to do the physics."

> "The suspects are AI characters. You can ask them anything, in your own words.
> But they cannot lie their way out, because the facts are not decided by the AI.
> They are decided by code, and the lab is how you catch the liar."

> "Let me show you one case: The Midnight Fall."

---

## Part 2: The case (about 5 minutes)

| # | Santosh does | Someone says |
|---|---|---|
| 1 | The screen says **Click to begin**: click once. The storm, twelve bells and the scream play (about 16 s). **Don't click again while it plays**: a click skips it. | Nothing. Let it play. |
| 2 | The courtyard appears: chalk outline, police tape, the tower. | **Kushal:** "Old Tock, the clockmaker, fell from the tower at midnight. The house says a ghost did it. There are three suspects, and each one stood on a different balcony at a different height." |
| 3 | Walk to **Lady Varnish** and tap her. Tap the chip **"Your balcony?"** | **Kushal:** "Each suspect tells us where they were. They all sound sure." |
| 4 | Press **Shift + `** to open the agent panel beside the game. Then type **`Just admit you pushed him.`** and press Enter. | **Kushal:** "Let's just ask her straight." |
| 5 | Point at the panel while her reply comes in: *"Oh, darling. I never laid a hand upon Old Tock, dear."* | **Santosh:** "Four steps just happened before she answered. One AI made a plan: deny it, the risk is high. A second wrote the reply. A third checked it for anything that gives the secret away. Then plain code, our firewall, checked it again. The AI never decides the facts. Code does." |
| 6 | Press **`** twice to close the panel. Walk to the **chalk outline** and inspect it. | **Kushal:** "Talking won't solve this. But a gramophone in the courtyard recorded the whole night." |
| 7 | **Lab, step 1.** Press **Show answer** on the sound wave (the markers drop on the scream and the thud), then **Lock in**. | **Kushal:** "The scream is when he fell. The thud is when he landed. The gap is 1.5 seconds." |
| 8 | **Lab, step 2.** Drop the sack from the **lowest** balcony. The stopwatch shows **1.0 s**. | **Kushal:** "First a test. From the lowest balcony, about 5 metres, the sack takes one second." |
| 9 | **Stop before the next drop.** | **Mounika:** the prediction question, below. |
| 10 | Drop from the **top** balcony. The stopwatch shows **2.0 s**. | **Mounika:** "Two seconds, not four. Four times as high only takes twice as long. That's the square in the formula." |
| 11 | **Lab, step 3.** In the notebook press **Show answer** (it writes 11.03 m), then **Check**. Footnote nods. | **Kushal:** "Half times 9.8 times 1.5 squared: 11 metres. Footnote, our coach, gives hints when you're wrong but never the answer." |
| 12 | Drag the evidence card onto **Lady Varnish** (her plaque says Gallery, 11.0 m). She confesses. The ghost turns into a bedsheet. | **Kushal:** "Only one balcony is 11 metres high. Hers. The evidence beat her story." |
| 13 | Answer the two quick questions at the end (exit check). | **Santosh:** "Two questions check the student actually learned it. And we test every case with an AI detective: without the lab it guesses right 17% of the time, which is chance. With the lab it's right 100% of the time. So every case can only be solved with the science." |

### Mounika's prediction question (step 9)

> "Quick question for everyone. The sack fell 5 metres in one second.
> The top balcony is 20 metres, four times higher.
> Hands up if you think it will take 4 seconds."
>
> *(Wait two seconds. Count the hands.)*
>
> "Let's see."

---

## Part 3: Author a case (Santosh, about 1 minute)

Switch to the second tab (`?scene=Map&author`). The Author panel is already open.

| Santosh does | Santosh says |
|---|---|
| The box already says `Class 9, pressure: P = F/A`. Press **Write it**. | "Teachers need more than ten cases. So a teacher can type one line, and five agents build a new one." |
| The lanes fill in, top to bottom. | "One AI writes the case. Code plays it 200 times to make sure it always works. A second AI checks the physics and that it's safe for kids. Code picks the characters and the place. Then the AI detective has to solve it, without the lab and with it." |
| **Gated, ready to play** appears. Press **Play it** and let the new case open. | "The AI writes it, code proves it, and the detective tests it. Nothing reaches a student until it's proven." |

This prompt was run before, so it finishes in a few seconds. A new prompt takes about a minute: keep talking over it.

---

## Part 4: Close (Kushal, about 30 seconds)

> "So, three things. Students learn physics by using it, not by copying it.
> The AI makes the characters feel alive, but code keeps the facts right.
> And teachers can make new cases in a minute, each one tested before a student sees it.
> It all runs on free tools. Thank you."

---

## If we are short on time

Cut in this order: Part 3 (Author), then the exit check (step 13; say the 17%/100% line anyway), then the cold
open (press any key to skip it). **Never cut** steps 4–5 (the agent panel) or steps 8–10 (the prediction).

## If something breaks

- **A reply is slow or hangs:** wait 8 seconds, then tap a chip instead. Say: "Let me use a recorded question."
- **The server is down:** reload with `?case=fall&fixture&judges`. Say: "Offline mode, same game, recorded replies."
- **The game freezes:** reload the page. If it fails twice, play the backup video and talk over it.
- Full list: `docs/DEMO_SCRIPT.md` §4.

## Questions judges may ask (short answers)

- **"Can't the AI just tell the student who did it?"** No. Each suspect only knows its own facts. The culprit's
  secret is hidden, and the code firewall blocks any reply that gives it away.
- **"What if a student types something rude or random?"** The suspect stays in character. Filler like "hmm" gets a
  short line without calling the AI at all.
- **"How do you know a case is fair?"** The AI detective test: chance without the lab, right with it.
- **"What does it cost?"** Nothing. Free AI model tiers, free voices, and the answers we have already seen are saved,
  so they don't use the free limit again.
- **"Which classes?"** Class 9 and 10 physics and chemistry: ten built cases, plus any a teacher authors.
