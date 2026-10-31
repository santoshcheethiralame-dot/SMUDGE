import Phaser from "phaser";
import { W, H, FONT, DISPLAY } from "../consts";
import { Dialogue } from "../systems/dialogue";
import { makeGlow, wait, tween } from "../systems/fx";
import { overlay } from "../systems/ui";
import { sfx, themeFor, layer, ambience } from "../audio";
import { inkIn, inkOut } from "../systems/transition";
import { api } from "../api";
import { progress } from "../state";

const CYL = { x: 206, top: 64, bottom: 236, w: 46 };   // the measuring cylinder (Smudge in beaker form)
const ML_MAX = 100;
const mlToY = (ml: number) => CYL.bottom - (ml / ML_MAX) * (CYL.bottom - CYL.top);
const METALS: [string, number][] = [["gold", 19.3], ["lead", 11.3], ["silver", 10.5], ["copper", 8.96], ["brass", 8.5]];

export class Lab extends Phaser.Scene {
  private dlg!: Dialogue;
  private water!: Phaser.GameObjects.Rectangle;
  private level = 0;
  constructor() { super("Lab"); }

  async create() {
    themeFor("lab");
    layer(2);
    ambience("lab");
    void inkIn(this);
    makeGlow(this, "glow64", 64);
    this.add.image(0, 0, "bench").setOrigin(0, 0);
    const lamp = this.add.image(40, 30, "glow64").setScale(3.5, 2.4).setBlendMode(Phaser.BlendModes.ADD).setTint(0xffb35a).setAlpha(0.25);
    void lamp;
    this.dlg = new Dialogue(this);
    const c = api.current!;

    this.add.text(W - 8, H - 8, "Chapter 9 · Density lab", { fontFamily: FONT, fontSize: "10px", color: "#9AA6C8" }).setOrigin(1, 1);

    // balance with an LCD readout
    const balance = this.add.image(96, 232, "lab_balance").setOrigin(0.5, 1);
    const lcd = this.add.text(90, 217, "0 g", { fontFamily: FONT, fontSize: "10px", color: "#9CF5B5" }).setOrigin(0.5);
    const panY = 232 - 58 + 19;

    // the crown, draggable
    const crown = this.add.image(40, 228, "lab_crown").setOrigin(0.5, 0.85).setInteractive({ draggable: true, useHandCursor: true });
    const hand = this.add.text(40, 182, "drag me", { fontFamily: FONT, fontSize: "10px", color: "#FFC46B" }).setOrigin(0.5);
    this.tweens.add({ targets: hand, y: 178, yoyo: true, repeat: -1, duration: 500 });

    this.drawCylinder(c.water_before_ml);
    this.level = c.water_before_ml;

    await this.dlg.play([
      { who: "foot", expr: "happy", text: "Lab time! Density is mass divided by volume. Two measurements, one division." },
      { who: "foot", expr: "neutral", text: "Step one: weigh the crown. Drag it onto the balance." },
    ]);

    // step 1: weigh it
    await this.dragTo(crown, (x, y) => Math.abs(x - 96) < 50 && y > 150, 96, panY + 8);
    hand.destroy();
    sfx("tick");
    await tween(this, {
      targets: { v: 0 }, v: c.mass_g, duration: 900, ease: "Cubic.easeOut",
      onUpdate: (tw: Phaser.Tweens.Tween) => lcd.setText(`${Math.round((tw.targets[0] as any).v)} g`),
    });
    lcd.setText(`${c.mass_g} g`);
    await this.dlg.play([
      { who: "smudge", expr: "thinking", text: `${c.mass_g} grams. Write that down.` },
      { who: "foot", expr: "neutral", text: "Step two: volume. A crown is a terrible shape to measure with a ruler..." },
      { who: "smudge", expr: "determined", text: "So we measure the water it pushes out of the way. Beaker form!" },
    ]);

    // Smudge becomes the cylinder: a flash, then the eyes appear on the glass
    const flash = this.add.rectangle(CYL.x, (CYL.top + CYL.bottom) / 2, CYL.w + 20, CYL.bottom - CYL.top + 30, 0xffffff, 0.9);
    sfx("pop");
    this.tweens.add({ targets: flash, alpha: 0, duration: 400, onComplete: () => flash.destroy() });
    this.drawFace();
    await this.dlg.play([
      { who: "foot", expr: "neutral", text: `Read the water level BEFORE the crown goes in. Then drop the crown into Smudge.` },
    ]);

    // step 2: dunk it
    await this.dragTo(crown, (x, y) => Math.abs(x - CYL.x) < 40 && y < CYL.bottom, CYL.x, mlToY(this.level) + 6);
    crown.disableInteractive();
    sfx("splash");
    this.tweens.add({ targets: crown, y: CYL.bottom - 10, scale: 0.7, duration: 700, ease: "Quad.easeIn" });
    const after = c.water_before_ml + c.volume_ml;
    await tween(this, {
      targets: this, level: after, duration: 900, ease: "Sine.easeOut",
      onUpdate: () => { this.water.setSize(CYL.w - 6, CYL.bottom - mlToY(this.level)).setY(mlToY(this.level)); },
    });
    await this.dlg.play([{ who: "smudge", expr: "surprised", text: "Ooh, cold. Water's gone up. Read the new level, then do the maths in the notebook." }]);

    // step 3: the notebook
    const result = await this.notebook();
    // step 4: pick the metal
    const metal = await this.pickMetal(result.density, result.metal);
    progress.labDone = true;
    progress.evidence = {
      label: `density:${metal}`,
      badge: `EVIDENCE
crown = ${result.density} g/cm³
= ${metal.toUpperCase()}`,
      say: `Hold it. The crown's density is ${result.density}. That's ${metal}.`,
    };
    await this.evidenceCard(result.density, metal);
    await inkOut(this);
    this.scene.start("District", { kit: "density", from: "lab" });
  }

