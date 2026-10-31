// "Inside the case": a drawer for judges that shows the agents at work. It spoils the case (the culprit,
// the secret, the lie), so players never see it: it opens with the ` key, or from a button when the page is
// loaded with ?judges. The game pauses while it is open. Shift+` docks it beside the running game.
import Phaser from "phaser";
import { api } from "../api";
import { FIXTURE, live, pollTrace, lanesHtml, feedHtml, detailHtml, obsKey, OBS_CSS } from "./observatory";

interface Reply { q: string; raw: string; answer: string; source: string; rule: string | null; provider?: string; model?: string;
  cached?: boolean; ms?: number; who?: string; bait?: boolean }
interface Inside {
  title: string; kit: string; seed: number; culprit: string;
  truth: { hidden: Record<string, unknown>; public: Record<string, unknown>; lie: { id: string; text: string; contradicts: string } };
  agents: { role: string; count: number; model: string; knows: string; code_decides: string }[];
  gate: { this_case: null | { no_lab: string | null; with_lab: string | null; passed: boolean; culprit: string };
          summary: null | { seeds: number; chance: number; no_lab: number; with_lab: number; passed: number } };
  suspects: Record<string, { name: string; role: string; culprit: boolean; facts: string[]; secret: string; model: string; replies: Reply[] }>;
  filter: { checked: number; blocked: number; catches: Reply[]; baits: Reply[] };
  coach: { step: string; hint: string; source: string; context: string }[];
  lab: { step: string | null; ok: boolean }[];
  presents: { statement: string; evidence: string; hit: boolean }[];
}

const TABS = ["Live", "Overview", "Suspects", "Filter", "Coach & lab"] as const;
type Tab = (typeof TABS)[number];

const esc = (s: unknown) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);
const pct = (x: number) => `${Math.round(x * 100)}%`;

const CSS = `
#inside{--bg:#0B1026;--card:#141B3A;--ink:#EDE4C8;--soft:#A9B0CC;--rule:#2E4470;--pen:#F05A4C;--ok:#7FE0A0;--foot:#F07AAE;--gold:#FAC775;
  position:fixed;top:0;right:0;height:100%;width:min(600px,94vw);z-index:50;background:var(--bg);color:var(--ink);
  font:14px/1.5 "Segoe UI",system-ui,sans-serif;box-shadow:-8px 0 0 rgba(0,0,0,.35);display:flex;flex-direction:column;
  border-left:3px solid #C9302A;transform:translateX(102%);transition:transform .22s ease}
#inside.open{transform:none}
@media (prefers-reduced-motion:reduce){#inside{transition:none}}
#inside.docked{width:min(440px,36vw);box-shadow:none}
#inside header{padding:14px 18px 8px;border-bottom:1px solid var(--rule)}
#inside h2{font:400 24px/1.1 "Lilita One","Trebuchet MS",sans-serif;margin:0}
#inside .eyebrow{font:600 11px/1.2 "Pixelify Sans",monospace;letter-spacing:.1em;text-transform:uppercase;color:var(--foot)}
#inside nav{display:flex;gap:6px;padding:8px 18px;border-bottom:1px solid var(--rule);flex-wrap:wrap}
#inside nav button,#inside .act{font:600 13px/1 "Pixelify Sans",monospace;padding:7px 11px;border-radius:3px;border:1.5px solid var(--soft);
  background:transparent;color:var(--ink);cursor:pointer}
#inside nav button[aria-selected=true]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
#inside .act{border-color:var(--pen);color:#fff;background:#C9302A}
#inside button:focus-visible{outline:3px solid var(--foot);outline-offset:2px}
#inside .body{overflow:auto;padding:14px 18px 28px;display:grid;gap:14px;align-content:start}
#inside .card{background:var(--card);border:1px solid var(--rule);border-radius:4px;padding:12px 14px;display:grid;gap:8px;min-width:0}
#inside h3{margin:0;font:600 13px/1.2 "Pixelify Sans",monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--soft)}
#inside .big{font:400 20px/1.2 "Lilita One","Trebuchet MS",sans-serif}
#inside .tag{display:inline-block;font:600 11px/1 "Pixelify Sans",monospace;padding:3px 6px;border-radius:2px;border:1px solid var(--soft);color:var(--soft);margin-right:4px}
#inside .tag.red{border-color:var(--pen);color:var(--pen)} #inside .tag.ok{border-color:var(--ok);color:var(--ok)} #inside .tag.gold{border-color:var(--gold);color:var(--gold)}
#inside ul{margin:0;padding-left:1.1em;display:grid;gap:3px}
#inside .secret{border:1.5px solid var(--pen);background:rgba(240,90,76,.1);padding:8px 10px;border-radius:3px}
#inside .bar{height:10px;background:#0B1026;border:1px solid var(--rule);border-radius:2px;position:relative}
#inside .bar i{position:absolute;inset:0 auto 0 0;background:var(--ink)} #inside .bar b{position:absolute;top:-3px;bottom:-3px;width:2px;background:var(--foot)}
#inside .row{display:grid;grid-template-columns:8.5em 1fr;gap:8px;align-items:center}
#inside .q{color:var(--soft)} #inside s{color:var(--pen);text-decoration-thickness:2px}
#inside .reply{border-top:1px solid var(--rule);padding-top:8px;display:grid;gap:3px}
#inside .muted{color:var(--soft)} #inside table{border-collapse:collapse;width:100%;font-size:13px}
#inside td,#inside th{text-align:left;padding:5px 6px;border-bottom:1px solid var(--rule);vertical-align:top}
#inside th{font:600 11px/1 "Pixelify Sans",monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--soft)}
#inside-open{position:fixed;left:max(10px,env(safe-area-inset-left,0px));bottom:max(10px,env(safe-area-inset-bottom,0px));z-index:49;
  font:600 13px/1 "Pixelify Sans",monospace;padding:8px 12px;border-radius:3px;border:2px solid #C9302A;background:#0B1026;color:#EDE4C8;cursor:pointer}
`;

