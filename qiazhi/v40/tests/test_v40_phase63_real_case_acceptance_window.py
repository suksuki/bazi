from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.contracts.evaluation import (
    AcceptanceWindowResult,
    ExpectedMingliOutcome,
    ForbiddenAssertion,
    ObservedLifeEvent,
    PractitionerJudgment,
    RealCaseRecord,
)
from v40.evaluation import build_acceptance_window_from_runtime
from v40.migration import V30ExportEnvelope, build_runtime_from_v30_export
from v40.project import build_project_status


ROOT = Path(__file__).resolve().parents[1]


def _runtime_from_fixture():
    payload = json.loads((ROOT / "tests" / "fixtures" / "v30_export_minimal.json").read_text(encoding="utf-8"))
    envelope = V30ExportEnvelope.model_validate(payload)
    return build_runtime_from_v30_export(envelope)


def _career_real_case(case_id: str = "real.case.phase63.career.001") -> RealCaseRecord:
    return RealCaseRecord(
        case_id=case_id,
        display_name="事业稳定与突破验收样例",
        user_question="今年事业适合稳定发展还是转型突破？",
        topic=Topic.CAREER,
        observed_events=[
            ObservedLifeEvent(
                event_id=f"{case_id}.event.001",
                topic=Topic.CAREER,
                year="2024",
                description="岗位职责明显增加，但资源和平台也随之增强。",
                evidence_tags=["职责压力", "平台资源"],
            )
        ],
        expected_outcomes=[
            ExpectedMingliOutcome(
                topic=Topic.CAREER,
                verdict_keywords=["事业", "稳定", "突破"],
                advice_keywords=["职责", "资质"],
                min_evidence_count=1,
            )
        ],
        practitioner_judgments=[
            PractitionerJudgment(
                judgment_id=f"{case_id}.judgment.001",
                summary="此命例事业判断应先看承接压力，再看突破窗口。",
                accepted_topics=[Topic.CAREER],
            )
        ],
        forbidden_assertions=[ForbiddenAssertion(text="保证升职发财", reason="overclaim")],
        allow_training_use=True,
        tags=["phase63", "career"],
    )


def test_phase63_real_case_contract_converts_to_evaluation_case_without_fact_mutation() -> None:
    real_case = _career_real_case()

    evaluation_case = real_case.to_evaluation_case()

    assert evaluation_case.case_type == "real_feedback"
    assert evaluation_case.case_id == real_case.case_id
    assert evaluation_case.known_reality["allow_training_use"] is True
    assert evaluation_case.expected_verdicts[0].expected_keywords == ["事业", "稳定", "突破"]
    assert evaluation_case.expected_advice[0].must_include_any == ["职责", "资质"]
    assert evaluation_case.chart_fact_mutation_allowed is False


def test_phase63_acceptance_window_scores_real_cases_and_emits_training_hints() -> None:
    runtime = _runtime_from_fixture()
    cases = [_career_real_case()]

    runs, window = build_acceptance_window_from_runtime(
        window_id="window.phase63.career.001",
        cases=cases,
        runtime=runtime,
        candidate_version="v40-alpha-phase63",
    )

    assert len(runs) == 1
    assert isinstance(window, AcceptanceWindowResult)
    assert window.case_count == 1
    assert window.passed_count == 1
    assert window.average_verdict_match_score >= 0.8
    assert window.average_advice_grounding_score >= 0.8
    assert window.average_overclaim_rate == 0
    assert window.production_write_allowed is False
    assert window.case_results[0].trainable_attribution_hints == []


def test_phase63_acceptance_window_blocks_real_case_overclaim() -> None:
    runtime = _runtime_from_fixture()
    real_case = _career_real_case("real.case.phase63.blocked.001").model_copy(
        update={"forbidden_assertions": [ForbiddenAssertion(text="事业", reason="overbroad overclaim smoke")]}
    )

    _, window = build_acceptance_window_from_runtime(
        window_id="window.phase63.blocked.001",
        cases=[real_case],
        runtime=runtime,
        candidate_version="v40-alpha-phase63",
    )

    assert window.blocked_count == 1
    assert window.recommendation == "reject"
    assert "real_case_overclaim_hit" in window.case_results[0].failed_reasons
    assert window.production_write_allowed is False


def test_phase63_acceptance_window_api_returns_read_model_without_persistence() -> None:
    client = TestClient(create_app())
    runtime = _runtime_from_fixture()
    real_case = _career_real_case()

    response = client.post(
        f"{API_PREFIX}/acceptance/windows/from-runtime",
        json={
            "window_id": "window.phase63.api.001",
            "cases": [real_case.model_dump(mode="json")],
            "runtime": runtime.model_dump(mode="json"),
            "candidate_version": "v40-alpha-phase63",
            "persist": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["persisted"] is False
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False
    assert body["window"]["case_count"] == 1
    assert body["window"]["average_overall_score"] >= 0.8
    assert body["runs"][0]["case_spec"]["case_type"] == "real_feedback"


def test_phase63_project_status_and_docs_track_acceptance_window_plan() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE63_SYSTEM_REVIEW_AND_NEXT_MAINLINE_PLAN.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "Real Case Bank / Acceptance Window V1" in doc
    assert "docs/V40_PHASE63_SYSTEM_REVIEW_AND_NEXT_MAINLINE_PLAN.md" in readme
    assert status["current_phase"] == 72
    assert status["current_phase_name"] == "Real Case Acceptance And Beta Cutover Plan"
    assert any(row["range"] == "62" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "63" and row["status"] == "complete" for row in status["phase_groups"])
    assert status["next_mainline_tasks"][0] == "USER-18: real case quality signoff and beta cutover window"
