// The Midnight Fall's lab, in four steps (spec §4 beats 4-7):
//  1. the recording: play the record (playhead, rain, thunder, the cry, the thud), then drag two markers onto the cry
//     and the thud on its waveform. Δt is the fall time. A checklist top-left and gold arrows say what to do next.
//  2. the drop test: drop a sack from the lowest balcony, predict the top, drop it. Stopwatch and strobe trail.
//     (No gallery drop: its 1.5 s would hand over the answer before the notebook.)
//  3. slip or push: two sacks leave the same balcony at once, one slipping, one pushed. Same landing time.
//     Skipped under ?judges.
//  4. the notebook: h = ½ × g × t², checked by the server.
// Drawn over lab_tower / lab_gramophone at full opacity; every coordinate comes from fall_layout.json. Registered by cases/fall/index.ts.
import Phaser from "phaser";
import * as Tone from "tone";
import { W, H, Z, FONT, DISPLAY, JUDGES } from "../consts";
import { Dialogue } from "../systems/dialogue";
import { makePixel, wait, tween } from "../systems/fx";
import { overlay } from "../systems/ui";
import { sfx, themeFor, layer, ambience } from "../audio";
import { inkIn, inkOut } from "../systems/transition";
import { api, LabResult } from "../api";
import { progress } from "../state";
import { calc } from "../systems/lab/calc";
import { FALL } from "../cases/fall/layout";

interface Recording { length: number; cry_at: number; thud_at: number; thunder_at: number[] }
interface Balcony { id: string; name: string; h: number }
interface Sack { obj: Phaser.GameObjects.Image; x0: number; vx: number; h: number; landed: boolean }

// The art's own geometry (assets/case10/fall_layout.json): lab_tower is drawn for these numbers, so the sacks fall true to it.
const T = FALL.tower, STRIP = FALL.gramophone.strip;
const GROUND = T.ground_y, PXM = T.px_per_m, WALL = T.wall_x, DROP_X = T.drop_from_x, SNAP = 0.1;
// the right-hand panel (the sky beside the tower) holds the titles, stopwatch and results
const PX = 330;
const NAMES: Record<string, string> = { rivet: "Armoury", varnish: "Gallery", pendle: "Clock room" };
// the checklist in the top-left corner; slip or push is cut under ?judges
const STEPS = JUDGES ? ["Listen to the record", "Time the drops", "Work out the height"]
  : ["Listen to the record", "Time the drops", "Slip or push?", "Work out the height"];

export class LabFall extends Phaser.Scene {
  private dlg!: Dialogue;
  private g = 9.8;
  private gap = 0;
  private bits: Phaser.GameObjects.GameObject[] = [];
  private track: Phaser.GameObjects.GameObject[] = [];
  private run: { sacks: Sack[]; t: number; strobe: boolean; lastDot: number; watch?: Phaser.GameObjects.Text; done: (t: number) => void } | null = null;

  constructor() { super("LabFall"); }

  async create() {
    // scenes added after boot do not get the world zoom, so set it here
    this.cameras.main.setOrigin(0, 0).setZoom(Z);
    this.bits = [];
    this.track = [];
    this.run = null;
    this.gap = 0;
    this.g = Number(api.current?.g) || 9.8;
    makePixel(this);
    themeFor("lab");
    layer(2);
    ambience("lab");
    void inkIn(this);
    this.dlg = new Dialogue(this);
    await this.recording();
    await this.dropTest();
    if (!JUDGES) await this.slipOrPush();
    const r = await this.notebook();
    await this.evidenceCard(r);
    progress.labDone = true;
    await inkOut(this);
    this.scene.start("District", { kit: "fall", from: "lab" });
  }

