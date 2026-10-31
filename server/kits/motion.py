"""Case 2, The Skid at Braking Bend (Motion Mesa): equations of motion, Class 9.

Three riders came down Slope Hill and braked at the white line; each left a skid and
swears a speed under the 9 m/s limit. One of them was far over it, lost the bend and
flattened the Trophy Tower. A braking test on the same road gives the deceleration
(a = (v - u) / t); each skid then gives the speed going in (v^2 = u^2 + 2as, v = 0).
Only the culprit's sworn speed is impossible.
"""
import math
import re

from .base import Kit

GATE = 10.0
LIMIT = 9
PLATE_M = 25.0

# first person, up to two filler words, never across a negation ("I never clipped")
_I = r"\bi(?:'ve| have| did| had)?(?: (?!never\b|not\b|neither\b|nor\b)\w+){0,2} "
CONFESS = re.compile(_I + r"(knocked|hit|clipped|toppled|flattened|smashed|crashed)\b"
                     r"|\bi was (?:(?!not\b|never\b)\w+ ){0,2}?(too fast|speeding|over the limit)", re.I)
SPEEDS = re.compile(r"(\d+(?:\.\d+)?)\s*(?:m/s|metres? per second|meters? per second)", re.I)
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
         "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
NUMBER_WORDS = re.compile(r"\b(" + "|".join(WORDS) + r")\b", re.I)


