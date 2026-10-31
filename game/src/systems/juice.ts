// Game feel: tiny reusable bits of weight. A freeze-frame on impact, squash and stretch, buttons that answer
// the pointer, dust puffs, a screen flash. Shake and freeze are skipped for players who ask for reduced motion.
import Phaser from "phaser";
import { W, H } from "../consts";
import { sfx, type Sfx } from "../audio";
import { makePixel } from "./fx";

export const calm = () => typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Freeze the scene for a moment, like a hit landing. Rendering carries on; updates, tweens and timers pause. */
export function hitStop(scene: Phaser.Scene, ms = 90): Promise<void> {
  if (calm()) return Promise.resolve();
  scene.scene.pause();
  return new Promise((res) => setTimeout(() => { if (scene.scene.isPaused()) scene.scene.resume(); res(); }, ms));
}

/** A camera shake that respects reduced motion. */
export function shake(scene: Phaser.Scene, ms: number, amount: number) {
  if (!calm()) scene.cameras.main.shake(ms, amount);
}

type Scalable = Phaser.GameObjects.Components.Transform & Phaser.GameObjects.GameObject;
const base = new WeakMap<object, { x: number; y: number }>();
const baseOf = (t: Scalable) => {
  if (!base.has(t)) base.set(t, { x: t.scaleX, y: t.scaleY });
  return base.get(t)!;
};

/** Squash flat then spring back: a landing, a hop, a nod. */
export function squash(scene: Phaser.Scene, t: Scalable, amount = 0.18, ms = 110) {
  const b = baseOf(t);
  t.setScale(b.x * (1 + amount), b.y * (1 - amount));
  scene.tweens.add({ targets: t, scaleX: b.x, scaleY: b.y, duration: ms * 2.4, ease: "Back.easeOut" });
}

/** Pop up in size and settle: emphasis. */
export function punch(scene: Phaser.Scene, t: Scalable, amount = 0.2, ms = 90) {
  const b = baseOf(t);
  scene.tweens.add({ targets: t, scaleX: b.x * (1 + amount), scaleY: b.y * (1 + amount), duration: ms, yoyo: true, ease: "Quad.easeOut",
    onComplete: () => t.setScale(b.x, b.y) });
}

/** A little hop: up and back down, with a squash on landing unless something else owns the scale. */
export function hop(scene: Phaser.Scene, t: Scalable & { y: number }, height = 6, ms = 160, land = true) {
  const y0 = t.y;
  scene.tweens.add({ targets: t, y: y0 - height, duration: ms, ease: "Quad.easeOut", yoyo: true,
    onComplete: () => { t.y = y0; if (land) squash(scene, t, 0.14, 80); } });
}

/** Wiggle sideways: "no". */
export function wiggle(scene: Phaser.Scene, t: Scalable & { x: number }, px = 3, ms = 260) {
  if (calm()) return;
  const x0 = t.x;
  scene.tweens.add({ targets: t, x: { from: x0 - px, to: x0 + px }, duration: ms / 6, yoyo: true, repeat: 2, ease: "Sine.easeInOut",
    onComplete: () => { t.x = x0; } });
}

/** A full-screen flash of colour that fades. */
export function flash(scene: Phaser.Scene, color = 0xffffff, alpha = 0.6, ms = 220, depth = 4800) {
  const r = scene.add.rectangle(0, 0, W, H, color, alpha).setOrigin(0).setDepth(depth).setScrollFactor(0);
  scene.tweens.add({ targets: r, alpha: 0, duration: ms, ease: "Quad.easeOut", onComplete: () => r.destroy() });
}

/** A puff of dust at someone's feet. */
export function dustPuff(scene: Phaser.Scene, x: number, y: number, n = 5, tint = 0xcfc2a8, depth = y) {
  makePixel(scene);
  const p = scene.add.particles(x, y, "px", {
    speedX: { min: -26, max: 26 }, speedY: { min: -14, max: -2 }, lifespan: { min: 260, max: 520 },
    scale: { start: 2.4, end: 0.6 }, alpha: { start: 0.65, end: 0 }, tint, emitting: false,
  }).setDepth(depth);
  p.explode(n);
  scene.time.delayedCall(700, () => p.destroy());
}

/** Make a text or image feel like a button: it lifts on hover, sinks on press, and both make a sound.
 *  Text is re-anchored at its centre so it scales in place; its on-screen position does not change. */
export function buttonFeel(scene: Phaser.Scene, b: Phaser.GameObjects.Text | Phaser.GameObjects.Image, press: Sfx = "click") {
  const ox = b.originX, oy = b.originY;
  if (ox !== 0.5 || oy !== 0.5) {
    b.setPosition(b.x + (0.5 - ox) * b.displayWidth, b.y + (0.5 - oy) * b.displayHeight).setOrigin(0.5);
  }
  if (!b.input) b.setInteractive({ useHandCursor: true });
  const s = { x: b.scaleX, y: b.scaleY };
  const to = (k: number, ms: number) => scene.tweens.add({ targets: b, scaleX: s.x * k, scaleY: s.y * k, duration: ms, ease: "Quad.easeOut" });
  b.on("pointerover", () => { to(1.07, 90); sfx("hover"); });
  b.on("pointerout", () => to(1, 120));
  b.on("pointerdown", () => { to(0.93, 50); sfx(press); });
  b.on("pointerup", () => to(1.07, 90));
  return b;
}
