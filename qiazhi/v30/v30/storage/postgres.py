from __future__ import annotations

from typing import Any, Literal

from v30.contracts import CoreRuntimeResult
from v30.storage.names import require_v30_table
from v30.storage.postgres_schema import CREATE_TABLE_STATEMENTS, schema_sql


WritableTable = Literal[
    "v30_readings",
    "v30_runtime_traces",
    "v30_feedback_events",
    "v30_hidden_factor_states",
    "v30_validation_cases",
    "v30_policy_pointers",
    "v30_artifacts",
    "v30_diagnosis_runs",
    "v30_diagnosis_rule_matches",
    "v30_diagnosis_paths",
    "v30_diagnosis_portraits",
    "v30_diagnosis_claims",
    "v30_diagnosis_feedback",
]


def create_schema_sql() -> str:
    return schema_sql()


def create_table_sql(table_name: WritableTable) -> str:
    require_v30_table(table_name)
    return CREATE_TABLE_STATEMENTS[table_name]


def reading_record(runtime: CoreRuntimeResult) -> dict[str, Any]:
    return {
        "table": "v30_readings",
        "key": runtime.reading_id,
        "payload": runtime.model_dump(mode="json"),
    }


def trace_record(runtime: CoreRuntimeResult) -> dict[str, Any]:
    return {
        "table": "v30_runtime_traces",
        "key": runtime.trace_id,
        "reading_id": runtime.reading_id,
        "payload": runtime.model_dump(mode="json"),
    }


def upsert_reading_sql() -> str:
    return """
INSERT INTO v30_readings (reading_id, payload)
VALUES (%s, %s::jsonb)
ON CONFLICT (reading_id)
DO UPDATE SET payload = EXCLUDED.payload;
""".strip()


def upsert_trace_sql() -> str:
    return """
INSERT INTO v30_runtime_traces (trace_id, reading_id, payload)
VALUES (%s, %s, %s::jsonb)
ON CONFLICT (trace_id)
DO UPDATE SET payload = EXCLUDED.payload;
""".strip()


def select_reading_sql() -> str:
    return "SELECT payload FROM v30_readings WHERE reading_id = %s;"


def select_trace_sql() -> str:
    return "SELECT payload FROM v30_runtime_traces WHERE trace_id = %s;"
