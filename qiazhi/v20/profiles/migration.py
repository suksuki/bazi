from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path


QIAZHI_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_V19_PROFILE_PATH = QIAZHI_ROOT / "v19" / ".runtime" / "bazi_profiles.json"


def v19_profile_migration_preview(source_path: Path | None = None) -> dict[str, object]:
    path = source_path or DEFAULT_V19_PROFILE_PATH
    rows = _read_v19_profiles(path)
    owner_ids = sorted({str(row.get("owner_id") or "") for row in rows if isinstance(row, dict)})
    return {
        "version": "v20.v19_profile_migration_preview.v1",
        "status": "ready" if path.exists() else "source_missing",
        "source_path": str(path),
        "profile_count": len(rows),
        "owner_count": len(owner_ids),
        "owners": owner_ids[:12],
        "sample_profiles": [_profile_preview(row) for row in rows[:8]],
        "target_table": "v20_user_profiles",
        "runtime_mutation": False,
        "guardrails": [
            "PREVIEW_ONLY",
            "NO_PRIVATE_RAW_OUTPUT_BEYOND_LOCAL_PROFILE_METADATA",
            "V19_SOURCE_IS_READ_ONLY",
        ],
    }


def import_v19_profiles_to_postgres(
    *,
    apply: bool = False,
    source_path: Path | None = None,
    owner_id: str = "admin",
) -> dict[str, object]:
    path = source_path or DEFAULT_V19_PROFILE_PATH
    rows = _read_v19_profiles(path)
    url = os.getenv("V20_DATABASE_URL", "")
    payload = {
        "version": "v20.v19_profile_postgres_import.v1",
        "status": "dry_run",
        "source_path": str(path),
        "target_table": "v20_user_profiles",
        "target_owner_id": owner_id,
        "profile_count": len(rows),
        "apply": apply,
        "database_url_present": bool(url),
        "runtime_mutation": bool(apply),
        "guardrails": [
            "EXPLICIT_APPLY_REQUIRED",
            "V19_SOURCE_IS_READ_ONLY",
            "NO_SECRET_VALUES_RENDERED",
        ],
    }
    if not apply:
        return payload
    if not url:
        return payload | {"status": "blocked_missing_V20_DATABASE_URL", "imported_or_updated": 0}
    try:
        import psycopg2
        from psycopg2.extras import Json
    except Exception as exc:
        return payload | {"status": "blocked_missing_psycopg2", "error": str(exc), "imported_or_updated": 0}
    try:
        with psycopg2.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute(_CREATE_PROFILE_TABLE_SQL)
                imported = 0
                for row in rows:
                    normalized = _normalize_profile(row, owner_id=owner_id)
                    cur.execute(
                        """
                        INSERT INTO v20_user_profiles (profile_id, owner_id, source_ref, status, payload)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (profile_id) DO UPDATE SET
                          owner_id = EXCLUDED.owner_id,
                          source_ref = EXCLUDED.source_ref,
                          status = EXCLUDED.status,
                          payload = EXCLUDED.payload,
                          updated_at = now()
                        """,
                        (
                            normalized["profile_id"],
                            normalized["owner_id"],
                            normalized["source_ref"],
                            "imported_from_v19",
                            Json(normalized),
                        ),
                    )
                    imported += 1
            conn.commit()
    except Exception as exc:
        return payload | {"status": "postgres_import_failed", "error": str(exc), "imported_or_updated": 0}
    return payload | {"status": "imported", "imported_or_updated": imported}


def _read_v19_profiles(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        rows = [value for value in raw.values() if isinstance(value, dict)]
    elif isinstance(raw, list):
        rows = [value for value in raw if isinstance(value, dict)]
    else:
        rows = []
    return sorted(rows, key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""), reverse=True)


def _profile_preview(row: dict[str, object]) -> dict[str, object]:
    birth = dict(row.get("birth_input") or {})
    return {
        "profile_id": str(row.get("id") or ""),
        "owner_id": str(row.get("owner_id") or ""),
        "name": str(row.get("name") or "V19 Profile"),
        "birth_year": birth.get("year"),
        "calendar": birth.get("calendar") or birth.get("calendar_type"),
        "location_preserved": bool(birth.get("location")),
        "updated_at": row.get("updated_at") or row.get("created_at") or "",
    }


def _normalize_profile(row: dict[str, object], *, owner_id: str = "admin") -> dict[str, object]:
    profile_id = str(row.get("id") or "").strip()
    if not profile_id:
        digest = hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
        profile_id = f"v19_profile_{digest}"
    birth = dict(row.get("birth_input") or {})
    metadata = dict(row.get("metadata") or {})
    return {
        "version": "v20.user_profile.v1",
        "profile_id": profile_id,
        "owner_id": str(owner_id or "admin"),
        "display_name": str(row.get("name") or "V19 Profile"),
        "birth_input": birth,
        "metadata": {
            **metadata,
            "source_system": "v19",
            "source_profile_id": profile_id,
            "source_owner_id": str(row.get("owner_id") or ""),
            "location_preserved": bool(birth.get("location")),
        },
        "source_ref": f"v19:bazi_profiles:{profile_id}",
        "created_at": row.get("created_at") or "",
        "updated_at": row.get("updated_at") or row.get("created_at") or "",
        "guardrails": [
            "PROFILE_DATA_IMPORTED_AS_USER_CONTEXT",
            "LOCATION_PRESERVED_NOT_USED_FOR_CHART_FACTS_UNLESS_SUPPORTED",
            "NO_RULE_MUTATION_FROM_PROFILE_IMPORT",
        ],
    }


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