  update(_time: number, delta: number) {
    const run = this.run;
    if (!run) return;
    run.t += Math.min(delta, 100) / 1000;
    for (const s of run.sacks) {
      if (s.landed) continue;
      const fallen = Math.min(s.h, 0.5 * this.g * run.t * run.t);
      const t = Math.sqrt((2 * fallen) / this.g);
      // sideways travel is measured from the wall, the sack is drawn at the balcony rail (DROP_X), so ease the 18 px back
      // in as it falls: a push of 3 m/s for 1.5 s then lands exactly on the chalk outline, 4.5 m from the wall
      s.obj.setPosition(s.x0 + s.vx * t * PXM - (s.vx > 0 ? (DROP_X - WALL) * (fallen / s.h) : 0), GROUND - (s.h - fallen) * PXM - 8);
      if (fallen >= s.h) s.landed = true;
    }
    if (run.strobe) {
      while (run.lastDot + 0.1 <= run.t && !run.sacks[0].landed) {
        run.lastDot += 0.1;
        const s = run.sacks[0];
        const y = GROUND - (s.h - 0.5 * this.g * run.lastDot ** 2) * PXM - 8;
        this.keep(this.add.circle(s.x0, y + 5, 1.5, 0xfac775));
      }
    }
    const tLand = Math.sqrt((2 * run.sacks[0].h) / this.g);
    run.watch?.setText(`${Math.min(run.t, tLand).toFixed(2)} s`);
    if (run.sacks.every((s) => s.landed)) {
      this.run = null;
      sfx("thunk");
      run.watch?.setText(`${tLand.toFixed(2)} s`);
      run.done(tLand);
    }
  }

  // ---- helpers -------------------------------------------------------------
  private keep<T extends Phaser.GameObjects.GameObject>(o: T): T { this.bits.push(o); return o; }
  private clear() { for (const o of this.bits) o.destroy(); this.bits = []; }
  private label(x: number, y: number, text: string, size = 9, color = "#F2E9CF") {
    return this.keep(this.add.text(x, y, text, { fontFamily: FONT, fontSize: `${size}px`, color }));
  }
  private button(x: number, y: number, text: string, fn: () => void, fill = "#C9302A") {
    const b = this.keep(this.add.text(x, y, text, { fontFamily: FONT, fontSize: "10px", color: "#FFFFFF", backgroundColor: fill })
      .setPadding(8, 3, 8, 3).setOrigin(0.5).setInteractive({ useHandCursor: true }));
    b.on("pointerdown", () => { sfx("click"); fn(); });
    return b;
  }
  /** The checklist: steps done are ticked, the current one is lit, with what to do right now under it. */
  private step(n: number, todo: string) {
    for (const o of this.track) o.destroy();
    this.track = [];
    let y = 5;
    STEPS.forEach((name, i) => {
      const now = i === n;
      const t = this.add.text(5, y, `${i < n ? "✓" : now ? "▸" : " "} ${i + 1}  ${name}`, {
        fontFamily: FONT, fontSize: "8px", color: now ? "#FAC775" : i < n ? "#7FD4A0" : "#7A86A8",
      }).setDepth(1000).setPadding(3, 1, 3, 1).setBackgroundColor("rgba(7,10,23,0.78)");
      this.track.push(t);
      y += 11;
      if (now) {
        const d = this.add.text(12, y, todo, { fontFamily: FONT, fontSize: "7px", color: "#F2E9CF", wordWrap: { width: 108 } })
          .setDepth(1000).setPadding(3, 1, 3, 2).setBackgroundColor("rgba(7,10,23,0.78)");
        this.tweens.add({ targets: d, alpha: { from: 0, to: 1 }, x: { from: 6, to: 12 }, duration: 220 });
        this.track.push(d);
        y += d.height + 2;
      }
    });
  }
  /** A bouncing gold waypoint pointing at what to touch next. */
  private arrow(x: number, y: number, dir: "down" | "up" = "down") {
    const s = dir === "down" ? 1 : -1;
    const a = this.keep(this.add.graphics({ x, y }).setDepth(900));
    a.fillStyle(0x0e1938).fillTriangle(-6, -9 * s, 6, -9 * s, 0, 1 * s);
    a.fillStyle(0xfac775).fillTriangle(-4, -8 * s, 4, -8 * s, 0, -1 * s);
    this.tweens.add({ targets: a, y: y - 4 * s, duration: 380, yoyo: true, repeat: -1, ease: "Sine.easeInOut" });
    return a;
  }
  /** A thin cry that rises (the same voice as the cold open). */
  private cry() {
    if (Tone.getContext().state !== "running") return;
    try {
      const s = new Tone.Synth({ oscillator: { type: "sine" }, portamento: 0.3, envelope: { attack: 0.03, decay: 0.1, sustain: 0.8, release: 0.3 } }).toDestination();
      s.volume.value = -14;
      s.triggerAttack("D5");
      setTimeout(() => { try { s.setNote("B5"); } catch { /* gone */ } }, 90);
      setTimeout(() => { try { s.triggerRelease(); } catch { /* gone */ } }, 380);
      setTimeout(() => { try { s.dispose(); } catch { /* gone */ } }, 1500);
    } catch { /* sound is a bonus */ }
  }
  private hint(text: string) { void this.dlg.say({ who: "foot", expr: "worried", text }); }
  private balconies(): Balcony[] {
    const b = (api.current?.balconies ?? { rivet: 4.9, varnish: 11.0, pendle: 19.6 }) as Record<string, number>;
    return Object.entries(b).map(([id, h]) => ({ id, name: NAMES[id] ?? id, h })).sort((a, z) => a.h - z.h);
  }
  private balconyY(h: number) { return GROUND - h * PXM; }          // = tower.balconies[id].y in fall_layout.json

