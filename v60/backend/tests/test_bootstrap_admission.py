from __future__ import annotations

from datetime import date, time

import pytest
from abu_v60.db.engine import engine
from abu_v60.dream import (
    LifeTreeAdmissionError,
    LifeTreeAdmissionService,
    LifeTreeDefinition,
    validate_persisted_life_tree_admission,
)
from abu_v60.dream.first_slice import FIRST_ACTOR_REF, FIRST_TREE_REF
from abu_v60.dream.seed import (
    SEED_BATCH_REF,
    SYNTHETIC_CASE_REF,
    SYNTHETIC_PROFILE_REF,
    SYSTEM_ACCOUNT_REF,
    seed_first_slice,
)
from abu_v60.migration import (
    MigrationBatchAdmissionError,
    MigrationBatchAdmissionService,
    MigrationBatchDefinition,
)
from abu_v60.mingli import (
    MingliCaseAdmissionDefinition,
    MingliCaseAdmissionError,
    MingliCaseAdmissionService,
)
from abu_v60.mingli.calendar import CALENDAR_ENGINE_VERSION, BirthInput, resolve_four_pillars
from abu_v60.mingli.compiler import compile_case
from abu_v60.world import (
    WorldActorAdmissionError,
    WorldActorAdmissionService,
    WorldActorDefinition,
    validate_persisted_world_actor_admission,
)
from sqlalchemy import text


def _runtime_snapshot() -> dict[str, object]:
    with engine.connect() as connection:
        actor = (
            connection.execute(
                text(
                    """
                    SELECT actor_version, timeline_json, state_json, state_hash
                    FROM world.actors
                    WHERE actor_ref = :actor_ref
                    """
                ),
                {"actor_ref": FIRST_ACTOR_REF},
            )
            .mappings()
            .one()
        )
        tree = (
            connection.execute(
                text(
                    """
                    SELECT tree_version, state, organs_json, projection_hash
                    FROM dream.life_trees
                    WHERE tree_ref = :tree_ref
                    """
                ),
                {"tree_ref": FIRST_TREE_REF},
            )
            .mappings()
            .one()
        )
        batches = connection.execute(
            text("SELECT count(*) FROM platform.migration_batches")
        ).scalar_one()
    return {
        "actor": dict(actor),
        "tree": dict(tree),
        "migration_batch_count": int(batches),
    }


def _seed_case_definition(
    *,
    source_manifest: dict[str, object],
) -> MingliCaseAdmissionDefinition:
    birth_input = BirthInput(
        calendar_type="solar",
        birth_date=date(1991, 8, 14),
        birth_time=time(9, 20),
        timezone="Asia/Shanghai",
        true_solar_time_policy="not_applied",
    )
    compiled = compile_case(
        case_ref=SYNTHETIC_CASE_REF,
        birth_input=birth_input,
        chart=resolve_four_pillars(birth_input),
    )
    return MingliCaseAdmissionDefinition.from_compiled(
        compiled=compiled,
        case_ref=SYNTHETIC_CASE_REF,
        owner_account_ref=SYSTEM_ACCOUNT_REF,
        profile_ref=SYNTHETIC_PROFILE_REF,
        subject_kind="CANONICAL_SYNTHETIC",
        birth_input_hash=birth_input.input_hash,
        algorithm_version=CALENDAR_ENGINE_VERSION,
        source_manifest=source_manifest,
    )


def test_seed_replay_preserves_evolved_actor_and_tree() -> None:
    before = _runtime_snapshot()

    seed_first_slice(engine)
    seed_first_slice(engine)

    assert _runtime_snapshot() == before


def test_existing_seed_batch_rejects_manifest_redefinition() -> None:
    changed = MigrationBatchDefinition(
        batch_ref=SEED_BATCH_REF,
        source_system="V60",
        source_database="qiazhi_v60",
        status="COMPLETED",
        manifest={"seed_id": "redefined"},
    )
    with engine.begin() as connection, pytest.raises(
        MigrationBatchAdmissionError,
        match="migration_batch_admission_conflict",
    ):
        MigrationBatchAdmissionService().admit(
            connection,
            definition=changed,
        )


