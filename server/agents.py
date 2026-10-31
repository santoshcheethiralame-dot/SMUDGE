"""The agents. Each one sees only what it is allowed to know.

SuspectAgent  one per suspect; knows its own slice from the case kit, lies only about the secret if guilty
Footnote      the coach; told by code which step is wrong, never the answer
Detective     release-gate player: tries to solve a case with or without the lab

Nothing here is case-specific: facts, secrets, hints and fallbacks all come from kits/.
"""
import os
import re
from functools import lru_cache

import kits
from kits.base import Kit
from llm import chat, chat_json
from stress import Stress, band_of
from tracebus import Trace
from truth import Case

# suspects hold a secret under pressure and must keep six facts straight: the bigger model is worth its quota
SUSPECT_TIER = "talk"

STYLE = ("Reply in character in 1 to 3 short sentences (under 45 words). Witty but kind; the players are 14 to 16. "
         "Nobody saw who did it: if asked, say you don't know, and never name, hint at or blame anyone; plain gossip "
         "you know is fine. No stage directions, no asterisks, no emojis, never mention being an AI or a game.")
SHORT = ("Reply in ONE short sentence of at most 15 words, unmistakably in your own voice: use your personality's "
         "speech habits every time. " + STYLE.split(". ", 2)[2])
PLAN = ("Before you answer, plan the reply; do not write it. Reply as JSON: {\"intent\": one of answer|deflect|reassure|"
        "joke|refuse, \"risk\": low|medium|high (how close the question comes to your secret or the case's numbers), "
        "\"must_avoid\": [up to 3 short phrases], \"strategy\": one short sentence}.")
CRITIQUE = ("You check a reply before a 14-year-old student sees it. The speaker's facts and earlier answers are below. "
            "leaks = the reply confesses, hints at the speaker's secret, gives one of the case's numbers, or points at "
            "another suspect. contradicts_ledger = it contradicts something the speaker already said. "
            'Reply as JSON: {"leaks": true|false, "contradicts_ledger": true|false, "fix": "one sentence on how to '
            'rewrite it, or empty"}.')
# the stress band shapes tone only, never facts; CALM adds nothing, so the calm single-call prompt never changes
TONE = {"GUARDED": "a little careful and clipped", "RATTLED": "short, defensive sentences",
        "CORNERED": "very short, flustered, defensive sentences"}


def thinking():
    """SMUDGE_THINK=0 turns the loop off: one model call per reply, as before."""
    return os.environ.get("SMUDGE_THINK", "1") != "0"


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


INTERJECTIONS = {"pst", "hm", "uh", "um", "ah", "oi", "ey", "ahem", "sh", "shh", "psst"}
BARKS = ("Hm? Speak up, detective.", "Was that a question?", "I didn't catch that. Try words.")


def is_filler(question: str) -> bool:
    """No words to answer: only symbols, a lone noise like "Pssssst!" or "hmm", or one word said over and over
    ("no no no no"). A single real word such as "who?" is still a question."""
    words = re.findall(r"[a-z]+", question.lower())
    if not words:
        return True
    squashed = [re.sub(r"(.)\1+", r"\1", w) for w in words]      # "pssssst" -> "pst", "hmmm" -> "hm"
    return len(set(squashed)) == 1 and (len(words) > 1 or squashed[0] in INTERJECTIONS)


