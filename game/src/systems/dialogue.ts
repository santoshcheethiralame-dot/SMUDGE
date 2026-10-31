// Dialogue box: a sheet of ruled notebook paper with a portrait, a name tag,
// typewriter text and per-character voice blips. `await say(...)` resolves
// once the player has read the line and tapped to continue.
import Phaser from "phaser";
import { blip, blipEvery, duck, sfx } from "../audio";
import { calm } from "./juice";
import { FONT, INK, PAPER, RED, W, H } from "../consts";
import { api } from "../api";
import { speak, hush, prefetch, ready } from "./voice";

// any case's suspect id works too; a suspect is anyone with a "<id>_portraits" sheet loaded
export type Who = "smudge" | "foot" | "baron" | "narrator" | (string & {});
/** Every line is spoken aloud a page at a time, so the voice and the text never drift apart; `voice: false` keeps one silent. */
export interface Line { who: Who; text: string; expr?: string; voice?: boolean }

const SMUDGE_EXPR = ["neutral", "smug", "surprised", "thinking", "determined", "happy", "worried", "angry"];
const FOOT_EXPR = ["neutral", "happy", "worried", "surprised"];
const NAMES: Record<string, string> = { smudge: "Smudge", foot: "Footnote", baron: "???", narrator: "" };
const SUSPECT_EXPR = ["neutral", "smug", "nervous", "shocked", "angry"];
const TAGS: Record<string, number> = { smudge: 0x16264f, foot: 0xc23c74, baron: 0x2e5cad, narrator: 0x55361a, karat: 0x3a7e99, cyl: 0x22305c, bob: 0x8e1a14, dash: 0xc4401e, rolla: 0x94591e, mu: 0x8c5e2c };
const TAG_COLOURS = [0x3a7e99, 0x8e1a14, 0x55361a, 0x2e5cad, 0x1f8c86, 0x7a1a60, 0x94591e, 0x22305c];
const tagOf = (who: string) => TAGS[who] ?? TAG_COLOURS[[...who].reduce((h, ch) => h + ch.charCodeAt(0), 0) % TAG_COLOURS.length];
const nameOf = (who: string) => NAMES[who] ?? api.current?.suspects[who]?.name ?? who.charAt(0).toUpperCase() + who.slice(1);

const BOX = { x: 8, y: 6, w: W - 16, h: 74 };
const TEXT_X = 110;

/** Split on sentence ends so no page runs past `max` characters (a single long sentence stays whole). */
export function paginate(text: string, max = 110): string[] {
  const sentences = text.match(/[^.!?…]+[.!?…]*\s*/g)?.map((x) => x.trim()).filter(Boolean) ?? [text];
  const pages: string[] = [];
  for (const sent of sentences) {
    const last = pages.length - 1;
    if (last >= 0 && pages[last].length + 1 + sent.length <= max) pages[last] += " " + sent;
    else pages.push(sent);
  }
  return pages.length ? pages : [text];
}

export class Dialogue {
  private scene: Phaser.Scene;
  private root: Phaser.GameObjects.Container;
  private portrait: Phaser.GameObjects.Sprite;
  private nameBg: Phaser.GameObjects.Rectangle;
  private nameText: Phaser.GameObjects.Text;
  private body: Phaser.GameObjects.Text;
  private more: Phaser.GameObjects.Text;
  private typing = false;
  private full = "";
  private shown = 0;
  private resolve: (() => void) | null = null;
  private timer?: Phaser.Time.TimerEvent;
  private talkTimer?: Phaser.Time.TimerEvent;
  private who: Who = "narrator";
  private exprRow = 0;
  /** ticks to wait before the next letter: the pause after a comma or a full stop */
  private hold = 0;
  /** held down (pointer, space or enter): type fast and turn the page by itself */
  private held = false;
  private heldSince = 0;
  /** when the current line finished typing */
  private doneAt = 0;
  active = false;

  private isSuspect(who: string) {
    return !["smudge", "foot", "baron", "narrator"].includes(who) && this.scene.textures.exists(`${who}_portraits`);
  }

