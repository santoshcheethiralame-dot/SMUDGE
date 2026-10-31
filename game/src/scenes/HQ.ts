import Phaser from "phaser";
import { W, H, FONT, DISPLAY, FEET_ORIGIN, project, dirFromVector, Dir } from "../consts";
import { Dialogue, Line } from "../systems/dialogue";
import { makeGlow, makeCone, makePixel, dust, wait, tween, pageReveal, pageTurn } from "../systems/fx";
import { sfx, music, step, layer, ambience } from "../audio";
import { progress } from "../state";
import { CASES, CASE_ORDER } from "../cases";

const C = { cu: 0, cv: 88 };
const P = (x: number, y: number, z: number) => project(x, y, z, C.cu, C.cv);

const LANE = { xMin: 40, xMax: 448, yMin: P(0, 0, 10).y, yMax: P(0, 0, 24).y };
const WALK = 58;
const RUN = 104;

interface Spot { key: string; x: number; markY: number; label: string }
const SPOTS: Spot[] = [
  { key: "bed", x: P(-156, 0, 0).x, markY: P(-156, 22, -6).y, label: "Bed" },
  { key: "caseboard", x: P(-86, 0, 0).x, markY: P(-86, 96, -36).y, label: "Case board" },
  { key: "cards", x: P(22, 0, 0).x, markY: P(22, 76, -40).y, label: "Formula frames" },
  { key: "hatrack", x: P(104, 0, 0).x, markY: P(104, 52, -14).y, label: "Hat rack" },
  { key: "door", x: P(214, 0, 0).x - 8, markY: P(214, 70, -6).y, label: "Way out" },
];

export class HQ extends Phaser.Scene {
  private dlg!: Dialogue;
  private smudge!: Phaser.GameObjects.Sprite;
  private shadow!: Phaser.GameObjects.Ellipse;
  private foot!: Phaser.GameObjects.Sprite;
  private target: { x: number; y: number; spot?: Spot } | null = null;
  private dir: Dir = "E";
  private keys!: Record<string, Phaser.Input.Keyboard.Key>;
  private busy = false;
  private briefed = false;
  private stepTimer = 0;
  private marks: Phaser.GameObjects.Container[] = [];
  private prompt!: Phaser.GameObjects.Text;
  private seen = new Set<string>();

  constructor() { super("HQ"); }

  /** Solved cases earn a Formula Card. There are five frames, so they hold the five most recent; the full list is read out at the wall. */
  private solvedCards() {
    return [...progress.solvedCases].map((k) => CASES[k]).filter(Boolean);
  }
  private fillFrames() {
    const shown = this.solvedCards().slice(-5);
    const tints = [0xfac775, 0xf4a6c6, 0x9ad0f0, 0xb7e3a1, 0xf2e9cf];
    shown.forEach((c, i) => {
      const { x, y } = P([-12, 5, 22, 39, 56][i], 62, -40);
      const sym = c.restore.card.split(/[=<]/)[0].trim().slice(0, 3);
      this.add.rectangle(x, y, 10, 14, tints[i % tints.length]).setStrokeStyle(1, 0x0e1938);
      this.add.text(x, y, sym, { fontFamily: FONT, fontSize: "7px", color: "#0E1938" }).setOrigin(0.5);
    });
  }

