from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from experience.dream import DreamSceneGrant, DreamVisit
from experience.dream_navigation import (
    DreamControlCredential,
    DreamControlLease,
    DreamDepartureAnchor,
    DreamDepartureResult,
    DreamGuestAnchorMigrationResult,
    DreamRecoveryCheckpoint,
)
from experience.dream_game import (
    BlindRoundDefinition,
    DreamGameAttempt,
    DreamGameRecordEnvelope,
    FlowerClosureRecord,
    FlowerLifecycle,
    MaturedFruitContentPack,
    OutcomeEvidence,
    SharedFruit,
    SystemJudgmentSeal,
    UserJudgmentSeal,
)
from product.database_schema import check_product_database_schema
from product.dream_store_contracts import DreamStoreConflict, normalize_dream_visit


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

        visit = normalize_dream_visit(visit)
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

        visit = normalize_dream_visit(visit)
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
        return normalize_dream_visit(row["visit_json"]) if row else None

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
        return normalize_dream_visit(row["visit_json"]) if row else None

    def list_visits(self, *, owner_user_id: str, case_namespace: str = "") -> list[DreamVisit]:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                if case_namespace:
                    cur.execute(
                        """
                        SELECT visit_json
                        FROM v50_dream_visits
                        WHERE owner_user_id = %s
                          AND COALESCE(visit_json->>'case_namespace', '') = %s
                        ORDER BY created_at, visit_id
                        """,
                        (owner_user_id, case_namespace),
                    )
                else:
                    cur.execute(
                        """
                        SELECT visit_json
                        FROM v50_dream_visits
                        WHERE owner_user_id = %s
                        ORDER BY created_at, visit_id
                        """,
                        (owner_user_id,),
                    )
                rows = cur.fetchall()
        return [normalize_dream_visit(row["visit_json"]) for row in rows]

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

    def acquire_control_lease(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
        client_instance_id: str,
        now: datetime,
        real_expires_at: datetime,
        takeover: bool,
    ) -> DreamControlLease:
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT lease_json
                    FROM v50_dream_control_leases
                    WHERE viewer_id = %s AND case_namespace = %s
                    FOR UPDATE
                    """,
                    (viewer_id, case_namespace),
                )
                row = cur.fetchone()
                current = DreamControlLease.model_validate(row["lease_json"]) if row else None
                active = bool(
                    current
                    and current.status == "active"
                    and now < current.real_expires_at
                )
                if active and current is not None and current.client_instance_id == client_instance_id:
                    lease = current.model_copy(update={"real_expires_at": real_expires_at})
                else:
                    if active and current is not None and not takeover:
                        raise DreamStoreConflict("dream_control_takeover_required")
                    lease = DreamControlLease(
                        lease_id=f"dream-lease-{uuid4().hex}",
                        viewer_id=viewer_id,
                        case_namespace=case_namespace,
                        client_instance_id=client_instance_id,
                        lease_epoch=(current.lease_epoch + 1) if current else 1,
                        fence_token=(current.fence_token + 1) if current else 1,
                        acquired_at=now,
                        real_expires_at=real_expires_at,
                        status="active",
                    )
                cur.execute(
                    """
                    INSERT INTO v50_dream_control_leases
                        (viewer_id, case_namespace, lease_epoch, fence_token, lease_id,
                         client_instance_id, status, real_expires_at, lease_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (viewer_id, case_namespace) DO UPDATE SET
                        lease_epoch = EXCLUDED.lease_epoch,
                        fence_token = EXCLUDED.fence_token,
                        lease_id = EXCLUDED.lease_id,
                        client_instance_id = EXCLUDED.client_instance_id,
                        status = EXCLUDED.status,
                        real_expires_at = EXCLUDED.real_expires_at,
                        lease_json = EXCLUDED.lease_json,
                        updated_at = now()
                    """,
                    (
                        viewer_id,
                        case_namespace,
                        lease.lease_epoch,
                        lease.fence_token,
                        lease.lease_id,
                        lease.client_instance_id,
                        lease.status,
                        lease.real_expires_at,
                        Jsonb(lease.model_dump(mode="json")),
                    ),
                )
        return lease

    def validate_control_lease(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
        credential: DreamControlCredential,
        now: datetime,
    ) -> DreamControlLease:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT lease_json
                    FROM v50_dream_control_leases
                    WHERE viewer_id = %s AND case_namespace = %s
                    """,
                    (viewer_id, case_namespace),
                )
                row = cur.fetchone()
        return _validate_lease_row(row, credential=credential, now=now)

    def renew_control_lease(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
        credential: DreamControlCredential,
        now: datetime,
        real_expires_at: datetime,
    ) -> DreamControlLease:
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT lease_json
                    FROM v50_dream_control_leases
                    WHERE viewer_id = %s AND case_namespace = %s
                    FOR UPDATE
                    """,
                    (viewer_id, case_namespace),
                )
                current = _validate_lease_row(cur.fetchone(), credential=credential, now=now)
                renewed = current.model_copy(update={"real_expires_at": real_expires_at})
                cur.execute(
                    """
                    UPDATE v50_dream_control_leases
                    SET real_expires_at = %s, lease_json = %s, updated_at = now()
                    WHERE viewer_id = %s AND case_namespace = %s
                    """,
                    (
                        real_expires_at,
                        Jsonb(renewed.model_dump(mode="json")),
                        viewer_id,
                        case_namespace,
                    ),
                )
        return renewed

    def save_recovery_checkpoint(
        self,
        checkpoint: DreamRecoveryCheckpoint,
        *,
        credential: DreamControlCredential,
        now: datetime,
    ) -> DreamRecoveryCheckpoint:
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT lease_json
                    FROM v50_dream_control_leases
                    WHERE viewer_id = %s AND case_namespace = %s
                    FOR UPDATE
                    """,
                    (checkpoint.viewer_id, checkpoint.case_namespace),
                )
                lease = _validate_lease_row(cur.fetchone(), credential=credential, now=now)
                if lease.lease_epoch != checkpoint.lease_epoch:
                    raise DreamStoreConflict("dream_control_lease_stale")
                cur.execute(
                    """
                    SELECT record_json
                    FROM v50_dream_navigation_records
                    WHERE viewer_id = %s AND case_namespace = %s AND record_kind = 'recovery'
                    ORDER BY updated_at DESC
                    LIMIT 1
                    FOR UPDATE
                    """,
                    (checkpoint.viewer_id, checkpoint.case_namespace),
                )
                row = cur.fetchone()
                current = DreamRecoveryCheckpoint.model_validate(row["record_json"]) if row else None
                if current is not None and checkpoint.recovery_sequence <= current.recovery_sequence:
                    if checkpoint.recovery_sequence == current.recovery_sequence:
                        return current
                    raise DreamStoreConflict("dream_recovery_sequence_stale")
                cur.execute(
                    """
                    INSERT INTO v50_dream_navigation_records
                        (record_id, record_kind, viewer_id, case_namespace, source_visit_id,
                         status, record_json)
                    VALUES (%s, 'recovery', %s, %s, %s, 'active', %s)
                    ON CONFLICT (record_id) DO UPDATE SET
                        source_visit_id = EXCLUDED.source_visit_id,
                        status = EXCLUDED.status,
                        record_json = EXCLUDED.record_json,
                        updated_at = now()
                    """,
                    (
                        checkpoint.recovery_checkpoint_id,
                        checkpoint.viewer_id,
                        checkpoint.case_namespace,
                        checkpoint.visit_id,
                        Jsonb(checkpoint.model_dump(mode="json")),
                    ),
                )
        return checkpoint

    def latest_recovery_checkpoint(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
    ) -> DreamRecoveryCheckpoint | None:
        row = self._latest_navigation_row(
            viewer_id=viewer_id,
            case_namespace=case_namespace,
            record_kind="recovery",
        )
        return DreamRecoveryCheckpoint.model_validate(row["record_json"]) if row else None

    def latest_departure_anchor(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
    ) -> DreamDepartureAnchor | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT record_json
                    FROM v50_dream_navigation_records
                    WHERE viewer_id = %s
                      AND case_namespace = %s
                      AND record_kind = 'departure'
                      AND status = 'active'
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    (viewer_id, case_namespace),
                )
                row = cur.fetchone()
        return DreamDepartureAnchor.model_validate(row["record_json"]) if row else None

    def commit_departure(
        self,
        *,
        visit: DreamVisit,
        anchor: DreamDepartureAnchor,
        credential: DreamControlCredential,
        expected_row_version: int,
        now: datetime,
    ) -> DreamDepartureResult:
        from psycopg.errors import UniqueViolation
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        try:
            with self._connect() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        """
                        SELECT record_json
                        FROM v50_dream_navigation_records
                        WHERE idempotency_key = %s
                        """,
                        (anchor.idempotency_key,),
                    )
                    existing_row = cur.fetchone()
                    if existing_row:
                        existing = DreamDepartureAnchor.model_validate(existing_row["record_json"])
                        return _departure_result(existing, idempotent_replay=True)
                    cur.execute(
                        """
                        SELECT lease_json
                        FROM v50_dream_control_leases
                        WHERE viewer_id = %s AND case_namespace = %s
                        FOR UPDATE
                        """,
                        (anchor.viewer_id, anchor.case_namespace),
                    )
                    _validate_lease_row(cur.fetchone(), credential=credential, now=now)
                    cur.execute(
                        """
                        SELECT visit_json
                        FROM v50_dream_visits
                        WHERE visit_id = %s AND owner_user_id = %s
                        FOR UPDATE
                        """,
                        (visit.visit_id, anchor.viewer_id),
                    )
                    visit_row = cur.fetchone()
                    if not visit_row:
                        raise DreamStoreConflict("dream_visit_not_found")
                    current = normalize_dream_visit(visit_row["visit_json"])
                    if current.row_version != expected_row_version:
                        raise DreamStoreConflict("dream_visit_version_conflict")
                    cur.execute(
                        """
                        INSERT INTO v50_dream_navigation_records
                            (record_id, record_kind, viewer_id, case_namespace,
                             source_visit_id, status, idempotency_key, record_json)
                        VALUES (%s, 'departure', %s, %s, %s, 'active', %s, %s)
                        """,
                        (
                            anchor.anchor_id,
                            anchor.viewer_id,
                            anchor.case_namespace,
                            anchor.source_visit_id,
                            anchor.idempotency_key,
                            Jsonb(anchor.model_dump(mode="json")),
                        ),
                    )
                    cur.execute(
                        """
                        UPDATE v50_dream_visits
                        SET state = %s, visit_json = %s, updated_at = now()
                        WHERE visit_id = %s AND owner_user_id = %s
                        """,
                        (
                            visit.state.value,
                            Jsonb(visit.model_dump(mode="json")),
                            visit.visit_id,
                            visit.owner_user_id,
                        ),
                    )
                    released = _validate_lease_row(
                        cur.execute(
                            """
                            SELECT lease_json
                            FROM v50_dream_control_leases
                            WHERE viewer_id = %s AND case_namespace = %s
                            """,
                            (anchor.viewer_id, anchor.case_namespace),
                        ).fetchone(),
                        credential=credential,
                        now=now,
                    ).model_copy(update={"status": "released"})
                    cur.execute(
                        """
                        UPDATE v50_dream_control_leases
                        SET status = 'released', lease_json = %s, updated_at = now()
                        WHERE viewer_id = %s AND case_namespace = %s
                        """,
                        (
                            Jsonb(released.model_dump(mode="json")),
                            anchor.viewer_id,
                            anchor.case_namespace,
                        ),
                    )
                    cur.execute(
                        """
                        INSERT INTO v50_dream_projection_outbox
                            (outbox_id, aggregate_ref, event_type, payload_json)
                        VALUES (%s, %s, 'dream_departure_committed', %s)
                        """,
                        (
                            f"dream-outbox-{uuid4().hex}",
                            visit.visit_id,
                            Jsonb({
                                "departure_commit_id": anchor.departure_commit_id,
                                "waking_route": "/experience",
                            }),
                        ),
                    )
        except UniqueViolation:
            existing = self.departure_result(
                viewer_id=anchor.viewer_id,
                case_namespace=anchor.case_namespace,
                visit_id=anchor.source_visit_id,
                commit_sequence=anchor.commit_sequence,
            )
            if existing is not None:
                return existing
            raise
        return _departure_result(anchor, idempotent_replay=False)

    def departure_result(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
        visit_id: str,
        commit_sequence: int,
    ) -> DreamDepartureResult | None:
        from psycopg.rows import dict_row

        key = _departure_idempotency_key(
            viewer_id=viewer_id,
            case_namespace=case_namespace,
            visit_id=visit_id,
            commit_sequence=commit_sequence,
        )
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT record_json
                    FROM v50_dream_navigation_records
                    WHERE idempotency_key = %s
                    """,
                    (key,),
                )
                row = cur.fetchone()
        if not row:
            return None
        return _departure_result(
            DreamDepartureAnchor.model_validate(row["record_json"]),
            idempotent_replay=True,
        )

    def save_guest_departure_anchor(self, anchor: DreamDepartureAnchor) -> DreamDepartureAnchor:
        from psycopg.errors import UniqueViolation
        from psycopg.types.json import Jsonb

        if not anchor.viewer_id.startswith("guest:") or anchor.migration_status != "available":
            raise DreamStoreConflict("dream_guest_anchor_invalid")
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO v50_dream_navigation_records
                            (record_id, record_kind, viewer_id, case_namespace,
                             source_visit_id, status, idempotency_key,
                             migration_capability_hash, record_json)
                        VALUES (%s, 'departure', %s, %s, %s, 'active', %s, %s, %s)
                        """,
                        (
                            anchor.anchor_id,
                            anchor.viewer_id,
                            anchor.case_namespace,
                            anchor.source_visit_id,
                            anchor.idempotency_key,
                            anchor.migration_capability_hash,
                            Jsonb(anchor.model_dump(mode="json")),
                        ),
                    )
        except UniqueViolation as exc:
            raise DreamStoreConflict("dream_guest_anchor_capability_conflict") from exc
        return anchor

    def migrate_guest_anchor(
        self,
        *,
        capability_hash: str,
        target_viewer_id: str,
        target_case_namespace: str,
        now: datetime,
    ) -> DreamGuestAnchorMigrationResult:
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT record_id, record_json
                    FROM v50_dream_navigation_records
                    WHERE migration_capability_hash = %s
                    FOR UPDATE
                    """,
                    (capability_hash,),
                )
                row = cur.fetchone()
                source = DreamDepartureAnchor.model_validate(row["record_json"]) if row else None
                if source is None or source.migration_status != "available":
                    raise DreamStoreConflict("dream_guest_anchor_unavailable")
                cur.execute(
                    """
                    SELECT record_json
                    FROM v50_dream_navigation_records
                    WHERE viewer_id = %s AND case_namespace = %s
                      AND record_kind = 'departure' AND status = 'active'
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    (target_viewer_id, target_case_namespace),
                )
                previous_row = cur.fetchone()
                previous = (
                    DreamDepartureAnchor.model_validate(previous_row["record_json"])
                    if previous_row
                    else None
                )
                anchor = source.model_copy(update={
                    "anchor_id": f"dream-departure-anchor-{uuid4().hex}",
                    "viewer_id": target_viewer_id,
                    "case_namespace": target_case_namespace,
                    "anchor_version": (previous.anchor_version + 1) if previous else 1,
                    "committed_at": now,
                    "departure_commit_id": f"dream-guest-migration-{uuid4().hex}",
                    "idempotency_key": f"guest-anchor-migration|{capability_hash}|{target_viewer_id}",
                    "migration_status": "not_applicable",
                    "migration_capability_hash": "",
                    "migrated_to_anchor_id": "",
                })
                consumed = source.model_copy(update={
                    "migration_status": "consumed",
                    "migrated_to_anchor_id": anchor.anchor_id,
                })
                cur.execute(
                    """
                    UPDATE v50_dream_navigation_records
                    SET status = 'consumed', record_json = %s, updated_at = now()
                    WHERE record_id = %s
                    """,
                    (Jsonb(consumed.model_dump(mode="json")), source.anchor_id),
                )
                cur.execute(
                    """
                    INSERT INTO v50_dream_navigation_records
                        (record_id, record_kind, viewer_id, case_namespace,
                         source_visit_id, status, idempotency_key, record_json)
                    VALUES (%s, 'departure', %s, %s, %s, 'active', %s, %s)
                    """,
                    (
                        anchor.anchor_id,
                        anchor.viewer_id,
                        anchor.case_namespace,
                        anchor.source_visit_id,
                        anchor.idempotency_key,
                        Jsonb(anchor.model_dump(mode="json")),
                    ),
                )
        return DreamGuestAnchorMigrationResult(
            source_anchor_id=source.anchor_id,
            target_anchor=anchor,
            consumed_capability_hash=capability_hash,
        )

    def save_game_content_pack(
        self,
        pack: MaturedFruitContentPack,
    ) -> MaturedFruitContentPack:
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT pack_json FROM v50_dream_game_content_packs WHERE pack_id = %s FOR UPDATE",
                    (pack.pack_id,),
                )
                row = cur.fetchone()
                if row:
                    current = MaturedFruitContentPack.model_validate(row["pack_json"])
                    if current.immutable_hash != pack.immutable_hash:
                        raise DreamStoreConflict("dream_game_content_pack_conflict")
                    return current
                cur.execute(
                    """
                    INSERT INTO v50_dream_game_content_packs
                        (pack_id, evidence_class, content_state, release_eligible,
                         verified_real_gate_contribution, pack_json)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        pack.pack_id,
                        pack.evidence_class,
                        pack.content_state,
                        pack.release_eligible,
                        pack.verified_real_gate_contribution,
                        Jsonb(pack.model_dump(mode="json")),
                    ),
                )
        return pack

    def get_game_content_pack(self, *, pack_id: str) -> MaturedFruitContentPack | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT pack_json FROM v50_dream_game_content_packs WHERE pack_id = %s",
                    (pack_id,),
                )
                row = cur.fetchone()
        return MaturedFruitContentPack.model_validate(row["pack_json"]) if row else None

    def list_game_content_packs(self) -> list[MaturedFruitContentPack]:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT pack_json FROM v50_dream_game_content_packs ORDER BY pack_id")
                rows = cur.fetchall()
        return [MaturedFruitContentPack.model_validate(row["pack_json"]) for row in rows]

    def save_game_round(self, round_definition: BlindRoundDefinition) -> BlindRoundDefinition:
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT round_json FROM v50_dream_game_rounds WHERE round_id = %s FOR UPDATE",
                    (round_definition.round_id,),
                )
                row = cur.fetchone()
                if row:
                    current = BlindRoundDefinition.model_validate(row["round_json"])
                    if current.immutable_hash != round_definition.immutable_hash:
                        raise DreamStoreConflict("dream_game_round_conflict")
                    return current
                cur.execute(
                    """
                    INSERT INTO v50_dream_game_rounds
                        (round_id, pack_id, resident_scene_ref, content_state, round_json)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        round_definition.round_id,
                        round_definition.pack_id,
                        round_definition.resident_scene_ref,
                        round_definition.content_state,
                        Jsonb(round_definition.model_dump(mode="json")),
                    ),
                )
        return round_definition

    def get_game_round(self, *, round_id: str) -> BlindRoundDefinition | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT round_json FROM v50_dream_game_rounds WHERE round_id = %s",
                    (round_id,),
                )
                row = cur.fetchone()
        return BlindRoundDefinition.model_validate(row["round_json"]) if row else None

    def list_game_rounds(self) -> list[BlindRoundDefinition]:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT round_json FROM v50_dream_game_rounds ORDER BY round_id")
                rows = cur.fetchall()
        return [BlindRoundDefinition.model_validate(row["round_json"]) for row in rows]

    def save_game_system_seal(self, seal: SystemJudgmentSeal) -> SystemJudgmentSeal:
        return self._save_immutable_game_object(
            table="v50_dream_game_system_seals",
            id_column="seal_id",
            object_id=seal.seal_id,
            round_id=seal.round_id,
            hash_value=seal.immutable_hash,
            json_column="seal_json",
            payload=seal.model_dump(mode="json"),
            model=SystemJudgmentSeal,
            conflict_code="dream_game_system_seal_conflict",
        )

    def get_game_system_seal(self, *, seal_id: str) -> SystemJudgmentSeal | None:
        return self._get_game_object(
            table="v50_dream_game_system_seals",
            id_column="seal_id",
            object_id=seal_id,
            json_column="seal_json",
            model=SystemJudgmentSeal,
        )

    def save_game_outcome_evidence(self, evidence: OutcomeEvidence) -> OutcomeEvidence:
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT evidence_json FROM v50_dream_game_outcome_evidence WHERE evidence_id = %s FOR UPDATE",
                    (evidence.evidence_id,),
                )
                row = cur.fetchone()
                if row:
                    current = OutcomeEvidence.model_validate(row["evidence_json"])
                    if current.immutable_hash != evidence.immutable_hash:
                        raise DreamStoreConflict("dream_game_outcome_evidence_conflict")
                    return current
                cur.execute(
                    """
                    INSERT INTO v50_dream_game_outcome_evidence
                        (evidence_id, round_id, evidence_class, verification_status,
                         immutable_hash, evidence_json)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        evidence.evidence_id,
                        evidence.round_id,
                        evidence.evidence_class,
                        evidence.verification_status,
                        evidence.immutable_hash,
                        Jsonb(evidence.model_dump(mode="json")),
                    ),
                )
        return evidence

    def get_game_outcome_evidence(self, *, evidence_id: str) -> OutcomeEvidence | None:
        return self._get_game_object(
            table="v50_dream_game_outcome_evidence",
            id_column="evidence_id",
            object_id=evidence_id,
            json_column="evidence_json",
            model=OutcomeEvidence,
        )

    def find_game_outcome_evidence(self, *, round_id: str) -> OutcomeEvidence | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT evidence_json FROM v50_dream_game_outcome_evidence WHERE round_id = %s",
                    (round_id,),
                )
                row = cur.fetchone()
        return OutcomeEvidence.model_validate(row["evidence_json"]) if row else None

    def create_game_attempt(self, attempt: DreamGameAttempt) -> DreamGameAttempt:
        from psycopg.errors import UniqueViolation
        from psycopg.types.json import Jsonb

        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO v50_dream_game_attempts
                            (attempt_id, round_id, viewer_id, visit_id, state,
                             row_version, attempt_json)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            attempt.attempt_id,
                            attempt.round_id,
                            attempt.viewer_id,
                            attempt.visit_id,
                            attempt.state.value,
                            attempt.row_version,
                            Jsonb(attempt.model_dump(mode="json")),
                        ),
                    )
        except UniqueViolation as exc:
            raise DreamStoreConflict("dream_game_attempt_already_exists") from exc
        return attempt

    def get_game_attempt(
        self,
        *,
        attempt_id: str,
        viewer_id: str,
    ) -> DreamGameAttempt | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT attempt_json FROM v50_dream_game_attempts
                    WHERE attempt_id = %s AND viewer_id = %s
                    """,
                    (attempt_id, viewer_id),
                )
                row = cur.fetchone()
        return DreamGameAttempt.model_validate(row["attempt_json"]) if row else None

    def find_game_attempt(
        self,
        *,
        round_id: str,
        viewer_id: str,
        visit_id: str,
    ) -> DreamGameAttempt | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT attempt_json FROM v50_dream_game_attempts
                    WHERE round_id = %s AND viewer_id = %s AND visit_id = %s
                    """,
                    (round_id, viewer_id, visit_id),
                )
                row = cur.fetchone()
        return DreamGameAttempt.model_validate(row["attempt_json"]) if row else None

    def save_game_flower(self, flower: FlowerLifecycle) -> FlowerLifecycle:
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT flower_json FROM v50_dream_game_flowers
                    WHERE round_id = %s FOR UPDATE
                    """,
                    (flower.round_id,),
                )
                row = cur.fetchone()
                if row:
                    current = FlowerLifecycle.model_validate(row["flower_json"])
                    if (
                        current.flower_id != flower.flower_id
                        or current.question_seal_ref != flower.question_seal_ref
                        or current.answer_close_at != flower.answer_close_at
                        or current.outcome_due_at != flower.outcome_due_at
                    ):
                        raise DreamStoreConflict("dream_game_flower_conflict")
                    return current
                cur.execute(
                    """
                    INSERT INTO v50_dream_game_flowers
                        (flower_id, round_id, state, row_version, flower_json)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        flower.flower_id,
                        flower.round_id,
                        flower.state,
                        flower.row_version,
                        Jsonb(flower.model_dump(mode="json")),
                    ),
                )
        return flower

    def get_game_flower(self, *, round_id: str) -> FlowerLifecycle | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT flower_json FROM v50_dream_game_flowers WHERE round_id = %s",
                    (round_id,),
                )
                row = cur.fetchone()
        return FlowerLifecycle.model_validate(row["flower_json"]) if row else None

    def find_game_answer_seal(
        self,
        *,
        round_id: str,
        viewer_id: str,
    ) -> UserJudgmentSeal | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT r.record_json
                    FROM v50_dream_game_answers a
                    JOIN v50_dream_game_records r ON r.record_id = a.seal_id
                    WHERE a.round_id = %s AND a.viewer_id = %s
                    """,
                    (round_id, viewer_id),
                )
                row = cur.fetchone()
        if not row:
            return None
        envelope = DreamGameRecordEnvelope.model_validate(row["record_json"])
        return UserJudgmentSeal.model_validate(envelope.payload)

    def list_game_answer_seals(self, *, round_id: str) -> list[UserJudgmentSeal]:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT r.record_json
                    FROM v50_dream_game_answers a
                    JOIN v50_dream_game_records r ON r.record_id = a.seal_id
                    WHERE a.round_id = %s
                    ORDER BY a.seal_id
                    """,
                    (round_id,),
                )
                rows = cur.fetchall()
        return [
            UserJudgmentSeal.model_validate(
                DreamGameRecordEnvelope.model_validate(row["record_json"]).payload
            )
            for row in rows
        ]

    def commit_game_answer_bundle(
        self,
        attempt: DreamGameAttempt,
        records: list[DreamGameRecordEnvelope],
        *,
        user_seal: UserJudgmentSeal,
        submitted_at: datetime,
        expected_row_version: int,
    ) -> DreamGameAttempt:
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT row_version FROM v50_dream_game_attempts
                    WHERE attempt_id = %s AND viewer_id = %s FOR UPDATE
                    """,
                    (attempt.attempt_id, attempt.viewer_id),
                )
                attempt_row = cur.fetchone()
                if not attempt_row:
                    raise DreamStoreConflict("dream_game_attempt_not_found")
                if int(attempt_row["row_version"]) != expected_row_version:
                    raise DreamStoreConflict("dream_game_attempt_version_conflict")
                cur.execute(
                    """
                    SELECT flower_json FROM v50_dream_game_flowers
                    WHERE round_id = %s FOR UPDATE
                    """,
                    (attempt.round_id,),
                )
                flower_row = cur.fetchone()
                if not flower_row:
                    raise DreamStoreConflict("dream_game_flower_not_found")
                flower = FlowerLifecycle.model_validate(flower_row["flower_json"])
                if (
                    flower.state != "OPEN"
                    or submitted_at >= flower.answer_close_at
                    or submitted_at >= flower.outcome_due_at
                ):
                    raise DreamStoreConflict("dream_game_answer_collection_closed")
                cur.execute(
                    """
                    SELECT seal_id FROM v50_dream_game_answers
                    WHERE round_id = %s AND viewer_id = %s
                    """,
                    (attempt.round_id, attempt.viewer_id),
                )
                if cur.fetchone():
                    raise DreamStoreConflict("dream_game_answer_already_sealed")
                self._insert_game_records(cur, records)
                cur.execute(
                    """
                    INSERT INTO v50_dream_game_answers
                        (round_id, viewer_id, attempt_id, seal_id, immutable_hash, sealed_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        attempt.round_id,
                        attempt.viewer_id,
                        attempt.attempt_id,
                        user_seal.seal_id,
                        user_seal.immutable_hash,
                        user_seal.sealed_at,
                    ),
                )
                cur.execute(
                    """
                    UPDATE v50_dream_game_attempts
                    SET state = %s, row_version = %s, attempt_json = %s, updated_at = now()
                    WHERE attempt_id = %s AND row_version = %s
                    """,
                    (
                        attempt.state.value,
                        attempt.row_version,
                        Jsonb(attempt.model_dump(mode="json")),
                        attempt.attempt_id,
                        expected_row_version,
                    ),
                )
                if cur.rowcount != 1:
                    raise DreamStoreConflict("dream_game_attempt_version_conflict")
                updated_flower = flower.model_copy(update={
                    "answer_count": flower.answer_count + 1,
                    "updated_at": submitted_at,
                    "row_version": flower.row_version + 1,
                })
                cur.execute(
                    """
                    UPDATE v50_dream_game_flowers
                    SET state = %s, row_version = %s, flower_json = %s, updated_at = now()
                    WHERE round_id = %s AND row_version = %s
                    """,
                    (
                        updated_flower.state,
                        updated_flower.row_version,
                        Jsonb(updated_flower.model_dump(mode="json")),
                        updated_flower.round_id,
                        flower.row_version,
                    ),
                )
                if cur.rowcount != 1:
                    raise DreamStoreConflict("dream_game_flower_version_conflict")
        return attempt

    def commit_game_flower_closure(
        self,
        flower: FlowerLifecycle,
        closure: FlowerClosureRecord,
        shared_fruit: SharedFruit | None,
        records: list[DreamGameRecordEnvelope],
        *,
        expected_row_version: int,
    ) -> FlowerLifecycle:
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT flower_json, row_version FROM v50_dream_game_flowers
                    WHERE round_id = %s FOR UPDATE
                    """,
                    (flower.round_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise DreamStoreConflict("dream_game_flower_not_found")
                current = FlowerLifecycle.model_validate(row["flower_json"])
                if current.state != "OPEN":
                    if current.closure_ref == flower.closure_ref:
                        return current
                    raise DreamStoreConflict("dream_game_flower_already_closed")
                if int(row["row_version"]) != expected_row_version:
                    raise DreamStoreConflict("dream_game_flower_version_conflict")
                cur.execute(
                    """
                    SELECT seal_id FROM v50_dream_game_answers
                    WHERE round_id = %s ORDER BY seal_id
                    """,
                    (flower.round_id,),
                )
                actual_refs = [str(item["seal_id"]) for item in cur.fetchall()]
                if actual_refs != closure.answer_seal_refs:
                    raise DreamStoreConflict("dream_game_flower_answer_set_conflict")
                if (shared_fruit is None) != (closure.answer_count == 0):
                    raise DreamStoreConflict("dream_game_shared_fruit_cardinality_invalid")
                self._insert_game_records(cur, records)
                cur.execute(
                    """
                    UPDATE v50_dream_game_flowers
                    SET state = %s, row_version = %s, flower_json = %s, updated_at = now()
                    WHERE round_id = %s AND row_version = %s
                    """,
                    (
                        flower.state,
                        flower.row_version,
                        Jsonb(flower.model_dump(mode="json")),
                        flower.round_id,
                        expected_row_version,
                    ),
                )
                if cur.rowcount != 1:
                    raise DreamStoreConflict("dream_game_flower_version_conflict")
        return flower

    def update_game_attempt(
        self,
        attempt: DreamGameAttempt,
        *,
        expected_row_version: int,
    ) -> DreamGameAttempt:
        return self.commit_game_attempt_bundle(
            attempt,
            [],
            expected_row_version=expected_row_version,
        )

    def commit_game_attempt_bundle(
        self,
        attempt: DreamGameAttempt,
        records: list[DreamGameRecordEnvelope],
        *,
        expected_row_version: int,
    ) -> DreamGameAttempt:
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT attempt_json, row_version FROM v50_dream_game_attempts
                    WHERE attempt_id = %s AND viewer_id = %s FOR UPDATE
                    """,
                    (attempt.attempt_id, attempt.viewer_id),
                )
                row = cur.fetchone()
                if not row:
                    raise DreamStoreConflict("dream_game_attempt_not_found")
                if int(row["row_version"]) != expected_row_version:
                    raise DreamStoreConflict("dream_game_attempt_version_conflict")
                for record in records:
                    cur.execute(
                        "SELECT immutable_hash FROM v50_dream_game_records WHERE record_id = %s",
                        (record.record_id,),
                    )
                    existing = cur.fetchone()
                    if existing and existing["immutable_hash"] != record.immutable_hash:
                        raise DreamStoreConflict("dream_game_record_conflict")
                    if not existing:
                        cur.execute(
                            """
                            INSERT INTO v50_dream_game_records
                                (record_id, record_kind, round_id, viewer_id,
                                 immutable_hash, record_json)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                            (
                                record.record_id,
                                record.record_kind,
                                record.round_id,
                                record.viewer_id or None,
                                record.immutable_hash,
                                Jsonb(record.model_dump(mode="json")),
                            ),
                        )
                cur.execute(
                    """
                    UPDATE v50_dream_game_attempts
                    SET state = %s, row_version = %s, attempt_json = %s, updated_at = now()
                    WHERE attempt_id = %s AND row_version = %s
                    """,
                    (
                        attempt.state.value,
                        attempt.row_version,
                        Jsonb(attempt.model_dump(mode="json")),
                        attempt.attempt_id,
                        expected_row_version,
                    ),
                )
                if cur.rowcount != 1:
                    raise DreamStoreConflict("dream_game_attempt_version_conflict")
        return attempt

    def get_game_record(self, *, record_id: str) -> DreamGameRecordEnvelope | None:
        return self._get_game_object(
            table="v50_dream_game_records",
            id_column="record_id",
            object_id=record_id,
            json_column="record_json",
            model=DreamGameRecordEnvelope,
        )

    def find_game_record(
        self,
        *,
        round_id: str,
        viewer_id: str,
        record_kind: str,
    ) -> DreamGameRecordEnvelope | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT record_json FROM v50_dream_game_records
                    WHERE round_id = %s AND viewer_id = %s AND record_kind = %s
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (round_id, viewer_id, record_kind),
                )
                row = cur.fetchone()
        return DreamGameRecordEnvelope.model_validate(row["record_json"]) if row else None

    def revoke_game_content_pack(
        self,
        *,
        pack_id: str,
        revoked_at: datetime,
    ) -> MaturedFruitContentPack:
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT pack_json FROM v50_dream_game_content_packs WHERE pack_id = %s FOR UPDATE",
                    (pack_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise DreamStoreConflict("dream_game_content_pack_not_found")
                pack = MaturedFruitContentPack.model_validate(row["pack_json"])
                revoked = pack.model_copy(update={
                    "content_state": "REVOKED",
                    "release_eligible": False,
                    "verified_real_gate_contribution": 0,
                    "revoked_at": revoked_at,
                })
                cur.execute(
                    """
                    UPDATE v50_dream_game_content_packs
                    SET content_state = 'REVOKED', release_eligible = false,
                        verified_real_gate_contribution = 0, pack_json = %s,
                        updated_at = now()
                    WHERE pack_id = %s
                    """,
                    (Jsonb(revoked.model_dump(mode="json")), pack_id),
                )
                cur.execute(
                    """
                    UPDATE v50_dream_game_rounds
                    SET content_state = 'REVOKED',
                        round_json = jsonb_set(
                            jsonb_set(round_json, '{content_state}', '"REVOKED"'),
                            '{release_eligible}', 'false'
                        ),
                        updated_at = now()
                    WHERE pack_id = %s
                    """,
                    (pack_id,),
                )
        return revoked

    def verified_real_game_content_count(self) -> int:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COALESCE(SUM(verified_real_gate_contribution), 0)
                    FROM v50_dream_game_content_packs
                    WHERE evidence_class = 'VERIFIED_REAL'
                      AND content_state = 'PUBLISHABLE'
                      AND release_eligible = true
                    """
                )
                row = cur.fetchone()
        return int(row[0]) if row else 0

    @staticmethod
    def _insert_game_records(cur, records: list[DreamGameRecordEnvelope]) -> None:
        from psycopg.types.json import Jsonb

        for record in records:
            cur.execute(
                "SELECT immutable_hash FROM v50_dream_game_records WHERE record_id = %s",
                (record.record_id,),
            )
            existing = cur.fetchone()
            if existing and existing["immutable_hash"] != record.immutable_hash:
                raise DreamStoreConflict("dream_game_record_conflict")
            if existing:
                continue
            cur.execute(
                """
                INSERT INTO v50_dream_game_records
                    (record_id, record_kind, round_id, viewer_id,
                     immutable_hash, record_json)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    record.record_id,
                    record.record_kind,
                    record.round_id,
                    record.viewer_id or None,
                    record.immutable_hash,
                    Jsonb(record.model_dump(mode="json")),
                ),
            )

    def _save_immutable_game_object(
        self,
        *,
        table: str,
        id_column: str,
        object_id: str,
        round_id: str,
        hash_value: str,
        json_column: str,
        payload: dict,
        model,
        conflict_code: str,
    ):
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb

        allowed = {"v50_dream_game_system_seals"}
        if table not in allowed:
            raise DreamStoreConflict("dream_game_store_table_not_allowed")
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"SELECT {json_column} FROM {table} WHERE {id_column} = %s FOR UPDATE",
                    (object_id,),
                )
                row = cur.fetchone()
                if row:
                    current = model.model_validate(row[json_column])
                    if current.immutable_hash != hash_value:
                        raise DreamStoreConflict(conflict_code)
                    return current
                cur.execute(
                    f"INSERT INTO {table} ({id_column}, round_id, immutable_hash, {json_column}) VALUES (%s, %s, %s, %s)",
                    (object_id, round_id, hash_value, Jsonb(payload)),
                )
        return model.model_validate(payload)

    def _get_game_object(
        self,
        *,
        table: str,
        id_column: str,
        object_id: str,
        json_column: str,
        model,
    ):
        from psycopg.rows import dict_row

        allowed = {
            "v50_dream_game_system_seals",
            "v50_dream_game_outcome_evidence",
            "v50_dream_game_records",
        }
        if table not in allowed:
            raise DreamStoreConflict("dream_game_store_table_not_allowed")
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"SELECT {json_column} FROM {table} WHERE {id_column} = %s",
                    (object_id,),
                )
                row = cur.fetchone()
        return model.model_validate(row[json_column]) if row else None

    def _latest_navigation_row(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
        record_kind: str,
    ):
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT record_json
                    FROM v50_dream_navigation_records
                    WHERE viewer_id = %s AND case_namespace = %s AND record_kind = %s
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    (viewer_id, case_namespace, record_kind),
                )
                return cur.fetchone()


