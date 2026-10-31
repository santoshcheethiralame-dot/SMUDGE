import Phaser from "phaser";
import { W, H, FONT, DISPLAY, FEET_ORIGIN, project } from "../consts";
import { makeGlow, makeCone, dust, wait } from "../systems/fx";
import { startAudio, sfx, themeFor, layer, ambience } from "../audio";

const C = { cu: 0, cv: 100 };
const P = (x: number, y: number, z: number) => project(x, y, z, C.cu, C.cv);

export class Title extends Phaser.Scene {
  private leaving = false;
  constructor() { super("Title"); }

  create() {
    this.leaving = false;
    themeFor("night");
    layer(0);
    ambience("title");
    this.cameras.main.fadeIn(900, 5, 6, 15);
    this.add.image(0, 0, "title").setOrigin(0, 0);
    makeGlow(this, "glow64", 64);
    makeCone(this, "cone", 180, 200);

    // lamp: a banded light cone with a slow flicker, plus a warm pool on the page
    const lampAt = P(-150, 140, 32);
    const cone = this.add.image(lampAt.x, lampAt.y, "cone").setOrigin(0.5, 0).setBlendMode(Phaser.BlendModes.ADD)
      .setTint(0xffc46b).setAlpha(0.32).setRotation(-0.62).setDepth(5);
    const pool = this.add.image(P(-40, 6, 20).x, P(-40, 6, 20).y, "glow64").setScale(3.2, 0.9).setBlendMode(Phaser.BlendModes.ADD)
      .setTint(0xffb35a).setAlpha(0.25).setDepth(4);
    this.tweens.add({ targets: [cone, pool], alpha: "*=0.86", duration: 90, yoyo: true, repeat: -1, repeatDelay: 2600, ease: "Stepped" });

    // the lighthouse turns: its beam sweeps by squashing through zero
    const lantern = P(-118, 101, 18);
    const beam = this.add.image(lantern.x, lantern.y, "cone").setOrigin(0.5, 0).setScale(0.35, 1.4).setRotation(Math.PI / 2)
      .setBlendMode(Phaser.BlendModes.ADD).setTint(0xffe2a0).setAlpha(0.3).setDepth(6);
    this.tweens.add({ targets: beam, scaleX: { from: 0.35, to: -0.35 }, duration: 2200, yoyo: true, repeat: -1, ease: "Sine.easeInOut" });
    const lanternGlow = this.add.image(lantern.x, lantern.y, "glow64").setScale(0.5).setBlendMode(Phaser.BlendModes.ADD).setTint(0xffd27a).setAlpha(0.7).setDepth(6);
    this.tweens.add({ targets: lanternGlow, alpha: 0.35, duration: 1100, yoyo: true, repeat: -1 });

    // the resistor house's antenna blinks
    const ant = P(40, 100, 22);
    const antGlow = this.add.image(ant.x, ant.y, "glow64").setScale(0.28).setBlendMode(Phaser.BlendModes.ADD).setTint(0x7df9ff).setDepth(6);
    this.tweens.add({ targets: antGlow, alpha: 0.15, duration: 600, yoyo: true, repeat: -1, repeatDelay: 900 });

    dust(this, 70, 110, 220, 130, 0xffe0a8, 40);

    // Smudge stands on the open page, Footnote bobbing beside
    const s = P(-6, 5, 38);
    this.add.sprite(s.x, s.y, "smudge", "idle/S/0").setOrigin(FEET_ORIGIN.x, FEET_ORIGIN.y).play("idle_S").setDepth(10);
    const shadow = this.add.ellipse(s.x, s.y - 1, 22, 5, 0x000000, 0.35).setDepth(9);
    void shadow;
    const f = P(20, 5, 44);
    this.add.sprite(f.x, f.y, "foot_idle", 0).setOrigin(FEET_ORIGIN.x, FEET_ORIGIN.y).play("foot_idle_S").setDepth(10);

    // logo
    const logo = this.add.text(W / 2, 44, "Smudge", {
      fontFamily: DISPLAY, fontSize: "58px", color: "#F6E7C6", stroke: "#0E1938", strokeThickness: 8,
      shadow: { offsetX: 3, offsetY: 4, color: "#000000", blur: 0, fill: true, stroke: true },
    }).setOrigin(0.5).setDepth(20);
    const underline = this.add.graphics().setDepth(20);
    underline.lineStyle(4, 0xc9302a, 1);
    underline.beginPath();
    underline.moveTo(W / 2 - 92, 72);
    underline.lineTo(W / 2 + 10, 76);
    underline.lineTo(W / 2 + 96, 70);
    underline.strokePath();
    // ink drips off the logo, one at a time
    for (const dx of [-60, 18, 70]) {
      const drip = this.add.ellipse(W / 2 + dx, 64, 3, 4, 0x0e1938).setDepth(19);
      this.tweens.add({ targets: drip, y: 112, scaleY: 1.6, alpha: 0, duration: 1600, repeat: -1, delay: Math.random() * 3000, repeatDelay: 2500 + Math.random() * 3000, ease: "Quad.easeIn" });
    }
    this.add.text(W / 2, 86, "and the Case of the Missing Laws", { fontFamily: FONT, fontSize: "11px", color: "#E9D9B4" })
      .setOrigin(0.5).setDepth(20);
    const prompt = this.add.text(W / 2, 106, "Tap to open the book", { fontFamily: FONT, fontSize: "10px", color: "#FFC46B" })
      .setOrigin(0.5).setDepth(20);
    this.tweens.add({ targets: prompt, alpha: 0.25, duration: 800, yoyo: true, repeat: -1 });
    this.add.text(W - 6, H - 6, "agentathon build", { fontFamily: FONT, fontSize: "10px", color: "#55607F" })
      .setOrigin(1, 1).setDepth(20);
    this.tweens.add({ targets: logo, y: 46, duration: 2400, yoyo: true, repeat: -1, ease: "Sine.easeInOut" });

    const go = () => this.begin(s.x, s.y);
    this.input.once("pointerdown", go);
    this.input.keyboard?.once("keydown", go);
  }

  private async begin(x: number, y: number) {
    if (this.leaving) return;
    this.leaving = true;
    await startAudio();
    sfx("chime");
    sfx("rise");
    layer(1);
    const cam = this.cameras.main;
    cam.pan(x, y - 20, 1400, "Sine.easeInOut");
    cam.zoomTo(3, 1400, "Cubic.easeIn");
    await wait(this, 900);
    cam.fadeOut(500, 5, 6, 15);
    await wait(this, 520);
    this.scene.start("Prologue");
  }
}
