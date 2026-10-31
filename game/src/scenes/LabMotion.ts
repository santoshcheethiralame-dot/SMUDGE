// Case 2's lab, in three steps:
//  1. the braking test: a toy cart crosses the speed gate at 10.0 m/s on Braking Bend's own asphalt and skids
//     to a stop; Smudge, as a stopwatch, times it. a = (v - u) / t.
//  2. the skid plate: the evidence photo of the three skids, drawn to scale from the case; Smudge, as a tape,
//     measures each one from the brake line. s.
//  3. the notebook: a, then u = sqrt(2as) for each skid, checked by the server step by step.
// Backdrops come from art/world/scene_skidlab.py; its camera centre and plate geometry are mirrored here.
import Phaser from "phaser";
import { W, H, FONT, DISPLAY, project } from "../consts";
import { Dialogue } from "../systems/dialogue";
import { makePixel, wait, tween } from "../systems/fx";
import { overlay } from "../systems/ui";
import { sfx, themeFor, layer, ambience } from "../audio";
import { inkIn, inkOut } from "../systems/transition";
import { api } from "../api";
import { progress } from "../state";
import { calc } from "../systems/lab/calc";

const CV = 100;                                  // scene_skidlab CENTRE
const L = (x: number, y: number, z: number, dy = 0) => {
  const p = project(x, y, z, 0, CV);
  return { x: p.x, y: p.y + dy };
};
// the braking test
const ROAD_Y = 35.4, ROAD_Z = -6, GATE_X = -120, TRACK_PX_PER_M = 24;
// the skid plate (scene_skidlab: PLATE_START, PX_PER_M, ROWS, photo face z = -55), drawn 40 px lower than rendered
const PLATE_DY = 40, PLATE_START = -183, PLATE_PX_PER_M = 15, PLATE_Z = -55;
const ROWS: Record<string, number> = { dash: 180, rolla: 138, mu: 94 };
const TAG: Record<string, string> = { dash: "D", rolla: "R", mu: "M" };
const TREAD: Record<string, string> = { dash: "skate-line", rolla: "chevron", mu: "scuff" };

export class LabMotion extends Phaser.Scene {
  private dlg!: Dialogue;
  private measured: Record<string, number> = {};
  private stopTime = 0;
  constructor() { super("LabMotion"); }

  async create() {
    this.measured = {};
    this.stopTime = 0;
    makePixel(this);
    themeFor("lab");
    layer(2);
    ambience("lab");
    void inkIn(this);
    this.dlg = new Dialogue(this);
    await this.brakingTest();
    await this.skidPlate();
    const r = await this.notebook();
    await this.evidenceCard(r.speeds!, r.evidence!);
    progress.labDone = true;
    await inkOut(this);
    this.scene.start("District", { kit: "motion", from: "lab" });
  }

