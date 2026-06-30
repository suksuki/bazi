from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from v40.api.app import API_PREFIX, create_app
from v40.storage import resolve_v40_database_config


def test_v40_evaluation_training_and_release_gate_api_persist_assets() -> None:
    if resolve_v40_database_config() is None:
        pytest.skip("V40_DATABASE_URL is not configured")

    client = TestClient(create_app())

    case_payload = {
        "case_id": "case.phase5.career.001",
        "case_type": "golden",
        "user_question": "今年事业适合稳定还是突破？",
        "topic": "career",
        "expected_verdicts": [
            {
                "topic": "career",
                "expected_keywords": ["事业", "稳定", "突破"],
                "min_evidence_count": 1,
            }
        ],
        "forbidden_assertions": [
            {
                "text": "保证升职发财",
                "severity": "high",
                "reason": "overclaim",
            }
        ],
    }
    case_response = client.post(f"{API_PREFIX}/evaluation/cases", json=case_payload)
    assert case_response.status_code == 200
    assert case_response.json()["saved"] is True
    case_list = client.get(f"{API_PREFIX}/evaluation/cases?limit=5").json()["cases"]
    assert any(case["case_id"] == "case.phase5.career.001" for case in case_list)

    label_payload = {
        "event_id": "label.phase5.career.001",
        "reading_id": "v40-reading-phase5-001",
        "source": "practitioner_selection",
        "target_type": "verdict",
        "target_ids": ["verdict.career.path"],
        "label": "matches_reality",
        "strength": 0.82,
        "confidence": 0.78,
        "reason": "命理师确认事业判断贴合反馈",
        "created_by_role": "practitioner",
        "local_only": True,
    }
    label_response = client.post(f"{API_PREFIX}/training/labels", json=label_payload)
    assert label_response.status_code == 200
    assert label_response.json()["local_only"] is True
    label_list = client.get(
        f"{API_PREFIX}/training/labels?reading_id=v40-reading-phase5-001&limit=5"
    ).json()["events"]
    assert any(event["event_id"] == "label.phase5.career.001" for event in label_list)

    gate_payload = {
        "gate_id": "gate.phase5.candidate.001",
        "candidate_version": "v40-alpha-phase5",
        "fact_gate_passed": True,
        "golden_case_gate_passed": False,
        "overclaim_gate_passed": True,
        "advice_grounding_gate_passed": True,
        "probe_yield_gate_passed": False,
        "llm_boundary_gate_passed": True,
        "leakage_gate_passed": True,
        "regression_failures": ["golden_case_score_below_threshold"],
        "recommendation": "needs_review",
        "production_write_allowed": False,
    }
    gate_response = client.post(f"{API_PREFIX}/release-gates", json=gate_payload)
    assert gate_response.status_code == 200
    assert gate_response.json()["production_write_allowed"] is False
    gate_list = client.get(f"{API_PREFIX}/release-gates?limit=5").json()["gates"]
    assert any(gate["gate_id"] == "gate.phase5.candidate.001" for gate in gate_list)


def test_v40_phase5_repository_sql_is_v40_only() -> None:
    source = Path("v40/storage/postgres.py").read_text(encoding="utf-8")
    assert "v40_evaluation_cases" in source
    assert "v40_training_label_events" in source
    assert "v40_release_gates" in source
    assert "INSERT INTO v30_" not in source
    assert "UPDATE v30_" not in source
    assert "FROM v30_" not in source
