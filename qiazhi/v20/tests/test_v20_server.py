from __future__ import annotations

import json
from http.cookies import SimpleCookie
from pathlib import Path

from fastapi import HTTPException, Response
from starlette.requests import Request

from v20.llm.practitioner import unwrap_practitioner_text
from v20.api.schemas import MeasureRequest
from v20.server import _stream_role_answer_payload, app


def _endpoint(path: str, method: str = "GET"):
    method = method.upper()
    for route in app.routes:
        if getattr(route, "path", "") == path and method in getattr(route, "methods", set()):
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def _request(path: str = "/", *, cookies: dict[str, str] | None = None) -> Request:
    headers = []
    if cookies:
        cookie_header = "; ".join(f"{key}={value}" for key, value in cookies.items())
        headers.append((b"cookie", cookie_header.encode("utf-8")))
    return Request({"type": "http", "method": "GET", "path": path, "headers": headers, "client": ("testclient", 5000)})


def _measure_payload(**overrides) -> MeasureRequest:
    payload = {
        "year": "甲子",
        "month": "戊辰",
        "day": "甲午",
        "hour": "辛酉",
        "locale": "zh",
    }
    payload.update(overrides)
    return MeasureRequest(**payload)


def _cookies_from_response(response: Response) -> dict[str, str]:
    cookie = SimpleCookie()
    cookie.load(response.headers.get("set-cookie", ""))
    return {key: morsel.value for key, morsel in cookie.items()}



def test_v20_service_health_is_read_only_and_profile_aware() -> None:
    data = _endpoint("/health")()
    assert data["version"] == "v20.service_health.v1"
    assert data["status"] == "ok"
    assert data["active_profile"] == "local_macos"
    assert data["runtime_mutation"] is False
    assert data["connection_policy"] == "no_postgres_or_redis_connection_on_health_check"
    assert "NO_SECRET_VALUES_RENDERED" in data["guardrails"]


def test_v20_liveness_and_readiness_health_endpoints_are_secret_free(monkeypatch) -> None:
    monkeypatch.setenv("V20_DATABASE_URL", "postgres://secret-user:secret-pass@localhost/db")
    monkeypatch.setenv("V20_REDIS_URL", "redis://:secret@localhost:6379/0")
    monkeypatch.setattr(
        "v20.server.readiness_report",
        lambda: {
            "version": "v20.service_readiness.v1",
            "status": "degraded",
            "ready": False,
            "active_profile": "local_macos",
            "postgres": {"ready": False, "status": "unavailable", "failure": "OperationalError"},
            "redis": {"ready": False, "status": "unavailable", "failure": "ConnectionError"},
            "runtime_mutation": False,
            "connection_policy": "dependency_ping_without_secret_rendering",
            "guardrails": ["READINESS_CHECK_MAY_CONNECT_TO_DEPENDENCIES", "NO_SECRET_VALUES_RENDERED"],
        },
    )
    live_data = _endpoint("/health/live")()
    ready_data = _endpoint("/health/ready")()
    assert live_data["version"] == "v20.service_liveness.v1"
    assert live_data["connection_policy"] == "no_external_dependency_connection_on_liveness_check"
    assert "NO_NETWORK_CONNECTION_ATTEMPTED" in live_data["guardrails"]
    assert ready_data["version"] == "v20.service_readiness.v1"
    assert ready_data["connection_policy"] == "dependency_ping_without_secret_rendering"
    assert "READINESS_CHECK_MAY_CONNECT_TO_DEPENDENCIES" in ready_data["guardrails"]
    rendered = json.dumps(ready_data, ensure_ascii=False)
    assert "secret-pass" not in rendered
    assert "redis://:secret" not in rendered


