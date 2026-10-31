# Case 2: The Skid at Braking Bend (Motion Mesa)

Approved 2026-10-20 from the concept page (claude.ai/artifact/2JDxKddA8r6tXVS5ej1kHJ).
Decisions: keep Dash, Rolla and Mu as drawn; the notebook works all three skids; the crime is the toppled Trophy Tower.

## The case

Motion Mesa (Chapter 8, Class 9 Motion). The Rubber Baron erased the equations of motion, so friction flickers.
The night before the Grand Derby, a rider came down Slope Hill over the 9 m/s limit, lost Braking Bend and flattened
the Trophy Tower. Three riders came down; each braked at the white line and left a skid; each swears a speed under
the limit. Only the culprit's oath is false, and only the skids prove it.

Science: `a = (v − u) / t` from a braking test, then `v² = u² + 2as` with v = 0 for each skid, so `u = √(2as)`.

## Truth engine: `server/kits/motion.py` (a Kit, same contract as density)

- **generate(rng)**: culprit uniform over {dash, rolla, mu}. Stop time t ∈ {2.0, 2.5} s from the gate's 10.0 m/s, so
  a ∈ {5, 4} m/s². Innocent true speeds are drawn from {6, 7, 8} m/s and their sworn speed equals it. The culprit's
  true speed is drawn from {12, 13, 14} (a = 5) or {12, 13} (a = 4), and the sworn speed from {6, 7, 8}. Skid
  s = round(u² / 2a, 1) m, at most 25 m.
  - hidden: `speeds`, `claims`.
  - public: `gate_speed` 10.0, `stop_time` t, `skids` {sid: s}, `limit` 9.
- **testimony**, four lines each:
  1. "I came round Braking Bend at {claim} m/s. Under the limit, like always." The culprit's line is the lie, with
     `contradicts = "speed:{sid}"`.
  2. "I braked at the white line, same as everyone. The {tread} skid is mine." (true)
  3. "The Trophy Tower was standing when I went past." (true unless culprit)
  4. "Whoever knocked the tower down, it wasn't me." (true unless culprit)
- **check_constraints**: exactly one rider over the limit, and it is the culprit; every sworn speed is under the
  limit; the lie is unique; √(2as) from each rounded s is within 0.15 of the true speed; every skid is at most 25 m.
- **check_lab(working)**: the fields are `time, accel, s_dash, s_rolla, s_mu, u_dash, u_rolla, u_mu`. Steps are
  checked in this order, and the first failure is returned as `step`:
  1. `time` (±0.06 s)
  2. `accel` (|a| within 0.11; either sign is fine)
  3. `skid` (each s within 0.15 m)
  4. `forgot_root` (a u that equals 2as)
  5. `speed` (each u within 0.2 of √(2as))

  When everything passes it returns `ok`, `evidence = "speed:{over-limit sid}"`, `speeds` and `rows` (per-row
  flags for the UI).
- **knowledge**: route, own skid tread, the limit, true gossip about one other rider's tread, the district glitch.
  - Innocents also get their true speed, that the tower was standing when they passed, and that they don't know who
    did it.
  - The culprit's secret is the true speed and the clip, plus the sworn speed they tell everyone; they deny calmly.
- **units** (number filter): metres only, `m(?!/)|metres?|meters?|cm`, so a suspect can say their own speed and never
  a skid length.
- **admits**: applies to every suspect, not just the culprit. Blocked:
  - any m/s figure other than their own sworn speed
  - first-person knocked/hit/clipped/toppled/flattened/smashed, unless negated
  - "I was going too fast / speeding / over the limit"
- **hints**: time, accel, skid, forgot_root, speed, present. None names a rider.
- **detective**: three questions (speed, skid, who), and a lab report giving gate speed, stop time, skid lengths by
  tread, and the limit.

## Engine changes (case-agnostic)

- `agents.SuspectAgent.filter` calls `kit.admits` for every suspect. Density's `admits` already only concerns the
  speaker's own metal.
- Footnote's answer-word guard and the kit contract test match whole words (so "mu" never matches "must").

## Art (in the existing pipeline)

- `art/mascot/src/palette.py` gains the ramps DASH, FLETCH, RUBBER, PIE, PINE, HARDHAT, SKATE. The Dash, Rolla and
  Mu classes move into `src/suspects.py` as concepted. Dash and Rolla are billboards.
- `build_suspects.py dash,rolla,mu` gives sheets (idle, talk, nervous, shocked × 8 directions) and portraits
  (5 expressions × 3 talk frames).
- `art/world/scene_mesa.py`, two renders, `glitch=1` and `glitch=0`, at 720×270.
- `art/world/scene_skidlab.py`:
  - `plate`: a blank asphalt print with the metre scale (0–25 m) and D/R/M tags, no skids
  - `track`: bench, test road and speed gate, no cart or skid
  - `cart`: a transparent sprite

  Skids and the cart are drawn live in Phaser from the case numbers.
- Outputs are copied to `game/public/assets/case2/`.

## Game

- `systems/district.ts`: a shared district scene with walking, hotspots, interrogation via askBox, the checklist,
  the prompt and a stage hook. `Bay` and the new `Mesa` subclass it with their config and decorations; Bay behaviour
  is unchanged.
- `src/cases.ts`: per-case content:
  - kit, title, district scene, lab scene
  - greeting and chip questions per suspect
  - checklist text
  - evidence badge text
  - confessions per culprit
  - restore formula, subtitle and background keys
  - Formula Card text
  - the next case
- `LabMotion` scene:
  1. **Braking test.** The cart animates past the gate; tap starts and stops the big stopwatch; the time is
     kept (±0.05 s of the true time snaps to it).
  2. **Skid plate.** Skids are drawn to scale from `skids`. Drag the tape (Smudge ruler form) from the brake line;
     it reads 0.1 m and snaps within 0.1 m of a skid end. Each skid is measured once.
  3. **Notebook.** Time, a, then three rows of s and u. `api.labCheck(working)`; a wrong step gets Footnote's
     hint. The evidence card names the over-limit skid's speed and km/h.
- `CrossExam`, `Restore` and `CaseSolved` read from `cases.ts`. The suspect order and spotlights come from the
  case. The evidence string comes from the lab result.
- Dialogue and audio gain dash, rolla and mu (portraits, name tags, voices).
- `api.newCase(kit)`, `api.labCheck(working)`, an offline case per kit.
- **Flow.** Solving Case 1 unlocks Case 2. CaseSolved offers "Next case: Motion Mesa", and the HQ door goes to the
  next unsolved case. `?scene=Mesa` works directly.

## Verification

- `server/tests`: the kit contract runs on both kits, plus motion-specific filter tests. All offline.
- Release gate on the motion kit: no-lab accuracy near chance and with-lab accuracy high, with failing seeds kept
  out of the pool.
- `tsc` clean. A browser playtest of Case 1 → Case 2: explore, ask a live suspect, all three lab steps including
  a wrong answer, STRIKETHROUGH, restore, solved.

## Out of scope

Customise and settings screens, the world map, Case 3, persistence across reloads.
