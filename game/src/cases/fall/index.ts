// Case 10, The Midnight Fall: Hollowmere Manor in a storm. How long Old Tock fell tells you whose balcony.
// Spec: docs/superpowers/specs/2026-10-31-midnight-fall.md. Text rules (§3): lines of 12 words or fewer.
import Phaser from "phaser";
import type { CaseDef } from "../types";
import { FONT, W, H } from "../../consts";
import { sfx } from "../../audio";
import { ColdOpen, coldOpenDone } from "../../scenes/ColdOpen";
import { LabFall } from "../../scenes/LabFall";
import { ghostReveal, exitCheck } from "./finale";
import { FALL, World3 } from "./layout";

// Where things are in the art comes from fall_layout.json (world [x, y, z], run through the district's project()).
const LAB = FALL.district;
const BALCONIES: { id: string; label: string }[] = [
  { id: "rivet", label: "Sir Rivet's armoury" }, { id: "varnish", label: "Lady Varnish's gallery" }, { id: "pendle", label: "Pendle's clock room" }];
const CLUES: { id: string; tag: string; at: World3; w: number; h: number; note: string }[] = [
  { id: "sheet", tag: "SHEET", at: LAB.clues.sheet as World3, w: 90, h: 40, note: "A chalk outline. A white sheet." },
  { id: "gramophone", tag: "RECORDER", at: LAB.clues.gramophone as World3, w: 40, h: 36, note: "It recorded all night." },
  { id: "tower", tag: "TOWER", at: LAB.clues.tower as World3, w: 90, h: 120, note: "Three balconies. Three heights." },
];

/** Clues found this visit, kept across the lab and back. Cleared by a fresh page load. */
const found = new Set<string>();

