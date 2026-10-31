# The Midnight Fall: stage cut, clear numbers, point out the liar

Approved Oct 31, night. The finals slot is 8 minutes for pitch and demo (Q&A is separate), so the game gets
about 5 minutes. The rehearsal run took about 8:20, the numbers were hard to read, and the cross-examination
confused us. Option C: what makes the game better goes to everyone, and what only saves stage time sits
behind `?judges`.

## 1. Everyone

**Drop test, two drops.** Lowest balcony, then the prediction, then the top. The gallery drop goes: its 1.5 s
matched the gramophone and gave the answer away before the notebook. Footnote's "Four times higher. Only twice
as long!" becomes a line in the right-hand panel under "You said 4 s. It took 2.0 s.", so no dialogue box
covers the stopwatch or the clock-room balcony, and no click goes to a dialogue box. Slip or push's spoken
line moves into the panel the same way.

**Point out the liar** (replaces the Midnight Fall's cross-examination; the shared `CrossExam` keeps its
behaviour for the other nine cases). Same scene, a `point` mode chosen by the case:
- each suspect under their spotlight has a plaque with their balcony and height and a speech line with their
  statement 0 ("Old Tock never came out on my balcony tonight.");
- no tabs, rows, Press button or Present button;
- drag the evidence card onto a suspect, or tap a suspect, to present against their statement 0;
- right: HOLD IT, the speech line is struck through, the existing confession and restore;
- wrong: the existing patience star loss, and Footnote names the gap, e.g. "Armoury is 4.9 m. He fell 11.0 m.";
- one intro line instead of two: "Whose balcony is that high? Drag the evidence onto them."

**Clear numbers.** Pixelify Sans draws 5 like 9 at every size and resolution (the rehearsal misread 1.50 as
1.90 and 4.5 as 4.8). A `"Smudge Digits"` face (Silkscreen, digits only, by `unicode-range`) goes first in every
font stack, in the canvas and in the HTML overlays. Letters stay Pixelify; digits become Silkscreen, which stays
pixel-styled and keeps 5, 8 and 9 apart. Boot waits for it with the other fonts.

**Fewer taps.** The wrong guess goes from three lines to two.

## 2. `?judges` only

- Questioning one suspect is enough to call everyone to the stage; the checklist reads "Question a suspect
  (n/1)". Normal play still needs all three.
- Slip or push is skipped (first on the demo script's cut list).

## 3. Not changing

The cold open, the waveform, the prediction, the notebook, the strikethrough, the ghost reveal and the exit
check: they carry the learning and the wow. The other nine cases.

## Target on stage

Cold open + pitch 0:45 · Varnish + Observatory 1:30 · wrong guess 0:10 · waveform 0:30 · two drops +
prediction 0:50 · notebook 0:30 · point out the liar 0:20 · restore + exit check 0:40 = about 5:15.

## Testing

`npm run build` passes (typecheck). A full fixture run and a full live run on `?judges` in the browser pane,
timed, with a wrong present and a wrong notebook step. The other nine cases' cross-exam is unchanged (one case
opened to check). Server tests stay green (no server change).

## Ownership

These touch Kushal's scenes. Santosh takes them, including Kushal's rehearsal items 1 and 3; item 2
("4.8 m") was the font, not the maths.
