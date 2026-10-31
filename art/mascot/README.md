# Smudge mascot sprites

Smudge is modelled once in 3D (signed-distance shapes in `src/rig.py`), posed by small Python animation functions, and raymarched into 64×64 pixel art from 8 directions. Changing the model or a pose and re-running the build regenerates every sheet consistently.

## Run
```
python build.py                  # everything (~10 min on 12 cores)
python build.py --only walk,run  # just these sheets and previews
python build.py --portraits      # just the dialogue portraits
python make_review.py            # bundle out/review.html
python -m pytest tests -q
```
Needs Python 3.10+, numpy and Pillow.

## Output (`out/`)
| File | What it is |
|---|---|
| `sheets/<anim>.png` | One sheet per animation. Rows are S, SE, E, NE, N, NW, W, SW; columns are frames; 64 px cells, transparent |
| `smudge_atlas_*.png` + `smudge_atlas.json` | Phaser 3 multiatlas, 2048 px pages. Frame names `<anim>/<dir>/<i>` |
| `smudge_anims.json` | Phaser animation defs, keys `<anim>_<dir>`, with frame rate and repeat |
| `portraits.png`, `portraits/` | 96 px dialogue busts: 8 expressions × rest, blink, talk1–3 |
| `previews/<anim>.gif` | All 8 directions side by side at 4× |
| `review.html` | Interactive viewer for every sheet |

Feet sit on row 60 of each cell. In Phaser use `pixelArt: true`, integer scales, and `setOrigin(0.5, 0.94)`. Jump height is left to the engine: `jump_air` is drawn in place. `smoke/index.html` is a keyboard-driven Phaser test. Serve the `mascot` folder and open `/smoke/`.

## Where things live
| File | Role |
|---|---|
| `src/sdf.py` | Distance primitives |
| `src/rig.py` | The character: proportions, coat, hat, props, instrument forms, a tiny arm IK (`reach`) |
| `src/render.py` | Camera (20° pitch, orthographic), lights fixed to the camera, cel ramps, outlines, eye and mouth decals |
| `src/palette.py` | The only colours allowed. Tests fail on anything else |
| `src/anims/*.py` | One function per animation: `frame(i, n) -> Pose`. Register with `@anim(name, frames, fps, loop)` |
