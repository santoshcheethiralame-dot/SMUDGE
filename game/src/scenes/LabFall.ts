// The Midnight Fall's lab, in four steps (spec §4 beats 4-7):
//  1. the recording: drag two markers onto the cry and the thud on the gramophone's waveform. Δt is the fall time.
//  2. the drop test: drop a sack from each balcony, with a stopwatch and a strobe trail; predict the top drop first.
//  3. slip or push: two sacks leave the same balcony at once, one slipping, one pushed. Same landing time.
//  4. the notebook: h = ½ × g × t², checked by the server.
// Drawn with shapes over the lab backdrops, so it works with the placeholder art. Registered by cases/fall/index.ts.
import Phaser from "phaser";
import { W, H, Z, FONT, DISPLAY } from "../consts";
import { Dialogue } from "../systems/dialogue";
import { makePixel, wait, tween } from "../systems/fx";
import { overlay } from "../systems/ui";
import { sfx, themeFor, layer, ambience } from "../audio";
import { inkIn, inkOut } from "../systems/transition";
import { api, LabResult } from "../api";
import { progress } from "../state";
import { calc } from "../systems/lab/calc";

interface Recording { length: number; cry_at: number; thud_at: number; thunder_at: number[] }
interface Balcony { id: string; name: string; h: number }
interface Sack { obj: Phaser.GameObjects.Arc; x0: number; vx: number; h: number; landed: boolean }

// the drop-test tower: metres to pixels, the same scale both ways so the paths are true to life
const GROUND = 240, PXM = 8, WALL = 360, SNAP = 0.1;
const NAMES: Record<string, string> = { rivet: "Armoury", varnish: "Gallery", pendle: "Clock room" };

export class LabFall extends Phaser.Scene {
  private dlg!: Dialogue;
  private g = 9.8;
  private gap = 0;
  private bits: Phaser.GameObjects.GameObject[] = [];
  private run: { sacks: Sack[]; t: number; strobe: boolean; lastDot: number; watch?: Phaser.GameObjects.Text; done: (t: number) => void } | null = null;

  constructor() { super("LabFall"); }

