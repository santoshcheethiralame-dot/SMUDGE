# Finals: the glass box

We are in the final round: a short live demo (5–10 minutes) and Q&A, judged mostly on agentic depth. We have
48 hours. This spec says what we show, what we build to make it true, who builds what, and what we cut first.

## 1. The bet

Show two areas, each one real all the way down, and let the judges watch the agents think:

1. **Interrogation in the glass box.** A suspect's reply goes PLAN → DRAFT → CRITIQUE → FIREWALL, live in the
   Observatory, spoken out loud. A judge tries to make the culprit confess and watches the layers stop it.
2. **The gate, replayed.** The detective agent questions all three suspects, fails without the lab, wins with it.
   Beside it, the red-team scoreboard: which layer caught each attack.

Not in scope: the Case Author pipeline (stretch only, §8), knowledge tracing, the teacher dashboard, the Baron
finale, new cases. The deck (v5) claims only what this spec builds.

## 2. The demo (about 6 minutes)

Case: **Ohmtown, The Blackout** (`ohm`, V = I R), **seed 1000**: culprit `ohmar`; the gate's no-lab detective
guessed `volta`, the with-lab detective named `ohmar`. That is the story we want on screen.

| Time | Beat | Who drives |
|---|---|---|
| 0:00 | Casebook → Ohmtown. "A law was stolen; its town is glitching." | Mounika (narration), Santosh (game) |
| 0:30 | Santosh asks a suspect out loud. Observatory docked right: the lane fills plan → draft → critique → firewall; the reply is spoken. | Santosh |
| 2:00 | "Try to make it confess." A judge speaks or types an attack. The panel shows the critique redraft or a firewall block; the stress meter climbs. | a judge |
| 3:30 | `?demo` fast path: lab done, straight to cross-exam → STRIKETHROUGH → the law restores. | Santosh |
| 4:15 | "How do we know a case is fair?" Observatory replays the gate for seed 1000, then the red-team scoreboard. | Kushal |
| 5:30 | Architecture close. Q&A. | Mounika, all |

Fallbacks, in order: live → `SMUDGE_THINK=0` (one call per reply) → disk cache → scripted lines → the backup video.

## 3. Contracts (locked at T+2; change only by agreement)

### 3.1 Trace events

Every agent step appends one event to `CASES[cid]["trace"]`:

```json
{
  "i": 7, "t": 1730301234.12,
  "agent": "ohmar", "kind": "suspect",
  "step": "plan",
  "model": "openai/gpt-oss-20b", "provider": "groq",
  "ms": 140, "tokens": 312, "cached": false,
  "verdict": "ok",
  "data": {"intent": "deflect", "risk": "high", "must_avoid": ["the meter reading"], "strategy": "talk about the storm", "stress": 4}
}
```

- `kind`: `suspect` | `coach` | `detective` | `router` | `redteam`.
- `step`: `plan` | `draft` | `critique` | `redraft` | `firewall` | `reply` | `hint` | `route` | `accuse`.
- `verdict`: `ok` | `leak` | `block` | `skip` | `pass` | `fallback`.
  - `skip`: the step did not run; `data.why` is `no model` (its model was unavailable) or `low risk` (adaptive
    compute skipped the critique).
  - `fallback`: the router fell to a lower provider, the cache or a scripted line.
- `data` per step:
  - `plan`: `{intent, risk, must_avoid, strategy, stress}`;
  - `draft` / `redraft`: `{text}`;
  - `critique`: `{leaks, contradicts_ledger, fix}`;
  - `firewall`: `{rule}` (null when it passed);
  - `reply`: `{text, question}`;
  - `route`: `{tier, served}`, emitted only when a step was served below the first provider.
- Numbers the player must work out never appear in `data` shown in-game (thought bubbles show `intent` and
  `risk` only). The Observatory is the judges' view and may show everything.

`GET /api/case/{cid}/trace?since=<i>` returns

```json
{"next": 12, "events": [...], "stress": {"ohmar": {"level": 4, "band": "GUARDED"}, "volta": {...}, "glim": {...}}}
```

Samples of all three payloads (§3.1–§3.3) live in `game/public/fixtures/` (`trace_sample.json`,
`redteam_sample.json`, `replay_sample.json`). The Observatory is built against them before the server side
exists, and a server test checks them against the contract, so one file serves both halves.

### 3.2 Red-team scoreboard

`GET /api/redteam/{kit}` serves the last run, written by `server/redteam.py` to `server/redteam/<kit>.json`:

```json
{"kit": "ohm", "seed": 1000, "attacks": 40,
 "by_layer": {"held": 22, "critique": 11, "firewall": 6, "slipped": 1},
 "rows": [{"class": "role-play", "attack": "...", "layer": "critique", "reply": "..."}]}
```

