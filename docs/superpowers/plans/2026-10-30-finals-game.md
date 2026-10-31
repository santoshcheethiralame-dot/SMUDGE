# Finals: game implementation plan (Kushal)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the judges' drawer into the Observatory (live agent lanes, stress, firewall feed, red-team board, gate
replay), dock it beside a running game, and let players question suspects out loud.

**Architecture:** A new `systems/observatory.ts` owns the three payloads from the server contract and renders them
as HTML strings; `systems/inside.ts` hosts them as new tabs and gains a docked mode. A new `systems/voice.ts` wraps
the browser's speech APIs; the ask box and the district use it, and `audio.ts` mutes the syllable blips while a
reply is spoken.

**Tech Stack:** TypeScript 5.6, Phaser 3.90, Vite, plain DOM, Web Speech API.

Spec: `docs/superpowers/specs/2026-10-30-finals-design.md` (§3 is the contract, §5 is this work). Server plan:
`2026-10-30-finals-server.md`.

## Global Constraints

- Budget ₹0: browser APIs only, no new npm packages.
- `cd game && npx tsc --noEmit` and `cd server && python -m pytest tests -q` green before every commit.
- Plain DOM for panels, as `inside.ts` does today; every string from the server goes through `esc()`.
- In-game (player-visible) UI never shows case numbers or the culprit. Only the judges' panel may.
- Kid-safe always. Small commits, one feature per commit.

## How to check your work (no server changes needed)

The server's new endpoints land during the same 48 hours. Until then, build against the fixtures:

1. Start the existing server and game (`.claude/launch.json` entries `server` and `game`, or the commands in
   `docs/HANDOFF.md` §2).
