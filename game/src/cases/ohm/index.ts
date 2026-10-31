// Case 6, Ohmtown: Volta's Battery Barn, the Grand Light Board, Ohmar's Resistor Works, Glim's Lamp Shop.
// A voltmeter and an ammeter across the swapped part; R = V / I names the value, and the value names the shop.
import Phaser from "phaser";
import type { CaseDef } from "../types";
import type { CaseData } from "../../api";

const CASE: CaseDef = {
  kit: "ohm", num: 6, title: "The Blackout", place: "Ohmtown", chapter: "Chapter 11: Electricity",
  assets: { folder: "case6", images: ["ohm_glitch", "ohm_restored"], suspects: ["volta", "ohmar", "glim"] },
  bg: { glitch: "ohm_glitch", restored: "ohm_restored" },
  map: { x: 296, y: 220, icon: "bolt" },
  layout: {
    width: 720, cu: 0, cv: 90, startX: -330,
    spots: [
      { key: "volta", x: -260, markY: 50, markZ: 8 },
      { key: "stage", x: -90, markY: 56, markZ: -64 },
      { key: "ohmar", x: 110, markY: 54, markZ: 8 },
      { key: "glim", x: 250, markY: 50, markZ: 8 },
    ],
    suspects: [{ key: "volta", x: -260, z: 8 }, { key: "ohmar", x: 110, z: 8 }, { key: "glim", x: 250, z: 8 }],
  },
  decorate(scene, P, restored) {
    if (restored) {
      // the festival back on: the marquee bulbs chase
      const row = Array.from({ length: 15 }, (_, k) => P(-125 + 5 * k, 55, -61.8));
      const dots = row.map((p) => scene.add.circle(p.x, p.y, 1.5, 0xfffce0, 0).setBlendMode(Phaser.BlendModes.ADD));
      let k = 0;
      scene.time.addEvent({ delay: 120, loop: true, callback: () => { dots.forEach((d, i) => d.setAlpha(i % 5 === k % 5 ? 0.9 : 0)); k++; } });
      return;
    }
    // blackout: a spark crackles on the board now and then
    const at = P(-68, 40, -61);
    const spark = scene.add.image(at.x, at.y, "glow64").setBlendMode(Phaser.BlendModes.ADD).setTint(0xa8c8ff).setScale(0.3).setAlpha(0);
    const crackle = () => {
      spark.setAlpha(0.9).setScale(Phaser.Math.FloatBetween(0.2, 0.45));
      scene.tweens.add({ targets: spark, alpha: 0, duration: 140 });
      scene.time.delayedCall(Phaser.Math.Between(600, 2400), crackle);
    };
    scene.time.delayedCall(800, crackle);
  },
  lab: "CaseLab",
  labSteps: [
    { kind: "say", lines: [
      { who: "foot", expr: "happy", text: "Lab time! We've got the swapped part out of the board. Two meters across it: a voltmeter and an ammeter." },
      { who: "foot", expr: "neutral", text: "Ohm's law: R = V ÷ I. Volts across, amps through. Careful: this ammeter reads in milliamps." },
    ] },
    { kind: "gauge", record: "m",
      intro: [{ who: "smudge", expr: "determined", text: "Meter form! Reading the dials as they settle." }],
      items: (c: CaseData) => [
        { key: "v", label: "Voltmeter across the part", value: c.volts as number, min: 0, max: 12, step: 0.5, unit: "V", style: "dial" as const, labelEvery: 4 },
        { key: "ma", label: "Ammeter through the part", value: c.milliamps as number, min: 0, max: 1200, step: 50, unit: "mA", style: "dial" as const, labelEvery: 4 },
      ],
      done: [{ who: "foot", expr: "neutral", text: "Two readings. Now the notebook. Remember: a thousand milliamps make one amp." }] },
    { kind: "notebook", hint: "*Turn the milliamps into amps first, then R = V ÷ I.",
      note: "1000 mA = 1 A · R = V ÷ I · the slot should hold 100 Ω",
      fields: (c: CaseData, m: Record<string, number>) => [
        { key: "v", label: "Voltage, V", unit: "V", given: m.m_v ?? (c.volts as number) },
        { key: "ma", label: "Current", unit: "mA", given: m.m_ma ?? (c.milliamps as number) },
        { key: "i", label: "Current in amps, I", unit: "A" },
        { key: "r", label: "Resistance, R = V ÷ I", unit: "Ω" },
      ] },
  ],
  greet: {
    volta: { who: "volta", expr: "smug", text: "Volta, Battery Barn! Positively charged to meet you, sparky. Ha! Get it? Ask away." },
    ohmar: { who: "ohmar", expr: "nervous", text: "Oh. A detective. I'm Ohmar, I make resistors. I... resist questions a bit. But go on." },
    glim: { who: "glim", expr: "neutral", text: "Glim. I make lamps. It's very dark tonight, isn't it. I rather like it. Ask, detective." },
  },
  chips: {
    volta: ["What resistors do you stock?", "Is any of your stock missing?", "Who do you think swapped the resistor?"],
    ohmar: ["What resistors do you stock?", "Is any of your stock missing?", "Heard any gossip?"],
    glim: ["What resistors do you stock?", "Is any of your stock missing?", "Who do you think swapped the resistor?"],
  },
  arrive: [
    { who: "foot", expr: "worried", text: "Ohmtown, festival night... and a blackout. Sparks hanging frozen in the air. The Baron erased Ohm's law." },
    { who: "smudge", expr: "thinking", text: "Someone swapped a resistor on the Grand Light Board. The current surged and every bulb in town blew." },
    { who: "foot", expr: "neutral", text: "Volta, Ohmar and Glim each stock one resistor value. Talk to them, and look at the board." },
  ],
  inspect: [
    { who: "smudge", expr: "thinking", text: "The slot's marked 100 Ω. The part in it is the same size, same shape. You can't tell by looking." },
    { who: "smudge", expr: "thinking", text: "But a smaller resistance lets more current through. That's what blew the bulbs." },
    { who: "foot", expr: "neutral", text: "Then measure it. Volts and amps tell you the ohms. To the lab!" },
  ],
  toLab: { who: "smudge", expr: "determined", text: "To the lab. Two meters, one law." },
  afterLab: { who: "foot", expr: "happy", text: "We know the swapped part's value. Call them to the stand and check their stories." },
  checklist: ["Inspect the light board", "Measure the swapped part"],
  stageLabel: "The light board",
  badge: (ev) => ev.badge,
  miss: () => "*That shop's resistors aren't the value we measured. Whose are?",
  stuck: () => "*Your R matches exactly one shop's stock. Find whose.",
  confess: {
    volta: [
      { expr: "shocked", text: "Oh... I'm flat. Completely flat." },
      { expr: "nervous", text: "I swapped in one of my 10 Ω parts. The Baron said a big surge would sell a LOT of new batteries. I didn't think every bulb would go." },
    ],
    ohmar: [
      { expr: "shocked", text: "I... I can't resist any more." },
      { expr: "nervous", text: "It was mine. A 20 Ω. The Baron said the board needed 'a little less resistance'. I always do as I'm told. I'm so sorry." },
    ],
    glim: [
      { expr: "shocked", text: "...Oh. The lights. You turned them on me." },
      { expr: "nervous", text: "I put a 50 Ω part in. I wanted one dark night, just one. The Baron said I'd have it forever. I'm sorry, Ohmtown." },
    ],
  },
  restore: { glyphs: ["V", " ", "=", " ", "I", " ", "R"], sub: "Ohm's law is back in the book. Let there be light.",
    card: "V = I R", cardSub: "Electricity · Chapter 11" },
  solved: (name) => `The swapped part came from ${name}'s stock. Ohm's law proved it.`,
};

export default CASE;
