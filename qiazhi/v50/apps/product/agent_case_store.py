from __future__ import annotations

import os
from typing import Any, Protocol


FORBIDDEN_LEGACY_FORMAL_WRITE_KEYS = frozenset({
    "conversation_history",
    "conversation_memory",
    "first_reading",
    "legacy_report",
    "old_workspace",
    "probe_history",
    "report",
    "report_json",
    "review_json",
    "run_record",
})


class LegacyFormalWriteBlocked(ValueError):
    """Raised when a retired representation attempts to become case authority."""


class AgentCaseStore(Protocol):
    persistent: bool
    storage_name: str

    def save(self, *, case_id: str, user_id: str | None, profile_id: str | None, payload: dict[str, Any]) -> None: ...
    def get(self, *, case_id: str, user_id: str | None = None) -> dict[str, Any] | None: ...
    def list_for_user(self, *, user_id: str) -> list[dict[str, Any]]: ...


class MemoryAgentCaseStore:
    persistent = False
    storage_name = "memory_only"

    def __init__(self) -> None:
        self._cases: dict[str, dict[str, Any]] = {}

    def save(self, *, case_id: str, user_id: str | None, profile_id: str | None, payload: dict[str, Any]) -> None:
        canonical = _canonical_case_payload(payload)
        self._cases[case_id] = {**canonical, "case_id": case_id, "user_id": user_id, "profile_id": profile_id}

    def get(self, *, case_id: str, user_id: str | None = None) -> dict[str, Any] | None:
        row = self._cases.get(case_id)
        if row is None or (user_id is not None and row.get("user_id") not in {None, user_id}):
            return None
        return _compatibility_case_row(row)

    def list_for_user(self, *, user_id: str) -> list[dict[str, Any]]:
        return [_compatibility_case_row(row) for row in self._cases.values() if row.get("user_id") == user_id]


