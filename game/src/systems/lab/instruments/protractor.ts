// Smudge's protractor form: line the arm up with a ray and read the angle. Angles are measured either from the
// ground (a sun ray over a shadow) or from the normal (a light ray at a surface, above or below it).
// Drag the arm or use the arrow keys; snaps within 1°, records within 1.5° on release or Enter.
import Phaser from "phaser";
import { FONT } from "../../../consts";
import { sfx } from "../../../audio";
import { AREA, panel } from "../parts";
import type { LabCtx, ProtractorStep } from "../types";

export const kind = "protractor";

const rad = (d: number) => (d * Math.PI) / 180;

export async function run(ctx: LabCtx, step: ProtractorStep) {
  const { scene, dlg } = ctx;
  const items = step.items(ctx.c);
  await dlg.play(step.intro);
  dlg.hide();
  for (const it of items) {
    const objs: Phaser.GameObjects.GameObject[] = panel(scene, it.label, it.from === "ground" ? 0x6f8fc6 : 0x1c2852);
    const V = it.from === "ground" ? { x: AREA.x + AREA.w * 0.66, y: AREA.y + AREA.h - 22 } : { x: AREA.x + AREA.w * 0.5, y: AREA.y + 20 + (AREA.h - 26) / 2 };
    // direction of an angle a, for this item's convention
    const dir = (a: number) => it.from === "ground" ? { x: -Math.cos(rad(a)), y: -Math.sin(rad(a)) }
      : it.side === "down" ? { x: Math.sin(rad(a)), y: Math.cos(rad(a)) } : { x: -Math.sin(rad(a)), y: -Math.cos(rad(a)) };
    const angleAt = (px: number, py: number) => {
      const dx = px - V.x, dy = py - V.y;
      const a = it.from === "ground" ? Math.atan2(-dy, -dx) : it.side === "down" ? Math.atan2(dx, dy) : Math.atan2(-dx, -dy);
      return Phaser.Math.Clamp((a * 180) / Math.PI, 0, it.from === "ground" ? 90 : 89);
    };
    const R = 46, ARM = R + 18;
    const g = scene.add.graphics();
    objs.push(g);
    if (it.from === "ground") {
      // ground, a pole, its shadow, and the sun's ray grazing the pole's top to the shadow's tip
      // the pole is as tall as the photo allows, so a steep sun still fits: shadow = height / tan(angle)
      const t = Math.tan(rad(it.angle));
      const len = Math.min(150, (V.y - AREA.y - 40) / t);
      const top = { x: V.x - len, y: V.y - len * t };
      g.fillStyle(0x3a5a2a, 1).fillRect(AREA.x + 6, V.y, AREA.w - 12, AREA.y + AREA.h - 6 - V.y);
      g.fillStyle(0x05060f, 0.5).fillTriangle(top.x, V.y - 1, top.x, V.y + 3, V.x, V.y + 1);
      g.lineStyle(3, 0x6b4a2a, 1).lineBetween(top.x, V.y, top.x, top.y);
      // the ray runs on past the pole's top to the sun, which sits on it near the top of the photo
      const k = Math.min((top.y - AREA.y - 26) / Math.sin(rad(it.angle)), 80);
      const sun = { x: top.x - k * Math.cos(rad(it.angle)), y: top.y - k * Math.sin(rad(it.angle)) };
      g.lineStyle(1, 0xfff1b0, 0.9).lineBetween(sun.x, sun.y, V.x, V.y);
      g.fillStyle(0xffe08a, 1).fillCircle(sun.x, sun.y, 6);
    } else {
      // a surface, the dashed normal, a block of glass or water below, and the ray
      g.fillStyle(0x7db2ea, 0.25).fillRect(AREA.x + 6, V.y, AREA.w - 12, AREA.y + AREA.h - 6 - V.y);
      if (it.below) objs.push(scene.add.text(AREA.x + AREA.w - 12, AREA.y + AREA.h - 10, it.below, { fontFamily: FONT, fontSize: "10px", color: "#D2ECFF" }).setOrigin(1, 1));
      g.lineStyle(1, 0xd2ecff, 1).lineBetween(AREA.x + 6, V.y, AREA.x + AREA.w - 6, V.y);
      for (let y = AREA.y + 20; y < AREA.y + AREA.h - 8; y += 6) g.lineStyle(1, 0xf4f0e6, 0.7).lineBetween(V.x, y, V.x, y + 3);
      if (it.other !== undefined) {
        const o = it.side === "down" ? { x: -Math.sin(rad(it.other)), y: -Math.cos(rad(it.other)) } : { x: Math.sin(rad(it.other)), y: Math.cos(rad(it.other)) };
        g.lineStyle(2, 0xffe08a, 0.45).lineBetween(V.x, V.y, V.x + o.x * 70, V.y + o.y * 70);
      }
      const d = dir(it.angle);
      g.lineStyle(2, 0xffe08a, 1).lineBetween(V.x, V.y, V.x + d.x * 80, V.y + d.y * 80);
    }
    // the protractor: a half-disc of ticks around the vertex, zero along the base direction
    // a rendered acrylic quarter (vertex at its bottom-right corner), turned round for rays below the surface
    const S = R + 10;
    objs.push(scene.add.image(V.x, V.y, `lab_protractor${R}`).setOrigin((S - 5) / S).setAngle(it.side === "down" ? 180 : 0).setAlpha(0.85).setDepth(449));
    const p = scene.add.graphics().setDepth(450);
    objs.push(p);
    for (let a = 0; a <= 90; a += 5) {
      const d = dir(a), l = a % 10 === 0 ? 7 : 4;
      p.lineStyle(1, 0x0e1938, 1).lineBetween(V.x + d.x * R, V.y + d.y * R, V.x + d.x * (R - l), V.y + d.y * (R - l));
      if (a % 30 === 0) objs.push(scene.add.text(V.x + d.x * (R + 8), V.y + d.y * (R + 8), `${a}`, { fontFamily: FONT, fontSize: "9px", color: "#F2E9CF" }).setOrigin(0.5).setDepth(451));
    }
    const arm = scene.add.graphics().setDepth(460);
    const knob = scene.add.image(0, 0, "lab_knob").setDepth(461).setInteractive({ useHandCursor: true, draggable: true });
    const read = scene.add.text(0, 0, "", { fontFamily: FONT, fontSize: "11px", color: "#0E1938", backgroundColor: "#F2E9CF" }).setPadding(4, 1, 4, 1).setOrigin(0.5).setDepth(462);
    const help = scene.add.text(240, 262, "Drag the red knob onto the ray · arrow keys nudge 1° · Enter to record", { fontFamily: FONT, fontSize: "10px", color: "#F2E9CF", backgroundColor: "#0E1938" })
      .setPadding(5, 2, 5, 2).setOrigin(0.5, 1).setDepth(503);
    objs.push(arm, knob, read, help);
    let a = it.from === "ground" ? 10 : 5;
    const draw = () => {
      const d = dir(a);
      arm.clear().lineStyle(2, 0xc9302a, 1).lineBetween(V.x, V.y, V.x + d.x * ARM, V.y + d.y * ARM);
      knob.setPosition(V.x + d.x * ARM, V.y + d.y * ARM);
      read.setPosition(V.x + d.x * (ARM + 16) + (it.from === "ground" ? 0 : d.x < 0 ? -10 : 10), V.y + d.y * (ARM + 16)).setText(`${Math.round(a)}°`);
    };
    draw();
    await new Promise<void>((res) => {
      const set = (v: number) => {
        const was = a;
        a = Math.round(v);
        if (Math.abs(a - it.angle) <= 1) a = it.angle;
        if (a !== was) sfx(a === it.angle ? "snap" : "type");
        draw();
      };
      const record = () => {
        if (Math.abs(a - it.angle) <= 1.5) {
          cleanup();
          sfx("chime");
          ctx.measured[`${step.record}_${it.key}`] = it.angle;
          res();
        } else {
          sfx("wrong");
          dlg.say({ who: "foot", expr: "worried", text: it.from === "ground" ? "*Lay the arm right along the sun's ray, from the shadow's tip." : "*Measure from the dashed normal, not from the surface. Lay the arm along the ray." })
            .then(() => dlg.hide());
        }
      };
      const onDrag = (pt: Phaser.Input.Pointer, o: Phaser.GameObjects.GameObject) => { if (o === knob) set(angleAt(pt.worldX, pt.worldY)); };
      const onEnd = (_p: Phaser.Input.Pointer, o: Phaser.GameObjects.GameObject) => { if (o === knob) record(); };
      const onKey = (e: KeyboardEvent) => {
        if (e.key === "ArrowUp" || e.key === "ArrowRight") set(a + 1);
        else if (e.key === "ArrowDown" || e.key === "ArrowLeft") set(a - 1);
        else if (e.key === "Enter") record();
      };
      scene.input.on("drag", onDrag);
      scene.input.on("dragend", onEnd);
      scene.input.keyboard?.on("keydown", onKey);
      const cleanup = () => {
        scene.input.off("drag", onDrag);
        scene.input.off("dragend", onEnd);
        scene.input.keyboard?.off("keydown", onKey);
      };
    });
    await dlg.say({ who: "smudge", expr: "happy", text: `${it.label}: ${it.angle}°. Noted.` });
    dlg.hide();
    for (const o of objs) o.destroy();
  }
  await dlg.play(step.done);
  dlg.hide();
}
