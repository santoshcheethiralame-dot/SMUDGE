// All sound is synthesised with Tone.js: no audio files to license or load.
//
// Four buses (music, ambience, sfx, voice) meet in a limiter. Scenes ask for what they want (theme, layer,
// ambience) at any time; before the first click or key the browser keeps audio locked, so wishes are remembered
// and played the moment it unlocks. Every call is a no-op until then, so nothing here can throw from a scene.
import * as Tone from "tone";
import { voiceOf, type Voice } from "./audio/voices";
import { THEMES, steps, type Theme } from "./audio/themes";
import { place } from "./audio/ambience";
import { speaking } from "./systems/voice";

let started = false;
let starting: Promise<void> | null = null;
const MUTE_KEY = "smudge.mute";
const LEVEL = { music: -8, amb: 10, sfx: 6, voice: 10 };
const bus = {} as Record<keyof typeof LEVEL, Tone.Volume>;
let reverb: Tone.Reverb;

// what the scenes want right now, applied on unlock
const want = { theme: "night", layer: 0, place: "title", restored: false };

// ---- start-up and the mute switch ----------------------------------------------------------------

export function startAudio(): Promise<void> {
  if (started) return Promise.resolve();
  return (starting ??= (async () => {
    await Tone.start();
    const limiter = new Tone.Limiter(-1).toDestination();
    const master = new Tone.Volume(0).connect(limiter);
    for (const k of Object.keys(LEVEL) as (keyof typeof LEVEL)[]) bus[k] = new Tone.Volume(LEVEL[k]).connect(master);
    reverb = new Tone.Reverb({ decay: 3.2, wet: 0.3 }).connect(master);
    Tone.getDestination().mute = muted();
    buildSfx();
    buildScore();
    Tone.getTransport().start();
    started = true;
    applyTheme(want.theme, true);
    place(want.place, bus.amb, want.restored);
  })());
}

function muted() {
  try { return localStorage.getItem(MUTE_KEY) === "1"; } catch { return false; }
}

export function isMuted() { return started ? Tone.getDestination().mute : muted(); }

export function toggleMute() {
  const m = !isMuted();
  try { localStorage.setItem(MUTE_KEY, m ? "1" : "0"); } catch { /* private window */ }
  if (started) Tone.getDestination().mute = m;
  return m;
}

/** Unlock on the first click or key anywhere, M toggles mute, and a small speaker button sits in the corner. */
export function installAudio(canvas: () => HTMLCanvasElement | undefined) {
  const unlock = () => { void startAudio(); };
  window.addEventListener("pointerdown", unlock, { once: true, capture: true });
  window.addEventListener("keydown", unlock, { once: true, capture: true });
  const btn = document.createElement("button");
  btn.type = "button";
  btn.setAttribute("aria-label", "Sound on or off (M)");
  btn.title = "Sound (M)";
  const draw = () => {
    btn.innerHTML = `<svg viewBox="0 0 16 16" width="100%" height="100%" aria-hidden="true"><path d="M2 6h3l4-3v10l-4-3H2z" fill="#F2E9CF"/>` +
      (isMuted() ? `<path d="M11 6l4 4M15 6l-4 4" stroke="#C9302A" stroke-width="1.6"/>` : `<path d="M11 5.5q2 2.5 0 5M12.6 4q3.4 4 0 8" stroke="#F2E9CF" stroke-width="1.2" fill="none"/>`) + `</svg>`;
  };
  btn.style.cssText = "position:fixed;z-index:20;width:26px;height:26px;padding:4px;border:0;border-radius:6px;" +
    "background:rgba(14,25,56,.55);cursor:pointer;opacity:.55;transition:opacity .15s,transform .1s;";
  btn.onmouseenter = () => { btn.style.opacity = "1"; };
  btn.onmouseleave = () => { btn.style.opacity = ".55"; };
  btn.onpointerdown = (e) => { e.stopPropagation(); btn.style.transform = "scale(.88)"; };
  btn.onpointerup = () => { btn.style.transform = ""; };
  btn.onclick = (e) => { e.stopPropagation(); toggleMute(); draw(); };
  const placeBtn = () => {
    const r = canvas()?.getBoundingClientRect();
    if (!r) return;
    // in the letterbox when there is one, so it never sits on the game; else tucked in the corner
    if (window.innerHeight - r.bottom >= 34) { btn.style.left = `${r.left + 6}px`; btn.style.top = `${r.bottom + 4}px`; }
    else if (r.left >= 34) { btn.style.left = `${r.left - 32}px`; btn.style.top = `${r.bottom - 30}px`; }
    else { btn.style.left = `${r.left + 4}px`; btn.style.top = `${r.bottom - 30}px`; }
  };
  draw();
  document.body.appendChild(btn);
  window.addEventListener("resize", placeBtn);
  window.setInterval(placeBtn, 500);      // the canvas settles its size after load and on panel changes
  window.addEventListener("keydown", (e) => {
    const t = e.target as HTMLElement;
    if (e.key.toLowerCase() === "m" && !(t instanceof HTMLInputElement || t instanceof HTMLTextAreaElement)) { toggleMute(); draw(); }
  });
}

