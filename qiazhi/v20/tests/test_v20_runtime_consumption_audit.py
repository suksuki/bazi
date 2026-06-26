from __future__ import annotations

from v20.ops.runtime_consumption_audit import build_runtime_consumption_audit
from v20.tests.support_paths import read_v20_text


def test_v20_runtime_consumption_audit_exposes_pointer_families() -> None:
    audit = build_runtime_consumption_audit()
    rows = {row["family"]: row for row in audit["families"]}

    assert audit["version"] == "v20.runtime_consumption_audit.v1"
    assert audit["family_count"] == 7
    assert audit["consumed_family_count"] == 7
    assert audit["pointer_effect_summary"]["version"] == "v20.runtime_pointer_effect_summary.v1"
    assert audit["pointer_effect_summary"]["active_pointer_count"] >= 0
    assert audit["runtime_mutation"] is False
    assert {"orchestrator", "role_view", "question", "corpus", "rule", "portrait", "knowledge"} <= set(rows)
    assert rows["question"]["runtime_consumer_status"] == "consumed"
    assert rows["corpus"]["runtime_consumer_status"] == "consumed"
    assert rows["rule"]["runtime_consumer_status"] == "consumed"
    assert rows["portrait"]["runtime_consumer_status"] == "consumed"
    assert rows["knowledge"]["runtime_consumer_status"] == "consumed"
    assert rows["knowledge"]["before_after_effect"]["version"] == "v20.runtime_pointer_before_after_effect.v1"
    assert rows["knowledge"]["effect_scope"]
    assert audit["status"] == "complete"
    assert audit["next_actions"] == []


def test_v20_runtime_consumption_audit_endpoint_is_declared() -> None:
    server_text = read_v20_text("server.py")

    assert "/api/v20/admin/runtime-consumption-audit" in server_text
    assert "build_runtime_consumption_audit" in server_text
