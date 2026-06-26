from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.main_module_completion_review import run_main_module_completion_review
from v30.validation.stage_a_evidence_review import (
    STAGE_A_EVIDENCE_REVIEW_VERSION,
    run_stage_a_evidence_review,
)


CORE_MAINLINE_SELECTION_AFTER_RELEASE_HOLD_VERSION = "v30.core_mainline_selection_after_release_hold.v1"


def run_core_mainline_selection_after_release_hold(
    *,
    sample_limit: int = 8,
    shard_id: int = 7,
    shard_limit: int = 16,
    reading_id: str = "mcr3-core-mainline-selection",
    rerun_stage_a_review: bool = False,
) -> dict[str, Any]:
    stage_a_review = (
        run_stage_a_evidence_review(
            sample_limit=sample_limit,
            shard_id=shard_id,
            shard_limit=shard_limit,
            reading_id=reading_id,
        )
        if rerun_stage_a_review
        else _recorded_stage_a_review_stub()
    )
    module_review = run_main_module_completion_review(reading_id=f"{reading_id}-module-review")
    return build_core_mainline_selection_after_release_hold(
        stage_a_evidence_review=stage_a_review,
        main_module_completion_review=module_review,
    )


def build_core_mainline_selection_after_release_hold(
    *,
    stage_a_evidence_review: Mapping[str, Any],
    main_module_completion_review: Mapping[str, Any],
) -> dict[str, Any]:
    selected_at = datetime.now(timezone.utc)
    release_hold = _release_hold_summary(stage_a_evidence_review)
    module_review = _module_review_summary(main_module_completion_review)
    candidates = _candidate_rows()
    ranked = sorted(candidates, key=lambda row: int(row["priority_score"]), reverse=True)
    decision = _decision(release_hold=release_hold, module_review=module_review, ranked_candidates=ranked)
    return {
        "version": CORE_MAINLINE_SELECTION_AFTER_RELEASE_HOLD_VERSION,
        "selected_at": selected_at.isoformat(),
        "status": "completed" if decision["core_mainline_selection_ready"] else "blocked",
        "task": {
            "task_id": "MCR3",
            "title": "Return To Core Module Mainline Selection",
            "scope": "select_next_core_business_module_task_after_stage_a_release_hold",
        },
        "release_hold_summary": release_hold,
        "module_review_summary": module_review,
        "ranked_candidates": ranked,
        "decision": decision,
        "policy_boundary": {
            "external_release_allowed": False,
            "full_pytest_run": False,
            "synthetic_all_run": False,
            "live_llm_smoke_run": False,
            "real_env_smoke_run": False,
            "full_518k_run": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "real_person_truth_label_allowed": False,
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "mcr3_selects_core_measurement_work_without_release_expansion_or_chart_fact_mutation",
    }


def _recorded_stage_a_review_stub() -> dict[str, Any]:
    return {
        "version": STAGE_A_EVIDENCE_REVIEW_VERSION,
        "status": "completed",
        "decision": {
            "stage_a_evidence_review_complete": True,
            "decision_status": "rel_s4_stage_a_evidence_review_complete_external_release_held",
            "reviewed_gate_ids": ["controlled_release_readiness", "synthetic_all", "518k_sample", "518k_shard"],
            "blockers": [],
            "controlled_trial_readiness_confirmed": True,
            "external_release_allowed": False,
            "return_to_core_module_mainline": True,
            "additional_heavy_live_gate_authorization_recommended": False,
            "full_pytest_authorized": False,
            "live_llm_smoke_authorized": False,
            "real_env_smoke_authorized": False,
            "full_518k_authorized": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
        "boundary": "recorded_rel_s4_evidence_stub_prevents_routine_stage_a_rerun",
    }


def _release_hold_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "stage_a_evidence_review_complete": bool(decision.get("stage_a_evidence_review_complete")),
        "controlled_trial_readiness_confirmed": bool(decision.get("controlled_trial_readiness_confirmed")),
        "external_release_allowed": bool(decision.get("external_release_allowed")),
        "return_to_core_module_mainline": bool(decision.get("return_to_core_module_mainline")),
        "additional_heavy_live_gate_authorization_recommended": bool(decision.get("additional_heavy_live_gate_authorization_recommended")),
        "full_pytest_authorized": bool(decision.get("full_pytest_authorized")),
        "live_llm_smoke_authorized": bool(decision.get("live_llm_smoke_authorized")),
        "real_env_smoke_authorized": bool(decision.get("real_env_smoke_authorized")),
        "full_518k_authorized": bool(decision.get("full_518k_authorized")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _module_review_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    matrix = _list(payload.get("module_completion_matrix"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(decision.get("decision_status") or ""),
        "main_module_completion_review_ready": bool(decision.get("main_module_completion_review_ready")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "synthetic_all_required": bool(decision.get("synthetic_all_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "live_llm_required": bool(decision.get("live_llm_required")),
        "policy_pointer_write_allowed": bool(decision.get("policy_pointer_write_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "module_count": len(matrix),
        "core_module_count": len([
            row
            for row in matrix
            if isinstance(row, Mapping)
            and str(row.get("module_id") or "") in {"M1/M2", "M3", "M4", "M5", "M6", "M7", "M8"}
        ]),
    }


def _candidate_rows() -> list[dict[str, Any]]:
    return [
        _candidate(
            "SYN-CAL1",
            "Synthetic Archetype Rule-Claim Calibration",
            "m3_m5_m6_measurement_quality",
            96,
            [
                "build typical synthetic Bazi archetypes instead of unverifiable real-person labels",
                "verify rule matching, portrait features, dynamic paths, ranked decisions, and practical claims together",
                "route failures to M3/M5/M6 calibration queues without mutating chart facts",
            ],
            ["M3", "M5", "M6", "M7", "BT"],
        ),
        _candidate(
            "M5-CAL2",
            "Ranked Decision Weight Replay Calibration",
            "m5_decision_quality",
            88,
            [
                "replay synthetic archetype evidence through strength, structure, and useful-god candidates",
                "keep useful-god and structure as ranked bounded candidates",
            ],
            ["M4", "M5", "M7"],
        ),
        _candidate(
            "M6-CAL2",
            "Practical Claim Density And Evidence Calibration",
            "m6_reading_quality",
            84,
            [
                "tighten domain claim density and evidence trace readability",
                "avoid generic language without using LLM as a fact generator",
            ],
            ["M3", "M5", "M6", "LLM"],
        ),
        _candidate(
            "IQ-CAL2",
            "Question Strategy Calibration From Synthetic Archetypes",
            "question_strategy",
            76,
            [
                "adapt next questions to synthetic archetype state",
                "keep hidden factors as feedback clues only",
            ],
            ["IQ", "M3", "BT"],
        ),
        _candidate(
            "REL-LIVE1",
            "Additional Release Live Or Full Gate Authorization",
            "release_boundary",
            20,
            [
                "not needed after REL-S4 because external release remains held",
                "only run if operator explicitly chooses release expansion",
            ],
            ["REL"],
        ),
    ]


def _candidate(
    task_id: str,
    title: str,
    selected_track: str,
    priority_score: int,
    reasons: list[str],
    modules: list[str],
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "title": title,
        "selected_track": selected_track,
        "priority_score": priority_score,
        "target_modules": modules,
        "reasons": reasons,
        "heavy_default_required": False,
        "chart_fact_mutation_allowed": False,
        "real_person_truth_label_allowed": False,
    }


def _decision(
    *,
    release_hold: Mapping[str, Any],
    module_review: Mapping[str, Any],
    ranked_candidates: list[Mapping[str, Any]],
) -> dict[str, Any]:
    blockers: list[str] = []
    if release_hold["version"] != STAGE_A_EVIDENCE_REVIEW_VERSION:
        blockers.append("rel_s4_evidence_missing")
    if not release_hold["stage_a_evidence_review_complete"]:
        blockers.append("rel_s4_evidence_not_complete")
    if release_hold["external_release_allowed"]:
        blockers.append("external_release_unexpectedly_allowed")
    if not release_hold["return_to_core_module_mainline"]:
        blockers.append("release_hold_does_not_return_to_core_mainline")
    if release_hold["full_pytest_authorized"] or release_hold["live_llm_smoke_authorized"] or release_hold["real_env_smoke_authorized"] or release_hold["full_518k_authorized"]:
        blockers.append("unexpected_heavy_live_gate_authorization")
    if release_hold["policy_pointer_promotion_allowed"] or release_hold["chart_fact_mutation_allowed"]:
        blockers.append("unexpected_policy_or_chart_mutation_permission")
    if not module_review["main_module_completion_review_ready"]:
        blockers.append("main_module_completion_review_not_ready")
    if module_review["policy_pointer_write_allowed"] or module_review["chart_fact_mutation_allowed"]:
        blockers.append("module_review_allows_policy_or_chart_mutation")
    if not ranked_candidates:
        blockers.append("no_core_mainline_candidate")

    selected = dict(ranked_candidates[0]) if ranked_candidates else {}
    ready = not blockers
    return {
        "core_mainline_selection_ready": ready,
        "decision_status": "mcr3_core_mainline_selected" if ready else "mcr3_core_mainline_selection_blocked",
        "selected_task_id": str(selected.get("task_id") or ""),
        "selected_title": str(selected.get("title") or ""),
        "selected_track": str(selected.get("selected_track") or ""),
        "selected_priority_score": int(selected.get("priority_score", 0) or 0),
        "blockers": blockers,
        "external_release_allowed": False,
        "return_to_core_module_mainline": ready,
        "full_pytest_required": False,
        "synthetic_all_required": False,
        "full_518k_required": False,
        "live_llm_required": False,
        "real_env_smoke_required": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "real_person_truth_label_allowed": False,
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["core_mainline_selection_ready"]:
        return {
            "task_id": decision["selected_task_id"],
            "title": decision["selected_title"],
            "selected_track": decision["selected_track"],
            "scope": [
                "use synthetic typical Bazi archetypes as verifiable calibration fixtures",
                "validate M3 rules, portraits, features, dynamic paths, M5 ranked decisions, and M6 claims together",
                "route evidence to calibration queues without chart-fact mutation or pointer promotion",
            ],
            "full_pytest_run_now": False,
            "synthetic_all_run_now": False,
            "full_518k_run_now": False,
            "live_llm_run_now": False,
            "external_release_now": False,
        }
    return {
        "task_id": "MCR3-FR",
        "title": "Core Mainline Selection Failure Repair",
        "selected_track": "mainline_selection",
        "scope": [
            "repair release-hold or module-review evidence",
            "do not run release gates while blocked",
            "do not mutate chart facts or promote pointers",
        ],
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []
