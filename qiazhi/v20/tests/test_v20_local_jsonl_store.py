from __future__ import annotations

from fastapi.testclient import TestClient

from v20.interaction.feedback_record import record_feedback_analysis
from v20.server import app
from v20.storage.local_jsonl import LocalJsonlStore


def test_v20_local_jsonl_store_appends_redacted_feedback_only(tmp_path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    result = record_feedback_analysis(
        input_id="local.store",
        source_role="user",
        feedback_text="姓名: 张三，电话 010-12345678，我想看财",
        feature_ids=("feature.wealth.material_available",),
        store=store,
    )
    status = store.status()
    ledger_path = tmp_path / result["storage"]["relative_path"]
    text = ledger_path.read_text(encoding="utf-8")

    assert result["runtime_mutation"] is True
    assert result["analysis"]["runtime_mutation"] is False
    assert result["storage"]["runtime_mutation"] is True
    assert status["ledger_count"] == 1
    assert "张三" not in text
    assert "010-12345678" not in text
    assert "[number]" in text
    assert "ONLY_REDACTED_ANALYSIS_IS_PERSISTED" in result["guardrails"]


def test_v20_local_jsonl_store_rotates_oversized_ledger(tmp_path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path, max_ledger_bytes=240)
    first = store.append_record("feedback_ledger", {"text": "x" * 220})
    second = store.append_record("feedback_ledger", {"text": "y" * 220})
    status = store.status()
    active_path = tmp_path / second["relative_path"]
    rotated_path = tmp_path / second["rotated_relative_path"]

    assert first["rotated"] is False
    assert second["rotated"] is True
    assert active_path.exists()
    assert rotated_path.exists()
    assert active_path.name == "feedback_ledger.jsonl"
    assert rotated_path.name.startswith("feedback_ledger.")
    assert status["ledger_count"] == 2
    assert status["max_ledger_bytes"] == 240
    assert "LOCAL_JSONL_SIZE_BOUNDED" in second["guardrails"]


def test_v20_local_jsonl_status_endpoint_does_not_render_file_content(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    client = TestClient(app)
    record = client.post(
        "/api/v20/feedback/record",
        json={
            "input_id": "endpoint.record",
            "source_role": "analyst",
            "feedback_text": "名字: 李四，用神边界要清楚",
            "feature_ids": ["feature.useful_god.evidence_gate"],
        },
    ).json()
    status = client.get("/api/v20/storage/local-jsonl").json()
    text = str(status)

    assert record["runtime_mutation"] is True
    assert status["runtime_mutation"] is False
    assert status["ledger_count"] == 1
    assert "李四" not in text
    assert "NO_FILE_CONTENT_RENDERED" in status["guardrails"]
