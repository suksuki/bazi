from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.policy import RuntimePointerStore
from v30.validation.targeted_calibration_pointer_decision import build_targeted_calibration_pointer_decision


def _settings(tmp_path: Path) -> V30Settings:
    return V30Settings(
        database_url=None,
        redis_url=None,
        redis_prefix="v30",
        runtime_dir=tmp_path / ".runtime",
        host="127.0.0.1",
        port=9030,
        env="test",
        repository="memory",
    )


def _ready_pointer_review() -> dict[str, object]:
    return {
        "version": "v30.targeted_calibration_pointer_review.v1",
        "review_id": "unit-f5",
        "decision": {
            "pointer_review_ready": True,
            "decision_status": "ready_for_explicit_operator_pointer_decision",
        },
        "pointer_diff_summary": {
            "diff_count": 4,
            "would_change_count": 4,
            "rows": [
                {"family": "structure_policy", "would_change_pointer": True},
                {"family": "rule_policy", "would_change_pointer": True},
                {"family": "question_policy", "would_change_pointer": True},
                {"family": "answer_policy", "would_change_pointer": True},
            ],
        },
        "active_pointer_summary": {
            "candidate_families": ["structure_policy", "rule_policy", "question_policy", "answer_policy"],
        },
    }


def test_targeted_calibration_pointer_decision_defers_without_pointer_write(tmp_path: Path) -> None:
    store = RuntimePointerStore(_settings(tmp_path))
    before = store.active_versions(("structure_policy", "rule_policy", "question_policy", "answer_policy"))
    result = build_targeted_calibration_pointer_decision(
        pointer_review=_ready_pointer_review(),
        operator_decision="defer",
        store=store,
        decision_id="unit-f5",
    )
    after = store.active_versions(("structure_policy", "rule_policy", "question_policy", "answer_policy"))

    assert result["version"] == "v30.targeted_calibration_pointer_decision.v1"
    assert result["decision"]["pointer_decision_recorded"] is True
    assert result["decision"]["operator_deferred_promotion"] is True
    assert result["decision"]["policy_pointer_promotion_allowed"] is False
    assert result["pointer_write_summary"]["pointer_write_performed"] is False
    assert result["pointer_write_summary"]["changed_pointer_count"] == 0
    assert result["operator_boundary"]["chart_fact_mutation_allowed"] is False
    assert before == after
    assert result["next_mainline_selection"]["task_id"] == "F6"


def test_targeted_calibration_pointer_decision_blocks_promotion_request_without_write_command(tmp_path: Path) -> None:
    result = build_targeted_calibration_pointer_decision(
        pointer_review=_ready_pointer_review(),
        operator_decision="request_promotion",
        store=RuntimePointerStore(_settings(tmp_path)),
        decision_id="unit-f5-blocked",
    )

    assert result["decision"]["pointer_decision_recorded"] is False
    assert result["decision"]["promotion_request_recorded"] is True
    assert "promotion_requires_separate_explicit_pointer_write_command" in result["decision"]["blockers"]
    assert result["pointer_write_summary"]["pointer_write_performed"] is False
    assert result["next_mainline_selection"]["task_id"] == "F5"
