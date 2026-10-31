// Case 5, Prism Port: Frost's ice house, the lighthouse on its rock, Pane's glassworks, Geo's sapphire grotto.
// A laser through the fake lens; n = sin i / sin r names the material, and the material names its owner.
import Phaser from "phaser";
import type { CaseDef } from "../types";
import type { CaseData } from "../../api";

const CASE: CaseDef = {
  kit: "refraction", num: 5, title: "The Bent Light", place: "Prism Port", chapter: "Chapter 10: Light: Refraction",
  assets: { folder: "case5", images: ["prism_glitch", "prism_restored"], suspects: ["frost", "pane", "geo"] },
  bg: { glitch: "prism_glitch", restored: "prism_restored" },
  map: { x: 92, y: 220, icon: "prism" },
  layout: {
    width: 720, cu: 0, cv: 90, startX: -330,
    spots: [
      { key: "frost", x: -260, markY: 46, markZ: 8 },
      { key: "stage", x: -90, markY: 70, markZ: -110 },
      { key: "pane", x: 110, markY: 52, markZ: 8 },
      { key: "geo", x: 250, markY: 46, markZ: 8 },
    ],
    suspects: [{ key: "frost", x: -260, z: 8 }, { key: "pane", x: 110, z: 8 }, { key: "geo", x: 250, z: 8 }],
  },
  decorate(scene, P, restored) {
    // the lighthouse lamp breathes: bright and steady once the diamond's back, fitful while the fake sits there
    const at = P(-90, 104, -126);
    const glow = scene.add.image(at.x, at.y, "glow64").setBlendMode(Phaser.BlendModes.ADD).setTint(restored ? 0xe8f4ff : 0x9c8ed0).setAlpha(0.5).setScale(0.8);
    scene.tweens.add({ targets: glow, alpha: restored ? 0.75 : 0.15, scale: restored ? 1.0 : 0.6, duration: restored ? 1600 : 380,
      yoyo: true, repeat: -1, ease: restored ? "Sine.easeInOut" : "Stepped" });
    // sparks drifting up from the glassworks chimney
    const ch = P(132, 98, -100);
    scene.add.particles(ch.x, ch.y, "px", {
      speedY: { min: -24, max: -12 }, speedX: { min: -6, max: 6 }, lifespan: 1400, alpha: { start: 1, end: 0 },
      tint: [0xffd860, 0xffa830, 0xf07018], frequency: 140, quantity: 1,
    });
  },
  lab: "CaseLab",
  labSteps: [
    { kind: "say", lines: [
      { who: "foot", expr: "happy", text: "Lab time! The fake lens looks clear as anything. But every clear material bends light by its own amount." },
      { who: "foot", expr: "neutral", text: "That amount is the refractive index: n = sin i ÷ sin r. Ice is 1.31, glass 1.50, sapphire 1.77. Real diamond: 2.42." },
    ] },
    { kind: "protractor", record: "ang",
      intro: [{ who: "smudge", expr: "determined", text: "Protractor form! A laser goes into the fake lens. Angles from the dashed normal, not from the surface." }],
      items: (c: CaseData) => [
        { key: "i", label: "The laser in the air", angle: c.i as number, from: "normal" as const, side: "up" as const, other: c.r as number, below: "the fake lens" },
        { key: "r", label: "The laser inside the lens", angle: c.r as number, from: "normal" as const, side: "down" as const, other: c.i as number, below: "the fake lens" },
      ],
      done: [{ who: "foot", expr: "neutral", text: "Two angles. It bent toward the normal going in, as it should. Now: by how much?" }] },
    { kind: "notebook", hint: "*n = sin i ÷ sin r. Look each angle up in the sine table first.",
      note: "sin 60° = 0.87 · sin 41° = 0.66 · sin 35° = 0.57 · sin 29° = 0.48 · sin 21° = 0.36",
      fields: (c: CaseData, m: Record<string, number>) => [
        { key: "i", label: "Angle in the air, i", unit: "°", given: m.ang_i ?? (c.i as number) },
        { key: "r", label: "Angle in the lens, r", unit: "°", given: m.ang_r ?? (c.r as number) },
        { key: "sin_i", label: "sin i", unit: "" },
        { key: "sin_r", label: "sin r", unit: "" },
        { key: "n", label: "n = sin i ÷ sin r", unit: "" },
      ] },
  ],
  greet: {
    frost: { who: "frost", expr: "neutral", text: "Frost. Ice sculptor. Make it quick, detective, I'm on a schedule. And slowly melting." },
    pane: { who: "pane", expr: "smug", text: "Pane, glassblower! Come in, come in, mind the furnace. Clear as glass, that's my motto." },
    geo: { who: "geo", expr: "neutral", text: "Hm. Geo. I cut sapphire. Ask your questions. One at a time." },
  },
  chips: {
    frost: ["What do you work with?", "Is any of it missing?", "Who do you think swapped the lens?"],
    pane: ["What do you work with?", "Is any of it missing?", "Heard any gossip?"],
    geo: ["What do you work with?", "Is any of it missing?", "Who do you think swapped the lens?"],
  },
  arrive: [
    { who: "foot", expr: "worried", text: "Prism Port. Look at the lighthouse beam, Smudge: it kinks and wanders. The Baron erased the law of refraction." },
    { who: "smudge", expr: "thinking", text: "And the lighthouse lens is dull. Someone swapped the diamond lens for a fake last night." },
    { who: "foot", expr: "neutral", text: "Frost works ice, Pane works glass, Geo works sapphire. A fake lens has to be cut from something..." },
  ],
  inspect: [
    { who: "smudge", expr: "thinking", text: "The fake's a perfect copy. Same size, same facets, clear as diamond. To the eye." },
    { who: "smudge", expr: "thinking", text: "But diamond bends light more than anything else in Prism Port. This one barely bends it at all." },
    { who: "foot", expr: "neutral", text: "Then let's measure exactly how much it bends. The lab has a laser." },
  ],
  toLab: { who: "smudge", expr: "determined", text: "To the lab. One laser, one protractor." },
  afterLab: { who: "foot", expr: "happy", text: "We know what the fake is made of. Call them to the stand and check their stories." },
  checklist: ["Inspect the lighthouse lens", "Measure the fake lens"],
  stageLabel: "The lighthouse",
  badge: (ev) => ev.badge,
  miss: () => "*That suspect's material doesn't bend light like the fake. Whose does?",
  stuck: () => "*Your n matches one material, and each material belongs to one suspect.",
  confess: {
    frost: [
      { expr: "shocked", text: "...I'm melting. Literally. Look at me." },
      { expr: "nervous", text: "I carved it from my best block. The Baron said nobody would tell ice from diamond in the dark. He was nearly right." },
    ],
    pane: [
      { expr: "shocked", text: "Shattered. Clean through." },
      { expr: "nervous", text: "I blew the fake myself, it was my finest piece! The Baron said nobody measures a lens. Clear as glass, they'd never know." },
    ],
    geo: [
      { expr: "shocked", text: "Hm. Hm! ...Hm." },
      { expr: "nervous", text: "I cut it from the sapphire in my safe. The Baron wanted the diamond. I wanted to prove sapphire was just as good. It isn't." },
    ],
  },
  restore: { glyphs: ["n", " ", "=", " ", "s", "i", "n", " ", "i", " ", "/", " ", "s", "i", "n", " ", "r"], sub: "Refraction is back in the book. The beam runs true.",
    card: "n = sin i / sin r", cardSub: "Light: Refraction · Chapter 10" },
  solved: (name) => `The fake lens bent light like ${name}'s stock. The laser proved it.`,
};

export default CASE;
