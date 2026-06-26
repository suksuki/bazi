from __future__ import annotations

import json

from v20.learning.rule_runtime_pointer import (
    RULE_ACTIVE_POINTER_VERSION,
    build_rule_runtime_pointer,
    write_rule_runtime_pointer_activate_candidate,
)
from v20.storage.local_jsonl import local_jsonl_store_from_env


def test_v20_rule_runtime_pointer_blocks_without_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))

    pointer = build_rule_runtime_pointer()

    assert pointer["status"] == "blocked"
    assert pointer["runtime_applied"] is False
    assert pointer["blocking_gate"] == "rule_replay_eval_not_ready"


def test_v20_rule_runtime_pointer_activates_candidate_from_replay_and_registry(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    runtime = local_jsonl_store_from_env().runtime_dir
    replay_dir = runtime / "training" / "rule_replay_eval"
    registry_dir = runtime / "training" / "decision_registry_iteration"
    replay_dir.mkdir(parents=True, exist_ok=True)
    registry_dir.mkdir(parents=True, exist_ok=True)
    replay = {
        "version": "v20.rule_replay_eval_report.v1",
        "status": "ready",
        "runtime_activation_count": 1,
        "evaluations": [
            {
                "rule_key": "rule.test.wealth_capacity",
                "domain": "wealth",
                "subcondition_count": 2,
                "counterexample_signal_count": 1,
                "runtime_activation": True,
            }
        ],
    }
    registry = {
        "version": "v20.decision_registry_iteration_report.v1",
        "status": "ready",
        "runtime_activation_count": 1,
        "records": [
            {
                "source_rule_key": "rule.test.wealth_capacity",
                "runtime_allowed": True,
            }
        ],
    }
    (replay_dir / "latest.json").write_text(json.dumps(replay), encoding="utf-8")
    (registry_dir / "latest.json").write_text(json.dumps(registry), encoding="utf-8")

    result = write_rule_runtime_pointer_activate_candidate(source_role="system", reason="test")
    pointer = build_rule_runtime_pointer()

    assert result["status"] == "candidate_active"
    assert result["runtime_mutation"] is True
    assert result["candidate"]["rule_policy_count"] == 1
    assert pointer["status"] == "candidate_active"
    assert pointer["runtime_applied"] is True
    assert pointer["policy_payload"]["rule_weight_policy"][0]["rule_key"] == "rule.test.wealth_capacity"
    active_path = runtime / "training" / "rule_policy_versions" / "active_pointer.json"
    active = json.loads(active_path.read_text(encoding="utf-8"))
    assert active["version"] == RULE_ACTIVE_POINTER_VERSION
