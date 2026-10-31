// What makes a district feel alive and a little wrong: weather and drifting life for each place, birds crossing
// the sky, a soft vignette, and while the law is missing, glitch tears and scan lines that grow stronger the
// closer Smudge gets to the crime scene.
import Phaser from "phaser";
import { W, H } from "../consts";
import { sfx } from "../audio";
import { makePixel, makeGlow } from "./fx";

type Weather = (scene: Phaser.Scene, width: number) => void;

const rain: Weather = (scene) => {
  scene.add.particles(0, 0, "px", {
    x: { min: -40, max: W + 40 }, y: -10, speedY: { min: 260, max: 320 }, speedX: -60, lifespan: 1200,
    scaleY: { min: 5, max: 8 }, scaleX: 1, alpha: { min: 0.15, max: 0.35 }, tint: 0xa8c0e8, frequency: 18, quantity: 2,
  }).setScrollFactor(0).setDepth(860);
};

const snow: Weather = (scene) => {
  scene.add.particles(0, 0, "px", {
    x: { min: -20, max: W + 20 }, y: -6, speedY: { min: 12, max: 26 }, speedX: { min: -10, max: 6 }, lifespan: 12000,
    scale: { min: 1, max: 2 }, alpha: { min: 0.5, max: 0.9 }, tint: 0xffffff, frequency: 90, quantity: 1, advance: 8000,
  }).setScrollFactor(0.4, 0).setDepth(860);
};

const motes = (tint: number, rise: number, freq = 200): Weather => (scene, width) => {
  scene.add.particles(0, 0, "px", {
    x: { min: 0, max: width }, y: { min: 120, max: 240 }, speedY: { min: rise - 6, max: rise + 4 }, speedX: { min: -5, max: 5 },
    lifespan: { min: 2500, max: 5000 }, alpha: { values: [0, 0.8, 0] }, scale: { min: 1, max: 1.6 }, tint,
    frequency: freq, quantity: 1, blendMode: Phaser.BlendModes.ADD, advance: 4000,
  }).setDepth(855);
};

const glints = (tint: number, y0: number, y1: number): Weather => (scene, width) => {
  scene.add.particles(0, 0, "px", {
    x: { min: 0, max: width }, y: { min: y0, max: y1 }, lifespan: 600, scale: { values: [0, 2, 0] }, alpha: 0.9, tint,
    frequency: 110, quantity: 1, blendMode: Phaser.BlendModes.ADD,
  }).setDepth(2);
};

const wind: Weather = (scene, width) => {
  scene.add.particles(0, 0, "px", {
    x: -20, y: { min: 60, max: 250 }, speedX: { min: 220, max: 320 }, lifespan: (width + 60) / 0.26, scaleX: { min: 6, max: 14 },
    alpha: { min: 0.08, max: 0.2 }, tint: 0xfff2d0, frequency: 220, quantity: 1,
  }).setDepth(855);
};

const bubbles: Weather = (scene, width) => {
  if (!scene.textures.exists("bubble")) {
    const g = scene.make.graphics({}, false);
    g.lineStyle(1, 0xffffff, 0.9).strokeCircle(4, 4, 3).fillStyle(0xffffff, 0.8).fillRect(2, 2, 1, 1);
    g.generateTexture("bubble", 8, 8);
    g.destroy();
  }
  scene.add.particles(0, 0, "bubble", {
    x: { min: 0, max: width }, y: 250, speedY: { min: -26, max: -14 }, speedX: { min: -8, max: 8 }, lifespan: 7000,
    scale: { min: 0.5, max: 1.1 }, alpha: { values: [0, 0.7, 0.7, 0] }, frequency: 650, quantity: 1, advance: 6000,
  }).setDepth(855);
};

const mist: Weather = (scene, width) => {
  makeGlow(scene, "glow64", 64);
  scene.add.particles(0, 0, "glow64", {
    x: { min: 0, max: width }, y: { min: 170, max: 250 }, speedX: { min: 4, max: 10 }, lifespan: 14000,
    scaleX: { min: 2, max: 3.5 }, scaleY: { min: 0.5, max: 0.8 }, alpha: { values: [0, 0.12, 0] }, tint: 0xcfe4ff,
    frequency: 1200, quantity: 1, advance: 12000,
  }).setDepth(856);
};

const WEATHER: Record<string, Weather[]> = {
  density: [glints(0xfff3c4, 205, 250), motes(0xfff0b0, -6, 400)],
  motion: [wind, motes(0xe8c48a, -2, 300)],
  sound: [rain],
  heights: [motes(0xfff4b8, -4, 260)],
  refraction: [mist, glints(0xe4f2ff, 200, 250)],
  ohm: [motes(0x9ad8ff, -14, 180)],
  heat: [snow, motes(0xffffff, -18, 500)],
  acids: [bubbles],
  power: [motes(0xffa04a, -20, 220)],
};
const BIRDS = new Set(["density", "heights", "refraction", "motion"]);

/** Dresses a district. Call update() every frame with Smudge's x and the crime scene's x (world). */
export function atmosphere(scene: Phaser.Scene, kit: string, width: number, bgKey: string, restored: boolean) {
  makePixel(scene);
  vignette(scene);
  for (const w of WEATHER[kit] ?? []) w(scene, width);
  if (BIRDS.has(kit)) birds(scene, width);
  if (restored) return { update: (_x: number, _stage: number) => {} };

  // the missing law shows: scan lines and torn slices of the backdrop
  scanTexture(scene);
  const scan = scene.add.tileSprite(0, 0, W, H, "scan").setOrigin(0).setScrollFactor(0).setDepth(870).setAlpha(0.05);
  let heat = 0;
  let next = 800;
  return {
    update(x: number, stageX: number, dtMs = 16) {
      heat = Phaser.Math.Clamp(1 - Math.abs(x - stageX) / 360, 0, 1);
      scan.setAlpha(0.04 + heat * 0.12);
      scan.tilePositionY -= dtMs * 0.01;
      next -= dtMs;
      if (next > 0) return;
      next = Phaser.Math.Between(2600, 5200) * (1 - heat * 0.8);
      tear(scene, bgKey, width, heat);
      if (heat > 0.55 && Math.random() < 0.6) sfx("zap");
    },
  };
}

function tear(scene: Phaser.Scene, bgKey: string, width: number, heat: number) {
  const n = 1 + Math.round(heat * 2);
  for (let i = 0; i < n; i++) {
    const y = Phaser.Math.Between(20, 250), h = Phaser.Math.Between(2, 6 + Math.round(heat * 10));
    const dx = Phaser.Math.Between(3, 6 + Math.round(heat * 10)) * (Math.random() < 0.5 ? -1 : 1);
    const slice = scene.add.image(dx, 0, bgKey).setOrigin(0).setCrop(0, y, width, h).setDepth(1);
    const ghost = scene.add.image(-dx * 0.6, 0, bgKey).setOrigin(0).setCrop(0, y, width, h).setDepth(1)
      .setTint(i % 2 ? 0xff4fd8 : 0x4ff0ff).setAlpha(0.45).setBlendMode(Phaser.BlendModes.ADD);
    scene.time.delayedCall(Phaser.Math.Between(60, 140), () => { slice.destroy(); ghost.destroy(); });
  }
}

function scanTexture(scene: Phaser.Scene) {
  if (scene.textures.exists("scan")) return;
  const g = scene.make.graphics({}, false);
  g.fillStyle(0x000000, 1).fillRect(0, 0, 4, 1);
  g.generateTexture("scan", 4, 3);
  g.destroy();
}

/** Darkened corners, drawn once into a canvas texture. */
export function vignette(scene: Phaser.Scene, alpha = 0.55) {
  if (!scene.textures.exists("vignette")) {
    const t = scene.textures.createCanvas("vignette", W, H)!;
    const ctx = t.getContext();
    const g = ctx.createRadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, W * 0.62);
    g.addColorStop(0, "rgba(5,6,15,0)");
    g.addColorStop(1, "rgba(5,6,15,1)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
    t.refresh();
  }
  return scene.add.image(0, 0, "vignette").setOrigin(0).setScrollFactor(0).setDepth(865).setAlpha(alpha);
}

/** A loose flock crossing the sky now and then. */
function birds(scene: Phaser.Scene, width: number) {
  if (!scene.textures.exists("bird")) {
    const g = scene.make.graphics({}, false);
    g.fillStyle(0x1a1d2e, 1).fillRect(0, 0, 2, 1).fillRect(2, 1, 1, 1).fillRect(3, 0, 2, 1);
    g.generateTexture("bird", 5, 2);
    g.destroy();
  }
  const fly = () => {
    const n = Phaser.Math.Between(2, 5), y = Phaser.Math.Between(24, 80), dir = Math.random() < 0.5 ? 1 : -1;
    for (let i = 0; i < n; i++) {
      const b = scene.add.image(dir > 0 ? -20 - i * 9 : width + 20 + i * 9, y + Phaser.Math.Between(-6, 6), "bird").setDepth(3).setScale(1.4);
      scene.tweens.add({ targets: b, scaleY: 0.4, duration: 180, yoyo: true, repeat: -1, delay: i * 60 });
      scene.tweens.add({ targets: b, x: dir > 0 ? width + 40 : -40, y: b.y - Phaser.Math.Between(4, 20), duration: Phaser.Math.Between(9000, 13000),
        onComplete: () => b.destroy() });
    }
    scene.time.delayedCall(Phaser.Math.Between(9000, 18000), fly);
  };
  scene.time.delayedCall(Phaser.Math.Between(1500, 5000), fly);
}
