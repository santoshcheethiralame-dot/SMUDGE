import Phaser from "phaser";
import { W, H, FONT, DISPLAY } from "../consts";
import { makeGlow, makePixel, wait, tween, pageTurn } from "../systems/fx";
import { sfx, music, themeFor, layer, ambience, sting } from "../audio";
import { buttonFeel, punch, shake } from "../systems/juice";
import { vignette } from "../systems/atmosphere";
import { api } from "../api";
import { progress } from "../state";
import { CASES, CASE_ORDER, after } from "../cases";

// The law writes itself back into the page and the district snaps back to normal.
export class Restore extends Phaser.Scene {
  constructor() { super("Restore"); }

  async create() {
    const c = CASES[progress.kit];
    makeGlow(this, "glow64", 64);
    const bw = 720;
    const before = this.add.image(-(bw - W) / 2 - 60, 0, c.bg.glitch).setOrigin(0, 0);
    const after = this.add.image(-(bw - W) / 2 - 60, 0, c.bg.restored).setOrigin(0, 0);
    // the restored district spreads out from the formula in a widening ring, not a crossfade
    const hole = this.make.graphics({}, false);
    after.setMask(hole.createGeometryMask());
    vignette(this, 0.4);
    this.cameras.main.fadeIn(800, 255, 245, 220);
    music("off");
    ambience(c.kit, false);
    await wait(this, 600);
    // the formula writes itself across the sky, one glyph at a time
    const text = this.add.text(W / 2, 70, "", { fontFamily: '"Georgia", serif', fontSize: "44px", fontStyle: "italic", color: "#FFE9B0", stroke: "#0E1938", strokeThickness: 5 })
      .setOrigin(0.5);
    const halo = this.add.image(W / 2, 70, "glow64").setScale(3.4, 1.2).setBlendMode(Phaser.BlendModes.ADD).setTint(0xffd27a).setAlpha(0);
    let s = "";
    for (const g of c.restore.glyphs) {
      s += g;
      text.setText(s);
      if (g.trim()) sfx("tick");
      await wait(this, 200);
    }
    sfx("fanfare");
    this.tweens.add({ targets: halo, alpha: 0.6, duration: 600, yoyo: true, repeat: 2 });
    punch(this, text, 0.12, 120);
    ambience(c.kit, true);
    themeFor(c.kit);
    layer(3);
    const ring = this.add.graphics().setDepth(5);
    const o = { r: 0 };
    let chimed = 0;
    shake(this, 300, 0.004);
    await tween(this, {
      targets: o, r: 560, duration: 1900, ease: "Cubic.easeIn",
      onUpdate: () => {
        hole.clear().fillStyle(0xffffff).fillCircle(W / 2, 70, o.r);
        ring.clear().lineStyle(3, 0xffe9b0, Math.max(0, 1 - o.r / 560)).strokeCircle(W / 2, 70, o.r)
          .lineStyle(8, 0xffd27a, 0.25 * Math.max(0, 1 - o.r / 560)).strokeCircle(W / 2, 70, o.r + 4);
        if (o.r > chimed * 90 && chimed < 6) { chimed++; sfx("sparkle"); }
      },
    });
    after.clearMask(true);
    ring.destroy();
    before.destroy();
    const sub = this.add.text(W / 2, 104, c.restore.sub, { fontFamily: FONT, fontSize: "11px", color: "#F2E9CF" })
      .setOrigin(0.5).setAlpha(0);
    await tween(this, { targets: sub, alpha: 1, duration: 500 });
    await wait(this, 900);

    // Formula Card
    const card = this.add.container(W / 2, 170).setScale(0.2).setAlpha(0);
    const bg = this.add.rectangle(0, 0, 160, 96, 0xf2e9cf).setStrokeStyle(2, 0x0e1938);
    const shine = this.add.rectangle(-40, 0, 14, 110, 0xffffff, 0.35).setAngle(20);
    const t1 = this.add.text(0, -34, "FORMULA CARD", { fontFamily: FONT, fontSize: "10px", color: "#C9302A" }).setOrigin(0.5);
    const t2 = this.add.text(0, -6, c.restore.card, { fontFamily: '"Georgia", serif', fontSize: "22px", fontStyle: "italic", color: "#0E1938" }).setOrigin(0.5);
    const t3 = this.add.text(0, 24, c.restore.cardSub, { fontFamily: FONT, fontSize: "9px", color: "#55361A" }).setOrigin(0.5);
    card.add([bg, shine, t1, t2, t3]);
    sting("evidence");
    await tween(this, { targets: card, scale: 1, alpha: 1, angle: -3, duration: 420, ease: "Back.easeOut" });
    this.tweens.add({ targets: shine, x: 60, duration: 900, repeat: -1, repeatDelay: 1200 });
    await wait(this, 2600);
    this.cameras.main.fadeOut(700, 5, 6, 15);
    await wait(this, 720);
    this.scene.start("CaseSolved");
  }
}

