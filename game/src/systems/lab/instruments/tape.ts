// Smudge's tape-measure form on an evidence photo: drag the hat from the start line to where each mark ends
// (arrow keys nudge, Enter records). Snaps within one step of the true end; records within 1.5 steps.
import Phaser from "phaser";
import { FONT } from "../../../consts";
import { sfx } from "../../../audio";
import { AREA, panel, tick } from "../parts";
import type { LabCtx, TapeStep } from "../types";

export const kind = "tape";

const INK = 0x0b0910;

function drawMark(g: Phaser.GameObjects.Graphics, style: string, x0: number, y: number, len: number) {
  if (style === "skid2") {
    g.lineStyle(1.5, INK, 1).lineBetween(x0, y - 3, x0 + len, y - 3).lineBetween(x0, y + 3, x0 + len, y + 3);
  } else if (style === "chevron") {
    for (let x = 0; x < len - 3; x += 5) g.lineStyle(2, INK, 1).lineBetween(x0 + x, y - 5, x0 + x + 2.5, y).lineBetween(x0 + x + 2.5, y, x0 + x, y + 5);
  } else if (style === "scuff") {
    for (let x = 0; x < len; x++) for (let j = -7; j <= 7; j += 2) {
      if (Math.sin(x * 0.7 + j * 2.6) * 0.5 + 0.5 < 0.2 + 0.5 * (x / len)) continue;
      g.fillStyle(INK, 1).fillRect(Math.round(x0 + x), Math.round(y + j * (1 - 0.3 * x / len)), 1, 1);
    }
  } else if (style === "shadow") {
    g.fillStyle(0x05060f, 0.55).fillTriangle(x0, y - 5, x0, y + 5, x0 + len, y);
    // the landmark casting it, standing at the shadow's foot
    g.fillStyle(0x2c2440, 1).fillRect(x0 - 2, y - 14, 4, 16).fillStyle(0xffe08a, 1).fillRect(x0 - 3, y - 16, 6, 3);
  } else {
    g.fillStyle(INK, 0.85).fillRect(x0, y - 3, len, 6);
  }
}

export async function run(ctx: LabCtx, step: TapeStep) {
  const { scene, dlg } = ctx;
  const rows = step.rows(ctx.c);
  const objs: Phaser.GameObjects.GameObject[] = panel(scene, step.title, step.fill ?? 0x5a5166);
  const x0 = AREA.x + 58, x1 = AREA.x + AREA.w - 22;
  const pxPer = (x1 - x0) / step.max;
  const top = AREA.y + 30, gap = Math.min(36, (AREA.h - 46) / Math.max(1, rows.length - 1 || 1));
  const g = scene.add.graphics();
  objs.push(g);
  g.lineStyle(3, 0xf4f0e6, 1).lineBetween(x0 - 2, AREA.y + 18, x0 - 2, AREA.y + AREA.h - 8);
  // the scale along the bottom
  const scaleY = AREA.y + AREA.h - 8;
  const every = step.max <= 10 ? 1 : step.max <= 30 ? 2 : 5;
  for (let v = 0; v <= step.max + 1e-6; v += every) {
    const x = x0 + v * pxPer;
    g.lineStyle(1, 0xf4f0e6, 1).lineBetween(x, scaleY - 4, x, scaleY);
    objs.push(scene.add.text(x, scaleY + 2, `${v}`, { fontFamily: FONT, fontSize: "9px", color: "#0E1938" }).setOrigin(0.5, 0));
  }
  rows.forEach((r, i) => {
    const y = top + i * gap;
    drawMark(g, r.style ?? "bar", x0, y, r.length * pxPer);
    objs.push(scene.add.text(AREA.x + 10, y, r.label, { fontFamily: FONT, fontSize: "10px", color: "#0E1938", backgroundColor: "#F2E9CF" })
      .setPadding(2, 1, 2, 1).setOrigin(0, 0.5));
  });

  await dlg.play(step.intro);
  dlg.hide();
  const tape = scene.add.graphics().setDepth(500);
  const head = scene.add.sprite(x0, top, "smudge", "form_ruler/S/0").setOrigin(0.5, 0.9).setDepth(501).setInteractive({ useHandCursor: true, draggable: true });
  const read = scene.add.text(0, 0, "", { fontFamily: FONT, fontSize: "11px", color: "#0E1938", backgroundColor: "#F2E9CF" })
    .setPadding(4, 1, 4, 1).setOrigin(0.5, 1).setDepth(502);
  const help = scene.add.text(240, 262, "Drag the hat along the mark · arrow keys nudge · Enter to record", { fontFamily: FONT, fontSize: "10px", color: "#F2E9CF", backgroundColor: "#0E1938" })
    .setPadding(5, 2, 5, 2).setOrigin(0.5, 1).setDepth(503);
  objs.push(tape, head, read, help);
  const unitStep = step.step ?? 0.1;
  const dp = Math.max(0, Math.round(-Math.log10(unitStep)));

  for (const [i, r] of rows.entries()) {
    const y = top + i * gap;
    let m = 0;
    const draw = () => {
      const bx = x0 + m * pxPer;
      // a steel tape: yellow blade, a mark every scale step, a brass hook at the end
      tape.clear().fillStyle(0xe5b848, 1).fillRect(x0, y - 3, Math.max(1, bx - x0), 6).fillStyle(0xfff4c8, 1).fillRect(x0, y - 3, Math.max(1, bx - x0), 1);
      tape.lineStyle(1, 0x3e2a06, 1).strokeRect(x0, y - 3, Math.max(1, bx - x0), 6);
      for (let v = every; x0 + v * pxPer < bx; v += every) tape.lineBetween(x0 + v * pxPer, y - 3, x0 + v * pxPer, y);
      tape.fillStyle(0xc08f2c, 1).fillRect(bx - 1, y - 5, 2, 10);
      head.setPosition(bx, y - 2);
      read.setPosition(bx, y - 24).setText(`${m.toFixed(dp)} ${step.unit}`);
    };
    draw();
    await new Promise<void>((res) => {
      const set = (v: number) => {
        const was = m;
        m = Phaser.Math.Clamp(Math.round(v / unitStep) * unitStep, 0, step.max);
        if (Math.abs(m - r.length) <= unitStep * 1.01) m = r.length;
        if (m !== was) sfx(m === r.length ? "snap" : "type");
        draw();
      };
      const record = () => {
        if (Math.abs(m - r.length) <= unitStep * 1.5) {
          cleanup();
          sfx("chime");
          ctx.measured[`${step.record}_${r.key}`] = r.length;
          objs.push(tick(scene, x0 + r.length * pxPer + 8, y, `${r.length.toFixed(dp)} ${step.unit}`));
          res();
        } else if (m > unitStep * 2) {
          sfx("wrong");
          dlg.say({ who: "foot", expr: "worried", text: m < r.length ? "*It keeps going. Stretch further!" : "*Too far: stop where the mark ends." }).then(() => dlg.hide());
        }
      };
      const onDrag = (_p: Phaser.Input.Pointer, o: Phaser.GameObjects.GameObject, x: number) => { if (o === head) set((x - x0) / pxPer); };
      const onEnd = (_p: Phaser.Input.Pointer, o: Phaser.GameObjects.GameObject) => { if (o === head) record(); };
      const onKey = (e: KeyboardEvent) => {
        if (e.key === "ArrowRight") set(m + unitStep);
        else if (e.key === "ArrowLeft") set(m - unitStep);
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
  }
  await dlg.play(step.done);
  dlg.hide();
  for (const o of objs) o.destroy();
}