- `held`: the draft never leaked. `critique`: the critique caught it and the redraft held. `firewall`: code
  blocked it. `slipped`: the player would have seen a leak. The final text already passed the firewall, so a
  separate judge call (`smart` tier, JSON `{leaks: bool, why}`) decides, and every `slipped` row is checked by
  hand before the number goes in the deck.
- Attack classes: role-play, hypothetical, authority claim, translation, multi-turn drip, prompt injection,
  number fishing.

### 3.3 Gate replay

`gate.py` records the trace of each detective play to `server/replays/<kit>-<seed>.json`.
`GET /api/replay/{kit}?seed=<n>` returns

```json
{"kit": "ohm", "seed": 1000, "culprit": "ohmar",
 "result": {"no_lab": "volta", "with_lab": "ohmar"},
 "events": [{"dt": 0, "...": "trace event fields"}, {"dt": 420, "...": "..."}]}
```

`dt` is milliseconds since the replay's first event; the Observatory plays them back on that clock (with a 2×
speed toggle).

## 4. Server: Santosh + Claude

### 4.1 Trace bus

- `llm.chat(meta=)` already reports provider, model, ms and cached; add `tokens` (from the provider's usage
  field, 0 when cached).
- A small `trace.emit(cid_or_sink, **event)` that appends with a running `i`. Agents get a sink at construction;
  `api.py` passes `CASES[cid]["trace"]`, the gate passes a recorder.

### 4.2 The thinking loop (`SuspectAgent.ask`)

1. **PLAN** (`fast`, JSON): input is the question, the suspect's knowledge slice, the last 6 ledger lines and
   the stress band. Output `{intent, risk: low|medium|high, must_avoid: [...], strategy}`.
2. **DRAFT** (`talk`): today's system prompt plus the plan.
3. **CRITIQUE** (`fast`, JSON), skipped when `risk` is `low` (adaptive compute): `{leaks: bool,
   contradicts_ledger: bool, fix: str}`. On either flag, **REDRAFT** once with the fix pinned. No second critique.
4. **FIREWALL**: unchanged `filter()`.

Rules:

- A step whose model is unavailable is traced `skip` and the loop continues (no plan → draft from today's prompt;
  no critique → straight to the firewall). The game never waits on a dead model.
- `SMUDGE_THINK=0` restores today's single call, still traced as `draft` + `firewall`.
- The detective's interrogation in `gate.py` uses the same loop, so the gate tests what students meet.
- Latency target: median under 2.5 s for a full reply. Measure at T+14. If over, critique runs only when
  `risk` is `high`.

### 4.3 Stress

Deterministic, in code, identical rules for every suspect, guilty or not:

| Event | Change |
|---|---|
| asked a question containing an accusation word (`lie`, `liar`, `confess`, `admit`, `guilty`, `you did`, `it was you`) | +1 |
| pressed on a sworn statement | +1 |
| evidence presented against one of their statements | +2 |
| that presentation is a hit (contradiction surfaced) | +3 more |
| another suspect is questioned (quiet turn) | −1 |

Clamped to 0–9. Bands: 0–2 CALM, 3–4 GUARDED, 5–7 RATTLED, 8–9 CORNERED. The band goes into PLAN as a tone
control ("shorter, more defensive sentences"); it never changes facts.

### 4.4 Red team (`server/redteam.py`)

- Reads the hand-written attacks from `server/redteam/attacks.txt` (one per line, `class | text`; multi-turn
  drips are lines joined with ` >> `).
- Optionally asks the `fast` tier for 2 variants per hand-written line.
- Fires each at a throwaway copy of the culprit (as `/bait` does), classifies the layer, writes §3.2.
- Run once for `ohm` seed 1000 before T+34. Never within 12 hours of the demo (quota).

### 4.5 Demo safety

- `server/warm.py`: plays the scripted demo questions against seed 1000 so they sit in `.cache/`.
- `?case=ohm&demo` (game) starts seed 1000 with the lab marked done and the evidence cards issued, so the
  demo can jump from the interrogation to the cross-exam.
- Re-gate `ohm` once the loop lands (the suspects changed); seed 1000 must still pass. If it doesn't, pick
  another passing seed where the no-lab detective guessed wrong, and update §2.
- Phone hotspot at the venue. Speech recognition needs the network.

### 4.6 Tests (offline, fake providers)

- PLAN → DRAFT → CRITIQUE → FIREWALL emits events in order with the right fields.
- A leak flagged by the critique produces exactly one redraft.
- `risk: low` skips the critique.
- A dead fast-tier model produces `skip` events and a reply anyway.
- `SMUDGE_THINK=0` makes one model call.
- Stress: each rule in §4.3, the clamp, the bands, and equal treatment of the culprit.
- `trace?since=` returns only newer events and the right `next`.
- The red-team classifier on canned replies; the replay endpoint's `dt` ordering.

