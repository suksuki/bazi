from __future__ import annotations

from types import SimpleNamespace

from v30.validation.stage_a_release_gate_execution import (
    STAGE_A_RELEASE_GATE_EXECUTION_VERSION,
    build_stage_a_release_gate_execution,
)


def _authorization(*, authorized: bool = True) -> dict[str, object]:
    return {
        "version": "v30.explicit_release_gate_authorization.v1",
        "status": "completed" if authorized else "blocked",
        "decision": {
            "authorization_recorded": authorized,
            "decision_status": "rel_s2_stage_a_gates_authorized_pending_execution" if authorized else "blocked",
            "authorized_gate_ids": [
                "controlled_release_readiness",
                "synthetic_all",
                "518k_sample",
                "518k_shard",
            ]
            if authorized
            else [],
            "deferred_gate_ids": ["full_pytest", "live_llm_smoke", "real_env_smoke", "full_518k"],
            "runs_triggered": False,
            "external_release_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
        },
    }


def _controlled() -> dict[str, object]:
    return {
        "status": "completed",
        "decision": {
            "controlled_release_readiness_ready": True,
            "decision_status": "rel_s1_controlled_release_readiness_ready",
            "check_count": 6,
            "passed_check_count": 6,
            "controlled_trial_ready": True,
            "external_release_ready": False,
        },
    }


def _synthetic_all(*, passed: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        passed=passed,
        suite_id="v30.synthetic.all",
        case_count=38,
        passed_count=38 if passed else 37,
    )


def _corpus(mode: str, *, count: int, shard_ids: list[int] | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        promotion_signal="eligible",
        run_id=f"v30.518k.{mode}.test",
        mode=mode,
        case_count=count,
        shard_ids=shard_ids or [],
        artifact_uri=f"artifacts/{mode}.json",
        index_uri=f"artifacts/{mode}.index.json",
        artifact_record_id=f"{mode}-record",
        artifact_search_backend="json_fallback",
    )


def test_rel_s3_stage_a_execution_passes_authorized_gates() -> None:
    result = build_stage_a_release_gate_execution(
        authorization=_authorization(),
        gate_results={
            "controlled_release_readiness": _controlled(),
            "synthetic_all": _synthetic_all(),
            "518k_sample": _corpus("sample", count=8),
            "518k_shard": _corpus("shard", count=16, shard_ids=[7]),
        },
    )

    assert result["version"] == STAGE_A_RELEASE_GATE_EXECUTION_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["decision_status"] == "rel_s3_stage_a_gates_passed"
    assert result["decision"]["passed_gate_count"] == 4
    assert result["decision"]["external_release_allowed"] is False
    assert result["decision"]["full_pytest_run"] is False
    assert result["decision"]["live_llm_smoke_run"] is False
    assert result["decision"]["full_518k_run"] is False
    assert result["policy_boundary"]["policy_pointer_promotion_allowed"] is False
    assert result["next_mainline_selection"]["task_id"] == "REL-S4"


def test_rel_s3_blocks_when_authorization_missing() -> None:
    result = build_stage_a_release_gate_execution(
        authorization=_authorization(authorized=False),
        gate_results={},
    )

    assert result["status"] == "blocked"
    assert result["decision"]["decision_status"] == "rel_s3_stage_a_gates_blocked"
    assert "rel_s2_stage_a_authorization_missing" in result["decision"]["blockers"]
    assert "stage_a_gate_execution_missing" in result["decision"]["blockers"]
    assert set(result["decision"]["missing_gate_ids"]) == {
        "controlled_release_readiness",
        "synthetic_all",
        "518k_sample",
        "518k_shard",
    }


def test_rel_s3_records_failed_stage_a_gate() -> None:
    result = build_stage_a_release_gate_execution(
        authorization=_authorization(),
        gate_results={
            "controlled_release_readiness": _controlled(),
            "synthetic_all": _synthetic_all(passed=False),
            "518k_sample": _corpus("sample", count=8),
            "518k_shard": _corpus("shard", count=16, shard_ids=[7]),
        },
    )

    assert result["status"] == "blocked"
    assert "synthetic_all" in result["decision"]["failed_gate_ids"]
    assert result["next_mainline_selection"]["task_id"] == "REL-S3-FR"
