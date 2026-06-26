from __future__ import annotations

from v20.learning.question_dag_training import build_question_dag_training_report


def test_v20_question_dag_training_builds_candidate_policy_from_synthetic_cases() -> None:
    report = build_question_dag_training_report()
    policy = report["candidate_policy"]

    assert report["version"] == "v20.question_dag_training_report.v1"
    assert report["status"] == "ready"
    assert report["case_count"] >= 10
    assert "question_stage_transition" in report["training_targets"]
    assert report["stage_coverage"]["coverage_ratio"] == 1.0
    assert report["coherence_report"]["status"] == "pass"
    assert report["coherence_report"]["failure_count"] == 0
    assert report["transition_count"] > 0
    assert policy["policy_key"] == "next_question_policy"
    assert policy["runtime_mutation"] is False
    assert "NO_RUNTIME_POINTER_MUTATION" in policy["guardrails"]


def test_v20_question_dag_training_keeps_role_paths_and_review_policy_structured() -> None:
    report = build_question_dag_training_report(
        question_review_training_report={
            "version": "v20.question_review_training_report.v1",
            "status": "ready",
            "review_count": 2,
            "recommendations": [
                {
                    "recommendation_key": "question_review.suppress.user.q_branch_relation_detail",
                    "recommendation_type": "suppress_question_candidate",
                    "question_key": "q_branch_relation_detail",
                    "role_target": "user",
                    "domain": "branch",
                    "stage": "review",
                    "basis": "2 reviews; negative ratio 1.0",
                }
            ],
        }
    )
    policy = report["candidate_policy"]
    role_paths = {row["role_key"]: row["default_path"] for row in policy["role_default_policy"]}
    review_policy = policy["question_review_policy"]

    assert role_paths["guest"] == ("entry", "focus", "advice", "closure")
    assert role_paths["user"] == ("entry", "focus", "structure", "timing", "advice", "closure")
    assert role_paths["analyst"] == ("structure", "review", "timing", "closure")
    assert role_paths["admin"] == ("observe", "review", "closure")
    assert review_policy["candidate_effects"]["downrank"] == "ranking_penalty_candidate"
    assert review_policy["candidate_effects"]["delete"] == "suppression_candidate"
    assert review_policy["candidate_effects"]["suppress_role_stage_question_candidate"] == "role_stage_penalty_candidate"
    assert review_policy["source_report_version"] == "v20.question_review_training_report.v1"
    assert review_policy["source_review_count"] == 2
    assert review_policy["recommendation_count"] == 1
    assert review_policy["training_recommendations"][0]["training_source"] == "question_review_training"
    assert review_policy["training_recommendations"][0]["runtime_allowed"] is False
    assert review_policy["runtime_mutation"] is False


def test_v20_question_dag_training_transition_policy_is_supported_by_synthetic_paths() -> None:
    report = build_question_dag_training_report()
    transitions = {
        (row["from_stage"], row["to_stage"]): row
        for row in report["candidate_policy"]["synthetic_transition_policy"]
    }

    assert ("entry", "focus") in transitions
    assert ("focus", "structure") in transitions
    assert ("structure", "review") in transitions
    assert ("review", "timing") in transitions
    assert transitions[("entry", "focus")]["support_count"] >= 1
    assert transitions[("entry", "focus")]["priority"] > 0