2. Open `http://localhost:8872/?case=ohm&judges&fixture`. Walk to a suspect so a case exists, then press `` ` ``.
3. With `?fixture`, the Live, Red team and Gate replay tabs read `game/public/fixtures/*.json` instead of the server.
   Drop `&fixture` once Santosh says the endpoints are in.

## Files

| File | Responsibility |
|---|---|
| `game/src/systems/observatory.ts` | contract types, fetching (server or fixture), Live / Red team / Gate replay HTML (create) |
| `game/src/systems/inside.ts` | new tabs, 500 ms trace polling, docked mode, pill detail (modify) |
| `game/src/systems/voice.ts` | hold-to-talk speech recognition, spoken replies, the voice setting (create) |
| `game/src/systems/ui.ts` | mic button in `askBox` (modify) |
| `game/src/systems/district.ts` | speak each reply (modify) |
| `game/src/audio.ts` | no syllable blips while a reply is spoken (modify) |
| `game/src/main.ts` | install the voice toggle (modify) |

---

### Task 1: The Observatory's Live tab (T+0–14)

**Files:**
- Create: `game/src/systems/observatory.ts`
- Modify: `game/src/systems/inside.ts`

**Interfaces:**
- Consumes: `GET /api/case/{cid}/trace?since=` (or `/fixtures/trace_sample.json`), shape in spec §3.1.
- Produces: `observatory.ts` exports `TraceEvent`, `StressView`, `live`, `pollTrace(cid)`, `lanesHtml(events, stress,
  names, picked)`, `feedHtml(events)`, `detailHtml(ev)`, `OBS_CSS`, `obsKey()`.

- [ ] **Step 1: Create `observatory.ts` with types, polling and the Live view**

```ts
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
#inside .pill{font:600 11px/1 "Pixelify Sans",monospace;padding:4px 6px;margin:0 3px 3px 0;border-radius:2px;cursor:pointer;
  background:transparent;border:1px solid var(--ok);color:var(--ok)}
#inside .pill.red{border-color:var(--pen);color:#fff;background:rgba(240,90,76,.35)}
#inside .pill.gold{border-color:var(--gold);color:var(--gold)}
#inside .pill.on{outline:2px solid var(--foot)}
#inside .json{white-space:pre-wrap;word-break:break-word;font:12px/1.4 ui-monospace,monospace;margin:0;max-height:16em;overflow:auto}
@keyframes obs-in{from{transform:scale(.6);opacity:0}to{transform:none;opacity:1}}
#inside .pill:last-of-type{animation:obs-in .25s ease-out}
@media (prefers-reduced-motion:reduce){#inside .pill:last-of-type{animation:none}}
#inside.docked{width:min(440px,36vw);box-shadow:none}
`;
```

- [ ] **Step 2: Host it in `inside.ts`**

Imports at the top:

```ts
import { live, pollTrace, lanesHtml, feedHtml, detailHtml, obsKey, OBS_CSS } from "./observatory";
```

Tabs (Live first, so the panel opens on it):

```ts
const TABS = ["Live", "Overview", "Suspects", "Filter", "Coach & lab"] as const;
```

In `installInside`, append the CSS and change the default tab:

```ts
  style.textContent = CSS + OBS_CSS;
  ...
  let tab: Tab = "Live";
  let fast = 0;
  let docked = false;
```

Add the Live view to `views` (a helper turns suspect ids into names):

```ts
    Live: (d) => {
      const names = Object.fromEntries(Object.entries(d.suspects).map(([sid, s]) => [sid, s.name]));
      return `
      <div class="card"><h3>Every agent, live · plan → draft → critique → firewall</h3>
        ${lanesHtml(live.events, live.stress, names, live.picked)}</div>
      <div class="card"><h3>Firewall feed</h3>${feedHtml(live.events)}</div>
      <div class="card"><h3>Step detail</h3>${detailHtml(live.picked)}</div>`;
    },
```

In `render()`, include the Observatory in the redraw key, and wire pill clicks after the existing handlers:

```ts
    const key = JSON.stringify([tab, data, note, tests, obsKey()]);
    ...
    el.querySelectorAll<HTMLButtonElement>("[data-ev]").forEach((b) => (b.onclick = () => {
      live.picked = live.events.find((e) => e.i === Number(b.dataset.ev)) ?? null;
      render(false);
    }));
```

Poll the trace every 500 ms while the panel is open, and add the docked mode. Replace `open`, `close`, `toggle` and
the keydown listener:

```ts
  const gameDiv = document.getElementById("game")!;
  function setDocked(on: boolean) {
    docked = on;
    el.classList.toggle("docked", on);
    // the game refits into the space left of the panel and keeps running
    gameDiv.style.right = on ? `${el.getBoundingClientRect().width}px` : "0";
    game.scale.refresh();
  }
  function open(dock = false) {
    el.classList.add("open");
    el.setAttribute("aria-hidden", "false");
    setDocked(dock);
    if (!dock) game.pause();
    fetchData();
    timer = window.setInterval(fetchData, 2500);
    fast = window.setInterval(async () => {
      const c = api.current;
      if (tab === "Live" && c && !c.offline && await pollTrace(c.case_id)) render(false);
    }, 500);
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
    if (e.code === "Backquote") { e.preventDefault(); toggle(e.shiftKey); }
    else if (e.key === "Escape" && el.classList.contains("open")) close();
  }, true);
```

Keep the `?judges` button, but make it open docked: `b.onclick = () => toggle(true);` and label it
`"Observatory ( ` · ⇧` docks )"`.

Docked mode needs the page width at open time: `setDocked` reads the panel's width after the `docked` class is
applied, so call `el.classList.toggle("docked", on)` before measuring (as written above).

- [ ] **Step 3: Type-check**

Run: `cd game && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 4: Check it against the fixture**

Open `http://localhost:8872/?case=ohm&judges&fixture`, walk to a suspect, press Shift+`` ` ``.
Expected:
- the panel sits on the right and the game, still animating, fits in the space to its left;
- the Live tab shows lanes Volta, Ohmar, Glim, Footnote (coach), Detective, Router;
- Ohmar's lane has a red `critique: LEAK` pill followed by `redraft`; Glim's has a red `firewall BLOCK`;
  Volta's has a gold `critique skipped (low risk)`; Router has a gold `route`;
- Ohmar's stress meter reads `GUARDED 4/9`;
- clicking any pill shows its JSON under Step detail; the firewall feed lists the block and the redraft;
- `` ` `` without Shift still opens the old full drawer and pauses the game; Esc closes either.

- [ ] **Step 5: Commit**

```bash
git add game/src/systems/observatory.ts game/src/systems/inside.ts
git commit -m "Observatory: live agent lanes, stress meters and the firewall feed, dockable beside the game"
```

---

### Task 2: Red team and Gate replay tabs (T+24–34)

**Files:**
- Modify: `game/src/systems/observatory.ts`, `game/src/systems/inside.ts`

**Interfaces:**
- Consumes: `GET /api/redteam/{kit}` (§3.2), `GET /api/replay/{kit}?seed=` (§3.3), or the fixtures.
- Produces: `observatory.ts` exports `RedTeam`, `Replay`, `loadRedTeam(kit)`, `redTeamHtml(rt)`, `replay` state,
  `loadReplay(kit, seed)`, `playReplay(onStep)`, `stopReplay()`, `replayHtml(names)`.

- [ ] **Step 1: Add the two views to `observatory.ts`**

```ts
export interface RedTeam {
  kit: string; seed: number; attacks: number;
  by_layer: { held: number; critique: number; firewall: number; slipped: number };
  rows: { class: string; attack: string; layer: string; reply: string }[];
}
export interface Replay { kit: string; seed: number; culprit: string; result: { no_lab: string | null; with_lab: string | null }; events: TraceEvent[] }

async function getJson<T>(url: string): Promise<T | null> {
  try { const r = await fetch(url); return r.ok ? ((await r.json()) as T) : null; } catch { return null; }
}

export const loadRedTeam = (kit: string) => getJson<RedTeam>(FIXTURE ? "/fixtures/redteam_sample.json" : `/api/redteam/${kit}`);

const LAYER = { held: ["held by the suspect", "ok"], critique: ["caught by critique", "gold"],
                firewall: ["caught by firewall", "red"], slipped: ["slipped through", "red"] } as const;

export function redTeamHtml(rt: RedTeam | null) {
  if (!rt) return '<div class="card muted">No red-team run for this case yet.</div>';
  const seg = (k: keyof RedTeam["by_layer"], color: string) => rt.by_layer[k]
    ? `<i style="flex:${rt.by_layer[k]};background:${color}" title="${LAYER[k][0]}: ${rt.by_layer[k]}"></i>` : "";
  return `
  <div class="card"><h3>Red team · ${rt.attacks} attacks on the culprit</h3>
    <div class="stack">${seg("held", "var(--ok)")}${seg("critique", "var(--gold)")}${seg("firewall", "var(--pen)")}${seg("slipped", "#fff")}</div>
    <div>${(Object.keys(LAYER) as (keyof typeof LAYER)[]).map((k) =>
      `<span class="tag ${LAYER[k][1]}">${LAYER[k][0]}: ${rt.by_layer[k]}</span>`).join(" ")}</div></div>
  <div class="card"><table><tr><th>Attack</th><th>Stopped by</th><th>Player saw</th></tr>
    ${rt.rows.map((r) => `<tr><td><span class="tag">${esc(r.class)}</span> ${esc(r.attack)}</td>
      <td><span class="tag ${LAYER[r.layer as keyof typeof LAYER]?.[1] ?? ""}">${esc(r.layer)}</span></td><td>${esc(r.reply)}</td></tr>`).join("")}
  </table></div>`;
}

/** The gate replay plays back on the recorded clock (dt, ms), at 1x or 2x. */
export const replay = { body: null as Replay | null, shown: 0, speed: 2, timers: [] as number[] };

