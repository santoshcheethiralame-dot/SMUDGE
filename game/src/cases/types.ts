import type Phaser from "phaser";
import type { Line } from "../systems/dialogue";
import type { Evidence } from "../state";
import type { LabStep } from "../systems/lab/types";

/** Where things stand in a district: world coordinates, same camera as the backdrop render. */
export interface Layout {
  width: number;
  cu: number;
  cv: number;
  /** each suspect's spot and the crime scene ("stage"): world x, and where the sparkle marker floats */
  spots: { key: string; x: number; markY: number; markZ: number }[];
  suspects: { key: string; x: number; z: number }[];
  startX: number;
}

export type Project = (x: number, y: number, z: number) => { x: number; y: number };

/** One case: what it says and shows. The facts come from the server's kit with the same `kit` id. */
export interface CaseDef {
  kit: string;
  num: number;
  title: string;
  place: string;
  chapter: string;
  /** the art this case needs: images by key, and the folder its suspect sheets live in */
  assets: { folder: string; images: string[]; suspects: string[] };
  bg: { glitch: string; restored: string };
  layout: Layout;
  /** scenery on top of the backdrop: animated props, particles, glows */
  decorate?: (scene: Phaser.Scene, P: Project, restored: boolean) => void;
  /** a bespoke lab scene, or steps for the shared CaseLab */
  lab: string;
  labSteps?: LabStep[];
  greet: Record<string, Line>;
  chips: Record<string, string[]>;
  arrive: Line[];
  inspect: Line[];
  toLab: Line;
  afterLab: Line;
  checklist: [string, string];
  stageLabel: string;
  badge(ev: Evidence): string;
  miss(ev: Evidence): string;
  stuck(ev: Evidence): string;
  confess: Record<string, { expr: string; text: string }[]>;
  restore: {
    glyphs: string[]; sub: string; card: string; cardSub: string;
    /** optional: plays over the restored district, before the formula card */
    reveal?: (scene: Phaser.Scene) => Promise<void>;
    /** optional: plays after the formula card, before the case-solved screen (an exit check, say) */
    after?: (scene: Phaser.Scene) => Promise<void>;
  };
  solved(name: string): string;
  /** where it sits on the map: x, y on the 480x270 book spread */
  map: { x: number; y: number; icon: string };
}

/** Older name, kept so scenes read naturally. */
export type CaseContent = CaseDef;
