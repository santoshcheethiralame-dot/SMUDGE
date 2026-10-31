// Small pieces every instrument uses: the evidence panel, buttons, a reading box, a "recorded" tick.
import Phaser from "phaser";
import { FONT } from "../../consts";
import { overlay } from "../ui";
import { calc } from "./calc";

/** The working area under the dialogue box. */
export const AREA = { x: 16, y: 88, w: 448, h: 150 };

/** A pinned evidence photo / card: paper frame, a fill, a title strip. Returns its graphics to destroy later. */
export function panel(scene: Phaser.Scene, title: string, fill = 0x2c3448, area = AREA) {
  const g = scene.add.graphics();
  g.fillStyle(0x000000, 0.35).fillRect(area.x + 3, area.y + 3, area.w, area.h);
  g.fillStyle(0xf4f0e6, 1).fillRect(area.x, area.y, area.w, area.h);
  g.fillStyle(fill, 1).fillRect(area.x + 6, area.y + 16, area.w - 12, area.h - 22);
  g.fillStyle(0xc9302a, 1).fillCircle(area.x + area.w / 2, area.y + 4, 2.5);
  const t = scene.add.text(area.x + area.w / 2, area.y + 9, title, { fontFamily: FONT, fontSize: "10px", color: "#0E1938" }).setOrigin(0.5);
  return [g, t] as Phaser.GameObjects.GameObject[];
}

export function button(scene: Phaser.Scene, x: number, y: number, label: string, fill = "#C9302A") {
  return scene.add.text(x, y, label, { fontFamily: FONT, fontSize: "10px", color: "#FFFFFF", backgroundColor: fill })
    .setPadding(8, 3, 8, 3).setOrigin(0.5).setInteractive({ useHandCursor: true }).setDepth(600);
}

export function tick(scene: Phaser.Scene, x: number, y: number, text: string) {
  return scene.add.text(x, y, `${text} ✓`, { fontFamily: FONT, fontSize: "9px", color: "#9CF5B5", backgroundColor: "#0E1938" })
    .setPadding(3, 1, 3, 1).setOrigin(0, 0.5).setDepth(400);
}

export function clicked(obj: Phaser.GameObjects.GameObject) {
  return new Promise<void>((res) => obj.once("pointerdown", () => res()));
}

/** A small HTML box over the canvas for typing a reading; resolves with the number when Record is pressed. */
export function readingBox(scene: Phaser.Scene, x: number, y: number, unit: string): { value: Promise<number>; remove: () => void } {
  const wrap = document.createElement("form");
  wrap.style.cssText = `font-family:"Smudge Digits","Pixelify Sans",monospace;background:#F2E9CF;border:2px solid #0E1938;border-radius:4px;padding:4px 6px;
    box-sizing:border-box;display:flex;gap:6px;align-items:center;color:#0E1938`;
  wrap.innerHTML = `<input id="reading" inputmode="decimal" autocomplete="off" aria-label="Your reading"
      style="width:4.6em;font:inherit;padding:1px 4px;border:1.5px solid #0E1938;background:#FFFBEF;color:#0E1938;border-radius:3px">
    <span>${unit}</span><button type="submit" style="font:inherit;padding:2px 8px;border:2px solid #0E1938;background:#C9302A;color:#fff;border-radius:3px;cursor:pointer">Record</button>`;
  ["pointerdown", "keydown", "keyup"].forEach((ev) => wrap.addEventListener(ev, (e) => e.stopPropagation()));
  const remove = overlay(scene, wrap, x, y, 150, 24);
  scene.input.keyboard!.enabled = false;
  const value = new Promise<number>((res) => {
    wrap.onsubmit = (e) => {
      e.preventDefault();
      const v = calc((document.getElementById("reading") as HTMLInputElement).value);
      if (!Number.isNaN(v)) res(v);
    };
  });
  setTimeout(() => (document.getElementById("reading") as HTMLInputElement | null)?.focus(), 50);
  return { value, remove: () => { remove(); scene.input.keyboard!.enabled = true; } };
}
