// Talking to the suspects out loud: hold-to-talk speech recognition in, browser speech synthesis out.
// Both are on-device or browser-provided and free. Typing always works; without recognition the mic hides.
import { voiceOf } from "../audio/voices";
import { isMuted } from "../audio";

const Rec: any = (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition;
const canRecord = () => Boolean(navigator.mediaDevices?.getUserMedia) && typeof MediaRecorder !== "undefined";
export const canListen = () => Boolean(Rec) || canRecord();

const SARVAM_WAIT = 4000;   // after release, how long Sarvam gets before the browser's own transcript is used

/** Send a clip to the server, which asks Sarvam (the key lives there). Resolves null on any failure. */
async function sarvam(blob: Blob): Promise<string | null> {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), SARVAM_WAIT);
  try {
    const r = await fetch("/api/stt", { method: "POST", body: blob, headers: { "Content-Type": blob.type || "audio/webm" }, signal: ctl.signal });
    if (!r.ok) return null;
    return ((await r.json()).text ?? "").trim() || null;
  } catch { return null; } finally { clearTimeout(t); }
}

/** Start listening; onText gets interim and final transcripts. Call the returned function to stop: it returns a
 *  promise that settles once the final text has been delivered (Sarvam's if it answered in time, else the browser's).
 *  Two recognisers run at once: the browser's own for live words and as the fallback, and Sarvam on the recorded clip. */
export function listen(onText: (text: string, final: boolean) => void, onError?: (why: string) => void): () => Promise<void> {
  hush();                                    // talking over a suspect cuts them off
  let local = "";
  let rec: any = null;
  if (Rec) {
    rec = new Rec();
    rec.lang = "en-IN";
    rec.interimResults = true;
    rec.continuous = true;
    rec.onresult = (e: any) => {
      let text = "", final = false;
      for (let n = 0; n < e.results.length; n++) {
        text += e.results[n][0].transcript;
        final = e.results[n].isFinal;
      }
      local = text.trim();
      onText(local, final);
    };
    // with Sarvam recording alongside, a browser-recogniser error is not fatal; only report it when it is all we have
    rec.onerror = (e: any) => { if (!canRecord()) onError?.(String(e?.error ?? "error")); };
    try { rec.start(); } catch { /* already running */ }
  }

  let clip: Promise<Blob | null> = Promise.resolve(null);
  let recorder: MediaRecorder | null = null;
  let live = true;
  if (canRecord()) {
    clip = navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
      const chunks: Blob[] = [];
      const mr = new MediaRecorder(stream);
      recorder = mr;
      mr.ondataavailable = (e) => { if (e.data.size) chunks.push(e.data); };
      return new Promise<Blob | null>((resolve) => {
        mr.onstop = () => { stream.getTracks().forEach((t) => t.stop()); resolve(chunks.length ? new Blob(chunks, { type: mr.mimeType || "audio/webm" }) : null); };
        if (live) mr.start(); else { stream.getTracks().forEach((t) => t.stop()); resolve(null); }   // released before the mic opened
      });
    }).catch((e) => { if (!Rec) onError?.(e?.name === "NotAllowedError" ? "not-allowed" : "error"); return null; });
  }

  return async () => {
    live = false;
    try { rec?.stop(); } catch { /* already stopped */ }
    try { if (recorder && recorder.state !== "inactive") recorder.stop(); } catch { /* already stopped */ }
    const blob = await Promise.race([clip, new Promise<null>((r) => setTimeout(() => r(null), 1500))]);
    const text = blob ? await sarvam(blob) : null;
    if (text) onText(text, true);
    else if (Rec) await new Promise((r) => setTimeout(r, 600));   // the browser's last words arrive just after release
  };
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

