// A voice for every speaker: the blips that play as their line types out. Shaped from each persona, so a
// diamond tinkles, a crane hook grunts and a motor buzzes. Speakers missing here get a steady voice from their id.

export interface Voice {
  /** "synth" is one oscillator; "fm" adds a modulator for bells, buzz and metal */
  kind: "synth" | "fm";
  osc: "sine" | "triangle" | "square" | "sawtooth";
  /** pitch range in Hz each blip picks from */
  lo: number;
  hi: number;
  /** how long each blip rings, seconds */
  decay: number;
  /** dB */
  vol: number;
  /** blip on every Nth letter: 1 chatters, 3 is slow and deliberate */
  every: number;
  /** semitones the blip slides through: + rises (bubbly, bright), - drops (heavy, grumpy) */
  slide?: number;
  /** fm only */
  harmonicity?: number;
  index?: number;
}

const v = (kind: Voice["kind"], osc: Voice["osc"], lo: number, hi: number, decay: number, vol: number, every: number,
  extra: Partial<Voice> = {}): Voice => ({ kind, osc, lo, hi, decay, vol, every, ...extra });

export const VOICES: Record<string, Voice> = {
  smudge: v("synth", "triangle", 180, 260, 0.07, -14, 2),
  foot: v("synth", "square", 700, 980, 0.05, -26, 2),
  baron: v("synth", "sawtooth", 90, 120, 0.1, -20, 2),
  narrator: v("synth", "sine", 400, 460, 0.05, -22, 2),
  // Case 1, the Bay
  karat: v("fm", "sine", 880, 1180, 0.09, -18, 2, { harmonicity: 3.01, index: 2, slide: 2 }),     // sparkly, haughty
  cyl: v("synth", "square", 130, 170, 0.06, -27, 3),                                                // grumpy, clipped
  bob: v("synth", "triangle", 320, 520, 0.08, -15, 1, { slide: 3 }),                                 // bobbing, rambling
  // Case 2, Motion Mesa
  dash: v("synth", "sawtooth", 620, 760, 0.035, -28, 1),
  rolla: v("synth", "sine", 380, 470, 0.12, -14, 2, { slide: 2 }),
  mu: v("synth", "triangle", 95, 120, 0.14, -12, 3),
  // Case 3, Echo Valley
  reverb: v("fm", "sine", 150, 210, 0.16, -14, 2, { harmonicity: 1.5, index: 1.2 }),             // booming radio
  thump: v("synth", "square", 110, 150, 0.05, -24, 2, { slide: -4 }),                              // drum beats
  coil: v("synth", "triangle", 520, 760, 0.04, -16, 1, { slide: 7 }),                              // boing
  // Case 4, Lumen Heights
  lumen: v("synth", "sine", 300, 360, 0.11, -15, 2),                                                // gentle, proper
  vane: v("synth", "triangle", 420, 640, 0.07, -16, 2, { slide: -3 }),                              // breezy, swooping
  sola: v("synth", "sine", 560, 760, 0.07, -15, 1, { slide: 2 }),                                   // chatty, warm
  // Case 5, Prism Port
  frost: v("fm", "sine", 900, 1100, 0.05, -21, 3, { harmonicity: 4.2, index: 1.5 }),               // cool, crystalline
  pane: v("fm", "sine", 600, 820, 0.09, -18, 2, { harmonicity: 2.5, index: 1.2, slide: 2 }),       // ringing glass
  geo: v("synth", "triangle", 120, 150, 0.12, -13, 3, { slide: -2 }),                               // grumbly, slow
  // Case 6, Ohmtown
  volta: v("synth", "square", 520, 700, 0.04, -25, 1, { slide: 4 }),                                // bubbly, fast
  ohmar: v("synth", "triangle", 240, 300, 0.06, -16, 2, { slide: -1 }),                             // anxious
  glim: v("synth", "sine", 640, 760, 0.16, -17, 3),                                                 // dreamy, soft
  // Case 7, Kelvin Springs
  al: v("fm", "triangle", 420, 560, 0.05, -20, 1, { harmonicity: 2, index: 3 }),                   // clangy, busy
  ferris: v("synth", "sawtooth", 85, 110, 0.12, -24, 3, { slide: -2 }),                             // rumbling
  brewster: v("synth", "sine", 820, 1040, 0.08, -17, 2, { slide: 5 }),                              // whistling kettle
  // Case 8, Acid Alley
  citrine: v("synth", "square", 600, 820, 0.035, -26, 1, { slide: -3 }),                            // sharp, zesty
  bicarb: v("synth", "sine", 260, 330, 0.1, -14, 2, { slide: 4 }),                                  // soft, fizzy
  sudsy: v("synth", "sine", 520, 780, 0.06, -15, 1, { slide: 9 }),                                  // bubbles
  // Case 9, Watt Works
  cog: v("fm", "square", 700, 760, 0.025, -26, 2, { harmonicity: 5.1, index: 6 }),                  // ticking
  hoist: v("synth", "sawtooth", 70, 90, 0.16, -22, 3, { slide: -3 }),                               // gruff, heavy
  dynamo: v("fm", "sawtooth", 300, 420, 0.03, -28, 1, { harmonicity: 0.5, index: 8 }),              // buzzing
};

/** A steady fallback voice for a speaker with no entry, picked from its id. */
export function voiceOf(who: string): Voice {
  if (VOICES[who]) return VOICES[who];
  const h = [...who].reduce((a, ch) => a * 31 + ch.charCodeAt(0), 7) >>> 0;
  const base = 160 + (h % 9) * 70;
  return v("synth", (["sine", "triangle", "square"] as const)[h % 3], base, base * 1.3, 0.07, h % 3 === 2 ? -24 : -15, 2);
}
