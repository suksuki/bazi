from __future__ import annotations


def lab_api_scope() -> dict[str, object]:
    return {
        "version": "v20.lab_api_scope.v1",
        "allowed": ["runtime_replay", "corpus_precompute", "eval_report", "test_tier_report", "learning_proposal"],
        "blocked": ["untraced_rule_activation", "answer_conclusion_mutation", "test_result_direct_override"],
    }
