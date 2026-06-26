from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from v20.corpus.full_precompute import preview_full_precompute_batch
from v20.learning.arbitration_loop import build_arbitration_loop_report, write_arbitration_loop_artifact
from v20.learning.answer_governance_training import (
    build_answer_governance_training_report,
    write_answer_governance_training_artifact,
)
from v20.learning.decision_training import build_decision_training_plan
from v20.learning.decision_registry_iteration import (
    build_decision_registry_iteration_report,
    write_decision_registry_iteration_artifact,
)
from v20.learning.dynamic_decision_training import (
    run_dynamic_decision_training_batch,
    write_dynamic_decision_training_artifact,
)
from v20.decision.knowledge_bridge import build_knowledge_rule_review_overlay
from v20.learning.knowledge_rule_review_overlay import write_knowledge_rule_review_overlay_artifact
from v20.learning.orchestrator_memory_training import (
    build_orchestrator_memory_training_report,
    write_orchestrator_memory_training_artifact,
)
from v20.learning.orchestrator_policy_candidates import (
    build_orchestrator_policy_candidate_report,
    write_orchestrator_policy_candidate_artifact,
)
from v20.learning.orchestrator_policy_observability_training import (
    build_policy_observability_training_report,
    write_policy_observability_training_artifact,
)
from v20.learning.orchestrator_policy_replay import (
    build_orchestrator_policy_replay_report,
    write_orchestrator_policy_replay_artifact,
)
from v20.learning.orchestrator_policy_versioning import (
    build_orchestrator_policy_version_candidate,
    write_orchestrator_policy_version_candidate_artifact,
)
from v20.learning.practitioner_calibration_training import (
    build_practitioner_calibration_training_report,
    write_practitioner_calibration_training_artifact,
)
from v20.learning.question_dag_training import build_question_dag_training_report
from v20.learning.question_dag_policy_replay import (
    build_question_dag_policy_replay_report,
    write_question_dag_policy_replay_artifact,
)
from v20.learning.question_dag_policy_promotion import build_question_dag_policy_promotion_gate
from v20.learning.question_review_training import (
    build_question_review_training_report,
    write_question_review_training_artifact,
)
from v20.learning.question_ranking_learning import (
    build_question_ranking_learning_report,
    write_question_ranking_learning_artifact,
)
from v20.learning.question_source_training import (
    build_question_source_training_report,
    write_question_source_training_artifact,
)
from v20.learning.role_interaction_training import build_role_interaction_training_report
from v20.learning.role_question_click_training import (
    build_role_question_click_training_report,
    write_role_question_click_training_artifact,
)
from v20.learning.role_view_policy_candidates import (
    build_role_view_policy_candidate_report,
    write_role_view_policy_candidate_artifact,
)
from v20.learning.role_view_policy_calibration import build_role_view_policy_calibration_report
from v20.learning.role_view_policy_promotion import build_role_view_policy_promotion_gate
from v20.learning.role_view_policy_replay import (
    build_role_view_policy_replay_report,
    write_role_view_policy_replay_artifact,
)
from v20.learning.rule_subcondition_split import (
    build_rule_subcondition_split_report,
    write_rule_subcondition_split_artifact,
)
from v20.learning.rule_replay_eval import build_rule_replay_eval_report, write_rule_replay_eval_artifact
from v20.storage.local_jsonl import local_jsonl_store_from_env
from v20.validation.synthetic_replay import run_synthetic_bazi_replay
from v20.validation.synthetic_schema import synthetic_bazi_coverage_report
from v20.validation.next_question_synthetic import (
    build_next_question_synthetic_validation_report,
    write_next_question_synthetic_validation_artifact,
)
from v20.validation.rule_portrait_batch import run_rule_portrait_batch, write_rule_portrait_batch_artifact
from v20.validation.rule_synthetic import (
    RULE_SYNTHETIC_CASES,
    build_rule_synthetic_training_report,
    write_rule_synthetic_training_artifact,
)

ProgressCallback = Callable[[str], None]