  // ---- 1. the recording ----------------------------------------------------
  private recording(): Promise<void> {
    const rec = api.current!.recording as Recording;
    const X0 = STRIP.x0, XW = STRIP.x1 - STRIP.x0, PXS = STRIP.px_per_s, Y0 = STRIP.mid;
    this.keep(this.add.image(0, 0, "lab_gramophone").setOrigin(0));
    this.step(0, "Press Play and listen for the cry and the thud.");
    // the waveform: low noise, wide thunder, a thin cry, a sharp thud
    const bump = (t: number, c: number, s: number) => Math.exp(-((t - c) ** 2) / (2 * s * s));
    const noise = (i: number) => Math.abs((Math.sin(i * 12.9898) * 43758.5453) % 1);
    const wave = this.keep(this.add.graphics());
    wave.lineStyle(1, 0x8fe0c0, 0.9);
    for (let x = 0; x <= XW; x++) {
      const t = x / PXS;
      let a = 2 + noise(x) * 4;
      for (const th of rec.thunder_at) a += 33 * bump(t, th, 0.18) * (0.55 + 0.45 * noise(x + 99));
      a += 36 * bump(t, rec.cry_at, 0.02) + 24 * bump(t, rec.thud_at, 0.01);
      wave.lineBetween(X0 + x, Y0 - Math.min(a, 36), X0 + x, Y0 + Math.min(a, 36));
    }
    const readout = this.label(STRIP.x1, 96, "", 10, "#FFFFFF").setOrigin(1, 0);

    const spikes = [rec.cry_at, rec.thud_at];
    const markers = () => {
      if (lockWay) return;
      this.step(0, "Drag the pink marker onto the cry, the blue one onto the thud.");
      marks.forEach((m) => { if (!m.way) m.way = this.arrow(m.handle.x, STRIP.y1 + 38, "up"); });
    };
    let lock: Phaser.GameObjects.Text | undefined, lockWay: Phaser.GameObjects.Graphics | undefined;
    const ready = () => {
      const [a, b] = [Math.min(marks[0].t, marks[1].t), Math.max(marks[0].t, marks[1].t)];
      if (a === rec.cry_at && b === rec.thud_at && !lockWay && lock) {
        this.step(0, "That's the fall time. Lock it in.");
        lockWay = this.arrow(lock.x, lock.y - 12);
      }
    };
    const marks: { t: number; line: Phaser.GameObjects.Rectangle; handle: Phaser.GameObjects.Rectangle; way?: Phaser.GameObjects.Graphics }[] = [1.0, 4.0].map((t0, i) => {
      const line = this.keep(this.add.rectangle(0, Y0, 1, STRIP.y1 - STRIP.y0, i ? 0x7ab4ff : 0xf07aae));
      const handle = this.keep(this.add.rectangle(0, STRIP.y1 + 22, 12, 10, i ? 0x7ab4ff : 0xf07aae).setInteractive({ useHandCursor: true, draggable: true }));
      const m: { t: number; line: Phaser.GameObjects.Rectangle; handle: Phaser.GameObjects.Rectangle; way?: Phaser.GameObjects.Graphics } = { t: t0, line, handle };
      const place = () => { const x = X0 + m.t * PXS; line.setX(x); handle.setX(x); };
      handle.on("drag", (_p: Phaser.Input.Pointer, dragX: number) => {
        let t = Phaser.Math.Clamp((dragX - X0) / PXS, 0, STRIP.seconds);
        for (const s of spikes) if (Math.abs(t - s) <= SNAP) t = s;     // a marker clicks onto a spike nearby
        m.t = t;
        place();
        show();
        m.way?.setX(m.handle.x);
        if (spikes.includes(t)) { m.way?.setVisible(false); ready(); }
        else m.way?.setVisible(true);
      });
      place();
      return m;
    });
    const show = () => readout.setText(`Δt = ${Math.abs(marks[1].t - marks[0].t).toFixed(2)} s`);
    show();
    // the record itself: a playhead sweeps the strip and you hear the rain, the thunder, the cry and the thud
    const play = this.button(58, 214, "▶ Play", () => {
      if (!play.input?.enabled) return;
      playWay.destroy();
      play.disableInteractive().setAlpha(0.5);
      void this.playRecord(rec).then(() => { play.setInteractive({ useHandCursor: true }).setAlpha(1).setText("▶ Again"); markers(); });
    }, "#2E5CAD");
    const playWay = this.arrow(58, 200);
    return new Promise((resolve) => {
      lock = this.button(W / 2, 252, "Lock in Δt", () => {
        const [a, b] = [Math.min(marks[0].t, marks[1].t), Math.max(marks[0].t, marks[1].t)];
        if (a === rec.cry_at && b === rec.thud_at) {
          this.gap = Math.round((rec.thud_at - rec.cry_at) * 100) / 100;
          sfx("chime");
          this.dlg.hide();
          this.clear();
          resolve();
        } else {
          sfx("wrong");
          this.hint("*Measure from the cry to the thud. Not the thunder.");
        }
      });
    });
  }

