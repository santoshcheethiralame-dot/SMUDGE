import Phaser from "phaser";
import { W, H, FONT, DISPLAY, FEET_ORIGIN } from "../consts";
import { Dialogue, Who } from "../systems/dialogue";
import { makeGlow, makeCone, makePixel, wait, tween } from "../systems/fx";
import { sfx, music, themeFor, layer, ambience, sting } from "../audio";
import { api } from "../api";
import { progress, Evidence } from "../state";
import { CASES, CaseContent } from "../cases";
import { inkIn } from "../systems/transition";
import { buttonFeel, flash, hitStop, hop, shake, squash, wiggle } from "../systems/juice";
import { vignette } from "../systems/atmosphere";

const SPOT_X = [170, 250, 330];

export class CrossExam extends Phaser.Scene {
  private dlg!: Dialogue;
  private content!: CaseContent;
  private order: string[] = [];
  private sel = { who: "", idx: 0 };
  private rows: Phaser.GameObjects.Text[] = [];
  private tabs: Record<string, Phaser.GameObjects.Text> = {};
  /** point mode: each suspect's one statement, in a bubble over their head */
  private bubbles: Record<string, Phaser.GameObjects.Text> = {};
  private sprites: Record<string, Phaser.GameObjects.Sprite> = {};
  private patience = 3;
  private stars: Phaser.GameObjects.Container[] = [];
  private badge!: Phaser.GameObjects.Text;
  private busy = false;
  private smudge!: Phaser.GameObjects.Sprite;

  constructor() { super("CrossExam"); }

