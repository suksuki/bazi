from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from v17_rebirth.testing.synthetic_tuning_bridge import (
    build_parameter_candidate_plan,
    build_tuning_bridge_report,
)


EXPERIMENT_RUNNER_VERSION = "v17.parameter_candidate_runner.v1"


@dataclass(frozen=True)
class ParameterExperiment:
    experiment_id: str
    parameter_family: str
    hypothesis: str
    candidate_patch: dict[str, Any]
    synthetic_cases: tuple[str, ...]
    benchmark_cases: tuple[str, ...]
    required_commands: tuple[str, ...]
    safety_gates: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol": EXPERIMENT_RUNNER_VERSION,
            "experiment_id": self.experiment_id,
            "parameter_family": self.parameter_family,
            "hypothesis": self.hypothesis,
            "candidate_patch": dict(self.candidate_patch),
            "synthetic_cases": list(self.synthetic_cases),
            "benchmark_cases": list(self.benchmark_cases),
            "required_commands": list(self.required_commands),
            "safety_gates": list(self.safety_gates),
            "application_mode": "dry_run_plan_only",
        }


def build_parameter_experiments_from_report(report: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(report, dict):
        report = {}
    candidates = report.get("parameter_candidate_plan")
    if not isinstance(candidates, list) or not candidates:
        candidates = build_parameter_candidate_plan(
            report.get("parameter_family_counts")
            if isinstance(report.get("parameter_family_counts"), dict)
            else {}
        )
    benchmark_cases = [
        str(row.get("case_id") or "").strip()
        for row in (report.get("audits") or [])
        if isinstance(row, dict) and str(row.get("case_id") or "").strip()
    ]
    return [
        _experiment_from_candidate(row, benchmark_cases=tuple(benchmark_cases)).to_dict()
        for row in candidates
        if isinstance(row, dict)
    ]


def build_current_parameter_experiment_report() -> dict[str, Any]:
    tuning_report = build_tuning_bridge_report()
    experiments = build_parameter_experiments_from_report(tuning_report)
    return {
        "protocol": EXPERIMENT_RUNNER_VERSION,
        "tuning_bridge_protocol": tuning_report.get("protocol"),
        "experiment_count": len(experiments),
        "experiments": experiments,
        "state": "no_experiment_needed" if not experiments else "manual_review_required",
    }


def _experiment_from_candidate(
    candidate: dict[str, Any],
    *,
    benchmark_cases: tuple[str, ...],
) -> ParameterExperiment:
    family = str(candidate.get("parameter_family") or "").strip()
    synthetic_cases = tuple(
        str(case_id).strip()
        for case_id in (candidate.get("synthetic_cases") or [])
        if str(case_id).strip()
    )
    return ParameterExperiment(
        experiment_id=f"experiment::{family}",
        parameter_family=family,
        hypothesis=_hypothesis_for_family(family),
        candidate_patch=_candidate_patch_for_family(family),
        synthetic_cases=synthetic_cases,
        benchmark_cases=benchmark_cases,
        required_commands=(
            "python3 -m pytest qiazhi/v17_rebirth/tests -m synthetic -q",
            "bash qiazhi/v17_rebirth/scripts/run_practitioner_benchmarks.sh",
            "python3 -m pytest qiazhi/v17_rebirth/tests/test_parameter_candidate_runner.py -q",
        ),
        safety_gates=(
            "dry_run_only",
            "manual_review_required",
            "must_not_reduce_existing_passed_benchmarks",
            "must_not_change_config_without_explicit_approval",
        ),
    )


def _hypothesis_for_family(parameter_family: str) -> str:
    family = str(parameter_family or "")
    if family.startswith("relation_formation."):
        key = family.split(".", 1)[-1]
        return f"{key} relation formation may need gate/factor calibration."
    if family.startswith("relation_dynamics."):
        key = family.split(".", 1)[-1]
        return f"{key} relation dynamics may need energy/stability damping calibration."
    if family.startswith("relation_gate."):
        key = family.split(".", 1)[-1]
        return f"{key} gate may be too permissive or too strict."
    if family.startswith("ten_gods."):
        return "Ten-god static basis or decomposition may need calibration."
    if family.startswith("authority."):
        return "Authority ranking or hard/soft layer weights may need calibration."
    return "Related protocol may need calibration."


def _candidate_patch_for_family(parameter_family: str) -> dict[str, Any]:
    family = str(parameter_family or "")
    if family.startswith("relation_formation."):
        key = family.split(".", 1)[-1].upper()
        return {
            "target_config": "backend/logic/configs/v17_core_constants.json",
            "candidate_scope": "constants.L0_FOUNDATION",
            "parameters_to_review": [
                f"REL_FAMILY_BASE_FACTOR_{key}",
                f"REL_FAMILY_FULL_CLEAN_{key}",
                f"REL_VISIBLE_STEM_RESONANCE_{key}",
            ],
            "patch_mode": "review_only",
        }
    if family.startswith("relation_dynamics."):
        key = family.split(".", 1)[-1].upper()
        return {
            "target_config": "backend/logic/configs/v17_core_constants.json",
            "candidate_scope": "constants.L0_FOUNDATION",
            "parameters_to_review": [
                f"REL_ROOT_PENALTY_{key}",
                f"REL_SOURCE_ATTENUATION_{key}",
                f"REL_SOURCE_RETENTION_MIN_{key}",
            ],
            "patch_mode": "review_only",
        }
    if family.startswith("relation_gate."):
        return {
            "target_module": "backend/logic/L1_atomic_ops/relation_geometry_*",
            "parameters_to_review": ["family completeness gate", "runtime origin gate"],
            "patch_mode": "review_only",
        }
    if family.startswith("ten_gods."):
        return {
            "target_config": "backend/logic/configs/v17_core_constants.json",
            "candidate_scope": "constants.L0_FOUNDATION",
            "parameters_to_review": [
                "STEM_BASE",
                "BRANCH_BASE",
                "ROOTED_GAIN",
                "CROSS_POLARITY_ROOT_SUPPORT_FACTOR",
                "SEASON_POWER_*",
            ],
            "patch_mode": "review_only",
        }
    if family.startswith("authority."):
        return {
            "target_config": "backend/logic/configs/v17_core_constants.json",
            "candidate_scope": "constants.AUTHORITY_LAYER",
            "parameters_to_review": ["MAX_BIAS_RATIO", "SOFT_BIAS_FLOOR", "OVERRIDE_FORBIDDEN"],
            "patch_mode": "review_only",
        }
    return {
        "target": "unknown",
        "parameters_to_review": [],
        "patch_mode": "review_only",
    }

