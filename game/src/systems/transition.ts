// Scene transitions with intent: ink blots that spread to cover the screen and shrink away to reveal the next,
// and the chapter card that opens each case.
import Phaser from "phaser";
import { W, H, FONT, DISPLAY } from "../consts";
import { sfx, sting } from "../audio";
import { tween, wait } from "./fx";

const INK = 0x0e1938;

/** The same blot layout every time, so a cover and its reveal match. Radii are at full spread. */
const BLOTS = (() => {
  let s = 7;
  const r = () => ((s = (s * 16807) % 2147483647) / 2147483647);
  const out: { x: number; y: number; r: number; d: number }[] = [];
  for (let i = 0; i < 22; i++) out.push({ x: r() * W, y: r() * H, r: 70 + r() * 90, d: r() * 0.35 });
  return out;
})();

function blots(scene: Phaser.Scene) {
  const g = scene.add.graphics().setDepth(6000).setScrollFactor(0);
  const draw = (t: number) => {
    g.clear();
    if (t >= 1) { g.fillStyle(INK, 1).fillRect(-4, -4, W + 8, H + 8); return; }
    g.fillStyle(INK, 1);
    for (const b of BLOTS) {
      const k = Phaser.Math.Clamp((t - b.d) / (1 - b.d), 0, 1);
      if (k <= 0) continue;
      const e = Phaser.Math.Easing.Cubic.In(k);
      g.fillCircle(b.x, b.y, b.r * e);
      // a few satellite droplets give the edge an ink-splash wobble
      g.fillCircle(b.x + b.r * 0.7 * e, b.y - b.r * 0.2 * e, b.r * 0.32 * e);
      g.fillCircle(b.x - b.r * 0.5 * e, b.y + b.r * 0.6 * e, b.r * 0.24 * e);
    }
  };
  return { g, draw };
}

/** Ink spreads until the screen is covered. Start the next scene after this resolves. */
export async function inkOut(scene: Phaser.Scene, ms = 480) {
  const { g, draw } = blots(scene);
  sfx("whoosh");
  const o = { t: 0 };
  draw(0);
  await tween(scene, { targets: o, t: 1, duration: ms, ease: "Linear", onUpdate: () => draw(o.t) });
  draw(1);
  void g;
}

/** The screen starts covered in ink, which shrinks away. Call first thing in create(). */
export function inkIn(scene: Phaser.Scene, ms = 520): Promise<void> {
  const { g, draw } = blots(scene);
  draw(1);
  const o = { t: 1 };
  return tween(scene, { targets: o, t: 0, duration: ms, ease: "Linear", delay: 60, onUpdate: () => draw(o.t) }).then(() => g.destroy());
}

/** The chapter card: an ink band slams in with the case number and chapter, the place name types itself out,
 *  then it all slides away. A tap skips ahead. */
export async function chapterCard(scene: Phaser.Scene, c: { num: number; chapter: string; place: string; title: string }) {
  const root = scene.add.container(0, 0).setDepth(5500).setScrollFactor(0);
  const band = scene.add.rectangle(-W, H / 2 - 4, W, 78, INK, 0.94).setOrigin(0, 0.5);
  const edge = scene.add.graphics();
  edge.lineStyle(2, 0xc9302a, 1).lineBetween(0, -36, W, -36).lineBetween(0, 36, W, 36);
  const edges = scene.add.container(-W, H / 2 - 4, [edge]);
  const kicker = scene.add.text(W / 2, H / 2 - 28, `CASE ${c.num}  ·  ${c.chapter.toUpperCase()}`, { fontFamily: FONT, fontSize: "10px", color: "#E8705F" })
    .setOrigin(0.5).setAlpha(0);
  const place = scene.add.text(W / 2, H / 2 - 4, "", { fontFamily: DISPLAY, fontSize: "30px", color: "#F2E9CF", stroke: "#05060F", strokeThickness: 4 })
    .setOrigin(0.5);
  const title = scene.add.text(W / 2, H / 2 + 22, c.title, { fontFamily: FONT, fontSize: "11px", color: "#FAC775" }).setOrigin(0.5).setAlpha(0);
  root.add([band, edges, kicker, place, title]);

  let skip = false;
  const onTap = () => { skip = true; };
  scene.input.once("pointerdown", onTap);
  const pause = (ms: number) => (skip ? Promise.resolve() : wait(scene, ms));

  sting("chapter");
  await tween(scene, { targets: [band, edges], x: 0, duration: 260, ease: "Cubic.easeOut" });
  scene.cameras.main.shake(120, 0.004);
  await tween(scene, { targets: kicker, alpha: 1, duration: 160 });
  for (let i = 1; i <= c.place.length; i++) {
    place.setText(c.place.slice(0, i));
    if (!skip) { if (c.place[i - 1] !== " ") sfx("type"); await wait(scene, 45); }
  }
  place.setText(c.place);
  await tween(scene, { targets: title, alpha: 1, duration: 200 });
  await pause(1300);
  await tween(scene, { targets: root, x: W, alpha: 0, duration: 300, ease: "Cubic.easeIn" });
  scene.input.off("pointerdown", onTap);
  root.destroy();
}
