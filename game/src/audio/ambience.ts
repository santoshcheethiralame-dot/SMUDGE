// Ambience: one synthesised soundscape per place, built from filtered noise beds, hums and little random events
// (gulls, bells, drips, crackles). place() crossfades from the old bed to the new one.
import * as Tone from "tone";

type Fn = (t: number) => void;

interface Bed { gain: Tone.Gain; nodes: { dispose(): unknown }[]; timers: number[]; alive: boolean }

let current: Bed | null = null;
let currentKey = "";

const db = (d: number) => Tone.dbToGain(d);

/** Crossfade to the soundscape for `key` (a case kit, "title", "hq", "map", "lab", "crossexam" or "none"). */
export function place(key: string, out: Tone.ToneAudioNode, restored = false) {
  const full = `${key}:${restored}`;
  if (full === currentKey) return;
  currentKey = full;
  const old = current;
  if (old) {
    old.gain.gain.rampTo(0, 1.4);
    setTimeout(() => kill(old), 1700);
  }
  current = null;
  const recipe = RECIPES[key];
  if (!recipe) return;
  const bed: Bed = { gain: new Tone.Gain(0).connect(out), nodes: [], timers: [], alive: true };
  bed.nodes.push(bed.gain);
  recipe(kit(bed), restored);
  bed.gain.gain.rampTo(1, 1.6);
  current = bed;
}

function kill(b: Bed) {
  b.alive = false;
  b.timers.forEach(clearTimeout);
  for (const n of b.nodes) {
    try { (n as any).stop?.(); } catch { /* already stopped */ }
    n.dispose();
  }
}