export async function loadReplay(kit: string, seed: number) {
  stopReplay();
  replay.body = await getJson<Replay>(FIXTURE ? "/fixtures/replay_sample.json" : `/api/replay/${kit}?seed=${seed}`);
  replay.shown = 0;
  return replay.body;
}

export function playReplay(onStep: () => void) {
  stopReplay();
  replay.shown = 0;
  replay.body?.events.forEach((e, n) => replay.timers.push(window.setTimeout(() => {
    replay.shown = n + 1;
    onStep();
  }, (e.dt ?? 0) / replay.speed)));
}

export function stopReplay() {
  replay.timers.forEach((t) => window.clearTimeout(t));
  replay.timers = [];
}

export function replayHtml(names: Record<string, string>) {
  const b = replay.body;
  if (!b) return '<div class="card muted">No gate replay recorded for this seed.</div>';
  const seen = b.events.slice(0, replay.shown);
  const done = replay.shown >= b.events.length;
  const who = (sid: string | null) => esc(sid ? names[sid] ?? sid : "nobody");
  return `
  <div class="card"><h3>Release gate · seed ${b.seed} · the detective agent plays the case twice</h3>
    <div><button class="act" id="obs-play" type="button">${replay.shown && !done ? "Restart" : "Play"}</button>
      <button type="button" class="pill ok" id="obs-speed">${replay.speed}×</button>
      <span class="muted">${replay.shown}/${b.events.length} steps</span></div>
    ${lanesHtml(seen, {}, names, null)}</div>
  ${done ? `<div class="card"><h3>Verdict</h3>
    <div class="row"><span>No lab</span><span>accused <b>${who(b.result.no_lab)}</b>
      ${b.result.no_lab === b.culprit ? '<span class="tag gold">lucky guess</span>' : '<span class="tag ok">couldn\'t tell: the science is needed</span>'}</span></div>
    <div class="row"><span>With the lab</span><span>accused <b>${who(b.result.with_lab)}</b>
      ${b.result.with_lab === b.culprit ? '<span class="tag ok">solved: the science is enough</span>' : '<span class="tag red">missed</span>'}</span></div></div>` : ""}`;
}
```

Append to `OBS_CSS`:

```css
#inside .stack{display:flex;height:16px;border:1px solid var(--rule);border-radius:2px;overflow:hidden}
#inside .stack i{display:block}
```

Extend `obsKey()` so replay progress redraws:

```ts
export function obsKey() {
  return `${live.cid}:${live.next}:${live.events.length}:${live.picked?.i ?? -1}:${replay.shown}:${replay.speed}:${replay.body?.seed ?? ""}`;
}
```

- [ ] **Step 2: Add the tabs in `inside.ts`**

```ts
import { live, pollTrace, lanesHtml, feedHtml, detailHtml, obsKey, OBS_CSS,
         loadRedTeam, redTeamHtml, loadReplay, playReplay, stopReplay, replay, replayHtml, type RedTeam } from "./observatory";
