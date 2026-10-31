// Case 4, Lumen Heights: Ladder Lane's lamps, the plaza sundial under the town hall clock, the Weathercock Spire,
// the Sunflower Mill. Alibi photos, shadow lengths, tan(elevation) = height / shadow.
import type { CaseDef } from "../types";
import type { CaseData } from "../../api";

const NAMES: Record<string, string> = { lumen: "Lumen", vane: "Vane", sola: "Sola" };
const MARKS: Record<string, string> = { lumen: "the Old Lamp", vane: "the Spire", sola: "the Mill" };
const heights = (c: CaseData) => c.heights as Record<string, number>;
const shadows = (c: CaseData) => c.shadows as Record<string, number>;

const CASE: CaseDef = {
  kit: "heights", num: 4, title: "The Long Shadow", place: "Lumen Heights", chapter: "Chapter 9: Heights and Distances",
  assets: { folder: "case4", images: ["heights_glitch", "heights_restored"], suspects: ["lumen", "vane", "sola"] },
  bg: { glitch: "heights_glitch", restored: "heights_restored" },
  map: { x: 172, y: 186, icon: "sun" },
  layout: {
    width: 720, cu: 0, cv: 90, startX: -330,
    spots: [
      { key: "lumen", x: -260, markY: 50, markZ: 8 },
      { key: "stage", x: -90, markY: 30, markZ: -38 },
      { key: "vane", x: 110, markY: 50, markZ: 8 },
      { key: "sola", x: 250, markY: 52, markZ: 8 },
    ],
    suspects: [{ key: "lumen", x: -260, z: 8 }, { key: "vane", x: 110, z: 8 }, { key: "sola", x: 250, z: 8 }],
  },
  decorate(scene, P, restored) {
    if (restored) {
      // golden afternoon: pollen drifting off the sunflower field
      scene.add.particles(0, 0, "px", {
        x: { min: 520, max: 700 }, y: { min: 120, max: 200 }, lifespan: 3000, alpha: { values: [0, 0.9, 0] },
        speedX: { min: -14, max: -4 }, speedY: { min: -6, max: 2 }, tint: 0xffe08a, frequency: 220, quantity: 1,
      });
      return;
    }
    // the law is gone: a lost shadow slides across the plaza and back, never where the sun would put it
    const at = P(-90, 0, -20);
    const blot = scene.add.ellipse(at.x - 60, at.y, 30, 7, 0x1e1830, 0.55).setDepth(5);
    scene.tweens.add({ targets: blot, x: at.x + 80, duration: 5200, yoyo: true, repeat: -1, ease: "Sine.easeInOut" });
    scene.tweens.add({ targets: blot, scaleX: 1.6, duration: 1300, yoyo: true, repeat: -1, ease: "Sine.easeInOut" });
  },
  lab: "CaseLab",
  labSteps: [
    { kind: "say", lines: [
      { who: "foot", expr: "happy", text: "Lab time! Three alibi photos from the Gazette, each one 'taken at noon'. A photo can't lie about the sun, though." },
      { who: "foot", expr: "neutral", text: "The higher the sun, the shorter the shadow. Let's find out how high the noon sun stands here first." },
    ] },
    { kind: "protractor", record: "ref",
      intro: [{ who: "smudge", expr: "determined", text: "Protractor form! The reference photo: the town hall clock says twelve. Lay my arm along the sun's ray." }],
      items: () => [{ key: "noon", label: "Reference: town hall at 12:00", angle: 60, from: "ground" as const }],
      done: [{ who: "foot", expr: "happy", text: "60° at noon. Remember it. At 10 and 2 the sun is at 45°; at 8 and 4, only 30°." }] },
    { kind: "tape", record: "s", title: "The alibi photos: shadow lengths (m)", unit: "m", max: 25, step: 0.1, fill: 0x8eb4d8,
      intro: [{ who: "smudge", expr: "determined", text: "Tape form. I'll measure each landmark's shadow, from its foot to the tip." }],
      rows: (c: CaseData) => Object.entries(shadows(c)).map(([sid, s]) => ({ key: sid, label: NAMES[sid] ?? sid, length: s, style: "shadow" as const })),
      done: [{ who: "foot", expr: "neutral", text: "Three shadows. Each photo has its landmark's height printed underneath. Now the notebook." }] },
    { kind: "notebook", hint: "*tan of the sun's angle = height ÷ shadow. Then look the answer up in the tan table.",
      note: "tan 30° = 0.58 · tan 45° = 1.00 · tan 60° = 1.73",
      fields: (c: CaseData, m: Record<string, number>) => Object.keys(heights(c)).flatMap((sid) => [
        { key: `h_${sid}`, label: `${NAMES[sid]}: ${MARKS[sid]}'s height`, unit: "m", given: heights(c)[sid] },
        { key: `s_${sid}`, label: `${NAMES[sid]}: shadow`, unit: "m", given: m[`s_${sid}`] ?? shadows(c)[sid] },
        { key: `r_${sid}`, label: `${NAMES[sid]}: height ÷ shadow`, unit: "" },
        { key: `a_${sid}`, label: `${NAMES[sid]}: sun's angle`, unit: "°" },
      ]) },
  ],
  greet: {
    lumen: { who: "lumen", expr: "neutral", text: "Good evening, detective. Lumen, lamplighter of Ladder Lane. Yes, it's the afternoon. I say it at every hour." },
    vane: { who: "vane", expr: "smug", text: "Vane, forecaster! Today's outlook: a detective, with scattered questions. Fire away." },
    sola: { who: "sola", expr: "smug", text: "Ooh, a detective, petal! Sola, 'Sunny Side' column. Anything you say may appear in print." },
  },
  chips: {
    lumen: ["Where were you at noon?", "Tell me about your photo.", "Who do you think took the gnomon?"],
    vane: ["Where were you at noon?", "Tell me about your photo.", "Heard any gossip?"],
    sola: ["Where were you at noon?", "Tell me about your photo.", "Who do you think took the gnomon?"],
  },
  arrive: [
    { who: "foot", expr: "worried", text: "Lumen Heights. Look at the shadows, Smudge: they're falling TOWARD the sun. The Baron erased heights and distances." },
    { who: "smudge", expr: "thinking", text: "And the plaza sundial's blade is gone. The Golden Gnomon, lifted at noon, in broad daylight." },
    { who: "foot", expr: "neutral", text: "Lumen, Vane and Sola all sent the Gazette photos to prove where they were at noon. Talk to them, and look at the sundial." },
  ],
  inspect: [
    { who: "smudge", expr: "thinking", text: "Four bolt holes and a scratch. Someone unscrewed the gnomon, carefully. No rush, no witnesses." },
    { who: "smudge", expr: "thinking", text: "Everyone's got a photo 'taken at noon'. But a photo shows the sun, too. In every shadow." },
    { who: "foot", expr: "neutral", text: "Then let's measure the shadows and see where the sun really was. To the lab!" },
  ],
  toLab: { who: "smudge", expr: "determined", text: "To the lab. Three photos, one protractor, one tape." },
  afterLab: { who: "foot", expr: "happy", text: "Every photo has a sun angle now. Call them to the stand and check their stories." },
  checklist: ["Inspect the sundial", "Measure the photo shadows"],
  stageLabel: "The sundial",
  badge: (ev) => ev.badge,
  miss: () => "*That photo's sun matches noon. Find the one whose shadow is too long.",
  stuck: () => "*Noon here is 60°. Whose photo shows a lower sun?",
  confess: {
    lumen: [
      { expr: "shocked", text: "Good... good heavens. My schedule. My perfect schedule." },
      { expr: "nervous", text: "I took my photo at four, when the lamps go on. At noon I was at the dial. The Baron said a lamp could stay lit forever with a golden gnomon inside." },
    ],
    vane: [
      { expr: "shocked", text: "Forecast... changed. Sharply." },
      { expr: "nervous", text: "I was in the plaza at noon. The Baron promised the gnomon would make me point true, whatever the wind did. My photo's from the morning." },
    ],
    sola: [
      { expr: "shocked", text: "Petal... that's going to be a headline, isn't it?" },
      { expr: "nervous", text: "I wanted the scoop: 'GNOMON VANISHES!' So I made it vanish. The Baron said nobody reads shadows. My photo was from the afternoon." },
    ],
  },
  restore: { glyphs: ["t", "a", "n", " ", "θ", " ", "=", " ", "h", " ", "/", " ", "s"], sub: "Heights and distances are back in the book. The shadows fall true.",
    card: "tan θ = h / s", cardSub: "Heights and Distances · Chapter 9" },
  solved: (name) => `${name}'s shadow was too long for noon. The sun gave it away.`,
};

export default CASE;
