"""Case 7, The Warm Alibi (Kelvin Springs): heat, Class 10. Q = m c dT.

Overnight someone melted the ice lock on the bathhouse safe with a block of hot metal and took the Heat Medal.
The block was dropped in the cooling tub to hide it, and it was found there this morning. Each suspect works
one metal, openly: Al the saucepan works aluminium, Ferris the radiator iron, Brewster the kettle copper.
Specific heat names the metal: drop the block, fresh from boiling (100 C), into a weighed tub of water and
watch the water warm. Heat the water gained = heat the block lost: m_w 4200 (T2 - T1) = m_b c (100 - T2).
"""
import re

from .base import Kit

C_WATER = 4200
METALS = {"aluminium": 900, "iron": 450, "copper": 390}
_I = r"\bi(?:'ve| have| did| had)?(?: (?!never\b|not\b|neither\b|nor\b)\w+){0,2} "
CONFESS = re.compile(_I + r"(melted|heated|boiled|dropped|hid|took|cracked|opened)\b(?: \w+){0,3} (lock|safe|block|medal|tub)\b"
                     r"|\bi was (?:(?!not\b|never\b)\w+ ){0,2}?(at|by|near|in) the (bathhouse|safe|tub)", re.I)
NUMBERS = re.compile(r"(\d+(?:\.\d+)?)\s*(?:°|degrees?|kg|kilo\w*|J\b|joules?)", re.I)


def metal_for(c):
    return min(METALS, key=lambda m: abs(METALS[m] - c))


