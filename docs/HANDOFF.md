# Smudge: team handoff

Read this first. It covers what the game is, how to run it and how it is built.

**Finals:** what we are building now is in [WORK_SPLIT.md](../WORK_SPLIT.md) and the
[finals spec](superpowers/specs/2026-10-30-finals-design.md). They replace the plan in §9.

## 1. What Smudge is

*Smudge and the Case of the Missing Laws* is our education-track agentathon entry (Team Strikethrough, PES
University). It is a detective game for 14–16 year olds.

**The story.** A science law has been stolen from a living textbook, and its district is glitching. The player
is Smudge, an ink-blot detective.

**The player's loop:**

1. Question three AI suspects. Each suspect is its own agent with its own secret.
2. Take real measurements in the lab and do the maths.
3. Present evidence against the one sworn statement that is a lie: **STRIKETHROUGH**.
4. The law writes itself back.

**The 9 cases** (the casebook ends at 9):

| # | Kit | District | Law | Suspects |
|---|---|---|---|---|
| 1 | `density` | the Bay | ρ = m / V | karat, cyl, bob |
| 2 | `motion` | Motion Mesa | v² = u² + 2as | dash, rolla, mu |
| 3 | `sound` | the Valley | d = v t | reverb, thump, coil |
| 4 | `heights` | Lumen Heights | tan θ = h / s | lumen, vane, sola |
| 5 | `refraction` | Prism Port | n = sin i / sin r | frost, pane, geo |
| 6 | `ohm` | Ohmtown | V = I R | volta, ohmar, glim |
| 7 | `heat` | Kelvin Springs | Q = m c ΔT | al, ferris, brewster |
| 8 | `acids` | Acid Alley | pH and dilution | citrine, bicarb, sudsy |
| 9 | `power` | Watt Works | P = m g h / t | cog, hoist, dynamo |

The shortlist deck is `Downloads\Strikethrough-Agentathon-v3.pptx`. It describes the features in §9 as if they
already exist, so building them is how we make the deck true.

## 2. Run it

**Keys.** Create `smudge/.env` with the two keys below. Never print it, paste it or commit it; it is in
`.gitignore`.

```
GROQ_API_KEY=...
GEMINI_API_KEY=...
```

**Start both halves in two terminals:**

```bash
cd server && python -m uvicorn api:app --port 8873
```

```bash
npm --prefix game run dev
```

- The game runs on http://localhost:8872. Vite proxies `/api` to port 8873; set `SMUDGE_API_PORT` to change that.
- In the Claude desktop app, the `game` and `server` entries in `.claude/launch.json` start the two halves.

**URL parameters:**

| Param | Does |
|---|---|
| `?case=<kit>` | Drops you straight into that case's district, e.g. `?case=ohm`. |
| `?scene=<Scene>` | Starts any scene: Title, HQ, Map, Bench, CrossExam, … |
| `?scene=Bench&kind=<instrument>` | Opens one lab instrument on its own, e.g. `kind=tape`. |
| `?judges` | Opens the judges' panel on load. The backtick key also toggles it. |

Solved cases are saved in `localStorage` (`smudge.solved`). Clear that key to start the casebook from scratch.

## 3. Architecture map