def test_v20_measure_endpoint_returns_bazi_measurement_runtime() -> None:
    data = _endpoint("/api/v20/measure", "POST")(
        _measure_payload(input_id="server.test", user_text="我想看财和用神"),
        _request("/api/v20/measure"),
    )

    assert data["version"] == "v20.runtime_result.v1"
    assert data["input_id"] == "server.test"
    assert data["runtime_mutation"] is False
    assert data["feature_layer"]["macro_feature_count"] >= 4
    assert data["knowledge_alignment"]["status"] == "pass"
    assert data["measurement_report"]["core_focus"] == "bazi_measurement"
    assert data["selected_question"]["question_key"]
    assert data["llm_assist"]["status"] == "ready"
    assert data["llm_assist"]["answer_safety_review"]["result"]["ok"] is True
    assert "当前命局可见" in data["answer_text"]
    assert "八字测算重点" not in data["answer_text"]
    assert "feature." not in data["answer_text"]
    assert "core." not in data["answer_text"]


def test_v20_measure_stream_returns_runtime_then_answer_events() -> None:
    from v20.server import _sse

    projected = {"role_view_model": {"explanation_profile": {"style": "guided_plain_language"}}}
    done_payload = _stream_role_answer_payload("用户解读：关系先看配偶宫。", "user", projected)
    body = (
        _sse("runtime", {"result": {"input_id": "server.stream.test"}})
        + _sse("delta", {"text": "用户解读：关系先看配偶宫。"})
        + _sse("done", done_payload | {"status": "ok"})
    )

    assert "event: runtime" in body
    assert "event: delta" in body
    assert "event: done" in body
    assert "server.stream.test" in body
    done = body.split("event: done", 1)[-1]
    assert "用户解读：" in done
    assert "role_answer_profile" in done
    assert "answer_governance_quality" in done
    assert "stream_practitioner_answer_text" in done
    assert "一页图谱画像" not in body.split("event: done", 1)[-1]


def test_v20_stream_done_answer_uses_role_projection() -> None:
    payload = _stream_role_answer_payload(
        "事业先看官杀和食伤。",
        "user",
        {"role_view_model": {"explanation_profile": {"style": "guided_plain_language"}}},
    )

    assert payload["answer_text"].startswith("用户解读：")
    assert payload["role_answer_profile"]["source_answer"] == "stream_practitioner_answer_text"
    assert payload["answer_governance_quality"]["version"] == "v20.answer_governance_quality.v1"
    assert payload["answer_governance_quality"]["runtime_mutation"] is False


def test_v20_practitioner_text_unwraps_json_shell() -> None:
    assert unwrap_practitioner_text('{"text":"事业先看官杀和食伤。"}') == "事业先看官杀和食伤。"
    assert unwrap_practitioner_text("事业先看官杀和食伤。") == "事业先看官杀和食伤。"


def test_v20_stream_day_master_validation_blocks_wrong_stem() -> None:
    from v20.llm.practitioner import validate_practitioner_answer_day_master

    bad = validate_practitioner_answer_day_master("这个盘是甲木日主，先看财官。", "乙")
    ok = validate_practitioner_answer_day_master("这个盘是乙木日主，先看财官。", "乙")

    assert bad["ok"] is False
    assert bad["failures"] == ["day_master_mismatch:甲_mentioned_expected_乙"]
    assert ok["ok"] is True


def test_v20_bazi_domain_alignment_endpoint_is_read_only() -> None:
    data = _endpoint("/api/v20/measurement/bazi-domain-alignment")()
    assert data["version"] == "v20.bazi_domain_alignment_manifest.v1"
    assert "strength" in data["core_domains"]
    assert "career" in data["applied_domains"]


def test_v20_dimensions_and_latent_factor_manifests_are_read_only() -> None:
    dimensions = _endpoint("/api/v20/measurement/dimensions")()
    latent = _endpoint("/api/v20/learning/latent-factor-calibration")()

    assert dimensions["version"] == "v20.bazi_dimension_manifest.v1"
    assert dimensions["domain_dimension_map"]["wealth"]["dimension_layer"] == "macro"
    assert latent["version"] == "v20.latent_factor_calibration_manifest.v1"
    assert latent["latent_factor_count"] == 12
    assert {"baseline_amplifier", "wealth_amplifier", "career_amplifier"} <= {
        row["factor_id"] for row in latent["latent_factors"]
    }
    assert latent["factor_kind_counts"]["hidden_setting"] >= 1
    assert latent["factor_kind_counts"]["change_amplifier"] >= 1
    assert latent["runtime_mutation"] is False