// Spoken lines come from Sarvam (through the server) when it answers, and from the browser's own voice when it doesn't.
const clips = new Map<string, Promise<HTMLAudioElement | null>>();
const clipsReady = new Map<string, HTMLAudioElement>();
let ttsWorked = false;                       // once Sarvam has answered, a slow line waits for it rather than switching to a different voice
let ttsDownUntil = 0;                        // after a failure, skip Sarvam for a while so a dead service never delays a line
let gen = 0;                                 // bumps on every hush(), so a late clip knows it was cut off
let clip: HTMLAudioElement | null = null;    // the line playing right now, if it is a Sarvam clip
const spoken = (text: string) => text.replace(/^\*+\s*/, "");
const clipKey = (who: string, text: string) => `${who}\u0001${text}`;

/** Start fetching a line's audio now, so it is ready by the time the line is shown. Safe to call twice. */
export function prefetch(who: string, text: string) {
  text = spoken(text);
  const k = clipKey(who, text);
  if (!text.trim() || isMuted() || Date.now() < ttsDownUntil || clips.has(k)) return;
  if (clips.size > 80) { const old = clips.keys().next().value!; clips.delete(old); clipsReady.delete(old); }
  clips.set(k, fetch("/api/tts", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ who, text }) })
    .then(async (r) => {
      if (!r.ok) { ttsDownUntil = Date.now() + (r.status === 503 ? 600_000 : 15_000); clips.delete(k); return null; }
      const a = new Audio(URL.createObjectURL(await r.blob()));
      a.preload = "auto";
      ttsWorked = true;
      clipsReady.set(k, a);
      return a;
    })
    .catch(() => { ttsDownUntil = Date.now() + 15_000; clips.delete(k); return null; }));
}

/** Resolves when the line's audio is ready, or after `ms`, whichever comes first, so text and voice can start together
 *  without a slow or dead Sarvam ever holding the text back. */
export async function ready(who: string, text: string, ms = 1500): Promise<void> {
  prefetch(who, text);
  const p = clips.get(clipKey(who, spoken(text)));
  if (p) await Promise.race([p, new Promise((r) => setTimeout(r, ms))]);
}

let talking = false;
let finish: (() => void) | null = null;       // ends the line being spoken, so nothing waits on a speech that never ends
export const speaking = () => talking;

/** Speak a reply in this speaker's voice: the Sarvam clip if it is ready, else the browser's voice. */
export function speak(who: string, text: string): Promise<void> {
  // everyone is voiced; the speaker button / M key (the game's mute) silences speech too
  text = spoken(text);
  if (isMuted() || !text.trim()) return Promise.resolve();
  const k = clipKey(who, text);
  const a = clipsReady.get(k);
  if (a) return playClip(a, () => browserSpeak(who, text));
  prefetch(who, text);
  const pending = clips.get(k);
  // Sarvam is working but this clip is late: wait for it (up to 6 s) so the speaker keeps their own voice.
  // Only when Sarvam is down or has never answered does the browser voice speak the line.
  if (pending && ttsWorked) {
    const mine = gen;             // a newer line or hush() in the meantime means this one is no longer wanted
    return Promise.race([pending, new Promise<null>((r) => setTimeout(() => r(null), 6000))]).then((c) =>
      c && gen === mine ? playClip(c, () => browserSpeak(who, text)) : c ? undefined : gen === mine ? browserSpeak(who, text) : undefined);
  }
  return browserSpeak(who, text);
}

function playClip(a: HTMLAudioElement, fallback: () => Promise<void>): Promise<void> {
  hush();
  talking = true;
  return new Promise((resolve) => {
    const done = () => { a.onended = a.onerror = null; if (finish === done) { finish = null; talking = false; clip = null; } resolve(); };
    finish = done;
    clip = a;
    a.onended = done;
    a.onerror = () => { done(); void fallback(); };
    a.currentTime = 0;
    a.play().catch(() => { done(); void fallback(); });
  });
}

/** Pitch follows the speaker's blip voice, deep voices also slow down. */
function browserSpeak(who: string, text: string): Promise<void> {
  if (!("speechSynthesis" in window)) return Promise.resolve();
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
  gen++;
  if (clip) { try { clip.pause(); } catch { /* already stopped */ } clip = null; }
  if ("speechSynthesis" in window) { try { speechSynthesis.cancel(); } catch { /* nothing to cancel */ } }
  const f = finish;
  finish = null;
  talking = false;
  f?.();
}
