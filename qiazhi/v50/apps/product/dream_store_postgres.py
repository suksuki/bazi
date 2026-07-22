from __future__ import annotations

from experience.dream import DreamSceneGrant, DreamVisit
from product.database_schema import check_product_database_schema
from product.dream_store_contracts import DreamStoreConflict


class PostgresDreamStore:
    persistent = True
    storage_name = "v50_postgresql"

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        check_product_database_schema(database_url)

    def _connect(self):
        import psycopg

        return psycopg.connect(self.database_url)

    def create_visit(self, visit: DreamVisit) -> DreamVisit:
        from psycopg.errors import UniqueViolation
        from psycopg.types.json import Jsonb

        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO v50_dream_visits
                            (visit_id, owner_user_id, state, visit_json)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            visit.visit_id,
                            visit.owner_user_id,
                            visit.state.value,
                            Jsonb(visit.model_dump(mode="json")),
                        ),
                    )
        except UniqueViolation as exc:
            raise DreamStoreConflict("dream_visit_already_exists") from exc
        return visit

    def update_visit(self, visit: DreamVisit, *, expected_row_version: int) -> DreamVisit:
        from psycopg.types.json import Jsonb

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE v50_dream_visits
                    SET state = %s, visit_json = %s, updated_at = now()
                    WHERE visit_id = %s
                      AND owner_user_id = %s
                      AND COALESCE((visit_json->>'row_version')::integer, 0) = %s
                    """,
                    (
                        visit.state.value,
                        Jsonb(visit.model_dump(mode="json")),
                        visit.visit_id,
                        visit.owner_user_id,
                        expected_row_version,
                    ),
                )
                if cur.rowcount != 1:
                    raise DreamStoreConflict("dream_visit_version_conflict")
        return visit

    def get_visit(self, *, visit_id: str, owner_user_id: str) -> DreamVisit | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT visit_json
                    FROM v50_dream_visits
                    WHERE visit_id = %s AND owner_user_id = %s
                    """,
                    (visit_id, owner_user_id),
                )
                row = cur.fetchone()
        return DreamVisit.model_validate(row["visit_json"]) if row else None

    def find_resumable_visit(self, *, owner_user_id: str) -> DreamVisit | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT visit_json
                    FROM v50_dream_visits
                    WHERE owner_user_id = %s AND state <> 'COMPLETED'
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    (owner_user_id,),
                )
                row = cur.fetchone()
        return DreamVisit.model_validate(row["visit_json"]) if row else None

    def save_grant(self, grant: DreamSceneGrant) -> DreamSceneGrant:
        from psycopg.types.json import Jsonb

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v50_dream_scene_grants
                        (grant_id, case_id, public_scene_ref, status, grant_json)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (grant_id) DO UPDATE SET
                        case_id = EXCLUDED.case_id,
                        public_scene_ref = EXCLUDED.public_scene_ref,
                        status = EXCLUDED.status,
                        grant_json = EXCLUDED.grant_json,
                        updated_at = now()
                    """,
                    (
                        grant.grant_id,
                        grant.case_id,
                        grant.public_scene_ref,
                        grant.status,
                        Jsonb(grant.model_dump(mode="json")),
                    ),
                )
        return grant

    def get_grant(self, *, public_scene_ref: str) -> DreamSceneGrant | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT grant_json
                    FROM v50_dream_scene_grants
                    WHERE public_scene_ref = %s
                    """,
                    (public_scene_ref,),
                )
                row = cur.fetchone()
        return DreamSceneGrant.model_validate(row["grant_json"]) if row else None

    def list_grants(self) -> list[DreamSceneGrant]:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT grant_json
                    FROM v50_dream_scene_grants
                    ORDER BY created_at, grant_id
                    """
                )
                rows = cur.fetchall()
        return [DreamSceneGrant.model_validate(row["grant_json"]) for row in rows]


__all__ = ["PostgresDreamStore"]