// ---- voices -------------------------------------------------------------------------------------

const voiceSynths = new Map<string, Tone.Synth | Tone.FMSynth>();

function voiceSynth(who: string, v: Voice) {
  let s = voiceSynths.get(who);
  if (!s) {
    const env = { attack: 0.002, decay: v.decay, sustain: 0, release: Math.min(0.05, v.decay) };
    s = v.kind === "fm"
      ? new Tone.FMSynth({ harmonicity: v.harmonicity ?? 2, modulationIndex: v.index ?? 2, oscillator: { type: v.osc }, envelope: env })
      : new Tone.Synth({ oscillator: { type: v.osc }, envelope: env });
    s.volume.value = v.vol;
    s.connect(bus.voice);
    s.connect(reverb);
    voiceSynths.set(who, s);
  }
  return s;
}

/** How many letters go by between blips for this speaker. */
export function blipEvery(who: string) { return voiceOf(who).every; }

/** One syllable of a character's voice. */
export function blip(who: string) {
  if (!started || speaking()) return;
  const v = voiceOf(who);
  const s = voiceSynth(who, v);
  const now = Tone.now();
  const f = v.lo + Math.random() * (v.hi - v.lo);
  try {
    s.triggerAttackRelease(f, v.decay, now);
    if (v.slide) s.frequency.exponentialRampToValueAtTime(f * Math.pow(2, v.slide / 12), now + v.decay);
  } catch { /* skipped */ }
}

// ---- sound effects ------------------------------------------------------------------------------

let plop: Tone.MembraneSynth, noise: Tone.NoiseSynth, rub: Tone.NoiseSynth, rubFilter: Tone.Filter, chime: Tone.PolySynth;
let tickS: Tone.Synth, click: Tone.Synth, swoop: Tone.Synth, swoopF: Tone.Filter, air: Tone.NoiseSynth, airF: Tone.Filter;
let crunch: Tone.NoiseSynth, crunchF: Tone.Filter, clank: Tone.MetalSynth, stab: Tone.PolySynth, sparkle: Tone.PolySynth;
let wrongS: Tone.Synth;

