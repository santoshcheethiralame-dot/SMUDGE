import Phaser from "phaser";
import { W, FONT, FEET_ORIGIN, project } from "../consts";
import { Dialogue } from "../systems/dialogue";
import { makeGlow, makePixel, dust, wait, tween, playOnce, pageTurn } from "../systems/fx";
import { sfx, music, ambience } from "../audio";
import { api } from "../api";
import { progress } from "../state";

const C = { cu: 0, cv: 92 };
const P = (x: number, y: number, z: number) => project(x, y, z, C.cu, C.cv);

const SMUDGE_AT = P(-40, 0, 28);
const ASTERISK = P(93.5, 0, -50.5);
const FOOT_AT = P(60, 0, 8);
// the nib image is 210x190 with its tip at (47, 177)
const NIB_TIP = { x: 47 / 210, y: 177 / 190 };

export class Prologue extends Phaser.Scene {
  private dlg!: Dialogue;
  private skipped = false;
  constructor() { super("Prologue"); }

  create() {
    ambience("title");
    this.skipped = false;
    makeGlow(this, "glow64", 64);
    makePixel(this);
    this.cameras.main.fadeIn(700, 5, 6, 15);
    this.add.image(0, 0, "prologue").setOrigin(0, 0);
    const erased = this.add.image(0, 0, "prologue_erased").setOrigin(0, 0).setVisible(false);
    const lampGlow = this.add.image(60, 10, "glow64").setScale(4, 2.2).setBlendMode(Phaser.BlendModes.ADD).setTint(0xffb35a).setAlpha(0.22);
    this.tweens.add({ targets: lampGlow, alpha: 0.17, duration: 90, yoyo: true, repeat: -1, repeatDelay: 3100, ease: "Stepped" });
    dust(this, 0, 20, W, 160, 0xffe0a8, 30);
    this.dlg = new Dialogue(this);

    const skip = this.add.text(W - 8, 270 - 8, "Skip ▸▸", { fontFamily: FONT, fontSize: "9px", color: "#E9D9B4", backgroundColor: "#0E1938" })
      .setOrigin(1, 1).setPadding(4, 2, 4, 2).setDepth(2000).setInteractive({ useHandCursor: true });
    skip.on("pointerdown", (_p: any, _x: any, _y: any, e: any) => { e?.stopPropagation?.(); this.skipTo(); });

    this.run(erased);
  }

  private async skipTo() {
    if (this.skipped) return;
    this.skipped = true;
    this.cameras.main.fadeOut(300, 5, 6, 15);
    await wait(this, 320);
    this.toManor();
  }

  /** The prologue leads straight into the Midnight Fall, the case the ghost story sets up. */
  private toManor() {
    if (progress.kit !== "fall" || progress.solved) { progress.reset("fall"); api.current = null; }
    this.scene.start("District", { kit: "fall", from: "hq" });
  }

