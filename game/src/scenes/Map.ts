// The casebook: the open textbook, one medallion per chapter whose law was stolen. Built cases come from
// src/cases; the rest of the slate shows greyed out as "being written" until its folder exists.
import Phaser from "phaser";
import { W, H, FONT, DISPLAY } from "../consts";
import { pageReveal, pageTurn, makeGlow, dust } from "../systems/fx";
import { sfx, themeFor, layer, ambience } from "../audio";
import { buttonFeel } from "../systems/juice";
import { api } from "../api";
import { progress } from "../state";
import { CASES, CASE_ORDER } from "../cases";
import { openAuthor } from "../systems/author";

/** The planned slate, by case number. A case folder with the same num replaces its entry. */
const SLATE: { num: number; title: string; place: string; chapter: string }[] = [
  { num: 3, title: "The Thunder Alibi", place: "Echo Valley", chapter: "Sound" },
  { num: 4, title: "The Long Shadow", place: "Lumen Heights", chapter: "Heights and distances" },
  { num: 5, title: "The Bent Light", place: "Prism Port", chapter: "Refraction" },
  { num: 6, title: "The Blackout", place: "Ohmtown", chapter: "Electricity" },
  { num: 7, title: "The Warm Alibi", place: "Kelvin Springs", chapter: "Heat" },
  { num: 8, title: "The Colour Swap", place: "Acid Alley", chapter: "Acids and bases" },
  { num: 9, title: "The Slow Lift", place: "Watt Works", chapter: "Work and power" },
];
// Ten chapters on a trail that snakes down the left page, across the foot of the book and up the right page.
// Each spot is the foot of a pop-up; its label sits to the right, the trail runs down the left.
const SPOTS = [[100, 79], [100, 120], [100, 161], [100, 202], [100, 243], [330, 243], [330, 202], [330, 161], [330, 120], [330, 79]];
const TRAIL_X = [56, 282];

export class CaseMap extends Phaser.Scene {
  constructor() { super("Map"); }

  async create(data: { from?: string }) {
    makeGlow(this, "glow64", 64);
    themeFor("night");
    layer(1);
    ambience("map");
    // the open book on the desk, rendered: pages at x 16..238 and 242..464, y 38..256
    this.add.image(0, 0, "map_book").setOrigin(0);
    dust(this, 0, 30, W, H - 40, 0xffe0a8, 18);
    this.add.text(W / 2, 18, "THE CASEBOOK", { fontFamily: DISPLAY, fontSize: "20px", color: "#F2E9CF" }).setOrigin(0.5);
    const solvedN = CASE_ORDER.filter((k) => progress.solvedCases.has(k)).length;
    this.add.text(W - 14, 18, `${solvedN}/${CASE_ORDER.length} laws restored`, { fontFamily: FONT, fontSize: "9px", color: "#FAC775" }).setOrigin(1, 0.5);
    this.add.text(14, 18, "◂ HQ", { fontFamily: FONT, fontSize: "10px", color: "#9AA6C8" }).setOrigin(0, 0.5)
      .setInteractive({ useHandCursor: true }).on("pointerdown", () => pageTurn(this, () => { this.scene.start("HQ"); }));

    const built = CASE_ORDER.map((k) => CASES[k]);
    const entries = [
      ...built.map((c) => ({ num: c.num, title: c.title, place: c.place, chapter: c.chapter, kit: c.kit as string | null })),
      ...SLATE.filter((s) => !built.some((c) => c.num === s.num)).map((s) => ({ ...s, kit: null as string | null })),
    ].sort((a, b) => a.num - b.num);

    // the trail: a dotted spine down each page with a stub out to every chapter, joined across the foot of the book
    const trail = this.add.graphics();
    const dot = (x: number, y: number, done: boolean) => {
      if (Math.abs(x - 240) < 7) return;                        // the dots jump the gutter
      trail.fillStyle(done ? 0xc9302a : 0x0e1938, done ? 0.75 : 0.4).fillRect(Math.round(x) - 1, Math.round(y), 2, 1);
    };
    const solvedAt = (i: number) => !!entries[i]?.kit && progress.solvedCases.has(entries[i].kit!);
    const n = Math.min(entries.length, SPOTS.length);
    for (let i = 0; i < n; i++) {
      const [x, y] = SPOTS[i], tx = TRAIL_X[x < 240 ? 0 : 1];
      for (let sx = tx; sx < x - 28; sx += 4) dot(sx, y, solvedAt(i));
      if (i < n - 1) {
        const [x1, y1] = SPOTS[i + 1];
        if ((x < 240) === (x1 < 240)) for (let sy = Math.min(y, y1); sy <= Math.max(y, y1); sy += 4) dot(tx, sy, solvedAt(i));
        else {
          // across the foot of the book: a shallow curve from one spine to the other
          const a = { x: tx, y }, b = { x: TRAIL_X[1], y: y1 }, c = { x: 172, y: 262 };
          for (let k = 0; k <= 60; k++) {
            const t = k / 60, u = 1 - t;
            dot(u * u * a.x + 2 * u * t * c.x + t * t * b.x, u * u * a.y + 2 * u * t * c.y + t * t * b.y, solvedAt(i));
          }
        }
      }
    }

    entries.forEach((e, i) => {
      const [x, y] = SPOTS[i % SPOTS.length];
      const solved = !!e.kit && progress.solvedCases.has(e.kit);
      const live = !!e.kit;
      // a paper pop-up of the district standing on the page; chapters still being written are pencil-grey
      const m = this.add.container(x, y);
      const pop = this.add.image(0, 8, `map_pop${e.num}`).setOrigin(0.5, 1);
      if (!live) pop.setTint(0xb8b0a0).setAlpha(0.6);
      const badge = this.add.circle(-26, 0, 7, live ? 0x0e1938 : 0xc9bc98).setStrokeStyle(1, 0xf2e9cf);
      const n = this.add.text(-26, -1, `${e.num}`, { fontFamily: DISPLAY, fontSize: "10px", color: "#F2E9CF" }).setOrigin(0.5);
      const label = this.add.text(28, -10, live ? e.place : `${e.place} · soon`, { fontFamily: FONT, fontSize: "10px", color: live ? "#0E1938" : "#8F8268" }).setOrigin(0, 0.5);
      const sub = this.add.text(28, 1, live ? e.title.replace(/^The /, "") : "", { fontFamily: FONT, fontSize: "9px", color: "#8F8268" }).setOrigin(0, 0.5);
      m.add([pop, badge, n, label, sub]);
      if (solved) {
        const stamp = this.add.text(18, -26, "✓", { fontFamily: DISPLAY, fontSize: "16px", color: "#C9302A" }).setOrigin(0.5).setAngle(-12);
        m.add(stamp);
      }
      if (live) {
        if (!solved) this.tweens.add({ targets: pop, y: 6, duration: 800, yoyo: true, repeat: -1, ease: "Sine.easeInOut", delay: i * 140 });
        // hovering lifts the pop-up off the page
        const lift = (on: boolean) => {
          this.tweens.add({ targets: [pop], scaleX: on ? 1.1 : 1, scaleY: on ? 1.1 : 1, duration: 120, ease: "Back.easeOut" });
          label.setColor(on ? "#C9302A" : "#0E1938");
          if (on) sfx("hover");
        };
        for (const t of [pop, label]) {
          t.setInteractive({ useHandCursor: true }).on("pointerdown", () => this.open(e.kit!));
          t.on("pointerover", () => lift(true)).on("pointerout", () => lift(false));
        }
      }
    });
    // the Author agents: one line in, a new case on a built district out
    const pen = this.add.text(W - 14, H - 1, "✎ Author a case", { fontFamily: FONT, fontSize: "10px", color: "#FFFFFF", backgroundColor: "#C9302A" })
      .setPadding(6, 2, 6, 1).setOrigin(1, 1).setDepth(50).setInteractive({ useHandCursor: true });
    buttonFeel(this, pen, "select");
    pen.on("pointerup", () => this.author());
    if (new URLSearchParams(location.search).has("author")) this.time.delayedCall(300, () => this.author());
    if (data?.from === "hq") await pageReveal(this);
    else this.cameras.main.fadeIn(400, 5, 6, 15);
  }

