#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT / "apps"))

from core.contracts import BirthInputCanonical  # noqa: E402
from product.product_store import PostgresProductStore  # noqa: E402


DEFAULT_SOURCE_DATABASE_URL = "postgresql:///qiazhi_v40?host=/tmp"
DEFAULT_TARGET_DATABASE_URL = "postgresql:///qiazhi_v50?host=/tmp"


def imported_profile_id(source_profile_id: str) -> str:
    digest = hashlib.sha256(source_profile_id.encode("utf-8")).hexdigest()[:20]
    return f"v50-v40-profile-{digest}"


def birth_input_from_v40(row: dict[str, Any]) -> BirthInputCanonical:
    birth = dict(row.get("birth_json") or {})
    chart = dict(row.get("chart_json") or {})
    source_profile_id = str(row["profile_id"])
    gender = {"乾": "male", "坤": "female", "male": "male", "female": "female"}.get(
        str(row.get("gender") or birth.get("gender") or ""),
        "unknown",
    )
    location = str(birth.get("location") or "").strip()
    warnings = [f"imported_from_v40_admin_profile:{source_profile_id}"]
    if not location:
        location = "未记录（V40 导入）"
        warnings.append("source_birth_location_missing")
    return BirthInputCanonical(
        birth_input_id=f"v40-import:{source_profile_id}",
        name=str(row.get("display_name") or "V40 导入档案").strip(),
        gender=gender,
        calendar_type="lunar" if birth.get("calendar_type") == "lunar" else "solar",
        birth_date=str(birth.get("birth_date") or ""),
        birth_time=str(birth.get("birth_time") or "12:00"),
        birth_location=location,
        timezone=str(birth.get("timezone") or "Asia/Shanghai"),
        lunar_leap_month=bool(birth.get("leap_month", False)),
        true_solar_time_policy="not_applied",
        year_pillar=f"{chart.get('year_stem', '')}{chart.get('year_branch', '')}",
        month_pillar=f"{chart.get('month_stem', '')}{chart.get('month_branch', '')}",
        day_pillar=f"{chart.get('day_stem', '')}{chart.get('day_branch', '')}",
        hour_pillar=f"{chart.get('hour_stem', '')}{chart.get('hour_branch', '')}",
        input_quality="v40_admin_profile_import",
        warnings=warnings,
    )


def import_profiles(
    *,
    source_database_url: str,
    target_database_url: str,
    admin_email: str,
    apply: bool,
) -> dict[str, Any]:
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(source_database_url, row_factory=dict_row) as source:
        rows = source.execute(
            """
            SELECT p.profile_id, p.display_name, p.gender, p.chart_json, p.birth_json, p.is_default
            FROM v40_bazi_profiles p
            JOIN v40_user_accounts a ON a.user_id = p.user_id
            WHERE lower(a.email) = lower(%s) AND a.active = true AND p.deleted = false
            ORDER BY p.created_at, p.profile_id
            """,
            (admin_email,),
        ).fetchall()

    with psycopg.connect(target_database_url, row_factory=dict_row) as target:
        admin = target.execute(
            "SELECT user_id FROM v50_user_accounts WHERE lower(email) = lower(%s) AND account_role = 'admin' AND active = true",
            (admin_email,),
        ).fetchone()
        if not admin:
            raise RuntimeError("active_v50_admin_not_found")
        user_id = str(admin["user_id"])
        existing_rows = target.execute(
            "SELECT profile_id, is_default FROM v50_bazi_profiles WHERE user_id = %s AND deleted = false",
            (user_id,),
        ).fetchall()
    existing_ids = {str(row["profile_id"]) for row in existing_rows}
    previous_default = next((str(row["profile_id"]) for row in existing_rows if row["is_default"]), None)
    planned = [
        {
            "source_profile_id": str(row["profile_id"]),
            "target_profile_id": imported_profile_id(str(row["profile_id"])),
            "display_name": str(row["display_name"]),
            "source_default": bool(row["is_default"]),
            "birth_input": birth_input_from_v40(dict(row)),
        }
        for row in rows
    ]
    if not apply:
        return {
            "status": "dry_run",
            "source_count": len(planned),
            "would_create": sum(item["target_profile_id"] not in existing_ids for item in planned),
            "would_update": sum(item["target_profile_id"] in existing_ids for item in planned),
        }

    store = PostgresProductStore(target_database_url)
    for item in planned:
        if item["target_profile_id"] in existing_ids:
            store.save_profile(
                user_id=user_id,
                birth_input=item["birth_input"],
                profile_id=item["target_profile_id"],
            )
        else:
            _save_new_with_stable_id(store, user_id, item, target_database_url)

    selected_default = previous_default or next(
        (item["target_profile_id"] for item in planned if item["source_default"]),
        planned[0]["target_profile_id"] if planned else None,
    )
    if selected_default:
        with psycopg.connect(target_database_url) as target:
            target.execute(
                """
                UPDATE v50_bazi_profiles
                SET is_default = (profile_id = %s),
                    profile_json = jsonb_set(profile_json, '{is_default}', to_jsonb(profile_id = %s)),
                    updated_at = CASE WHEN profile_id = %s THEN now() ELSE updated_at END
                WHERE user_id = %s AND deleted = false
                """,
                (selected_default, selected_default, selected_default, user_id),
            )
    return {
        "status": "imported",
        "source_count": len(planned),
        "created": sum(item["target_profile_id"] not in existing_ids for item in planned),
        "updated": sum(item["target_profile_id"] in existing_ids for item in planned),
        "default_profile_preserved": previous_default is not None,
        "target_admin_email": admin_email,
    }


def _save_new_with_stable_id(
    store: PostgresProductStore,
    user_id: str,
    item: dict[str, Any],
    target_database_url: str,
) -> None:
    # The public store allocates random IDs for new user input. Migration IDs are deterministic for idempotency.
    profile = store.save_profile(user_id=user_id, birth_input=item["birth_input"])
    import psycopg

    with psycopg.connect(target_database_url) as conn:
        conn.execute(
            """
            UPDATE v50_bazi_profiles
            SET profile_id = %s,
                profile_json = jsonb_set(profile_json, '{profile_id}', to_jsonb(%s::text))
            WHERE user_id = %s AND profile_id = %s
            """,
            (item["target_profile_id"], item["target_profile_id"], user_id, profile["profile_id"]),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Idempotently import V40 admin Bazi profiles into the V50 admin archive.")
    parser.add_argument("--source-database-url", default=DEFAULT_SOURCE_DATABASE_URL)
    parser.add_argument("--target-database-url", default=DEFAULT_TARGET_DATABASE_URL)
    parser.add_argument("--admin-email", default="jerrydidi@gmail.com")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    result = import_profiles(
        source_database_url=args.source_database_url,
        target_database_url=args.target_database_url,
        admin_email=args.admin_email,
        apply=args.apply,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
