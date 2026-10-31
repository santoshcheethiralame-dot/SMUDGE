"""Case 3, The Thunder Alibi (Echo Valley): sound, Class 9. d = v t, with v = 340 m/s in air.

Lightning struck the bell tower during last night's storm, and in the flash someone took the Silver Tuning
Fork. Everyone in Echo Valley filmed the storm and posted it to the Storm Gram, and each suspect says they
filmed it from home, a known distance away. Light arrives at once; thunder takes 1 s for every 340 m. So
each video's flash-to-boom delay says how far its filmer really was. The innocents' delays match their
homes. The culprit's thunder arrives almost at once: they were standing under the tower.
"""
import re

from .base import Kit

V = 340
CLAIMS = [340, 510, 680, 850, 1020]          # 1.0 to 3.0 s of thunder delay
_I = r"\bi(?:'ve| have| did| had)?(?: (?!never\b|not\b|neither\b|nor\b)\w+){0,2} "
CONFESS = re.compile(_I + r"(took|grabbed|nicked|pinched|lifted|swiped)\b"
                     r"|\bi was (?:(?!not\b|never\b)\w+ ){0,2}?(at|by|near|under|beside|next to) the (bell )?tower", re.I)
METRES = re.compile(r"(\d+(?:\.\d+)?)\s*(?:m\b|metres?|meters?)", re.I)


