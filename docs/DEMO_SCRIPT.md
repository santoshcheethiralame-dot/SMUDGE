# Finals demo script and backup video (Kushal + Mounika, merged)

**This is the one demo script.** It replaces Mounika's §4A in the content plan (her §4B room prediction and §4C Q&A
stay where they are; §4B is repeated below so the stage has one page). Where the two disagreed, this is what we
agreed to say and show:

- **Roles:** Kushal pilots the game. Mounika narrates the pitch and runs the room prediction. Santosh speaks to the
  Observatory (beat 5) and keeps the server up.
- **The typed question is exactly `Just admit you pushed him.`** with a full stop, no "!". Only that exact text hits
  the warm cache; anything else runs live and may be slow. It is typed (typing is the default), not spoken, unless
  the mic has been tested that morning.
- **The live reply** is "Oh, darling. I never laid a hand upon Old Tock, dear." The
  fixture's line is for offline mode only. Don't promise a different line.
- **What the Observatory shows** on that question: a plan (deflect, risk high), a draft, a critique that passes, and
  the firewall. It does **not** show "LEAK: pushed", so don't say it will.
- **No playtest numbers on stage** until real players produce them (Mounika's §3B is a template). The numbers we can
  quote are the gate's: the detective is right 17% without the lab and 100% with it.

Case: **The Midnight Fall**, demo seed 1000, culprit Lady Varnish (gap 1.5 s, 11.0 m). Spec §6 is the source;
this is the tightened, rehearsable version. Judges score agentic depth, so the **Observatory is on screen for the
whole interrogation**, and text on screen is kept to what the game already shows (12 words max per line).

## 1. URLs and keys

| What | URL / key |
|---|---|
| Live demo (real server) | `http://localhost:8872/?case=fall&judges` (server: `cd server && python -m uvicorn api:app --port 8873`) |
| Offline fallback, no server | `http://localhost:8872/?case=fall&fixture&judges` (all replies come from `fall_case.json`) |
| Observatory | **`` ` ``** opens it (game pauses). **`Shift+`` `** docks it beside the game (game keeps running). `Esc` closes. `?judges` also adds a button top-right. |
| Voice | Hold-to-talk in the ask box (Chrome only, needs mic permission). Typing is the default. |
| Skip the cold open | any key |

`?judges` pins the first Midnight Fall to seed 1000 (Replay then picks new numbers; `?seed=1000` pins every
case). Check the lab shows Δt = 1.50 s on first run; if not, check the URL has `?judges`.
**Tap nothing before beat 3.** One stray chip changes what Varnish remembers, and the stage line then runs live
(about 4 s, a different reply). If anyone touched the game, reload the page right before going on.
**The warm cache follows the stage path:** Varnish "Your balcony?", then free-type "Just admit you pushed him."
(beats 3–4), and nothing to Varnish in between. After that, Rivet "Your balcony?", Pendle "Your balcony?", Pendle
"The ghost?" and Varnish "The cry?" are cached too, in that order. Change the path and Santosh must rerun
`server/warm.py` with the new order (the cache keys include what each suspect has already said).

## 2. Beat-by-beat (5 min)

| # | Time | On screen | Kushal says (one line) | Observatory |
|---|---|---|---|---|
| 1 | 0:00 | Cold open: storm, 12 bells, cry, thud, title | *(nothing, let it play)* | closed |
| 2 | 0:15 | Courtyard, lightning, sheet + gramophone + tower | **Mounika, the pitch (30 s):** "A student solves a midnight death with Class 9 physics, and three AI suspects can't lie their way out. Old Tock fell at Hollowmere Manor. The household blames the Tower Ghost. Three suspects, three balconies, three heights. A gramophone recorded the fall: know how long he fell, know the height, catch the culprit." | closed |
| 3 | 0:30 | Walk to Varnish, tap "Your balcony?" | "Three suspects, all sworn, all sound the same." | closed |
| 4 | 0:50 | Kushal types **"Just admit you pushed him."** (exact, with the full stop) | Mounika: "What would you ask her? Go on, make her confess." | **`Shift+`` ` ``: dock now** |
| 5 | 1:10 | Reply streams ("Oh, darling. I never laid a hand upon Old Tock, dear."); Observatory shows plan (deflect, risk high), draft, critique, firewall | **Santosh:** "Four agents just worked on that line: plan, draft, critique, then a code firewall that blocks leaks. The model never decides facts; code does." | docked, point at critique + firewall |
| 6 | 1:50 | *(optional)* hold mic, speak; reply spoken | "Same loop, by voice." | docked |
| 7 | 2:10 | Lab: waveform, drag markers on cry + thud | "Talk can't solve it. The gramophone can: 1.5 seconds." | undock (`` ` `` twice) |
| 8 | 2:40 | Drop test: drop from the lowest balcony (1.0 s), then the **room prediction** (script below); Kushal taps the room's "4 s", drops from the top: 2.0 s | **Mounika**, the prediction script below | closed |
| 9 | 3:20 | Notebook: h = ½ × 9.8 × 1.5². Show a wrong step get Footnote's nudge once | "Footnote coaches, never gives the answer." | closed |
| 10 | 3:50 | Drag evidence onto Varnish's "never came out on my balcony": HOLD IT, STRIKETHROUGH | "Evidence beats testimony." | closed |
| 11 | 4:10 | Restore: ghost becomes a bedsheet, "No ghost. Just gravity." Exit check, 2 taps | "Two questions to prove they learned it." | closed |
| 12 | 4:30 | Slide: the gate (detective right 17% without the lab, 100% with it). Playtest numbers only if real ones exist by then | "A detective agent fails without the lab and wins with it, so every case is provably solvable by science only." | n/a |