  /** Play the record: a playhead sweeps the strip, the disc spins, and each sound rings out of the horn on cue. */
  private async playRecord(rec: Recording) {
    const ms = STRIP.seconds * 1000, BELL = { x: 159, y: 58 }, DISC = { x: 58, y: 148 };
    const head = this.keep(this.add.rectangle(STRIP.x0, STRIP.mid, 2, STRIP.y1 - STRIP.y0 + 8, 0xc9302a, 0.95).setDepth(5));
    const glint = this.keep(this.add.graphics().setDepth(5));
    const ring = (big: number) => {
      const c = this.keep(this.add.circle(BELL.x, BELL.y, 6).setStrokeStyle(1.5, 0xfff0b0, 0.9).setDepth(5));
      this.tweens.add({ targets: c, radius: big, alpha: 0, duration: 650, onComplete: () => c.destroy() });
    };
    const at = (t: number, fn: () => void) => this.time.delayedCall(t * 1000, fn);
    for (const th of rec.thunder_at) at(th - 0.15, () => { sfx("rumble"); ring(34); });
    at(rec.cry_at, () => { this.cry(); ring(22); });
    at(rec.thud_at, () => { sfx("thunk"); ring(28); this.cameras.main.shake(90, 0.004); });
    const crackle = this.time.addEvent({ delay: 130, repeat: Math.floor(ms / 130), callback: () => { if (Math.random() < 0.45) sfx("type"); } });
    await tween(this, {
      targets: head, x: STRIP.x1, duration: ms, ease: "Linear",
      onUpdate: () => {
        const a = this.time.now / 70;
        glint.clear().lineStyle(1, 0xd8dcec, 0.85)
          .lineBetween(DISC.x + Math.cos(a) * 9, DISC.y + Math.sin(a) * 2.2, DISC.x + Math.cos(a) * 26, DISC.y + Math.sin(a) * 6.2);
      },
    });
    crackle.remove();
    head.destroy();
    glint.destroy();
  }