  async create() {
    this.busy = true;
    this.patience = 3;
    this.content = CASES[progress.kit];
    const point = this.content.point;
    this.order = Object.keys(api.current!.suspects);
    this.rows = [];
    this.tabs = {};
    this.bubbles = {};
    this.stars = [];
    this.sel = { who: "", idx: 0 };
    makeGlow(this, "glow64", 64);
    makeCone(this, "cone", 180, 200);
    makePixel(this);
    themeFor("tense");
    layer(1);
    ambience("crossexam");

    // the Hall of Records: dark stage, three spotlights, ruled lines for floorboards
    this.add.rectangle(0, 0, W, H, 0x070a17).setOrigin(0);
    const stage = this.content.stage;
    if (stage) {
      // the case's own district, held in shadow, rain falling through the spotlights
      this.add.image(stage.x, stage.y, this.content.bg.glitch).setOrigin(0);
      this.add.rectangle(0, 0, W, H, 0x070a17, 0.6).setOrigin(0);
      const fl = this.add.graphics();
      for (let i = 0; i < 6; i++) fl.fillStyle(0x070a17, 0.12 * (i + 1)).fillRect(0, 168 + i * 8, W, 8);
      fl.fillStyle(0x070a17, 0.8).fillRect(0, 216, W, H - 216);
      this.add.particles(0, 0, "px", {
        x: { min: 0, max: W + 40 }, y: -10, speedY: { min: 300, max: 380 }, speedX: -40, lifespan: 900, frequency: 20, quantity: 2,
        alpha: { start: 0.35, end: 0.05 }, tint: 0x8fa4cc, scaleY: 4, advance: 1000,
      });
    } else {
      const fl = this.add.graphics();
      fl.fillStyle(0x0e1430, 1).fillRect(0, 150, W, 120);
      fl.lineStyle(1, 0x22305c, 1);
      for (let y = 154; y < 200; y += 6) fl.lineBetween(0, y + 0.5, W, y + 0.5);
    }
    this.add.particles(0, 0, "px", {
      x: { min: 120, max: 380 }, y: { min: 20, max: 170 }, speedY: { min: -3, max: 3 }, speedX: { min: -2, max: 2 }, lifespan: 5000,
      alpha: { values: [0, 0.5, 0] }, tint: 0xfff1c8, frequency: 160, blendMode: Phaser.BlendModes.ADD, advance: 3000,
    });
    const lights: [Phaser.GameObjects.Image, Phaser.GameObjects.Ellipse][] = [];
    for (const [i, who] of this.order.entries()) {
      const x = SPOT_X[i];
      const cone = this.add.image(x, -10, "cone").setOrigin(0.5, 0).setScale(0.42, 0.95).setBlendMode(Phaser.BlendModes.ADD).setTint(0xfff1c8).setAlpha(0);
      const pool = this.add.ellipse(x, 178, 46, 10, 0xfff1c8, 0).setBlendMode(Phaser.BlendModes.ADD);
      this.add.ellipse(x, 178, 20, 5, 0x000000, 0.4);
      this.sprites[who] = this.add.sprite(x, 179, `${who}_idle`, 0).setOrigin(FEET_ORIGIN.x, FEET_ORIGIN.y).play(`${who}_idle_S`).setAlpha(0);
      lights.push([cone, pool]);
    }
    this.add.ellipse(66, 186, 22, 5, 0x000000, 0.4);
    this.smudge = this.add.sprite(66, 187, "smudge", "idle/E/0").setOrigin(FEET_ORIGIN.x, FEET_ORIGIN.y).play("idle_E");
    this.add.sprite(40, 180, "foot_idle", 0).setOrigin(FEET_ORIGIN.x, FEET_ORIGIN.y).play("foot_idle_SE");
    vignette(this, 0.7);

    // evidence badge and Footnote's patience, as three ink stars
    this.badge = this.add.text(8, 92, this.content.badge(this.evidence()), { fontFamily: FONT, fontSize: "10px", color: "#0E1938", backgroundColor: "#FAC775", lineSpacing: 1 })
      .setPadding(4, 3, 4, 3).setAlpha(0);
    // drag the evidence card onto a statement: the same as picking that statement and pressing Present
    this.badge.setInteractive({ useHandCursor: true, draggable: true });
    const home = { x: this.badge.x, y: this.badge.y };
    const rowAt = (p: Phaser.Input.Pointer) =>
      this.rows.findIndex((r) => r.text.trim() && Math.abs(p.worldY - r.getBounds().centerY) <= 6 && p.worldX > 8 && p.worldX < W - 8);
    const tint = (over: number) => this.rows.forEach((r, k) => r.setColor(k === over ? "#2E5CAD" : k === this.sel.idx ? "#C9302A" : "#0E1938"));
    // point mode: the card lands on a suspect instead, and presents against their one statement
    const whoAt = (p: Phaser.Input.Pointer) =>
      this.order.find((_, i) => Math.abs(p.worldX - SPOT_X[i]) < 30 && p.worldY > 120 && p.worldY < 200);
    const lit = (who?: string) => this.order.forEach((k) => (k === who ? this.sprites[k].setTint(0xfac775) : this.sprites[k].clearTint()));
    this.badge.on("drag", (p: Phaser.Input.Pointer, x: number, y: number) => {
      if (this.busy) return;
      this.badge.setPosition(x, y).setDepth(950);
      if (point) lit(whoAt(p));
      else tint(rowAt(p));
    });
    this.badge.on("dragend", (p: Phaser.Input.Pointer) => {
      this.badge.setPosition(home.x, home.y).setDepth(0);
      if (point) {
        const who = this.busy ? undefined : whoAt(p);
        lit();
        if (!who) return;
        this.pick(who, 0, true);
        void this.present();
        return;
      }
      const i = this.busy ? -1 : rowAt(p);
      tint(-1);
      if (i < 0) return;
      this.pick(this.sel.who, i, true);
      void this.present();
    });
    this.add.text(W - 8, 92, "Footnote's patience", { fontFamily: FONT, fontSize: "9px", color: "#EB6A9E" }).setOrigin(1, 0);
    for (let i = 0; i < 3; i++) this.stars.push(this.star(W - 52 + i * 18, 114));

    // testimony panel, waiting below the screen
    const panel = this.add.container(0, 90);
    const tails: Phaser.GameObjects.Graphics[] = [];
    const pg = this.add.graphics();
    pg.fillStyle(0xf2e9cf, 1).fillRect(8, 196, W - 16, 68);
    pg.lineStyle(2, 0x0e1938, 1).strokeRect(8, 196, W - 16, 68);
    panel.add(pg);
    if (point) {
      // no panel: a plaque under each spotlight, the oath over each head, and the suspect itself is the target
      pg.clear();
      this.order.forEach((who, i) => {
        // a brass plaque in an ink frame with a bevel, and the oath in a speech bubble with a tail
        const pl = this.add.text(SPOT_X[i], 186, point.plaque(who), { fontFamily: FONT, fontSize: "9px", color: "#0E1938", backgroundColor: "#FAC775", align: "center" })
          .setPadding(4, 1, 4, 1).setOrigin(0.5, 0).setDepth(2);
        const pb = pl.getBounds();
        this.add.graphics().setDepth(1).fillStyle(0x0e1938).fillRect(pb.x - 2, pb.y - 2, pb.width + 4, pb.height + 4)
          .fillStyle(0x8a5a14).fillRect(pb.x - 1, pb.y - 1, pb.width + 2, pb.height + 2)
          .fillStyle(0xfff0b0).fillRect(pb.x - 1, pb.y - 1, pb.width + 1, 1);
        const b = this.bubbles[who] = this.add.text(SPOT_X[i], 128, api.current!.statements[who][0].text, {
          fontFamily: FONT, fontSize: "8px", color: "#0E1938", backgroundColor: "#F2E9CF", align: "center", wordWrap: { width: 70 },
        }).setPadding(3, 2, 3, 2).setOrigin(0.5, 1).setAlpha(0).setDepth(5);
        const bb = b.getBounds(), cx = SPOT_X[i];
        tails.push(this.add.graphics().setDepth(4).setAlpha(0)
          .fillStyle(0x0e1938).fillRect(bb.x - 1, bb.y - 1, bb.width + 2, bb.height + 2)
          .fillTriangle(cx - 5, bb.bottom, cx + 5, bb.bottom, cx, bb.bottom + 7)
          .fillStyle(0xf2e9cf).fillTriangle(cx - 4, bb.bottom - 1, cx + 4, bb.bottom - 1, cx, bb.bottom + 5));
        this.sprites[who].setInteractive({ useHandCursor: true }).on("pointerdown", () => {
          if (this.busy) return;
          this.pick(who, 0, true);
          void this.present();
        });
      });
    } else {
    let tx = 16;
    this.order.forEach((who) => {
      const t = this.add.text(tx, 199, api.current!.suspects[who].name, { fontFamily: FONT, fontSize: "9px", color: "#F2E9CF", backgroundColor: "#0E1938" })
        .setPadding(6, 1, 6, 1).setInteractive({ useHandCursor: true });
      t.on("pointerover", () => sfx("hover"));
      t.on("pointerdown", () => { if (!this.busy && this.sel.who !== who) this.pick(who, 0); });
      tx += t.width + 6;                                // lay tabs out by their real width, with a gap
      this.tabs[who] = t;
      panel.add(t);
    });
    for (let i = 0; i < 4; i++) {
      const r = this.add.text(18, 214 + i * 12, "", { fontFamily: FONT, fontSize: "9px", color: "#0E1938" })
        .setInteractive({ useHandCursor: true });
      r.on("pointerover", () => { if (this.sel.idx !== i) r.setColor("#2E5CAD"); });
      r.on("pointerout", () => r.setColor(this.sel.idx === i ? "#C9302A" : "#0E1938"));
      r.on("pointerdown", () => { if (!this.busy && this.sel.idx !== i) { this.pick(this.sel.who, i); sfx("tick"); } });
      this.rows.push(r);
      panel.add(r);
    }
    const btn = (x: number, label: string, fill: string, fn: () => void) => {
      const b = this.add.text(x, 199, label, { fontFamily: FONT, fontSize: "9px", color: "#ffffff", backgroundColor: fill })
        .setPadding(8, 1, 8, 1).setInteractive({ useHandCursor: true });
      panel.add(b);
      buttonFeel(this, b, "select");
      b.on("pointerdown", (_p: any, _x: any, _y: any, e: any) => { e?.stopPropagation?.(); fn(); });
      return b;
    };
    btn(W - 168, "Press", "#2E5CAD", () => this.press());
    btn(W - 112, "Present evidence", "#C9302A", () => this.present());
    }
    this.pick(this.order[0], 0, true);

    // the entrance: lights thunk on one by one, each suspect drops into its spot, the banner slams across
    await inkIn(this, 460);
    for (const [i, who] of this.order.entries()) {
      const [cone, pool] = lights[i];
      sfx("thunk");
      cone.setAlpha(0.4);
      pool.setFillStyle(0xfff1c8, 0.3);
      this.tweens.add({ targets: cone, alpha: 0.22, duration: 300 });
      this.tweens.add({ targets: pool, fillAlpha: 0.16, duration: 300 });
      const sp = this.sprites[who];
      sp.setAlpha(1).setY(120);
      this.tweens.add({ targets: sp, y: 179, duration: 240, ease: "Quad.easeIn", onComplete: () => { squash(this, sp, 0.2, 80); sfx("plop"); } });
      await wait(this, 300);
    }
    await this.banner("CROSS-EXAMINATION");
    this.tweens.add({ targets: panel, y: 0, duration: 320, ease: "Back.easeOut" });
    this.tweens.add({ targets: this.badge, alpha: 1, duration: 300 });
    if (point) this.tweens.add({ targets: [...Object.values(this.bubbles), ...tails], alpha: 1, duration: 300 });
    sfx("open");
    this.pick(this.sel.who, this.sel.idx, true);
    await wait(this, 320);

    this.dlg = new Dialogue(this);
    await this.dlg.play(point ? [{ who: "foot", expr: "neutral", text: point.intro }] : [
      { who: "foot", expr: "neutral", text: "Cross-examination! Pick a suspect, pick a statement. PRESS it to dig deeper." },
      { who: "foot", expr: "worried", text: "When a statement can't be true because of your evidence, PRESENT the evidence, or drag the card onto it. But my patience has limits." },
    ]);
    this.busy = false;
  }