class PostgresAgentCaseStore:
    persistent = True
    storage_name = "v50_postgresql"

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.ensure_schema()

    def _connect(self):
        import psycopg

        return psycopg.connect(self.database_url)

    def ensure_schema(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS v50_mingli_agent_cases (
                        case_id TEXT PRIMARY KEY,
                        user_id TEXT NULL REFERENCES v50_user_accounts(user_id),
                        profile_id TEXT NULL,
                        case_json JSONB NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_v50_agent_cases_user ON v50_mingli_agent_cases (user_id, updated_at DESC)"
                )

    def save(self, *, case_id: str, user_id: str | None, profile_id: str | None, payload: dict[str, Any]) -> None:
        from psycopg.types.json import Jsonb

        canonical = _canonical_case_payload(payload)

        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO v50_mingli_agent_cases (case_id, user_id, profile_id, case_json)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (case_id) DO UPDATE SET
                        user_id = COALESCE(EXCLUDED.user_id, v50_mingli_agent_cases.user_id),
                        profile_id = COALESCE(EXCLUDED.profile_id, v50_mingli_agent_cases.profile_id),
                        case_json = EXCLUDED.case_json,
                        updated_at = now()
                    """,
                    (case_id, user_id, profile_id, Jsonb(canonical)),
                )

    def get(self, *, case_id: str, user_id: str | None = None) -> dict[str, Any] | None:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                if user_id is None:
                    cur.execute("SELECT case_json, user_id, profile_id FROM v50_mingli_agent_cases WHERE case_id = %s", (case_id,))
                else:
                    cur.execute(
                        "SELECT case_json, user_id, profile_id FROM v50_mingli_agent_cases WHERE case_id = %s AND (user_id = %s OR user_id IS NULL)",
                        (case_id, user_id),
                    )
                row = cur.fetchone()
        return _compatibility_case_row({
            **dict(row["case_json"]),
            "user_id": row["user_id"],
            "profile_id": row["profile_id"],
        }) if row else None

    def list_for_user(self, *, user_id: str) -> list[dict[str, Any]]:
        from psycopg.rows import dict_row

        with self._connect() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT case_json FROM v50_mingli_agent_cases WHERE user_id = %s ORDER BY updated_at DESC LIMIT 100",
                    (user_id,),
                )
                rows = cur.fetchall()
        return [_compatibility_case_row(dict(row["case_json"])) for row in rows]


def build_agent_case_store() -> AgentCaseStore:
    database_url = os.getenv("V50_DATABASE_URL", "").strip()
    return PostgresAgentCaseStore(database_url) if database_url else MemoryAgentCaseStore()


def _canonical_case_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Accept canonical case state and cut retired representations from writes."""

    canonical = dict(payload)
    forbidden = sorted(
        key
        for key in FORBIDDEN_LEGACY_FORMAL_WRITE_KEYS
        if canonical.get(key) is not None and canonical.get(key) != ""
    )
    if forbidden:
        raise LegacyFormalWriteBlocked(f"legacy_formal_write_blocked:{','.join(forbidden)}")
    if "case_belief_state" not in canonical and isinstance(canonical.get("workspace"), dict):
        canonical["case_belief_state"] = canonical["workspace"]
    if isinstance(canonical.get("case_belief_state"), dict):
        belief_state = dict(canonical["case_belief_state"])
        # RealityEvidence in LifeCase is authoritative. Old callers receive a
        # derived probe history through _compatibility_case_row instead.
        belief_state.pop("probe_history", None)
        canonical["case_belief_state"] = belief_state
    canonical.pop("workspace", None)
    return canonical


def _compatibility_case_row(payload: dict[str, Any]) -> dict[str, Any]:
    """Expose a derived legacy alias to old callers without persisting it."""

    row = dict(payload)
    if "workspace" not in row and isinstance(row.get("case_belief_state"), dict):
        workspace = dict(row["case_belief_state"])
        if not workspace.get("probe_history"):
            workspace["probe_history"] = _derived_probe_history(row.get("life_case"))
        row["workspace"] = workspace
    return row


def _derived_probe_history(life_case: Any) -> list[dict[str, Any]]:
    """Rebuild the legacy probe view from canonical RealityEvidence on reads."""

    if not isinstance(life_case, dict):
        return []
    derived: list[dict[str, Any]] = []
    for evidence in life_case.get("reality_evidence") or []:
        if not isinstance(evidence, dict) or evidence.get("source") != "probe":
            continue
        details = evidence.get("structured_payload") or {}
        if not isinstance(details, dict):
            details = {}
        source = details.get("reported_by") or "user_reported"
        if source not in {"user_reported", "practitioner_reported", "research_observation"}:
            source = "user_reported"
        derived.append({
            "evidence_id": str(evidence.get("evidence_id") or ""),
            "plan_id": str(details.get("plan_id") or "legacy-derived"),
            "source_probe_id": str(details.get("source_probe_id") or evidence.get("source_ref") or ""),
            "option_id": str(details.get("option_id") or "legacy-derived"),
            "option_label": str(details.get("option_label") or evidence.get("summary") or "已记录"),
            "recorded_at": str(evidence.get("recorded_at") or ""),
            "evidence_kind": str(evidence.get("kind") or "behavior"),
            "scenario": str(details.get("scenario") or "recognition"),
            "domain": str(evidence.get("domain") or "whole_chart"),
            "hidden_attribute_observations": details.get("hidden_attribute_observations") or {},
            "evidence_strength": str(details.get("evidence_strength") or "medium"),
            "reliability": float(details.get("reliability") or 0.55),
            "relevance": float(details.get("relevance") or 0.8),
            "year_value": details.get("year_value"),
            "event_note": str(evidence.get("summary") or ""),
            "recurrence_count": details.get("recurrence_count"),
            "hypothesis_updates": details.get("hypothesis_updates") or {},
            "assertion_updates": details.get("assertion_updates") or {},
            "source": source,
        })
    return derived
