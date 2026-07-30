from __future__ import annotations

from typing import Any

from sqlalchemy import text

from abu_v60.dream.errors import DreamConflictError, DreamStateError
from abu_v60.game import DreamCommandEnvelope, DreamCommandReceipt
from abu_v60.provenance import canonical_json, content_hash, stable_ref


class DreamRepository:
    """Owns Dream aggregate persistence and optimistic concurrency checks."""

    @staticmethod
    def create_encounter(
        *,
        connection: Any,
        account_ref: str,
        question_ref: str,
        actor_ref: str,
        tree_ref: str,
        causation_id: str,
        cutoff_tick: int,
        npc_choice_id: str,
    ) -> str:
        encounter_identity = {
            "viewer_account_ref": account_ref,
            "question_ref": question_ref,
        }
        encounter_ref = stable_ref("v60-encounter", encounter_identity)
        correlation_id = stable_ref("v60-correlation", encounter_identity)
        state = {
            "observed_organs": [],
            "question_visible": False,
            "answer_sealed": False,
            "world_settled": False,
            "revealed": False,
            "reconciled": False,
        }
        inserted = connection.execute(
            text(
                """
                INSERT INTO dream.encounters
                    (encounter_ref, viewer_account_ref, actor_ref, tree_ref,
                     question_ref, status, version, correlation_id, causation_id,
                     state_json, state_hash)
                VALUES
                    (:encounter_ref, :account_ref, :actor_ref, :tree_ref,
                     :question_ref, 'OBSERVING', 1, :correlation_id, :causation_id,
                     CAST(:state_json AS jsonb), :state_hash)
                ON CONFLICT (viewer_account_ref, question_ref) DO NOTHING
                RETURNING encounter_ref
                """
            ),
            {
                "encounter_ref": encounter_ref,
                "account_ref": account_ref,
                "actor_ref": actor_ref,
                "tree_ref": tree_ref,
                "question_ref": question_ref,
                "correlation_id": correlation_id,
                "causation_id": causation_id,
                "state_json": canonical_json(state),
                "state_hash": content_hash(state),
            },
        ).scalar_one_or_none()
        if inserted is not None:
            seal_payload = {
                "encounter_ref": encounter_ref,
                "question_ref": question_ref,
                "actor_role": "NPC",
                "actor_ref": actor_ref,
                "choice_id": npc_choice_id,
                "sealed_at_tick": cutoff_tick,
                "cutoff_tick": cutoff_tick,
                "idempotency_key": f"npc:{correlation_id}",
            }
            connection.execute(
                text(
                    """
                    INSERT INTO dream.answer_seals
                        (answer_seal_ref, encounter_ref, question_ref, actor_role,
                         actor_ref, choice_id, sealed_at_tick, cutoff_tick,
                         idempotency_key, seal_hash)
                    VALUES
                        (:seal_ref, :encounter_ref, :question_ref, 'NPC',
                         :actor_ref, :choice_id, :sealed_at_tick, :cutoff_tick,
                         :idempotency_key, :seal_hash)
                    """
                ),
                {
                    **seal_payload,
                    "seal_ref": stable_ref("v60-answer-seal", seal_payload),
                    "seal_hash": content_hash(seal_payload),
                },
            )
        return encounter_ref

    @staticmethod
    def command_replayed(
        *,
        connection: Any,
        account_ref: str,
        envelope: DreamCommandEnvelope,
    ) -> bool:
        row = (
            connection.execute(
                text(
                    """
                    SELECT command_receipt_ref, viewer_account_ref,
                           idempotency_key, command, envelope_json,
                           envelope_hash, result_encounter_ref,
                           result_version, result_status, result_state_hash,
                           receipt_hash
                    FROM dream.command_receipts
                    WHERE viewer_account_ref = :account_ref
                      AND idempotency_key = :idempotency_key
                    """
                ),
                {
                    "account_ref": account_ref,
                    "idempotency_key": envelope.idempotency_key,
                },
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return False
        receipt_payload = {
            "receipt_version": "v60.dream-command-receipt.001",
            "command_receipt_ref": row["command_receipt_ref"],
            "viewer_account_ref": row["viewer_account_ref"],
            "idempotency_key": row["idempotency_key"],
            "command": row["command"],
            "envelope": row["envelope_json"],
            "envelope_hash": row["envelope_hash"],
            "result_encounter_ref": row["result_encounter_ref"],
            "result_version": row["result_version"],
            "result_status": row["result_status"],
            "result_state_hash": row["result_state_hash"],
        }
        try:
            receipt = DreamCommandReceipt.model_validate(receipt_payload)
        except ValueError as exc:
            raise DreamStateError("dream_command_receipt_invalid") from exc
        if content_hash(receipt.model_dump(mode="json")) != row["receipt_hash"]:
            raise DreamStateError("dream_command_receipt_hash_mismatch")
        if receipt.envelope_hash != content_hash(envelope.model_dump(mode="json")):
            raise DreamConflictError("dream_command_idempotency_conflict")
        return True

    @staticmethod
    def record_command_receipt(
        *,
        connection: Any,
        account_ref: str,
        envelope: DreamCommandEnvelope,
        result_encounter_ref: str,
    ) -> None:
        result = (
            connection.execute(
                text(
                    """
                    SELECT viewer_account_ref, version, status, state_hash
                    FROM dream.encounters
                    WHERE encounter_ref = :encounter_ref
                    """
                ),
                {"encounter_ref": result_encounter_ref},
            )
            .mappings()
            .one()
        )
        if result["viewer_account_ref"] != account_ref:
            raise DreamStateError("dream_command_result_owner_mismatch")
        envelope_payload = envelope.model_dump(mode="json")
        receipt_ref = stable_ref(
            "v60-dream-command-receipt",
            {
                "viewer_account_ref": account_ref,
                "idempotency_key": envelope.idempotency_key,
            },
        )
        receipt = DreamCommandReceipt(
            receipt_version="v60.dream-command-receipt.001",
            command_receipt_ref=receipt_ref,
            viewer_account_ref=account_ref,
            idempotency_key=envelope.idempotency_key,
            command=envelope.command,
            envelope=envelope,
            envelope_hash=content_hash(envelope_payload),
            result_encounter_ref=result_encounter_ref,
            result_version=int(result["version"]),
            result_status=result["status"],
            result_state_hash=result["state_hash"],
        )
        receipt_payload = receipt.model_dump(mode="json")
        receipt_hash = content_hash(receipt_payload)
        inserted = connection.execute(
            text(
                """
                INSERT INTO dream.command_receipts
                    (command_receipt_ref, viewer_account_ref, encounter_ref,
                     idempotency_key, command, expected_version,
                     envelope_json, envelope_hash, result_encounter_ref,
                     result_version, result_status, result_state_hash,
                     receipt_hash)
                VALUES
                    (:receipt_ref, :account_ref, :encounter_ref,
                     :idempotency_key, :command, :expected_version,
                     CAST(:envelope_json AS jsonb), :envelope_hash,
                     :result_encounter_ref, :result_version, :result_status,
                     :result_state_hash, :receipt_hash)
                ON CONFLICT (viewer_account_ref, idempotency_key) DO NOTHING
                RETURNING command_receipt_ref
                """
            ),
            {
                "receipt_ref": receipt_ref,
                "account_ref": account_ref,
                "encounter_ref": envelope.encounter_ref,
                "idempotency_key": envelope.idempotency_key,
                "command": envelope.command.value,
                "expected_version": envelope.expected_version,
                "envelope_json": canonical_json(envelope_payload),
                "envelope_hash": receipt.envelope_hash,
                "result_encounter_ref": result_encounter_ref,
                "result_version": receipt.result_version,
                "result_status": receipt.result_status.value,
                "result_state_hash": receipt.result_state_hash,
                "receipt_hash": receipt_hash,
            },
        ).scalar_one_or_none()
        if inserted is not None:
            return
        existing = (
            connection.execute(
                text(
                    """
                    SELECT envelope_hash, receipt_hash
                    FROM dream.command_receipts
                    WHERE viewer_account_ref = :account_ref
                      AND idempotency_key = :idempotency_key
                    """
                ),
                {
                    "account_ref": account_ref,
                    "idempotency_key": envelope.idempotency_key,
                },
            )
            .mappings()
            .one()
        )
        if (
            existing["envelope_hash"] != receipt.envelope_hash
            or existing["receipt_hash"] != receipt_hash
        ):
            raise DreamConflictError("dream_command_idempotency_conflict")

    @staticmethod
    def current_encounter(
        connection: Any,
        *,
        account_ref: str,
        for_update: bool,
    ) -> dict[str, Any] | None:
        lock_clause = "FOR UPDATE" if for_update else ""
        # Apply the departure fence after choosing the account's latest
        # timeline tip so an older non-departed Encounter cannot resurrect.
        # Expired opportunities remain non-completed history, so status must
        # not outrank the newer current Encounter.
        row = (
            connection.execute(
                text(
                    f"""
                    WITH latest_encounter AS (
                        SELECT encounter_ref
                        FROM dream.encounters
                        WHERE viewer_account_ref = :account_ref
                        ORDER BY updated_at DESC, encounter_ref DESC
                        LIMIT 1
                    )
                    SELECT encounter.*
                    FROM dream.encounters AS encounter
                    JOIN latest_encounter AS latest
                      ON latest.encounter_ref = encounter.encounter_ref
                    WHERE COALESCE(
                            encounter.state_json ->> 'departed_to_grove',
                            'false'
                          ) <> 'true'
                    {lock_clause}
                    """
                ),
                {"account_ref": account_ref},
            )
            .mappings()
            .one_or_none()
        )
        return dict(row) if row is not None else None

    def locked_encounter(
        self,
        connection: Any,
        *,
        account_ref: str,
    ) -> dict[str, Any]:
        row = self.current_encounter(
            connection,
            account_ref=account_ref,
            for_update=True,
        )
        if row is None:
            raise DreamStateError("encounter_not_created")
        return row

    @staticmethod
    def completed_encounter_count(connection: Any, *, account_ref: str) -> int:
        return int(
            connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM dream.encounters
                    WHERE viewer_account_ref = :account_ref
                      AND status = 'COMPLETED'
                      AND state_json @> '{"reconciled": true}'::jsonb
                    """
                ),
                {"account_ref": account_ref},
            ).scalar_one()
        )

    @staticmethod
    def write_encounter_state(
        *,
        connection: Any,
        encounter: dict[str, Any],
        status: str,
        state: dict[str, Any],
    ) -> None:
        result = connection.execute(
            text(
                """
                UPDATE dream.encounters
                SET status = :status,
                    version = version + 1,
                    state_json = CAST(:state_json AS jsonb),
                    state_hash = :state_hash,
                    updated_at = now()
                WHERE encounter_ref = :encounter_ref
                  AND version = :expected_version
                """
            ),
            {
                "status": status,
                "state_json": canonical_json(state),
                "state_hash": content_hash(state),
                "encounter_ref": encounter["encounter_ref"],
                "expected_version": encounter["version"],
            },
        )
        if result.rowcount != 1:
            raise DreamConflictError("encounter_version_conflict")

    @staticmethod
    def write_tree_state(
        *,
        connection: Any,
        tree_ref: str,
        state: str,
        target_version: int,
    ) -> None:
        tree = (
            connection.execute(
                text(
                    """
                    SELECT tree_version, state, organs_json
                    FROM dream.life_trees
                    WHERE tree_ref = :tree_ref
                    FOR UPDATE
                    """
                ),
                {"tree_ref": tree_ref},
            )
            .mappings()
            .one()
        )
        current_version = int(tree["tree_version"])
        if current_version > target_version:
            return
        if current_version == target_version:
            if tree["state"] != state:
                raise DreamConflictError("tree_state_version_identity_conflict")
            return
        if current_version + 1 != target_version:
            raise DreamConflictError("tree_state_version_gap")
        projection = {
            "tree_ref": tree_ref,
            "tree_version": target_version,
            "state": state,
            "organs": tree["organs_json"],
        }
        result = connection.execute(
            text(
                """
                UPDATE dream.life_trees
                SET state = :state,
                    tree_version = :tree_version,
                    projection_hash = :projection_hash,
                    updated_at = now()
                WHERE tree_ref = :tree_ref
                  AND tree_version = :expected_version
                """
            ),
            {
                "state": state,
                "tree_version": target_version,
                "tree_ref": tree_ref,
                "expected_version": current_version,
                "projection_hash": content_hash(projection),
            },
        )
        if result.rowcount != 1:
            raise DreamConflictError("tree_version_conflict")
