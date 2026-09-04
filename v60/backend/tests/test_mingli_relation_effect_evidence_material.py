from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Event, Lock, current_thread

import pytest
from abu_v60.db import engine
from abu_v60.experience.home import HomeExperienceService
from abu_v60.mingli import (
    RELATION_EFFECT_EVIDENCE_MATERIAL_REQUEST_VERSION,
    RELATION_EFFECT_EVIDENCE_REQUEST_VERSION,
    MingliRelationEffectEvidencePacketEnvelope,
    RelationEffectEvidenceBibliographyMetadata,
    RelationEffectEvidenceMaterialConflictError,
    RelationEffectEvidenceMaterialRecord,
    RelationEffectEvidenceMaterialRequest,
    RelationEffectEvidenceMaterialStore,
    RelationEffectEvidencePreparationRequest,
    RelationEffectEvidenceRequestReceipt,
    RelationEffectEvidenceRequestStore,
)
from abu_v60.mingli.relation_effect_history import (
    MingliRelationEffectHistoricalPacketResolver,
)
from abu_v60.observability import RuntimeIntegrityService
from abu_v60.provenance import canonical_json, content_hash
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError


def _account_ref() -> str:
    with engine.connect() as connection:
        return str(
            connection.execute(
                text(
                    """
                    SELECT owner_account_ref
                    FROM mingli.cases
                    WHERE subject_kind = 'HUMAN_OWNER'
                      AND status = 'ACTIVE'
                    GROUP BY owner_account_ref
                    HAVING count(*) = 1
                    ORDER BY owner_account_ref
                    LIMIT 1
                    """
                )
            ).scalar_one()
        )


def _context(connection):
    account_ref = _account_ref()
    snapshot = HomeExperienceService(engine).snapshot(account_ref=account_ref)
    packet = MingliRelationEffectEvidencePacketEnvelope.model_validate(
        snapshot["mingli"]["relation_effect_evidence_packet"]
    )
    if not packet.demand_packets:
        pytest.skip("active owner chart has no relation-effect evidence demand")
    receipt_payload = snapshot["mingli"]["relation_effect_evidence_request_receipt"]
    if receipt_payload is None:
        receipt = RelationEffectEvidenceRequestStore(engine).request_in_connection(
            connection,
            account_ref=account_ref,
            request=RelationEffectEvidencePreparationRequest(
                request_version=RELATION_EFFECT_EVIDENCE_REQUEST_VERSION,
                expected_packet_ref=packet.packet_ref,
                expected_packet_hash=packet.packet_hash,
                idempotency_key=("qa:relation-effect-material:preparation"),
            ),
            packet=packet,
        )
    else:
        receipt = RelationEffectEvidenceRequestReceipt.model_validate(receipt_payload)
    return account_ref, packet, receipt


def _bibliography() -> RelationEffectEvidenceBibliographyMetadata:
    return RelationEffectEvidenceBibliographyMetadata(
        title="子平法关系规则书目候选",
        responsible_party="待核验责任者",
        edition_or_publication_identity="待核验版本一",
        locator="卷一·关系规则·第十二节",
    )


def _material_request(
    receipt: RelationEffectEvidenceRequestReceipt,
    *,
    idempotency_key: str,
    bibliography: RelationEffectEvidenceBibliographyMetadata | None = None,
) -> RelationEffectEvidenceMaterialRequest:
    item = receipt.request_items[0]
    slot = next(
        slot for slot in item.dimension_slots if slot.dimension_id == "PROFESSIONAL_PROVENANCE"
    )
    return RelationEffectEvidenceMaterialRequest(
        material_request_version=(RELATION_EFFECT_EVIDENCE_MATERIAL_REQUEST_VERSION),
        expected_receipt_ref=receipt.receipt_ref,
        expected_receipt_hash=receipt.receipt_hash,
        expected_packet_ref=receipt.packet_ref,
        expected_packet_hash=receipt.packet_hash,
        expected_request_item_ref=item.request_item_ref,
        expected_demand_packet_ref=item.demand_packet_ref,
        expected_demand_packet_hash=item.demand_packet_hash,
        expected_slot_ref=slot.slot_ref,
        candidate_kind="BIBLIOGRAPHIC_COORDINATE_CANDIDATE",
        target_artifact_kind="PROFESSIONAL_SOURCE_MANIFEST",
        bibliography=bibliography or _bibliography(),
        idempotency_key=idempotency_key,
    )


