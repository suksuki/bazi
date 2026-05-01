from __future__ import annotations

import os
from typing import Any


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


def _public_profile(row: dict[str, Any]) -> dict[str, object]:
    payload = dict(row.get("payload") or {})
    birth = dict(payload.get("birth_input") or {})
    metadata = dict(payload.get("metadata") or {})
    return {
        "profile_id": str(row.get("profile_id") or payload.get("profile_id") or ""),
        "owner_id": str(row.get("owner_id") or payload.get("owner_id") or ""),
        "display_name": str(payload.get("display_name") or "V20 Profile"),
        "birth_input": birth,
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
