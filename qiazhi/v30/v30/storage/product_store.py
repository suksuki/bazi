from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from v30.config import V30Settings
from v30.storage.repository import _default_postgres_connect


ProductStorePayload = dict[str, dict[str, object]]


class ProductStoreRepository(Protocol):
    def load(self) -> ProductStorePayload: ...

    def save(self, store: ProductStorePayload) -> None: ...


class LocalJsonProductStoreRepository:
    def __init__(self, path: Path):
        self._path = path

    def load(self) -> ProductStorePayload:
        return _coerce_store(_read_json(self._path))

    def save(self, store: ProductStorePayload) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(_coerce_store(store), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self._path)


class PostgresProductStoreRepository:
    def __init__(
        self,
        settings: V30Settings,
        *,
        fallback_path: Path,
        connect: Callable[[str], Any] | None = None,
    ):
        if not settings.database_url:
            raise ValueError("V30_DATABASE_URL is required for Postgres product store")
        self._database_url = settings.database_url
        self._fallback = LocalJsonProductStoreRepository(fallback_path)
        self._connect = connect or _default_postgres_connect

    def load(self) -> ProductStorePayload:
        try:
            store = self._load_postgres()
        except Exception:
            return self._fallback.load()
        if any(store[key] for key in ("users", "sessions", "profiles")):
            return store
        fallback = self._fallback.load()
        if any(fallback[key] for key in ("users", "sessions", "profiles")):
            self.save(fallback)
            return fallback
        return store

    def save(self, store: ProductStorePayload) -> None:
        store = _coerce_store(store)
        with self._connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM v30_product_sessions;")
                cursor.execute("DELETE FROM v30_bazi_profiles;")
                cursor.execute("DELETE FROM v30_product_users;")
                for username, user in store["users"].items():
                    cursor.execute(
                        """
INSERT INTO v30_product_users (username, actor_id, role, payload)
VALUES (%s, %s, %s, %s::jsonb)
ON CONFLICT (username)
DO UPDATE SET actor_id = EXCLUDED.actor_id, role = EXCLUDED.role, payload = EXCLUDED.payload, updated_at = NOW();
""".strip(),
                        (
                            username,
                            str(user.get("actor_id") or ""),
                            str(user.get("role") or "user"),
                            json.dumps(user, ensure_ascii=False),
                        ),
                    )
                for token, session in store["sessions"].items():
                    cursor.execute(
                        """
INSERT INTO v30_product_sessions (session_token, username, actor_id, payload)
VALUES (%s, %s, %s, %s::jsonb)
ON CONFLICT (session_token)
DO UPDATE SET username = EXCLUDED.username, actor_id = EXCLUDED.actor_id, payload = EXCLUDED.payload;
""".strip(),
                        (
                            token,
                            str(session.get("username") or ""),
                            str(session.get("actor_id") or ""),
                            json.dumps(session, ensure_ascii=False),
                        ),
                    )
                for profile_id, profile in store["profiles"].items():
                    cursor.execute(
                        """
INSERT INTO v30_bazi_profiles (profile_id, actor_id, status, payload)
VALUES (%s, %s, %s, %s::jsonb)
ON CONFLICT (profile_id)
DO UPDATE SET actor_id = EXCLUDED.actor_id, status = EXCLUDED.status, payload = EXCLUDED.payload, updated_at = NOW();
""".strip(),
                        (
                            profile_id,
                            str(profile.get("actor_id") or ""),
                            str(profile.get("status") or "active"),
                            json.dumps(profile, ensure_ascii=False),
                        ),
                    )
            connection.commit()

    def _load_postgres(self) -> ProductStorePayload:
        store = _empty_store()
        with self._connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT username, payload FROM v30_product_users;")
                for username, payload in cursor.fetchall():
                    row = _payload_dict(payload)
                    if row:
                        store["users"][str(username)] = row
                cursor.execute("SELECT session_token, payload FROM v30_product_sessions;")
                for token, payload in cursor.fetchall():
                    row = _payload_dict(payload)
                    if row:
                        store["sessions"][str(token)] = row
                cursor.execute("SELECT profile_id, payload FROM v30_bazi_profiles;")
                for profile_id, payload in cursor.fetchall():
                    row = _payload_dict(payload)
                    if row:
                        store["profiles"][str(profile_id)] = row
        return store


def build_product_store_repository(settings: V30Settings, path: Path) -> ProductStoreRepository:
    if settings.repository == "postgres":
        return PostgresProductStoreRepository(settings, fallback_path=path)
    return LocalJsonProductStoreRepository(path)


def _read_json(path: Path) -> object:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _coerce_store(payload: object) -> ProductStorePayload:
    payload = payload if isinstance(payload, dict) else {}
    return {
        "users": payload.get("users") if isinstance(payload.get("users"), dict) else {},
        "sessions": payload.get("sessions") if isinstance(payload.get("sessions"), dict) else {},
        "profiles": payload.get("profiles") if isinstance(payload.get("profiles"), dict) else {},
    }


def _empty_store() -> ProductStorePayload:
    return {"users": {}, "sessions": {}, "profiles": {}}


def _payload_dict(payload: object) -> dict[str, object]:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}
