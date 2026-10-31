// Cases written by the Author agents (server/author.py). The server keeps them as specs; here each becomes a
// CaseDef on the art of the built case it borrows (its district, its suspects), with a notebook-only lab.
import type { CaseDef } from "./types";
import type { CaseData } from "../api";
import type { Line } from "../systems/dialogue";
import { CASES } from "./index";

export interface Spec {
  id: string; title: string; chapter: string; law: string; formula: string; borrow: string; num?: number;
  out: { sym: string; name: string; unit: string };
  ins: { sym: string; name: string; unit: string; values: number[] }[];
  consts?: Record<string, number>;
  thing: string; item: string; crime: string; measure: string; hint: string;
  arrive: string[]; inspect: string[]; confession: string;
  /** added by the server: the borrowed suspects' names and roles */
  cast: Record<string, { name: string; role: string }>;
}

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

export function fromSpec(s: Spec): CaseDef {
  const base = CASES[s.borrow];
  const ids = Object.keys(s.cast);
  const name = (sid: string) => s.cast[sid]?.name ?? sid;
  const consts = Object.entries(s.consts ?? {}).map(([k, v]) => `${k} = ${v}`).join(", ");
  const say = (lines: string[], who: ("foot" | "smudge")[]): Line[] =>
    lines.map((text, i) => ({ who: who[i % who.length], expr: i ? "neutral" : "thinking", text }));
  return {
    ...base,
    kit: s.id, num: s.num ?? 50, title: s.title, chapter: s.chapter,
    lab: "CaseLab",
    labSteps: [
      { kind: "say", lines: [
        { who: "foot", expr: "happy", text: `Lab time! ${s.measure}` },
        { who: "foot", expr: "neutral", text: `The law: ${s.formula}. Work out each ${s.thing}'s ${s.out.name}, then check it against what they swore.` },
      ] },
      { kind: "notebook", hint: s.hint, note: consts ? `${s.formula}   (${consts})` : s.formula,
        fields: (c: CaseData) => ids.flatMap((sid) => [
          ...s.ins.map((i) => ({ key: `${i.sym}_${sid}`, label: `${name(sid)}: ${i.name}`, unit: i.unit, given: (c.ins as Record<string, Record<string, number>>)[sid][i.sym] })),
          { key: `out_${sid}`, label: `${name(sid)}: ${s.out.name}`, unit: s.out.unit },
        ]) },
    ],
    greet: Object.fromEntries(ids.map((sid) => [sid, { who: sid, expr: "neutral", text: `${name(sid)}, ${s.cast[sid].role}. You're here about the ${s.item}? Ask, then.` }])),
    chips: Object.fromEntries(ids.map((sid) => [sid, [`What is your ${s.thing}'s ${s.out.name}?`, "What happened last night?", "Who do you think is behind it?"]])),
    arrive: say(s.arrive, ["foot", "smudge", "foot"]),
    afterFirst: undefined,
    inspect: say(s.inspect, ["smudge", "foot"]),
    toLab: { who: "smudge", expr: "determined", text: `To the lab. Three ${s.thing}s, one formula.` },
    afterLab: { who: "foot", expr: "happy", text: `Every ${s.thing} has its ${s.out.name} now. Call them to the stage and check their stories.` },
    checklist: [`Inspect the ${s.item}`, `Work out the ${s.out.name}s`],
    stageLabel: cap(`the ${s.item}`),
    badge: (ev) => ev.badge,
    miss: () => `*That ${s.thing} matches what they swore. Find the one that doesn't.`,
    stuck: () => `*Line up each sworn ${s.out.name} with the one you worked out. Only one is off.`,
    confess: Object.fromEntries(ids.map((sid) => [sid, [{ expr: "shocked", text: "...The numbers. Of course it was the numbers." }, { expr: "nervous", text: s.confession }]])),
    caught: undefined,
    point: undefined,
    restore: { glyphs: s.formula.split(""), sub: `The law of ${s.law.toLowerCase()} is back in the book.`, card: s.formula,
      cardSub: `${s.law} · ${s.chapter.split(":")[0]}` },
    solved: (who) => `${who} lied about the ${s.out.name}. ${s.law} proved it.`,
  };
}

/** Register an authored case; returns its kit id. */
export function addSpec(s: Spec): string | null {
  if (!CASES[s.borrow]) return null;
  CASES[s.id] = fromSpec(s);
  return s.id;
}

/** Every case the server has authored so far. Quietly nothing when the server is down. */
export async function loadGenerated() {
  try {
    const r = await fetch("/api/kits/generated", { signal: AbortSignal.timeout(2500) });
    if (r.ok) for (const s of (await r.json()) as Spec[]) addSpec(s);
  } catch { /* no server, no authored cases */ }
}
