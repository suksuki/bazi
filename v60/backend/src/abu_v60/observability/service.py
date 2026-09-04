from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from abu_v60.architecture import runtime_architecture
from abu_v60.media import MediaCatalogError, RuntimeMediaError, runtime_media_manifest
from abu_v60.mingli.relation_effect_history import (
    MingliRelationEffectHistoricalPacketResolver,
)
from abu_v60.mingli.relation_effect_material import (
    RelationEffectEvidenceMaterialStore,
)
from abu_v60.mingli.relation_effect_material_contracts import (
    RelationEffectEvidenceMaterialRecord,
    RelationEffectEvidenceMaterialRequest,
)
from abu_v60.mingli.relation_effect_request import RelationEffectEvidenceRequestStore
from abu_v60.mingli.relation_effect_request_contracts import (
    RelationEffectEvidencePreparationRequest,
    RelationEffectEvidenceRequestReceipt,
)


class RuntimeIntegrityService:
    """Read-only operational proof for the reduced V60 runtime."""

    @staticmethod
    def _count_invalid_relation_effect_evidence_requests(
        connection: Connection,
        *,
        resolver: MingliRelationEffectHistoricalPacketResolver,
    ) -> int:
        invalid_count = 0
        rows = (
            connection.execute(
                text(
                    """
                    SELECT request.*, account.account_ref
                               AS persisted_account_ref,
                           owner_case.owner_account_ref,
                           owner_case.subject_kind
                               AS owner_case_subject_kind,
                           reading.case_ref AS reading_case_ref,
                           reading.reading_hash AS persisted_reading_hash
                    FROM mingli.relation_effect_evidence_request_receipts
                         AS request
                    LEFT JOIN identity.accounts AS account
                      ON account.account_ref = request.requester_account_ref
                    LEFT JOIN mingli.cases AS owner_case
                      ON owner_case.case_ref = request.case_ref
                    LEFT JOIN mingli.readings AS reading
                      ON reading.reading_ref = request.reading_ref
                    """
                )
            )
            .mappings()
            .all()
        )
        for row in rows:
            try:
                receipt = RelationEffectEvidenceRequestReceipt.model_validate(
                    row["receipt_json"]
                )
                expected_columns = {
                    "receipt_ref": receipt.receipt_ref,
                    "receipt_version": receipt.receipt_version,
                    "requester_account_ref": receipt.requester_account_ref,
                    "case_ref": receipt.case_ref,
                    "reading_ref": receipt.reading_ref,
                    "packet_ref": receipt.packet_ref,
                    "packet_hash": receipt.packet_hash,
                    "idempotency_key": receipt.idempotency_key,
                    "receipt_hash": receipt.receipt_hash,
                }
                packet = resolver.resolve_in_connection(
                    connection,
                    reading_ref=receipt.reading_ref,
                )
                expected_receipt = RelationEffectEvidenceRequestStore.derive_expected_receipt(
                    account_ref=receipt.requester_account_ref,
                    request=RelationEffectEvidencePreparationRequest(
                        request_version=receipt.request_version,
                        expected_packet_ref=receipt.packet_ref,
                        expected_packet_hash=receipt.packet_hash,
                        idempotency_key=receipt.idempotency_key,
                    ),
                    packet=packet,
                )
                if (
                    any(row[key] != value for key, value in expected_columns.items())
                    or row["receipt_json"] != receipt.model_dump(mode="json")
                    or row["persisted_account_ref"] != receipt.requester_account_ref
                    or row["owner_account_ref"] != receipt.requester_account_ref
                    or row["owner_case_subject_kind"] != "HUMAN_OWNER"
                    or row["reading_case_ref"] != receipt.case_ref
                    or row["persisted_reading_hash"] != receipt.reading_hash
                    or receipt != expected_receipt
                ):
                    invalid_count += 1
            except (TypeError, ValueError):
                invalid_count += 1
        return invalid_count

    @staticmethod
    def _count_invalid_relation_effect_evidence_materials(
        connection: Connection,
        *,
        resolver: MingliRelationEffectHistoricalPacketResolver,
    ) -> int:
        invalid_count = 0
        rows = (
            connection.execute(
                text(
                    """
                    SELECT material.*,
                           account.account_ref AS persisted_account_ref,
                           owner_case.owner_account_ref,
                           owner_case.subject_kind
                               AS owner_case_subject_kind,
                           reading.case_ref AS reading_case_ref,
                           reading.reading_hash AS persisted_reading_hash,
                           request.receipt_json,
                           request.requester_account_ref AS receipt_account_ref,
                           request.receipt_hash AS persisted_receipt_hash,
                           request.packet_ref AS receipt_packet_ref,
                           request.packet_hash AS receipt_packet_hash
                    FROM mingli.relation_effect_evidence_material_records
                         AS material
                    LEFT JOIN identity.accounts AS account
                      ON account.account_ref = material.requester_account_ref
                    LEFT JOIN mingli.cases AS owner_case
                      ON owner_case.case_ref = material.case_ref
                    LEFT JOIN mingli.readings AS reading
                      ON reading.reading_ref = material.reading_ref
                    LEFT JOIN mingli.relation_effect_evidence_request_receipts
                         AS request
                      ON request.receipt_ref = material.request_receipt_ref
                    """
                )
            )
            .mappings()
            .all()
        )
        for row in rows:
            try:
                record = RelationEffectEvidenceMaterialRecord.model_validate(
                    row["material_json"]
                )
                receipt = RelationEffectEvidenceRequestReceipt.model_validate(
                    row["receipt_json"]
                )
                packet = resolver.resolve_in_connection(
                    connection,
                    reading_ref=record.reading_ref,
                )
                expected_receipt = RelationEffectEvidenceRequestStore.derive_expected_receipt(
                    account_ref=receipt.requester_account_ref,
                    request=RelationEffectEvidencePreparationRequest(
                        request_version=receipt.request_version,
                        expected_packet_ref=receipt.packet_ref,
                        expected_packet_hash=receipt.packet_hash,
                        idempotency_key=receipt.idempotency_key,
                    ),
                    packet=packet,
                )
                expected_record = RelationEffectEvidenceMaterialStore.derive_expected_record(
                    account_ref=record.requester_account_ref,
                    request=RelationEffectEvidenceMaterialRequest(
                        material_request_version=record.material_request_version,
                        expected_receipt_ref=record.request_receipt_ref,
                        expected_receipt_hash=record.request_receipt_hash,
                        expected_packet_ref=record.packet_ref,
                        expected_packet_hash=record.packet_hash,
                        expected_request_item_ref=record.request_item_ref,
                        expected_demand_packet_ref=record.demand_packet_ref,
                        expected_demand_packet_hash=record.demand_packet_hash,
                        expected_slot_ref=record.slot_ref,
                        candidate_kind=record.candidate_kind,
                        target_artifact_kind=record.target_artifact_kind,
                        bibliography=record.bibliography,
                        idempotency_key=record.idempotency_key,
                    ),
                    receipt=receipt,
                    packet=packet,
                )
                expected_columns = {
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
                    "material_hash": record.material_hash,
                }
                if (
                    any(row[key] != value for key, value in expected_columns.items())
                    or row["material_json"] != record.model_dump(mode="json")
                    or row["persisted_account_ref"] != record.requester_account_ref
                    or row["owner_account_ref"] != record.requester_account_ref
                    or row["owner_case_subject_kind"] != "HUMAN_OWNER"
                    or row["reading_case_ref"] != record.case_ref
                    or row["persisted_reading_hash"] != record.reading_hash
                    or row["receipt_account_ref"] != record.requester_account_ref
                    or row["persisted_receipt_hash"] != record.request_receipt_hash
                    or row["receipt_packet_ref"] != record.packet_ref
                    or row["receipt_packet_hash"] != record.packet_hash
                    or receipt != expected_receipt
                    or record != expected_record
                ):
                    invalid_count += 1
            except (TypeError, ValueError):
                invalid_count += 1
        return invalid_count

    def inspect(self, engine: Engine) -> dict[str, Any]:
        architecture = runtime_architecture()
        architecture.validate_boundaries()
        resolver = MingliRelationEffectHistoricalPacketResolver(engine)

        with engine.connect() as connection:
            migration_head = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            counts = (
                connection.execute(
                    text(
                        """
                        SELECT
                            (SELECT count(*) FROM identity.accounts) AS accounts,
                            (SELECT count(*) FROM identity.profiles) AS profiles,
                            (SELECT count(*) FROM mingli.cases) AS cases,
                            (SELECT count(*) FROM mingli.readings) AS readings,
                            (SELECT count(*) FROM mingli.agent_readings)
                                AS agent_readings,
                            (SELECT count(*) FROM mingli.focused_readings)
                                AS focused_readings,
                            (SELECT count(*) FROM mingli.focused_pass_records)
                                AS focused_pass_records,
                            (SELECT count(*) FROM cognition.decision_records)
                                AS decisions,
                            (SELECT count(*) FROM media.mingli_narration_assets)
                                AS narration_assets,
                            (SELECT count(*)
                             FROM mingli.relation_effect_evidence_request_receipts)
                                AS relation_effect_evidence_requests,
                            (SELECT count(*)
                             FROM mingli.relation_effect_evidence_material_records)
                                AS relation_effect_evidence_materials
                        """
                    )
                )
                .mappings()
                .one()
            )
            integrity = {
                "invalid_relation_effect_evidence_request_receipts": (
                    self._count_invalid_relation_effect_evidence_requests(
                        connection,
                        resolver=resolver,
                    )
                ),
                "invalid_relation_effect_evidence_material_records": (
                    self._count_invalid_relation_effect_evidence_materials(
                        connection,
                        resolver=resolver,
                    )
                ),
            }

        try:
            media_runtime: dict[str, object] = {
                "status": "READY",
                **runtime_media_manifest(),
            }
        except (FileNotFoundError, MediaCatalogError, RuntimeMediaError) as exc:
            media_runtime = {"status": "INVALID", "reason": str(exc)}

        ready = all(value == 0 for value in integrity.values()) and (
            media_runtime["status"] == "READY"
        )
        return {
            "status": "READY" if ready else "DEGRADED",
            "migration_head": migration_head,
            "architecture_version": architecture.architecture_version,
            "counts": {key: int(value) for key, value in counts.items()},
            "integrity": integrity,
            "media_runtime": media_runtime,
            "canonical_write_owners": {
                schema: module.module_id
                for module in architecture.modules
                for schema in module.owns_schemas
            },
            "product_units": list(architecture.product_units),
        }
