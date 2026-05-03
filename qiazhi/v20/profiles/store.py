from __future__ import annotations

import os
import uuid
from typing import Any

from v20.core.calendar import chart_defaults_from_birth_input


_CREATE_PROFILE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS v20_user_profiles (
  profile_id text PRIMARY KEY,
  owner_id text NOT NULL,
  source_ref text NOT NULL,
  status text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  payload jsonb NOT NULL
)
"""


def list_profiles_from_postgres(*, owner_id: str = "", limit: int = 80) -> dict[str, object]:
    url = os.getenv("V20_DATABASE_URL", "")
    payload = {
        "version": "v20.profile_list.v1",
        "status": "dry_config",
        "owner_id": owner_id,
        "profiles": [],
        "profile_count": 0,
        "database_url_present": bool(url),
        "runtime_mutation": False,
        "guardrails": ["PROFILE_LIST_READ_ONLY", "NO_SECRET_VALUES_RENDERED"],
    }
    if not url:
        return payload | {"status": "blocked_missing_V20_DATABASE_URL"}
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except Exception as exc:
        return payload | {"status": "blocked_missing_psycopg2", "error": str(exc)}
    try:
        with psycopg2.connect(url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                where = "where owner_id = %s" if owner_id else ""
                params: list[object] = [owner_id] if owner_id else []
                params.append(max(1, min(int(limit or 80), 200)))
                cur.execute(
                    f"""
                    select profile_id, owner_id, source_ref, status, created_at, updated_at, payload
                    from v20_user_profiles
                    {where}
                    order by updated_at desc
                    limit %s
                    """,
                    params,
                )
                rows = cur.fetchall()
    except Exception as exc:
        return payload | {"status": "postgres_query_failed", "error": str(exc)}
    profiles = [_public_profile(dict(row)) for row in rows]
    return payload | {
        "status": "ready",
        "profiles": profiles,
        "profile_count": len(profiles),
    }


def read_profile_from_postgres(profile_id: str) -> dict[str, object]:
    clean_id = str(profile_id or "").strip()
    payload = {
        "version": "v20.profile_detail.v1",
        "status": "not_found",
        "profile_id": clean_id,
        "profile": {},
        "runtime_mutation": False,
        "guardrails": ["PROFILE_DETAIL_READ_ONLY", "NO_SECRET_VALUES_RENDERED"],
    }
    if not clean_id:
        return payload
    url = os.getenv("V20_DATABASE_URL", "")
    if not url:
        return payload | {"status": "blocked_missing_V20_DATABASE_URL"}
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except Exception as exc:
        return payload | {"status": "blocked_missing_psycopg2", "error": str(exc)}
    try:
        with psycopg2.connect(url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    select profile_id, owner_id, source_ref, status, created_at, updated_at, payload
                    from v20_user_profiles
                    where profile_id = %s
                    """,
                    (clean_id,),
                )
                row = cur.fetchone()
    except Exception as exc:
        return payload | {"status": "postgres_query_failed", "error": str(exc)}
    if not row:
        return payload
    return payload | {"status": "ready", "profile": _public_profile(dict(row))}


def create_profile_in_postgres(*, owner_id: str, payload: dict[str, Any]) -> dict[str, object]:
    profile_id = f"v20_profile_{uuid.uuid4().hex[:16]}"
    clean_payload = _normalized_mutation_payload(payload, profile_id=profile_id, owner_id=owner_id)
    return _upsert_profile(profile_id=profile_id, owner_id=owner_id, payload=clean_payload, created=True)


def update_profile_in_postgres(*, profile_id: str, owner_id: str, payload: dict[str, Any]) -> dict[str, object]:
    clean_id = str(profile_id or "").strip()
    clean_payload = _normalized_mutation_payload(payload, profile_id=clean_id, owner_id=owner_id)
    return _upsert_profile(profile_id=clean_id, owner_id=owner_id, payload=clean_payload, created=False)


def delete_profile_from_postgres(profile_id: str) -> dict[str, object]:
    clean_id = str(profile_id or "").strip()
    payload = {
        "version": "v20.profile_delete.v1",
        "status": "not_found",
        "profile_id": clean_id,
        "deleted": False,
        "runtime_mutation": True,
        "guardrails": ["PROFILE_DELETE_EXPLICIT_REQUEST", "NO_RULE_MUTATION_FROM_PROFILE_MANAGEMENT"],
    }
    if not clean_id:
        return payload
    url = os.getenv("V20_DATABASE_URL", "")
    if not url:
        return payload | {"status": "blocked_missing_V20_DATABASE_URL"}
    try:
        import psycopg2
    except Exception as exc:
        return payload | {"status": "blocked_missing_psycopg2", "error": str(exc)}
    try:
        with psycopg2.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute("delete from v20_user_profiles where profile_id = %s", (clean_id,))
                deleted = cur.rowcount > 0
            conn.commit()
    except Exception as exc:
        return payload | {"status": "postgres_delete_failed", "error": str(exc)}
    return payload | {"status": "deleted" if deleted else "not_found", "deleted": deleted}


