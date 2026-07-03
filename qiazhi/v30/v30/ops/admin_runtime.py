from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from v30.llm.provider import (
    V30LLMProviderConfig,
    load_v30_llm_provider_config_from_env,
    llm_provider_readiness_report,
    resolve_llm_base_url,
)

CONFIG_VERSION = "v30.admin_runtime_config.v1"
SECRET_FIELDS = {"database_url", "api_key"}

DB_FIELD_ENV = {
    "repository": "V30_REPOSITORY",
    "database_url": "V30_DATABASE_URL",
}

REDIS_FIELD_ENV = {
    "redis_url": "V30_REDIS_URL",
}

LLM_FIELD_ENV = {
    "enabled": "V30_LLM_ENABLED",
    "execute_llm": "V30_LLM_EXECUTE",
    "provider": "V30_LLM_PROVIDER",
    "host": "V30_LLM_HOST",
    "port": "V30_LLM_PORT",
    "base_url": "V30_LLM_BASE_URL",
    "model": "V30_LLM_MODEL",
    "api_key": "V30_LLM_API_KEY",
    "api_key_env": "V30_LLM_API_KEY_ENV",
    "http_timeout_sec": "V30_LLM_HTTP_TIMEOUT_SEC",
    "temperature": "V30_LLM_TEMPERATURE",
    "max_tokens": "V30_LLM_MAX_TOKENS",
}


def admin_config_path() -> Path:
    configured = os.getenv("V30_ADMIN_CONFIG_PATH", "").strip()
    if configured:
        return Path(configured)
    runtime_dir = Path(os.getenv("V30_RUNTIME_DIR", ".runtime")).resolve()
    return runtime_dir / "admin_config.json"


def apply_saved_v30_admin_env_overrides() -> None:
    payload = _read_config()
    env = payload.get("env", {})
    if not isinstance(env, dict):
        return
    for key, value in env.items():
        if isinstance(key, str) and key.startswith("V30_") and value not in (None, ""):
            os.environ[key] = str(value)


def admin_runtime_config_status() -> dict[str, object]:
    apply_saved_v30_admin_env_overrides()
    path = admin_config_path()
    return {
        "version": "v30.admin_runtime_config_status.v1",
        "path": str(path),
        "exists": path.exists(),
        "database": _public_section(DB_FIELD_ENV),
        "redis": _public_section(REDIS_FIELD_ENV),
        "llm": _public_section(LLM_FIELD_ENV),
        "restart_required_fields": sorted({*DB_FIELD_ENV.values(), *REDIS_FIELD_ENV.values(), "V30_REPOSITORY"}),
        "runtime_mutation": False,
        "guardrails": ["ADMIN_CONFIG_STATUS_ONLY", "NO_SECRET_VALUES_RENDERED", "V30_ENV_ONLY"],
        "boundary": "admin_runtime_config_projects_v30_env_without_exposing_secret_values",
    }


def save_admin_database_config(payload: dict[str, Any]) -> dict[str, object]:
    updates, secret_fields = _extract_updates(payload, DB_FIELD_ENV)
    repository = updates.get("V30_REPOSITORY")
    if repository and repository not in {"memory", "local_json", "postgres"}:
        raise ValueError("invalid_repository")
    database_url = updates.get("V30_DATABASE_URL")
    if database_url:
        _validate_v30_database_url(database_url)
    _persist_env_updates(updates)
    return _save_response("v30.admin_database_config_save.v1", updates, secret_fields, restart_required=True)


def save_admin_redis_config(payload: dict[str, Any]) -> dict[str, object]:
    updates, secret_fields = _extract_updates(payload, REDIS_FIELD_ENV)
    redis_url = updates.get("V30_REDIS_URL")
    if redis_url and not redis_url.startswith("redis://"):
        raise ValueError("invalid_redis_url")
    _persist_env_updates(updates)
    return _save_response("v30.admin_redis_config_save.v1", updates, secret_fields, restart_required=True)


