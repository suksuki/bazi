from __future__ import annotations

from typing import Any

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from abu_v60.identity import lock_account_transaction
from abu_v60.mingli.relation_effect_evidence_contracts import (
    MingliRelationEffectEvidencePacketEnvelope,
)
from abu_v60.mingli.relation_effect_material_contracts import (
    RelationEffectEvidenceMaterialRecord,
    RelationEffectEvidenceMaterialRequest,
)
from abu_v60.mingli.relation_effect_request import (
    RelationEffectEvidenceRequestStore,
)
from abu_v60.mingli.relation_effect_request_contracts import (
    RelationEffectEvidencePreparationRequest,
    RelationEffectEvidenceRequestReceipt,
)
from abu_v60.provenance import canonical_json


class RelationEffectEvidenceMaterialError(ValueError):
    pass


class RelationEffectEvidenceMaterialConflictError(RelationEffectEvidenceMaterialError):
    pass


class RelationEffectEvidenceMaterialStore:
    """Append-only, account-private candidate bibliography material."""

    def __init__(
        self,
        engine: Engine,
        *,
        evidence_requests: RelationEffectEvidenceRequestStore | None = None,
    ) -> None:
        self._engine = engine
        self._evidence_requests = evidence_requests or RelationEffectEvidenceRequestStore(engine)

    def register_in_connection(
        self,
        connection: Connection,
        *,
        account_ref: str,
        request: RelationEffectEvidenceMaterialRequest,
        receipt: RelationEffectEvidenceRequestReceipt,
        packet: MingliRelationEffectEvidencePacketEnvelope,
    ) -> RelationEffectEvidenceMaterialRecord:
        request = RelationEffectEvidenceMaterialRequest.model_validate(
            request.model_dump(mode="python")
        )
        receipt = RelationEffectEvidenceRequestReceipt.model_validate(
            receipt.model_dump(mode="python")
        )
        packet = MingliRelationEffectEvidencePacketEnvelope.model_validate(
            packet.model_dump(mode="python")
        )
        expected = self.derive_expected_record(
            account_ref=account_ref,
            request=request,
            receipt=receipt,
            packet=packet,
        )
        lock_account_transaction(connection, account_ref=account_ref)
        if not self._case_is_active_owned(
            connection,
            account_ref=account_ref,
            case_ref=receipt.case_ref,
        ):
            raise RelationEffectEvidenceMaterialConflictError(
                "relation_effect_evidence_material_active_case_conflict"
            )
        persisted_receipt = self._evidence_requests.for_packet_in_connection(
            connection,
            account_ref=account_ref,
            packet=packet,
        )
        if persisted_receipt != receipt:
            raise RelationEffectEvidenceMaterialConflictError(
                "relation_effect_evidence_material_receipt_conflict"
            )
        replay = self._load_by_idempotency(
            connection,
            account_ref=account_ref,
            idempotency_key=request.idempotency_key,
        )
        if replay is not None:
            if replay != expected:
                raise RelationEffectEvidenceMaterialConflictError(
                    "relation_effect_evidence_material_idempotency_conflict"
                )
            return replay
        connection.execute(
            text(
                """
                INSERT INTO mingli.relation_effect_evidence_material_records
                    (material_ref, material_version,
                     requester_account_ref, case_ref, reading_ref,
                     request_receipt_ref, request_receipt_hash,
                     packet_ref, packet_hash, request_item_ref,
                     demand_packet_ref, demand_packet_hash, slot_ref,
                     dimension_id, candidate_kind, target_artifact_kind,
                     bibliography_hash, idempotency_key,
                     material_json, material_hash)
                VALUES
                    (:material_ref, :material_version,
                     :requester_account_ref, :case_ref, :reading_ref,
                     :request_receipt_ref, :request_receipt_hash,
                     :packet_ref, :packet_hash, :request_item_ref,
                     :demand_packet_ref, :demand_packet_hash, :slot_ref,
                     :dimension_id, :candidate_kind,
                     :target_artifact_kind, :bibliography_hash,
                     :idempotency_key, CAST(:material_json AS jsonb),
                     :material_hash)
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "material_ref": expected.material_ref,
                "material_version": expected.material_version,
                "requester_account_ref": account_ref,
                "case_ref": expected.case_ref,
                "reading_ref": expected.reading_ref,
                "request_receipt_ref": expected.request_receipt_ref,
                "request_receipt_hash": expected.request_receipt_hash,
                "packet_ref": expected.packet_ref,
                "packet_hash": expected.packet_hash,
                "request_item_ref": expected.request_item_ref,
                "demand_packet_ref": expected.demand_packet_ref,
                "demand_packet_hash": expected.demand_packet_hash,
                "slot_ref": expected.slot_ref,
                "dimension_id": expected.dimension_id,
                "candidate_kind": expected.candidate_kind,
                "target_artifact_kind": (expected.target_artifact_kind),
                "bibliography_hash": expected.bibliography_hash,
                "idempotency_key": expected.idempotency_key,
                "material_json": canonical_json(expected.model_dump(mode="json")),
                "material_hash": expected.material_hash,
            },
        )
        persisted = self._load_by_idempotency(
            connection,
            account_ref=account_ref,
            idempotency_key=request.idempotency_key,
        )
        if persisted is None:
            duplicate = self._load_by_bibliography(
                connection,
                account_ref=account_ref,
                request_receipt_ref=receipt.receipt_ref,
                request_item_ref=expected.request_item_ref,
                slot_ref=expected.slot_ref,
                bibliography_hash=expected.bibliography_hash,
            )
            if duplicate is not None:
                raise RelationEffectEvidenceMaterialConflictError(
                    "relation_effect_evidence_material_already_recorded"
                )
            raise RelationEffectEvidenceMaterialError(
                "relation_effect_evidence_material_persistence_conflict"
            )
        if persisted != expected:
            raise RelationEffectEvidenceMaterialConflictError(
                "relation_effect_evidence_material_idempotency_conflict"
            )
        return persisted

    def for_receipt(
        self,
        *,
        account_ref: str,
        receipt: RelationEffectEvidenceRequestReceipt,
        packet: MingliRelationEffectEvidencePacketEnvelope,
    ) -> tuple[RelationEffectEvidenceMaterialRecord, ...]:
        receipt = RelationEffectEvidenceRequestReceipt.model_validate(
            receipt.model_dump(mode="python")
        )
        packet = MingliRelationEffectEvidencePacketEnvelope.model_validate(
            packet.model_dump(mode="python")
        )
        with self._engine.connect() as connection:
            return self.for_receipt_in_connection(
                connection,
                account_ref=account_ref,
                receipt=receipt,
                packet=packet,
            )

    def for_receipt_in_connection(
        self,
        connection: Connection,
        *,
        account_ref: str,
        receipt: RelationEffectEvidenceRequestReceipt,
        packet: MingliRelationEffectEvidencePacketEnvelope,
    ) -> tuple[RelationEffectEvidenceMaterialRecord, ...]:
        receipt = RelationEffectEvidenceRequestReceipt.model_validate(
            receipt.model_dump(mode="python")
        )
        packet = MingliRelationEffectEvidencePacketEnvelope.model_validate(
            packet.model_dump(mode="python")
        )
        rows = (
            connection.execute(
                text(
                    """
                    SELECT material_ref, material_version,
                           requester_account_ref, case_ref, reading_ref,
                           request_receipt_ref, request_receipt_hash,
                           packet_ref, packet_hash, request_item_ref,
                           demand_packet_ref, demand_packet_hash, slot_ref,
                           dimension_id, candidate_kind,
                           target_artifact_kind, bibliography_hash,
                           idempotency_key, material_json, material_hash
                    FROM mingli.relation_effect_evidence_material_records
                    WHERE requester_account_ref = :account_ref
                      AND request_receipt_ref = :request_receipt_ref
                    ORDER BY created_at, material_ref
                    """
                ),
                {
                    "account_ref": account_ref,
                    "request_receipt_ref": receipt.receipt_ref,
                },
            )
            .mappings()
            .all()
        )
        records = tuple(self._validate_row(row) for row in rows)
        if any(
            record.request_receipt_hash != receipt.receipt_hash
            or record.packet_ref != receipt.packet_ref
            or record.packet_hash != receipt.packet_hash
            or record.case_ref != receipt.case_ref
            or record.reading_ref != receipt.reading_ref
            or record.reading_hash != receipt.reading_hash
            or record.requester_account_ref != account_ref
            for record in records
        ):
            raise RelationEffectEvidenceMaterialError(
                "relation_effect_evidence_material_projection_lineage_mismatch"
            )
        for record in records:
            expected = self.derive_expected_record(
                account_ref=account_ref,
                request=RelationEffectEvidenceMaterialRequest(
                    material_request_version=(record.material_request_version),
                    expected_receipt_ref=record.request_receipt_ref,
                    expected_receipt_hash=record.request_receipt_hash,
                    expected_packet_ref=record.packet_ref,
                    expected_packet_hash=record.packet_hash,
                    expected_request_item_ref=record.request_item_ref,
                    expected_demand_packet_ref=(record.demand_packet_ref),
                    expected_demand_packet_hash=(record.demand_packet_hash),
                    expected_slot_ref=record.slot_ref,
                    candidate_kind=record.candidate_kind,
                    target_artifact_kind=record.target_artifact_kind,
                    bibliography=record.bibliography,
                    idempotency_key=record.idempotency_key,
                ),
                receipt=receipt,
                packet=packet,
            )
            if record != expected:
                raise RelationEffectEvidenceMaterialError(
                    "relation_effect_evidence_material_projection_not_canonical"
                )
        return records

    @staticmethod
    def derive_expected_record(
        *,
        account_ref: str,
        request: RelationEffectEvidenceMaterialRequest,
        receipt: RelationEffectEvidenceRequestReceipt,
        packet: MingliRelationEffectEvidencePacketEnvelope,
    ) -> RelationEffectEvidenceMaterialRecord:
        if (
            request.expected_receipt_ref,
            request.expected_receipt_hash,
            request.expected_packet_ref,
            request.expected_packet_hash,
        ) != (
            receipt.receipt_ref,
            receipt.receipt_hash,
            packet.packet_ref,
            packet.packet_hash,
        ):
            raise RelationEffectEvidenceMaterialConflictError(
                "relation_effect_evidence_material_lineage_conflict"
            )
        if (
            receipt.requester_account_ref != account_ref
            or receipt.packet_ref != packet.packet_ref
            or receipt.packet_hash != packet.packet_hash
            or receipt.case_ref != packet.case_ref
            or receipt.chart_version_ref != packet.chart_version_ref
            or receipt.reading_ref != packet.reading_ref
            or receipt.reading_hash != packet.reading_hash
        ):
            raise RelationEffectEvidenceMaterialConflictError(
                "relation_effect_evidence_material_receipt_packet_conflict"
            )
        expected_receipt = RelationEffectEvidenceRequestStore.derive_expected_receipt(
            account_ref=account_ref,
            request=RelationEffectEvidencePreparationRequest(
                request_version=receipt.request_version,
                expected_packet_ref=receipt.packet_ref,
                expected_packet_hash=receipt.packet_hash,
                idempotency_key=receipt.idempotency_key,
            ),
            packet=packet,
        )
        if receipt != expected_receipt:
            raise RelationEffectEvidenceMaterialConflictError(
                "relation_effect_evidence_material_receipt_not_canonical"
            )
        item_matches = tuple(
            item
            for item in receipt.request_items
            if (
                item.request_item_ref == request.expected_request_item_ref
                and item.demand_packet_ref == request.expected_demand_packet_ref
                and item.demand_packet_hash == request.expected_demand_packet_hash
            )
        )
        if len(item_matches) != 1:
            raise RelationEffectEvidenceMaterialConflictError(
                "relation_effect_evidence_material_demand_chain_conflict"
            )
        item = item_matches[0]
        slot_matches = tuple(
            slot for slot in item.dimension_slots if slot.slot_ref == request.expected_slot_ref
        )
        if len(slot_matches) != 1:
            raise RelationEffectEvidenceMaterialConflictError(
                "relation_effect_evidence_material_slot_conflict"
            )
        slot = slot_matches[0]
        if (
            slot.dimension_id != "PROFESSIONAL_PROVENANCE"
            or request.candidate_kind != "BIBLIOGRAPHIC_COORDINATE_CANDIDATE"
            or request.target_artifact_kind != "PROFESSIONAL_SOURCE_MANIFEST"
            or request.target_artifact_kind not in slot.requested_artifact_kinds
        ):
            raise RelationEffectEvidenceMaterialConflictError(
                "relation_effect_evidence_material_scope_not_allowed"
            )
        return RelationEffectEvidenceMaterialRecord.issue(
            requester_account_ref=account_ref,
            idempotency_key=request.idempotency_key,
            case_ref=receipt.case_ref,
            chart_version_ref=receipt.chart_version_ref,
            reading_ref=receipt.reading_ref,
            reading_hash=receipt.reading_hash,
            request_receipt_ref=receipt.receipt_ref,
            request_receipt_hash=receipt.receipt_hash,
            packet_ref=receipt.packet_ref,
            packet_hash=receipt.packet_hash,
            request_item_ref=item.request_item_ref,
            demand_packet_ref=item.demand_packet_ref,
            demand_packet_hash=item.demand_packet_hash,
            slot_ref=slot.slot_ref,
            dimension_id=slot.dimension_id,
            candidate_kind=request.candidate_kind,
            target_artifact_kind=request.target_artifact_kind,
            bibliography=request.bibliography,
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
    ) -> RelationEffectEvidenceMaterialRecord | None:
        row = (
            connection.execute(
                text(
                    """
                    SELECT material_ref, material_version,
                           requester_account_ref, case_ref, reading_ref,
                           request_receipt_ref, request_receipt_hash,
                           packet_ref, packet_hash, request_item_ref,
                           demand_packet_ref, demand_packet_hash, slot_ref,
                           dimension_id, candidate_kind,
                           target_artifact_kind, bibliography_hash,
                           idempotency_key, material_json, material_hash
                    FROM mingli.relation_effect_evidence_material_records
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
    def _load_by_bibliography(
        cls,
        connection: Any,
        *,
        account_ref: str,
        request_receipt_ref: str,
        request_item_ref: str,
        slot_ref: str,
        bibliography_hash: str,
    ) -> RelationEffectEvidenceMaterialRecord | None:
        row = (
            connection.execute(
                text(
                    """
                    SELECT material_ref, material_version,
                           requester_account_ref, case_ref, reading_ref,
                           request_receipt_ref, request_receipt_hash,
                           packet_ref, packet_hash, request_item_ref,
                           demand_packet_ref, demand_packet_hash, slot_ref,
                           dimension_id, candidate_kind,
                           target_artifact_kind, bibliography_hash,
                           idempotency_key, material_json, material_hash
                    FROM mingli.relation_effect_evidence_material_records
                    WHERE requester_account_ref = :account_ref
                      AND request_receipt_ref = :request_receipt_ref
                      AND request_item_ref = :request_item_ref
                      AND slot_ref = :slot_ref
                      AND bibliography_hash = :bibliography_hash
                    """
                ),
                {
                    "account_ref": account_ref,
                    "request_receipt_ref": request_receipt_ref,
                    "request_item_ref": request_item_ref,
                    "slot_ref": slot_ref,
                    "bibliography_hash": bibliography_hash,
                },
            )
            .mappings()
            .one_or_none()
        )
        return cls._validate_row(row) if row is not None else None

    @staticmethod
    def _validate_row(
        row: Any,
    ) -> RelationEffectEvidenceMaterialRecord:
        try:
            record = RelationEffectEvidenceMaterialRecord.model_validate(row["material_json"])
        except (ValidationError, ValueError) as exc:
            raise RelationEffectEvidenceMaterialError(
                "relation_effect_evidence_material_record_invalid"
            ) from exc
        expected = {
            "material_ref": record.material_ref,
            "material_version": record.material_version,
            "requester_account_ref": record.requester_account_ref,
            "case_ref": record.case_ref,
            "reading_ref": record.reading_ref,
            "request_receipt_ref": record.request_receipt_ref,
            "request_receipt_hash": record.request_receipt_hash,
            "packet_ref": record.packet_ref,
            "packet_hash": record.packet_hash,
            "request_item_ref": record.request_item_ref,
            "demand_packet_ref": record.demand_packet_ref,
            "demand_packet_hash": record.demand_packet_hash,
            "slot_ref": record.slot_ref,
            "dimension_id": record.dimension_id,
            "candidate_kind": record.candidate_kind,
            "target_artifact_kind": record.target_artifact_kind,
            "bibliography_hash": record.bibliography_hash,
            "idempotency_key": record.idempotency_key,
            "material_json": record.model_dump(mode="json"),
            "material_hash": record.material_hash,
        }
        if dict(row) != expected:
            raise RelationEffectEvidenceMaterialError(
                "relation_effect_evidence_material_column_mismatch"
            )
        return record
