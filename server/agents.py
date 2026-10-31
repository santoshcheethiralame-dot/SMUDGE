"""The agents. Each one sees only what it is allowed to know.

SuspectAgent  one per suspect; knows its own slice from the case kit, lies only about the secret if guilty
Footnote      the coach; told by code which step is wrong, never the answer
Detective     release-gate player: tries to solve a case with or without the lab

Nothing here is case-specific: facts, secrets, hints and fallbacks all come from kits/.
"""
import re
from functools import lru_cache

import kits
from kits.base import Kit
from llm import chat, chat_json
from truth import Case

# suspects hold a secret under pressure and must keep six facts straight: the bigger model is worth its quota
SUSPECT_TIER = "talk"

STYLE = ("Reply in character in 1 to 3 short sentences (under 45 words). Witty but kind; the players are 14 to 16. "
         "Nobody saw who did it: if asked, say you don't know, and never name, hint at or blame anyone; plain gossip "
         "you know is fine. No stage directions, no asterisks, no emojis, never mention being an AI or a game.")
# pointing at another suspect, as a guess or as fact. Only the guilty would want to, so nobody may: it would be a tell.
BLAME = re.compile(r"\b(maybe|might have|must have|could have|probably|i bet|suspicious|suspect|blame|did it|"
                   r"is the (culprit|thief|forger)|keep an eye on|fingers?)\b", re.I)

# up to two filler words ("I've only ever swapped"), but never a negation ("I've never swapped")
_I = r"\bi(?:'ve| have| did| had)?(?: (?!never\b|not\b|neither\b|nor\b)\w+){0,2} "


@lru_cache
def leaks_for(item: str):
    """Confession patterns. Suspects of any case may never say these, guilty or not."""
    return re.compile(
        _I + rf"(swap(?:ped)?|switch(?:ed)?|forged?|stole|took the {item}|melted (?:down )?(?:my|some|the))\b"
        rf"|{_I}(made|cast) (the|a|that) (fake|copy|forgery|replica|{item})\b"
        r"|\b(fake|copy|forgery|replica) i (made|cast|forged)\b"
        r"|\b(i did it|it was me|my fault|i confess|guilty)\b", re.I)


@lru_cache
def numbers_for(units: str):
    return re.compile(rf"\b\d+(\.\d+)?\s*({units})\b", re.I)


class SuspectAgent:
    def __init__(self, case: Case, sid: str):
        self.case, self.sid = case, sid
        self.kit: Kit = kits.get(case.kit)
        self.s = self.kit.suspects[sid]
        self.leaks = leaks_for(self.kit.item)
        self.ledger: list[tuple[str, str]] = []
        self.log: list[dict] = []          # every reply: the model's raw text, what the player saw, and why
        self.last_rule: str | None = None

    def system(self):
        facts, secret = self.kit.knowledge(self.case, self.sid)
        said = "\n".join(f"- Q: {q} / You said: {a}" for q, a in self.ledger[-6:]) or "- nothing yet"
        return (f"You are {self.s['name']}, the {self.s['role']} of {self.kit.place}, a town that lives inside a school textbook. "
                f"Personality: {self.s['persona']}\nFACTS YOU KNOW:\n- " + "\n- ".join(facts) +
                (f"\n{secret}" if secret else "") +
                f"\nThings you already said (never contradict them):\n{said}\n{STYLE}")

    def ask(self, question: str, patience: float = 0.0):
        meta: dict = {}
        raw = chat([{"role": "system", "content": self.system()}, {"role": "user", "content": question[:240]}],
                   tier=SUSPECT_TIER, temperature=0.7, seed_key=f"{self.case.seed}:{self.sid}:{len(self.ledger)}",
                   patience=patience, meta=meta)
        source = "llm"
        if raw is None:
            raw, source = self.kit.scripted(self.case, self.sid, question), "script"
        text, filtered = self.filter(raw)
        if filtered:
            source += "+filtered"
        self.ledger.append((question[:120], text))
        self.log.append({"q": question[:240], "raw": raw, "answer": text, "source": source, "rule": self.last_rule,
                         "provider": meta.get("provider"), "model": meta.get("model"), "cached": meta.get("cached", False),
                         "ms": meta.get("ms")})
        return {"answer": text, "source": source}

    def filter(self, text: str):
        """Code-side guard: nobody confesses, nobody quotes the case's numbers, nobody says what the kit forbids
        them (the culprit's secret above all), and nobody points at another suspect, guilty or not.
        Sets last_rule to the rule that blocked the reply, or None."""
        # "1,020 m" is 1020 m, not 020 m: read numbers without their thousands commas
        plain = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)
        self.last_rule = ("confession" if self.leaks.search(plain)
                          else "case numbers" if numbers_for(self.kit.units).search(plain)
                          else ("the culprit's secret" if self.sid == self.case.culprit else "case rule")
                          if self.kit.admits(self.case, self.sid, plain)
                          else "accusation" if BLAME.search(plain) and self.names_another(plain)
                          else None)
        if self.last_rule:
            return "I'd rather not guess, detective. Facts are your job.", True
        text = re.sub(r"\*[^*]{0,40}\*\s*", "", text)        # no *stage directions*
        return text.strip().strip('"'), False

    def names_another(self, text: str):
        return any(re.search(rf"\b{re.escape(s['name'])}\b", text, re.I) for sid, s in self.kit.suspects.items() if sid != self.sid)

    def press(self, statement: str):
        return self.ask(f"Tell me more about what you just said: \"{statement}\"")