def _upsert_profile(*, profile_id: str, owner_id: str, payload: dict[str, Any], created: bool) -> dict[str, object]:
    base = {
        "version": "v20.profile_mutation.v1",
        "status": "dry_config",
        "profile_id": profile_id,
        "profile": {},
        "runtime_mutation": True,
        "guardrails": ["PROFILE_MANAGEMENT_USER_REQUEST", "NO_RULE_MUTATION_FROM_PROFILE_MANAGEMENT"],
    }
    if not profile_id or not owner_id:
        return base | {"status": "invalid_profile"}
    url = os.getenv("V20_DATABASE_URL", "")
    if not url:
        return base | {"status": "blocked_missing_V20_DATABASE_URL"}
    try:
        import psycopg2
        from psycopg2.extras import Json, RealDictCursor
    except Exception as exc:
        return base | {"status": "blocked_missing_psycopg2", "error": str(exc)}
    try:
        with psycopg2.connect(url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(_CREATE_PROFILE_TABLE_SQL)
                cur.execute(
                    """
                    insert into v20_user_profiles (profile_id, owner_id, source_ref, status, payload)
                    values (%s, %s, %s, %s, %s)
                    on conflict (profile_id) do update set
                      owner_id = excluded.owner_id,
                      source_ref = excluded.source_ref,
                      status = excluded.status,
                      payload = excluded.payload,
                      updated_at = now()
                    returning profile_id, owner_id, source_ref, status, created_at, updated_at, payload
                    """,
                    (
                        profile_id,
                        owner_id,
                        str(payload.get("source_ref") or f"v20:native:{profile_id}"),
                        str(payload.get("status") or "active"),
                        Json(payload),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception as exc:
        return base | {"status": "postgres_mutation_failed", "error": str(exc)}
    return base | {
        "status": "created" if created else "updated",
        "profile": _public_profile(dict(row or {})),
    }


def _normalized_mutation_payload(payload: dict[str, Any], *, profile_id: str, owner_id: str) -> dict[str, object]:
    birth = dict(payload.get("birth_input") or {})
    metadata = dict(payload.get("metadata") or {})
    return {
        "version": "v20.user_profile.v1",
        "profile_id": profile_id,
        "owner_id": owner_id,
        "display_name": str(payload.get("display_name") or "未命名档案").strip()[:120],
        "birth_input": birth,
        "metadata": {
            **metadata,
            "source_system": str(metadata.get("source_system") or "v20_native"),
            "location_preserved": bool(metadata.get("location_preserved")),
        },
        "source_ref": str(payload.get("source_ref") or f"v20:native:{profile_id}"),
        "status": str(payload.get("status") or "active"),
        "guardrails": [
            "PROFILE_DATA_IS_USER_CONTEXT",
            "NO_RULE_MUTATION_FROM_PROFILE_MANAGEMENT",
        ],
    }


def _public_profile(row: dict[str, Any]) -> dict[str, object]:
    payload = dict(row.get("payload") or {})
    birth = dict(payload.get("birth_input") or {})
    metadata = dict(payload.get("metadata") or {})
    chart_defaults = chart_defaults_from_birth_input(birth) if birth else {}
    return {
        "profile_id": str(row.get("profile_id") or payload.get("profile_id") or ""),
        "owner_id": str(row.get("owner_id") or payload.get("owner_id") or ""),
        "display_name": str(payload.get("display_name") or "V20 Profile"),
        "birth_input": birth,
        "chart_defaults": chart_defaults,
        "source_ref": str(row.get("source_ref") or payload.get("source_ref") or ""),
        "status": str(row.get("status") or ""),
        "created_at": _iso(row.get("created_at") or payload.get("created_at") or ""),
        "updated_at": _iso(row.get("updated_at") or payload.get("updated_at") or ""),
        "metadata": {
            "source_system": str(metadata.get("source_system") or ""),
            "source_owner_id": str(metadata.get("source_owner_id") or ""),
            "location_preserved": bool(metadata.get("location_preserved")),
        },
    }


def _iso(value: object) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value or "")