  constructor(scene: Phaser.Scene) {
    this.scene = scene;
    const g = scene.add.graphics();
    // drop shadow, paper, ink border, ruled lines and a red margin
    g.fillStyle(0x000000, 0.45).fillRect(BOX.x + 3, BOX.y + 3, BOX.w, BOX.h);
    g.fillStyle(Phaser.Display.Color.HexStringToColor(PAPER).color, 1).fillRect(BOX.x, BOX.y, BOX.w, BOX.h);
    g.lineStyle(1, 0x9cb8dc, 0.9);
    for (let y = BOX.y + 22; y < BOX.y + BOX.h - 2; y += 14) g.lineBetween(BOX.x + 2, y + 0.5, BOX.x + BOX.w - 2, y + 0.5);
    g.lineStyle(1, 0xd47676, 1).lineBetween(TEXT_X - 6.5, BOX.y + 1, TEXT_X - 6.5, BOX.y + BOX.h - 1);
    g.lineStyle(2, Phaser.Display.Color.HexStringToColor(INK).color, 1).strokeRect(BOX.x, BOX.y, BOX.w, BOX.h);
    // three binder holes, a small detail that sells "notebook"
    g.fillStyle(0x0b0f1e, 1);
    for (const hx of [BOX.x + 160, BOX.x + 240, BOX.x + 320]) g.fillCircle(hx, BOX.y + BOX.h - 6, 2);

    this.portrait = scene.add.sprite(BOX.x + 2, BOX.y + 1, "smudge_portraits", 0).setOrigin(0, 0).setCrop(0, 14, 96, BOX.h - 2);
    this.nameBg = scene.add.rectangle(TEXT_X - 2, BOX.y + BOX.h - 6, 60, 13, TAGS.smudge).setOrigin(0, 0).setStrokeStyle(1, 0x05030c);
    this.nameText = scene.add.text(TEXT_X + 4, BOX.y + BOX.h - 5, "", { fontFamily: FONT, fontSize: "10px", color: "#ffffff" });
    this.body = scene.add.text(TEXT_X, BOX.y + 9, "", {
      fontFamily: FONT, fontSize: "11px", color: INK, lineSpacing: 3,
      wordWrap: { width: BOX.x + BOX.w - TEXT_X - 10 },
    });
    this.more = scene.add.text(BOX.x + BOX.w - 12, BOX.y + BOX.h - 14, "▼", { fontFamily: FONT, fontSize: "9px", color: RED });
    scene.tweens.add({ targets: this.more, y: "+=2", yoyo: true, repeat: -1, duration: 380 });

    this.root = scene.add.container(0, 0, [g, this.portrait, this.nameBg, this.nameText, this.body, this.more]);
    this.root.setDepth(1000).setScrollFactor(0).setVisible(false);

    const down = () => { if (!this.held) { this.held = true; this.heldSince = scene.time.now; } this.advance(); };
    const up = () => { this.held = false; };
    scene.input.on("pointerdown", down);
    scene.input.on("pointerup", up);
    scene.input.on("pointerupoutside", up);
    scene.input.keyboard?.on("keydown-SPACE", (e: KeyboardEvent) => { if (!e.repeat) down(); });
    scene.input.keyboard?.on("keyup-SPACE", up);
    scene.input.keyboard?.on("keydown-ENTER", (e: KeyboardEvent) => { if (!e.repeat) down(); });
    scene.input.keyboard?.on("keyup-ENTER", up);
    scene.input.keyboard?.on("keydown-E", () => this.advance());
    // held down: each finished line turns the page by itself after a beat
    const auto = () => {
      if (this.active && !this.typing && this.resolve && this.rushing && scene.time.now - this.doneAt > 240) this.advance();
    };
    scene.events.on("update", auto);
    scene.events.once("shutdown", () => scene.events.off("update", auto));
  }

  async play(lines: Line[]) {
    for (const l of lines) await this.say(l);
    this.hide();
  }

  /** Fast-forwarding: the button has been held a moment, not just tapped. */
  private get rushing() { return this.held && this.scene.time.now - this.heldSince > 280; }

  /** A long line is shown a page at a time; the red ▼ is the "more" click. A page is about two sentences or 110 characters. */
  say(line: Line): Promise<void> {
    const pages = paginate(line.text);
    return (async () => {
      if (line.voice !== false) for (const text of pages) prefetch(line.who, text);   // every page's audio starts loading now
      for (const text of pages) {
        if (line.voice !== false) { await ready(line.who, text); void speak(line.who, text); }   // text and voice start together
        await this.sayPage({ ...line, text });
      }
      if (line.voice !== false) hush();                 // moving on cuts the voice off with the page
    })();
  }

