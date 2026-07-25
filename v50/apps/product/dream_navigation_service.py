from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
from typing import Callable
from uuid import uuid4

from experience.dream import DreamAuditEvent, DreamVisit, DreamVisitState, transition_visit
from experience.dream_navigation import (
    DREAM_GEOMETRY_VERSION,
    DREAM_WORLD_SPACE_REF,
    CanonicalAbuProjection,
    DreamAnchorResolution,
    DreamControlCredential,
    DreamControlLease,
    DreamControlLeaseProjection,
    DreamDepartureAnchor,
    DreamDepartureResult,
    DreamGuestAnchorMigrationResult,
    DreamNavigationSample,
    DreamRecoveryCheckpoint,
    DreamRuntimeState,
    DreamWorldPosition,
    DreamWorldProjectionBinding,
    TreeObservationAnchor,
)
from product.dream_store_contracts import DreamStore, DreamStoreConflict


CONTROL_LEASE_TTL = timedelta(seconds=90)
RECOVERY_CHECKPOINT_TTL = timedelta(hours=24)
WORLD_PROJECTION_TTL = timedelta(hours=12)
FORMAL_ENTRANCE = DreamWorldPosition(x=50, y=88)
OWN_TREE_SAFE_POINT = DreamWorldPosition(x=28, y=82)
CANONICAL_ABU_POSITION = DreamWorldPosition(x=47, y=76)


class DreamNavigationError(ValueError):
    pass


