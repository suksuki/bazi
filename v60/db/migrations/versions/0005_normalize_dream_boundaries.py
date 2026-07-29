"""Normalize legacy Dream tree and Encounter projection state.

Revision ID: 0005_normalize_dream_boundaries
Revises: 0004_question_organ_snapshots
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "0005_normalize_dream_boundaries"
down_revision: str | None = "0004_question_organ_snapshots"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FIRST_FUTURE_EVENT_REF = "v60-world-event-yanzhou-channel-outcome-v1"
RETURN_BASELINE_EVENT_REF = "v60-world-event-yanzhou-stone-loosened-v1"
RETURN_FUTURE_EVENT_REF = "v60-world-event-yanzhou-root-spread-v1"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _content_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _canonical_tree_state(event_statuses: dict[str, str]) -> str:
    if event_statuses.get(RETURN_FUTURE_EVENT_REF) == "SETTLED":
        return "RETURN_FRUIT_MATURED"
    if event_statuses.get(RETURN_BASELINE_EVENT_REF) == "SETTLED":
        return "RETURN_BASELINE_COMMITTED"
    if event_statuses.get(FIRST_FUTURE_EVENT_REF) == "SETTLED":
        return "FIRST_FRUIT_MATURED"
    return "DORMANT_QUESTION"


def _organ_key_from_ref(organ_ref: str) -> str | None:
    for token, key in (
        ("-leaf-world-", "evidence_leaf_world"),
        ("-leaf-structure-", "evidence_leaf_structure"),
        ("-branch-", "structure_branch"),
    ):
        if token in organ_ref:
            return key
    return None


def upgrade() -> None:
    connection = op.get_bind()
    event_statuses = dict(
        connection.execute(
            sa.text(
                """
                SELECT world_event_ref, status
                FROM world.events
                WHERE world_event_ref IN (:first_future, :return_baseline, :return_future)
                """
            ),
            {
                "first_future": FIRST_FUTURE_EVENT_REF,
                "return_baseline": RETURN_BASELINE_EVENT_REF,
                "return_future": RETURN_FUTURE_EVENT_REF,
            },
        ).all()
    )
    canonical_state = _canonical_tree_state(event_statuses)

    trees = connection.execute(
        sa.text(
            """
            SELECT tree_ref, tree_version, organs_json
            FROM dream.life_trees
            """
        )
    ).mappings()
    for tree in trees:
        projection = {
            "tree_ref": tree["tree_ref"],
            "tree_version": tree["tree_version"],
            "state": canonical_state,
            "organs": tree["organs_json"],
        }
        connection.execute(
            sa.text(
                """
                UPDATE dream.life_trees
                SET state = :state,
                    projection_hash = :projection_hash,
                    updated_at = now()
                WHERE tree_ref = :tree_ref
                """
            ),
            {
                "state": canonical_state,
                "projection_hash": _content_hash(projection),
                "tree_ref": tree["tree_ref"],
            },
        )

    encounters = connection.execute(
        sa.text(
            """
            SELECT e.encounter_ref, e.state_json, q.organ_set_json
            FROM dream.encounters AS e
            JOIN story.question_instances AS q ON q.question_ref = e.question_ref
            """
        )
    ).mappings()
    for encounter in encounters:
        state = dict(encounter["state_json"])
        organs = encounter["organ_set_json"]
        valid_refs = {organ["organ_ref"] for organ in organs.values()}
        normalized_refs: list[str] = []
        for observed_ref in state.get("observed_organs", []):
            if observed_ref in valid_refs:
                normalized_ref = observed_ref
            else:
                organ_key = _organ_key_from_ref(observed_ref)
                normalized_ref = (
                    organs[organ_key]["organ_ref"]
                    if organ_key is not None and organ_key in organs
                    else None
                )
            if normalized_ref is not None and normalized_ref not in normalized_refs:
                normalized_refs.append(normalized_ref)

        if normalized_refs == state.get("observed_organs", []):
            continue
        state["observed_organs"] = normalized_refs
        connection.execute(
            sa.text(
                """
                UPDATE dream.encounters
                SET state_json = CAST(:state_json AS jsonb),
                    state_hash = :state_hash,
                    updated_at = now()
                WHERE encounter_ref = :encounter_ref
                """
            ),
            {
                "state_json": _canonical_json(state),
                "state_hash": _content_hash(state),
                "encounter_ref": encounter["encounter_ref"],
            },
        )


def downgrade() -> None:
    # The previous global tree state cannot be reconstructed without reviving
    # viewer-private writes. Keep normalized values on downgrade.
    pass
