// Case 1, Buoyant Bay: the pier, the sinking paper boats, the crown on its cushion.
import Phaser from "phaser";
import type { CaseDef } from "../types";
import { dust } from "../../systems/fx";
import { progress } from "../../state";

const CASE: CaseDef = {
    kit: "density", num: 1, title: "The Forged Crown", place: "Buoyant Bay", chapter: "Chapter 9: Density",
    lab: "Lab", bg: { glitch: "bay_flooded", restored: "bay_restored" },
    greet: {
      karat: { who: "karat", expr: "smug", text: "Ah, a detective. With a hat. How quaint. Karat, royal jeweller. Do be quick, the bay is ruining my shine." },
      cyl: { who: "cyl", expr: "neutral", text: "Cyl. Harbour master. Boats are sinking, so make it snappy." },
      bob: { who: "bob", expr: "smug", text: "Ahoy! Bob, buoy about town. I've heard EVERYTHING today. Ask away!" },
    },
    chips: {
      karat: ["Where were you today?", "Do you keep any metal?", "Who handled the crown?"],
      cyl: ["Where were you today?", "Do you keep any metal?", "Who handled the crown?"],
      bob: ["Where were you today?", "Do you keep any metal?", "Heard any gossip?"],
    },
    arrive: [
      { who: "foot", expr: "worried", text: "Buoyant Bay. Look at the boats, Smudge. They're going under, slowly. No density, no floating." },
      { who: "smudge", expr: "thinking", text: "And the crown on that stage is the town's pride and joy. Which somebody swapped." },
      { who: "foot", expr: "neutral", text: "Karat, Cyl and Bob all handled it today. Talk to them, and look at the crown up close." },
      { who: "narrator", text: "Tap a suspect to question them. You can type ANY question; each suspect is its own AI agent and only knows their own story." },
    ],
    inspect: [
      { who: "smudge", expr: "thinking", text: "The Harbour Crown. Gold. Or gold-coloured, anyway." },
      { who: "smudge", expr: "thinking", text: "It feels... light. Lighter than something this size should be, if it's really gold." },
      { who: "foot", expr: "neutral", text: "Gut feelings don't hold up on a case board. Measure it! Density is mass divided by volume." },
    ],
    toLab: { who: "smudge", expr: "determined", text: "Right. To the lab bench. Beaker form, here I come." },
    afterLab: { who: "foot", expr: "happy", text: "Evidence in hand! When you're ready, call everyone to the stage." },
    checklist: ["Inspect the crown", "Measure its density"],
    stageLabel: "The crown",
    badge: (ev) => ev.badge,
    miss: (ev) => `*That statement doesn't clash with a ${ev.label.split(":")[1]} crown. Look for the one that CAN'T be true.`,
    stuck: (ev) => { const m = ev.label.split(":")[1]; return `*Think: the fake is ${m}. Who keeps ${m}? And what did they swear about it?`; },
    confess: {
      karat: [
        { expr: "shocked", text: "I... how vulgar. Measuring a crown? Who MEASURES a crown?" },
        { expr: "nervous", text: "Fine. My silver offcuts. Melted, gilded, swapped at dawn. The Rubber Baron promised me the real gold." },
      ],
      cyl: [
        { expr: "shocked", text: "Blast. Blast and barnacles." },
        { expr: "nervous", text: "Two of my lead weights. Swapped it in the vault at noon. The Baron said nobody would ever measure it." },
      ],
      bob: [
        { expr: "shocked", text: "Ding... dong." },
        { expr: "nervous", text: "My spare brass fittings. Swapped it on the way to the stage. The Baron said it'd be a laugh. It isn't, is it." },
      ],
    },
    restore: { glyphs: ["ρ", " ", "=", " ", "m", " ", "/", " ", "V"], sub: "The law of density is back in the book.", card: "ρ = m / V", cardSub: "Density · Chapter 9" },
    solved: (name) => `${name} swapped it. Density proved it.`,
    assets: { folder: "case1", images: ["bay_flooded", "bay_restored", "bench", "boat_s", "boat_m", "boat_l", "crown"],
      suspects: ["karat", "cyl", "bob"] },
    map: { x: 92, y: 96, icon: "crown" },
    layout: {
      width: 720, cu: 0, cv: 90, startX: -300,
      spots: [
        { key: "cyl", x: -228, markY: 50, markZ: 8 },
        { key: "karat", x: -60, markY: 40, markZ: 8 },
        { key: "stage", x: 60, markY: 46, markZ: -8 },
        { key: "bob", x: 214, markY: 46, markZ: 8 },
      ],
      suspects: [{ key: "cyl", x: -228, z: 8 }, { key: "karat", x: -60, z: 8 }, { key: "bob", x: 214, z: 8 }],
    },
    decorate(scene, P, restored) {
      // paper boats in the bay, slowly going down (they bob, settle, and bubble)
      const boats: [string, number, number, number][] = [["boat_m", 190, -95, 0], ["boat_l", 300, -140, 1], ["boat_s", -170, -60, 2], ["boat_s", 330, -45, 3]];
      for (const [key, x, z, i] of boats) {
        const at = P(x, restored ? -14 : -3, z);
        const b = scene.add.image(at.x, at.y + (restored ? 0 : 6), key).setOrigin(0.5, 0.86);
        if (!restored) {
          b.setAngle(i % 2 ? 9 : -7);
          scene.tweens.add({ targets: b, y: "+=3", angle: b.angle * 1.4, duration: 2600 + i * 400, yoyo: true, repeat: -1, ease: "Sine.easeInOut" });
          scene.add.particles(at.x, at.y + 2, "px", {
            x: { min: -10, max: 10 }, speedY: { min: -14, max: -6 }, lifespan: 1400, alpha: { start: 0.9, end: 0 },
            tint: 0xbfe4ff, frequency: 420 + i * 90, quantity: 1,
          });
        } else {
          scene.tweens.add({ targets: b, y: "-=2", duration: 1800 + i * 300, yoyo: true, repeat: -1, ease: "Sine.easeInOut" });
        }
      }
      const lantern = P(-250, 177, -120);
      const lg = scene.add.image(lantern.x, lantern.y, "glow64").setScale(0.8).setBlendMode(Phaser.BlendModes.ADD).setTint(0xffd27a).setAlpha(0.6);
      scene.tweens.add({ targets: lg, alpha: 0.3, duration: 1200, yoyo: true, repeat: -1 });
      dust(scene, 0, 40, 720, 150, 0xffe0a8, 40);
      // the crown on its cushion (it goes to the lab once measured)
      const cushion = P(60, 31, -8);
      scene.add.image(cushion.x, cushion.y, "crown").setOrigin(0.5, 0.8).setVisible(!progress.labDone || restored);
      const glint = scene.add.image(cushion.x + 4, cushion.y - 10, "glow64").setScale(0.18).setBlendMode(Phaser.BlendModes.ADD).setTint(0xfff1b0);
      scene.tweens.add({ targets: glint, alpha: 0, scale: 0.05, duration: 600, yoyo: true, repeat: -1, repeatDelay: 1800 });
    },
};

export default CASE;
