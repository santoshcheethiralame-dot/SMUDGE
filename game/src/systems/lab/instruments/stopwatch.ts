// Smudge's stopwatch form, timing clips on a screen. "flashboom": a storm video where lightning flashes and the
// thunder arrives `seconds` later; tap once at the flash, again at the boom. "rise": security footage of a lift
// climbing a shaft for `seconds`; tap when it starts moving, again when it stops. Within 0.25 s snaps to the truth;
// after three tries Footnote's own watch steps in, so nobody gets stuck on reflexes.
import Phaser from "phaser";
import { FONT } from "../../../consts";
import { sfx } from "../../../audio";
import { wait } from "../../fx";
import type { LabCtx, StopwatchStep } from "../types";

export const kind = "stopwatch";

const SCREEN = { x: 22, y: 92, w: 262, h: 150 };

export async function run(ctx: LabCtx, step: StopwatchStep) {
  const { scene, dlg } = ctx;
  const watch = scene.add.sprite(372, 120, "smudge", "form_stopwatch/S/0").setScale(2).play("form_stopwatch_S");
  const lcd = scene.add.text(372, 168, "0.00 s", { fontFamily: FONT, fontSize: "16px", color: "#9CF5B5", backgroundColor: "#0E1938" })
    .setPadding(6, 2, 6, 2).setOrigin(0.5);
  // the phone screen the storm videos play on
  const frame = scene.add.image(12, 76, "lab_phone").setOrigin(0).setDepth(5);
  const title = scene.add.text(SCREEN.x, SCREEN.y - 13, "", { fontFamily: FONT, fontSize: "9px", color: "#F2E9CF" }).setDepth(6);
  const sky = scene.add.graphics();
  const bolt = scene.add.graphics();
  const flash = scene.add.rectangle(SCREEN.x, SCREEN.y, SCREEN.w, SCREEN.h, 0xffffff, 0).setOrigin(0);
  const boom = scene.add.text(SCREEN.x + SCREEN.w / 2, SCREEN.y + SCREEN.h / 2, "", { fontFamily: '"Lilita One", sans-serif', fontSize: "28px", color: "#FAC775", stroke: "#0E1938", strokeThickness: 5 })
    .setOrigin(0.5).setDepth(6);
  const drawSky = (lit: number) => {
    sky.clear();
    for (let i = 0; i < 6; i++) {
      const c = Phaser.Display.Color.Interpolate.ColorWithColor(
        Phaser.Display.Color.ValueToColor(0x0a0f24), Phaser.Display.Color.ValueToColor(0x3a4a78), 5, i);
      const col = Phaser.Display.Color.GetColor(c.r + lit, c.g + lit, c.b + lit);
      sky.fillStyle(col, 1).fillRect(SCREEN.x, SCREEN.y + (i * SCREEN.h) / 6, SCREEN.w, SCREEN.h / 6 + 1);
    }
    sky.fillStyle(0x141b3a, 1).fillRect(SCREEN.x, SCREEN.y + SCREEN.h - 26, SCREEN.w, 26);       // hills
    sky.fillStyle(0x22305c, 1).fillTriangle(SCREEN.x + 150, SCREEN.y + SCREEN.h - 26, SCREEN.x + 170, SCREEN.y + 56, SCREEN.x + 190, SCREEN.y + SCREEN.h - 26); // the bell tower
  };
  drawSky(0);
  // the lift shaft, for "rise" clips: brick walls, two guide rails, the crate on its platform
  const shaft = scene.add.graphics();
  const SH = { x: SCREEN.x + SCREEN.w / 2, top: SCREEN.y + 18, bottom: SCREEN.y + SCREEN.h - 14 };
  shaft.fillStyle(0x1e1418, 1).fillRect(SCREEN.x, SCREEN.y, SCREEN.w, SCREEN.h);
  for (let y = SCREEN.y; y < SCREEN.y + SCREEN.h; y += 6) {
    for (let x = SCREEN.x + ((y / 6) % 2) * 6; x < SCREEN.x + SCREEN.w; x += 12) shaft.fillStyle(0x3a2026, 1).fillRect(x, y, 11, 5);
  }
  shaft.fillStyle(0x0a0608, 0.85).fillRect(SH.x - 34, SCREEN.y, 68, SCREEN.h);
  shaft.lineStyle(2, 0x626e7f, 1).lineBetween(SH.x - 30, SCREEN.y, SH.x - 30, SCREEN.y + SCREEN.h).lineBetween(SH.x + 30, SCREEN.y, SH.x + 30, SCREEN.y + SCREEN.h);
  shaft.fillStyle(0x47515f, 1).fillRect(SH.x - 34, SH.top - 6, 68, 3).fillRect(SH.x - 34, SH.bottom + 10, 68, 4);
  shaft.lineStyle(1, 0x9aa4af, 0.8).lineBetween(SH.x, SCREEN.y, SH.x, SH.top - 6);
  const crate = scene.add.image(SH.x, SH.bottom, "lab_crate").setOrigin(0.5, 1);
  const rec = scene.add.text(SCREEN.x + 6, SCREEN.y + 4, "● REC  TOWER CAM 2", { fontFamily: FONT, fontSize: "9px", color: "#FF5A4A" });
  const setStyle = (rise: boolean) => { for (const o of [shaft, crate, rec]) o.setVisible(rise); sky.setVisible(!rise); };

  await dlg.play(step.intro);
  dlg.hide();

  for (const clip of step.clips(ctx.c)) {
    title.setText(`▶ ${clip.label}`);
    const rise = clip.style === "rise";
    setStyle(rise);
    for (let attempt = 1; ; attempt++) {
      lcd.setText("0.00 s");
      boom.setText("");
      const go = scene.add.text(372, 204, "▶  Play the video", { fontFamily: FONT, fontSize: "11px", color: "#FFFFFF", backgroundColor: "#C9302A" })
        .setPadding(8, 3, 8, 3).setOrigin(0.5).setInteractive({ useHandCursor: true });
      await new Promise<void>((res) => go.once("pointerdown", () => res()));
      go.destroy();
      crate.setY(SH.bottom);
      const tap = scene.add.text(372, 204, rise ? "TAP: when it moves, when it stops" : "TAP: at the flash, at the boom", { fontFamily: FONT, fontSize: "9px", color: "#0E1938", backgroundColor: "#F2E9CF" })
        .setPadding(5, 2, 5, 2).setOrigin(0.5);
      let started = -1, stopped = -1, clock = 0;
      const onTap = () => {
        if (started < 0) { started = clock; sfx("tick"); } else if (stopped < 0) { stopped = clock; sfx("tick"); }
      };
      scene.input.on("pointerdown", onTap);
      scene.input.keyboard?.on("keydown-SPACE", onTap);

      const lead = 0.8 + Math.random() * 1.2;          // the flash comes when it comes
      const total = lead + clip.seconds + 1.4;
      await new Promise<void>((res) => {
        const t0 = scene.time.now;
        let flashed = false, boomed = false;
        const ev = scene.time.addEvent({
          delay: 16, loop: true, callback: () => {
            clock = (scene.time.now - t0) / 1000;
            if (rise) {
              const f = Phaser.Math.Clamp((clock - lead) / clip.seconds, 0, 1);
              crate.setY(SH.bottom - f * (SH.bottom - SH.top - 30));
              if (!flashed && clock >= lead) { flashed = true; sfx("tick"); }
              if (!boomed && clock >= lead + clip.seconds) { boomed = true; sfx("tick"); scene.cameras.main.shake(120, 0.003); }
            } else if (!flashed && clock >= lead) {
              flashed = true;
              flash.setAlpha(0.95);
              scene.tweens.add({ targets: flash, alpha: 0, duration: 260 });
              const x0 = SCREEN.x + 60 + Math.random() * 60;
              bolt.clear().lineStyle(3, 0xfff8d0, 1).beginPath().moveTo(x0, SCREEN.y + 4);
              let x = x0, y = SCREEN.y + 4;
              while (y < SCREEN.y + SCREEN.h - 30) { x += (Math.random() - 0.5) * 22; y += 12 + Math.random() * 10; bolt.lineTo(x, y); }
              bolt.strokePath();
              drawSky(40);
              scene.time.delayedCall(180, () => { bolt.clear(); drawSky(0); });
            }
            if (!rise && !boomed && clock >= lead + clip.seconds) {
              boomed = true;
              sfx("rumble");
              scene.cameras.main.shake(380, 0.006);
              boom.setText("BOOM").setScale(0.4).setAlpha(1);
              scene.tweens.add({ targets: boom, scale: 1.1, duration: 220, ease: "Back.easeOut" });
              scene.tweens.add({ targets: boom, alpha: 0, delay: 700, duration: 300 });
            }
            if (started >= 0) lcd.setText(`${((stopped >= 0 ? stopped : clock) - started).toFixed(2)} s`);
            if (clock > total && (stopped >= 0 || clock > total + 1.5)) { ev.remove(); res(); }
          },
        });
      });
      scene.input.off("pointerdown", onTap);
      scene.input.keyboard?.off("keydown-SPACE", onTap);
      tap.destroy();
      const timed = started >= 0 && stopped >= 0 ? stopped - started : NaN;
      const good = Math.abs(timed - clip.seconds) <= 0.25;
      if (good || attempt >= 3) {
        ctx.measured[`${step.record}_${clip.key}`] = clip.seconds;
        lcd.setText(`${clip.seconds.toFixed(2)} s`);
        sfx("chime");
        await dlg.say(good
          ? { who: "smudge", expr: "happy", text: `${clip.label}: ${clip.seconds.toFixed(2)} s${rise ? " from start to stop" : " from flash to boom"}. Noted.` }
          : { who: "foot", expr: "neutral", text: `*Tricky one! Smudge's watch caught it anyway: ${clip.seconds.toFixed(2)} s.` });
        dlg.hide();
        await wait(scene, 200);
        break;
      }
      sfx("wrong");
      await dlg.say({ who: "foot", expr: "worried", text: Number.isNaN(timed)
        ? (rise ? "*Tap once when it starts moving and again when it stops. Let's play it again." : "*Tap once at the flash and again at the boom. Let's play it again.")
        : rise ? `*You got ${timed.toFixed(2)} s. Tap the moment the crate starts to rise, and again the moment it stops.`
          : `*You got ${timed.toFixed(2)} s. Tap the very moment you see the flash, and again at the boom.` });
      dlg.hide();
    }
  }
  await dlg.play(step.done);
  dlg.hide();
  for (const o of [watch, lcd, frame, title, sky, bolt, flash, boom, shaft, crate, rec]) o.destroy();
}