def save_admin_llm_config(payload: dict[str, Any]) -> dict[str, object]:
    payload = _expand_quick_ollama_payload(payload)
    updates, secret_fields = _extract_updates(payload, LLM_FIELD_ENV)
    _persist_env_updates(updates)
    return _save_response("v30.admin_llm_config_save.v1", updates, secret_fields, restart_required=False)


def database_admin_status() -> dict[str, object]:
    from v30.storage.names import V30_TABLES

    apply_saved_v30_admin_env_overrides()
    repository = os.getenv("V30_REPOSITORY", "memory")
    database_url = os.getenv("V30_DATABASE_URL", "")
    payload: dict[str, object] = {
        "version": "v30.admin_database_status.v1",
        "status": "config_only",
        "repository": repository,
        "database_url_present": bool(database_url),
        "postgres": _postgres_public_config(database_url),
        "table_names": list(V30_TABLES),
        "counts": {},
        "runtime_mutation": False,
        "restart_required_after_config_save": True,
        "guardrails": ["ADMIN_STATUS_ONLY", "NO_SECRET_VALUES_RENDERED", "POSTGRES_IS_RUNTIME_REPOSITORY_WHEN_CONFIGURED"],
        "boundary": "database_admin_status_observes_v30_postgres_without_mutating_chart_facts",
    }
    if repository != "postgres":
        return payload | {"status": "not_postgres_repository"}
    if not database_url:
        return payload | {"status": "missing_database_url"}
    try:
        import psycopg  # type: ignore[import-not-found]
    except Exception as exc:
        return payload | {"status": "driver_missing", "error": _failure_detail(exc)}
    try:
        counts: dict[str, int | None] = {}
        missing: list[str] = []
        with psycopg.connect(database_url, connect_timeout=3) as connection:
            with connection.cursor() as cursor:
                for table_name in V30_TABLES:
                    cursor.execute("SELECT to_regclass(%s)", (table_name,))
                    exists = cursor.fetchone()[0]
                    if not exists:
                        counts[table_name] = None
                        missing.append(table_name)
                        continue
                    cursor.execute(f"SELECT count(*) FROM {table_name}")
                    counts[table_name] = int(cursor.fetchone()[0])
    except Exception as exc:
        return payload | {"status": "connection_failed", "error": _failure_detail(exc)}
    return payload | {
        "status": "connected" if not missing else "schema_incomplete",
        "counts": counts,
        "missing_tables": missing,
        "schema_table_count": len(V30_TABLES),
    }


def apply_database_schema() -> dict[str, object]:
    from v30.storage.names import V30_TABLES
    from v30.storage.postgres_schema import CREATE_TABLE_STATEMENTS

    apply_saved_v30_admin_env_overrides()
    database_url = os.getenv("V30_DATABASE_URL", "")
    base = {
        "version": "v30.admin_database_schema_apply.v1",
        "status": "not_started",
        "database_url_present": bool(database_url),
        "table_names": list(V30_TABLES),
        "runtime_mutation": True,
        "guardrails": ["ADMIN_SCHEMA_APPLY_ONLY", "V30_TABLES_ONLY", "NO_CHART_FACT_MUTATION"],
    }
    if not database_url:
        return base | {"status": "missing_database_url"}
    try:
        import psycopg  # type: ignore[import-not-found]
    except Exception as exc:
        return base | {"status": "driver_missing", "error": _failure_detail(exc)}
    try:
        with psycopg.connect(database_url, connect_timeout=3) as connection:
            with connection.cursor() as cursor:
                for table_name in V30_TABLES:
                    cursor.execute(CREATE_TABLE_STATEMENTS[table_name])
            connection.commit()
    except Exception as exc:
        return base | {"status": "failed", "error": _failure_detail(exc)}
    return base | {"status": "applied", "applied_table_count": len(V30_TABLES)}