function buildSfx() {
  const out = bus.sfx;
  plop = new Tone.MembraneSynth({ pitchDecay: 0.04, octaves: 4, envelope: { attack: 0.001, decay: 0.25, sustain: 0 } }).connect(out);
  plop.volume.value = -8;
  noise = new Tone.NoiseSynth({ noise: { type: "brown" }, envelope: { attack: 0.3, decay: 1.6, sustain: 0 } }).connect(out);
  noise.volume.value = -4;
  rubFilter = new Tone.Filter(900, "bandpass").connect(out);
  rub = new Tone.NoiseSynth({ noise: { type: "pink" }, envelope: { attack: 0.02, decay: 0.12, sustain: 0.6, release: 0.2 } }).connect(rubFilter);
  rub.volume.value = -10;
  chime = new Tone.PolySynth(Tone.Synth, { oscillator: { type: "sine" }, envelope: { attack: 0.005, decay: 0.6, sustain: 0, release: 0.6 } }).connect(reverb);
  chime.connect(out);
  chime.volume.value = -16;
  tickS = new Tone.Synth({ oscillator: { type: "sine" }, envelope: { attack: 0.001, decay: 0.03, sustain: 0, release: 0.01 } }).connect(out);
  tickS.volume.value = -18;
  click = new Tone.Synth({ oscillator: { type: "square" }, envelope: { attack: 0.001, decay: 0.018, sustain: 0, release: 0.01 } })
    .connect(new Tone.Filter(900, "highpass").connect(out));
  click.volume.value = -26;
  swoopF = new Tone.Filter(1200, "lowpass").connect(out);
  swoop = new Tone.Synth({ oscillator: { type: "triangle" }, envelope: { attack: 0.005, decay: 0.12, sustain: 0.3, release: 0.08 } }).connect(swoopF);
  swoop.volume.value = -16;
  airF = new Tone.Filter({ type: "bandpass", frequency: 800, Q: 0.8 }).connect(out);
  air = new Tone.NoiseSynth({ noise: { type: "pink" }, envelope: { attack: 0.06, decay: 0.25, sustain: 0, release: 0.1 } }).connect(airF);
  air.volume.value = -10;
  crunchF = new Tone.Filter(1800, "lowpass").connect(out);
  crunch = new Tone.NoiseSynth({ noise: { type: "white" }, envelope: { attack: 0.002, decay: 0.05, sustain: 0 } }).connect(crunchF);
  crunch.volume.value = -22;
  clank = new Tone.MetalSynth({ envelope: { attack: 0.001, decay: 0.12, release: 0.05 }, harmonicity: 5.1, modulationIndex: 20, resonance: 3000, octaves: 1.2 }).connect(out);
  clank.volume.value = -30;
  stab = new Tone.PolySynth(Tone.Synth, { oscillator: { type: "sawtooth" }, envelope: { attack: 0.004, decay: 0.25, sustain: 0.1, release: 0.3 } })
    .connect(new Tone.Filter(2200, "lowpass").connect(out));
  stab.connect(reverb);
  stab.volume.value = -18;
  sparkle = new Tone.PolySynth(Tone.FMSynth, { harmonicity: 3.01, modulationIndex: 3, envelope: { attack: 0.001, decay: 0.5, sustain: 0, release: 0.4 } }).connect(reverb);
  sparkle.connect(out);
  sparkle.volume.value = -24;
  wrongS = new Tone.Synth({ oscillator: { type: "square" }, envelope: { attack: 0.003, decay: 0.06, sustain: 0.4, release: 0.05 } })
    .connect(new Tone.Filter(1200, "lowpass").connect(out));
  wrongS.volume.value = -20;
}

const glide = (s: Tone.Synth, from: number, to: number, dur: number, t: number) => {
  s.triggerAttack(from, t);
  s.frequency.setValueAtTime(from, t);
  s.frequency.exponentialRampToValueAtTime(to, t + dur);
  s.triggerRelease(t + dur);
};

const whoosh = (t: number, from: number, to: number, dur: number) => {
  airF.frequency.setValueAtTime(from, t);
  airF.frequency.exponentialRampToValueAtTime(to, t + dur);
  air.triggerAttackRelease(dur, t);
};

export type Sfx = "plop" | "rumble" | "rubStart" | "rubStop" | "chime" | "pop" | "step" | "swish" | "tick" | "splash" | "strike"
  | "fanfare" | "wrong" | "hover" | "click" | "open" | "close" | "type" | "flip" | "stamp" | "whoosh" | "thunk" | "zap" | "hop"
  | "snap" | "crack" | "sparkle" | "rise" | "drop" | "heart" | "select" | "back" | "deny";

let lastHover = 0;

export function sfx(name: Sfx) {
  if (!started) return;
  // a voice still busy with a sound scheduled a moment ahead can refuse a new one: drop it, never throw
  try { playSfx(name); } catch { /* skipped */ }
}

