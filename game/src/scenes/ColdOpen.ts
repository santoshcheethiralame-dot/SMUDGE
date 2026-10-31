// The Midnight Fall's cold open (15 s): rain, the clock strikes twelve, lightning shows a figure on the tower,
// a cry, a thud, black, then the title card. No text until the card. Any key or click skips it.
// It runs on top of a paused District and resumes it when done (see cases/fall/index.ts).
import Phaser from "phaser";
import * as Tone from "tone";
import { W, H, Z, DISPLAY } from "../consts";
import { makePixel } from "../systems/fx";
import { sfx } from "../audio";

let played = false;
/** True once the cold open has played (or been skipped) in this page load. */
export const coldOpenDone = () => played;

const TOWER = { x: 340, top: 46 };

export class ColdOpen extends Phaser.Scene {
  private synths: Tone.ToneAudioNode[] = [];
  private over = false;

  constructor() { super("ColdOpen"); }

  create() {
    // scenes added after boot do not get the world zoom, so set it here
    this.cameras.main.setOrigin(0, 0).setZoom(Z);
    this.over = false;
    makePixel(this);
    this.add.rectangle(0, 0, W, H, 0x03040c).setOrigin(0).setDepth(0);
    const sky = this.add.rectangle(0, 0, W, H, 0xb8c4dc).setOrigin(0).setAlpha(0).setDepth(1);

    // the tower, a dark shape; the clock face glows a little
    const g = this.add.graphics().setDepth(2);
    g.fillStyle(0x0a0d22).fillRect(TOWER.x - 34, TOWER.top, 68, H - TOWER.top);
    g.fillTriangle(TOWER.x - 40, TOWER.top, TOWER.x, TOWER.top - 40, TOWER.x + 40, TOWER.top);
    const face = this.add.circle(TOWER.x, TOWER.top + 24, 15, 0xf0e6bc, 0.55).setDepth(3);
    this.add.graphics().setDepth(3).lineStyle(1, 0x0a0d22).lineBetween(TOWER.x, TOWER.top + 24, TOWER.x, TOWER.top + 12);
    // the figure on a balcony: small, dark, and no balcony drawn, so nobody knows which
    const figure = this.add.graphics().setDepth(4).setAlpha(0);
    figure.fillStyle(0x03040c).fillRect(TOWER.x - 4, 138, 8, 20).fillCircle(TOWER.x, 134, 5);

    this.add.particles(0, 0, "px", {
      x: { min: 0, max: W + 40 }, y: -10, speedY: { min: 320, max: 400 }, speedX: -50, lifespan: 800, frequency: 16, quantity: 2,
      alpha: { start: 0.5, end: 0.1 }, tint: 0x8fa4cc, scaleY: 4,
    }).setDepth(6);

    const flash = (ms: number) => {
      sky.setAlpha(0.92);
      this.tweens.add({ targets: sky, alpha: 0, duration: ms, ease: "Quad.easeOut" });
    };

    // the timeline, in ms from the start
    const at = (ms: number, fn: () => void) => this.time.delayedCall(ms, () => { if (!this.over) fn(); });
    at(800, () => this.tweens.add({ targets: face, alpha: 0.85, duration: 1200 }));
    for (let n = 0; n < 12; n++) at(1600 + n * 600, () => { this.bell(n === 11); this.tweens.add({ targets: face, scale: 1.12, duration: 90, yoyo: true }); });
    at(9200, () => { figure.setAlpha(1); flash(420); sfx("rumble"); });
    at(9800, () => figure.setAlpha(0));
    at(10600, () => this.cry());
    at(12100, () => { sfx("thunk"); this.cameras.main.shake(120, 0.01); });
    at(12400, () => this.tweens.add({ targets: [face, g], alpha: 0, duration: 200 }));
    at(13000, () => {
      const title = this.add.text(W / 2, H / 2, "THE MIDNIGHT FALL", { fontFamily: DISPLAY, fontSize: "26px", color: "#F2E9CF" })
        .setOrigin(0.5).setAlpha(0).setDepth(20);
      this.tweens.add({ targets: title, alpha: 1, duration: 900 });
    });
    at(15200, () => this.finish());

    this.input.keyboard?.once("keydown", () => this.finish());
    this.input.once("pointerdown", () => this.finish());
  }

  /** A struck bell: an FM clang that rings long. The last of the twelve is a little louder. */
  private bell(last: boolean) {
    if (Tone.getContext().state !== "running") return;     // audio is locked until the first click or key
    try {
      const s = new Tone.FMSynth({ harmonicity: 5.1, modulationIndex: 6, envelope: { attack: 0.002, decay: 2.2, sustain: 0, release: 1 },
        modulationEnvelope: { attack: 0.002, decay: 1.2, sustain: 0, release: 0.5 } }).toDestination();
      s.volume.value = last ? -8 : -13;
      s.triggerAttackRelease("A3", 0.4);
      this.synths.push(s);
    } catch { /* sound is a bonus */ }
  }

  /** A thin cry that rises. */
  private cry() {
    if (Tone.getContext().state !== "running") return;
    try {
      const s = new Tone.Synth({ oscillator: { type: "sine" }, portamento: 0.4, envelope: { attack: 0.04, decay: 0.1, sustain: 0.8, release: 0.5 } }).toDestination();
      s.volume.value = -16;
      s.triggerAttack("D5");
      setTimeout(() => { try { s.setNote("B5"); } catch { /* gone */ } }, 120);
      setTimeout(() => { try { s.triggerRelease(); } catch { /* gone */ } }, 900);
      this.synths.push(s);
    } catch { /* sound is a bonus */ }
  }

  private finish() {
    if (this.over) return;
    this.over = true;
    played = true;
    for (const s of this.synths) setTimeout(() => { try { s.dispose(); } catch { /* already gone */ } }, 3000);
    this.cameras.main.fadeOut(350, 5, 6, 15);
    this.cameras.main.once("camerafadeoutcomplete", () => {
      this.scene.resume("District");
      this.scene.stop();
    });
  }
}
