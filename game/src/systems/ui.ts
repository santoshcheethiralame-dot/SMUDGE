// HTML overlays positioned over the canvas: text input for free questions and
// the lab notebook. Kept in the DOM so phone keyboards and typing just work.
import Phaser from "phaser";
import { W } from "../consts";
import { sfx } from "../audio";
import { canListen, listen } from "./voice";

const FONT = '"Smudge Digits", "Pixelify Sans", monospace';

/** Motion for the HTML overlays, injected once: slide in, shake on a wrong answer, stamp on a right one. */
const STYLE = `
@keyframes smIn { from { transform: translateY(14px); opacity: 0 } to { transform: none; opacity: 1 } }
@keyframes smShake { 0%,100% { transform: translateX(0) } 20% { transform: translateX(-6px) } 40% { transform: translateX(5px) }
  60% { transform: translateX(-4px) } 80% { transform: translateX(2px) } }
@keyframes smStamp { from { transform: scale(2.6) rotate(-12deg); opacity: 0 } to { transform: scale(1) rotate(-12deg); opacity: .92 } }
.sm-in { animation: smIn .22s cubic-bezier(.2,1.4,.4,1) both }
.sm-shake { animation: smShake .34s ease both }
.sm-stamp { animation: smStamp .16s ease-in both }
.sm-btn { transition: transform .08s ease, filter .12s ease }
.sm-btn:hover { transform: translateY(-1px) scale(1.04); filter: brightness(1.1) }
.sm-btn:active { transform: scale(.94) }
.sm-btn:disabled { filter: grayscale(.6) brightness(.9); cursor: wait }
@media (prefers-reduced-motion: reduce) { .sm-in, .sm-shake, .sm-stamp { animation: none } }`;
if (!document.getElementById("sm-style")) {
  const st = document.createElement("style");
  st.id = "sm-style";
  st.textContent = STYLE;
  document.head.appendChild(st);
}

/** Hover, press and typing sounds for an overlay's buttons and fields. */
export function feel(root: HTMLElement) {
  root.querySelectorAll("button").forEach((b) => {
    b.classList.add("sm-btn");
    b.addEventListener("pointerenter", () => sfx("hover"));
    b.addEventListener("pointerdown", () => sfx("click"));
  });
  root.querySelectorAll("input").forEach((i) => i.addEventListener("keydown", (e) => {
    if (!i.readOnly && e.key.length === 1) sfx("type");
  }));
}

/** Replay a CSS animation class on an element. */
export function replay(el: HTMLElement, cls: string) {
  el.classList.remove(cls);
  void el.offsetWidth;
  el.classList.add(cls);
}

function canvasRect(scene: Phaser.Scene) {
  return scene.game.canvas.getBoundingClientRect();
}

/** Places an HTML element over game coordinates (x, y, w, h) and keeps it there on resize. */
export function overlay(scene: Phaser.Scene, el: HTMLElement, x: number, y: number, w: number, h: number) {
  const place = () => {
    const r = canvasRect(scene);
    const s = r.width / W;
    Object.assign(el.style, {
      position: "fixed", left: `${r.left + x * s}px`, top: `${r.top + y * s}px`,
      width: `${w * s}px`, height: `${h * s}px`, fontSize: `${Math.max(12, 9 * s)}px`, zIndex: "10",
    });
  };
  place();
  // every overlay slides in, and its buttons and fields answer with sound
  el.classList.add("sm-in");
  feel(el);
  document.body.appendChild(el);
  scene.scale.on("resize", place);
  window.addEventListener("resize", place);
  return () => {
    scene.scale.off("resize", place);
    window.removeEventListener("resize", place);
    el.remove();
  };
}