function playSfx(name: Sfx) {
  const now = Tone.now() + 0.005;
  switch (name) {
    case "plop": plop.triggerAttackRelease("C2", 0.2, now); break;
    case "pop": plop.triggerAttackRelease("G3", 0.1, now); break;
    case "step": plop.triggerAttackRelease("A1", 0.05, now, 0.25); break;
    case "rumble": noise.triggerAttackRelease(2.2, now); break;
    case "rubStart": rub.triggerAttack(now); rubFilter.frequency.rampTo(1400, 0.4); break;
    case "rubStop": rub.triggerRelease(now); break;
    case "chime": chime.triggerAttackRelease(["E5", "B5", "G#5"], 0.4, now); break;
    case "swish": whoosh(now, 400, 2400, 0.3); break;
    case "tick": tickS.triggerAttackRelease(1200, 0.02, now); break;
    case "splash": plop.triggerAttackRelease("E2", 0.3, now); noise.triggerAttackRelease(0.25, now + 0.02); break;
    case "strike":
      noise.triggerAttackRelease(0.6, now); plop.triggerAttackRelease("C1", 0.5, now);
      stab.triggerAttackRelease(["C4", "G4", "C5", "Eb5"], 0.35, now);
      chime.triggerAttackRelease(["C5", "G5", "C6"], 0.5, now + 0.15); break;
    case "fanfare":
      chime.triggerAttackRelease(["C5", "E5", "G5"], 0.3, now); chime.triggerAttackRelease(["D5", "F#5", "A5"], 0.3, now + 0.3);
      chime.triggerAttackRelease(["E5", "G#5", "B5", "E6"], 0.9, now + 0.6); break;
    case "wrong": glide(wrongS, 220, 150, 0.12, now); glide(wrongS, 160, 98, 0.22, now + 0.16); break;
    case "deny": glide(wrongS, 300, 240, 0.06, now); break;
    // the UI: quiet, short, tactile
    case "hover": if (now - lastHover > 0.05) { lastHover = now; tickS.triggerAttackRelease(2200, 0.012, now, 0.35); } break;
    case "click": click.triggerAttackRelease(1600, 0.01, now); plop.triggerAttackRelease("C4", 0.04, now, 0.2); break;
    case "select": glide(swoop, 520, 780, 0.06, now); break;
    case "back": glide(swoop, 620, 420, 0.07, now); break;
    case "type": click.triggerAttackRelease(900 + Math.random() * 500, 0.006, now, 0.5); break;
    case "open": whoosh(now, 500, 1800, 0.16); tickS.triggerAttackRelease(900, 0.015, now + 0.12, 0.4); break;
    case "close": whoosh(now, 1600, 500, 0.12); break;
    case "flip": whoosh(now, 900, 3200, 0.22); crunch.triggerAttackRelease(0.03, now + 0.18); break;
    case "whoosh": whoosh(now, 300, 3000, 0.35); break;
    case "stamp": plop.triggerAttackRelease("D2", 0.12, now); crunch.triggerAttackRelease(0.04, now); break;
    case "thunk": plop.triggerAttackRelease("G1", 0.25, now); clank.triggerAttackRelease(80, 0.05, now, 0.4); break;
    case "zap": glide(swoop, 2600, 140, 0.08, now); crunch.triggerAttackRelease(0.03, now); break;
    case "hop": glide(swoop, 300, 640, 0.07, now); break;
    case "drop": glide(swoop, 700, 200, 0.12, now); break;
    case "snap": click.triggerAttackRelease(2400, 0.008, now); tickS.triggerAttackRelease(1800, 0.02, now + 0.01); break;
    case "crack": crunch.triggerAttackRelease(0.08, now); clank.triggerAttackRelease(300, 0.1, now, 0.6); break;
    case "sparkle": sparkle.triggerAttackRelease(["E6", "B6"], 0.2, now); sparkle.triggerAttackRelease(["G#6", "E7"], 0.25, now + 0.08); break;
    case "rise": whoosh(now, 200, 4000, 0.7); break;
    case "heart": plop.triggerAttackRelease("A0", 0.12, now, 0.8); plop.triggerAttackRelease("A0", 0.1, now + 0.18, 0.5); break;
  }
}

/** One footstep on the ground this place is made of. */
export type Ground = "wood" | "stone" | "snow" | "dirt" | "metal";
export function step(ground: Ground) {
  if (!started) return;
  try { playStep(ground); } catch { /* skipped */ }
}

