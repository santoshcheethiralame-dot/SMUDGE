// Case 9, Watt Works: Cog's workshop under the arches, the clock tower's lift shaft, Hoist's crane, Dynamo's shed.
// Weigh the crate, measure the shaft, time the climb on the tower camera; P = mgh / t names the winch.
import Phaser from "phaser";
import type { CaseDef } from "../types";
import type { CaseData } from "../../api";

const CASE: CaseDef = {
  kit: "power", num: 9, title: "The Slow Lift", place: "Watt Works", chapter: "Chapter 10: Work and Energy",
  assets: { folder: "case9", images: ["power_glitch", "power_restored"], suspects: ["cog", "hoist", "dynamo"] },
  bg: { glitch: "power_glitch", restored: "power_restored" },
  map: { x: 404, y: 112, icon: "gear" },
  layout: {
    width: 720, cu: 0, cv: 90, startX: -330,
    spots: [
      { key: "cog", x: -260, markY: 46, markZ: 8 },
      { key: "stage", x: -64, markY: 30, markZ: -102 },
      { key: "hoist", x: 110, markY: 48, markZ: 8 },
      { key: "dynamo", x: 250, markY: 46, markZ: 8 },
    ],
    suspects: [{ key: "cog", x: -260, z: 8 }, { key: "hoist", x: 110, z: 8 }, { key: "dynamo", x: 250, z: 8 }],
  },
  decorate(scene, P, restored) {
    // the spark gap at Dynamo's shed snaps now and then
    const at = P(288, 28, -84);
    const spark = scene.add.image(at.x, at.y, "glow64").setBlendMode(Phaser.BlendModes.ADD).setTint(0xb8d4ff).setScale(0.25).setAlpha(0);
    const snap = () => {
      spark.setAlpha(0.9);
      scene.tweens.add({ targets: spark, alpha: 0, duration: 160 });
      scene.time.delayedCall(Phaser.Math.Between(900, 2600), snap);
    };
    scene.time.delayedCall(600, snap);
    if (restored) return;
    // with the law erased, loose grit drifts upward off the towpath
    scene.add.particles(0, 0, "px", {
      x: { min: 0, max: 720 }, y: { min: 200, max: 240 }, speedY: { min: -14, max: -6 }, lifespan: 3000,
      alpha: { values: [0, 0.6, 0] }, tint: 0x968676, frequency: 140, quantity: 1,
    });
  },
  lab: "CaseLab",
  labSteps: [
    { kind: "say", lines: [
      { who: "foot", expr: "happy", text: "Lab time! The lift has no motor: someone clipped their winch on. Each winch has its power on a brass plate." },
      { who: "foot", expr: "neutral", text: "Power is how fast work gets done. Work = mass × g × height, with g = 10. Then P = work ÷ time." },
    ] },
    { kind: "balance", record: "m", unit: "kg",
      intro: [{ who: "smudge", expr: "determined", text: "First, the crate that rode up in the lift. Onto the balance." }],
      items: (c: CaseData) => [{ key: "crate", label: "The crate", mass: c.mass as number }],
      done: [{ who: "foot", expr: "neutral", text: "Now the height of the shaft, from the photo of the tower." }] },
    { kind: "tape", record: "h", title: "The lift shaft, photo on its side (m)", unit: "m", max: 16, step: 0.5, fill: 0x3a2026,
      intro: [{ who: "smudge", expr: "determined", text: "Tape form. From the floor of the shaft to the top platform." }],
      rows: (c: CaseData) => [{ key: "shaft", label: "Shaft", length: c.height as number, style: "bar" as const }],
      done: [{ who: "foot", expr: "neutral", text: "And the tower camera caught the lift going up. Time it." }] },
    { kind: "stopwatch", record: "t",
      intro: [{ who: "smudge", expr: "determined", text: "Stopwatch form. Tap when the crate starts to rise, tap again when it stops at the top." }],
      clips: (c: CaseData) => [{ key: "lift", label: "Tower cam: the lift", seconds: c.seconds as number, style: "rise" as const }],
      done: [{ who: "foot", expr: "neutral", text: "Mass, height, time. Now the notebook." }] },
    { kind: "notebook", hint: "*Work = m × g × h with g = 10. Then power = work ÷ time.",
      note: "g = 10 N/kg · W = m g h · P = W ÷ t · winches: Cog 400 W, Hoist 800 W, Dynamo 1200 W",
      fields: (c: CaseData, m: Record<string, number>) => [
        { key: "m", label: "Crate's mass", unit: "kg", given: m.m_crate ?? (c.mass as number) },
        { key: "h", label: "Shaft's height", unit: "m", given: m.h_shaft ?? (c.height as number) },
        { key: "t", label: "Time to climb", unit: "s", given: m.t_lift ?? (c.seconds as number) },
        { key: "w", label: "Work done, W", unit: "J" },
        { key: "p", label: "Power, P", unit: "W" },
      ] },
  ],
  greet: {
    cog: { who: "cog", expr: "neutral", text: "Cog. Clockmaker. You are four minutes late, detective. Proceed, precisely." },
    hoist: { who: "hoist", expr: "neutral", text: "Hoist. Crane. ...Ask." },
    dynamo: { who: "dynamo", expr: "smug", text: "Dynamo-dynamo-hi! Generator shed! Ask quick, I'm buzzing, I've got coils on!" },
  },
  chips: {
    cog: ["Tell me about your winch.", "Where were you last night?", "Who do you think used the lift?"],
    hoist: ["Tell me about your winch.", "Where were you last night?", "Heard any gossip?"],
    dynamo: ["Tell me about your winch.", "Where were you last night?", "Who do you think used the lift?"],
  },
  arrive: [
    { who: "foot", expr: "worried", text: "Watt Works. Smudge, those crates are floating off the towpath. The Baron erased work and power." },
    { who: "smudge", expr: "thinking", text: "And the clock tower's stopped. Someone rode the crate lift up last night and took the Golden Escapement." },
    { who: "foot", expr: "neutral", text: "The lift needs a winch. Cog, Hoist and Dynamo each own one, every rating on a brass plate. Look at the lift." },
  ],
  inspect: [
    { who: "smudge", expr: "thinking", text: "Fresh scratches on the winch bracket, where someone clipped a winch on. The crate's still in the cage." },
    { who: "smudge", expr: "thinking", text: "And a camera on the tower. If it filmed the climb, we know how long it took." },
    { who: "foot", expr: "neutral", text: "A heavy crate, a tall shaft, a short time: that's a powerful winch. Let's put numbers on it." },
  ],
  toLab: { who: "smudge", expr: "determined", text: "To the lab. A balance, a tape, a stopwatch." },
  afterLab: { who: "foot", expr: "happy", text: "We know how powerful that winch was. Call them to the stand and check their stories." },
  checklist: ["Inspect the tower lift", "Work out the winch's power"],
  stageLabel: "The tower lift",
  badge: (ev) => ev.badge,
  miss: () => "*That winch is the wrong power for the lift we timed. Whose matches?",
  stuck: () => "*Your P matches exactly one winch plate.",
  confess: {
    cog: [
      { expr: "shocked", text: "...Unforgivably imprecise of me." },
      { expr: "nervous", text: "I clipped my winch on and rode up. The Baron said the Escapement would make my clocks the only true ones in town. It was slow. I am never slow." },
    ],
    hoist: [
      { expr: "shocked", text: "...Dropped." },
      { expr: "nervous", text: "My winch. My crate. Up the tower. Baron said a crane should lift the heaviest prize in town. Sorry." },
    ],
    dynamo: [
      { expr: "shocked", text: "Bzzzt... bzt... oh." },
      { expr: "nervous", text: "Okay-okay it was me, my winch, so fast, up and down! The Baron said the Escapement would make me spin forever. I'm so sorry." },
    ],
  },
  restore: { glyphs: ["P", " ", "=", " ", "W", " ", "/", " ", "t"], sub: "Work and power are back in the book. The clock ticks again.",
    card: "P = W / t = m g h / t", cardSub: "Work and Energy · Chapter 10" },
  solved: (name) => `${name}'s winch hauled that lift. The power proved it.`,
};

export default CASE;
