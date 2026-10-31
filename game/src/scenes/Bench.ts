// Dev bench: try any lab instrument on sample data, no server needed. ?scene=Bench&kind=<instrument>
// (tape, protractor, gauge, dropper, tally, balance, stopwatch). Shows what it recorded when done.
import Phaser from "phaser";
import { W, FONT } from "../consts";
import { Dialogue } from "../systems/dialogue";
import { makePixel } from "../systems/fx";
import type { CaseData } from "../api";
import type { Instrument, LabCtx, LabStep } from "../systems/lab/types";

const INSTRUMENTS: Record<string, Instrument> = {};
for (const m of Object.values(import.meta.glob<Instrument>("../systems/lab/instruments/*.ts", { eager: true }))) INSTRUMENTS[m.kind] = m;

const hi = [{ who: "foot" as const, expr: "neutral", text: "Bench test." }];
const SAMPLES: Record<string, LabStep> = {
  tape: { kind: "tape", intro: hi, done: hi, title: "Shadows at noon (metres)", unit: "m", max: 12, record: "s",
    rows: () => [{ key: "pole", label: "Pole", length: 4.2, style: "shadow" }, { key: "tree", label: "Tree", length: 7.5, style: "bar" }, { key: "skid", label: "Skid", length: 9.9, style: "skid2" }] },
  protractor: { kind: "protractor", intro: hi, done: hi, record: "a",
    items: () => [{ key: "sun", label: "Sun's elevation", angle: 37, from: "ground" }, { key: "i", label: "Angle of incidence", angle: 40, from: "normal", side: "up" },
      { key: "r", label: "Angle of refraction", angle: 25, from: "normal", side: "down", other: 40 }] },
  gauge: { kind: "gauge", intro: hi, done: hi, record: "g",
    items: () => [{ key: "t", label: "Water temperature", value: 46, min: 0, max: 100, step: 2, unit: "°C", style: "thermo" },
      { key: "v", label: "Voltmeter", value: 4.5, min: 0, max: 10, step: 0.5, unit: "V", style: "dial", labelEvery: 2 }] },
  dropper: { kind: "dropper", intro: hi, done: hi, record: "ph",
    samples: () => [{ key: "a", label: "Bottle A", ph: 3 }, { key: "b", label: "Bottle B", ph: 7 }, { key: "c", label: "Bottle C", ph: 11 }] },
  tally: { kind: "tally", intro: hi, done: hi, record: "n", sets: () => [{ key: "red", label: "The red die", counts: [8, 9, 7, 10, 8, 18] }] },
  balance: { kind: "balance", intro: hi, done: hi, record: "m", unit: "kg",
    items: () => [{ key: "crate", label: "Crate", mass: 40 }, { key: "water", label: "Water", mass: 2, look: "tub" as const }] },
  stopwatch: { kind: "stopwatch", intro: hi, done: hi, record: "t", clips: () => [{ key: "x", label: "Storm video", seconds: 1.5, style: "flashboom" }] },
  lift: { kind: "stopwatch", intro: hi, done: hi, record: "t", clips: () => [{ key: "x", label: "Tower cam: the lift", seconds: 4, style: "rise" }] },
};

export class Bench extends Phaser.Scene {
  constructor() { super("Bench"); }

  async create() {
    makePixel(this);
    this.add.image(0, 0, "bench").setOrigin(0, 0);
    const kind = new URLSearchParams(location.search).get("kind") ?? "tape";
    const ctx: LabCtx = { scene: this, dlg: new Dialogue(this), c: {} as CaseData, measured: {} };
    (window as unknown as { benchCtx: LabCtx }).benchCtx = ctx;
    await INSTRUMENTS[SAMPLES[kind].kind].run(ctx, SAMPLES[kind]);
    this.add.text(W / 2, 120, `recorded\n${JSON.stringify(ctx.measured, null, 1)}`, { fontFamily: FONT, fontSize: "9px", color: "#F2E9CF", backgroundColor: "#0E1938", align: "center" })
      .setPadding(8, 6, 8, 6).setOrigin(0.5);
  }
}
