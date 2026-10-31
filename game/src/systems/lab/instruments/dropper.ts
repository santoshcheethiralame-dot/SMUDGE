// Universal indicator: tap a tube to drip indicator in, watch it change colour, then tap the matching colour on
// the pH chart. The right swatch records that sample's pH.
import Phaser from "phaser";
import { FONT } from "../../../consts";
import { sfx } from "../../../audio";
import { tween, wait } from "../../fx";
import { AREA, panel, tick } from "../parts";
import type { LabCtx, DropperStep } from "../types";

export const kind = "dropper";

/** Universal indicator colours, pH 1 to 14. */
export const PH_COLOURS = [0xe0261b, 0xe8471a, 0xf07018, 0xf4a21c, 0xf2c621, 0xd9db2a, 0x7cc242, 0x2fa84f, 0x1e9e8e, 0x2b7bc0, 0x3b57b0, 0x4b3f9e, 0x5b2e8c, 0x4a2172];

export async function run(ctx: LabCtx, step: DropperStep) {
  const { scene, dlg } = ctx;
  const samples = step.samples(ctx.c);
  const objs: Phaser.GameObjects.GameObject[] = panel(scene, "Universal indicator", 0xe3d8b8);
  const g = scene.add.graphics();
  objs.push(g);
  // the pH chart along the bottom
  const sw = (AREA.w - 40) / 14, cy = AREA.y + AREA.h - 22;
  const swatches = PH_COLOURS.map((c, i) => {
    const x = AREA.x + 20 + i * sw;
    const r = scene.add.rectangle(x + sw / 2, cy, sw - 2, 14, c).setStrokeStyle(1, 0x0e1938).setInteractive({ useHandCursor: true });
    objs.push(r, scene.add.text(x + sw / 2, cy + 11, `${i + 1}`, { fontFamily: FONT, fontSize: "9px", color: "#0E1938" }).setOrigin(0.5, 0));
    return r;
  });
  // the tubes in a rack
  const tx = (i: number) => AREA.x + 80 + i * ((AREA.w - 160) / Math.max(1, samples.length - 1 || 1));
  const tubes = samples.map((s, i) => {
    const x = samples.length === 1 ? AREA.x + AREA.w / 2 : tx(i);
    const liquid = scene.add.rectangle(x, AREA.y + 86, 10, 30, 0xdfe8f0).setOrigin(0.5, 1);
    objs.push(scene.add.image(x, AREA.y + 60, "lab_tube").setAlpha(0.6));
    const hit = scene.add.rectangle(x, AREA.y + 60, 22, 64, 0xffffff, 0.001).setInteractive({ useHandCursor: true });
    objs.push(liquid, hit, scene.add.text(x, AREA.y + 96, s.label, { fontFamily: FONT, fontSize: "10px", color: "#0E1938" }).setOrigin(0.5, 0));
    return { liquid, hit, x };
  });
  // a wooden rack behind the tubes
  g.fillStyle(0x47270f, 1).fillRect(AREA.x + 50, AREA.y + 62, AREA.w - 100, 5).fillRect(AREA.x + 50, AREA.y + 90, AREA.w - 100, 4);
  g.fillStyle(0x8c5022, 1).fillRect(AREA.x + 50, AREA.y + 62, AREA.w - 100, 2).fillRect(AREA.x + 50, AREA.y + 90, AREA.w - 100, 1);
  const dropper = scene.add.image(0, AREA.y + 12, "lab_dropper").setDepth(500).setVisible(false);
  const drop = scene.add.circle(0, 0, 1.6, 0x7cc242).setDepth(501).setVisible(false);
  objs.push(dropper, drop);
  await dlg.play(step.intro);
  dlg.hide();

  for (const [i, s] of samples.entries()) {
    const t = tubes[i];
    const hint = scene.add.text(t.x, AREA.y + 24, "▼ tap", { fontFamily: FONT, fontSize: "10px", color: "#C9302A" }).setOrigin(0.5);
    objs.push(hint);
    await new Promise<void>((res) => t.hit.once("pointerdown", () => res()));
    hint.destroy();
    // drip, drip
    for (let k = 0; k < 3; k++) {
      dropper.setX(t.x).setVisible(true);
      drop.setPosition(t.x, AREA.y + 34 + k * 6).setVisible(true);
      sfx("tick");
      await wait(scene, 160);
    }
    dropper.setVisible(false);
    drop.setVisible(false);
    const target = PH_COLOURS[s.ph - 1];
    const from = Phaser.Display.Color.ValueToColor(0xdfe8f0), to = Phaser.Display.Color.ValueToColor(target);
    await tween(scene, {
      targets: { k: 0 }, k: 100, duration: 700,
      onUpdate: (tw: Phaser.Tweens.Tween) => {
        const c = Phaser.Display.Color.Interpolate.ColorWithColor(from, to, 100, (tw.targets[0] as { k: number }).k);
        t.liquid.setFillStyle(Phaser.Display.Color.GetColor(c.r, c.g, c.b));
      },
    });
    await dlg.say({ who: "foot", expr: "neutral", text: `*${s.label} turned this colour. Tap the matching colour on the chart.` });
    dlg.hide();
    for (let attempt = 1; ; attempt++) {
      const picked = await new Promise<number>((res) => swatches.forEach((sw2, j) => sw2.once("pointerdown", () => res(j + 1))));
      swatches.forEach((sw2) => sw2.removeAllListeners("pointerdown"));
      if (picked === s.ph || attempt >= 3) {
        sfx("chime");
        ctx.measured[`${step.record}_${s.key}`] = s.ph;
        objs.push(tick(scene, t.x - 14, AREA.y + 112, `pH ${s.ph}`));
        break;
      }
      sfx("wrong");
      await dlg.say({ who: "foot", expr: "worried", text: picked < s.ph ? "*Close, but the tube's a little further along the chart than that." : "*Close, but back a little: the tube's colour comes earlier on the chart." });
      dlg.hide();
    }
  }
  await dlg.play(step.done);
  dlg.hide();
  for (const o of objs) o.destroy();
}