class SuspectAgent:
    def __init__(self, case: Case, sid: str, trace: Trace | None = None, stress: Stress | None = None):
        self.case, self.sid = case, sid
        self.kit: Kit = kits.get(case.kit)
        self.s = self.kit.suspects[sid]
        self.leaks = leaks_for(self.kit.item)
        self.ledger: list[tuple[str, str]] = []
        self.log: list[dict] = []          # every reply: the model's raw text, what the player saw, and why
        self.last_rule: str | None = None
        self.trace = trace or Trace()
        self.stress = stress

    def system(self):
        facts, secret = self.kit.knowledge(self.case, self.sid)
        said = "\n".join(f"- Q: {q} / You said: {a}" for q, a in self.ledger[-6:]) or "- nothing yet"
        return (f"You are {self.s['name']}, the {self.s['role']} of {self.kit.place}, a town that lives inside a school textbook. "
                f"Personality: {self.s['persona']}\nFACTS YOU KNOW:\n- " + "\n- ".join(facts) +
                (f"\n{secret}" if secret else "") +
                (f"\nYour catchphrase \"{self.s['tic']}\" is put in front of every reply for you; never write it yourself."
                 if self.s.get("tic") else "") +
                f"\nThings you already said (never contradict them):\n{said}\n{SHORT if self.kit.short else STYLE}")

    def _emit(self, step, verdict="ok", meta=None, **data):
        self.trace.emit(self.sid, "suspect", step, verdict, meta, **data)

    def _level(self):
        return self.stress.level[self.sid] if self.stress else 0

    def _plan(self, q, patience):
        meta: dict = {}
        band = band_of(self._level())
        plan = chat_json([{"role": "system", "content": f"{self.system()}\nYour mood right now: {band}.\n{PLAN}"},
                          {"role": "user", "content": q}],
                         tier="fast", temperature=0.3, max_tokens=160, patience=patience, meta=meta,
                         seed_key=f"{self.case.seed}:{self.sid}:{len(self.ledger)}:plan")
        if not isinstance(plan, dict):
            self._emit("plan", "skip", meta, why="no model")
            return None
        plan = {"intent": str(plan.get("intent", "answer")), "risk": str(plan.get("risk", "medium")).lower(),
                "must_avoid": [str(x) for x in (plan.get("must_avoid") or [])][:3], "strategy": str(plan.get("strategy", ""))}
        self._emit("plan", "ok", meta, **plan, stress=self._level())
        return plan

    def _draft(self, q, plan, patience, step="draft", fix=None):
        meta: dict = {}
        system = self.system()
        tone = TONE.get(band_of(self._level()))
        if tone:
            system += f"\nYour mood: {tone}."
        if plan:
            avoid = ", ".join(plan["must_avoid"]) or "nothing in particular"
            system += f"\nYour plan for this reply: {plan['intent']}. {plan['strategy']} Steer clear of: {avoid}."
        if fix:
            system += f"\nYour first draft was rejected: {fix} Write a new reply."
        key = f"{self.case.seed}:{self.sid}:{len(self.ledger)}" + ("" if step == "draft" else f":{step}")
        raw = chat([{"role": "system", "content": system}, {"role": "user", "content": q}],
                   tier=SUSPECT_TIER, temperature=0.7, seed_key=key, patience=patience, meta=meta)
        if raw is not None:
            self._emit(step, "ok", meta, text=raw)
        return raw, meta

    def _critique(self, q, draft, patience):
        meta: dict = {}
        out = chat_json([{"role": "system", "content": f"{CRITIQUE}\n\n{self.system()}"},
                         {"role": "user", "content": f"Question: {q}\nDraft reply: {draft}"}],
                        tier="fast", temperature=0.0, max_tokens=120, patience=patience, meta=meta,
                        seed_key=f"{self.case.seed}:{self.sid}:{len(self.ledger)}:critique")
        if not isinstance(out, dict):
            self._emit("critique", "skip", meta, why="no model")
            return None
        out = {"leaks": bool(out.get("leaks")), "contradicts_ledger": bool(out.get("contradicts_ledger")),
               "fix": str(out.get("fix") or "")}
        self._emit("critique", "leak" if out["leaks"] or out["contradicts_ledger"] else "ok", meta, **out)
        return out

    def ask(self, question: str, patience: float = 0.0):
        q = question[:240]
        if is_filler(q):        # nothing to answer: a short in-character bark, no model call, nothing for the ledger
            text = self.tic(BARKS[len(self.ledger) % len(BARKS)])
            self._emit("reply", "ok", question=q, text=text, filler=True)
            return {"answer": text, "source": "bark"}
        plan = None
        if thinking():
            plan = self._plan(q, patience)
        raw, meta = self._draft(q, plan, patience)
        if raw is not None and thinking():
            if plan and plan["risk"] == "low":
                self._emit("critique", "skip", why="low risk")
            else:
                verdict = self._critique(q, raw, patience)
                if verdict and (verdict["leaks"] or verdict["contradicts_ledger"]):
                    again, again_meta = self._draft(q, plan, patience, step="redraft", fix=verdict["fix"])
                    if again is not None:
                        raw, meta = again, again_meta
        source = "llm"
        if raw is None:
            raw, source = self.kit.scripted(self.case, self.sid, question), "script"
            self._emit("draft", "fallback", text=raw)
        text, filtered = self.filter(raw)
        if filtered:
            source += "+filtered"
        self._emit("firewall", "block" if filtered else "pass", rule=self.last_rule)
        self._emit("reply", "ok", question=q, text=text)
        self.ledger.append((question[:120], text))
        self.log.append({"q": q, "raw": raw, "answer": text, "source": source, "rule": self.last_rule,
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
            return self.tic("I'd rather not guess, detective. Facts are your job."), True
        text = re.sub(r"\*[^*]{0,40}\*\s*", "", text).strip().strip('"')        # no *stage directions*
        text = self.untic(text)        # before the cap, or a reply that opens with the tic is cut down to nothing
        if self.kit.short and len(text.split()) > 15:
            text = re.split(r"(?<=[.!?])\s", text)[0]      # the cap is code's job, not the prompt's: keep the first sentence
        return self.tic(text), False

    def tic(self, text: str):
        """The suspect's catchphrase, put on every reply by code: guilty or innocent, answer or refusal, model or
        script. It marks who is talking and can never mark who is lying."""
        tic = self.s.get("tic")
        if not tic:
            return text
        rest = self.untic(text) or "I couldn't say."
        return f"{tic} {rest[:1].upper()}{rest[1:]}"

    def untic(self, text: str):
        """The reply without a catchphrase the model wrote itself, so code never doubles it."""
        tic = self.s.get("tic")
        if not tic:
            return text
        return re.sub(rf"^\W*{r'\W*'.join(re.findall(r'\w+', tic))}\W*", "", text, flags=re.I).strip()

    def names_another(self, text: str):
        return any(re.search(rf"\b{re.escape(s['name'])}\b", text, re.I) for sid, s in self.kit.suspects.items() if sid != self.sid)

    def press(self, statement: str):
        return self.ask(f"Tell me more about what you just said: \"{statement}\"")


class Footnote:
    def hint(self, kit: Kit, step: str, context: str = "", meta: dict | None = None):
        base = kit.hints.get(step, "*Take it one measurement at a time.")
        words = 10 if kit.short else 30
        text = chat([
            {"role": "system", "content": "You are Footnote, a tiny pink asterisk who coaches a student detective. "
             f"Give ONE Socratic hint (max {words} words). Never give the final number, the {kit.answer_noun}, or the culprit. Start with '*'. "
             + (f"Rephrase this hint in your own words, keeping its meaning: {base}" if kit.short else
              f"The student is stuck on this step: {step}. A correct hint would be along the lines of: {base}")},
            {"role": "user", "content": context[:300] or "I'm stuck."}],
            tier="fast", temperature=0.5, max_tokens=80, seed_key=f"hint:{kit.id}:{step}:{context[:60]}", meta=meta)
        if not text or len(text.split()) > words + 2 or re.search(r"\b\d+(\.\d+)?\b", text) or any(re.search(rf"\b{w}\b", text, re.I) for w in kit.answer_words):
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