class DreamNavigationService:
    """Owns Dream navigation state; it never writes Mingli or relationship facts."""

    def __init__(
        self,
        *,
        store: DreamStore,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.store = store
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def acquire(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
        client_instance_id: str,
        takeover: bool,
    ) -> DreamControlLease:
        now = self.clock()
        try:
            return self.store.acquire_control_lease(
                viewer_id=viewer_id,
                case_namespace=case_namespace,
                client_instance_id=client_instance_id,
                now=now,
                real_expires_at=now + CONTROL_LEASE_TTL,
                takeover=takeover,
            )
        except DreamStoreConflict as exc:
            raise DreamNavigationError(str(exc)) from exc

    def validate(
        self,
        *,
        visit: DreamVisit,
        credential: DreamControlCredential,
    ) -> DreamControlLease:
        if not visit.case_namespace:
            raise DreamNavigationError("dream_case_namespace_missing")
        try:
            return self.store.validate_control_lease(
                viewer_id=visit.owner_user_id,
                case_namespace=visit.case_namespace,
                credential=credential,
                now=self.clock(),
            )
        except DreamStoreConflict as exc:
            raise DreamNavigationError(str(exc)) from exc

    def heartbeat(
        self,
        *,
        visit: DreamVisit,
        credential: DreamControlCredential,
    ) -> DreamControlLease:
        now = self.clock()
        try:
            return self.store.renew_control_lease(
                viewer_id=visit.owner_user_id,
                case_namespace=visit.case_namespace,
                credential=credential,
                now=now,
                real_expires_at=now + CONTROL_LEASE_TTL,
            )
        except DreamStoreConflict as exc:
            raise DreamNavigationError(str(exc)) from exc

    @staticmethod
    def lease_projection(lease: DreamControlLease) -> DreamControlLeaseProjection:
        return DreamControlLeaseProjection(
            lease_id=lease.lease_id,
            client_instance_id=lease.client_instance_id,
            lease_epoch=lease.lease_epoch,
            fence_token=lease.fence_token,
            real_expires_at=lease.real_expires_at,
        )

    @staticmethod
    def canonical_abu() -> CanonicalAbuProjection:
        return CanonicalAbuProjection(
            public_position=CANONICAL_ABU_POSITION,
            public_action="resting",
        )

    def bind_world_projection(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
        authorization_version: str,
        projection_version: str,
    ) -> DreamWorldProjectionBinding:
        now = self.clock()
        return DreamWorldProjectionBinding(
            world_projection_ref=f"dream-world-projection-{uuid4().hex}",
            viewer_id=viewer_id,
            case_namespace=case_namespace,
            authorization_version=authorization_version,
            projection_version=projection_version,
            issued_at=now,
            expires_at=now + WORLD_PROJECTION_TTL,
        )

    def resolve_anchor(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
        prefer_recovery: bool,
    ) -> DreamAnchorResolution:
        now = self.clock()
        departure = self.store.latest_departure_anchor(
            viewer_id=viewer_id,
            case_namespace=case_namespace,
        )
        recovery = self.store.latest_recovery_checkpoint(
            viewer_id=viewer_id,
            case_namespace=case_namespace,
        )
        recovery_valid = bool(
            recovery
            and now < recovery.expires_at
            and (departure is None or recovery.updated_at > departure.committed_at)
        )
        if prefer_recovery and recovery_valid and recovery is not None:
            return self._resolved(
                source="recovery_checkpoint",
                position=recovery.latest_safe_forest_position,
                camera_heading=recovery.camera_heading,
                geometry_version=recovery.geometry_version,
                source_ref=recovery.recovery_checkpoint_id,
            )
        if departure is not None:
            return self._resolved(
                source="departure_anchor",
                position=departure.last_stable_forest_position,
                camera_heading=departure.camera_heading,
                geometry_version=departure.geometry_version,
                source_ref=departure.anchor_id,
            )
        if recovery_valid and recovery is not None:
            return self._resolved(
                source="recovery_checkpoint",
                position=recovery.latest_safe_forest_position,
                camera_heading=recovery.camera_heading,
                geometry_version=recovery.geometry_version,
                source_ref=recovery.recovery_checkpoint_id,
            )
        return DreamAnchorResolution(
            source="formal_grove_entrance",
            position=FORMAL_ENTRANCE,
            camera_heading=0,
            fallback_reason="no_compatible_navigation_anchor",
        )

    def activate_forest(self, visit: DreamVisit) -> DreamVisit:
        now = self.clock()
        return visit.model_copy(update={
            "runtime_state": DreamRuntimeState.FOREST_ACTIVE,
            "updated_at": now,
            "row_version": visit.row_version + 1,
        })

    def set_tree_observation_anchor(
        self,
        *,
        visit: DreamVisit,
        resident_scene_ref: str,
        sample: DreamNavigationSample,
        credential: DreamControlCredential,
    ) -> DreamVisit:
        self.validate(visit=visit, credential=credential)
        position = self._validated_navigation_sample(visit=visit, sample=sample)
        now = self.clock()
        return visit.model_copy(update={
            "tree_observation_anchor": TreeObservationAnchor(
                visit_id=visit.visit_id,
                resident_scene_ref=resident_scene_ref,
                viewer_position=position,
                camera_heading=sample.camera_heading,
                root_mirror_space_ref=f"root-mirror:{resident_scene_ref}",
                created_at=now,
            ),
            "runtime_state": DreamRuntimeState.MIRROR_ACTIVE,
            "updated_at": now,
            "row_version": visit.row_version + 1,
        })

    def clear_tree_observation_anchor(self, visit: DreamVisit) -> DreamVisit:
        now = self.clock()
        return visit.model_copy(update={
            "tree_observation_anchor": None,
            "runtime_state": DreamRuntimeState.FOREST_ACTIVE,
            "updated_at": now,
            "row_version": visit.row_version + 1,
        })

    def checkpoint(
        self,
        *,
        visit: DreamVisit,
        sample: DreamNavigationSample,
        recovery_sequence: int,
        credential: DreamControlCredential,
    ) -> tuple[DreamVisit, DreamRecoveryCheckpoint]:
        lease = self.validate(visit=visit, credential=credential)
        position = self._validated_navigation_sample(visit=visit, sample=sample)
        if self._inside_departure_mist(position):
            raise DreamNavigationError("dream_recovery_position_not_stable")
        if recovery_sequence <= visit.recovery_sequence:
            if recovery_sequence == visit.recovery_sequence and visit.recovery_checkpoint_ref:
                existing = self.store.latest_recovery_checkpoint(
                    viewer_id=visit.owner_user_id,
                    case_namespace=visit.case_namespace,
                )
                if existing is not None:
                    return visit, existing
            raise DreamNavigationError("dream_recovery_sequence_stale")
        now = self.clock()
        checkpoint = DreamRecoveryCheckpoint(
            recovery_checkpoint_id=(
                visit.recovery_checkpoint_ref
                or f"dream-recovery-{hashlib.sha256(f'{visit.owner_user_id}|{visit.case_namespace}'.encode()).hexdigest()[:32]}"
            ),
            viewer_id=visit.owner_user_id,
            case_namespace=visit.case_namespace,
            visit_id=visit.visit_id,
            latest_safe_forest_position=position,
            camera_heading=sample.camera_heading,
            geometry_version=DREAM_GEOMETRY_VERSION,
            lease_epoch=lease.lease_epoch,
            recovery_sequence=recovery_sequence,
            updated_at=now,
            expires_at=now + RECOVERY_CHECKPOINT_TTL,
        )
        try:
            saved = self.store.save_recovery_checkpoint(
                checkpoint,
                credential=credential,
                now=now,
            )
        except DreamStoreConflict as exc:
            raise DreamNavigationError(str(exc)) from exc
        updated = visit.model_copy(update={
            "recovery_checkpoint_ref": saved.recovery_checkpoint_id,
            "recovery_sequence": saved.recovery_sequence,
            "updated_at": now,
            "row_version": visit.row_version + 1,
            "audit_events": [
                *visit.audit_events,
                DreamAuditEvent(event_code="dream_recovery_checkpointed", occurred_at=now),
            ],
        })
        return updated, saved

    def suspend(self, visit: DreamVisit) -> DreamVisit:
        now = self.clock()
        next_visit = visit
        if visit.state == DreamVisitState.MIRROR_OPEN:
            next_visit = transition_visit(visit, DreamVisitState.TREE_OBSERVING, at=now)
        return next_visit.model_copy(update={
            "prepared_onecanvas_view_ref": "",
            "active_onecanvas_view_ref": "",
            "active_verification_state": "none",
            "tree_observation_anchor": None,
            "runtime_state": DreamRuntimeState.VISIT_SUSPENDED,
            "updated_at": now,
            "row_version": max(next_visit.row_version, visit.row_version + 1),
            "audit_events": [
                *next_visit.audit_events,
                DreamAuditEvent(event_code="dream_visit_suspended", occurred_at=now),
            ],
        })

    def recover(self, visit: DreamVisit) -> DreamVisit:
        now = self.clock()
        resolution = self.resolve_anchor(
            viewer_id=visit.owner_user_id,
            case_namespace=visit.case_namespace,
            prefer_recovery=True,
        )
        return visit.model_copy(update={
            "runtime_state": DreamRuntimeState.LOCAL_MIST_REENTRY,
            "anchor_resolution": resolution,
            "prepared_onecanvas_view_ref": "",
            "active_onecanvas_view_ref": "",
            "active_verification_state": "none",
            "tree_observation_anchor": None,
            "updated_at": now,
            "row_version": visit.row_version + 1,
            "audit_events": [
                *visit.audit_events,
                DreamAuditEvent(event_code="dream_visit_recovered", occurred_at=now),
                DreamAuditEvent(event_code="dream_anchor_resolved", occurred_at=now),
            ],
        })

    def departure_intent(self, visit: DreamVisit, *, active: bool) -> DreamVisit:
        now = self.clock()
        return visit.model_copy(update={
            "runtime_state": (
                DreamRuntimeState.DEPARTURE_INTENT
                if active
                else DreamRuntimeState.FOREST_ACTIVE
            ),
            "updated_at": now,
            "row_version": visit.row_version + 1,
            "audit_events": [
                *visit.audit_events,
                DreamAuditEvent(
                    event_code=(
                        "dream_departure_intent_started"
                        if active
                        else "dream_departure_intent_cancelled"
                    ),
                    occurred_at=now,
                ),
            ],
        })

    def commit_departure(
        self,
        *,
        visit: DreamVisit,
        trigger: str,
        sample: DreamNavigationSample,
        boundary_position: DreamWorldPosition | None,
        commit_sequence: int,
        credential: DreamControlCredential,
    ) -> DreamDepartureResult:
        existing = self.store.departure_result(
            viewer_id=visit.owner_user_id,
            case_namespace=visit.case_namespace,
            visit_id=visit.visit_id,
            commit_sequence=commit_sequence,
        )
        if existing is not None:
            return existing
        self.validate(visit=visit, credential=credential)
        if visit.state == DreamVisitState.MIRROR_OPEN or visit.runtime_state == DreamRuntimeState.MIRROR_ACTIVE:
            raise DreamNavigationError("dream_departure_requires_closed_mirror")
        if trigger not in {"SPATIAL_BOUNDARY", "SEMANTIC_EXIT"}:
            raise DreamNavigationError("dream_departure_trigger_invalid")
        position = self._validated_navigation_sample(visit=visit, sample=sample)
        if trigger == "SPATIAL_BOUNDARY" and (
            boundary_position is None
            or not self._crossed_departure_boundary(boundary_position)
        ):
            raise DreamNavigationError("dream_spatial_departure_boundary_not_crossed")
        if commit_sequence <= visit.departure_commit_sequence:
            raise DreamNavigationError("dream_departure_sequence_stale")
        now = self.clock()
        previous = self.store.latest_departure_anchor(
            viewer_id=visit.owner_user_id,
            case_namespace=visit.case_namespace,
        )
        idempotency_key = _departure_idempotency_key(
            viewer_id=visit.owner_user_id,
            case_namespace=visit.case_namespace,
            visit_id=visit.visit_id,
            commit_sequence=commit_sequence,
        )
        anchor = DreamDepartureAnchor(
            anchor_id=f"dream-departure-anchor-{uuid4().hex}",
            viewer_id=visit.owner_user_id,
            case_namespace=visit.case_namespace,
            world_space_ref=DREAM_WORLD_SPACE_REF,
            last_stable_forest_position=position,
            camera_heading=sample.camera_heading,
            geometry_version=DREAM_GEOMETRY_VERSION,
            source_visit_id=visit.visit_id,
            visit_sequence=visit.visit_sequence,
            commit_sequence=commit_sequence,
            anchor_version=(previous.anchor_version + 1) if previous else 1,
            departure_world_time=_canonical_world_tick(now),
            committed_at=now,
            departure_commit_id=f"dream-departure-{uuid4().hex}",
            departure_trigger=trigger,
            idempotency_key=idempotency_key,
        )
        original_version = visit.row_version
        closed = transition_visit(visit, DreamVisitState.COMPLETED, at=now)
        closed = closed.model_copy(update={
            "runtime_state": DreamRuntimeState.DEPARTED,
            "departure_anchor_ref": anchor.anchor_id,
            "departure_commit_sequence": commit_sequence,
            "prepared_onecanvas_view_ref": "",
            "active_onecanvas_view_ref": "",
            "active_verification_state": "none",
            "tree_observation_anchor": None,
            "audit_events": [
                *closed.audit_events,
                DreamAuditEvent(event_code="dream_departure_commit_requested", occurred_at=now),
                DreamAuditEvent(event_code="dream_departure_committed", occurred_at=now),
            ],
        })
        try:
            return self.store.commit_departure(
                visit=closed,
                anchor=anchor,
                credential=credential,
                expected_row_version=original_version,
                now=now,
            )
        except DreamStoreConflict as exc:
            replay = self.store.departure_result(
                viewer_id=visit.owner_user_id,
                case_namespace=visit.case_namespace,
                visit_id=visit.visit_id,
                commit_sequence=commit_sequence,
            )
            if replay is not None:
                return replay
            raise DreamNavigationError(str(exc)) from exc

    def migrate_guest_anchor(
        self,
        *,
        capability: str,
        target_viewer_id: str,
        target_case_namespace: str,
        accepted: bool,
    ) -> DreamGuestAnchorMigrationResult:
        if not accepted:
            raise DreamNavigationError("dream_guest_anchor_consent_required")
        capability_hash = hashlib.sha256(capability.encode()).hexdigest()
        try:
            return self.store.migrate_guest_anchor(
                capability_hash=capability_hash,
                target_viewer_id=target_viewer_id,
                target_case_namespace=target_case_namespace,
                now=self.clock(),
            )
        except DreamStoreConflict as exc:
            raise DreamNavigationError(str(exc)) from exc

    def _validated_navigation_sample(
        self,
        *,
        visit: DreamVisit,
        sample: DreamNavigationSample,
    ) -> DreamWorldPosition:
        binding = visit.world_projection
        now = self.clock()
        if binding is None:
            raise DreamNavigationError("dream_world_projection_required")
        if (
            sample.world_projection_ref != binding.world_projection_ref
            or binding.viewer_id != visit.owner_user_id
            or binding.case_namespace != visit.case_namespace
            or now >= binding.expires_at
        ):
            raise DreamNavigationError("dream_world_projection_invalid")
        if (
            sample.world_space_ref != DREAM_WORLD_SPACE_REF
            or sample.geometry_version != DREAM_GEOMETRY_VERSION
        ):
            raise DreamNavigationError("dream_world_geometry_invalid")
        return DreamWorldPosition(
            x=min(97, max(7, sample.position.x)),
            y=min(91, max(24, sample.position.y)),
        )

    def _resolved(
        self,
        *,
        source: str,
        position: DreamWorldPosition,
        camera_heading: float,
        geometry_version: str,
        source_ref: str,
    ) -> DreamAnchorResolution:
        if geometry_version != DREAM_GEOMETRY_VERSION:
            return DreamAnchorResolution(
                source="own_tree_safe_point",
                position=OWN_TREE_SAFE_POINT,
                camera_heading=0,
                fallback_reason="geometry_version_unmapped",
            )
        if self._inside_departure_mist(position):
            return DreamAnchorResolution(
                source=source,
                position=DreamWorldPosition(x=87.5, y=min(91, max(24, position.y))),
                camera_heading=camera_heading,
                source_ref=source_ref,
                fallback_reason="anchor_mapped_to_nearest_safe_geometry",
            )
        if not self._position_is_safe(position):
            return DreamAnchorResolution(
                source="own_tree_safe_point",
                position=OWN_TREE_SAFE_POINT,
                camera_heading=0,
                fallback_reason="anchor_outside_current_safe_geometry",
            )
        return DreamAnchorResolution(
            source=source,
            position=position,
            camera_heading=camera_heading,
            source_ref=source_ref,
        )

    @staticmethod
    def _position_is_safe(position: DreamWorldPosition) -> bool:
        return (
            7 <= position.x <= 93
            and 24 <= position.y <= 91
            and not DreamNavigationService._inside_departure_mist(position)
        )

    @staticmethod
    def _inside_departure_mist(position: DreamWorldPosition) -> bool:
        return position.x >= 88 and position.y >= 80

    @staticmethod
    def _crossed_departure_boundary(position: DreamWorldPosition) -> bool:
        return position.x >= 95 and position.y >= 86


def _canonical_world_tick(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def _departure_idempotency_key(
    *,
    viewer_id: str,
    case_namespace: str,
    visit_id: str,
    commit_sequence: int,
) -> str:
    return f"{viewer_id}|{case_namespace}|{visit_id}|{commit_sequence}"


__all__ = [
    "CONTROL_LEASE_TTL",
    "DreamNavigationError",
    "DreamNavigationService",
    "RECOVERY_CHECKPOINT_TTL",
    "WORLD_PROJECTION_TTL",
]
