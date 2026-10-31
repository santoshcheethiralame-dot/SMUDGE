import Phaser from "phaser";
import { FONT, DISPLAY, W, H } from "../consts";
import { CASES } from "../cases";
import { loadGenerated } from "../cases/generated";

const FOOT_ANIMS = ["foot_idle", "foot_talk", "foot_pop", "foot_worried", "foot_spin"];
const FOOT_META: Record<string, { frames: number; fps: number; loop: boolean }> = {
  foot_idle: { frames: 8, fps: 6, loop: true },
  foot_talk: { frames: 8, fps: 10, loop: true },
  foot_pop: { frames: 8, fps: 12, loop: false },
  foot_worried: { frames: 8, fps: 10, loop: true },
  foot_spin: { frames: 8, fps: 14, loop: false },
};
const DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"];
// every case folder in src/cases says what art it needs
const SUSPECTS: Record<string, string> = Object.fromEntries(
  Object.values(CASES).flatMap((c) => c.assets.suspects.map((sid) => [sid, c.assets.folder])));
const SUSPECT_ANIMS: Record<string, { frames: number; fps: number; loop: boolean }> = {
  idle: { frames: 8, fps: 6, loop: true }, talk: { frames: 8, fps: 10, loop: true },
  nervous: { frames: 8, fps: 12, loop: true }, shocked: { frames: 6, fps: 12, loop: false },
};

export class Boot extends Phaser.Scene {
  constructor() { super("Boot"); }

  preload() {
    const bar = this.add.rectangle(W / 2 - 60, H / 2, 0, 3, 0xc9302a).setOrigin(0, 0.5);
    this.add.rectangle(W / 2, H / 2, 122, 7).setStrokeStyle(1, 0x3d4c85);
    this.load.on("progress", (v: number) => { bar.width = 120 * v; });

    this.load.multiatlas("smudge", "assets/smudge/smudge_atlas.json", "assets/smudge/");
    this.load.json("smudge_anims", "assets/smudge/smudge_anims.json");
    this.load.spritesheet("smudge_portraits", "assets/smudge/portraits.png", { frameWidth: 96, frameHeight: 96 });
    this.load.spritesheet("foot_portraits", "assets/footnote/portraits.png", { frameWidth: 96, frameHeight: 96 });
    for (const a of FOOT_ANIMS) this.load.spritesheet(a, `assets/footnote/${a}.png`, { frameWidth: 64, frameHeight: 64 });
    for (const bg of ["title", "prologue", "prologue_erased", "hq", "nib", "eraser"]) this.load.image(bg, `assets/bg/${bg}.png`);
    // the casebook and its pop-ups, rendered by art/world/build_casebook.py
    for (const k of ["book", ...Array.from({ length: 10 }, (_, i) => `pop${i + 1}`)]) this.load.image(`map_${k}`, `assets/map/map_${k}.png`);
    // shared lab props, rendered by art/world/build_instruments.py
    for (const k of ["phone", "dial", "hub", "knob", "thermo", "protractor46", "tube", "dropper", "cylinder",
      "balance", "crate", "tub", "ingot", "crown", "die1", "die2", "die3", "die4", "die5", "die6"]) this.load.image(`lab_${k}`, `assets/lab/lab_${k}.png`);
    for (const c of Object.values(CASES)) for (const k of c.assets.images) this.load.image(k, `assets/${c.assets.folder}/${k}.png`);
    for (const [who, dir] of Object.entries(SUSPECTS)) {
      for (const a of Object.keys(SUSPECT_ANIMS)) this.load.spritesheet(`${who}_${a}`, `assets/${dir}/${who}_${a}.png`, { frameWidth: 64, frameHeight: 64 });
      this.load.spritesheet(`${who}_portraits`, `assets/${dir}/${who}_portraits.png`, { frameWidth: 96, frameHeight: 96 });
    }
  }

  async create() {
    this.anims.fromJSON(this.cache.json.get("smudge_anims"));
    for (const a of FOOT_ANIMS) {
      const m = FOOT_META[a];
      DIRS.forEach((d, r) => {
        this.anims.create({
          key: `${a}_${d}`, frameRate: m.fps, repeat: m.loop ? -1 : 0,
          frames: this.anims.generateFrameNumbers(a, { start: r * m.frames, end: r * m.frames + m.frames - 1 }),
        });
      });
    }
    for (const who of Object.keys(SUSPECTS)) {
      for (const [a, m] of Object.entries(SUSPECT_ANIMS)) {
        DIRS.forEach((d, r) => {
          this.anims.create({
            key: `${who}_${a}_${d}`, frameRate: m.fps, repeat: m.loop ? -1 : 0,
            frames: this.anims.generateFrameNumbers(`${who}_${a}`, { start: r * m.frames, end: r * m.frames + m.frames - 1 }),
          });
        });
      }
    }
    try {
      await Promise.all([document.fonts.load(`10px ${FONT}`), document.fonts.load(`10px "Smudge Digits"`, "023456789"), document.fonts.load(`40px ${DISPLAY}`)]);
    } catch { /* fonts are a nicety; fall back silently */ }
    // ?case=<kit> drops straight into a district; ?scene=<Scene> into any scene
    const q = new URLSearchParams(location.search);
    await loadGenerated();          // cases the Author agents wrote, on the art of the case each one borrows
    const kit = q.get("case");
    if (kit && CASES[kit]) this.scene.start("District", { kit, from: "hq" });
    else this.scene.start(q.get("scene") || "Title", { kit: kit ?? undefined });
  }
}
