// Case 3, Echo Valley: the bell tower on its hill, Reverb's radio shack, Thump's bandstand, Coil's post office.
// Storm videos, flash-to-boom delays, d = 340 t.
import Phaser from "phaser";
import type { CaseDef } from "../types";
import type { CaseData } from "../../api";

const NAMES: Record<string, string> = { reverb: "Reverb", thump: "Thump", coil: "Coil" };

const CASE: CaseDef = {
  kit: "sound", num: 3, title: "The Thunder Alibi", place: "Echo Valley", chapter: "Chapter 11: Sound",
  assets: { folder: "case3", images: ["valley_glitch", "valley_restored"], suspects: ["reverb", "thump", "coil"] },
  bg: { glitch: "valley_glitch", restored: "valley_restored" },
  map: { x: 112, y: 146, icon: "bell" },
  layout: {
    width: 720, cu: 0, cv: 90, startX: -330,
    spots: [
      { key: "reverb", x: -260, markY: 50, markZ: 8 },
      { key: "stage", x: -90, markY: 30, markZ: -96 },
      { key: "thump", x: 110, markY: 50, markZ: 8 },
      { key: "coil", x: 250, markY: 52, markZ: 8 },
    ],
    suspects: [{ key: "reverb", x: -260, z: 8 }, { key: "thump", x: 110, z: 8 }, { key: "coil", x: 250, z: 8 }],
  },
  decorate(scene, _P, restored) {
    if (restored) {
      // after the storm: a few fireflies over the hill
      scene.add.particles(0, 0, "px", {
        x: { min: 120, max: 520 }, y: { min: 110, max: 190 }, lifespan: 2400, alpha: { values: [0, 1, 0] },
        speedX: { min: -6, max: 6 }, speedY: { min: -4, max: 4 }, tint: 0xfff3a0, frequency: 260, quantity: 1,
      });
      return;
    }
    // rain, slanting, all the way across the valley
    scene.add.particles(0, -10, "px", {
      x: { min: -40, max: 760 }, speedY: { min: 260, max: 320 }, speedX: -60, lifespan: 1100,
      scaleX: 1, scaleY: { min: 4, max: 7 }, rotate: 11, alpha: { min: 0.25, max: 0.55 }, tint: 0xb8c8f0, frequency: 14, quantity: 2,
    }).setDepth(800);
    // lightning now and then; the thunder follows a moment later, as it should
    const flash = scene.add.rectangle(0, 0, 720, 270, 0xdde6ff, 0).setOrigin(0).setDepth(799);
    const strike = () => {
      flash.setAlpha(0.5);
      scene.tweens.add({ targets: flash, alpha: 0, duration: 320 });
      scene.time.delayedCall(Phaser.Math.Between(6000, 11000), strike);
    };
    scene.time.delayedCall(2500, strike);
  },
  lab: "CaseLab",
  labSteps: [
    { kind: "say", lines: [
      { who: "foot", expr: "happy", text: "Lab time! Everyone in Echo Valley posted a storm video to the Storm Gram. Flash first, then the boom." },
      { who: "foot", expr: "neutral", text: "Light gets to you instantly. Sound is slow: 340 metres every second. So the gap between flash and boom says how far away you were." },
    ] },
    { kind: "stopwatch", record: "t",
      intro: [{ who: "smudge", expr: "determined", text: "Stopwatch form. One tap at the flash, one at the boom. Three videos." }],
      clips: (c: CaseData) => Object.entries(c.delays as Record<string, number>).map(([sid, s]) => ({ key: sid, label: `${NAMES[sid] ?? sid}'s video`, seconds: s, style: "flashboom" as const })),
      done: [{ who: "foot", expr: "neutral", text: "Three delays. Now turn each one into a distance in the notebook." }] },
    { kind: "notebook", hint: "*Distance = speed x time. Sound does 340 m every second. One trip, from the strike to the camera.",
      fields: (c: CaseData, m: Record<string, number>) => Object.keys(c.delays as Record<string, number>).flatMap((sid) => [
        { key: `t_${sid}`, label: `${NAMES[sid] ?? sid}: delay`, unit: "s", given: m[`t_${sid}`] ?? (c.delays as Record<string, number>)[sid] },
        { key: `d_${sid}`, label: `${NAMES[sid] ?? sid}: distance`, unit: "m" },
      ]) },
  ],
  greet: {
    reverb: { who: "reverb", expr: "smug", text: "Good evening, listeners! Reverb, Echo Valley Radio. And you must be the detective. Ooh, dramatic." },
    thump: { who: "thump", expr: "neutral", text: "Thump. Bandleader. Storm wrecked the rehearsal. Ask. Quick." },
    coil: { who: "coil", expr: "nervous", text: "Coil, post! Boing. Sorry, I bounce when I'm nervous. Not that I'm nervous. Ask away!" },
  },
  chips: {
    reverb: ["Where did you film the storm from?", "How far from the tower?", "Who do you think took the fork?"],
    thump: ["Where did you film the storm from?", "How far from the tower?", "Heard any gossip?"],
    coil: ["Where did you film the storm from?", "How far from the tower?", "Who do you think took the fork?"],
  },
  arrive: [
    { who: "foot", expr: "worried", text: "Echo Valley. Listen, Smudge... nothing. The bells swing and make no sound. The Baron erased the law of sound." },
    { who: "smudge", expr: "thinking", text: "And up on the bell tower, the Silver Tuning Fork is gone. Taken in last night's storm, right when the lightning struck." },
    { who: "foot", expr: "neutral", text: "Reverb, Thump and Coil all say they were home. Question them, and look at the tower." },
  ],
  inspect: [
    { who: "smudge", expr: "thinking", text: "Scorch marks on the lightning rod. The fork's stand is empty, still humming faintly." },
    { who: "smudge", expr: "thinking", text: "Everyone filmed the storm. If one of those videos was shot right here..." },
    { who: "foot", expr: "neutral", text: "Then its thunder would arrive almost with the flash. Let's time the videos." },
  ],
  toLab: { who: "smudge", expr: "determined", text: "To the lab. Three videos, one stopwatch." },
  afterLab: { who: "foot", expr: "happy", text: "Every video has a distance now. Call them to the stage and check their stories." },
  checklist: ["Inspect the bell tower", "Time the storm videos"],
  stageLabel: "The bell tower",
  badge: (ev) => ev.badge,
  miss: () => "*That video matches where they said they were. Find the one that doesn't.",
  stuck: () => "*Line up each suspect's sworn distance with the distance from their video. Only one is off.",
  confess: {
    reverb: [
      { expr: "shocked", text: "...Dead air. I've never had dead air in my life." },
      { expr: "nervous", text: "I was under the tower doing a live storm report. The fork was RIGHT there. The Baron said nobody would hear a thing. Nobody could." },
    ],
    thump: [
      { expr: "shocked", text: "Off. The. Beat." },
      { expr: "nervous", text: "I wanted the perfect pitch for the band. The Baron said with sound gone, nobody would ever know the fork was missing." },
    ],
    coil: [
      { expr: "shocked", text: "Boi... oing." },
      { expr: "nervous", text: "I was delivering to the tower when the flash hit. I just... grabbed it. The Baron said it'd never be missed." },
    ],
  },
  restore: { glyphs: ["d", " ", "=", " ", "v", " ", "×", " ", "t"], sub: "The law of sound is back in the book. Listen: the bells.",
    card: "d = v × t", cardSub: "Sound · Chapter 11" },
  solved: (name) => `${name} was under the tower. The thunder proved it.`,
};

export default CASE;
