from __future__ import annotations

import json
import os
import time
import urllib.request

from v20.llm.provider import load_llm_provider_config_from_env, llm_provider_readiness_report
from v20.ops.dependencies import dependency_readiness_report
from v20.storage.postgres_pool import pooled_postgres_connection, postgres_pool_status
from v20.storage.postgres_schema import build_postgres_schema_contract


def database_admin_status() -> dict[str, object]:
    deps = dependency_readiness_report()
    contract = build_postgres_schema_contract()
    table_names = [table.name for table in contract.tables]
    url = os.getenv("V20_DATABASE_URL", "")
    payload = {
        "version": "v20.admin_database_status.v1",
        "status": "config_only",
        "active_profile": deps["active_profile"],
        "postgres": deps["postgres"],
        "postgres_pool": postgres_pool_status(),
        "database_url_present": bool(url),
        "table_names": table_names,
        "counts": {},
        "corpus_indexes": [],
        "runtime_mutation": False,
        "guardrails": [
            "ADMIN_STATUS_ONLY",
            "NO_SECRET_VALUES_RENDERED",
            "POSTGRES_IS_AUTHORITATIVE",
        ],
    }
    if not url:
        return payload
    try:
        from psycopg2 import sql
    except Exception as exc:
        return payload | {"status": "driver_missing", "error": str(exc)}
    try:
        counts: dict[str, int | None] = {}
        with pooled_postgres_connection(url) as conn:
            with conn.cursor() as cur:
                for table_name in table_names:
                    cur.execute("SELECT to_regclass(%s)", (table_name,))
                    exists = cur.fetchone()[0]
                    if not exists:
                        counts[table_name] = None
                        continue
                    cur.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table_name)))
                    counts[table_name] = int(cur.fetchone()[0])
                cur.execute(
                    """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE tablename = 'v20_corpus_snapshots'
                    ORDER BY indexname
                    """
                )
                indexes = [row[0] for row in cur.fetchall()]
    except Exception as exc:
        return payload | {"status": "connection_failed", "error": str(exc)}
    return payload | {
        "status": "connected",
        "counts": counts,
        "corpus_indexes": indexes,
        "authority_table": "v20_corpus_snapshots",
    }


def llm_admin_status(*, probe_models: bool = False) -> dict[str, object]:
    cfg = load_llm_provider_config_from_env()
    readiness = llm_provider_readiness_report(cfg)
    payload = {
        "version": "v20.admin_llm_status.v1",
        "status": "ready" if readiness["ready_for_connection"] else "config_only",
        "readiness": readiness,
        "probe_models": probe_models,
        "model_count": 0,
        "models": [],
        "runtime_mutation": False,
        "guardrails": [
            "ADMIN_STATUS_ONLY",
            "NO_SECRET_VALUES_RENDERED",
            "LLM_IS_ASSISTIVE_NOT_AUTHORITATIVE",
        ],
    }
    if not probe_models:
        return payload
    if not readiness["ready_for_connection"]:
        return payload | {"status": "not_ready_for_probe"}
    try:
        models = _load_models(cfg)
    except Exception as exc:
        return payload | {"status": "model_probe_failed", "error": str(exc)}
    return payload | {
        "status": "model_probe_ready",
        "model_count": len(models),
        "models": models,
    }


def llm_admin_test(payload: dict[str, object] | None = None) -> dict[str, object]:
    cfg = load_llm_provider_config_from_env()
    readiness = llm_provider_readiness_report(cfg)
    base = {
        "version": "v20.admin_llm_test.v1",
        "status": "not_ready",
        "provider": cfg.provider,
        "model": cfg.model,
        "ready_for_connection": readiness["ready_for_connection"],
        "executed": False,
        "runtime_mutation": False,
        "guardrails": [
            "ADMIN_ONLY_LLM_CONNECTIVITY_TEST",
            "NO_SECRET_VALUES_RENDERED",
            "TEST_PROMPT_ONLY_NO_RUNTIME_TRUTH_MUTATION",
        ],
    }
    if not readiness["ready_for_connection"]:
        return base | {"failure": "provider_not_ready"}
    prompt = str((payload or {}).get("prompt") or "Reply with one short sentence: Qiazhi admin LLM test ok.").strip()
    started = time.monotonic()
    try:
        text = _test_completion(cfg, prompt[:500])
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


def _load_models(cfg) -> list[dict[str, object]]:
    if cfg.provider in {"ollama", "ollama_native"}:
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
    rows = body.get("data", [])
    if not isinstance(rows, list):
        return []
    models = []
    for row in rows[:48]:
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
    rows = body.get("models", [])
    if not isinstance(rows, list):
        return []
    models = []
    for row in rows[:48]:
        if isinstance(row, dict):
            model_id = row.get("name") or row.get("model") or row.get("id") or ""
            models.append({"id": str(model_id), "owned_by": "ollama"})
    return models


def _test_completion(cfg, prompt: str) -> str:
    if cfg.provider in {"ollama", "ollama_native"}:
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
    if cfg.provider in {"ollama", "ollama_native"}:
        message = response_payload.get("message") if isinstance(response_payload, dict) else {}
        return str(message.get("content") or response_payload.get("response") or "").strip() if isinstance(message, dict) else ""
    return str(response_payload["choices"][0]["message"]["content"]).strip()


def _completion_timeout(cfg) -> float:
    timeout = float(getattr(cfg, "http_timeout_sec", 15.0) or 15.0)
    if cfg.provider in {"ollama", "ollama_native"}:
        return max(timeout, 30.0)
    return max(timeout, 1.0)


def _failure_detail(exc: Exception) -> str:
    detail = str(exc).strip()
    return detail[:300] if detail else type(exc).__name__


def _headers(cfg) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv(cfg.api_key_env, "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers
