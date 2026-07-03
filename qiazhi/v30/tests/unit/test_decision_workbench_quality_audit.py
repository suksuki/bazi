from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v30.api.app import create_app
from v30.runtime import create_smoke_runtime
from v30.validation.decision_workbench_quality import build_decision_workbench_quality_audit


def test_decision_workbench_quality_audit_tracks_output_orchestration() -> None:
    runtime = create_smoke_runtime("pytest-dca17-quality")

    audit = build_decision_workbench_quality_audit(runtime)
    summary = audit["summary"]
    decision = audit["decision"]

    assert audit["version"] == "v30.decision_workbench_quality_audit.v1"
    assert audit["status"] == "ready"
    assert summary["journey_step_count"] == 7
    assert summary["uses_seven_step_journey"] is True
    assert summary["journey_llm_not_required_count"] == 7
    assert summary["verdict_count"] >= 5
    assert summary["conflict_count"] >= 1
    assert summary["branch_option_set_count"] >= 1
    assert summary["practitioner_option_set_count"] >= summary["branch_option_set_count"]
    assert summary["user_training_signal_visible"] is False
    assert summary["practitioner_training_signal_visible"] is True
    assert summary["admin_training_signal_visible"] is True
    assert summary["dialogue_source"] == "central_reading_state.brain_decision_trace"
    assert summary["customer_visible_question_count"] <= 1
    assert summary["chart_fact_mutation_allowed"] is False
    assert audit["quality_scores"]["overall_score"] >= 0.9
    assert decision["decision_workbench_quality_ready"] is True
    assert decision["chart_fact_mutation_allowed"] is False
    assert decision["policy_pointer_write_allowed"] is False
    assert all(row["passed"] for row in audit["checks"] if row["severity"] == "error")
    assert all(row["judgement"] == "ready" for row in audit["admin_diff_rows"])


def test_admin_decision_workbench_quality_endpoint(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("V30_RUNTIME_DIR", str(tmp_path / ".runtime"))
    monkeypatch.setenv("V30_ENV", "test")
    monkeypatch.setenv("V30_REPOSITORY", "memory")
    app = create_app()
    client = TestClient(app)
    reading_id = "pytest-dca17-quality-api"

    client.get(f"/api/v30/readings/{reading_id}")
    response = client.get(f"/api/v30/admin/readings/{reading_id}/decision-workbench-quality")
    payload = response.json()

    assert response.status_code == 200
    assert payload["version"] == "v30.decision_workbench_quality_audit.v1"
    assert payload["reading_id"] == reading_id
    assert payload["decision"]["decision_workbench_quality_ready"] is True
    assert payload["summary"]["journey_step_count"] == 7
    assert payload["summary"]["journey_llm_policy_count"] == 7
    assert payload["summary"]["user_training_signal_visible"] is False
