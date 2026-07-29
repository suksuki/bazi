from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.architecture import runtime_architecture
from abu_v60.dream.catalog import DreamEpisodeCatalog, EpisodeCatalogError
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

    def inspect(self, engine: Engine) -> dict[str, Any]:
        architecture = runtime_architecture()
        architecture.validate_boundaries()
        episode_catalog_service = DreamEpisodeCatalog()
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
                        (SELECT count(*) FROM world.actors) AS actors,
                        (SELECT count(*) FROM cognition.decision_records) AS decisions,
                        (SELECT count(*) FROM world.events) AS world_events,
                        (SELECT count(*) FROM story.question_instances) AS questions,
                        (SELECT count(*) FROM dream.life_trees) AS life_trees,
                        (SELECT count(*) FROM dream.encounters) AS encounters,
                        (SELECT count(*) FROM dream.command_receipts) AS command_receipts,
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
