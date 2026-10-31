"""Case 4, The Long Shadow (Lumen Heights): heights and distances, Class 10. tan(elevation) = height / shadow.

At noon someone lifted the Golden Gnomon off the plaza sundial. Every suspect says they were at their own
landmark at noon and sent the Lumen Gazette a photo to prove it, the landmark's height printed underneath. In
Lumen Heights the noon sun stands at 60 degrees; at 10 am and 2 pm it is 45, at 8 am and 4 pm, 30. A shadow
says where the sun was: height / shadow = tan(elevation). The innocents' photos show the noon sun. The
culprit's shows a lower one: it was taken hours away from noon, and at noon they were in the plaza.
"""
import re

from .base import Kit, an

TAN = {30: 0.58, 45: 1.00, 60: 1.73}
TIMES = {30: "8 am or 4 pm", 45: "10 am or 2 pm", 60: "noon"}
SHADOWS = [4, 5, 6, 7]                                 # noon shadows, metres; heights are 1.73 times these
HEIGHTS = {s: round(s * 1.732, 1) for s in SHADOWS}    # 6.9, 8.7, 10.4, 12.1 m
_I = r"\bi(?:'ve| have| did| had)?(?: (?!never\b|not\b|neither\b|nor\b)\w+){0,2} "
CONFESS = re.compile(_I + r"(took|grabbed|nicked|pinched|lifted|swiped|pocketed|unscrewed)\b"
                     r"|\bi was (?:(?!not\b|never\b)\w+ ){0,2}?(at|by|near|in|on) the (plaza|sundial|square)"
                     r"|\bi (?:saw|watched|felt|noticed) (?:the )?(?:golden )?gnomon"
                     r"|^at the (?:sundial|plaza)\b"
                     r"|\b(?:my|the) photo was(?: (?!not\b|never\b)\w+){0,2} (?:taken|snapped|shot) "
                     r"(?:before|after|later|earlier|in the (?:morning|afternoon)|at (?!noon\b|twelve\b|midday\b)\w+)", re.I)
METRES = re.compile(r"(\d+(?:\.\d+)?)\s*(?:m\b|metres?|meters?)", re.I)


def _shadow(h, angle):
    return round(h / (3 ** 0.5 if angle == 60 else 1.0 if angle == 45 else 1 / 3 ** 0.5), 1)


