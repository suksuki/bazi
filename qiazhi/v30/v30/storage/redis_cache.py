from __future__ import annotations

import json
from typing import Any, Protocol

from v30.contracts import CoreRuntimeResult
from v30.config import V30Settings
from v30.storage.names import redis_key


class RedisLike(Protocol):
    def get(self, key: str) -> Any: ...

    def set(self, key: str, value: str, ex: int | None = None) -> Any: ...


class V30RedisKeyspace:
    def __init__(self, settings: V30Settings):
        self._settings = settings

    def reading(self, reading_id: str) -> str:
        return redis_key(self._settings.env, "reading", reading_id)

    def trace(self, trace_id: str) -> str:
        return redis_key(self._settings.env, "trace", trace_id)

    def feedback(self, event_id: str) -> str:
        return redis_key(self._settings.env, "feedback", event_id)

    def policy(self, family: str) -> str:
        return redis_key(self._settings.env, "policy", family)

    def lock(self, name: str) -> str:
        return redis_key(self._settings.env, "lock", name)


class V30RedisCache:
    def __init__(self, client: RedisLike, settings: V30Settings, *, ttl_seconds: int = 3600):
        self._client = client
        self._keys = V30RedisKeyspace(settings)
        self._ttl_seconds = ttl_seconds

    def set_reading(self, runtime: CoreRuntimeResult) -> str:
        key = self._keys.reading(runtime.reading_id)
        self._client.set(key, json.dumps(runtime.model_dump(mode="json"), ensure_ascii=False), ex=self._ttl_seconds)
        return key

    def get_reading_payload(self, reading_id: str) -> dict[str, Any] | None:
        value = self._client.get(self._keys.reading(reading_id))
        if value is None:
            return None
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        if not isinstance(value, str):
            return None
        payload = json.loads(value)
        return payload if isinstance(payload, dict) else None

    def set_trace(self, runtime: CoreRuntimeResult) -> str:
        key = self._keys.trace(runtime.trace_id)
        self._client.set(key, json.dumps(runtime.model_dump(mode="json"), ensure_ascii=False), ex=self._ttl_seconds)
        return key

    def get_trace_payload(self, trace_id: str) -> dict[str, Any] | None:
        value = self._client.get(self._keys.trace(trace_id))
        if value is None:
            return None
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        if not isinstance(value, str):
            return None
        payload = json.loads(value)
        return payload if isinstance(payload, dict) else None


def build_runtime_cache(settings: V30Settings) -> V30RedisCache | None:
    if not settings.redis_url:
        return None
    try:
        import redis  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("V30_REDIS_URL requires installing redis") from exc
    client = redis.Redis.from_url(settings.redis_url)
    return V30RedisCache(client, settings)
