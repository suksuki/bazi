from __future__ import annotations

from pathlib import Path

from v30.config import V30Settings
from v30.policy import PromotionResult, RuntimePointerStore, make_baseline_candidate, quarantine_failed_candidate
from v30.validation.training_candidate_quarantine import build_training_candidate_quarantine


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


def test_quarantine_failed_candidate_persists_record_without_pointer_write(tmp_path: Path) -> None:
    store = RuntimePointerStore(_settings(tmp_path))
    before = store.load_pointer("question_policy")
    candidate = make_baseline_candidate(
        candidate_id="failed-question-policy",
        family="question_policy",
        payload={
            "mode": "auto_apply_training",
            "family": "question_policy",
            "weights": {"topic_weights": {"hidden_factor": 99.0}},
            "training_signals": [{"signal_id": "v30.training_signal.question_dialogue_outcome"}],
        },
        change_summary="failed question policy candidate",
    )
    promotion = PromotionResult(
        candidate_id=candidate.candidate_id,
        family=candidate.family,
        promoted=False,
        validation_run_id="v30.synthetic.failed+v30.518k.sample.failed",
        failures=["visible_next_question_regression"],
    )

    record = quarantine_failed_candidate(
        candidate=candidate,
        promotion=promotion,
        store=store,
        source_signals=candidate.payload["training_signals"],
    )
    after = store.load_pointer("question_policy")

    assert record.version == "v30.training_candidate_quarantine_record.v1"
    assert record.status == "quarantined"
    assert record.candidate_id == "failed-question-policy"
    assert record.failed_validation_ids == ["v30.synthetic.failed", "v30.518k.sample.failed"]
    assert record.rollback_target_pointer["active_artifact_id"] == before.active_artifact_id
    assert record.pointer_unchanged is True
    assert after.active_artifact_id == before.active_artifact_id
    assert record.artifact_uri
    assert Path(record.artifact_uri).exists()


def test_training_candidate_quarantine_accepts_last_good_runtime() -> None:
    result = build_training_candidate_quarantine(
        bt4_training_closeout=_bt4_ready(),
        quarantine_record=_quarantine_record(),
        pointer_before=_pointer(),
        pointer_after=_pointer(),
        runtime_summary={
            "reading_id": "bt5-runtime",
            "question_policy_version": "question_policy.v30-baseline",
            "recommended_question_count": 3,
            "chart_status": "ready",
        },
    )

    assert result["version"] == "v30.training_candidate_quarantine.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "bt5_training_candidate_quarantine_ready"
    assert result["decision"]["training_completion"] == 99
    assert result["quarantine_summary"]["record_id"] == "question_policy.failed.quarantine"
    assert result["runtime_pointer_summary"]["pointer_unchanged"] is True
    assert result["runtime_last_good_summary"]["runtime_uses_last_good_pointer"] is True
    assert result["next_mainline_selection"]["task_id"] == "BT6"


def test_training_candidate_quarantine_blocks_missing_failed_validation_and_pointer_drift() -> None:
    pointer_after = _pointer()
    pointer_after["active_artifact_id"] = "question_policy.failed"
    record = _quarantine_record()
    record["failed_validation_ids"] = []
    record["pointer_unchanged"] = False

    result = build_training_candidate_quarantine(
        bt4_training_closeout=_bt4_ready(),
        quarantine_record=record,
        pointer_before=_pointer(),
        pointer_after=pointer_after,
        runtime_summary={
            "reading_id": "bt5-runtime",
            "question_policy_version": "question_policy.failed",
            "recommended_question_count": 3,
            "chart_status": "ready",
        },
    )

    assert result["status"] == "blocked"
    assert "source_signals_and_failed_validations_recorded" in result["decision"]["failed_check_ids"]
    assert "rollback_target_and_artifact_recorded" in result["decision"]["failed_check_ids"]
    assert "pointer_stays_on_last_good_artifact" in result["decision"]["failed_check_ids"]
    assert result["next_mainline_selection"]["task_id"] == "BT5-FR"


def _bt4_ready() -> dict[str, object]:
    return {
        "version": "v30.training_system_closeout.v1",
        "status": "completed",
        "decision": {
            "training_system_closeout_ready": True,
            "decision_status": "bt4_training_system_closeout_ready",
            "training_completion": 97,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "full_pytest_required": False,
            "full_518k_required": False,
        },
    }


def _pointer() -> dict[str, object]:
    return {
        "family": "question_policy",
        "active_artifact_id": "question_policy.v30-baseline",
        "active_artifact_version": "v30.policy_artifact.v1",
        "previous_artifact_id": "",
        "status": "active",
    }


def _quarantine_record() -> dict[str, object]:
    return {
        "version": "v30.training_candidate_quarantine_record.v1",
        "record_id": "question_policy.failed.quarantine",
        "candidate_id": "failed",
        "family": "question_policy",
        "status": "quarantined",
        "source_signal_ids": [
            "v30.training_signal.question_dialogue_outcome",
            "v30.training_signal.interaction_loop_quality",
        ],
        "source_signal_count": 2,
        "failed_validation_ids": ["v30.synthetic.failed", "v30.518k.sample.failed"],
        "failures": ["visible_next_question_regression", "question_policy_distribution_drift"],
        "rollback_target_pointer": {
            "family": "question_policy",
            "active_artifact_id": "question_policy.v30-baseline",
            "active_artifact_version": "v30.policy_artifact.v1",
        },
        "pointer_unchanged": True,
        "artifact_uri": "/tmp/question_policy.failed.quarantine.json",
        "remediation_route": {
            "route_id": "route.training_candidate_quarantine",
            "runtime_pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
    }
