from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.storage import V40PostgresRepository, resolve_v40_database_config


ROOT = Path(__file__).resolve().parents[1]


def test_v40_repository_config_stays_private() -> None:
    config = resolve_v40_database_config()
    if config is None:
        pytest.skip("V40_DATABASE_URL is not configured")

    assert config.dsn
    assert config.source in {"env:V40_DATABASE_URL", ".env.v40.local"}


def test_v40_shadow_compare_can_persist_and_list_history() -> None:
    if resolve_v40_database_config() is None:
        pytest.skip("V40_DATABASE_URL is not configured")

    client = TestClient(create_app())
    payload = json.loads((ROOT / "tests" / "fixtures" / "v30_export_minimal.json").read_text(encoding="utf-8"))

    response = client.post(f"{API_PREFIX}/shadow-compare?persist=true", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["persisted"] is True
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False

    runs_response = client.get(f"{API_PREFIX}/shadow-compare/runs?limit=5")
    assert runs_response.status_code == 200
    runs = runs_response.json()["runs"]
    assert runs
    assert any(run["compare_id"] == body["compare"]["compare_id"] for run in runs)
    assert all(run["compare_id"].startswith("compare:") for run in runs)


def test_v40_repository_uses_only_v40_tables() -> None:
    source = (ROOT / "v40" / "storage" / "postgres.py").read_text(encoding="utf-8")
    assert "v40_runtime_records" in source
    assert "v40_shadow_compare_runs" in source
    assert "INSERT INTO v30_" not in source
    assert "UPDATE v30_" not in source
    assert "FROM v30_" not in source


def test_repository_class_requires_v40_database_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("V40_DATABASE_URL", raising=False)
    monkeypatch.setattr("v40.storage.config._read_local_env_value", lambda key: "")

    with pytest.raises(RuntimeError, match="V40_DATABASE_URL"):
        V40PostgresRepository.from_env()