  create(data: { from?: string }) {
    this.busy = false;
    this.briefed = false;
    this.seen.clear();
    makeGlow(this, "glow64", 64);
    makeCone(this, "cone", 180, 200);
    makePixel(this);
    this.add.image(0, 0, "hq").setOrigin(0, 0);
    this.fillFrames();

    // light: the thimble lamp breathes, the doorway pours warm light in
    const thimble = P(34, 35, -10);
    const tg = this.add.image(thimble.x, thimble.y, "glow64").setScale(1.1).setBlendMode(Phaser.BlendModes.ADD).setTint(0x7fd8ff).setAlpha(0.55);
    this.tweens.add({ targets: tg, alpha: 0.35, scale: 1.0, duration: 1600, yoyo: true, repeat: -1, ease: "Sine.easeInOut" });
    const door = P(232, 56, -6);
    this.add.image(door.x, door.y, "glow64").setScale(1.8, 2.2).setBlendMode(Phaser.BlendModes.ADD).setTint(0xffc877).setAlpha(0.45);
    const shaft = this.add.image(door.x + 4, door.y - 30, "cone").setOrigin(0.5, 0).setRotation(1.2)
      .setScale(0.9, 1.4).setBlendMode(Phaser.BlendModes.ADD).setTint(0xffc877).setAlpha(0.16);
    this.tweens.add({ targets: shaft, alpha: 0.1, duration: 2600, yoyo: true, repeat: -1, ease: "Sine.easeInOut" });
    dust(this, 280, 120, 190, 110, 0xffd9a0, 30);
    dust(this, 230, 160, 90, 50, 0xa8e8ff, 14);
    this.glassRim();

    // sparkles mark everything you can look at
    for (const s of SPOTS) this.marks.push(this.sparkle(s.x, s.markY));

    // Smudge and Footnote
    const startX = data?.from === "prologue" ? 20 : 220;
    const startY = (LANE.yMin + LANE.yMax) / 2 + 2;
    this.shadow = this.add.ellipse(startX, startY - 1, 22, 5, 0x000000, 0.35).setDepth(startY - 1);
    this.smudge = this.add.sprite(startX, startY, "smudge", "idle/E/0").setOrigin(FEET_ORIGIN.x, FEET_ORIGIN.y).play("idle_E");
    this.foot = this.add.sprite(startX - 26, startY - 4, "foot_idle", 0).setOrigin(FEET_ORIGIN.x, FEET_ORIGIN.y).play("foot_idle_E");

    // HUD
    const pill = this.add.text(8, 8, "Prologue · The Inkwell", { fontFamily: FONT, fontSize: "9px", color: "#F2E9CF", backgroundColor: "#0E1938" })
      .setPadding(5, 2, 5, 2).setDepth(900);
    void pill;
    this.prompt = this.add.text(0, 0, "", { fontFamily: FONT, fontSize: "9px", color: "#0E1938", backgroundColor: "#F2E9CF" })
      .setPadding(4, 1, 4, 1).setOrigin(0.5, 1).setDepth(901).setVisible(false);

    this.dlg = new Dialogue(this);
    this.keys = this.input.keyboard!.addKeys("UP,DOWN,LEFT,RIGHT,W,A,S,D,SHIFT,E,SPACE") as any;
    this.input.on("pointerdown", (p: Phaser.Input.Pointer) => this.onTap(p));
    this.input.keyboard?.on("keydown-E", () => this.tryInteract());
    this.input.keyboard?.on("keydown-SPACE", () => this.tryInteract());

    music("night");
    layer(1);
    ambience("hq");
    this.intro(data?.from === "prologue");
  }

  private async intro(fromPrologue: boolean) {
    this.busy = true;
    if (fromPrologue) {
      await pageReveal(this);
      this.smudge.play("walk_E");
      this.tweens.add({ targets: this.foot, x: 70, duration: 1400, ease: "Sine.easeOut" });
      await tween(this, { targets: [this.smudge, this.shadow], x: 96, duration: 1400 });
      this.smudge.play("idle_E");
      await this.dlg.play([
        { who: "foot", expr: "happy", text: "Ta-da! The Inkwell. Detective Club HQ since... well, since someone knocked the ink bottle over." },
        { who: "smudge", expr: "thinking", text: "It's very dark. And very bottle." },
        { who: "foot", expr: "neutral", text: "Have a look around. The case board is the important bit." },
        { who: "narrator", text: "Tap the floor to walk. Tap anything that sparkles to look closer. (Keyboard: arrows, Shift to run, E to look.)" },
      ]);
    } else {
      this.cameras.main.fadeIn(500, 5, 6, 15);
    }
    this.busy = false;
  }

