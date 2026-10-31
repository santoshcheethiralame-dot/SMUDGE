# Game feel: sound, transitions, juice, a living world

Date: 2026-10-21. Owner: Santosh + Claude. Status: approved to build without review (Santosh away, standing go-ahead).

## Goal

Smudge plays correctly; it should also *feel* like a finished game. Every scene gets a soundscape, every scene change
gets a transition with intent, every important action gets weight, and the districts move on their own.

## Decisions

- **All sound stays synthesised in Tone.js.** ₹0, no licences, no downloads, one coherent toy-box voice. Realism is
  not the goal; character is.
- **Phaser's own tweens, particles, cameras and masks only.** No GSAP, no shaders beyond what Phaser ships.
- **The camera zoom stays at Z.** Every camera zooms from the top-left (see `main.ts`), so camera zoom punches are
  out; weight comes from hit-stop, shake, flash, squash and sound.
- **Nothing that hints at the culprit.** Fidgets, glances, voices and music treat all three suspects alike.

## Units

| Unit | File | Does |
|---|---|---|
| Audio engine | `src/audio.ts` | Buses (music, ambience, sfx, voice) into a limiter; unlock on the first gesture anywhere; mute (`M` key and a corner button), saved in `localStorage`. Old `sfx()`, `music()`, `blip()` keep working. |
| Voices | `src/audio/voices.ts` | A hand-set voice for each of the 30 speakers: waveform, pitch range, envelope, volume. |
| Ambience | `src/audio/ambience.ts` | One synthesised bed per place (sea, wind, drizzle, hum, bubbling, gears, room tone...), crossfaded. |
| Score | `src/audio/score.ts` | One theme per district: key, tempo, chords, bass, motif. Four layers that open with progress (pad; bass; motif; percussion), a tense mode for cross-exam, stingers, and ducking under dialogue. |
| Juice | `src/systems/juice.ts` | `hitStop`, `squash`, `punch`, `buttonFeel` (hover, press, sound) for every clickable text, `flashTint`, `dustPuff`. |
| Transitions | `src/systems/transition.ts` | Ink-blot wipe out/in (a mask of growing blots), a chapter title card. |
| Atmosphere | `src/systems/atmosphere.ts` | Per-district weather and life: particles, passing birds, glitch tears that grow near the crime scene. |

## Moments

- **Arrival:** ink wipe in, chapter card ("Case 9 · Chapter 10: Work and Energy", place name typed out, sting), then
  an establishing pan from the crime scene back to Smudge. Theme and ambience fade in.
- **Walking:** Smudge eases in and out of motion, puffs dust when running and stopping, the camera leads the way he
  faces. Footsteps match the ground. Suspects breathe, glance at Smudge as he passes, fidget now and then.
- **The glitch:** tears, scan lines and crackle grow as Smudge nears the crime scene; gone once the law is back.
- **Talking:** the dialogue box drops in with a rustle and leaves upward; typing pauses at commas and full stops; lines
  ending in `!` or spoken shocked/angry shake the box; portraits flinch. Holding the button fast-forwards. Music ducks.
  First meeting with a suspect: the camera eases over, the suspect hops, a name plate slides in with a sting.
- **Progress:** the theme adds a layer after the inspection, after the lab, and after all three are questioned.
- **Lab:** ink wipe in, instruments click and snap; the notebook slides up, its boxes tick as you type, shakes on a
  wrong answer, stamps on a right one.
- **Cross-exam:** spotlights thunk on one by one, a banner slams across, tense theme. Picking a suspect hops them.
  PRESENT throws a "HOLD IT!" ink burst. A miss: hit-stop, red flash, the badge recoils, a patience star cracks and
  falls. STRIKETHROUGH: hit-stop, the existing slash, flash, burst, a sting.
- **Restore:** the restored district spreads out from the formula in a ring, not a crossfade; chimes rise with it.
- **Menus:** every button hovers, presses and clicks. Casebook pop-ups lift on hover; page turns rustle.
- **Quality of life:** hold to fast-forward; after 25 s idle in a district Footnote nudges toward the next checklist
  item; a mute button.

## Testing

`tsc` green; the audio engine never throws without a gesture (every call is a no-op until unlocked); a browser pass
over every scene with no console errors; pytest untouched. Effects respect `prefers-reduced-motion` by dropping
shake and hit-stop.
