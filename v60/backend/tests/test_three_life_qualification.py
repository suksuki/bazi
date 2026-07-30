from __future__ import annotations

from abu_v60.context import PublicWorldEvidence
from abu_v60.db.engine import engine
from abu_v60.decision import CognitiveDecisionLedger
from abu_v60.dream import THREE_LIFE_POOL_REF, DreamGroveRepository
from abu_v60.dream.opportunity import DreamOpportunityMaterializer
from abu_v60.dream.qualification_seed import (
    HEYANG_CHAPTER_TWO_PACKAGE_HASH,
    HEYANG_CHAPTER_TWO_PACKAGE_REF,
    HEYANG_CHAPTER_TWO_QUESTION_REF,
    HEYANG_CHAPTER_TWO_TRANSITION_HASH,
    HEYANG_CHAPTER_TWO_TRANSITION_REF,
    HEYANG_CHAPTER_TWO_WORLD_EVENT_REF,
    THREE_LIFE_CHAPTER_TWO_SEED_BATCH_REF,
    THREE_LIFE_HEYANG_CHAPTER_TWO_SEED_BATCH_REF,
    THREE_LIFE_LEGACY_SOURCE_REGISTRY_HASH,
    WENXI_CHAPTER_TWO_PACKAGE_HASH,
    WENXI_CHAPTER_TWO_PACKAGE_REF,
    WENXI_CHAPTER_TWO_QUESTION_REF,
    WENXI_CHAPTER_TWO_SOURCE_REGISTRY_HASH,
    WENXI_CHAPTER_TWO_TRANSITION_HASH,
    WENXI_CHAPTER_TWO_TRANSITION_REF,
    WENXI_CHAPTER_TWO_WORLD_EVENT_REF,
    seed_three_life_qualification,
)
from abu_v60.provenance import content_hash
from abu_v60.story import QUALIFICATION_EPISODE_SOURCE_REGISTRY_HASH
from abu_v60.world import WorldContinuityEngine
from sqlalchemy import text


