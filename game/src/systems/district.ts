// A walkable district: one scrolling backdrop, suspects to question, a crime scene that leads to the lab,
// and the call to the stage. One scene serves every case: the layout, scenery and lines come from the case's
// folder in src/cases, the facts from the server's case. Start it with { kit, from }.
import Phaser from "phaser";
import { W, FONT, DISPLAY, FEET_ORIGIN, project, dirFromVector, Dir } from "../consts";
import { Dialogue, Who } from "./dialogue";
import { makeGlow, makePixel, wait, pageReveal, tween } from "./fx";
import { askBox } from "./ui";
import { sfx, step, music, themeFor, layer, ambience, sting, type Ground } from "../audio";
import { api } from "../api";
import { progress } from "../state";
import { CASES, CaseContent, Layout } from "../cases";
import { atmosphere } from "./atmosphere";
import { chapterCard, inkIn, inkOut } from "./transition";
import { dustPuff, hop, punch, squash } from "./juice";
import { speak } from "./voice";

const WALK = 60, RUN = 110;
/** how fast Smudge gets up to speed and stops, per second */
const ACCEL = 9;
/** what each district's ground is made of, for footsteps */
const GROUND: Record<string, Ground> = {
  density: "wood", motion: "dirt", sound: "stone", heights: "stone", refraction: "wood",
  ohm: "dirt", heat: "snow", acids: "stone", power: "metal",
};
const DUST: Record<string, number> = { motion: 0xd9b27c, heat: 0xffffff, ohm: 0x7d8c5a };
const IDLE_NUDGE_MS = 25000;
/** chapters already opened this session: the chapter card plays once each */
const seenChapters = new Set<string>();

export interface Spot { key: string; x: number; markY: number; label: string }

export class District extends Phaser.Scene {
  protected content!: CaseContent;
  protected dlg!: Dialogue;
  protected smudge!: Phaser.GameObjects.Sprite;
  protected foot!: Phaser.GameObjects.Sprite;
  protected busy = false;
  private shadow!: Phaser.GameObjects.Ellipse;
  private target: { x: number; y: number; spot?: Spot } | null = null;
  private dir: Dir = "E";
  private keys!: Record<string, Phaser.Input.Keyboard.Key>;
  private stepTimer = 0;
  private dustTimer = 0;
  private prompt!: Phaser.GameObjects.Text;
  private promptFor: Spot | null = null;
  private checklist!: Phaser.GameObjects.Text;
  private spots: Spot[] = [];
  private lane = { xMin: 0, xMax: 0, yMin: 0, yMax: 0 };
  private vel = { x: 0, y: 0 };
  private wasRunning = false;
  private lead = 0;
  /** while set, the camera looks here instead of at Smudge */
  private focusX: number | null = null;
  private suspects: Record<string, Phaser.GameObjects.Sprite> = {};
  private glanceTimer = 0;
  private air!: { update: (x: number, stageX: number, dtMs?: number) => void };
  private idleMs = 0;
  private nudged = 0;
  private lastLayer = 0;
  private ticks = "";

  constructor() { super("District"); }

  protected layout(): Layout { return this.content.layout; }

  /** Screen position of a world point in this district. */
  protected P(x: number, y: number, z: number) {
    const L = this.layout();
    const p = project(x, y, z, L.cu, L.cv);
    return { x: p.x + (L.width - W) / 2, y: p.y };
  }

