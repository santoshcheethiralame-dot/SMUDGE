// Roll a die many times and keep a tally chart: four strokes and a bar for every five. The counts come from the
// case; the rolls play out in a shuffled order so the chart fills the way real rolling would.
import Phaser from "phaser";
import { FONT } from "../../../consts";
import { sfx } from "../../../audio";
import { wait } from "../../fx";
import { AREA, panel, button, clicked } from "../parts";
import type { LabCtx, TallyStep } from "../types";

export const kind = "tally";

export async function run(ctx: LabCtx, step: TallyStep) {
  const { scene, dlg } = ctx;
  await dlg.play(step.intro);
  dlg.hide();
  for (const set of step.sets(ctx.c)) {
    const objs: Phaser.GameObjects.GameObject[] = panel(scene, set.label, 0xf2e9cf);
    const die = scene.add.image(AREA.x + 70, AREA.y + 76, "lab_die1");
    const marks = scene.add.graphics();
    objs.push(die, marks);
    const faces = set.counts.length;
    const rowY = (f: number) => AREA.y + 26 + f * ((AREA.h - 36) / faces);
    for (let f = 0; f < faces; f++) objs.push(scene.add.text(AREA.x + 150, rowY(f) + 4, `${f + 1}`, { fontFamily: FONT, fontSize: "9px", color: "#0E1938" }).setOrigin(0.5));
    const nums = objs.length;
    void nums;
    const drawDie = (v: number, wob: number) =>
      die.setTexture(`lab_die${Math.min(v, 6)}`).setPosition(AREA.x + 70 + wob, AREA.y + 76 - Math.abs(wob) * 2).setScale(1.5);
    drawDie(1, 0);
    const go = button(scene, AREA.x + 70, AREA.y + 124, `▶ Roll ${set.counts.reduce((a, b) => a + b, 0)} times`);
    objs.push(go);
    await clicked(go);
    go.destroy();
    const rolls = set.counts.flatMap((n, f) => Array(n).fill(f + 1)) as number[];
    Phaser.Utils.Array.Shuffle(rolls);
    const got = Array(faces).fill(0);
    const drawMarks = () => {
      marks.clear().lineStyle(1.5, 0x0e1938, 1);
      got.forEach((n, f) => {
        for (let k = 0; k < n; k++) {
          const grp = Math.floor(k / 5), inG = k % 5, x = AREA.x + 166 + grp * 22 + inG * 4, y = rowY(f);
          if (inG === 4) marks.lineStyle(1.5, 0xc9302a, 1).lineBetween(x - 18, y + 8, x - 1, y);
          else marks.lineStyle(1.5, 0x0e1938, 1).lineBetween(x, y, x, y + 8);
        }
      });
    };
    for (const [i, v] of rolls.entries()) {
      drawDie(v, i % 2 ? 3 : -3);
      got[v - 1]++;
      drawMarks();
      if (i % 3 === 0) sfx("tick");
      await wait(scene, Math.max(25, 140 - i * 4));
    }
    drawDie(rolls[rolls.length - 1], 0);
    set.counts.forEach((n, f) => { ctx.measured[`${step.record}_${set.key}_${f + 1}`] = n; });
    ctx.measured[`${step.record}_${set.key}_total`] = rolls.length;
    got.forEach((n, f) => objs.push(scene.add.text(AREA.x + AREA.w - 14, rowY(f) + 4, `${n}`, { fontFamily: FONT, fontSize: "9px", color: "#C9302A" }).setOrigin(1, 0.5)));
    sfx("chime");
    await dlg.say({ who: "smudge", expr: "thinking", text: `${set.label}: tallied. ${rolls.length} rolls.` });
    dlg.hide();
    await wait(scene, 400);
    for (const o of objs) o.destroy();
  }
  await dlg.play(step.done);
  dlg.hide();
}
