"""Case 10, The Midnight Fall (Hollowmere Manor): free fall, Class 9. h = ½ g t².

At midnight Old Tock the clockkeeper fell from the clock tower, and the household blames the Tower Ghost. Three
balconies look down on the courtyard, one per suspect, each at its own height. The ghost-hunter's gramophone
recorded the cry as he went over and the thud as he landed: the gap is the fall time, h = ½ g t² is the height,
and the height is a balcony. The culprit swears he never came out on theirs. The classic slips are dropping the
half and forgetting to square the time.
"""
import re

from .base import Kit

G = 9.8
PUSH = 3.0               # a running shove, m/s; the chalk outline lands push × t from the wall
_I = r"\bi(?:'ve| have| did| had)?(?: (?!never\b|not\b|neither\b|nor\b)\w+){0,2} "
CONFESS = re.compile(_I + r"(push(?:ed)?|shov(?:e|ed)|knock(?:ed)?|tipp(?:ed)?|threw)\b"
                     r"|\b(he|tock) (was|came out) on my balcony\b|\bfell from my\b", re.I)
METRES = re.compile(r"(\d+(?:\.\d+)?)\s*(?:m\b|metres?|meters?)", re.I)
WORDS = r"\b(won't|wont|didn't|never|not|no)\b"


class FallKit(Kit):
    id = "fall"
    num = 10
    title = "The Midnight Fall"
    place = "Hollowmere Manor"
    item = "tower"
    answer_noun = "balcony"
    answer_words = ("armoury", "gallery", "clock room")
    units = r"s|secs?|seconds?|m/s"
    short = True             # the demo case: one short sentence per reply
    suspects = {
        "rivet": dict(name="Sir Rivet", role="suit of armour", room="armoury", height=4.9, t=1.0,
                      persona="A rusty suit of armour. Booming and brave-sounding, secretly scared of the dark; "
                              "clanks when nervous."),
        "varnish": dict(name="Lady Varnish", role="walking portrait", room="gallery", height=11.0, t=1.5,
                        persona="An oil portrait in a gilt frame who walks the halls. Grand and theatrical, calls "
                                "everyone darling, adores her own reflection."),
        "pendle": dict(name="Pendle", role="clock-room pendulum", room="clock room", height=19.6, t=2.0,
                       persona="The tower clock's pendulum. Anxious, talks in ticks and tocks, swings faster when "
                               "nervous, hates being rushed."),
    }
    gossip = {"rivet": "varnish", "varnish": "pendle", "pendle": "rivet"}
    hints = {
        "gap": "*Measure from the cry to the thud. Not the thunder.",
        "forgot_half": "*Check the formula. Did you keep the half?",
        "not_squared": "*Time gets squared. Square it first.",
        "height": "*h = ½ × g × t². Try again.",
        "present": "*Whose sworn word does the height break?",
    }
    detective_questions = ["Where is your balcony, and did Old Tock come out on it tonight?",
                           "What did you hear at midnight?",
                           "Who do you think made Old Tock fall?"]

    # --- the truth -----------------------------------------------------------
    def generate(self, rng):
        culprit = rng.choice(list(self.suspects))
        t = self.suspects[culprit]["t"]
        cry = rng.choice([1.6, 1.8, 2.0, 2.1, 2.3])
        thunder = [rng.choice([0.5, 0.6, 0.8]), rng.choice([5.1, 5.2, 5.4])]
        return culprit, {"fell_from": culprit}, {
            "g": G, "balconies": {sid: s["height"] for sid, s in self.suspects.items()},
            "recording": {"length": 6.0, "cry_at": cry, "thud_at": round(cry + t, 2), "thunder_at": thunder},
            "landing": {"from_wall": round(PUSH * t, 1)}}

    def testimony(self, sid, culprit, hidden):
        oath = "Old Tock never came out on my balcony tonight."
        return [
            {"text": oath, "true": True} if sid != culprit else
            {"text": oath, "true": False, "contradicts": f"balcony:{sid}"},
            {"text": "I heard a cry, then a thud.", "true": True},
            {"text": "I saw a white shape on the tower.", "true": True},
            {"text": "I never touched Old Tock.", "true": sid != culprit},
        ]

    def clues(self, hidden):
        return [
            dict(id="outline", name="Chalk outline", text="Under the white sheet, out from the tower wall."),
            dict(id="gramophone", name="Ghost-hunter's gramophone", text="Recording all night. It caught the cry and the thud."),
            dict(id="balconies", name="Three balconies", text="Armoury 4.9 m, gallery 11.0 m, clock room 19.6 m."),
        ]

    def _owner(self, t):
        return [sid for sid, s in self.suspects.items() if abs(s["height"] - G * t * t / 2) < 0.3]

    def check_constraints(self, case):
        r = case.public_facts["recording"]
        lies = [x for v in case.statements.values() for x in v if x.get("contradicts")]
        quiet = all(abs(r["cry_at"] - x) > 0.3 and abs(r["thud_at"] - x) > 0.3 for x in r["thunder_at"])
        return (self._owner(r["thud_at"] - r["cry_at"]) == [case.culprit] and quiet and r["thud_at"] < r["length"]
                and len(lies) == 1 and lies[0]["id"].startswith(case.culprit + "-"))

    # --- the lab -------------------------------------------------------------
    def check_lab(self, case, working):
        r = case.public_facts["recording"]
        t = r["thud_at"] - r["cry_at"]
        gap, h = float(working["gap"]), float(working["height"])
        want = G * t * t / 2
        step = ("gap" if abs(gap - t) > 0.1 else None if abs(h - want) <= 0.3
                else "forgot_half" if abs(h - G * t * t) <= 0.3 else "not_squared" if abs(h - G * t / 2) <= 0.3
                else "height")
        out = {"ok": step is None, "step": step}
        if out["ok"]:
            owners = self._owner(t)
            out["height"] = round(want, 1)
            out["evidence"] = f"balcony:{owners[0]}" if owners else None
            if owners:
                s = self.suspects[owners[0]]
                out["card"] = {"title": f"Fell {round(want, 1)} m", "line": f"Only the {s['room']} is that high.",
                               "badge": f"EVIDENCE\nfall {t:g} s\nh = ½gt² = {round(want, 1)} m",
                               "say": f"Hold it. A {t:g} second fall is {round(want, 1)} metres. Your {s['room']}, {s['name']}."}
        return out

    def solution(self, case):
        r = case.public_facts["recording"]
        t = round(r["thud_at"] - r["cry_at"], 2)
        return {"gap": t, "height": round(G * t * t / 2, 2)}

    def lab_report(self, case):
        r = case.public_facts["recording"]
        rooms = ", ".join(f"{s['name']}'s {s['room']} {s['height']} m up" for s in self.suspects.values())
        return (f"LAB RESULT: the gramophone in the courtyard recorded thunder at {r['thunder_at'][0]} s and "
                f"{r['thunder_at'][1]} s, a cry at {r['cry_at']} s as Old Tock went over, and the thud of the landing at "
                f"{r['thud_at']} s. g = {G} m/s². A fall from height h takes time t where h = ½ g t². "
                f"Balconies: {rooms}.")

    def detective_brief(self):
        return "Decide from whose balcony Old Tock fell at midnight: that suspect is behind it."

    # --- the suspects --------------------------------------------------------
    def knowledge(self, case, sid):
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        facts = [
            f"Your room is the {s['room']}. Its balcony is {s['height']} m above the courtyard; everyone knows. "
            f"If asked, say exactly {s['height']} m.",
            "At midnight Old Tock the clockkeeper fell from the clock tower into the courtyard and did not survive.",
            "You heard a cry, then a thud. You saw a white shape on the tower in the lightning; people say it was the Tower Ghost.",
            f"Gossip you know is true: {o['name']}'s balcony is the {o['room']}, {o['height']} m up.",
            "You never time anything and never give any times.",
            "Hollowmere Manor is glitching because the Rubber Baron erased the law of falling: raindrops hang in the air.",
        ]
        if sid != case.culprit:
            facts.insert(1, "You were in your room at midnight. Old Tock never came out on your balcony.")
            facts.insert(2, "You do not know how Old Tock fell.")
            return facts, ""
        secret = (f"SECRET, never reveal or hint at it: at midnight Old Tock came out on your balcony in the {s['room']}, "
                  f"you argued, and you pushed him. You tell everyone he never came out on your balcony. If anyone "
                  f"accuses you, deny it calmly and stay in character; everything else you say is true.")
        return facts, secret

    def admits(self, case, sid, text):
        """Nobody names a height but their own and the one they know by gossip; nobody owns up to the push."""
        allowed = {self.suspects[sid]["height"], self.suspects[self.gossip[sid]]["height"]}
        if any(float(x) not in allowed for x in METRES.findall(text)):
            return True
        if CONFESS.search(text):
            return True
        return sid == case.culprit and bool(re.search(r"\bmy balcony\b", text, re.I)) and not re.search(WORDS, text, re.I)

    def leak_examples(self, case):
        s = self.suspects[case.culprit]
        return ["Fine. I pushed him off.", "He came out on my balcony at midnight, if you must know.",
                f"He fell {s['t']:g} seconds, I counted."]

    def scripted(self, case, sid, question):
        q = question.lower()
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        if any(k in q for k in ["balcony", "room", "where", "high", "come out"]):
            return f"My balcony's the {s['room']}, {s['height']} m up. He never came out on it."
        if any(k in q for k in ["hear", "cry", "thud", "sound", "midnight"]):
            return "A cry, then a thud. Then only the rain."
        if any(k in q for k in ["ghost", "shape", "see", "saw", "white"]):
            return "A white shape on the tower. The ghost, they say."
        if any(k in q for k in ["who", "think", "gossip", "suspect"]):
            return f"Can't say. {o['name']}'s balcony is the {o['room']}, mind."
        return {"rivet": "Ask, then. Quickly. It's dark.",
                "varnish": "Ask away, darling.",
                "pendle": "Tick... ask. Tock... slowly."}[sid]
