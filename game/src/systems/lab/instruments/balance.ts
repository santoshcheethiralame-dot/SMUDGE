// A digital balance: drag each item onto the pan, the display counts up and settles, the mass is recorded.
import Phaser from "phaser";
import { FONT } from "../../../consts";
import { sfx } from "../../../audio";
import { tween } from "../../fx";
import { AREA, panel, tick } from "../parts";
import type { LabCtx, BalanceStep } from "../types";

export const kind = "balance";

export async function run(ctx: LabCtx, step: BalanceStep) {
  const { scene, dlg } = ctx;
  const items = step.items(ctx.c);
  const objs: Phaser.GameObjects.GameObject[] = panel(scene, "Balance", 0x3a3342);
  // the rendered balance: its pan centre sits 19 px down the image, the LCD 24 px below that and 6 px left
  const pan = { x: AREA.x + AREA.w - 120, y: AREA.y + 92 };
  objs.push(scene.add.image(pan.x, pan.y, "lab_balance").setOrigin(0.5, 19.4 / 58));
  const lcd = scene.add.text(pan.x - 6, pan.y + 23, "0", { fontFamily: FONT, fontSize: "11px", color: "#9CF5B5" }).setOrigin(0.5);
  objs.push(lcd);
  await dlg.play(step.intro);
  dlg.hide();
  for (const [i, it] of items.entries()) {
    const home = { x: AREA.x + 50 + i * 60, y: AREA.y + 100 };
    const crate = scene.add.container(home.x, home.y);
    const bare = it.look === "tub" || it.look === "ingot";
    const box = scene.add.image(0, 0, `lab_${it.look ?? "crate"}`);
    const lbl = scene.add.text(0, bare ? 17 : 2, it.label, { fontFamily: FONT, fontSize: "9px", color: bare ? "#F2E9CF" : "#0E1938", align: "center", wordWrap: { width: bare ? 60 : 26 } }).setOrigin(0.5);
    crate.add([box, lbl]).setSize(40, 38).setInteractive({ useHandCursor: true, draggable: true });
    objs.push(crate);
    const hint = scene.add.text(home.x, home.y - 22, "drag me", { fontFamily: FONT, fontSize: "10px", color: "#FFC46B" }).setOrigin(0.5);
    objs.push(hint);
    await new Promise<void>((res) => {
      const onDrag = (_p: Phaser.Input.Pointer, o: Phaser.GameObjects.GameObject, x: number, y: number) => { if (o === crate) crate.setPosition(x, y); };
      const onStart = (_p: Phaser.Input.Pointer, o: Phaser.GameObjects.GameObject) => {
        if (o !== crate) return;
        sfx("hop");
        scene.tweens.add({ targets: crate, scale: 1.1, duration: 90 });
      };
      const onEnd = (_p: Phaser.Input.Pointer, o: Phaser.GameObjects.GameObject) => {
        if (o !== crate) return;
        if (Math.abs(crate.x - pan.x) < 50 && Math.abs(crate.y - pan.y) < 40) {
          scene.input.off("drag", onDrag);
          scene.input.off("dragend", onEnd);
          scene.input.off("dragstart", onStart);
          crate.setPosition(pan.x, pan.y - 10).setScale(1.12, 0.86);
          scene.tweens.add({ targets: crate, scaleX: 1, scaleY: 1, duration: 220, ease: "Back.easeOut" });
          sfx("plop");
          res();
        } else {
          sfx("drop");
          scene.tweens.add({ targets: crate, x: home.x, y: home.y, scale: 1, duration: 220, ease: "Back.easeOut" });
        }
      };
      scene.input.on("dragstart", onStart);
      scene.input.on("drag", onDrag);
      scene.input.on("dragend", onEnd);
    });
    hint.destroy();
    sfx("tick");
    const s = { v: 0 };
    let shownV = -1;
    await tween(scene, { targets: s, v: it.mass, duration: 900, ease: "Cubic.easeOut", onUpdate: () => {
      const v = Math.round(s.v);
      if (v !== shownV && v % Math.max(1, Math.round(it.mass / 12)) === 0) sfx("type");
      shownV = v;
      lcd.setText(`${v} ${step.unit}`);
    } });
    lcd.setText(`${it.mass} ${step.unit}`);
    ctx.measured[`${step.record}_${it.key}`] = it.mass;
    sfx("chime");
    await dlg.say({ who: "smudge", expr: "thinking", text: `${it.label}: ${it.mass} ${step.unit}.` });
    dlg.hide();
    crate.disableInteractive();
    scene.tweens.add({ targets: crate, x: home.x, y: home.y, duration: 260 });
    objs.push(tick(scene, home.x - 16, home.y + (bare ? 30 : 22), `${it.mass} ${step.unit}`));
    lcd.setText(`0 ${step.unit}`);
  }
  await dlg.play(step.done);
  dlg.hide();
  for (const o of objs) o.destroy();
}