  private drawCylinder(level: number) {
    const g = this.add.graphics();
    const x0 = CYL.x - CYL.w / 2;
    this.add.image(CYL.x, 148, "lab_cylinder");      // rendered glass, 60 x 192, inner walls on CYL
    this.water = this.add.rectangle(CYL.x, mlToY(level), CYL.w - 6, CYL.bottom - mlToY(level), 0x2c66ae, 0.85).setOrigin(0.5, 0);
    const marks = this.add.graphics();
    marks.lineStyle(1, 0xe6f4ff, 0.9);
    for (let ml = 5; ml < ML_MAX; ml += 5) {
      const y = Math.round(mlToY(ml)) + 0.5;
      marks.lineBetween(x0 + 2, y, x0 + (ml % 10 === 0 ? 14 : 8), y);
      if (ml % 10 === 0) this.add.text(x0 - 4, y, `${ml}`, { fontFamily: FONT, fontSize: "10px", color: "#F2E9CF" }).setOrigin(1, 0.5);
    }
    this.add.text(x0 - 4, CYL.top - 8, "ml", { fontFamily: FONT, fontSize: "10px", color: "#9AA6C8" }).setOrigin(1, 0.5);
    const glass = this.add.graphics();
    glass.lineStyle(2, 0xffffff, 0.35).lineBetween(x0 + CYL.w - 6, CYL.top + 6, x0 + CYL.w - 6, CYL.bottom - 8);
  }

