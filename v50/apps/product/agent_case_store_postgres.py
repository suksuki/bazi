from __future__ import annotations

from typing import Any

from product.agent_case_payload import canonical_case_payload, compatibility_case_row
from product.database_schema import check_product_database_schema


class PostgresAgentCaseStore:
    persistent = True
    storage_name = "v50_postgresql"

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        check_product_database_schema(database_url)

    def _connect(self):
        import psycopg

        return psycopg.connect(self.database_url)

    def save(self, *, case_id: str, user_id: str | None, profile_id: str | None, payload: dict[str, Any]) -> None:
        from psycopg.types.json import Jsonb

        canonical = canonical_case_payload(payload)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v50_mingli_agent_cases (case_id, user_id, profile_id, case_json)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (case_id) DO UPDATE SET
                        user_id = COALESCE(EXCLUDED.user_id, v50_mingli_agent_cases.user_id),
                        profile_id = COALESCE(EXCLUDED.profile_id, v50_mingli_agent_cases.profile_id),
                        case_json = EXCLUDED.case_json,
                        updated_at = now()
                    """,
                    (case_id, user_id, profile_id, Jsonb(canonical)),
                )

    def get(self, *, case_id: str, user_id: str | None = None) -> dict[str, Any] | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                if user_id is None:
                    cur.execute("SELECT case_json, user_id, profile_id FROM v50_mingli_agent_cases WHERE case_id = %s", (case_id,))
                else:
                    cur.execute(
                        "SELECT case_json, user_id, profile_id FROM v50_mingli_agent_cases WHERE case_id = %s AND (user_id = %s OR user_id IS NULL)",
                        (case_id, user_id),
                    )
                row = cur.fetchone()
        return compatibility_case_row({
            **dict(row["case_json"]),
            "user_id": row["user_id"],
            "profile_id": row["profile_id"],
        }) if row else None

    def list_for_user(self, *, user_id: str) -> list[dict[str, Any]]:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT case_json FROM v50_mingli_agent_cases WHERE user_id = %s ORDER BY updated_at DESC LIMIT 100",
                    (user_id,),
                )
                rows = cur.fetchall()
        return [compatibility_case_row(dict(row["case_json"])) for row in rows]
