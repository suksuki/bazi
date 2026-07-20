from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from product.agent_case_store import (
    LegacyFormalWriteBlocked,
    MemoryAgentCaseStore,
)
from product.app import create_product_app
from product.legacy_usage import MemoryLegacyUsageStore
from product.product_store import MemoryProductStore
from product.theater_envelope import ProductExperienceEnvelopePort
from scripts.v50_audit_architecture_purification import audit


ROOT = Path(__file__).resolve().parents[1]


def test_retired_formal_shapes_cannot_be_persisted() -> None:
    store = MemoryAgentCaseStore()
    with pytest.raises(LegacyFormalWriteBlocked, match="legacy_formal_write_blocked:report"):
        store.save(case_id="case-legacy", user_id=None, profile_id=None, payload={"report": {"claim": "old"}})


def test_probe_history_is_derived_from_life_case_and_not_dual_written() -> None:
    store = MemoryAgentCaseStore()
    payload = {
        "case_belief_state": {"case_id": "case-one", "probe_history": [{"option_id": "legacy"}]},
        "life_case": {
            "reality_evidence": [
                {
                    "evidence_id": "evidence-one",
                    "source": "probe",
                    "source_ref": "probe-one",
                    "kind": "behavior",
                    "summary": "更倾向先验证再行动",
                    "domain": "whole_chart",
                    "recorded_at": "2026-07-18T00:00:00+00:00",
                    "structured_payload": {"option_id": "option-one"},
                }
            ]
        },
    }
    store.save(case_id="case-one", user_id="user-one", profile_id=None, payload=payload)
    assert "probe_history" not in store._cases["case-one"]["case_belief_state"]
    assert store.get(case_id="case-one")["workspace"]["probe_history"][0]["option_id"] == "option-one"


def test_experience_envelope_exposes_structured_four_pillars_without_reasoning() -> None:
    store = MemoryAgentCaseStore()
    store.save(
        case_id="case-envelope",
        user_id="user-envelope",
        profile_id=None,
        payload={
            "world": {
                "world_id": "world-envelope",
                "pillars": ["丁巳", "乙巳", "乙丑", "乙酉"],
                "facts": [
                    {
                        "category": "visible",
                        "payload": {"visible_ten_gods": [
                            {"slot": "year", "ten_god": "食神"},
                            {"slot": "month", "ten_god": "比肩"},
                            {"slot": "hour", "ten_god": "比肩"}
                        ]},
                    },
                    {
                        "category": "hidden_stems",
                        "payload": {"rows": [
                            {"slot": "year", "hidden_stems": ["丙", "戊", "庚"], "hidden_ten_gods": ["伤官", "正财", "正官"]},
                            {"slot": "month", "hidden_stems": ["丙", "戊", "庚"], "hidden_ten_gods": ["伤官", "正财", "正官"]},
                            {"slot": "day", "hidden_stems": ["己", "癸", "辛"], "hidden_ten_gods": ["偏财", "偏印", "七杀"]},
                            {"slot": "hour", "hidden_stems": ["辛"], "hidden_ten_gods": ["七杀"]}
                        ]},
                    },
                ],
            },
        },
    )
    envelope = ProductExperienceEnvelopePort(case_store=store).issue_envelope(
        participant_id="user-envelope",
        topic_id="baseline",
        topic_version="v1",
        disclosure_level="chart_facts",
        case_id="case-envelope",
    )
    assert envelope.mode == "chart_facts_only"
    assert [(item.stem, item.branch) for item in envelope.allowed_chart_facts] == [
        ("丁", "巳"), ("乙", "巳"), ("乙", "丑"), ("乙", "酉")
    ]
    assert envelope.allowed_chart_facts[0].hidden_stems[0].ten_god == "伤官"
    assert envelope.allowed_chart_facts[2].visible_ten_god == "日主"
    assert not envelope.approved_claims


def test_new_experience_routes_are_independent_and_legacy_usage_is_counted() -> None:
    usage = MemoryLegacyUsageStore()
    client = TestClient(
        create_product_app(
            product_store=MemoryProductStore(),
            agent_case_store=MemoryAgentCaseStore(),
            legacy_usage_store=usage,
        )
    )
    assert client.get("/experience").status_code == 200
    assert client.get("/app").status_code == 200
    assert usage.snapshot()[0]["route_key"] == "legacy-shell:index"


def test_architecture_purification_machine_audit_passes() -> None:
    result = audit()
    assert result["passed"], json.dumps(result, ensure_ascii=False, indent=2)
    script_import_check = next(
        item
        for item in result["checks"]
        if item["check"] == "production_code_does_not_import_scripts"
    )
    assert script_import_check["passed"]
    assert script_import_check["violations"] == []
    source = (ROOT / "apps/product/experience_shell/src/api.ts").read_text(encoding="utf-8")
    assert "/api/v50/agent" not in source
    assert "/api/v50/experience" in source