  private glassRim() {
    // the curved rim of the bottle catching the light, top corners
    const g = this.add.graphics().setDepth(800).setBlendMode(Phaser.BlendModes.ADD);
    g.lineStyle(2, 0x6fb4d8, 0.22);
    g.beginPath();
    const pts = new Phaser.Curves.QuadraticBezier(new Phaser.Math.Vector2(-10, 150), new Phaser.Math.Vector2(30, -18), new Phaser.Math.Vector2(250, -12));
    pts.draw(g, 32);
    g.lineStyle(1, 0xbfe4ff, 0.3);
    const pts2 = new Phaser.Curves.QuadraticBezier(new Phaser.Math.Vector2(330, -10), new Phaser.Math.Vector2(470, -14), new Phaser.Math.Vector2(490, 110));
    pts2.draw(g, 32);
    const glint = this.add.rectangle(-40, 0, 6, H * 2, 0xffffff, 0.06).setRotation(0.5).setDepth(801).setBlendMode(Phaser.BlendModes.ADD);
    this.tweens.add({ targets: glint, x: W + 60, duration: 5200, repeat: -1, repeatDelay: 6000, ease: "Sine.easeInOut" });
  }

  private sparkle(x: number, y: number) {
    const c = this.add.container(x, y).setDepth(700);
    const g = this.add.graphics();
    g.fillStyle(0xfff3c4, 1).fillRect(-0.5, -3.5, 1, 7).fillRect(-3.5, -0.5, 7, 1);
    g.fillStyle(0xffffff, 1).fillRect(-0.5, -0.5, 1, 1);
    c.add(g);
    c.setBlendMode(Phaser.BlendModes.ADD);
    this.tweens.add({ targets: c, scale: { from: 0.4, to: 1.1 }, alpha: { from: 0.3, to: 1 }, duration: 700, yoyo: true, repeat: -1, delay: Math.random() * 700 });
    return c;
  }

  private onTap(p: Phaser.Input.Pointer) {
    if (this.busy || this.dlg.active) return;
    // tapped near a sparkle or the object under it? (world coordinates: the camera zooms, see main.ts)
    const wx = p.worldX, wy = p.worldY;
    const spot = SPOTS.find((s) => Math.abs(wx - s.x) < 22 && wy > s.markY - 16 && wy < LANE.yMax + 6);
    const tx = Phaser.Math.Clamp(spot ? spot.x : wx, LANE.xMin, LANE.xMax);
    const ty = Phaser.Math.Clamp(wy, LANE.yMin, LANE.yMax);
    this.target = { x: tx, y: spot ? (LANE.yMin + LANE.yMax) / 2 : ty, spot };
  }

  private nearest(): Spot | undefined {
    return SPOTS.find((s) => Math.abs(this.smudge.x - s.x) < 20);
  }

  private tryInteract() {
    if (this.busy || this.dlg.active) return;
    const s = this.nearest();
    if (s) this.interact(s);
  }

