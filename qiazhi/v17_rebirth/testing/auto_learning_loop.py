from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from v17_rebirth.testing.parameter_sandbox import PARAMETER_SANDBOX_VERSION, build_shadow_override, patched_v17_constants
from v17_rebirth.testing.synthetic_batch_lab import DEFAULT_SYNTHETIC_BATCH_CASES, build_synthetic_batch_report


AUTO_LEARNING_LOOP_VERSION = "v17.auto_learning_loop.v1"


@dataclass(frozen=True)
class ShadowExperimentResult:
    experiment_id: str
    parameter_path: str
    multiplier: float
    override: dict[str, Any]
    baseline_failed: int
    candidate_failed: int
    decision: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "parameter_path": self.parameter_path,
            "multiplier": round(float(self.multiplier), 4),
            "override": dict(self.override),
            "baseline_failed": int(self.baseline_failed),
            "candidate_failed": int(self.candidate_failed),
            "decision": self.decision,
            "rationale": self.rationale,
        }


def run_auto_learning_cycle() -> dict[str, Any]:
    baseline = build_synthetic_batch_report(DEFAULT_SYNTHETIC_BATCH_CASES)
    if int(baseline.get("failed_count") or 0) == 0:
        return {
            "protocol": AUTO_LEARNING_LOOP_VERSION,
            "sandbox_protocol": PARAMETER_SANDBOX_VERSION,
            "baseline": _compact_batch_summary(baseline),
            "shadow_experiments": [],
            "analyst_feedback_items": [],
            "state": "baseline_green_no_parameter_tuning",
            "can_auto_apply": False,
        }

    experiments = baseline.get("parameter_experiments") if isinstance(baseline.get("parameter_experiments"), list) else []
    shadow_results: list[dict[str, Any]] = []
    feedback_items: list[dict[str, Any]] = []
    for experiment in experiments:
        if not isinstance(experiment, dict):
            continue
        trial_specs = _trial_specs_for_experiment(experiment)
        if not trial_specs:
            feedback_items.append(_analyst_item_from_experiment(experiment, reason="no_numeric_parameter_candidate"))
            continue
        for parameter_path, multiplier in trial_specs:
            override = build_shadow_override(parameter_path=parameter_path, multiplier=multiplier)
            if not override:
                feedback_items.append(
                    _analyst_item_from_experiment(
                        experiment,
                        reason=f"parameter_path_not_numeric:{parameter_path}",
                    )
                )
                continue
            with patched_v17_constants(override):
                candidate = build_synthetic_batch_report(DEFAULT_SYNTHETIC_BATCH_CASES)
            shadow_results.append(
                ShadowExperimentResult(
                    experiment_id=str(experiment.get("experiment_id") or ""),
                    parameter_path=parameter_path,
                    multiplier=multiplier,
                    override=override,
                    baseline_failed=int(baseline.get("failed_count") or 0),
                    candidate_failed=int(candidate.get("failed_count") or 0),
                    decision=(
                        "candidate_improves"
                        if int(candidate.get("failed_count") or 0) < int(baseline.get("failed_count") or 0)
                        else "candidate_rejected_or_neutral"
                    ),
                    rationale="Synthetic batch failure count comparison; real config was not modified.",
                ).to_dict()
            )

    improving = [row for row in shadow_results if row.get("decision") == "candidate_improves"]
    return {
        "protocol": AUTO_LEARNING_LOOP_VERSION,
        "sandbox_protocol": PARAMETER_SANDBOX_VERSION,
        "baseline": _compact_batch_summary(baseline),
        "shadow_experiments": shadow_results,
        "analyst_feedback_items": feedback_items,
        "state": "candidate_requires_review" if improving else "needs_analyst_feedback",
        "can_auto_apply": False,
    }


def _trial_specs_for_experiment(experiment: dict[str, Any]) -> list[tuple[str, float]]:
    family = str(experiment.get("parameter_family") or "")
    patch = experiment.get("candidate_patch") if isinstance(experiment.get("candidate_patch"), dict) else {}
    params = [str(item) for item in (patch.get("parameters_to_review") or []) if str(item).strip()]
    if family.startswith("relation_gate."):
        return []
    if not params:
        return []
    scope = str(patch.get("candidate_scope") or "").replace("constants.", "").strip(".")
    out: list[tuple[str, float]] = []
    for param in params[:2]:
        if "*" in param:
            continue
        path = f"{scope}.{param}" if scope else param
        out.append((path, 1.05))
        out.append((path, 0.95))
    return out


def _compact_batch_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "protocol": report.get("protocol"),
        "case_count": int(report.get("case_count") or 0),
        "passed_count": int(report.get("passed_count") or 0),
        "failed_count": int(report.get("failed_count") or 0),
        "parameter_family_counts": dict(report.get("parameter_family_counts") or {}),
        "learning_loop_state": report.get("learning_loop_state"),
    }


def _analyst_item_from_experiment(experiment: dict[str, Any], *, reason: str) -> dict[str, Any]:
    return {
        "experiment_id": str(experiment.get("experiment_id") or ""),
        "parameter_family": str(experiment.get("parameter_family") or ""),
        "reason": reason,
        "requested_feedback": "This issue appears to be gate/protocol/semantic rather than numeric tuning. Please review the rule definition before parameter search.",
    }

