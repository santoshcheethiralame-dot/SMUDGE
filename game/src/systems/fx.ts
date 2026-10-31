// Small reusable effects: soft light textures, dust motes, a paper-tear wipe,
// promise wrappers so cutscenes read top to bottom.
import Phaser from "phaser";
import { W, H } from "../consts";
import { sfx } from "../audio";

/** Radial gradient texture (white -> transparent) for additive glows. */
export function makeGlow(scene: Phaser.Scene, key: string, r: number, steps = 6) {
  if (scene.textures.exists(key)) return;
  const g = scene.make.graphics({ x: 0, y: 0 }, false);
  for (let i = steps; i >= 1; i--) {
    g.fillStyle(0xffffff, (1 / steps) * 0.55);
    g.fillCircle(r, r, (r * i) / steps);
  }
  g.generateTexture(key, r * 2, r * 2);
  g.destroy();
}

/** Banded cone texture for lamp beams (pointing down from the top centre). */
export function makeCone(scene: Phaser.Scene, key: string, w: number, h: number, steps = 7) {
  if (scene.textures.exists(key)) return;
  const g = scene.make.graphics({ x: 0, y: 0 }, false);
  for (let i = steps; i >= 1; i--) {
    const f = i / steps;
    g.fillStyle(0xffffff, 0.06);
    g.fillTriangle(w / 2, 0, w / 2 - (w / 2) * f, h * (0.6 + 0.4 * f), w / 2 + (w / 2) * f, h * (0.6 + 0.4 * f));
  }
  g.generateTexture(key, w, h);
  g.destroy();
}

export function makePixel(scene: Phaser.Scene) {
  if (scene.textures.exists("px")) return;
  const g = scene.make.graphics({ x: 0, y: 0 }, false);
  g.fillStyle(0xffffff, 1).fillRect(0, 0, 1, 1);
  g.generateTexture("px", 1, 1);
  g.destroy();
}

/** Drifting dust motes inside a rectangle; returns the emitter. */
export function dust(scene: Phaser.Scene, x: number, y: number, w: number, h: number, tint = 0xfff0c8, qty = 40) {
  makePixel(scene);
  return scene.add.particles(0, 0, "px", {
    x: { min: x, max: x + w }, y: { min: y, max: y + h },
    lifespan: { min: 3000, max: 7000 }, speedX: { min: -3, max: 3 }, speedY: { min: -4, max: 2 },
    alpha: { start: 0.75, end: 0 }, tint, frequency: 140, maxParticles: 0, quantity: 1,
    blendMode: Phaser.BlendModes.ADD, advance: 4000,
  }).setDepth(50);
}

export const wait = (scene: Phaser.Scene, ms: number) =>
  new Promise<void>((res) => scene.time.delayedCall(ms, () => res()));

export const tween = (scene: Phaser.Scene, cfg: Phaser.Types.Tweens.TweenBuilderConfig) =>
  new Promise<void>((res) => scene.tweens.add({ ...cfg, onComplete: () => res() }));

export function playOnce(sprite: Phaser.GameObjects.Sprite, key: string) {
  return new Promise<void>((res) => {
    sprite.play(key);
    sprite.once(Phaser.Animations.Events.ANIMATION_COMPLETE, () => res());
  });
}

/** Page-turn wipe: a sheet of paper sweeps across with a curl shadow. */
export async function pageTurn(scene: Phaser.Scene, onMid: () => void | Promise<void>) {
  sfx("flip");
  const sheet = scene.add.rectangle(W + 40, 0, W + 80, H, 0xf2e9cf).setOrigin(0, 0).setDepth(5000).setScrollFactor(0);
  const shade = scene.add.rectangle(W + 30, 0, 14, H, 0x000000, 0.35).setOrigin(0, 0).setDepth(5001).setScrollFactor(0);
  const lines = scene.add.graphics().setDepth(5002).setScrollFactor(0);
  const drawLines = () => {
    lines.clear();
    lines.lineStyle(1, 0x9cb8dc, 0.9);
    for (let y = 14; y < H; y += 14) lines.lineBetween(sheet.x, y + 0.5, sheet.x + sheet.width, y + 0.5);
    lines.lineStyle(1, 0xd47676, 1).lineBetween(sheet.x + 40.5, 0, sheet.x + 40.5, H);
  };
  await tween(scene, { targets: [sheet, shade], x: "-=" + (W + 80), duration: 520, ease: "Cubic.easeIn", onUpdate: drawLines });
  await onMid();
}

/** Second half of the page turn: the sheet slides off and reveals the new scene. */
export async function pageReveal(scene: Phaser.Scene) {
  const sheet = scene.add.rectangle(-40, 0, W + 80, H, 0xf2e9cf).setOrigin(0, 0).setDepth(5000).setScrollFactor(0);
  const lines = scene.add.graphics().setDepth(5002).setScrollFactor(0);
  const draw = () => {
    lines.clear();
    lines.lineStyle(1, 0x9cb8dc, 0.9);
    for (let y = 14; y < H; y += 14) lines.lineBetween(sheet.x, y + 0.5, sheet.x + sheet.width, y + 0.5);
  };
  draw();
  await tween(scene, { targets: sheet, x: -(W + 120), duration: 520, ease: "Cubic.easeOut", onUpdate: draw });
  sheet.destroy();
  lines.destroy();
}
