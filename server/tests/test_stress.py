"""Stress is plain code, the same rules for every suspect, so it can never point at the culprit."""
import pytest

from stress import Stress, band_of

SIDS = ["volta", "ohmar", "glim"]


@pytest.mark.parametrize("level,band", [(0, "CALM"), (2, "CALM"), (3, "GUARDED"), (4, "GUARDED"), (5, "RATTLED"),
                                         (7, "RATTLED"), (8, "CORNERED"), (9, "CORNERED")])
def test_bands(level, band):
    assert band_of(level) == band


def test_accusing_question_raises_only_the_one_asked():
    s = Stress(SIDS)
    s.asked("ohmar", "Admit it, you're lying!")
    assert s.level == {"volta": 0, "ohmar": 1, "glim": 0}


def test_a_plain_question_changes_nothing_for_the_one_asked():
    s = Stress(SIDS)
    s.asked("ohmar", "Where were you last night?")
    assert s.level["ohmar"] == 0


def test_quiet_turns_cool_the_others_down():
    s = Stress(SIDS)
    s.level.update(volta=3, glim=1)
    s.asked("ohmar", "Hello")
    assert s.level == {"volta": 2, "ohmar": 0, "glim": 0}


def test_press_and_present():
    s = Stress(SIDS)
    s.pressed("glim")
    assert s.level["glim"] == 1
    s.presented("glim", hit=False)
    assert s.level["glim"] == 3
    s.presented("glim", hit=True)
    assert s.level["glim"] == 8 and s.band("glim") == "CORNERED"


def test_clamped_to_0_9():
    s = Stress(SIDS)
    for _ in range(5):
        s.presented("volta", hit=True)
    assert s.level["volta"] == 9
    for _ in range(20):
        s.asked("glim", "hi")
    assert s.level["volta"] == 0


def test_view_shape():
    assert Stress(SIDS).view()["ohmar"] == {"level": 0, "band": "CALM"}
