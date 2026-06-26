from __future__ import annotations

from pydantic import Field

from v30.contracts import FeatureEvidence, V30Model


class HiddenFactorCalibration(V30Model):
    calibration_id: str
    status: str
    hypothesis_strength: float
    amplifier_candidate: bool
    evidence_ids: list[str] = Field(default_factory=list)
    required_next_feedback: list[str] = Field(default_factory=list)
    boundary: str = "calibration_hypothesis_not_deterministic_fact"


def calibrate_hidden_factors(context_id: str, evidence: list[FeatureEvidence]) -> HiddenFactorCalibration:
    hidden = [row for row in evidence if row.domain == "ten_god" and row.kind == "hidden_stem"]
    feedback = [row for row in evidence if row.domain == "feedback" and row.kind == "hidden_factor_calibration"]
    rule_countered = [
        row for row in evidence
        if row.domain == "rule"
        and row.kind == "hidden_factor"
        and "rule_decision_state:countered" in row.supports
    ]
    if feedback and rule_countered:
        return HiddenFactorCalibration(
            calibration_id=f"{context_id}:hidden_factor:calibration",
            status="feedback_calibrated",
            hypothesis_strength=0.78,
            amplifier_candidate=True,
            evidence_ids=[*(row.evidence_id for row in hidden), *(row.evidence_id for row in feedback), *(row.evidence_id for row in rule_countered)],
            required_next_feedback=["repeat_state_confirmation", "time_layer_alignment"],
        )
    if hidden:
        return HiddenFactorCalibration(
            calibration_id=f"{context_id}:hidden_factor:calibration",
            status="needs_dialogue",
            hypothesis_strength=0.42,
            amplifier_candidate=False,
            evidence_ids=[row.evidence_id for row in hidden],
            required_next_feedback=["special_event_year", "repeated_state_pattern"],
        )
    return HiddenFactorCalibration(
        calibration_id=f"{context_id}:hidden_factor:calibration",
        status="not_applicable",
        hypothesis_strength=0.0,
        amplifier_candidate=False,
    )