  private sayPage(line: Line): Promise<void> {
    const opening = !this.root.visible || this.root.alpha < 0.5;
    this.active = true;
    this.who = line.who;
    this.scene.tweens.killTweensOf(this.root);      // a hide still fading out would otherwise blank this line
    this.root.setVisible(true);
    duck(true);
    if (opening) {
      // the sheet drops in from above with a rustle
      this.root.setAlpha(0).setY(-16);
      this.scene.tweens.add({ targets: this.root, alpha: 1, y: 0, duration: 170, ease: "Back.easeOut" });
      sfx("open");
    } else {
      this.root.setAlpha(1).setY(0);
    }
    const isSmudge = line.who === "smudge";
    const isFoot = line.who === "foot";
    const isSuspect = this.isSuspect(line.who);
    this.portrait.setVisible(isSmudge || isFoot || isSuspect);
    if (isSuspect) {
      this.exprRow = Math.max(0, SUSPECT_EXPR.indexOf(line.expr ?? "neutral"));
      this.portrait.setTexture(`${line.who}_portraits`, this.exprRow * 3).setY(BOX.y - 13);
    }
    if (isSmudge) {
      this.exprRow = Math.max(0, SMUDGE_EXPR.indexOf(line.expr ?? "neutral"));
      this.portrait.setTexture("smudge_portraits", this.exprRow * 5).setY(BOX.y - 13);
    } else if (isFoot) {
      this.portrait.setTexture("foot_portraits", Math.max(0, FOOT_EXPR.indexOf(line.expr ?? "neutral"))).setY(BOX.y - 13);
    }
    const name = nameOf(line.who);
    this.nameText.setText(name);
    this.nameBg.setVisible(!!name).setFillStyle(tagOf(line.who));
    this.nameBg.width = this.nameText.width + 12;
    this.body.setX(isSmudge || isFoot || isSuspect ? TEXT_X : 24);
    this.body.setStyle({ fontStyle: line.who === "narrator" ? "italic" : "normal" });
    this.full = line.text.replace(/f(?=[fil])/g, "f\u200c");   // the pixel font draws "fi" as one odd glyph ("Arst"); a zero-width break keeps the letters apart
    this.shown = 0;
    this.hold = 0;
    // a shout, or a shock, shakes the sheet and makes the face flinch
    if (/!\s*$/.test(line.text) || ["shocked", "angry", "surprised"].includes(line.expr ?? "")) {
      if (!calm()) this.scene.tweens.add({ targets: this.root, x: { from: -3, to: 3 }, duration: 40, yoyo: true, repeat: 2, onComplete: () => this.root.setX(0) });
      this.scene.tweens.add({ targets: this.portrait, scaleX: 1.08, scaleY: 1.08, duration: 70, yoyo: true });
    }
    this.body.setText("");
    this.more.setVisible(false);
    this.typing = true;
    this.timer?.remove();
    this.timer = this.scene.time.addEvent({ delay: 28, loop: true, callback: () => this.tick() });
    this.startTalk();
    return new Promise((res) => { this.resolve = res; });
  }

  private startTalk() {
    this.talkTimer?.remove();
    let f = 0;
    this.talkTimer = this.scene.time.addEvent({
      delay: 110, loop: true, callback: () => {
        if (!this.typing) { this.restFace(); return; }
        f++;
        if (this.who === "smudge") this.portrait.setFrame(this.exprRow * 5 + 2 + (f % 3));
        if (this.who === "foot") this.portrait.y = BOX.y - 13 - (f % 2);
        if (this.isSuspect(this.who)) this.portrait.setFrame(this.exprRow * 3 + 1 + (f % 2));
      },
    });
  }

  private restFace() {
    if (this.isSuspect(this.who)) this.portrait.setFrame(this.exprRow * 3);
    if (this.who === "smudge") {
      const blink = Math.random() < 0.04;
      this.portrait.setFrame(this.exprRow * 5 + (blink ? 1 : 0));
    }
    this.portrait.y = BOX.y - 13;
  }

  private tick() {
    if (!this.typing) return;
    if (this.rushing) { this.shown += 4; this.hold = 0; }
    else if (this.hold > 0) { this.hold--; return; }
    else this.shown++;
    const ch = this.full[this.shown - 1];
    if (ch && /[a-z0-9]/i.test(ch) && this.shown % blipEvery(this.who) === 0) blip(this.who);
    // breathe at punctuation, but not inside "3.5" or "..." mid-word
    const after = this.full[this.shown] ?? " ";
    if (ch && after === " ") this.hold = /[.!?]/.test(ch) ? 7 : /[,;:]/.test(ch) ? 3 : 0;
    this.body.setText(this.full.slice(0, this.shown));
    if (this.shown >= this.full.length) this.finishTyping();
  }

  private finishTyping() {
    this.typing = false;
    this.timer?.remove();
    this.body.setText(this.full);
    this.more.setVisible(true);
    this.doneAt = this.scene.time.now;
  }

  advance() {
    if (!this.active) return;
    if (this.typing) { this.finishTyping(); return; }
    const r = this.resolve;
    this.resolve = null;
    r?.();
  }

  hide() {
    this.active = false;
    this.talkTimer?.remove();
    duck(false);
    this.scene.tweens.add({ targets: this.root, alpha: 0, y: -10, duration: 140, ease: "Quad.easeIn", onComplete: () => this.root.setVisible(false).setY(0) });
  }
}
