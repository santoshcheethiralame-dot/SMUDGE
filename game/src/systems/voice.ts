// Talking to the suspects out loud: hold-to-talk speech recognition in, browser speech synthesis out.
// Both are on-device or browser-provided and free. Typing always works; without recognition the mic hides.
import { voiceOf } from "../audio/voices";
import { isMuted } from "../audio";

const Rec: any = (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition;
export const canListen = () => Boolean(Rec);

/** Start listening; onText gets interim and final transcripts. Call the returned function to stop. */
export function listen(onText: (text: string, final: boolean) => void, onError?: (why: string) => void): () => void {
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
  rec.onerror = (e: any) => { onError?.(String(e?.error ?? "error")); };   // typing still works
  try { rec.start(); } catch { /* already running */ }
  return () => { try { rec.stop(); } catch { /* already stopped */ } };
}

/** Each speaker gets their own installed voice (stable from their id), so the cast doesn't all sound alike.
 *  English voices first; Footnote and Smudge take the first two so they stay distinct from the suspects. */
function pickVoice(who: string): SpeechSynthesisVoice | null {
  const all = speechSynthesis.getVoices();
  const en = all.filter((x) => /^en/i.test(x.lang));
  const pool = en.length ? en : all;
  if (!pool.length) return null;
  // the neural voices (Edge "Natural"/"Online", Chrome "Google") sound human; the rest are the robotic offline ones
  const quality = (x: SpeechSynthesisVoice) => (/natural|online/i.test(x.name) ? 0 : /google/i.test(x.name) ? 1 : 2);
  const good = pool.filter((x) => quality(x) < 2);
  const ranked = (good.length >= 2 ? good : pool).slice().sort((x, y) => quality(x) - quality(y) || x.name.localeCompare(y.name));
  const h = [...who].reduce((a, ch) => a * 31 + ch.charCodeAt(0), 7) >>> 0;
  return ranked[h % ranked.length];
}
if ("speechSynthesis" in window) speechSynthesis.getVoices();   // voices load lazily in Chrome; warm the list

let talking = false;
let finish: (() => void) | null = null;       // ends the line being spoken, so nothing waits on a speech that never ends
export const speaking = () => talking;

/** Speak a reply in this speaker's voice: pitch follows their blip voice, deep voices also slow down. */
export function speak(who: string, text: string): Promise<void> {
  // everyone is voiced; the speaker button / M key (the game's mute) silences speech too
  text = text.replace(/^\*+\s*/, "");
  if (!("speechSynthesis" in window) || isMuted() || !text.trim()) return Promise.resolve();
  hush();
  const v = voiceOf(who);
  const mid = (v.lo + v.hi) / 2;
  const u = new SpeechSynthesisUtterance(text);
  u.pitch = Math.min(2, Math.max(0.1, mid / 220));
  u.rate = Math.min(1.3, Math.max(0.75, 0.8 + mid / 1500));
  const pick = pickVoice(who);
  if (pick) { u.voice = pick; u.lang = pick.lang; } else u.lang = "en-IN";
  talking = true;
  return new Promise((resolve) => {
    // Chrome sometimes never fires onend (no voices installed, a long line, a tab in the background), which would
    // freeze the next question; so a timer ends the line too, a little after it should have finished.
    const guard = setTimeout(() => done(), 1500 + text.split(/\s+/).length * 450);
    const done = () => { clearTimeout(guard); if (finish === done) { finish = null; talking = false; } resolve(); };
    finish = done;
    u.onend = done;
    // a chosen voice that fails (a network voice with no network, say) would leave that speaker mute: retry once with the default voice
    u.onerror = (e) => {
      const why = (e as SpeechSynthesisErrorEvent).error;
      if (u.voice && why !== "interrupted" && why !== "canceled" && finish === done) {
        const again = new SpeechSynthesisUtterance(text);
        again.pitch = u.pitch; again.rate = u.rate; again.lang = "en-IN";
        again.onend = again.onerror = done;
        try { speechSynthesis.speak(again); return; } catch { /* fall through */ }
      }
      done();
    };
    try { speechSynthesis.speak(u); } catch { done(); }
  });
}

export function hush() {
  if ("speechSynthesis" in window) { try { speechSynthesis.cancel(); } catch { /* nothing to cancel */ } }
  const f = finish;
  finish = null;
  talking = false;
  f?.();
}