def _insert_record(connection, record) -> None:
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
                 :dimension_id, :candidate_kind, :target_artifact_kind,
                 :bibliography_hash, :idempotency_key,
                 CAST(:material_json AS jsonb), :material_hash)
            """
        ),
        {
            **record.model_dump(
                mode="json",
                include={
                    "material_ref",
                    "material_version",
                    "requester_account_ref",
                    "case_ref",
                    "reading_ref",
                    "request_receipt_ref",
                    "request_receipt_hash",
                    "packet_ref",
                    "packet_hash",
                    "request_item_ref",
                    "demand_packet_ref",
                    "demand_packet_hash",
                    "slot_ref",
                    "dimension_id",
                    "candidate_kind",
                    "target_artifact_kind",
                    "bibliography_hash",
                    "idempotency_key",
                    "material_hash",
                },
            ),
            "material_json": canonical_json(record.model_dump(mode="json")),
        },
    )


def test_material_contract_is_metadata_only_and_never_evidence() -> None:
    with engine.connect() as connection:
        account_ref, packet, receipt = _context(connection)
    request = _material_request(
        receipt,
        idempotency_key="qa:relation-effect-material:contract",
    )
    record = RelationEffectEvidenceMaterialStore.derive_expected_record(
        account_ref=account_ref,
        request=request,
        receipt=receipt,
        packet=packet,
    )

    assert set(type(request).model_fields) == {
        "material_request_version",
        "expected_receipt_ref",
        "expected_receipt_hash",
        "expected_packet_ref",
        "expected_packet_hash",
        "expected_request_item_ref",
        "expected_demand_packet_ref",
        "expected_demand_packet_hash",
        "expected_slot_ref",
        "candidate_kind",
        "target_artifact_kind",
        "bibliography",
        "idempotency_key",
    }
    assert set(type(request.bibliography).model_fields) == {
        "title",
        "responsible_party",
        "edition_or_publication_identity",
        "locator",
    }
    assert record.status == ("CANDIDATE_METADATA_RECORDED_NOT_REQUESTED_ARTIFACT")
    assert record.semantics == "UNVERIFIED_BIBLIOGRAPHY_METADATA_ONLY"
    assert record.evidence_role == "NOT_EVIDENCE"
    assert record.requested_artifact_satisfied is False
    assert record.bibliography_hash == content_hash(request.bibliography.model_dump(mode="json"))
    assert (
        record.professional_material_count,
        record.professional_evidence_count,
        record.ready_dimension_slot_count,
    ) == (0, 0, 0)
    assert record.effect_status == "UNRESOLVED"
    assert record.usability_status == "UNRESOLVED"
    assert record.structured_bibliography_metadata_allowed is True
    assert all(
        getattr(record, field) is False
        for field in (
            "material_truth_verified",
            "source_authenticity_verified",
            "artifact_content_present",
            "citation_body_present",
            "llm_allowed",
            "provider_invoked",
            "reasoner_invoked",
            "owner_professional_review_invoked",
            "knowledge_admission_eligible",
            "knowledge_write_allowed",
            "gate_invoked",
            "decision_request_created",
            "decision_created",
            "file_upload_allowed",
            "url_submission_allowed",
            "quotation_body_submission_allowed",
            "conclusion_submission_allowed",
            "unstructured_notes_submission_allowed",
        )
    )

    payload = request.model_dump(mode="json")
    with pytest.raises(ValidationError, match="extra_forbidden"):
        RelationEffectEvidenceMaterialRequest.model_validate(
            {**payload, "quotation_body": "不允许的引文正文"}
        )
    for field in type(request.bibliography).model_fields:
        forged = {
            **request.bibliography.model_dump(mode="json"),
            field: "https://not-accepted.invalid/source",
        }
        with pytest.raises(
            ValidationError,
            match="relation_effect_evidence_material_url_not_allowed",
        ):
            RelationEffectEvidenceBibliographyMetadata.model_validate(forged)
        forged = {
            **request.bibliography.model_dump(mode="json"),
            field: "候选\x01坐标",
        }
        with pytest.raises(
            ValidationError,
            match=("relation_effect_evidence_material_metadata_not_canonical"),
        ):
            RelationEffectEvidenceBibliographyMetadata.model_validate(forged)


def test_material_store_is_private_idempotent_deduplicated_and_append_only() -> None:
    store = RelationEffectEvidenceMaterialStore(engine)
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            account_ref, packet, receipt = _context(connection)
            request = _material_request(
                receipt,
                idempotency_key=("qa:relation-effect-material:transaction"),
            )
            first = store.register_in_connection(
                connection,
                account_ref=account_ref,
                request=request,
                receipt=receipt,
                packet=packet,
            )
            assert (
                store.register_in_connection(
                    connection,
                    account_ref=account_ref,
                    request=request,
                    receipt=receipt,
                    packet=packet,
                )
                == first
            )
            assert store.for_receipt_in_connection(
                connection,
                account_ref=account_ref,
                receipt=receipt,
                packet=packet,
            ) == (first,)
            assert (
                store.for_receipt_in_connection(
                    connection,
                    account_ref="v60-account-private-other",
                    receipt=receipt,
                    packet=packet,
                )
                == ()
            )

            changed = _material_request(
                receipt,
                idempotency_key=request.idempotency_key,
                bibliography=RelationEffectEvidenceBibliographyMetadata(
                    title="不同候选",
                    responsible_party="待核验责任者",
                    edition_or_publication_identity="待核验版本一",
                    locator="卷二",
                ),
            )
            with pytest.raises(
                RelationEffectEvidenceMaterialConflictError,
                match="relation_effect_evidence_material_idempotency_conflict",
            ):
                store.register_in_connection(
                    connection,
                    account_ref=account_ref,
                    request=changed,
                    receipt=receipt,
                    packet=packet,
                )
            duplicate = _material_request(
                receipt,
                idempotency_key=("qa:relation-effect-material:changed-key"),
            )
            with pytest.raises(
                RelationEffectEvidenceMaterialConflictError,
                match="relation_effect_evidence_material_already_recorded",
            ):
                store.register_in_connection(
                    connection,
                    account_ref=account_ref,
                    request=duplicate,
                    receipt=receipt,
                    packet=packet,
                )
            with pytest.raises(
                RelationEffectEvidenceMaterialConflictError,
                match=("relation_effect_evidence_material_receipt_packet_conflict"),
            ):
                store.register_in_connection(
                    connection,
                    account_ref="v60-account-private-other",
                    request=request,
                    receipt=receipt,
                    packet=packet,
                )

            savepoint = connection.begin_nested()
            with pytest.raises(
                DBAPIError,
                match=("mingli_relation_effect_evidence_materials_are_append_only"),
            ):
                connection.execute(
                    text(
                        """
                        UPDATE
                            mingli.relation_effect_evidence_material_records
                        SET material_version = 'forbidden'
                        WHERE material_ref = :material_ref
                        """
                    ),
                    {"material_ref": first.material_ref},
                )
            savepoint.rollback()
            savepoint = connection.begin_nested()
            with pytest.raises(
                DBAPIError,
                match=("mingli_relation_effect_evidence_materials_are_append_only"),
            ):
                connection.execute(
                    text(
                        """
                        DELETE FROM
                            mingli.relation_effect_evidence_material_records
                        WHERE material_ref = :material_ref
                        """
                    ),
                    {"material_ref": first.material_ref},
                )
            savepoint.rollback()
        finally:
            transaction.rollback()


def test_material_rejects_wrong_dimension_and_cross_demand_binding() -> None:
    with engine.connect() as connection:
        account_ref, packet, receipt = _context(connection)
    request = _material_request(
        receipt,
        idempotency_key="qa:relation-effect-material:forged-chain",
    )
    item = receipt.request_items[0]
    non_provenance = next(
        slot for slot in item.dimension_slots if slot.dimension_id != "PROFESSIONAL_PROVENANCE"
    )
    with pytest.raises(
        RelationEffectEvidenceMaterialConflictError,
        match="relation_effect_evidence_material_scope_not_allowed",
    ):
        RelationEffectEvidenceMaterialStore.derive_expected_record(
            account_ref=account_ref,
            request=request.model_copy(update={"expected_slot_ref": non_provenance.slot_ref}),
            receipt=receipt,
            packet=packet,
        )
    for update in (
        {"expected_request_item_ref": "forged-request-item"},
        {"expected_demand_packet_ref": "forged-demand"},
        {"expected_demand_packet_hash": "0" * 64},
    ):
        with pytest.raises(
            RelationEffectEvidenceMaterialConflictError,
            match=("relation_effect_evidence_material_demand_chain_conflict"),
        ):
            RelationEffectEvidenceMaterialStore.derive_expected_record(
                account_ref=account_ref,
                request=request.model_copy(update=update),
                receipt=receipt,
                packet=packet,
            )


def test_material_requires_current_active_human_owner_case() -> None:
    store = RelationEffectEvidenceMaterialStore(engine)
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            account_ref, packet, receipt = _context(connection)
            request = _material_request(
                receipt,
                idempotency_key=("qa:relation-effect-material:inactive-case"),
            )
            connection.execute(
                text(
                    """
                    UPDATE mingli.cases
                    SET status = 'INACTIVE'
                    WHERE case_ref = :case_ref
                    """
                ),
                {"case_ref": receipt.case_ref},
            )
            with pytest.raises(
                RelationEffectEvidenceMaterialConflictError,
                match=("relation_effect_evidence_material_active_case_conflict"),
            ):
                store.register_in_connection(
                    connection,
                    account_ref=account_ref,
                    request=request,
                    receipt=receipt,
                    packet=packet,
                )
        finally:
            transaction.rollback()


def test_projection_and_integrity_reject_self_consistent_wrong_slot() -> None:
    store = RelationEffectEvidenceMaterialStore(engine)
    resolver = MingliRelationEffectHistoricalPacketResolver(engine)
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            account_ref, packet, receipt = _context(connection)
            canonical_request = _material_request(
                receipt,
                idempotency_key=("qa:relation-effect-material:forged-slot"),
            )
            item = receipt.request_items[0]
            forged_slot = next(
                slot
                for slot in item.dimension_slots
                if slot.dimension_id != "PROFESSIONAL_PROVENANCE"
            )
            forged = RelationEffectEvidenceMaterialRecord.issue(
                requester_account_ref=account_ref,
                idempotency_key=canonical_request.idempotency_key,
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
                slot_ref=forged_slot.slot_ref,
                dimension_id="PROFESSIONAL_PROVENANCE",
                candidate_kind="BIBLIOGRAPHIC_COORDINATE_CANDIDATE",
                target_artifact_kind="PROFESSIONAL_SOURCE_MANIFEST",
                bibliography=canonical_request.bibliography,
            )
            invalid_before = (
                RuntimeIntegrityService._count_invalid_relation_effect_evidence_materials(
                    connection,
                    resolver=resolver,
                )
            )
            _insert_record(connection, forged)
            with pytest.raises(
                RelationEffectEvidenceMaterialConflictError,
                match="relation_effect_evidence_material_scope_not_allowed",
            ):
                store.for_receipt_in_connection(
                    connection,
                    account_ref=account_ref,
                    receipt=receipt,
                    packet=packet,
                )
            invalid_after = (
                RuntimeIntegrityService._count_invalid_relation_effect_evidence_materials(
                    connection,
                    resolver=resolver,
                )
            )
            assert invalid_after == invalid_before + 1
        finally:
            transaction.rollback()


def test_home_replays_material_without_upgrading_packet_or_receipt() -> None:
    account_ref = _account_ref()
    baseline = HomeExperienceService(engine).snapshot(account_ref=account_ref)
    packet = MingliRelationEffectEvidencePacketEnvelope.model_validate(
        baseline["mingli"]["relation_effect_evidence_packet"]
    )
    if not packet.demand_packets:
        pytest.skip("active owner chart has no relation-effect evidence demand")
    receipt_payload = baseline["mingli"]["relation_effect_evidence_request_receipt"]
    receipt = (
        RelationEffectEvidenceRequestReceipt.model_validate(receipt_payload)
        if receipt_payload is not None
        else RelationEffectEvidenceRequestStore.derive_expected_receipt(
            account_ref=account_ref,
            request=RelationEffectEvidencePreparationRequest(
                request_version=RELATION_EFFECT_EVIDENCE_REQUEST_VERSION,
                expected_packet_ref=packet.packet_ref,
                expected_packet_hash=packet.packet_hash,
                idempotency_key=("qa:relation-effect-material:home-receipt"),
            ),
            packet=packet,
        )
    )
    request = _material_request(
        receipt,
        idempotency_key="qa:relation-effect-material:home",
    )
    record = RelationEffectEvidenceMaterialStore.derive_expected_record(
        account_ref=account_ref,
        request=request,
        receipt=receipt,
        packet=packet,
    )

    class ReceiptProjection:
        @staticmethod
        def for_packet(*, account_ref: str, packet):
            return receipt

    class MaterialProjection:
        @staticmethod
        def for_receipt(*, account_ref: str, receipt, packet):
            return (record,)

    projected = HomeExperienceService(
        engine,
        relation_effect_requests=ReceiptProjection(),
        relation_effect_materials=MaterialProjection(),
    ).snapshot(account_ref=account_ref)
    assert projected["mingli"]["relation_effect_evidence_materials"] == [
        record.model_dump(mode="json")
    ]
    assert projected["lab"]["relation_effect_evidence_material_refs"] == [record.material_ref]
    assert projected["lab"]["relation_effect_evidence_material_hashes"] == [record.material_hash]
    assert projected["lab"]["relation_effect_evidence_material_count"] == 1
    assert (
        projected["mingli"]["relation_effect_evidence_request_receipt"][
            "professional_material_count"
        ]
        == 0
    )
    assert (
        projected["mingli"]["relation_effect_evidence_packet"]["professional_evidence_count"] == 0
    )


def test_account_lock_serializes_material_snapshot_and_mechanism_write() -> None:
    account_ref = _account_ref()
    baseline = HomeExperienceService(engine).snapshot(account_ref=account_ref)
    packet = MingliRelationEffectEvidencePacketEnvelope.model_validate(
        baseline["mingli"]["relation_effect_evidence_packet"]
    )
    if not packet.demand_packets:
        pytest.skip("active owner chart has no relation-effect evidence demand")
    receipt_payload = baseline["mingli"]["relation_effect_evidence_request_receipt"]
    receipt = (
        RelationEffectEvidenceRequestReceipt.model_validate(receipt_payload)
        if receipt_payload is not None
        else RelationEffectEvidenceRequestStore.derive_expected_receipt(
            account_ref=account_ref,
            request=RelationEffectEvidencePreparationRequest(
                request_version=RELATION_EFFECT_EVIDENCE_REQUEST_VERSION,
                expected_packet_ref=packet.packet_ref,
                expected_packet_hash=packet.packet_hash,
                idempotency_key=("qa:relation-effect-material:lock-receipt"),
            ),
            packet=packet,
        )
    )
    baseline = deepcopy(baseline)
    baseline["mingli"]["relation_effect_evidence_request_receipt"] = receipt.model_dump(mode="json")
    request = _material_request(
        receipt,
        idempotency_key="qa:relation-effect-material:lock",
    )
    expected = RelationEffectEvidenceMaterialStore.derive_expected_record(
        account_ref=account_ref,
        request=request,
        receipt=receipt,
        packet=packet,
    )
    material_entered = Event()
    release_material = Event()
    comparison_started = Event()
    second_snapshot_reached = Event()
    snapshot_lock = Lock()
    snapshot_threads: list[str] = []

    class BlockingMaterials:
        def register_in_connection(self, connection, **kwargs):
            material_entered.set()
            if not release_material.wait(timeout=5):
                raise AssertionError("material lock test timed out")
            return expected

    class Comparison:
        @staticmethod
        def compare_in_connection(connection, **kwargs):
            return {"decision_ref": "qa-material-lock"}

    class CoordinatedHome(HomeExperienceService):
        def snapshot(self, *, account_ref: str):
            with snapshot_lock:
                snapshot_threads.append(current_thread().name)
                if len(snapshot_threads) == 2:
                    second_snapshot_reached.set()
            return baseline

    service = CoordinatedHome(
        engine,
        relation_effect_materials=BlockingMaterials(),
        mechanism_comparison=Comparison(),
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        material_future = pool.submit(
            service.register_relation_effect_evidence_material,
            account_ref=account_ref,
            request=request,
        )
        assert material_entered.wait(timeout=5)
        comparison_future = pool.submit(
            lambda: (
                comparison_started.set(),
                service.compare_mechanisms(account_ref=account_ref),
            )[1]
        )
        assert comparison_started.wait(timeout=5)
        try:
            assert second_snapshot_reached.wait(timeout=0.25) is False
            assert comparison_future.done() is False
        finally:
            release_material.set()
        assert material_future.result(timeout=5) == expected
        assert comparison_future.result(timeout=5) == {"decision_ref": "qa-material-lock"}
    assert len(snapshot_threads) == 2
