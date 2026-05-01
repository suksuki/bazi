from __future__ import annotations

from fastapi.testclient import TestClient

from v20.interaction.portrait_calibration import analyze_portrait_calibration, record_portrait_calibration
from v20.server import app
from v20.storage.local_jsonl import LocalJsonlStore


def test_v20_portrait_calibration_is_signal_only() -> None:
    report = analyze_portrait_calibration(
        input_id="portrait.case",
        feature_id="feature.useful_god.candidate_paths",
        source_role="analyst",
        signal="needs_review",
        note="姓名: 张三，用神候选证据还要补充，电话 010-12345678",
    )
    text = str(report)

    assert report["runtime_mutation"] is False
    assert report["raw_note_retained"] is False
    assert "张三" not in text
    assert "010-12345678" not in text
    assert report["calibration_signal"]["signal"] == "needs_review"
    assert "NO_ANSWER_CONCLUSION_MUTATION" in report["guardrails"]


def test_v20_portrait_calibration_record_is_append_only(tmp_path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    result = record_portrait_calibration(
        input_id="portrait.record",
        feature_id="feature.element.balance_distribution",
        source_role="user",
        signal="confirm",
        note="名字: 李四，五行摘要符合我的理解",
        store=store,
    )
    status = store.status()
    text = (tmp_path / result["storage"]["relative_path"]).read_text(encoding="utf-8")

    assert result["runtime_mutation"] is True
    assert result["analysis"]["runtime_mutation"] is False
    assert status["ledger_count"] == 1
    assert "李四" not in text
    assert "NO_RUNTIME_FEATURE_MUTATION" in result["guardrails"]


def test_v20_portrait_calibration_endpoints_are_guarded(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    client = TestClient(app)
    analyzed = client.post(
        "/api/v20/portrait/calibration/analyze",
        json={
            "input_id": "portrait.endpoint",
            "feature_id": "feature.useful_god.candidate_paths",
            "source_role": "analyst",
            "signal": "evidence_gap",
            "note": "候选路径需要更多证据",
        },
    ).json()
    recorded = client.post(
        "/api/v20/portrait/calibration/record",
        json={
            "input_id": "portrait.endpoint",
            "feature_id": "feature.useful_god.candidate_paths",
            "source_role": "analyst",
            "signal": "evidence_gap",
            "note": "候选路径需要更多证据",
        },
    ).json()

    assert analyzed["runtime_mutation"] is False
    assert recorded["runtime_mutation"] is True
    assert recorded["storage"]["ledger_name"] == "portrait_calibration_ledger"
