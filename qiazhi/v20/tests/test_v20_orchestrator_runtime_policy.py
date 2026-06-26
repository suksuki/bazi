from __future__ import annotations

import json

from v20.orchestrator.runtime_policy import (
    build_runtime_policy_pointer,
    write_runtime_policy_activate_latest_candidate,
    write_runtime_policy_rollback,
)
from v20.storage.local_jsonl import LocalJsonlStore
from v20.storage.postgres_ledger_import import build_ledger_postgres_import_plan


def test_v20_runtime_policy_pointer_uses_baseline_without_candidate(tmp_path) -> None:
    pointer = build_runtime_policy_pointer(
        brain_memory_signal={"memory_key": "brain.memory.test"},
        store=LocalJsonlStore(runtime_dir=tmp_path),
    )

    assert pointer["status"] == "baseline_active_fast_track_ready"
    assert pointer["active_policy_version"] == "v20.orchestrator_policy.baseline.v1"
    assert pointer["candidate_policy_version"] == ""
    assert pointer["rollback_policy_version"] == "v20.orchestrator_policy.baseline.v1"
    assert pointer["candidate_status"] == "not_built"
    assert pointer["runtime_applied"] is False
    assert pointer["runtime_mutation"] is False


def test_v20_runtime_policy_pointer_auto_activates_fast_track_candidate(tmp_path) -> None:
    artifact_dir = tmp_path / "training" / "orchestrator_policy_versions"
    artifact_dir.mkdir(parents=True)
    candidate = {
        "version": "v20.orchestrator_policy_version_candidate.v1",
        "status": "ready_for_replay",
        "candidate_policy_version": "v20.orchestrator_policy.candidate.test",
        "candidate_count": 3,
        "runtime_allowed": True,
    }
    (artifact_dir / "latest.json").write_text(json.dumps(candidate), encoding="utf-8")

    pointer = build_runtime_policy_pointer(
        brain_memory_signal={"memory_key": "brain.memory.test"},
        store=LocalJsonlStore(runtime_dir=tmp_path),
    )

    assert pointer["status"] == "fast_track_candidate_active"
    assert pointer["active_policy_version"] == "v20.orchestrator_policy.candidate.test"
    assert pointer["candidate_policy_version"] == "v20.orchestrator_policy.candidate.test"
    assert pointer["rollback_policy_version"] == "v20.orchestrator_policy.baseline.v1"
    assert pointer["candidate_status"] == "ready_for_replay"
    assert pointer["candidate_count"] == 3
    assert pointer["runtime_applied"] is True
    assert pointer["runtime_effect"] == "version_pointer_active"
    assert pointer["runtime_mutation"] is False


def test_v20_runtime_policy_rollback_overrides_latest_candidate(tmp_path) -> None:
    artifact_dir = tmp_path / "training" / "orchestrator_policy_versions"
    artifact_dir.mkdir(parents=True)
    candidate = {
        "version": "v20.orchestrator_policy_version_candidate.v1",
        "status": "ready_for_replay",
        "candidate_policy_version": "v20.orchestrator_policy.candidate.test",
        "candidate_count": 1,
        "runtime_allowed": True,
        "policy_payload": {
            "mainline_arbitration_weight_policy": (
                {"runtime_allowed": True, "suggested_action": "increase_primary_stability_weight"},
            )
        },
    }
    (artifact_dir / "latest.json").write_text(json.dumps(candidate), encoding="utf-8")
    store = LocalJsonlStore(runtime_dir=tmp_path)

    rollback = write_runtime_policy_rollback(source_role="admin", reason="bad candidate", store=store)
    pointer = build_runtime_policy_pointer(brain_memory_signal={"memory_key": "brain.memory.test"}, store=store)

    assert rollback["version"] == "v20.orchestrator_policy_rollback_result.v1"
    assert rollback["status"] == "rolled_back"
    assert rollback["previous_active_policy_version"] == "v20.orchestrator_policy.candidate.test"
    assert rollback["runtime_mutation"] is True
    assert pointer["status"] == "rollback_baseline_active"
    assert pointer["active_policy_version"] == "v20.orchestrator_policy.baseline.v1"
    assert pointer["candidate_policy_version"] == "v20.orchestrator_policy.candidate.test"
    assert pointer["rollout_mode"] == "rollback_to_baseline"
    assert pointer["runtime_applied"] is False
    assert pointer["runtime_effect"] == "rollback_pointer_active"
    assert pointer["policy_payload"] == {}
    assert (tmp_path / "ledger" / "orchestrator_policy_rollback_audit.jsonl").exists()
    plan = build_ledger_postgres_import_plan(ledger_name="orchestrator_policy_rollback_audit", store=store)
    assert plan["status"] == "dry_run"
    assert plan["record_count"] == 1


def test_v20_runtime_policy_can_reactivate_latest_candidate_after_rollback(tmp_path) -> None:
    artifact_dir = tmp_path / "training" / "orchestrator_policy_versions"
    artifact_dir.mkdir(parents=True)
    candidate = {
        "version": "v20.orchestrator_policy_version_candidate.v1",
        "status": "ready_for_replay",
        "candidate_policy_version": "v20.orchestrator_policy.candidate.test",
        "candidate_count": 1,
        "runtime_allowed": True,
        "policy_payload": {"question_focus_policy": ({"runtime_allowed": True, "domain": "career"},)},
    }
    (artifact_dir / "latest.json").write_text(json.dumps(candidate), encoding="utf-8")
    store = LocalJsonlStore(runtime_dir=tmp_path)

    write_runtime_policy_rollback(source_role="admin", store=store)
    activated = write_runtime_policy_activate_latest_candidate(source_role="admin", reason="restore", store=store)
    pointer = build_runtime_policy_pointer(brain_memory_signal={}, store=store)

    assert activated["version"] == "v20.orchestrator_policy_activation_result.v1"
    assert activated["status"] == "latest_candidate_active"
    assert activated["previous_active_policy_version"] == "v20.orchestrator_policy.baseline.v1"
    assert pointer["status"] == "fast_track_candidate_active"
    assert pointer["active_policy_version"] == "v20.orchestrator_policy.candidate.test"
    assert pointer["runtime_applied"] is True
    assert pointer["consumable_policy_types"] == ["question_focus_policy"]