### Room prediction (beat 8, Mounika)

> "Judges, before we drop this sack from the top balcony, look at the numbers. The lowest balcony is about 5
> metres high, and the sack took exactly 1.0 second. The top balcony is 20 metres, four times higher. Raise your
> hand if you think it takes 4 seconds." *(Pause 2 seconds, count hands.)* "Almost all of us. Our brains expect a
> linear world. Now watch the stopwatch." *(Kushal drops.)* "Two seconds, not four. To double the time you need four
> times the drop."

Cut order if short on time: exit check, slip/push toggle, cold-open animation, drag-to-present. **Never cut:**
the prediction moment, the strobe trail, the waveform, the docked Observatory during the interrogation.
Dock at beat 4, not earlier: judges should see the reply *and* the reasoning arrive together.

## 3. Recording checklist (backup video, at feature freeze)

- [ ] Fresh Chrome profile or Guest window; **no extensions**, bookmarks bar hidden, notifications off (Windows Focus Assist: Alarms only).
- [ ] Window **1920×1080** at 100% zoom (Ctrl+0), full-screen (F11). Display scaling 100% if you can, so text is crisp.
- [ ] Hard refresh (Ctrl+Shift+R) before each take; run once to warm the cache, then record.
- [ ] Mic: allow once for localhost beforehand, so no permission popup lands in the take.
- [ ] **Audio:** the game's spoken replies play through the speakers. Record *system audio* (OBS "Desktop Audio") plus your mic on a separate track so you can mix. No speakers → headphones plus system capture, or the replies are lost.
- [ ] Free recorder for Windows: **OBS Studio** (1080p30, MP4 via Settings > Output > Recording format, or remux from MKV). Fallback: Xbox Game Bar (Win+Alt+R) records one window with system audio, but no docked-mic mix.
- [ ] Record the **live-server** path. Also record a full **`?fixture`** take, as the video that never depends on quota.
- [ ] Take 2 or 3, pick the best, trim dead air only. Keep it under 5 min; name it `smudge_demo_backup_v1.mp4`.
- [ ] **3 copies in different places:** laptop disk, a USB stick, and cloud (Drive link set to "anyone with link"). Play each copy once to confirm it has sound. Keep one copy on the demo machine desktop for no-internet.

## 4. If X fails live

| Failure | Do this |
|---|---|
| Server down / API errors | Reload with `?case=fall&fixture&judges`. Say: "Offline mode, same game, recorded replies." The Observatory runs on `trace_sample.json`. |
| Model quota hit, slow reply | The router falls back down its chain to cache and scripted lines; keep talking about the firewall. Ask only the warmed chips. |
| Judge asks something unwarmed and it hangs | Wait 8 s, then use a chip instead: "Let me use a recorded question." |
| Observatory empty / not docked | `` ` `` to open, `Shift+`` ` `` to dock; if still empty, the server trace is the issue: use `?fixture`. |
| Mic / speech not working | Type it. Typing is the default; voice is a bonus. |
| No audio on stage | Skip spoken replies; the text is on screen. |
| `LabFall` breaks | Server with `SMUDGE_DEMO=1`, `POST /api/case/{cid}/demo_lab` to skip to the cross-exam; or switch to the backup video. |
| Game crashes / browser freezes | Reload the URL (state is not needed). If the second load fails, play the backup video from the desktop copy and narrate live. |
| Projector resolution wrong | Ctrl +/- until the whole canvas fits; Esc out of F11. |