  async create(data: { kit?: string; from?: string }) {
    this.content = CASES[data?.kit ?? progress.kit];
    this.busy = true;
    this.target = null;
    this.focusX = null;
    this.vel = { x: 0, y: 0 };
    this.idleMs = 0;
    this.nudged = 0;
    this.suspects = {};
    makeGlow(this, "glow64", 64);
    makePixel(this);
    const L = this.layout();
    const restored = progress.kit === this.content.kit && progress.solved;
    this.lane = { xMin: 30, xMax: L.width - 30, yMin: this.P(0, 0, 12).y, yMax: this.P(0, 0, 24).y };
    const bgKey = restored ? this.content.bg.restored : this.content.bg.glitch;
    this.add.image(0, 0, bgKey).setOrigin(0, 0);
    this.content.decorate?.(this, (x, y, z) => this.P(x, y, z), restored);

    for (const s of L.suspects) {
      const at = this.P(s.x, 0, s.z);
      this.add.ellipse(at.x, at.y - 1, 20, 5, 0x000000, 0.3).setDepth(at.y - 1);
      const sp = this.add.sprite(at.x, at.y, `${s.key}_idle`, 0).setOrigin(FEET_ORIGIN.x, FEET_ORIGIN.y).play(`${s.key}_idle_S`).setDepth(at.y);
      // everyone breathes, out of step with each other
      this.tweens.add({ targets: sp, scaleY: 1.025, scaleX: 0.99, duration: 1300 + Math.random() * 500, yoyo: true, repeat: -1,
        ease: "Sine.easeInOut", delay: Math.random() * 1200 });
      this.suspects[s.key] = sp;
    }
    this.spots = L.spots.map((s) => ({
      key: s.key, x: this.P(s.x, 0, 0).x, markY: this.P(s.x, s.markY, s.markZ).y,
      label: s.key === "stage" ? this.content.stageLabel : this.content.greet[s.key]?.who ? this.nameOf(s.key) : s.key,
    }));
    for (const s of this.spots) this.sparkle(s.x, s.markY);

    const stage = this.spots.find((s) => s.key === "stage")!;
    const startX = data?.from === "lab" ? stage.x : this.P(L.startX, 0, 0).x;
    const startY = (this.lane.yMin + this.lane.yMax) / 2 + 1;
    this.shadow = this.add.ellipse(startX, startY - 1, 22, 5, 0x000000, 0.35);
    this.smudge = this.add.sprite(startX, startY, "smudge", "idle/E/0").setOrigin(FEET_ORIGIN.x, FEET_ORIGIN.y).play("idle_E");
    this.foot = this.add.sprite(startX - 24, startY - 6, "foot_idle", 0).setOrigin(FEET_ORIGIN.x, FEET_ORIGIN.y).play("foot_idle_E");
    this.cameras.main.scrollX = this.camX(this.smudge.x);
    this.air = atmosphere(this, this.content.kit, L.width, bgKey, restored);

    this.add.text(8, 8, `Case ${this.content.num} · ${this.content.title}`, { fontFamily: FONT, fontSize: "9px", color: "#F2E9CF", backgroundColor: "#0E1938" })
      .setPadding(5, 2, 5, 2).setScrollFactor(0).setDepth(900);
    this.checklist = this.add.text(W - 8, 8, "", { fontFamily: FONT, fontSize: "10px", color: "#0E1938", backgroundColor: "#F2E9CF", lineSpacing: 2 })
      .setPadding(5, 3, 5, 3).setOrigin(1, 0).setScrollFactor(0).setDepth(900);
    this.prompt = this.add.text(0, 0, "", { fontFamily: FONT, fontSize: "9px", color: "#0E1938", backgroundColor: "#F2E9CF" })
      .setPadding(4, 1, 4, 1).setOrigin(0.5, 1).setDepth(901).setVisible(false);
    this.promptFor = null;

    this.dlg = new Dialogue(this);
    this.keys = this.input.keyboard!.addKeys("UP,DOWN,LEFT,RIGHT,W,A,S,D,SHIFT,E,SPACE") as any;
    this.input.on("pointerdown", (p: Phaser.Input.Pointer) => this.onTap(p));
    this.input.keyboard?.on("keydown-E", () => this.tryInteract());
    this.input.keyboard?.on("keydown", () => { this.idleMs = 0; });

    themeFor(this.content.kit);
    ambience(this.content.kit, restored);
    this.lastLayer = restored ? 3 : this.progressLayer();
    layer(this.lastLayer);
    const reveal = data?.from === "lab" || data?.from === "crossexam" ? inkIn(this) : null;
    if (!api.current || api.current.kit !== this.content.kit) {
      progress.reset(this.content.kit);
      try {
        await api.newCase(this.content.kit);
      } catch {
        this.cameras.main.fadeIn(400, 5, 6, 15);
        await this.dlg.play([{ who: "foot", expr: "worried", text: "*This case's suspects live on the agent server, and it isn't answering. Start it (server/, uvicorn) and come back." }]);
        this.scene.start("Map");
        return;
      }
    }
    this.refreshChecklist(false);
    if (data?.from === "hq" || data?.from === "next") {
      await pageReveal(this);
      if (!seenChapters.has(this.content.kit)) {
        seenChapters.add(this.content.kit);
        await chapterCard(this, { num: this.content.num, chapter: this.content.chapter, place: this.content.place, title: this.content.title });
      }
      // the establishing shot: look over the crime scene, then come back to Smudge
      this.focusX = stage.x;
      await wait(this, 1100);
      this.focusX = null;
      await wait(this, 350);
      await this.dlg.play(this.content.arrive);
    } else if (data?.from === "lab") {
      await reveal;
      await this.dlg.play([this.content.afterLab]);
    } else if (reveal) {
      await reveal;
    } else {
      this.cameras.main.fadeIn(400, 5, 6, 15);
    }
    this.busy = false;
  }