def redis_admin_status() -> dict[str, object]:
    from v30.storage.names import redis_key

    apply_saved_v30_admin_env_overrides()
    redis_url = os.getenv("V30_REDIS_URL", "")
    env = os.getenv("V30_ENV", "local")
    payload: dict[str, object] = {
        "version": "v30.admin_redis_status.v1",
        "status": "config_only",
        "redis_url_present": bool(redis_url),
        "keyspace": redis_key(env, "*", "*"),
        "db": _redis_db(redis_url),
        "ping": False,
        "key_count": 0,
        "runtime_mutation": False,
        "restart_required_after_config_save": True,
        "guardrails": ["ADMIN_STATUS_ONLY", "REDIS_IS_CACHE_NOT_AUTHORITY", "NO_SECRET_VALUES_RENDERED"],
        "boundary": "redis_admin_status_observes_v30_cache_without_becoming_authoritative",
    }
    if not redis_url:
        return payload | {"status": "missing_redis_url"}
    try:
        import redis  # type: ignore[import-not-found]
    except Exception as exc:
        return payload | {"status": "driver_missing", "error": _failure_detail(exc)}
    try:
        client = redis.Redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
        ping = bool(client.ping())
        pattern = redis_key(env, "*", "*")
        key_count = sum(1 for _ in client.scan_iter(match=pattern, count=100))
    except Exception as exc:
        return payload | {"status": "connection_failed", "error": _failure_detail(exc)}
    return payload | {"status": "connected", "ping": ping, "key_count": key_count}


def llm_admin_status(*, probe_models: bool = False) -> dict[str, object]:
    apply_saved_v30_admin_env_overrides()
    cfg = load_v30_llm_provider_config_from_env()
    readiness = llm_provider_readiness_report(cfg)
    payload: dict[str, object] = {
        "version": "v30.admin_llm_status.v1",
        "status": "ready" if readiness["ready_for_connection"] else "config_only",
        "readiness": readiness,
        "config": cfg.to_dict(),
        "probe_models": probe_models,
        "model_count": 0,
        "models": [],
        "runtime_mutation": False,
        "guardrails": ["ADMIN_STATUS_ONLY", "NO_SECRET_VALUES_RENDERED", "LLM_IS_ASSISTIVE_NOT_AUTHORITATIVE"],
        "boundary": "llm_admin_status_observes_bazi_llm_provider_without_generating_chart_facts",
    }
    if not probe_models:
        return payload
    if not readiness["ready_for_connection"]:
        return payload | {"status": "not_ready_for_probe"}
    try:
        models = _load_models(cfg)
    except Exception as exc:
        return payload | {"status": "model_probe_failed", "error": _failure_detail(exc)}
    return payload | {"status": "model_probe_ready", "model_count": len(models), "models": models}


def llm_admin_probe(payload: dict[str, object] | None = None) -> dict[str, object]:
    cfg = _temporary_llm_config(payload or {}, default_execute=True)
    readiness = llm_provider_readiness_report(cfg)
    base: dict[str, object] = {
        "version": "v30.admin_llm_probe.v1",
        "status": "not_ready",
        "provider": cfg.provider,
        "host": cfg.host,
        "port": cfg.port,
        "model": cfg.model,
        "resolved_base_url": cfg.resolved_base_url(),
        "ready_for_connection": readiness["ready_for_connection"],
        "model_count": 0,
        "models": [],
        "runtime_mutation": False,
        "guardrails": ["ADMIN_ONLY_LLM_PROBE", "NO_CONFIG_WRITE", "NO_SECRET_VALUES_RENDERED"],
        "boundary": "llm_probe_reads_remote_models_without_saving_runtime_config",
    }
    if not readiness["ready_for_connection"]:
        return base | {"failure": "provider_not_ready"}
    try:
        models = _load_ollama_native_models(cfg) if cfg.provider.lower() in {"ollama", "ollama_native"} else _load_models(cfg)
    except Exception as exc:
        return base | {"status": "model_probe_failed", "failure": type(exc).__name__, "failure_detail": _failure_detail(exc)}
    return base | {
        "status": "model_probe_ready",
        "model_count": len(models),
        "models": models,
    }