  private async run(erased: Phaser.GameObjects.Image) {
    const smudge = this.add.sprite(SMUDGE_AT.x, SMUDGE_AT.y, "smudge", "shapeshift_reform/S/0")
      .setOrigin(FEET_ORIGIN.x, FEET_ORIGIN.y).setVisible(false).setDepth(20);
    const shadow = this.add.ellipse(SMUDGE_AT.x, SMUDGE_AT.y - 1, 22, 5, 0x000000, 0.3).setVisible(false).setDepth(19);

    // the pen descends, wells up, and lets one drop go
    const nib = this.add.image(SMUDGE_AT.x + 6, -120, "nib").setOrigin(NIB_TIP.x, NIB_TIP.y).setDepth(30);
    await tween(this, { targets: nib, y: 118, duration: 1600, ease: "Sine.easeOut" });
    await wait(this, 300);
    const drop = this.add.ellipse(nib.x, nib.y + 1, 2, 2, 0x0b1433).setDepth(29);
    await tween(this, { targets: drop, scaleX: 2.4, scaleY: 3, duration: 900, ease: "Sine.easeIn" });
    if (this.skipped) return;
    await tween(this, { targets: drop, y: SMUDGE_AT.y - 3, scaleY: 4, duration: 520, ease: "Quad.easeIn" });
    drop.destroy();
    sfx("plop");
    this.cameras.main.shake(120, 0.004);
    const splat = this.add.ellipse(SMUDGE_AT.x, SMUDGE_AT.y - 2, 4, 2, 0x0b1433).setDepth(18);
    await tween(this, { targets: splat, scaleX: 7, scaleY: 3.5, duration: 160, ease: "Back.easeOut" });
    this.tweens.add({ targets: nib, y: -140, duration: 1400, ease: "Sine.easeIn", delay: 400 });
    splat.destroy();
    smudge.setVisible(true);
    shadow.setVisible(true);
    await playOnce(smudge, "shapeshift_reform_S");
    smudge.play("idle_S");
    await wait(this, 500);
    await playOnce(smudge, "idle_fidget_S");
    smudge.play("idle_S");
    if (this.skipped) return;

    await this.dlg.play([
      { who: "smudge", expr: "surprised", text: "...Huh. I'm a blot." },
      { who: "smudge", expr: "thinking", text: "A blot in a hat. On page one hundred and thirty-seven." },
    ]);

    // Footnote peels itself off the page
    const patch = this.paperPatch(ASTERISK.x, ASTERISK.y);
    const foot = this.add.sprite(ASTERISK.x, ASTERISK.y + 2, "foot_pop", 0).setOrigin(FEET_ORIGIN.x, FEET_ORIGIN.y).setDepth(21);
    patch.setVisible(true);
    sfx("pop");
    await playOnce(foot, "foot_pop_S");
    foot.play("foot_idle_S");
    await tween(this, { targets: foot, x: FOOT_AT.x, y: FOOT_AT.y, duration: 900, ease: "Sine.easeInOut" });
    smudge.play("idle_SE");
    if (this.skipped) return;

    await this.dlg.play([
      { who: "foot", expr: "happy", text: "Psst! Over here! I'm Footnote. I live at the bottom of things." },
      { who: "foot", expr: "neutral", text: "You dripped right onto the chapter on falling. Gravity! It's the one that explains why things drop." },
      { who: "smudge", expr: "smug", text: "Riveting." },
    ]);

    // the Tower Ghost sweeps across the page, and the law fades out behind it
    music("tense");
    sfx("rumble");
    this.cameras.main.shake(1800, 0.006);
    await wait(this, 500);
    smudge.play("surprised_E");
    foot.play("foot_worried_S");
    // sheet_ghost.png is two 32 px frames; frame "0" is the ghost with its eyes
    const tex = this.textures.get("sheet_ghost");
    if (!tex.has("0")) { tex.add("0", 0, 0, 0, 32, 32); tex.add("1", 0, 32, 0, 32, 32); }
    const ghost = this.add.image(W + 140, 226, "sheet_ghost", "0").setOrigin(0.5, 0.92).setScale(4).setDepth(25)
      .setTint(0xc8dcff).setAlpha(0.9);
    const halo = this.add.image(ghost.x, 180, "glow64").setScale(3.2).setBlendMode(Phaser.BlendModes.ADD).setTint(0x6a9aff).setAlpha(0.35).setDepth(24);
    const crumbs = this.add.particles(0, 0, "px", {
      speedX: { min: 10, max: 50 }, speedY: { min: -30, max: -5 },
      lifespan: { min: 600, max: 1200 }, tint: [0xa8c8ff, 0x6a9aff, 0xe8f0ff], alpha: { start: 0.8, end: 0 },
      blendMode: Phaser.BlendModes.ADD, quantity: 2, frequency: 30, emitting: false,
    }).setDepth(26);
    const mask = this.make.graphics({ x: 0, y: 0 }, false);
    erased.setVisible(true).setMask(mask.createGeometryMask());
    sfx("whoosh");
    crumbs.start();
    await tween(this, {
      targets: ghost, x: -150, duration: 3200, ease: "Sine.easeInOut",
      onUpdate: () => {
        const ex = ghost.x;
        mask.clear().fillStyle(0xffffff).fillRect(Math.max(0, ex), 150, W, 120);
        crumbs.setPosition(ghost.x + 50, 200 + Math.random() * 40);
        ghost.y = 216 + Math.sin(ghost.x * 0.04) * 8;
        ghost.angle = Math.sin(ghost.x * 0.06) * 6;
        halo.setPosition(ghost.x, ghost.y - 64);
      },
    });
    crumbs.stop();
    halo.destroy();
    erased.clearMask(true);
    patch.setVisible(false);
    music("night");
    smudge.play("idle_E");
    if (this.skipped) return;

    await this.dlg.play([
      { who: "foot", expr: "worried", text: "No. No no no. The Tower Ghost! It just wiped the law of falling off the page!" },
      { who: "smudge", expr: "thinking", text: "Ghosts aren't real." },
      { who: "foot", expr: "worried", text: "Tell that to Hollowmere Manor. Someone fell from the clock tower tonight, and they all swear the ghost did it." },
      { who: "smudge", expr: "determined", text: "Then somebody has to find out what really happened." },
      { who: "foot", expr: "happy", text: "Somebody in a detective hat, maybe? Come on. The manor is just down the gutter." },
    ]);
    if (this.skipped) return;

    // off they go, east
    smudge.play("walk_E");
    foot.play("foot_idle_E");
    this.tweens.add({ targets: foot, x: W + 40, duration: 2200, ease: "Sine.easeIn", delay: 200 });
    this.tweens.add({ targets: shadow, x: W + 20, duration: 2600 });
    await tween(this, { targets: smudge, x: W + 20, duration: 2600 });
    await pageTurn(this, () => this.toManor());
  }

  /** Cover the printed asterisk with the strip of page just to its right (ruled lines and all). */
  private paperPatch(x: number, y: number) {
    const w = 22, h = 18, shift = -26;                // blank page to the right (the left holds the formula)
    return this.add.image(shift, 0, "prologue").setOrigin(0, 0)
      .setCrop(Math.round(x - w / 2 - shift), Math.round(y - h + 2), w, h).setDepth(2).setVisible(false);
  }
}
