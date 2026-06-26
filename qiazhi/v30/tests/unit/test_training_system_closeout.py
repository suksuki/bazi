from __future__ import annotations

from v30.validation.training_system_closeout import (
    CORE_POLICY_FAMILIES,
    build_training_system_closeout,
)


def test_training_system_closeout_accepts_complete_training_loop() -> None:
    result = build_training_system_closeout(
        bt3_failure_routing=_bt3_ready(),
        auto_training_result=_training_result(),
        policy_artifacts=_artifacts(),
        runtime_pointers=_pointers(),
        promotion_lineage=_lineage(),
    )

    assert result["version"] == "v30.training_system_closeout.v1"
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "bt4_training_system_closeout_ready"
    assert result["decision"]["training_completion"] == 97
    assert result["training_summary"]["promoted_count"] == 4
    assert result["artifact_summary"]["question_policy_comparison_ready"] is True
    assert result["runtime_pointer_summary"]["rollback_pointer_count"] == 4
    assert result["promotion_lineage_summary"]["lineage_count"] == 4
    assert result["future_policy_boundary"]["future_families_promoted_by_default"] is False
    assert result["policy_boundary"]["training_signal_may_change_chart_facts"] is False
    assert result["next_mainline_selection"]["task_id"] == "BT5"


def test_training_system_closeout_blocks_future_family_promotion() -> None:
    training = _training_result()
    training["families"] = [*training["families"], "answer_policy"]
    training["candidates"] = [*training["candidates"], {"candidate_id": "bt4.answer", "family": "answer_policy"}]
    training["promotions"] = [
        *training["promotions"],
        {"candidate_id": "bt4.answer", "family": "answer_policy", "promoted": True, "artifact_id": "answer_policy.bt4"},
    ]

    result = build_training_system_closeout(
        bt3_failure_routing=_bt3_ready(),
        auto_training_result=training,
        policy_artifacts=_artifacts(),
        runtime_pointers=_pointers(),
        promotion_lineage=_lineage(),
    )

    assert result["status"] == "blocked"
    assert "auto_training_applies_core_policy_families" in result["decision"]["failed_check_ids"]
    assert "future_policy_families_not_promoted_by_default" in result["decision"]["failed_check_ids"]
    assert result["future_policy_boundary"]["promoted_future_families"] == ["answer_policy"]
    assert result["next_mainline_selection"]["task_id"] == "BT4-FR"


def test_training_system_closeout_blocks_missing_rollback_and_lineage() -> None:
    pointers = _pointers()
    pointers["question_policy"]["rollback_pointer"] = {}
    lineage = _lineage()
    lineage["question_policy"]["lineage_id"] = ""

    result = build_training_system_closeout(
        bt3_failure_routing=_bt3_ready(),
        auto_training_result=_training_result(),
        policy_artifacts=_artifacts(),
        runtime_pointers=pointers,
        promotion_lineage=lineage,
    )

    assert result["status"] == "blocked"
    assert "runtime_pointers_and_rollback_ready" in result["decision"]["failed_check_ids"]
    assert "question_comparison_and_lineage_ready" in result["decision"]["failed_check_ids"]


def _bt3_ready() -> dict[str, object]:
    return {
        "version": "v30.brain_failure_route.v1",
        "status": "completed",
        "decision": {
            "brain_failure_routing_ready": True,
            "decision_status": "bt3_brain_failure_routing_ready",
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "full_pytest_required": False,
            "full_518k_required": False,
        },
    }


def _training_result() -> dict[str, object]:
    families = list(CORE_POLICY_FAMILIES)
    return {
        "training_run_id": "bt4-closeout",
        "status": "applied",
        "auto_apply": True,
        "families": families,
        "candidates": [
            {"candidate_id": f"bt4-closeout.{family}", "family": family}
            for family in families
        ],
        "promotions": [
            {
                "candidate_id": f"bt4-closeout.{family}",
                "family": family,
                "promoted": True,
                "artifact_id": f"{family}.bt4-closeout.{family}",
            }
            for family in families
        ],
        "active_policy_versions": {
            family: f"{family}.bt4-closeout.{family}"
            for family in families
        },
        "metrics": {
            "candidate_count": 4,
            "promoted_count": 4,
            "failed_count": 0,
            "training_signal_count": 35,
            "synthetic_signal_case_count": 95,
        },
        "failures": [],
    }


def _artifacts() -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for family in CORE_POLICY_FAMILIES:
        validation = {
            "synthetic": {"suite_id": f"v30.synthetic.promotion.{family}.all", "passed": True},
            "corpus_518k_sample": {"run_id": f"{family}.sample", "promotion_signal": "eligible"},
        }
        if family == "question_policy":
            validation["question_policy_comparison"] = {
                "version": "v30.question_policy_comparison.v1",
                "candidate_id": "bt4-closeout.question_policy",
                "artifact_uri": "/tmp/question-comparison.json",
            }
        rows[family] = {
            "artifact_id": f"{family}.bt4-closeout.{family}",
            "candidate_id": f"bt4-closeout.{family}",
            "payload": {
                "mode": "auto_apply_training",
                "family": family,
                "training_signals": [{"signal_id": "v30.training_signal.question_dialogue_outcome"}],
                "weights": {"*": 1.0},
            },
            "validation_summary": validation,
            "metrics": {
                "synthetic_case_count": 95,
                "synthetic_passed_count": 95,
                "corpus_518k_sample_case_count": 8,
                "corpus_518k_promotion_signal": "eligible",
            },
        }
    return rows


def _pointers() -> dict[str, dict[str, object]]:
    return {
        family: {
            "family": family,
            "active_artifact_id": f"{family}.bt4-closeout.{family}",
            "previous_artifact_id": f"{family}.v30-baseline",
            "validation_run_id": f"validation.{family}",
            "status": "active",
            "promotion_reason": "synthetic_all_and_518k_sample_passed",
            "rollback_pointer": {
                "family": family,
                "active_artifact_id": f"{family}.v30-baseline",
            },
            "updated_by": "v30.policy.promotion",
        }
        for family in CORE_POLICY_FAMILIES
    }


def _lineage() -> dict[str, dict[str, object]]:
    return {
        family: {
            "lineage_id": f"{family}:bt4:lineage",
            "active_artifact_id": f"{family}.bt4-closeout.{family}",
            "candidate_id": f"bt4-closeout.{family}",
            "validation_artifacts": [{"family": "518k_validation", "artifact_uri": "/tmp/518k.json"}],
            "rollback_pointer": {
                "family": family,
                "active_artifact_id": f"{family}.v30-baseline",
            },
            "boundaries": ["promotion_lineage_is_diagnostic_not_policy_mutation"],
        }
        for family in CORE_POLICY_FAMILIES
    }