def llm_admin_test(payload: dict[str, object] | None = None) -> dict[str, object]:
    apply_saved_v30_admin_env_overrides()
    raw_payload = payload or {}
    cfg = (
        _temporary_llm_config(raw_payload, default_execute=True)
        if _has_llm_connection_override(raw_payload)
        else load_v30_llm_provider_config_from_env()
    )
    readiness = llm_provider_readiness_report(cfg)
    base: dict[str, object] = {
        "version": "v30.admin_llm_test.v1",
        "status": "not_ready",
        "provider": cfg.provider,
        "model": cfg.model,
        "ready_for_connection": readiness["ready_for_connection"],
        "executed": False,
        "runtime_mutation": False,
        "guardrails": ["ADMIN_ONLY_LLM_CONNECTIVITY_TEST", "NO_SECRET_VALUES_RENDERED", "TEST_PROMPT_ONLY_NO_RUNTIME_TRUTH_MUTATION"],
    }
    if not readiness["ready_for_connection"]:
        return base | {"failure": "provider_not_ready"}
    if not cfg.model:
        return base | {"failure": "missing_model"}
    prompt = str((payload or {}).get("prompt") or "用一句中文回答：启智 V30 LLM 测试正常。").strip()[:500]
    started = time.monotonic()
    try:
        text = _test_completion(cfg, prompt)
    except Exception as exc:
        return base | {
            "status": "failed",
            "executed": True,
            "duration_ms": round((time.monotonic() - started) * 1000, 2),
            "failure": type(exc).__name__,
            "failure_detail": _failure_detail(exc),
            "timeout_sec": _completion_timeout(cfg),
        }
    return base | {
        "status": "ok",
        "executed": True,
        "duration_ms": round((time.monotonic() - started) * 1000, 2),
        "timeout_sec": _completion_timeout(cfg),
        "sample": text[:500],
    }


def _extract_updates(payload: dict[str, Any], field_env: dict[str, str]) -> tuple[dict[str, str], list[str]]:
    updates: dict[str, str] = {}
    secret_fields: list[str] = []
    for field, env_name in field_env.items():
        if field not in payload:
            continue
        value = payload[field]
        if field in SECRET_FIELDS and value in (None, ""):
            continue
        clean = _normalize_value(field, value)
        if clean is None:
            continue
        updates[env_name] = clean
        if field in SECRET_FIELDS:
            secret_fields.append(field)
    return updates, secret_fields


def _expand_quick_ollama_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("quick_ollama"):
        return payload
    host = str(payload.get("host") or "").strip()
    port = _normalize_value("port", payload.get("port") or 11434) or "11434"
    return {
        **payload,
        "enabled": True,
        "execute_llm": True,
        "provider": "ollama_native",
        "host": host,
        "port": port,
        "base_url": resolve_llm_base_url("", host, int(port)),
        "http_timeout_sec": payload.get("http_timeout_sec") or 60,
        "temperature": payload.get("temperature") or 0.2,
        "max_tokens": payload.get("max_tokens") or 1200,
    }