  update(_t: number, dtMs: number) {
    const dt = dtMs / 1000;
    let vx = 0, vy = 0;
    const k = this.keys;
    if (!this.busy && !this.dlg.active) {
      if (k.LEFT.isDown || k.A.isDown) vx -= 1;
      if (k.RIGHT.isDown || k.D.isDown) vx += 1;
      if (k.UP.isDown || k.W.isDown) vy -= 1;
      if (k.DOWN.isDown || k.S.isDown) vy += 1;
      if (vx || vy) this.target = null;
      if (!vx && !vy && this.target) {
        const dx = this.target.x - this.smudge.x, dy = this.target.y - this.smudge.y;
        if (Math.hypot(dx, dy) < 2) {
          const spot = this.target.spot;
          this.target = null;
          if (spot) this.interact(spot);
        } else { vx = dx; vy = dy; }
      }
    }
    const moving = vx !== 0 || vy !== 0;
    if (moving) {
      const run = k.SHIFT.isDown || (this.target && Math.abs(this.target.x - this.smudge.x) > 140);
      const speed = run ? RUN : WALK;
      const len = Math.hypot(vx, vy * 1.0) || 1;
      this.smudge.x = Phaser.Math.Clamp(this.smudge.x + (vx / len) * speed * dt, LANE.xMin, LANE.xMax);
      this.smudge.y = Phaser.Math.Clamp(this.smudge.y + (vy / len) * speed * 0.35 * dt, LANE.yMin, LANE.yMax);
      this.dir = dirFromVector(vx, vy * 0.6);
      this.smudge.play(`${run ? "run" : "walk"}_${this.dir}`, true);
      this.stepTimer -= dtMs;
      if (this.stepTimer <= 0) { step("wood"); this.stepTimer = run ? 180 : 300; }
    } else if (!this.busy && !this.dlg.active) {
      this.smudge.play(`idle_${this.dir}`, true);
    }
    this.shadow.setPosition(this.smudge.x, this.smudge.y - 1);
    this.smudge.setDepth(this.smudge.y);
    this.shadow.setDepth(this.smudge.y - 1);

    // Footnote floats along behind, a little above the floor
    const behind = this.dir.includes("W") ? 24 : -24;
    const fx = this.smudge.x + behind, fy = this.smudge.y - 6;
    this.foot.x += (fx - this.foot.x) * Math.min(1, dt * 2.5);
    this.foot.y += (fy - this.foot.y) * Math.min(1, dt * 2.5);
    this.foot.setDepth(this.foot.y + 0.5);
    const fdir = this.foot.x < this.smudge.x ? "SE" : "SW";
    if (!this.foot.anims.currentAnim?.key.startsWith("foot_talk")) this.foot.play(`foot_idle_${fdir}`, true);

    // "look" prompt over whatever Smudge is standing next to
    const s = this.nearest();
    if (s && !this.dlg.active && !this.busy) {
      this.prompt.setText(`▸ ${s.label}`).setPosition(s.x, s.markY - 8).setVisible(true);
    } else this.prompt.setVisible(false);
  }

  private async talk(lines: Line[]) {
    this.busy = true;
    this.prompt.setVisible(false);
    this.foot.play("foot_talk_SE");
    await this.dlg.play(lines);
    this.busy = false;
  }

  private async interact(s: Spot) {
    this.seen.add(s.key);
    this.smudge.play("idle_N");
    this.dir = "N";
    switch (s.key) {
      case "bed":
        await this.talk([
          { who: "smudge", expr: "thinking", text: "A matchbox bed with a cotton-ball pillow." },
          { who: "foot", expr: "happy", text: "The last detective who slept here snored in italics." },
        ]);
        break;
      case "caseboard":
        await this.talk([
          { who: "foot", expr: "neutral", text: "The case board. Every clue you find goes up here. With string." },
          { who: "smudge", expr: "smug", text: "I've always wanted string." },
          { who: "foot", expr: "worried", text: "Case one: the law of density. Stolen. Last seen being rubbed out right in front of us." },
          { who: "foot", expr: "worried", text: "Buoyant Bay will feel it first. Boats, harbour, the lot." },
          { who: "smudge", expr: "determined", text: "Then that's where we start." },
        ]);
        if (!this.briefed) {
          this.briefed = true;
          sfx("chime");
          await this.caseCard();
        }
        break;
      case "cards":
        {
          const won = this.solvedCards();
          if (!won.length) {
            await this.talk([
              { who: "foot", expr: "neutral", text: "Formula frames. Every law you win back earns a Formula Card, and it goes up here." },
              { who: "smudge", expr: "worried", text: "They're all empty." },
              { who: "foot", expr: "happy", text: "For now!" },
            ]);
          } else {
            await this.talk([
              { who: "foot", expr: "happy", text: `${won.length} of ${CASE_ORDER.length} laws are back in the book!` },
              ...won.map((c): Line => ({ who: "foot", expr: "neutral", text: `${c.restore.card}  (${c.restore.cardSub})` })),
            ]);
          }
        }
        break;
      case "hatrack":
        await this.talk([
          { who: "smudge", expr: "happy", text: "A spare hat." },
          { who: "foot", expr: "neutral", text: "Always keep a spare. Hats fly off when the plot thickens." },
        ]);
        break;
      case "door":
        if (!this.briefed) {
          await this.talk([{ who: "foot", expr: "neutral", text: "Not so fast, detective. Check the case board first." }]);
        } else {
          await this.talk([
            { who: "foot", expr: "happy", text: "Buoyant Bay is down the gutter, left at the margin. Ready?" },
            { who: "smudge", expr: "determined", text: "Ready." },
          ]);
          await this.leave();
        }
        break;
    }
  }

