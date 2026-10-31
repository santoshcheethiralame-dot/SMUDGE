// The Observatory: the agents' live trace, the red-team board and the gate replay, drawn inside the judges' panel.
// Payloads follow docs/superpowers/specs/2026-10-30-finals-design.md §3. With ?fixture they come from /fixtures.

export interface TraceEvent {
  i: number; t: number; agent: string; kind: string; step: string; model: string | null; provider: string | null;
  ms: number; tokens: number; cached: boolean; verdict: string; data: Record<string, any>; dt?: number;
}
export interface StressView { level: number; band: string }
interface TracePage { next: number; events: TraceEvent[]; stress: Record<string, StressView> }

export const FIXTURE = new URLSearchParams(location.search).has("fixture");

const esc = (s: unknown) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);

/** Everything seen so far for the current case. Reset when the case changes. */
export const live = { cid: "", next: 0, events: [] as TraceEvent[], stress: {} as Record<string, StressView>, picked: null as TraceEvent | null };

/** Fetch new events. Resolves true when something new arrived. */
export async function pollTrace(cid: string): Promise<boolean> {
  if (cid !== live.cid) Object.assign(live, { cid, next: 0, events: [], stress: {}, picked: null });
  if (FIXTURE && live.events.length) return false;
  try {
    const r = await fetch(FIXTURE ? "/fixtures/trace_sample.json" : `/api/case/${cid}/trace?since=${live.next}`);
    if (!r.ok) return false;
    const page = (await r.json()) as TracePage;
    live.events.push(...page.events);
    live.next = page.next;
    live.stress = page.stress;
    return page.events.length > 0;
  } catch {
    return false;
  }
}

const tone = (v: string) => (v === "leak" || v === "block" ? "red" : v === "skip" || v === "fallback" ? "gold" : "ok");
const SPECIAL: Record<string, string> = { footnote: "Footnote (coach)", detective: "Detective", router: "Router" };

function pill(e: TraceEvent, picked: TraceEvent | null) {
  const label = e.step === "critique" && e.verdict === "leak" ? "critique: LEAK"
    : e.step === "firewall" ? `firewall ${e.verdict === "block" ? "BLOCK" : "ok"}`
    : e.step === "plan" && e.data.intent ? `plan · ${e.data.intent} · ${e.data.risk}`
    : e.verdict === "skip" ? `${e.step} skipped (${e.data.why ?? ""})`
    : e.step;
  const time = e.cached ? " · cache" : e.ms ? ` · ${e.ms}ms` : "";
  return `<button type="button" class="pill ${tone(e.verdict)}${picked === e ? " on" : ""}" data-ev="${e.i}">${esc(label)}${time}</button>`;
}

/** One lane per suspect (in the case's order), then the coach, the detective and the router. */
export function lanesHtml(events: TraceEvent[], stress: Record<string, StressView>, names: Record<string, string>,
                          picked: TraceEvent | null) {
  const lanes = [...Object.keys(names), "footnote", "detective", "router"];
  return lanes.map((who) => {
    const mine = events.filter((e) => e.agent === who).slice(-24);
    const s = stress[who];
    const meter = s ? `<span class="stress"><span class="bar"><i style="width:${(s.level / 9) * 100}%"></i></span>
        <span class="tag ${s.level >= 5 ? "red" : s.level >= 3 ? "gold" : "ok"}">${esc(s.band)} ${s.level}/9</span></span>` : "";
    // a reply ends a row, so each question reads as one line of steps
    const pills = mine.map((e) => pill(e, picked) + (e.step === "reply" || e.step === "accuse" ? "<br>" : "")).join("");
    return `<div class="lane"><div class="who"><b>${esc(names[who] ?? SPECIAL[who] ?? who)}</b>${meter}</div>
      <div class="pills">${pills || '<span class="muted">quiet</span>'}</div></div>`;
  }).join("");
}

/** Blocks and caught leaks, newest first. */
export function feedHtml(events: TraceEvent[]) {
  const hits = events.filter((e) => (e.step === "firewall" && e.verdict === "block") || (e.step === "critique" && e.verdict === "leak"));
  if (!hits.length) return '<div class="muted">Nothing caught yet.</div>';
  return hits.slice(-8).reverse().map((e) => e.step === "firewall"
    ? `<div><span class="tag red">BLOCK</span> ${esc(e.data.rule)} · <b>${esc(e.agent)}</b></div>`
    : `<div><span class="tag gold">REDRAFT</span> critique caught a leak · <b>${esc(e.agent)}</b> <span class="muted">${esc(e.data.fix)}</span></div>`).join("");
}

export function detailHtml(e: TraceEvent | null) {
  return e ? `<pre class="json">${esc(JSON.stringify(e, null, 2))}</pre>` : '<div class="muted">Click any step to see its JSON.</div>';
}

/** Changes whenever anything the Observatory draws changes; inside.ts redraws only then. */
export function obsKey() {
  return `${live.cid}:${live.next}:${live.events.length}:${live.picked?.i ?? -1}`;
}

export const OBS_CSS = `
#inside .lane{display:grid;grid-template-columns:9.5em 1fr;gap:8px;border-top:1px solid var(--rule);padding-top:6px}
#inside .who{display:grid;gap:4px;align-content:start}
#inside .stress{display:grid;gap:3px}
#inside .stress .bar{height:6px}
#inside .pills{line-height:2}
#inside .pill{font:600 11px/1 "DotGothic16",monospace;padding:4px 6px;margin:0 3px 3px 0;border-radius:2px;cursor:pointer;
  background:transparent;border:1px solid var(--ok);color:var(--ok)}
#inside .pill.red{border-color:var(--pen);color:#fff;background:rgba(240,90,76,.35)}
#inside .pill.gold{border-color:var(--gold);color:var(--gold)}
#inside .pill.on{outline:2px solid var(--foot)}
#inside .json{white-space:pre-wrap;word-break:break-word;font:12px/1.4 ui-monospace,monospace;margin:0;max-height:16em;overflow:auto}
@keyframes obs-in{from{transform:scale(.6);opacity:0}to{transform:none;opacity:1}}
#inside .pill:last-of-type{animation:obs-in .25s ease-out}
@media (prefers-reduced-motion:reduce){#inside .pill:last-of-type{animation:none}}
`;
