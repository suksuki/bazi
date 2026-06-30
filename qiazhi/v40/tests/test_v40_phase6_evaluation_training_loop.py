from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from v40.api.app import API_PREFIX, create_app
from v40.contracts.evaluation import EvaluationCaseSpec, EvaluationStatus, ExpectedVerdict, ForbiddenAssertion
from v40.contracts.base import Topic
from v40.evaluation import evaluate_runtime_against_case
from v40.migration import V30ExportEnvelope, build_runtime_from_v30_export
from v40.storage import resolve_v40_database_config


ROOT = Path(__file__).resolve().parents[1]


def _runtime_from_fixture():
    payload = json.loads((ROOT / "tests" / "fixtures" / "v30_export_minimal.json").read_text(encoding="utf-8"))
    envelope = V30ExportEnvelope.model_validate(payload)
    return build_runtime_from_v30_export(envelope)


def _career_case(case_id: str = "case.phase6.career.001") -> EvaluationCaseSpec:
    return EvaluationCaseSpec(
        case_id=case_id,
        topic=Topic.CAREER,
        expected_verdicts=[
            ExpectedVerdict(
                topic=Topic.CAREER,
                expected_keywords=["事业", "稳定", "突破"],
                min_evidence_count=1,
            )
        ],
        forbidden_assertions=[ForbiddenAssertion(text="保证升职发财", reason="overclaim")],
    )


def test_evaluation_runner_scores_runtime_and_builds_release_gate() -> None:
    runtime = _runtime_from_fixture()
    case_spec = _career_case()

    run = evaluate_runtime_against_case(
        run_id="run.phase6.career.001",
        case_spec=case_spec,
        runtime=runtime,
        candidate_version="v40-alpha-phase6",
    )

    assert run.metric_summary.status == EvaluationStatus.PASSED
    assert run.metric_summary.overclaim_rate == 0
    assert run.metric_summary.overall_score >= 0.82
    assert run.release_gate is not None
    assert run.release_gate.production_write_allowed is False


def test_evaluation_runner_blocks_forbidden_assertion_hits() -> None:
    runtime = _runtime_from_fixture()
    case_spec = EvaluationCaseSpec(
        case_id="case.phase6.blocked.001",
        topic=Topic.CAREER,
        expected_verdicts=[ExpectedVerdict(topic=Topic.CAREER)],
        forbidden_assertions=[ForbiddenAssertion(text="事业", reason="too_broad_forbidden_smoke")],
    )

    run = evaluate_runtime_against_case(
        run_id="run.phase6.blocked.001",
        case_spec=case_spec,
        runtime=runtime,
        candidate_version="v40-alpha-phase6",
    )

    assert run.metric_summary.status == EvaluationStatus.BLOCKED
    assert "forbidden_assertion_hit" in run.metric_summary.failed_reasons
    assert run.release_gate is not None
    assert run.release_gate.production_write_allowed is False


def test_phase6_api_persists_evaluation_run_and_training_impact() -> None:
    if resolve_v40_database_config() is None:
        pytest.skip("V40_DATABASE_URL is not configured")

    client = TestClient(create_app())
    runtime = _runtime_from_fixture()
    case_spec = _career_case("case.phase6.api.001")

    evaluation_response = client.post(
        f"{API_PREFIX}/evaluation/runs/from-runtime",
        json={
            "run_id": "run.phase6.api.001",
            "case_spec": case_spec.model_dump(mode="json"),
            "runtime": runtime.model_dump(mode="json"),
            "candidate_version": "v40-alpha-phase6",
            "build_release_gate": True,
            "persist": True,
        },
    )
    assert evaluation_response.status_code == 200
    evaluation_body = evaluation_response.json()
    assert evaluation_body["persisted"] is True
    assert evaluation_body["run"]["metric_summary"]["overall_score"] >= 0.82

    impact_response = client.post(
        f"{API_PREFIX}/training/impact-from-evaluation",
        json={
            "training_run_id": "train.phase6.api.001",
            "base_version": "v40-alpha-phase5",
            "candidate_version": "v40-alpha-phase6",
            "evaluation_run": evaluation_body["run"],
            "persist": True,
        },
    )
    assert impact_response.status_code == 200
    impact_body = impact_response.json()
    assert impact_body["persisted"] is True
    assert impact_body["impact"]["production_write_allowed"] is False

    runs = client.get(f"{API_PREFIX}/evaluation/runs?limit=5").json()["runs"]
    assert any(run["run_id"] == "run.phase6.api.001" for run in runs)
    impacts = client.get(f"{API_PREFIX}/training/impact-diffs?limit=5").json()["impacts"]
    assert any(impact["training_run_id"] == "train.phase6.api.001" for impact in impacts)