  // ---- 2. the drop test ----------------------------------------------------
  private drawTower() {
    // the tower, the metre strip, the balcony rails and the chalk outline are all in the picture
    this.keep(this.add.image(0, 0, "lab_tower").setOrigin(0));
    for (const b of this.balconies()) this.label(WALL + 37, this.balconyY(b.h) - 11, `${b.name}
${b.h} m`, 7, "#F2E9CF").setLineSpacing(1);
    // one dark panel in the sky holds the stopwatch and everything measured, so nothing floats over the art
    this.keep(this.add.rectangle(PX - 8, 4, W - PX + 4, 142, 0x070a17, 0.78).setOrigin(0).setStrokeStyle(1, 0x3a4468));
  }

  /** Resolves when the player clicks one of these balconies (any balcony when ids is empty). */
  private pickBalcony(ids: string[]): Promise<Balcony> {
    return new Promise((resolve) => {
      const zones: Phaser.GameObjects.GameObject[] = [];
      for (const b of this.balconies()) {
        const ok = !ids.length || ids.includes(b.id);
        const y = this.balconyY(b.h);
        const glow = ok ? this.keep(this.add.rectangle(WALL + 2, y - 4, 34, 9, 0xfac775, 0.5).setOrigin(0)) : null;
        if (glow) this.tweens.add({ targets: glow, alpha: 0.1, duration: 500, yoyo: true, repeat: -1 });
        if (!ok) continue;
        const z = this.keep(this.add.zone(WALL, y - 12, 70, 24).setOrigin(0).setInteractive({ useHandCursor: true }));
        zones.push(z, ...(glow ? [glow] : []), this.arrow(WALL + 16, y - 16));
        z.on("pointerdown", () => { for (const o of zones) o.destroy(); resolve(b); });
      }
    });
  }

  private sack(x: number, y: number, tint?: number) {
    const o = this.add.image(x, y, "sack");
    if (tint) o.setTint(tint);
    return o;
  }

  private launch(sacks: { vx: number; h: number; tint?: number }[], strobe: boolean, watch?: Phaser.GameObjects.Text): Promise<number> {
    sfx("swish");
    return new Promise((done) => {
      const list = sacks.map((s) => ({
        obj: this.keep(this.sack(DROP_X, this.balconyY(s.h) - 8, s.tint)), x0: DROP_X, vx: s.vx, h: s.h, landed: false,
      }));
      this.run = { sacks: list, t: 0, strobe, lastDot: 0, watch, done };
    });
  }