  private nameOf(key: string) {
    return api.current?.suspects[key]?.name ?? key.charAt(0).toUpperCase() + key.slice(1);
  }

  /** 0 on arrival, +1 for the inspection, the lab and questioning everyone: the theme grows with the case. */
  private progressLayer() {
    return (progress.inspected ? 1 : 0) + (progress.labDone ? 1 : 0) + (progress.questioned.size >= 3 ? 1 : 0);
  }

  private refreshChecklist(celebrate = true) {
    const q = progress.questioned;
    const tick = (b: boolean) => (b ? "☑" : "☐");
    const marks = [progress.inspected, progress.labDone, q.size >= 3, progress.solved].map((b) => (b ? "1" : "0")).join("");
    this.checklist.setText([
      `${tick(progress.inspected)} ${this.content.checklist[0]}`,
      `${tick(progress.labDone)} ${this.content.checklist[1]}`,
      `${tick(q.size >= 3)} Question all three (${q.size}/3)`,
      `${tick(progress.solved)} Call everyone to the stage`,
    ].join("\n"));
    if (celebrate && this.ticks && marks !== this.ticks && marks.split("1").length > this.ticks.split("1").length) {
      punch(this, this.checklist, 0.08, 110);
      sfx("snap");
    }
    this.ticks = marks;
    const n = progress.solved ? 3 : this.progressLayer();
    if (n > this.lastLayer) {
      this.lastLayer = n;
      layer(n);
      if (celebrate) sting("progress");
    }
  }

  private sparkle(x: number, y: number) {
    const c = this.add.container(x, y).setDepth(700);
    const g = this.add.graphics();
    g.fillStyle(0xfff3c4, 1).fillRect(-0.5, -3.5, 1, 7).fillRect(-3.5, -0.5, 7, 1);
    c.add(g);
    this.tweens.add({ targets: c, scale: { from: 0.4, to: 1.1 }, alpha: { from: 0.3, to: 1 }, duration: 700, yoyo: true, repeat: -1, delay: Math.random() * 700 });
  }

  private onTap(p: Phaser.Input.Pointer) {
    this.idleMs = 0;
    if (this.busy || this.dlg.active) return;
    const wx = p.worldX, wy = p.worldY;
    const spot = this.spots.find((s) => Math.abs(wx - s.x) < 22 && wy > s.markY - 20 && wy < this.lane.yMax + 8);
    const tx = Phaser.Math.Clamp(spot ? spot.x + (this.smudge.x < spot.x ? -14 : 14) : wx, this.lane.xMin, this.lane.xMax);
    const ty = Phaser.Math.Clamp(wy, this.lane.yMin, this.lane.yMax);
    this.target = { x: tx, y: spot ? this.lane.yMax - 2 : ty, spot };
    this.tapMark(tx, this.target.y);
  }

  /** A small ink ring where the player tapped. */
  private tapMark(x: number, y: number) {
    const r = this.add.ellipse(x, y, 6, 2).setStrokeStyle(1, 0xf2e9cf, 0.9).setDepth(y - 2);
    this.tweens.add({ targets: r, scaleX: 3, scaleY: 3, alpha: 0, duration: 380, ease: "Quad.easeOut", onComplete: () => r.destroy() });
  }

