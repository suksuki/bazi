from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from v30.config import V30Settings
from v30.learning import DEFAULT_AUTO_TRAINING_FAMILIES, run_auto_apply_training
from v30.policy import RuntimePointerStore
from v30.policy.lineage import build_promotion_lineage
from v30.policy.runtime_pointer import PolicyFamily
from v30.validation.central_brain_failure_routing import run_central_brain_failure_routing


TRAINING_SYSTEM_CLOSEOUT_VERSION = "v30.training_system_closeout.v1"
CORE_POLICY_FAMILIES: tuple[PolicyFamily, ...] = DEFAULT_AUTO_TRAINING_FAMILIES
FUTURE_POLICY_FAMILIES: tuple[PolicyFamily, ...] = (
    "answer_policy",
    "presentation_policy",
    "portrait_policy",
    "hidden_factor_policy",
)


def run_training_system_closeout(*, training_run_id: str = "bt4-closeout") -> dict[str, Any]:
    bt3 = run_central_brain_failure_routing()
    with tempfile.TemporaryDirectory(prefix="v30-bt4-closeout-") as temp_root:
        root = Path(temp_root)
        settings = V30Settings(
            database_url=None,
            redis_url=None,
            redis_prefix="v30",
            runtime_dir=root / ".runtime",
            host="127.0.0.1",
            port=9030,
            env="bt4-closeout",
            repository="memory",
        )
        store = RuntimePointerStore(settings)
        result = run_auto_apply_training(
            training_run_id=training_run_id,
            store=store,
            validation_artifact_dir=root / "validation" / "518k",
        )
        artifacts = {
            family: store.load_active_artifact(family).model_dump(mode="json")
            for family in CORE_POLICY_FAMILIES
        }
        pointers = {
            family: store.load_pointer(family).model_dump(mode="json")
            for family in CORE_POLICY_FAMILIES
        }
        lineage = {
            family: build_promotion_lineage(
                family=family,
                settings=settings,
                store=store,
            ).model_dump(mode="json")
            for family in CORE_POLICY_FAMILIES
        }
        return build_training_system_closeout(
            bt3_failure_routing=bt3,
            auto_training_result=result.model_dump(mode="json"),
            policy_artifacts=artifacts,
            runtime_pointers=pointers,
            promotion_lineage=lineage,
        )


def build_training_system_closeout(
    *,
    bt3_failure_routing: Mapping[str, Any],
    auto_training_result: Mapping[str, Any],
    policy_artifacts: Mapping[str, Mapping[str, Any]] | None = None,
    runtime_pointers: Mapping[str, Mapping[str, Any]] | None = None,
    promotion_lineage: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc)
    artifacts = {str(key): dict(value) for key, value in (policy_artifacts or {}).items()}
    pointers = {str(key): dict(value) for key, value in (runtime_pointers or {}).items()}
    lineage = {str(key): dict(value) for key, value in (promotion_lineage or {}).items()}
    result = dict(auto_training_result)
    bt3_summary = _bt3_summary(bt3_failure_routing)
    training_summary = _training_summary(result)
    artifact_summary = _artifact_summary(artifacts)
    pointer_summary = _pointer_summary(pointers)
    lineage_summary = _lineage_summary(lineage)
    future_boundary = _future_policy_boundary(result, artifacts, pointers)
    checks = _closeout_checks(
        bt3_summary=bt3_summary,
        training_summary=training_summary,
        artifact_summary=artifact_summary,
        pointer_summary=pointer_summary,
        lineage_summary=lineage_summary,
        future_boundary=future_boundary,
    )
    decision = _decision(checks)
    return {
        "version": TRAINING_SYSTEM_CLOSEOUT_VERSION,
        "executed_at": executed_at.isoformat(),
        "status": "completed" if decision["training_system_closeout_ready"] else "blocked",
        "decision": decision,
        "bt3_summary": bt3_summary,
        "training_summary": training_summary,
        "artifact_summary": artifact_summary,
        "runtime_pointer_summary": pointer_summary,
        "promotion_lineage_summary": lineage_summary,
        "future_policy_boundary": future_boundary,
        "closeout_checks": checks,
        "policy_boundary": {
            "closeout_admin_endpoint_read_only": True,
            "runtime_mutation_allowed": False,
            "chart_fact_mutation_allowed": False,
            "training_signal_may_change_chart_facts": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "future_policy_family_promotion_allowed_by_default": False,
            "boundary": "bt4_closeout_validates_training_loop_without_authorizing_chart_fact_or_future_family_mutation",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "bt4_training_system_closeout_gate_is_validation_evidence_not_user_facing_calculation_logic",
    }


def _bt3_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, Mapping) else {}
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "brain_failure_routing_ready": bool(decision.get("brain_failure_routing_ready")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
    }