def test_three_life_seed_is_idempotent_and_grove_projection_is_safe() -> None:
    first = seed_three_life_qualification(engine)
    second = seed_three_life_qualification(engine)

    assert first == second
    assert first["llm_calls"] == 0
    assert (
        first["source_registry_hash"]
        == QUALIFICATION_EPISODE_SOURCE_REGISTRY_HASH
    )
    assert (
        first["legacy_source_registry_hash"]
        == THREE_LIFE_LEGACY_SOURCE_REGISTRY_HASH
    )
    assert (
        first["chapter_two_seed_batch_ref"]
        == THREE_LIFE_CHAPTER_TWO_SEED_BATCH_REF
    )
    assert (
        first["heyang_chapter_two_seed_batch_ref"]
        == THREE_LIFE_HEYANG_CHAPTER_TWO_SEED_BATCH_REF
    )
    assert len(first["candidates"]) == 3
    assert {item["domain"] for item in first["candidates"]} == {
        "career",
        "wealth",
        "relationship",
    }
    assert len({item["scene_ref"] for item in first["candidates"]}) == 3
    assert len(
        {
            tuple(
                sorted(
                    item["phenotype"]["element_membership_ratios"].items()
                )
            )
            for item in first["candidates"]
        }
    ) == 3

    with engine.connect() as connection:
        candidates = DreamGroveRepository.active_candidates(
            connection,
            pool_ref=THREE_LIFE_POOL_REF,
        )
        counts = connection.execute(
            text(
                """
                SELECT
                    (SELECT count(*) FROM dream.grove_candidates
                     WHERE pool_ref = :pool_ref AND runtime_status = 'ACTIVE')
                        AS grove_count,
                    (SELECT count(*) FROM world.actors
                     WHERE actor_ref = ANY(:actor_refs)) AS actor_count,
                    (SELECT count(*) FROM dream.life_trees
                     WHERE tree_ref = ANY(:tree_refs)) AS tree_count,
                    (SELECT count(*) FROM story.question_instances
                     WHERE question_ref = ANY(:question_refs)) AS question_count
                """
            ),
            {
                "pool_ref": THREE_LIFE_POOL_REF,
                "actor_refs": [item["actor_ref"] for item in first["candidates"]],
                "tree_refs": [item["tree_ref"] for item in first["candidates"]],
                "question_refs": [
                    item["question_ref"] for item in first["candidates"]
                ],
            },
        ).mappings().one()
        chapter_two = (
            connection.execute(
                text(
                    """
                    SELECT question.question_ref, question.actor_ref,
                           question.episode_contract_json,
                           event.world_event_ref, event.event_json
                    FROM story.question_instances AS question
                    JOIN world.events AS event
                      ON event.world_event_ref = question.world_event_ref
                    WHERE question.question_ref = :question_ref
                    """
                ),
                {"question_ref": WENXI_CHAPTER_TWO_QUESTION_REF},
            )
            .mappings()
            .one()
        )
        heyang_chapter_two = (
            connection.execute(
                text(
                    """
                    SELECT question.question_ref, question.actor_ref,
                           question.episode_contract_json,
                           event.world_event_ref, event.event_json
                    FROM story.question_instances AS question
                    JOIN world.events AS event
                      ON event.world_event_ref = question.world_event_ref
                    WHERE question.question_ref = :question_ref
                    """
                ),
                {"question_ref": HEYANG_CHAPTER_TWO_QUESTION_REF},
            )
            .mappings()
            .one()
        )
        transition = (
            connection.execute(
                text(
                    """
                    SELECT transition_ref, from_question_ref, to_question_ref,
                           transition_json, transition_hash
                    FROM story.episode_transitions
                    WHERE transition_ref = :transition_ref
                    """
                ),
                {"transition_ref": WENXI_CHAPTER_TWO_TRANSITION_REF},
            )
            .mappings()
            .one()
        )
        heyang_transition = (
            connection.execute(
                text(
                    """
                    SELECT transition_ref, from_question_ref, to_question_ref,
                           transition_json, transition_hash
                    FROM story.episode_transitions
                    WHERE transition_ref = :transition_ref
                    """
                ),
                {"transition_ref": HEYANG_CHAPTER_TWO_TRANSITION_REF},
            )
            .mappings()
            .one()
        )
        extension_batch = (
            connection.execute(
                text(
                    """
                    SELECT manifest_json, manifest_hash
                    FROM platform.migration_batches
                    WHERE batch_ref = :batch_ref
                    """
                ),
                {"batch_ref": THREE_LIFE_CHAPTER_TWO_SEED_BATCH_REF},
            )
            .mappings()
            .one()
        )
        heyang_extension_batch = (
            connection.execute(
                text(
                    """
                    SELECT manifest_json, manifest_hash
                    FROM platform.migration_batches
                    WHERE batch_ref = :batch_ref
                    """
                ),
                {"batch_ref": THREE_LIFE_HEYANG_CHAPTER_TWO_SEED_BATCH_REF},
            )
            .mappings()
            .one()
        )
        legacy_batch_hash = connection.execute(
            text(
                """
                SELECT manifest_json ->> 'source_registry_hash'
                FROM platform.migration_batches
                WHERE batch_ref = 'v60-seed-batch-three-life-qualification-v1'
                """
            )
        ).scalar_one()
        case_source_hashes = (
            connection.execute(
                text(
                    """
                    SELECT DISTINCT chart.source_manifest_json
                                      ->> 'source_registry_hash'
                    FROM mingli.cases AS cases
                    JOIN mingli.chart_versions AS chart
                      ON chart.case_ref = cases.case_ref
                    WHERE cases.case_ref = ANY(:case_refs)
                    """
                ),
                {
                    "case_refs": [
                        "v60-synthetic-case-wenxi-v1",
                        "v60-synthetic-case-heyang-v1",
                        "v60-synthetic-case-zhaoning-v1",
                    ]
                },
            )
            .scalars()
            .all()
        )

    assert len(candidates) == 3
    assert dict(counts) == {
        "grove_count": 3,
        "actor_count": 3,
        "tree_count": 3,
        "question_count": 3,
    }
    runtime = chapter_two["episode_contract_json"]
    assert chapter_two["actor_ref"] == "v60-actor-wenxi-v1"
    assert chapter_two["world_event_ref"] == WENXI_CHAPTER_TWO_WORLD_EVENT_REF
    assert runtime["entrypoint"] is False
    assert runtime["chapter"] == "RETURN_VISIT"
    assert runtime["entry_world_event"]["caused_by_event_ref"] == (
        "v60-world-event-wenxi-archive-role-v1"
    )
    assert chapter_two["event_json"]["summary"] == (
        "观察共同修复后形成的新索引会怎样进入下一册工作。"
    )
    heyang_runtime = heyang_chapter_two["episode_contract_json"]
    assert heyang_chapter_two["actor_ref"] == "v60-actor-heyang-v1"
    assert (
        heyang_chapter_two["world_event_ref"]
        == HEYANG_CHAPTER_TWO_WORLD_EVENT_REF
    )
    assert heyang_runtime["entrypoint"] is False
    assert heyang_runtime["chapter"] == "RETURN_VISIT"
    assert heyang_runtime["entry_world_event"]["caused_by_event_ref"] == (
        "v60-world-event-heyang-cloth-exchange-v1"
    )
    assert heyang_chapter_two["event_json"]["summary"] == (
        "观察小批订单交付后是否形成可核验的验收与余款记录。"
    )
    assert transition["from_question_ref"] == (
        "v60-question-wenxi-archive-trial-v1"
    )
    assert transition["to_question_ref"] == WENXI_CHAPTER_TWO_QUESTION_REF
    assert transition["transition_hash"] == WENXI_CHAPTER_TWO_TRANSITION_HASH
    assert content_hash(transition["transition_json"]) == (
        WENXI_CHAPTER_TWO_TRANSITION_HASH
    )
    assert heyang_transition["from_question_ref"] == (
        "v60-question-heyang-dyed-cloth-v1"
    )
    assert (
        heyang_transition["to_question_ref"]
        == HEYANG_CHAPTER_TWO_QUESTION_REF
    )
    assert (
        heyang_transition["transition_hash"]
        == HEYANG_CHAPTER_TWO_TRANSITION_HASH
    )
    assert content_hash(heyang_transition["transition_json"]) == (
        HEYANG_CHAPTER_TWO_TRANSITION_HASH
    )
    expected_extension_manifest = {
        "seed_id": "v60.dream-three-life-wenxi-chapter-two.v1",
        "parent_batch_ref": "v60-seed-batch-three-life-qualification-v1",
        "source_origin": "V60_OWNER_APPROVED_SYNTHETIC_CONTENT",
        "source_registry_hash": WENXI_CHAPTER_TWO_SOURCE_REGISTRY_HASH,
        "package_ref": WENXI_CHAPTER_TWO_PACKAGE_REF,
        "package_hash": WENXI_CHAPTER_TWO_PACKAGE_HASH,
        "question_ref": WENXI_CHAPTER_TWO_QUESTION_REF,
        "world_event_ref": WENXI_CHAPTER_TWO_WORLD_EVENT_REF,
        "transition_ref": WENXI_CHAPTER_TWO_TRANSITION_REF,
        "transition_hash": WENXI_CHAPTER_TWO_TRANSITION_HASH,
        "llm_calls": 0,
    }
    assert extension_batch["manifest_json"] == expected_extension_manifest
    assert extension_batch["manifest_hash"] == content_hash(
        expected_extension_manifest
    )
    expected_heyang_extension_manifest = {
        "seed_id": "v60.dream-three-life-heyang-chapter-two.v1",
        "parent_batch_ref": "v60-seed-batch-three-life-qualification-v1",
        "source_origin": "V60_OWNER_APPROVED_SYNTHETIC_CONTENT",
        "source_registry_hash": QUALIFICATION_EPISODE_SOURCE_REGISTRY_HASH,
        "package_ref": HEYANG_CHAPTER_TWO_PACKAGE_REF,
        "package_hash": HEYANG_CHAPTER_TWO_PACKAGE_HASH,
        "question_ref": HEYANG_CHAPTER_TWO_QUESTION_REF,
        "world_event_ref": HEYANG_CHAPTER_TWO_WORLD_EVENT_REF,
        "transition_ref": HEYANG_CHAPTER_TWO_TRANSITION_REF,
        "transition_hash": HEYANG_CHAPTER_TWO_TRANSITION_HASH,
        "llm_calls": 0,
    }
    assert (
        heyang_extension_batch["manifest_json"]
        == expected_heyang_extension_manifest
    )
    assert heyang_extension_batch["manifest_hash"] == content_hash(
        expected_heyang_extension_manifest
    )
    assert legacy_batch_hash == THREE_LIFE_LEGACY_SOURCE_REGISTRY_HASH
    assert case_source_hashes == [THREE_LIFE_LEGACY_SOURCE_REGISTRY_HASH]
    serialized = str(candidates)
    assert "sealed_outcome" not in serialized
    assert "npc_choice" not in serialized
    assert "evidence" not in serialized
    assert all(
            set(candidate) == {
                "candidate_ref",
                "candidate_hash",
                "tree_ref",
                "domain",
                "public_alias",
                "premise",
            "display_order",
            "tree",
        }
        for candidate in candidates
    )