  private async dropTest() {
    this.drawTower();
    const watch = this.label(PX, 10, "0.00 s", 16, "#FFFFFF").setFontFamily(DISPLAY);
    this.label(PX, 40, "balcony       height   time", 8, "#9AA6C8");
    const bs = this.balconies();
    const order = [bs[0], bs[bs.length - 1]];       // lowest, then the top: four times the height, twice the time
    let row = 0;
    for (const b of order) {
      let guess = 0;
      if (b === bs[bs.length - 1]) {
        this.step(1, `Guess first: how long will a sack take to fall from the ${b.name}?`);
        guess = await this.predict(b);
      }
      this.dlg.hide();                                  // Footnote's box would sit over the stopwatch and eat the click
      this.step(1, `Click the glowing ${b.name} balcony to drop a sack. Watch the stopwatch.`);
      await this.pickBalcony([b.id]);
      const t = await this.launch([{ vx: 0, h: b.h }], true, watch);
      this.label(PX, 52 + row++ * 12, `${b.name.padEnd(12)} ${b.h.toFixed(1).padStart(4)} m   ${t.toFixed(1)} s`, 9);
      if (guess) {
        const v = this.label(PX, 84, `You said ${guess} s. It took ${t.toFixed(1)} s.`, 9, "#FAC775").setWordWrapWidth(140);
        this.tweens.add({ targets: v, scale: { from: 1.3, to: 1 }, duration: 300, ease: "Back.easeOut" });
        // in the panel, not a dialogue box: a box would cover the stopwatch and the clock-room balcony
        this.label(PX, 112, "Four times higher. Only twice as long!", 9, "#FFFFFF").setWordWrapWidth(140);
      }
      await wait(this, 700);
    }
    this.step(1, "Four times the height, only twice the time. Press Next.");
    await this.next();
    this.dlg.hide();
    this.clear();
  }

  /** The prediction dial before the top drop. Stored for the playtest numbers. */
  private predict(b: Balcony): Promise<number> {
    const head = this.label(PX, 84, `Predict: from ${b.name}, how long?`, 9, "#FFFFFF").setWordWrapWidth(140);
    return new Promise((resolve) => {
      const btns = [1, 2, 3, 4].map((n, i) => this.button(PX + 16 + i * 36, 120, `${n} s`, () => {
        try { localStorage.setItem("smudge.predict", String(n)); } catch { /* private window */ }
        for (const x of btns) x.destroy();
        head.destroy();
        resolve(n);
      }, "#2E5CAD"));
    });
  }

  private next(): Promise<void> {
    return new Promise((resolve) => {
      const way = this.arrow(W - 60, 242);
      const b = this.button(W - 60, 256, "Next ▸", () => { b.destroy(); way.destroy(); resolve(); });
    });
  }

  // ---- 3. slip or push? ----------------------------------------------------
  private async slipOrPush() {
    this.drawTower();
    this.step(2, "Click any balcony. One sack slips off, one is pushed. Which lands first?");
    const out = Number((api.current?.landing as { from_wall?: number } | undefined)?.from_wall) || T.outline.metres;
    this.label(PX, 40, "pale: slips off, 0.5 m/s\nred: pushed, 3 m/s", 9);
    this.label(PX, 64, "Pushed or dropped, they land together.", 9, "#FFFFFF").setWordWrapWidth(140);
    const b = await this.pickBalcony([]);
    const t = await this.launch([{ vx: 0.5, h: b.h }, { vx: 3, h: b.h, tint: 0xff7a6a }], false);
    const same = this.label(PX + 70, 100, "SAME TIME", 20, "#FAC775").setFontFamily(DISPLAY).setOrigin(0.5);
    this.tweens.add({ targets: same, scale: { from: 0.3, to: 1 }, duration: 300, ease: "Back.easeOut" });
    const pushed = 3 * Math.sqrt((2 * b.h) / 9.8);   // exact fall time, not frame-timed t
    this.label(PX, 124, `slip lands ${(0.5 * Math.sqrt((2 * b.h) / 9.8)).toFixed(1)} m out\npush lands ${pushed.toFixed(1)} m out`, 9);
    if (Math.abs(pushed - out) < 0.4) this.label(PX, 150, "The push lands on the outline.", 9, "#FAC775");
    this.step(2, "A push changes where it lands, not when. Press Next.");
    await this.next();
    this.dlg.hide();
    this.clear();
  }

