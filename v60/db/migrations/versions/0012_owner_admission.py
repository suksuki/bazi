"""Bind Actor and LifeTree identity to their canonical write owners.

Revision ID: 0012_owner_admission
Revises: 0011_world_event_admission
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_owner_admission"
down_revision: str | None = "0011_world_event_admission"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _content_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def upgrade() -> None:
    for table, schema in (("actors", "world"), ("life_trees", "dream")):
        op.add_column(
            table,
            sa.Column(
                "admission_manifest_json",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            schema=schema,
        )
        op.add_column(
            table,
            sa.Column("admission_manifest_hash", sa.String(length=64), nullable=True),
            schema=schema,
        )

    connection = op.get_bind()
    actors = connection.execute(
        sa.text(
            """
            SELECT actor_ref, world_ref, case_ref, actor_kind, display_name, branch
            FROM world.actors
            ORDER BY actor_ref
            """
        )
    ).mappings()
    for actor in actors:
        identity = dict(actor)
        manifest = {
            "admission_version": "v60.world-actor-admission.001",
            **identity,
            "identity_hash": _content_hash(identity),
        }
        connection.execute(
            sa.text(
                """
                UPDATE world.actors
                SET admission_manifest_json = CAST(:manifest AS jsonb),
                    admission_manifest_hash = :manifest_hash
                WHERE actor_ref = :actor_ref
                """
            ),
            {
                "actor_ref": actor["actor_ref"],
                "manifest": _canonical_json(manifest),
                "manifest_hash": _content_hash(manifest),
            },
        )

    trees = connection.execute(
        sa.text(
            """
            SELECT tree_ref, actor_ref, scene_ref, organs_json
            FROM dream.life_trees
            ORDER BY tree_ref
            """
        )
    ).mappings()
    for tree in trees:
        manifest = {
            "admission_version": "v60.life-tree-admission.backfill.001",
            "tree_ref": tree["tree_ref"],
            "actor_ref": tree["actor_ref"],
            "scene_ref": tree["scene_ref"],
            "organ_set_hash": _content_hash(tree["organs_json"]),
        }
        connection.execute(
            sa.text(
                """
                UPDATE dream.life_trees
                SET admission_manifest_json = CAST(:manifest AS jsonb),
                    admission_manifest_hash = :manifest_hash
                WHERE tree_ref = :tree_ref
                """
            ),
            {
                "tree_ref": tree["tree_ref"],
                "manifest": _canonical_json(manifest),
                "manifest_hash": _content_hash(manifest),
            },
        )

    for table, schema, constraint in (
        ("actors", "world", "uq_world_actor_admission_manifest_hash"),
        ("life_trees", "dream", "uq_life_tree_admission_manifest_hash"),
    ):
        op.alter_column(table, "admission_manifest_json", nullable=False, schema=schema)
        op.alter_column(table, "admission_manifest_hash", nullable=False, schema=schema)
        op.create_unique_constraint(
            constraint,
            table,
            ["admission_manifest_hash"],
            schema=schema,
        )


def downgrade() -> None:
    for table, schema, constraint in (
        ("life_trees", "dream", "uq_life_tree_admission_manifest_hash"),
        ("actors", "world", "uq_world_actor_admission_manifest_hash"),
    ):
        op.drop_constraint(constraint, table, schema=schema, type_="unique")
        op.drop_column(table, "admission_manifest_hash", schema=schema)
        op.drop_column(table, "admission_manifest_json", schema=schema)