  async create() {
    // scenes added after boot do not get the world zoom, so set it here
    this.cameras.main.setOrigin(0, 0).setZoom(Z);
    this.bits = [];
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
    await this.slipOrPush();
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
      s.obj.setPosition(s.x0 - s.vx * t * PXM, GROUND - (s.h - fallen) * PXM - 3);
      if (fallen >= s.h) s.landed = true;
    }
    if (run.strobe) {
      while (run.lastDot + 0.1 <= run.t && !run.sacks[0].landed) {
        run.lastDot += 0.1;
        const s = run.sacks[0];
        const y = GROUND - (s.h - 0.5 * this.g * run.lastDot ** 2) * PXM - 3;
        this.keep(this.add.circle(s.x0, y, 1.5, 0xfac775));
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
  private hint(text: string) { void this.dlg.say({ who: "foot", expr: "worried", text }); }
  private balconies(): Balcony[] {
    const b = (api.current?.balconies ?? { rivet: 4.9, varnish: 11.0, pendle: 19.6 }) as Record<string, number>;
    return Object.entries(b).map(([id, h]) => ({ id, name: NAMES[id] ?? id, h })).sort((a, z) => a.h - z.h);
  }
  private balconyY(h: number) { return GROUND - h * PXM; }

  // ---- 1. the recording ----------------------------------------------------
  private recording(): Promise<void> {
    const rec = api.current!.recording as Recording;
    const X0 = 24, XW = 432, PXS = XW / rec.length, Y0 = 150;
    this.keep(this.add.image(0, 0, "lab_gramophone").setOrigin(0).setAlpha(0.35));
    this.keep(this.add.rectangle(16, 92, 448, 120, 0x070a17, 0.9).setOrigin(0).setStrokeStyle(1, 0x3d4c85));
    this.label(24, 96, "THE GRAMOPHONE · drag a marker onto the cry, one onto the thud", 8, "#FAC775");
    // the waveform: low noise, wide thunder, a thin cry, a sharp thud
    const bump = (t: number, c: number, s: number) => Math.exp(-((t - c) ** 2) / (2 * s * s));
    const noise = (i: number) => Math.abs((Math.sin(i * 12.9898) * 43758.5453) % 1);
    const wave = this.keep(this.add.graphics());
    wave.lineStyle(1, 0x8fe0c0, 0.9);
    for (let x = 0; x < XW; x++) {
      const t = x / PXS;
      let a = 2 + noise(x) * 4;
      for (const th of rec.thunder_at) a += 46 * bump(t, th, 0.18) * (0.55 + 0.45 * noise(x + 99));
      a += 50 * bump(t, rec.cry_at, 0.02) + 34 * bump(t, rec.thud_at, 0.01);
      wave.lineBetween(X0 + x, Y0 - Math.min(a, 52), X0 + x, Y0 + Math.min(a, 52));
    }
    for (let s = 0; s <= rec.length; s++) this.label(X0 + s * PXS - 3, 200, `${s}s`, 7, "#9AA6C8");
    const readout = this.label(456, 96, "", 10, "#FFFFFF").setOrigin(1, 0);

    const spikes = [rec.cry_at, rec.thud_at];
    const marks = [1.0, 4.0].map((t0, i) => {
      const line = this.keep(this.add.rectangle(0, Y0, 1, 108, i ? 0x7ab4ff : 0xf07aae));
      const handle = this.keep(this.add.rectangle(0, 212, 12, 10, i ? 0x7ab4ff : 0xf07aae).setInteractive({ useHandCursor: true, draggable: true }));
      const m = { t: t0, line, handle };
      const place = () => { const x = X0 + m.t * PXS; line.setX(x); handle.setX(x); };
      handle.on("drag", (_p: Phaser.Input.Pointer, dragX: number) => {
        let t = Phaser.Math.Clamp((dragX - X0) / PXS, 0, rec.length);
        for (const s of spikes) if (Math.abs(t - s) <= SNAP) t = s;     // a marker clicks onto a spike nearby
        m.t = t;
        place();
        show();
      });
      place();
      return m;
    });
    const show = () => readout.setText(`Δt = ${Math.abs(marks[1].t - marks[0].t).toFixed(2)} s`);
    show();
    void this.dlg.say({ who: "foot", expr: "neutral", text: "*Find the cry and the thud." });
    return new Promise((resolve) => {
      this.button(W / 2, 252, "Lock in Δt", () => {
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

  // ---- 2. the drop test ----------------------------------------------------
  private drawTower(title: string) {
    this.keep(this.add.image(0, 0, "lab_tower").setOrigin(0).setAlpha(0.4));
    this.keep(this.add.rectangle(0, GROUND, W, H - GROUND, 0x2a2838).setOrigin(0));
    this.keep(this.add.rectangle(WALL, 60, 80, GROUND - 60, 0x3c3858).setOrigin(0));
    // the metre strip up the wall
    const strip = this.keep(this.add.graphics());
    strip.lineStyle(1, 0xf2e9cf, 0.7);
    for (let m = 0; m <= 21; m++) strip.lineBetween(WALL + 2, GROUND - m * PXM, WALL + (m % 5 ? 6 : 12), GROUND - m * PXM);
    for (let m = 5; m <= 20; m += 5) this.label(WALL + 14, GROUND - m * PXM - 5, `${m} m`, 7, "#F2E9CF");
    for (const b of this.balconies()) {
      const y = this.balconyY(b.h);
      this.keep(this.add.rectangle(WALL - 22, y, 22, 3, 0xc8b88a).setOrigin(0, 0));
      this.label(WALL - 26, y - 11, `${b.name} ${b.h} m`, 7, "#C8B88A").setOrigin(1, 0);
    }
    this.label(16, 90, title, 9, "#FAC775");
  }

  /** Resolves when the player clicks one of these balconies (any balcony when ids is empty). */
  private pickBalcony(ids: string[]): Promise<Balcony> {
    return new Promise((resolve) => {
      const zones: Phaser.GameObjects.GameObject[] = [];
      for (const b of this.balconies()) {
        const ok = !ids.length || ids.includes(b.id);
        const y = this.balconyY(b.h);
        const glow = ok ? this.keep(this.add.rectangle(WALL - 24, y - 3, 26, 9, 0xfac775, 0.5).setOrigin(0)) : null;
        if (glow) this.tweens.add({ targets: glow, alpha: 0.1, duration: 500, yoyo: true, repeat: -1 });
        if (!ok) continue;
        const z = this.keep(this.add.zone(WALL - 40, y - 12, 60, 22).setOrigin(0).setInteractive({ useHandCursor: true }));
        zones.push(z, ...(glow ? [glow] : []));
        z.on("pointerdown", () => { for (const o of zones) o.destroy(); resolve(b); });
      }
    });
  }

  private launch(sacks: { vx: number; h: number; color: number }[], strobe: boolean, watch?: Phaser.GameObjects.Text): Promise<number> {
    sfx("swish");
    return new Promise((done) => {
      const list = sacks.map((s) => ({
        obj: this.keep(this.add.circle(WALL - 8, this.balconyY(s.h) - 3, 3, s.color)), x0: WALL - 8, vx: s.vx, h: s.h, landed: false,
      }));
      this.run = { sacks: list, t: 0, strobe, lastDot: 0, watch, done };
    });
  }

  private async dropTest() {
    this.drawTower("THE DROP TEST · click the glowing balcony to drop the sack");
    const watch = this.label(220, 108, "0.00 s", 16, "#FFFFFF").setFontFamily(DISPLAY);
    this.label(16, 108, "balcony      height     time", 8, "#9AA6C8");
    const bs = this.balconies();
    const order = [bs[0], bs[bs.length - 1], ...bs.slice(1, -1)];       // lowest, then the top, then the middle
    let row = 0;
    for (const b of order) {
      let guess = 0;
      if (b === bs[bs.length - 1]) guess = await this.predict(b);
      await this.pickBalcony([b.id]);
      const t = await this.launch([{ vx: 0, h: b.h, color: 0xe8d8b0 }], true, watch);
      this.label(16, 122 + row++ * 12, `${b.name.padEnd(12)} ${b.h.toFixed(1).padStart(4)} m   ${t.toFixed(1)} s`, 9);
      if (guess) {
        const v = this.label(220, 132, `You said ${guess} s. It took ${t.toFixed(1)} s.`, 9, "#FAC775");
        this.tweens.add({ targets: v, scale: { from: 1.3, to: 1 }, duration: 300, ease: "Back.easeOut" });
        void this.dlg.say({ who: "foot", expr: "surprised", text: "*Four times higher. Only twice as long!" });
      }
      await wait(this, 700);
    }
    await this.next();
    this.dlg.hide();
    this.clear();
  }

  /** The prediction dial before the top drop. Stored for the playtest numbers. */
  private predict(b: Balcony): Promise<number> {
    const head = this.label(220, 150, `Predict: from ${b.name}, how long?`, 9, "#FFFFFF");
    return new Promise((resolve) => {
      const btns = [1, 2, 3, 4].map((n, i) => this.button(240 + i * 34, 172, `${n} s`, () => {
        try { localStorage.setItem("smudge.predict", String(n)); } catch { /* private window */ }
        for (const x of btns) x.destroy();
        head.destroy();
        resolve(n);
      }, "#2E5CAD"));
    });
  }

  private next(): Promise<void> {
    return new Promise((resolve) => { const b = this.button(W - 60, 256, "Next ▸", () => { b.destroy(); resolve(); }); });
  }

  // ---- 3. slip or push? ----------------------------------------------------
  private async slipOrPush() {
    this.drawTower("SLIP OR PUSH? · pick any balcony");
    const out = Number((api.current?.landing as { from_wall?: number } | undefined)?.from_wall) || 4.5;
    const ox = WALL - 8 - out * PXM;
    this.keep(this.add.ellipse(ox, GROUND + 4, 18, 6).setStrokeStyle(1, 0xf2e9cf));
    this.label(ox, GROUND + 10, `outline ${out} m`, 7, "#F2E9CF").setOrigin(0.5, 0);
    this.label(16, 108, "pale: slips off, 0.5 m/s\nred: pushed, 3 m/s", 9);
    void this.dlg.say({ who: "smudge", expr: "determined", text: "Pushed or dropped, they land together." });
    const b = await this.pickBalcony([]);
    const t = await this.launch([{ vx: 0.5, h: b.h, color: 0xe8d8b0 }, { vx: 3, h: b.h, color: 0xc9302a }], false);
    const same = this.label(W / 2 - 40, 150, "SAME TIME", 20, "#FAC775").setFontFamily(DISPLAY).setOrigin(0.5);
    this.tweens.add({ targets: same, scale: { from: 0.3, to: 1 }, duration: 300, ease: "Back.easeOut" });
    const pushed = 3 * t;
    this.label(16, 140, `slip lands ${(0.5 * t).toFixed(1)} m out\npush lands ${pushed.toFixed(1)} m out`, 9);
    if (Math.abs(pushed - out) < 0.4) void this.dlg.say({ who: "foot", expr: "worried", text: "*The push lands on the outline." });
    await this.next();
    this.dlg.hide();
    this.clear();
  }

  // ---- 4. the notebook -----------------------------------------------------
  private notebook(): Promise<LabResult> {
    void this.dlg.say({ who: "foot", expr: "neutral", text: "*Now the height. Use the time you measured." });
    return new Promise((resolve) => {
      const form = document.createElement("form");
      form.setAttribute("aria-label", "Notebook");
      form.style.cssText = `font-family:"Pixelify Sans",monospace;background:#F2E9CF;border:2px solid #0E1938;border-radius:4px;
        padding:8px 10px;box-sizing:border-box;display:flex;flex-direction:column;gap:8px;color:#0E1938;
        background-image:repeating-linear-gradient(#F2E9CF 0 15px,#9cb8dc 15px 16px);`;
      const box = (id: string, value = "", readonly = false) =>
        `<input id="${id}" value="${value}" ${readonly ? "readonly tabindex=-1" : ""} inputmode="decimal" autocomplete="off"
          style="width:3.6em;font:inherit;padding:1px 4px;border:1.5px solid #0E1938;background:${readonly ? "#E6DCC0" : "#FFFBEF"};color:#0E1938;border-radius:3px">`;
      form.innerHTML = `<div style="font-weight:700;color:#C9302A">Notebook</div>
        <div style="display:flex;gap:4px;align-items:center;flex-wrap:wrap">h = ½ × ${box("nb-g", String(this.g), true)} × ${box("nb-t", String(this.gap), true)}² = ${box("nb-h")} m</div>
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
          this.hint(r?.hint ?? "*h = ½ × g × t². Try again.");
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
