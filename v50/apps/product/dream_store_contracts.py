from __future__ import annotations

from datetime import datetime
from typing import Protocol

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


class DreamStoreConflict(RuntimeError):
    pass


DREAM_VISIT_AUDIT_WINDOW = 128


def normalize_dream_visit(value: DreamVisit | dict[str, object]) -> DreamVisit:
    payload = value.model_dump(mode="json") if isinstance(value, DreamVisit) else dict(value)
    audit_events = payload.get("audit_events")
    if isinstance(audit_events, list) and len(audit_events) > DREAM_VISIT_AUDIT_WINDOW:
        payload["audit_events"] = audit_events[-DREAM_VISIT_AUDIT_WINDOW:]
    return DreamVisit.model_validate(payload)


class DreamStore(Protocol):
    persistent: bool
    storage_name: str

    def create_visit(self, visit: DreamVisit) -> DreamVisit: ...
    def update_visit(self, visit: DreamVisit, *, expected_row_version: int) -> DreamVisit: ...
    def get_visit(self, *, visit_id: str, owner_user_id: str) -> DreamVisit | None: ...
    def find_resumable_visit(self, *, owner_user_id: str) -> DreamVisit | None: ...
    def list_visits(self, *, owner_user_id: str, case_namespace: str = "") -> list[DreamVisit]: ...
    def save_grant(self, grant: DreamSceneGrant) -> DreamSceneGrant: ...
    def get_grant(self, *, public_scene_ref: str) -> DreamSceneGrant | None: ...
    def list_grants(self) -> list[DreamSceneGrant]: ...
    def acquire_control_lease(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
        client_instance_id: str,
        now: datetime,
        real_expires_at: datetime,
        takeover: bool,
    ) -> DreamControlLease: ...
    def validate_control_lease(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
        credential: DreamControlCredential,
        now: datetime,
    ) -> DreamControlLease: ...
    def renew_control_lease(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
        credential: DreamControlCredential,
        now: datetime,
        real_expires_at: datetime,
    ) -> DreamControlLease: ...
    def save_recovery_checkpoint(
        self,
        checkpoint: DreamRecoveryCheckpoint,
        *,
        credential: DreamControlCredential,
        now: datetime,
    ) -> DreamRecoveryCheckpoint: ...
    def latest_recovery_checkpoint(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
    ) -> DreamRecoveryCheckpoint | None: ...
    def latest_departure_anchor(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
    ) -> DreamDepartureAnchor | None: ...
    def commit_departure(
        self,
        *,
        visit: DreamVisit,
        anchor: DreamDepartureAnchor,
        credential: DreamControlCredential,
        expected_row_version: int,
        now: datetime,
    ) -> DreamDepartureResult: ...
    def departure_result(
        self,
        *,
        viewer_id: str,
        case_namespace: str,
        visit_id: str,
        commit_sequence: int,
    ) -> DreamDepartureResult | None: ...
    def save_guest_departure_anchor(self, anchor: DreamDepartureAnchor) -> DreamDepartureAnchor: ...
    def migrate_guest_anchor(
        self,
        *,
        capability_hash: str,
        target_viewer_id: str,
        target_case_namespace: str,
        now: datetime,
    ) -> DreamGuestAnchorMigrationResult: ...
    def save_game_content_pack(
        self,
        pack: MaturedFruitContentPack,
    ) -> MaturedFruitContentPack: ...
    def get_game_content_pack(self, *, pack_id: str) -> MaturedFruitContentPack | None: ...
    def list_game_content_packs(self) -> list[MaturedFruitContentPack]: ...
    def save_game_round(self, round_definition: BlindRoundDefinition) -> BlindRoundDefinition: ...
    def get_game_round(self, *, round_id: str) -> BlindRoundDefinition | None: ...
    def list_game_rounds(self) -> list[BlindRoundDefinition]: ...
    def save_game_system_seal(self, seal: SystemJudgmentSeal) -> SystemJudgmentSeal: ...
    def get_game_system_seal(self, *, seal_id: str) -> SystemJudgmentSeal | None: ...
    def save_game_outcome_evidence(self, evidence: OutcomeEvidence) -> OutcomeEvidence: ...
    def get_game_outcome_evidence(self, *, evidence_id: str) -> OutcomeEvidence | None: ...
    def find_game_outcome_evidence(self, *, round_id: str) -> OutcomeEvidence | None: ...
    def create_game_attempt(self, attempt: DreamGameAttempt) -> DreamGameAttempt: ...
    def get_game_attempt(
        self,
        *,
        attempt_id: str,
        viewer_id: str,
    ) -> DreamGameAttempt | None: ...
    def find_game_attempt(
        self,
        *,
        round_id: str,
        viewer_id: str,
        visit_id: str,
    ) -> DreamGameAttempt | None: ...
    def save_game_flower(self, flower: FlowerLifecycle) -> FlowerLifecycle: ...
    def get_game_flower(self, *, round_id: str) -> FlowerLifecycle | None: ...
    def find_game_answer_seal(
        self,
        *,
        round_id: str,
        viewer_id: str,
    ) -> UserJudgmentSeal | None: ...
    def list_game_answer_seals(self, *, round_id: str) -> list[UserJudgmentSeal]: ...
    def commit_game_answer_bundle(
        self,
        attempt: DreamGameAttempt,
        records: list[DreamGameRecordEnvelope],
        *,
        user_seal: UserJudgmentSeal,
        submitted_at: datetime,
        expected_row_version: int,
    ) -> DreamGameAttempt: ...
    def commit_game_flower_closure(
        self,
        flower: FlowerLifecycle,
        closure: FlowerClosureRecord,
        shared_fruit: SharedFruit | None,
        records: list[DreamGameRecordEnvelope],
        *,
        expected_row_version: int,
    ) -> FlowerLifecycle: ...
    def update_game_attempt(
        self,
        attempt: DreamGameAttempt,
        *,
        expected_row_version: int,
    ) -> DreamGameAttempt: ...
    def commit_game_attempt_bundle(
        self,
        attempt: DreamGameAttempt,
        records: list[DreamGameRecordEnvelope],
        *,
        expected_row_version: int,
    ) -> DreamGameAttempt: ...
    def get_game_record(self, *, record_id: str) -> DreamGameRecordEnvelope | None: ...
    def find_game_record(
        self,
        *,
        round_id: str,
        viewer_id: str,
        record_kind: str,
    ) -> DreamGameRecordEnvelope | None: ...
    def revoke_game_content_pack(
        self,
        *,
        pack_id: str,
        revoked_at: datetime,
    ) -> MaturedFruitContentPack: ...
    def verified_real_game_content_count(self) -> int: ...


__all__ = ["DreamStore", "DreamStoreConflict"]
