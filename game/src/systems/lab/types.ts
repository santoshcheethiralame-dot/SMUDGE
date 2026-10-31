import type Phaser from "phaser";
import type { Line, Dialogue } from "../dialogue";
import type { CaseData, LabResult } from "../../api";

/** What every instrument gets: the lab scene, its dialogue box, the live case, and the measurements so far. */
export interface LabCtx {
  scene: Phaser.Scene;
  dlg: Dialogue;
  c: CaseData;
  measured: Record<string, number>;
  /** the server's verdict on the notebook, once it says the working is right */
  result?: LabResult;
}

/** An instrument: src/systems/lab/instruments/<kind>.ts exports `kind` and `run`, and is found automatically. */
export interface Instrument {
  kind: string;
  run(ctx: LabCtx, step: any): Promise<void>;
}

export interface SayStep { kind: "say"; lines: Line[] }

/** Time something on a screen with Smudge's stopwatch: tap at the start cue, tap at the end cue. */
export interface StopwatchStep {
  kind: "stopwatch";
  intro: Line[];
  /** one clip per thing to time; seconds is the truth the stopwatch snaps to */
  clips: (c: CaseData) => { key: string; label: string; seconds: number; style: "flashboom" | "rise" }[];
  /** measured[record + "_" + clip.key] = seconds */
  record: string;
  done: Line[];
}

/** Measure lengths on an evidence photo with Smudge's tape. measured[record + "_" + row.key] = length. */
export interface TapeStep {
  kind: "tape";
  intro: Line[];
  done: Line[];
  title: string;
  unit: string;
  /** the scale's full length, in `unit` */
  max: number;
  /** reading resolution (default 0.1) */
  step?: number;
  fill?: number;
  record: string;
  rows: (c: CaseData) => { key: string; label: string; length: number; style?: "skid2" | "chevron" | "scuff" | "shadow" | "bar" }[];
}

/** Measure angles with Smudge's protractor. From the ground (a sun ray) or from the normal (a light ray).
 *  measured[record + "_" + item.key] = angle in degrees. */
export interface ProtractorStep {
  kind: "protractor";
  intro: Line[];
  done: Line[];
  record: string;
  /** below: a label for the medium under the surface in normal mode ("glass block", "the fake lens") */
  items: (c: CaseData) => { key: string; label: string; angle: number; from: "ground" | "normal"; side?: "up" | "down"; other?: number; below?: string }[];
}

/** Read a thermometer or a dial meter; the player types the reading. measured[record + "_" + item.key] = value. */
export interface GaugeStep {
  kind: "gauge";
  intro: Line[];
  done: Line[];
  record: string;
  items: (c: CaseData) => { key: string; label: string; value: number; min: number; max: number; step: number; unit: string; style: "thermo" | "dial"; labelEvery?: number }[];
}

/** Universal indicator: drip, then match the colour on the pH chart. measured[record + "_" + sample.key] = pH. */
export interface DropperStep {
  kind: "dropper";
  intro: Line[];
  done: Line[];
  record: string;
  samples: (c: CaseData) => { key: string; label: string; ph: number }[];
}

/** Roll a die and tally. measured[record + "_" + set.key + "_" + face] = count, and "_total". */
export interface TallyStep {
  kind: "tally";
  intro: Line[];
  done: Line[];
  record: string;
  sets: (c: CaseData) => { key: string; label: string; counts: number[] }[];
}

/** Weigh items on a digital balance. measured[record + "_" + item.key] = mass. */
export interface BalanceStep {
  kind: "balance";
  intro: Line[];
  done: Line[];
  record: string;
  unit: string;
  /** look: what sits on the pan, a crate (default), a tub of water or a bare metal block */
  items: (c: CaseData) => { key: string; label: string; mass: number; look?: "crate" | "tub" | "ingot" }[];
}

export interface Field {
  key: string;
  label: string;
  unit: string;
  /** a measurement carried over from an earlier step: shown, not edited */
  given?: number;
}

/** The player's working, checked by the server's kit; the evidence card comes back from it. */
export interface NotebookStep {
  kind: "notebook";
  hint: string;
  /** a reference line kept in view at the top of the notebook: a table, a constant */
  note?: string;
  fields: (c: CaseData, measured: Record<string, number>) => Field[];
}

export type LabStep = SayStep | StopwatchStep | TapeStep | ProtractorStep | GaugeStep | DropperStep | TallyStep | BalanceStep | NotebookStep;
