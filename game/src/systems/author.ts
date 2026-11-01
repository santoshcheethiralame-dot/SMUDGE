// "Author a case": a teacher types one line and watches the agents write, prove and gate a new case
// (server/author.py), then plays it. Opened from the casebook map, or straight away with ?author.
import { addSpec, pretty, type Spec } from "../cases/generated";
import type { TraceEvent } from "./observatory";

const esc = (s: unknown) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);

const LANES: [string, string, string][] = [
  ["designer", "Designer", "model writes the case"],
  ["solver", "Solver", "code plays 200 seeds"],
  ["critic", "Critic", "model checks physics + safety"],
  ["casting", "Casting", "code picks cast + district"],
  ["gate", "Gate", "detective agent solves it"],
];

const CSS = `
#author{--bg:#0B1026;--card:#141B3A;--ink:#EDE4C8;--soft:#A9B0CC;--rule:#2E4470;--pen:#F05A4C;--ok:#7FE0A0;--foot:#F07AAE;--gold:#FAC775;
  position:fixed;inset:0;z-index:60;display:grid;place-items:center;background:rgba(5,6,15,.72);font:14px/1.5 "Segoe UI",system-ui,sans-serif;color:var(--ink)}
#author .box{background:var(--bg);border:1px solid var(--rule);border-top:3px solid #C9302A;width:min(760px,94vw);max-height:92vh;overflow:auto;
  padding:18px 20px;display:grid;gap:12px;box-shadow:0 10px 0 rgba(0,0,0,.35)}
#author .eyebrow{font:600 11px/1.2 "DotGothic16",monospace;letter-spacing:.1em;text-transform:uppercase;color:var(--foot)}
#author h2{font:400 26px/1.1 "Lilita One","Trebuchet MS",sans-serif;margin:2px 0 0}
#author form{display:flex;gap:8px;flex-wrap:wrap}
#author input{flex:1 1 18em;font:16px/1.2 "Segoe UI",system-ui,sans-serif;padding:9px 11px;border-radius:3px;border:1.5px solid var(--soft);background:#0E1430;color:var(--ink)}
#author button{font:600 13px/1 "DotGothic16",monospace;padding:9px 13px;border-radius:3px;border:1.5px solid var(--soft);background:transparent;color:var(--ink);cursor:pointer}
#author button.go{border-color:var(--pen);background:#C9302A;color:#fff}
#author button:disabled{opacity:.5;cursor:default}
#author button:focus-visible,#author input:focus-visible{outline:3px solid var(--foot);outline-offset:2px}
#author .lane{display:grid;grid-template-columns:11em 1fr;gap:10px;border-top:1px solid var(--rule);padding-top:7px}
#author .who b{display:block} #author .who span{color:var(--soft);font-size:12px}
#author .pill{display:inline-block;font:600 11px/1 "DotGothic16",monospace;padding:5px 7px;margin:0 4px 4px 0;border-radius:2px;border:1px solid var(--ok);color:var(--ok)}
#author .pill.red{border-color:var(--pen);color:#fff;background:rgba(240,90,76,.35)} #author .pill.gold{border-color:var(--gold);color:var(--gold)}
#author .pill.wait{border-style:dashed;border-color:var(--soft);color:var(--soft);animation:au-pulse 1s ease-in-out infinite}
@keyframes au-pulse{50%{opacity:.4}} @media (prefers-reduced-motion:reduce){#author .pill.wait{animation:none}}
#author .feed{background:var(--card);border:1px solid var(--rule);border-radius:4px;padding:10px 12px;display:grid;gap:4px;font-size:13px}
#author .feed:empty{display:none}
#author .tag{font:600 11px/1 "DotGothic16",monospace;padding:3px 6px;border-radius:2px;border:1px solid var(--gold);color:var(--gold);margin-right:6px}
#author .done{background:#F2E9CF;color:#0E1938;border:2px solid #0E1938;border-radius:4px;padding:12px 14px;display:grid;gap:6px}
#author .done h3{margin:0;font:400 22px/1.1 "Lilita One","Trebuchet MS",sans-serif}
#author .done .f{font:600 18px/1.2 "DotGothic16",monospace;color:#C9302A}
#author .row{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap}
#author .muted{color:var(--soft)}
`;

function label(e: TraceEvent): [string, string] {
  const d = e.data;
  const time = e.ms ? ` · ${(e.ms / 1000).toFixed(1)}s` : "";
  switch (e.step) {
    case "design": return [e.verdict === "fallback" ? `round ${d.round} · golden spec` : `round ${d.round} · ${d.title ?? ""}${time}`, e.verdict === "fallback" ? "gold" : "ok"];
    case "solve": return [e.verdict === "pass" ? `round ${d.round} · 200 seeds ✓` : `round ${d.round} · ${d.problems.length} problem${d.problems.length > 1 ? "s" : ""} → redesign`, e.verdict === "pass" ? "ok" : "red"];
    case "critique": return [e.verdict === "skip" ? "skipped (no model)" : e.verdict === "pass" ? `round ${d.round} · approved${time}` : `round ${d.round} · ${d.issues.length} fix${d.issues.length > 1 ? "es" : ""} → redesign`, e.verdict === "pass" ? "ok" : e.verdict === "skip" ? "gold" : "red"];
    case "cast": return [`${d.place}: ${d.suspects.join(", ")}`, "ok"];
    case "gate": return [`seed ${d.seed} · ${d.lab ? "with lab" : "no lab"} · ${d.guess === d.culprit ? "right" : "wrong"}`, d.lab ? (d.guess === d.culprit ? "ok" : "red") : "gold"];
    default: return [e.step, "ok"];
  }
}

