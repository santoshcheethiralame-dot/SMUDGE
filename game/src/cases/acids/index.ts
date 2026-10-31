// Case 8, Acid Alley: Citrine's cordial stand, the Mayor's fountain, Bicarb's bakery, Sudsy's laundry.
// Indicator on the fountain and on every product; undo the tenfold dilution and one product matches.
import Phaser from "phaser";
import type { CaseDef } from "../types";
import type { CaseData } from "../../api";

const PRODUCTS: Record<string, string> = { citrine: "Lemon cordial", bicarb: "Baking soda", sudsy: "Soap flakes" };

const CASE: CaseDef = {
  kit: "acids", num: 8, title: "The Colour Swap", place: "Acid Alley", chapter: "Chapter 2: Acids, Bases and Salts",
  assets: { folder: "case8", images: ["acids_glitch", "acids_restored"], suspects: ["citrine", "bicarb", "sudsy"] },
  bg: { glitch: "acids_glitch", restored: "acids_restored" },
  map: { x: 306, y: 140, icon: "flask" },
  layout: {
    width: 720, cu: 0, cv: 90, startX: -330,
    spots: [
      { key: "citrine", x: -260, markY: 46, markZ: 8 },
      { key: "stage", x: -90, markY: 44, markZ: -50 },
      { key: "bicarb", x: 110, markY: 46, markZ: 8 },
      { key: "sudsy", x: 250, markY: 46, markZ: 8 },
    ],
    suspects: [{ key: "citrine", x: -260, z: 8 }, { key: "bicarb", x: 110, z: 8 }, { key: "sudsy", x: 250, z: 8 }],
  },
  decorate(scene, P, restored) {
    // the fountain's jets catch the light; soap bubbles drift down the alley from the laundry
    const jet = P(-90, 26, -50);
    scene.add.particles(jet.x, jet.y, "px", {
      speed: { min: 10, max: 22 }, angle: { min: 200, max: 340 }, gravityY: 60, lifespan: 700, alpha: { start: 0.8, end: 0 },
      tint: restored ? [0x4ebc6a, 0xe6fff0] : [0xf4a04a, 0xfff0e0], frequency: 60, quantity: 1,
    });
    const bub = P(268, 14, -70);
    scene.add.particles(bub.x, bub.y, "px", {
      speedX: { min: -22, max: -8 }, speedY: { min: -10, max: 4 }, lifespan: 4200, scale: { min: 1, max: 2.5 },
      alpha: { start: 0.7, end: 0 }, tint: 0xeaf4ff, frequency: 420, quantity: 1,
    });
    void Phaser;
  },
  lab: "CaseLab",
  labSteps: [
    { kind: "say", lines: [
      { who: "foot", expr: "happy", text: "Lab time! Universal indicator turns a colour for every pH. Below 7 is an acid, 7 is neutral, above 7 is a base." },
      { who: "foot", expr: "neutral", text: "We'll test the fountain, then a sample of every product sold in the alley." },
    ] },
    { kind: "dropper", record: "ph",
      intro: [{ who: "smudge", expr: "determined", text: "Dropper form! A few drops in each tube, then match the colour on the chart." }],
      samples: (c: CaseData) => [
        { key: "fountain", label: "Fountain", ph: c.fountain_ph as number },
        ...Object.entries(c.products as Record<string, number>).map(([sid, ph]) => ({ key: sid, label: PRODUCTS[sid] ?? sid, ph })),
      ],
      done: [
        { who: "smudge", expr: "thinking", text: "Hm. The fountain doesn't match any of the three products." },
        { who: "foot", expr: "neutral", text: "Because it's DILUTED. A 10-litre can went into a fountain that now holds 100 litres. Dilution drags pH toward 7." },
      ] },
    { kind: "notebook", hint: "*How many times was the can diluted? Each tenfold dilution moves pH one step toward 7, so step back the other way.",
      note: "×10 dilution = 1 pH step toward 7 · below 7 acid · above 7 base",
      fields: (c: CaseData, m: Record<string, number>) => [
        { key: "ph", label: "Fountain's pH now", unit: "", given: m.ph_fountain ?? (c.fountain_ph as number) },
        { key: "poured", label: "Can poured in", unit: "L", given: c.poured_l as number },
        { key: "total", label: "Fountain now holds", unit: "L", given: c.total_l as number },
        { key: "factor", label: "Diluted how many times?", unit: "×" },
        { key: "shift", label: "pH steps it moved", unit: "" },
        { key: "before", label: "pH before it went in", unit: "" },
      ] },
  ],
  greet: {
    citrine: { who: "citrine", expr: "smug", text: "Citrine, lemon cordial, best in the alley. Sharp, sweet, and I don't do refunds. Ask away, sleuth." },
    bicarb: { who: "bicarb", expr: "nervous", text: "Oh! Um, hello. I'm Bicarb. I do the bread. Sorry, I fizz a bit when I'm nervous." },
    sudsy: { who: "sudsy", expr: "smug", text: "Sudsy, laundry! Ooh, a detective, how exciting. Ask me anything. I'll come clean!" },
  },
  chips: {
    citrine: ["What do you sell?", "Where were you last night?", "Who do you think spiked the fountain?"],
    bicarb: ["What do you sell?", "Where were you last night?", "Heard any gossip?"],
    sudsy: ["What do you sell?", "Where were you last night?", "Who do you think spiked the fountain?"],
  },
  arrive: [
    { who: "foot", expr: "worried", text: "Acid Alley. Smudge, the lemons in that crate are blowing soap bubbles. The Baron erased acids and bases." },
    { who: "smudge", expr: "thinking", text: "And the Mayor's fountain has gone a nasty colour. It's kept neutral, glowing green. Someone tipped something in." },
    { who: "foot", expr: "neutral", text: "Citrine sells lemon cordial, Bicarb baking soda, Sudsy soap flakes. Talk to them, and look at the fountain." },
  ],
  inspect: [
    { who: "smudge", expr: "thinking", text: "An empty 10-litre can by the basin, rinsed out. Whatever was in it is in the fountain now." },
    { who: "smudge", expr: "thinking", text: "The koi have turned the colour of the water. The water's colour IS the indicator talking." },
    { who: "foot", expr: "neutral", text: "Then let's read it properly. Samples, indicator, a pH chart. To the lab!" },
  ],
  toLab: { who: "smudge", expr: "determined", text: "To the lab. One fountain, three products, one chart." },
  afterLab: { who: "foot", expr: "happy", text: "We know what went into the fountain. Call them to the stand and check their stories." },
  checklist: ["Inspect the fountain", "Test the fountain's pH"],
  stageLabel: "The fountain",
  badge: (ev) => ev.badge,
  miss: () => "*That product's pH doesn't match what went in. Whose does?",
  stuck: () => "*Undo the dilution: the pH before it went in matches exactly one product.",
  confess: {
    citrine: [
      { expr: "shocked", text: "...That's sour. That's really sour." },
      { expr: "nervous", text: "I poured a can of cordial in. The Baron said the koi would turn lemon yellow and everyone would want my cordial. Nobody wants orange fish." },
    ],
    bicarb: [
      { expr: "shocked", text: "*fizzzzzz*" },
      { expr: "nervous", text: "It was me. A can of soda water from the bakery. The Baron said it'd make the fountain bubble like a cake. I just wanted it to rise." },
    ],
    sudsy: [
      { expr: "shocked", text: "Oh. Oh, I'm in a lather now." },
      { expr: "nervous", text: "I tipped my soap flakes in. The Baron said a sparkling-clean fountain would win the Mayor's prize. I've made a terrible stain." },
    ],
  },
  restore: { glyphs: ["p", "H", " ", "7", " ", "=", " ", "n", "e", "u", "t", "r", "a", "l"], sub: "Acids and bases are back in the book. The fountain glows green.",
    card: "pH < 7 acid · 7 neutral · > 7 base", cardSub: "Acids, Bases and Salts · Chapter 2" },
  solved: (name) => `${name}'s product went into the fountain. The indicator told on it.`,
};

export default CASE;
