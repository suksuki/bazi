from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock, current_thread

import pytest
from abu_v60.db import engine
from abu_v60.experience.home import HomeExperienceService
from abu_v60.mingli import (
    RELATION_EFFECT_EVIDENCE_REQUEST_RECEIPT_VERSION,
    RELATION_EFFECT_EVIDENCE_REQUEST_VERSION,
    MingliRelationEffectAdmissionProjector,
    MingliRelationEffectEvidencePacketEnvelope,
    MingliRelationEffectEvidencePacketProjector,
    RelationEffectEvidencePreparationRequest,
    RelationEffectEvidenceRequestConflictError,
    RelationEffectEvidenceRequestedSlot,
    RelationEffectEvidenceRequestStore,
)
from abu_v60.mingli.calendar import ChartPillars
from abu_v60.mingli.relation_effect_history import (
    MingliRelationEffectHistoricalPacketResolver,
)
from abu_v60.observability import RuntimeIntegrityService
from abu_v60.provenance import canonical_json
from mingli_relation_effect_test_support import (
    project_relation_effect_frontier,
    relation_effect_bundle,
)
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError


def _packet(
    pillars: ChartPillars,
) -> MingliRelationEffectEvidencePacketEnvelope:
    bundle = relation_effect_bundle(pillars)
    frontier = project_relation_effect_frontier(bundle)
    review = MingliRelationEffectAdmissionProjector().project(frontier=frontier)
    return MingliRelationEffectEvidencePacketProjector().project(
        reading=bundle["reading"],
        frontier=frontier,
        admission_review=review,
    )


def _request(
    packet: MingliRelationEffectEvidencePacketEnvelope,
    *,
    idempotency_key: str,
) -> RelationEffectEvidencePreparationRequest:
    return RelationEffectEvidencePreparationRequest(
        request_version=RELATION_EFFECT_EVIDENCE_REQUEST_VERSION,
        expected_packet_ref=packet.packet_ref,
        expected_packet_hash=packet.packet_hash,
        idempotency_key=idempotency_key,
    )


def _active_owner_account_ref() -> str:
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


def test_request_contract_derives_one_demand_and_six_slots_without_input() -> None:
    packet = _packet(
        ChartPillars(
            year="己巳",
            month="丙子",
            day="丙寅",
            hour="甲午",
        )
    )
    request = _request(
        packet,
        idempotency_key="qa:relation-effect-request:contract",
    )
    receipt = RelationEffectEvidenceRequestStore.derive_expected_receipt(
        account_ref="v60-account-relation-effect-request-contract",
        request=request,
        packet=packet,
    )

    assert set(type(request).model_fields) == {
        "request_version",
        "expected_packet_ref",
        "expected_packet_hash",
        "idempotency_key",
    }
    assert receipt.receipt_version == (RELATION_EFFECT_EVIDENCE_REQUEST_RECEIPT_VERSION)
    assert receipt.request_version == (RELATION_EFFECT_EVIDENCE_REQUEST_VERSION)
    assert receipt.packet_ref == packet.packet_ref
    assert receipt.packet_hash == packet.packet_hash
    assert receipt.request_item_count == 1
    assert receipt.requested_dimension_slot_count == 6
    assert receipt.ready_dimension_slot_count == 0
    assert receipt.professional_material_count == 0
    assert receipt.professional_evidence_count == 0
    assert receipt.status == "REQUEST_RECORDED_NOT_EVIDENCE"
    assert receipt.semantics == ("PREPARATION_REQUEST_NOT_PROFESSIONAL_EVIDENCE")
    assert receipt.evidence_role == "NOT_EVIDENCE"
    assert receipt.effect_decision_status == "WITHHELD"
    assert receipt.effect_status == "UNRESOLVED"
    assert receipt.usability_status == "UNRESOLVED"
    item = receipt.request_items[0]
    demand = packet.demand_packets[0]
    assert (
        item.demand_packet_ref,
        item.demand_packet_hash,
        item.assessment_ref,
        item.assessment_hash,
        item.demand_ref,
    ) == (
        demand.demand_packet_ref,
        demand.demand_packet_hash,
        demand.assessment_ref,
        demand.assessment_hash,
        demand.demand_ref,
    )
    assert item.requested_dimension_slot_count == 6
    assert [slot.dimension_id for slot in item.dimension_slots] == [
        slot.dimension_id for slot in demand.dimension_slots
    ]
    assert [slot.slot_ref for slot in item.dimension_slots] == [
        slot.slot_ref for slot in demand.dimension_slots
    ]
    assert all(
        requested.requirement == source.requirement
        and requested.requested_artifact_kinds == source.requested_artifact_kinds
        and requested.next_action == source.next_action
        and requested.status == "REQUESTED_NOT_EVIDENCE"
        and requested.professional_material_count == 0
        and requested.professional_evidence_count == 0
        and requested.ready is False
        for requested, source in zip(
            item.dimension_slots,
            demand.dimension_slots,
            strict=True,
        )
    )
    assert all(
        getattr(receipt, field) is False
        for field in (
            "llm_allowed",
            "provider_invoked",
            "reasoner_invoked",
            "owner_professional_review_invoked",
            "knowledge_admission_eligible",
            "knowledge_write_allowed",
            "gate_invoked",
            "decision_request_created",
            "decision_created",
            "professional_verdict_allowed",
            "probability_claim_allowed",
            "effect_or_usability_write_allowed",
            "material_intake_open",
            "file_upload_allowed",
            "url_submission_allowed",
            "free_text_submission_allowed",
        )
    )
    assert receipt.private_to_requester_account is True
    assert receipt.append_only is True
    assert receipt.read_only is True

    payload = request.model_dump(mode="json")
    with pytest.raises(ValidationError, match="extra_forbidden"):
        RelationEffectEvidencePreparationRequest.model_validate(
            {
                **payload,
                "source_url": "https://not-accepted.invalid",
            }
        )
    with pytest.raises(ValidationError, match="Field required"):
        RelationEffectEvidencePreparationRequest.model_validate(
            {key: value for key, value in payload.items() if key != "request_version"}
        )


