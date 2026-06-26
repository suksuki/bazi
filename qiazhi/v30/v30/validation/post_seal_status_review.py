from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


POST_SEAL_STATUS_REVIEW_VERSION = "v30.post_seal_status_review.v1"


CORE_MODULES = [
    ("M1_birthinput_chart_facts", "BirthInput and deterministic chart facts", 95, "phase_sealed"),
    ("M2_base_fact_explanation", "Base Bazi fact explanation layer", 92, "phase_sealed"),
    ("M3_evidence_rule_structure_spine", "Evidence / rule / knowledge / structure spine", 96, "phase_sealed"),
    ("M4_ten_god_energy_model", "Ten-god energy model", 88, "phase_sealed"),
    ("M5_ranked_decisions", "Strength / structure / useful-god ranked decisions", 88, "phase_sealed"),
    ("M6_practical_reading_output", "Practical reading output", 85, "phase_sealed"),
    ("M7_real_case_calibration", "Core validation / real-case calibration", 90, "phase_sealed"),
    ("M8_api_projection", "User presentation / API projection", 90, "phase_sealed"),
]

SUPPORT_TRACKS = [
    ("runtime_api_ui_spine", "Runtime/API/UI spine", 97, "release_gated"),
    ("training_synthetic_release_gates", "Training/synthetic/release gates", 97, "release_gated"),
    ("post_seal_release_hardening", "Post-seal release hardening", 100, "release_candidate_ready"),
    ("role_session_foundation", "Role/session foundation", 70, "bounded_foundation"),
    ("llm_expression", "LLM expression", 72, "bounded_optional"),
    ("production_replay_metadata", "Production real replay metadata", 80, "store_search_active"),
]

COMPLETED_TASKS = [
    ("R1", "Release Gate And Contract Hardening", "completed", "post_seal_contracts"),
    ("R2", "Production API Smoke And Customer Loop Contract", "completed", "production_api_smoke"),
    ("R3", "Minimal Durable Session / Read-History Hardening", "completed", "reading_history_visibility"),
    ("R4", "Bounded LLM Live Smoke And Failure Telemetry", "completed", "llm_live_smoke"),
    ("R5", "Production Replay Metadata Preparation", "completed", "production_replay_metadata"),
    ("R6", "Observability And Admin Artifact Review", "completed", "release_artifact_review"),
    ("R7", "Post-Seal Status Review And Next Mainline Selection", "completed", "post_seal_status_review"),
    ("R8", "Metadata-Safe Production Replay Intake", "completed", "production_replay_intake"),
    ("R9", "Metadata-Safe Replay Store And Search", "completed", "production_replay_store"),
    ("R10", "Post-Seal Release Candidate Review", "completed", "release_candidate_review"),
    ("R11", "Standard Release-Candidate Gate", "completed", "release_candidate_gate_review"),
    ("R12", "Release Boundary Finalization Review", "completed", "release_boundary_finalization"),
]


def build_post_seal_status_review(*, release_artifact_review: dict[str, Any] | None = None) -> dict[str, Any]:
    release_artifact_review = release_artifact_review if isinstance(release_artifact_review, dict) else {}
    core_rows = [_module_row(row) for row in CORE_MODULES]
    support_rows = [_track_row(row) for row in SUPPORT_TRACKS]
    completed = [
        {
            "task_id": task_id,
            "title": title,
            "status": status,
            "primary_evidence": evidence,
        }
        for task_id, title, status, evidence in COMPLETED_TASKS
    ]
    next_selection = _next_selection()
    return {
        "version": POST_SEAL_STATUS_REVIEW_VERSION,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "status": "ready_for_next_mainline",
        "core_module_summary": {
            "module_count": len(core_rows),
            "phase_sealed_count": sum(1 for row in core_rows if row["status"] == "phase_sealed"),
            "average_completion": _average(row["completion"] for row in core_rows),
            "modules": core_rows,
        },
        "support_track_summary": {
            "track_count": len(support_rows),
            "average_completion": _average(row["completion"] for row in support_rows),
            "tracks": support_rows,
        },
        "completed_post_seal_tasks": completed,
        "release_evidence_summary": _release_evidence_summary(release_artifact_review),
        "risk_register": _risk_register(),
        "reopen_rules": {
            "core_modules_reopen_only_on_validation_failure": True,
            "no_private_content_into_chart_facts": True,
            "full_pytest_and_full_518k_reserved_for_release_boundary": True,
            "training_signals_do_not_mutate_deterministic_facts": True,
        },
        "next_mainline_selection": next_selection,
        "deferred_tracks": _deferred_tracks(),
        "boundary": "post_seal_status_review_selects_next_mainline_without_mutating_policy_or_chart_facts",
    }