def test_world_actor_identity_redefinition_is_rejected() -> None:
    changed = WorldActorDefinition(
        actor_ref=FIRST_ACTOR_REF,
        world_ref="v60-world-primary",
        case_ref=SYNTHETIC_CASE_REF,
        actor_kind="CANONICAL_SYNTHETIC",
        display_name="被改写的砚舟",
        branch="canonical_world",
        initial_timeline={"timeline_version": 1, "events": []},
        initial_state={"location": "south-slope-old-channel"},
    )
    with engine.begin() as connection, pytest.raises(
        WorldActorAdmissionError,
        match="world_actor_admission_conflict",
    ):
        WorldActorAdmissionService().admit(
            connection,
            definition=changed,
        )


def test_backfilled_tree_accepts_replay_but_rejects_identity_drift() -> None:
    with engine.begin() as connection:
        persisted = (
            connection.execute(
                text(
                    """
                    SELECT tree_ref, actor_ref, scene_ref, organs_json
                    FROM dream.life_trees
                    WHERE tree_ref = :tree_ref
                    """
                ),
                {"tree_ref": FIRST_TREE_REF},
            )
            .mappings()
            .one()
        )
        definition = LifeTreeDefinition(
            tree_ref=persisted["tree_ref"],
            actor_ref=persisted["actor_ref"],
            scene_ref=persisted["scene_ref"],
            initial_state="DORMANT",
            organs=persisted["organs_json"],
        )
        admitted = LifeTreeAdmissionService().admit(
            connection,
            definition=definition,
        )
        assert admitted.admission_version == "v60.life-tree-admission.backfill.001"

        changed = definition.model_copy(update={"scene_ref": "scene:drift"})
        with pytest.raises(
            LifeTreeAdmissionError,
            match="life_tree_admission_conflict",
        ):
            LifeTreeAdmissionService().admit(
                connection,
                definition=changed,
            )


def test_mingli_case_rejects_source_manifest_drift() -> None:
    changed = _seed_case_definition(
        source_manifest={
            "source_origin": "UNAUTHORIZED_REDEFINITION",
            "seed_batch_ref": SEED_BATCH_REF,
            "llm_calls": 0,
        }
    )
    with engine.begin() as connection, pytest.raises(
        MingliCaseAdmissionError,
        match="mingli_case_admission_conflict",
    ):
        MingliCaseAdmissionService().admit(
            connection,
            definition=changed,
        )


def test_actor_and_tree_manifest_tampering_is_detected() -> None:
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(
                text(
                    """
                    UPDATE world.actors
                    SET admission_manifest_hash = :tampered
                    WHERE actor_ref = :actor_ref
                    """
                ),
                {"actor_ref": FIRST_ACTOR_REF, "tampered": "0" * 64},
            )
            actor = (
                connection.execute(
                    text("SELECT * FROM world.actors WHERE actor_ref = :actor_ref"),
                    {"actor_ref": FIRST_ACTOR_REF},
                )
                .mappings()
                .one()
            )
            with pytest.raises(
                WorldActorAdmissionError,
                match="manifest_hash_mismatch",
            ):
                validate_persisted_world_actor_admission(dict(actor))

            connection.execute(
                text(
                    """
                    UPDATE dream.life_trees
                    SET admission_manifest_hash = :tampered
                    WHERE tree_ref = :tree_ref
                    """
                ),
                {"tree_ref": FIRST_TREE_REF, "tampered": "0" * 64},
            )
            tree = (
                connection.execute(
                    text("SELECT * FROM dream.life_trees WHERE tree_ref = :tree_ref"),
                    {"tree_ref": FIRST_TREE_REF},
                )
                .mappings()
                .one()
            )
            with pytest.raises(
                LifeTreeAdmissionError,
                match="manifest_hash_mismatch",
            ):
                validate_persisted_life_tree_admission(dict(tree))
        finally:
            transaction.rollback()