  private async author() {
    this.input.enabled = false;
    const kit = await openAuthor();
    this.input.enabled = true;
    if (!kit) return;
    progress.reset(kit);
    api.current = null;
    pageTurn(this, () => { this.scene.start("District", { kit, from: "hq" }); });
  }

  private open(kit: string) {
    const c = CASES[kit];
    sfx("open");
    const card = this.add.container(W / 2, H / 2 + 6).setDepth(100);
    const shade = this.add.rectangle(-W / 2, -H / 2 - 6, W, H, 0x05060f, 0.55).setOrigin(0).setInteractive();
    const bg = this.add.rectangle(0, 0, 230, 116, 0xf2e9cf).setStrokeStyle(2, 0x0e1938);
    const t1 = this.add.text(0, -42, `CASE ${c.num} · ${c.chapter.toUpperCase()}`, { fontFamily: FONT, fontSize: "10px", color: "#C9302A" }).setOrigin(0.5);
    const t2 = this.add.text(0, -20, c.title, { fontFamily: DISPLAY, fontSize: "18px", color: "#0E1938" }).setOrigin(0.5);
    const t3 = this.add.text(0, 2, c.place, { fontFamily: FONT, fontSize: "10px", color: "#55361A" }).setOrigin(0.5);
    const go = this.add.text(48, 34, "Open case ▸", { fontFamily: FONT, fontSize: "10px", color: "#FFFFFF", backgroundColor: "#C9302A" })
      .setPadding(8, 3, 8, 3).setOrigin(0.5).setInteractive({ useHandCursor: true });
    const back = this.add.text(-56, 34, "Not yet", { fontFamily: FONT, fontSize: "10px", color: "#0E1938", backgroundColor: "#E6DCC0" })
      .setPadding(8, 3, 8, 3).setOrigin(0.5).setInteractive({ useHandCursor: true });
    card.add([shade, bg, t1, t2, t3, go, back]);
    shade.setAlpha(0);
    for (const o of [bg, t1, t2, t3, go, back]) (o as any).setScale?.(0.6);
    this.tweens.add({ targets: shade, alpha: 1, duration: 160 });
    this.tweens.add({ targets: [bg, t1, t2, t3, go, back], scale: 1, duration: 220, ease: "Back.easeOut" });
    buttonFeel(this, go, "select");
    buttonFeel(this, back, "back");
    const close = () => { sfx("close"); this.tweens.add({ targets: card, alpha: 0, duration: 120, onComplete: () => card.destroy() }); };
    back.on("pointerup", close);
    shade.on("pointerdown", close);
    go.on("pointerup", () => {
      if (progress.kit !== kit || progress.solved) { progress.reset(kit); api.current = null; }
      pageTurn(this, () => { this.scene.start("District", { kit, from: "hq" }); });
    });
  }
}
