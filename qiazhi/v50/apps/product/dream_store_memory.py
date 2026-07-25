from __future__ import annotations

from datetime import datetime
from threading import RLock
from uuid import uuid4

from experience.dream import DreamSceneGrant, DreamVisit, DreamVisitState
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
from product.dream_store_contracts import DreamStoreConflict, normalize_dream_visit


class MemoryDreamStore:
    persistent = False
    storage_name = "memory_only"

    def __init__(self) -> None:
        self._visits: dict[str, DreamVisit] = {}
        self._grants: dict[str, DreamSceneGrant] = {}
        self._leases: dict[tuple[str, str], DreamControlLease] = {}
        self._departures: dict[str, DreamDepartureAnchor] = {}
        self._recoveries: dict[str, DreamRecoveryCheckpoint] = {}
        self._idempotency: dict[str, str] = {}
        self._guest_capabilities: dict[str, str] = {}
        self._outbox: dict[str, dict[str, object]] = {}
        self._game_content_packs: dict[str, MaturedFruitContentPack] = {}
        self._game_rounds: dict[str, BlindRoundDefinition] = {}
        self._game_system_seals: dict[str, SystemJudgmentSeal] = {}
        self._game_outcomes: dict[str, OutcomeEvidence] = {}
        self._game_attempts: dict[str, DreamGameAttempt] = {}
        self._game_records: dict[str, DreamGameRecordEnvelope] = {}
        self._game_flowers: dict[str, FlowerLifecycle] = {}
        self._game_answer_seals: dict[tuple[str, str], str] = {}
        self._lock = RLock()

    def create_visit(self, visit: DreamVisit) -> DreamVisit:
        with self._lock:
            if visit.visit_id in self._visits:
                raise DreamStoreConflict("dream_visit_already_exists")
            visit = normalize_dream_visit(visit)
            self._visits[visit.visit_id] = visit
            return visit

    def update_visit(self, visit: DreamVisit, *, expected_row_version: int) -> DreamVisit:
        with self._lock:
            current = self._visits.get(visit.visit_id)
            if current is None:
                raise DreamStoreConflict("dream_visit_not_found")
            if current.row_version != expected_row_version:
                raise DreamStoreConflict("dream_visit_version_conflict")
            visit = normalize_dream_visit(visit)
            self._visits[visit.visit_id] = visit
            return visit

    def get_visit(self, *, visit_id: str, owner_user_id: str) -> DreamVisit | None:
        with self._lock:
            visit = self._visits.get(visit_id)
            return visit if visit and visit.owner_user_id == owner_user_id else None

    def find_resumable_visit(self, *, owner_user_id: str) -> DreamVisit | None:
        with self._lock:
            values = [
                visit
                for visit in self._visits.values()
                if visit.owner_user_id == owner_user_id
                and visit.state != DreamVisitState.COMPLETED
            ]
            return max(values, key=lambda item: item.updated_at, default=None)

    def list_visits(self, *, owner_user_id: str, case_namespace: str = "") -> list[DreamVisit]:
        with self._lock:
            return sorted(
                [
                    visit
                    for visit in self._visits.values()
                    if visit.owner_user_id == owner_user_id
                    and (not case_namespace or visit.case_namespace == case_namespace)
                ],
                key=lambda item: (item.created_at, item.visit_sequence, item.visit_id),
            )

    def save_grant(self, grant: DreamSceneGrant) -> DreamSceneGrant:
        with self._lock:
            existing = self._grants.get(grant.public_scene_ref)
            if existing and existing.grant_id != grant.grant_id:
                raise DreamStoreConflict("dream_public_scene_ref_conflict")
            self._grants[grant.public_scene_ref] = grant
            return grant

    def get_grant(self, *, public_scene_ref: str) -> DreamSceneGrant | None:
        with self._lock:
            return self._grants.get(public_scene_ref)

    def list_grants(self) -> list[DreamSceneGrant]:
        with self._lock:
            return list(self._grants.values())

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
        key = (viewer_id, case_namespace)
        with self._lock:
            current = self._leases.get(key)
            active = bool(
                current
                and current.status == "active"
                and now < current.real_expires_at
            )
            if active and current is not None and current.client_instance_id == client_instance_id:
                renewed = current.model_copy(update={"real_expires_at": real_expires_at})
                self._leases[key] = renewed
                return renewed
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
            self._leases[key] = lease
            return lease

    def validate_control_lease(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
        credential: DreamControlCredential,
        now: datetime,
    ) -> DreamControlLease:
        with self._lock:
            return self._validated_lease(
                viewer_id=viewer_id,
                case_namespace=case_namespace,
                credential=credential,
                now=now,
            )

    def renew_control_lease(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
        credential: DreamControlCredential,
        now: datetime,
        real_expires_at: datetime,
    ) -> DreamControlLease:
        key = (viewer_id, case_namespace)
        with self._lock:
            current = self._validated_lease(
                viewer_id=viewer_id,
                case_namespace=case_namespace,
                credential=credential,
                now=now,
            )
            renewed = current.model_copy(update={"real_expires_at": real_expires_at})
            self._leases[key] = renewed
            return renewed

    def save_recovery_checkpoint(
        self,
        checkpoint: DreamRecoveryCheckpoint,
        *,
        credential: DreamControlCredential,
        now: datetime,
    ) -> DreamRecoveryCheckpoint:
        with self._lock:
            lease = self._validated_lease(
                viewer_id=checkpoint.viewer_id,
                case_namespace=checkpoint.case_namespace,
                credential=credential,
                now=now,
            )
            if lease.lease_epoch != checkpoint.lease_epoch:
                raise DreamStoreConflict("dream_control_lease_stale")
            current = self.latest_recovery_checkpoint(
                viewer_id=checkpoint.viewer_id,
                case_namespace=checkpoint.case_namespace,
            )
            if current is not None and checkpoint.recovery_sequence <= current.recovery_sequence:
                if checkpoint.recovery_sequence == current.recovery_sequence:
                    return current
                raise DreamStoreConflict("dream_recovery_sequence_stale")
            self._recoveries[checkpoint.recovery_checkpoint_id] = checkpoint
            return checkpoint

    def latest_recovery_checkpoint(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
    ) -> DreamRecoveryCheckpoint | None:
        with self._lock:
            values = [
                item
                for item in self._recoveries.values()
                if item.viewer_id == viewer_id and item.case_namespace == case_namespace
            ]
            return max(values, key=lambda item: (item.recovery_sequence, item.updated_at), default=None)

    def latest_departure_anchor(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
    ) -> DreamDepartureAnchor | None:
        with self._lock:
            values = [
                item
                for item in self._departures.values()
                if item.viewer_id == viewer_id
                and item.case_namespace == case_namespace
                and item.migration_status != "consumed"
            ]
            return max(values, key=lambda item: (item.anchor_version, item.committed_at), default=None)

    def commit_departure(
        self,
        *,
        visit: DreamVisit,
        anchor: DreamDepartureAnchor,
        credential: DreamControlCredential,
        expected_row_version: int,
        now: datetime,
    ) -> DreamDepartureResult:
        with self._lock:
            existing_id = self._idempotency.get(anchor.idempotency_key)
            if existing_id:
                existing = self._departures[existing_id]
                return self._departure_result(existing, idempotent_replay=True)
            self._validated_lease(
                viewer_id=anchor.viewer_id,
                case_namespace=anchor.case_namespace,
                credential=credential,
                now=now,
            )
            current = self._visits.get(visit.visit_id)
            if current is None or current.owner_user_id != anchor.viewer_id:
                raise DreamStoreConflict("dream_visit_not_found")
            if current.row_version != expected_row_version:
                raise DreamStoreConflict("dream_visit_version_conflict")
            self._departures[anchor.anchor_id] = anchor
            self._idempotency[anchor.idempotency_key] = anchor.anchor_id
            self._visits[visit.visit_id] = visit
            lease_key = (anchor.viewer_id, anchor.case_namespace)
            current_lease = self._leases[lease_key]
            self._leases[lease_key] = current_lease.model_copy(update={"status": "released"})
            outbox_id = f"dream-outbox-{uuid4().hex}"
            self._outbox[outbox_id] = {
                "event_type": "dream_departure_committed",
                "aggregate_ref": visit.visit_id,
                "departure_commit_id": anchor.departure_commit_id,
            }
            return self._departure_result(anchor, idempotent_replay=False)

    def departure_result(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
        visit_id: str,
        commit_sequence: int,
    ) -> DreamDepartureResult | None:
        with self._lock:
            key = _departure_idempotency_key(
                viewer_id=viewer_id,
                case_namespace=case_namespace,
                visit_id=visit_id,
                commit_sequence=commit_sequence,
            )
            anchor_id = self._idempotency.get(key)
            if not anchor_id:
                return None
            return self._departure_result(self._departures[anchor_id], idempotent_replay=True)

    def save_guest_departure_anchor(self, anchor: DreamDepartureAnchor) -> DreamDepartureAnchor:
        with self._lock:
            if not anchor.viewer_id.startswith("guest:") or anchor.migration_status != "available":
                raise DreamStoreConflict("dream_guest_anchor_invalid")
            if anchor.migration_capability_hash in self._guest_capabilities:
                raise DreamStoreConflict("dream_guest_anchor_capability_conflict")
            self._departures[anchor.anchor_id] = anchor
            self._guest_capabilities[anchor.migration_capability_hash] = anchor.anchor_id
            return anchor

    def migrate_guest_anchor(
        self,
        *,
        capability_hash: str,
        target_viewer_id: str,
        target_case_namespace: str,
        now: datetime,
    ) -> DreamGuestAnchorMigrationResult:
        with self._lock:
            source_id = self._guest_capabilities.get(capability_hash)
            source = self._departures.get(source_id or "")
            if source is None or source.migration_status != "available":
                raise DreamStoreConflict("dream_guest_anchor_unavailable")
            previous = self.latest_departure_anchor(
                viewer_id=target_viewer_id,
                case_namespace=target_case_namespace,
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
            self._departures[source.anchor_id] = consumed
            self._departures[anchor.anchor_id] = anchor
            return DreamGuestAnchorMigrationResult(
                source_anchor_id=source.anchor_id,
                target_anchor=anchor,
                consumed_capability_hash=capability_hash,
            )

    def save_game_content_pack(
        self,
        pack: MaturedFruitContentPack,
    ) -> MaturedFruitContentPack:
        with self._lock:
            existing = self._game_content_packs.get(pack.pack_id)
            if existing and existing.immutable_hash != pack.immutable_hash:
                raise DreamStoreConflict("dream_game_content_pack_conflict")
            self._game_content_packs[pack.pack_id] = pack
            return pack

    def get_game_content_pack(self, *, pack_id: str) -> MaturedFruitContentPack | None:
        with self._lock:
            return self._game_content_packs.get(pack_id)

    def list_game_content_packs(self) -> list[MaturedFruitContentPack]:
        with self._lock:
            return sorted(self._game_content_packs.values(), key=lambda item: item.pack_id)

    def save_game_round(self, round_definition: BlindRoundDefinition) -> BlindRoundDefinition:
        with self._lock:
            existing = self._game_rounds.get(round_definition.round_id)
            if existing and existing.immutable_hash != round_definition.immutable_hash:
                raise DreamStoreConflict("dream_game_round_conflict")
            self._game_rounds[round_definition.round_id] = round_definition
            return round_definition

    def get_game_round(self, *, round_id: str) -> BlindRoundDefinition | None:
        with self._lock:
            return self._game_rounds.get(round_id)

    def list_game_rounds(self) -> list[BlindRoundDefinition]:
        with self._lock:
            return sorted(self._game_rounds.values(), key=lambda item: item.round_id)

    def save_game_system_seal(self, seal: SystemJudgmentSeal) -> SystemJudgmentSeal:
        with self._lock:
            existing = self._game_system_seals.get(seal.seal_id)
            if existing and existing.immutable_hash != seal.immutable_hash:
                raise DreamStoreConflict("dream_game_system_seal_conflict")
            self._game_system_seals[seal.seal_id] = seal
            return seal

    def get_game_system_seal(self, *, seal_id: str) -> SystemJudgmentSeal | None:
        with self._lock:
            return self._game_system_seals.get(seal_id)

    def save_game_outcome_evidence(self, evidence: OutcomeEvidence) -> OutcomeEvidence:
        with self._lock:
            existing = self._game_outcomes.get(evidence.evidence_id)
            if existing and existing.immutable_hash != evidence.immutable_hash:
                raise DreamStoreConflict("dream_game_outcome_evidence_conflict")
            self._game_outcomes[evidence.evidence_id] = evidence
            return evidence

    def get_game_outcome_evidence(self, *, evidence_id: str) -> OutcomeEvidence | None:
        with self._lock:
            return self._game_outcomes.get(evidence_id)

    def find_game_outcome_evidence(self, *, round_id: str) -> OutcomeEvidence | None:
        with self._lock:
            return next(
                (item for item in self._game_outcomes.values() if item.round_id == round_id),
                None,
            )

    def create_game_attempt(self, attempt: DreamGameAttempt) -> DreamGameAttempt:
        with self._lock:
            if attempt.attempt_id in self._game_attempts:
                raise DreamStoreConflict("dream_game_attempt_already_exists")
            self._game_attempts[attempt.attempt_id] = attempt
            return attempt

    def get_game_attempt(
        self,
        *,
        attempt_id: str,
        viewer_id: str,
    ) -> DreamGameAttempt | None:
        with self._lock:
            attempt = self._game_attempts.get(attempt_id)
            return attempt if attempt and attempt.viewer_id == viewer_id else None

    def find_game_attempt(
        self,
        *,
        round_id: str,
        viewer_id: str,
        visit_id: str,
    ) -> DreamGameAttempt | None:
        with self._lock:
            return next(
                (
                    item
                    for item in self._game_attempts.values()
                    if item.round_id == round_id
                    and item.viewer_id == viewer_id
                    and item.visit_id == visit_id
                ),
                None,
            )

    def save_game_flower(self, flower: FlowerLifecycle) -> FlowerLifecycle:
        with self._lock:
            existing = self._game_flowers.get(flower.round_id)
            if existing is not None and (
                existing.flower_id != flower.flower_id
                or existing.question_seal_ref != flower.question_seal_ref
                or existing.answer_close_at != flower.answer_close_at
                or existing.outcome_due_at != flower.outcome_due_at
            ):
                raise DreamStoreConflict("dream_game_flower_conflict")
            if existing is not None:
                return existing
            self._game_flowers[flower.round_id] = flower
            return flower

    def get_game_flower(self, *, round_id: str) -> FlowerLifecycle | None:
        with self._lock:
            return self._game_flowers.get(round_id)

    def find_game_answer_seal(
        self,
        *,
        round_id: str,
        viewer_id: str,
    ) -> UserJudgmentSeal | None:
        with self._lock:
            seal_id = self._game_answer_seals.get((round_id, viewer_id))
            envelope = self._game_records.get(seal_id or "")
            return (
                UserJudgmentSeal.model_validate(envelope.payload)
                if envelope is not None
                else None
            )

    def list_game_answer_seals(self, *, round_id: str) -> list[UserJudgmentSeal]:
        with self._lock:
            values = []
            for (candidate_round_id, _viewer_id), seal_id in self._game_answer_seals.items():
                if candidate_round_id != round_id:
                    continue
                envelope = self._game_records.get(seal_id)
                if envelope is not None:
                    values.append(UserJudgmentSeal.model_validate(envelope.payload))
            return sorted(values, key=lambda item: item.seal_id)

    def commit_game_answer_bundle(
        self,
        attempt: DreamGameAttempt,
        records: list[DreamGameRecordEnvelope],
        *,
        user_seal: UserJudgmentSeal,
        submitted_at: datetime,
        expected_row_version: int,
    ) -> DreamGameAttempt:
        with self._lock:
            current = self._game_attempts.get(attempt.attempt_id)
            if current is None:
                raise DreamStoreConflict("dream_game_attempt_not_found")
            if current.row_version != expected_row_version:
                raise DreamStoreConflict("dream_game_attempt_version_conflict")
            flower = self._game_flowers.get(attempt.round_id)
            if flower is None:
                raise DreamStoreConflict("dream_game_flower_not_found")
            if (
                flower.state != "OPEN"
                or submitted_at >= flower.answer_close_at
                or submitted_at >= flower.outcome_due_at
            ):
                raise DreamStoreConflict("dream_game_answer_collection_closed")
            answer_key = (attempt.round_id, attempt.viewer_id)
            if answer_key in self._game_answer_seals:
                raise DreamStoreConflict("dream_game_answer_already_sealed")
            for record in records:
                existing = self._game_records.get(record.record_id)
                if existing and existing.immutable_hash != record.immutable_hash:
                    raise DreamStoreConflict("dream_game_record_conflict")
            self._game_attempts[attempt.attempt_id] = attempt
            for record in records:
                self._game_records[record.record_id] = record
            self._game_answer_seals[answer_key] = user_seal.seal_id
            self._game_flowers[flower.round_id] = flower.model_copy(update={
                "answer_count": flower.answer_count + 1,
                "updated_at": submitted_at,
                "row_version": flower.row_version + 1,
            })
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
        with self._lock:
            current = self._game_flowers.get(flower.round_id)
            if current is None:
                raise DreamStoreConflict("dream_game_flower_not_found")
            if current.row_version != expected_row_version:
                raise DreamStoreConflict("dream_game_flower_version_conflict")
            actual_refs = sorted(
                seal.seal_id for seal in self.list_game_answer_seals(round_id=flower.round_id)
            )
            if actual_refs != closure.answer_seal_refs:
                raise DreamStoreConflict("dream_game_flower_answer_set_conflict")
            if current.state != "OPEN":
                if current.closure_ref == flower.closure_ref:
                    return current
                raise DreamStoreConflict("dream_game_flower_already_closed")
            if (shared_fruit is None) != (closure.answer_count == 0):
                raise DreamStoreConflict("dream_game_shared_fruit_cardinality_invalid")
            for record in records:
                existing = self._game_records.get(record.record_id)
                if existing and existing.immutable_hash != record.immutable_hash:
                    raise DreamStoreConflict("dream_game_record_conflict")
            for record in records:
                self._game_records[record.record_id] = record
            self._game_flowers[flower.round_id] = flower
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
        with self._lock:
            current = self._game_attempts.get(attempt.attempt_id)
            if current is None:
                raise DreamStoreConflict("dream_game_attempt_not_found")
            if current.row_version != expected_row_version:
                raise DreamStoreConflict("dream_game_attempt_version_conflict")
            for record in records:
                existing = self._game_records.get(record.record_id)
                if existing and existing.immutable_hash != record.immutable_hash:
                    raise DreamStoreConflict("dream_game_record_conflict")
            self._game_attempts[attempt.attempt_id] = attempt
            for record in records:
                self._game_records[record.record_id] = record
            return attempt

    def get_game_record(self, *, record_id: str) -> DreamGameRecordEnvelope | None:
        with self._lock:
            return self._game_records.get(record_id)

    def find_game_record(
        self,
        *,
        round_id: str,
        viewer_id: str,
        record_kind: str,
    ) -> DreamGameRecordEnvelope | None:
        with self._lock:
            values = [
                item for item in self._game_records.values()
                if item.round_id == round_id
                and item.viewer_id == viewer_id
                and item.record_kind == record_kind
            ]
            return max(values, key=lambda item: item.created_at, default=None)

    def revoke_game_content_pack(
        self,
        *,
        pack_id: str,
        revoked_at: datetime,
    ) -> MaturedFruitContentPack:
        with self._lock:
            pack = self._game_content_packs.get(pack_id)
            if pack is None:
                raise DreamStoreConflict("dream_game_content_pack_not_found")
            revoked = pack.model_copy(update={
                "content_state": "REVOKED",
                "release_eligible": False,
                "verified_real_gate_contribution": 0,
                "revoked_at": revoked_at,
            })
            self._game_content_packs[pack_id] = revoked
            for round_id, item in list(self._game_rounds.items()):
                if item.pack_id == pack_id:
                    self._game_rounds[round_id] = item.model_copy(update={
                        "content_state": "REVOKED",
                        "release_eligible": False,
                        "verified_real_gate_contribution": 0,
                    })
            return revoked

    def verified_real_game_content_count(self) -> int:
        with self._lock:
            return sum(
                item.verified_real_gate_contribution
                for item in self._game_content_packs.values()
                if item.content_state == "PUBLISHABLE"
                and item.evidence_class == "VERIFIED_REAL"
                and item.release_eligible
                and item.revoked_at is None
            )

    def _validated_lease(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
        credential: DreamControlCredential,
        now: datetime,
    ) -> DreamControlLease:
        current = self._leases.get((viewer_id, case_namespace))
        if current is None:
            raise DreamStoreConflict("dream_control_lease_required")
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

    @staticmethod
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


__all__ = ["MemoryDreamStore"]
