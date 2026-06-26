from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


CONFIG_VERSION = "v20.admin_runtime_config.v1"
SECRET_FIELDS = {"password", "database_url", "api_key", "audit_api_key"}


DB_FIELD_ENV = {
    "enabled": "V20_POSTGRES_ENABLED",
    "host": "V20_POSTGRES_HOST",
    "port": "V20_POSTGRES_PORT",
    "database": "V20_POSTGRES_DB",
    "username": "V20_POSTGRES_USER",
    "password": "V20_POSTGRES_PASSWORD",
    "database_url": "V20_DATABASE_URL",
    "sslmode": "V20_POSTGRES_SSLMODE",
}

LLM_FIELD_ENV = {
    "enabled": "V20_LLM_ENABLED",
    "execute_llm": "V20_LLM_EXECUTE",
    "provider": "V20_LLM_PROVIDER",
    "host": "V20_LLM_HOST",
    "port": "V20_LLM_PORT",
    "base_url": "V20_LLM_BASE_URL",
    "model": "V20_LLM_MODEL",
    "embedding_model": "V20_LLM_EMBEDDING_MODEL",
    "api_key": "V20_LLM_API_KEY",
    "audit_model": "V20_LLM_AUDIT_MODEL",
    "audit_base_url": "V20_LLM_AUDIT_BASE_URL",
    "audit_api_key": "V20_LLM_AUDIT_API_KEY",
    "http_timeout_sec": "V20_LLM_HTTP_TIMEOUT_SEC",
    "fuse_wait_timeout_sec": "V20_LLM_FUSE_WAIT_TIMEOUT_SEC",
    "temperature": "V20_LLM_TEMPERATURE",
    "max_tokens": "V20_LLM_MAX_TOKENS",
}


def admin_config_path() -> Path:
    configured = os.getenv("V20_ADMIN_CONFIG_PATH", "").strip()
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[1] / ".runtime" / "admin_config.json"


def apply_saved_admin_env_overrides() -> None:
    payload = _read_config()
    env = payload.get("env", {})
    if not isinstance(env, dict):
        return
    for key, value in env.items():
        if isinstance(key, str) and key.startswith("V20_") and value not in (None, ""):
            os.environ[key] = str(value)


def admin_config_status() -> dict[str, object]:
    apply_saved_admin_env_overrides()
    path = admin_config_path()
    db = _public_section(DB_FIELD_ENV)
    llm = _public_section(LLM_FIELD_ENV)
    return {
        "version": "v20.admin_config_status.v1",
        "path": str(path),
        "exists": path.exists(),
        "database": db,
        "llm": llm,
        "runtime_mutation": False,
        "guardrails": ["ADMIN_CONFIG_STATUS_ONLY", "NO_SECRET_VALUES_RENDERED"],
    }


def save_admin_database_config(payload: dict[str, Any]) -> dict[str, object]:
    updates, secret_fields = _extract_updates(payload, DB_FIELD_ENV)
    _persist_env_updates(updates)
    return _save_response("v20.admin_database_config_save.v1", updates, secret_fields)


def save_admin_llm_config(payload: dict[str, Any]) -> dict[str, object]:
    updates, secret_fields = _extract_updates(payload, LLM_FIELD_ENV)
    _persist_env_updates(updates)
    return _save_response("v20.admin_llm_config_save.v1", updates, secret_fields)


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
    if field in {"http_timeout_sec", "fuse_wait_timeout_sec", "temperature"}:
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


def _save_response(version: str, updates: dict[str, str], secret_fields: list[str]) -> dict[str, object]:
    return {
        "version": version,
        "status": "saved" if updates else "no_changes",
        "updated_env": sorted(updates),
        "secret_fields_written": sorted(secret_fields),
        "path": str(admin_config_path()),
        "runtime_mutation": True,
        "guardrails": ["ADMIN_ONLY_CONFIG_MUTATION", "NO_SECRET_VALUES_RENDERED"],
    }
