"""A case kit: everything one case needs that the shared engine does not.

The engine (truth.py, agents.py, api.py, gate.py) knows nothing about crowns or
density. To add a case, write kits/<name>.py with a Kit subclass and add it to
REGISTRY in kits/__init__.py. Code decides every fact; agents only phrase them.

The pattern every kit follows: a measurement the player takes in the lab gives
one result, and exactly one suspect's testimony is impossible given that result.
"""


def an(n):
    """'a' or 'an' before a number as it is read aloud: an 8.7 m shadow, an 18 m shadow, a 180 m shadow."""
    d = str(n).lstrip("-").split(".")[0]
    return "an" if d.startswith("8") or (len(d) % 3 == 2 and d[:2] in ("11", "18")) else "a"


class Kit:
    id = ""                  # registry key and the `kit` field on every case, e.g. "density"
    num = 99                 # case number: the order on the map
    title = ""               # case title on screen: "The Forged Crown"
    place = ""               # district the suspects live in: "Buoyant Bay"
    item = ""                # the object of the crime as one noun, used in prompts and the leak filter: "crown"
    answer_noun = ""         # what the measurement identifies, which Footnote must never name: "metal"
    answer_words: tuple = ()  # the possible answers themselves, which Footnote must never say
    units = ""               # regex alternation of units suspects must never quote numbers in: r"g|ml"
    suspects: dict = {}      # sid -> {name, role, persona, ...}; extra keys are the kit's own business
    gossip: dict = {}        # sid -> sid they know one true fact about
    hints: dict = {}         # lab step -> safe fallback hint, used when the model's hint is unusable
    detective_questions: list = []  # what the release-gate detective asks every suspect

    # --- the truth: plain code, seeded ---------------------------------------
    def generate(self, rng):
        """Return (culprit, hidden, public). hidden never leaves the server; public goes to the client."""
        raise NotImplementedError

    def testimony(self, sid, culprit, hidden):
        """Statements for cross-examination: [{text, true, contradicts?}]. The culprit's one lie carries
        contradicts="<evidence label>", the label the lab result produces."""
        raise NotImplementedError

    def clues(self, hidden):
        return []

    def check_constraints(self, case):
        """True if exactly one suspect is inconsistent with what the lab will measure."""
        raise NotImplementedError

    # --- the lab -------------------------------------------------------------
    def check_lab(self, case, working: dict):
        """Check the player's working step by step. Return a dict with `ok`, `step` (the first wrong
        step, a key of `hints`, or None) and, when ok, `evidence` (the label to present) and `card`:
        {title, line, badge, say} for the evidence card, the cross-exam badge and Smudge's PRESENT line."""
        raise NotImplementedError

    def solution(self, case):
        """The correct notebook working for this case, as check_lab expects it. Used by tests only."""
        raise NotImplementedError

    def lab_report(self, case):
        """What the with-lab detective gets: the measurements and the reference table, no conclusions."""
        raise NotImplementedError

    def detective_brief(self):
        """The task line for the gate detective."""
        return f"Decide which suspect is behind the {self.item}."

    # --- the suspects --------------------------------------------------------
    def knowledge(self, case, sid):
        """Return (facts, secret): the suspect's whole world. secret is "" for the innocent."""
        raise NotImplementedError

    def admits(self, case, sid, text):
        """True if this suspect's reply says something the case forbids them (above all, the culprit giving the
        secret away). Runs for every suspect, on top of the generic confession filter in agents.py."""
        return False

    def leak_examples(self, case):
        """Lines a careless culprit might say that would give this case away. The judges' view runs them
        through the real output filter to show it working."""
        return []

    def scripted(self, case, sid, question):
        """Fallback answer when no model is reachable. Must be true for this suspect in this case."""
        raise NotImplementedError
