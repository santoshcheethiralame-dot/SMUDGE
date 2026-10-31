"""Dialogue portraits: 8 expressions x (rest, blink, talk 1-3)."""
from .rig import Pose

EXPR = {
    # expression: (eyes, look, head_roll, head_pitch, resting mouth, hat_tilt)
    "neutral":    ("neutral", (0.0, 0.0), 0.0, 0.0, "line", 0.0),
    "smug":       ("smug", (0.5, 0.0), 0.08, -0.06, "smirk", 0.12),
    "surprised":  ("surprised", (0.0, 0.0), 0.0, -0.08, "o", -0.18),
    "thinking":   ("thinking", (0.6, -1.0), 0.12, -0.05, "line", 0.0),
    "determined": ("determined", (0.0, 0.0), 0.0, 0.06, "line", 0.14),
    "happy":      ("happy", (0.0, 0.0), -0.06, -0.04, "smile", 0.0),
    "worried":    ("worried", (0.0, 0.5), -0.08, 0.04, "frown", 0.0),
    "angry":      ("angry", (0.0, 0.0), 0.0, 0.08, "frown", 0.18),
}
FRAMES = ["rest", "blink", "talk1", "talk2", "talk3"]
TALK = ["open", "wide", "open"]


def portrait_pose(expr, frame):
    eyes, look, roll, pitch, mouth, tilt = EXPR[expr]
    pose = Pose(eyes=eyes, look=look, head_roll=roll, head_pitch=pitch, hat_tilt=tilt,
                blink=1.0 if frame == "blink" else 0.0, drip=0.45)
    if frame.startswith("talk"):
        mouth = TALK[int(frame[-1]) - 1]
    return pose, mouth
