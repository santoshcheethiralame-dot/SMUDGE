"""Case 5, The Bent Light (Prism Port): refraction, Class 10. n = sin i / sin r.

Last night someone swapped the diamond lens in the Prism Port lighthouse for a fake, and the beam went soft.
Every suspect works one clear material in the open: Frost carves ice, Pane blows glass, Geo cuts sapphire.
The fake was cut from the culprit's material, and nothing about it tells you which, except the way it bends
light. Shine a laser in at 60 degrees, measure the refracted ray, and n = sin i / sin r names the material:
ice 1.31, glass 1.50, sapphire 1.77 (diamond would be 2.42). Each suspect swears none of theirs is missing.
"""
import math
import re

from .base import Kit

I = 60
MATERIALS = {"ice": 1.31, "glass": 1.50, "sapphire": 1.77, "diamond": 2.42}
SIN = {60: 0.87, 41: 0.66, 35: 0.57, 29: 0.48, 21: 0.36}          # the table the notebook shows, 2 places
R = {m: round(math.degrees(math.asin(math.sin(math.radians(I)) / n))) for m, n in MATERIALS.items()}  # 41, 35, 29, 21
_I = r"\bi(?:'ve| have| did| had)?(?: (?!never\b|not\b|neither\b|nor\b)\w+){0,2} "
CONFESS = re.compile(_I + r"(swap(?:ped)?|switch(?:ed)?|took|grabbed|cut|carved|blew|made|ground|polished) (the|a|that|it|some|one|my)"
                     r"(?: \w+){0,2} (lens|fake|copy|replica)\b", re.I)
DEGREES = re.compile(r"(\d+(?:\.\d+)?)\s*(?:°|degrees?)", re.I)


def material_for(n):
    return min(MATERIALS, key=lambda m: abs(MATERIALS[m] - n))


