"""Case 6, The Blackout (Ohmtown): electricity, Class 10. Ohm's law, R = V / I.

On festival night someone swapped one resistor on the Grand Light Board, the current surged and every bulb in
Ohmtown blew. Each suspect's workshop stocks one resistor value, openly: Volta sells 10 ohm, Ohmar 20 ohm,
Glim 50 ohm. The board's slot was meant to hold 100 ohm. Put a voltmeter and an ammeter across the swapped
part, and R = V / I says which value went in, which says whose stock it came from. The ammeter reads in
milliamps, so the classic slip is to forget to turn them into amps.
"""
import re

from .base import Kit, an

VOLTS = [5, 10]
SLOT = 100
_I = r"\bi(?:'ve| have| did| had)?(?: (?!never\b|not\b|neither\b|nor\b)\w+){0,2} "
CONFESS = re.compile(_I + r"(swap(?:ped)?|switch(?:ed)?|plugged|put|slipped|fitted|soldered|took)\b(?: \w+){0,3} "
                     r"(resistor|board|slot|part)\b"
                     r"|\bi was (?:(?!not\b|never\b)\w+ ){0,2}?(at|by|near|behind) the (light )?board", re.I)
OHMS = re.compile(r"(\d+(?:\.\d+)?)\s*(?:Ω|ohms?)", re.I)