  private nearest(): Spot | undefined {
    return this.spots.find((s) => Math.abs(this.smudge.x - s.x) < 24);
  }

  private tryInteract() {
    if (this.busy || this.dlg.active) return;
    const s = this.nearest();
    if (s) this.interact(s);
  }

  /** Camera left edge that keeps x centred, clamped to the backdrop. (Phaser's own follow and bounds assume a
   *  centred camera origin; ours zooms from the top-left, see main.ts.) */
  private camX(x: number) { return Phaser.Math.Clamp(Math.round(x - W / 2), 0, this.layout().width - W); }

  update(_t: number, dtMs: number) {
    if (!this.smudge) return;
    const dt = Math.min(dtMs, 50) / 1000;
    const cam = this.cameras.main;
    // the camera leads a little in the direction Smudge faces, or looks where a scene wants it to
    const facing = this.dir.includes("E") ? 1 : this.dir.includes("W") ? -1 : 0;
    this.lead += ((Math.abs(this.vel.x) > 8 ? facing * 36 : 0) - this.lead) * Math.min(1, dt * 1.6);
    const look = this.focusX ?? this.smudge.x + this.lead;
    cam.scrollX += (this.camX(look) - cam.scrollX) * Math.min(1, dt * (this.focusX !== null ? 2.2 : 5));

    let ix = 0, iy = 0;
    const k = this.keys;
    const free = !this.busy && !this.dlg.active;
    let run = false;
    if (free) {
      if (k.LEFT.isDown || k.A.isDown) ix -= 1;
      if (k.RIGHT.isDown || k.D.isDown) ix += 1;
      if (k.UP.isDown || k.W.isDown) iy -= 1;
      if (k.DOWN.isDown || k.S.isDown) iy += 1;
      if (ix || iy) this.target = null;
      if (!ix && !iy && this.target) {
        const dx = this.target.x - this.smudge.x, dy = this.target.y - this.smudge.y;
        if (Math.hypot(dx, dy) < 2) {
          const spot = this.target.spot;
          this.target = null;
          if (spot) this.interact(spot);
        } else { ix = dx; iy = dy; }
      }
      run = k.SHIFT.isDown || (!!this.target && Math.abs(this.target.x - this.smudge.x) > 150);
    }
    // ease towards the wanted velocity instead of starting and stopping dead
    const len = Math.hypot(ix, iy) || 1;
    const speed = run ? RUN : WALK;
    let wx = ix ? (ix / len) * speed : 0, wy = iy ? (iy / len) * speed * 0.35 : 0;
    if (this.target) {
      // ease in to a tapped target so Smudge doesn't overshoot it
      const d = Math.hypot(this.target.x - this.smudge.x, this.target.y - this.smudge.y);
      const k2 = Math.min(1, d / 14);
      wx *= k2; wy *= k2;
    }
    const a = Math.min(1, dt * ACCEL);
    this.vel.x += (wx - this.vel.x) * a;
    this.vel.y += (wy - this.vel.y) * a;
    if (!ix && !iy && Math.hypot(this.vel.x, this.vel.y) < 4) this.vel = { x: 0, y: 0 };
    if (!free) this.vel = { x: 0, y: 0 };

    const moving = Math.hypot(this.vel.x, this.vel.y) > 4;
    if (moving) {
      this.idleMs = 0;
      this.smudge.x = Phaser.Math.Clamp(this.smudge.x + this.vel.x * dt, this.lane.xMin, this.lane.xMax);
      this.smudge.y = Phaser.Math.Clamp(this.smudge.y + this.vel.y * dt, this.lane.yMin, this.lane.yMax);
      if (ix || iy) this.dir = dirFromVector(ix, iy * 0.6);
      const running = Math.hypot(this.vel.x, this.vel.y) > (WALK + RUN) / 2;
      this.smudge.play(`${running ? "run" : "walk"}_${this.dir}`, true);
      this.stepTimer -= dtMs;
      if (this.stepTimer <= 0) { step(GROUND[this.content.kit] ?? "stone"); this.stepTimer = running ? 180 : 300; }
      this.dustTimer -= dtMs;
      if (running && this.dustTimer <= 0) { dustPuff(this, this.smudge.x, this.smudge.y, 3, DUST[this.content.kit]); this.dustTimer = 220; }
      this.wasRunning = running;
    } else {
      if (this.wasRunning) { dustPuff(this, this.smudge.x + (this.dir.includes("W") ? -6 : 6), this.smudge.y, 6, DUST[this.content.kit]); squash(this, this.smudge, 0.1, 70); }
      this.wasRunning = false;
      if (free) this.smudge.play(`idle_${this.dir}`, true);
    }
    this.shadow.setPosition(this.smudge.x, this.smudge.y - 1).setDepth(this.smudge.y - 1);
    this.smudge.setDepth(this.smudge.y + 0.2);
    const behind = this.dir.includes("W") ? 24 : -24;
    this.foot.x += (this.smudge.x + behind - this.foot.x) * Math.min(1, dt * 2.5);
    this.foot.y += (this.smudge.y - 6 - this.foot.y) * Math.min(1, dt * 2.5);
    this.foot.setDepth(this.foot.y + 0.5);
    this.foot.play(`foot_idle_${this.foot.x < this.smudge.x ? "SE" : "SW"}`, true);

    this.glance(dtMs);
    const stage = this.spots.find((s) => s.key === "stage");
    if (stage) this.air.update(this.smudge.x, stage.x, dtMs);

    const s = this.nearest();
    if (s && free) {
      if (this.promptFor !== s) {
        this.promptFor = s;
        this.prompt.setText(`▸ ${s.label}`).setPosition(s.x, s.markY - 4).setAlpha(0).setVisible(true);
        this.tweens.add({ targets: this.prompt, y: s.markY - 8, alpha: 1, duration: 140, ease: "Back.easeOut" });
        sfx("hover");
      }
    } else if (this.promptFor) {
      this.promptFor = null;
      this.prompt.setVisible(false);
    }

    if (free) {
      this.idleMs += dtMs;
      if (this.idleMs > IDLE_NUDGE_MS && this.nudged < 2) { this.idleMs = 0; this.nudged++; void this.nudge(); }
    }
  }