export function installInside(game: Phaser.Game) {
  const style = document.createElement("style");
  style.textContent = CSS + OBS_CSS;
  document.head.appendChild(style);
  const el = document.createElement("aside");
  el.id = "inside";
  el.setAttribute("aria-label", "Inside the case");
  el.setAttribute("aria-hidden", "true");
  document.body.appendChild(el);
  let tab: Tab = "Live";
  let timer = 0;
  let fast = 0;
  let docked = false;
  let data: Inside | null = null;
  let note = "";
  let last = "";                         // what was last drawn: redraw only when something changed
  let tests: { line: string; rule: string | null; shown: string }[] = [];
  ["keydown", "keyup", "pointerdown", "wheel"].forEach((ev) => el.addEventListener(ev, (e) => e.stopPropagation()));

  const fetchData = async () => {
    const c = api.current;
    if (!c) { data = null; note = "No case is loaded yet. Walk into a district first."; return render(); }
    if (c.offline) { data = null; note = "The agent server is offline, so suspects are scripted and there is nothing to show."; return render(); }
    try {
      const r = await fetch(`/api/case/${c.case_id}/inside`);
      data = r.ok ? await r.json() : null;
      note = r.ok ? "" : "The server doesn't know this case (was it restarted?).";
    } catch { data = null; note = "Couldn't reach the agent server."; }
    render(false);
  };

  const name = (sid: string | null | undefined) => (sid && data?.suspects[sid]?.name) || sid || "nobody";
  const replyHtml = (r: Reply) => `
    <div class="reply"><div class="q">${r.bait ? '<span class="tag gold">bait</span>' : ""}${r.who ? `<b>${esc(name(r.who))}</b> · ` : ""}"${esc(r.q)}"</div>
      ${r.rule ? `<div><s>${esc(r.raw)}</s></div><div>Player saw: "${esc(r.answer)}"</div>` : `<div>"${esc(r.answer)}"</div>`}
      <div>${r.rule ? `<span class="tag red">blocked: ${esc(r.rule)}</span>` : r.bait ? '<span class="tag ok">held the secret by itself</span>' : '<span class="tag ok">passed filter</span>'}
        <span class="tag">${esc(r.source.startsWith("script") ? "scripted fallback" : (r.model ?? r.provider ?? "model"))}</span>
        ${r.cached ? '<span class="tag">cached</span>' : r.ms ? `<span class="tag">${r.ms} ms</span>` : ""}</div></div>`;

  const liveView = () => {
    // names come from the case when we have it; with ?fixture the stress map carries the suspect ids
    const ids = data ? Object.keys(data.suspects) : Object.keys(live.stress);
    const names = Object.fromEntries(ids.map((sid) => [sid, data?.suspects[sid]?.name ?? sid]));
    return `
      <div class="card"><h3>Every agent, live · plan → draft → critique → firewall</h3>
        ${lanesHtml(live.events, live.stress, names, live.picked)}</div>
      <div class="card"><h3>Firewall feed</h3>${feedHtml(live.events)}</div>
      <div class="card"><h3>Step detail</h3>${detailHtml(live.picked)}</div>`;
  };

  const views: Record<Tab, (d: Inside) => string> = {
    Live: () => liveView(),
    Overview: (d) => {
      const g = d.gate.this_case, s = d.gate.summary;
      return `
      <div class="card"><h3>The truth engine (plain code, no model)</h3>
        <div class="big">Culprit: ${esc(name(d.culprit))}</div>
        <div>The one statement the lab can break: <b>"${esc(d.truth.lie.text)}"</b> <span class="tag red">${esc(d.truth.lie.contradicts)}</span></div>
        <div class="muted">Seed ${d.seed}. Code decides every fact, checks the lab working and judges every PRESENT. Models only phrase things.</div></div>
      <div class="card"><h3>Release gate · was this case fair to ship?</h3>
        ${g ? `<div class="row"><span>No lab</span><span>Detective agent accused <b>${esc(name(g.no_lab))}</b> ${g.no_lab === g.culprit ? '<span class="tag gold">lucky guess</span>' : '<span class="tag ok">couldn\'t tell</span>'}</span></div>
               <div class="row"><span>With the lab</span><span>accused <b>${esc(name(g.with_lab))}</b> ${g.with_lab === g.culprit ? '<span class="tag ok">solved</span>' : '<span class="tag red">missed</span>'}</span></div>
               <div>${g.passed ? '<span class="tag ok">passed: the science is needed and enough</span>' : '<span class="tag red">failed</span>'}</div>`
             : '<div class="muted">This seed was generated live and hasn\'t been through the gate.</div>'}
        ${s ? `<div class="muted">Across ${s.seeds} gated seeds for this case:</div>
          <div class="row"><span>No lab ${pct(s.no_lab)}</span><div class="bar" title="pink line: chance"><i style="width:${pct(s.no_lab)}"></i><b style="left:${pct(s.chance)}"></b></div></div>
          <div class="row"><span>With lab ${pct(s.with_lab)}</span><div class="bar"><i style="width:${pct(s.with_lab)}"></i><b style="left:${pct(s.chance)}"></b></div></div>
          <div class="muted">Pink line: chance (${pct(s.chance)}). ${s.passed}/${s.seeds} seeds passed into the play pool.</div>` : ""}</div>
      <div class="card"><h3>The agents</h3>
        <table><tr><th>Agent</th><th>Model</th><th>Knows</th><th>Code decides</th></tr>
        ${d.agents.map((a) => `<tr><td><b>${esc(a.role)}</b>${a.count > 1 ? ` ×${a.count}` : ""}</td><td>${esc(a.model)}</td><td>${esc(a.knows)}</td><td>${esc(a.code_decides)}</td></tr>`).join("")}</table></div>
      <div class="card"><h3>Output filter</h3><div class="big">${d.filter.checked} replies checked · ${d.filter.blocked} blocked</div>
        <div class="muted">Every suspect reply passes a code filter before the player sees it. See the Filter tab, or bait the culprit there.</div></div>`;
    },
    Suspects: (d) => Object.entries(d.suspects).map(([, s]) => `
      <div class="card"><div><span class="big">${esc(s.name)}</span> <span class="muted">${esc(s.role)}</span>
        ${s.culprit ? ' <span class="tag red">culprit</span>' : ' <span class="tag ok">innocent</span>'} <span class="tag">${esc(s.model)}</span></div>
        <h3>Knowledge slice: all this agent is told</h3><ul>${s.facts.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>
        ${s.secret ? `<div class="secret">${esc(s.secret)}</div>` : '<div class="muted">No secret. It cannot leak what it was never told.</div>'}
        <h3>Replies (${s.replies.length})</h3>${s.replies.length ? s.replies.slice().reverse().map(replyHtml).join("") : '<div class="muted">Not questioned yet.</div>'}</div>`).join(""),
    Filter: (d) => `
      <div class="card"><h3>Try to break the culprit</h3>
        <div>Sends confession bait to a throwaway copy of <b>${esc(name(d.culprit))}</b>. The real suspect's memory isn't touched.</div>
        <div><button class="act" id="inside-bait" type="button">Bait the culprit</button></div>
        <div class="muted">The model usually holds the secret on its own. The filter is the backstop for when it doesn't.</div></div>
      <div class="card"><h3>Filter test · scripted leaks, no model</h3>
        <div>Feeds lines that would give this case away through the same code filter every reply goes through.</div>
        <div><button class="act" id="inside-test" type="button">Run the filter test</button></div>
        ${tests.map((t) => `<div class="reply"><div><s>${esc(t.line)}</s></div><div>Player would see: "${esc(t.shown)}"</div>
          <div>${t.rule ? `<span class="tag red">blocked: ${esc(t.rule)}</span>` : '<span class="tag gold">not blocked</span>'}</div></div>`).join("")}</div>
      <div class="card"><h3>Blocked replies (${d.filter.blocked})</h3>
        ${d.filter.catches.length ? d.filter.catches.slice().reverse().map(replyHtml).join("") : '<div class="muted">Nothing blocked yet: every reply so far was safe to show.</div>'}</div>
      ${d.filter.baits.length ? `<div class="card"><h3>Bait attempts</h3>${d.filter.baits.slice().reverse().map(replyHtml).join("")}</div>` : ""}`,
    "Coach & lab": (d) => `
      <div class="card"><h3>Lab checks (code)</h3>${d.lab.length ? `<table><tr><th>#</th><th>Result</th></tr>${d.lab.map((l, i) =>
        `<tr><td>${i + 1}</td><td>${l.ok ? '<span class="tag ok">all correct</span>' : `<span class="tag red">first wrong step: ${esc(l.step)}</span>`}</td></tr>`).join("")}</table>` : '<div class="muted">No working checked yet.</div>'}</div>
      <div class="card"><h3>Footnote's hints (coach agent)</h3>${d.coach.length ? d.coach.slice().reverse().map((h) => `
        <div class="reply"><div><span class="tag">${esc(h.step)}</span><span class="tag ${h.source === "llm" ? "ok" : "gold"}">${h.source === "llm" ? "written by the model" : "safe fallback"}</span></div>
          <div>${esc(h.hint)}</div><div class="muted">Told by code which step is wrong; never given the answer.</div></div>`).join("") : '<div class="muted">No hints asked for yet.</div>'}</div>
      <div class="card"><h3>Evidence presented</h3>${d.presents.length ? `<table><tr><th>Statement</th><th>Evidence</th><th>Code says</th></tr>${d.presents.map((p) =>
        `<tr><td>${esc(p.statement)}</td><td>${esc(p.evidence)}</td><td>${p.hit ? '<span class="tag ok">breaks it</span>' : '<span class="tag red">no clash</span>'}</td></tr>`).join("")}</table>` : '<div class="muted">Nothing presented yet.</div>'}</div>`,
  };

  function render(force = true) {
    const key = JSON.stringify([tab, data, note, tests, obsKey()]);
    if (!force && key === last) return;
    last = key;
    const old = el.querySelector(".body");
    const scroll = old?.scrollTop ?? 0;
    const atEnd = !old || old.scrollHeight - old.clientHeight - scroll < 40;   // follow new events only if the reader was at the bottom
    el.innerHTML = `
      <header><div class="eyebrow">Inside the case · spoilers</div><h2>${esc(data?.title ?? "Smudge")}</h2></header>
      <nav role="tablist">${TABS.map((t) => `<button type="button" role="tab" aria-selected="${t === tab}" data-tab="${t}">${t}</button>`).join("")}
        <button type="button" id="inside-close" style="margin-left:auto">Close ✕</button></nav>
      <div class="body">${tab === "Live" ? liveView() : data ? views[tab](data) : `<div class="card">${esc(note || "Loading...")}</div>`}</div>`;
    const body = el.querySelector(".body");
    if (body && !force) body.scrollTop = tab === "Live" && atEnd ? body.scrollHeight : scroll;
    el.querySelectorAll<HTMLButtonElement>("[data-tab]").forEach((b) => (b.onclick = () => { tab = b.dataset.tab as Tab; render(); }));
    (el.querySelector("#inside-close") as HTMLButtonElement).onclick = close;
    el.querySelectorAll<HTMLButtonElement>("[data-ev]").forEach((b) => (b.onclick = () => {
      live.picked = live.events.find((e) => e.i === Number(b.dataset.ev)) ?? null;
      render(false);
    }));
    const bait = el.querySelector<HTMLButtonElement>("#inside-bait");
    if (bait && api.current) bait.onclick = async () => {
      bait.disabled = true;
      bait.textContent = "Baiting...";
      await fetch(`/api/case/${api.current!.case_id}/bait`, { method: "POST" }).catch(() => null);
      await fetchData();
    };
    const test = el.querySelector<HTMLButtonElement>("#inside-test");
    if (test && api.current) test.onclick = async () => {
      test.disabled = true;
      const r = await fetch(`/api/case/${api.current!.case_id}/filtertest`, { method: "POST" }).catch(() => null);
      tests = r?.ok ? await r.json() : [];
      render(false);
    };
  }

  const gameDiv = document.getElementById("game")!;
  // Docked: the panel sits on the right and the game keeps running in the space left of it (Phaser FIT refits).
  function setDocked(on: boolean) {
    docked = on;
    el.classList.toggle("docked", on);          // class first, so the width below is the docked width
    gameDiv.style.right = on ? `${Math.round(el.getBoundingClientRect().width)}px` : "0";
    const refit = () => { game.scale.getParentBounds(); game.scale.refresh(); };
    refit();
    requestAnimationFrame(refit);               // Phaser reads the parent size a frame late
    window.setTimeout(refit, 120);
  }
  function open(dock = false) {
    el.classList.add("open");
    el.setAttribute("aria-hidden", "false");
    setDocked(dock);
    if (!dock) game.pause();
    fetchData();
    timer = window.setInterval(fetchData, 2500);
    const tick = async () => {
      const c = api.current;
      const cid = FIXTURE ? "fixture" : c && !c.offline ? c.case_id : "";
      if (tab === "Live" && cid && await pollTrace(cid)) render(false);
    };
    tick();
    fast = window.setInterval(tick, 500);
    (el.querySelector("#inside-close") as HTMLButtonElement | null)?.focus();
  }
  function close() {
    el.classList.remove("open");
    el.setAttribute("aria-hidden", "true");
    window.clearInterval(timer);
    window.clearInterval(fast);
    if (docked) setDocked(false);
    else game.resume();
  }
  const toggle = (dock = false) => (el.classList.contains("open") ? close() : open(dock));

  window.addEventListener("keydown", (e) => {
    if (e.code === "Backquote" || e.key === "`" || e.key === "~") { e.preventDefault(); toggle(e.shiftKey); }
    else if (e.key === "Escape" && el.classList.contains("open")) close();
  }, true);
  if (new URLSearchParams(location.search).has("judges")) {
    const b = document.createElement("button");
    b.id = "inside-open";
    b.type = "button";
    b.textContent = "Observatory ( ` · ⇧ docks )";
    b.onclick = () => toggle(true);
    document.body.appendChild(b);
  }
  render();
}