/** Ask-box: suggested question chips plus a free-text field. Resolves with a question, or null for "Done". */
export function askBox(scene: Phaser.Scene, chips: string[], placeholder: string): Promise<string | null> {
  return new Promise((resolve) => {
    const wrap = document.createElement("div");
    wrap.style.cssText = `display:flex;flex-direction:column;gap:6px;font-family:${FONT};`;
    const row = document.createElement("div");
    row.style.cssText = "display:flex;flex-wrap:wrap;gap:6px;";
    for (const [n, c] of chips.entries()) {
      const b = document.createElement("button");
      b.className = "sm-in";
      b.style.animationDelay = `${60 + n * 50}ms`;
      b.textContent = c;
      b.style.cssText = `font:inherit;font-size:0.9em;padding:4px 10px;border-radius:12px;border:2px solid #0E1938;background:#F2E9CF;color:#0E1938;cursor:pointer;`;
      b.onclick = () => finish(c);
      row.appendChild(b);
    }
    const form = document.createElement("form");
    form.style.cssText = "display:flex;gap:6px;";
    const input = document.createElement("input");
    input.id = "ask-input";
    input.placeholder = placeholder;
    input.maxLength = 160;
    input.autocomplete = "off";
    input.style.cssText = `flex:1;font:inherit;padding:6px 8px;border:2px solid #0E1938;background:#FFFBEF;color:#0E1938;border-radius:6px;min-width:0;`;
    const send = document.createElement("button");
    send.type = "submit";
    send.textContent = "Send";
    send.style.cssText = `font:inherit;padding:4px 12px;border:2px solid #0E1938;background:#C9302A;color:#fff;border-radius:6px;cursor:pointer;`;
    const done = document.createElement("button");
    done.type = "button";
    done.textContent = "Done";
    done.style.cssText = `font:inherit;padding:4px 12px;border:2px solid #0E1938;background:#0E1938;color:#F2E9CF;border-radius:6px;cursor:pointer;`;
    done.onclick = () => finish(null);
    const mic = document.createElement("button");
    mic.type = "button";
    mic.textContent = "🎙 Hold to talk";
    mic.setAttribute("aria-label", "Hold to ask out loud");
    mic.style.cssText = `font:inherit;padding:4px 10px;border:2px solid #0E1938;background:#F2E9CF;color:#0E1938;border-radius:6px;cursor:pointer;touch-action:none;`;
    let stop: (() => void) | null = null;
    const down = (e: Event) => {
      e.preventDefault();
      if (stop) return;
      mic.style.background = "#F07AAE";
      input.value = "";
      input.placeholder = "Listening... let go to send";
      stop = listen((text) => { input.value = text; }, (why) => {
        input.placeholder = why === "not-allowed" || why === "service-not-allowed" ? "Mic blocked: allow it in the browser, or type"
          : why === "network" ? "Speech needs internet (Chrome sends audio to Google). Type instead" : `Mic problem (${why}). Type instead`;
      });
    };
    const up = () => {
      if (!stop) return;
      stop();
      stop = null;
      mic.style.background = "#F2E9CF";
      // the last words arrive just after release; give them a moment, then ask
      setTimeout(() => {
        const v = input.value.trim();
        if (v) finish(v);
        else if (input.placeholder.startsWith("Listening")) input.placeholder = "Didn't catch that. Hold 🎙 and try again, or type.";
      }, 600);
    };
    mic.addEventListener("pointerdown", down);
    mic.addEventListener("pointerup", up);
    mic.addEventListener("pointerleave", up);
    form.append(input, ...(canListen() ? [mic] : []), send, done);
    form.onsubmit = (e) => { e.preventDefault(); const v = input.value.trim(); if (v) finish(v); };
    wrap.append(row, form);
    ["pointerdown", "keydown", "keyup"].forEach((ev) => wrap.addEventListener(ev, (e) => e.stopPropagation()));
    const remove = overlay(scene, wrap, 14, 196, 452, 66);
    scene.input.keyboard!.enabled = false;
    setTimeout(() => input.focus(), 50);
    function finish(v: string | null) {
      remove();
      scene.input.keyboard!.enabled = true;
      resolve(v);
    }
  });
}
