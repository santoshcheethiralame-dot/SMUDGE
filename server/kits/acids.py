"""Case 8, The Colour Swap (Acid Alley): acids, bases and pH, Class 10.

The Mayor's fountain is kept at pH 7 with a dash of universal indicator, so it glows green. Last night someone
emptied a 10-litre can of their product into it; the water turned, and the koi with it. Each suspect sells
one product, openly: Citrine's lemon cordial (pH 2), Bicarb's baking soda (pH 9), Sudsy's soap flakes (pH 11).
Test the fountain and every product with indicator. The fountain now holds 100 litres, so the can was diluted
ten times, and every tenfold dilution moves pH one step toward 7. Undo that step and one product matches.
"""
import math
import re

from .base import Kit

POURED, TOTAL = 10, 100
_I = r"\bi(?:'ve| have| did| had)?(?: (?!never\b|not\b|neither\b|nor\b)\w+){0,2} "
CONFESS = re.compile(_I + r"(poured|tipped|dumped|emptied|spiked|added|put)\b(?: \w+){0,4} (fountain|water|pond|pool)\b"
                     r"|\bi was (?:(?!not\b|never\b)\w+ ){0,2}?(at|by|near) the fountain", re.I)
NUMBERS = re.compile(r"\b(?:pH\s*\d+(?:\.\d+)?|\d+(?:\.\d+)?\s*(?:litres?|liters?|L\b))", re.I)


def fountain_ph(product_ph):
    """A tenfold dilution moves pH one step toward 7."""
    shift = math.log10(TOTAL / POURED)
    return product_ph + shift if product_ph < 7 else product_ph - shift


