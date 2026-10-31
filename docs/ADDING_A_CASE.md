# Adding a case

A case is a self-contained set of new files. Nothing shared is edited: the server, the art pipeline and the game
each discover cases on their own. Case 3, The Thunder Alibi (`sound`), is the worked example to copy from.

| Part | File | What it is |
|---|---|---|
| Truth engine | `server/kits/<kit>.py` | the facts, the lie, the lab check, what each suspect knows |
| Tests | `server/tests/test_<kit>.py` | case-specific checks (the shared contract runs on its own) |
| Cast | `art/mascot/src/cast/<kit>.py` | three SDF suspects, their palette ramps, portrait framing |
| District | `art/world/scene_<place>.py` | the 720×270 backdrop, law erased and restored |
| Game | `game/src/cases/<kit>/index.ts` | layout, scenery, lab steps, every line of dialogue |
| Art in game | `game/public/assets/case<N>/` | rendered backdrops and suspect sheets |

## 1. Design the mystery first

Every case has one shape, and the release gate enforces it:

- **One measurement, one category.** The lab produces a number (a density, a speed, a distance, an angle, a
  pH...). That number points at exactly one thing (a metal, a skid, a place, a time, a product).
- **Every suspect makes the same kind of sworn statement.** Each owns one category openly ("Yes, I keep silver"),
  or swears one number ("I filmed it from 680 m away"). The innocents' statements are true. The culprit's matches
  in form but is false, and only the measurement shows it.
- **Symmetric without the lab.** Nothing in the testimony, the personas or the gossip should point at the
  culprit. The culprit is chosen at random each seed. A suspect with a bad reputation is a good red herring;
  any fixed bias still scores chance.
- **Kid-safe.** Something is stolen, swapped, broken or knocked over. Nobody is hurt.
- **Whole numbers.** Choose values so the maths comes out clean (s = u²/2a with u from {6, 7, 8}; delays that
  are multiples of 0.5 s; standard angles 30/45/60°).

## 2. The truth engine: `server/kits/<kit>.py`

Subclass `Kit` (`kits/base.py` documents every hook). Copy `kits/sound.py` and change it. You need:

