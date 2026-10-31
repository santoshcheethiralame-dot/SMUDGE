"""Case 9, The Slow Lift (Watt Works): work, energy and power, Class 9. P = W / t = m g h / t, with g = 10.

After hours someone hauled a crate up the clock tower's lift shaft to reach the works, and stole the clock's
Golden Escapement. The lift has no motor of its own: you clip on a winch. Each suspect owns one winch, its power
on a brass plate for all to see: Cog's 400 W, Hoist's 800 W, Dynamo's 1200 W. The tower camera recorded the
lift going up. Weigh the crate, measure the shaft, time the climb: the power it took names the winch.
"""
import re

from .base import Kit, an

G = 10
LOADS = [(30, 12), (40, 12), (50, 12)]           # crate kg, shaft m: 3600, 4800, 6000 J
_I = r"\bi(?:'ve| have| did| had)?(?: (?!never\b|not\b|neither\b|nor\b)\w+){0,2} "
CONFESS = re.compile(_I + r"(hauled|lifted|winched|raised|hoisted|clipped|took|ran|used)\b(?: \w+){0,3} "
                     r"(crate|lift|escapement|winch|tower)\b"
                     r"|\bi was (?:(?!not\b|never\b)\w+ ){0,2}?(at|by|near|in|up) the (clock )?tower"
                     r"|\bmy winch was (?!off\b|not\b|never\b|idle\b)\w+", re.I)
NUMBERS = re.compile(r"\b\d+(?:\.\d+)?\s*(?:kg|kilo\w*|m\b|metres?|meters?|s\b|seconds?|J\b|joules?)", re.I)


