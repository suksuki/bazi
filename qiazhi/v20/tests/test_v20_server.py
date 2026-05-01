from __future__ import annotations

from pathlib import Path
import json

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
    assert storage["schema"]["table_count"] == 9
    assert storage["runtime_mutation"] is False
    assert redis["validation"]["ok"] is True
    assert redis["contract"]["keyspace_count"] == 5
    assert redis["runtime_mutation"] is False


def test_v20_admin_status_endpoints_are_db_llm_only_and_secret_free() -> None:
    client = TestClient(app)
    db = client.get("/api/v20/admin/db").json()
    llm = client.get("/api/v20/admin/llm").json()

    assert db["version"] == "v20.admin_database_status.v1"
    assert db["runtime_mutation"] is False
    assert db["postgres"]["password_env"] == "V20_POSTGRES_PASSWORD"
    assert "NO_SECRET_VALUES_RENDERED" in db["guardrails"]
    assert "v20_corpus_snapshots" in db["table_names"]
    assert "v20_user_profiles" in db["table_names"]
    assert llm["version"] == "v20.admin_llm_status.v1"
    assert llm["runtime_mutation"] is False
    assert llm["readiness"]["api_key_env"] == "V20_LLM_API_KEY"
    assert "LLM_IS_ASSISTIVE_NOT_AUTHORITATIVE" in llm["guardrails"]


def test_v20_v19_profile_migration_preview_is_read_only() -> None:
    client = TestClient(app)
    preview = client.get("/api/v20/profiles/v19-migration-preview").json()
    dry_run = client.post("/api/v20/profiles/import-v19").json()
    auth_preview = client.get("/api/v20/auth/v19-migration-preview").json()
    auth_dry_run = client.post("/api/v20/auth/import-v19").json()

    assert preview["version"] == "v20.v19_profile_migration_preview.v1"
    assert preview["target_table"] == "v20_user_profiles"
    assert preview["runtime_mutation"] is False
    assert "V19_SOURCE_IS_READ_ONLY" in preview["guardrails"]
    assert dry_run["version"] == "v20.v19_profile_postgres_import.v1"
    assert dry_run["status"] == "dry_run"
    assert dry_run["target_owner_id"] == "admin"
    assert dry_run["apply"] is False
    assert dry_run["runtime_mutation"] is False
    assert auth_preview["version"] == "v20.v19_auth_migration_preview.v1"
    assert auth_preview["session_count"] >= 1
    assert auth_preview["runtime_mutation"] is False
    assert "NO_SESSION_TOKENS_RENDERED" in auth_preview["guardrails"]
    assert auth_dry_run["version"] == "v20.v19_auth_session_import.v1"
    assert auth_dry_run["status"] == "dry_run"
    assert auth_dry_run["runtime_mutation"] is False


def test_v20_profile_list_endpoint_is_read_only_without_database_url(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("V20_DATABASE_URL", raising=False)
    monkeypatch.setenv("V20_AUTH_STORE", str(tmp_path / "auth.json"))
    client = TestClient(app)
    client.post("/api/v20/auth/guest", json={"locale": "zh"})

    response = client.get("/api/v20/profiles")

    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "v20.profile_list.v1"
    assert data["status"] == "blocked_missing_V20_DATABASE_URL"
    assert data["profiles"] == []
    assert data["runtime_mutation"] is False
    assert "NO_SECRET_VALUES_RENDERED" in data["guardrails"]


def test_v20_local_auth_supports_guest_and_registered_roles(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_AUTH_STORE", str(tmp_path / "auth.json"))
    client = TestClient(app)

    guest = client.post("/api/v20/auth/guest", json={"locale": "zh"}).json()
    me = client.get("/api/v20/auth/me").json()

    assert guest["ok"] is True
    assert guest["session"]["role"] == "user"
    assert me["authenticated"] is True
    assert me["session"]["role"] == "user"

    practitioner = TestClient(app)
    registered = practitioner.post(
        "/api/v20/auth/register",
        json={"username": "local_practitioner", "password": "pass1234", "role": "analyst", "locale": "zh"},
    ).json()
    logged_in = practitioner.post(
        "/api/v20/auth/login",
        json={"username": "local_practitioner", "password": "pass1234", "locale": "zh"},
    ).json()

    assert registered["ok"] is True
    assert registered["session"]["role"] == "analyst"
    assert logged_in["session"]["role"] == "analyst"


def test_v20_can_import_v19_auth_sessions_and_accept_legacy_cookie(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_AUTH_STORE", str(tmp_path / "auth.json"))
    client = TestClient(app)

    result = client.post("/api/v20/auth/import-v19?apply=true", json={"admin_password": "abcd1235"}).json()
    source = Path(__file__).resolve().parents[2] / "v19/.runtime/auth_sessions.json"
    token = next(iter(json.loads(source.read_text(encoding="utf-8")).keys()))

    client.cookies.set("v19_auth_session", token)
    me = client.get("/api/v20/auth/me").json()

    assert result["status"] == "imported"
    assert result["admin_password_configured"] is True
    assert result["imported_sessions"] >= 1
    assert "v19_auth_session" in result["recognized_cookie_names"]
    assert me["authenticated"] is True
    assert me["session"]["role"] in {"user", "analyst", "admin"}
    login = client.post("/api/v20/auth/login", json={"username": "admin", "password": "abcd1235"}).json()
    assert login["session"]["role"] == "admin"


def test_v20_service_scripts_and_docs_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    macos = root / "v20/scripts/start_macos.sh"
    linux = root / "v20/scripts/start_linux.sh"
    doc = root / "docs/v20/V20_SERVICE_RUNTIME.md"

    assert "v20.server:app" in macos.read_text(encoding="utf-8")
    assert "source \"${SCRIPT_DIR}/_python.sh\"" in macos.read_text(encoding="utf-8")
    assert "source \"${SCRIPT_DIR}/_python.sh\"" in linux.read_text(encoding="utf-8")
    assert "V20_ENV=\"${V20_ENV:-local_macos}\"" in macos.read_text(encoding="utf-8")
    assert "V20_ENV=\"${V20_ENV:-linux_0_13}\"" in linux.read_text(encoding="utf-8")
    assert "POST /api/v20/measure" in doc.read_text(encoding="utf-8")
