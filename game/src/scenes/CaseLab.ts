// The shared lab: runs a case's lab steps (src/cases/<kit>/index.ts, labSteps) with the instruments in
// src/systems/lab/instruments, then shows the evidence card the server's kit wrote, and goes back to the district.
import Phaser from "phaser";
import { W, H, FONT, DISPLAY } from "../consts";
import { Dialogue } from "../systems/dialogue";
import { makePixel, tween } from "../systems/fx";
import { sfx, themeFor, layer, ambience, sting } from "../audio";
import { inkIn, inkOut } from "../systems/transition";
import { shake } from "../systems/juice";
import { vignette } from "../systems/atmosphere";
import { api } from "../api";
import { progress } from "../state";
import { CASES } from "../cases";
import type { Instrument, LabCtx } from "../systems/lab/types";

const INSTRUMENTS: Record<string, Instrument> = {};
for (const m of Object.values(import.meta.glob<Instrument>("../systems/lab/instruments/*.ts", { eager: true }))) INSTRUMENTS[m.kind] = m;

export class CaseLab extends Phaser.Scene {
  constructor() { super("CaseLab"); }

  async create(data: { kit?: string }) {
    const content = CASES[data?.kit ?? progress.kit];
    makePixel(this);
    this.add.image(0, 0, "bench").setOrigin(0, 0);
    vignette(this, 0.45);
    themeFor("lab");
    layer(2);
    ambience("lab");
    void inkIn(this);
    this.add.text(W - 8, H - 8, `${content.chapter} · lab`, { fontFamily: FONT, fontSize: "10px", color: "#9AA6C8" }).setOrigin(1, 1);
    const ctx: LabCtx = { scene: this, dlg: new Dialogue(this), c: api.current!, measured: {} };
    for (const step of content.labSteps ?? []) {
      const ins = INSTRUMENTS[step.kind];
      if (!ins) throw new Error(`No instrument "${step.kind}" in src/systems/lab/instruments`);
      await ins.run(ctx, step);
    }
    const r = ctx.result!;
    progress.labDone = true;
    progress.evidence = { label: r.evidence!, badge: r.card!.badge, say: r.card!.say };
    await this.card(ctx, r.card!.title, r.card!.line);
    await inkOut(this);
    this.scene.start("District", { kit: content.kit, from: "lab" });
  }

  private async card(ctx: LabCtx, title: string, line: string) {
    const card = this.add.container(W / 2, H / 2).setDepth(1500).setScale(0.2).setAlpha(0);
    const bg = this.add.rectangle(0, 0, 280, 100, 0xf2e9cf).setStrokeStyle(2, 0x0e1938);
    const t1 = this.add.text(0, -34, "EVIDENCE", { fontFamily: FONT, fontSize: "9px", color: "#C9302A" }).setOrigin(0.5);
    const t2 = this.add.text(0, -10, title, { fontFamily: DISPLAY, fontSize: "18px", color: "#0E1938" }).setOrigin(0.5);
    const t3 = this.add.text(0, 16, line, { fontFamily: FONT, fontSize: "10px", color: "#55361A", align: "center", wordWrap: { width: 260 } })
      .setOrigin(0.5);
    card.add([bg, t1, t2, t3]);
    sting("evidence");
    // the card slaps down on the bench
    card.setScale(1.6).setAlpha(0).setAngle(6);
    await tween(this, { targets: card, scale: 1, alpha: 1, angle: -2, duration: 220, ease: "Quad.easeIn" });
    sfx("stamp");
    shake(this, 120, 0.006);
    const stamp = this.add.text(104, -30, "FILED", { fontFamily: DISPLAY, fontSize: "14px", color: "#C9302A" }).setOrigin(0.5).setAngle(14).setScale(2).setAlpha(0);
    card.add(stamp);
    this.time.delayedCall(380, () => { sfx("stamp"); this.tweens.add({ targets: stamp, scale: 1, alpha: 0.85, duration: 140, ease: "Quad.easeIn" }); });
    await ctx.dlg.play([
      { who: "smudge", expr: "smug", text: "That doesn't square with somebody's story." },
      { who: "foot", expr: "happy", text: "Evidence filed! Now: whose statement does it break?" },
    ]);
    card.destroy();
  }
}