def _module_row(row: tuple[str, str, int, str]) -> dict[str, Any]:
    module_id, title, completion, status = row
    return {
        "module_id": module_id,
        "title": title,
        "completion": completion,
        "status": status,
        "reopen_policy": "only_with_concrete_validation_failure",
    }


def _track_row(row: tuple[str, str, int, str]) -> dict[str, Any]:
    track_id, title, completion, status = row
    return {
        "track_id": track_id,
        "title": title,
        "completion": completion,
        "status": status,
    }


def _release_evidence_summary(release_artifact_review: dict[str, Any]) -> dict[str, Any]:
    return {
        "release_artifact_review_version": str(release_artifact_review.get("version") or ""),
        "release_artifact_review_status": str(release_artifact_review.get("status") or ""),
        "check_count": int(release_artifact_review.get("check_count", 0) or 0),
        "admin_review_sections": release_artifact_review.get("admin_review_sections", [])
        if isinstance(release_artifact_review.get("admin_review_sections"), list) else [],
        "artifact_count": len(release_artifact_review.get("artifact_index", []))
        if isinstance(release_artifact_review.get("artifact_index"), list) else 0,
        "policy_promotion_allowed": bool(
            (release_artifact_review.get("promotion_review", {}) if isinstance(release_artifact_review.get("promotion_review"), dict) else {}).get("policy_promotion_allowed")
        ),
        "boundary": "release_evidence_is_read_only_status_input",
    }


def _risk_register() -> list[dict[str, Any]]:
    return [
        {
            "risk_id": "production_replay_store_needs_real_rows",
            "severity": "medium",
            "track": "production_replay_metadata",
            "current_completion": 80,
            "mitigation": "R11 standard gate passed; real row ingestion remains a metadata-only calibration expansion after release-boundary review.",
        },
        {
            "risk_id": "llm_provider_not_required_for_chart_facts",
            "severity": "low",
            "track": "llm_expression",
            "current_completion": 72,
            "mitigation": "Keep rule answer primary; only expand provider taxonomy after live provider evidence exists.",
        },
        {
            "risk_id": "role_session_is_not_full_auth",
            "severity": "low",
            "track": "role_session_foundation",
            "current_completion": 70,
            "mitigation": "Keep actor/session hooks as owner scopes until product requirements demand durable auth.",
        },
        {
            "risk_id": "full_corpus_cost",
            "severity": "medium",
            "track": "validation_cost",
            "current_completion": 85,
            "mitigation": "Use sample/shard gates for normal work; reserve full 518K for production release boundaries.",
        },
    ]


def _next_selection() -> dict[str, Any]:
    return {
        "task_id": "R13",
        "title": "External Release Dry Run And Full Pytest Decision",
        "selected_track": "external_release_boundary",
        "selection_reason": (
            "R12 finalized the internal release candidate boundary. The next step is an explicit external release "
            "dry run decision, including whether to run full pytest before external release."
        ),
        "scope": [
            "run or explicitly defer full pytest for external release",
            "review policy pointer promotion as a manual operator action",
            "keep full 518K separate unless external production release requires it",
            "do not promote policy pointers without explicit operator approval",
        ],
        "explicit_non_goals": [
            "no M1-M8 speculative reopening",
            "no full login system",
            "no live LLM requirement",
            "no policy pointer promotion",
            "no full 518K by default",
        ],
        "recommended_gate": [
            "python3 -m compileall -q v30",
            "pytest -q tests/unit/test_release_boundary_finalization.py tests/unit/test_post_seal_status_review.py",
            "python3 scripts/run_release_boundary_finalization.py --sample-limit 8 --shard-id 7 --shard-limit 16",
        ],
    }


def _deferred_tracks() -> list[dict[str, Any]]:
    return [
        {
            "track": "durable_auth",
            "reason": "Role/session hooks already satisfy current owner-scope projection; full auth is product scope.",
        },
        {
            "track": "live_llm_provider_expansion",
            "reason": "LLM is bounded expression only and cannot generate chart facts; wait for live provider failures.",
        },
        {
            "track": "core_module_rework",
            "reason": "M1-M8 are phase sealed; reopen only after concrete validation failure.",
        },
        {
            "track": "ui_expansion",
            "reason": "Current product principle is simple UI with strong modules; next evidence gap is replay intake.",
        },
    ]


def _average(values: Any) -> float:
    rows = [float(value) for value in values]
    return round(sum(rows) / max(1, len(rows)), 1)
