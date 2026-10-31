// Case 7, Kelvin Springs: Al's Steam Kitchen, the bathhouse safe and its cooling tub, Ferris's boiler house,
// Brewster's tea house. Weigh the block and the water, read the water before and after; c names the metal.
import Phaser from "phaser";
import type { CaseDef } from "../types";
import type { CaseData } from "../../api";

const CASE: CaseDef = {
  kit: "heat", num: 7, title: "The Warm Alibi", place: "Kelvin Springs", chapter: "Chapter 12: Heat",
  assets: { folder: "case7", images: ["heat_glitch", "heat_restored"], suspects: ["al", "ferris", "brewster"] },
  bg: { glitch: "heat_glitch", restored: "heat_restored" },
  map: { x: 384, y: 196, icon: "steam" },
  layout: {
    width: 720, cu: 0, cv: 90, startX: -330,
    spots: [
      { key: "al", x: -260, markY: 50, markZ: 8 },
      { key: "stage", x: -90, markY: 30, markZ: -50 },
      { key: "ferris", x: 110, markY: 46, markZ: 8 },
      { key: "brewster", x: 250, markY: 46, markZ: 8 },
    ],
    suspects: [{ key: "al", x: -260, z: 8 }, { key: "ferris", x: 110, z: 8 }, { key: "brewster", x: 250, z: 8 }],
  },
  decorate(scene, P, restored) {
    // snow drifting down over everything
    scene.add.particles(0, -10, "px", {
      x: { min: -20, max: 740 }, speedY: { min: 14, max: 30 }, speedX: { min: -8, max: 4 }, lifespan: 9000,
      alpha: { min: 0.5, max: 0.9 }, tint: 0xf2f6ff, frequency: 90, quantity: 1,
    }).setDepth(800);
    if (!restored) return;
    // steam lifting off the pools, now that heat behaves
    for (const [x, z] of [[-170, -130], [-20, -140], [190, -150]]) {
      const at = P(x, 6, z);
      scene.add.particles(at.x, at.y, "px", {
        x: { min: -18, max: 18 }, speedY: { min: -12, max: -6 }, speedX: { min: -3, max: 3 }, lifespan: 2600,
        scale: { start: 2, end: 5 }, alpha: { start: 0.35, end: 0 }, tint: 0xe2e8f4, frequency: 160, quantity: 1,
      });
    }
    void Phaser;
  },
  lab: "CaseLab",
  labSteps: [
    { kind: "say", lines: [
      { who: "foot", expr: "happy", text: "Lab time! We've got the block from the tub. Every metal soaks up heat differently: that's its specific heat, c." },
      { who: "foot", expr: "neutral", text: "Plan: boil the block to 100 °C, drop it in cold water, and see how warm the water gets. Heat the water gains = heat the block loses." },
    ] },
    { kind: "balance", record: "m", unit: "kg",
      intro: [{ who: "smudge", expr: "determined", text: "First, weigh both: the block, and the water in the tub." }],
      items: (c: CaseData) => [
        { key: "block", label: "The block", mass: c.block_kg as number, look: "ingot" as const },
        { key: "water", label: "The water", mass: c.water_kg as number, look: "tub" as const },
      ],
      done: [{ who: "foot", expr: "neutral", text: "Masses noted. Now the thermometer, before and after the hot block goes in." }] },
    { kind: "gauge", record: "t",
      intro: [{ who: "smudge", expr: "determined", text: "Thermometer in the water. Reading it cold, then again once the block's dropped in and it settles." }],
      items: (c: CaseData) => [
        { key: "1", label: "Water, before", value: c.t1 as number, min: 0, max: 60, step: 1, unit: "°C", style: "thermo" as const, labelEvery: 10 },
        { key: "2", label: "Water, after the block", value: c.t2 as number, min: 0, max: 60, step: 1, unit: "°C", style: "thermo" as const, labelEvery: 10 },
      ],
      done: [{ who: "foot", expr: "neutral", text: "The water warmed up and the block cooled down. Same heat, both ways. To the notebook!" }] },
    { kind: "notebook", hint: "*Heat gained by the water: Q = m × 4200 × rise. Then c = Q ÷ (block's mass × block's drop from 100 °C).",
      note: "water: c = 4200 J/kg°C · the block started at 100 °C · Q = m c ΔT",
      fields: (c: CaseData, m: Record<string, number>) => [
        { key: "mb", label: "Block's mass", unit: "kg", given: m.m_block ?? (c.block_kg as number) },
        { key: "mw", label: "Water's mass", unit: "kg", given: m.m_water ?? (c.water_kg as number) },
        { key: "t1", label: "Water before", unit: "°C", given: m.t_1 ?? (c.t1 as number) },
        { key: "t2", label: "Water after", unit: "°C", given: m.t_2 ?? (c.t2 as number) },
        { key: "q", label: "Heat the water gained, Q", unit: "J" },
        { key: "c", label: "Block's specific heat, c", unit: "J/kg°C" },
      ] },
  ],
  greet: {
    al: { who: "al", expr: "smug", text: "Al, Steam Kitchen! Quick quick, chef, I've got a sauce reducing. What can I do you for?" },
    ferris: { who: "ferris", expr: "neutral", text: "Ferris. Boilerman. *clank* Keeps the whole town's pipes toasty. Ask away, I'm warmed up." },
    brewster: { who: "brewster", expr: "neutral", text: "Brewster, of the Copper Kettle. Do come in out of the snow. Tea? Do ask your questions." },
  },
  chips: {
    al: ["What metal do you work?", "Is any of it missing?", "Who do you think melted the lock?"],
    ferris: ["What metal do you work?", "Is any of it missing?", "Heard any gossip?"],
    brewster: ["What metal do you work?", "Is any of it missing?", "Who do you think melted the lock?"],
  },
  arrive: [
    { who: "foot", expr: "worried", text: "Kelvin Springs. Smudge, the steam over the pools has frozen solid in the air. The Baron erased the law of heat." },
    { who: "smudge", expr: "thinking", text: "And someone melted the ice lock on the bathhouse safe and took the Heat Medal. With a block of hot metal." },
    { who: "foot", expr: "neutral", text: "Al works aluminium, Ferris iron, Brewster copper. The block was found in the cooling tub. Look at it, and talk to them." },
  ],
  inspect: [
    { who: "smudge", expr: "thinking", text: "A plain grey block, scrubbed clean. No stamp, no shine. Could be any metal in town." },
    { who: "smudge", expr: "thinking", text: "But metals hold heat differently. Heat it up, drop it in water, and the water tells you how much heat it carried." },
    { who: "foot", expr: "neutral", text: "Specific heat! Let's measure it. To the lab." },
  ],
  toLab: { who: "smudge", expr: "determined", text: "To the lab. A balance, a thermometer, a tub of water." },
  afterLab: { who: "foot", expr: "happy", text: "We know the block's metal. Call them to the stand and check their stories." },
  checklist: ["Inspect the safe and the tub", "Measure the block's specific heat"],
  stageLabel: "The bathhouse safe",
  badge: (ev) => ev.badge,
  miss: () => "*That suspect's metal has a different specific heat. Whose matches?",
  stuck: () => "*Your c matches one metal, and each metal belongs to one suspect.",
  confess: {
    al: [
      { expr: "shocked", text: "Oh, that's... that's boiled over, chef." },
      { expr: "nervous", text: "I heated one of my aluminium ingots on the stove and held it to the lock. The Baron said the Medal would make my kitchen the hottest in the hills." },
    ],
    ferris: [
      { expr: "shocked", text: "*CLANK.* ...Rumble." },
      { expr: "nervous", text: "I put an iron fire-bar in the boiler till it glowed. The Baron promised the Medal would keep the bathhouse warm forever. It's freezing now, isn't it." },
    ],
    brewster: [
      { expr: "shocked", text: "*wheeeeeee* Oh dear. Oh dear oh dear." },
      { expr: "nervous", text: "A copper sheet, folded and heated. The Baron said a proper gentleman deserves a proper medal. Most improper of me. I'm sorry." },
    ],
  },
  restore: { glyphs: ["Q", " ", "=", " ", "m", "c", "Δ", "T"], sub: "Heat is back in the book. The steam rises again.",
    card: "Q = m c ΔT", cardSub: "Heat · Chapter 12" },
  solved: (name) => `The block was ${name}'s metal. Its specific heat gave it away.`,
};

export default CASE;