  // ---- 1. the braking test ----------------------------------------------------
  private async brakingTest() {
    const c = api.current!;
    const t = c.stop_time, u = c.gate_speed, a = u / t;
    const bg = this.add.image(0, 0, "lab_track").setOrigin(0, 0);
    this.add.text(W - 8, H - 8, "Chapter 8 · Motion lab", { fontFamily: FONT, fontSize: "10px", color: "#9AA6C8" }).setOrigin(1, 1);
    const watch = this.add.sprite(352, 112, "smudge", "form_stopwatch/S/0").setScale(2).play("form_stopwatch_S");
    const lcd = this.add.text(352, 160, "0.00 s", { fontFamily: FONT, fontSize: "16px", color: "#9CF5B5", backgroundColor: "#0E1938" })
      .setPadding(6, 2, 6, 2).setOrigin(0.5);
    const skid = this.add.graphics();
    const cartAt = (x: number) => { const p = L(x, 44, ROAD_Z); return { x: p.x, y: p.y - 3.6 }; };
    const cart = this.add.image(cartAt(-235).x, cartAt(-235).y, "cart");

    await this.dlg.play([
      { who: "foot", expr: "happy", text: "Lab time! First: how hard does Braking Bend's road brake? This cart is on the same asphalt." },
      { who: "foot", expr: "neutral", text: "It crosses the gate at exactly 10.0 m/s, then brakes to a stop. Time it, from the gate to the stop." },
      { who: "smudge", expr: "determined", text: "Stopwatch form. Tap once at the gate, tap again when it stops." },
    ]);

    for (let attempt = 1; ; attempt++) {
      skid.clear();
      lcd.setText("0.00 s");
      const go = this.add.text(352, 196, "▶  Run the cart", { fontFamily: FONT, fontSize: "11px", color: "#FFFFFF", backgroundColor: "#C9302A" })
        .setPadding(8, 3, 8, 3).setOrigin(0.5).setInteractive({ useHandCursor: true });
      await new Promise<void>((res) => go.once("pointerdown", () => res()));
      go.destroy();
      const tap = this.add.text(352, 196, "TAP anywhere: start / stop", { fontFamily: FONT, fontSize: "10px", color: "#0E1938", backgroundColor: "#F2E9CF" })
        .setPadding(6, 2, 6, 2).setOrigin(0.5);

      let started = -1, stopped = -1, clock = 0;
      const onTap = () => {
        const now = clock;
        if (started < 0) { started = now; sfx("tick"); } else if (stopped < 0) { stopped = now; sfx("tick"); }
      };
      this.input.on("pointerdown", onTap);
      this.input.keyboard?.on("keydown-SPACE", onTap);

      // run: constant 10 m/s to the gate, then a = -u/t to rest. Clock is game time in seconds.
      const lead = (GATE_X + 235) / TRACK_PX_PER_M / u;
      const total = lead + t + 0.9;
      await new Promise<void>((res) => {
        const startMs = this.time.now;
        const ev = this.time.addEvent({
          delay: 16, loop: true, callback: () => {
            const s = (this.time.now - startMs) / 1000;
            clock = s;
            let x: number;
            if (s < lead) x = -235 + u * s * TRACK_PX_PER_M;
            else { const tt = Math.min(s - lead, t); x = GATE_X + (u * tt - 0.5 * a * tt * tt) * TRACK_PX_PER_M; }
            const p = cartAt(x);
            cart.setPosition(p.x, p.y);
            if (s >= lead) {
              const g0 = L(GATE_X, ROAD_Y, ROAD_Z), g1 = L(x - 9, ROAD_Y, ROAD_Z);
              skid.clear().lineStyle(2, 0x0b0910, 0.85).lineBetween(g0.x, g0.y - 1, g1.x, g1.y - 1).lineBetween(g0.x + 6, g0.y + 4, g1.x + 6, g1.y + 4);
            }
            if (started >= 0) lcd.setText(`${((stopped >= 0 ? stopped : s) - started).toFixed(2)} s`);
            if (s > total && (stopped >= 0 || s > total + 1.5)) { ev.remove(); res(); }
          },
        });
      });
      this.input.off("pointerdown", onTap);
      this.input.keyboard?.off("keydown-SPACE", onTap);
      tap.destroy();
      const timed = started >= 0 && stopped >= 0 ? stopped - started : NaN;
      if (Math.abs(timed - t) <= 0.25 || attempt >= 3) {
        this.stopTime = t;
        lcd.setText(`${t.toFixed(2)} s`);
        sfx("chime");
        await this.dlg.play([
          attempt >= 3 && !(Math.abs(timed - t) <= 0.25)
            ? { who: "foot", expr: "neutral", text: `*Tricky! Smudge's stopwatch caught it anyway: ${t.toFixed(2)} s from the gate to the stop.` }
            : { who: "smudge", expr: "happy", text: `${t.toFixed(2)} seconds, gate to stop. Write that down.` },
          { who: "foot", expr: "neutral", text: "From 10.0 m/s to nothing in that time. Keep it for the notebook. Now, the skids." },
        ]);
        break;
      }
      sfx("wrong");
      await this.dlg.play([{ who: "foot", expr: "worried", text: Number.isNaN(timed)
        ? "*Tap once as the cart crosses the gate, and again the moment it stops. Let's run it again."
        : `*You got ${timed.toFixed(2)} s. Start right at the gate, stop the instant it stops. Again!` }]);
    }
    watch.destroy(); lcd.destroy(); cart.destroy(); skid.destroy(); bg.destroy();
  }

