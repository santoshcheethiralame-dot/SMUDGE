// The Midnight Fall's cold open (16 s): rain, the clock strikes twelve, lightning shows a figure on the tower,
// a cry, a thud, black, then the title card. Three short caption beats (place, the fall, "what is this place?"). Any key or click skips it.
// It runs on top of a paused District and resumes it when done (see cases/fall/index.ts).
import Phaser from "phaser";
import * as Tone from "tone";
import { W, H, Z, DISPLAY } from "../consts";
import { makePixel } from "../systems/fx";
import { sfx } from "../audio";

let played = false;
/** True once the cold open has played (or been skipped) in this page load. */
export const coldOpenDone = () => played;

// bx, top: the clock in manor_glitch (x 510, y 27) and on screen at 2x; TILT: how far below it the shot starts
const TOWER = { x: 340, bx: 510, top: 54 };
const TILT = 80;

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
    // the manor's own tower at 2x, held in shadow; the shot tilts up from the courtyard to the clock
    const g = this.add.container(0, -TILT).setDepth(2);
    g.add(this.add.image(TOWER.x - TOWER.bx * 2, 0, "manor_glitch").setOrigin(0).setScale(2));
    const shade = this.add.rectangle(0, 0, W, H, 0x03040c, 0.55).setOrigin(0).setDepth(2.5);
    const sky = this.add.rectangle(0, 0, W, H, 0xb8c4dc).setOrigin(0).setAlpha(0).setDepth(2.6).setBlendMode(Phaser.BlendModes.ADD);
    const face = this.add.circle(TOWER.x, TOWER.top, 22, 0xf0e6bc, 0.25).setBlendMode(Phaser.BlendModes.ADD);
    // the figure, a silhouette on the clock ledge: no balcony, so nobody knows which
    const figure = this.add.graphics().setAlpha(0);
    figure.fillStyle(0x03040c).fillRect(TOWER.x - 5, TOWER.top + 4, 10, 22).fillCircle(TOWER.x, TOWER.top - 1, 6);
    g.add([face, figure]);
    this.tweens.add({ targets: g, y: 0, duration: 8600, ease: "Sine.easeInOut" });

    this.add.particles(0, 0, "px", {
      x: { min: 0, max: W + 40 }, y: -10, speedY: { min: 320, max: 400 }, speedX: -50, lifespan: 800, frequency: 16, quantity: 2,
      alpha: { start: 0.5, end: 0.1 }, tint: 0x8fa4cc, scaleY: 4,
    }).setDepth(6);

    const flash = (ms: number) => {
      sky.setAlpha(0.35);
      shade.setAlpha(0);
      this.tweens.add({ targets: sky, alpha: 0, duration: ms, ease: "Quad.easeOut" });
      this.tweens.add({ targets: shade, alpha: 0.55, duration: ms * 1.6, ease: "Quad.easeIn" });
    };

    // the timeline, in ms from the start
    const at = (ms: number, fn: () => void) => this.time.delayedCall(ms, () => { if (!this.over) fn(); });
    at(800, () => this.tweens.add({ targets: face, alpha: 0.5, duration: 1200 }));
    for (let n = 0; n < 12; n++) at(1600 + n * 600, () => { this.bell(n === 11); this.tweens.add({ targets: face, scale: 1.12, duration: 90, yoyo: true }); });
    at(9200, () => { figure.setAlpha(1); flash(420); sfx("rumble"); });
    at(9800, () => figure.setAlpha(0));
    at(10600, () => this.cry());
    at(12100, () => { sfx("thunk"); this.cameras.main.shake(120, 0.01); });
    at(12400, () => this.tweens.add({ targets: g, alpha: 0, duration: 200 }));
    at(13000, () => {
      const title = this.add.text(W / 2, H / 2, "THE MIDNIGHT FALL", { fontFamily: DISPLAY, fontSize: "26px", color: "#F2E9CF" })
        .setOrigin(0.5).setAlpha(0).setDepth(20);
      this.tweens.add({ targets: title, alpha: 1, duration: 900 });
    });
    // three caption beats, under 40 words: the place and mood, the strange fall, then the question. They hint at nothing about the lie.
    const caption = (ms: number, text: string, hold: number) => at(ms, () => {
      const t = this.add.text(W / 2, H - 40, text, { fontFamily: DISPLAY, fontSize: "11px", color: "#C9D2E8", align: "center", wordWrap: { width: W - 60 } })
        .setOrigin(0.5).setAlpha(0).setDepth(20);
      this.tweens.add({ targets: t, alpha: 1, duration: 500, yoyo: true, hold, onComplete: () => t.destroy() });
    });
    caption(900, "Midnight. Rain. The old clock tower.", 2200);
    caption(10300, "Someone fell. It was not a normal fall.", 1100);
    caption(13900, "What is this place?", 900);
    at(16000, () => this.finish());

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