  /** Suspects turn to look at Smudge when he's close, and now and then shuffle on the spot. Everyone alike. */
  private glance(dtMs: number) {
    this.glanceTimer -= dtMs;
    if (this.glanceTimer > 0) return;
    this.glanceTimer = 400;
    for (const [key, sp] of Object.entries(this.suspects)) {
      const dx = this.smudge.x - sp.x;
      const want = Math.abs(dx) < 120 ? dirFromVector(dx, (this.smudge.y - sp.y) + 30) : "S";
      const anim = `${key}_idle_${want}`;
      if (sp.anims.currentAnim?.key !== anim && !sp.anims.currentAnim?.key.includes("_talk_")) sp.play(anim, true);
      if (Math.random() < 0.035 && !this.dlg.active) hop(this, sp, 3, 120, false);
    }
  }

  /** After a long quiet spell, Footnote points at the next thing to do. */
  private async nudge() {
    this.busy = true;
    const next = !progress.inspected ? `Look at ${this.content.stageLabel.toLowerCase()}: walk up to it and press E, or tap it.`
      : !progress.labDone ? `${this.content.stageLabel} again: the lab's waiting.`
        : progress.questioned.size < 3 ? `We still need ${3 - progress.questioned.size} more statement${progress.questioned.size === 2 ? "" : "s"}. Talk to everyone.`
          : `Everyone's on record. Back to ${this.content.stageLabel.toLowerCase()}, and call them to the stage!`;
    await this.dlg.play([{ who: "foot", expr: "neutral", text: `Psst, Smudge. ${next}` }]);
    this.busy = false;
  }

  private async interact(s: Spot) {
    this.busy = true;
    this.promptFor = null;
    this.prompt.setVisible(false);
    this.smudge.play("idle_N");
    this.dir = "N";
    if (s.key === "stage") await this.stage();
    else await this.interrogate(s.key);
    this.refreshChecklist();
    this.idleMs = 0;
    this.busy = false;
  }