const CASE: CaseDef = {
  kit: "fall", num: 10, title: "The Midnight Fall", place: "Hollowmere Manor", chapter: "Motion and gravity",
  lab: "LabFall", bg: { glitch: "manor_glitch", restored: "manor_restored" },
  greet: {
    rivet: { who: "rivet", expr: "neutral", text: "Sir Rivet. Armoury. Keep your questions short." },
    varnish: { who: "varnish", expr: "smug", text: "Lady Varnish, darling. Do mind the frame." },
    pendle: { who: "pendle", expr: "nervous", text: "P-Pendle. Clock room. I swear it was the ghost." },
  },
  chips: {
    rivet: ["Your balcony?", "The cry?", "The ghost?"],
    varnish: ["Your balcony?", "The cry?", "The ghost?"],
    pendle: ["Your balcony?", "The cry?", "The ghost?"],
  },
  arrive: [
    { who: "foot", expr: "worried", text: "Hollowmere Manor. Midnight." },
    { who: "smudge", expr: "thinking", text: "They say the Tower Ghost took him." },
  ],
  inspect: [{ who: "foot", expr: "neutral", text: "Three balconies. Three heights." },
    { who: "smudge", expr: "thinking", text: "Lightning reveals clues hidden in the rain." }],
  // the early wrong guess (a nervous Pendle on the top floor looks guilty), then Footnote's "check it" and the way to check
  afterFirst: [
    { who: "smudge", expr: "determined", text: "Pendle's nervous, and his room is highest. It's him!" },
    { who: "foot", expr: "neutral", text: "Check it. A hunch isn't evidence." },
    { who: "foot", expr: "worried", text: "Talk won't crack them. Use the lab." },
  ],
  toLab: { who: "smudge", expr: "determined", text: "The gramophone caught every sound." },
  afterLab: { who: "foot", expr: "happy", text: "Now we know the balcony." },
  checklist: ["Inspect the courtyard", "Time the fall"],
  stageLabel: "Chalk outline",
  badge: (ev) => ev.badge,
  miss: () => "*That oath fits the fall. Find the lie.",
  stuck: () => "*Whose balcony could he fall from?",
  confess: {
    rivet: [{ expr: "shocked", text: "...My balcony. A slip. I never meant it." }],
    varnish: [{ expr: "shocked", text: "...Eleven metres. Oh, darling. You measured." }],
    pendle: [{ expr: "shocked", text: "...Nineteen metres. I... confess." }],
  },
  restore: { glyphs: ["h", " ", "=", " ", "½", "g", "t", "²"], sub: "The law of falling bodies is back in the book.",
    card: "h = ½gt²", cardSub: "Motion · Gravitation", reveal: ghostReveal, after: exitCheck },
  solved: (name) => `${name} did it. No ghost. Just gravity.`,
  assets: { folder: "case10", images: ["manor_glitch", "manor_restored", "lab_tower", "lab_gramophone", "sack", "sheet_ghost"], suspects: ["rivet", "varnish", "pendle"] },
  map: { x: 400, y: 120, icon: "tower" },
  layout: {
    width: LAB.width, cu: LAB.cu, cv: LAB.cv, startX: -330,
    spots: [
      { key: "rivet", x: LAB.hotspots.rivet, markY: 50, markZ: 8 },
      { key: "varnish", x: LAB.hotspots.varnish, markY: 50, markZ: 8 },
      { key: "pendle", x: LAB.hotspots.pendle, markY: 50, markZ: 8 },
      { key: "stage", x: LAB.hotspots.stage, markY: 30, markZ: -40 },
    ],
    suspects: ["rivet", "varnish", "pendle"].map((key) => ({ key, x: LAB.hotspots[key as "rivet"], z: 8 })),
  },
  decorate(scene, P, restored) {
    // this case's own scenes are added here, the first time the district opens, so main.ts needs no edit
    if (!scene.scene.get("LabFall")) scene.scene.add("LabFall", LabFall);
    if (!scene.scene.get("ColdOpen")) scene.scene.add("ColdOpen", ColdOpen);
    if (restored) return;
    // the cold open plays once per load, on top of the paused district
    if (!coldOpenDone()) {
      scene.scene.pause();
      scene.scene.launch("ColdOpen");
    }
    // rain, over everything but the UI
    scene.add.particles(0, 0, "px", {
      x: { min: 0, max: 760 }, y: -10, speedY: { min: 420, max: 520 }, speedX: -70, lifespan: 620, frequency: 14, quantity: 3,
      alpha: { start: 0.55, end: 0.15 }, tint: 0x9bb0d8, scaleY: 5,
    }).setDepth(800);

    // (the sheet on the washing line is in the backdrop; the sheet_ghost sprite appears in the ghost reveal)

    // HUD of clues found
    const at = CLUES.map((c) => P(...c.at));
    const towerX = P(...(LAB.clues.tower as World3)).x;
    const balconyY = BALCONIES.map((b) => P(...(LAB.balconies[b.id as "rivet"] as World3)).y);
    const hud = CLUES.map((c, i) => scene.add.text(8 + i * 62, 26, c.tag, { fontFamily: FONT, fontSize: "8px", color: "#8F8268", backgroundColor: "#0E1938" })
      .setPadding(3, 1, 3, 1).setScrollFactor(0).setDepth(900));
    const refresh = () => CLUES.forEach((c, i) => hud[i].setColor(found.has(c.id) ? "#FAC775" : "#8F8268"));
    refresh();

    // lightning: a flash every 6 to 10 s; clues can be clicked for 600 ms after it
    let litUntil = 0;
    const glows = [...CLUES.filter((c) => c.id !== "tower").map((c, i) => ({ x: at[CLUES.indexOf(c)].x, y: at[CLUES.indexOf(c)].y })), ...balconyY.map((y) => ({ x: towerX, y }))].map((p) =>
      scene.add.image(p.x, p.y, "glow64").setBlendMode(Phaser.BlendModes.ADD).setTint(0xfff0c8).setAlpha(0).setDepth(3));
    const flash = scene.add.rectangle(0, 0, W, H, 0xffffff).setOrigin(0).setScrollFactor(0).setAlpha(0).setDepth(850);
    const strike = () => {
      litUntil = scene.time.now + 600;
      flash.setAlpha(0.6);
      scene.tweens.add({ targets: flash, alpha: 0, duration: 120 });
      scene.tweens.add({ targets: glows, alpha: { from: 0.7, to: 0 }, duration: 600 });
      scene.time.delayedCall(350, () => sfx("rumble"));
      scene.time.delayedCall(Phaser.Math.Between(6000, 10000), strike);
    };
    scene.time.delayedCall(2500, strike);

    const say = (x: number, y: number, text: string) => {
      const t = scene.add.text(x, y, text, { fontFamily: FONT, fontSize: "9px", color: "#0E1938", backgroundColor: "#F2E9CF" })
        .setPadding(4, 1, 4, 1).setOrigin(0.5, 1).setDepth(902);
      scene.tweens.add({ targets: t, y: y - 10, alpha: 0, delay: 900, duration: 500, onComplete: () => t.destroy() });
    };
    const hit = (id: string, x: number, y: number, note: string) => {
      if (scene.time.now > litUntil) return;               // only what a flash lights up
      sfx("chime");
      say(x, y - 8, note);
      if (!found.has(id)) { found.add(id); refresh(); }
    };
    for (const [i, c] of CLUES.entries()) {
      if (c.id === "tower") continue;
      const p = at[i];
      scene.add.zone(p.x, p.y, c.w, c.h).setInteractive().on("pointerdown", () => hit(c.id, p.x, p.y - c.h / 2, c.note));
    }
    for (const [i, b] of BALCONIES.entries()) {
      scene.add.zone(towerX, balconyY[i], 90, 30).setInteractive().on("pointerdown", () => hit("tower", towerX, balconyY[i] - 16, b.label));
    }
  },
};

export default CASE;