def test_request_store_is_private_replay_safe_append_only_and_rolled_back() -> None:
    account_ref = _active_owner_account_ref()
    snapshot = HomeExperienceService(engine).snapshot(account_ref=account_ref)
    packet = MingliRelationEffectEvidencePacketEnvelope.model_validate(
        snapshot["mingli"]["relation_effect_evidence_packet"]
    )
    assert packet.demand_packet_count == 1
    store = RelationEffectEvidenceRequestStore(engine)
    request = _request(
        packet,
        idempotency_key="qa:relation-effect-request:transaction",
    )

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            before = connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM mingli.relation_effect_evidence_request_receipts
                    """
                )
            ).scalar_one()
            first = store.request_in_connection(
                connection,
                account_ref=account_ref,
                request=request,
                packet=packet,
            )
            replay = store.request_in_connection(
                connection,
                account_ref=account_ref,
                request=request,
                packet=packet,
            )
            restored = store.for_packet_in_connection(
                connection,
                account_ref=account_ref,
                packet=packet,
            )

            assert replay == first
            assert restored == first
            assert (
                store.for_packet_in_connection(
                    connection,
                    account_ref="v60-account-other-private-scope",
                    packet=packet,
                )
                is None
            )
            assert (
                connection.execute(
                    text(
                        """
                    SELECT count(*)
                    FROM mingli.relation_effect_evidence_request_receipts
                    """
                    )
                ).scalar_one()
                == before + 1
            )

            with pytest.raises(
                RelationEffectEvidenceRequestConflictError,
                match=("relation_effect_evidence_request_already_recorded"),
            ):
                store.request_in_connection(
                    connection,
                    account_ref=account_ref,
                    request=_request(
                        packet,
                        idempotency_key=("qa:relation-effect-request:different-key"),
                    ),
                    packet=packet,
                )
            with pytest.raises(
                RelationEffectEvidenceRequestConflictError,
                match=("relation_effect_evidence_request_active_case_conflict"),
            ):
                store.request_in_connection(
                    connection,
                    account_ref="v60-account-other-private-scope",
                    request=_request(
                        packet,
                        idempotency_key=("qa:relation-effect-request:other-account"),
                    ),
                    packet=packet,
                )

            changed_packet = MingliRelationEffectEvidencePacketEnvelope.issue(
                case_ref=packet.case_ref,
                chart_version_ref=packet.chart_version_ref,
                reading_ref=packet.reading_ref,
                reading_hash=packet.reading_hash,
                frontier_ref=f"{packet.frontier_ref}:changed",
                frontier_hash=packet.frontier_hash,
                admission_review_ref=(packet.admission_review_ref),
                admission_review_hash=(packet.admission_review_hash),
                policy_ref=packet.policy_ref,
                policy_hash=packet.policy_hash,
                proposal_ref=packet.proposal_ref,
                proposal_hash=packet.proposal_hash,
                demand_packets=packet.demand_packets,
            )
            with pytest.raises(
                RelationEffectEvidenceRequestConflictError,
                match=("relation_effect_evidence_request_idempotency_conflict"),
            ):
                store.request_in_connection(
                    connection,
                    account_ref=account_ref,
                    request=_request(
                        changed_packet,
                        idempotency_key=request.idempotency_key,
                    ),
                    packet=changed_packet,
                )

            savepoint = connection.begin_nested()
            with pytest.raises(
                DBAPIError,
                match=("mingli_relation_effect_evidence_requests_are_append_only"),
            ):
                connection.execute(
                    text(
                        """
                        UPDATE mingli.relation_effect_evidence_request_receipts
                        SET receipt_version = 'forbidden-rewrite'
                        WHERE receipt_ref = :receipt_ref
                        """
                    ),
                    {"receipt_ref": first.receipt_ref},
                )
            savepoint.rollback()

            delete_savepoint = connection.begin_nested()
            with pytest.raises(
                DBAPIError,
                match=(
                    "mingli_relation_effect_evidence_requests_"
                    "are_append_only"
                ),
            ):
                connection.execute(
                    text(
                        """
                        DELETE FROM
                            mingli.relation_effect_evidence_request_receipts
                        WHERE receipt_ref = :receipt_ref
                        """
                    ),
                    {"receipt_ref": first.receipt_ref},
                )
            delete_savepoint.rollback()
        finally:
            transaction.rollback()


def test_clear_packet_rejects_request_before_any_write() -> None:
    clear = _packet(
        ChartPillars(
            year="丁巳",
            month="乙巳",
            day="乙丑",
            hour="乙酉",
        )
    )
    assert clear.demand_packets == ()
    store = RelationEffectEvidenceRequestStore(engine)

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            before = connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM mingli.relation_effect_evidence_request_receipts
                    """
                )
            ).scalar_one()
            with pytest.raises(
                RelationEffectEvidenceRequestConflictError,
                match="relation_effect_evidence_request_not_triggered",
            ):
                store.request_in_connection(
                    connection,
                    account_ref="v60-account-clear-no-write",
                    request=_request(
                        clear,
                        idempotency_key=("qa:relation-effect-request:clear"),
                    ),
                    packet=clear,
                )
            after = connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM mingli.relation_effect_evidence_request_receipts
                    """
                )
            ).scalar_one()
            assert after == before
        finally:
            transaction.rollback()


def test_home_projection_shares_recovered_receipt_without_evidence_credit() -> None:
    account_ref = _active_owner_account_ref()
    first = HomeExperienceService(engine).snapshot(account_ref=account_ref)
    canonical_packet = MingliRelationEffectEvidencePacketEnvelope.model_validate(
        first["mingli"]["relation_effect_evidence_packet"]
    )
    receipt = RelationEffectEvidenceRequestStore.derive_expected_receipt(
        account_ref=account_ref,
        request=_request(
            canonical_packet,
            idempotency_key=("qa:relation-effect-request:home-projection"),
        ),
        packet=canonical_packet,
    )

    class RecoveredReceiptProjection:
        @staticmethod
        def for_packet(*, account_ref: str, packet: object):
            assert account_ref == receipt.requester_account_ref
            assert packet == canonical_packet
            return receipt

    recovered = HomeExperienceService(
        engine,
        relation_effect_requests=RecoveredReceiptProjection(),
    ).snapshot(account_ref=account_ref)

    assert recovered["mingli"]["relation_effect_evidence_request_receipt"] == receipt.model_dump(
        mode="json"
    )
    assert recovered["lab"]["relation_effect_evidence_request_receipt_ref"] == receipt.receipt_ref
    assert recovered["lab"]["relation_effect_evidence_request_receipt_hash"] == receipt.receipt_hash
    original_packet = recovered["mingli"]["relation_effect_evidence_packet"]
    assert original_packet["professional_evidence_count"] == 0
    assert original_packet["ready_dimension_slot_count"] == 0


def test_request_slot_rejects_noncanonical_professional_guidance() -> None:
    packet = _packet(
        ChartPillars(
            year="己巳",
            month="丙子",
            day="丙寅",
            hour="甲午",
        )
    )
    source_slot = packet.demand_packets[0].dimension_slots[0]
    forged = {
        **source_slot.model_dump(
            mode="json",
            include={
                "slot_ref",
                "dimension_id",
                "requirement",
                "requested_artifact_kinds",
                "next_action",
            },
        ),
        "requirement": "伪造的自洽专业要求。",
        "status": "REQUESTED_NOT_EVIDENCE",
        "professional_material_count": 0,
        "professional_evidence_count": 0,
        "ready": False,
    }

    with pytest.raises(
        ValidationError,
        match=(
            "relation_effect_evidence_request_slot_"
            "canonical_guidance_mismatch"
        ),
    ):
        RelationEffectEvidenceRequestedSlot.model_validate(forged)


def test_historical_packet_resolver_rebuilds_from_persisted_reading() -> None:
    account_ref = _active_owner_account_ref()
    snapshot = HomeExperienceService(engine).snapshot(
        account_ref=account_ref
    )
    packet = MingliRelationEffectEvidencePacketEnvelope.model_validate(
        snapshot["mingli"]["relation_effect_evidence_packet"]
    )
    resolver = MingliRelationEffectHistoricalPacketResolver(engine)

    with engine.connect() as connection:
        rebuilt = resolver.resolve_in_connection(
            connection,
            reading_ref=packet.reading_ref,
        )

    assert rebuilt == packet


def test_runtime_integrity_rejects_self_consistent_forged_packet_lineage() -> None:
    account_ref = _active_owner_account_ref()
    snapshot = HomeExperienceService(engine).snapshot(
        account_ref=account_ref
    )
    packet = MingliRelationEffectEvidencePacketEnvelope.model_validate(
        snapshot["mingli"]["relation_effect_evidence_packet"]
    )
    forged_packet = MingliRelationEffectEvidencePacketEnvelope.issue(
        case_ref=packet.case_ref,
        chart_version_ref=packet.chart_version_ref,
        reading_ref=packet.reading_ref,
        reading_hash=packet.reading_hash,
        frontier_ref=f"{packet.frontier_ref}:forged",
        frontier_hash=packet.frontier_hash,
        admission_review_ref=packet.admission_review_ref,
        admission_review_hash=packet.admission_review_hash,
        policy_ref=packet.policy_ref,
        policy_hash=packet.policy_hash,
        proposal_ref=packet.proposal_ref,
        proposal_hash=packet.proposal_hash,
        demand_packets=packet.demand_packets,
    )
    forged_request = _request(
        forged_packet,
        idempotency_key=(
            "qa:relation-effect-request:forged-packet-lineage"
        ),
    )
    forged_receipt = (
        RelationEffectEvidenceRequestStore.derive_expected_receipt(
            account_ref=account_ref,
            request=forged_request,
            packet=forged_packet,
        )
    )
    resolver = MingliRelationEffectHistoricalPacketResolver(engine)

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            invalid_before = (
                RuntimeIntegrityService
                ._count_invalid_relation_effect_evidence_requests(
                    connection,
                    resolver=resolver,
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO
                        mingli.relation_effect_evidence_request_receipts
                        (receipt_ref, receipt_version,
                         requester_account_ref, case_ref, reading_ref,
                         packet_ref, packet_hash, idempotency_key,
                         receipt_json, receipt_hash)
                    VALUES
                        (:receipt_ref, :receipt_version,
                         :requester_account_ref, :case_ref, :reading_ref,
                         :packet_ref, :packet_hash, :idempotency_key,
                         CAST(:receipt_json AS jsonb), :receipt_hash)
                    """
                ),
                {
                    "receipt_ref": forged_receipt.receipt_ref,
                    "receipt_version": forged_receipt.receipt_version,
                    "requester_account_ref": account_ref,
                    "case_ref": forged_receipt.case_ref,
                    "reading_ref": forged_receipt.reading_ref,
                    "packet_ref": forged_receipt.packet_ref,
                    "packet_hash": forged_receipt.packet_hash,
                    "idempotency_key": forged_receipt.idempotency_key,
                    "receipt_json": canonical_json(
                        forged_receipt.model_dump(mode="json")
                    ),
                    "receipt_hash": forged_receipt.receipt_hash,
                },
            )
            invalid_after = (
                RuntimeIntegrityService
                ._count_invalid_relation_effect_evidence_requests(
                    connection,
                    resolver=resolver,
                )
            )

            assert invalid_after == invalid_before + 1
        finally:
            transaction.rollback()


