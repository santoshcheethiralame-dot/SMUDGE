// Shared numbers. World art is pre-rendered with an orthographic camera
// pitched 20 degrees down; these helpers turn world positions into screen pixels.
export const W = 480;
export const H = 270;
/** The canvas is W*Z by H*Z; every camera zooms Z. Art stays pixel-crisp, text renders at full sharpness. */
export const Z = 3;

const PITCH = (20 * Math.PI) / 180;
const COS = Math.cos(PITCH);
const SIN = Math.sin(PITCH);

/** World (x, y, z) -> screen (x, y) for a backdrop rendered with centre (cu, cv). */
export function project(x: number, y: number, z: number, cu: number, cv: number) {
  const v = y * COS - z * SIN;
  return { x: x - cu + W / 2, y: H / 2 - (v - cv) };
}

/** Sprites: 64 px cells with feet on row 60. */
export const FEET_ORIGIN = { x: 0.5, y: 60 / 64 };

export const DIRS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"] as const;
export type Dir = (typeof DIRS)[number];

export function dirFromVector(dx: number, dy: number): Dir {
  // screen space: +x right, +y down (toward the camera = "S")
  const a = Math.atan2(dx, dy); // 0 = S, +pi/2 = E
  const i = Math.round(a / (Math.PI / 4));
  return DIRS[((i % 8) + 8) % 8];
}

export const INK = "#0E1938";
export const PAPER = "#F2E9CF";
export const RED = "#C9302A";
export const FONT = '"Smudge Digits", "Pixelify Sans", monospace';
export const DISPLAY = '"Lilita One", "Trebuchet MS", sans-serif';
/** ?judges: the stage cut (one interview opens the stage, slip-or-push is skipped) */
export const JUDGES = new URLSearchParams(location.search).has("judges");