class HeightsKit(Kit):
    id = "heights"
    num = 4
    title = "The Long Shadow"
    place = "Lumen Heights"
    item = "gnomon"
    answer_noun = "time"
    answer_words = ("lumen", "vane", "sola")
    units = r"degrees?|°|o'clock|am|pm"
    suspects = {
        "lumen": dict(name="Lumen", role="lamplighter",
                      persona="A cast-iron street lamp with a glowing glass head. Old-fashioned, gentle and very proper; "
                              "says 'good evening' at every hour; fussy about everyone keeping to schedule.",
                      landmark="the Old Lamp on Ladder Lane"),
        "vane": dict(name="Vane", role="weather forecaster",
                     persona="A copper weathervane with an arrow for a hat. Breezy, dramatic, always pointing somewhere; "
                             "forecasts everything, even conversations.",
                     landmark="the Weathercock Spire"),
        "sola": dict(name="Sola", role="gossip columnist",
                     persona="A sunflower in a terracotta pot who always turns to face the sun. Chatty, warm, nosy; writes "
                             "the 'Sunny Side' column in the Lumen Gazette and calls everyone 'petal'.",
                     landmark="the Sunflower Mill"),
    }
    gossip = {"lumen": "vane", "vane": "sola", "sola": "lumen"}
    hints = {
        "measure": "*Use the heights printed on the photos and the shadows you measured, as they are.",
        "flipped": "*Tan is opposite over adjacent: the height goes on top, the shadow underneath.",
        "ratio": "*Divide each landmark's height by its shadow's length.",
        "angle": "*Find your ratio in the tan table: which angle has that tangent?",
        "present": "*Noon here means one sun angle. Whose photo shows a different one?",
    }
    detective_questions = ["Where were you at noon, and can you prove it?",
                           "What do you know about the missing gnomon?",
                           "Who do you think lifted the gnomon?"]

    # --- the truth -----------------------------------------------------------
    def generate(self, rng):
        culprit = rng.choice(list(self.suspects))
        heights, angles = {}, {}
        for sid in self.suspects:
            heights[sid] = HEIGHTS[rng.choice(SHADOWS)]
            angles[sid] = rng.choice([30, 45]) if sid == culprit else 60
        shadows = {sid: _shadow(heights[sid], angles[sid]) for sid in self.suspects}
        return culprit, {"angles": angles}, {"heights": heights, "shadows": shadows, "noon": 60, "tan": TAN}

    def testimony(self, sid, culprit, hidden):
        s = self.suspects[sid]
        oath = f"At noon I was at {s['landmark']}. I took my Gazette photo there at twelve."
        return [
            {"text": oath, "true": True} if sid != culprit else
            {"text": oath, "true": False, "contradicts": f"time:{sid}"},
            {"text": "My landmark is in the photo, its height printed underneath.", "true": True},
            {"text": "The Golden Gnomon was on the sundial this morning. Everybody saw it.", "true": True},
            {"text": "I never went near the plaza at noon.", "true": sid != culprit},
        ]

    def clues(self, hidden):
        return [
            dict(id="photos", name="The Gazette photos", text="Three alibi photos, each 'taken at noon', each landmark's height printed underneath."),
            dict(id="sun", name="The noon sun", text="In Lumen Heights the noon sun stands at 60°. At 10 am and 2 pm it is 45°, at 8 am and 4 pm, 30°."),
        ]

    def check_constraints(self, case):
        p, h = case.public_facts, case.hidden
        lies = [x for v in case.statements.values() for x in v if x.get("contradicts")]
        off = [sid for sid in self.suspects if self._angle(p["heights"][sid] / p["shadows"][sid]) != 60]
        ok_angles = all(self._angle(p["heights"][sid] / p["shadows"][sid]) == h["angles"][sid] for sid in self.suspects)
        return off == [case.culprit] and ok_angles and len(lies) == 1 and lies[0]["id"].startswith(case.culprit + "-")

    @staticmethod
    def _angle(ratio):
        return min(TAN, key=lambda a: abs(TAN[a] - ratio))

    # --- the lab -------------------------------------------------------------
    def check_lab(self, case, working):
        p = case.public_facts
        bad, kinds = [], set()
        for sid in self.suspects:
            hh, ss = p["heights"][sid], p["shadows"][sid]
            hw, sw, rw, aw = (float(working[f"{k}_{sid}"]) for k in "hsra")
            if abs(hw - hh) > 0.05 or abs(sw - ss) > 0.15:
                kinds.add("measure"); bad.append(f"h_{sid}" if abs(hw - hh) > 0.05 else f"s_{sid}"); continue
            right = hh / ss
            if abs(rw - right) > 0.03:
                bad.append(f"r_{sid}")
                kinds.add("flipped" if abs(rw - ss / hh) <= 0.03 else "ratio")
                continue
            if abs(aw - self._angle(right)) > 0.5:
                bad.append(f"a_{sid}"); kinds.add("angle")
        step = next((k for k in ("measure", "flipped", "ratio", "angle") if k in kinds), None)
        out = {"ok": step is None, "step": step, "bad": bad}
        if out["ok"]:
            out["angles"] = {sid: self._angle(p["heights"][sid] / p["shadows"][sid]) for sid in self.suspects}
            off = [sid for sid, a in out["angles"].items() if a != 60]
            out["evidence"] = f"time:{off[0]}" if off else None
            if off:
                sid = off[0]
                name, a, hh, ss = self.suspects[sid]["name"], out["angles"][sid], p["heights"][sid], p["shadows"][sid]
                out["card"] = {"title": f"{name}'s photo: sun at {a}°",
                               "line": f"{an(hh).capitalize()} {hh} m landmark, {an(ss)} {ss} m shadow: tan = {hh / ss:.2f}, so {a}°. Noon here is 60°. "
                                       f"That photo was taken at {TIMES[a]}.",
                               "badge": f"EVIDENCE\n{name}'s 'noon' photo\nsun at {a}° = {TIMES[a]}",
                               "say": f"Hold it! In your 'noon' photo the sun is at {a}°. At noon it stands at 60°. "
                                      f"That picture was taken at {TIMES[a]}."}
        return out

    def solution(self, case):
        p, w = case.public_facts, {}
        for sid in self.suspects:
            hh, ss = p["heights"][sid], p["shadows"][sid]
            w.update({f"h_{sid}": hh, f"s_{sid}": ss, f"r_{sid}": round(hh / ss, 2), f"a_{sid}": self._angle(hh / ss)})
        return w

    def lab_report(self, case):
        p = case.public_facts
        d = ", ".join(f"{self.suspects[sid]['name']}'s photo: landmark {p['heights'][sid]} m, shadow {p['shadows'][sid]} m"
                      for sid in self.suspects)
        return (f"LAB RESULT: tan(sun's elevation) = landmark height / shadow length. Tan table: 30° 0.58, 45° 1.00, "
                f"60° 1.73. In Lumen Heights the sun stands at 60° at noon, 45° at 10 am and 2 pm, 30° at 8 am and 4 pm. "
                f"Each suspect's alibi photo, which they swear was taken at noon: {d}.")

    def detective_brief(self):
        return "Decide who lifted the Golden Gnomon off the plaza sundial at noon."

    # --- the suspects --------------------------------------------------------
    def knowledge(self, case, sid):
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        h = case.public_facts["heights"][sid]
        facts = [
            f"Your landmark is {s['landmark']}. It is {h} m tall; that height is printed under your photo. If asked, say exactly {h} m.",
            "Today at noon the Golden Gnomon, the brass blade that casts the shadow on the plaza sundial, was lifted off it.",
            "Nobody saw it go. You only heard about it afterwards, from the Gazette's afternoon edition, like everyone else.",
            "Everyone sent the Lumen Gazette a photo of themselves at their landmark to show where they were at noon.",
            f"Gossip you know is true: {o['name']} the {o['role']} sent in a photo from {o['landmark']}.",
            "You never measure shadows or angles and know nothing about anyone's photo but your own.",
            "Lumen Heights is glitching because the Rubber Baron erased the law of heights and distances: shadows point the wrong way.",
        ]
        if sid != case.culprit:
            facts.insert(1, f"At noon you really were at {s['landmark']} and took your photo there at twelve sharp.")
            facts.insert(2, "You do not know who lifted the gnomon.")
            return facts, ""
        a = case.hidden["angles"][sid]
        secret = (f"SECRET, never reveal or hint at it: at noon you were in the plaza and lifted the Golden Gnomon off the "
                  f"sundial. Your 'noon' photo at {s['landmark']} was really taken at {TIMES[a]}. You tell everyone you took "
                  f"it at noon. Talk about the theft only as news you read in the Gazette; never describe seeing it happen or "
                  f"being anywhere near the sundial. Never mention any other time. If anyone accuses you, deny it calmly. Stay in character; "
                  f"everything else you say is true.")
        return facts, secret

    def admits(self, case, sid, text):
        """Nobody gives a length but their own landmark's height; nobody owns up to the plaza or the photo's time."""
        h = case.public_facts["heights"][sid]
        if any(abs(float(x) - h) > 1e-6 for x in METRES.findall(text)):
            return True
        return bool(CONFESS.search(text))

    def leak_examples(self, case):
        a = case.hidden["angles"][case.culprit]
        return ["Fine, I was in the plaza at noon, near the sundial.", "Alright, I lifted the gnomon. It came right off.",
                f"My photo was taken earlier, about {TIMES[a]}."]

    def scripted(self, case, sid, question):
        q = question.lower()
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        h = case.public_facts["heights"][sid]
        if any(k in q for k in ["where", "noon", "prove", "photo", "alibi"]):
            return f"At noon I was at {s['landmark']}. The photo is in the Gazette, with its height, {h} m, printed underneath."
        if any(k in q for k in ["who", "think", "gossip", "suspect"]):
            return f"Can't say who's behind it. {o['name']} sent a photo from {o['landmark']}, I know that."
        if any(k in q for k in ["gnomon", "sundial", "plaza", "see"]):
            return "The gnomon was on the sundial this morning. Everybody saw it."
        return {"lumen": "Good evening, detective. Ask away, but do keep to schedule.",
                "vane": "Forecast: a question, with a strong chance of an answer.",
                "sola": "Ooh, a detective! Ask me anything, petal."}[sid]
