// Case 2, Motion Mesa: Slope Hill, Braking Bend and its three skids, Rolla's pie shop, the Derby gate.
import Phaser from "phaser";
import type { CaseDef } from "../types";
import { dust } from "../../systems/fx";

const SLOPE = 80 / 300;   // Slope Hill: matches art/world/scene_mesa.py

const CASE: CaseDef = {
    kit: "motion", num: 2, title: "The Skid at Braking Bend", place: "Motion Mesa", chapter: "Chapter 8: Motion",
    lab: "LabMotion", bg: { glitch: "mesa_glitch", restored: "mesa_restored" },
    greet: {
      dash: { who: "dash", expr: "smug", text: "Dash. Courier. Magnitude AND direction. I've got letters going stale, so, quick questions." },
      rolla: { who: "rolla", expr: "neutral", text: "Oh, hello, love! Rolla. I bake the Derby pies. Mind the crumbs, I'm still warm." },
      mu: { who: "mu", expr: "neutral", text: "Mu. Slope inspector. I measure friction. Ask your questions. Slowly." },
    },
    chips: {
      dash: ["How fast were you going?", "Which skid is yours?", "Who do you think did it?"],
      rolla: ["How fast were you going?", "Which skid is yours?", "Heard any gossip?"],
      mu: ["How fast were you going?", "Which skid is yours?", "Who do you think did it?"],
    },
    arrive: [
      { who: "foot", expr: "worried", text: "Motion Mesa. Look, Smudge: pebbles sliding UP the hill. No equations of motion, nothing knows how to stop." },
      { who: "smudge", expr: "thinking", text: "And down at Braking Bend, the Trophy Tower's flat. The Derby's tomorrow." },
      { who: "foot", expr: "neutral", text: "Dash, Rolla and Mu all came down Slope Hill tonight. Question them, and look at the bend." },
    ],
    inspect: [
      { who: "smudge", expr: "thinking", text: "Three skids, all starting at the white line. Twin skate lines, a chevron tread, a broad scuff." },
      { who: "smudge", expr: "thinking", text: "One of them goes on a LOT longer than the others..." },
      { who: "foot", expr: "neutral", text: "Long doesn't prove fast until you know how hard this road brakes. Test it, then measure every skid." },
    ],
    toLab: { who: "smudge", expr: "determined", text: "To the lab. Stopwatch first, then the tape." },
    afterLab: { who: "foot", expr: "happy", text: "Every skid has a speed now. Call the riders to the stage and check their oaths." },
    checklist: ["Inspect the skids", "Brake test and measure"],
    stageLabel: "Braking Bend",
    badge: (ev) => ev.badge,
    miss: () => "*That rider's oath matches their skid. Find the sworn speed the skids make impossible.",
    stuck: () => "*Line up each rider's sworn speed with the speed from their skid. Only one doesn't match.",
    confess: {
      dash: [
        { expr: "shocked", text: "Wh... you MEASURED it? Nobody measures a skid!" },
        { expr: "nervous", text: "Fine. I was late. Big magnitude, wrong direction. The Baron said friction would catch me. It didn't." },
      ],
      rolla: [
        { expr: "shocked", text: "Oh, crumbs." },
        { expr: "nervous", text: "The pies were going cold, love. I let myself roll. The Baron swore the bend would hold me. It didn't." },
      ],
      mu: [
        { expr: "shocked", text: "...That is a very accurate number." },
        { expr: "nervous", text: "I was testing the new slope. I couldn't... stop. The Baron told me friction would hold. It didn't." },
      ],
    },
    restore: { glyphs: ["v", "²", " ", "=", " ", "u", "²", " ", "+", " ", "2", "a", "s"], sub: "The equations of motion are back in the book.",
      card: "v² = u² + 2as", cardSub: "Motion · Chapter 8" },
    solved: (name) => `${name} came in too fast. The skids proved it.`,
    assets: { folder: "case2", images: ["mesa_glitch", "mesa_restored", "lab_track", "lab_plate", "cart"], suspects: ["dash", "rolla", "mu"] },
    map: { x: 158, y: 172, icon: "skid" },
    layout: {
      width: 720, cu: 0, cv: 90, startX: -320,
      spots: [
        { key: "mu", x: -280, markY: 44, markZ: 8 },
        { key: "dash", x: -170, markY: 50, markZ: 8 },
        { key: "stage", x: 10, markY: 12, markZ: -40 },
        { key: "rolla", x: 175, markY: 44, markZ: 8 },
      ],
      suspects: [{ key: "mu", x: -280, z: 8 }, { key: "dash", x: -170, z: 8 }, { key: "rolla", x: 175, z: 8 }],
    },
    decorate(scene, P, restored) {
      dust(scene, 0, 60, 720, 150, 0xffc890, 46);
      // the setting sun breathes a little
      const sun = P(250, 40, -330);
      const glow = scene.add.image(sun.x, sun.y, "glow64").setScale(2.4).setBlendMode(Phaser.BlendModes.ADD).setTint(0xffb070).setAlpha(0.35);
      scene.tweens.add({ targets: glow, alpha: 0.18, scale: 2.1, duration: 2400, yoyo: true, repeat: -1, ease: "Sine.easeInOut" });
      if (restored) return;
      // friction flickers: grit slides UP Slope Hill and never stops
      for (const [x0, z] of [[-110, -40], [-200, -58], [-300, -30]] as const) {
        const a = P(x0, (-60 - x0) * SLOPE + 1, z), b = P(x0 - 40, (-60 - (x0 - 40)) * SLOPE + 1, z);
        const ang = Phaser.Math.RadToDeg(Math.atan2(b.y - a.y, b.x - a.x));
        scene.add.particles(a.x, a.y, "px", {
          angle: ang, speed: { min: 14, max: 26 }, lifespan: 2600, alpha: { start: 1, end: 0 }, scale: { start: 1.6, end: 1 },
          tint: [0x928898, 0x9c8ed0], frequency: 520, quantity: 1,
        });
      }
    },
};

export default CASE;
