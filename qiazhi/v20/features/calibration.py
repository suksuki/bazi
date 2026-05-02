from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any

from v20.features.schema import BaziFeature


@dataclass(frozen=True)
class ConfidenceCalibrationPolicy:
    policy_id: str = "v20.confidence_calibration.default"
    domain_offsets: dict[str, float] = field(default_factory=dict)
    readiness_offsets: dict[str, float] = field(default_factory=dict)
    max_adjustment: float = 0.1
    floor: float = 0.18
    ceiling: float = 0.92
    source: str = "deterministic_default"
    status: str = "active"
    guardrails: tuple[str, ...] = (
        "CALIBRATION_ADJUSTS_CONFIDENCE_ONLY",
        "NO_FEATURE_CREATION",
        "NO_EVIDENCE_MUTATION",
        "LEARNED_POLICY_REQUIRES_PROMOTION_GATE",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_confidence_calibration_policy() -> ConfidenceCalibrationPolicy:
    return ConfidenceCalibrationPolicy()


def calibrate_features(
    features: tuple[BaziFeature, ...] | list[BaziFeature],
    policy: ConfidenceCalibrationPolicy | None = None,
) -> tuple[BaziFeature, ...]:
    policy = policy or default_confidence_calibration_policy()
    return tuple(_calibrate_feature(feature, policy) for feature in features)


def confidence_calibration_manifest() -> dict[str, object]:
    policy = default_confidence_calibration_policy()
    return {
        "version": "v20.confidence_calibration_manifest.v1",
        "default_policy": policy.to_dict(),
        "allowed_learning_inputs": [
            "synthetic_validation_stability",
            "coverage_gap_frequency",
            "anonymized_feedback_calibration_signal",
            "active_replay_delta",
        ],
        "blocked_learning_outputs": [
            "new_feature",
            "evidence_ref_rewrite",
            "rule_truth_update",
            "answer_conclusion",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "CONFIDENCE_CALIBRATION_IS_NUMERIC_ONLY",
            "FEATURE_IDS_AND_EVIDENCE_REFS_ARE_IMMUTABLE",
            "PROMOTION_GATE_REQUIRED_FOR_LEARNED_POLICY",
        ],
    }


def _calibrate_feature(feature: BaziFeature, policy: ConfidenceCalibrationPolicy) -> BaziFeature:
    adjustment = policy.domain_offsets.get(feature.domain, 0.0)
    adjustment += policy.readiness_offsets.get(feature.readiness, 0.0)
    bounded_adjustment = max(-policy.max_adjustment, min(policy.max_adjustment, adjustment))
    confidence = round(max(policy.floor, min(policy.ceiling, feature.confidence + bounded_adjustment)), 3)
    return replace(feature, confidence=confidence)