def test_account_lock_serializes_request_snapshot_and_mechanism_write() -> None:
    account_ref = _active_owner_account_ref()
    baseline = HomeExperienceService(engine).snapshot(
        account_ref=account_ref
    )
    packet = MingliRelationEffectEvidencePacketEnvelope.model_validate(
        baseline["mingli"]["relation_effect_evidence_packet"]
    )
    request = _request(
        packet,
        idempotency_key="qa:relation-effect-request:account-lock",
    )
    expected_receipt = (
        RelationEffectEvidenceRequestStore.derive_expected_receipt(
            account_ref=account_ref,
            request=request,
            packet=packet,
        )
    )
    request_entered = Event()
    release_request = Event()
    compare_started = Event()
    second_snapshot_reached = Event()
    snapshot_lock = Lock()
    snapshot_threads: list[str] = []

    class BlockingRequestStore:
        request_backend_pid: int | None = None

        def request_in_connection(
            self,
            connection,
            *,
            account_ref: str,
            request: RelationEffectEvidencePreparationRequest,
            packet: MingliRelationEffectEvidencePacketEnvelope,
        ):
            assert account_ref == expected_receipt.requester_account_ref
            assert request.idempotency_key == (
                expected_receipt.idempotency_key
            )
            assert packet.packet_ref == expected_receipt.packet_ref
            self.request_backend_pid = int(
                connection.execute(
                    text("SELECT pg_backend_pid()")
                ).scalar_one()
            )
            request_entered.set()
            if not release_request.wait(timeout=5):
                raise AssertionError("request lock test timed out")
            return expected_receipt

    class ComparisonRecorder:
        comparison_backend_pid: int | None = None

        def compare_in_connection(
            self,
            connection,
            *,
            account_ref: str,
            vector,
        ):
            assert account_ref == expected_receipt.requester_account_ref
            assert vector.vector_ref == baseline["lab"][
                "mechanism_vector_ref"
            ]
            self.comparison_backend_pid = int(
                connection.execute(
                    text("SELECT pg_backend_pid()")
                ).scalar_one()
            )
            return {"decision_ref": "qa-lock-serialized"}

    blocking_store = BlockingRequestStore()
    comparison = ComparisonRecorder()

    class CoordinatedHome(HomeExperienceService):
        def snapshot(self, *, account_ref: str):
            assert account_ref == expected_receipt.requester_account_ref
            with snapshot_lock:
                snapshot_threads.append(current_thread().name)
                if len(snapshot_threads) == 2:
                    second_snapshot_reached.set()
            return baseline

    service = CoordinatedHome(
        engine,
        relation_effect_requests=blocking_store,
        mechanism_comparison=comparison,
    )

    def run_compare():
        compare_started.set()
        return service.compare_mechanisms(account_ref=account_ref)

    with ThreadPoolExecutor(
        max_workers=2,
        thread_name_prefix="v60-account-lock",
    ) as pool:
        request_future = pool.submit(
            service.request_relation_effect_evidence,
            account_ref=account_ref,
            request=request,
        )
        assert request_entered.wait(timeout=5)
        compare_future = pool.submit(run_compare)
        assert compare_started.wait(timeout=5)
        try:
            assert second_snapshot_reached.wait(timeout=0.25) is False
            assert compare_future.done() is False
        finally:
            release_request.set()

        assert request_future.result(timeout=5) == expected_receipt
        assert compare_future.result(timeout=5) == {
            "decision_ref": "qa-lock-serialized"
        }

    assert len(snapshot_threads) == 2
    assert snapshot_threads[0] != snapshot_threads[1]
    assert blocking_store.request_backend_pid is not None
    assert comparison.comparison_backend_pid is not None
    assert (
        blocking_store.request_backend_pid
        != comparison.comparison_backend_pid
    )
