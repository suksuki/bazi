"""Activate the server-owned continuous world clock.

Revision ID: 0008_continuous_world_runtime
Revises: 0007_episode_runtime_metadata
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_continuous_world_runtime"
down_revision: str | None = "0007_episode_runtime_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            WITH next_epoch AS (
                SELECT world_ref,
                       current_epoch + 1 AS epoch,
                       current_tick AS start_tick
                FROM world.worlds
                FOR UPDATE
            ),
            inserted AS (
                INSERT INTO world.clock_epochs
                    (world_ref, epoch, start_tick, rate_numerator, rate_denominator)
                SELECT world_ref, epoch, start_tick, 1, 60
                FROM next_epoch
                RETURNING world_ref, epoch
            )
            UPDATE world.worlds AS world
            SET current_epoch = next_epoch.epoch,
                world_version = 'v2',
                state_json = world.state_json || jsonb_build_object(
                    'runtime_clock',
                    jsonb_build_object(
                        'mode', 'WALL_CLOCK',
                        'rate_numerator', 1,
                        'rate_denominator', 60,
                        'activated_epoch', next_epoch.epoch
                    )
                ),
                updated_at = now()
            FROM next_epoch
            JOIN inserted USING (world_ref, epoch)
            WHERE world.world_ref = next_epoch.world_ref
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DO $$
            DECLARE
                world_row record;
            BEGIN
                FOR world_row IN
                    SELECT world_ref,
                           current_epoch,
                           (state_json -> 'runtime_clock' ->> 'activated_epoch')::bigint
                               AS activated_epoch
                    FROM world.worlds
                    WHERE state_json ? 'runtime_clock'
                LOOP
                    IF world_row.current_epoch <> world_row.activated_epoch THEN
                        RAISE EXCEPTION
                            'cannot downgrade continuous clock after a later epoch';
                    END IF;
                END LOOP;
            END
            $$;

            UPDATE world.worlds
            SET current_epoch =
                    (state_json -> 'runtime_clock' ->> 'activated_epoch')::bigint - 1,
                world_version = 'v1',
                state_json = state_json - 'runtime_clock',
                updated_at = now()
            WHERE state_json ? 'runtime_clock';

            DELETE FROM world.clock_epochs AS epoch
            USING world.worlds AS world
            WHERE epoch.world_ref = world.world_ref
              AND epoch.epoch = world.current_epoch + 1
              AND epoch.rate_numerator = 1
              AND epoch.rate_denominator = 60;
            """
        )
    )
