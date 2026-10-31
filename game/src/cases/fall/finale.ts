// The Midnight Fall's ending, run by the Restore scene: the "ghost" on the tower blows off (it was the
// bedsheet), then a two-tap exit check. Answers go to localStorage["smudge.exit"] for the playtest numbers.
import Phaser from "phaser";
import { W, H, FONT, DISPLAY, project } from "../../consts";
import { FALL, World3 } from "./layout";
import { wait, tween } from "../../systems/fx";
import { sfx } from "../../audio";

/** The ghost on the washing line loses its eyes in a gust and flaps away: a bedsheet. Then the line. */
export async function ghostReveal(scene: Phaser.Scene) {
  // sheet_ghost.png is two 32 px frames: 0 the face, 1 the plain sheet. Added as an image, so cut the frames here.
  const tex = scene.textures.get("sheet_ghost");
  if (!tex.has("0")) { tex.add("0", 0, 0, 0, 32, 32); tex.add("1", 0, 32, 0, 32, 32); }
  // the Restore backdrop is shifted left by 180 px against the 720 px art; the ghost hangs where the art put it
  const g = FALL.district.clues.ghost as World3;
  const at = project(g[0], g[1], g[2], FALL.district.cu, FALL.district.cv);
  const ghost = scene.add.image(at.x + (FALL.district.width - W) / 2 - 180, at.y - 6, "sheet_ghost", "0").setDepth(40).setAlpha(0);
  await tween(scene, { targets: ghost, alpha: 1, duration: 500 });
  scene.tweens.add({ targets: ghost, angle: { from: -6, to: 6 }, duration: 350, yoyo: true, repeat: 3, ease: "Sine.easeInOut" });
  await wait(scene, 1500);
  sfx("whoosh");
  ghost.setFrame("1");                                   // the eyes go: a bedsheet
  await tween(scene, { targets: ghost, x: -40, y: 18, angle: -50, scaleY: 0.55, duration: 1300, ease: "Quad.easeIn" });
  ghost.destroy();
  const line = scene.add.text(W / 2, 150, "No ghost. Just gravity.", { fontFamily: DISPLAY, fontSize: "26px", color: "#F2E9CF", stroke: "#0E1938", strokeThickness: 5 })
    .setOrigin(0.5).setDepth(40).setScale(0.3).setAlpha(0);
  sfx("stamp");
  await tween(scene, { targets: line, scale: 1, alpha: 1, duration: 320, ease: "Back.easeOut" });
  await wait(scene, 1800);
  await tween(scene, { targets: line, alpha: 0, duration: 300 });
  line.destroy();
}

const QUESTIONS = [
  { q: "A sack falls for 3 s. How high?", options: ["15 m", "29 m", "44 m", "88 m"], right: 2 },
  { q: "Twice as high. Twice as long?", options: ["Yes", "No, less"], right: 1 },
];

/** Two questions, one tap each. A right answer gets a gold tick; a wrong one shows the right answer for 2 s. */
export async function exitCheck(scene: Phaser.Scene) {
  const answers: number[] = [];
  for (const [n, item] of QUESTIONS.entries()) {
    const box = scene.add.container(W / 2, H / 2).setDepth(60).setAlpha(0);
    box.add(scene.add.rectangle(0, 0, 340, 120, 0xf2e9cf).setStrokeStyle(2, 0x0e1938));
    box.add(scene.add.text(0, -44, `QUICK CHECK ${n + 1}/2`, { fontFamily: FONT, fontSize: "9px", color: "#C9302A" }).setOrigin(0.5));
    box.add(scene.add.text(0, -22, item.q, { fontFamily: FONT, fontSize: "12px", color: "#0E1938" }).setOrigin(0.5));
    const span = 300 / item.options.length;
    const btns = item.options.map((label, i) => {
      const b = scene.add.text(-150 + span * (i + 0.5), 18, label, { fontFamily: FONT, fontSize: "11px", color: "#FFFFFF", backgroundColor: "#2E5CAD" })
        .setPadding(8, 4, 8, 4).setOrigin(0.5).setInteractive({ useHandCursor: true });
      box.add(b);
      return b;
    });
    await tween(scene, { targets: box, alpha: 1, duration: 250 });
    const picked = await new Promise<number>((resolve) => btns.forEach((b, i) => b.once("pointerdown", () => resolve(i))));
    btns.forEach((b) => b.disableInteractive());
    answers.push(picked);
    const right = btns[item.right];
    right.setBackgroundColor("#C9A227");
    if (picked === item.right) {
      sfx("chime");
      box.add(scene.add.text(right.x, right.y - 22, "✓", { fontFamily: DISPLAY, fontSize: "18px", color: "#C9A227" }).setOrigin(0.5));
      await wait(scene, 900);
    } else {
      sfx("deny");
      btns[picked].setBackgroundColor("#8F8268");
      await wait(scene, 2000);
    }
    await tween(scene, { targets: box, alpha: 0, duration: 200 });
    box.destroy();
  }
  try { localStorage.setItem("smudge.exit", JSON.stringify({ answers, right: QUESTIONS.map((q) => q.right), at: Date.now() })); } catch { /* private window */ }
}