def _training_summary(result: Mapping[str, Any]) -> dict[str, Any]:
    families = [str(row) for row in result.get("families", []) if str(row)]
    candidates = [row for row in result.get("candidates", []) if isinstance(row, Mapping)]
    promotions = [row for row in result.get("promotions", []) if isinstance(row, Mapping)]
    metrics = result.get("metrics", {})
    metrics = metrics if isinstance(metrics, Mapping) else {}
    return {
        "training_run_id": str(result.get("training_run_id") or ""),
        "status": str(result.get("status") or ""),
        "auto_apply": bool(result.get("auto_apply", False)),
        "families": families,
        "candidate_count": int(metrics.get("candidate_count", len(candidates)) or 0),
        "promoted_count": int(metrics.get("promoted_count", 0) or 0),
        "failed_count": int(metrics.get("failed_count", 0) or 0),
        "training_signal_count": int(metrics.get("training_signal_count", 0) or 0),
        "synthetic_signal_case_count": int(metrics.get("synthetic_signal_case_count", 0) or 0),
        "candidate_families": sorted({str(row.get("family") or "") for row in candidates if row.get("family")}),
        "promotion_families": sorted({str(row.get("family") or "") for row in promotions if row.get("family")}),
        "promoted_artifact_ids": {
            str(row.get("family")): str(row.get("artifact_id") or "")
            for row in promotions
            if row.get("promoted") and row.get("family")
        },
        "failure_count": len(result.get("failures", []) if isinstance(result.get("failures", []), list) else []),
        "active_policy_versions": dict(result.get("active_policy_versions", {}))
        if isinstance(result.get("active_policy_versions", {}), Mapping)
        else {},
    }


