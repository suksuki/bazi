from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi.testclient import TestClient

from tests.unit.test_central_brain_phase2_replay_gate import _example
from v30.api.app import create_app
from v30.training import BrainTrainingExampleStore


def test_training_orchestrator_admin_plan_runs_quick_validation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("V30_RUNTIME_DIR", str(tmp_path / ".runtime"))
    monkeypatch.setenv("V30_ENV", "test")
    monkeypatch.setenv("V30_REPOSITORY", "memory")
    app = create_app()
    client = TestClient(app)

    plans = client.get("/api/v30/admin/training/orchestrator/plans").json()
    assert plans["version"] == "v30.admin.training_orchestrator_plans.v1"
    assert {row["plan_id"] for row in plans["plans"]} >= {
        "central_brain_auto_apply",
        "quick_validation_only",
        "m3_518k_validation",
        "central_brain_phase2_training",
    }

    response = client.post(
        "/api/v30/admin/training/orchestrator/run",
        json={
            "plan_id": "quick_validation_only",
            "training_run_id": "unit-orchestrator-quick",
            "promotion_validation_mode": "smoke",
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] in {"queued", "running"}
    job_id = payload["job_id"]

    final = payload
    for _ in range(40):
        final = client.get("/api/v30/admin/training/orchestrator/status", params={"job_id": job_id}).json()
        if final.get("status") in {"completed", "failed"}:
            break
        time.sleep(0.25)

    assert final["status"] == "completed"
    assert final["progress_percent"] == 100
    assert final["validation_result"]["passed"] is True
    assert final["lineage_summary"]["version"] == "v30.admin.policy_lineage_summary.v1"
    assert final["boundary"] == "training_orchestrator_runs_named_training_plan_without_mutating_chart_facts"

    history = client.get("/api/v30/admin/training/orchestrator/history").json()
    assert history["count"] >= 1
    assert history["jobs"][0]["job_id"] == job_id
    diff = client.get("/api/v30/admin/training/orchestrator/diff", params={"job_id": job_id}).json()
    assert diff["version"] == "v30.training_orchestrator.diff_summary.v1"
    assert diff["job_id"] == job_id
    assert diff["current_metrics"]["failed_step_count"] == 0
    assert diff["current_quality_metrics"]["m3_step_pass_rate"] == 1.0
    assert "quality_diff_rows" in diff


def test_training_orchestrator_admin_plan_runs_m3_518k_sample(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("V30_RUNTIME_DIR", str(tmp_path / ".runtime"))
    monkeypatch.setenv("V30_ENV", "test")
    monkeypatch.setenv("V30_REPOSITORY", "memory")
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v30/admin/training/orchestrator/run",
        json={
            "plan_id": "m3_518k_validation",
            "training_run_id": "unit-orchestrator-m3-518k",
            "sample_limit": 1,
            "persist_m3_to_db": False,
            "include_shard": False,
            "include_readiness_matrix": False,
        },
    )
    payload = response.json()
    assert response.status_code == 200
    job_id = payload["job_id"]

    final = payload
    for _ in range(80):
        final = client.get("/api/v30/admin/training/orchestrator/status", params={"job_id": job_id}).json()
        if final.get("status") in {"completed", "failed"}:
            break
        time.sleep(0.25)

    assert final["status"] == "completed"
    assert final["progress_percent"] == 100
    assert final["m3_518k_result"]["passed"] is True
    assert final["m3_518k_result"]["sample_limit"] == 1
    steps = [row["step"] for row in final["step_results"]]
    assert steps == ["m3_snapshot", "m3_synthetic", "training_pipeline", "518k_sample"]
    sample = next(row for row in final["step_results"] if row["step"] == "518k_sample")
    assert sample["promotion_signal"] == "eligible"


def test_training_orchestrator_reruns_failed_m3_step(tmp_path: Path, monkeypatch) -> None:
    runtime_dir = tmp_path / ".runtime"
    monkeypatch.setenv("V30_RUNTIME_DIR", str(runtime_dir))
    monkeypatch.setenv("V30_ENV", "test")
    monkeypatch.setenv("V30_REPOSITORY", "memory")
    failed_job_id = "training-orchestrator-job-unit-failed"
    job_dir = runtime_dir / "training" / "orchestrator_jobs"
    job_dir.mkdir(parents=True, exist_ok=True)
    failed_job = {
        "version": "v30.admin.training_orchestrator_job.v1",
        "job_id": failed_job_id,
        "plan_id": "m3_518k_validation",
        "plan_label": "M3 / 518K 验证",
        "status": "failed",
        "created_at": "2026-06-28T00:00:00+00:00",
        "finished_at": "2026-06-28T00:00:01+00:00",
        "current_step": "518k_sample",
        "completed_steps": 3,
        "total_steps": 4,
        "progress_percent": 75,
        "steps": ["m3_snapshot", "m3_synthetic", "training_pipeline", "518k_sample"],
        "step_results": [
            {"step": "m3_snapshot", "status": "completed"},
            {"step": "m3_synthetic", "passed": True, "case_count": 1, "passed_count": 1},
            {"step": "training_pipeline", "passed": True, "case_count": 1, "passed_count": 1},
            {"step": "518k_sample", "promotion_signal": "blocked", "case_count": 1},
        ],
        "config": {
            "plan_id": "m3_518k_validation",
            "training_run_id": "unit-rerun-failed",
            "sample_limit": 1,
            "persist_m3_to_db": False,
            "include_shard": False,
            "shard_id": 7,
            "shard_limit": 16,
            "include_readiness_matrix": False,
        },
        "boundary": "training_orchestrator_runs_named_training_plan_without_mutating_chart_facts",
    }
    (job_dir / f"{failed_job_id}.json").write_text(json.dumps(failed_job, ensure_ascii=False), encoding="utf-8")
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v30/admin/training/orchestrator/rerun-failed",
        json={"job_id": failed_job_id},
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["rerun_of_job_id"] == failed_job_id
    assert payload["rerun_steps"] == ["518k_sample"]
    rerun_job_id = payload["job_id"]

    final = payload
    for _ in range(60):
        final = client.get("/api/v30/admin/training/orchestrator/status", params={"job_id": rerun_job_id}).json()
        if final.get("status") in {"completed", "failed"}:
            break
        time.sleep(0.25)

    assert final["status"] == "completed"
    assert final["steps"] == ["518k_sample"]
    assert [row["step"] for row in final["step_results"]] == ["518k_sample"]
    assert final["step_results"][0]["promotion_signal"] == "eligible"


def test_training_orchestrator_diff_compares_business_quality_metrics(tmp_path: Path, monkeypatch) -> None:
    runtime_dir = tmp_path / ".runtime"
    monkeypatch.setenv("V30_RUNTIME_DIR", str(runtime_dir))
    monkeypatch.setenv("V30_ENV", "test")
    monkeypatch.setenv("V30_REPOSITORY", "memory")
    job_dir = runtime_dir / "training" / "orchestrator_jobs"
    job_dir.mkdir(parents=True, exist_ok=True)
    previous_job_id = "training-orchestrator-job-quality-previous"
    current_job_id = "training-orchestrator-job-quality-current"
    base_job = {
        "version": "v30.admin.training_orchestrator_job.v1",
        "plan_id": "central_brain_auto_apply",
        "plan_label": "中枢智能大脑自动训练",
        "status": "completed",
        "created_at": "2026-06-28T00:00:00+00:00",
        "finished_at": "2026-06-28T00:00:01+00:00",
        "current_step": "completed",
        "completed_steps": 4,
        "total_steps": 4,
        "progress_percent": 100,
        "steps": ["preflight_lineage", "auto_apply_training", "post_training_lineage", "history_snapshot"],
        "step_results": [{"step": "auto_apply_training", "status": "completed", "promoted_count": 4}],
        "config": {"plan_id": "central_brain_auto_apply", "training_run_id": "quality-diff"},
        "boundary": "training_orchestrator_runs_named_training_plan_without_mutating_chart_facts",
    }
    previous_job = {
        **base_job,
        "job_id": previous_job_id,
        "training_run": {
            "training_signal_summary": {
                "quality_metrics": {
                    "final_synthesis_quality_score": 0.62,
                    "advice_actionability": 0.58,
                    "decision_focus_coverage": 0.4,
                    "template_risk": 0.35,
                    "overclaim_risk": 0.22,
                }
            }
        },
    }
    current_job = {
        **base_job,
        "job_id": current_job_id,
        "training_run": {
            "training_signal_summary": {
                "quality_metrics": {
                    "final_synthesis_quality_score": 0.82,
                    "advice_actionability": 0.74,
                    "decision_focus_coverage": 0.9,
                    "template_risk": 0.12,
                    "overclaim_risk": 0.1,
                }
            }
        },
    }
    (job_dir / f"{previous_job_id}.json").write_text(json.dumps(previous_job, ensure_ascii=False), encoding="utf-8")
    (job_dir / f"{current_job_id}.json").write_text(json.dumps(current_job, ensure_ascii=False), encoding="utf-8")
    app = create_app()
    client = TestClient(app)

    diff = client.get("/api/v30/admin/training/orchestrator/diff", params={"job_id": current_job_id}).json()

    assert diff["previous_job_id"] == previous_job_id
    rows = {row["metric"]: row for row in diff["quality_diff_rows"]}
    assert rows["final_synthesis_quality_score"]["judgement"] == "improved"
    assert rows["advice_actionability"]["judgement"] == "improved"
    assert rows["template_risk"]["judgement"] == "improved"
    assert rows["overclaim_risk"]["judgement"] == "improved"
    assert diff["quality_regression_count"] == 0
    assert diff["quality_improvement_count"] >= 4


def test_training_orchestrator_runs_central_brain_phase2_training(tmp_path: Path, monkeypatch) -> None:
    runtime_dir = tmp_path / ".runtime"
    monkeypatch.setenv("V30_RUNTIME_DIR", str(runtime_dir))
    monkeypatch.setenv("V30_ENV", "test")
    monkeypatch.setenv("V30_REPOSITORY", "memory")
    store = BrainTrainingExampleStore(runtime_dir)
    for index in range(8):
        store.append(_example(f"orchestrator-phase2-{index}"))
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v30/admin/training/orchestrator/run",
        json={
            "plan_id": "central_brain_phase2_training",
            "training_run_id": "unit-orchestrator-phase2",
            "sample_limit": 1,
            "include_shard": False,
        },
    )
    payload = response.json()
    assert response.status_code == 200
    job_id = payload["job_id"]

    final = payload
    for _ in range(80):
        final = client.get("/api/v30/admin/training/orchestrator/status", params={"job_id": job_id}).json()
        if final.get("status") in {"completed", "failed"}:
            break
        time.sleep(0.25)

    assert final["status"] == "completed"
    assert final["progress_percent"] == 100
    assert final["phase2_result"]["passed"] is True
    assert final["phase2_result"]["distribution_promotion_signal"] == "eligible"
    assert final["phase2_distribution_gate"]["promotion_signal"] == "eligible"
    assert [row["step"] for row in final["step_results"]] == [
        "brain_example_summary",
        "build_training_splits",
        "optimize_policy_candidate",
        "synthetic_replay_gate",
        "518k_distribution_gate",
    ]
