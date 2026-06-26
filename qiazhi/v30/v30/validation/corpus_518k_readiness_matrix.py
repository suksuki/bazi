from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from v30.config import V30Settings, load_settings
from v30.learning import DEFAULT_AUTO_TRAINING_FAMILIES
from v30.storage.artifacts import search_518k_validation_artifacts
from v30.validation.corpus_518k import run_518k_validation


READINESS_MATRIX_VERSION = "v30.518k_readiness_matrix.v1"
DEFAULT_READINESS_SHARD_ID = 7


def run_518k_readiness_matrix(
    *,
    sample_limit: int = 8,
    shard_id: int = DEFAULT_READINESS_SHARD_ID,
    shard_limit: int = 16,
    artifact_dir: str | Path | None = None,
    settings: V30Settings | None = None,
) -> dict[str, Any]:
    settings = settings or load_settings()
    sample = run_518k_validation(mode="sample", limit=sample_limit, artifact_dir=artifact_dir)
    shard = run_518k_validation(mode="shard", shard_id=shard_id, limit=shard_limit, artifact_dir=artifact_dir)
    return build_518k_readiness_matrix(
        sample_result=sample.model_dump(mode="json"),
        shard_result=shard.model_dump(mode="json"),
        settings=settings,
        artifact_dir=artifact_dir,
        sample_limit=sample_limit,
        shard_id=shard_id,
        shard_limit=shard_limit,
    )