def _artifact_summary(artifacts: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    rows = []
    for family in CORE_POLICY_FAMILIES:
        artifact = artifacts.get(family, {})
        payload = artifact.get("payload", {}) if isinstance(artifact.get("payload", {}), Mapping) else {}
        validation = artifact.get("validation_summary", {})
        validation = validation if isinstance(validation, Mapping) else {}
        metrics = artifact.get("metrics", {})
        metrics = metrics if isinstance(metrics, Mapping) else {}
        training_signals = payload.get("training_signals", [])
        comparison = validation.get("question_policy_comparison", {})
        rows.append(
            {
                "family": family,
                "artifact_id": str(artifact.get("artifact_id") or ""),
                "candidate_id": str(artifact.get("candidate_id") or ""),
                "payload_mode": str(payload.get("mode") or ""),
                "has_training_signals": bool(training_signals),
                "training_signal_count": len(training_signals) if isinstance(training_signals, list) else 0,
                "has_validation_replay": "synthetic" in validation and "corpus_518k_sample" in validation,
                "synthetic_case_count": int(metrics.get("synthetic_case_count", 0) or 0),
                "synthetic_passed_count": int(metrics.get("synthetic_passed_count", 0) or 0),
                "corpus_518k_sample_case_count": int(metrics.get("corpus_518k_sample_case_count", 0) or 0),
                "corpus_518k_promotion_signal": str(metrics.get("corpus_518k_promotion_signal") or ""),
                "has_question_policy_comparison": family == "question_policy" and isinstance(comparison, Mapping) and bool(comparison),
                "weight_key_count": len(payload.get("weights", {})) if isinstance(payload.get("weights", {}), Mapping) else 0,
            }
        )
    return {
        "families": rows,
        "artifact_count": sum(1 for row in rows if row["artifact_id"]),
        "validation_replay_complete_count": sum(1 for row in rows if row["has_validation_replay"]),
        "training_signal_artifact_count": sum(1 for row in rows if row["has_training_signals"]),
        "question_policy_comparison_ready": any(row["has_question_policy_comparison"] for row in rows),
    }


def _pointer_summary(pointers: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    rows = []
    for family in CORE_POLICY_FAMILIES:
        pointer = pointers.get(family, {})
        rows.append(
            {
                "family": family,
                "active_artifact_id": str(pointer.get("active_artifact_id") or ""),
                "previous_artifact_id": str(pointer.get("previous_artifact_id") or ""),
                "validation_run_id": str(pointer.get("validation_run_id") or ""),
                "status": str(pointer.get("status") or ""),
                "promotion_reason": str(pointer.get("promotion_reason") or ""),
                "has_rollback_pointer": bool(pointer.get("rollback_pointer")),
                "updated_by": str(pointer.get("updated_by") or ""),
            }
        )
    return {
        "families": rows,
        "active_pointer_count": sum(1 for row in rows if row["status"] == "active" and row["active_artifact_id"]),
        "rollback_pointer_count": sum(1 for row in rows if row["has_rollback_pointer"]),
        "validation_run_count": sum(1 for row in rows if row["validation_run_id"]),
    }


def _lineage_summary(lineage: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    rows = []
    for family in CORE_POLICY_FAMILIES:
        graph = lineage.get(family, {})
        rows.append(
            {
                "family": family,
                "lineage_id": str(graph.get("lineage_id") or ""),
                "active_artifact_id": str(graph.get("active_artifact_id") or ""),
                "candidate_id": str(graph.get("candidate_id") or ""),
                "validation_artifact_count": len(graph.get("validation_artifacts", []))
                if isinstance(graph.get("validation_artifacts", []), list)
                else 0,
                "has_rollback_pointer": bool(graph.get("rollback_pointer")),
                "boundary_count": len(graph.get("boundaries", [])) if isinstance(graph.get("boundaries", []), list) else 0,
            }
        )
    return {
        "families": rows,
        "lineage_count": sum(1 for row in rows if row["lineage_id"]),
        "rollback_lineage_count": sum(1 for row in rows if row["has_rollback_pointer"]),
        "validation_artifact_lineage_count": sum(1 for row in rows if row["validation_artifact_count"] > 0),
    }


def _future_policy_boundary(
    result: Mapping[str, Any],
    artifacts: Mapping[str, Mapping[str, Any]],
    pointers: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    result_families = {str(row) for row in result.get("families", []) if str(row)}
    candidate_families = {
        str(row.get("family") or "")
        for row in result.get("candidates", [])
        if isinstance(row, Mapping) and row.get("family")
    }
    promoted_families = {
        str(row.get("family") or "")
        for row in result.get("promotions", [])
        if isinstance(row, Mapping) and row.get("promoted") and row.get("family")
    }
    observed_future = sorted(
        family
        for family in FUTURE_POLICY_FAMILIES
        if family in result_families or family in candidate_families or family in promoted_families or family in artifacts or family in pointers
    )
    return {
        "future_policy_families": list(FUTURE_POLICY_FAMILIES),
        "promoted_future_families": sorted(set(FUTURE_POLICY_FAMILIES) & promoted_families),
        "candidate_future_families": sorted(set(FUTURE_POLICY_FAMILIES) & candidate_families),
        "observed_future_families": observed_future,
        "future_families_promoted_by_default": bool(set(FUTURE_POLICY_FAMILIES) & promoted_families),
        "boundary": "answer_presentation_portrait_hidden_factor_policies_are_observed_or_candidate_only_until_explicit_promotion",
    }


def _closeout_checks(
    *,
    bt3_summary: Mapping[str, Any],
    training_summary: Mapping[str, Any],
    artifact_summary: Mapping[str, Any],
    pointer_summary: Mapping[str, Any],
    lineage_summary: Mapping[str, Any],
    future_boundary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    core_families = set(CORE_POLICY_FAMILIES)
    families = set(training_summary["families"])
    candidate_families = set(training_summary["candidate_families"])
    promotion_families = set(training_summary["promotion_families"])
    return [
        {
            "check_id": "bt3_failure_routing_ready",
            "passed": (
                bt3_summary["version"] == "v30.brain_failure_route.v1"
                and bt3_summary["brain_failure_routing_ready"]
                and bt3_summary["decision_status"] == "bt3_brain_failure_routing_ready"
            ),
            "expected": "BT3 failure routing is completed before training closeout",
        },
        {
            "check_id": "auto_training_applies_core_policy_families",
            "passed": (
                training_summary["status"] == "applied"
                and training_summary["auto_apply"]
                and families == core_families
                and candidate_families == core_families
                and promotion_families == core_families
                and training_summary["candidate_count"] == len(CORE_POLICY_FAMILIES)
                and training_summary["promoted_count"] == len(CORE_POLICY_FAMILIES)
                and training_summary["failed_count"] == 0
            ),
            "expected": "structure/mainline/question/rule candidates are all validated and promoted in the closeout store",
        },
        {
            "check_id": "training_signal_extraction_ready",
            "passed": (
                training_summary["training_signal_count"] >= 30
                and training_summary["synthetic_signal_case_count"] >= 90
                and artifact_summary["training_signal_artifact_count"] == len(CORE_POLICY_FAMILIES)
            ),
            "expected": "synthetic all produces broad training signals and embeds them in all core artifacts",
        },
        {
            "check_id": "validation_replay_artifacts_ready",
            "passed": (
                artifact_summary["artifact_count"] == len(CORE_POLICY_FAMILIES)
                and artifact_summary["validation_replay_complete_count"] == len(CORE_POLICY_FAMILIES)
            ),
            "expected": "each promoted artifact carries synthetic all and 518K sample validation replay",
        },
        {
            "check_id": "runtime_pointers_and_rollback_ready",
            "passed": (
                pointer_summary["active_pointer_count"] == len(CORE_POLICY_FAMILIES)
                and pointer_summary["rollback_pointer_count"] == len(CORE_POLICY_FAMILIES)
                and pointer_summary["validation_run_count"] == len(CORE_POLICY_FAMILIES)
            ),
            "expected": "runtime pointers are active and include validation and rollback metadata",
        },
        {
            "check_id": "question_comparison_and_lineage_ready",
            "passed": (
                artifact_summary["question_policy_comparison_ready"]
                and lineage_summary["lineage_count"] == len(CORE_POLICY_FAMILIES)
                and lineage_summary["rollback_lineage_count"] == len(CORE_POLICY_FAMILIES)
                and lineage_summary["validation_artifact_lineage_count"] >= 1
            ),
            "expected": "question comparison artifact and promotion lineage diagnostics are available",
        },
        {
            "check_id": "future_policy_families_not_promoted_by_default",
            "passed": not future_boundary["future_families_promoted_by_default"],
            "expected": "answer/presentation/portrait/hidden-factor policies stay observed or candidate-only by default",
        },
        {
            "check_id": "chart_fact_and_heavy_validation_boundaries_preserved",
            "passed": (
                not bt3_summary["chart_fact_mutation_allowed"]
                and not bt3_summary["full_pytest_required"]
                and not bt3_summary["full_518k_required"]
            ),
            "expected": "training closeout does not authorize chart fact mutation or default heavy gates",
        },
    ]


def _decision(checks: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if not row.get("passed")]
    ready = not failed
    return {
        "training_system_closeout_ready": ready,
        "decision_status": "bt4_training_system_closeout_ready" if ready else "bt4_training_system_closeout_blocked",
        "closeout_check_count": len(checks),
        "passed_closeout_check_count": sum(1 for row in checks if row.get("passed")),
        "failed_check_ids": failed,
        "training_completion": 97 if ready else 94,
        "blockers": ["training_system_closeout_checks_failed"] if failed else [],
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "rationale": (
            "Training system closeout is ready for the four core policy families with validation, artifacts, pointers, lineage, and rollback metadata."
            if ready
            else "BT4 cannot complete until training closeout blockers are repaired."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["training_system_closeout_ready"]:
        return {
            "task_id": "BT5",
            "title": "Failed Candidate Quarantine And Rollback Readiness",
            "selected_track": "brain_training_synthetic_completion",
            "scope": [
                "prove failed candidates are quarantined",
                "prove rollback metadata can restore previous pointers",
                "keep chart facts and release gates separate from training",
            ],
        }
    return {
        "task_id": "BT4-FR",
        "title": "Training System Closeout Failure Review",
        "selected_track": "brain_training_synthetic_completion",
        "scope": [
            "inspect failed BT4 closeout checks",
            "repair training signal, artifact, pointer, lineage, or rollback gaps",
            "keep future policy family promotion disabled while blocked",
        ],
    }
