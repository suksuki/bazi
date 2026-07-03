from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_job(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_job(path: Path, job: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _update_job(path: Path, **updates: Any) -> dict[str, Any]:
    job = _read_job(path)
    job.update(updates)
    _write_job(path, job)
    return job


def _append_event(path: Path, event: dict[str, Any], *, limit: int = 60) -> dict[str, Any]:
    job = _read_job(path)
    events = list(job.get("progress_events") or [])
    events.append(event)
    job["progress_events"] = events[-limit:]
    _write_job(path, job)
    return job


def _fail_job(path: Path, exc: BaseException) -> int:
    job = _read_job(path)
    job.update(
        {
            "status": "failed",
            "error": str(exc),
            "failures": [str(exc)],
            "finished_at": _utc_now(),
        }
    )
    if not job.get("progress_percent"):
        job["progress_percent"] = 1
    _write_job(path, job)
    return 1


def _auto_training_run_summary(result: object) -> dict[str, Any]:
    data = result.model_dump(mode="json") if hasattr(result, "model_dump") else {}
    promotions = data.get("promotions", [])
    compact_promotions: list[dict[str, Any]] = []
    if isinstance(promotions, list):
        for row in promotions:
            if not isinstance(row, dict):
                continue
            compact_promotions.append(
                {
                    "family": row.get("family"),
                    "artifact_id": row.get("artifact_id"),
                    "previous_artifact_id": row.get("previous_artifact_id"),
                    "promoted": row.get("promoted"),
                    "pointer_status": row.get("pointer_status"),
                    "failures": row.get("failures", []),
                }
            )
    return {
        "version": data.get("version", "v30.auto_training_run_summary.v1"),
        "training_run_id": data.get("training_run_id"),
        "families": data.get("families", []),
        "started_at": data.get("started_at"),
        "finished_at": data.get("finished_at"),
        "auto_apply": data.get("auto_apply"),
        "status": data.get("status"),
        "promotions": compact_promotions,
        "active_policy_versions": data.get("active_policy_versions", {}),
        "policy_application": data.get("policy_application", {}),
        "training_signal_summary": data.get("training_signal_summary", {}),
        "metrics": data.get("metrics", {}),
        "failures": data.get("failures", []),
    }


def _training_validation_summary(payload: dict[str, Any]) -> dict[str, Any]:
    results = payload.get("results")
    failed_preview: list[dict[str, Any]] = []
    if isinstance(results, list):
        for row in results:
            if not isinstance(row, dict):
                continue
            if row.get("passed") is True or str(row.get("status") or "").lower() in {"passed", "completed"}:
                continue
            failed_preview.append(
                {
                    "case_id": row.get("case_id") or row.get("id") or row.get("name") or "",
                    "status": row.get("status") or "",
                    "error": row.get("error") or row.get("reason") or "",
                }
            )
            if len(failed_preview) >= 5:
                break
    return {
        "version": "v30.training_validation_summary.v1",
        "suite_id": payload.get("suite_id") or "",
        "passed": bool(payload.get("passed")),
        "case_count": payload.get("case_count") or 0,
        "passed_count": payload.get("passed_count") or 0,
        "failed_count": payload.get("failed_count") or 0,
        "result_count": len(results) if isinstance(results, list) else 0,
        "failed_preview": failed_preview,
    }


def _policy_lineage_summary_payload() -> dict[str, Any]:
    from v30.config import load_settings
    from v30.policy import build_promotion_lineage

    settings = load_settings()
    families = ("structure_policy", "mainline_policy", "question_policy", "rule_policy")
    rows = [
        build_promotion_lineage(family=family, settings=settings).model_dump(mode="json")
        for family in families
    ]
    return {
        "version": "v30.admin.policy_lineage_summary.v1",
        "families": rows,
        "rollback_supported": True,
        "chart_fact_mutation_allowed": False,
        "boundary": "policy_lineage_summary_reads_runtime_pointers_and_supports_pointer_rollback_without_mutating_chart_facts",
    }


def _run_auto_apply(path: Path) -> int:
    from v30.learning import DEFAULT_AUTO_TRAINING_FAMILIES, run_auto_apply_training

    job = _update_job(
        path,
        status="running",
        started_at=_utc_now(),
        current_step="started",
        progress_percent=1,
        worker_pid=os.getpid(),
        worker_mode="isolated_process",
    )
    config = dict(job.get("config") or {})
    families = tuple(config.get("families") or DEFAULT_AUTO_TRAINING_FAMILIES)
    training_run_id = str(config.get("training_run_id") or "")
    promotion_validation_mode = str(config.get("promotion_validation_mode") or "strict")

    def _progress(event: dict[str, object]) -> None:
        current = _read_job(path)
        events = list(current.get("progress_events") or [])
        events.append(event)
        current["progress_events"] = events[-40:]
        current["current_step"] = str(event.get("step") or current.get("current_step") or "running")
        current["progress_percent"] = int(event.get("progress_percent") or current.get("progress_percent") or 0)
        current["message"] = str(event.get("message") or "")
        current["completed_steps"] = int(event.get("completed_steps") or current.get("completed_steps") or 0)
        current["total_steps"] = int(event.get("total_steps") or current.get("total_steps") or len(families))
        _write_job(path, current)

    result = run_auto_apply_training(
        families=families,
        training_run_id=training_run_id,
        promotion_validation_mode=promotion_validation_mode,
        progress_callback=_progress,
    )
    summary = _auto_training_run_summary(result)
    status = "completed" if summary.get("status") == "applied" else "failed"
    _update_job(
        path,
        status=status,
        current_step="completed",
        finished_at=_utc_now(),
        progress_percent=100,
        completed_steps=len(families),
        total_steps=len(families),
        training_run=summary,
        metrics=summary.get("metrics", {}),
        policy_application=summary.get("policy_application", {}),
        training_signal_summary=summary.get("training_signal_summary", {}),
        active_policy_versions=summary.get("active_policy_versions", {}),
        failures=summary.get("failures", []),
    )
    return 0 if status == "completed" else 1


def _m3_step_result(name: str, payload: object) -> dict[str, Any]:
    if name == "m3_snapshot" and isinstance(payload, dict):
        inventory = payload.get("inventory", {})
        db_write = payload.get("db_write", {})
        synthetic = payload.get("synthetic_validation", {})
        return {
            "step": name,
            "snapshot_id": payload.get("snapshot_id"),
            "artifact_uri": payload.get("artifact_uri"),
            "krp_unit_count": inventory.get("krp_unit_count") if isinstance(inventory, dict) else None,
            "rule_spec_count": inventory.get("rule_spec_count") if isinstance(inventory, dict) else None,
            "portrait_asset_count": inventory.get("portrait_asset_count") if isinstance(inventory, dict) else None,
            "synthetic": {
                "passed": synthetic.get("passed") if isinstance(synthetic, dict) else None,
                "passed_count": synthetic.get("passed_count") if isinstance(synthetic, dict) else None,
                "case_count": synthetic.get("case_count") if isinstance(synthetic, dict) else None,
            },
            "db_write": db_write if isinstance(db_write, dict) else {},
        }
    if name in {"m3_synthetic", "training_pipeline"} and hasattr(payload, "model_dump"):
        data = payload.model_dump(mode="json")
        return {
            "step": name,
            "suite_id": data.get("suite_id"),
            "passed": data.get("passed"),
            "passed_count": data.get("passed_count"),
            "case_count": data.get("case_count"),
        }
    if name in {"518k_sample", "518k_shard"} and hasattr(payload, "model_dump"):
        data = payload.model_dump(mode="json")
        return {
            "step": name,
            "run_id": data.get("run_id"),
            "mode": data.get("mode"),
            "promotion_signal": data.get("promotion_signal"),
            "case_count": data.get("case_count"),
            "shard_ids": data.get("shard_ids"),
            "artifact_uri": data.get("artifact_uri"),
            "index_uri": data.get("index_uri"),
            "artifact_record_id": data.get("artifact_record_id"),
            "artifact_search_backend": data.get("artifact_search_backend"),
        }
    if name == "518k_readiness_matrix" and isinstance(payload, dict):
        checks = payload.get("checks", [])
        return {
            "step": name,
            "version": payload.get("version"),
            "passed": payload.get("passed"),
            "check_count": len(checks) if isinstance(checks, list) else None,
        }
    return {"step": name, "summary": str(payload)[:500]}


@contextmanager
def _local_validation_env():
    keys = ("V30_ADMIN_CONFIG_PATH", "V30_REPOSITORY", "V30_DATABASE_URL")
    previous = {key: os.environ.get(key) for key in keys}
    runtime_dir = os.environ.get("V30_RUNTIME_DIR", str(ROOT / ".runtime"))
    os.environ["V30_ADMIN_CONFIG_PATH"] = str(Path(runtime_dir) / "training" / "m3_background_no_db_admin_config.json")
    os.environ["V30_REPOSITORY"] = "local_json"
    os.environ.pop("V30_DATABASE_URL", None)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _run_orchestrator(path: Path) -> int:
    job = _update_job(
        path,
        status="running",
        started_at=_utc_now(),
        current_step="started",
        progress_percent=1,
        worker_pid=os.getpid(),
        worker_mode="isolated_process",
    )
    config = dict(job.get("config") or {})
    plan_id = str(job.get("plan_id") or config.get("plan_id") or "")
    rerun_steps = [str(row) for row in config.get("rerun_steps", [])] if isinstance(config.get("rerun_steps"), list) else []
    if plan_id == "central_brain_auto_apply":
        return _run_orchestrator_auto_apply(path, config)
    if plan_id == "central_brain_phase2_training":
        return _run_orchestrator_phase2(path, config)
    if plan_id == "evaluation_spine_quality_gate":
        return _run_orchestrator_evaluation_spine(path)
    if plan_id == "m3_518k_validation":
        return _run_orchestrator_m3(path, config, rerun_steps)
    if plan_id == "quick_validation_only":
        return _run_orchestrator_quick(path, rerun_steps)
    raise ValueError(f"unsupported training orchestrator plan: {plan_id}")


def _run_orchestrator_auto_apply(path: Path, config: dict[str, Any]) -> int:
    from v30.learning import DEFAULT_AUTO_TRAINING_FAMILIES, run_auto_apply_training

    families = tuple(config.get("families") or DEFAULT_AUTO_TRAINING_FAMILIES)
    training_run_id = str(config.get("training_run_id") or "")
    promotion_validation_mode = str(config.get("promotion_validation_mode") or "strict")
    step_results: list[dict[str, Any]] = []
    _update_job(path, current_step="preflight_lineage", progress_percent=8, completed_steps=0)
    preflight = _policy_lineage_summary_payload()
    step_results.append({"step": "preflight_lineage", "status": "completed", "family_count": len(preflight["families"])})
    _update_job(path, lineage_before=preflight, step_results=step_results)

    def _progress(event: dict[str, object]) -> None:
        inner_percent = int(event.get("progress_percent") or 0)
        outer_percent = 15 + int(inner_percent * 0.65)
        _update_job(
            path,
            current_step=f"auto_apply_training:{event.get('step') or 'running'}",
            progress_percent=max(15, min(80, outer_percent)),
        )
        _append_event(path, event)

    result = run_auto_apply_training(
        families=families,
        training_run_id=training_run_id,
        promotion_validation_mode=promotion_validation_mode,
        progress_callback=_progress,
    )
    training_run = _auto_training_run_summary(result)
    metrics = training_run.get("metrics") if isinstance(training_run.get("metrics"), dict) else {}
    step_results.append(
        {
            "step": "auto_apply_training",
            "status": training_run.get("status"),
            "promoted_count": metrics.get("promoted_count"),
        }
    )
    _update_job(
        path,
        training_run=training_run,
        step_results=step_results,
        completed_steps=2,
        current_step="post_training_lineage",
        progress_percent=86,
    )
    post_lineage = _policy_lineage_summary_payload()
    step_results.append({"step": "post_training_lineage", "status": "completed", "family_count": len(post_lineage["families"])})
    history = {"version": "v30.admin.auto_apply_training_history_snapshot.v1", "jobs": []}
    step_results.append({"step": "history_snapshot", "status": "completed", "job_count": 0})
    status = "completed" if training_run.get("status") == "applied" else "failed"
    _update_job(
        path,
        lineage_summary=post_lineage,
        history_snapshot=history,
        step_results=step_results,
        completed_steps=4,
        current_step="completed",
        progress_percent=100,
        status=status,
        finished_at=_utc_now(),
        failures=training_run.get("failures", []),
    )
    return 0 if status == "completed" else 1


def _run_orchestrator_quick(path: Path, rerun_steps: list[str]) -> int:
    from v30.validation import run_synthetic_tier

    quick_steps = ["training_pipeline_synthetic", "lineage_snapshot"]
    if rerun_steps:
        quick_steps = [row for row in quick_steps if row in set(rerun_steps)]
        if not quick_steps:
            raise ValueError(f"no runnable failed steps for quick_validation_only: {','.join(rerun_steps)}")
    step_results: list[dict[str, Any]] = []
    validation_payload: dict[str, Any] = {}
    if "training_pipeline_synthetic" in quick_steps:
        _update_job(path, current_step="training_pipeline_synthetic", progress_percent=25, completed_steps=0)
        validation = run_synthetic_tier("training_pipeline")
        validation_payload = _training_validation_summary(validation.model_dump(mode="json"))
        step_results.append(
            {
                "step": "training_pipeline_synthetic",
                "status": "passed" if validation_payload.get("passed") else "failed",
                "passed_count": validation_payload.get("passed_count"),
                "case_count": validation_payload.get("case_count"),
            }
        )
    lineage: dict[str, Any] = {}
    if "lineage_snapshot" in quick_steps:
        lineage = _policy_lineage_summary_payload()
        step_results.append({"step": "lineage_snapshot", "status": "completed", "family_count": len(lineage["families"])})
    status = "completed" if not validation_payload or validation_payload.get("passed") else "failed"
    _update_job(
        path,
        validation_result=validation_payload,
        lineage_summary=lineage,
        step_results=step_results,
        completed_steps=len(quick_steps),
        current_step="completed",
        progress_percent=100,
        status=status,
        finished_at=_utc_now(),
    )
    return 0 if status == "completed" else 1


def _run_orchestrator_m3(path: Path, config: dict[str, Any], rerun_steps: list[str]) -> int:
    from v30.validation import run_518k_readiness_matrix, run_518k_validation, run_m3_core_spine_snapshot, run_synthetic_tier

    sample_limit = int(config.get("sample_limit") or 8)
    shard_id = int(config.get("shard_id") or 7)
    shard_limit = int(config.get("shard_limit") or 16)
    with _local_validation_env():
        m3_steps: list[tuple[str, Any]] = [
            (
                "m3_snapshot",
                lambda: run_m3_core_spine_snapshot(
                    include_518k_sample=False,
                    sample_limit=sample_limit,
                    write_db=False,
                    artifact_dir=".runtime/validation/m3",
                ),
            ),
            ("m3_synthetic", lambda: run_synthetic_tier("m3_core_spine")),
            ("training_pipeline", lambda: run_synthetic_tier("training_pipeline")),
            ("518k_sample", lambda: run_518k_validation(mode="sample", limit=sample_limit)),
        ]
        if config.get("include_shard"):
            m3_steps.append(("518k_shard", lambda: run_518k_validation(mode="shard", shard_id=shard_id, limit=shard_limit)))
        if config.get("include_readiness_matrix"):
            m3_steps.append(
                (
                    "518k_readiness_matrix",
                    lambda: run_518k_readiness_matrix(sample_limit=sample_limit, shard_id=shard_id, shard_limit=shard_limit),
                )
            )
        if rerun_steps:
            m3_steps = [row for row in m3_steps if row[0] in set(rerun_steps)]
            if not m3_steps:
                raise ValueError(f"no runnable failed steps for m3_518k_validation: {','.join(rerun_steps)}")
        total_steps = len(m3_steps)
        step_results: list[dict[str, Any]] = []
        passed = True
        for index, (step_name, runner) in enumerate(m3_steps):
            _update_job(
                path,
                current_step=step_name,
                progress_percent=max(5, int((index / total_steps) * 94)),
                completed_steps=index,
            )
            summary = _m3_step_result(step_name, runner())
            step_results.append(summary)
            if summary.get("passed") is False:
                passed = False
            if step_name in {"518k_sample", "518k_shard"} and summary.get("promotion_signal") not in {"eligible", None}:
                passed = False
            _update_job(
                path,
                step_results=step_results,
                completed_steps=index + 1,
                progress_percent=int(((index + 1) / total_steps) * 100),
            )
    lineage = _policy_lineage_summary_payload()
    status = "completed" if passed else "failed"
    _update_job(
        path,
        lineage_summary=lineage,
        step_results=step_results,
        completed_steps=total_steps,
        current_step="completed",
        progress_percent=100,
        status=status,
        finished_at=_utc_now(),
        m3_518k_result={
            "version": "v30.training_orchestrator.m3_518k_result.v1",
            "passed": passed,
            "sample_limit": sample_limit,
            "include_shard": bool(config.get("include_shard")),
            "include_readiness_matrix": bool(config.get("include_readiness_matrix")),
            "step_count": total_steps,
        },
        failures=[] if passed else ["m3_518k_validation_failed"],
    )
    return 0 if status == "completed" else 1


def _run_orchestrator_phase2(path: Path, config: dict[str, Any]) -> int:
    from v30.brain.policy_optimizer import optimize_central_brain_policy
    from v30.brain.training_examples import BrainTrainingExampleStore
    from v30.config import load_settings
    from v30.validation import run_518k_validation
    from v30.validation.central_brain_phase2_distribution_gate import build_central_brain_phase2_distribution_gate
    from v30.validation.central_brain_phase2_replay_gate import build_central_brain_phase2_replay_gate

    settings = load_settings()
    store = BrainTrainingExampleStore(settings.runtime_dir)
    sample_limit = int(config.get("sample_limit") or 1)
    shard_id = int(config.get("shard_id") or 7)
    shard_limit = int(config.get("shard_limit") or 1)
    step_results: list[dict[str, Any]] = []
    total_steps = 5
    _update_job(path, current_step="brain_example_summary", progress_percent=5, completed_steps=0)
    raw_summary = store.summary(split="raw")
    step_results.append(
        {
            "step": "brain_example_summary",
            "status": "completed",
            "example_count": raw_summary.get("example_count"),
            "answered_count": raw_summary.get("answered_count"),
        }
    )
    _update_job(path, step_results=step_results, completed_steps=1, progress_percent=18)
    _update_job(path, current_step="build_training_splits", progress_percent=22)
    split_manifest = store.build_splits(seed=20260628, train_ratio=0.7, validation_ratio=0.2)
    step_results.append(
        {
            "step": "build_training_splits",
            "status": "completed",
            "raw_count": split_manifest.get("raw_count"),
            "splits": split_manifest.get("splits", {}),
        }
    )
    _update_job(path, step_results=step_results, completed_steps=2, progress_percent=36)
    _update_job(path, current_step="optimize_policy_candidate", progress_percent=42)
    train_examples = store.read(split="train", limit=100000)
    candidate = optimize_central_brain_policy(train_examples, min_examples=3, max_delta=0.06)
    step_results.append(
        {
            "step": "optimize_policy_candidate",
            "status": candidate.get("status"),
            "promotion_signal": candidate.get("promotion_signal"),
            "example_count": candidate.get("example_count"),
        }
    )
    _update_job(path, phase2_candidate_policy=candidate, step_results=step_results, completed_steps=3, progress_percent=56)
    _update_job(path, current_step="synthetic_replay_gate", progress_percent=62)
    replay_examples = store.read(split="replay", limit=100000)
    replay_gate = build_central_brain_phase2_replay_gate(
        candidate_policy=candidate,
        replay_examples=replay_examples,
        min_replay_examples=1,
    )
    step_results.append(
        {
            "step": "synthetic_replay_gate",
            "status": replay_gate.get("status"),
            "promotion_signal": replay_gate.get("promotion_signal"),
            "failed_check_ids": (replay_gate.get("decision") or {}).get("failed_check_ids")
            if isinstance(replay_gate.get("decision"), dict)
            else [],
        }
    )
    _update_job(path, phase2_replay_gate=replay_gate, step_results=step_results, completed_steps=4, progress_percent=74)
    _update_job(path, current_step="518k_distribution_gate", progress_percent=80)
    policy_overrides = {"question_policy": {"central_brain_phase2_policy": candidate}}
    sample = run_518k_validation(
        mode="sample",
        limit=sample_limit,
        artifact_dir=settings.runtime_dir / "validation" / "518k",
        policy_payload_overrides=policy_overrides,
    ).model_dump(mode="json")
    shard: dict[str, Any] = {}
    if config.get("include_shard"):
        shard = run_518k_validation(
            mode="shard",
            shard_id=shard_id,
            limit=shard_limit,
            artifact_dir=settings.runtime_dir / "validation" / "518k",
            policy_payload_overrides=policy_overrides,
        ).model_dump(mode="json")
    distribution_gate = build_central_brain_phase2_distribution_gate(
        replay_gate=replay_gate,
        sample_result=sample,
        shard_result=shard,
        min_sample_cases=sample_limit,
        require_shard=bool(config.get("include_shard")),
    )
    passed = distribution_gate.get("promotion_signal") == "eligible"
    step_results.append(
        {
            "step": "518k_distribution_gate",
            "status": distribution_gate.get("status"),
            "promotion_signal": distribution_gate.get("promotion_signal"),
            "case_count": (distribution_gate.get("distribution_518k") or {}).get("sample", {}).get("case_count")
            if isinstance(distribution_gate.get("distribution_518k"), dict)
            else None,
            "failed_check_ids": (distribution_gate.get("decision") or {}).get("failed_check_ids")
            if isinstance(distribution_gate.get("decision"), dict)
            else [],
        }
    )
    status = "completed" if passed else "failed"
    _update_job(
        path,
        phase2_split_manifest=split_manifest,
        phase2_replay_gate=replay_gate,
        phase2_distribution_gate=distribution_gate,
        step_results=step_results,
        completed_steps=total_steps,
        current_step="completed",
        progress_percent=100,
        status=status,
        finished_at=_utc_now(),
        phase2_result={
            "version": "v30.training_orchestrator.phase2_result.v1",
            "passed": passed,
            "sample_limit": sample_limit,
            "include_shard": bool(config.get("include_shard")),
            "candidate_promotion_signal": candidate.get("promotion_signal"),
            "replay_promotion_signal": replay_gate.get("promotion_signal"),
            "distribution_promotion_signal": distribution_gate.get("promotion_signal"),
            "full_518k_required": False,
        },
        failures=[] if passed else ["central_brain_phase2_training_failed"],
    )
    return 0 if status == "completed" else 1


def _run_orchestrator_evaluation_spine(path: Path) -> int:
    from v30.validation.evaluation_training_spine import run_evaluation_training_spine

    step_results: list[dict[str, Any]] = []
    total_steps = 3
    _update_job(path, current_step="evaluation_training_spine", progress_percent=10, completed_steps=0)
    evaluation = run_evaluation_training_spine(include_phase2=True)
    decision = evaluation.get("decision") if isinstance(evaluation.get("decision"), dict) else {}
    passed = evaluation.get("status") == "passed" and bool(decision.get("evaluation_training_spine_ready"))
    step_results.append(
        {
            "step": "evaluation_training_spine",
            "status": "passed" if passed else "blocked",
            "case_count": decision.get("case_count"),
            "passed_count": decision.get("passed_case_count"),
            "average_overall_score": decision.get("average_overall_score"),
            "evidence_coverage_rate": decision.get("evidence_coverage_rate"),
            "overclaim_rate": decision.get("overclaim_rate"),
            "advice_grounding_rate": decision.get("advice_grounding_rate"),
            "probe_yield_score": decision.get("probe_yield_score"),
            "failed_case_ids": decision.get("failed_case_ids") or [],
        }
    )
    _update_job(
        path,
        evaluation_training_spine=evaluation,
        step_results=step_results,
        completed_steps=1,
        progress_percent=58,
        current_step="policy_lineage_snapshot",
    )
    lineage = _policy_lineage_summary_payload()
    step_results.append({"step": "policy_lineage_snapshot", "status": "completed", "family_count": len(lineage["families"])})
    _update_job(
        path,
        lineage_summary=lineage,
        step_results=step_results,
        completed_steps=2,
        progress_percent=78,
        current_step="quality_diff_snapshot",
    )
    quality_snapshot = {
        "version": "v30.evaluation_spine_quality_snapshot.v1",
        "evaluation_ready": passed,
        "average_overall_score": decision.get("average_overall_score"),
        "evidence_coverage_rate": decision.get("evidence_coverage_rate"),
        "overclaim_rate": decision.get("overclaim_rate"),
        "advice_grounding_rate": decision.get("advice_grounding_rate"),
        "probe_yield_score": decision.get("probe_yield_score"),
        "production_policy_write_allowed": False,
        "chart_fact_mutation_allowed": False,
    }
    step_results.append(
        {
            "step": "quality_diff_snapshot",
            "status": "completed",
            "average_overall_score": quality_snapshot["average_overall_score"],
            "overclaim_rate": quality_snapshot["overclaim_rate"],
        }
    )
    status = "completed" if passed else "failed"
    _update_job(
        path,
        evaluation_quality_snapshot=quality_snapshot,
        step_results=step_results,
        completed_steps=total_steps,
        current_step="completed",
        progress_percent=100,
        status=status,
        finished_at=_utc_now(),
        evaluation_spine_result={
            "version": "v30.training_orchestrator.evaluation_spine_result.v1",
            "passed": passed,
            "case_count": decision.get("case_count"),
            "passed_case_count": decision.get("passed_case_count"),
            "production_policy_write_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
        failures=[] if passed else ["evaluation_spine_quality_gate_failed"],
    )
    return 0 if status == "completed" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run V30 admin training job outside the API server process.")
    parser.add_argument("--kind", choices=("auto-apply", "orchestrator"), required=True)
    parser.add_argument("--job-file", required=True)
    args = parser.parse_args()
    path = Path(args.job_file)
    try:
        if args.kind == "auto-apply":
            return _run_auto_apply(path)
        return _run_orchestrator(path)
    except Exception as exc:
        return _fail_job(path, exc)


if __name__ == "__main__":
    raise SystemExit(main())
