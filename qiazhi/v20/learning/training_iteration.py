from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from v20.corpus.full_precompute import preview_full_precompute_batch
from v20.learning.arbitration_loop import build_arbitration_loop_report, write_arbitration_loop_artifact
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
from v20.learning.practitioner_calibration_training import (
    build_practitioner_calibration_training_report,
    write_practitioner_calibration_training_artifact,
)
from v20.learning.question_ranking_learning import (
    build_question_ranking_learning_report,
    write_question_ranking_learning_artifact,
)
from v20.learning.rule_subcondition_split import (
    build_rule_subcondition_split_report,
    write_rule_subcondition_split_artifact,
)
from v20.learning.rule_replay_eval import build_rule_replay_eval_report, write_rule_replay_eval_artifact
from v20.storage.local_jsonl import local_jsonl_store_from_env
from v20.validation.rule_portrait_batch import run_rule_portrait_batch, write_rule_portrait_batch_artifact
from v20.validation.rule_synthetic import build_rule_synthetic_training_report, write_rule_synthetic_training_artifact

ProgressCallback = Callable[[str], None]


def run_training_iteration(
    *,
    write: bool = False,
    include_rule_batch: bool = False,
    include_replay_eval: bool = False,
    dynamic_case_limit: int = 12,
    rule_iteration_limit: int = 120,
    corpus_preview_limit: int = 0,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    phases = [
        "dynamic_decision_training",
        "practitioner_calibration_training",
        "arbitration_loop",
        "question_ranking_training",
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

    emit_phase("rule_synthetic_training")
    results["rule_synthetic_training"] = (
        write_rule_synthetic_training_artifact()
        if write
        else build_rule_synthetic_training_report()
    )

    emit_phase("knowledge_rule_review_overlay")
    results["knowledge_rule_review_overlay"] = (
        write_knowledge_rule_review_overlay_artifact(progress=progress)
        if write
        else build_knowledge_rule_review_overlay()
    )

    emit_phase("rule_subcondition_split")
    results["rule_subcondition_split"] = (
        write_rule_subcondition_split_artifact(progress=progress, **rule_iteration_kwargs)
        if write
        else build_rule_subcondition_split_report(progress=progress, **rule_iteration_kwargs)
    )

    if include_replay_eval:
        emit_phase("rule_replay_eval")
        results["rule_replay_eval"] = (
            write_rule_replay_eval_artifact(progress=progress, **rule_iteration_kwargs)
            if write
            else build_rule_replay_eval_report(progress=progress, **rule_iteration_kwargs)
        )

    emit_phase("decision_registry_iteration")
    results["decision_registry_iteration"] = (
        write_decision_registry_iteration_artifact(progress=progress, **rule_iteration_kwargs)
        if write
        else build_decision_registry_iteration_report(progress=progress, **rule_iteration_kwargs)
    )

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
        "failures": failures,
        "quality_findings": quality_findings,
        "runtime_mutation": write,
        "guardrails": [
            "TRAINING_ITERATION_IS_SCRIPT_ONLY",
            "NO_USER_UI_TRAINING_SURFACE",
            "ACTIVE_RULE_ITERATION",
            "HEAVY_CORPUS_WORK_REQUIRES_EXPLICIT_SCRIPT_FLAG",
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
        if payload.get("status") in {"fail", "blocked"} or payload.get("ok") is False:
            failures.append(f"{key}:status:{payload.get('status', '')}")
        failures.extend(f"{key}:{item}" for item in payload.get("failures", ()) if str(item))
    return failures


def _collect_quality_findings(results: dict[str, object]) -> list[str]:
    findings: list[str] = []
    for key, payload in results.items():
        if isinstance(payload, dict):
            findings.extend(f"{key}:{item}" for item in payload.get("quality_findings", ()) if str(item))
    return findings


def _progress_line(index: int, total: int, label: str) -> str:
    width = 20
    filled = round(width * index / total) if total else width
    bar = "#" * filled + "-" * (width - filled)
    pct = round(index * 100 / total) if total else 100
    return f"[{bar}] {pct:3d}% ({index}/{total}) {label}"


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)