def test_grove_template_materializes_a_fresh_world_opportunity() -> None:
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            source_question_ref = connection.execute(
                text(
                    """
                    SELECT question_ref
                    FROM dream.grove_candidates
                    WHERE pool_ref = :pool_ref
                    ORDER BY display_order
                    LIMIT 1
                    """
                ),
                {"pool_ref": THREE_LIFE_POOL_REF},
            ).scalar_one()
            source_prompt = connection.execute(
                text(
                    """
                    SELECT prompt
                    FROM story.question_instances
                    WHERE question_ref = :question_ref
                    """
                ),
                {"question_ref": source_question_ref},
            ).scalar_one()
            world = WorldContinuityEngine(CognitiveDecisionLedger())
            current_tick = world.current_tick(connection)
            episode = DreamOpportunityMaterializer(world=world).materialize(
                connection,
                source_question_ref=str(source_question_ref),
            )
            row = (
                connection.execute(
                    text(
                        """
                        SELECT question.prompt, question.options_json,
                               question.cutoff_tick, question.due_tick,
                               event.status, event.event_json
                        FROM story.question_instances AS question
                        JOIN world.events AS event
                          ON event.world_event_ref = question.world_event_ref
                        WHERE question.question_ref = :question_ref
                        """
                    ),
                    {"question_ref": episode.question_ref},
                )
                .mappings()
                .one()
            )
            baseline_evidence = (
                connection.execute(
                    text(
                        """
                        SELECT evidence_json
                        FROM world.event_evidence
                        WHERE world_event_ref = :event_ref
                        ORDER BY evidence_ref
                        """
                    ),
                    {"event_ref": episode.baseline_event_ref},
                )
                .scalars()
                .all()
            )

            assert episode.question_ref != source_question_ref
            assert row["prompt"] == source_prompt
            assert int(row["cutoff_tick"]) == current_tick
            assert int(row["due_tick"]) > current_tick
            assert row["status"] == "SCHEDULED"
            assert row["event_json"]["source_question_ref"] == source_question_ref
            assert row["event_json"]["tree_projection_scope"] == "ENCOUNTER"
            assert row["event_json"]["baseline_evidence_lineage"]
            assert baseline_evidence
            assert all(
                PublicWorldEvidence.model_validate(item)
                for item in baseline_evidence
            )
            assert all(
                set(item) == {
                    "evidence_ref",
                    "summary",
                    "observed_at_tick",
                    "epistemic_role",
                }
                for item in baseline_evidence
            )
            serialized = str(row["options_json"])
            assert "sealed_outcome" not in serialized
            assert "actual_event" not in serialized
        finally:
            transaction.rollback()


