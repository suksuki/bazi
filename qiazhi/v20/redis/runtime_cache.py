from __future__ import annotations

import copy
import hashlib
import json
import os
from typing import Any

from v20.redis.contracts import redis_contract_manifest


CACHE_VERSION = "v20.redis_runtime_cache.v1"
CACHE_DISABLED_META = {
    "cache_status": "disabled",
    "cache_key": "",
    "cache_ttl_seconds": 0,
    "cache_runtime_mutation": False,
}


def runtime_cache_key(payload: dict[str, Any], *, role_key: str = "") -> str:
    stable_payload = {
        "version": CACHE_VERSION,
        "role_key": role_key,
        "payload": payload,
    }
    encoded = json.dumps(stable_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    prefix = _request_cache_prefix()
    return f"{prefix}{digest}"


def get_runtime_cache(key: str) -> dict[str, Any] | None:
    client = _redis_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
        if not raw:
            return None
        payload = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else str(raw))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    result = payload.get("result")
    if not isinstance(result, dict):
        return None
    cloned = copy.deepcopy(result)
    _attach_cache_meta(cloned, "hit", key, int(payload.get("ttl_seconds", _request_cache_ttl())))
    return cloned


def set_runtime_cache(key: str, result: dict[str, Any], *, ttl_seconds: int | None = None) -> bool:
    client = _redis_client()
    if client is None:
        return False
    ttl = int(ttl_seconds or _request_cache_ttl())
    payload = {
        "version": CACHE_VERSION,
        "result": _without_cache_meta(result),
        "ttl_seconds": ttl,
        "runtime_mutation": False,
    }
    try:
        client.setex(key, ttl, json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return True
    except Exception:
        return False


def runtime_cache_status() -> dict[str, Any]:
    prefix = _request_cache_prefix()
    ttl = _request_cache_ttl()
    client = _redis_client()
    status = {
        "version": "v20.redis_runtime_cache_status.v1",
        "status": "unavailable",
        "keyspace": "request_cache",
        "prefix": prefix,
        "ttl_seconds": ttl,
        "key_count": 0,
        "db": _configured_db(),
        "runtime_mutation": False,
        "guardrails": [
            "REDIS_STATUS_IS_OBSERVABILITY_ONLY",
            "NO_CACHE_VALUES_RENDERED",
            "REDIS_REMAINS_EPHEMERAL",
        ],
    }
    if client is None:
        return status | {"failure": "client_unavailable"}
    try:
        key_count = sum(1 for _ in client.scan_iter(match=f"{prefix}*", count=100))
        return status | {
            "status": "ready",
            "key_count": key_count,
            "ping": bool(client.ping()),
        }
    except Exception as exc:
        return status | {
            "status": "degraded",
            "failure": f"{type(exc).__name__}: {exc}",
        }


def cacheable_measure_payload(payload: object, *, pillars: dict[str, str], luck_pillar: str) -> dict[str, Any]:
    return {
        "year": pillars.get("year", ""),
        "month": pillars.get("month", ""),
        "day": pillars.get("day", ""),
        "hour": pillars.get("hour", ""),
        "flow_year_pillar": getattr(payload, "flow_year_pillar", ""),
        "luck_pillar": luck_pillar,
        "flow_month_pillar": getattr(payload, "flow_month_pillar", ""),
        "question_key": getattr(payload, "question_key", ""),
        "question_id": getattr(payload, "question_id", ""),
        "user_text": getattr(payload, "user_text", ""),
        "locale": getattr(payload, "locale", "zh"),
        "llm_mode": "deterministic",
        "practitioner_selections": [
            selection.model_dump() if hasattr(selection, "model_dump") else dict(selection)
            for selection in getattr(payload, "practitioner_selections", ())
        ],
        "latent_event_answers": [
            answer.model_dump() if hasattr(answer, "model_dump") else dict(answer)
            for answer in getattr(payload, "latent_event_answers", ())
        ],
        "answered_question_ids": list(getattr(payload, "answered_question_ids", ())),
        "answered_question_keys": list(getattr(payload, "answered_question_keys", ())),
    }


def should_cache_measure(payload: object) -> bool:
    return getattr(payload, "llm_mode", "deterministic") == "deterministic"


def attach_cache_miss_meta(result: dict[str, Any], key: str, *, stored: bool) -> dict[str, Any]:
    _attach_cache_meta(result, "miss_stored" if stored else "miss_not_stored", key, _request_cache_ttl())
    return result


def _attach_cache_meta(result: dict[str, Any], status: str, key: str, ttl_seconds: int) -> None:
    result["redis_cache"] = {
        "version": CACHE_VERSION,
        "cache_status": status,
        "keyspace": "request_cache",
        "cache_key": key,
        "ttl_seconds": ttl_seconds,
        "runtime_mutation": False,
        "guardrails": [
            "REDIS_CACHE_IS_EPHEMERAL",
            "CACHE_HIT_DOES_NOT_CHANGE_AUTHORITY",
            "DETERMINISTIC_RUNTIME_ONLY",
        ],
    }


def _without_cache_meta(result: dict[str, Any]) -> dict[str, Any]:
    cloned = copy.deepcopy(result)
    cloned.pop("redis_cache", None)
    return cloned


def _redis_client() -> Any | None:
    if os.getenv("V20_REDIS_ENABLED", "1").lower() in {"0", "false", "no"}:
        return None
    try:
        import redis as redis_module
    except Exception:
        return None
    url = os.getenv("V20_REDIS_URL", "")
    try:
        if url:
            return redis_module.Redis.from_url(url, socket_connect_timeout=0.08, socket_timeout=0.08)
        return redis_module.Redis(
            host=os.getenv("V20_REDIS_HOST", "127.0.0.1"),
            port=int(os.getenv("V20_REDIS_PORT", "6379")),
            db=int(os.getenv("V20_REDIS_DB", "20")),
            socket_connect_timeout=0.08,
            socket_timeout=0.08,
        )
    except Exception:
        return None


def _configured_db() -> int:
    url = os.getenv("V20_REDIS_URL", "")
    if "/" in url.rsplit("@", 1)[-1]:
        tail = url.rsplit("/", 1)[-1]
        if tail.isdigit():
            return int(tail)
    try:
        return int(os.getenv("V20_REDIS_DB", "20"))
    except ValueError:
        return 20


def _request_cache_prefix() -> str:
    contract = redis_contract_manifest()
    for row in contract.keyspaces:
        if row.name == "request_cache":
            return row.prefix
    return "v20:cache:request:"


def _request_cache_ttl() -> int:
    contract = redis_contract_manifest()
    for row in contract.keyspaces:
        if row.name == "request_cache":
            return int(row.ttl_seconds)
    return 300