  /** A banner that slams across the middle of the screen and leaves. */
  private async banner(text: string) {
    const c = this.add.container(W + 260, 70).setDepth(800);
    const bg = this.add.rectangle(0, 0, 330, 34, 0xc9302a).setAngle(-3);
    const t = this.add.text(0, 0, text, { fontFamily: DISPLAY, fontSize: "24px", color: "#F2E9CF", stroke: "#0E1938", strokeThickness: 5 })
      .setOrigin(0.5).setAngle(-3);
    c.add([bg, t]);
    sfx("whoosh");
    await tween(this, { targets: c, x: W / 2, duration: 220, ease: "Cubic.easeOut" });
    sfx("stamp");
    shake(this, 140, 0.006);
    await wait(this, 750);
    await tween(this, { targets: c, x: -260, duration: 200, ease: "Cubic.easeIn" });
    c.destroy();
  }

  /** One patience star, drawn as a five-point ink star. */
  private star(x: number, y: number) {
    const g = this.add.graphics();
    const pts: Phaser.Math.Vector2[] = [];
    for (let i = 0; i < 10; i++) {
      const a = -Math.PI / 2 + (i * Math.PI) / 5, r = i % 2 ? 3 : 7;
      pts.push(new Phaser.Math.Vector2(Math.cos(a) * r, Math.sin(a) * r));
    }
    g.fillStyle(0xeb6a9e, 1).fillPoints(pts, true);
    g.lineStyle(1, 0x0e1938, 1).strokePoints(pts, true);
    const c = this.add.container(x, y, [g]);
    this.tweens.add({ targets: c, angle: { from: -6, to: 6 }, duration: 900 + Math.random() * 300, yoyo: true, repeat: -1, ease: "Sine.easeInOut" });
    return c;
  }