def test_each_grove_tree_materializes_an_independent_current_world_question() -> None:
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            sources = (
                connection.execute(
                    text(
                        """
                        SELECT grove.question_ref, question.prompt
                        FROM dream.grove_candidates AS grove
                        JOIN story.question_instances AS question
                          ON question.question_ref = grove.question_ref
                        WHERE grove.pool_ref = :pool_ref
                        ORDER BY grove.display_order
                        """
                    ),
                    {"pool_ref": THREE_LIFE_POOL_REF},
                )
                .mappings()
                .all()
            )
            assert len(sources) == 3
            assert len({str(item["prompt"]) for item in sources}) == 3

            world = WorldContinuityEngine(CognitiveDecisionLedger())
            current_tick = world.current_tick(connection)
            episodes = [
                DreamOpportunityMaterializer(world=world).materialize(
                    connection,
                    source_question_ref=str(source["question_ref"]),
                )
                for source in sources
            ]
            rows = (
                connection.execute(
                    text(
                        """
                        SELECT question.question_ref, question.prompt,
                               question.cutoff_tick, question.due_tick,
                               event.event_json
                        FROM story.question_instances AS question
                        JOIN world.events AS event
                          ON event.world_event_ref = question.world_event_ref
                        WHERE question.question_ref = ANY(:question_refs)
                        ORDER BY question.question_ref
                        """
                    ),
                    {"question_refs": [item.question_ref for item in episodes]},
                )
                .mappings()
                .all()
            )

            assert len({item.question_ref for item in episodes}) == 3
            assert {str(item["prompt"]) for item in rows} == {
                str(item["prompt"]) for item in sources
            }
            assert all(int(item["cutoff_tick"]) == current_tick for item in rows)
            assert all(int(item["due_tick"]) > current_tick for item in rows)
            assert {
                str(item["event_json"]["source_question_ref"]) for item in rows
            } == {str(item["question_ref"]) for item in sources}
        finally:
            transaction.rollback()