  private async caseCard() {
    this.busy = true;
    const card = this.add.container(W / 2, H / 2 - 20).setDepth(1500).setScale(0.2).setAlpha(0);
    const bg = this.add.rectangle(0, 0, 200, 92, 0xf2e9cf).setStrokeStyle(2, 0x0e1938);
    const pin = this.add.circle(0, -42, 4, 0xc9302a);
    const t1 = this.add.text(0, -26, "NEW CASE", { fontFamily: FONT, fontSize: "9px", color: "#C9302A" }).setOrigin(0.5);
    const t2 = this.add.text(0, -4, "The Forged Crown", { fontFamily: DISPLAY, fontSize: "20px", color: "#0E1938" }).setOrigin(0.5);
    const t3 = this.add.text(0, 20, "Buoyant Bay · Chapter 9: Density", { fontFamily: FONT, fontSize: "9px", color: "#55361A" }).setOrigin(0.5);
    const t4 = this.add.text(0, 34, "added to the case board", { fontFamily: FONT, fontSize: "10px", color: "#7E2D47" }).setOrigin(0.5);
    card.add([bg, pin, t1, t2, t3, t4]);
    await tween(this, { targets: card, scale: 1, alpha: 1, angle: -3, duration: 420, ease: "Back.easeOut" });
    await wait(this, 1700);
    await tween(this, { targets: card, scale: 0.15, x: SPOTS[1].x, y: SPOTS[1].markY + 20, alpha: 0, duration: 520, ease: "Cubic.easeIn" });
    card.destroy();
    this.busy = false;
  }

  private async leave() {
    this.busy = true;
    this.smudge.play("walk_E");
    this.tweens.add({ targets: this.foot, x: W + 30, duration: 1600 });
    await tween(this, { targets: [this.smudge, this.shadow], x: W + 30, duration: 1300 });
    // the door opens onto the casebook: every chapter with a stolen law
    await pageTurn(this, () => { this.scene.start("Map", { from: "hq" }); });
  }
}

export class EndCard extends Phaser.Scene {
  constructor() { super("EndCard"); }
  create() {
    this.cameras.main.fadeIn(600, 5, 6, 15);
    this.add.rectangle(0, 0, W, H, 0x05060f).setOrigin(0);
    this.add.text(W / 2, 70, "CASE 1", { fontFamily: FONT, fontSize: "11px", color: "#C9302A" }).setOrigin(0.5);
    this.add.text(W / 2, 100, "The Forged Crown", { fontFamily: DISPLAY, fontSize: "34px", color: "#F2E9CF" }).setOrigin(0.5);
    this.add.text(W / 2, 134, "Buoyant Bay is sinking. Someone swapped the crown.\nOnly density can prove it.", { fontFamily: FONT, fontSize: "10px", color: "#9AA6C8", align: "center", lineSpacing: 4 }).setOrigin(0.5);
    this.add.sprite(W / 2, 228, "smudge", "idle/S/0").setOrigin(0.5, 60 / 64).play("idle_S");
    this.add.text(W / 2, 252, "End of the prologue · tap to play again", { fontFamily: FONT, fontSize: "9px", color: "#55607F" }).setOrigin(0.5);
    this.input.once("pointerdown", () => this.scene.start("Title"));
    this.input.keyboard?.once("keydown", () => this.scene.start("Title"));
  }
}