def test_v20_measure_endpoint_rejects_invalid_pillar_without_mutation() -> None:
    try:
        _endpoint("/api/v20/runtime/measure", "POST")(
            MeasureRequest(year="甲子", month="戊辰", day="甲午", hour="XX"),
            _request("/api/v20/runtime/measure"),
        )
        raise AssertionError("invalid pillar should fail")
    except HTTPException as exc:
        assert exc.status_code == 400
        detail = exc.detail
    assert detail["error"] == "V20_MEASURE_INPUT_INVALID"
    assert "hour stem is not supported" in detail["message"]


def test_v20_measure_endpoint_accepts_explicit_time_layer() -> None:
    data = _endpoint("/api/v20/measure", "POST")(
        _measure_payload(flow_year_pillar="庚子", user_text="我想看流年触发"),
        _request("/api/v20/measure"),
    )

    assert data["time_context"]["status"] == "ready"
    assert data["selected_question"]["domain"] == "time"
    assert data["runtime_mutation"] is False


def test_v20_ops_and_testing_metadata_endpoints_hide_secrets() -> None:
    ops = _endpoint("/api/v20/ops/config")()
    profile = _endpoint("/api/v20/ops/profile/{profile_name}")("linux_0_13")
    tiers = _endpoint("/api/v20/testing/tiers")()
    storage = _endpoint("/api/v20/storage/schema")()
    redis = _endpoint("/api/v20/redis/contract")()

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