// The case card, then on to the next case (or replay this one with a new culprit).
export class CaseSolved extends Phaser.Scene {
  constructor() { super("CaseSolved"); }

  create() {
    const c = CASES[progress.kit];
    this.cameras.main.fadeIn(600, 5, 6, 15);
    this.add.rectangle(0, 0, W, H, 0x05060f).setOrigin(0);
    makePixel(this);
    ambience("map");
    themeFor("night");
    layer(2);
    this.add.particles(0, 0, "px", {
      x: { min: 0, max: W }, y: -4, speedY: { min: 20, max: 50 }, speedX: { min: -12, max: 12 }, lifespan: 7000, rotate: { min: 0, max: 360 },
      scale: { min: 1.5, max: 3 }, tint: [0xc9302a, 0xfac775, 0xf2e9cf, 0x2e5cad], frequency: 70, quantity: 1, advance: 3000,
    });
    const who = progress.culprit ? api.current?.suspects[progress.culprit]?.name ?? "" : "";
    this.add.text(W / 2, 54, `CASE ${c.num} SOLVED`, { fontFamily: FONT, fontSize: "11px", color: "#C9302A" }).setOrigin(0.5);
    const head = this.add.text(W / 2, 84, c.title, { fontFamily: DISPLAY, fontSize: "32px", color: "#F2E9CF" }).setOrigin(0.5).setScale(0.3).setAlpha(0);
    this.tweens.add({ targets: head, scale: 1, alpha: 1, duration: 360, ease: "Back.easeOut", delay: 250 });
    const stampT = this.add.text(W / 2 + 120, 60, "SOLVED", { fontFamily: DISPLAY, fontSize: "18px", color: "#C9302A", stroke: "#F2E9CF", strokeThickness: 2 })
      .setOrigin(0.5).setAngle(-14).setScale(3).setAlpha(0);
    this.tweens.add({ targets: stampT, scale: 1, alpha: 0.9, duration: 160, ease: "Quad.easeIn", delay: 750,
      onStart: () => this.time.delayedCall(150, () => { sfx("stamp"); shake(this, 120, 0.006); }) });
    this.add.text(W / 2, 118, `${c.solved(who)}\nEvery replay picks a new culprit and new numbers.`, { fontFamily: FONT, fontSize: "10px", color: "#9AA6C8", align: "center", lineSpacing: 4 })
      .setOrigin(0.5);
    this.add.sprite(W / 2, 214, "smudge", "celebrate/S/0").setOrigin(0.5, 60 / 64).play("celebrate_S");

    const go = (kit: string, from: string) => {
      const next = CASES[kit];
      progress.reset(kit);
      api.current = null;
      pageTurn(this, () => { this.scene.start("District", { kit: next.kit, from }); });
    };
    const button = (x: number, label: string, fill: string, fn: () => void) => {
      const b = this.add.text(x, 246, label, { fontFamily: FONT, fontSize: "10px", color: "#FFFFFF", backgroundColor: fill })
        .setPadding(10, 4, 10, 4).setOrigin(0.5).setInteractive({ useHandCursor: true });
      buttonFeel(this, b);
      b.on("pointerup", fn);
      return b;
    };
    const nxt = after(c.kit);
    const dx = nxt ? 0 : 60;          // two buttons sit centred when there's no next case
    button(W / 2 - 120 + dx, "Replay", "#2E5CAD", () => go(c.kit, "new"));
    button(W / 2 + dx, "Casebook map", "#55361A", () => pageTurn(this, () => { this.scene.start("Map"); }));
    if (CASE_ORDER.every((k) => progress.solvedCases.has(k))) {
      this.add.text(W / 2, 142, "Every law is back in the book. But the Baron is still out there...", {
        fontFamily: FONT, fontSize: "10px", color: "#FAC775" }).setOrigin(0.5);
    }
    if (nxt) {
      const n = button(W / 2 + 128, `Next: ${nxt.place} ▸`, "#C9302A", () => go(nxt.kit, "next"));
      this.tweens.add({ targets: n, y: n.y - 2, duration: 600, yoyo: true, repeat: -1, ease: "Sine.easeInOut" });
    }
  }
}