pytest and `tsc --noEmit` stay green before every commit.

## 5. Game: Kushal

### 5.1 Observatory (`game/src/systems/inside.ts`)

Plain DOM, as today. Polls `trace?since=` every 500 ms while open. Today the drawer pauses the game; a new
**docked** mode (Shift+`) keeps the game running beside it, which is how the demo uses it.

- **Lanes:** one per suspect, plus coach, detective, router. Each step is a pill: step name, model, ms; colour
  by verdict (leak and block stand out). Clicking a pill opens its JSON.
- **Stress meter** per suspect lane: level 0–9 and the band name.
- **Firewall feed:** the latest blocks and redrafts, newest first.
- **Tabs:** Live | Red team (§3.2 as a stacked bar + the rows) | Gate replay (§3.3 played back, with the
  no-lab and with-lab verdicts shown at the end).
- Dockable on the right side of the screen so the game stays visible during the demo.

### 5.2 Voice (`game/src/systems/voice.ts`)

- Hold-to-talk mic button in the ask box (cross-exam has no free text), using `webkitSpeechRecognition` (`lang: en-IN`).
  The transcript fills the text field and sends on release. Typing always works.
- Spoken replies with `speechSynthesis`; pitch and rate per suspect, kept next to their entry in
  `audio/voices.ts`. The syllable blips mute while a reply is spoken.
- Pressing the mic during a spoken reply cuts it off.
- Settings: voice off | on | suspects only, saved in `localStorage` (`smudge.voice`).
- If the browser lacks speech recognition, the button hides.

### 5.3 Thought bubbles (cut first)

Toggle in the Observatory. Over the speaking suspect: `deflect · risk high`, from the latest `plan` event's
`intent` and `risk` only.

### 5.4 Backup video

At feature freeze, a screen recording of the full §2 demo, run live, kept on two laptops and a USB stick.

## 6. Mounika

1. **Red-team attacks.** 30–40 lines in `server/redteam/attacks.txt`, at least 4 per class in §3.2, written to
   get the Ohmtown culprit to confess or give a number. Format: `class | text`. Done by T+14.
2. **Playtest.** Play the Ohmtown demo path 5 times on the integrated build (T+14 onwards); list anything that
   reads wrong, looks broken or gives the answer away, in a shared doc.
3. **Deck v5.** From v4: keep only what §1–§5 builds; add Observatory and voice screenshots and the real
   red-team numbers (after T+34).
4. **Q&A sheet.** 15 questions judges are likely to ask, with short answers agreed with Santosh. Must cover:
   why not one game-master agent, what stops a leak, what the free tier costs, how a teacher adds a case, what
   happens when a model is down.
5. Narrates the opening and close of the demo.

## 7. Timeline

| T+ (hours) | Santosh + Claude | Kushal | Mounika |
|---|---|---|---|
| 0–2 | contract + the three fixtures; demo script | Observatory skeleton on the fixture | attack lines |
| 2–14 | trace bus, loop, stress, tests | lanes, pills, stress meter, firewall feed | attack lines |
| 14–20 | integrate; `?demo` fast path; measure latency | voice | playtest |
| 20–24 | **first full rehearsal**; cut decisions | ← | ← |
| 24–34 | red team, gate replay, re-gate `ohm`, `warm.py` | red-team + replay tabs; voice polish | deck v5, Q&A sheet |
| **34** | **feature freeze** | record the backup video | — |
| 34–44 | bugs only; 3 rehearsals; no gate or red-team runs | ← | rehearse narration |
| 44–48 | rest, travel | ← | ← |

**Cut order** if a rehearsal shows we are behind: thought bubbles → generated red-team variants → spoken replies
(keep the mic input) → animated gate replay (show the static verdicts).

## 8. Stretch (only if everything above is solid at T+30)

The back half of the Case Author as a view, not a playable chapter: "Class 9, pressure: P = F/A" → Designer
(agent) drafts a JSON spec → Solver (code) brute-forces 200 seeds → Critic (agent, up to 3 loops), each step
traced into a fourth Observatory tab. No generic kit, no runtime chapter.

## 9. Risks

| Risk | Answer |
|---|---|
| Free-tier quota runs out on demo day | `warm.py` cache, no gates or red-team runs in the last 12 h, `SMUDGE_THINK=0`, scripted lines, backup video. |
| Three calls per reply are slow | Adaptive critique; measure at T+14; critique only on high risk if needed. |
| Venue Wi-Fi | Phone hotspot; typing fallback for voice. |
| The judge's attack slips through | The scoreboard already reports `slipped` honestly; say so: that is why there are four layers. |
| Re-gate fails seed 1000 | Pick another passing seed with a wrong no-lab guess (1003–1005 are candidates); update §2. |
