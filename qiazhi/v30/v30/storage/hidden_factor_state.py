from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from v30.config import V30Settings
from v30.hidden_factor import HiddenFactorState
from v30.storage.repository import _default_postgres_connect, _payload_to_dict


class HiddenFactorStateRepository(Protocol):
    def save_state(self, state: HiddenFactorState) -> None: ...

    def get_state_payload(self, state_id: str) -> dict[str, object] | None: ...


class LocalJsonHiddenFactorStateRepository:
    def __init__(self, settings: V30Settings):
        self._root = settings.runtime_dir / "hidden_factor_states"

    def save_state(self, state: HiddenFactorState) -> None:
        path = self._path(state.state_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")

    def get_state_payload(self, state_id: str) -> dict[str, object] | None:
        path = self._path(state_id)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None

    def _path(self, state_id: str) -> Path:
        return self._root / f"{state_id.replace('/', '_').replace(':', '_')}.json"


class PostgresHiddenFactorStateRepository:
    def __init__(self, settings: V30Settings, connect: Callable[[str], Any] | None = None):
        if not settings.database_url:
            raise ValueError("V30_DATABASE_URL is required for Postgres hidden-factor state repository")
        self._database_url = settings.database_url
        self._connect = connect or _default_postgres_connect

    def save_state(self, state: HiddenFactorState) -> None:
        payload = json.dumps(state.model_dump(mode="json"), ensure_ascii=False)
        with self._connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    upsert_hidden_factor_state_sql(),
                    (state.state_id, state.reading_id, state.context_id, payload),
                )
            connection.commit()

    def get_state_payload(self, state_id: str) -> dict[str, object] | None:
        with self._connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(select_hidden_factor_state_sql(), (state_id,))
                row = cursor.fetchone()
        if row is None:
            return None
        return _payload_to_dict(row[0])


def upsert_hidden_factor_state_sql() -> str:
    return """
INSERT INTO v30_hidden_factor_states (state_id, reading_id, context_id, payload)
VALUES (%s, %s, %s, %s::jsonb)
ON CONFLICT (state_id)
DO UPDATE SET payload = EXCLUDED.payload, updated_at = NOW();
""".strip()


def select_hidden_factor_state_sql() -> str:
    return "SELECT payload FROM v30_hidden_factor_states WHERE state_id = %s;"


def build_hidden_factor_state_repository(settings: V30Settings) -> HiddenFactorStateRepository:
    if settings.repository == "postgres":
        return PostgresHiddenFactorStateRepository(settings)
    return LocalJsonHiddenFactorStateRepository(settings)
