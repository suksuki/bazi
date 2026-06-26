from __future__ import annotations

import copy
import hashlib
import json
import os
import time
from typing import Any

from v20.redis.contracts import redis_contract_manifest
from v20.storage.local_jsonl import local_jsonl_store_from_env


CACHE_VERSION = "v20.redis_runtime_cache.v1"
CACHE_DISABLED_META = {
    "cache_status": "disabled",
    "cache_key": "",
    "cache_ttl_seconds": 0,
    "cache_runtime_mutation": False,
}
RATE_LIMIT_VERSION = "v20.redis_rate_limit.v1"


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


def clear_runtime_request_cache(*, batch_size: int = 100) -> dict[str, Any]:
    prefix = _request_cache_prefix()
    client = _redis_client()
    result = {
        "version": "v20.redis_runtime_cache_clear.v1",
        "status": "unavailable",
        "keyspace": "request_cache",
        "prefix": prefix,
        "deleted_count": 0,
        "runtime_mutation": True,
        "guardrails": [
            "REQUEST_CACHE_ONLY",
            "NO_CACHE_VALUES_RENDERED",
            "REDIS_REMAINS_EPHEMERAL",
        ],
    }
    if client is None:
        return result | {"failure": "client_unavailable"}
    try:
        keys = list(client.scan_iter(match=f"{prefix}*", count=batch_size))
        deleted = 0
        for index in range(0, len(keys), batch_size):
            chunk = keys[index : index + batch_size]
            if chunk:
                deleted += int(client.delete(*chunk) or 0)
        return result | {
            "status": "cleared",
            "deleted_count": deleted,
        }
    except Exception as exc:
        return result | {
            "status": "degraded",
            "failure": f"{type(exc).__name__}: {exc}",
        }


def check_rate_limit(
    identity: str,
    *,
    route_key: str,
    limit: int | None = None,
    window_seconds: int | None = None,
) -> dict[str, Any]:
    limit = int(limit or os.getenv("V20_RATE_LIMIT_PER_MINUTE", "30"))
    window_seconds = int(window_seconds or os.getenv("V20_RATE_LIMIT_WINDOW_SECONDS", "60"))
    limit = max(1, limit)
    window_seconds = max(1, window_seconds)
    prefix = _rate_limit_prefix()
    client = _redis_client()
    safe_identity = hashlib.sha256(str(identity or "anonymous").encode("utf-8")).hexdigest()[:16]
    safe_route = hashlib.sha256(str(route_key or "route").encode("utf-8")).hexdigest()[:10]
    window = int(time.time() // window_seconds)
    key = f"{prefix}{safe_route}:{safe_identity}:{window}"
    result = {
        "version": RATE_LIMIT_VERSION,
        "status": "unavailable",
        "allowed": True,
        "route_key": route_key,
        "limit": limit,
        "window_seconds": window_seconds,
        "remaining": limit,
        "retry_after_seconds": 0,
        "runtime_mutation": False,
        "guardrails": [
            "RATE_LIMIT_IS_EPHEMERAL",
            "NO_RAW_IDENTITY_RENDERED",
            "FAIL_OPEN_WHEN_REDIS_UNAVAILABLE",
        ],
    }
    if client is None:
        return result | {"failure": "client_unavailable"}
    try:
        count = int(client.incr(key))
        if count == 1:
            client.expire(key, window_seconds)
        remaining = max(0, limit - count)
        allowed = count <= limit
        return result | {
            "status": "allowed" if allowed else "blocked",
            "allowed": allowed,
            "remaining": remaining,
            "retry_after_seconds": 0 if allowed else window_seconds,
            "runtime_mutation": True,
        }
    except Exception as exc:
        return result | {
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
        "active_runtime_pointers": _active_runtime_pointer_versions(),
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


def _active_runtime_pointer_versions() -> dict[str, str]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    pointers = {
        "question": runtime_dir / "training" / "question_policy_versions" / "active_pointer.json",
        "orchestrator": runtime_dir / "training" / "orchestrator_policy_versions" / "active_pointer.json",
        "rule": runtime_dir / "training" / "rule_policy_versions" / "active_pointer.json",
        "portrait": runtime_dir / "training" / "portrait_policy_versions" / "active_pointer.json",
        "structure_dynamics": runtime_dir / "training" / "structure_dynamics_policy_versions" / "active_pointer.json",
    }
    versions: dict[str, str] = {}
    for key, path in pointers.items():
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        active = str(payload.get("active_policy_version", ""))
        if active:
            versions[key] = active
    return versions


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


def _rate_limit_prefix() -> str:
    contract = redis_contract_manifest()
    for row in contract.keyspaces:
        if row.name == "rate_limit":
            return row.prefix
    return "v20:rate:"


def _request_cache_ttl() -> int:
    contract = redis_contract_manifest()
    for row in contract.keyspaces:
        if row.name == "request_cache":
            return int(row.ttl_seconds)
    return 300