def _temporary_llm_config(payload: dict[str, object], *, default_execute: bool) -> V30LLMProviderConfig:
    expanded = _expand_quick_ollama_payload(dict(payload))
    current = load_v30_llm_provider_config_from_env()
    provider = str(expanded.get("provider") or "ollama_native").strip() or "ollama_native"
    host = str(expanded.get("host") or current.host or "127.0.0.1").strip()
    port = int(_normalize_value("port", expanded.get("port") or current.port or 11434) or 11434)
    model = str(expanded.get("model") or current.model or "").strip()
    base_url = str(expanded.get("base_url") or "").strip()
    if expanded.get("quick_ollama") and not base_url:
        base_url = resolve_llm_base_url("", host, port)
    return V30LLMProviderConfig(
        enabled=_bool_payload(expanded.get("enabled"), True),
        execute_llm=_bool_payload(expanded.get("execute_llm"), default_execute),
        provider=provider,
        host=host,
        port=port,
        base_url=base_url,
        model=model,
        api_key_env=str(expanded.get("api_key_env") or current.api_key_env or "V30_LLM_API_KEY"),
        http_timeout_sec=float(expanded.get("http_timeout_sec") or current.http_timeout_sec or 60.0),
        temperature=float(expanded.get("temperature") or current.temperature or 0.2),
        max_tokens=int(expanded.get("max_tokens") or current.max_tokens or 1200),
        config_source="admin_temporary_probe",
    )


def _has_llm_connection_override(payload: dict[str, object]) -> bool:
    return any(key in payload for key in ("quick_ollama", "host", "port", "base_url", "model", "provider"))


def _bool_payload(value: object, default: bool) -> bool:
    if value in (None, ""):
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _normalize_value(field: str, value: Any) -> str | None:
    if value is None:
        return None
    if field in {"enabled", "execute_llm"}:
        return "1" if bool(value) else "0"
    if field in {"port", "max_tokens"}:
        number = int(value)
        if field == "port" and (number < 1 or number > 65535):
            raise ValueError(f"invalid_{field}")
        if field == "max_tokens" and number < 1:
            raise ValueError(f"invalid_{field}")
        return str(number)
    if field in {"http_timeout_sec", "temperature"}:
        number = float(value)
        if number < 0:
            raise ValueError(f"invalid_{field}")
        return str(number)
    clean = str(value).strip()
    if not clean and field not in SECRET_FIELDS:
        return None
    return clean


def _persist_env_updates(updates: dict[str, str]) -> None:
    if not updates:
        return
    current = _read_config()
    env = current.get("env", {})
    if not isinstance(env, dict):
        env = {}
    env.update(updates)
    payload = {"version": CONFIG_VERSION, "env": env}
    path = admin_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    for key, value in updates.items():
        os.environ[key] = value