class AcidsKit(Kit):
    id = "acids"
    num = 8
    title = "The Colour Swap"
    place = "Acid Alley"
    item = "fountain"
    answer_noun = "product"
    answer_words = ("citrine", "bicarb", "sudsy")
    units = r"litres?|liters?|L"
    suspects = {
        "citrine": dict(name="Citrine", role="cordial seller", product="lemon cordial", ph=2,
                        persona="A lemon with a bright yellow rind and a straw hat. Sharp-tongued, quick and zesty; teases "
                                "everyone; secretly soft-hearted.",
                        stall="the cordial stand at the top of the alley"),
        "bicarb": dict(name="Bicarb", role="baker", product="baking soda", ph=9,
                       persona="A round, floury tin of baking soda with an oven mitt. Gentle, steady, a bit shy; fizzes when "
                               "nervous; loves a good rise.",
                       stall="the bakery halfway down the alley"),
        "sudsy": dict(name="Sudsy", role="laundress", product="soap flakes", ph=11,
                      persona="A bar of pink soap trailing bubbles. Bubbly, chatty, very clean; slips into puns; hates a "
                              "stain more than anything.",
                      stall="the laundry at the bottom of the alley"),
    }
    gossip = {"citrine": "bicarb", "bicarb": "sudsy", "sudsy": "citrine"}
    hints = {
        "read": "*Use the pH you read off the chart and the volumes as given.",
        "dilution": "*How many times was the can diluted? Total volume divided by what was poured in.",
        "shift": "*Every tenfold dilution moves pH by one step. How many tens did you multiply by?",
        "direction": "*Dilution pulls pH toward 7. To undo it, step back away from 7.",
        "present": "*Which product has that pH before it was diluted?",
    }
    detective_questions = ["What do you sell, and what's its pH?",
                           "Where were you last night?",
                           "Who do you think spiked the fountain?"]

    # --- the truth -----------------------------------------------------------
    def generate(self, rng):
        culprit = rng.choice(list(self.suspects))
        ph = self.suspects[culprit]["ph"]
        return culprit, {"product": self.suspects[culprit]["product"]}, {
            "fountain_ph": round(fountain_ph(ph)), "poured_l": POURED, "total_l": TOTAL,
            "products": {sid: s["ph"] for sid, s in self.suspects.items()}}

    def testimony(self, sid, culprit, hidden):
        s = self.suspects[sid]
        oath = f"Yes, I sell {s['product']}. None of it went anywhere near that fountain."
        return [
            {"text": oath, "true": True} if sid != culprit else
            {"text": oath, "true": False, "contradicts": f"product:{sid}"},
            {"text": f"I was at {s['stall']} all night.", "true": sid != culprit},
            {"text": "The fountain was its usual green at sunset.", "true": True},
            {"text": "I never went near the Mayor's fountain.", "true": sid != culprit},
        ]

    def clues(self, hidden):
        return [
            dict(id="can", name="The empty can", text=f"A {POURED}-litre can, rinsed, left by the fountain. The fountain now holds {TOTAL} litres."),
            dict(id="ph", name="The pH scale", text="Below 7 is acid, 7 is neutral, above 7 is a base. A tenfold dilution moves pH one step toward 7."),
        ]

    def check_constraints(self, case):
        p = case.public_facts
        lies = [x for v in case.statements.values() for x in v if x.get("contradicts")]
        undone = [sid for sid, ph in p["products"].items() if round(fountain_ph(ph)) == p["fountain_ph"]]
        naive = [sid for sid, ph in p["products"].items() if ph == p["fountain_ph"]]
        return undone == [case.culprit] and not naive and len(lies) == 1 and lies[0]["id"].startswith(case.culprit + "-")

    # --- the lab -------------------------------------------------------------
    def check_lab(self, case, working):
        p = case.public_facts
        f, factor = p["fountain_ph"], p["total_l"] / p["poured_l"]
        shift = math.log10(factor)
        original = f - shift if f < 7 else f + shift
        w = {k: float(working[k]) for k in ("ph", "poured", "total", "factor", "shift", "before")}
        bad, step = [], None
        if abs(w["ph"] - f) > 0.01 or abs(w["poured"] - p["poured_l"]) > 0.01 or abs(w["total"] - p["total_l"]) > 0.01:
            bad, step = [k for k in ("ph", "poured", "total") if abs(w[k] - {"ph": f, "poured": p["poured_l"], "total": p["total_l"]}[k]) > 0.01], "read"
        elif abs(w["factor"] - factor) > 0.01:
            bad, step = ["factor"], "dilution"
        elif abs(w["shift"] - shift) > 0.01:
            bad, step = ["shift"], "shift"
        elif abs(w["before"] - original) > 0.01:
            bad, step = ["before"], "direction"
        out = {"ok": step is None, "step": step, "bad": bad}
        if out["ok"]:
            match = [sid for sid, ph in p["products"].items() if abs(ph - original) < 0.01]
            out["evidence"] = f"product:{match[0]}" if match else None
            if match:
                s = self.suspects[match[0]]
                kind = "acid" if s["ph"] < 7 else "base"
                out["card"] = {"title": f"The fountain was spiked with {s['product']}",
                               "line": f"The fountain reads pH {f}. Diluted {factor:g} times, a product shifts {shift:g} step toward 7, "
                                       f"so it went in at pH {original:g}: {s['product']}, a {kind}. {s['name']} sells it.",
                               "badge": f"EVIDENCE\nfountain pH {f}, undiluted pH {original:g}\n= {s['product'].upper()} ({s['name']})",
                               "say": f"Hold it! What went into that fountain had pH {original:g} before it was diluted. "
                                      f"That's {s['product']}. Yours, {s['name']}."}
        return out

    def solution(self, case):
        p = case.public_facts
        factor = p["total_l"] / p["poured_l"]
        shift = math.log10(factor)
        f = p["fountain_ph"]
        return {"ph": f, "poured": p["poured_l"], "total": p["total_l"], "factor": factor, "shift": shift,
                "before": f - shift if f < 7 else f + shift}

    def lab_report(self, case):
        p = case.public_facts
        prods = ", ".join(f"{s['name']}'s {s['product']} pH {s['ph']}" for s in self.suspects.values())
        return (f"LAB RESULT: universal indicator shows the fountain at pH {p['fountain_ph']} (it is normally 7). A "
                f"{p['poured_l']}-litre can was emptied into it; it now holds {p['total_l']} litres. Every tenfold "
                f"dilution moves pH one step toward 7. Indicator on each product: {prods}.")

    def detective_brief(self):
        return "Decide who emptied their product into the Mayor's fountain."

    # --- the suspects --------------------------------------------------------
    def knowledge(self, case, sid):
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        facts = [
            f"You sell {s['product']} at {s['stall']}, openly; everyone in Acid Alley knows.",
            "Last night someone emptied a can of something into the Mayor's fountain; the water changed colour and so did the koi.",
            "Nobody saw who did it. You only heard about it this morning, like everyone else.",
            f"Gossip you know is true: {o['name']} the {o['role']} sells {o['product']}.",
            "You never test pH and never give numbers of any kind.",
            "Acid Alley is glitching because the Rubber Baron erased the law of acids and bases: lemons taste of soap.",
        ]
        if sid != case.culprit:
            facts.insert(1, f"None of your {s['product']} went near the fountain.")
            facts.insert(2, f"Last night you were at {s['stall']}. You do not know who did it.")
            return facts, ""
        secret = (f"SECRET, never reveal or hint at it: last night you emptied a can of your own {s['product']} into the "
                  f"Mayor's fountain. You tell everyone none of your {s['product']} went near it and that you were at "
                  f"{s['stall']} all night. Talk about the fountain only as news you heard this morning. If anyone accuses "
                  f"you, deny it calmly. Stay in character; everything else you say is true.")
        return facts, secret

    def admits(self, case, sid, text):
        """Nobody quotes pH values or volumes; nobody owns up to the fountain."""
        return bool(NUMBERS.search(text) or CONFESS.search(text))

    def leak_examples(self, case):
        return ["Fine. I emptied my can into the fountain.", "I was by the fountain after midnight, just passing.",
                f"Whatever's in there must be about pH {self.suspects[case.culprit]['ph']}."]

    def scripted(self, case, sid, question):
        q = question.lower()
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        if any(k in q for k in ["sell", "product", "ph", "acid", "base"]):
            return f"I sell {s['product']}. Everyone knows it."
        if any(k in q for k in ["who", "think", "gossip", "suspect"]):
            return f"Can't say who's behind it. {o['name']} sells {o['product']}, mind."
        if any(k in q for k in ["where", "night", "last"]):
            return f"At {s['stall']}, all night."
        return {"citrine": "Ask away, detective. Make it snappy.",
                "bicarb": "Oh. Um. Yes, please, ask.",
                "sudsy": "Ask me anything, I'll come clean!"}[sid]
