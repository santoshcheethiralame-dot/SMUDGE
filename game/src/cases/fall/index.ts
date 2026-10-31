// Case 10, The Midnight Fall: Hollowmere Manor in a storm. How long Old Tock fell tells you whose balcony.
// Spec: docs/superpowers/specs/2026-10-31-midnight-fall.md. Text rules (§3): lines of 12 words or fewer.
import Phaser from "phaser";
import type { CaseDef } from "../types";
import { FONT, W, H } from "../../consts";
import { sfx } from "../../audio";
import { ColdOpen, coldOpenDone } from "../../scenes/ColdOpen";
import { LabFall } from "../../scenes/LabFall";
import { ghostReveal, exitCheck } from "./finale";

// The backdrop art is 720x270 and the tower stands on its right third (art/world/placeholder_fall.py).
const TOWER = { x: 630, balconies: [{ id: "rivet", y: 163, label: "Sir Rivet's armoury" },
  { id: "varnish", y: 133, label: "Lady Varnish's gallery" }, { id: "pendle", y: 90, label: "Pendle's clock room" }] };
const CLUES: { id: string; tag: string; x: number; y: number; w: number; h: number; note: string }[] = [
  { id: "sheet", tag: "SHEET", x: 505, y: 206, w: 90, h: 40, note: "A chalk outline. A white sheet." },
  { id: "gramophone", tag: "RECORDER", x: 443, y: 196, w: 40, h: 36, note: "It recorded all night." },
  { id: "tower", tag: "TOWER", x: TOWER.x, y: 115, w: 90, h: 120, note: "Three balconies. Three heights." },
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
  inspect: [{ who: "foot", expr: "neutral", text: "Three balconies. Three heights." }],
  toLab: { who: "smudge", expr: "determined", text: "The gramophone heard everything." },
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
  assets: { folder: "case10", images: ["manor_glitch", "manor_restored", "lab_tower", "lab_gramophone"], suspects: ["rivet", "varnish", "pendle"] },
  map: { x: 400, y: 120, icon: "tower" },
  layout: {
    width: 720, cu: 0, cv: 90, startX: -330,
    spots: [
      { key: "rivet", x: -250, markY: 50, markZ: 8 },
      { key: "varnish", x: -120, markY: 50, markZ: 8 },
      { key: "pendle", x: 20, markY: 50, markZ: 8 },
      { key: "stage", x: 145, markY: 30, markZ: -40 },
    ],
    suspects: [{ key: "rivet", x: -250, z: 8 }, { key: "varnish", x: -120, z: 8 }, { key: "pendle", x: 20, z: 8 }],
  },
  decorate(scene, _P, restored) {
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

    // the sheet on the washing line flaps
    const sheet = scene.add.rectangle(140, 126, 56, 40, 0xebebf5).setOrigin(0.5, 0).setAlpha(0.9).setDepth(2);
    scene.tweens.add({ targets: sheet, angle: { from: -4, to: 4 }, scaleX: { from: 1, to: 0.9 }, duration: 700, yoyo: true, repeat: -1, ease: "Sine.easeInOut" });

    // HUD of clues found
    const hud = CLUES.map((c, i) => scene.add.text(8 + i * 62, 26, c.tag, { fontFamily: FONT, fontSize: "8px", color: "#8F8268", backgroundColor: "#0E1938" })
      .setPadding(3, 1, 3, 1).setScrollFactor(0).setDepth(900));
    const refresh = () => CLUES.forEach((c, i) => hud[i].setColor(found.has(c.id) ? "#FAC775" : "#8F8268"));
    refresh();

    // lightning: a flash every 6 to 10 s; clues can be clicked for 600 ms after it
    let litUntil = 0;
    const glows = [...CLUES.map((c) => ({ x: c.x, y: c.y })), ...TOWER.balconies.map((b) => ({ x: TOWER.x, y: b.y }))].map((p) =>
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
    for (const c of CLUES.filter((c) => c.id !== "tower")) {
      scene.add.zone(c.x, c.y, c.w, c.h).setInteractive().on("pointerdown", () => hit(c.id, c.x, c.y - c.h / 2, c.note));
    }
    for (const b of TOWER.balconies) {
      scene.add.zone(TOWER.x, b.y, 90, 30).setInteractive().on("pointerdown", () => hit("tower", TOWER.x, b.y - 16, b.label));
    }
  },
};

export default CASE;
