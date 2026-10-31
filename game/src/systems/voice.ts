// Talking to the suspects out loud: hold-to-talk speech recognition in, browser speech synthesis out.
// Both are on-device or browser-provided and free. Typing always works; without recognition the mic hides.
import { voiceOf } from "../audio/voices";

type Mode = "off" | "on" | "suspects";
const KEY = "smudge.voice";

export function voiceMode(): Mode {
  try { return (localStorage.getItem(KEY) as Mode) || "suspects"; } catch { return "suspects"; }
}
export function setVoiceMode(m: Mode) {
  try { localStorage.setItem(KEY, m); } catch { /* private window: this session only */ }
}

const Rec: any = (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition;
export const canListen = () => Boolean(Rec) && voiceMode() !== "off";

/** Start listening; onText gets interim and final transcripts. Call the returned function to stop. */
export function listen(onText: (text: string, final: boolean) => void): () => void {
  hush();                                    // talking over a suspect cuts them off
  const rec = new Rec();
  rec.lang = "en-IN";
  rec.interimResults = true;
  rec.continuous = true;
  rec.onresult = (e: any) => {
    let text = "", final = false;
    for (let n = 0; n < e.results.length; n++) {
      text += e.results[n][0].transcript;
      final = e.results[n].isFinal;
    }
    onText(text.trim(), final);
  };
  rec.onerror = () => { /* no mic, denied, or offline: typing still works */ };
  try { rec.start(); } catch { /* already running */ }
  return () => { try { rec.stop(); } catch { /* already stopped */ } };
}

let talking = false;
export const speaking = () => talking;

/** Speak a reply in this speaker's voice: pitch follows their blip voice, deep voices also slow down. */
export function speak(who: string, text: string): Promise<void> {
  const mode = voiceMode();
  if (mode === "off" || !("speechSynthesis" in window) || (mode === "suspects" && (who === "smudge" || who === "foot"))) {
    return Promise.resolve();
  }
  hush();
  const v = voiceOf(who);
  const mid = (v.lo + v.hi) / 2;
  const u = new SpeechSynthesisUtterance(text);
  u.pitch = Math.min(2, Math.max(0.1, mid / 220));
  u.rate = Math.min(1.3, Math.max(0.75, 0.8 + mid / 1500));
  u.lang = "en-IN";
  talking = true;
  return new Promise((resolve) => {
    u.onend = u.onerror = () => { talking = false; resolve(); };
    speechSynthesis.speak(u);
  });
}

export function hush() {
  if ("speechSynthesis" in window) speechSynthesis.cancel();
  talking = false;
}

const LABEL: Record<Mode, string> = { on: "🗣 Voices: all", suspects: "🗣 Voices: suspects", off: "🗣 Voices: off" };
const NEXT: Record<Mode, Mode> = { suspects: "on", on: "off", off: "suspects" };

/** A small corner button that cycles the voice setting. Top-left, so the docked Observatory never covers it. */
export function installVoiceToggle() {
  const b = document.createElement("button");
  b.type = "button";
  b.style.cssText = `position:fixed;top:max(10px,env(safe-area-inset-top,0px));left:max(10px,env(safe-area-inset-left,0px));z-index:49;
    font:600 12px/1 "Pixelify Sans",monospace;padding:6px 9px;border-radius:3px;border:2px solid #0E1938;background:#F2E9CF;color:#0E1938;cursor:pointer`;
  const show = () => { b.textContent = LABEL[voiceMode()]; };
  b.onclick = () => { setVoiceMode(NEXT[voiceMode()]); if (voiceMode() === "off") hush(); show(); };
  show();
  document.body.appendChild(b);
}

// ui.ts imports this module, so the toggle installs itself: no hook needed in main.ts.
if (typeof document !== "undefined") {
  if (document.body) installVoiceToggle();
  else document.addEventListener("DOMContentLoaded", installVoiceToggle, { once: true });
}