/** Open the panel. Resolves with the new case's kit id when the teacher presses Play, or null when closed. */
export function openAuthor(): Promise<string | null> {
  return new Promise((resolve) => {
    if (!document.getElementById("author-css")) {
      const st = document.createElement("style");
      st.id = "author-css";
      st.textContent = CSS;
      document.head.appendChild(st);
    }
    const el = document.createElement("div");
    el.id = "author";
    el.innerHTML = `<div class="box" role="dialog" aria-modal="true" aria-labelledby="au-h">
      <div><div class="eyebrow">Author a case · five agents</div><h2 id="au-h">One line in. A solvable case out.</h2></div>
      <form><input id="au-q" value="Class 9, pressure: P = F/A" aria-label="What should the case teach?" autocomplete="off">
        <button type="submit" class="go" id="au-go">Write it ▸</button><button type="button" id="au-x">Close</button></form>
      <div id="au-lanes"></div><div class="feed" id="au-feed"></div><div id="au-out"></div></div>`;
    document.body.appendChild(el);
    const $ = <T extends HTMLElement>(id: string) => el.querySelector<T>(`#${id}`)!;
    let timer = 0;
    const close = (kit: string | null) => { clearInterval(timer); el.remove(); window.removeEventListener("keydown", onKey, true); resolve(kit); };
    const onKey = (ev: KeyboardEvent) => { ev.stopPropagation(); if (ev.key === "Escape") close(null); };
    window.addEventListener("keydown", onKey, true);         // typing here must not move Smudge
    $("au-x").onclick = () => close(null);

    const draw = (events: TraceEvent[], status: string) => {
      const busy = status === "running";
      const last = events[events.length - 1]?.agent;
      const nextLane = busy ? (last ? LANES[Math.min(LANES.findIndex((l) => l[0] === last) + (["design", "cast"].includes(events[events.length - 1].step) ? 1 : 0), LANES.length - 1)][0] : "designer") : "";
      $("au-lanes").innerHTML = LANES.map(([id, name, sub]) => {
        const pills = events.filter((e) => e.agent === id).map((e) => { const [t, tone] = label(e); return `<span class="pill ${tone}">${esc(t)}</span>`; }).join("");
        return `<div class="lane"><div class="who"><b>${name}</b><span>${sub}</span></div>
          <div>${pills}${id === nextLane ? '<span class="pill wait">working…</span>' : ""}${!pills && id !== nextLane ? '<span class="muted">waiting</span>' : ""}</div></div>`;
      }).join("");
      $("au-feed").innerHTML = events.filter((e) => (e.step === "solve" && e.verdict === "block") || (e.step === "critique" && e.verdict === "leak"))
        .flatMap((e) => (e.data.problems ?? e.data.issues).map((p: string) => `<div><span class="tag">${e.step === "solve" ? "SOLVER" : "CRITIC"}</span>${esc(p)}</div>`)).join("");
    };

    el.querySelector("form")!.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const prompt = $<HTMLInputElement>("au-q").value.trim();
      if (!prompt) return;
      $<HTMLButtonElement>("au-go").disabled = true;
      $("au-out").innerHTML = "";
      let job: string;
      try {
        const r = await fetch("/api/author", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt }) });
        if (!r.ok) throw new Error(String(r.status));
        job = (await r.json()).job;
      } catch {
        $("au-out").innerHTML = `<div class="feed"><div><span class="tag">OFFLINE</span>The agent server isn't answering. Start it, then try again.</div></div>`;
        $<HTMLButtonElement>("au-go").disabled = false;
        return;
      }
      const events: TraceEvent[] = [];
      draw(events, "running");
      timer = window.setInterval(async () => {
        let page: { status: string; next: number; events: TraceEvent[]; spec: Spec | null; error: string | null };
        try { page = await (await fetch(`/api/author/${job}?since=${events.length}`)).json(); } catch { return; }
        events.push(...page.events);
        draw(events, page.status);
        if (page.status === "running") return;
        clearInterval(timer);
        $<HTMLButtonElement>("au-go").disabled = false;
        if (page.status === "failed" || !page.spec) {
          $("au-out").innerHTML = `<div class="feed"><div><span class="tag">STOPPED</span>${esc(page.error ?? "no case")}</div></div>`;
          return;
        }
        const s = page.spec;
        const res = await fetch("/api/kits/generated").then((r) => r.json()).catch(() => []) as Spec[];
        const kit = addSpec(res.find((x) => x.id === s.id) ?? { ...s, cast: {} });
        $("au-out").innerHTML = `<div class="done"><div class="eyebrow" style="color:#C9302A">Gated · ready to play</div>
          <h3>${esc(s.title)}</h3><div class="f">${esc(pretty(s.formula))}</div><div>${esc(s.chapter)} · ${esc(s.crime)}</div>
          <div class="row"><button type="button" class="go" id="au-play">Play it ▸</button></div></div>`;
        $("au-play").onclick = () => close(kit);
        $("au-play").focus();
      }, 500);
    });
    $<HTMLInputElement>("au-q").focus();
  });
}