def build_518k_readiness_matrix(
    *,
    sample_result: Mapping[str, Any],
    shard_result: Mapping[str, Any],
    settings: V30Settings | None = None,
    artifact_dir: str | Path | None = None,
    sample_limit: int = 8,
    shard_id: int = DEFAULT_READINESS_SHARD_ID,
    shard_limit: int = 16,
) -> dict[str, Any]:
    settings = settings or load_settings()
    sample = dict(sample_result)
    shard = dict(shard_result)
    full_boundary = _full_mode_boundary()
    artifact_summary = _artifact_summary(sample, shard)
    search_summary = _search_summary(settings=settings, artifact_dir=artifact_dir, sample_run_id=str(sample.get("run_id") or ""))
    coverage = _coverage_summary(sample, shard)
    candidate_matrix = _candidate_family_coverage_matrix(sample, shard)
    checks = _checks(
        sample=sample,
        shard=shard,
        full_boundary=full_boundary,
        artifact_summary=artifact_summary,
        search_summary=search_summary,
        coverage=coverage,
        candidate_matrix=candidate_matrix,
        sample_limit=sample_limit,
        shard_id=shard_id,
        shard_limit=shard_limit,
    )
    decision = _decision(checks)
    return {
        "version": READINESS_MATRIX_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["readiness_matrix_ready"] else "blocked",
        "decision": decision,
        "mode_readiness": {
            "sample": _mode_row(sample, expected_mode="sample", expected_case_count=sample_limit),
            "shard": _mode_row(shard, expected_mode="shard", expected_case_count=shard_limit),
            "full": full_boundary,
        },
        "corpus_mount_contract": _corpus_mount_contract(sample, shard),
        "artifact_persistence": artifact_summary,
        "artifact_search": search_summary,
        "coverage_summary": coverage,
        "candidate_family_coverage_matrix": candidate_matrix,
        "readiness_checks": checks,
        "policy_boundary": {
            "matrix_is_read_only": True,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "full_518k_run_allowed_by_default": False,
            "full_518k_requires_explicit_confirmation": True,
            "sample_and_shard_are_distribution_gates_not_destiny_truth": True,
            "boundary": "bt9_518k_readiness_matrix_documents_distribution_gate_readiness_without_running_full_518k",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "bt9_518k_readiness_matrix_keeps_full_mode_explicit_and_read_only",
    }


def _mode_row(result: Mapping[str, Any], *, expected_mode: str, expected_case_count: int) -> dict[str, Any]:
    coverage = result.get("coverage_metrics", {})
    coverage = coverage if isinstance(coverage, Mapping) else {}
    drift = result.get("drift_metrics", {})
    drift = drift if isinstance(drift, Mapping) else {}
    return {
        "mode": str(result.get("mode") or ""),
        "expected_mode": expected_mode,
        "run_id": str(result.get("run_id") or ""),
        "case_count": int(result.get("case_count", 0) or 0),
        "expected_case_count": expected_case_count,
        "promotion_signal": str(result.get("promotion_signal") or ""),
        "shard_ids": list(result.get("shard_ids", [])) if isinstance(result.get("shard_ids", []), list) else [],
        "artifact_uri": str(result.get("artifact_uri") or ""),
        "index_uri": str(result.get("index_uri") or ""),
        "index_entry_uri": str(result.get("index_entry_uri") or ""),
        "artifact_record_id": str(result.get("artifact_record_id") or ""),
        "artifact_search_backend": str(result.get("artifact_search_backend") or ""),
        "artifact_searchable": bool(result.get("artifact_searchable")),
        "coverage": {
            "question_recommendation_coverage": int(coverage.get("question_recommendation_coverage", 0) or 0),
            "krp_signal_coverage": int(coverage.get("krp_signal_coverage", 0) or 0),
            "model_signal_summary_coverage": int(coverage.get("model_signal_summary_coverage", 0) or 0),
            "interaction_state_coverage": int(coverage.get("interaction_state_coverage", 0) or 0),
            "visible_internal_next_question_split_count": int(coverage.get("visible_internal_next_question_split_count", 0) or 0),
            "calibration_probe_user_visible_count": int(coverage.get("calibration_probe_user_visible_count", 0) or 0),
        },
        "drift": {
            "unsupported_question_rate": float(drift.get("unsupported_question_rate", 1.0) or 0.0),
            "missing_model_signal_summary_rate": float(drift.get("missing_model_signal_summary_rate", 1.0) or 0.0),
            "missing_interaction_state_rate": float(drift.get("missing_interaction_state_rate", 1.0) or 0.0),
            "calibration_probe_user_visible_rate": float(drift.get("calibration_probe_user_visible_rate", 1.0) or 0.0),
        },
    }


def _full_mode_boundary() -> dict[str, Any]:
    try:
        run_518k_validation(mode="full", limit=1)
    except ValueError as exc:
        blocked_reason = str(exc)
    else:  # pragma: no cover - defensive regression guard.
        blocked_reason = ""
    return {
        "mode": "full",
        "status": "explicit_confirmation_required" if blocked_reason else "unexpectedly_allowed",
        "run_executed": False,
        "confirm_full_required": True,
        "blocked_reason": blocked_reason,
        "default_limit": 518_400,
        "major_node_only": True,
        "boundary": "full_518k_validation_requires_confirm_full_true_and_is_not_a_default_local_test",
    }


def _artifact_summary(sample: Mapping[str, Any], shard: Mapping[str, Any]) -> dict[str, Any]:
    rows = [_artifact_row(sample), _artifact_row(shard)]
    return {
        "artifact_count": sum(1 for row in rows if row["artifact_exists"]),
        "index_count": sum(1 for row in rows if row["index_exists"] and row["index_entry_exists"]),
        "record_id_count": sum(1 for row in rows if row["artifact_record_id"]),
        "rows": rows,
        "boundary": "518k_artifacts_are_validation_evidence_not_policy_pointer_writes",
    }


def _artifact_row(result: Mapping[str, Any]) -> dict[str, Any]:
    artifact_uri = str(result.get("artifact_uri") or "")
    index_uri = str(result.get("index_uri") or "")
    entry_uri = str(result.get("index_entry_uri") or "")
    return {
        "mode": str(result.get("mode") or ""),
        "run_id": str(result.get("run_id") or ""),
        "artifact_uri": artifact_uri,
        "artifact_exists": bool(artifact_uri and Path(artifact_uri).exists()),
        "index_uri": index_uri,
        "index_exists": bool(index_uri and Path(index_uri).exists()),
        "index_entry_uri": entry_uri,
        "index_entry_exists": bool(entry_uri and Path(entry_uri).exists()),
        "artifact_record_id": str(result.get("artifact_record_id") or ""),
        "artifact_search_backend": str(result.get("artifact_search_backend") or ""),
        "artifact_searchable": bool(result.get("artifact_searchable")),
    }


def _search_summary(
    *,
    settings: V30Settings,
    artifact_dir: str | Path | None,
    sample_run_id: str,
) -> dict[str, Any]:
    result = search_518k_validation_artifacts(
        settings=settings,
        mode="sample",
        run_id=sample_run_id,
        limit=5,
        artifact_dir=artifact_dir,
    )
    return {
        "backend": result.backend,
        "searchable": result.searchable,
        "fallback_used": result.fallback_used,
        "count": result.count,
        "artifact_record_ids": [row.artifact_record_id for row in result.artifacts],
        "boundary": "518k_artifact_search_uses_postgres_when_available_or_json_fallback_without_blocking_readiness",
    }


def _coverage_summary(sample: Mapping[str, Any], shard: Mapping[str, Any]) -> dict[str, Any]:
    sample_row = _mode_row(sample, expected_mode="sample", expected_case_count=int(sample.get("case_count", 0) or 0))
    shard_row = _mode_row(shard, expected_mode="shard", expected_case_count=int(shard.get("case_count", 0) or 0))
    total_cases = sample_row["case_count"] + shard_row["case_count"]
    return {
        "sample_case_count": sample_row["case_count"],
        "shard_case_count": shard_row["case_count"],
        "total_checked_case_count": total_cases,
        "question_recommendation_coverage": sample_row["coverage"]["question_recommendation_coverage"] + shard_row["coverage"]["question_recommendation_coverage"],
        "krp_signal_coverage": sample_row["coverage"]["krp_signal_coverage"] + shard_row["coverage"]["krp_signal_coverage"],
        "model_signal_summary_coverage": sample_row["coverage"]["model_signal_summary_coverage"] + shard_row["coverage"]["model_signal_summary_coverage"],
        "interaction_state_coverage": sample_row["coverage"]["interaction_state_coverage"] + shard_row["coverage"]["interaction_state_coverage"],
        "calibration_probe_user_visible_count": sample_row["coverage"]["calibration_probe_user_visible_count"] + shard_row["coverage"]["calibration_probe_user_visible_count"],
    }


def _corpus_mount_contract(sample: Mapping[str, Any], shard: Mapping[str, Any]) -> dict[str, Any]:
    corpus_versions = sorted({str(row.get("corpus_version") or "") for row in (sample, shard) if row.get("corpus_version")})
    return {
        "generated_contract_available": "v30.generated_518k_contract.v1" in corpus_versions,
        "external_source_supported": True,
        "supported_external_formats": ["jsonl", "csv"],
        "full_corpus_mount_required_for_full_mode": True,
        "sample_and_shard_can_use_generated_contract": True,
        "corpus_versions": corpus_versions,
        "boundary": "corpus_mount_contract_separates_generated_contract_checks_from_external_full_corpus_mount",
    }


def _candidate_family_coverage_matrix(sample: Mapping[str, Any], shard: Mapping[str, Any]) -> list[dict[str, Any]]:
    sample_ready = str(sample.get("promotion_signal") or "") == "eligible"
    shard_ready = str(shard.get("promotion_signal") or "") == "eligible"
    rows = []
    for family in DEFAULT_AUTO_TRAINING_FAMILIES:
        rows.append(
            {
                "family": family,
                "requires_synthetic_all": True,
                "requires_518k_sample": True,
                "requires_518k_shard_before_release": True,
                "sample_ready": sample_ready,
                "shard_ready": shard_ready,
                "full_518k_required_by_default": False,
                "pointer_promotion_allowed_by_matrix": False,
                "boundary": "candidate_family_coverage_matrix_documents_required_distribution_gates_not_pointer_promotion",
            }
        )
    return rows


def _checks(
    *,
    sample: Mapping[str, Any],
    shard: Mapping[str, Any],
    full_boundary: Mapping[str, Any],
    artifact_summary: Mapping[str, Any],
    search_summary: Mapping[str, Any],
    coverage: Mapping[str, Any],
    candidate_matrix: list[Mapping[str, Any]],
    sample_limit: int,
    shard_id: int,
    shard_limit: int,
) -> list[dict[str, Any]]:
    sample_row = _mode_row(sample, expected_mode="sample", expected_case_count=sample_limit)
    shard_row = _mode_row(shard, expected_mode="shard", expected_case_count=shard_limit)
    return [
        {
            "check_id": "sample_mode_distribution_gate_ready",
            "passed": sample_row["mode"] == "sample" and sample_row["case_count"] == sample_limit and sample_row["promotion_signal"] == "eligible",
            "expected": "sample mode runs the requested lightweight distribution gate and is eligible",
        },
        {
            "check_id": "shard_mode_distribution_gate_ready",
            "passed": shard_row["mode"] == "shard" and shard_row["case_count"] == shard_limit and shard_row["shard_ids"] == [shard_id] and shard_row["promotion_signal"] == "eligible",
            "expected": "shard mode targets the selected shard and is eligible",
        },
        {
            "check_id": "full_mode_requires_explicit_confirmation",
            "passed": full_boundary.get("status") == "explicit_confirmation_required" and full_boundary.get("run_executed") is False,
            "expected": "full 518K cannot run without explicit confirm_full=True",
        },
        {
            "check_id": "runtime_coverage_has_no_projection_leak",
            "passed": (
                int(coverage["total_checked_case_count"]) == sample_limit + shard_limit
                and int(coverage["question_recommendation_coverage"]) == int(coverage["total_checked_case_count"])
                and int(coverage["krp_signal_coverage"]) == int(coverage["total_checked_case_count"])
                and int(coverage["model_signal_summary_coverage"]) == int(coverage["total_checked_case_count"])
                and int(coverage["interaction_state_coverage"]) == int(coverage["total_checked_case_count"])
                and int(coverage["calibration_probe_user_visible_count"]) == 0
            ),
            "expected": "sample+shard cover runtime signals and do not leak calibration probes as user-visible next questions",
        },
        {
            "check_id": "artifact_and_index_persistence_ready",
            "passed": artifact_summary["artifact_count"] >= 2 and artifact_summary["index_count"] >= 2 and artifact_summary["record_id_count"] >= 2,
            "expected": "sample and shard write artifacts, index entries, and artifact record ids",
        },
        {
            "check_id": "artifact_search_fallback_or_postgres_ready",
            "passed": search_summary["backend"] in {"json_fallback", "postgres", "postgres_unavailable"} and int(search_summary["count"]) >= 1,
            "expected": "artifact search can retrieve sample evidence through Postgres or JSON fallback",
        },
        {
            "check_id": "candidate_family_distribution_matrix_ready",
            "passed": (
                {str(row["family"]) for row in candidate_matrix} == set(DEFAULT_AUTO_TRAINING_FAMILIES)
                and all(row["sample_ready"] and row["shard_ready"] for row in candidate_matrix)
                and all(not row["pointer_promotion_allowed_by_matrix"] for row in candidate_matrix)
            ),
            "expected": "core policy candidate families have documented 518K sample/shard gate coverage without pointer promotion",
        },
    ]


def _decision(checks: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if not row.get("passed")]
    ready = not failed
    return {
        "readiness_matrix_ready": ready,
        "decision_status": "bt9_518k_readiness_matrix_ready" if ready else "bt9_518k_readiness_matrix_blocked",
        "check_count": len(checks),
        "passed_check_count": sum(1 for row in checks if row.get("passed")),
        "failed_check_ids": failed,
        "validation_518k_completion": 95 if ready else 85,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "blockers": ["518k_readiness_matrix_checks_failed"] if failed else [],
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["readiness_matrix_ready"]:
        return {
            "task_id": "BT10",
            "title": "Unified Brain / Training / Synthetic Closeout",
            "selected_track": "brain_training_synthetic_completion",
            "scope": [
                "summarize BT1-BT9 readiness",
                "run targeted support-system closeout checks",
                "keep full pytest and full 518K explicit release gates",
            ],
        }
    return {
        "task_id": "BT9-FR",
        "title": "518K Readiness Matrix Failure Review",
        "selected_track": "brain_training_synthetic_completion",
        "scope": [
            "inspect failed readiness matrix checks",
            "repair sample/shard/artifact/search readiness",
            "do not run full 518K by default",
        ],
    }