def _read_config() -> dict[str, Any]:
    path = admin_config_path()
    if not path.exists():
        return {"version": CONFIG_VERSION, "env": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": CONFIG_VERSION, "env": {}}
    return payload if isinstance(payload, dict) else {"version": CONFIG_VERSION, "env": {}}


def _public_section(field_env: dict[str, str]) -> dict[str, object]:
    section: dict[str, object] = {}
    for field, env_name in field_env.items():
        if field in SECRET_FIELDS:
            section[f"{field}_configured"] = bool(os.getenv(env_name))
        else:
            section[field] = os.getenv(env_name, "")
    return section


def _save_response(version: str, updates: dict[str, str], secret_fields: list[str], *, restart_required: bool) -> dict[str, object]:
    return {
        "version": version,
        "status": "saved" if updates else "no_changes",
        "updated_env": sorted(updates),
        "secret_fields_written": sorted(secret_fields),
        "path": str(admin_config_path()),
        "restart_required": restart_required,
        "runtime_mutation": True,
        "guardrails": ["ADMIN_ONLY_CONFIG_MUTATION", "NO_SECRET_VALUES_RENDERED", "V30_ENV_ONLY"],
        "boundary": "admin_config_save_updates_runtime_env_without_mutating_bazi_chart_facts",
    }


def _validate_v30_database_url(database_url: str) -> None:
    parsed = urlparse(database_url)
    db_name = parsed.path.rsplit("/", 1)[-1].lower()
    if "v20" in db_name:
        raise ValueError("database_url_must_not_point_to_v20")


def _postgres_public_config(database_url: str) -> dict[str, object]:
    if not database_url:
        return {"host": "", "port": "", "database": "", "username": "", "sslmode": ""}
    parsed = urlparse(database_url)
    query = dict(part.split("=", 1) for part in parsed.query.split("&") if "=" in part)
    return {
        "host": parsed.hostname or "",
        "port": parsed.port or "",
        "database": parsed.path.rsplit("/", 1)[-1],
        "username": parsed.username or "",
        "sslmode": query.get("sslmode", ""),
    }


def _redis_db(redis_url: str) -> int | str:
    if not redis_url:
        return ""
    parsed = urlparse(redis_url)
    try:
        return int((parsed.path or "/0").strip("/") or "0")
    except ValueError:
        return ""


def _load_models(cfg) -> list[dict[str, object]]:
    if cfg.provider.lower() in {"ollama", "ollama_native"}:
        try:
            return _load_openai_compatible_models(cfg)
        except Exception:
            return _load_ollama_native_models(cfg)
    return _load_openai_compatible_models(cfg)


def _load_openai_compatible_models(cfg) -> list[dict[str, object]]:
    request = urllib.request.Request(
        f"{cfg.resolved_base_url().rstrip('/')}/models",
        headers=_headers(cfg),
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=cfg.http_timeout_sec) as response:
        body = json.loads(response.read().decode("utf-8"))
    rows = body.get("data", []) if isinstance(body, dict) else []
    models = []
    model_rows = rows[:48] if isinstance(rows, list) else []
    for row in model_rows:
        if isinstance(row, dict):
            model_id = row.get("id") or row.get("name") or ""
            models.append({"id": str(model_id), "owned_by": str(row.get("owned_by", ""))})
    return models


def _load_ollama_native_models(cfg) -> list[dict[str, object]]:
    request = urllib.request.Request(
        f"{cfg.resolved_base_url().rstrip('/').removesuffix('/v1')}/api/tags",
        headers={"Content-Type": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=cfg.http_timeout_sec) as response:
        body = json.loads(response.read().decode("utf-8"))
    rows = body.get("models", []) if isinstance(body, dict) else []
    models = []
    model_rows = rows[:48] if isinstance(rows, list) else []
    for row in model_rows:
        if isinstance(row, dict):
            model_id = row.get("name") or row.get("model") or row.get("id") or ""
            models.append({"id": str(model_id), "owned_by": "ollama"})
    return models


def _test_completion(cfg, prompt: str) -> str:
    if cfg.provider.lower() in {"ollama", "ollama_native"}:
        body = {
            "model": cfg.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "think": False,
            "options": {"temperature": 0, "num_predict": 80},
        }
        request = urllib.request.Request(
            f"{cfg.resolved_base_url().rstrip('/').removesuffix('/v1')}/api/chat",
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
    else:
        body = {
            "model": cfg.model,
            "temperature": 0,
            "max_tokens": 80,
            "messages": [{"role": "user", "content": prompt}],
        }
        request = urllib.request.Request(
            f"{cfg.resolved_base_url().rstrip('/')}/chat/completions",
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers=_headers(cfg),
            method="POST",
        )
    with urllib.request.urlopen(request, timeout=_completion_timeout(cfg)) as response:
        response_payload = json.loads(response.read().decode("utf-8"))
    if cfg.provider.lower() in {"ollama", "ollama_native"}:
        message = response_payload.get("message") if isinstance(response_payload, dict) else {}
        if isinstance(message, dict):
            return str(message.get("content") or response_payload.get("response") or "").strip()
        return ""
    return str(response_payload["choices"][0]["message"]["content"]).strip()


def _completion_timeout(cfg) -> float:
    timeout = float(getattr(cfg, "http_timeout_sec", 15.0) or 15.0)
    if cfg.provider.lower() in {"ollama", "ollama_native"}:
        return max(timeout, 30.0)
    return max(timeout, 1.0)


def _headers(cfg) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv(cfg.api_key_env, "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _failure_detail(exc: Exception) -> str:
    detail = str(exc).strip()
    return detail[:300] if detail else type(exc).__name__
