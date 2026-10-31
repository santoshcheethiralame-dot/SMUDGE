// Thin client for the agent server (FastAPI on :8873, proxied at /api by Vite).
// Every call has a timeout and a scripted fallback so the game never stalls.

export interface Statement { id: string; text: string }
export interface CaseData {
  case_id: string; seed: number; kit: string; title?: string; place?: string;
  // density (Case 1)
  volume_ml: number; mass_g: number; water_before_ml: number;
  // motion (Case 2)
  gate_speed: number; stop_time: number; skids: Record<string, number>; limit: number;
  statements: Record<string, Statement[]>;
  suspects: Record<string, { name: string; role: string }>;
  offline?: boolean;
  /** every other case's public facts (delays, angles, readings...), named by its kit */
  [fact: string]: any;
}
export interface LabResult {
  ok: boolean; step: string | null; evidence?: string | null; hint?: string;
  /** the evidence card, written by the server's kit */
  card?: { title: string; line: string; badge: string; say: string };
  /** notebook fields the kit flags as wrong */
  bad?: string[];
  // density
  mass_ok?: boolean; volume_ok?: boolean; density_ok?: boolean; used_total_level?: boolean; metal?: string;
  // motion
  time_ok?: boolean; accel_ok?: boolean; speeds?: Record<string, number>;
  rows?: Record<string, { s_ok: boolean; u_ok: boolean; squared: boolean }>;
}

