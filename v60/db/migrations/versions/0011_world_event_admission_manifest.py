"""Bind WorldEvents to deterministic World-owner admission receipts.

Revision ID: 0011_world_event_admission
Revises: 0010_episode_admission_manifest
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011_world_event_admission"
down_revision: str | None = "0010_episode_admission_manifest"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _content_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("definition_hash", sa.String(length=64), nullable=True),
        schema="world",
    )
    op.add_column(
        "events",
        sa.Column(
            "admission_manifest_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        schema="world",
    )
    op.add_column(
        "events",
        sa.Column("admission_manifest_hash", sa.String(length=64), nullable=True),
        schema="world",
    )

    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT event.world_event_ref, event.world_ref, event.actor_ref,
                   event.event_type, event.due_tick, event.event_json,
                   event.sealed_outcome_json, event.outcome_hash,
                   actor.case_ref AS actor_case_ref,
                   actor.actor_kind, actor.branch AS actor_branch
            FROM world.events AS event
            JOIN world.actors AS actor
              ON actor.actor_ref = event.actor_ref
            ORDER BY event.world_event_ref
            """
        )
    ).mappings()
    for row in rows:
        initial_status = "SCHEDULED" if row["sealed_outcome_json"] else "SETTLED"
        initial_evidence: list[dict[str, Any]] = []
        if initial_status == "SETTLED":
            evidence_rows = connection.execute(
                sa.text(
                    """
                    SELECT evidence_ref, committed_at_tick, evidence_hash
                    FROM world.event_evidence
                    WHERE world_event_ref = :event_ref
                    ORDER BY evidence_ref
                    """
                ),
                {"event_ref": row["world_event_ref"]},
            ).mappings()
            initial_evidence = [
                {
                    "evidence_ref": evidence["evidence_ref"],
                    "committed_at_tick": evidence["committed_at_tick"],
                    "evidence_hash": evidence["evidence_hash"],
                }
                for evidence in evidence_rows
            ]
        definition_payload = {
            "world_event_ref": row["world_event_ref"],
            "world_ref": row["world_ref"],
            "actor_ref": row["actor_ref"],
            "actor_case_ref": row["actor_case_ref"],
            "event_type": row["event_type"],
            "due_tick": row["due_tick"],
            "initial_status": initial_status,
            "event_payload": row["event_json"],
            "sealed_outcome": row["sealed_outcome_json"],
            "initial_evidence": initial_evidence,
        }
        definition_hash = _content_hash(definition_payload)
        manifest = {
            "admission_version": "v60.world-event-admission.001",
            "world_event_ref": row["world_event_ref"],
            "world_ref": row["world_ref"],
            "actor_ref": row["actor_ref"],
            "actor_case_ref": row["actor_case_ref"],
            "actor_kind": row["actor_kind"],
            "actor_branch": row["actor_branch"],
            "event_type": row["event_type"],
            "due_tick": row["due_tick"],
            "initial_status": initial_status,
            "event_payload_hash": _content_hash(row["event_json"]),
            "outcome_hash": row["outcome_hash"],
            "initial_evidence": initial_evidence,
            "definition_hash": definition_hash,
        }
        connection.execute(
            sa.text(
                """
                UPDATE world.events
                SET definition_hash = :definition_hash,
                    admission_manifest_json = CAST(:manifest AS jsonb),
                    admission_manifest_hash = :manifest_hash
                WHERE world_event_ref = :event_ref
                """
            ),
            {
                "event_ref": row["world_event_ref"],
                "definition_hash": definition_hash,
                "manifest": _canonical_json(manifest),
                "manifest_hash": _content_hash(manifest),
            },
        )

    op.alter_column("events", "definition_hash", nullable=False, schema="world")
    op.alter_column(
        "events",
        "admission_manifest_json",
        nullable=False,
        schema="world",
    )
    op.alter_column(
        "events",
        "admission_manifest_hash",
        nullable=False,
        schema="world",
    )
    op.create_unique_constraint(
        "uq_world_event_definition_hash",
        "events",
        ["definition_hash"],
        schema="world",
    )
    op.create_unique_constraint(
        "uq_world_event_admission_manifest_hash",
        "events",
        ["admission_manifest_hash"],
        schema="world",
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_world_event_admission_manifest_hash",
        "events",
        type_="unique",
        schema="world",
    )
    op.drop_constraint(
        "uq_world_event_definition_hash",
        "events",
        type_="unique",
        schema="world",
    )
    op.drop_column("events", "admission_manifest_hash", schema="world")
    op.drop_column("events", "admission_manifest_json", schema="world")
    op.drop_column("events", "definition_hash", schema="world")