def test_v20_admin_status_endpoints_are_db_llm_only_and_secret_free(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_AUTH_STORE", str(tmp_path / "auth.json"))
    monkeypatch.setenv("V20_ADMIN_CONFIG_PATH", str(tmp_path / "admin_config.json"))
    monkeypatch.setenv("V20_BCRYPT_ROUNDS", "4")
    monkeypatch.setenv("V20_POSTGRES_PASSWORD", "")
    monkeypatch.setenv("V20_DATABASE_URL", "")
    monkeypatch.setenv("V20_LLM_API_KEY", "")
    try:
        _endpoint("/api/v20/admin/db")(_request("/api/v20/admin/db"))
        raise AssertionError("admin endpoint should require authentication")
    except HTTPException as exc:
        blocked_status = exc.status_code

    monkeypatch.setattr("v20.server._require_admin_session", lambda request: {"role": "admin", "user_id": "admin"})
    admin_request = _request("/api/v20/admin/db")
    saved_db = _endpoint("/api/v20/admin/db/config", "POST")(
        {
            "enabled": True,
            "host": "db.internal",
            "port": 5433,
            "database": "qiazhi_admin",
            "username": "qiazhi_admin",
            "password": "secret-db-pass",
        },
        admin_request,
    )
    saved_llm = _endpoint("/api/v20/admin/llm/config", "POST")(
        {
            "enabled": True,
            "execute_llm": True,
            "provider": "openai_compatible",
            "base_url": "https://llm.example.test/v1",
            "model": "qwen-admin",
            "api_key": "secret-llm-key",
        },
        admin_request,
    )
    db = _endpoint("/api/v20/admin/db")(admin_request)
    llm = _endpoint("/api/v20/admin/llm")(admin_request)
    config = _endpoint("/api/v20/admin/config")(admin_request)
    policy = _endpoint("/api/v20/admin/policy-observability")(admin_request)

    assert blocked_status == 401
    assert saved_db["version"] == "v20.admin_database_config_save.v1"
    assert saved_db["runtime_mutation"] is True
    assert saved_db["secret_fields_written"] == ["password"]
    assert saved_llm["version"] == "v20.admin_llm_config_save.v1"
    assert saved_llm["secret_fields_written"] == ["api_key"]
    rendered_saved = json.dumps({"db": saved_db, "llm": saved_llm, "config": config}, ensure_ascii=False)
    assert "secret-db-pass" not in rendered_saved
    assert "secret-llm-key" not in rendered_saved
    assert db["version"] == "v20.admin_database_status.v1"
    assert db["runtime_mutation"] is False
    assert db["postgres"]["password_env"] == "V20_POSTGRES_PASSWORD"
    assert db["postgres"]["host"] == "db.internal"
    assert db["postgres"]["port"] == 5433
    assert "NO_SECRET_VALUES_RENDERED" in db["guardrails"]
    assert "v20_corpus_snapshots" in db["table_names"]
    assert "v20_user_profiles" in db["table_names"]
    assert llm["version"] == "v20.admin_llm_status.v1"
    assert llm["runtime_mutation"] is False
    assert llm["readiness"]["api_key_env"] == "V20_LLM_API_KEY"
    assert llm["readiness"]["api_key_present"] is True
    assert llm["readiness"]["model"] == "qwen-admin"
    assert config["database"]["password_configured"] is True
    assert config["llm"]["api_key_configured"] is True
    assert "LLM_IS_ASSISTIVE_NOT_AUTHORITATIVE" in llm["guardrails"]
    assert policy["version"] == "v20.admin_policy_observability.v1"
    assert policy["runtime_mutation"] is False
    assert policy["training_report"]["version"] == "v20.orchestrator_policy_observability_training_report.v1"
    assert policy["question_source_graph"]["version"] == "v20.question_source_graph.v1"
    assert policy["question_source_graph"]["runtime_mutation"] is False
    assert "QUESTION_SOURCE_GRAPH_OBSERVABILITY_READ_ONLY" in policy["question_source_graph"]["guardrails"]
    assert "ADMIN_POLICY_OBSERVABILITY_READ_ONLY" in policy["guardrails"]
    rendered_policy = json.dumps(policy, ensure_ascii=False)
    assert "secret-db-pass" not in rendered_policy
    assert "secret-llm-key" not in rendered_policy


def test_v20_v19_auth_migration_preview_is_read_only() -> None:
    auth_preview = _endpoint("/api/v20/auth/v19-migration-preview")()
    auth_dry_run = _endpoint("/api/v20/auth/import-v19", "POST")()

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
    response = Response()
    _endpoint("/api/v20/auth/guest", "POST")(response, {"locale": "zh"})
    cookies = _cookies_from_response(response)

    data = _endpoint("/api/v20/profiles")(_request("/api/v20/profiles", cookies=cookies))

    assert data["version"] == "v20.profile_list.v1"
    assert data["status"] == "blocked_missing_V20_DATABASE_URL"
    assert data["profiles"] == []
    assert data["runtime_mutation"] is False
    assert "NO_SECRET_VALUES_RENDERED" in data["guardrails"]


def test_v20_local_auth_supports_guest_and_registered_roles(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_AUTH_STORE", str(tmp_path / "auth.json"))
    monkeypatch.setenv("V20_BCRYPT_ROUNDS", "4")

    response = Response()
    guest = _endpoint("/api/v20/auth/guest", "POST")(response, {"locale": "zh"})
    cookies = _cookies_from_response(response)
    me = _endpoint("/api/v20/auth/me")(_request("/api/v20/auth/me", cookies=cookies))

    assert guest["ok"] is True
    assert guest["session"]["role"] == "user"
    assert me["authenticated"] is True
    assert me["session"]["role"] == "user"
    logout_response = Response()
    logged_out = _endpoint("/api/v20/auth/logout", "POST")(
        logout_response,
        _request("/api/v20/auth/logout", cookies=cookies),
    )
    after_logout = _endpoint("/api/v20/auth/me")(_request("/api/v20/auth/me", cookies=cookies))
    assert logged_out["ok"] is True
    assert after_logout["authenticated"] is False

    registered = _endpoint("/api/v20/auth/register", "POST")(
        {"username": "local_practitioner", "password": "pass1234", "role": "analyst", "locale": "zh"},
        Response(),
    )
    logged_in = _endpoint("/api/v20/auth/login", "POST")(
        {"username": "local_practitioner", "password": "pass1234", "locale": "zh"},
        Response(),
    )

    assert registered["ok"] is True
    assert registered["session"]["role"] == "analyst"
    assert logged_in["session"]["role"] == "analyst"

    registered_user = _endpoint("/api/v20/auth/register", "POST")(
        {"username": "regular_user", "password": "pass1234", "role": "user", "locale": "zh"},
        Response(),
    )
    assert registered_user["ok"] is True
    assert registered_user["session"]["role"] == "user"

    try:
        _endpoint("/api/v20/auth/register", "POST")(
            {"username": "another_admin", "password": "pass1234", "role": "admin", "locale": "zh"},
            Response(),
        )
        raise AssertionError("admin self-registration should fail")
    except HTTPException as exc:
        assert exc.status_code == 400
        assert exc.detail["code"] == "admin_registration_disabled"


def test_v20_can_import_v19_auth_sessions_and_accept_legacy_cookie(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_AUTH_STORE", str(tmp_path / "auth.json"))
    monkeypatch.setenv("V20_BCRYPT_ROUNDS", "4")

    result = _endpoint("/api/v20/auth/import-v19", "POST")(True, {"admin_password": "abcd1235"})
    source = Path(__file__).resolve().parents[2] / "v19/.runtime/auth_sessions.json"
    token = next(iter(json.loads(source.read_text(encoding="utf-8")).keys()))

    me = _endpoint("/api/v20/auth/me")(
        _request("/api/v20/auth/me", cookies={"v19_auth_session": token})
    )

    assert result["status"] == "imported"
    assert result["admin_password_configured"] is True
    assert result["imported_sessions"] >= 1
    assert "v19_auth_session" in result["recognized_cookie_names"]
    assert me["authenticated"] is True
    assert me["session"]["role"] in {"user", "analyst", "admin"}
    login = _endpoint("/api/v20/auth/login", "POST")(
        {"username": "admin", "password": "abcd1235"},
        Response(),
    )
    assert login["session"]["role"] == "admin"


def test_v20_service_scripts_and_docs_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    macos = root / "v20/scripts/start_macos.sh"
    linux = root / "v20/scripts/start_linux.sh"
    macos_service = root / "v20/scripts/service_macos.sh"
    linux_service = root / "v20/scripts/service_linux.sh"
    doc = root / "docs/v20/V20_SERVICE_RUNTIME.md"

    assert "v20.server:app" in macos.read_text(encoding="utf-8")
    assert "exec \"${PYTHON_BIN}\" -m uvicorn" in macos.read_text(encoding="utf-8")
    assert "already listening" in macos.read_text(encoding="utf-8")
    assert "source \"${SCRIPT_DIR}/_python.sh\"" in macos.read_text(encoding="utf-8")
    assert "source \"${SCRIPT_DIR}/_python.sh\"" in linux.read_text(encoding="utf-8")
    assert "V20_ENV=\"${V20_ENV:-local_macos}\"" in macos.read_text(encoding="utf-8")
    assert "V20_ENV=\"${V20_ENV:-linux_0_13}\"" in linux.read_text(encoding="utf-8")
    assert "launchd-plist" in macos_service.read_text(encoding="utf-8")
    assert "systemd-unit" in linux_service.read_text(encoding="utf-8")
    assert "SERVICE_ENV_FILE" in macos_service.read_text(encoding="utf-8")
    assert "SERVICE_ENV_FILE" in linux_service.read_text(encoding="utf-8")
    assert "Stopping unmanaged V20 macOS listener" in macos_service.read_text(encoding="utf-8")
    assert "Stopping unmanaged V20 Linux listener" in linux_service.read_text(encoding="utf-8")
    assert "screen -dmS" in macos_service.read_text(encoding="utf-8")
    assert "screen -dmS" in linux_service.read_text(encoding="utf-8")
    assert macos_service.stat().st_mode & 0o111
    assert linux_service.stat().st_mode & 0o111
    assert "service_macos.sh start" in doc.read_text(encoding="utf-8")
    assert "service_linux.sh start" in doc.read_text(encoding="utf-8")
    assert "POST /api/v20/measure" in doc.read_text(encoding="utf-8")