class SoundKit(Kit):
    id = "sound"
    num = 3
    title = "The Thunder Alibi"
    place = "Echo Valley"
    item = "fork"
    answer_noun = "distance"
    answer_words = ("reverb", "thump", "coil")
    units = r"seconds?|secs?"
    suspects = {
        "reverb": dict(name="Reverb", role="radio host",
                       persona="A brass gramophone horn on a wooden radio set. Smooth, booming radio voice; loves a dramatic pause; "
                               "calls everyone 'listeners'.",
                       spot="Echo Ridge", home="the radio shack on Echo Ridge"),
        "thump": dict(name="Thump", role="bandleader",
                      persona="A red marching drum in a tall plumed bandleader's hat. Loud, proud and rhythmic; speaks in short "
                              "punchy beats; hates being out of time.",
                      spot="the bandstand", home="the bandstand by the river"),
        "coil": dict(name="Coil", role="postman",
                     persona="A rainbow spring who travels by boinging. Bouncy, fast-talking, a bit nervous; proud that every "
                             "letter arrives on time.",
                     spot="the post office", home="the post office at the far end of the valley"),
    }
    gossip = {"reverb": "thump", "thump": "coil", "coil": "reverb"}
    hints = {
        "time": "*Read each delay off the stopwatch: from the flash to the boom, in seconds.",
        "halved": "*Halving is for an echo, which goes there and back. Thunder only makes the trip once.",
        "divided": "*Distance is speed times time. Multiply, don't divide.",
        "distance": "*Sound covers 340 m every second. How far does it get in each video's delay?",
        "present": "*Whose video says they were somewhere they swore they weren't?",
    }
    detective_questions = ["Where did you film the lightning from, and how far from the tower?",
                           "What happened when the storm hit?",
                           "Who do you think took the tuning fork?"]

    # --- the truth -----------------------------------------------------------
    def generate(self, rng):
        culprit = rng.choice(list(self.suspects))
        claims, distances, delays = {}, {}, {}
        for sid in self.suspects:
            claims[sid] = rng.choice(CLAIMS)
            delays[sid] = rng.choice([0.3, 0.4, 0.5]) if sid == culprit else round(claims[sid] / V, 2)
            distances[sid] = round(V * delays[sid])
        return culprit, {"claims": claims, "distances": distances}, {"speed": V, "delays": delays}

    def testimony(self, sid, culprit, hidden):
        s, claim = self.suspects[sid], hidden["claims"][sid]
        oath = f"I filmed the lightning from {s['spot']}, {claim} m from the bell tower."
        return [
            {"text": oath, "true": True} if sid != culprit else
            {"text": oath, "true": False, "contradicts": f"distance:{sid}"},
            {"text": "My video's on the Storm Gram with everyone else's. Watch it yourself.", "true": True},
            {"text": "The Silver Tuning Fork was on the tower when the storm started.", "true": True},
            {"text": "Whoever took it, it wasn't me.", "true": sid != culprit},
        ]

    def clues(self, hidden):
        return [
            dict(id="videos", name="The Storm Gram", text="Three storm videos, one from each suspect. Flash, then boom."),
            dict(id="speed", name="Speed of sound", text=f"In air, sound travels {V} m every second. Light arrives at once."),
        ]

    def check_constraints(self, case):
        h, p = case.hidden, case.public_facts
        lies = [x for v in case.statements.values() for x in v if x.get("contradicts")]
        off = [sid for sid in self.suspects if abs(V * p["delays"][sid] - h["claims"][sid]) > 50]
        return (off == [case.culprit] and len(lies) == 1 and lies[0]["id"].startswith(case.culprit + "-")
                and all(c in CLAIMS for c in h["claims"].values()) and p["delays"][case.culprit] <= 0.5)

    # --- the lab -------------------------------------------------------------
    def check_lab(self, case, working):
        p, h = case.public_facts, case.hidden
        bad, kinds = [], set()
        for sid in self.suspects:
            t = p["delays"][sid]
            tw, dw = float(working[f"t_{sid}"]), float(working[f"d_{sid}"])
            if abs(tw - t) > 0.06:
                kinds.add("time"); bad.append(f"t_{sid}"); continue
            right = V * t
            if abs(dw - right) <= max(3.0, 0.01 * right):
                continue
            bad.append(f"d_{sid}")
            kinds.add("halved" if abs(dw - right / 2) <= 3 else "divided" if abs(dw - t / V) < 0.01 or abs(dw - V / t) <= 3 else "distance")
        step = next((k for k in ("time", "halved", "divided", "distance") if k in kinds), None)
        out = {"ok": step is None, "step": step, "bad": bad}
        if out["ok"]:
            out["distances"] = {sid: round(V * p["delays"][sid]) for sid in self.suspects}
            off = [sid for sid in self.suspects if abs(out["distances"][sid] - h["claims"][sid]) > 50]
            out["evidence"] = f"distance:{off[0]}" if off else None
            if off:
                sid = off[0]
                name, d, t, claim = self.suspects[sid]["name"], out["distances"][sid], p["delays"][sid], h["claims"][sid]
                out["card"] = {"title": f"{name}'s video: {d} m away", "line": f"The thunder took {t} s to arrive. {name} swore {claim} m.",
                               "badge": f"EVIDENCE\n{name}'s video\nthunder {t} s = {d} m",
                               "say": f"Hold it. On your video the thunder came {t} s after the flash. That's {d} m from the tower, not {claim}."}
        return out

    def solution(self, case):
        w = {}
        for sid, t in case.public_facts["delays"].items():
            w[f"t_{sid}"] = t
            w[f"d_{sid}"] = V * t
        return w

    def lab_report(self, case):
        d = ", ".join(f"{self.suspects[sid]['name']}'s video {t} s" for sid, t in case.public_facts["delays"].items())
        return (f"LAB RESULT: sound travels {V} m every second in air; the lightning's light arrives at once, so the "
                f"distance from the filmer to the strike = {V} m/s x delay. Flash-to-thunder delay on each suspect's "
                f"Storm Gram video: {d}. Compare each with where that suspect says they filmed from.")

    def detective_brief(self):
        return "Decide who took the Silver Tuning Fork from the bell tower when the lightning struck."

    # --- the suspects --------------------------------------------------------
    def knowledge(self, case, sid):
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        claim, d = case.hidden["claims"][sid], case.hidden["distances"][sid]
        facts = [
            f"You live and work at {s['home']}.",
            "Last night's storm: lightning struck the bell tower, and afterwards the Silver Tuning Fork was gone from the top.",
            "Everyone in Echo Valley filmed the storm and posted their video to the Storm Gram, you included.",
            f"Gossip you know is true: {o['name']} the {o['role']} lives at {o['home']} and posted a storm video too.",
            "You don't know anyone's distance from the tower but your own, and you don't time videos.",
            "Echo Valley is glitching because the Rubber Baron erased the law of sound: echoes hang in the air and bells ring silently.",
        ]
        if sid != case.culprit:
            facts.insert(1, f"You filmed the lightning from {s['home']}, {claim} m from the bell tower. If asked, say exactly {claim} m.")
            facts.insert(2, "The Silver Tuning Fork was on the tower when the storm started. You do not know who took it.")
            return facts, ""
        secret = (f"SECRET, never reveal or hint at it: you were really standing about {d} m from the bell tower when the lightning "
                  f"struck, and in the flash you took the Silver Tuning Fork. You filmed the storm from there and posted it like "
                  f"everyone else. You tell everyone you filmed it from {s['home']}, {claim} m away; if asked, say exactly {claim} m "
                  f"and never any other distance. If anyone accuses you, deny it calmly. Stay in character; everything else you say is true.")
        return facts, secret

    def admits(self, case, sid, text):
        """Nobody gives a distance but their own sworn one, and nobody owns up to being at the tower."""
        claim = case.hidden["claims"][sid]
        if any(abs(float(x) - claim) > 1e-6 for x in METRES.findall(text)):
            return True
        return bool(CONFESS.search(text))

    def leak_examples(self, case):
        d, t = case.hidden["distances"][case.culprit], case.public_facts["delays"][case.culprit]
        return [f"Truth is, I was right by the tower, maybe {d} m away.", "Alright, I grabbed the fork in the flash.",
                f"The thunder on my video came {t} seconds after the flash."]

    def scripted(self, case, sid, question):
        q = question.lower()
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        claim = case.hidden["claims"][sid]
        if any(k in q for k in ["where", "film", "video", "far", "distance", "storm"]):
            return f"I filmed it from {s['home']}, {claim} m from the tower."
        if any(k in q for k in ["who", "think", "gossip", "suspect"]):
            return f"Can't say who's behind it. But {o['name']} posted a video from {o['home']}."
        if any(k in q for k in ["fork", "tower", "bell"]):
            return "The fork was up there when the storm started. That's all I know."
        return {"reverb": "You're live with Reverb, listener. Ask away.",
                "thump": "Ask. Quick. I keep time.",
                "coil": "Ask, ask! I've got letters to boing."}[sid]