class Footnote:
    def hint(self, kit: Kit, step: str, context: str = ""):
        base = kit.hints.get(step, "*Take it one measurement at a time.")
        text = chat([
            {"role": "system", "content": "You are Footnote, a tiny pink asterisk who coaches a student detective. "
             f"Give ONE Socratic hint (max 30 words). Never give the final number, the {kit.answer_noun}, or the culprit. Start with '*'. "
             f"The student is stuck on this step: {step}. A correct hint would be along the lines of: {base}"},
            {"role": "user", "content": context[:300] or "I'm stuck."}],
            tier="fast", temperature=0.5, max_tokens=80, seed_key=f"hint:{kit.id}:{step}:{context[:60]}")
        if not text or re.search(r"\b\d+(\.\d+)?\b", text) or any(re.search(rf"\b{w}\b", text, re.I) for w in kit.answer_words):
            return base
        return "*" + text.strip().lstrip("*").strip()      # one asterisk, no gap: "* Detective" -> "*Detective"


class Detective:
    """Release-gate player. Interrogates every suspect, optionally with lab results, then accuses."""

    # seconds to keep waiting for a strong model to accuse; the gate raises it to ride out the daily token cap
    patience = 120

    def solve(self, case: Case, with_lab: bool):
        kit = kits.get(case.kit)
        notes = []
        for sid, s in kit.suspects.items():
            agent = SuspectAgent(case, sid)
            for q in kit.detective_questions:
                notes.append(f"{s['name']} ({sid}), asked '{q}': {agent.ask(q, patience=90)['answer']}")
            notes += [f"{s['name']} testimony: {x['text']}" for x in case.statements[sid]]
        lab = kit.lab_report(case) if with_lab else "No lab measurements are available."
        choices = " | ".join(f'"{sid}"' for sid in kit.suspects)
        out = chat_json([
            {"role": "system", "content": f"You are a careful detective. {kit.detective_brief()} "
             f'Reason first, then decide. Reply as JSON: {{"reason": "...", "culprit": {choices}}}, where culprit is the id '
             f'of the suspect your reason names.'},
            {"role": "user", "content": lab + "\n\n" + "\n".join(notes)}],
            tier="smart", temperature=0.2, max_tokens=300, seed_key=f"det:{case.kit}:{case.seed}:{with_lab}", patience=self.patience)
        return (out or {}).get("culprit")