  /** First meeting: the camera eases over, the suspect hops, a name plate slides in. */
  private async introduce(who: string) {
    const sp = this.suspects[who];
    if (sp) { this.focusX = (sp.x + this.smudge.x) / 2; hop(this, sp, 7, 150); }
    sting("intro");
    const s = api.current!.suspects[who];
    const plate = this.add.container(-200, 248).setScrollFactor(0).setDepth(950);
    const bg = this.add.rectangle(0, 0, 170, 30, 0x0e1938, 0.95).setOrigin(0, 0.5).setStrokeStyle(1, 0xc9302a);
    const n = this.add.text(10, -6, s.name.toUpperCase(), { fontFamily: DISPLAY, fontSize: "16px", color: "#F2E9CF" }).setOrigin(0, 0.5);
    const r = this.add.text(10, 8, s.role, { fontFamily: FONT, fontSize: "9px", color: "#FAC775" }).setOrigin(0, 0.5);
    plate.add([bg, n, r]);
    await tween(this, { targets: plate, x: 0, duration: 260, ease: "Back.easeOut" });
    this.time.delayedCall(1500, () => this.tweens.add({ targets: plate, x: -200, duration: 220, ease: "Cubic.easeIn", onComplete: () => plate.destroy() }));
  }

  private async interrogate(who: string) {
    const first = !progress.questioned.has(who);
    progress.questioned.add(who);
    if (first) await this.introduce(who);
    else if (this.suspects[who]) this.focusX = (this.suspects[who].x + this.smudge.x) / 2;
    await this.dlg.say(first ? this.content.greet[who] : { who: who as Who, expr: "neutral", text: "Back again, detective?" });
    const sp = this.suspects[who];
    for (let i = 0; i < 8; i++) {
      this.dlg.hide();
      const q = await askBox(this, this.content.chips[who], `Ask ${api.current!.suspects[who].name} anything...`);
      if (!q) break;
      this.dlg.say({ who: "smudge", expr: "thinking", text: q });
      sp?.play(`${who}_talk_S`, true);
      const r = await api.ask(who, q);
      const spoken = speak(who, r.answer);
      // long replies are paged by Dialogue.say, so speech and transcript keep the full text
      await this.dlg.say({ who: who as Who, expr: /nothing|none|never|wasn't|not me/i.test(r.answer) ? "smug" : "neutral", text: r.answer });
      await spoken;
      sp?.play(`${who}_idle_S`, true);
      progress.transcript.push({ who, q, a: r.answer });
    }
    if (progress.questioned.size === 1 && !progress.labDone && this.content.afterFirst) {
      await this.dlg.play(this.content.afterFirst);
    }
    this.dlg.hide();
    this.focusX = null;
  }

  private async stage() {
    if (progress.solved) {
      await this.dlg.play([{ who: "foot", expr: "happy", text: "Case closed! The law's back in the book, and this place is behaving again." }]);
      return;
    }
    const stage = this.spots.find((s) => s.key === "stage")!;
    this.focusX = stage.x;
    if (!progress.inspected) {
      progress.inspected = true;
      await this.dlg.play(this.content.inspect);
      this.refreshChecklist();
    }
    if (!progress.labDone) {
      await this.dlg.play([this.content.toLab]);
      await inkOut(this);
      this.scene.start(this.content.lab, { kit: this.content.kit });
      return;
    }
    this.focusX = null;
    if (progress.questioned.size < 3) {
      await this.dlg.play([{ who: "foot", expr: "neutral", text: `You've got your evidence. Question everyone first, so we have their statements on record. (${progress.questioned.size}/3)` }]);
      return;
    }
    const names = Object.values(api.current!.suspects).map((s) => s.name);
    await this.dlg.play([
      { who: "smudge", expr: "determined", text: `${names.join(". ")}. To the stage, please. One of you has some explaining to do.` },
    ]);
    music("off");
    sfx("rise");
    await inkOut(this, 560);
    this.scene.start("CrossExam");
  }
}