  // ---- 2. the skid plate ------------------------------------------------------
  private async skidPlate() {
    const c = api.current!;
    this.add.rectangle(0, 0, W, PLATE_DY + 2, 0xdcd2b4).setOrigin(0, 0);
    const lines = this.add.graphics();
    lines.lineStyle(1, 0x506b92, 0.8);
    for (let y = 6; y < PLATE_DY; y += 12) lines.lineBetween(0, y + 0.5, W, y + 0.5);
    this.add.image(0, PLATE_DY, "lab_plate").setOrigin(0, 0);
    const P = (m: number, y: number) => L(PLATE_START + m * PLATE_PX_PER_M, y, PLATE_Z, PLATE_DY);
    this.drawSkids(c.skids, P);

    await this.dlg.play([
      { who: "foot", expr: "neutral", text: "The photo from Braking Bend. D, R and M: I matched each skid to its rider by the tread." },
      { who: "smudge", expr: "determined", text: "Tape form. Drag my hat from the white line to where the rubber ends." },
    ]);
    this.dlg.hide();

    const order = ["dash", "rolla", "mu"].filter((k) => k in c.skids);
    const tape = this.add.graphics().setDepth(500);
    const head = this.add.sprite(0, 0, "smudge", "form_ruler/S/0").setOrigin(0.5, 0.9).setDepth(501).setInteractive({ useHandCursor: true, draggable: true });
    const read = this.add.text(0, 0, "", { fontFamily: FONT, fontSize: "11px", color: "#0E1938", backgroundColor: "#F2E9CF" })
      .setPadding(4, 1, 4, 1).setOrigin(0.5, 1).setDepth(502);
    const done: Record<string, Phaser.GameObjects.Text> = {};
    const help = this.add.text(W / 2, H - 6, "Drag the hat along the skid · arrow keys nudge 0.1 m · Enter to record", { fontFamily: FONT, fontSize: "10px", color: "#F2E9CF", backgroundColor: "#0E1938" })
      .setPadding(5, 2, 5, 2).setOrigin(0.5, 1).setDepth(503);

    for (const sid of order) {
      const rowY = sid === "dash" ? ROWS.dash - 3.5 : ROWS[sid];
      let m = 0;
      const draw = () => {
        const a = P(0, rowY), b = P(m, rowY);
        tape.clear().fillStyle(0xe5b848, 1).fillRect(a.x, a.y - 3, Math.max(1, b.x - a.x), 6).lineStyle(1, 0x3e2a06, 1).strokeRect(a.x, a.y - 3, Math.max(1, b.x - a.x), 6);
        for (let k = 0; k <= m * 10 + 0.001; k++) {
          const x = P(k / 10, rowY).x;
          tape.lineStyle(1, 0x3e2a06, 1).lineBetween(x, a.y - 3, x, a.y - 3 + (k % 10 === 0 ? 4 : k % 5 === 0 ? 2.5 : 1.2));
        }
        tape.fillStyle(0x0e1938, 1).fillRect(a.x - 5, a.y - 6, 5, 12);
        head.setPosition(b.x, b.y - 2);
        read.setPosition(b.x, b.y - 26).setText(`${TAG[sid]}  ${m.toFixed(1)} m`);
      };
      draw();
      const s = c.skids[sid];
      await new Promise<void>((res) => {
        const set = (mm: number) => {
          m = Phaser.Math.Clamp(Math.round(mm * 10) / 10, 0, 25);
          if (Math.abs(m - s) <= 0.1) m = s;                       // snap to the rubber's end
          draw();
        };
        const record = () => {
          if (Math.abs(m - s) <= 0.15) {
            cleanup();
            sfx("chime");
            this.measured[sid] = s;
            const at = P(s, rowY);
            done[sid] = this.add.text(at.x + 8, at.y, `${s.toFixed(1)} m ✓`, { fontFamily: FONT, fontSize: "9px", color: "#9CF5B5", backgroundColor: "#0E1938" })
              .setPadding(3, 1, 3, 1).setOrigin(0, 0.5).setDepth(400);
            res();
          } else if (m > 0.2) {
            sfx("wrong");
            this.dlg.say({ who: "foot", expr: "worried", text: m < s ? "*The rubber keeps going. Stretch further!" : "*Too far: stop the hat where the skid ends." })
              .then(() => this.dlg.hide());
          }
        };
        const onDrag = (_p: Phaser.Input.Pointer, obj: Phaser.GameObjects.GameObject, x: number) => {
          if (obj === head) set((x - P(0, rowY).x) / (P(1, rowY).x - P(0, rowY).x));
        };
        const onEnd = (_p: Phaser.Input.Pointer, obj: Phaser.GameObjects.GameObject) => { if (obj === head) record(); };
        const onKey = (e: KeyboardEvent) => {
          if (e.key === "ArrowRight") set(m + 0.1);
          else if (e.key === "ArrowLeft") set(m - 0.1);
          else if (e.key === "Enter") record();
        };
        this.input.on("drag", onDrag);
        this.input.on("dragend", onEnd);
        this.input.keyboard?.on("keydown", onKey);
        const cleanup = () => {
          this.input.off("drag", onDrag);
          this.input.off("dragend", onEnd);
          this.input.keyboard?.off("keydown", onKey);
        };
      });
    }
    tape.destroy(); head.destroy(); read.destroy(); help.destroy();
    await this.dlg.play([{ who: "smudge", expr: "thinking", text: "Three skids measured. Notebook time." }]);
    this.dlg.hide();
  }

