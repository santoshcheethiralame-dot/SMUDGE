// Every case folder registers itself: add src/cases/<kit>/index.ts exporting a CaseDef and it is in the game,
// on the map, and its art is loaded. Nothing else to edit.
import type { CaseDef } from "./types";

export type { CaseDef, CaseContent, Layout, Project } from "./types";

const found = import.meta.glob<{ default: CaseDef }>("./*/index.ts", { eager: true });

export const CASES: Record<string, CaseDef> = {};
for (const m of Object.values(found)) CASES[m.default.kit] = m.default;

/** Case kits in book order. */
export const CASE_ORDER = Object.values(CASES).sort((a, b) => a.num - b.num).map((c) => c.kit);

/** The case after this one in book order, if any. */
export function after(kit: string): CaseDef | undefined {
  return CASES[CASE_ORDER[CASE_ORDER.indexOf(kit) + 1]];
}

/** The first unsolved case, or the last one if everything is solved. */
export function nextCase(solved: Set<string>): CaseDef {
  return CASES[CASE_ORDER.find((k) => !solved.has(k)) ?? CASE_ORDER[CASE_ORDER.length - 1]];
}
