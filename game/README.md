# Smudge: the game

Phaser 3.90 + TypeScript + Vite. All sound is synthesised with Tone.js, and all art is pre-rendered from code in `../art`.

```
npm install
npm run dev        # http://localhost:8872
npm run build      # dist/
```

Jump straight to a scene with `?scene=Title|Prologue|HQ|EndCard`.

## Scenes
| Scene | What happens |
|---|---|
| Title | A night desk with a lamp. The pop-up city has a sweeping lighthouse beam and a blinking antenna; Smudge and Footnote stand on the open book. |
| Prologue | Cutscene, skippable. The pen drips, Smudge forms from the puddle, Footnote peels off the page's asterisk, and the Rubber Baron's eraser rubs out ρ = m / V. |
| HQ | Playable. Inside the toppled ink bottle: tap or arrow keys to walk, Shift to run, tap sparkles or press E to look. The case board unlocks the door. |
| EndCard | Case 1 teaser. Tap to restart. |

## Art pipeline
Backdrops are 3D SDF scenes raymarched to 480×270 pixel art. They use the same camera and key light as the sprites, so characters and world match.
```
cd ../art/world
python render_scene.py scene_title
python render_scene.py scene_prologue prologue
python render_scene.py scene_prologue prologue_erased erased=1
python render_scene.py scene_hq hq
python render_scene.py scene_props nib which=nib
python render_scene.py scene_props eraser which=eraser
```
Then copy `out/*.png` into `public/assets/bg/`. Mascot sprites come from `../art/mascot` (`build.py`, `build_footnote.py`).

`src/consts.ts` `project()` converts a world point in a backdrop into screen pixels, so sprites can stand exactly on rendered floors.