  private drawSkids(skids: Record<string, number>, P: (m: number, y: number) => { x: number; y: number }) {
    const g = this.add.graphics().setDepth(100);
    const ink = 0x0b0910;
    if ("dash" in skids) {                       // two thin skate lines
      for (const dy of [0, -7]) {
        const a = P(0, ROWS.dash + dy), b = P(skids.dash, ROWS.dash + dy);
        g.lineStyle(1.5, ink, 1).lineBetween(a.x, a.y, b.x, b.y);
      }
    }
    if ("rolla" in skids) {                      // one wide chevron tread
      const n = Math.floor(skids.rolla * PLATE_PX_PER_M / 5);
      for (let k = 0; k < n; k++) {
        const m = (k * 5) / PLATE_PX_PER_M;
        const top = P(m, ROWS.rolla + 5), mid = P(m + 2.5 / PLATE_PX_PER_M, ROWS.rolla), bot = P(m, ROWS.rolla - 5);
        g.lineStyle(2, ink, 1).lineBetween(top.x, top.y, mid.x, mid.y).lineBetween(mid.x, mid.y, bot.x, bot.y);
      }
    }
    if ("mu" in skids) {                         // a broad flat scuff that fades as he slows
      const len = skids.mu * PLATE_PX_PER_M;
      for (let k = 0; k < len; k += 1) {
        const f = k / len;
        const half = 9 - 3 * f;
        for (let j = -half; j <= half; j += 2) {
          if (Math.sin(k * 0.7 + j * 2.6) * 0.5 + 0.5 < 0.2 + 0.5 * f) continue;
          const p = P(k / PLATE_PX_PER_M, ROWS.mu + j);
          g.fillStyle(ink, 1).fillRect(Math.round(p.x), Math.round(p.y), 1, 1);
        }
      }
    }
  }