function playStep(ground: Ground) {
  const now = Tone.now();
  const v = 0.8 + Math.random() * 0.2;
  switch (ground) {
    case "wood": plop.triggerAttackRelease(Math.random() < 0.5 ? "A2" : "G2", 0.04, now, 0.22 * v); click.triggerAttackRelease(700, 0.004, now, 0.25); break;
    case "stone": crunchF.frequency.setValueAtTime(3000, now); crunch.triggerAttackRelease(0.02, now, 0.5 * v); plop.triggerAttackRelease("E2", 0.02, now, 0.12); break;
    case "snow": crunchF.frequency.setValueAtTime(900, now); crunch.triggerAttackRelease(0.09, now, 0.8 * v); break;
    case "dirt": crunchF.frequency.setValueAtTime(1400, now); crunch.triggerAttackRelease(0.04, now, 0.6 * v); plop.triggerAttackRelease("A1", 0.03, now, 0.15); break;
    case "metal": clank.triggerAttackRelease(160 + Math.random() * 40, 0.03, now, 0.35 * v); break;
  }
}

// ---- the score ----------------------------------------------------------------------------------

let pad: Tone.PolySynth, bass: Tone.MonoSynth, lead: Tone.PolySynth<Tone.Synth> | Tone.PolySynth<Tone.FMSynth>;
let kick: Tone.MembraneSynth, hat: Tone.NoiseSynth, echo: Tone.FeedbackDelay;
const layerVol: Tone.Volume[] = [];
let leadVol: Tone.Volume;
let theme: Theme | null = null;
let themeName = "";
let step16 = 0;
let musicOn = true;
let ducked = false;

function buildScore() {
  for (let i = 0; i < 4; i++) layerVol.push(new Tone.Volume(-60).connect(bus.music));
  const roomy = new Tone.Reverb({ decay: 4, wet: 0.35 }).connect(layerVol[0]);
  pad = new Tone.PolySynth(Tone.Synth, { oscillator: { type: "sine" }, envelope: { attack: 1.2, decay: 1, sustain: 0.6, release: 2.5 } }).connect(roomy);
  pad.volume.value = -9;
  bass = new Tone.MonoSynth({ oscillator: { type: "triangle" }, filter: { Q: 1, type: "lowpass" },
    envelope: { attack: 0.01, decay: 0.3, sustain: 0.3, release: 0.3 }, filterEnvelope: { attack: 0.01, decay: 0.2, sustain: 0.2, baseFrequency: 160, octaves: 2.2 } })
    .connect(layerVol[1]);
  bass.volume.value = -7;
  echo = new Tone.FeedbackDelay("8n.", 0.3).connect(layerVol[2]);
  leadVol = new Tone.Volume(-8).connect(layerVol[2]);
  leadVol.connect(echo);
  kick = new Tone.MembraneSynth({ pitchDecay: 0.05, octaves: 5, envelope: { attack: 0.001, decay: 0.3, sustain: 0 } }).connect(layerVol[3]);
  kick.volume.value = -10;
  hat = new Tone.NoiseSynth({ noise: { type: "white" }, envelope: { attack: 0.001, decay: 0.03, sustain: 0 } })
    .connect(new Tone.Filter(6000, "highpass").connect(layerVol[3]));
  hat.volume.value = -26;
  new Tone.Loop((time) => tickScore(time), "16n").start(0);
}

function makeLead(t: Theme) {
  lead?.dispose();
  const env = { attack: 0.005, decay: t.lead.decay, sustain: 0, release: t.lead.decay * 0.6 };
  lead = t.lead.kind === "fm"
    ? new Tone.PolySynth(Tone.FMSynth, { harmonicity: t.lead.harmonicity ?? 2, modulationIndex: t.lead.index ?? 2, oscillator: { type: t.lead.osc }, envelope: env })
    : new Tone.PolySynth(Tone.Synth, { oscillator: { type: t.lead.osc }, envelope: env });
  lead.maxPolyphony = 6;
  lead.volume.value = t.lead.vol;
  lead.connect(leadVol);
  echo.wet.value = t.lead.echo;
}

