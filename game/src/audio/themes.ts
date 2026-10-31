// The score: one theme per place. Each bar plays one chord; the motif runs bar by bar alongside it.
// Four layers open as a case comes together: 0 pad, 1 bass, 2 motif, 3 percussion (see audio.ts, layer()).
// Notes in motif bars are 16 sixteenth-note steps, "." for a rest.

export interface Lead {
  kind: "synth" | "fm";
  osc: "sine" | "triangle" | "square" | "sawtooth";
  decay: number;
  harmonicity?: number;
  index?: number;
  /** how much of the motif goes through the echo, 0..1 */
  echo: number;
  vol: number;
}

export interface Theme {
  bpm: number;
  chords: string[][];
  bass: string[];
  /** the steps in each bar the bass plays on */
  bassSteps: number[];
  motif: string[];
  lead: Lead;
  pad: "sine" | "triangle";
  kick: number[];
  hat: number[];
}

const L = (kind: Lead["kind"], osc: Lead["osc"], decay: number, echo: number, vol: number, extra: Partial<Lead> = {}): Lead =>
  ({ kind, osc, decay, echo, vol, ...extra });

export const THEMES: Record<string, Theme> = {
  // menus and HQ: a sleepy lullaby
  night: {
    bpm: 72, pad: "sine",
    chords: [["D3", "A3", "F#4"], ["B2", "F#3", "D4"], ["G2", "D3", "B3"], ["A2", "E3", "C#4"]],
    bass: ["D2", "B1", "G1", "A1"], bassSteps: [0],
    motif: ["F#5 . . . A5 . . . . . . . . . . .", "D5 . . . F#5 . . . E5 . . . . . . .",
      "B4 . . . D5 . . . G5 . . . F#5 . . .", "E5 . . . . . . . C#5 . . . . . . ."],
    lead: L("fm", "sine", 0.9, 0.35, -20, { harmonicity: 3, index: 1.2 }), kick: [], hat: [8],
  },
  // Case 1, the Bay: a seaside bounce on marimba
  density: {
    bpm: 96, pad: "triangle",
    chords: [["F3", "A3", "C4"], ["D3", "F3", "A3"], ["Bb2", "D3", "F3"], ["C3", "E3", "G3"]],
    bass: ["F2", "D2", "Bb1", "C2"], bassSteps: [0, 8, 12],
    motif: ["A4 . C5 . F5 . . . E5 . C5 . A4 . . .", "D5 . . . F5 . E5 . D5 . A4 . . . . .",
      "Bb4 . D5 . F5 . . . G5 . F5 . D5 . . .", "E5 . . . G5 . . . C5 . . . . . . ."],
    lead: L("fm", "sine", 0.3, 0.2, -16, { harmonicity: 4, index: 2 }), kick: [0, 8], hat: [4, 12],
  },
  // Case 2, Motion Mesa: a desert gallop
  motion: {
    bpm: 120, pad: "triangle",
    chords: [["E3", "G3", "B3"], ["C3", "E3", "G3"], ["D3", "F#3", "A3"], ["B2", "D#3", "F#3"]],
    bass: ["E2", "C2", "D2", "B1"], bassSteps: [0, 3, 6, 8, 11, 14],
    motif: ["E5 . G5 . B5 . . A5 G5 . E5 . . . D5 .", "E5 . . . G5 . E5 . C5 . . . . . . .",
      "F#5 . A5 . D6 . . C6 B5 . A5 . . . F#5 .", "D#5 . F#5 . B5 . . . A5 . F#5 . D#5 . . ."],
    lead: L("synth", "square", 0.12, 0.15, -24), kick: [0, 4, 8, 12], hat: [2, 6, 10, 14],
  },
  // Case 3, Echo Valley: rain and far-off bells
  sound: {
    bpm: 80, pad: "sine",
    chords: [["A2", "E3", "C4"], ["F2", "C3", "A3"], ["C3", "G3", "E4"], ["G2", "D3", "B3"]],
    bass: ["A1", "F1", "C2", "G1"], bassSteps: [0, 10],
    motif: ["E5 . . . . . A5 . . . . . G5 . . .", "C5 . . . . . . . A4 . . . . . . .",
      "G5 . . . . . E5 . . . . . D5 . . .", "B4 . . . . . . . D5 . . . . . . ."],
    lead: L("fm", "sine", 1.2, 0.45, -18, { harmonicity: 3.5, index: 3 }), kick: [0], hat: [8],
  },
  // Case 4, Lumen Heights: a sunny walk with a flute
  heights: {
    bpm: 88, pad: "sine",
    chords: [["G2", "D3", "B3"], ["E3", "G3", "B3"], ["C3", "G3", "E4"], ["D3", "A3", "F#4"]],
    bass: ["G1", "E2", "C2", "D2"], bassSteps: [0, 6, 8],
    motif: ["D5 . . . G5 . . . B5 . A5 . G5 . . .", "E5 . . . G5 . . . B5 . . . . . . .",
      "C6 . B5 . A5 . G5 . E5 . . . G5 . . .", "F#5 . . . A5 . . . D5 . . . . . . ."],
    lead: L("synth", "sine", 0.5, 0.25, -15), kick: [0, 8], hat: [4, 12],
  },
  // Case 5, Prism Port: glass and fog
  refraction: {
    bpm: 84, pad: "sine",
    chords: [["Eb3", "G3", "Bb3", "D4"], ["F3", "A3", "C4"], ["C3", "Eb3", "G3"], ["Bb2", "D3", "F3"]],
    bass: ["Eb2", "F2", "C2", "Bb1"], bassSteps: [0, 8],
    motif: ["G5 . . . Bb5 . . . D6 . . . . . . .", "A5 . . . C6 . . . F5 . . . . . . .",
      "G5 . Eb5 . C5 . . . Eb5 . G5 . . . . .", "F5 . . . D5 . . . Bb4 . . . . . . ."],
    lead: L("fm", "sine", 0.7, 0.4, -19, { harmonicity: 5.07, index: 2.5 }), kick: [0], hat: [4, 12],
  },
  // Case 6, Ohmtown: a festival on the grid
  ohm: {
    bpm: 110, pad: "triangle",
    chords: [["C3", "Eb3", "G3"], ["Ab2", "C3", "Eb3"], ["Eb3", "G3", "Bb3"], ["Bb2", "D3", "F3"]],
    bass: ["C2", "Ab1", "Eb2", "Bb1"], bassSteps: [0, 2, 4, 6, 8, 10, 12, 14],
    motif: ["G5 . G5 . Eb5 . . . C5 . . . D5 . Eb5 .", "C5 . . . Eb5 . . . Ab5 . G5 . . . . .",
      "Bb5 . Bb5 . G5 . . . Eb5 . . . F5 . G5 .", "F5 . . . D5 . . . Bb4 . . . . . . ."],
    lead: L("synth", "sawtooth", 0.14, 0.25, -27), kick: [0, 4, 8, 12], hat: [2, 6, 10, 14],
  },
  // Case 7, Kelvin Springs: snow, steam and a celesta
  heat: {
    bpm: 76, pad: "sine",
    chords: [["Bb2", "F3", "D4"], ["G2", "D3", "Bb3"], ["Eb3", "Bb3", "G4"], ["F2", "C3", "A3"]],
    bass: ["Bb1", "G1", "Eb2", "F1"], bassSteps: [0, 8],
    motif: ["D6 . . . F5 . . . Bb5 . . . . . . .", "D6 . . . G5 . . . Bb5 . . . A5 . . .",
      "G5 . . . Bb5 . . . Eb6 . . . D6 . . .", "C6 . . . A5 . . . F5 . . . . . . ."],
    lead: L("fm", "sine", 0.8, 0.3, -18, { harmonicity: 7, index: 1.5 }), kick: [0], hat: [0, 4, 8, 12],
  },
  // Case 8, Acid Alley: a market tune in D minor
  acids: {
    bpm: 104, pad: "triangle",
    chords: [["D3", "F3", "A3"], ["G2", "Bb2", "D3"], ["A2", "C#3", "E3"], ["D3", "F3", "A3"]],
    bass: ["D2", "G1", "A1", "D2"], bassSteps: [0, 3, 8, 11],
    motif: ["A4 . D5 . F5 . E5 . D5 . . . A4 . . .", "Bb4 . D5 . G5 . F5 . D5 . . . . . . .",
      "C#5 . E5 . A5 . G5 . F5 . E5 . . . . .", "D5 . . . F5 . . . D5 . . . . . . ."],
    lead: L("synth", "triangle", 0.18, 0.2, -14), kick: [0, 6, 8], hat: [4, 12, 14],
  },
  // Case 9, Watt Works: clockwork in G minor
  power: {
    bpm: 100, pad: "triangle",
    chords: [["G2", "D3", "Bb3"], ["Eb3", "G3", "Bb3"], ["F2", "C3", "A3"], ["D3", "F#3", "A3"]],
    bass: ["G1", "Eb2", "F1", "D2"], bassSteps: [0, 4, 8, 12],
    motif: ["G5 . D5 . G5 . D5 . Bb5 . A5 . G5 . . .", "G5 . Eb5 . G5 . Eb5 . Bb5 . . . . . . .",
      "A5 . F5 . A5 . F5 . C6 . Bb5 . A5 . . .", "F#5 . . . A5 . . . D5 . . . . . . ."],
    lead: L("synth", "square", 0.08, 0.15, -27), kick: [0, 8], hat: [2, 6, 10, 14],
  },
  // the lab bench: curious and light
  lab: {
    bpm: 90, pad: "sine",
    chords: [["C3", "G3", "E4"], ["A2", "E3", "C4"], ["F2", "C3", "A3"], ["G2", "D3", "B3"]],
    bass: ["C2", "A1", "F1", "G1"], bassSteps: [0, 8],
    motif: ["E5 . G5 . . . E5 . C5 . . . . . . .", "C5 . E5 . . . C5 . A4 . . . . . . .",
      "A4 . C5 . F5 . . . E5 . . . D5 . . .", "B4 . D5 . G5 . . . . . . . . . . ."],
    lead: L("synth", "triangle", 0.15, 0.2, -16), kick: [], hat: [4, 12],
  },
  // the Midnight Fall: a music box left running in an empty manor. D minor, a tritone that never resolves,
  // an A chord with a flat ninth, and a slow heartbeat for a kick
  fall: {
    bpm: 58, pad: "triangle",
    chords: [["D3", "A3", "F4"], ["D3", "Ab3", "F4"], ["Bb2", "F3", "D4"], ["A2", "C#4", "Bb4"]],
    bass: ["D2", "D2", "Bb1", "A1"], bassSteps: [0],
    motif: ["A5 . . . F5 . . . E5 . . . D5 . . .", "D5 . C#5 . D5 . . . F5 . . . Ab5 . . .",
      "G5 . . . F5 . . . D5 . . . Bb4 . . .", "A4 . . . . . . . C#5 . . . Bb4 . . ."],
    lead: L("fm", "sine", 1.6, 0.5, -22, { harmonicity: 7, index: 2.2 }), kick: [0, 3], hat: [],
  },
  // cross-examination: a heartbeat under a minor-second grind
  tense: {
    bpm: 96, pad: "triangle",
    chords: [["C3", "G3", "Eb4"], ["Db3", "Ab3", "F4"], ["C3", "G3", "Eb4"], ["B2", "F3", "D4"]],
    bass: ["C2", "Db2", "C2", "B1"], bassSteps: [0, 2, 4, 6, 8, 10, 12, 14],
    motif: ["G5 . . . . . . . Ab5 . . . G5 . . .", "Ab5 . . . . . . . F5 . . . . . . .",
      "G5 . . . . . . . Eb5 . . . D5 . . .", "D5 . . . F5 . . . Ab5 . . . G5 . . ."],
    lead: L("synth", "sawtooth", 0.3, 0.3, -28), kick: [0, 3, 8, 11], hat: [],
  },
};

/** Motif bar -> 16 notes or nulls. */
export function steps(bar: string): (string | null)[] {
  const t = bar.trim().split(/\s+/).map((x) => (x === "." ? null : x));
  while (t.length < 16) t.push(null);
  return t.slice(0, 16);
}