  private drawFace() {
    const g = this.add.graphics();
    const y = CYL.top + 18;
    g.fillStyle(0x16264f, 1).fillEllipse(CYL.x, CYL.top - 2, CYL.w + 8, 14);
    g.fillStyle(0xffffff, 1).fillRect(CYL.x - 11, y, 7, 10).fillRect(CYL.x + 4, y, 7, 10);
    g.fillStyle(0x04061a, 1).fillRect(CYL.x - 8, y + 4, 4, 5).fillRect(CYL.x + 4, y + 4, 4, 5);
    g.fillStyle(0x4a2d17, 1).fillEllipse(CYL.x, CYL.top - 6, CYL.w + 16, 6).fillRect(CYL.x - 12, CYL.top - 18, 24, 12);
    g.fillStyle(0xc9302a, 1).fillRect(CYL.x - 12, CYL.top - 10, 24, 3);
  }

  private dragTo(obj: Phaser.GameObjects.Image, ok: (x: number, y: number) => boolean, snapX: number, snapY: number) {
    return new Promise<void>((res) => {
      const home = { x: obj.x, y: obj.y };
      obj.setInteractive({ draggable: true, useHandCursor: true });
      const onDrag = (_p: any, o: any, x: number, y: number) => { if (o === obj) obj.setPosition(x, y); };
      const onEnd = (_p: any, o: any) => {
        if (o !== obj) return;
        if (ok(obj.x, obj.y)) {
          this.input.off("drag", onDrag);
          this.input.off("dragend", onEnd);
          this.tweens.add({ targets: obj, x: snapX, y: snapY, duration: 160, ease: "Back.easeOut", onComplete: () => res() });
        } else {
          this.tweens.add({ targets: obj, x: home.x, y: home.y, duration: 220, ease: "Sine.easeOut" });
        }
      };
      this.input.on("drag", onDrag);
      this.input.on("dragend", onEnd);
    });
  }

  private notebook(): Promise<{ density: number; metal: string }> {
    return new Promise((resolve) => {
      const wrap = document.createElement("form");
      wrap.style.cssText = `font-family:"Smudge Digits","Pixelify Sans",monospace;background:#F2E9CF;border:2px solid #0E1938;border-radius:4px;
        padding:8px 10px;box-sizing:border-box;display:flex;flex-direction:column;gap:5px;color:#0E1938;
        background-image:repeating-linear-gradient(#F2E9CF 0 15px,#9cb8dc 15px 16px);`;
      const field = (id: string, label: string, unit: string) =>
        `<label for="${id}" style="display:flex;align-items:center;gap:6px;justify-content:space-between">
           <span>${label}</span><span style="display:flex;align-items:center;gap:4px">
           <input id="${id}" inputmode="decimal" autocomplete="off" style="width:4.5em;font:inherit;padding:1px 4px;border:1.5px solid #0E1938;background:#FFFBEF;color:#0E1938;border-radius:3px">
           <span style="width:3.2em">${unit}</span></span></label>`;
      wrap.innerHTML = `<div style="font-weight:700;color:#C9302A">Working</div>
        ${field("nb-mass", "mass", "g")}${field("nb-before", "water before", "ml")}${field("nb-after", "water after", "ml")}
        ${field("nb-vol", "volume", "cm³")}${field("nb-dens", "density = m ÷ V", "g/cm³")}
        <button type="submit" style="font:inherit;margin-top:4px;padding:4px;border:2px solid #0E1938;background:#C9302A;color:#fff;border-radius:4px;cursor:pointer">Check working</button>`;
      ["pointerdown", "keydown", "keyup"].forEach((ev) => wrap.addEventListener(ev, (e) => e.stopPropagation()));
      const remove = overlay(this, wrap, 290, 52, 182, 150);
      this.input.keyboard!.enabled = false;
      const val = (id: string) => parseFloat((document.getElementById(id) as HTMLInputElement).value.replace(",", "."));
      wrap.onsubmit = async (e) => {
        e.preventDefault();
        const m = val("nb-mass"), b = val("nb-before"), a = val("nb-after"), v = val("nb-vol"), d = val("nb-dens");
        if ([m, b, a, v, d].some((x) => Number.isNaN(x))) {
          this.say("foot", "neutral", "*Fill in every line first. Numbers only.");
          return;
        }
        if (Math.abs(v - (a - b)) > 0.6) {
          this.say("foot", "worried", await api.hint("volume", `before=${b}, after=${a}, volume=${v}`));
          return;
        }
        const r = await api.labCheck({ mass: m, before: b, after: a, density: d });
        if (r && r.density_ok && r.metal) {
          remove();
          this.input.keyboard!.enabled = true;
          sfx("chime");
          resolve({ density: Math.round(d * 100) / 100, metal: r.metal });
        } else {
          sfx("wrong");
          this.say("foot", "worried", r?.hint ?? "*Check each number again.");
        }
      };
    });
  }