function tickScore(time: number) {
  try { playStep16(time); } catch { step16++; }
}

function playStep16(time: number) {
  if (!theme || !musicOn) return;
  const s = step16 % 16, bar = Math.floor(step16 / 16);
  const ci = bar % theme.chords.length;
  if (s === 0) pad.triggerAttackRelease(theme.chords[ci], "1m", time);
  if (want.layer >= 1 && theme.bassSteps.includes(s)) bass.triggerAttackRelease(theme.bass[ci], "8n", time);
  if (want.layer >= 2) {
    const n = steps(theme.motif[bar % theme.motif.length])[s];
    if (n) lead.triggerAttackRelease(n, "8n", time);
  }
  if (want.layer >= 3) {
    if (theme.kick.includes(s)) kick.triggerAttackRelease("C1", "8n", time);
    if (theme.hat.includes(s)) hat.triggerAttackRelease("32n", time);
  }
  step16++;
}

function applyTheme(name: string, instant = false) {
  const t = THEMES[name];
  if (!t || !started) return;
  if (name === themeName && musicOn) { applyLayer(); return; }
  const swap = () => {
    theme = t;
    themeName = name;
    musicOn = true;
    step16 = 0;
    pad.set({ oscillator: { type: t.pad } });
    makeLead(t);
    Tone.getTransport().bpm.value = t.bpm;
    bus.music.volume.rampTo(LEVEL.music - (ducked ? 9 : 0), 0.8);
    applyLayer();
  };
  if (instant || !theme) { swap(); return; }
  bus.music.volume.rampTo(-60, 0.6);
  pad.releaseAll();
  setTimeout(swap, 650);
}

function applyLayer() {
  layerVol.forEach((v, i) => v.volume.rampTo(i <= want.layer ? 0 : -60, i <= want.layer ? 2.5 : 1));
}

/** Switch the score to a place's theme ("night", "lab", "tense" or a case kit). */
export function themeFor(name: string) {
  want.theme = THEMES[name] ? name : "night";
  if (started) applyTheme(want.theme);
}

/** How much of the score plays: 0 pad, 1 + bass, 2 + motif, 3 + percussion. */
export function layer(n: number) {
  want.layer = Math.max(0, Math.min(3, n));
  if (started) applyLayer();
}

/** Older API, kept: a mood is a theme. "off" lets the score fall silent. */
export function music(mood: "night" | "tense" | "off" | "lab") {
  if (mood === "off") {
    if (!started) return;
    musicOn = false;
    pad.releaseAll();
    bus.music.volume.rampTo(-60, 0.4);
    themeName = "";
    return;
  }
  themeFor(mood);
  if (mood === "tense") layer(Math.max(want.layer, 1));
}

/** Levels of each bus in dB, live: for tuning the mix from the console. */
export function meters() {
  if (!started) return null;
  return Object.fromEntries((Object.keys(bus) as (keyof typeof LEVEL)[]).map((k) => [k, bus[k]]));
}

/** The soundscape for a place: a case kit, "title", "hq", "map", "lab", "crossexam", or "none". */
export function ambience(key: string, restored = false) {
  want.place = key;
  want.restored = restored;
  if (started) place(key, bus.amb, restored);
}

/**
 * A scream that falls away: three detuned sawtooth voices and a breath of noise through "aah" vowel formants
 * (800, 1150, 2600 Hz), with vibrato. The pitch leaps up into the cry, holds, then drops as the voice falls away.
 * old: band-limited like a gramophone horn, dry; otherwise out in the courtyard, with reverb.
 */