def run_training_iteration(
    *,
    write: bool = False,
    include_rule_batch: bool = False,
    include_replay_eval: bool = False,
    include_knowledge_overlay: bool = False,
    include_rule_iteration: bool = False,
    dynamic_case_limit: int = 12,
    rule_iteration_limit: int = 120,
    rule_synthetic_limit: int = 12,
    knowledge_overlay_limit: int = 24,
    synthetic_replay_limit: int = 1,
    corpus_preview_limit: int = 0,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    phases = [
        "dynamic_decision_training",
        "practitioner_calibration_training",
        "orchestrator_memory_training",
        "orchestrator_policy_observability",
        "question_source_training",
        "orchestrator_policy_candidates",
        "orchestrator_policy_version_candidate",
        "orchestrator_policy_replay",
        "arbitration_loop",
        "question_ranking_training",
        "synthetic_bazi_coverage",
        "synthetic_bazi_replay",
        "answer_governance_training",
        "question_review_training",
        "question_dag_training",
        "question_dag_policy_replay",
        "question_dag_policy_promotion_gate",
        "next_question_synthetic_validation",
        "role_interaction_training",
        "role_question_click_training",
        "role_view_policy_candidates",
        "role_view_policy_replay",
        "role_view_policy_calibration",
        "role_view_policy_promotion_gate",
        "rule_synthetic_training",
        "knowledge_rule_review_overlay",
        "rule_subcondition_split",
        *(("rule_replay_eval",) if include_replay_eval else ()),
        "decision_registry_iteration",
        *(("rule_portrait_batch",) if include_rule_batch else ()),
        *(("corpus_preview",) if corpus_preview_limit > 0 else ()),
        "decision_training_plan",
    ]
    phase_count = len(phases)
    phase_index = 0

    def emit_phase(name: str, message: str = "") -> None:
        nonlocal phase_index
        phase_index += 1
        suffix = f": {message}" if message else ""
        _emit(progress, _progress_line(phase_index, phase_count, f"{name}{suffix}"))

    results: dict[str, object] = {}
    dynamic_kwargs = {"max_cases": max(0, dynamic_case_limit)}
    rule_iteration_kwargs = {"limit": max(0, rule_iteration_limit)}
    rule_synthetic_cases = RULE_SYNTHETIC_CASES[:rule_synthetic_limit] if rule_synthetic_limit > 0 else RULE_SYNTHETIC_CASES

    emit_phase("dynamic_decision_training")
    results["dynamic_decision_training"] = (
        write_dynamic_decision_training_artifact(progress=progress, **dynamic_kwargs)
        if write
        else run_dynamic_decision_training_batch(progress=progress, **dynamic_kwargs)
    )

    emit_phase("practitioner_calibration_training")
    results["practitioner_calibration_training"] = (
        write_practitioner_calibration_training_artifact(progress=progress)
        if write
        else build_practitioner_calibration_training_report(progress=progress)
    )

    emit_phase("orchestrator_memory_training")
    results["orchestrator_memory_training"] = (
        write_orchestrator_memory_training_artifact(progress=progress)
        if write
        else build_orchestrator_memory_training_report(progress=progress)
    )

    emit_phase("orchestrator_policy_observability")
    results["orchestrator_policy_observability"] = (
        write_policy_observability_training_artifact(progress=progress)
        if write
        else build_policy_observability_training_report(progress=progress)
    )

    emit_phase("question_source_training")
    results["question_source_training"] = (
        write_question_source_training_artifact(progress=progress)
        if write
        else build_question_source_training_report(progress=progress)
    )

    emit_phase("orchestrator_policy_candidates")
    results["orchestrator_policy_candidates"] = (
        write_orchestrator_policy_candidate_artifact(
            policy_observability_report=results["orchestrator_policy_observability"],
            question_source_training_report=results.get("question_source_training", {}),
            progress=progress,
        )
        if write
        else build_orchestrator_policy_candidate_report(
            memory_training_report=results["orchestrator_memory_training"],
            policy_observability_report=results["orchestrator_policy_observability"],
            question_source_training_report=results.get("question_source_training", {}),
            progress=progress,
        )
    )

    emit_phase("orchestrator_policy_version_candidate")
    results["orchestrator_policy_version_candidate"] = (
        write_orchestrator_policy_version_candidate_artifact(progress=progress)
        if write
        else build_orchestrator_policy_version_candidate(candidate_report=results["orchestrator_policy_candidates"], progress=progress)
    )

    emit_phase("orchestrator_policy_replay")
    results["orchestrator_policy_replay"] = (
        write_orchestrator_policy_replay_artifact(progress=progress)
        if write
        else build_orchestrator_policy_replay_report(policy_version_candidate=results["orchestrator_policy_version_candidate"], progress=progress)
    )

    emit_phase("arbitration_loop")
    results["arbitration_loop"] = (
        write_arbitration_loop_artifact(progress=progress)
        if write
        else build_arbitration_loop_report(progress=progress)
    )

    emit_phase("question_ranking_training")
    results["question_ranking_training"] = (
        write_question_ranking_learning_artifact()
        if write
        else build_question_ranking_learning_report()
    )

    emit_phase("synthetic_bazi_coverage")
    results["synthetic_bazi_coverage"] = synthetic_bazi_coverage_report()

    emit_phase("synthetic_bazi_replay", f"limit={max(0, synthetic_replay_limit)}")
    results["synthetic_bazi_replay"] = run_synthetic_bazi_replay(max_cases=max(0, synthetic_replay_limit))

    emit_phase("answer_governance_training")
    results["answer_governance_training"] = (
        write_answer_governance_training_artifact(
            replay_report=results["synthetic_bazi_replay"]
            if isinstance(results["synthetic_bazi_replay"], dict)
            else None,
            max_cases=max(0, synthetic_replay_limit),
        )
        if write
        else build_answer_governance_training_report(
            replay_report=results["synthetic_bazi_replay"]
            if isinstance(results["synthetic_bazi_replay"], dict)
            else None,
            max_cases=max(0, synthetic_replay_limit),
        )
    )

    emit_phase("question_review_training")
    results["question_review_training"] = (
        write_question_review_training_artifact()
        if write
        else build_question_review_training_report()
    )

    emit_phase("question_dag_training")
    results["question_dag_training"] = build_question_dag_training_report(
        question_review_training_report=results["question_review_training"]
        if isinstance(results["question_review_training"], dict)
        else None
    )

    emit_phase("question_dag_policy_replay")
    results["question_dag_policy_replay"] = (
        write_question_dag_policy_replay_artifact()
        if write
        else build_question_dag_policy_replay_report(
            question_dag_training_report=results["question_dag_training"]
            if isinstance(results["question_dag_training"], dict)
            else None
        )
    )

    emit_phase("question_dag_policy_promotion_gate")
    results["question_dag_policy_promotion_gate"] = build_question_dag_policy_promotion_gate(
        replay_report=results["question_dag_policy_replay"]
        if isinstance(results["question_dag_policy_replay"], dict)
        else None
    )

    emit_phase("next_question_synthetic_validation")
    results["next_question_synthetic_validation"] = (
        write_next_question_synthetic_validation_artifact()
        if write
        else build_next_question_synthetic_validation_report()
    )

    emit_phase("role_interaction_training")
    results["role_interaction_training"] = build_role_interaction_training_report()

    emit_phase("role_question_click_training")
    results["role_question_click_training"] = (
        write_role_question_click_training_artifact()
        if write
        else build_role_question_click_training_report()
    )

    emit_phase("role_view_policy_candidates")
    results["role_view_policy_candidates"] = (
        write_role_view_policy_candidate_artifact()
        if write
        else build_role_view_policy_candidate_report(
            click_training_report=results["role_question_click_training"]
            if isinstance(results["role_question_click_training"], dict)
            else None
        )
    )

    emit_phase("role_view_policy_replay")
    results["role_view_policy_replay"] = (
        write_role_view_policy_replay_artifact()
        if write
        else build_role_view_policy_replay_report(
            policy_candidate_report=results["role_view_policy_candidates"]
            if isinstance(results["role_view_policy_candidates"], dict)
            else None
        )
    )

    emit_phase("role_view_policy_calibration")
    results["role_view_policy_calibration"] = build_role_view_policy_calibration_report(
        click_training_report=results["role_question_click_training"]
        if isinstance(results["role_question_click_training"], dict)
        else None,
        replay_report=results["role_view_policy_replay"]
        if isinstance(results["role_view_policy_replay"], dict)
        else None,
    )

    emit_phase("role_view_policy_promotion_gate")
    results["role_view_policy_promotion_gate"] = build_role_view_policy_promotion_gate(
        replay_report=results["role_view_policy_replay"]
        if isinstance(results["role_view_policy_replay"], dict)
        else None,
        calibration_report=results["role_view_policy_calibration"]
        if isinstance(results["role_view_policy_calibration"], dict)
        else None,
    )

    emit_phase("rule_synthetic_training", f"limit={max(0, rule_synthetic_limit)}")
    results["rule_synthetic_training"] = (
        write_rule_synthetic_training_artifact(cases=rule_synthetic_cases)
        if write
        else build_rule_synthetic_training_report(cases=rule_synthetic_cases)
    )

    emit_phase("knowledge_rule_review_overlay", f"limit={max(0, knowledge_overlay_limit)}")
    if include_knowledge_overlay:
        results["knowledge_rule_review_overlay"] = (
            write_knowledge_rule_review_overlay_artifact(
                limit=max(0, knowledge_overlay_limit),
                synthetic_case_limit=max(0, rule_synthetic_limit),
                progress=progress,
            )
            if write
            else build_knowledge_rule_review_overlay(
                limit=max(0, knowledge_overlay_limit),
                synthetic_case_limit=max(0, rule_synthetic_limit),
            )
        )
    else:
        results["knowledge_rule_review_overlay"] = {
            "version": "v20.knowledge_rule_review_overlay_skip.v1",
            "status": "skipped",
            "reason": "heavy_phase_requires_include_knowledge_overlay",
            "runtime_mutation": False,
            "guardrails": [
                "HEAVY_KNOWLEDGE_OVERLAY_REQUIRES_EXPLICIT_SCRIPT_FLAG",
                "FAST_ITERATION_DEFAULT_REMAINS_LIGHTWEIGHT",
            ],
        }

    emit_phase("rule_subcondition_split")
    if include_rule_iteration:
        results["rule_subcondition_split"] = (
            write_rule_subcondition_split_artifact(progress=progress, **rule_iteration_kwargs)
            if write
            else build_rule_subcondition_split_report(progress=progress, **rule_iteration_kwargs)
        )
    else:
        results["rule_subcondition_split"] = {
            "version": "v20.rule_subcondition_split_skip.v1",
            "status": "skipped",
            "reason": "heavy_phase_requires_include_rule_iteration",
            "runtime_mutation": False,
            "guardrails": [
                "RULE_SUBCONDITION_SPLIT_REQUIRES_EXPLICIT_SCRIPT_FLAG",
                "FAST_ITERATION_DEFAULT_REMAINS_LIGHTWEIGHT",
            ],
        }

    if include_replay_eval:
        emit_phase("rule_replay_eval")
        results["rule_replay_eval"] = (
            write_rule_replay_eval_artifact(progress=progress, **rule_iteration_kwargs)
            if write
            else build_rule_replay_eval_report(progress=progress, **rule_iteration_kwargs)
        )

    emit_phase("decision_registry_iteration")
    if include_rule_iteration:
        results["decision_registry_iteration"] = (
            write_decision_registry_iteration_artifact(progress=progress, **rule_iteration_kwargs)
            if write
            else build_decision_registry_iteration_report(progress=progress, **rule_iteration_kwargs)
        )
    else:
        results["decision_registry_iteration"] = {
            "version": "v20.decision_registry_iteration_skip.v1",
            "status": "skipped",
            "reason": "heavy_phase_requires_include_rule_iteration",
            "runtime_mutation": False,
            "guardrails": [
                "DECISION_REGISTRY_ITERATION_REQUIRES_EXPLICIT_SCRIPT_FLAG",
                "FAST_ITERATION_DEFAULT_REMAINS_LIGHTWEIGHT",
            ],
        }

    if include_rule_batch:
        emit_phase("rule_portrait_batch")
        results["rule_portrait_batch"] = (
            write_rule_portrait_batch_artifact(progress=progress)
            if write
            else run_rule_portrait_batch(progress=progress)
        )

    if corpus_preview_limit > 0:
        emit_phase("corpus_preview", f"limit={corpus_preview_limit}")
        results["corpus_preview"] = preview_full_precompute_batch(start=0, limit=corpus_preview_limit)

    emit_phase("decision_training_plan")
    results["decision_training_plan"] = build_decision_training_plan()

    failures = _collect_failures(results)
    quality_findings = _collect_quality_findings(results)
    orchestrator_policy_learning_summary = _orchestrator_policy_learning_summary(
        results.get("orchestrator_policy_observability", {})
    )
    report = {
        "version": "v20.training_iteration_report.v1",
        "status": "pass" if not failures else "fail",
        "quality_status": "needs_review" if quality_findings else "clean",
        "ok": not failures,
        "phase_count": phase_count,
        "write": write,
        "results": results,
        "failure_count": len(failures),
        "quality_finding_count": len(quality_findings),
        "orchestrator_policy_learning_summary": orchestrator_policy_learning_summary,
        "failures": failures,
        "quality_findings": quality_findings,
        "runtime_mutation": write,
        "guardrails": [
            "TRAINING_ITERATION_IS_SCRIPT_ONLY",
            "NO_USER_UI_TRAINING_SURFACE",
            "ACTIVE_RULE_ITERATION",
            "HEAVY_CORPUS_WORK_REQUIRES_EXPLICIT_SCRIPT_FLAG",
            "ORCHESTRATOR_POLICY_RECOMMENDATIONS_ARE_READ_ONLY",
        ],
    }
    if write:
        return _write_training_iteration_artifact(report, output_dir=output_dir)
    return report


def read_training_iteration_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "iteration") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.training_iteration_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def _write_training_iteration_artifact(report: dict[str, object], *, output_dir: Path | None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    directory = output_dir or runtime_dir / "training" / "iteration"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"training_iteration_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.training_iteration_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "quality_status": report["quality_status"],
        "failure_count": report["failure_count"],
        "quality_finding_count": report["quality_finding_count"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "ACTIVE_RULE_ITERATION",
        ],
    }