  private say(who: "foot", expr: string, text: string) {
    this.dlg.say({ who, expr, text }).then(() => this.dlg.hide());
  }

  private pickMetal(density: number, truth: string): Promise<string> {
    return new Promise((resolve) => {
      this.dlg.say({ who: "foot", expr: "happy", text: `${density} g/cm³! Now: which material has that density? Tap it in the table.` });
      const panel = this.add.container(380, 120).setDepth(800);
      const bg = this.add.rectangle(0, 0, 170, 116, 0xf2e9cf).setStrokeStyle(2, 0x0e1938);
      panel.add(bg);
      panel.add(this.add.text(0, -48, "Density table (g/cm³)", { fontFamily: FONT, fontSize: "9px", color: "#C9302A" }).setOrigin(0.5));
      METALS.forEach(([name, rho], i) => {
        const row = this.add.text(0, -28 + i * 18, `${name.padEnd(7, " ")} ${rho}`, { fontFamily: FONT, fontSize: "11px", color: "#0E1938", backgroundColor: "#FFFBEF" })
          .setOrigin(0.5).setPadding(10, 2, 10, 2).setInteractive({ useHandCursor: true });
        row.on("pointerdown", (_p: any, _x: any, _y: any, e: any) => {
          e?.stopPropagation?.();
          if (name === truth) {
            sfx("chime");
            panel.destroy();
            this.dlg.hide();
            resolve(name);
          } else {
            sfx("wrong");
            row.setColor("#C9302A");
            this.dlg.say({ who: "foot", expr: "worried", text: `*${name} is ${rho}. Which number is CLOSEST to ${density}?` });
          }
        });
        panel.add(row);
      });
    });
  }

  private async evidenceCard(density: number, metal: string) {
    const card = this.add.container(W / 2, H / 2).setDepth(1500).setScale(0.2).setAlpha(0);
    const bg = this.add.rectangle(0, 0, 250, 110, 0xf2e9cf).setStrokeStyle(2, 0x0e1938);
    const t1 = this.add.text(0, -40, "EVIDENCE", { fontFamily: FONT, fontSize: "9px", color: "#C9302A" }).setOrigin(0.5);
    const t2 = this.add.text(0, -16, `Crown density: ${density} g/cm³`, { fontFamily: DISPLAY, fontSize: "16px", color: "#0E1938" }).setOrigin(0.5);
    const t3 = this.add.text(0, 8, `That's ${metal.toUpperCase()}. Gold would be 19.3.`, { fontFamily: FONT, fontSize: "10px", color: "#55361A" }).setOrigin(0.5);
    const t4 = this.add.text(0, 30, "The crown is a forgery.", { fontFamily: FONT, fontSize: "10px", color: "#8E1A14" }).setOrigin(0.5);
    card.add([bg, t1, t2, t3, t4]);
    sfx("fanfare");
    await tween(this, { targets: card, scale: 1, alpha: 1, angle: -2, duration: 420, ease: "Back.easeOut" });
    await this.dlg.play([
      { who: "smudge", expr: "smug", text: `A gold crown that's really ${metal}. Somebody in this harbour keeps ${metal}...` },
      { who: "foot", expr: "happy", text: "Evidence filed! Now we need to know who's lying about it." },
    ]);
    card.destroy();
  }
}