  // ---- 4. the notebook -----------------------------------------------------
  private notebook(): Promise<LabResult> {
    this.step(STEPS.length - 1, `Fill in the notebook: h = 1/2 × g × t × t, with the ${this.gap} s you measured.`);
    return new Promise((resolve) => {
      const form = document.createElement("form");
      form.setAttribute("aria-label", "Notebook");
      form.style.cssText = `font-family:"Smudge Digits","DotGothic16",monospace;background:#F2E9CF;border:2px solid #0E1938;border-radius:4px;
        padding:8px 10px;box-sizing:border-box;display:flex;flex-direction:column;gap:8px;color:#0E1938;
        background-image:repeating-linear-gradient(#F2E9CF 0 15px,#9cb8dc 15px 16px);`;
      const box = (id: string, value = "", readonly = false) =>
        `<input id="${id}" value="${value}" ${readonly ? "readonly tabindex=-1" : ""} inputmode="decimal" autocomplete="off"
          style="width:3.6em;font:inherit;padding:1px 4px;border:1.5px solid #0E1938;background:${readonly ? "#E6DCC0" : "#FFFBEF"};color:#0E1938;border-radius:3px">`;
      form.innerHTML = `<div style="font-weight:700;color:#C9302A">Notebook</div>
        <div style="display:flex;gap:4px;align-items:center;flex-wrap:wrap">h = 1/2 × ${box("nb-g", String(this.g), true)} × ${box("nb-t", String(this.gap), true)} × ${box("nb-t2", String(this.gap), true)} = ${box("nb-h")} m</div>
        <button type="submit" style="font:inherit;padding:4px;border:2px solid #0E1938;background:#C9302A;color:#fff;border-radius:4px;cursor:pointer">Check</button>`;
      ["pointerdown", "keydown", "keyup"].forEach((ev) => form.addEventListener(ev, (e) => e.stopPropagation()));
      const remove = overlay(this, form, 120, 110, 240, 92);
      this.input.keyboard!.enabled = false;
      setTimeout(() => (document.getElementById("nb-h") as HTMLInputElement | null)?.focus(), 50);
      form.onsubmit = async (e) => {
        e.preventDefault();
        const height = calc((document.getElementById("nb-h") as HTMLInputElement).value);
        if (Number.isNaN(height)) { this.hint("*Type a number, or a sum like 0.5*9.8*2."); return; }
        const r = await api.labCheck({ gap: this.gap, height });
        if (r?.ok && r.evidence) {
          remove();
          this.input.keyboard!.enabled = true;
          this.dlg.hide();
          sfx("chime");
          resolve(r);
        } else {
          sfx("wrong");
          (document.getElementById("nb-h") as HTMLInputElement).style.borderColor = "#C9302A";
          this.hint(r?.hint ?? "*h = 1/2 × g × t × t. Try again.");
        }
      };
    });
  }

  private async evidenceCard(r: LabResult) {
    const card = r.card ?? { title: "Evidence", line: "", badge: "EVIDENCE", say: "Hold it." };
    progress.evidence = { label: r.evidence!, badge: card.badge, say: card.say };
    const c = this.add.container(W / 2, H / 2).setDepth(1500).setScale(0.2).setAlpha(0);
    c.add([
      this.add.rectangle(0, 0, 250, 96, 0xf2e9cf).setStrokeStyle(2, 0x0e1938),
      this.add.text(0, -32, "EVIDENCE", { fontFamily: FONT, fontSize: "9px", color: "#C9302A" }).setOrigin(0.5),
      this.add.text(0, -8, card.title, { fontFamily: DISPLAY, fontSize: "20px", color: "#0E1938" }).setOrigin(0.5),
      this.add.text(0, 20, card.line, { fontFamily: FONT, fontSize: "10px", color: "#55361A" }).setOrigin(0.5),
    ]);
    sfx("fanfare");
    await tween(this, { targets: c, scale: 1, alpha: 1, angle: -2, duration: 420, ease: "Back.easeOut" });
    await this.dlg.play([{ who: "foot", expr: "happy", text: "Evidence filed! Whose oath does it break?" }]);
    c.destroy();
  }
}
