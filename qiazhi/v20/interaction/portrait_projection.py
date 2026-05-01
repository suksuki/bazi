from __future__ import annotations

from v20.answer.measurement_policy import domain_label, feature_label, measurement_focus, measurement_stage
from v20.features.schema import FeatureLayer


def portrait_projection(feature_layer: FeatureLayer) -> dict[str, object]:
    axes = _profile_axes(feature_layer)
    return {
        "version": "v20.portrait_projection.v1",
        "status": "ready" if feature_layer.features else "empty",
        "role": "bazi_feature_projection_and_calibration_surface_only",
        "measurement_role": "命理画像只投影已编译特征，用于校准测算入口，不驱动结论。",
        "axes": axes,
        "items": [
            {
                "feature_id": feature.feature_id,
                "title": feature_label(feature),
                "domain": feature.domain,
                "measurement_topic": domain_label(feature.domain),
                "measurement_stage": measurement_stage(feature.domain),
                "measurement_focus": measurement_focus(feature),
                "confidence": feature.confidence,
                "calibration_state": feature.calibration_state,
            }
            for feature in feature_layer.features[:8]
        ],
        "guardrails": [
            "PORTRAIT_IS_FEATURE_PROJECTION",
            "NO_QUESTION_BIAS_FROM_PORTRAIT",
            "NO_PORTRAIT_DRIVEN_FORTUNE_VERDICT",
        ],
    }


def _profile_axes(feature_layer: FeatureLayer) -> list[dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for feature in feature_layer.features:
        row = rows.setdefault(
            feature.domain,
            {
                "domain": feature.domain,
                "label": domain_label(feature.domain),
                "measurement_stage": measurement_stage(feature.domain),
                "feature_count": 0,
                "peak_confidence": 0.0,
                "calibration_state": feature.calibration_state,
            },
        )
        row["feature_count"] = int(row["feature_count"]) + 1
        row["peak_confidence"] = max(float(row["peak_confidence"]), feature.confidence)
    return sorted(rows.values(), key=lambda row: (str(row["measurement_stage"]), str(row["label"])))