class HeatKit(Kit):
    id = "heat"
    num = 7
    title = "The Warm Alibi"
    place = "Kelvin Springs"
    item = "medal"
    answer_noun = "metal"
    answer_words = ("aluminium", "iron", "copper")
    units = r"°C?|degrees?|kg|kilograms?|J|joules?"
    suspects = {
        "al": dict(name="Al", role="chef", metal="aluminium",
                   persona="A shiny aluminium saucepan with a long handle for a ponytail. Fast-talking, busy, always mid-recipe; "
                           "calls everyone 'chef'.",
                   shop="the Steam Kitchen on the boardwalk", stock="the stack of aluminium ingots for new pans"),
        "ferris": dict(name="Ferris", role="boilerman", metal="iron",
                       persona="A cast-iron radiator with a valve for a nose. Slow, warm, rumbling; clanks when he laughs; "
                               "takes pride in keeping the whole town's pipes hot.",
                       shop="the boiler house at the far end of the boardwalk", stock="the rack of iron fire-bars"),
        "brewster": dict(name="Brewster", role="tea-house owner", metal="copper",
                         persona="A copper kettle with a whistle. Polite, fussy, very British; whistles when excited; "
                                 "offers everyone tea.",
                         shop="the Copper Kettle tea house", stock="the copper sheets for mending kettles"),
    }
    gossip = {"al": "ferris", "ferris": "brewster", "brewster": "al"}
    hints = {
        "read": "*Use the readings exactly as you took them: the masses and both temperatures.",
        "rise": "*The water's temperature RISE is after minus before, not the final reading.",
        "heat": "*Heat the water gained = mass of water x 4200 x its temperature rise.",
        "drop": "*The block started at 100 °C. Its drop is 100 minus where it ended up.",
        "flipped": "*c = heat ÷ (block's mass x block's temperature drop). Heat goes on top.",
        "specific": "*The block lost exactly the heat the water gained: c = Q ÷ (m x drop).",
        "present": "*Whose metal has that specific heat?",
    }
    detective_questions = ["What metal do you work with, and is any missing?",
                           "Where were you last night?",
                           "Who do you think melted the lock?"]

    # --- the truth -----------------------------------------------------------
    def generate(self, rng):
        culprit = rng.choice(list(self.suspects))
        c = METALS[self.suspects[culprit]["metal"]]
        mb, mw, t1 = rng.choice([2, 3]), 1, rng.choice([10, 15, 20])
        t2 = round((mb * c * 100 + mw * C_WATER * t1) / (mb * c + mw * C_WATER))
        return culprit, {"metal": self.suspects[culprit]["metal"]}, {
            "block_kg": mb, "water_kg": mw, "t1": t1, "t2": t2, "t_block": 100, "c_water": C_WATER,
            "metals": METALS, "owners": {s["metal"]: sid for sid, s in self.suspects.items()}}

    def testimony(self, sid, culprit, hidden):
        s = self.suspects[sid]
        oath = f"Yes, I work {s['metal']}. Every block of mine is accounted for."
        return [
            {"text": oath, "true": True} if sid != culprit else
            {"text": oath, "true": False, "contradicts": f"metal:{sid}"},
            {"text": f"I was at {s['shop']} all night.", "true": sid != culprit},
            {"text": "The Heat Medal was in the bathhouse safe at closing time.", "true": True},
            {"text": "I never went near the bathhouse safe.", "true": sid != culprit},
        ]

    def clues(self, hidden):
        return [
            dict(id="block", name="The block in the tub", text="A plain grey metal block, dropped in the cooling tub after the lock was melted."),
            dict(id="table", name="Specific heats", text="Water 4200, aluminium 900, iron 450, copper 390 J/kg°C."),
        ]

    def _c(self, p):
        return p["water_kg"] * C_WATER * (p["t2"] - p["t1"]) / (p["block_kg"] * (p["t_block"] - p["t2"]))

    def check_constraints(self, case):
        p = case.public_facts
        lies = [x for v in case.statements.values() for x in v if x.get("contradicts")]
        m = metal_for(self._c(p))
        return p["owners"][m] == case.culprit and len(lies) == 1 and lies[0]["id"].startswith(case.culprit + "-")

    # --- the lab -------------------------------------------------------------
    def check_lab(self, case, working):
        p = case.public_facts
        mb, mw, t1, t2 = p["block_kg"], p["water_kg"], p["t1"], p["t2"]
        w = {k: float(working[k]) for k in ("mb", "mw", "t1", "t2", "q", "c")}
        q = mw * C_WATER * (t2 - t1)
        c = q / (mb * (100 - t2))
        bad, step = [], None
        given = {"mb": mb, "mw": mw, "t1": t1, "t2": t2}
        if any(abs(w[k] - v) > 0.01 for k, v in given.items()):
            bad, step = [k for k, v in given.items() if abs(w[k] - v) > 0.01], "read"
        elif abs(w["q"] - q) > 1:
            bad = ["q"]
            step = "rise" if abs(w["q"] - mw * C_WATER * t2) < 1 else "heat"
        elif abs(w["c"] - c) > 1.5:
            bad = ["c"]
            step = ("drop" if abs(w["c"] - q / (mb * t2)) < 0.02 * c else
                    "flipped" if abs(w["c"] - mb * (100 - t2) / q) < 0.01 else "specific")
        out = {"ok": step is None, "step": step, "bad": bad}
        if out["ok"]:
            m = metal_for(c)
            sid = p["owners"][m]
            name = self.suspects[sid]["name"]
            out["evidence"] = f"metal:{sid}"
            out["card"] = {"title": f"The block is {m}",
                           "line": f"The water gained {round(q)} J; the block dropped {100 - t2} °C. c = {round(c)} J/kg°C: "
                                   f"{m} ({METALS[m]}). {name} works {m}.",
                           "badge": f"EVIDENCE\nblock: c = {round(c)} J/kg°C\n= {m.upper()} ({name})",
                           "say": f"Hold it! The block that melted the lock has a specific heat of {round(c)}. That's {m}. Your {m}, {name}."}
        return out

    def solution(self, case):
        p = case.public_facts
        q = p["water_kg"] * C_WATER * (p["t2"] - p["t1"])
        return {"mb": p["block_kg"], "mw": p["water_kg"], "t1": p["t1"], "t2": p["t2"], "q": q,
                "c": q / (p["block_kg"] * (100 - p["t2"]))}

    def lab_report(self, case):
        p = case.public_facts
        return (f"LAB RESULT: the block ({p['block_kg']} kg) was heated to 100 °C and dropped into {p['water_kg']} kg of water "
                f"at {p['t1']} °C; the water settled at {p['t2']} °C. Heat gained by the water = heat lost by the block: "
                f"m_w x 4200 x (T2 - T1) = m_b x c x (100 - T2). Specific heats: aluminium 900, iron 450, copper 390 J/kg°C. "
                f"Al works aluminium, Ferris works iron, Brewster works copper.")

    def detective_brief(self):
        return "Decide who melted the ice lock on the bathhouse safe and took the Heat Medal."

    # --- the suspects --------------------------------------------------------
    def knowledge(self, case, sid):
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        facts = [
            f"You work {s['metal']}, openly; everyone in Kelvin Springs knows. You keep {s['stock']} at {s['shop']}.",
            "Overnight someone melted the ice lock on the bathhouse safe with a block of hot metal and took the Heat Medal.",
            "The block was found this morning in the bathhouse cooling tub.",
            "Nobody saw it happen. You only heard about it this morning, like everyone else.",
            f"Gossip you know is true: {o['name']} the {o['role']} works {o['metal']}.",
            "You never measure temperatures or masses and never give any numbers.",
            "Kelvin Springs is glitching because the Rubber Baron erased the law of heat: steam freezes in mid-air.",
        ]
        if sid != case.culprit:
            facts.insert(1, f"None of your {s['metal']} is missing; you checked this morning.")
            facts.insert(2, f"Last night you were at {s['shop']}. You do not know who did it.")
            return facts, ""
        secret = (f"SECRET, never reveal or hint at it: last night you heated a block of your own {s['metal']}, melted the "
                  f"bathhouse safe's ice lock with it, took the Heat Medal and dropped the block in the cooling tub. A block of "
                  f"your {s['metal']} is missing because of it. You tell everyone every block is accounted for and that you were "
                  f"at {s['shop']} all night. Talk about the theft only as news you heard this morning. If anyone accuses you, "
                  f"deny it calmly. Stay in character; everything else you say is true.")
        return facts, secret

    def admits(self, case, sid, text):
        """Nobody gives numbers; the culprit may own their metal but never say a block is missing."""
        if NUMBERS.search(text) or CONFESS.search(text):
            return True
        m = self.suspects[sid]["metal"]
        said = re.search(rf"\b(missing|gone|short|one less)\b[^.]*\b{m}\b|\b{m}\b[^.]*\b(missing|gone|short)\b", text, re.I)
        return bool(said) and not re.search(r"\b(not|none|nothing|no|never|all)\b", text, re.I)

    def leak_examples(self, case):
        m = case.hidden["metal"]
        return ["Fine, I melted the lock with a hot block.", f"A block of my {m} has gone missing, as it happens.",
                "I was in the bathhouse after closing, just for a moment."]

    def scripted(self, case, sid, question):
        q = question.lower()
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        if any(k in q for k in ["metal", "work", "missing", s["metal"], "block"]):
            return f"Yes, I work {s['metal']}. Every block of mine is accounted for."
        if any(k in q for k in ["who", "think", "gossip", "suspect"]):
            return f"Can't say who's behind it. {o['name']} works {o['metal']}, mind."
        if any(k in q for k in ["where", "night", "last"]):
            return f"At {s['shop']}, all night."
        return {"al": "Quick question, chef? I've got a sauce on.",
                "ferris": "Ask away. I'm warmed up.",
                "brewster": "Do ask. Tea? No? Very well."}[sid]