**server/** (Python, FastAPI)

| File | Role |
|---|---|
| `api.py` | Endpoints and in-memory case sessions (`CASES[cid]`). Routes: `/api/case/new`, `/ask`, `/press`, `/lab/check`, `/hint`, `/present`, `/case/{cid}/inside`, `/filtertest`, `/bait`. |
| `truth.py` | The truth engine. `new_case(seed, kit)` and `check_constraints`. Code decides every fact. |
| `kits/base.py` | The `Kit` contract: `generate`, `testimony`, `check_constraints`, `check_lab`, `solution`, `lab_report`, `knowledge`, `admits`, `leak_examples`, `scripted`. |
| `kits/<kit>.py` | One file per case. Auto-discovered. |
| `agents.py` | `SuspectAgent` (system prompt from its knowledge slice, then `ask`, `filter`, `press`), `Footnote` (the coach), `Detective` (the gate player). |
| `llm.py` | The model router: `PROVIDERS` (Groq gpt-oss-120b/20b, then Groq gpt-oss-20b and qwen3.8-27b as extra quota, then Gemini Flash-Lite), tiers fast/talk/smart, a disk cache in `.cache/`, and `chat(meta=)`, which reports the provider, model, whether it was cached, and the time in ms. |
| `gate.py` | The release gate. It writes passing seeds to `case_pool.json`. |
| `tests/` | pytest: the shared kit contract in `test_kits.py`, plus one test file per kit. |

**game/src/** (Phaser 3, TypeScript, Vite)

| File | Role |
|---|---|
| `scenes/Boot.ts` | Loads assets and handles the URL params. |
| `scenes/Title`, `Prologue`, `HQ`, `Map` | Front end. `Map` is the 9-chapter casebook. |
| `scenes/CaseLab`, `Lab`, `LabMotion`, `Bench` | The lab. `Bench` hosts one instrument. |
| `scenes/CrossExam`, `Restore` | The accusation and the law coming back. |
| `systems/district.ts` | The district scene: walking around and chatting with suspects. |
| `systems/dialogue.ts` | Typed dialogue boxes. |
| `systems/inside.ts` | The judges' panel. It becomes the Observatory (§9). |
| `systems/lab/instruments/*` | say, stopwatch, tape, protractor, gauge, dropper, tally, balance, notebook. |
| `cases/<kit>/index.ts` | One `CaseDef` per case: layout, scenery, lab steps, every line of dialogue. |
| `api.ts`, `state.ts` | Server calls and saved progress. |
| `audio.ts`, `audio/` | All sound, synthesised in Tone.js (§7b). |
| `systems/juice.ts`, `transition.ts`, `atmosphere.ts` | Game feel: hit-stop, squash, button feel; ink wipes and the chapter card; weather, birds, glitch tears (§7b). |

**art/**

| Folder | Role |
|---|---|
| `art/mascot` | 3D SDF rigs rendered to 64 px pixel art in 8 directions. Casts live in `src/cast/<kit>.py`. |
| `art/world` | District backdrops (`scene_*.py`), instruments, the casebook. |

**Request path for one question:**

1. The student asks.
2. The orchestrator (`api.py`) routes the question to that suspect's agent.
3. The agent is grounded in its knowledge slice from the truth engine.
4. The router generates the reply.
5. The firewall (`SuspectAgent.filter`) checks it.
6. The reply goes back to the student.
7. The call is logged for the judges' panel.

## 4. How the agents work today

- **Knowledge slices.** Each suspect sees only `kit.knowledge(case, sid)`: its own sworn statement, gossip and
  persona. The culprit also gets its secret.
- **The firewall** (`agents.py`, `SuspectAgent.filter`) is code, not a model. It blocks a reply for:
  - a confession;
  - the case's numbers;
  - anything `kit.admits` flags, such as the culprit's secret;
  - any suspect, guilty or not, pointing at another suspect ("maybe Hoist did it"). Only the culprit would want
    to deflect, so letting just innocents be blocked was a tell; every suspect's prompt also says nobody saw who
    did it.

  It also strips `*stage directions*`. When it blocks, `last_rule` names the rule that fired.
- **Coach (Footnote).** Given the lab step the student got wrong, it writes a targeted hint. `kit.check_lab`
  names the step.
- **Detective.** It interrogates all three suspects, writes its reason, then names a culprit. It plays once
  without the lab and once with it.
- **Router fallback order:** Groq gpt-oss-120b, then Groq gpt-oss-20b, then Groq qwen3.8-27b, then Gemini, then
  the disk cache, then `kit.scripted` lines. The game never stalls on a model.
  - Groq meters quota per model, so each extra model is free quota, and a 429 cools down only that model.
  - The small models stand in for suspects and the coach only. The gate's detective (`smart` tier) plays only
    on gpt-oss-120b or Gemini: as a stand-in, gpt-oss-20b misread plain lab results.
  - The cache key ignores the provider. If a weak model ever answers a tier it shouldn't, delete its rows from
    `.cache/` (each row records its `provider`).

## 5. Adding a case by hand

Follow [ADDING_A_CASE.md](ADDING_A_CASE.md). It covers the six files per case, the design rules and a table of
the 9 built cases.

## 6. Tests and gates

**Tests.** Both must be green before every commit:

```bash
cd server && python -m pytest tests -q
```

```bash
cd game && npx tsc --noEmit
```

- `pytest` runs 229 tests. They need no keys, because the fixture fakes the providers.
- The contract enforces one formatting rule: a sworn statement is at most 90 characters.

**Gate:**

```bash
cd server && python gate.py 6 <kit>
```

- **Pass bar:**
  - without the lab, the detective should score about chance (33–67% over 6 seeds);
  - with the lab, it must name the culprit.
- **Run one gate at a time.** One gate is about 12 detective plays, and the free tier runs out fast. If the models
  stop answering mid-gate, `gate.py` exits without touching `case_pool.json`.
- **Results so far:**

| Kit | No lab | With lab | Seeds in pool |
|---|---|---|---|
| density | 0.33 | 0.92 | 11/12 |
| motion | 0.33 | 1.0 | 9/9 |
| sound | 0.33 | 0.78 | 7/9 |
| heights | 0.5 | 1.0 | 6/6 |
| refraction | 0.67 | 1.0 | 6/6 |
| ohm | 0.5 | 1.0 | 6/6 |
| heat | 0.5 | 1.0 | 6/6 |
| acids | pending | pending | quota |
| power | pending | pending | quota |

- **If no-lab accuracy is high, the case leaks.** Look for:
  - a suspect narrating what it witnessed instead of news it heard;
  - a persona that biases the detective, e.g. a shop placed next to the scene of the crime.

  Fix the kit's knowledge or `admits`, not the detective.

## 7. Art pipeline

**Mascot and suspects** (`art/mascot`):

- `python build.py` renders Smudge.
- `build_suspects.py` renders the suspect sheets.
- `tools/preview_cast.py` previews a cast before a full render.
- **Gotcha:** palette ramps in `P.register` need exactly 5 colours.

**World** (`art/world`):

- `render_scene.py <scene>` renders one backdrop. Each scene is 720×270, with the law erased and restored.
- `build_instruments.py` renders the lab props.
- `build_casebook.py` renders the casebook.

**Output.** Renders go to `art/*/out/`, which is git-ignored. Shipped copies live in
`game/public/assets/case<N>/`.

## 7b. Sound and game feel

Spec: `docs/superpowers/specs/2026-10-21-game-feel-design.md`. Everything is synthesised in Tone.js, so there are
no audio files.

**Audio** (`src/audio.ts`):

- **Buses.** Music, ambience, sfx and voice each have their own bus, and all four meet in a limiter.
  Levels live in `LEVEL` at the top of the file.
- **Unlocking.** The first click or key anywhere unlocks audio, so `?case=` links get sound too. Until then
  every call is a no-op and nothing can throw.
- **Muting.** `M` or the speaker button mutes; the choice is saved in `localStorage` (`smudge.mute`).
- **The API scenes use:**
  - `themeFor(kit | "night" | "lab" | "tense")` picks the score;
  - `layer(0..3)` opens the score's layers;
  - `ambience(place, restored)` sets the soundscape;
  - `sfx(name)` plays an effect;
  - `step(ground)` plays a footstep;
  - `sting(name)` plays a short musical cue;
  - `duck(on)` steps the music back while someone talks;
  - `blip(who)` plays one syllable of a voice.

  The older `music("night" | "tense" | "off")` still works.
- **Score** (`audio/themes.ts`). One theme per district, plus `night`, `lab` and `tense`. Each bar plays one
  chord, and a motif runs over it. The layers open with progress: 0 pad, 1 bass after the inspection, 2 motif
  after the lab, 3 percussion once all three are questioned.
- **Ambience** (`audio/ambience.ts`). One recipe per place, built from noise beds, hums and random events
  (gulls, drips, thunder, gears...). Places crossfade.
- **Voices** (`audio/voices.ts`). One for each of the 30 speakers, shaped from their persona. A new suspect
  without an entry gets a steady voice derived from its id.
- **Tuning the mix.** `meters()` returns the live buses. Connect a `Tone.Meter` to each from the console.
  The current targets are music about -21 dB average, ambience about -28, with voices and effects above them.

**Feel:**

- **Transitions.** Ink-blot wipes go into and out of the lab and cross-exam. A chapter card plays the first
  time a case opens each session, followed by an establishing pan over the crime scene.
- **Districts.** Smudge eases in and out of motion and puffs dust, and the camera leads. Suspects breathe,
  glance at Smudge and shuffle, all of them alike so nothing hints at the culprit. Each district has its own
  weather and birds. While the law is missing, glitch tears and scan lines grow near the crime scene.
- **Dialogue.** The box drops in, pauses at punctuation and shakes on a shout. Holding the button
  fast-forwards. After 25 s idle, Footnote nudges the player.
- **Cross-exam.** The entrance has spotlights and a banner. PRESENT throws a "HOLD IT!" burst. A miss gets a
  hit-stop and a patience star cracks and falls; STRIKETHROUGH gets a bigger hit-stop.
- **Restore.** The restored district spreads out in a ring from the formula.
- **Overlays.** Every HTML overlay goes through `overlay()` in `systems/ui.ts`, which slides it in and gives its
  buttons and fields sounds.
- **Reduced motion.** `prefers-reduced-motion` turns off shake and hit-stop.

## 8. Known issues

- **Free-tier quota is the bottleneck.** Groq's daily limit ran out on gate days. The disk cache softens repeat
  calls, the extra Groq models give suspects more headroom, and a gate that loses its models leaves the pool alone.
  While a gate runs, it shares the quota with the game.
- **First load in dev takes about 25 s.** That is Vite loading modules, not a game bug. A production build
  (`npm run build`) loads fast.
- **A hidden preview pane freezes the game.** The browser stops `requestAnimationFrame` while the pane is
  hidden, so the game looks frozen. Bring the pane to the front, or take screenshots to keep it rendering. To
  drive it from a script anyway, step the clock by hand: `game.step(t, 16.67)` in a loop. The game's modules can
  be reached with `await import(<the /src/state.ts URL from performance.getEntriesByType("resource")>)`; after
  a hot reload that URL carries a `?t=` stamp, and a plain `/src/state.ts` import gives you a second, unused
  copy.
- **The game and the gate share one quota.** While a gate runs, suspects in the game fall back to scripted
  lines.
- **The acids and power gates have not run yet.** `server/case_pool.json` has uncommitted rows from a partial
  run. Re-run each gate when quota allows, then commit the pool.

## 9. The two-week plan (superseded by the finals spec)

Must-ship, in this order of risk.

**A. Thinking suspects.** Santosh + Claude, days 1–4.

Every reply becomes a loop:

1. **PLAN** (fast tier, JSON): `{intent, risk, must_avoid, strategy}`.
2. **DRAFT** (talk tier), written from the plan.
3. **CRITIQUE** (fast tier, JSON): `{leaks, contradicts_ledger, fix}`. If it fails, redraft once.
4. **FIREWALL**, unchanged.

Supporting work:

- **Ledger memory.** Per suspect, per case. It is fed back into PLAN.
- **Trace bus.** Every step emits `{agent, step, model, provider, ms, tokens, cached, verdict}` into `CASES[cid]`,
  served by a new `GET /api/case/{cid}/trace?since=`.
- **Red-team agent** (`server/redteam.py`). It attacks each culprit and reports leaks caught by the critique,
  caught by the firewall, or slipped through.
- **Quota.** Add Groq's other models to `PROVIDERS` (separate quotas), and add a `SMUDGE_THINK=0` switch that
  falls back to one call per reply.
- **Done when:**
  - the tests are green, and the loop is tested offline with fake providers;
  - every existing case still passes its gate;
  - the red-team report runs.

**B. Agent Observatory.** Mounika, days 2–7.

Upgrade `systems/inside.ts` into a live control room by polling `/trace?since=` every 500 ms. It needs:

- **Swimlanes per agent:** suspects, coach, detective, router. Each step is a pill showing model, ms and tokens;
  clicking a pill opens its JSON.
- **In-game thought bubbles** (toggle), e.g. "deflect · risk: high".
- **A firewall feed and a red-team scoreboard.**
- **A small agent graph** whose edges pulse when an event arrives.

Use plain DOM, as `inside.ts` already does.

**Done when:** asking a suspect a question shows plan → draft → critique appearing live.

**C. Voice interrogation.** Mounika, days 6–8. Kushal tunes the voices.

- **Hold-to-talk mic** using `webkitSpeechRecognition`, with typing as the fallback. It feeds the existing ask
  flow in `api.ts`.
- **Spoken replies.** `speechSynthesis` speaks each reply, with a pitch and rate per suspect, set in `audio.ts`
  and synced to `dialogue.ts`.
- **Interrupts.** Pressing during speech cuts the suspect off.
- **A settings toggle:** off / on / suspects only.

**Done when:** a full cross-examination works by voice alone.

**D. Case Author Agent.** Santosh + Claude for the backend, days 5–12. Kushal writes the content and does QA.

1. **`server/kits/generic.py`.** A `GenericKit(spec)` built from JSON.
   - Formulas are parsed safely with `ast`, never `eval`.
   - `kits/__init__.py` also loads `kits/generated/*.json`.
   - The contract tests cover generated kits automatically.
2. **`server/author.py`.** The pipeline, every step traced:
   1. Designer (agent).
   2. Solver (code, 200 seeds).
   3. Critic (agent; up to 3 loops back to the Designer).
   4. Casting (re-skins 3 of the 27 suspects and picks a district).
   5. Gate.

   Only cases that pass get published.
3. **Game.**
   - Add `GET /api/kits/generated`; `Boot` builds CaseDefs from those specs at runtime.
   - Add an "Author a case" button on the casebook (`Map.ts`), with a live pipeline view.
4. **Kushal's part.**
   - Write 3 hand-checked golden specs for the Designer prompt: pressure P = F/A, speed d/t, and Hooke's law.
   - QA every generated case.

**Done when:** typing "Class 9, pressure: P = F/A" produces a case that passes its gate and plays end to end.

**Timeline:**

| Days | Santosh + Claude | Mounika | Kushal |
|---|---|---|---|
| 1 | quota providers, trace bus | read this; Observatory skeleton | read this; gate acids and power; playtest pass |
| 2–4 | thinking suspects, ledger, red-team | trace timeline, bubbles | 3 golden specs; start `docs/BUGS.md` |
| 5–8 | generic kit, author pipeline | agent graph, firewall feed, then voice | voice tuning; QA thinking suspects |
| 9–12 | runtime cases, author backend | author pipeline view on the casebook | QA generated cases; red-team prompts |
| 13 | fix, gate everything | polish | demo video (`brag` / Remotion) |
| 14 | freeze | freeze | deck v4 with the real red-team numbers |

**Stretch, only if all four must-ships are done:**

1. Deduction grading agent.
2. Teacher dashboard.
3. The Baron finale case.
4. Hindi/Kannada suspects.

## 10. Conventions

- **Budget is ₹0.** Free model tiers and browser APIs only.
- **Git:** GitHub, `santoshcheethiralame-dot/SMUDGE`, branch `main`. Pull before you start.
  - Make small commits, one feature per commit.
  - Commits made with Claude end with its `Co-Authored-By` line.
- **Never commit `.env` or anything under `server/.cache/`.**
- **Green tests before every commit:** pytest and `tsc`.
- **Gates:** one at a time, and only after a kit change.
- **Kid-safe always.** Things get stolen, swapped or broken; nobody gets hurt.
- **Who to ask:**
  - Santosh: server, agents, kits, the gate.
  - Mounika: game UI, the Observatory, voice.
  - Kushal: case content, QA, the demo video.
