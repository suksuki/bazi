from __future__ import annotations

from v30.evaluation.contracts import TrainingImpactDiff
from v30.training.mingli_training import EngineTrainingExample


def build_training_impact_diff(
    *,
    run_id: str,
    before_examples: list[EngineTrainingExample],
    after_examples: list[EngineTrainingExample],
) -> TrainingImpactDiff:
    before_metrics = _aggregate(before_examples)
    after_metrics = _aggregate(after_examples)
    keys = sorted(set(before_metrics) | set(after_metrics))
    deltas = {key: round(after_metrics.get(key, 0.0) - before_metrics.get(key, 0.0), 3) for key in keys}
    targets = sorted({
        *[target for example in before_examples for target in example.trainable_targets],
        *[target for example in after_examples for target in example.trainable_targets],
    })
    regression = any(
        deltas.get(key, 0.0) < -0.02
        for key in ("overall_quality", "evidence_binding", "advice_actionability")
    ) or deltas.get("overclaim_risk", 0.0) > 0.02
    return TrainingImpactDiff(
        run_id=run_id,
        before_example_count=len(before_examples),
        after_example_count=len(after_examples),
        before_metrics=before_metrics,
        after_metrics=after_metrics,
        metric_deltas=deltas,
        changed_trainable_targets=targets,
        regression_detected=regression,
    )


def _aggregate(examples: list[EngineTrainingExample]) -> dict[str, float]:
    count = max(1, len(examples))
    return {
        "overall_quality": round(sum(example.quality_score.overall_score for example in examples) / count, 3) if examples else 0.0,
        "evidence_binding": round(sum(example.quality_score.evidence_binding for example in examples) / count, 3) if examples else 0.0,
        "advice_actionability": round(sum(example.quality_score.advice_actionability for example in examples) / count, 3) if examples else 0.0,
        "template_risk": round(sum(example.quality_score.template_risk for example in examples) / count, 3) if examples else 0.0,
        "overclaim_risk": round(sum(example.quality_score.overclaim_risk for example in examples) / count, 3) if examples else 0.0,
    }