class PowerKit(Kit):
    id = "power"
    num = 9
    title = "The Slow Lift"
    place = "Watt Works"
    item = "escapement"
    answer_noun = "winch"
    answer_words = ("cog", "hoist", "dynamo")
    units = r"kg|kilograms?|s|seconds?|J|joules?"
    suspects = {
        "cog": dict(name="Cog", role="clockmaker", watts=400,
                    persona="A brass gear with a jeweller's eyepiece and a ticking voice. Precise, prim and punctual; speaks "
                            "in neat clipped sentences; corrects people's grammar.",
                    shop="the clockmaker's workshop under the arches"),
        "hoist": dict(name="Hoist", role="crane operator", watts=800,
                      persona="A big iron crane hook on a chain. Gruff, slow and strong; few words; proud of lifting anything.",
                      shop="the dockyard crane by the canal"),
        "dynamo": dict(name="Dynamo", role="generator mechanic", watts=1200,
                       persona="A buzzing electric motor with copper coils and a spinning fan. Hyper, impatient, talks at "
                               "double speed; loves anything fast.",
                       shop="the generator shed at the edge of town"),
    }
    gossip = {"cog": "hoist", "hoist": "dynamo", "dynamo": "cog"}
    hints = {
        "read": "*Use the mass, the height and the time just as you measured them.",
        "gravity": "*Work against gravity is m x g x h. Don't forget g = 10.",
        "work": "*Work done lifting = mass x g x height.",
        "times": "*Power is work per second: divide the work by the time, don't multiply.",
        "flipped": "*Power = work ÷ time, with the work on top.",
        "power": "*P = W ÷ t, in watts.",
        "present": "*Which winch is rated at exactly that power?",
    }
    detective_questions = ["Tell me about your winch. Was it used last night?",
                           "Where were you last night?",
                           "Who do you think used the lift?"]

    # --- the truth -----------------------------------------------------------
    def generate(self, rng):
        culprit = rng.choice(list(self.suspects))
        m, h = rng.choice(LOADS)
        p = self.suspects[culprit]["watts"]
        t = m * G * h / p
        return culprit, {"winch": p}, {"mass": m, "height": h, "seconds": t, "g": G,
                                       "ratings": {sid: s["watts"] for sid, s in self.suspects.items()}}

    def testimony(self, sid, culprit, hidden):
        s = self.suspects[sid]
        oath = f"My winch is the {s['watts']} W one. It was switched off all night."
        return [
            {"text": oath, "true": True} if sid != culprit else
            {"text": oath, "true": False, "contradicts": f"winch:{sid}"},
            {"text": f"I was at {s['shop']} last night.", "true": sid != culprit},
            {"text": "The Golden Escapement was ticking in the clock at closing time.", "true": True},
            {"text": "I never went near the clock tower lift.", "true": sid != culprit},
        ]

    def clues(self, hidden):
        return [
            dict(id="lift", name="The tower lift", text="No motor of its own: you clip a winch on. The camera recorded it going up after hours."),
            dict(id="plates", name="Winch plates", text="Cog's winch 400 W, Hoist's 800 W, Dynamo's 1200 W."),
        ]

    def check_constraints(self, case):
        p = case.public_facts
        lies = [x for v in case.statements.values() for x in v if x.get("contradicts")]
        power = p["mass"] * G * p["height"] / p["seconds"]
        owners = [sid for sid, w in p["ratings"].items() if abs(w - power) < 1]
        return (owners == [case.culprit] and p["seconds"] * 2 == int(p["seconds"] * 2) and len(lies) == 1
                and lies[0]["id"].startswith(case.culprit + "-"))

    # --- the lab -------------------------------------------------------------
    def check_lab(self, case, working):
        p = case.public_facts
        m, h, t = p["mass"], p["height"], p["seconds"]
        w = {k: float(working[k]) for k in ("m", "h", "t", "w", "p")}
        work = m * G * h
        bad, step = [], None
        given = {"m": m, "h": h, "t": t}
        if any(abs(w[k] - v) > 0.01 for k, v in given.items()):
            bad, step = [k for k, v in given.items() if abs(w[k] - v) > 0.01], "read"
        elif abs(w["w"] - work) > 0.5:
            bad, step = ["w"], ("gravity" if abs(w["w"] - m * h) < 0.5 else "work")
        elif abs(w["p"] - work / t) > 0.5:
            bad = ["p"]
            step = ("times" if abs(w["p"] - work * t) < 0.5 else "flipped" if abs(w["p"] - t / work) < 1e-3
                    else "gravity" if abs(w["p"] - m * h / t) < 0.5 else "power")
        out = {"ok": step is None, "step": step, "bad": bad}
        if out["ok"]:
            power = work / t
            owners = [sid for sid, r in p["ratings"].items() if abs(r - power) < 1]
            out["evidence"] = f"winch:{owners[0]}" if owners else None
            if owners:
                name = self.suspects[owners[0]]["name"]
                out["card"] = {"title": f"The lift ran on {an(round(power))} {round(power)} W winch",
                               "line": f"{m} kg up {h} m is {work} J of work, done in {t:g} s: P = {work} ÷ {t:g} = {round(power)} W. "
                                       f"That's {name}'s winch.",
                               "badge": f"EVIDENCE\nlift: {work} J in {t:g} s\n= {round(power)} W ({name}'s winch)",
                               "say": f"Hold it! Whoever hauled that crate up used {an(round(power))} {round(power)} W winch. There's only one in Watt Works, {name}: yours."}
        return out

    def solution(self, case):
        p = case.public_facts
        work = p["mass"] * G * p["height"]
        return {"m": p["mass"], "h": p["height"], "t": p["seconds"], "w": work, "p": work / p["seconds"]}

    def lab_report(self, case):
        p = case.public_facts
        return (f"LAB RESULT: the crate on the clock-tower lift has a mass of {p['mass']} kg; the shaft is {p['height']} m tall; "
                f"the camera shows the lift taking {p['seconds']:g} s to climb it. Work = m x g x h with g = 10; power = work / time. "
                f"Winch ratings: Cog 400 W, Hoist 800 W, Dynamo 1200 W.")

    def detective_brief(self):
        return "Decide whose winch hauled the lift up the clock tower to steal the Golden Escapement."

    # --- the suspects --------------------------------------------------------
    def knowledge(self, case, sid):
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        facts = [
            f"You own {an(s['watts'])} {s['watts']} W winch; its brass plate says so and everyone in Watt Works knows. You work at {s['shop']}.",
            "Last night someone used the clock tower's crate lift after hours, climbed to the works and stole the Golden Escapement.",
            "The lift has no motor; you have to clip a winch on to raise it.",
            "Nobody saw who did it. You only heard about it this morning, like everyone else.",
            f"Gossip you know is true: {o['name']} the {o['role']} owns {an(o['watts'])} {o['watts']} W winch.",
            "You never measure masses, heights or times and never give numbers except your winch's rating.",
            "Watt Works is glitching because the Rubber Baron erased the law of work and power: cranes lift things that float back down.",
        ]
        if sid != case.culprit:
            facts.insert(1, "Your winch was switched off all night.")
            facts.insert(2, f"Last night you were at {s['shop']}. You do not know who did it.")
            return facts, ""
        secret = (f"SECRET, never reveal or hint at it: last night you clipped your {s['watts']} W winch onto the clock tower "
                  f"lift, rode a crate up and stole the Golden Escapement. You tell everyone your winch was off all night and "
                  f"that you were at {s['shop']}. Talk about the theft only as news you heard this morning. If anyone accuses "
                  f"you, deny it calmly. Stay in character; everything else you say is true.")
        return facts, secret

    def admits(self, case, sid, text):
        """Nobody quotes masses, heights or times; nobody owns up to the tower or the winch being used."""
        if NUMBERS.search(text) or CONFESS.search(text):
            return True
        allowed = {self.suspects[sid]["watts"], self.suspects[self.gossip[sid]]["watts"]}
        return any(float(x) not in allowed for x in re.findall(r"(\d+(?:\.\d+)?)\s*(?:W\b|watts?)", text, re.I))

    def leak_examples(self, case):
        return ["Alright, I winched the crate up the tower.", "My winch was running half the night, as it happens.",
                f"The lift took about {case.public_facts['seconds']:g} seconds, I reckon."]

    def scripted(self, case, sid, question):
        q = question.lower()
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        if any(k in q for k in ["winch", "used", "power", "watt", "motor"]):
            return f"My winch is the {s['watts']} W one. It was off all night."
        if any(k in q for k in ["who", "think", "gossip", "suspect"]):
            return f"Can't say who's behind it. {o['name']} has {an(o['watts'])} {o['watts']} W winch, mind."
        if any(k in q for k in ["where", "night", "last"]):
            return f"At {s['shop']}."
        return {"cog": "Ask. Precisely, please.",
                "hoist": "Ask.",
                "dynamo": "Ask-ask-ask, quick, I'm buzzing!"}[sid]
