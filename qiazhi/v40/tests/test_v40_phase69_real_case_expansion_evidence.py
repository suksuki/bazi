from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import ReleaseRecommendation, Topic
from v40.contracts.evaluation import (
    AcceptanceWindowCaseResult,
    AcceptanceWindowResult,
    EvaluationStatus,
    ExpectedMingliOutcome,
    ForbiddenAssertion,
    RealCaseRecord,
)
from v40.project import build_project_status, build_real_case_expansion_evidence_pack


REQUIRED_TOPICS = [
    Topic.CAREER,
    Topic.WEALTH,
    Topic.RELATIONSHIP,
    Topic.HEALTH,
    Topic.TIMING,
    Topic.USEFUL_GOD,
    Topic.HIDDEN_ATTRIBUTE,
]


def _case(topic: Topic, index: int, *, allow_training: bool = True) -> RealCaseRecord:
    return RealCaseRecord(
        case_id=f"real.case.phase69.{topic.value}.{index}",
        display_name=f"{topic.value} case {index}",
        user_question=f"{topic.value} 如何判断？",
        topic=topic,
        expected_outcomes=[
            ExpectedMingliOutcome(
                topic=topic,
                verdict_keywords=[topic.value],
                advice_keywords=["建议"],
                min_evidence_count=1,
            )
        ],
        forbidden_assertions=[ForbiddenAssertion(text="保证发财升职", reason="overclaim")],
        allow_training_use=allow_training,
        tags=["phase69", topic.value],
    )


def _approved_window(cases: list[RealCaseRecord]) -> AcceptanceWindowResult:
    results = [
        AcceptanceWindowCaseResult(
            case_id=case.case_id,
            run_id=f"run:{case.case_id}",
            reading_id=f"reading:{case.case_id}",
            verdict_match_score=0.86,
            advice_grounding_score=0.84,
            overclaim_rate=0.0,
            domain_coverage_score=1.0,
            probe_usefulness_score=0.82,
            llm_expression_clarity_score=0.88,
            overall_score=0.87,
            status=EvaluationStatus.PASSED,
        )
        for case in cases
    ]
    return AcceptanceWindowResult(
        window_id="window.phase69.approved",
        candidate_version="v40-alpha-phase69",
        case_count=len(results),
        case_results=results,
        run_ids=[result.run_id for result in results],
        passed_count=len(results),
        review_count=0,
        blocked_count=0,
        average_verdict_match_score=0.86,
        average_advice_grounding_score=0.84,
        average_overclaim_rate=0.0,
        average_domain_coverage_score=1.0,
        average_probe_usefulness_score=0.82,
        average_llm_expression_clarity_score=0.88,
        average_overall_score=0.87,
        recommendation=ReleaseRecommendation.APPROVE,
    )


def test_phase69_evidence_pack_blocks_when_real_case_coverage_is_missing() -> None:
    cases = [_case(Topic.CAREER, 1, allow_training=False)]

    evidence = build_real_case_expansion_evidence_pack(
        cases=cases,
        acceptance_windows=[],
        target_case_count=7,
        min_cases_per_topic=1,
        min_trainable_case_count=3,
    )

    assert evidence["automatic_status"] == "blocked"
    assert evidence["cutover_status"] == "blocked_by_real_case_evidence"
    assert evidence["case_count_ready"] is False
    assert evidence["trainable_case_ready"] is False
    assert evidence["acceptance_window_ready"] is False
    assert any(gap["topic"] == Topic.WEALTH.value for gap in evidence["coverage_gaps"])
    assert evidence["writes_v40_production"] is False


def test_phase69_evidence_pack_can_be_ready_but_still_requires_human_cutover_signoff() -> None:
    cases = [_case(topic, index) for index, topic in enumerate(REQUIRED_TOPICS, start=1)]
    window = _approved_window(cases)

    evidence = build_real_case_expansion_evidence_pack(
        cases=cases,
        acceptance_windows=[window],
        target_case_count=len(cases),
        min_cases_per_topic=1,
        min_trainable_case_count=len(cases),
    )

    assert evidence["automatic_status"] == "ready"
    assert evidence["cutover_status"] == "ready_for_human_signoff"
    assert evidence["coverage_gaps"] == []
    assert evidence["latest_acceptance_window"]["ready"] is True
    assert "线上切换窗口" in evidence["manual_signoff_required"]
    assert evidence["next_collection_tasks"] == ["真实案例证据已满足自动门槛，等待人工确认上线窗口。"]


def test_phase69_api_returns_readonly_real_case_expansion_evidence() -> None:
    cases = [_case(topic, index) for index, topic in enumerate(REQUIRED_TOPICS, start=1)]
    window = _approved_window(cases)

    response = TestClient(create_app()).post(
        f"{API_PREFIX}/project/real-case-expansion-evidence",
        json={
            "cases": [case.model_dump(mode="json") for case in cases],
            "acceptance_windows": [window.model_dump(mode="json")],
            "target_case_count": len(cases),
            "min_cases_per_topic": 1,
            "min_trainable_case_count": len(cases),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "v40.real_case_expansion_evidence_response.v1"
    assert body["evidence"]["automatic_status"] == "ready"
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False
    assert body["boundary"] == "real_case_expansion_evidence_reads_cases_without_cutover_or_policy_write"


def test_phase69_docs_and_project_status_track_real_case_expansion_evidence() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE69_REAL_CASE_EXPANSION_AND_CUTOVER_EVIDENCE.md").read_text(
        encoding="utf-8"
    )
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "Real Case Expansion And Cutover Evidence" in doc
    assert "POST /api/v40/project/real-case-expansion-evidence" in doc
    assert "docs/V40_PHASE69_REAL_CASE_EXPANSION_AND_CUTOVER_EVIDENCE.md" in readme
    assert status["current_phase"] == 70
    assert status["current_phase_name"] == "Direct Training Activation Evidence"
    assert any(row["range"] == "68" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "69" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "70" and row["status"] == "active" for row in status["phase_groups"])
    assert status["next_mainline_tasks"][0] == "TRAIN-16: direct training activation before/after acceptance and rollback UX"