  // ---- 3. the notebook --------------------------------------------------------
  private notebook(): Promise<NonNullable<Awaited<ReturnType<typeof api.labCheck>>>> {
    const c = api.current!;
    const order = ["dash", "rolla", "mu"].filter((k) => k in c.skids);
    return new Promise((resolve) => {
      this.dlg.say({ who: "foot", expr: "neutral", text: "*a = (v - u) / t first. Then every rider stops, so v = 0 in v² = u² + 2as. Find each u." });
      const wrap = document.createElement("form");
      wrap.setAttribute("aria-label", "Notebook");
      wrap.style.cssText = `font-family:"Smudge Digits","Pixelify Sans",monospace;background:#F2E9CF;border:2px solid #0E1938;border-radius:4px;
        padding:8px 10px;box-sizing:border-box;display:flex;flex-direction:column;gap:5px;color:#0E1938;overflow:auto;
        background-image:repeating-linear-gradient(#F2E9CF 0 15px,#9cb8dc 15px 16px);`;
      const box = (id: string, value = "", readonly = false) =>
        `<input id="${id}" value="${value}" ${readonly ? "readonly tabindex=-1" : ""} inputmode="decimal" autocomplete="off"
          style="width:5.2em;font:inherit;padding:1px 4px;border:1.5px solid #0E1938;background:${readonly ? "#E6DCC0" : "#FFFBEF"};color:#0E1938;border-radius:3px">`;
      wrap.innerHTML = `<div style="font-weight:700;color:#C9302A;display:flex;justify-content:space-between"><span>Working</span><span style="font-weight:400;color:#46506E">type 2*5*4.9 or √49</span></div>
        <label style="display:flex;justify-content:space-between;align-items:center">stop time t (s) ${box("nb-t", this.stopTime.toFixed(2), true)}</label>
        <label style="display:flex;justify-content:space-between;align-items:center">a = (v − u) / t (m/s²) ${box("nb-a")}</label>
        <div style="display:grid;grid-template-columns:1.4em 1fr 1fr;gap:4px;align-items:center;font-size:.9em;color:#46506E"><span></span><span>skid s (m)</span><span>u (m/s)</span></div>
        ${order.map((sid) => `<div style="display:grid;grid-template-columns:1.4em 1fr 1fr;gap:4px;align-items:center"><b>${TAG[sid]}</b>${box(`nb-s-${sid}`, (this.measured[sid] ?? c.skids[sid]).toFixed(1), true)}${box(`nb-u-${sid}`)}</div>`).join("")}
        <button type="submit" style="font:inherit;margin-top:3px;padding:4px;border:2px solid #0E1938;background:#C9302A;color:#fff;border-radius:4px;cursor:pointer">Check working</button>`;
      ["pointerdown", "keydown", "keyup"].forEach((ev) => wrap.addEventListener(ev, (e) => e.stopPropagation()));
      const remove = overlay(this, wrap, 276, 84, 196, 180);
      this.input.keyboard!.enabled = false;
      const val = (id: string) => calc((document.getElementById(id) as HTMLInputElement).value);
      const mark = (id: string, bad: boolean) => { (document.getElementById(id) as HTMLInputElement).style.borderColor = bad ? "#C9302A" : "#0E1938"; };
      wrap.onsubmit = async (e) => {
        e.preventDefault();
        const working: Record<string, number> = { time: this.stopTime, accel: val("nb-a") };
        for (const sid of order) { working[`s_${sid}`] = this.measured[sid] ?? c.skids[sid]; working[`u_${sid}`] = val(`nb-u-${sid}`); }
        if (Object.values(working).some((x) => Number.isNaN(x))) {
          this.dlg.say({ who: "foot", expr: "neutral", text: "*Fill in a and every u first. Numbers, or a sum like 2*5*4.9." });
          return;
        }
        const r = await api.labCheck(working);
        if (!r) return;
        mark("nb-a", r.accel_ok === false);
        for (const sid of order) mark(`nb-u-${sid}`, !!r.rows && !r.rows[sid]?.u_ok && r.step !== "accel");
        if (r.ok && r.evidence) {
          remove();
          this.input.keyboard!.enabled = true;
          this.dlg.hide();
          sfx("chime");
          resolve(r);
        } else {
          sfx("wrong");
          this.dlg.say({ who: "foot", expr: "worried", text: r.hint ?? "*Check each number again, one at a time." });
        }
      };
    });
  }

  private async evidenceCard(speeds: Record<string, number>, evidence: string) {
    const c = api.current!;
    const sid = evidence.split(":")[1];
    const u = speeds[sid];
    const kmh = Math.round(u * 3.6);
    progress.evidence = {
      label: evidence,
      badge: `EVIDENCE\nskid ${TAG[sid]} (${TREAD[sid]}) = ${u} m/s\nlimit ${c.limit} m/s`,
      say: `Hold it. The ${TREAD[sid]} skid says ${u} m/s. The limit is ${c.limit}.`,
    };
    const card = this.add.container(W / 2, H / 2).setDepth(1500).setScale(0.2).setAlpha(0);
    const bg = this.add.rectangle(0, 0, 270, 112, 0xf2e9cf).setStrokeStyle(2, 0x0e1938);
    const t1 = this.add.text(0, -40, "EVIDENCE", { fontFamily: FONT, fontSize: "9px", color: "#C9302A" }).setOrigin(0.5);
    const t2 = this.add.text(0, -16, `Skid ${TAG[sid]}: ${u} m/s`, { fontFamily: DISPLAY, fontSize: "18px", color: "#0E1938" }).setOrigin(0.5);
    const t3 = this.add.text(0, 8, `About ${kmh} km/h, on a ${c.limit} m/s bend.`, { fontFamily: FONT, fontSize: "10px", color: "#55361A" }).setOrigin(0.5);
    const t4 = this.add.text(0, 30, Object.entries(speeds).map(([k, v]) => `${TAG[k]} ${v}`).join("   ·   ") + "  (m/s)", { fontFamily: FONT, fontSize: "9px", color: "#46506E" }).setOrigin(0.5);
    card.add([bg, t1, t2, t3, t4]);
    sfx("fanfare");
    await tween(this, { targets: card, scale: 1, alpha: 1, angle: -2, duration: 420, ease: "Back.easeOut" });
    await this.dlg.play([
      { who: "smudge", expr: "smug", text: `Skid ${TAG[sid]} came into the bend at ${u} m/s. Somebody swore they were under ${c.limit}...` },
      { who: "foot", expr: "happy", text: "Evidence filed! Now: whose oath does that break?" },
    ]);
    card.destroy();
  }
}
