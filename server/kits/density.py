"""Case 1, The Forged Crown (Buoyant Bay): density and Archimedes, Class 9.

Each suspect has access to one metal. The fake crown is cast from the culprit's
metal, and the only way to learn which metal is to measure the crown's density.
Every suspect openly owns their metal and swears none is missing; only the
culprit's oath is false, and only the lab can show which one.
"""
import re

from .base import Kit

GOLD = 19.3
METALS = {"lead": 11.3, "silver": 10.5, "copper": 8.96, "brass": 8.5}


def metal_for(density):
    """The table metal nearest a measured density (and how near)."""
    name, rho = min({"gold": GOLD, **METALS}.items(), key=lambda kv: abs(kv[1] - density))
    return name, abs(rho - density)


class DensityKit(Kit):
    id = "density"
    num = 1
    title = "The Forged Crown"
    place = "Buoyant Bay"
    item = "crown"
    answer_noun = "metal"
    answer_words = tuple(METALS)
    units = r"g|grams?|ml|millilit\w*|cm|g/cm"
    suspects = {
        "karat": dict(name="Karat", role="royal jeweller", metal="silver",
                      persona="A smug, sparkly diamond. Speaks in polished, slightly condescending sentences. Loves the word 'exquisite'.",
                      where_metal="his workshop drawer of silver offcuts from making rings",
                      custody="polished the crown at dawn in the workshop"),
        "cyl": dict(name="Cyl", role="harbour master", metal="lead",
                    persona="A tall, grumpy measuring cylinder. Short sentences, harbour slang, proud of his tidy scales.",
                    where_metal="the box of lead weights he uses to check the harbour scales",
                    custody="locked the crown in the lighthouse vault at noon"),
        "bob": dict(name="Bob", role="buoy and part-time fisherman", metal="brass",
                    persona="A cheerful, bobbing red-and-white buoy. Rambles, jokes, loves gossip and his brass bell.",
                    where_metal="the brass bell and spare brass fittings on his boat",
                    custody="carried the crown to the festival stage at sunset"),
    }
    gossip = {"karat": "bob", "cyl": "karat", "bob": "cyl"}
    hints = {
        "mass": "*Psst. The balance tells you the mass. Read the number it settles on, in grams.",
        "volume": "*Footnote: volume is how much the water ROSE, not where it ended up. After minus before.",
        "used_total_level": "*You wrote the final water level. What was it before the crown went in? Subtract!",
        "density": "*Density is mass divided by volume. Grams over cm³. Careful with the division.",
        "metal": "*Now compare your density with the table. Which metal is closest? Is it gold?",
        "present": "*Find the statement that your density result makes impossible.",
    }
    detective_questions = ["Where were you today and what did you do with the crown?",
                           "What metals do you keep, and is any missing?",
                           "Who do you think did it?"]

    # --- the truth -----------------------------------------------------------
    def generate(self, rng):
        culprit = rng.choice(list(self.suspects))
        fake = self.suspects[culprit]["metal"]
        volume = rng.randint(12, 20)
        mass = round(METALS[fake] * volume)
        before = rng.choice([40, 50, 60])
        return culprit, {"fake_metal": fake, "density": round(mass / volume, 2)}, \
            {"volume_ml": volume, "mass_g": mass, "water_before_ml": before}

    def testimony(self, sid, culprit, hidden):
        s = self.suspects[sid]
        oath = f"Yes, I keep {s['metal']}, everyone knows that. And every last gram of it is accounted for."
        lines = [
            {"text": f"I {s['custody']}. Ask anyone.", "true": True},
            {"text": "When I had the crown, it looked as golden as ever.", "true": True},
            {"text": oath, "true": True} if sid != culprit else
            {"text": oath, "true": False, "contradicts": f"density:{hidden['fake_metal']}"},
            {"text": "Whoever swapped that crown, it wasn't me.", "true": sid != culprit},
        ]
        return lines

    def clues(self, hidden):
        return [
            dict(id="crown", name="The Harbour Crown", text="Looks like gold. Feels a little light for its size?"),
            dict(id="metals", name="Density table", text="gold 19.3 · lead 11.3 · silver 10.5 · copper 8.96 · brass 8.5 (g/cm³)"),
        ]

    def check_constraints(self, case):
        """Exactly one suspect owns the fake's metal, and that suspect's lie is the only false statement about metals."""
        fake = case.hidden["fake_metal"]
        owners = [s for s, v in self.suspects.items() if v["metal"] == fake]
        lies = [x for v in case.statements.values() for x in v if x.get("contradicts")]
        measured, err = metal_for(case.public_facts["mass_g"] / case.public_facts["volume_ml"])
        return (len(owners) == 1 and owners[0] == case.culprit and len(lies) == 1
                and lies[0]["id"].startswith(case.culprit) and measured == fake and err < 0.3)

    # --- the lab -------------------------------------------------------------
    def check_lab(self, case, working):
        p = case.public_facts
        mass, before, after, density = (float(working[k]) for k in ("mass", "before", "after", "density"))
        out = {"mass_ok": abs(mass - p["mass_g"]) < 0.6,
               "volume_ok": abs((after - before) - p["volume_ml"]) < 0.6,
               "used_total_level": abs(after - p["water_before_ml"] - p["volume_ml"]) < 0.6 and abs(after - before - p["volume_ml"]) > 0.6}
        out["density_ok"] = out["mass_ok"] and out["volume_ok"] and abs(density - p["mass_g"] / p["volume_ml"]) < 0.15
        if out["density_ok"]:
            out["metal"], _ = metal_for(p["mass_g"] / p["volume_ml"])
            out["evidence"] = f"density:{out['metal']}"
            d, m = round(p["mass_g"] / p["volume_ml"], 2), out["metal"]
            out["card"] = {"title": f"Crown density: {d} g/cm³", "line": f"That's {m.upper()}. Gold would be 19.3.",
                           "badge": f"EVIDENCE\ncrown = {d} g/cm³\n= {m.upper()}", "say": f"Hold it. The crown's density is {d}. That's {m}."}
        out["ok"] = out["density_ok"]
        out["step"] = ("mass" if not out["mass_ok"] else "used_total_level" if out["used_total_level"]
                       else "volume" if not out["volume_ok"] else "density" if not out["density_ok"] else None)
        return out

    def solution(self, case):
        p = case.public_facts
        return {"mass": p["mass_g"], "before": p["water_before_ml"], "after": p["water_before_ml"] + p["volume_ml"],
                "density": round(p["mass_g"] / p["volume_ml"], 2)}

    def lab_report(self, case):
        p = case.public_facts
        return (f"LAB RESULT: crown mass {p['mass_g']} g, displaced {p['volume_ml']} ml of water. "
                f"Density table g/cm3: gold 19.3, lead 11.3, silver 10.5, copper 8.96, brass 8.5.")

    def detective_brief(self):
        return "Decide who swapped the gold crown for a fake."

    # --- the suspects --------------------------------------------------------
    def knowledge(self, case, sid):
        s = self.suspects[sid]
        o = self.suspects[self.gossip[sid]]
        facts = [
            f"You {s['custody']}.",
            "When you had the crown it looked golden to you.",
            f"Gossip you know is true: {o['name']} the {o['role']} keeps {o['metal']} in {o['where_metal']}.",
            "You do not know the crown's mass, volume or density.",
            "Buoyant Bay is slowly sinking because the Rubber Baron erased the law of density. Boats are taking on water.",
        ]
        facts.insert(1, f"You keep {s['metal']} in {s['where_metal']}. Everyone in town knows that, and you say so freely.")
        if sid != case.culprit:
            facts.insert(2, "None of your metal is missing.")
            facts.insert(3, "You do not know who swapped the crown.")
            return facts, ""
        secret = (f"SECRET, never reveal or hint at it: while you {s['custody']}, you swapped the real gold crown for a fake "
                  f"cast from some of your own {s['metal']}. You openly admit you keep {s['metal']}, like everyone does, "
                  f"but you insist none of it is missing. If anyone accuses you, deny it calmly: you did not swap, make, cast or touch "
                  f"any fake. Stay charming and vary your wording; everything else you say is true.")
        return facts, secret

    def admits(self, case, sid, text):
        """The culprit may own their metal openly, but must never admit some is missing."""
        m = self.suspects[sid]["metal"]
        said = re.search(rf"\b(missing|gone|used some|melted|short)\b[^.]*\b{m}\b|\b{m}\b[^.]*\b(missing|gone|short)\b", text, re.I)
        return bool(said) and not re.search(r"\b(not|none|nothing|no|never)\b", text, re.I)

    def leak_examples(self, case):
        m = case.hidden["fake_metal"]
        return [f"Fine. I swapped it at work and nobody noticed.", f"Some of my {m} has gone missing lately, if you must know.",
                "The crown weighs 158 g, I checked it myself."]

    def scripted(self, case, sid, question):
        q = question.lower()
        s, m = self.suspects[sid], self.suspects[sid]["metal"]
        if any(k in q for k in [m, "metal", "weights", "bell", "offcut"]):
            return f"Of course I keep {m}. Every last gram of it is accounted for."
        if any(k in q for k in ["where", "when", "crown", "today"]):
            return f"I {s['custody']}. It looked as golden as ever."
        if any(k in q for k in ["who", "suspect", "think", "gossip"]):
            o = self.suspects[self.gossip[sid]]
            return f"Can't say who's behind it. But {o['name']} keeps {o['metal']} in {o['where_metal']}. Just saying."
        return {"karat": "Exquisite question. Ask me about the crown, I polished it myself.",
                "cyl": "Busy day. Boats sinking. Ask what you need.",
                "bob": "Ha! Ask me anything, I hear everything bobbing about the harbour."}[sid]
