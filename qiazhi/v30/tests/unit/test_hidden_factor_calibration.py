from __future__ import annotations

from v30.runtime import create_smoke_runtime


def test_hidden_factor_calibration_starts_as_dialogue_hypothesis() -> None:
    runtime = create_smoke_runtime("v30-hidden-calibration-dialogue")
    calibration = runtime.question_plan.policy_effect["hidden_factor_calibration"]
    assert calibration["status"] == "needs_dialogue"
    assert calibration["amplifier_candidate"] is False
    assert "special_event_year" in calibration["required_next_feedback"]


def test_hidden_factor_calibration_uses_feedback_as_amplifier_candidate() -> None:
    runtime = create_smoke_runtime(
        "v30-hidden-calibration-feedback",
        hidden_factor_user_calibrated=True,
    )
    calibration = runtime.question_plan.policy_effect["hidden_factor_calibration"]
    assert calibration["status"] == "feedback_calibrated"
    assert calibration["amplifier_candidate"] is True
    assert calibration["hypothesis_strength"] > 0.7
