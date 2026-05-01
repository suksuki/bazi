from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    data_type: str
    nullable: bool = False
    purpose: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TableSpec:
    name: str
    owner_module: str
    purpose: str
    columns: tuple[ColumnSpec, ...]
    primary_key: tuple[str, ...]
    pii_policy: str = "no_raw_private_data"
    guardrails: tuple[str, ...] = (
        "POSTGRES_TABLE_IS_AUTHORITATIVE",
        "NO_SECRET_COLUMNS",
        "NO_REDIS_AUTHORITY",
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["columns"] = [row.to_dict() for row in self.columns]
        return payload


@dataclass(frozen=True)
class MigrationSpec:
    migration_id: str
    description: str
    sql: tuple[str, ...]
    reversible: bool = False
    destructive: bool = False
    guardrails: tuple[str, ...] = (
        "MIGRATION_REQUIRES_BACKUP",
        "MIGRATION_REQUIRES_REVIEW",
        "NO_DESTRUCTIVE_DEFAULT",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StorageSchemaContract:
    version: str
    backend: str
    tables: tuple[TableSpec, ...]
    migrations: tuple[MigrationSpec, ...]
    runtime_mutation: bool = False
    guardrails: tuple[str, ...] = (
        "SCHEMA_CONTRACT_ONLY",
        "NO_DATABASE_CONNECTION_BY_DEFAULT",
        "POSTGRES_IS_PERSISTENT_AUTHORITY",
        "REDIS_IS_EPHEMERAL",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "backend": self.backend,
            "table_count": len(self.tables),
            "tables": [row.to_dict() for row in self.tables],
            "migrations": [row.to_dict() for row in self.migrations],
            "runtime_mutation": self.runtime_mutation,
            "guardrails": list(self.guardrails),
        }
