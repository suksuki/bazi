from __future__ import annotations

import json
import os
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


def _load_models(cfg) -> list[dict[str, object]]:
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


def _headers(cfg) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv(cfg.api_key_env, "")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers
