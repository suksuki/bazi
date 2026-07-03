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
from v40.project import build_project_status, build_real_case_acceptance_pack


def _case(topic: Topic = Topic.CAREER, index: int = 1) -> RealCaseRecord:
    return RealCaseRecord(
        case_id=f"real.case.phase73.{topic.value}.{index}",
        display_name=f"{topic.value} owner review case",
        user_question=f"{topic.value} 应该如何判断？",
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
        allow_training_use=True,
    )


def _approved_window(cases: list[RealCaseRecord]) -> AcceptanceWindowResult:
    results = [
        AcceptanceWindowCaseResult(
            case_id=case.case_id,
            run_id=f"run:{case.case_id}",
            reading_id=f"reading:{case.case_id}",
            verdict_match_score=0.88,
            advice_grounding_score=0.86,
            overclaim_rate=0.0,
            domain_coverage_score=1.0,
            probe_usefulness_score=0.82,
            llm_expression_clarity_score=0.9,
            overall_score=0.89,
            status=EvaluationStatus.PASSED,
            trainable_attribution_hints=["advice_engine:career:advice_priority"],
        )
        for case in cases
    ]
    return AcceptanceWindowResult(
        window_id="window.phase73.approved",
        candidate_version="v40-beta-candidate",
        case_count=len(results),
        case_results=results,
        run_ids=[result.run_id for result in results],
        passed_count=len(results),
        review_count=0,
        blocked_count=0,
        average_verdict_match_score=0.88,
        average_advice_grounding_score=0.86,
        average_overclaim_rate=0.0,
        average_domain_coverage_score=1.0,
        average_probe_usefulness_score=0.82,
        average_llm_expression_clarity_score=0.9,
        average_overall_score=0.89,
        recommendation=ReleaseRecommendation.APPROVE,
    )


def _blocked_window(cases: list[RealCaseRecord]) -> AcceptanceWindowResult:
    results = [
        AcceptanceWindowCaseResult(
            case_id=case.case_id,
            run_id=f"run:{case.case_id}",
            reading_id=f"reading:{case.case_id}",
            verdict_match_score=0.52,
            advice_grounding_score=0.5,
            overclaim_rate=0.25,
            domain_coverage_score=0.7,
            probe_usefulness_score=0.5,
            llm_expression_clarity_score=0.62,
            overall_score=0.58,
            status=EvaluationStatus.BLOCKED,
            failed_reasons=["real_case_overclaim_hit"],
            trainable_attribution_hints=["llm_expression:style_policy"],
        )
        for case in cases
    ]
    return AcceptanceWindowResult(
        window_id="window.phase73.blocked",
        candidate_version="v40-beta-candidate",
        case_count=len(results),
        case_results=results,
        run_ids=[result.run_id for result in results],
        passed_count=0,
        review_count=0,
        blocked_count=len(results),
        average_verdict_match_score=0.52,
        average_advice_grounding_score=0.5,
        average_overclaim_rate=0.25,
        average_domain_coverage_score=0.7,
        average_probe_usefulness_score=0.5,
        average_llm_expression_clarity_score=0.62,
        average_overall_score=0.58,
        failed_reason_counts={"real_case_overclaim_hit": len(results)},
        recommendation=ReleaseRecommendation.REJECT,
    )


def _ready_real_case_evidence() -> dict[str, object]:
    return {
        "evidence": {
            "automatic_status": "ready",
            "cutover_status": "ready_for_human_signoff",
        }
    }


def _ready_cutover_decision() -> dict[str, object]:
    return {
        "decision": {
            "decision_status": "ready_for_human_signoff",
            "traffic_switch_allowed_by_system": False,
        }
    }


def test_phase73_acceptance_pack_ready_for_owner_review_without_cutover() -> None:
    cases = [_case(Topic.CAREER, 1), _case(Topic.WEALTH, 2)]
    pack = build_real_case_acceptance_pack(
        cases=cases,
        acceptance_window=_approved_window(cases),
        real_case_evidence=_ready_real_case_evidence(),
        online_cutover_decision=_ready_cutover_decision(),
        min_owner_review_case_count=2,
    )

    assert pack["acceptance_status"] == "ready_for_owner_review"
    assert pack["owner_review_required"] is True
    assert pack["traffic_switch_allowed_by_system"] is False
    assert pack["writes_v30_state"] is False
    assert pack["writes_v40_production"] is False
    assert pack["topic_counts"] == {"career": 1, "wealth": 1}
    assert pack["trainable_attribution_hints"] == ["advice_engine:career:advice_priority"]
    assert "beta 切换窗口" in pack["manual_signoff_required"]


def test_phase73_acceptance_pack_blocks_overclaim_quality_before_owner_review() -> None:
    cases = [_case(Topic.CAREER, 1)]
    pack = build_real_case_acceptance_pack(
        cases=cases,
        acceptance_window=_blocked_window(cases),
        real_case_evidence=_ready_real_case_evidence(),
        online_cutover_decision=_ready_cutover_decision(),
    )

    assert pack["acceptance_status"] == "blocked_by_quality"
    assert pack["owner_review_required"] is False
    assert pack["failed_reason_counts"] == {"real_case_overclaim_hit": 1}
    assert any(blocker["key"] == "acceptance_window_blocked" for blocker in pack["blockers"])
    assert any(blocker["key"] == "acceptance_window_overclaim" for blocker in pack["blockers"])
    assert "把 trainable_attribution_hints 送入训练影响 review。" in pack["next_actions"]


def test_phase73_acceptance_pack_api_is_readonly() -> None:
    cases = [_case(Topic.CAREER, 1), _case(Topic.WEALTH, 2)]
    response = TestClient(create_app()).post(
        f"{API_PREFIX}/project/real-case-acceptance-pack",
        json={
            "cases": [case.model_dump(mode="json") for case in cases],
            "acceptance_window": _approved_window(cases).model_dump(mode="json"),
            "real_case_evidence": _ready_real_case_evidence(),
            "online_cutover_decision": _ready_cutover_decision(),
            "min_owner_review_case_count": 2,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "v40.real_case_acceptance_pack_response.v1"
    assert body["pack"]["acceptance_status"] == "ready_for_owner_review"
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False
    assert body["traffic_switch_allowed_by_system"] is False
    assert body["boundary"] == "real_case_acceptance_pack_reads_evidence_without_cutover"


def test_phase73_docs_and_project_status_track_real_case_acceptance_pack() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE73_REAL_CASE_ACCEPTANCE_PACK.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()

    assert "Real Case Acceptance Pack" in doc
    assert "POST /api/v40/project/real-case-acceptance-pack" in doc
    assert "build_real_case_acceptance_pack" in spec
    assert "docs/V40_PHASE73_REAL_CASE_ACCEPTANCE_PACK.md" in readme
    assert status["current_phase"] == 73
    assert status["current_phase_name"] == "Real Case Acceptance Pack"
    assert any(row["range"] == "72" and row["status"] == "complete" for row in status["phase_groups"])
    assert any(row["range"] == "73" and row["status"] == "active" for row in status["phase_groups"])
    assert status["next_mainline_tasks"][0] == "QA-19: live LLM report/conversation acceptance on selected real cases"
