from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RedisKeyspaceSpec:
    name: str
    prefix: str
    owner_module: str
    purpose: str
    ttl_seconds: int
    value_shape: str
    persistent_authority: bool = False
    guardrails: tuple[str, ...] = (
        "REDIS_IS_EPHEMERAL",
        "TTL_REQUIRED",
        "NO_AUTHORITY_IN_REDIS",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RedisRuntimeContract:
    version: str
    keyspaces: tuple[RedisKeyspaceSpec, ...]
    runtime_mutation: bool = False
    guardrails: tuple[str, ...] = (
        "REDIS_CONTRACT_ONLY",
        "NO_CONNECTION_BY_DEFAULT",
        "REBUILD_FROM_POSTGRES_OR_DETERMINISTIC_RUNTIME",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "keyspace_count": len(self.keyspaces),
            "keyspaces": [row.to_dict() for row in self.keyspaces],
            "runtime_mutation": self.runtime_mutation,
            "guardrails": list(self.guardrails),
        }