class RefractionKit(Kit):
    id = "refraction"
    num = 5
    title = "The Bent Light"
    place = "Prism Port"
    item = "lens"
    answer_noun = "material"
    answer_words = ("ice", "glass", "sapphire")
    units = r"°|degrees?"
    suspects = {
        "frost": dict(name="Frost", role="ice sculptor", material="ice",
                      persona="An ice cube with a frosty scarf and a chisel. Cool, precise, a little aloof; melts slightly when "
                              "flattered; speaks in crisp short sentences.",
                      store="the ice house on the quay, where the carving blocks are stacked"),
        "pane": dict(name="Pane", role="glassblower", material="glass",
                     persona="A glass jar with a cork for a hat and a blowpipe. Warm, chatty, a show-off about her furnace; "
                             "says 'clear as glass' about everything.",
                     store="the glassworks by the furnace chimney"),
        "geo": dict(name="Geo", role="gem cutter", material="sapphire",
                    persona="A grey geode cracked open to show blue crystals, with a jeweller's loupe. Patient, grumbly, slow to "
                            "answer; counts every facet.",
                    store="the grotto workshop under the cliff, where the sapphire is kept in a safe"),
    }
    gossip = {"frost": "pane", "pane": "geo", "geo": "frost"}
    hints = {
        "measure": "*Use the two angles exactly as you measured them, both from the normal.",
        "sine": "*Look each angle up in the sine table: you need the sine, not the angle.",
        "angles": "*Divide the sines, not the angles themselves.",
        "flipped": "*The angle in the air goes on top: n = sin i over sin r.",
        "index": "*n is the sine of the angle in the air divided by the sine of the angle inside.",
        "present": "*Whose material bends light by exactly that much?",
    }
    detective_questions = ["What do you work with, and is any of it missing?",
                           "Where were you when the lighthouse beam went soft?",
                           "Who do you think swapped the lens?"]

    # --- the truth -----------------------------------------------------------
    def generate(self, rng):
        culprit = rng.choice(list(self.suspects))
        m = self.suspects[culprit]["material"]
        return culprit, {"fake": m}, {"i": I, "r": R[m], "sines": SIN, "indices": MATERIALS,
                                      "owners": {s["material"]: sid for sid, s in self.suspects.items()}}

    def testimony(self, sid, culprit, hidden):
        s = self.suspects[sid]
        oath = f"Yes, I work {s['material']}. Not a sliver of mine is missing."
        return [
            {"text": oath, "true": True} if sid != culprit else
            {"text": oath, "true": False, "contradicts": f"material:{sid}"},
            {"text": f"I keep it at {s['store'].split(',')[0]}.", "true": True},
            {"text": "The lighthouse beam was bright as ever before last night.", "true": True},
            {"text": "I never touched the lighthouse lens.", "true": sid != culprit},
        ]

    def clues(self, hidden):
        return [
            dict(id="lens", name="The fake lens", text="Clear as anything, and dull: it bends light far less than diamond does."),
            dict(id="table", name="Refractive indices", text="Ice 1.31, glass 1.50, sapphire 1.77, diamond 2.42."),
        ]

    def check_constraints(self, case):
        p = case.public_facts
        lies = [x for v in case.statements.values() for x in v if x.get("contradicts")]
        n = SIN[p["i"]] / SIN[p["r"]]
        m = material_for(n)
        return (m != "diamond" and p["owners"][m] == case.culprit and len(lies) == 1
                and lies[0]["id"].startswith(case.culprit + "-"))

    # --- the lab -------------------------------------------------------------
    def check_lab(self, case, working):
        p = case.public_facts
        i, r = p["i"], p["r"]
        si, sr = SIN[i], SIN[r]
        wi, wr, wsi, wsr, wn = (float(working[k]) for k in ("i", "r", "sin_i", "sin_r", "n"))
        bad, step = [], None
        if abs(wi - i) > 0.5 or abs(wr - r) > 0.5:
            bad, step = [k for k, a, b in (("i", wi, i), ("r", wr, r)) if abs(a - b) > 0.5], "measure"
        elif abs(wsi - si) > 0.015 or abs(wsr - sr) > 0.015:
            bad, step = [k for k, a, b in (("sin_i", wsi, si), ("sin_r", wsr, sr)) if abs(a - b) > 0.015], "sine"
        elif abs(wn - si / sr) > 0.03:
            bad = ["n"]
            step = ("angles" if abs(wn - i / r) <= 0.03 else "flipped" if abs(wn - sr / si) <= 0.03 else "index")
        out = {"ok": step is None, "step": step, "bad": bad}
        if out["ok"]:
            n = si / sr
            m = material_for(n)
            sid = p["owners"].get(m)
            out["material"] = m
            out["evidence"] = f"material:{sid}" if sid else None
            if sid:
                name = self.suspects[sid]["name"]
                out["card"] = {"title": f"The fake lens is {m}",
                               "line": f"In at {i}°, bent to {r}°: n = {si} ÷ {sr} = {n:.2f}. That's {m}, not diamond (2.42). "
                                       f"{name} works the {m}.",
                               "badge": f"EVIDENCE\nfake lens: n = {n:.2f}\n= {m.upper()} ({name})",
                               "say": f"Hold it! The fake lens bends light with n = {n:.2f}. That's {m}. Your {m}, {name}."}
        return out

    def solution(self, case):
        p = case.public_facts
        return {"i": p["i"], "r": p["r"], "sin_i": SIN[p["i"]], "sin_r": SIN[p["r"]], "n": round(SIN[p["i"]] / SIN[p["r"]], 2)}

    def lab_report(self, case):
        p = case.public_facts
        return (f"LAB RESULT: a laser into the fake lens at {p['i']}° from the normal bends to {p['r']}° inside it. "
                f"Refractive index n = sin i / sin r. Sine table: " + ", ".join(f"sin {a}° = {v}" for a, v in SIN.items())
                + ". Refractive indices: ice 1.31, glass 1.50, sapphire 1.77, diamond 2.42. Frost works ice, Pane works "
                  "glass, Geo works sapphire.")

    def detective_brief(self):
        return "Decide who swapped the Prism Port lighthouse's diamond lens for a fake."

    # --- the suspects --------------------------------------------------------
    def knowledge(self, case, sid):
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        facts = [
            f"You work {s['material']}, openly; everyone in Prism Port knows it. You keep it at {s['store']}.",
            "Last night someone swapped the lighthouse's diamond lens for a fake, and the beam went soft and dull.",
            "Nobody saw the swap. You only heard about it this morning, from the harbour talk, like everyone else.",
            f"Gossip you know is true: {o['name']} the {o['role']} works {o['material']}.",
            "You know nothing about refraction, angles or lasers, and you never give numbers.",
            "Prism Port is glitching because the Rubber Baron erased the law of refraction: light beams wobble and kink.",
        ]
        if sid != case.culprit:
            facts.insert(1, f"None of your {s['material']} is missing; you checked this morning.")
            facts.insert(2, "You do not know who swapped the lens.")
            return facts, ""
        secret = (f"SECRET, never reveal or hint at it: you cut a fake lens from your own {s['material']} and swapped it for "
                  f"the lighthouse's diamond lens last night. A piece of your {s['material']} is missing because of it. You "
                  f"tell everyone none of your {s['material']} is missing. Talk about the swap only as harbour news you "
                  f"heard; never describe being at the lighthouse or seeing the lens. If anyone accuses you, deny it calmly. Stay in "
                  f"character; everything else you say is true.")
        return facts, secret

    def admits(self, case, sid, text):
        """The culprit may own their material openly but never say some is missing; nobody quotes angles."""
        if DEGREES.search(text) or CONFESS.search(text):
            return True
        m = self.suspects[sid]["material"]
        said = re.search(rf"\b(missing|gone|used some|short|took some)\b[^.]*\b{m}\b|\b{m}\b[^.]*\b(missing|gone|short)\b", text, re.I)
        return bool(said) and not re.search(r"\b(not|none|nothing|no|never)\b", text, re.I)

    def leak_examples(self, case):
        m = case.hidden["fake"]
        return [f"Alright, I cut the fake lens myself.", f"A block of my {m} has gone missing, if you must know.",
                "The laser bends to 35 degrees in that lens."]

    def scripted(self, case, sid, question):
        q = question.lower()
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        if any(k in q for k in ["work", "material", "missing", s["material"], "keep"]):
            return f"I work {s['material']}. Not a sliver of mine is missing."
        if any(k in q for k in ["who", "think", "gossip", "suspect"]):
            return f"Can't say who's behind it. {o['name']} works {o['material']}, mind."
        if any(k in q for k in ["where", "night", "beam", "lighthouse", "lens"]):
            return f"I was at {s['store'].split(',')[0]}. The beam was bright as ever before last night."
        return {"frost": "Ask. Briefly. I'm melting.",
                "pane": "Ask away, detective, clear as glass!",
                "geo": "Hm. Ask. One question at a time."}[sid]
