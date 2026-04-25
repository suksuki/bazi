from __future__ import annotations

from typing import Any, Iterable


PRACTITIONER_EXPERIMENT_QUEUE_VERSION = "v17.practitioner.experiment_queue.v1"


def build_practitioner_experiment_queue(review_rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    reviews = [dict(row) for row in review_rows if isinstance(row, dict)]
    approved = [
        row
        for row in reviews
        if str(row.get("status") or "").strip().lower() == "approved_for_experiment"
    ]
    experiments = [_experiment_from_review(row) for row in approved]
    return {
        "ok": True,
        "protocol": PRACTITIONER_EXPERIMENT_QUEUE_VERSION,
        "experiment_count": len(experiments),
        "state": "ready_for_shadow_run" if experiments else "no_approved_experiment",
        "experiments": experiments,
        "guardrails": [
            "dry_run_plan_only",
            "no runtime parameter is changed by this queue",
            "synthetic and practitioner benchmark checks are required before promotion",
            "release approval and rollback notes are still required before apply",
        ],
    }


def _experiment_from_review(row: dict[str, Any]) -> dict[str, Any]:
    snapshot = row.get("candidate_snapshot") if isinstance(row.get("candidate_snapshot"), dict) else {}
    candidate_id = _text(row.get("candidate_id") or snapshot.get("candidate_id"))
    family = _text(row.get("parameter_family") or snapshot.get("parameter_family"))
    source_cases = _list_text(snapshot.get("source_cases"))
    source_plugins = _list_text(snapshot.get("source_plugins"))
    return {
        "protocol": PRACTITIONER_EXPERIMENT_QUEUE_VERSION,
        "experiment_id": f"practitioner_experiment::{candidate_id or family}",
        "source_review_id": int(row.get("id") or 0),
        "candidate_id": candidate_id,
        "parameter_family": family,
        "hypothesis": _hypothesis_for_family(family),
        "candidate_patch": _candidate_patch_for_family(family),
        "source_cases": source_cases,
        "source_plugins": source_plugins,
        "reviewer_note": _text(row.get("reviewer_note")),
        "required_commands": [
            "python3 -m pytest qiazhi/v17_rebirth/tests -m synthetic -q",
            "bash qiazhi/v17_rebirth/scripts/run_practitioner_benchmarks.sh",
            "python3 -m pytest qiazhi/v17_rebirth/tests/test_auth_api.py -q",
        ],
        "safety_gates": [
            "dry_run_only",
            "manual_review_required",
            "must_not_reduce_existing_passed_benchmarks",
            "must_not_change_config_without_release_approval",
            "rollback_plan_required_before_apply",
        ],
        "application_mode": "dry_run_plan_only",
    }


def _hypothesis_for_family(parameter_family: str) -> str:
    family = str(parameter_family or "")
    if family.startswith("pattern_specialization."):
        return "Classical pattern gate may be too permissive or too strict."
    if family.startswith("relation_gate."):
        return "Relation gate or runtime origin may need calibration."
    if family.startswith("relation_dynamics."):
        return "Runtime relation dynamics may need damping or source-weight calibration."
    if family.startswith("ten_gods."):
        return "Ten-god static basis or decomposition may need calibration."
    if family.startswith("authority."):
        return "Authority ranking or hard/soft layer weights may need calibration."
    if family.startswith("narrative."):
        return "Narrative contract may need to avoid overstating candidates as conclusions."
    return "Practitioner-reviewed signal may need a shadow experiment."


def _candidate_patch_for_family(parameter_family: str) -> dict[str, Any]:
    family = str(parameter_family or "")
    if family.startswith("pattern_specialization."):
        return {
            "target_module": "backend/logic/L2_structure_patterns/pattern_specializations.py",
            "parameters_to_review": ["pattern gate thresholds", "false-positive guards", "classical evidence requirements"],
            "patch_mode": "review_only",
        }
    if family.startswith("relation_gate."):
        return {
            "target_module": "backend/logic/L1_atomic_ops/relation_geometry_*",
            "parameters_to_review": ["family completeness gate", "runtime origin gate", "source priority"],
            "patch_mode": "review_only",
        }
    if family.startswith("relation_dynamics."):
        return {
            "target_config": "backend/logic/configs/v17_core_constants.json",
            "parameters_to_review": ["runtime source attenuation", "relation stability damping", "source retention floor"],
            "patch_mode": "review_only",
        }
    if family.startswith("ten_gods."):
        return {
            "target_config": "backend/logic/configs/v17_core_constants.json",
            "parameters_to_review": ["STEM_BASE", "BRANCH_BASE", "ROOTED_GAIN", "SEASON_POWER_*"],
            "patch_mode": "review_only",
        }
    if family.startswith("authority."):
        return {
            "target_config": "backend/logic/configs/v17_core_constants.json",
            "parameters_to_review": ["MAX_BIAS_RATIO", "SOFT_BIAS_FLOOR", "OVERRIDE_FORBIDDEN"],
            "patch_mode": "review_only",
        }
    if family.startswith("narrative."):
        return {
            "target": "prompt_contract",
            "parameters_to_review": ["candidate wording", "confidence qualifiers", "evidence citation"],
            "patch_mode": "review_only",
        }
    return {"target": "unknown", "parameters_to_review": [], "patch_mode": "review_only"}


def _list_text(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)][:12]


def _text(value: Any) -> str:
    return str(value or "").strip()
