from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from abu_v60.identity import lock_account_transaction
from abu_v60.mingli.relation_effect_evidence_contracts import (
    MingliRelationEffectEvidencePacketEnvelope,
)
from abu_v60.mingli.relation_effect_request_contracts import (
    RelationEffectEvidencePreparationRequest,
    RelationEffectEvidenceRequestedSlot,
    RelationEffectEvidenceRequestItem,
    RelationEffectEvidenceRequestReceipt,
)
from abu_v60.provenance import canonical_json


class RelationEffectEvidenceRequestError(ValueError):
    pass


class RelationEffectEvidenceRequestConflictError(RelationEffectEvidenceRequestError):
    pass


class RelationEffectEvidenceRequestStore:
    """Mingli-owned append-only, account-private preparation receipts."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def request(
        self,
        *,
        account_ref: str,
        request: RelationEffectEvidencePreparationRequest,
        packet: MingliRelationEffectEvidencePacketEnvelope,
    ) -> RelationEffectEvidenceRequestReceipt:
        request = RelationEffectEvidencePreparationRequest.model_validate(
            request.model_dump(mode="python")
        )
        packet = MingliRelationEffectEvidencePacketEnvelope.model_validate(
            packet.model_dump(mode="python")
        )
        self._validate_request_packet(request=request, packet=packet)
        with self._engine.begin() as connection:
            return self.request_in_connection(
                connection,
                account_ref=account_ref,
                request=request,
                packet=packet,
            )

    def request_in_connection(
        self,
        connection: Connection,
        *,
        account_ref: str,
        request: RelationEffectEvidencePreparationRequest,
        packet: MingliRelationEffectEvidencePacketEnvelope,
    ) -> RelationEffectEvidenceRequestReceipt:
        request = RelationEffectEvidencePreparationRequest.model_validate(
            request.model_dump(mode="python")
        )
        packet = MingliRelationEffectEvidencePacketEnvelope.model_validate(
            packet.model_dump(mode="python")
        )
        self._validate_request_packet(request=request, packet=packet)
        expected = self.derive_expected_receipt(
            account_ref=account_ref,
            request=request,
            packet=packet,
        )
        lock_account_transaction(
            connection,
            account_ref=account_ref,
        )
        if not self._case_is_active_owned(
            connection,
            account_ref=account_ref,
            case_ref=packet.case_ref,
        ):
            raise RelationEffectEvidenceRequestConflictError(
                "relation_effect_evidence_request_active_case_conflict"
            )
        replay = self._load_by_idempotency(
            connection,
            account_ref=account_ref,
            idempotency_key=request.idempotency_key,
        )
        if replay is not None:
            if replay != expected:
                raise RelationEffectEvidenceRequestConflictError(
                    "relation_effect_evidence_request_idempotency_conflict"
                )
            return replay
        connection.execute(
            text(
                """
                INSERT INTO mingli.relation_effect_evidence_request_receipts
                    (receipt_ref, receipt_version,
                     requester_account_ref, case_ref, reading_ref,
                     packet_ref, packet_hash, idempotency_key,
                     receipt_json, receipt_hash)
                VALUES
                    (:receipt_ref, :receipt_version,
                     :requester_account_ref, :case_ref, :reading_ref,
                     :packet_ref, :packet_hash, :idempotency_key,
                     CAST(:receipt_json AS jsonb), :receipt_hash)
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "receipt_ref": expected.receipt_ref,
                "receipt_version": expected.receipt_version,
                "requester_account_ref": account_ref,
                "case_ref": expected.case_ref,
                "reading_ref": expected.reading_ref,
                "packet_ref": expected.packet_ref,
                "packet_hash": expected.packet_hash,
                "idempotency_key": expected.idempotency_key,
                "receipt_json": canonical_json(expected.model_dump(mode="json")),
                "receipt_hash": expected.receipt_hash,
            },
        )
        persisted = self._load_by_idempotency(
            connection,
            account_ref=account_ref,
            idempotency_key=request.idempotency_key,
        )
        if persisted is None:
            existing_packet = self._load_by_packet(
                connection,
                account_ref=account_ref,
                packet_ref=packet.packet_ref,
            )
            if existing_packet is not None:
                raise RelationEffectEvidenceRequestConflictError(
                    "relation_effect_evidence_request_already_recorded"
                )
            raise RelationEffectEvidenceRequestError(
                "relation_effect_evidence_request_persistence_conflict"
            )
        if persisted != expected:
            raise RelationEffectEvidenceRequestConflictError(
                "relation_effect_evidence_request_idempotency_conflict"
            )
        return persisted

    def for_packet(
        self,
        *,
        account_ref: str,
        packet: MingliRelationEffectEvidencePacketEnvelope,
    ) -> RelationEffectEvidenceRequestReceipt | None:
        packet = MingliRelationEffectEvidencePacketEnvelope.model_validate(
            packet.model_dump(mode="python")
        )
        if not packet.demand_packets:
            return None
        with self._engine.connect() as connection:
            return self.for_packet_in_connection(
                connection,
                account_ref=account_ref,
                packet=packet,
            )

    def for_packet_in_connection(
        self,
        connection: Connection,
        *,
        account_ref: str,
        packet: MingliRelationEffectEvidencePacketEnvelope,
    ) -> RelationEffectEvidenceRequestReceipt | None:
        packet = MingliRelationEffectEvidencePacketEnvelope.model_validate(
            packet.model_dump(mode="python")
        )
        if not packet.demand_packets:
            return None
        receipt = self._load_by_packet(
            connection,
            account_ref=account_ref,
            packet_ref=packet.packet_ref,
        )
        if receipt is None:
            return None
        expected = self.derive_expected_receipt(
            account_ref=account_ref,
            request=RelationEffectEvidencePreparationRequest(
                request_version=receipt.request_version,
                expected_packet_ref=receipt.packet_ref,
                expected_packet_hash=receipt.packet_hash,
                idempotency_key=receipt.idempotency_key,
            ),
            packet=packet,
        )
        if receipt != expected:
            raise RelationEffectEvidenceRequestError(
                "relation_effect_evidence_request_projection_lineage_mismatch"
            )
        return receipt

    @staticmethod
    def _validate_request_packet(
        *,
        request: RelationEffectEvidencePreparationRequest,
        packet: MingliRelationEffectEvidencePacketEnvelope,
    ) -> None:
        if (
            request.expected_packet_ref,
            request.expected_packet_hash,
        ) != (packet.packet_ref, packet.packet_hash):
            raise RelationEffectEvidenceRequestConflictError(
                "relation_effect_evidence_request_packet_conflict"
            )
        if (
            not packet.demand_packets
            or packet.status != "EVIDENCE_INTAKE_REQUIRED"
            or packet.effect_decision_status != "WITHHELD"
        ):
            raise RelationEffectEvidenceRequestConflictError(
                "relation_effect_evidence_request_not_triggered"
            )
        if (
            packet.professional_evidence_count != 0
            or packet.ready_dimension_slot_count != 0
            or packet.owner_professional_review_invoked
            or packet.knowledge_admission_eligible
            or packet.gate_invoked
            or packet.decision_created
        ):
            raise RelationEffectEvidenceRequestError(
                "relation_effect_evidence_request_packet_boundary_invalid"
            )

    @staticmethod
    def derive_expected_receipt(
        *,
        account_ref: str,
        request: RelationEffectEvidencePreparationRequest,
        packet: MingliRelationEffectEvidencePacketEnvelope,
    ) -> RelationEffectEvidenceRequestReceipt:
        RelationEffectEvidenceRequestStore._validate_request_packet(
            request=request,
            packet=packet,
        )
        items = tuple(
            RelationEffectEvidenceRequestItem.issue(
                demand_packet_ref=demand.demand_packet_ref,
                demand_packet_hash=demand.demand_packet_hash,
                assessment_ref=demand.assessment_ref,
                assessment_hash=demand.assessment_hash,
                demand_ref=demand.demand_ref,
                dimension_slots=tuple(
                    RelationEffectEvidenceRequestedSlot.issue(
                        slot_ref=slot.slot_ref,
                        dimension_id=slot.dimension_id,
                        requirement=slot.requirement,
                        requested_artifact_kinds=(slot.requested_artifact_kinds),
                        next_action=slot.next_action,
                    )
                    for slot in demand.dimension_slots
                ),
            )
            for demand in packet.demand_packets
        )
        return RelationEffectEvidenceRequestReceipt.issue(
            requester_account_ref=account_ref,
            idempotency_key=request.idempotency_key,
            case_ref=packet.case_ref,
            chart_version_ref=packet.chart_version_ref,
            reading_ref=packet.reading_ref,
            reading_hash=packet.reading_hash,
            frontier_ref=packet.frontier_ref,
            frontier_hash=packet.frontier_hash,
            admission_review_ref=packet.admission_review_ref,
            admission_review_hash=packet.admission_review_hash,
            policy_ref=packet.policy_ref,
            policy_hash=packet.policy_hash,
            proposal_ref=packet.proposal_ref,
            proposal_hash=packet.proposal_hash,
            packet_ref=packet.packet_ref,
            packet_hash=packet.packet_hash,
            request_items=items,
        )

    @staticmethod
    def _case_is_active_owned(
        connection: Any,
        *,
        account_ref: str,
        case_ref: str,
    ) -> bool:
        return bool(
            connection.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM mingli.cases
                        WHERE case_ref = :case_ref
                          AND owner_account_ref = :account_ref
                          AND subject_kind = 'HUMAN_OWNER'
                          AND status = 'ACTIVE'
                    )
                    """
                ),
                {
                    "case_ref": case_ref,
                    "account_ref": account_ref,
                },
            ).scalar_one()
        )

    @classmethod
    def _load_by_idempotency(
        cls,
        connection: Any,
        *,
        account_ref: str,
        idempotency_key: str,
    ) -> RelationEffectEvidenceRequestReceipt | None:
        row = (
            connection.execute(
                text(
                    """
                    SELECT receipt_ref, receipt_version,
                           requester_account_ref, case_ref, reading_ref,
                           packet_ref, packet_hash, idempotency_key,
                           receipt_json, receipt_hash
                    FROM mingli.relation_effect_evidence_request_receipts
                    WHERE requester_account_ref = :account_ref
                      AND idempotency_key = :idempotency_key
                    """
                ),
                {
                    "account_ref": account_ref,
                    "idempotency_key": idempotency_key,
                },
            )
            .mappings()
            .one_or_none()
        )
        return cls._validate_row(row) if row is not None else None

    @classmethod
    def _load_by_packet(
        cls,
        connection: Any,
        *,
        account_ref: str,
        packet_ref: str,
    ) -> RelationEffectEvidenceRequestReceipt | None:
        row = (
            connection.execute(
                text(
                    """
                    SELECT receipt_ref, receipt_version,
                           requester_account_ref, case_ref, reading_ref,
                           packet_ref, packet_hash, idempotency_key,
                           receipt_json, receipt_hash
                    FROM mingli.relation_effect_evidence_request_receipts
                    WHERE requester_account_ref = :account_ref
                      AND packet_ref = :packet_ref
                    """
                ),
                {
                    "account_ref": account_ref,
                    "packet_ref": packet_ref,
                },
            )
            .mappings()
            .one_or_none()
        )
        return cls._validate_row(row) if row is not None else None

    @staticmethod
    def _validate_row(
        row: Any,
    ) -> RelationEffectEvidenceRequestReceipt:
        try:
            receipt = RelationEffectEvidenceRequestReceipt.model_validate(row["receipt_json"])
        except (ValidationError, ValueError) as exc:
            raise RelationEffectEvidenceRequestError(
                "relation_effect_evidence_request_receipt_invalid"
            ) from exc
        expected = {
            "receipt_ref": receipt.receipt_ref,
            "receipt_version": receipt.receipt_version,
            "requester_account_ref": receipt.requester_account_ref,
            "case_ref": receipt.case_ref,
            "reading_ref": receipt.reading_ref,
            "packet_ref": receipt.packet_ref,
            "packet_hash": receipt.packet_hash,
            "idempotency_key": receipt.idempotency_key,
            "receipt_json": receipt.model_dump(mode="json"),
            "receipt_hash": receipt.receipt_hash,
        }
        if dict(row) != expected:
            raise RelationEffectEvidenceRequestError(
                "relation_effect_evidence_request_receipt_column_mismatch"
            )
        return receipt
