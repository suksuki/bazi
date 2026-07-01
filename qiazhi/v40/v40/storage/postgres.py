from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

from v40.contracts.evaluation import (
    EvaluationBatchSummary,
    EvaluationCaseSpec,
    EvaluationRunResult,
    ReleaseGateResult,
    ReleaseReadinessSummary,
    ShadowCompareResult,
    TrainingExampleReplayResult,
    TrainingReplayBatchSummary,
)
from v40.contracts.output import ConversationTurn
from v40.contracts.review import (
    ConsentGrant,
    PractitionerReviewQueueItem,
    PractitionerReviewRequest,
    PractitionerReviewResult,
    ReviewRequestStatus,
)
from v40.contracts.runtime import RuntimeResult
from v40.contracts.training import (
    GlobalWeightVersion,
    LocalOverlay,
    TrainablePolicyRegistry,
    TrainingExampleV2,
    TrainingImpactDiff,
    TrainingLabelEvent,
    WeightActivationExecution,
    WeightActivationReview,
)
from v40.storage.config import V40DatabaseConfig, resolve_v40_database_config


class V40PostgresRepository:
    def __init__(self, config: V40DatabaseConfig) -> None:
        self._config = config

    @classmethod
    def from_env(cls) -> "V40PostgresRepository":
        config = resolve_v40_database_config()
        if config is None:
            raise RuntimeError("V40_DATABASE_URL is not configured")
        return cls(config)

    def save_runtime(self, runtime: RuntimeResult) -> None:
        payload = runtime.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_runtime_records (reading_id, version, runtime_json, updated_at)
                    VALUES (%s, %s, %s::jsonb, now())
                    ON CONFLICT (reading_id)
                    DO UPDATE SET
                        version = EXCLUDED.version,
                        runtime_json = EXCLUDED.runtime_json,
                        updated_at = now()
                    """,
                    (runtime.reading_id, runtime.version, json.dumps(payload, ensure_ascii=False)),
                )

    def save_shadow_compare(self, compare: ShadowCompareResult) -> None:
        payload = compare.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_shadow_compare_runs (
                        compare_id,
                        source_export_id,
                        v40_reading_id,
                        version,
                        compare_json,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb, now())
                    ON CONFLICT (compare_id)
                    DO UPDATE SET
                        source_export_id = EXCLUDED.source_export_id,
                        v40_reading_id = EXCLUDED.v40_reading_id,
                        version = EXCLUDED.version,
                        compare_json = EXCLUDED.compare_json,
                        created_at = now()
                    """,
                    (
                        compare.compare_id,
                        compare.v30_export_id,
                        compare.v40_reading_id,
                        compare.version,
                        json.dumps(payload, ensure_ascii=False),
                    ),
                )

    def list_shadow_compare_runs(self, *, limit: int = 20) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT
                        compare_id,
                        source_export_id,
                        v40_reading_id,
                        version,
                        compare_json,
                        created_at
                    FROM v40_shadow_compare_runs
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (bounded_limit,),
                )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_evaluation_case(self, case_spec: EvaluationCaseSpec) -> None:
        payload = case_spec.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_evaluation_cases (case_id, version, case_type, case_json, updated_at)
                    VALUES (%s, %s, %s, %s::jsonb, now())
                    ON CONFLICT (case_id)
                    DO UPDATE SET
                        version = EXCLUDED.version,
                        case_type = EXCLUDED.case_type,
                        case_json = EXCLUDED.case_json,
                        updated_at = now()
                    """,
                    (
                        case_spec.case_id,
                        case_spec.version,
                        case_spec.case_type.value,
                        json.dumps(payload, ensure_ascii=False),
                    ),
                )

    def list_evaluation_cases(self, *, limit: int = 20) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT case_id, version, case_type, case_json, created_at, updated_at
                    FROM v40_evaluation_cases
                    ORDER BY updated_at DESC, created_at DESC
                    LIMIT %s
                    """,
                    (bounded_limit,),
                )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_evaluation_run(self, run: EvaluationRunResult) -> None:
        payload = run.model_dump(mode="json")
        metric_payload = run.metric_summary.model_dump(mode="json")
        release_gate_id = run.release_gate.gate_id if run.release_gate else ""
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_evaluation_runs (
                        run_id,
                        case_id,
                        reading_id,
                        version,
                        status,
                        metric_json,
                        run_json,
                        release_gate_id,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, now())
                    ON CONFLICT (run_id)
                    DO UPDATE SET
                        case_id = EXCLUDED.case_id,
                        reading_id = EXCLUDED.reading_id,
                        version = EXCLUDED.version,
                        status = EXCLUDED.status,
                        metric_json = EXCLUDED.metric_json,
                        run_json = EXCLUDED.run_json,
                        release_gate_id = EXCLUDED.release_gate_id,
                        updated_at = now()
                    """,
                    (
                        run.run_id,
                        run.case_spec.case_id,
                        run.reading_id,
                        run.version,
                        run.status.value,
                        json.dumps(metric_payload, ensure_ascii=False),
                        json.dumps(payload, ensure_ascii=False),
                        release_gate_id,
                    ),
                )

    def list_evaluation_runs(self, *, limit: int = 20) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT
                        run_id,
                        case_id,
                        reading_id,
                        version,
                        status,
                        metric_json,
                        run_json,
                        release_gate_id,
                        created_at,
                        updated_at
                    FROM v40_evaluation_runs
                    ORDER BY updated_at DESC, created_at DESC
                    LIMIT %s
                    """,
                    (bounded_limit,),
                )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_evaluation_batch_summary(self, summary: EvaluationBatchSummary) -> None:
        payload = summary.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_evaluation_batches (
                        batch_id,
                        candidate_version,
                        version,
                        summary_json,
                        recommendation,
                        production_write_allowed,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s::jsonb, %s, %s, now())
                    ON CONFLICT (batch_id)
                    DO UPDATE SET
                        candidate_version = EXCLUDED.candidate_version,
                        version = EXCLUDED.version,
                        summary_json = EXCLUDED.summary_json,
                        recommendation = EXCLUDED.recommendation,
                        production_write_allowed = EXCLUDED.production_write_allowed,
                        updated_at = now()
                    """,
                    (
                        summary.batch_id,
                        summary.candidate_version,
                        summary.version,
                        json.dumps(payload, ensure_ascii=False),
                        summary.recommendation.value,
                        summary.production_write_allowed,
                    ),
                )

    def list_evaluation_batches(self, *, limit: int = 20) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT
                        batch_id,
                        candidate_version,
                        version,
                        summary_json,
                        recommendation,
                        production_write_allowed,
                        created_at,
                        updated_at
                    FROM v40_evaluation_batches
                    ORDER BY updated_at DESC, created_at DESC
                    LIMIT %s
                    """,
                    (bounded_limit,),
                )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_training_label_event(self, event: TrainingLabelEvent) -> None:
        payload = event.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_training_label_events (
                        event_id,
                        reading_id,
                        version,
                        label_json,
                        local_only,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s::jsonb, %s, now())
                    ON CONFLICT (event_id)
                    DO UPDATE SET
                        reading_id = EXCLUDED.reading_id,
                        version = EXCLUDED.version,
                        label_json = EXCLUDED.label_json,
                        local_only = EXCLUDED.local_only,
                        created_at = now()
                    """,
                    (
                        event.event_id,
                        event.reading_id,
                        event.version,
                        json.dumps(payload, ensure_ascii=False),
                        event.local_only,
                    ),
                )

    def list_training_label_events(self, *, limit: int = 20, reading_id: str = "") -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                if reading_id:
                    cur.execute(
                        """
                        SELECT event_id, reading_id, version, label_json, local_only, created_at
                        FROM v40_training_label_events
                        WHERE reading_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (reading_id, bounded_limit),
                    )
                else:
                    cur.execute(
                        """
                        SELECT event_id, reading_id, version, label_json, local_only, created_at
                        FROM v40_training_label_events
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (bounded_limit,),
                    )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_local_overlay(self, overlay: LocalOverlay) -> None:
        payload = overlay.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_local_overlays (
                        overlay_id,
                        reading_id,
                        version,
                        overlay_json,
                        expires_after_reading,
                        global_update_allowed,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s::jsonb, %s, %s, now())
                    ON CONFLICT (overlay_id)
                    DO UPDATE SET
                        reading_id = EXCLUDED.reading_id,
                        version = EXCLUDED.version,
                        overlay_json = EXCLUDED.overlay_json,
                        expires_after_reading = EXCLUDED.expires_after_reading,
                        global_update_allowed = EXCLUDED.global_update_allowed,
                        updated_at = now()
                    """,
                    (
                        overlay.overlay_id,
                        overlay.reading_id,
                        overlay.version,
                        json.dumps(payload, ensure_ascii=False),
                        overlay.expires_after_reading,
                        overlay.global_update_allowed,
                    ),
                )

    def list_local_overlays(self, *, limit: int = 20, reading_id: str = "") -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                if reading_id:
                    cur.execute(
                        """
                        SELECT
                            overlay_id,
                            reading_id,
                            version,
                            overlay_json,
                            expires_after_reading,
                            global_update_allowed,
                            created_at,
                            updated_at
                        FROM v40_local_overlays
                        WHERE reading_id = %s
                        ORDER BY updated_at DESC, created_at DESC
                        LIMIT %s
                        """,
                        (reading_id, bounded_limit),
                    )
                else:
                    cur.execute(
                        """
                        SELECT
                            overlay_id,
                            reading_id,
                            version,
                            overlay_json,
                            expires_after_reading,
                            global_update_allowed,
                            created_at,
                            updated_at
                        FROM v40_local_overlays
                        ORDER BY updated_at DESC, created_at DESC
                        LIMIT %s
                        """,
                        (bounded_limit,),
                    )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_training_example(self, example: TrainingExampleV2) -> None:
        payload = example.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_training_examples (
                        example_id,
                        reading_id,
                        topic,
                        version,
                        example_json,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb, now())
                    ON CONFLICT (example_id)
                    DO UPDATE SET
                        reading_id = EXCLUDED.reading_id,
                        topic = EXCLUDED.topic,
                        version = EXCLUDED.version,
                        example_json = EXCLUDED.example_json,
                        updated_at = now()
                    """,
                    (
                        example.example_id,
                        example.reading_id,
                        example.topic.value,
                        example.version,
                        json.dumps(payload, ensure_ascii=False),
                    ),
                )

    def list_training_examples(self, *, limit: int = 20, reading_id: str = "") -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                if reading_id:
                    cur.execute(
                        """
                        SELECT
                            example_id,
                            reading_id,
                            topic,
                            version,
                            example_json,
                            created_at,
                            updated_at
                        FROM v40_training_examples
                        WHERE reading_id = %s
                        ORDER BY updated_at DESC, created_at DESC
                        LIMIT %s
                        """,
                        (reading_id, bounded_limit),
                    )
                else:
                    cur.execute(
                        """
                        SELECT
                            example_id,
                            reading_id,
                            topic,
                            version,
                            example_json,
                            created_at,
                            updated_at
                        FROM v40_training_examples
                        ORDER BY updated_at DESC, created_at DESC
                        LIMIT %s
                        """,
                        (bounded_limit,),
                    )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_training_example_replay(self, replay: TrainingExampleReplayResult) -> None:
        payload = replay.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_training_example_replays (
                        replay_id,
                        example_id,
                        reading_id,
                        candidate_version,
                        version,
                        replay_json,
                        status,
                        recommendation,
                        production_write_allowed,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, now())
                    ON CONFLICT (replay_id)
                    DO UPDATE SET
                        example_id = EXCLUDED.example_id,
                        reading_id = EXCLUDED.reading_id,
                        candidate_version = EXCLUDED.candidate_version,
                        version = EXCLUDED.version,
                        replay_json = EXCLUDED.replay_json,
                        status = EXCLUDED.status,
                        recommendation = EXCLUDED.recommendation,
                        production_write_allowed = EXCLUDED.production_write_allowed,
                        created_at = now()
                    """,
                    (
                        replay.replay_id,
                        replay.example_id,
                        replay.reading_id,
                        replay.candidate_version,
                        replay.version,
                        json.dumps(payload, ensure_ascii=False),
                        replay.status.value,
                        replay.recommendation.value,
                        replay.production_write_allowed,
                    ),
                )

    def list_training_example_replays(self, *, limit: int = 20, reading_id: str = "") -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                if reading_id:
                    cur.execute(
                        """
                        SELECT
                            replay_id,
                            example_id,
                            reading_id,
                            candidate_version,
                            version,
                            replay_json,
                            status,
                            recommendation,
                            production_write_allowed,
                            created_at
                        FROM v40_training_example_replays
                        WHERE reading_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (reading_id, bounded_limit),
                    )
                else:
                    cur.execute(
                        """
                        SELECT
                            replay_id,
                            example_id,
                            reading_id,
                            candidate_version,
                            version,
                            replay_json,
                            status,
                            recommendation,
                            production_write_allowed,
                            created_at
                        FROM v40_training_example_replays
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (bounded_limit,),
                    )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_training_replay_batch_summary(self, summary: TrainingReplayBatchSummary) -> None:
        payload = summary.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_training_replay_batches (
                        batch_id,
                        candidate_version,
                        version,
                        summary_json,
                        recommendation,
                        production_write_allowed,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s::jsonb, %s, %s, now())
                    ON CONFLICT (batch_id)
                    DO UPDATE SET
                        candidate_version = EXCLUDED.candidate_version,
                        version = EXCLUDED.version,
                        summary_json = EXCLUDED.summary_json,
                        recommendation = EXCLUDED.recommendation,
                        production_write_allowed = EXCLUDED.production_write_allowed,
                        updated_at = now()
                    """,
                    (
                        summary.batch_id,
                        summary.candidate_version,
                        summary.version,
                        json.dumps(payload, ensure_ascii=False),
                        summary.recommendation.value,
                        summary.production_write_allowed,
                    ),
                )

    def list_training_replay_batches(self, *, limit: int = 20) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT
                        batch_id,
                        candidate_version,
                        version,
                        summary_json,
                        recommendation,
                        production_write_allowed,
                        created_at,
                        updated_at
                    FROM v40_training_replay_batches
                    ORDER BY updated_at DESC, created_at DESC
                    LIMIT %s
                    """,
                    (bounded_limit,),
                )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_conversation_turn(self, turn: ConversationTurn) -> None:
        payload = turn.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_conversation_turns (
                        turn_id,
                        reading_id,
                        version,
                        topic,
                        accepted,
                        turn_json,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb, now())
                    ON CONFLICT (turn_id)
                    DO UPDATE SET
                        reading_id = EXCLUDED.reading_id,
                        version = EXCLUDED.version,
                        topic = EXCLUDED.topic,
                        accepted = EXCLUDED.accepted,
                        turn_json = EXCLUDED.turn_json,
                        updated_at = now()
                    """,
                    (
                        turn.turn_id,
                        turn.reading_id,
                        turn.version,
                        turn.topic.value,
                        turn.accepted,
                        json.dumps(payload, ensure_ascii=False),
                    ),
                )

    def list_conversation_turns(self, *, limit: int = 20, reading_id: str = "") -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                if reading_id:
                    cur.execute(
                        """
                        SELECT turn_id, reading_id, version, topic, accepted, turn_json, created_at, updated_at
                        FROM v40_conversation_turns
                        WHERE reading_id = %s
                        ORDER BY updated_at DESC, created_at DESC
                        LIMIT %s
                        """,
                        (reading_id, bounded_limit),
                    )
                else:
                    cur.execute(
                        """
                        SELECT turn_id, reading_id, version, topic, accepted, turn_json, created_at, updated_at
                        FROM v40_conversation_turns
                        ORDER BY updated_at DESC, created_at DESC
                        LIMIT %s
                        """,
                        (bounded_limit,),
                    )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_consent_grant(self, grant: ConsentGrant) -> None:
        payload = grant.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_consent_grants (
                        grant_id,
                        reading_id,
                        version,
                        grant_json,
                        granted_by_role,
                        allow_practitioner_review,
                        allow_training_use,
                        revoked,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s, %s, now())
                    ON CONFLICT (grant_id)
                    DO UPDATE SET
                        reading_id = EXCLUDED.reading_id,
                        version = EXCLUDED.version,
                        grant_json = EXCLUDED.grant_json,
                        granted_by_role = EXCLUDED.granted_by_role,
                        allow_practitioner_review = EXCLUDED.allow_practitioner_review,
                        allow_training_use = EXCLUDED.allow_training_use,
                        revoked = EXCLUDED.revoked,
                        updated_at = now()
                    """,
                    (
                        grant.grant_id,
                        grant.reading_id,
                        grant.version,
                        json.dumps(payload, ensure_ascii=False),
                        grant.granted_by_role,
                        grant.allow_practitioner_review,
                        grant.allow_training_use,
                        grant.revoked,
                    ),
                )

    def list_consent_grants(self, *, limit: int = 20, reading_id: str = "") -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                if reading_id:
                    cur.execute(
                        """
                        SELECT
                            grant_id,
                            reading_id,
                            version,
                            grant_json,
                            granted_by_role,
                            allow_practitioner_review,
                            allow_training_use,
                            revoked,
                            created_at,
                            updated_at
                        FROM v40_consent_grants
                        WHERE reading_id = %s
                        ORDER BY updated_at DESC, created_at DESC
                        LIMIT %s
                        """,
                        (reading_id, bounded_limit),
                    )
                else:
                    cur.execute(
                        """
                        SELECT
                            grant_id,
                            reading_id,
                            version,
                            grant_json,
                            granted_by_role,
                            allow_practitioner_review,
                            allow_training_use,
                            revoked,
                            created_at,
                            updated_at
                        FROM v40_consent_grants
                        ORDER BY updated_at DESC, created_at DESC
                        LIMIT %s
                        """,
                        (bounded_limit,),
                    )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_practitioner_review_request(self, request: PractitionerReviewRequest) -> None:
        payload = request.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_practitioner_review_requests (
                        review_request_id,
                        consent_grant_id,
                        reading_id,
                        version,
                        topic,
                        status,
                        request_json,
                        assigned_to_practitioner_ref,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, now())
                    ON CONFLICT (review_request_id)
                    DO UPDATE SET
                        consent_grant_id = EXCLUDED.consent_grant_id,
                        reading_id = EXCLUDED.reading_id,
                        version = EXCLUDED.version,
                        topic = EXCLUDED.topic,
                        status = EXCLUDED.status,
                        request_json = EXCLUDED.request_json,
                        assigned_to_practitioner_ref = EXCLUDED.assigned_to_practitioner_ref,
                        updated_at = now()
                    """,
                    (
                        request.review_request_id,
                        request.consent_grant_id,
                        request.reading_id,
                        request.version,
                        request.requested_topic.value,
                        request.status.value,
                        json.dumps(payload, ensure_ascii=False),
                        request.assigned_to_practitioner_ref,
                    ),
                )

    def list_practitioner_review_requests(self, *, limit: int = 20, reading_id: str = "") -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                if reading_id:
                    cur.execute(
                        """
                        SELECT
                            review_request_id,
                            consent_grant_id,
                            reading_id,
                            version,
                            topic,
                            status,
                            request_json,
                            assigned_to_practitioner_ref,
                            created_at,
                            updated_at
                        FROM v40_practitioner_review_requests
                        WHERE reading_id = %s
                        ORDER BY updated_at DESC, created_at DESC
                        LIMIT %s
                        """,
                        (reading_id, bounded_limit),
                    )
                else:
                    cur.execute(
                        """
                        SELECT
                            review_request_id,
                            consent_grant_id,
                            reading_id,
                            version,
                            topic,
                            status,
                            request_json,
                            assigned_to_practitioner_ref,
                            created_at,
                            updated_at
                        FROM v40_practitioner_review_requests
                        ORDER BY updated_at DESC, created_at DESC
                        LIMIT %s
                        """,
                        (bounded_limit,),
                    )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_practitioner_review_queue_item(self, item: PractitionerReviewQueueItem) -> None:
        payload = item.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_practitioner_review_queue (
                        queue_item_id,
                        review_request_id,
                        reading_id,
                        version,
                        topic,
                        status,
                        queue_json,
                        assigned_to_practitioner_ref,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, now())
                    ON CONFLICT (queue_item_id)
                    DO UPDATE SET
                        review_request_id = EXCLUDED.review_request_id,
                        reading_id = EXCLUDED.reading_id,
                        version = EXCLUDED.version,
                        topic = EXCLUDED.topic,
                        status = EXCLUDED.status,
                        queue_json = EXCLUDED.queue_json,
                        assigned_to_practitioner_ref = EXCLUDED.assigned_to_practitioner_ref,
                        updated_at = now()
                    """,
                    (
                        item.queue_item_id,
                        item.review_request_id,
                        item.reading_id,
                        item.version,
                        item.topic.value,
                        item.status.value,
                        json.dumps(payload, ensure_ascii=False),
                        item.assigned_to_practitioner_ref,
                    ),
                )

    def list_practitioner_review_queue(
        self,
        *,
        limit: int = 20,
        status: ReviewRequestStatus | str | None = None,
        assigned_to_practitioner_ref: str = "",
    ) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        status_value = status.value if isinstance(status, ReviewRequestStatus) else str(status or "").strip()
        assignee = assigned_to_practitioner_ref.strip()
        filters = []
        params: list[Any] = []
        if status_value:
            filters.append("status = %s")
            params.append(status_value)
        if assignee:
            filters.append("assigned_to_practitioner_ref = %s")
            params.append(assignee)
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        params.append(bounded_limit)
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    SELECT
                        queue_item_id,
                        review_request_id,
                        reading_id,
                        version,
                        topic,
                        status,
                        queue_json,
                        assigned_to_practitioner_ref,
                        created_at,
                        updated_at
                    FROM v40_practitioner_review_queue
                    {where}
                    ORDER BY updated_at DESC, created_at DESC
                    LIMIT %s
                    """,
                    tuple(params),
                )
                return [_serialize_row(row) for row in cur.fetchall()]

    def assign_practitioner_review_queue_item(
        self,
        *,
        queue_item_id: str,
        practitioner_ref: str,
    ) -> dict[str, Any] | None:
        clean_ref = practitioner_ref.strip()
        if not clean_ref:
            raise RuntimeError("Practitioner assignment requires practitioner_ref")
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    UPDATE v40_practitioner_review_queue
                    SET status = %s,
                        assigned_to_practitioner_ref = %s,
                        queue_json = jsonb_set(
                            jsonb_set(queue_json, '{status}', to_jsonb(%s::text), true),
                            '{assigned_to_practitioner_ref}',
                            to_jsonb(%s::text),
                            true
                        ),
                        updated_at = now()
                    WHERE queue_item_id = %s
                    RETURNING
                        queue_item_id,
                        review_request_id,
                        reading_id,
                        version,
                        topic,
                        status,
                        queue_json,
                        assigned_to_practitioner_ref,
                        created_at,
                        updated_at
                    """,
                    (
                        ReviewRequestStatus.ASSIGNED.value,
                        clean_ref,
                        ReviewRequestStatus.ASSIGNED.value,
                        clean_ref,
                        queue_item_id,
                    ),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                review_request_id = row["review_request_id"]
                cur.execute(
                    """
                    UPDATE v40_practitioner_review_requests
                    SET status = %s,
                        assigned_to_practitioner_ref = %s,
                        request_json = jsonb_set(
                            jsonb_set(request_json, '{status}', to_jsonb(%s::text), true),
                            '{assigned_to_practitioner_ref}',
                            to_jsonb(%s::text),
                            true
                        ),
                        updated_at = now()
                    WHERE review_request_id = %s
                    """,
                    (
                        ReviewRequestStatus.ASSIGNED.value,
                        clean_ref,
                        ReviewRequestStatus.ASSIGNED.value,
                        clean_ref,
                        review_request_id,
                    ),
                )
                return _serialize_row(row)

    def save_practitioner_review_result(self, result: PractitionerReviewResult) -> None:
        payload = result.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_practitioner_review_results (
                        result_id,
                        review_request_id,
                        reading_id,
                        version,
                        decision,
                        reviewer_role,
                        result_json,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, now())
                    ON CONFLICT (result_id)
                    DO UPDATE SET
                        review_request_id = EXCLUDED.review_request_id,
                        reading_id = EXCLUDED.reading_id,
                        version = EXCLUDED.version,
                        decision = EXCLUDED.decision,
                        reviewer_role = EXCLUDED.reviewer_role,
                        result_json = EXCLUDED.result_json,
                        updated_at = now()
                    """,
                    (
                        result.result_id,
                        result.review_request_id,
                        result.reading_id,
                        result.version,
                        result.decision.value,
                        result.reviewer_role,
                        json.dumps(payload, ensure_ascii=False),
                    ),
                )
                cur.execute(
                    """
                    UPDATE v40_practitioner_review_queue
                    SET status = %s,
                        queue_json = jsonb_set(queue_json, '{status}', to_jsonb(%s::text), true),
                        updated_at = now()
                    WHERE review_request_id = %s
                    """,
                    (ReviewRequestStatus.COMPLETED.value, ReviewRequestStatus.COMPLETED.value, result.review_request_id),
                )
                cur.execute(
                    """
                    UPDATE v40_practitioner_review_requests
                    SET status = %s,
                        request_json = jsonb_set(request_json, '{status}', to_jsonb(%s::text), true),
                        updated_at = now()
                    WHERE review_request_id = %s
                    """,
                    (ReviewRequestStatus.COMPLETED.value, ReviewRequestStatus.COMPLETED.value, result.review_request_id),
                )
                for event in result.training_label_events:
                    event_payload = event.model_dump(mode="json")
                    cur.execute(
                        """
                        INSERT INTO v40_training_label_events (
                            event_id,
                            reading_id,
                            version,
                            label_json,
                            local_only,
                            created_at
                        )
                        VALUES (%s, %s, %s, %s::jsonb, %s, now())
                        ON CONFLICT (event_id)
                        DO UPDATE SET
                            reading_id = EXCLUDED.reading_id,
                            version = EXCLUDED.version,
                            label_json = EXCLUDED.label_json,
                            local_only = EXCLUDED.local_only,
                            created_at = now()
                        """,
                        (
                            event.event_id,
                            event.reading_id,
                            event.version,
                            json.dumps(event_payload, ensure_ascii=False),
                            event.local_only,
                        ),
                    )

    def list_practitioner_review_results(
        self,
        *,
        limit: int = 20,
        reading_id: str = "",
        review_request_id: str = "",
    ) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        filters = []
        params: list[Any] = []
        if reading_id:
            filters.append("reading_id = %s")
            params.append(reading_id)
        if review_request_id:
            filters.append("review_request_id = %s")
            params.append(review_request_id)
        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        params.append(bounded_limit)
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    f"""
                    SELECT
                        result_id,
                        review_request_id,
                        reading_id,
                        version,
                        decision,
                        reviewer_role,
                        result_json,
                        created_at,
                        updated_at
                    FROM v40_practitioner_review_results
                    {where}
                    ORDER BY updated_at DESC, created_at DESC
                    LIMIT %s
                    """,
                    tuple(params),
                )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_training_impact_diff(self, diff: TrainingImpactDiff) -> None:
        payload = diff.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_training_impact_diffs (
                        training_run_id,
                        base_version,
                        candidate_version,
                        version,
                        diff_json,
                        recommendation,
                        production_write_allowed,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, now())
                    ON CONFLICT (training_run_id)
                    DO UPDATE SET
                        base_version = EXCLUDED.base_version,
                        candidate_version = EXCLUDED.candidate_version,
                        version = EXCLUDED.version,
                        diff_json = EXCLUDED.diff_json,
                        recommendation = EXCLUDED.recommendation,
                        production_write_allowed = EXCLUDED.production_write_allowed,
                        created_at = now()
                    """,
                    (
                        diff.training_run_id,
                        diff.base_version,
                        diff.candidate_version,
                        diff.version,
                        json.dumps(payload, ensure_ascii=False),
                        diff.release_recommendation.value,
                        diff.production_write_allowed,
                    ),
                )

    def list_training_impact_diffs(self, *, limit: int = 20) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT
                        training_run_id,
                        base_version,
                        candidate_version,
                        version,
                        diff_json,
                        recommendation,
                        production_write_allowed,
                        created_at
                    FROM v40_training_impact_diffs
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (bounded_limit,),
                )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_trainable_policy_registry(self, registry: TrainablePolicyRegistry) -> None:
        payload = registry.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                if registry.active:
                    cur.execute(
                        """
                        UPDATE v40_trainable_policy_registries
                        SET active = false,
                            registry_json = jsonb_set(registry_json, '{active}', 'false'::jsonb, true),
                            updated_at = now()
                        WHERE active = true
                          AND registry_id <> %s
                        """,
                        (registry.registry_id,),
                    )
                cur.execute(
                    """
                    INSERT INTO v40_trainable_policy_registries (
                        registry_id,
                        active_policy_version,
                        candidate_policy_version,
                        version,
                        registry_json,
                        unit_count,
                        active,
                        previous_registry_id,
                        previous_policy_version,
                        activated_by_training_run_id,
                        rollback_available,
                        activated_at,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s, CASE WHEN %s THEN now() ELSE NULL END, now())
                    ON CONFLICT (registry_id)
                    DO UPDATE SET
                        active_policy_version = EXCLUDED.active_policy_version,
                        candidate_policy_version = EXCLUDED.candidate_policy_version,
                        version = EXCLUDED.version,
                        registry_json = EXCLUDED.registry_json,
                        unit_count = EXCLUDED.unit_count,
                        active = EXCLUDED.active,
                        previous_registry_id = EXCLUDED.previous_registry_id,
                        previous_policy_version = EXCLUDED.previous_policy_version,
                        activated_by_training_run_id = EXCLUDED.activated_by_training_run_id,
                        rollback_available = EXCLUDED.rollback_available,
                        activated_at = COALESCE(EXCLUDED.activated_at, v40_trainable_policy_registries.activated_at),
                        updated_at = now()
                    """,
                    (
                        registry.registry_id,
                        registry.active_policy_version,
                        registry.candidate_policy_version,
                        registry.version,
                        json.dumps(payload, ensure_ascii=False),
                        len(registry.units),
                        registry.active,
                        registry.previous_registry_id,
                        registry.previous_policy_version,
                        registry.activated_by_training_run_id,
                        registry.rollback_available,
                        registry.active,
                    ),
                )

    def get_active_trainable_policy_registry(self) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT
                        registry_id,
                        active_policy_version,
                        candidate_policy_version,
                        version,
                        registry_json,
                        unit_count,
                        active,
                        previous_registry_id,
                        previous_policy_version,
                        activated_by_training_run_id,
                        rollback_available,
                        activated_at,
                        created_at,
                        updated_at
                    FROM v40_trainable_policy_registries
                    WHERE active = true
                    ORDER BY activated_at DESC NULLS LAST, updated_at DESC, created_at DESC
                    LIMIT 1
                    """
                )
                row = cur.fetchone()
                return _serialize_row(row) if row else None

    def list_trainable_policy_registries(self, *, limit: int = 20) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT
                        registry_id,
                        active_policy_version,
                        candidate_policy_version,
                        version,
                        registry_json,
                        unit_count,
                        active,
                        previous_registry_id,
                        previous_policy_version,
                        activated_by_training_run_id,
                        rollback_available,
                        activated_at,
                        created_at,
                        updated_at
                    FROM v40_trainable_policy_registries
                    ORDER BY active DESC, updated_at DESC, created_at DESC
                    LIMIT %s
                    """,
                    (bounded_limit,),
                )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_global_weight_version(self, weight_version: GlobalWeightVersion) -> None:
        payload = weight_version.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_global_weight_versions (
                        weight_version_id,
                        source_training_run_id,
                        release_gate_id,
                        version,
                        weight_json,
                        active,
                        rollback_version_id,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, now())
                    ON CONFLICT (weight_version_id)
                    DO UPDATE SET
                        source_training_run_id = EXCLUDED.source_training_run_id,
                        release_gate_id = EXCLUDED.release_gate_id,
                        version = EXCLUDED.version,
                        weight_json = EXCLUDED.weight_json,
                        active = EXCLUDED.active,
                        rollback_version_id = EXCLUDED.rollback_version_id,
                        updated_at = now()
                    """,
                    (
                        weight_version.weight_version_id,
                        weight_version.source_training_run_id,
                        weight_version.release_gate_id,
                        weight_version.version,
                        json.dumps(payload, ensure_ascii=False),
                        weight_version.active,
                        weight_version.rollback_version_id,
                    ),
                )

    def list_global_weight_versions(self, *, limit: int = 20) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT
                        weight_version_id,
                        source_training_run_id,
                        release_gate_id,
                        version,
                        weight_json,
                        active,
                        rollback_version_id,
                        created_at,
                        updated_at
                    FROM v40_global_weight_versions
                    ORDER BY updated_at DESC, created_at DESC
                    LIMIT %s
                    """,
                    (bounded_limit,),
                )
                return [_serialize_row(row) for row in cur.fetchall()]

    def activate_global_weight_version(self, execution: WeightActivationExecution) -> WeightActivationExecution:
        payload = execution.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT weight_version_id
                    FROM v40_global_weight_versions
                    WHERE active = true
                    ORDER BY updated_at DESC
                    """
                )
                deactivated_ids = [
                    row["weight_version_id"]
                    for row in cur.fetchall()
                    if row["weight_version_id"] != execution.weight_version_id
                ]
                cur.execute(
                    """
                    SELECT weight_json
                    FROM v40_global_weight_versions
                    WHERE weight_version_id = %s
                    FOR UPDATE
                    """,
                    (execution.weight_version_id,),
                )
                target = cur.fetchone()
                if target is None:
                    raise RuntimeError("Target V40 weight version does not exist")
                target_payload = dict(target["weight_json"])
                target_payload["active"] = True
                target_payload["rollback_version_id"] = execution.rollback_version_id
                cur.execute("UPDATE v40_global_weight_versions SET active = false, updated_at = now() WHERE active = true")
                cur.execute(
                    """
                    UPDATE v40_global_weight_versions
                    SET active = true,
                        rollback_version_id = %s,
                        weight_json = %s::jsonb,
                        updated_at = now()
                    WHERE weight_version_id = %s
                    """,
                    (
                        execution.rollback_version_id,
                        json.dumps(target_payload, ensure_ascii=False),
                        execution.weight_version_id,
                    ),
                )
                applied = execution.model_copy(update={"deactivated_weight_ids": deactivated_ids})
                applied_payload = applied.model_dump(mode="json")
                cur.execute(
                    """
                    INSERT INTO v40_weight_activation_executions (
                        execution_id,
                        review_id,
                        weight_version_id,
                        release_readiness_id,
                        rollback_version_id,
                        version,
                        execution_json,
                        activation_applied,
                        v40_weight_write_applied,
                        source_state_mutated,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, now())
                    ON CONFLICT (execution_id)
                    DO UPDATE SET
                        review_id = EXCLUDED.review_id,
                        weight_version_id = EXCLUDED.weight_version_id,
                        release_readiness_id = EXCLUDED.release_readiness_id,
                        rollback_version_id = EXCLUDED.rollback_version_id,
                        version = EXCLUDED.version,
                        execution_json = EXCLUDED.execution_json,
                        activation_applied = EXCLUDED.activation_applied,
                        v40_weight_write_applied = EXCLUDED.v40_weight_write_applied,
                        source_state_mutated = EXCLUDED.source_state_mutated,
                        created_at = now()
                    """,
                    (
                        applied.execution_id,
                        applied.review_id,
                        applied.weight_version_id,
                        applied.release_readiness_id,
                        applied.rollback_version_id,
                        applied.version,
                        json.dumps(applied_payload, ensure_ascii=False),
                        applied.activation_applied,
                        applied.v40_weight_write_applied,
                        applied.v30_state_mutated,
                    ),
                )
                return applied

    def list_weight_activation_executions(self, *, limit: int = 20) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT
                        execution_id,
                        review_id,
                        weight_version_id,
                        release_readiness_id,
                        rollback_version_id,
                        version,
                        execution_json,
                        activation_applied,
                        v40_weight_write_applied,
                        source_state_mutated,
                        created_at
                    FROM v40_weight_activation_executions
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (bounded_limit,),
                )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_release_readiness(self, summary: ReleaseReadinessSummary) -> None:
        payload = summary.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_release_readiness (
                        readiness_id,
                        candidate_version,
                        version,
                        summary_json,
                        recommendation,
                        production_write_allowed,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s::jsonb, %s, %s, now())
                    ON CONFLICT (readiness_id)
                    DO UPDATE SET
                        candidate_version = EXCLUDED.candidate_version,
                        version = EXCLUDED.version,
                        summary_json = EXCLUDED.summary_json,
                        recommendation = EXCLUDED.recommendation,
                        production_write_allowed = EXCLUDED.production_write_allowed,
                        updated_at = now()
                    """,
                    (
                        summary.readiness_id,
                        summary.candidate_version,
                        summary.version,
                        json.dumps(payload, ensure_ascii=False),
                        summary.recommendation.value,
                        summary.production_write_allowed,
                    ),
                )

    def list_release_readiness(self, *, limit: int = 20) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT
                        readiness_id,
                        candidate_version,
                        version,
                        summary_json,
                        recommendation,
                        production_write_allowed,
                        created_at,
                        updated_at
                    FROM v40_release_readiness
                    ORDER BY updated_at DESC, created_at DESC
                    LIMIT %s
                    """,
                    (bounded_limit,),
                )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_weight_activation_review(self, review: WeightActivationReview) -> None:
        payload = review.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_weight_activation_reviews (
                        review_id,
                        weight_version_id,
                        release_readiness_id,
                        version,
                        review_json,
                        decision,
                        activation_applied,
                        production_write_allowed,
                        updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s, now())
                    ON CONFLICT (review_id)
                    DO UPDATE SET
                        weight_version_id = EXCLUDED.weight_version_id,
                        release_readiness_id = EXCLUDED.release_readiness_id,
                        version = EXCLUDED.version,
                        review_json = EXCLUDED.review_json,
                        decision = EXCLUDED.decision,
                        activation_applied = EXCLUDED.activation_applied,
                        production_write_allowed = EXCLUDED.production_write_allowed,
                        updated_at = now()
                    """,
                    (
                        review.review_id,
                        review.weight_version_id,
                        review.release_readiness_id,
                        review.version,
                        json.dumps(payload, ensure_ascii=False),
                        review.decision.value,
                        review.activation_applied,
                        review.production_write_allowed,
                    ),
                )

    def list_weight_activation_reviews(self, *, limit: int = 20) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT
                        review_id,
                        weight_version_id,
                        release_readiness_id,
                        version,
                        review_json,
                        decision,
                        activation_applied,
                        production_write_allowed,
                        created_at,
                        updated_at
                    FROM v40_weight_activation_reviews
                    ORDER BY updated_at DESC, created_at DESC
                    LIMIT %s
                    """,
                    (bounded_limit,),
                )
                return [_serialize_row(row) for row in cur.fetchall()]

    def save_release_gate(self, gate: ReleaseGateResult) -> None:
        payload = gate.model_dump(mode="json")
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v40_release_gates (
                        gate_id,
                        candidate_version,
                        version,
                        gate_json,
                        recommendation,
                        production_write_allowed,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s::jsonb, %s, %s, now())
                    ON CONFLICT (gate_id)
                    DO UPDATE SET
                        candidate_version = EXCLUDED.candidate_version,
                        version = EXCLUDED.version,
                        gate_json = EXCLUDED.gate_json,
                        recommendation = EXCLUDED.recommendation,
                        production_write_allowed = EXCLUDED.production_write_allowed,
                        created_at = now()
                    """,
                    (
                        gate.gate_id,
                        gate.candidate_version,
                        gate.version,
                        json.dumps(payload, ensure_ascii=False),
                        gate.recommendation.value,
                        gate.production_write_allowed,
                    ),
                )

    def list_release_gates(self, *, limit: int = 20) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(limit, 100))
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT
                        gate_id,
                        candidate_version,
                        version,
                        gate_json,
                        recommendation,
                        production_write_allowed,
                        created_at
                    FROM v40_release_gates
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (bounded_limit,),
                )
                return [_serialize_row(row) for row in cur.fetchall()]

    def lab_summary(self) -> dict[str, Any]:
        tables = {
            "runtime_records": "v40_runtime_records",
            "evaluation_cases": "v40_evaluation_cases",
            "evaluation_runs": "v40_evaluation_runs",
            "training_label_events": "v40_training_label_events",
            "local_overlays": "v40_local_overlays",
            "training_examples": "v40_training_examples",
            "training_example_replays": "v40_training_example_replays",
            "training_replay_batches": "v40_training_replay_batches",
            "conversation_turns": "v40_conversation_turns",
            "consent_grants": "v40_consent_grants",
            "practitioner_review_requests": "v40_practitioner_review_requests",
            "practitioner_review_queue": "v40_practitioner_review_queue",
            "practitioner_review_results": "v40_practitioner_review_results",
            "training_impact_diffs": "v40_training_impact_diffs",
            "trainable_policy_registries": "v40_trainable_policy_registries",
            "shadow_compare_runs": "v40_shadow_compare_runs",
            "release_gates": "v40_release_gates",
            "evaluation_batches": "v40_evaluation_batches",
            "global_weight_versions": "v40_global_weight_versions",
            "release_readiness": "v40_release_readiness",
            "weight_activation_reviews": "v40_weight_activation_reviews",
            "weight_activation_executions": "v40_weight_activation_executions",
        }
        counts: dict[str, int] = {}
        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                for key, table in tables.items():
                    cur.execute(f"SELECT count(*) AS count FROM {table}")
                    row = cur.fetchone()
                    counts[key] = int(row["count"] if row else 0)
                latest_runs = self._latest_rows(cur, "v40_evaluation_runs", "updated_at", limit=5)
                latest_batches = self._latest_rows(cur, "v40_evaluation_batches", "updated_at", limit=5)
                latest_impacts = self._latest_rows(cur, "v40_training_impact_diffs", "created_at", limit=5)
                latest_policy_registries = self._latest_rows(
                    cur,
                    "v40_trainable_policy_registries",
                    "updated_at",
                    limit=5,
                )
                latest_local_overlays = self._latest_rows(cur, "v40_local_overlays", "updated_at", limit=5)
                latest_training_examples = self._latest_rows(cur, "v40_training_examples", "updated_at", limit=5)
                latest_training_example_replays = self._latest_rows(
                    cur,
                    "v40_training_example_replays",
                    "created_at",
                    limit=5,
                )
                latest_training_replay_batches = self._latest_rows(
                    cur,
                    "v40_training_replay_batches",
                    "updated_at",
                    limit=5,
                )
                latest_conversation_turns = self._latest_rows(cur, "v40_conversation_turns", "updated_at", limit=5)
                latest_consent_grants = self._latest_rows(cur, "v40_consent_grants", "updated_at", limit=5)
                latest_practitioner_review_requests = self._latest_rows(
                    cur,
                    "v40_practitioner_review_requests",
                    "updated_at",
                    limit=5,
                )
                latest_practitioner_review_queue = self._latest_rows(
                    cur,
                    "v40_practitioner_review_queue",
                    "updated_at",
                    limit=5,
                )
                latest_practitioner_review_results = self._latest_rows(
                    cur,
                    "v40_practitioner_review_results",
                    "updated_at",
                    limit=5,
                )
                latest_gates = self._latest_rows(cur, "v40_release_gates", "created_at", limit=5)
                latest_weights = self._latest_rows(cur, "v40_global_weight_versions", "updated_at", limit=5)
                latest_readiness = self._latest_rows(cur, "v40_release_readiness", "updated_at", limit=5)
                latest_activation_reviews = self._latest_rows(
                    cur,
                    "v40_weight_activation_reviews",
                    "updated_at",
                    limit=5,
                )
                latest_activation_executions = self._latest_rows(
                    cur,
                    "v40_weight_activation_executions",
                    "created_at",
                    limit=5,
                )
        return {
            "counts": counts,
            "latest_evaluation_runs": latest_runs,
            "latest_evaluation_batches": latest_batches,
            "latest_training_impacts": latest_impacts,
            "latest_trainable_policy_registries": latest_policy_registries,
            "latest_local_overlays": latest_local_overlays,
            "latest_training_examples": latest_training_examples,
            "latest_training_example_replays": latest_training_example_replays,
            "latest_training_replay_batches": latest_training_replay_batches,
            "latest_conversation_turns": latest_conversation_turns,
            "latest_consent_grants": latest_consent_grants,
            "latest_practitioner_review_requests": latest_practitioner_review_requests,
            "latest_practitioner_review_queue": latest_practitioner_review_queue,
            "latest_practitioner_review_results": latest_practitioner_review_results,
            "latest_release_gates": latest_gates,
            "latest_global_weight_versions": latest_weights,
            "latest_release_readiness": latest_readiness,
            "latest_weight_activation_reviews": latest_activation_reviews,
            "latest_weight_activation_executions": latest_activation_executions,
        }

    def _connect(self) -> psycopg.Connection[Any]:
        return psycopg.connect(self._config.dsn)

    def _latest_rows(
        self,
        cur: psycopg.Cursor[Any],
        table: str,
        order_column: str,
        *,
        limit: int,
    ) -> list[dict[str, Any]]:
        cur.execute(
            f"""
            SELECT *
            FROM {table}
            ORDER BY {order_column} DESC
            LIMIT %s
            """,
            (limit,),
        )
        return [_serialize_row(row) for row in cur.fetchall()]


def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    serialized = dict(row)
    created_at = serialized.get("created_at")
    if isinstance(created_at, datetime):
        serialized["created_at"] = created_at.isoformat()
    updated_at = serialized.get("updated_at")
    if isinstance(updated_at, datetime):
        serialized["updated_at"] = updated_at.isoformat()
    activated_at = serialized.get("activated_at")
    if isinstance(activated_at, datetime):
        serialized["activated_at"] = activated_at.isoformat()
    return serialized
