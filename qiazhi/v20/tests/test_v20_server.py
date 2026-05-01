from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v20.server import app


def test_v20_service_health_is_read_only_and_profile_aware() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "v20.service_health.v1"
    assert data["status"] == "ok"
    assert data["active_profile"] == "local_macos"
    assert data["runtime_mutation"] is False
    assert data["connection_policy"] == "no_postgres_or_redis_connection_on_health_check"
    assert "NO_SECRET_VALUES_RENDERED" in data["guardrails"]


def test_v20_measure_endpoint_returns_bazi_measurement_runtime() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v20/measure",
        json={
            "year": "甲子",
            "month": "戊辰",
            "day": "甲午",
            "hour": "辛酉",
            "input_id": "server.test",
            "user_text": "我想看财和用神",
            "locale": "zh",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "v20.runtime_result.v1"
    assert data["input_id"] == "server.test"
    assert data["runtime_mutation"] is False
    assert data["feature_layer"]["macro_feature_count"] >= 4
    assert data["knowledge_alignment"]["status"] == "pass"
    assert data["measurement_report"]["core_focus"] == "bazi_measurement"
    assert data["selected_question"]["question_key"]
    assert data["llm_assist"]["status"] == "ready"
    assert data["llm_assist"]["answer_safety_review"]["result"]["ok"] is True
    assert "八字测算重点" in data["answer_text"]
    assert "feature." not in data["answer_text"]
    assert "core." not in data["answer_text"]


def test_v20_measure_endpoint_rejects_invalid_pillar_without_mutation() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v20/runtime/measure",
        json={"year": "甲子", "month": "戊辰", "day": "甲午", "hour": "XX"},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error"] == "V20_MEASURE_INPUT_INVALID"
    assert "hour stem is not supported" in detail["message"]


def test_v20_measure_endpoint_accepts_explicit_time_layer() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v20/measure",
        json={
            "year": "甲子",
            "month": "戊辰",
            "day": "甲午",
            "hour": "辛酉",
            "flow_year_pillar": "庚子",
            "user_text": "我想看流年触发",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["time_context"]["status"] == "ready"
    assert data["selected_question"]["domain"] == "time"
    assert data["runtime_mutation"] is False


def test_v20_ops_and_testing_metadata_endpoints_hide_secrets() -> None:
    client = TestClient(app)
    ops = client.get("/api/v20/ops/config").json()
    profile = client.get("/api/v20/ops/profile/linux_0_13").json()
    tiers = client.get("/api/v20/testing/tiers").json()
    storage = client.get("/api/v20/storage/schema").json()
    redis = client.get("/api/v20/redis/contract").json()

    assert ops["validation"]["ok"] is True
    assert ops["config"]["profiles"][0]["postgres"]["secret_policy"] == "env_names_only_no_secret_values"
    assert profile["profile"]["public_host"] == "0.13"
    assert profile["profile"]["redis"]["non_authoritative"] is True
    assert tiers["manifest"]["default_tier"] == "fast"
    assert tiers["runtime_mutation"] is False
    assert storage["schema"]["backend"] == "postgres"
    assert storage["schema"]["table_count"] == 6
    assert storage["runtime_mutation"] is False
    assert redis["validation"]["ok"] is True
    assert redis["contract"]["keyspace_count"] == 5
    assert redis["runtime_mutation"] is False


def test_v20_service_scripts_and_docs_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    macos = root / "v20/scripts/start_macos.sh"
    linux = root / "v20/scripts/start_linux.sh"
    doc = root / "docs/v20/V20_SERVICE_RUNTIME.md"

    assert "v20.server:app" in macos.read_text(encoding="utf-8")
    assert "V20_ENV=\"${V20_ENV:-local_macos}\"" in macos.read_text(encoding="utf-8")
    assert "V20_ENV=\"${V20_ENV:-linux_0_13}\"" in linux.read_text(encoding="utf-8")
    assert "POST /api/v20/measure" in doc.read_text(encoding="utf-8")