export function scream(old = false) {
  if (!started || Tone.getContext().state !== "running") return;
  const t = Tone.now() + 0.02, dur = 1.3;
  const nodes: Tone.ToneAudioNode[] = [];
  const keep = <T extends Tone.ToneAudioNode>(n: T) => (nodes.push(n), n);
  const out = keep(new Tone.Gain(0)).connect(bus.sfx);
  if (!old) out.connect(reverb);
  const colour = keep(old ? new Tone.Filter({ type: "bandpass", frequency: 1300, Q: 0.8 }) : new Tone.Filter(7000, "lowpass"));
  colour.chain(keep(new Tone.Distortion(old ? 0.35 : 0.15)), out);
  const voice = keep(new Tone.Gain(1));
  for (const [f, q, g] of [[800, 5, 0], [1150, 7, -3], [2600, 9, -10]]) {
    voice.chain(keep(new Tone.Filter({ type: "bandpass", frequency: f, Q: q })), keep(new Tone.Gain(Tone.dbToGain(g))), colour);
  }
  const vib = keep(new Tone.LFO({ frequency: 6.2, min: -45, max: 45 }));
  for (const r of [1, 1.006, 0.993]) {
    const o = keep(new Tone.Oscillator({ type: "sawtooth" })).connect(voice);
    vib.connect(o.detune);
    o.frequency.setValueAtTime(360 * r, t);
    o.frequency.exponentialRampToValueAtTime(880 * r, t + 0.14);
    o.frequency.linearRampToValueAtTime(950 * r, t + 0.6);
    o.frequency.exponentialRampToValueAtTime(380 * r, t + dur);
    o.start(t).stop(t + dur + 0.05);
  }
  const breath = keep(new Tone.Noise("pink"));
  breath.chain(keep(new Tone.Filter(1800, "highpass")), keep(new Tone.Gain(Tone.dbToGain(-12))), voice);
  breath.start(t).stop(t + dur + 0.05);
  vib.start(t).stop(t + dur + 0.05);
  out.gain.setValueAtTime(0, t);
  out.gain.linearRampToValueAtTime(old ? 0.42 : 0.32, t + 0.07);
  out.gain.linearRampToValueAtTime(old ? 0.34 : 0.26, t + 0.7);
  out.gain.exponentialRampToValueAtTime(0.001, t + dur);
  setTimeout(() => nodes.forEach((n) => { try { n.dispose(); } catch { /* gone */ } }), (dur + 4) * 1000);
}

/** Music and ambience step back while someone is talking. */
export function duck(on: boolean) {
  if (!started || on === ducked) return;
  ducked = on;
  if (musicOn) bus.music.volume.rampTo(LEVEL.music - (on ? 9 : 0), on ? 0.15 : 0.6);
  bus.amb.volume.rampTo(LEVEL.amb - (on ? 5 : 0), on ? 0.15 : 0.6);
}

/** Short musical punctuation, in the current theme's key. */
export function sting(name: "chapter" | "intro" | "evidence" | "holdit" | "solved" | "progress") {
  if (!started) return;
  try { playSting(name); } catch { /* skipped */ }
}

function playSting(name: "chapter" | "intro" | "evidence" | "holdit" | "solved" | "progress") {
  const now = Tone.now() + 0.01;
  const chord = (theme ?? THEMES.night).chords[0].map((n) => Tone.Frequency(n).transpose(12).toNote());
  switch (name) {
    case "chapter":
      whoosh(now, 200, 3000, 0.6);
      chord.forEach((n, i) => sparkle.triggerAttackRelease(Tone.Frequency(n).transpose(12).toNote(), 0.5, now + 0.35 + i * 0.09));
      stab.triggerAttackRelease(chord, 0.8, now + 0.35 + chord.length * 0.09);
      break;
    case "intro":
      stab.triggerAttackRelease(chord.map((n) => Tone.Frequency(n).transpose(-12).toNote()), 0.08, now);
      stab.triggerAttackRelease(chord, 0.22, now + 0.14);
      break;
    case "progress":
      chord.forEach((n, i) => chime.triggerAttackRelease(n, 0.35, now + i * 0.07));
      break;
    case "evidence":
      sfx("sparkle");
      chime.triggerAttackRelease(chord, 0.7, now + 0.12);
      break;
    case "holdit":
      plop.triggerAttackRelease("C1", 0.3, now);
      stab.triggerAttackRelease(["C4", "Eb4", "G4", "C5"], 0.12, now);
      stab.triggerAttackRelease(["D4", "F4", "Ab4", "D5"], 0.3, now + 0.12);
      break;
    case "solved":
      sfx("fanfare");
      break;
  }
}