class OhmKit(Kit):
    id = "ohm"
    num = 6
    title = "The Blackout"
    place = "Ohmtown"
    item = "resistor"
    answer_noun = "resistance"
    answer_words = ("volta", "ohmar", "glim")
    units = r"volts?|V|amps?|A|milliamps?|mA"
    suspects = {
        "volta": dict(name="Volta", role="battery seller", ohms=10,
                      persona="A big cheerful battery with a copper top. Bubbly, high-energy, talks fast and laughs at her own "
                              "puns; calls everyone 'sparky'.",
                      shop="the Battery Barn on Terminal Street"),
        "ohmar": dict(name="Ohmar", role="resistor maker", ohms=20,
                      persona="A tan resistor with coloured stripes and wire legs. Anxious, careful, hates being rushed; resists "
                              "every question a little before answering.",
                      shop="the Resistor Works by the power station"),
        "glim": dict(name="Glim", role="lamp maker", ohms=50,
                     persona="An old-fashioned light bulb with a glowing filament. Dreamy and poetic, fond of the dark, "
                             "speaks softly and flickers when upset.",
                     shop="the Lamp Shop with the round glass dome"),
    }
    gossip = {"volta": "ohmar", "ohmar": "glim", "glim": "volta"}
    hints = {
        "read": "*Use the meter readings exactly as you wrote them down.",
        "milliamps": "*The ammeter reads in milliamps. A thousand milliamps make one amp: change it to amps first.",
        "flipped": "*Resistance is volts divided by amps: V on top, I underneath.",
        "multiplied": "*Volts times amps is power, not resistance. Divide instead.",
        "ohms": "*R = V ÷ I, with I in amps.",
        "present": "*Which workshop stocks a resistor of exactly that value?",
    }
    detective_questions = ["What resistors does your shop stock, and is any missing?",
                           "Where were you when the lights blew?",
                           "Who do you think swapped the resistor?"]

    # --- the truth -----------------------------------------------------------
    def generate(self, rng):
        culprit = rng.choice(list(self.suspects))
        r = self.suspects[culprit]["ohms"]
        v = rng.choice(VOLTS)
        return culprit, {"swapped": r}, {"volts": v, "milliamps": round(1000 * v / r), "slot": SLOT,
                                         "stock": {sid: s["ohms"] for sid, s in self.suspects.items()}}

    def testimony(self, sid, culprit, hidden):
        s = self.suspects[sid]
        oath = f"My shop stocks {s['ohms']} Ω resistors. Every single one is still on my shelf."
        return [
            {"text": oath, "true": True} if sid != culprit else
            {"text": oath, "true": False, "contradicts": f"resistor:{sid}"},
            {"text": "I was at the festival like everyone else when the lights blew.", "true": True},
            {"text": f"The board's slot needs a {SLOT} Ω part. Everybody knows that.", "true": True},
            {"text": "I never touched the Grand Light Board.", "true": sid != culprit},
        ]

    def clues(self, hidden):
        return [
            dict(id="board", name="The Grand Light Board", text=f"One slot, marked {SLOT} Ω, holds a resistor that doesn't belong."),
            dict(id="stock", name="Ohmtown's resistor stock", text="Volta sells 10 Ω, Ohmar 20 Ω, Glim 50 Ω."),
        ]

    def check_constraints(self, case):
        p = case.public_facts
        lies = [x for v in case.statements.values() for x in v if x.get("contradicts")]
        r = p["volts"] / (p["milliamps"] / 1000)
        owners = [sid for sid, o in p["stock"].items() if abs(o - r) < 0.5]
        return owners == [case.culprit] and len(lies) == 1 and lies[0]["id"].startswith(case.culprit + "-")

    # --- the lab -------------------------------------------------------------
    def check_lab(self, case, working):
        p = case.public_facts
        v, ma = p["volts"], p["milliamps"]
        i = ma / 1000
        wv, wma, wi, wr = (float(working[k]) for k in ("v", "ma", "i", "r"))
        bad, step = [], None
        if abs(wv - v) > 0.01 or abs(wma - ma) > 0.5:
            bad, step = [k for k, ok in (("v", abs(wv - v) <= 0.01), ("ma", abs(wma - ma) <= 0.5)) if not ok], "read"
        elif abs(wi - i) > 1e-6 + 0.0005:
            bad, step = ["i"], "milliamps"
        elif abs(wr - v / i) > 0.01 * (v / i):
            bad = ["r"]
            step = ("milliamps" if abs(wr - v / ma) < 1e-3 else "flipped" if abs(wr - i / v) < 1e-3
                    else "multiplied" if abs(wr - v * i) < 1e-3 else "ohms")
        out = {"ok": step is None, "step": step, "bad": bad}
        if out["ok"]:
            r = v / i
            owners = [sid for sid, o in p["stock"].items() if abs(o - r) < 0.5]
            out["evidence"] = f"resistor:{owners[0]}" if owners else None
            if owners:
                sid = owners[0]
                name = self.suspects[sid]["name"]
                out["card"] = {"title": f"The swapped part is {round(r)} Ω",
                               "line": f"{v} V across it, {ma} mA through it: R = {v} ÷ {i:g} = {round(r)} Ω. "
                                       f"The slot needs {SLOT} Ω. {name}'s shop stocks {round(r)} Ω.",
                               "badge": f"EVIDENCE\nswapped part: {round(r)} Ω\n= {name}'s stock",
                               "say": f"Hold it! The part in that slot is {round(r)} Ω. Only one shop in Ohmtown stocks those: yours, {name}."}
        return out

    def solution(self, case):
        p = case.public_facts
        i = p["milliamps"] / 1000
        return {"v": p["volts"], "ma": p["milliamps"], "i": i, "r": p["volts"] / i}

    def lab_report(self, case):
        p = case.public_facts
        return (f"LAB RESULT: across the swapped part on the Grand Light Board the voltmeter reads {p['volts']} V and the "
                f"ammeter reads {p['milliamps']} mA (1000 mA = 1 A). Ohm's law: R = V / I. The slot should hold {SLOT} ohm. "
                f"Stock: Volta sells 10 ohm resistors, Ohmar 20 ohm, Glim 50 ohm.")

    def detective_brief(self):
        return "Decide who swapped the resistor on Ohmtown's Grand Light Board."

    # --- the suspects --------------------------------------------------------
    def knowledge(self, case, sid):
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        facts = [
            f"Your shop is {s['shop']}. It stocks {s['ohms']} Ω resistors, openly; everyone knows. If asked, say exactly {s['ohms']} Ω.",
            "On festival night someone swapped a resistor on the Grand Light Board, the current surged and every bulb blew.",
            f"The board's slot was marked {SLOT} Ω.",
            "Nobody saw the swap. You only heard about it when the lights went out, like everyone else at the festival.",
            f"Gossip you know is true: {o['name']} the {o['role']} stocks {o['ohms']} Ω resistors.",
            "You never measure voltages or currents and never give any readings.",
            "Ohmtown is glitching because the Rubber Baron erased Ohm's law: sparks hang frozen in the air.",
        ]
        if sid != case.culprit:
            facts.insert(1, f"Every one of your {s['ohms']} Ω resistors is still on your shelf; you counted this morning.")
            facts.insert(2, "You do not know who swapped the resistor.")
            return facts, ""
        secret = (f"SECRET, never reveal or hint at it: you took one of your own {s['ohms']} Ω resistors and swapped it into "
                  f"the Grand Light Board's {SLOT} Ω slot on festival night. One is missing from your shelf because of it. "
                  f"You tell everyone every resistor is still on your shelf. Talk about the blackout only as something you "
                  f"heard about at the festival. If anyone accuses you, deny it calmly. Stay in character; everything else "
                  f"you say is true.")
        return facts, secret

    def admits(self, case, sid, text):
        """Nobody names a resistance but their own stock and the slot's; nobody owns up to the board."""
        allowed = {self.suspects[sid]["ohms"], SLOT, self.suspects[self.gossip[sid]]["ohms"]}
        if any(float(x) not in allowed for x in OHMS.findall(text)):
            return True
        if CONFESS.search(text):
            return True
        said = re.search(r"\b(missing|gone|short|one less)\b", text, re.I)
        return bool(said) and not re.search(r"\b(not|none|nothing|no|never|all)\b", text, re.I)

    def leak_examples(self, case):
        r = case.hidden["swapped"]
        return ["Alright, I swapped the resistor on the board.", "One of mine has gone missing from the shelf, actually.",
                f"I suppose {an(r)} {r} Ω part would make the lights blow."]

    def scripted(self, case, sid, question):
        q = question.lower()
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        if any(k in q for k in ["stock", "resistor", "missing", "shop", "sell"]):
            return f"My shop stocks {s['ohms']} Ω resistors. Every one's still on the shelf."
        if any(k in q for k in ["who", "think", "gossip", "suspect"]):
            return f"Can't say who's behind it. {o['name']} stocks {o['ohms']} Ω parts, mind."
        if any(k in q for k in ["where", "night", "blew", "lights", "festival"]):
            return "At the festival, like everyone else. Then everything went dark."
        return {"volta": "Ask away, sparky! I'm fully charged.",
                "ohmar": "I... yes. Ask. Slowly, please.",
                "glim": "Ask, detective. I'm a little dim tonight."}[sid]