/** The building blocks one recipe uses, all wired into its bed and torn down with it. */
function kit(b: Bed) {
  const keep = <T extends { dispose(): unknown }>(n: T) => (b.nodes.push(n), n);

  /** A filtered noise bed. lfo sweeps the filter (Hz), swell breathes the level (0..1). */
  const noise = (color: "white" | "pink" | "brown", type: BiquadFilterType, freq: number, level: number,
    o: { q?: number; lfo?: [number, number, number]; swell?: [number, number, number] } = {}) => {
    const g = keep(new Tone.Gain(db(level))).connect(b.gain);
    const f = keep(new Tone.Filter({ type, frequency: freq, Q: o.q ?? 1 })).connect(g);
    keep(new Tone.Noise(color)).connect(f).start();
    if (o.lfo) keep(new Tone.LFO({ frequency: o.lfo[0], min: o.lfo[1], max: o.lfo[2] })).connect(f.frequency).start();
    if (o.swell) {
      g.gain.value = 0;
      keep(new Tone.LFO({ frequency: o.swell[0], min: db(level) * o.swell[1], max: db(level) * o.swell[2] })).connect(g.gain).start();
    }
  };

  /** A steady electrical hum. */
  const hum = (freq: number, type: OscillatorType, level: number, cutoff: number) => {
    const g = keep(new Tone.Gain(db(level))).connect(b.gain);
    const f = keep(new Tone.Filter(cutoff, "lowpass")).connect(g);
    keep(new Tone.Oscillator(freq, type as any)).connect(f).start();
  };

  /** Run fn at random gaps between lo and hi seconds, for as long as the bed lives. */
  const every = (lo: number, hi: number, fn: Fn) => {
    const go = () => {
      if (!b.alive) return;
      // a clash on a busy voice drops one sound; it never stops the soundscape
      if (Tone.getContext().state === "running") try { fn(Tone.now() + 0.02); } catch { /* skipped */ }
      b.timers.push(window.setTimeout(go, (lo + Math.random() * (hi - lo)) * 1000));
    };
    b.timers.push(window.setTimeout(go, Math.random() * hi * 1000));
  };

  // event voices, made on first use
  let _chirp: Tone.Synth, _bell: Tone.FMSynth, _pop: Tone.NoiseSynth, _low: Tone.NoiseSynth, _tick: Tone.Synth;
  let _saw: Tone.Synth, _hiss: Tone.NoiseSynth, _clank: Tone.MetalSynth;
  const out = (level: number) => keep(new Tone.Gain(db(level))).connect(b.gain);
  const chirp = () => (_chirp ??= keep(new Tone.Synth({ oscillator: { type: "sine" }, envelope: { attack: 0.005, decay: 0.08, sustain: 0.4, release: 0.05 } }))
    .connect(out(-26)) as Tone.Synth);
  const bell = () => (_bell ??= keep(new Tone.FMSynth({ harmonicity: 3.5, modulationIndex: 6, envelope: { attack: 0.002, decay: 1.8, sustain: 0, release: 1 },
    modulationEnvelope: { attack: 0.002, decay: 0.6, sustain: 0, release: 0.5 } })).connect(out(-30)) as Tone.FMSynth);
  const pop = () => (_pop ??= keep(new Tone.NoiseSynth({ noise: { type: "white" }, envelope: { attack: 0.001, decay: 0.02, sustain: 0 } }))
    .connect(keep(new Tone.Filter(2400, "highpass")).connect(out(-30))) as Tone.NoiseSynth);
  const low = () => (_low ??= keep(new Tone.NoiseSynth({ noise: { type: "brown" }, envelope: { attack: 0.6, decay: 3, sustain: 0 } }))
    .connect(keep(new Tone.Filter(180, "lowpass")).connect(out(-14))) as Tone.NoiseSynth);
  const tick = () => (_tick ??= keep(new Tone.Synth({ oscillator: { type: "square" }, envelope: { attack: 0.001, decay: 0.012, sustain: 0, release: 0.01 } }))
    .connect(keep(new Tone.Filter(1500, "highpass")).connect(out(-34))) as Tone.Synth);
  const saw = () => (_saw ??= keep(new Tone.Synth({ oscillator: { type: "sawtooth" }, envelope: { attack: 0.002, decay: 0.08, sustain: 0.2, release: 0.1 } }))
    .connect(keep(new Tone.Filter(1800, "bandpass")).connect(out(-34))) as Tone.Synth);
  const hiss = () => (_hiss ??= keep(new Tone.NoiseSynth({ noise: { type: "white" }, envelope: { attack: 0.05, decay: 0.6, sustain: 0 } }))
    .connect(keep(new Tone.Filter(3500, "highpass")).connect(out(-32))) as Tone.NoiseSynth);
  const clank = () => (_clank ??= keep(new Tone.MetalSynth({ envelope: { attack: 0.001, decay: 0.3, release: 0.1 }, harmonicity: 5.1, modulationIndex: 16, resonance: 2400, octaves: 1 }))
    .connect(out(-40)) as Tone.MetalSynth);

  const glide = (s: Tone.Synth, from: number, to: number, dur: number, t: number) => {
    s.triggerAttack(from, t);
    s.frequency.setValueAtTime(from, t);
    s.frequency.exponentialRampToValueAtTime(to, t + dur);
    s.triggerRelease(t + dur);
  };

  return {
    noise, hum, every,
    gull: (t: number) => { glide(chirp(), 1500, 950, 0.22, t); glide(chirp(), 1450, 900, 0.26, t + 0.32); },
    birds: (t: number) => { for (let i = 0; i < 3; i++) glide(chirp(), 2600 + Math.random() * 600, 3600, 0.06, t + i * 0.11); },
    cricket: (t: number) => { for (let i = 0; i < 3; i++) { const s = chirp(); s.triggerAttackRelease(4300, 0.015, t + i * 0.045, 0.5); } },
    bubble: (t: number) => glide(chirp(), 280 + Math.random() * 120, 800 + Math.random() * 300, 0.07, t),
    drip: (t: number) => glide(chirp(), 1100, 2300, 0.04, t),
    bell: (t: number, note = "C6") => bell().triggerAttackRelease(note, 0.8, t),
    crackle: (t: number) => {
      // one noise voice: its bursts must be scheduled in time order
      const at = Array.from({ length: 2 + Math.floor(Math.random() * 5) }, () => Math.random() * 0.25).sort((a, b) => a - b);
      for (const [i, dt] of at.entries()) pop().triggerAttackRelease(0.01, t + dt + i * 0.03);
    },
    thunder: (t: number) => low().triggerAttackRelease(3, t),
    tick: (t: number, hi = true) => tick().triggerAttackRelease(hi ? 2400 : 1800, 0.01, t),
    zap: (t: number) => glide(saw(), 2400, 120, 0.09, t),
    creak: (t: number) => glide(saw(), 140, 190, 0.45, t),
    horn: (t: number) => { const s = saw(); s.triggerAttack(82, t); s.frequency.setValueAtTime(82, t); s.triggerRelease(t + 1.6); },
    hiss: (t: number) => hiss().triggerAttackRelease(0.6, t),
    clank: (t: number) => clank().triggerAttackRelease(220, 0.2, t),
  };
}

type Kit = ReturnType<typeof kit>;

