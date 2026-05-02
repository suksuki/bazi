from __future__ import annotations

from fastapi.testclient import TestClient

from v20.api.runtime import run_runtime_from_pillars
from v20.interaction.portrait_ontology import portrait_ontology_manifest
from v20.interaction.portrait_calibration import analyze_portrait_calibration, record_portrait_calibration
from v20.interaction.practitioner_calibration import (
    PractitionerControlSelection,
    analyze_practitioner_calibration,
    record_practitioner_calibration,
)
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


def test_v20_practitioner_calibration_is_structured_signal_only() -> None:
    report = analyze_practitioner_calibration(
        input_id="practitioner.case",
        source_role="analyst",
        selections=(
            PractitionerControlSelection(
                control_key="control.day_master_strength",
                option="中和偏弱",
                source_decision_keys=("decision.strength.day_master_capacity",),
            ),
        ),
    )

    assert report["runtime_mutation"] is False
    assert report["selection_count"] == 1
    assert report["training_signals"][0]["runtime_allowed"] is False
    assert report["training_signals"][0]["target"] == "decision_parameters.strength_capacity"
    assert "BUTTON_OR_SELECT_ONLY" in report["guardrails"]
    assert "NO_FREE_TEXT_CORE_DECISION" in report["guardrails"]


def test_v20_practitioner_calibration_record_is_append_only(tmp_path) -> None:
    store = LocalJsonlStore(runtime_dir=tmp_path)
    result = record_practitioner_calibration(
        input_id="practitioner.record",
        source_role="analyst",
        selections=(
            PractitionerControlSelection(
                control_key="control.wealth_capacity",
                option="需扶身",
                source_decision_keys=("decision.wealth.capacity",),
            ),
        ),
        store=store,
    )
    status = store.status()
    text = (tmp_path / result["storage"]["relative_path"]).read_text(encoding="utf-8")

    assert result["runtime_mutation"] is True
    assert result["analysis"]["runtime_mutation"] is False
    assert status["ledger_count"] == 1
    assert "practitioner_calibration_ledger" in text
    assert "NO_RUNTIME_RULE_MUTATION" in result["guardrails"]


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


def test_v20_practitioner_calibration_endpoints_are_guarded(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    client = TestClient(app)
    analyzed = client.post(
        "/api/v20/practitioner/calibration/analyze",
        json={
            "input_id": "practitioner.endpoint",
            "source_role": "analyst",
            "selections": [
                {
                    "control_key": "control.pattern_status",
                    "option": "候选",
                    "source_decision_keys": ["decision.pattern.status"],
                }
            ],
        },
    ).json()
    recorded = client.post(
        "/api/v20/practitioner/calibration/record",
        json={
            "input_id": "practitioner.endpoint",
            "source_role": "analyst",
            "selections": [
                {
                    "control_key": "control.pattern_status",
                    "option": "候选",
                    "source_decision_keys": ["decision.pattern.status"],
                }
            ],
        },
    ).json()
    invalid = client.post(
        "/api/v20/practitioner/calibration/analyze",
        json={
            "input_id": "practitioner.invalid",
            "source_role": "analyst",
            "selections": [
                {
                    "control_key": "control.pattern_status",
                    "option": "自由输入",
                    "source_decision_keys": ["decision.pattern.status"],
                }
            ],
        },
    )

    assert analyzed["runtime_mutation"] is False
    assert recorded["runtime_mutation"] is True
    assert recorded["storage"]["ledger_name"] == "practitioner_calibration_ledger"
    assert invalid.status_code == 400


def test_v20_portrait_projection_uses_decision_states_as_runtime_source() -> None:
    result = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="portrait.knowledge")
    projection = result["decision_report"]["portrait_projection"]
    strength_axis = next(row for row in projection["axes"] if row["domain"] == "strength")

    assert "dynamic_portrait" not in result
    assert projection["axis_source"] == "DecisionState+MainlineDecision+TopicProjection"
    assert projection["axis_count"] >= 1
    assert strength_axis["feature_ids"]
    assert "PORTRAIT_IS_DECISION_STATE_PROJECTION" in projection["guardrails"]
    assert "NO_PORTRAIT_DRIVEN_FORTUNE_VERDICT" in projection["guardrails"]


def test_v20_portrait_ontology_endpoint_is_contract_only() -> None:
    client = TestClient(app)
    manifest = portrait_ontology_manifest()
    endpoint = client.get("/api/v20/portrait/ontology").json()

    assert endpoint == manifest
    assert endpoint["runtime_mutation"] is False
    assert endpoint["source_policy"] == "dynamic_rule_decision_supported"
    assert "direct_personality_verdict" in endpoint["forbidden_knowledge_usage"]