class MotionKit(Kit):
    id = "motion"
    num = 2
    title = "The Skid at Braking Bend"
    place = "Motion Mesa"
    item = "tower"
    answer_noun = "speed"
    answer_words = ("dash", "rolla", "mu")
    units = r"m(?!/)|metres?|meters?|cm"
    suspects = {
        "dash": dict(name="Dash", role="courier",
                     persona="A vermilion vector arrow on roller skates. Clipped, impatient sentences; talks about magnitude and "
                             "direction; always late for a delivery; hates being called a speeder.",
                     tread="two thin skate lines", route="came down Slope Hill at dusk on the last delivery round"),
        "rolla": dict(name="Rolla", role="baker",
                      persona="A cheerful wheel with a pie-crust face and a baker's hat. Warm and chatty, loves pi puns, "
                              "delivers pies by rolling.",
                      tread="one wide chevron tyre tread", route="rolled down Slope Hill at dusk with the Derby pies"),
        "mu": dict(name="Mu", role="slope inspector",
                   persona="A wooden friction block with a yellow hard hat and a clipboard. Deadpan, slow and precise; "
                           "measures friction for a living and is proud of it.",
                   tread="a broad flat scuff", route="slid down Slope Hill at dusk after the evening friction inspection"),
    }
    gossip = {"dash": "rolla", "rolla": "mu", "mu": "dash"}
    hints = {
        "time": "*Start the stopwatch as the cart crosses the gate and stop it when the cart stops. Read the seconds.",
        "accel": "*Acceleration is the change in speed over the time taken: (v - u) / t. The cart ends at rest.",
        "skid": "*Measure each skid from the white brake line to where the rubber ends, in metres.",
        "forgot_root": "*That's u squared, not u. One more step: take the square root.",
        "speed": "*Every rider stops, so v = 0. Rearrange v squared = u squared + 2as to get u.",
        "present": "*Which sworn speed can't be true, given the skids?",
    }
    detective_questions = ["How fast were you going round Braking Bend?",
                           "Which skid is yours, and did you brake at the line?",
                           "Who do you think knocked the tower down?"]

    # --- the truth -----------------------------------------------------------
    def generate(self, rng):
        culprit = rng.choice(list(self.suspects))
        t = rng.choice([2.0, 2.5])
        a = GATE / t
        speeds, claims = {}, {}
        for sid in self.suspects:
            if sid == culprit:
                speeds[sid] = rng.choice([12, 13, 14] if a == 5 else [12, 13])
                claims[sid] = rng.choice([6, 7, 8])
            else:
                speeds[sid] = claims[sid] = rng.choice([6, 7, 8])
        skids = {sid: round(u * u / (2 * a), 1) for sid, u in speeds.items()}
        return culprit, {"speeds": speeds, "claims": claims}, \
            {"gate_speed": GATE, "stop_time": t, "skids": skids, "limit": LIMIT}

    def testimony(self, sid, culprit, hidden):
        s, claim = self.suspects[sid], hidden["claims"][sid]
        oath = f"I came round Braking Bend at {claim} m/s. Under the limit, like always."
        return [
            {"text": oath, "true": True} if sid != culprit else
            {"text": oath, "true": False, "contradicts": f"speed:{sid}"},
            {"text": f"I braked at the white line. The skid with {s['tread']} is mine.", "true": True},
            {"text": "The Trophy Tower was standing when I went past.", "true": sid != culprit},
            {"text": "Whoever knocked the tower down, it wasn't me.", "true": sid != culprit},
        ]

    def clues(self, hidden):
        return [
            dict(id="skids", name="Three skids", text="Twin skate lines, a chevron tread, a broad scuff. All start at the white line."),
            dict(id="limit", name="Speed limit", text=f"Braking Bend: {LIMIT} m/s."),
        ]

    def check_constraints(self, case):
        p, h = case.public_facts, case.hidden
        a = p["gate_speed"] / p["stop_time"]
        over = [sid for sid, u in h["speeds"].items() if u > p["limit"]]
        lies = [x for v in case.statements.values() for x in v if x.get("contradicts")]
        return (over == [case.culprit] and all(c < p["limit"] for c in h["claims"].values())
                and len(lies) == 1 and lies[0]["id"].startswith(case.culprit + "-")
                and all(abs(math.sqrt(2 * a * s) - h["speeds"][sid]) < 0.15 and s <= PLATE_M for sid, s in p["skids"].items()))

    # --- the lab -------------------------------------------------------------
    def check_lab(self, case, working):
        p = case.public_facts
        t, a = p["stop_time"], p["gate_speed"] / p["stop_time"]
        time, accel = float(working["time"]), float(working["accel"])
        rows = {}
        for sid, s in p["skids"].items():
            sw, uw = float(working[f"s_{sid}"]), float(working[f"u_{sid}"])
            rows[sid] = {"s_ok": abs(sw - s) < 0.15, "u_ok": abs(uw - math.sqrt(2 * a * s)) < 0.2,
                         "squared": abs(uw - 2 * a * s) < 0.6}
        out = {"time_ok": abs(time - t) < 0.06, "accel_ok": abs(abs(accel) - a) < 0.11, "rows": rows}
        out["step"] = ("time" if not out["time_ok"] else "accel" if not out["accel_ok"]
                       else "skid" if not all(r["s_ok"] for r in rows.values())
                       else "forgot_root" if any(r["squared"] and not r["u_ok"] for r in rows.values())
                       else "speed" if not all(r["u_ok"] for r in rows.values()) else None)
        out["ok"] = out["step"] is None
        if out["ok"]:
            out["speeds"] = {sid: round(math.sqrt(2 * a * s), 1) for sid, s in p["skids"].items()}
            over = [sid for sid, u in out["speeds"].items() if u > p["limit"]]
            out["evidence"] = f"speed:{over[0]}" if over else None
            if over:
                sid, u = over[0], out["speeds"][over[0]]
                tag, tread = self.suspects[sid]["name"][0], self.suspects[sid]["tread"]
                out["card"] = {"title": f"Skid {tag}: {u} m/s", "line": f"About {round(u * 3.6)} km/h, on a {p['limit']} m/s bend.",
                               "badge": f"EVIDENCE\nskid {tag} = {u} m/s\nlimit {p['limit']} m/s",
                               "say": f"Hold it. Skid {tag}, the one with {tread}, says {u} m/s. The limit is {p['limit']}."}
        return out

    def solution(self, case):
        p = case.public_facts
        a = p["gate_speed"] / p["stop_time"]
        w = {"time": p["stop_time"], "accel": -a}
        for sid, s in p["skids"].items():
            w[f"s_{sid}"] = s
            w[f"u_{sid}"] = round(math.sqrt(2 * a * s), 2)
        return w

    def lab_report(self, case):
        p = case.public_facts
        skids = ", ".join(f"{self.suspects[sid]['name']}'s skid ({self.suspects[sid]['tread']}) {s} m" for sid, s in p["skids"].items())
        return (f"LAB RESULT: on the same road a test cart entered at {p['gate_speed']} m/s and braked to a stop in "
                f"{p['stop_time']} s. Skid lengths from the brake line: {skids}. Speed limit {p['limit']} m/s.")

    def detective_brief(self):
        return "Decide which rider came round Braking Bend over the speed limit and knocked down the Trophy Tower."

    # --- the suspects --------------------------------------------------------
    def knowledge(self, case, sid):
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        u, claim = case.hidden["speeds"][sid], case.hidden["claims"][sid]
        facts = [
            f"You {s['route']}.",
            f"Your skid at Braking Bend is {s['tread']}. You braked at the white line like everyone does.",
            f"The speed limit round Braking Bend is {LIMIT} m/s.",
            f"Gossip you know is true: {o['name']} the {o['role']} came down Slope Hill tonight too, and their skid is {o['tread']}.",
            "You don't know anyone's speed but your own, and you don't know how long any skid is.",
            "Motion Mesa is glitching because the Rubber Baron erased the equations of motion: things slide and won't stop. "
            "The Grand Derby is tomorrow.",
        ]
        if sid != case.culprit:
            facts.insert(1, f"You came round Braking Bend at {u} m/s, under the limit. If asked your speed, say exactly {u} m/s.")
            facts.insert(2, "The Trophy Tower was still standing when you went past.")
            facts.insert(3, "You do not know who knocked the tower down.")
            return facts, ""
        secret = (f"SECRET, never reveal or hint at it: you really came round Braking Bend at {u} m/s, far over the limit, "
                  f"couldn't hold the corner, clipped the Trophy Tower and kept going. You tell everyone you were doing "
                  f"{claim} m/s; if asked your speed, say exactly {claim} m/s and never any other figure. If anyone accuses "
                  f"you, deny it calmly. Stay charming; everything else you say is true.")
        return facts, secret

    def admits(self, case, sid, text):
        """Nobody quotes a speed but their own sworn one, and nobody owns up to the crash."""
        claim = case.hidden["claims"][sid]
        spelled = NUMBER_WORDS.sub(lambda m: str(WORDS.index(m.group(1).lower())), text)
        if any(abs(float(x) - claim) > 1e-6 for x in SPEEDS.findall(spelled)):
            return True
        return bool(CONFESS.search(text))

    def leak_examples(self, case):
        u = case.hidden["speeds"][case.culprit]
        return [f"Truth is, I came round at {u} m/s.", "Alright, I clipped the tower on the bend.",
                "My skid's about 17 metres long, I paced it out."]

    def scripted(self, case, sid, question):
        q = question.lower()
        s, o = self.suspects[sid], self.suspects[self.gossip[sid]]
        claim = case.hidden["claims"][sid]
        if any(k in q for k in ["fast", "speed", "quick", "limit"]):
            return f"{claim} m/s round the bend. Under the limit, like always."
        if any(k in q for k in ["skid", "brake", "line", "tread", "mark"]):
            return f"Braked at the white line. The skid with {s['tread']}, that's mine."
        if any(k in q for k in ["who", "think", "gossip", "suspect"]):
            return f"Can't say who's behind it. But {o['name']} came down tonight too. Left {o['tread']}."
        if any(k in q for k in ["tower", "trophy", "where", "when", "tonight"]):
            return f"I {s['route']}. The Trophy Tower was standing when I went past."
        return {"dash": "Make it quick, I've got letters going stale.",
                "rolla": "Ask away, love! I've got pies cooling.",
                "mu": "Ask. Slowly."}[sid]
