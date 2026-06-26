from __future__ import annotations

from v20.learning.role_interaction_training import build_role_interaction_training_report


def test_v20_role_interaction_training_builds_candidate_policy() -> None:
    report = build_role_interaction_training_report()
    policy = report["candidate_policy"]

    assert report["version"] == "v20.role_interaction_training_report.v1"
    assert report["status"] == "ready"
    assert report["case_count"] >= 10
    assert report["runtime_mutation"] is False
    assert policy["policy_key"] == "role_interaction_policy"
    assert policy["runtime_mutation"] is False
    assert "NO_RUNTIME_POINTER_MUTATION" in policy["guardrails"]


def test_v20_role_interaction_training_declares_role_specific_modes() -> None:
    report = build_role_interaction_training_report()
    policies = {
        row["role_key"]: row
        for row in report["candidate_policy"]["role_policies"]
    }

    assert policies["guest"]["interaction_mode"] == "entry_choice"
    assert policies["guest"]["answer_mode"] == "llm"
    assert policies["guest"]["visibility"] == "public_entry"
    assert policies["guest"]["default_path"] == ("entry", "focus", "advice", "closure")
    assert policies["user"]["interaction_mode"] == "guided_choice"
    assert policies["analyst"]["learning_signal"] == "calibration_signal"
    assert policies["admin"]["interaction_mode"] == "system_observe"
    assert policies["admin"]["answer_mode"] == "hybrid"


def test_v20_role_interaction_training_suppresses_forbidden_stages_by_role() -> None:
    report = build_role_interaction_training_report()
    policies = {
        row["role_key"]: row
        for row in report["candidate_policy"]["role_policies"]
    }

    guest_forbidden = {row["stage"] for row in policies["guest"]["forbidden_stage_policy"]}
    user_forbidden = {row["stage"] for row in policies["user"]["forbidden_stage_policy"]}

    assert {"review", "observe"}.issubset(guest_forbidden)
    assert "observe" in user_forbidden
    assert all(row["effect"] == "suppress_for_role" for row in policies["guest"]["forbidden_stage_policy"])


def test_v20_role_interaction_training_includes_question_review_contract() -> None:
    report = build_role_interaction_training_report()
    policy = report["candidate_policy"]

    assert {"approve", "rewrite", "downrank", "merge", "delete"}.issubset(policy["question_review_actions"])
    assert {"role_mismatch", "mainline_mismatch", "duplicate"}.issubset(policy["question_review_reasons"])
