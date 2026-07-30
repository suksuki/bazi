from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from abu_v60.architecture import runtime_architecture
from abu_v60.dream.catalog import DreamEpisodeCatalog, EpisodeCatalogError
from abu_v60.dream.return_attention_contracts import (
    DreamReturnAttentionApplication,
    DreamReturnAttentionRecord,
)
from abu_v60.dream.tree_admission import (
    LifeTreeAdmissionError,
    validate_persisted_life_tree_admission,
)
from abu_v60.game import DreamCommandReceipt, life_tree_scene_registry
from abu_v60.media import (
    MediaCatalogError,
    RuntimeMediaError,
    runtime_media_manifest,
)
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
from abu_v60.mingli.relation_effect_request import (
    RelationEffectEvidenceRequestStore,
)
from abu_v60.mingli.relation_effect_request_contracts import (
    RelationEffectEvidencePreparationRequest,
    RelationEffectEvidenceRequestReceipt,
)
from abu_v60.observability.personal_journey_integrity import (
    DreamPersonalJourneyIntegrityInspector,
)
from abu_v60.provenance import content_hash
from abu_v60.runtime import world_runtime_worker
from abu_v60.system_manifest import PRIMARY_WORLD_ID
from abu_v60.world import (
    WorldActorAdmissionError,
    WorldEventAdmissionError,
    validate_persisted_world_actor_admission,
    validate_persisted_world_event_admission,
    validate_persisted_world_event_evidence,
)