def _collect_failures(results: dict[str, object]) -> list[str]:
    failures: list[str] = []
    for key, payload in results.items():
        if not isinstance(payload, dict):
            continue
        if payload.get("status") == "blocked" and key.endswith("_promotion_gate"):
            continue
        if payload.get("status") in {"fail", "blocked"} or payload.get("ok") is False:
            failures.append(f"{key}:status:{payload.get('status', '')}")
        failures.extend(f"{key}:{item}" for item in payload.get("failures", ()) if str(item))
    return failures


def _collect_quality_findings(results: dict[str, object]) -> list[str]:
    findings: list[str] = []
    for key, payload in results.items():
        if isinstance(payload, dict):
            if payload.get("status") == "blocked" and key.endswith("_promotion_gate"):
                findings.append(f"{key}:promotion_blocked:{payload.get('blocking_gate', 'not_ready')}")
            findings.extend(f"{key}:{item}" for item in payload.get("quality_findings", ()) if str(item))
    return findings


def _orchestrator_policy_learning_summary(policy_report: object) -> dict[str, object]:
    if not isinstance(policy_report, dict):
        policy_report = {}
    trend = policy_report.get("trend_summary", {})
    if not isinstance(trend, dict):
        trend = {}
    recommendations = policy_report.get("strategy_recommendations", ())
    if not isinstance(recommendations, list):
        recommendations = []
    timeline = policy_report.get("version_switch_timeline", ())
    if not isinstance(timeline, list):
        timeline = []
    return {
        "version": "v20.training_iteration_orchestrator_policy_learning_summary.v1",
        "status": str(trend.get("status", "")) or str(policy_report.get("status", "")) or "not_enough_data",
        "observation_count": int(policy_report.get("observation_count", 0) or 0),
        "candidate_consumed_ratio": float(policy_report.get("candidate_consumed_ratio", 0) or 0),
        "fallback_ratio": float(policy_report.get("fallback_ratio", 0) or 0),
        "dominant_active_policy_version": str(trend.get("dominant_active_policy_version", "")),
        "recommendation_count": len(recommendations),
        "recommendation_keys": [
            str(row.get("recommendation_key", ""))
            for row in recommendations
            if isinstance(row, dict) and row.get("recommendation_key")
        ][:8],
        "version_switch_event_count": len(timeline),
        "latest_switch_event": timeline[0] if timeline else {},
        "runtime_mutation": False,
        "guardrails": [
            "SUMMARY_READS_POLICY_OBSERVABILITY_ONLY",
            "NO_POLICY_WRITE_FROM_TRAINING_SUMMARY",
            "FAST_TRACK_REMAINS_ROLLBACKABLE",
        ],
    }


def _progress_line(index: int, total: int, label: str) -> str:
    width = 20
    filled = round(width * index / total) if total else width
    bar = "#" * filled + "-" * (width - filled)
    pct = round(index * 100 / total) if total else 100
    return f"[{bar}] {pct:3d}% ({index}/{total}) {label}"


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)
