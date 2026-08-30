"""A multi-state gesture has to be written pose by pose. Calibrated on every brief
on disk: certified multi-pose runs used 123-218 motion words with 3-6 named poses;
the two runs that summarised a four-state gesture in 64-76 words with none moved the
element about fifteen times further than the brief asked."""

from __future__ import annotations

from seedance_icons.strategy import check_motion_detail, enumerated_poses

FOUR_STATES = {"idle": "0-0.25", "hover": "0.25-0.5", "pressed": "0.5-0.75", "settled": "0.75-1"}


def test_a_small_single_gesture_is_left_alone() -> None:
    """Batch 2's briefs were 25 words with no enumerated poses and certified at
    0.998-1.0. Short is not the problem; short-for-what-was-asked is."""
    brief = {"motion": "The two wing tips shift up one step, return, then down one step, each pose held."}
    assert check_motion_detail(brief) == []


def test_a_summarised_multi_state_gesture_is_refused() -> None:
    brief = {
        "state_map": FOUR_STATES,
        "motion": (
            "The magnifying glass performs four separate held poses over the still bust, "
            "in order, each held motionless before the next. First it rests. Then it lifts "
            "by two small steps. Then it pushes down by three. Then it returns to rest."
        ),
    }
    problems = check_motion_detail(brief)
    assert len(problems) == 2
    assert "min 120" in problems[0]
    assert "names 0 held poses" in problems[1]


def test_an_enumerated_gesture_passes() -> None:
    motion = (
        "Beat 1, one pose: the glass holds exactly as captured. Beat 2, the sweep, five "
        "held poses: pose one, the lens over the cheek; pose two, over the bridge of the "
        "nose; pose three, at the top of its arc over the brow; pose four, over the hair "
        "mass; pose five, at the far left edge of the head. Beat 3, the press, two held "
        "poses: the glass drops squarely onto the face, its rim one shade darker, its lens "
        "one step larger. Beat 4, the return, three held poses retracing the sweep right "
        "and down, ending on the exact captured pose. The lens contents change with every "
        "pose to show the part of the bust the glass is over, and the glass itself never "
        "changes size or shape at any point in the cycle."
    )
    assert enumerated_poses(motion) >= 4
    assert check_motion_detail({"state_map": FOUR_STATES, "motion": motion}) == []
