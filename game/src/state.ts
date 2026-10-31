// Progress through the current case (in memory), and which cases are solved (kept in localStorage).
export interface Evidence {
  label: string;   // what the server's present check compares, e.g. "density:lead", "speed:mu"
  badge: string;   // the card shown in cross-examination
  say: string;     // what Smudge says when presenting it
}

const SAVE = "smudge.solved";
function loadSolved(): Set<string> {
  try { return new Set(JSON.parse(localStorage.getItem(SAVE) ?? "[]")); } catch { return new Set(); }
}

export const progress = {
  kit: "density",
  inspected: false,
  labDone: false,
  evidence: null as null | Evidence,
  questioned: new Set<string>(),
  transcript: [] as { who: string; q: string; a: string }[],
  solved: false,
  culprit: "",
  solvedCases: loadSolved(),
  /** Mark this case solved and remember it across reloads. */
  solve(kit: string) {
    this.solved = true;
    this.solvedCases.add(kit);
    try { localStorage.setItem(SAVE, JSON.stringify([...this.solvedCases])); } catch { /* private window: this session only */ }
  },
  /** Start a fresh case of this kit; solved cases stay solved. */
  reset(kit?: string) {
    this.kit = kit ?? this.kit;
    this.inspected = false;
    this.labDone = false;
    this.evidence = null;
    this.questioned = new Set();
    this.transcript = [];
    this.solved = false;
    this.culprit = "";
  },
};
