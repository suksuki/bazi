from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app


ROOT = Path(__file__).resolve().parents[1]


def test_v40_health_and_contracts_are_independent() -> None:
    client = TestClient(create_app())

    health = client.get(f"{API_PREFIX}/health").json()
    assert health["ok"] is True
    assert health["package"] == "v40"
    assert health["api_prefix"] == "/api/v40"
    assert health["database_boundary"] == "qiazhi_v40"
    assert health["postgres_table_prefix"] == "v40_"
    assert health["v30_runtime_import_allowed"] is False

    contracts = client.get(f"{API_PREFIX}/contracts").json()
    assert contracts["version"] == "v40.contract_manifest.v1"
    assert contracts["boundaries"]["v30_runtime_import_allowed"] is False
    assert "RuntimeSignal" in contracts["signal"]
    assert "TrainingImpactDiff" in contracts["training"]


def test_v40_shadow_compare_endpoint_accepts_plain_json_export_only() -> None:
    client = TestClient(create_app())
    payload = json.loads((ROOT / "tests" / "fixtures" / "v30_export_minimal.json").read_text(encoding="utf-8"))

    response = client.post(f"{API_PREFIX}/shadow-compare", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["version"] == "v40.shadow_compare_response.v1"
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False
    assert body["runtime"]["version"] == "v40.runtime_result.v1"
    assert body["runtime"]["v30_runtime_imported"] is False
    assert body["compare"]["import_coverage_rate"] == 1.0
    assert body["compare"]["product_projection_ready"] is True


def test_v40_schema_uses_only_v40_prefixed_tables() -> None:
    schema = (ROOT / "deploy" / "postgres_v40_schema.sql").read_text(encoding="utf-8")
    assert "v30_" not in schema
    table_lines = [
        line.strip()
        for line in schema.splitlines()
        if line.strip().upper().startswith("CREATE TABLE")
    ]
    assert table_lines
    assert all(" v40_" in line for line in table_lines)
