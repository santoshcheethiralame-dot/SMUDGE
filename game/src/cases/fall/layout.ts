// The numbers the case-10 art was drawn with (art/world, written to assets/case10/fall_layout.json).
// Imported, not fetched, so the district and the lab can never disagree with the backdrops.
import layout from "../../../public/assets/case10/fall_layout.json";

export type World3 = [number, number, number];
export const FALL = layout;