/** One recipe per place. */
const RECIPES: Record<string, (k: Kit, restored: boolean) => void> = {
  title: (k) => {
    k.noise("brown", "lowpass", 260, -30);
    k.every(0.5, 2.4, k.cricket);
  },
  hq: (k) => {
    k.noise("brown", "lowpass", 300, -32);
    k.noise("pink", "highpass", 3600, -38, { swell: [0.07, 0.3, 1] });      // rain on the window
    let hi = true;
    k.every(1, 1, (t) => { k.tick(t, hi); hi = !hi; });                       // the clock on the wall
  },
  map: (k) => {
    k.noise("brown", "lowpass", 240, -32);
    k.every(0.25, 1.4, k.crackle);                                            // the fire in the study
  },
  lab: (k) => {
    k.noise("brown", "lowpass", 260, -34);
    let hi = true;
    k.every(1, 1, (t) => { k.tick(t, hi); hi = !hi; });
  },
  fall: (k, restored) => {
    k.noise("pink", "highpass", 2800, restored ? -40 : -32, { swell: [0.06, 0.5, 1] });                 // rain
    if (restored) return;
    k.noise("pink", "bandpass", 500, -30, { q: 6, lfo: [0.07, 320, 900], swell: [0.045, 0.1, 1] });     // wind howling round the tower
    k.hum(55, "sawtooth", -40, 180);                                                                     // a drone under the floor
    k.hum(77.8, "sawtooth", -44, 160);                                                                   // a tritone above it
    k.every(16, 34, k.thunder);
    k.every(7, 15, k.creak);
    k.every(20, 40, (t) => k.bell(t, "D4"));                                                             // the clock, far off
  },
  crossexam: (k) => {
    k.noise("brown", "lowpass", 140, -24, { swell: [0.05, 0.4, 1] });
  },
  density: (k) => {
    k.noise("pink", "lowpass", 600, -22, { lfo: [0.11, 300, 1000], swell: [0.13, 0.25, 1] });   // waves on the pier
    k.every(5, 12, k.gull);
    k.every(9, 18, (t) => k.bell(t, "A5"));                                                      // Bob's brass bell
  },
  motion: (k) => {
    k.noise("pink", "bandpass", 700, -22, { q: 1.5, lfo: [0.07, 350, 1500], swell: [0.05, 0.3, 1] });   // desert wind
    k.every(6, 14, k.creak);
  },
  sound: (k, restored) => {
    k.noise("pink", "highpass", 2600, -30, { swell: [0.1, 0.6, 1] });       // drizzle
    k.noise("brown", "bandpass", 300, -30);
    k.every(0.8, 2.6, k.drip);
    k.every(12, 26, k.thunder);
    if (restored) k.every(3, 7, (t) => k.bell(t, ["E6", "G6", "B5"][Math.floor(Math.random() * 3)]));   // the bells ring again
  },
  heights: (k) => {
    k.noise("pink", "bandpass", 1200, -32, { q: 0.8, lfo: [0.06, 700, 1800] });
    k.every(3, 8, k.birds);
  },
  refraction: (k) => {
    k.noise("pink", "lowpass", 520, -25, { lfo: [0.09, 260, 900], swell: [0.1, 0.25, 1] });
    k.every(15, 30, k.horn);                                                  // the lighthouse foghorn
    k.every(6, 12, (t) => k.bell(t, "E7"));                                   // glass clinking in the shop
  },
  ohm: (k, restored) => {
    k.hum(50, "sawtooth", restored ? -40 : -34, 180);
    k.hum(100, "sine", -42, 400);
    k.every(1.5, 5, k.crackle);
    if (!restored) k.every(4, 10, k.zap);
  },
  heat: (k) => {
    k.noise("pink", "highpass", 2200, -36, { lfo: [0.05, 1600, 3200] });    // the hush of snow
    k.every(0.4, 1.6, k.bubble);                                              // the springs
    k.every(5, 10, k.hiss);                                                   // steam
  },
  acids: (k) => {
    k.noise("pink", "bandpass", 2200, -28, { q: 0.7, swell: [3.1, 0.6, 1] });   // the fountain
    k.noise("white", "highpass", 5200, -42);
    k.every(1, 3, k.drip);
    k.every(10, 20, (t) => k.bell(t, "D6"));
  },
  power: (k) => {
    k.noise("brown", "lowpass", 120, -28);
    let hi = true;
    k.every(0.5, 0.5, (t) => { k.tick(t, hi); hi = !hi; });                   // the clock tower's gears
    k.every(3, 7, k.hiss);
    k.every(6, 12, k.clank);
  },
};