async function post<T>(path: string, body: unknown, ms = 15000): Promise<T | null> {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), ms);
  try {
    const r = await fetch(`/api${path}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body), signal: ctl.signal });
    if (!r.ok) return null;
    return (await r.json()) as T;
  } catch {
    return null;
  } finally {
    clearTimeout(t);
  }
}

const BLANK = { volume_ml: 0, mass_g: 0, water_before_ml: 0, gate_speed: 0, stop_time: 0, skids: {}, limit: 0 };

// Local cases used only when the agent server is unreachable. Each one's culprit is fixed (see OFFLINE_TRUTH).
function offlineCase(kit: string): CaseData {
  if (kit === "motion") {
    const st = (sid: string, claim: number, tread: string): Statement[] => [
      { id: `${sid}-0`, text: `I came round Braking Bend at ${claim} m/s. Under the limit, like always.` },
      { id: `${sid}-1`, text: `I braked at the white line, same as everyone. The skid with ${tread} is mine.` },
      { id: `${sid}-2`, text: "The Trophy Tower was standing when I went past." },
      { id: `${sid}-3`, text: "Whoever knocked the tower down, it wasn't me." },
    ];
    return {
      ...BLANK, case_id: "offline", seed: 7, kit, offline: true, title: "The Skid at Braking Bend", place: "Motion Mesa",
      gate_speed: 10, stop_time: 2, skids: { dash: 4.9, rolla: 6.4, mu: 16.9 }, limit: 9,
      statements: { dash: st("dash", 7, "two thin skate lines"), rolla: st("rolla", 8, "one wide chevron tyre tread"), mu: st("mu", 6, "a broad flat scuff") },
      suspects: { dash: { name: "Dash", role: "courier" }, rolla: { name: "Rolla", role: "baker" }, mu: { name: "Mu", role: "slope inspector" } },
    };
  }
  const st = (sid: string, metal: string, custody: string): Statement[] => [
    { id: `${sid}-0`, text: `I ${custody}. Ask anyone.` },
    { id: `${sid}-1`, text: "When I had the crown, it looked as golden as ever." },
    { id: `${sid}-2`, text: `Yes, I keep ${metal}, everyone knows that. And every last gram of it is accounted for.` },
    { id: `${sid}-3`, text: "Whoever swapped that crown, it wasn't me." },
  ];
  return {
    ...BLANK, case_id: "offline", seed: 7, kit: "density", offline: true, title: "The Forged Crown", place: "Buoyant Bay",
    volume_ml: 14, mass_g: 158, water_before_ml: 50,
    statements: {
      karat: st("karat", "silver", "polished the crown at dawn in the workshop"),
      cyl: st("cyl", "lead", "locked the crown in the lighthouse vault at noon"),
      bob: st("bob", "brass", "carried the crown to the festival stage at sunset"),
    },
    suspects: { karat: { name: "Karat", role: "royal jeweller" }, cyl: { name: "Cyl", role: "harbour master" }, bob: { name: "Bob", role: "buoy and part-time fisherman" } },
  };
}
const OFFLINE_TRUTH: Record<string, { statement: string; evidence: string; culprit: string }> = {
  density: { statement: "cyl-2", evidence: "density:lead", culprit: "cyl" },
  motion: { statement: "mu-0", evidence: "speed:mu", culprit: "mu" },
};

function offlineLab(c: CaseData, w: Record<string, number>): LabResult {
  if (c.kit === "motion") {
    const a = c.gate_speed / c.stop_time;
    const rows: LabResult["rows"] = {};
    for (const [sid, s] of Object.entries(c.skids)) {
      const u = Math.sqrt(2 * a * s);
      rows[sid] = { s_ok: Math.abs(w[`s_${sid}`] - s) < 0.15, u_ok: Math.abs(w[`u_${sid}`] - u) < 0.2, squared: Math.abs(w[`u_${sid}`] - 2 * a * s) < 0.6 };
    }
    const r = Object.values(rows);
    const step = Math.abs(w.time - c.stop_time) >= 0.06 ? "time" : Math.abs(Math.abs(w.accel) - a) >= 0.11 ? "accel"
      : !r.every((x) => x.s_ok) ? "skid" : r.some((x) => x.squared && !x.u_ok) ? "forgot_root" : !r.every((x) => x.u_ok) ? "speed" : null;
    const speeds = Object.fromEntries(Object.entries(c.skids).map(([sid, s]) => [sid, Math.round(Math.sqrt(2 * a * s) * 10) / 10]));
    return { ok: !step, step, rows, speeds: step ? undefined : speeds, evidence: step ? undefined : "speed:mu",
      hint: step ? "*Check each number again, one at a time." : undefined };
  }
  const ok = Math.abs(w.mass - c.mass_g) < 0.6 && Math.abs(w.after - w.before - c.volume_ml) < 0.6 && Math.abs(w.density - c.mass_g / c.volume_ml) < 0.15;
  return { ok, step: ok ? null : "density", mass_ok: Math.abs(w.mass - c.mass_g) < 0.6, volume_ok: Math.abs(w.after - w.before - c.volume_ml) < 0.6,
    density_ok: ok, metal: ok ? "lead" : undefined, evidence: ok ? "density:lead" : undefined, hint: ok ? undefined : "*Check each number again, one at a time." };
}

// ?fixture serves the Midnight Fall from public/fixtures/fall_case.json, so the case plays with no server.
const FIX = new URLSearchParams(location.search).has("fixture");
interface FallFixture {
  case_new: CaseData;
  lab_check_ok: { reply: LabResult };
  lab_check_wrong: { reply: LabResult };
  ask_reply: { reply: { answer: string; source: string } };
  present_hit: { request: { statement_id: string; evidence: string } };
}
let fallFixture: Promise<FallFixture> | null = null;
const loadFall = () => (fallFixture ??= fetch("/fixtures/fall_case.json").then((r) => r.json() as Promise<FallFixture>));
const isFixture = (c: CaseData) => c.case_id === "fixture-fall";

/** A model can ramble; the dialogue box holds about three lines. Keep the first sentences, up to 220 characters. */
export function tidy(text: string, max = 220): string {
  const t = (text ?? "").trim();
  if (t.length <= max) return t;
  const cut = t.slice(0, max);
  const end = Math.max(cut.lastIndexOf(". "), cut.lastIndexOf("! "), cut.lastIndexOf("? "));
  return end > 60 ? cut.slice(0, end + 1) : cut.replace(/\s+\S*$/, "") + "...";
}

export class OfflineError extends Error {
  constructor(kit: string) { super(`The agent server is needed for the "${kit}" case.`); }
}

export const api = {
  current: null as CaseData | null,

  /** A fresh case from the server (a few tries, in case it is restarting). Only Cases 1 and 2 can be played
   *  offline; any other case throws OfflineError instead of loading the wrong case. */
  async newCase(kit = "density", seed?: number) {
    if (FIX && kit === "fall") {
      this.current = (await loadFall()).case_new;
      return this.current;
    }
    let c: CaseData | null = null;
    for (let i = 0; i < 3 && !c; i++) {
      c = await post<CaseData>("/case/new", { seed: seed ?? null, kit }, 8000);
      if (!c && i < 2) await new Promise((r) => setTimeout(r, 1200));
    }
    // the finals case plays from its fixture when the server is unreachable, so a dead network is never a dead stage
    if (!c && kit === "fall") {
      try { this.current = (await loadFall()).case_new; return this.current; } catch { /* no fixture either */ }
    }
    if (!c && !(kit in OFFLINE_TRUTH)) throw new OfflineError(kit);
    this.current = c ?? offlineCase(kit);
    return this.current;
  },

  async ask(suspect: string, question: string) {
    const c = this.current!;
    if (isFixture(c)) return (await loadFall()).ask_reply.reply;
    if (c.offline) return { answer: "(The agent server is offline, so I can only repeat my statement.) " + c.statements[suspect][0].text, source: "offline" };
    const r = await post<{ answer: string; source: string }>("/ask", { case_id: c.case_id, suspect, question }, 12000);
    return r ? { ...r, answer: tidy(r.answer) } : { answer: "...Sorry, what? It's noisy out here. Ask me again?", source: "timeout" };
  },

  async press(statementId: string) {
    const c = this.current!;
    if (isFixture(c)) return { answer: "I stand by what I said.", source: "fixture" };
    if (c.offline) return { answer: "I stand by what I said.", source: "offline" };
    return (await post<{ answer: string; source: string }>("/press", { case_id: c.case_id, statement_id: statementId })) ??
      { answer: "I stand by what I said.", source: "timeout" };
  },

  /** The player's notebook, keyed by the kit's own field names. */
  async labCheck(working: Record<string, number>): Promise<LabResult | null> {
    const c = this.current!;
    if (isFixture(c)) {
      const f = await loadFall();
      const g = (c.g as number) ?? 9.8;
      return Math.abs(working.height - 0.5 * g * working.gap ** 2) <= 0.3 ? f.lab_check_ok.reply : f.lab_check_wrong.reply;
    }
    if (c.offline) return offlineLab(c, working);
    return post<LabResult>("/lab/check", { case_id: c.case_id, working });
  },

  async present(statementId: string, evidence: string) {
    const c = this.current!;
    if (isFixture(c)) {
      const want = (await loadFall()).present_hit.request;
      const hit = statementId === want.statement_id && evidence === want.evidence;
      return { hit, culprit: hit ? "varnish" : undefined, close: !hit && statementId.startsWith("varnish-") };
    }
    if (c.offline) {
      const t = OFFLINE_TRUTH[c.kit];
      const hit = statementId === t.statement && evidence === t.evidence;
      return { hit, culprit: hit ? t.culprit : undefined, close: !hit && statementId.startsWith(`${t.culprit}-`) };
    }
    return (await post<{ hit: boolean; culprit?: string; close?: boolean }>("/present", { case_id: c.case_id, statement_id: statementId, evidence })) ?? { hit: false };
  },

  async hint(step: string, context = "") {
    const c = this.current!;
    if (isFixture(c) || c.offline) return "*Take it one step at a time.";
    return (await post<{ hint: string }>("/hint", { case_id: c.case_id, step, context }))?.hint ?? "*Take it one step at a time.";
  },
};