def _validate_lease_row(
    row,
    *,
    credential: DreamControlCredential,
    now: datetime,
) -> DreamControlLease:
    if not row:
        raise DreamStoreConflict("dream_control_lease_required")
    current = DreamControlLease.model_validate(row["lease_json"])
    if credential.fence_token < current.fence_token or credential.lease_epoch < current.lease_epoch:
        raise DreamStoreConflict("dream_control_lease_superseded")
    if (
        credential.lease_id != current.lease_id
        or credential.client_instance_id != current.client_instance_id
        or credential.lease_epoch != current.lease_epoch
        or credential.fence_token != current.fence_token
        or current.status != "active"
    ):
        raise DreamStoreConflict("dream_control_lease_stale")
    if now >= current.real_expires_at:
        raise DreamStoreConflict("dream_control_lease_expired")
    return current


def _departure_result(
    anchor: DreamDepartureAnchor,
    *,
    idempotent_replay: bool,
) -> DreamDepartureResult:
    return DreamDepartureResult(
        departure_commit_id=anchor.departure_commit_id,
        visit_id=anchor.source_visit_id,
        case_namespace=anchor.case_namespace,
        commit_sequence=anchor.commit_sequence,
        trigger=anchor.departure_trigger,
        anchor=anchor,
        idempotent_replay=idempotent_replay,
    )


def _departure_idempotency_key(
    *,
    viewer_id: str,
    case_namespace: str,
    visit_id: str,
    commit_sequence: int,
) -> str:
    return f"{viewer_id}|{case_namespace}|{visit_id}|{commit_sequence}"


__all__ = ["PostgresDreamStore"]