class RuntimeIntegrityService:
    """Read-only operational proof for the executable V60 boundaries."""

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
                      ON account.account_ref =
                         request.requester_account_ref
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
                receipt = (
                    RelationEffectEvidenceRequestReceipt.model_validate(
                        row["receipt_json"]
                    )
                )
                expected_columns = {
                    "receipt_ref": receipt.receipt_ref,
                    "receipt_version": receipt.receipt_version,
                    "requester_account_ref": (
                        receipt.requester_account_ref
                    ),
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
                expected_receipt = (
                    RelationEffectEvidenceRequestStore
                    .derive_expected_receipt(
                        account_ref=receipt.requester_account_ref,
                        request=(
                            RelationEffectEvidencePreparationRequest(
                                request_version=receipt.request_version,
                                expected_packet_ref=receipt.packet_ref,
                                expected_packet_hash=receipt.packet_hash,
                                idempotency_key=receipt.idempotency_key,
                            )
                        ),
                        packet=packet,
                    )
                )
                if (
                    any(
                        row[key] != value
                        for key, value in expected_columns.items()
                    )
                    or row["receipt_json"]
                    != receipt.model_dump(mode="json")
                    or row["persisted_account_ref"]
                    != receipt.requester_account_ref
                    or row["owner_account_ref"]
                    != receipt.requester_account_ref
                    or row["owner_case_subject_kind"] != "HUMAN_OWNER"
                    or row["reading_case_ref"] != receipt.case_ref
                    or row["persisted_reading_hash"]
                    != receipt.reading_hash
                    or receipt != expected_receipt
                ):
                    invalid_count += 1
            except ValueError:
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
                           request.requester_account_ref
                               AS receipt_account_ref,
                           request.receipt_hash
                               AS persisted_receipt_hash,
                           request.packet_ref AS receipt_packet_ref,
                           request.packet_hash AS receipt_packet_hash
                    FROM mingli.relation_effect_evidence_material_records
                         AS material
                    LEFT JOIN identity.accounts AS account
                      ON account.account_ref =
                         material.requester_account_ref
                    LEFT JOIN mingli.cases AS owner_case
                      ON owner_case.case_ref = material.case_ref
                    LEFT JOIN mingli.readings AS reading
                      ON reading.reading_ref = material.reading_ref
                    LEFT JOIN
                         mingli.relation_effect_evidence_request_receipts
                         AS request
                      ON request.receipt_ref =
                         material.request_receipt_ref
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
                expected_receipt = (
                    RelationEffectEvidenceRequestStore
                    .derive_expected_receipt(
                        account_ref=receipt.requester_account_ref,
                        request=RelationEffectEvidencePreparationRequest(
                            request_version=receipt.request_version,
                            expected_packet_ref=receipt.packet_ref,
                            expected_packet_hash=receipt.packet_hash,
                            idempotency_key=receipt.idempotency_key,
                        ),
                        packet=packet,
                    )
                )
                expected_record = (
                    RelationEffectEvidenceMaterialStore
                    .derive_expected_record(
                        account_ref=record.requester_account_ref,
                        request=RelationEffectEvidenceMaterialRequest(
                            material_request_version=(
                                record.material_request_version
                            ),
                            expected_receipt_ref=(
                                record.request_receipt_ref
                            ),
                            expected_receipt_hash=(
                                record.request_receipt_hash
                            ),
                            expected_packet_ref=record.packet_ref,
                            expected_packet_hash=record.packet_hash,
                            expected_request_item_ref=(
                                record.request_item_ref
                            ),
                            expected_demand_packet_ref=(
                                record.demand_packet_ref
                            ),
                            expected_demand_packet_hash=(
                                record.demand_packet_hash
                            ),
                            expected_slot_ref=record.slot_ref,
                            candidate_kind=record.candidate_kind,
                            target_artifact_kind=(
                                record.target_artifact_kind
                            ),
                            bibliography=record.bibliography,
                            idempotency_key=record.idempotency_key,
                        ),
                        receipt=receipt,
                        packet=packet,
                    )
                )
                expected_columns = {
                    "material_ref": record.material_ref,
                    "material_version": record.material_version,
                    "requester_account_ref": (
                        record.requester_account_ref
                    ),
                    "case_ref": record.case_ref,
                    "reading_ref": record.reading_ref,
                    "request_receipt_ref": (
                        record.request_receipt_ref
                    ),
                    "request_receipt_hash": (
                        record.request_receipt_hash
                    ),
                    "packet_ref": record.packet_ref,
                    "packet_hash": record.packet_hash,
                    "request_item_ref": record.request_item_ref,
                    "demand_packet_ref": record.demand_packet_ref,
                    "demand_packet_hash": record.demand_packet_hash,
                    "slot_ref": record.slot_ref,
                    "dimension_id": record.dimension_id,
                    "candidate_kind": record.candidate_kind,
                    "target_artifact_kind": (
                        record.target_artifact_kind
                    ),
                    "bibliography_hash": record.bibliography_hash,
                    "idempotency_key": record.idempotency_key,
                    "material_hash": record.material_hash,
                }
                if (
                    any(
                        row[key] != value
                        for key, value in expected_columns.items()
                    )
                    or row["material_json"]
                    != record.model_dump(mode="json")
                    or row["persisted_account_ref"]
                    != record.requester_account_ref
                    or row["owner_account_ref"]
                    != record.requester_account_ref
                    or row["owner_case_subject_kind"] != "HUMAN_OWNER"
                    or row["reading_case_ref"] != record.case_ref
                    or row["persisted_reading_hash"]
                    != record.reading_hash
                    or row["receipt_account_ref"]
                    != record.requester_account_ref
                    or row["persisted_receipt_hash"]
                    != record.request_receipt_hash
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
        episode_catalog_service = DreamEpisodeCatalog()
        relation_effect_packet_resolver = (
            MingliRelationEffectHistoricalPacketResolver(engine)
        )
        personal_journey_integrity = (
            DreamPersonalJourneyIntegrityInspector()
        )
        with engine.connect() as connection:
            migration_head = connection.execute(
                text("SELECT version_num FROM alembic_version"),
            ).scalar_one()
            world = (
                connection.execute(
                    text(
                        """
                    SELECT current_epoch, current_tick, branch
                    FROM world.worlds
                    WHERE world_ref = :world_ref
                    """
                    ),
                    {"world_ref": PRIMARY_WORLD_ID},
                )
                .mappings()
                .one()
            )
            counts = (
                connection.execute(
                    text(
                        """
                    SELECT
                        (SELECT count(*) FROM mingli.cases) AS cases,
                        (SELECT count(*) FROM mingli.readings) AS readings,
                        (SELECT count(*)
                         FROM mingli.relation_effect_evidence_request_receipts)
                            AS relation_effect_evidence_requests,
                        (SELECT count(*)
                         FROM mingli.relation_effect_evidence_material_records)
                            AS relation_effect_evidence_materials,
                        (SELECT count(*) FROM world.actors) AS actors,
                        (SELECT count(*) FROM cognition.decision_records) AS decisions,
                        (SELECT count(*) FROM world.events) AS world_events,
                        (SELECT count(*) FROM story.question_instances) AS questions,
                        (SELECT count(*) FROM dream.life_trees) AS life_trees,
                        (SELECT count(*) FROM dream.encounters) AS encounters,
                        (SELECT count(*) FROM dream.command_receipts) AS command_receipts,
                        (SELECT count(*) FROM dream.return_attention_selections)
                            AS return_attention_selections,
                        (SELECT count(*) FROM dream.return_attention_applications)
                            AS return_attention_applications,
                        (SELECT count(*) FROM dream.private_inquiries)
                            AS private_inquiries,
                        (SELECT count(*) FROM dream.personal_observation_tasks)
                            AS personal_observation_tasks,
                        (SELECT count(*)
                         FROM dream.personal_observation_checkins)
                            AS personal_observation_checkins,
                        (SELECT count(*) FROM dream.answer_seals) AS answer_seals,
                        (SELECT count(*) FROM dream.reveals) AS reveals
                    """
                    )
                )
                .mappings()
                .one()
            )
            orphan_encounters = int(
                connection.execute(
                    text(
                        """
                        SELECT count(*)
                        FROM dream.encounters AS encounter
                        LEFT JOIN world.actors AS actor
                          ON actor.actor_ref = encounter.actor_ref
                        LEFT JOIN dream.life_trees AS tree
                          ON tree.tree_ref = encounter.tree_ref
                        LEFT JOIN story.question_instances AS question
                          ON question.question_ref = encounter.question_ref
                        WHERE actor.actor_ref IS NULL
                           OR tree.tree_ref IS NULL
                           OR question.question_ref IS NULL
                        """
                    )
                ).scalar_one()
            )
            unhashed_question_organs = int(
                connection.execute(
                    text(
                        """
                        SELECT count(*)
                        FROM story.question_instances
                        WHERE organ_set_json IS NULL
                           OR organ_set_hash IS NULL
                           OR organ_set_hash = ''
                        """
                    )
                ).scalar_one()
            )
            unadmitted_questions = int(
                connection.execute(
                    text(
                        """
                        SELECT count(*)
                        FROM story.question_instances
                        WHERE admission_manifest_json IS NULL
                           OR admission_manifest_hash IS NULL
                           OR admission_manifest_hash = ''
                        """
                    )
                ).scalar_one()
            )
            unadmitted_world_events = int(
                connection.execute(
                    text(
                        """
                        SELECT count(*)
                        FROM world.events
                        WHERE definition_hash IS NULL
                           OR admission_manifest_json IS NULL
                           OR admission_manifest_hash IS NULL
                           OR admission_manifest_hash = ''
                        """
                    )
                ).scalar_one()
            )
            unadmitted_world_actors = int(
                connection.execute(
                    text(
                        """
                        SELECT count(*)
                        FROM world.actors
                        WHERE admission_manifest_json IS NULL
                           OR admission_manifest_hash IS NULL
                           OR admission_manifest_hash = ''
                        """
                    )
                ).scalar_one()
            )
            unadmitted_life_trees = int(
                connection.execute(
                    text(
                        """
                        SELECT count(*)
                        FROM dream.life_trees
                        WHERE admission_manifest_json IS NULL
                           OR admission_manifest_hash IS NULL
                           OR admission_manifest_hash = ''
                        """
                    )
                ).scalar_one()
            )
            invalid_world_actor_admissions = 0
            for actor_row in connection.execute(text("SELECT * FROM world.actors")).mappings():
                try:
                    validate_persisted_world_actor_admission(dict(actor_row))
                except WorldActorAdmissionError:
                    invalid_world_actor_admissions += 1
            invalid_life_tree_admissions = 0
            for tree_row in connection.execute(text("SELECT * FROM dream.life_trees")).mappings():
                try:
                    validate_persisted_life_tree_admission(dict(tree_row))
                except LifeTreeAdmissionError:
                    invalid_life_tree_admissions += 1
            invalid_world_event_admissions = 0
            world_event_rows = connection.execute(
                text(
                    """
                    SELECT event.*, actor.case_ref AS actor_case_ref,
                           actor.actor_kind, actor.branch AS actor_branch
                    FROM world.events AS event
                    JOIN world.actors AS actor
                      ON actor.actor_ref = event.actor_ref
                    """
                )
            ).mappings()
            for world_event_row in world_event_rows:
                try:
                    manifest = validate_persisted_world_event_admission(dict(world_event_row))
                    validate_persisted_world_event_evidence(
                        connection,
                        manifest=manifest,
                    )
                except WorldEventAdmissionError:
                    invalid_world_event_admissions += 1
            invalid_dream_command_receipts = 0
            command_receipt_rows = connection.execute(
                text(
                    """
                    SELECT command_receipt_ref, viewer_account_ref,
                           idempotency_key, command, envelope_json,
                           envelope_hash, result_encounter_ref,
                           result_version, result_status, result_state_hash,
                           receipt_hash
                    FROM dream.command_receipts
                    """
                )
            ).mappings()
            for command_receipt_row in command_receipt_rows:
                payload = {
                    "receipt_version": "v60.dream-command-receipt.001",
                    **{
                        key: command_receipt_row[key]
                        for key in (
                            "command_receipt_ref",
                            "viewer_account_ref",
                            "idempotency_key",
                            "command",
                            "envelope_hash",
                            "result_encounter_ref",
                            "result_version",
                            "result_status",
                            "result_state_hash",
                        )
                    },
                    "envelope": command_receipt_row["envelope_json"],
                }
                try:
                    receipt = DreamCommandReceipt.model_validate(payload)
                    if (
                        content_hash(receipt.model_dump(mode="json"))
                        != (command_receipt_row["receipt_hash"])
                    ):
                        invalid_dream_command_receipts += 1
                except ValueError:
                    invalid_dream_command_receipts += 1
            invalid_dream_return_attention_selections = 0
            attention_selection_rows = connection.execute(
                text(
                    """
                    SELECT selection.*, encounter.viewer_account_ref
                               AS encounter_viewer_account_ref,
                           encounter.tree_ref AS encounter_tree_ref,
                           candidate.candidate_hash
                               AS persisted_candidate_hash,
                           candidate.tree_ref AS candidate_tree_ref
                    FROM dream.return_attention_selections AS selection
                    LEFT JOIN dream.encounters AS encounter
                      ON encounter.encounter_ref =
                         selection.source_encounter_ref
                    LEFT JOIN dream.grove_candidates AS candidate
                      ON candidate.candidate_ref =
                         selection.source_candidate_ref
                    """
                )
            ).mappings()
            for selection_row in attention_selection_rows:
                try:
                    record = DreamReturnAttentionRecord.model_validate(
                        selection_row["record_json"]
                    )
                    expected = {
                        "attention_ref": record.attention_ref,
                        "viewer_account_ref": record.viewer_account_ref,
                        "source_encounter_ref": record.source_encounter_ref,
                        "source_encounter_version": (
                            record.source_encounter_version
                        ),
                        "source_echo_ref": record.source_echo_ref,
                        "source_echo_hash": record.source_echo_hash,
                        "source_candidate_ref": record.source_candidate_ref,
                        "source_candidate_hash": (
                            record.source_candidate_hash
                        ),
                        "tree_ref": record.tree_ref,
                        "observation_ref": (
                            record.observation.observation_ref
                        ),
                        "idempotency_key": record.idempotency_key,
                        "record_hash": record.attention_hash,
                    }
                    if (
                        any(
                            selection_row[key] != value
                            for key, value in expected.items()
                        )
                        or selection_row["encounter_viewer_account_ref"]
                        != record.viewer_account_ref
                        or selection_row["encounter_tree_ref"]
                        != record.tree_ref
                        or selection_row["persisted_candidate_hash"]
                        != record.source_candidate_hash
                        or selection_row["candidate_tree_ref"]
                        != record.tree_ref
                    ):
                        invalid_dream_return_attention_selections += 1
                except ValueError:
                    invalid_dream_return_attention_selections += 1
            invalid_dream_return_attention_applications = 0
            attention_application_rows = connection.execute(
                text(
                    """
                    SELECT application.*, selection.viewer_account_ref
                               AS selection_viewer_account_ref,
                           selection.record_hash AS attention_hash,
                           selection.tree_ref AS selection_tree_ref,
                           encounter.viewer_account_ref
                               AS encounter_viewer_account_ref,
                           encounter.tree_ref AS encounter_tree_ref
                    FROM dream.return_attention_applications AS application
                    LEFT JOIN dream.return_attention_selections AS selection
                      ON selection.attention_ref =
                         application.attention_ref
                    LEFT JOIN dream.encounters AS encounter
                      ON encounter.encounter_ref =
                         application.encounter_ref
                    """
                )
            ).mappings()
            for application_row in attention_application_rows:
                try:
                    application = (
                        DreamReturnAttentionApplication.model_validate(
                            application_row["application_json"]
                        )
                    )
                    expected = {
                        "application_ref": application.application_ref,
                        "viewer_account_ref": (
                            application.viewer_account_ref
                        ),
                        "attention_ref": application.attention_ref,
                        "encounter_ref": application.encounter_ref,
                        "tree_ref": application.tree_ref,
                        "application_hash": application.application_hash,
                    }
                    if (
                        any(
                            application_row[key] != value
                            for key, value in expected.items()
                        )
                        or application_row["selection_viewer_account_ref"]
                        != application.viewer_account_ref
                        or application_row["encounter_viewer_account_ref"]
                        != application.viewer_account_ref
                        or application_row["selection_tree_ref"]
                        != application.tree_ref
                        or application_row["encounter_tree_ref"]
                        != application.tree_ref
                        or application_row["attention_hash"]
                        != application.attention_hash
                    ):
                        invalid_dream_return_attention_applications += 1
                except ValueError:
                    invalid_dream_return_attention_applications += 1
            invalid_relation_effect_evidence_request_receipts = (
                self._count_invalid_relation_effect_evidence_requests(
                    connection,
                    resolver=relation_effect_packet_resolver,
                )
            )
            invalid_relation_effect_evidence_material_records = (
                self._count_invalid_relation_effect_evidence_materials(
                    connection,
                    resolver=relation_effect_packet_resolver,
                )
            )
            personal_journey_integrity_results = (
                personal_journey_integrity.inspect(connection)
            )
            inconsistent_reveals = int(
                connection.execute(
                    text(
                        """
                        SELECT count(*)
                        FROM dream.reveals AS reveal
                        LEFT JOIN world.events AS event
                          ON event.world_event_ref = reveal.world_event_ref
                        WHERE event.status IS DISTINCT FROM 'SETTLED'
                        """
                    )
                ).scalar_one()
            )
            try:
                episode_catalog = episode_catalog_service.load(connection).public_summary()
                materialized_opportunity_count = int(
                    connection.execute(
                        text(
                            """
                            SELECT count(*)
                            FROM story.question_instances AS question
                            JOIN world.events AS event
                              ON event.world_event_ref = question.world_event_ref
                            WHERE question.episode_contract_json
                                      ->> 'runtime_status' = 'ACTIVE'
                              AND event.event_json ? 'source_question_ref'
                            """
                        )
                    ).scalar_one()
                )
                episode_catalog["active_materialized_opportunity_count"] = (
                    materialized_opportunity_count
                )
                episode_catalog["active_template_episode_count"] = (
                    episode_catalog["active_episode_count"]
                    - materialized_opportunity_count
                )
            except EpisodeCatalogError as exc:
                episode_catalog = {
                    "status": "INVALID",
                    "reason": str(exc),
                }
            try:
                media_runtime = {
                    "status": "READY",
                    **runtime_media_manifest(),
                }
            except (FileNotFoundError, MediaCatalogError, RuntimeMediaError) as exc:
                media_runtime = {
                    "status": "INVALID",
                    "reason": str(exc),
                }

        integrity = {
            "orphan_encounters": orphan_encounters,
            "invalid_life_tree_admissions": invalid_life_tree_admissions,
            "invalid_world_actor_admissions": invalid_world_actor_admissions,
            "unhashed_question_organs": unhashed_question_organs,
            "unadmitted_life_trees": unadmitted_life_trees,
            "unadmitted_questions": unadmitted_questions,
            "unadmitted_world_actors": unadmitted_world_actors,
            "unadmitted_world_events": unadmitted_world_events,
            "invalid_world_event_admissions": invalid_world_event_admissions,
            "invalid_dream_command_receipts": invalid_dream_command_receipts,
            "invalid_dream_return_attention_selections": (
                invalid_dream_return_attention_selections
            ),
            "invalid_dream_return_attention_applications": (
                invalid_dream_return_attention_applications
            ),
            **personal_journey_integrity_results,
            "invalid_relation_effect_evidence_request_receipts": (
                invalid_relation_effect_evidence_request_receipts
            ),
            "invalid_relation_effect_evidence_material_records": (
                invalid_relation_effect_evidence_material_records
            ),
            "reveal_without_settled_world_event": inconsistent_reveals,
        }
        ready = (
            all(value == 0 for value in integrity.values())
            and episode_catalog["status"] == "READY"
            and media_runtime["status"] == "READY"
        )
        world_runtime = world_runtime_worker.status()
        if world_runtime["enabled"]:
            ready = ready and world_runtime["status"] in {
                "READY",
                "STANDBY",
                "STARTING",
                "CONFIGURED",
            }
        return {
            "status": "READY" if ready else "DEGRADED",
            "migration_head": migration_head,
            "architecture_version": architecture.architecture_version,
            "world": dict(world),
            "world_runtime": world_runtime,
            "counts": {key: int(value) for key, value in counts.items()},
            "integrity": integrity,
            "episode_catalog": episode_catalog,
            "media_runtime": media_runtime,
            "scene_registry": {
                "status": "READY",
                "scenes": life_tree_scene_registry().public_manifest(),
            },
            "canonical_write_owners": {
                schema: module.module_id
                for module in architecture.modules
                for schema in module.owns_schemas
            },
            "product_units": list(architecture.product_units),
        }