- `id`, `num` (case number), `title`, `place`, `item` (the crime's object, one noun), `answer_noun`,
  `answer_words` (suspect ids are fine), `units` (a regex of units suspects must never quote numbers in), and
  `suspects`, `gossip`, `hints`, `detective_questions`.
- `generate(rng)` returns `(culprit, hidden, public)`. `public` is everything the client needs to run the lab
  (true values the instruments snap to). `hidden` never leaves the server.
- `testimony()` returns four statements per suspect. Exactly one, the culprit's sworn line, carries
  `contradicts: "<evidence label>"`.
- `check_lab(case, working)` checks the notebook step by step. It returns `ok`, `step` (a key of `hints`),
  `bad` (wrong field keys) and, when ok, `evidence` plus `card: {title, line, badge, say}`. Give each classic
  mistake its own step and hint (sound has `halved` for the echo mistake and `divided`).
- `solution()` gives the correct working (tests use it). `lab_report()` gives the gate detective the
  measurements and the formula, not the conclusion.
- `knowledge()` returns each suspect's whole world. The culprit also gets the `SECRET`. Tell suspects the exact
  figure to give for their own number.
- `admits()` blocks anything the case forbids anyone to say: any figure but their own, and any first-person
  confession phrasing. `leak_examples()` returns three lines it must block (the judges' panel runs them).
- `scripted()` gives fallback answers. They must survive the filter.

Then:

```bash
cd server && python -m pytest tests -q
```

The shared contract (`tests/test_kits.py`) runs on every kit automatically. Add `tests/test_<kit>.py` for
numbers coming out whole, culprits spreading evenly, each mistake's hint, and the filter.

**Release gate.** `python gate.py 9 <kit>` uses about a third of a Groq model's daily free tokens. Run gates
one at a time, never two in parallel. Pass means no-lab accuracy near chance and with-lab accuracy high; failing
seeds are kept out of play automatically.

## 3. The cast: `art/mascot/src/cast/<kit>.py`

Three classes on `_Base` (see `cast/sound.py`):

- **Size and shape.** Feet at y = 0, front is +z, about 40–46 units tall. `eval(q)` returns `(distance,
  material)`.
- **Colours.** New colours via `P.register([...5 hex, dark to light], specular=...)` at the top of the file.
- **The face.** `skin` is the material the eyes may sit on: keep a plain patch of it where the face goes.
  `face_anchor()` places the eyes.
- **Billboards.** Flat things (an arrow, a wheel) set `billboard = True` so they stay readable.
- **Registration.** `CHARS = {...}` and `VCENTRE = {...}` (the portrait's face height).

To look before rendering everything: `python tools/preview_cast.py a,b,c out.png` (4 views and 5 portraits on paper).
Then render the full sheets:

```bash
cd art/mascot && python build_suspects.py a,b,c
```

Copy `out/suspects/<sid>_*.png` to `game/public/assets/case<N>/`.

## 4. The district: `art/world/scene_<place>.py`

Copy `scene_valley.py`. Pointers:

- **The world.** 720×270, `CENTRE = (0, 90)`. The walkable path is y = 0, z 0..30, and suspects stand at
  z = 8. Buildings go at z ≈ -80…-110 and far scenery at z ≈ -250…-330.
- **What fits on screen.** Screen height covers v = y·cos20° − z·sin20° from -45 to 225. Keep tall far things
  under v ≈ 200 or they swallow the sky.
- **Sign text.** Signs need the text mask at about 2 samples per world unit: a 36-unit-wide sign takes a
  72-pixel mask. Narrower and the strokes drop out ("POST" comes out as "PCST").
- **Lighting.** Use `key` ≥ 0.45 and `ambient` ≈ 0.15, or night scenes go muddy.
- **Two states.** `build(glitch=True)` shows the law erased (frozen rings, sliding grit, rubbed-out equations,
  afterimages); `build(glitch=False)` shows it restored, with the stolen thing back in place.

```bash
cd art/world && python render_scene.py scene_<place> <kit>_glitch glitch=1
python render_scene.py scene_<place> <kit>_restored glitch=0
```

Copy both to `game/public/assets/case<N>/`. Check the `_x3` previews by eye before moving on.

## 5. The game: `game/src/cases/<kit>/index.ts`

Copy `cases/sound/index.ts`.

- **`assets`.** The folder, the image keys, and the suspect ids.
- **`layout`.** World x of each suspect and of the crime scene (`stage`), matching the backdrop.
- **`decorate`.** Optional: particles, glows, and how the law-erased state moves.
- **`labSteps`.** Built from the instruments, then the notebook. Each instrument records
  `measured[record + "_" + key]`; notebook fields pick those up as `given`.
- **All dialogue.** Greetings, chips, arrival, inspection, confessions per culprit, restore glyphs, and the
  solved line.

Instruments (`game/src/systems/lab/instruments/`, try any with `?scene=Bench&kind=<name>`):

| kind | does | records |
|---|---|---|
| `say` | lines of dialogue | |
| `stopwatch` | time clips on a screen (style `flashboom`) | seconds per clip |
| `tape` | lengths on an evidence photo | length per row |
| `protractor` | angles from the ground or from the normal | degrees per item |
| `gauge` | read a thermometer or dial; the player types it | value per item |
| `dropper` | indicator colour against the pH chart | pH per sample |
| `tally` | roll a die into a tally chart | count per face |
| `balance` | weigh items on a digital balance | mass per item |
| `notebook` | the working, checked by the kit | |

A new instrument is one file there exporting `kind` and `run(ctx, step)`, plus its step type in `lab/types.ts`.

## 6. Check it

1. `cd server && python -m pytest tests -q` and `cd game && npx tsc --noEmit -p .` both pass.
2. Restart the agent server (it loads kits at start).
3. Play `http://localhost:8872/?case=<kit>`:
   - ask each suspect something live
   - inspect the crime scene
   - do the whole lab, including one classic mistake
   - present against an innocent (a miss), then the culprit (STRIKETHROUGH)
   - restore and solved
4. Open the judges' panel (`` ` ``): bait the culprit and run the filter test.
5. The case appears on the casebook map by itself.

---

## The casebook

Nine cases are built, and the casebook ends at nine. Each kit's docstring (`server/kits/<kit>.py`) is that
case's design: the crime, the owned categories, the measurement and the lie.

| # | Case | District | Law | Lab |
|---|---|---|---|---|
| 1 | The Forged Crown | Buoyant Bay | density | balance, displacement |
| 2 | The Skid at Braking Bend | Motion Mesa | v² = u² + 2as | stopwatch, skid tape |
| 3 | The Thunder Alibi | Echo Valley | d = v t | storm videos |
| 4 | The Long Shadow | Lumen Heights | tan θ = h / s | protractor, tape |
| 5 | The Bent Light | Prism Port | n = sin i / sin r | protractor (normal) |
| 6 | The Blackout | Ohmtown | V = I R | dial meters |
| 7 | The Warm Alibi | Kelvin Springs | Q = m c ΔT | balance, thermometer |
| 8 | The Colour Swap | Acid Alley | pH and dilution | dropper |
| 9 | The Slow Lift | Watt Works | P = m g h / t | balance, tape, stopwatch (rise) |
