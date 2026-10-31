// Read a scale: a thermometer's mercury, or a dial meter's needle. The reading settles, the player types what
// they read; within half a small division records the true value.
import Phaser from "phaser";
import { FONT } from "../../../consts";
import { sfx } from "../../../audio";
import { tween } from "../../fx";
import { AREA, panel, readingBox } from "../parts";
import type { LabCtx, GaugeStep } from "../types";

export const kind = "gauge";

export async function run(ctx: LabCtx, step: GaugeStep) {
  const { scene, dlg } = ctx;
  await dlg.play(step.intro);
  dlg.hide();
  for (const it of step.items(ctx.c)) {
    const objs: Phaser.GameObjects.GameObject[] = panel(scene, it.label, 0x22305c);
    const g = scene.add.graphics();
    const lab = (x: number, y: number, s: string, ox = 0.5) =>
      objs.push(scene.add.text(x, y, s, { fontFamily: FONT, fontSize: "9px", color: "#0E1938" }).setOrigin(ox, 0.5).setDepth(2));
    // the rendered body goes under the ticks; the geometry below matches art/world/scene_instruments.py
    objs.push(scene.add.image(it.style === "thermo" ? 122 : 50, it.style === "thermo" ? 92 : 112, it.style === "thermo" ? "lab_thermo" : "lab_dial").setOrigin(0));
    g.setDepth(1);
    objs.push(g);
    const ticks = Math.round((it.max - it.min) / it.step);
    const big = it.labelEvery ?? 5;
    if (it.style === "thermo") {
      const x = AREA.x + 120, y0 = AREA.y + AREA.h - 22, y1 = AREA.y + 26;
      const yOf = (v: number) => y0 - ((v - it.min) / (it.max - it.min)) * (y0 - y1);
      for (let k = 0; k <= ticks; k++) {
        const y = yOf(it.min + k * it.step);
        g.lineStyle(1, 0x0e1938, 1).lineBetween(x + 7, y, x + (k % big === 0 ? 16 : 11), y);
        if (k % big === 0) lab(x + 20, y, `${+(it.min + k * it.step).toFixed(4)}`, 0);
      }
      lab(x + 20, y1 - 12, it.unit, 0);
      const full = y0 + 2 - y1;
      const merc = scene.add.rectangle(x, y0 + 2, 4, full, 0xc9302a).setOrigin(0.5, 1).setScale(1, 0).setDepth(2);
      objs.push(merc);
      await tween(scene, { targets: merc, scaleY: (y0 + 2 - yOf(it.value)) / full, duration: 1400, ease: "Sine.easeOut" });
    } else {
      const cx = AREA.x + 130, cy = AREA.y + AREA.h - 30, r = 72;
      const angOf = (v: number) => Math.PI + ((v - it.min) / (it.max - it.min)) * Math.PI;
      for (let k = 0; k <= ticks; k++) {
        const a = angOf(it.min + k * it.step), l = k % big === 0 ? 10 : 5;
        g.lineStyle(1, 0x0e1938, 1).lineBetween(cx + Math.cos(a) * r, cy + Math.sin(a) * r, cx + Math.cos(a) * (r - l), cy + Math.sin(a) * (r - l));
        if (k % big === 0) objs.push(scene.add.text(cx + Math.cos(a) * (r - 18), cy + Math.sin(a) * (r - 18), `${+(it.min + k * it.step).toFixed(4)}`,
          { fontFamily: FONT, fontSize: "9px", color: "#0E1938" }).setOrigin(0.5).setDepth(2));
      }
      objs.push(scene.add.text(cx, cy - 22, it.unit, { fontFamily: FONT, fontSize: "10px", color: "#C9302A" }).setOrigin(0.5).setDepth(2));
      const needle = scene.add.graphics().setDepth(3);
      objs.push(needle, scene.add.image(cx, cy, "lab_hub").setDepth(4));
      const state = { v: it.min };
      await tween(scene, {
        targets: state, v: it.value, duration: 1400, ease: "Back.easeOut",
        onUpdate: () => { const a = angOf(state.v); needle.clear().lineStyle(2, 0xc9302a, 1).lineBetween(cx, cy, cx + Math.cos(a) * (r - 6), cy + Math.sin(a) * (r - 6)); },
      });
    }
    await dlg.say({ who: "foot", expr: "neutral", text: `*Read it carefully. Each small mark is ${it.step} ${it.unit}.` });
    dlg.hide();
    for (let attempt = 1; ; attempt++) {
      const box = readingBox(scene, 300, 150, it.unit);
      const v = await box.value;
      box.remove();
      if (Math.abs(v - it.value) <= it.step / 2 + 1e-9 || attempt >= 3) {
        sfx("chime");
        ctx.measured[`${step.record}_${it.key}`] = it.value;
        await dlg.say(attempt >= 3 && Math.abs(v - it.value) > it.step / 2
          ? { who: "foot", expr: "neutral", text: `*Close. It reads ${it.value} ${it.unit}: count the marks from the last number.` }
          : { who: "smudge", expr: "happy", text: `${it.label}: ${it.value} ${it.unit}. Noted.` });
        dlg.hide();
        break;
      }
      sfx("wrong");
      await dlg.say({ who: "foot", expr: "worried", text: `*Not quite. Find the last numbered mark, then count the small ones: each is ${it.step} ${it.unit}.` });
      dlg.hide();
    }
    for (const o of objs) o.destroy();
  }
  await dlg.play(step.done);
  dlg.hide();
}