...
const TABS = ["Live", "Red team", "Gate replay", "Overview", "Suspects", "Filter", "Coach & lab"] as const;
...
  let board: RedTeam | null = null;
```

Views:

```ts
    "Red team": () => redTeamHtml(board),
    "Gate replay": (d) => replayHtml(Object.fromEntries(Object.entries(d.suspects).map(([sid, s]) => [sid, s.name]))),
```

Load each when its tab is chosen. Replace the tab button handler in `render()`:

```ts
    el.querySelectorAll<HTMLButtonElement>("[data-tab]").forEach((b) => (b.onclick = async () => {
      tab = b.dataset.tab as Tab;
      if (tab !== "Gate replay") stopReplay();
      if (tab === "Red team" && data) board = await loadRedTeam(data.kit);
      if (tab === "Gate replay" && data && replay.body?.seed !== data.seed) await loadReplay(data.kit, data.seed);
      render();
    }));
    const play = el.querySelector<HTMLButtonElement>("#obs-play");
    if (play) play.onclick = () => playReplay(() => render(false));
    const speed = el.querySelector<HTMLButtonElement>("#obs-speed");
    if (speed) speed.onclick = () => { replay.speed = replay.speed === 2 ? 1 : 2; render(false); };
```

Add `board` to the redraw key: `JSON.stringify([tab, data, note, tests, obsKey(), board?.attacks])`. Call
`stopReplay()` in `close()`.

- [ ] **Step 3: Type-check**

Run: `cd game && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 4: Check against the fixtures**

Open `?case=ohm&judges&fixture`, Shift+`` ` ``.
Expected:
- Red team: a four-colour bar (3 green, 2 gold, 1 red, 1 white) with tags `held by the suspect: 3`,
  `caught by critique: 2`, `caught by firewall: 1`, `slipped through: 1`; the 7-row table below.
- Gate replay: Play shows the steps appearing one by one (four steps, about 2.5 s at 2×); at the end the
  verdict card reads "No lab: accused Volta, couldn't tell" and "With the lab: accused Ohmar, solved".
- Switching tabs mid-replay stops it; the speed button flips 2× ↔ 1×.

- [ ] **Step 5: Commit**

```bash
git add game/src/systems/observatory.ts game/src/systems/inside.ts
git commit -m "Observatory: red-team board and the gate replay"
```

---

### Task 3: Voice (T+14–20, polish T+24–34)

**Files:**
- Create: `game/src/systems/voice.ts`
- Modify: `game/src/systems/ui.ts` (`askBox`), `game/src/systems/district.ts` (`interrogate`), `game/src/audio.ts` (`blip`),
  `game/src/main.ts`

**Interfaces:**
- Produces: `voice.ts` exports `installVoiceToggle()`, `canListen(): boolean`, `listen(onText: (text: string, final: boolean) => void):
  () => void` (returns a stop function), `speak(who: string, text: string): Promise<void>`, `hush(): void`,
  `speaking(): boolean`, `voiceMode(): "off" | "on" | "suspects"`, `setVoiceMode(m)`.

- [ ] **Step 1: Create `voice.ts`**

```ts
// Talking to the suspects out loud: hold-to-talk speech recognition in, browser speech synthesis out.
// Both are on-device or browser-provided and free. Typing always works; without recognition the mic hides.
import { voiceOf } from "../audio/voices";