  /** The star for the patience just lost cracks and falls away. */
  private loseStar() {
    const s = this.stars[this.patience];
    if (!s) return;
    sfx("crack");
    this.tweens.killTweensOf(s);
    this.tweens.add({ targets: s, y: s.y + 60, angle: 160, alpha: 0, duration: 700, ease: "Quad.easeIn" });
  }

  /** Footnote gives one more chance: the first star grows back. */
  private restoreStar() {
    const s = this.stars[0];
    this.tweens.killTweensOf(s);
    s.setY(114).setAngle(0).setAlpha(0).setScale(0.3);
    this.tweens.add({ targets: s, alpha: 1, scale: 1, duration: 300, ease: "Back.easeOut" });
    sfx("sparkle");
  }

  /** What the lab proved. Reached without the lab (a direct link), there is nothing to present yet. */
  private evidence(): Evidence {
    return progress.evidence ?? { label: "none", badge: "NO EVIDENCE YET\ndo the lab first", say: "Hold it. ...I don't actually have evidence yet." };
  }

  private pick(who: string, idx: number, quiet = false) {
    const changed = who !== this.sel.who;
    this.sel = { who, idx };
    const st = api.current!.statements[who];
    this.rows.forEach((r, i) => {
      r.setText(`${i === idx ? "▸" : "  "} ${st[i]?.text ?? ""}`);
      r.setColor(i === idx ? "#C9302A" : "#0E1938");
    });
    for (const k of this.order) this.tabs[k]?.setBackgroundColor(k === who ? "#C9302A" : "#0E1938");
    if (!this.content.point && this.sprites[who].alpha > 0) for (const k of this.order) this.tweens.add({ targets: this.sprites[k], alpha: k === who ? 1 : 0.5, duration: 160 });
    if (changed && !quiet) { sfx("select"); hop(this, this.sprites[who], 5, 120); }
  }

