"""How rattled each suspect is, in plain code. The same rules apply to every suspect, guilty or not, so stress
shapes tone and can never be a tell. The PLAN step reads the band; facts never depend on it."""
import re

ACCUSE = re.compile(r"\b(lie|lied|lying|liar|confess|admit|guilty|you did|it was you)\b", re.I)
BANDS = ((2, "CALM"), (4, "GUARDED"), (7, "RATTLED"), (9, "CORNERED"))


def band_of(level: int) -> str:
    return next(name for top, name in BANDS if level <= top)


class Stress:
    def __init__(self, sids):
        self.level = {sid: 0 for sid in sids}

    def _add(self, sid, n):
        self.level[sid] = max(0, min(9, self.level[sid] + n))

    def _quiet_others(self, sid):
        for other in self.level:
            if other != sid:
                self._add(other, -1)

    def asked(self, sid, question: str):
        self._quiet_others(sid)
        if ACCUSE.search(question):
            self._add(sid, 1)

    def pressed(self, sid):
        self._quiet_others(sid)
        self._add(sid, 1)

    def presented(self, sid, hit: bool):
        self._add(sid, 2 + (3 if hit else 0))

    def band(self, sid):
        return band_of(self.level[sid])

    def view(self):
        return {sid: {"level": n, "band": band_of(n)} for sid, n in self.level.items()}