type Mode = "off" | "on" | "suspects";
const KEY = "smudge.voice";

export function voiceMode(): Mode {
  try { return (localStorage.getItem(KEY) as Mode) || "suspects"; } catch { return "suspects"; }
}
export function setVoiceMode(m: Mode) {
  try { localStorage.setItem(KEY, m); } catch { /* private window: this session only */ }
}

const Rec: any = (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition;
export const canListen = () => Boolean(Rec) && voiceMode() !== "off";

/** Start listening; onText gets interim and final transcripts. Call the returned function to stop. */
export function listen(onText: (text: string, final: boolean) => void): () => void {
  hush();                                    // talking over a suspect cuts them off
  const rec = new Rec();
  rec.lang = "en-IN";
  rec.interimResults = true;
  rec.continuous = true;
  rec.onresult = (e: any) => {
    let text = "", final = false;
    for (let n = 0; n < e.results.length; n++) {
      text += e.results[n][0].transcript;
      final = e.results[n].isFinal;
    }
    onText(text.trim(), final);
  };
  rec.onerror = () => { /* no mic, denied, or offline: typing still works */ };
  try { rec.start(); } catch { /* already running */ }
  return () => { try { rec.stop(); } catch { /* already stopped */ } };
}

let talking = false;
export const speaking = () => talking;

/** Speak a reply in this speaker's voice: pitch follows their blip voice, deep voices also slow down. */
export function speak(who: string, text: string): Promise<void> {
  const mode = voiceMode();
  if (mode === "off" || !("speechSynthesis" in window) || (mode === "suspects" && (who === "smudge" || who === "foot"))) {
    return Promise.resolve();
  }
  hush();
  const v = voiceOf(who);
  const mid = (v.lo + v.hi) / 2;
  const u = new SpeechSynthesisUtterance(text);
  u.pitch = Math.min(2, Math.max(0.1, mid / 220));
  u.rate = Math.min(1.3, Math.max(0.75, 0.8 + mid / 1500));
  u.lang = "en-IN";
  talking = true;
  return new Promise((resolve) => {
    u.onend = u.onerror = () => { talking = false; resolve(); };
    speechSynthesis.speak(u);
  });
}

export function hush() {
  if ("speechSynthesis" in window) speechSynthesis.cancel();
  talking = false;
}

const LABEL: Record<Mode, string> = { on: "🗣 Voices: all", suspects: "🗣 Voices: suspects", off: "🗣 Voices: off" };
const NEXT: Record<Mode, Mode> = { suspects: "on", on: "off", off: "suspects" };

/** A small corner button that cycles the voice setting. Top-left, so the docked Observatory never covers it. */
export function installVoiceToggle() {
  const b = document.createElement("button");
  b.type = "button";
  b.style.cssText = `position:fixed;top:max(10px,env(safe-area-inset-top,0px));left:max(10px,env(safe-area-inset-left,0px));z-index:49;
    font:600 12px/1 "Pixelify Sans",monospace;padding:6px 9px;border-radius:3px;border:2px solid #0E1938;background:#F2E9CF;color:#0E1938;cursor:pointer`;
  const show = () => { b.textContent = LABEL[voiceMode()]; };
  b.onclick = () => { setVoiceMode(NEXT[voiceMode()]); if (voiceMode() === "off") hush(); show(); };
  show();
  document.body.appendChild(b);
}
```

In `game/src/main.ts`, after `installAudio(...)`:

```ts
import { installVoiceToggle } from "./systems/voice";
...
installVoiceToggle();
```

(The mic button reads `canListen()` each time an ask box opens, so switching to off hides it from the next question.)

- [ ] **Step 2: Mute blips while speaking (`audio.ts`)**

```ts
import { speaking } from "./systems/voice";
...
export function blip(who: string) {
  if (!started || speaking()) return;
```

- [ ] **Step 3: Mic in the ask box (`ui.ts`)**

Import: `import { canListen, listen } from "./voice";`

In `askBox`, after the `send` button is created and before `form.append(...)`:

```ts
    const mic = document.createElement("button");
    mic.type = "button";
    mic.textContent = "🎙 Hold";
    mic.setAttribute("aria-label", "Hold to ask out loud");
    mic.style.cssText = `font:inherit;padding:4px 10px;border:2px solid #0E1938;background:#F2E9CF;color:#0E1938;border-radius:6px;cursor:pointer;touch-action:none;`;
    let stop: (() => void) | null = null;
    const down = (e: Event) => {
      e.preventDefault();
      mic.style.background = "#F07AAE";
      stop = listen((text) => { input.value = text; });
    };
    const up = () => {
      if (!stop) return;
      stop();
      stop = null;
      mic.style.background = "#F2E9CF";
      // the last words arrive just after release; give them a moment, then ask
      setTimeout(() => { const v = input.value.trim(); if (v) finish(v); }, 450);
    };
    mic.addEventListener("pointerdown", down);
    mic.addEventListener("pointerup", up);
    mic.addEventListener("pointerleave", up);
```

and change the append so the mic only shows when recognition exists:

```ts
    form.append(input, ...(canListen() ? [mic] : []), send, done);
```

- [ ] **Step 4: Speak each reply (`district.ts`, `interrogate`)**

Import: `import { speak } from "./voice";`

Replace the line that shows the reply:

```ts
      const r = await api.ask(who, q);
      const spoken = speak(who, r.answer);
      await this.dlg.say({ who: who as Who, expr: /nothing|none|never|wasn't|not me/i.test(r.answer) ? "smug" : "neutral", text: r.answer });
      await spoken;
```

- [ ] **Step 5: Type-check**

Run: `cd game && npx tsc --noEmit`
Expected: no errors.

- [ ] **Step 6: Check it in Chrome**

Open `?case=ohm`, walk to Volta, open the ask box.
Expected:
- a `🎙 Hold` button sits between the field and Ask; holding it turns it pink and your words appear in the field;
  releasing sends the question;
- Volta's reply is spoken in a higher, faster voice than Ohmar's; no syllable blips play under the speech;
- holding the mic while a reply is being spoken cuts the reply off;
- the top-left `🗣 Voices` button cycles suspects → all → off; on off, the next ask box has no mic and nothing is
  spoken; typing works; the choice survives a reload.
- In Firefox (no recognition): the mic is hidden; replies are still spoken.

- [ ] **Step 7: Commit**

```bash
git add game/src/systems/voice.ts game/src/systems/ui.ts game/src/systems/district.ts game/src/audio.ts game/src/main.ts
git commit -m "Voice: hold to ask out loud, suspects answer in their own voices"
```

---

### Task 4 (cut first): Thought bubbles

**Files:**
- Modify: `game/src/systems/district.ts`

**Interfaces:**
- Consumes: `live.events` from `observatory.ts` (only filled while the Observatory is open and polling).

- [ ] **Step 1: Show the latest plan over the speaking suspect**

In `interrogate`, after `const r = await api.ask(who, q);`:

```ts
      const plan = [...live.events].reverse().find((e) => e.agent === who && e.step === "plan" && e.verdict === "ok");
      if (plan && new URLSearchParams(location.search).has("judges") && this.suspects[who]) {
        // intent and risk only: never the plan's must_avoid list, which can name the case's facts
        const bubble = this.add.text(this.suspects[who].x, this.suspects[who].y - 46, `${plan.data.intent} · risk ${plan.data.risk}`,
          { fontFamily: FONT, fontSize: "8px", color: "#0E1938", backgroundColor: "#F2E9CF", padding: { x: 3, y: 2 } })
          .setOrigin(0.5, 1).setDepth(50);
        this.time.delayedCall(2600, () => bubble.destroy());
      }
```

Add `import { live } from "./observatory";`. `FONT` is already imported from `../consts`.

- [ ] **Step 2: Type-check, check, commit**

Run: `cd game && npx tsc --noEmit` (no errors). With the Observatory docked and the server running, ask a suspect:
a small `deflect · risk high` label appears above them for about 2.5 s; it never shows without `?judges`.

```bash
git add game/src/systems/district.ts
git commit -m "Thought bubbles: a suspect's plan, intent and risk only, for judges"
```

---

### Task 5: Backup video (T+34)

- [ ] Run the full demo from spec §2 live, at `?case=ohm&demo&judges` with the server started with `SMUDGE_DEMO=1`,
  screen-recorded with sound (OBS or the Windows Game Bar, `Win+Alt+R`).
- [ ] Watch it back once start to finish; re-record if a step fails.
- [ ] Copy it to two laptops and a USB stick.