  private async press() {
    if (this.busy) return;
    this.busy = true;
    const { who, idx } = this.sel;
    const st = api.current!.statements[who][idx];
    this.sprites[who].play(`${who}_talk_S`);
    this.dlg.say({ who: "smudge", expr: "thinking", text: `"${st.text}" Go on...` });
    const r = await api.press(st.id);
    await this.dlg.say({ who: who as Who, expr: "neutral", text: r.answer });
    this.dlg.hide();
    this.sprites[who].play(`${who}_idle_S`);
    this.busy = false;
  }

  /** "HOLD IT!": an ink splash with the words punched through it. */
  private async holdIt() {
    const c = this.add.container(W / 2, 100).setDepth(900).setScale(0.2).setAngle(-8);
    const g = this.add.graphics();
    const pts: Phaser.Math.Vector2[] = [];
    for (let i = 0; i < 22; i++) {
      const a = (i / 22) * Math.PI * 2, r = (i % 2 ? 58 : 84) + Math.random() * 12;
      pts.push(new Phaser.Math.Vector2(Math.cos(a) * r * 1.5, Math.sin(a) * r * 0.62));
    }
    g.fillStyle(0xf2e9cf, 1).fillPoints(pts, true);
    g.lineStyle(4, 0x0e1938, 1).strokePoints(pts, true);
    const t = this.add.text(0, 0, "HOLD IT!", { fontFamily: DISPLAY, fontSize: "40px", color: "#C9302A", stroke: "#0E1938", strokeThickness: 7 }).setOrigin(0.5);
    c.add([g, t]);
    sting("holdit");
    this.smudge.play("strikethrough_E");
    await tween(this, { targets: c, scale: 1, duration: 160, ease: "Back.easeOut" });
    shake(this, 200, 0.01);
    await hitStop(this, 90);
    await wait(this, 520);
    await tween(this, { targets: c, scale: 1.2, alpha: 0, duration: 160, ease: "Quad.easeIn" });
    c.destroy();
    this.smudge.play("idle_E");
  }

