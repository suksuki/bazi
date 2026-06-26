from __future__ import annotations

import json

from v20.learning.portrait_runtime_pointer import (
    PORTRAIT_ACTIVE_POINTER_VERSION,
    build_portrait_runtime_pointer,
    write_portrait_runtime_pointer_activate_candidate,
)
from v20.storage.local_jsonl import local_jsonl_store_from_env


def test_v20_portrait_runtime_pointer_blocks_without_artifact(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))

    pointer = build_portrait_runtime_pointer()

    assert pointer["status"] == "blocked"
    assert pointer["runtime_applied"] is False
    assert pointer["blocking_gate"] == "rule_portrait_batch_not_passed"


def test_v20_portrait_runtime_pointer_activates_candidate_from_batch(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    runtime = local_jsonl_store_from_env().runtime_dir
    batch_dir = runtime / "training" / "rule_portrait_batch"
    batch_dir.mkdir(parents=True, exist_ok=True)
    batch = {
        "version": "v20.rule_portrait_batch_report.v1",
        "status": "pass",
        "ok": True,
        "case_count": 2,
        "failure_count": 0,
        "case_results": [
            {
                "case_id": "case.wealth",
                "ok": True,
                "portrait_domains": ["wealth", "career"],
                "decision_domains": ["wealth"],
            },
            {
                "case_id": "case.relationship",
                "ok": True,
                "portrait_domains": ["relationship"],
                "decision_domains": ["relationship"],
            },
        ],
        "coverage_summary": {
            "version": "v20.rule_portrait_batch_coverage.v1",
            "portrait_domains": ["career", "relationship", "wealth"],
            "decision_domains_seen": ["relationship", "wealth"],
        },
    }
    (batch_dir / "latest.json").write_text(json.dumps(batch), encoding="utf-8")

    result = write_portrait_runtime_pointer_activate_candidate(source_role="system", reason="test")
    pointer = build_portrait_runtime_pointer()

    assert result["status"] == "candidate_active"
    assert result["runtime_mutation"] is True
    assert result["candidate"]["portrait_policy_count"] == 3
    assert pointer["status"] == "candidate_active"
    assert pointer["runtime_applied"] is True
    policy = pointer["policy_payload"]["portrait_axis_weight_policy"]
    assert {row["domain"] for row in policy} == {"career", "relationship", "wealth"}
    assert all(row["axis_weight_delta"] > 0 for row in policy)
    active_path = runtime / "training" / "portrait_policy_versions" / "active_pointer.json"
    active = json.loads(active_path.read_text(encoding="utf-8"))
    assert active["version"] == PORTRAIT_ACTIVE_POINTER_VERSION