  private async present() {
    if (this.busy) return;
    this.busy = true;
    const { who, idx } = this.sel;
    const st = api.current!.statements[who][idx];
    const ev = this.evidence();
    await this.holdIt();
    // ev.say names the culprit, so in point mode it is only said once the right suspect is hit
    if (!this.content.point) await this.dlg.say({ who: "smudge", expr: "determined", text: ev.say });
    const r = await api.present(st.id, ev.label);
    if (r.hit && this.content.point) await this.dlg.say({ who: "smudge", expr: "determined", text: ev.say });
    if (r.hit) {
      await this.strikethrough(who, idx);
      return;
    }
    sfx("wrong");
    await hitStop(this, 80);
    flash(this, 0xc9302a, 0.28, 260);
    shake(this, 160, 0.005);
    wiggle(this, this.badge, 4);
    this.patience -= 1;
    this.loseStar();
    layer(1 + Math.min(2, 3 - this.patience));
    if (r.close) {
      await this.dlg.say({ who: "foot", expr: "worried", text: "*Right suspect, wrong line. Which of their statements does your evidence make impossible?" });
    } else if (this.patience > 0) {
      await this.dlg.say({ who: "foot", expr: "worried", text: this.content.point?.miss(who) ?? this.content.miss(ev) });
    } else {
      await this.dlg.say({ who: "foot", expr: "worried", text: this.content.stuck(ev) });
      this.patience = 1;
      this.restoreStar();
    }
    this.dlg.hide();
    this.busy = false;
  }

  private async strikethrough(who: string, idx: number) {
    const row = this.content.point ? this.bubbles[who] : this.rows[idx];
    music("off");
    sfx("strike");
    this.smudge.play("strikethrough_E");
    // red pen slash across the lie (a bubble in point mode is centred on its spotlight, so use its bounds)
    const slash = this.add.graphics().setDepth(900);
    const b = this.content.point ? row.getBounds() : null;
    const y = b ? b.centerY : row.y + 6, x0 = b ? b.x : row.x, x1 = b ? b.right : row.x + row.width + 4;
    await tween(this, {
      targets: { t: 0 }, t: 1, duration: 260, ease: "Cubic.easeOut",
      onUpdate: (tw: Phaser.Tweens.Tween) => {
        const t = (tw.targets[0] as any).t;
        slash.clear().lineStyle(3, 0xc9302a, 1).lineBetween(x0, y + 1, x0 + (x1 - x0) * t, y - 2);
      },
    });
    await hitStop(this, 140);
    flash(this, 0xffffff, 0.9, 380, 950);
    shake(this, 500, 0.012);
    const ink = this.add.particles(W / 2, 110, "px", {
      speed: { min: 60, max: 220 }, angle: { min: 0, max: 360 }, lifespan: 700, scale: { start: 3, end: 1 },
      tint: [0xc9302a, 0x0e1938, 0x8e1a14], quantity: 60, emitting: false,
    }).setDepth(960);
    ink.explode(60);
    const word = this.add.text(W / 2, 110, "STRIKETHROUGH!", {
      fontFamily: DISPLAY, fontSize: "40px", color: "#E24B4A", stroke: "#0E1938", strokeThickness: 8,
      shadow: { offsetX: 3, offsetY: 3, color: "#000", blur: 0, fill: true, stroke: true },
    }).setOrigin(0.5).setDepth(970).setScale(0.2).setAngle(-8);
    await tween(this, { targets: word, scale: 1, duration: 320, ease: "Back.easeOut" });
    this.sprites[who].play(`${who}_shocked_S`);
    sfx("drop");
    await wait(this, 900);
    await tween(this, { targets: word, alpha: 0, scale: 1.3, duration: 300 });
    word.destroy();
    this.sprites[who].play(`${who}_nervous_S`);
    // the others step back into the dark; the culprit stands alone in the light
    for (const k of this.order) if (k !== who) this.tweens.add({ targets: this.sprites[k], alpha: 0.2, duration: 600 });
    progress.culprit = who;
    for (const l of this.content.confess[who]) await this.dlg.say({ who: who as Who, expr: l.expr, text: l.text });
    await this.dlg.play([
      { who: "foot", expr: "happy", text: this.content.caught ?? "The Baron again! But the truth is proven, and when the truth is proven..." },
      { who: "smudge", expr: "determined", text: "...the law writes itself back." },
    ]);
    progress.solve(progress.kit);
    sfx("rise");
    this.cameras.main.fadeOut(600, 255, 245, 220);
    await wait(this, 620);
    this.scene.start("Restore");
  }
}

