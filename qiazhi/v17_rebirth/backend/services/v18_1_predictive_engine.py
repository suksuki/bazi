from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from contextlib import contextmanager
from secrets import token_urlsafe
from typing import Any, Dict, Iterator, List, Optional

from v17_rebirth.backend.config import (
    PREDICTIVE_DATABASE_URL,
    PREDICTIVE_STORAGE_BACKEND,
    should_auto_migrate_predictive_json_to_postgres,
)
from v17_rebirth.infrastructure.llm_bridge import get_runtime_llm_config
from v17_rebirth.paths import RUNTIME_DIR


V18_1_SCHEMA_VERSION = "v18.1"
V18_1_SECRET = os.getenv("V18_1_SECRET", "v18.1-predictive-secret")
RULE_STATE_VALUES = {"experimental", "validated", "active", "deprecated"}
KNOWLEDGE_CARD_STATES = {"draft", "validated", "active", "deprecated", "archived"}
BAZI_KNOWLEDGE_DOMAINS = {"wealth", "career", "relationship", "health", "chart_structure"}
BAZI_KNOWLEDGE_CATEGORIES = {
    "wealth_star",
    "wealth_vault",
    "output_generate_wealth",
    "constraint_structure",
    "combination_clash_stability",
    "luck_flow_activation",
}
BAZI_KNOWLEDGE_STATES = {"draft", "reviewed", "deprecated"}
BAZI_FEATURE_TYPES = {
    "wealth_strength",
    "wealth_vault_activation",
    "wealth_vault_state",
    "output_generate_wealth",
    "wealth_constraint",
    "peer_competition",
    "wealth_flow_activation",
    "wealth_stability",
    "wealth_risk",
}
RULE_TEST_SUITE_STATES = {"draft", "validated", "active", "deprecated", "archived"}
RULE_CONFLICT_POLICIES = {"override", "merge", "suppress", "degrade", "defer_manual_review"}
RULE_GATEKEEPER_PROTOCOL = "v18.1.gatekeeper"
RULE_RUNTIME_TOKEN_TTL_SECONDS = 300
LIFECYCLE_BYPASS_CODE = "LIFECYCLE_BYPASS_ATTEMPT"
ENERGY_CLAMP_DECORATOR = "ENERGY_CLAMP"
ENERGY_CLAMP_LIMITS = {
    "unsigned_min": 0.0,
    "unsigned_max": 1.0,
    "signed_min": -1.0,
    "signed_max": 1.0,
    "raw_abs_max": 1000000.0,
}
RULE_TEST_ENGINE_VERSION = "v0.1"
RULE_TEST_ENGINE_VERSION_V02 = "v0.2"
RULE_TEST_CASE_SOURCES = {"synthetic", "historical", "feedback", "manual"}
RULE_TEST_ENGINE_THRESHOLD_V01 = {
    "version": RULE_TEST_ENGINE_VERSION,
    "precision_min": 0.8,
    "recall_min": 0.8,
    "precision_deprecate_max": 0.5,
    "recall_deprecate_max": 0.5,
    "conflict_max": 0.2,
    "min_cases": 5,
    "quality_score_min": 0.65,
    "high_conflict_rate": 0.6,
    "needs_review_conflict_rate": 0.35,
}
V18_1_STRICT_LIFECYCLE = os.getenv("V18_1_STRICT_LIFECYCLE", "1") in {"1", "true", "TRUE", "yes", "on"}
V18_STORAGE_BACKEND = PREDICTIVE_STORAGE_BACKEND
V18_POSTGRES_DSN = PREDICTIVE_DATABASE_URL
V18_KB_AUDIT_BASE_URL = (
    os.getenv("V18_KB_AUDIT_BASE_URL")
    or os.getenv("QWEN_AUDIT_BASE_URL")
    or os.getenv("LLM_BASE_URL")
    or ""
).strip()
V18_KB_AUDIT_MODEL = (
    os.getenv("V18_KB_AUDIT_MODEL")
    or os.getenv("QWEN_AUDIT_MODEL")
    or "qwen3.6.3.5"
).strip()
V18_KB_AUDIT_API_KEY = (
    os.getenv("V18_KB_AUDIT_API_KEY")
    or os.getenv("QWEN_AUDIT_API_KEY")
    or os.getenv("OPENAI_API_KEY")
    or ""
).strip()


V18_STATE_COLLECTIONS = (
    "rules",
    "active_rules",
    "knowledge_cards",
    "active_knowledge_cards",
    "rule_candidates",
    "knowledge_pr_queue",
    "prediction_ledger",
    "verifier_runs",
    "feedback",
    "learning_signals",
    "aggregated_insights",
    "candidate_rule_suggestions",
    "rule_test_results",
    "rule_test_suites",
    "active_rule_test_suites",
    "rule_test_cases",
    "rule_test_runs",
    "rule_quality_scores",
    "agent_sessions",
    "audit_events",
    "bazi_knowledge_units",
    "bazi_knowledge_sources",
    "bazi_knowledge_conflicts",
    "bazi_feature_definitions",
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _canonical_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _prediction_hash(payload: Dict[str, Any]) -> str:
    canonical = _canonical_json(payload)
    if not V18_1_SECRET:
        digest = _sha256(canonical)
    else:
        digest = hmac.new(
            key=V18_1_SECRET.encode("utf-8"),
            msg=canonical.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
    return f"sha256:{digest}"


def _contract_hash(payload: Dict[str, Any]) -> str:
    canonical_payload = dict(payload or {})
    canonical_payload.pop("contract_hash", None)
    canonical_payload.pop("prediction_hash", None)
    return f"sha256:{_sha256(_canonical_json(canonical_payload))}"


def _payload_hash(payload: Dict[str, Any]) -> str:
    return f"sha256:{_sha256(_canonical_json(dict(payload or {})))}"


def _audit_event_hash(payload: Dict[str, Any]) -> str:
    normalized = dict(payload or {})
    normalized.pop("event_hash", None)
    return _payload_hash(normalized)


def _ensure_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return [x for x in value]
    if value is None:
        return []
    return [value]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        raw = float(value)
    except (TypeError, ValueError):
        return default
    if raw != raw:
        return default
    return max(0.0, raw)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if not text:
        return default
    if text in {"1", "true", "yes", "on", "active", "pass", "hit"}:
        return True
    if text in {"0", "false", "no", "off", "inactive", "reject", "miss"}:
        return False
    return default


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _rule_storage_key(rule_id: str, version: str) -> str:
    return f"{_safe_str(rule_id)}::{_safe_str(version)}"


def _split_rule_key(key: str) -> tuple[str, str]:
    if "::" in key:
        rid, version = str(key).split("::", 1)
        return rid, version
    return str(key), "legacy"


def _rule_payload_fingerprint(payload: Dict[str, Any]) -> str:
    normalized = {
        "rule_id": _safe_str(payload.get("rule_id")),
        "theory_family": _safe_str(payload.get("theory_family")),
        "condition": dict(payload.get("condition") or {}),
        "effect": dict(payload.get("effect") or {}),
        "priority": _safe_float(payload.get("priority"), 0.0),
        "evidence_strength": _safe_float(payload.get("evidence_strength"), 0.0),
        "conflict_policy": _safe_str(payload.get("conflict_policy")),
        "version": _safe_str(payload.get("version")),
        "owner_plugin": _safe_str(payload.get("owner_plugin")),
        "effect_scope": _ensure_list(payload.get("effect_scope")),
        "allowed_topics": _ensure_list(payload.get("allowed_topics")),
    }
    return _sha256(_canonical_json(normalized))


def _knowledge_card_payload_fingerprint(payload: Dict[str, Any]) -> str:
    normalized = {
        "card_id": _safe_str(payload.get("card_id")),
        "knowledge_domain": _safe_str(payload.get("knowledge_domain")),
        "title": _safe_str(payload.get("title")),
        "summary": _safe_str(payload.get("summary")),
        "status": _safe_str(payload.get("status")),
        "version": _safe_str(payload.get("version")),
        "source_refs": _ensure_list(payload.get("source_refs")),
        "tags": _ensure_list(payload.get("tags")),
        "content": dict(payload.get("content") or {}),
    }
    return _sha256(_canonical_json(normalized))


def _bazi_knowledge_content_fingerprint(payload: Dict[str, Any]) -> str:
    normalized = {
        "knowledge_id": _safe_str(payload.get("knowledge_id")),
        "domain": _safe_str(payload.get("domain")),
        "category": _safe_str(payload.get("category")),
        "title": _safe_str(payload.get("title")),
        "statement": _safe_str(payload.get("statement")),
        "classical_source": _safe_str(payload.get("classical_source")),
        "modern_interpretation": _safe_str(payload.get("modern_interpretation")),
        "conditions": dict(payload.get("conditions") or {}),
        "feature_mapping": dict(payload.get("feature_mapping") or {}),
        "effects": dict(payload.get("effects") or {}),
        "risk_factors": _ensure_list(payload.get("risk_factors")),
        "uncertainty_factors": _ensure_list(payload.get("uncertainty_factors")),
        "conflicts": _ensure_list(payload.get("conflicts")),
        "confidence_prior": _safe_float(payload.get("confidence_prior"), 0.0),
    }
    return _sha256(_canonical_json(normalized))


def _feature_definition_content_fingerprint(payload: Dict[str, Any]) -> str:
    normalized = {
        "feature_type": _safe_str(payload.get("feature_type")),
        "domain": _safe_str(payload.get("domain")),
        "title": _safe_str(payload.get("title")),
        "input_requirements": dict(payload.get("input_requirements") or {}),
        "detection_logic": dict(payload.get("detection_logic") or {}),
        "output_fields": _ensure_list(payload.get("output_fields")),
        "effect_direction": _safe_str(payload.get("effect_direction")),
        "confidence_weight": _safe_float(payload.get("confidence_weight"), 0.0),
        "uncertainty_weight": _safe_float(payload.get("uncertainty_weight"), 0.0),
    }
    return _sha256(_canonical_json(normalized))


def _rule_test_suite_payload_fingerprint(payload: Dict[str, Any]) -> str:
    normalized = {
        "suite_id": _safe_str(payload.get("suite_id")),
        "rule_id": _safe_str(payload.get("rule_id")),
        "rule_version": _safe_str(payload.get("rule_version")),
        "title": _safe_str(payload.get("title")),
        "description": _safe_str(payload.get("description")),
        "status": _safe_str(payload.get("status")),
        "version": _safe_str(payload.get("version")),
        "test_cases": _ensure_list(payload.get("test_cases") or payload.get("cases")),
    }
    return _sha256(_canonical_json(normalized))


def _rule_test_run_payload_fingerprint(
    *,
    rule_id: str,
    rule_version: str,
    suite_id: str,
    suite_version: str,
    test_suite: str,
    test_cases: List[Dict[str, Any]],
) -> str:
    normalized_cases = []
    for raw in _ensure_list(test_cases):
        if not isinstance(raw, dict):
            continue
        normalized_cases.append(
            {
                "case_id": _safe_str(raw.get("case_id"), ""),
                "scenario": _safe_str(raw.get("scenario"), ""),
                "expected_active": _safe_bool(raw.get("expected_active"), False),
                "observed_active": _safe_bool(raw.get("observed_active"), False),
                "features": dict(raw.get("features") or {}),
            }
        )
    normalized = {
        "rule_id": _safe_str(rule_id),
        "rule_version": _safe_str(rule_version),
        "suite_id": _safe_str(suite_id),
        "suite_version": _safe_str(suite_version),
        "test_suite": _safe_str(test_suite),
        "test_cases": normalized_cases,
    }
    return _sha256(_canonical_json(normalized))


def _rule_candidate_id(payload: Dict[str, Any]) -> str:
    return f"rule_candidate_{_rule_payload_fingerprint(payload)[:16]}"


def _knowledge_card_content_fingerprint(payload: Dict[str, Any]) -> str:
    normalized = {
        "knowledge_domain": _safe_str(payload.get("knowledge_domain")),
        "title": _safe_str(payload.get("title")),
        "summary": _safe_str(payload.get("summary")),
        "source_refs": _ensure_list(payload.get("source_refs")),
        "tags": _ensure_list(payload.get("tags")),
        "content": dict(payload.get("content") or {}),
    }
    return _sha256(_canonical_json(normalized))


def _state_row_created_at(payload: Any) -> str:
    return _safe_str(payload.get("created_at") or payload.get("updated_at")) if isinstance(payload, dict) else ""


def _state_row_rule_id(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    if payload.get("rule_id"):
        return _safe_str(payload.get("rule_id"))
    nested = payload.get("rule_payload") if isinstance(payload.get("rule_payload"), dict) else {}
    return _safe_str(nested.get("rule_id"))


def _state_row_prediction_id(payload: Any) -> str:
    return _safe_str(payload.get("prediction_id")) if isinstance(payload, dict) else ""


def _state_row_insight_id(payload: Any) -> str:
    return _safe_str(payload.get("insight_id") or payload.get("based_on_insight_id")) if isinstance(payload, dict) else ""


class V18StorageAdapter:
    backend_name = "base"

    def load_snapshot(self) -> Dict[str, Any]:
        return {}

    def save_snapshot(self, snapshot: Dict[str, Any]) -> None:
        return None

    def transaction(self) -> Iterator[None]:
        @contextmanager
        def _noop() -> Iterator[None]:
            yield
        return _noop()

    def update_audit_event(self, *_args: Any, **_kwargs: Any) -> None:
        raise PredictiveServiceError("AUDIT_APPEND_ONLY", "audit events are append-only", 409)

    def delete_audit_event(self, *_args: Any, **_kwargs: Any) -> None:
        raise PredictiveServiceError("AUDIT_APPEND_ONLY", "audit events are append-only", 409)


class JsonStorageAdapter(V18StorageAdapter):
    backend_name = "json"


class PostgresStorageAdapter(V18StorageAdapter):
    backend_name = "postgres"

    def __init__(self, dsn: str) -> None:
        self.dsn = _safe_str(dsn)
        if not self.dsn:
            raise PredictiveServiceError("POSTGRES_DSN_REQUIRED", "PREDICTIVE_DATABASE_URL or DATABASE_URL is required for postgres backend", 500)
        self._ensure_schema()

    def _driver(self) -> Any:
        try:
            import psycopg  # type: ignore
            return "psycopg", psycopg
        except Exception:
            try:
                import psycopg2  # type: ignore
                return "psycopg2", psycopg2
            except Exception as exc:
                raise PredictiveServiceError("POSTGRES_DRIVER_MISSING", "install psycopg or psycopg2 for postgres backend", 500) from exc

    def _connect(self) -> Any:
        _name, driver = self._driver()
        return driver.connect(self.dsn)

    def _json_param(self, payload: Any) -> str:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)

    def _ensure_schema(self) -> None:
        ddl = [
            """
            CREATE TABLE IF NOT EXISTS predictive_state (
                collection TEXT NOT NULL,
                item_key TEXT NOT NULL,
                payload JSONB NOT NULL,
                created_at TIMESTAMPTZ,
                rule_id TEXT,
                prediction_id TEXT,
                contract_id TEXT,
                insight_id TEXT,
                session_id TEXT,
                PRIMARY KEY (collection, item_key)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS predictive_audit_events (
                event_hash TEXT PRIMARY KEY,
                previous_event_hash TEXT,
                payload JSONB NOT NULL,
                created_at TIMESTAMPTZ,
                rule_id TEXT,
                event_type TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS bazi_knowledge_units (
                knowledge_id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                statement TEXT NOT NULL,
                classical_source TEXT NOT NULL,
                modern_interpretation TEXT NOT NULL,
                conditions JSONB NOT NULL DEFAULT '{}'::jsonb,
                feature_mapping JSONB NOT NULL DEFAULT '{}'::jsonb,
                effects JSONB NOT NULL DEFAULT '{}'::jsonb,
                risk_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
                uncertainty_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
                conflicts JSONB NOT NULL DEFAULT '[]'::jsonb,
                confidence_prior DOUBLE PRECISION NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                created_by TEXT,
                reviewed_by TEXT,
                source_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
                content_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ,
                updated_at TIMESTAMPTZ,
                reviewed_at TIMESTAMPTZ
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS bazi_knowledge_sources (
                source_id TEXT PRIMARY KEY,
                knowledge_id TEXT NOT NULL,
                source_type TEXT NOT NULL,
                title TEXT NOT NULL,
                reference TEXT NOT NULL,
                notes TEXT,
                payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS bazi_knowledge_conflicts (
                conflict_id TEXT PRIMARY KEY,
                knowledge_id TEXT NOT NULL,
                conflicts_with TEXT NOT NULL,
                conflict_type TEXT NOT NULL,
                resolution_policy TEXT NOT NULL,
                payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS bazi_feature_definitions (
                feature_type TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                title TEXT NOT NULL,
                input_requirements JSONB NOT NULL DEFAULT '{}'::jsonb,
                detection_logic JSONB NOT NULL DEFAULT '{}'::jsonb,
                output_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
                effect_direction TEXT NOT NULL,
                confidence_weight DOUBLE PRECISION NOT NULL DEFAULT 0,
                uncertainty_weight DOUBLE PRECISION NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ,
                updated_at TIMESTAMPTZ
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_predictive_state_created_at ON predictive_state(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_predictive_state_rule_id ON predictive_state(rule_id)",
            "CREATE INDEX IF NOT EXISTS idx_predictive_state_prediction_id ON predictive_state(prediction_id)",
            "CREATE INDEX IF NOT EXISTS idx_predictive_state_contract_id ON predictive_state(contract_id)",
            "CREATE INDEX IF NOT EXISTS idx_predictive_state_insight_id ON predictive_state(insight_id)",
            "CREATE INDEX IF NOT EXISTS idx_predictive_state_session_id ON predictive_state(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_predictive_state_collection_created ON predictive_state(collection, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_predictive_audit_created_at ON predictive_audit_events(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_predictive_audit_rule_id ON predictive_audit_events(rule_id)",
            "CREATE INDEX IF NOT EXISTS idx_predictive_audit_event_type ON predictive_audit_events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_bazi_knowledge_units_domain ON bazi_knowledge_units(domain)",
            "CREATE INDEX IF NOT EXISTS idx_bazi_knowledge_units_category ON bazi_knowledge_units(category)",
            "CREATE INDEX IF NOT EXISTS idx_bazi_knowledge_units_status ON bazi_knowledge_units(status)",
            "CREATE INDEX IF NOT EXISTS idx_bazi_knowledge_units_domain_category_status ON bazi_knowledge_units(domain, category, status)",
            "CREATE INDEX IF NOT EXISTS idx_bazi_knowledge_sources_knowledge_id ON bazi_knowledge_sources(knowledge_id)",
            "CREATE INDEX IF NOT EXISTS idx_bazi_knowledge_conflicts_knowledge_id ON bazi_knowledge_conflicts(knowledge_id)",
            "CREATE INDEX IF NOT EXISTS idx_bazi_feature_definitions_domain ON bazi_feature_definitions(domain)",
        ]
        with self._connect() as conn:
            with conn.cursor() as cur:
                for stmt in ddl:
                    cur.execute(stmt)
            conn.commit()

    def load_snapshot(self) -> Dict[str, Any]:
        snapshot: Dict[str, Any] = {name: {} for name in V18_STATE_COLLECTIONS if name != "audit_events"}
        snapshot["audit_events"] = []
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT collection, item_key, payload FROM predictive_state")
                for collection, item_key, payload in cur.fetchall():
                    if isinstance(payload, str):
                        payload = json.loads(payload)
                    snapshot.setdefault(collection, {})[_safe_str(item_key)] = payload
                cur.execute("SELECT payload FROM predictive_audit_events ORDER BY created_at ASC")
                for (payload,) in cur.fetchall():
                    if isinstance(payload, str):
                        payload = json.loads(payload)
                    if isinstance(payload, dict):
                        snapshot["audit_events"].append(payload)
                cur.execute("SELECT knowledge_id, domain, category, title, statement, classical_source, modern_interpretation, conditions, feature_mapping, effects, risk_factors, uncertainty_factors, conflicts, confidence_prior, status, created_by, reviewed_by, source_refs, content_hash, created_at, updated_at, reviewed_at FROM bazi_knowledge_units")
                for row in cur.fetchall():
                    payload = {
                        "knowledge_id": row[0],
                        "domain": row[1],
                        "category": row[2],
                        "title": row[3],
                        "statement": row[4],
                        "classical_source": row[5],
                        "modern_interpretation": row[6],
                        "conditions": row[7],
                        "feature_mapping": row[8],
                        "effects": row[9],
                        "risk_factors": row[10],
                        "uncertainty_factors": row[11],
                        "conflicts": row[12],
                        "confidence_prior": row[13],
                        "status": row[14],
                        "created_by": row[15],
                        "reviewed_by": row[16],
                        "source_refs": row[17],
                        "content_hash": row[18],
                        "created_at": _safe_str(row[19]),
                        "updated_at": _safe_str(row[20]),
                        "reviewed_at": _safe_str(row[21]),
                    }
                    snapshot.setdefault("bazi_knowledge_units", {})[_safe_str(row[0])] = payload
                cur.execute("SELECT feature_type, domain, title, input_requirements, detection_logic, output_fields, effect_direction, confidence_weight, uncertainty_weight, status, content_hash, created_at, updated_at FROM bazi_feature_definitions")
                for row in cur.fetchall():
                    payload = {
                        "feature_type": row[0],
                        "domain": row[1],
                        "title": row[2],
                        "input_requirements": row[3],
                        "detection_logic": row[4],
                        "output_fields": row[5],
                        "effect_direction": row[6],
                        "confidence_weight": row[7],
                        "uncertainty_weight": row[8],
                        "status": row[9],
                        "content_hash": row[10],
                        "created_at": _safe_str(row[11]),
                        "updated_at": _safe_str(row[12]),
                    }
                    snapshot.setdefault("bazi_feature_definitions", {})[_safe_str(row[0])] = payload
                cur.execute("SELECT source_id, knowledge_id, source_type, title, reference, notes, payload, created_at FROM bazi_knowledge_sources")
                for row in cur.fetchall():
                    payload = {
                        "source_id": row[0],
                        "knowledge_id": row[1],
                        "source_type": row[2],
                        "title": row[3],
                        "reference": row[4],
                        "notes": row[5],
                        "payload": row[6],
                        "created_at": _safe_str(row[7]),
                    }
                    snapshot.setdefault("bazi_knowledge_sources", {})[_safe_str(row[0])] = payload
                cur.execute("SELECT conflict_id, knowledge_id, conflicts_with, conflict_type, resolution_policy, payload, created_at FROM bazi_knowledge_conflicts")
                for row in cur.fetchall():
                    payload = {
                        "conflict_id": row[0],
                        "knowledge_id": row[1],
                        "conflicts_with": row[2],
                        "conflict_type": row[3],
                        "resolution_policy": row[4],
                        "payload": row[5],
                        "created_at": _safe_str(row[6]),
                    }
                    snapshot.setdefault("bazi_knowledge_conflicts", {})[_safe_str(row[0])] = payload
        return snapshot

    def save_snapshot(self, snapshot: Dict[str, Any]) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                for collection, rows in snapshot.items():
                    if collection == "audit_events":
                        for event in rows if isinstance(rows, list) else []:
                            if not isinstance(event, dict):
                                continue
                            cur.execute(
                                """
                                INSERT INTO predictive_audit_events
                                (event_hash, previous_event_hash, payload, created_at, rule_id, event_type)
                                VALUES (%s, %s, %s::jsonb, %s, %s, %s)
                                ON CONFLICT (event_hash) DO NOTHING
                                """,
                                (
                                    _safe_str(event.get("event_hash")) or _audit_event_hash(event),
                                    _safe_str(event.get("previous_event_hash")),
                                    self._json_param(event),
                                    _safe_str(event.get("created_at")) or None,
                                    _safe_str(event.get("rule_id")) or None,
                                    _safe_str(event.get("event_type")) or None,
                                ),
                            )
                        continue
                    if not isinstance(rows, dict):
                        continue
                    for item_key, payload in rows.items():
                        if collection == "rules" and isinstance(payload, dict):
                            item_key = _rule_storage_key(_safe_str(payload.get("rule_id")), _safe_str(payload.get("version")))
                        cur.execute(
                            """
                            INSERT INTO predictive_state
                            (collection, item_key, payload, created_at, rule_id, prediction_id, contract_id, insight_id, session_id)
                            VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (collection, item_key) DO UPDATE SET
                                payload = EXCLUDED.payload,
                                created_at = EXCLUDED.created_at,
                                rule_id = EXCLUDED.rule_id,
                                prediction_id = EXCLUDED.prediction_id,
                                contract_id = EXCLUDED.contract_id,
                                insight_id = EXCLUDED.insight_id,
                                session_id = EXCLUDED.session_id
                            """,
                            (
                                collection,
                                _safe_str(item_key),
                                self._json_param(payload),
                                _state_row_created_at(payload) or None,
                                _state_row_rule_id(payload) or None,
                                _state_row_prediction_id(payload) or None,
                                _safe_str(payload.get("contract_id")) if isinstance(payload, dict) else None,
                                _state_row_insight_id(payload) or None,
                                _safe_str(payload.get("agent_session_id") or payload.get("session_id")) if isinstance(payload, dict) else None,
                            ),
                        )
                self._save_bazi_rows(cur, snapshot)
            conn.commit()

    def _save_bazi_rows(self, cur: Any, snapshot: Dict[str, Any]) -> None:
        for payload in (snapshot.get("bazi_knowledge_units") or {}).values():
            if not isinstance(payload, dict):
                continue
            cur.execute(
                """
                INSERT INTO bazi_knowledge_units
                (knowledge_id, domain, category, title, statement, classical_source, modern_interpretation, conditions, feature_mapping, effects, risk_factors, uncertainty_factors, conflicts, confidence_prior, status, created_by, reviewed_by, source_refs, content_hash, created_at, updated_at, reviewed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
                ON CONFLICT (knowledge_id) DO UPDATE SET
                    domain = EXCLUDED.domain,
                    category = EXCLUDED.category,
                    title = EXCLUDED.title,
                    statement = EXCLUDED.statement,
                    classical_source = EXCLUDED.classical_source,
                    modern_interpretation = EXCLUDED.modern_interpretation,
                    conditions = EXCLUDED.conditions,
                    feature_mapping = EXCLUDED.feature_mapping,
                    effects = EXCLUDED.effects,
                    risk_factors = EXCLUDED.risk_factors,
                    uncertainty_factors = EXCLUDED.uncertainty_factors,
                    conflicts = EXCLUDED.conflicts,
                    confidence_prior = EXCLUDED.confidence_prior,
                    status = EXCLUDED.status,
                    created_by = EXCLUDED.created_by,
                    reviewed_by = EXCLUDED.reviewed_by,
                    source_refs = EXCLUDED.source_refs,
                    content_hash = EXCLUDED.content_hash,
                    created_at = EXCLUDED.created_at,
                    updated_at = EXCLUDED.updated_at,
                    reviewed_at = EXCLUDED.reviewed_at
                """,
                (
                    _safe_str(payload.get("knowledge_id")),
                    _safe_str(payload.get("domain")),
                    _safe_str(payload.get("category")),
                    _safe_str(payload.get("title")),
                    _safe_str(payload.get("statement")),
                    _safe_str(payload.get("classical_source")),
                    _safe_str(payload.get("modern_interpretation")),
                    self._json_param(dict(payload.get("conditions") or {})),
                    self._json_param(dict(payload.get("feature_mapping") or {})),
                    self._json_param(dict(payload.get("effects") or {})),
                    self._json_param(_ensure_list(payload.get("risk_factors"))),
                    self._json_param(_ensure_list(payload.get("uncertainty_factors"))),
                    self._json_param(_ensure_list(payload.get("conflicts"))),
                    _safe_float(payload.get("confidence_prior"), 0.0),
                    _safe_str(payload.get("status")),
                    _safe_str(payload.get("created_by")),
                    _safe_str(payload.get("reviewed_by")),
                    self._json_param(_ensure_list(payload.get("source_refs"))),
                    _safe_str(payload.get("content_hash")),
                    _safe_str(payload.get("created_at")) or None,
                    _safe_str(payload.get("updated_at")) or None,
                    _safe_str(payload.get("reviewed_at")) or None,
                ),
            )
        for payload in (snapshot.get("bazi_feature_definitions") or {}).values():
            if not isinstance(payload, dict):
                continue
            cur.execute(
                """
                INSERT INTO bazi_feature_definitions
                (feature_type, domain, title, input_requirements, detection_logic, output_fields, effect_direction, confidence_weight, uncertainty_weight, status, content_hash, created_at, updated_at)
                VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (feature_type) DO UPDATE SET
                    domain = EXCLUDED.domain,
                    title = EXCLUDED.title,
                    input_requirements = EXCLUDED.input_requirements,
                    detection_logic = EXCLUDED.detection_logic,
                    output_fields = EXCLUDED.output_fields,
                    effect_direction = EXCLUDED.effect_direction,
                    confidence_weight = EXCLUDED.confidence_weight,
                    uncertainty_weight = EXCLUDED.uncertainty_weight,
                    status = EXCLUDED.status,
                    content_hash = EXCLUDED.content_hash,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    _safe_str(payload.get("feature_type")),
                    _safe_str(payload.get("domain")),
                    _safe_str(payload.get("title")),
                    self._json_param(dict(payload.get("input_requirements") or {})),
                    self._json_param(dict(payload.get("detection_logic") or {})),
                    self._json_param(_ensure_list(payload.get("output_fields"))),
                    _safe_str(payload.get("effect_direction")),
                    _safe_float(payload.get("confidence_weight"), 0.0),
                    _safe_float(payload.get("uncertainty_weight"), 0.0),
                    _safe_str(payload.get("status")),
                    _safe_str(payload.get("content_hash")),
                    _safe_str(payload.get("created_at")) or None,
                    _safe_str(payload.get("updated_at")) or None,
                ),
            )
        for payload in (snapshot.get("bazi_knowledge_sources") or {}).values():
            if not isinstance(payload, dict):
                continue
            cur.execute(
                """
                INSERT INTO bazi_knowledge_sources
                (source_id, knowledge_id, source_type, title, reference, notes, payload, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                ON CONFLICT (source_id) DO UPDATE SET
                    knowledge_id = EXCLUDED.knowledge_id,
                    source_type = EXCLUDED.source_type,
                    title = EXCLUDED.title,
                    reference = EXCLUDED.reference,
                    notes = EXCLUDED.notes,
                    payload = EXCLUDED.payload,
                    created_at = EXCLUDED.created_at
                """,
                (
                    _safe_str(payload.get("source_id")),
                    _safe_str(payload.get("knowledge_id")),
                    _safe_str(payload.get("source_type")),
                    _safe_str(payload.get("title")),
                    _safe_str(payload.get("reference")),
                    _safe_str(payload.get("notes")),
                    self._json_param(dict(payload.get("payload") or {})),
                    _safe_str(payload.get("created_at")) or None,
                ),
            )
        for payload in (snapshot.get("bazi_knowledge_conflicts") or {}).values():
            if not isinstance(payload, dict):
                continue
            cur.execute(
                """
                INSERT INTO bazi_knowledge_conflicts
                (conflict_id, knowledge_id, conflicts_with, conflict_type, resolution_policy, payload, created_at)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s)
                ON CONFLICT (conflict_id) DO UPDATE SET
                    knowledge_id = EXCLUDED.knowledge_id,
                    conflicts_with = EXCLUDED.conflicts_with,
                    conflict_type = EXCLUDED.conflict_type,
                    resolution_policy = EXCLUDED.resolution_policy,
                    payload = EXCLUDED.payload,
                    created_at = EXCLUDED.created_at
                """,
                (
                    _safe_str(payload.get("conflict_id")),
                    _safe_str(payload.get("knowledge_id")),
                    _safe_str(payload.get("conflicts_with")),
                    _safe_str(payload.get("conflict_type")),
                    _safe_str(payload.get("resolution_policy")),
                    self._json_param(dict(payload.get("payload") or {})),
                    _safe_str(payload.get("created_at")) or None,
                ),
            )


class RedisAccelerator:
    def __init__(self) -> None:
        self.url = _safe_str(os.getenv("PREDICTIVE_REDIS_URL") or os.getenv("REDIS_URL"))
        self.available = False
        self.client: Any = None
        if not self.url:
            return
        try:
            import redis  # type: ignore
            self.client = redis.Redis.from_url(self.url, decode_responses=True)
            self.client.ping()
            self.available = True
        except Exception:
            self.client = None
            self.available = False

    def get_json(self, key: str) -> Any:
        if not self.available:
            return None
        try:
            raw = self.client.get(key)
            return json.loads(raw) if raw else None
        except Exception:
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        if not self.available:
            return
        try:
            self.client.setex(key, ttl_seconds, json.dumps(value, ensure_ascii=False))
        except Exception:
            return

    def delete(self, *keys: str) -> None:
        if not self.available or not keys:
            return
        try:
            self.client.delete(*keys)
        except Exception:
            return

    def acquire_lock(self, key: str, ttl_seconds: int = 30) -> bool:
        if not self.available:
            return True
        try:
            return bool(self.client.set(key, "1", nx=True, ex=ttl_seconds))
        except Exception:
            return True

    def release_lock(self, key: str) -> None:
        self.delete(key)

    def idempotency_get(self, key: str) -> Any:
        return self.get_json(f"idempotency:{key}")

    def idempotency_set(self, key: str, value: Any, ttl_seconds: int = 86400) -> None:
        self.set_json(f"idempotency:{key}", value, ttl_seconds=ttl_seconds)


def _make_storage_adapter(backend: str, dsn: str) -> V18StorageAdapter:
    if backend == "postgres":
        return PostgresStorageAdapter(dsn)
    return JsonStorageAdapter()


def _normalize_claim(claim: Any) -> str:
    if isinstance(claim, str):
        return claim.strip()
    if isinstance(claim, dict):
        claim_id = _safe_str(claim.get("claim_id") or claim.get("id"))
        plugin_id = _safe_str(claim.get("plugin_id") or claim.get("source") or claim.get("plugin"))
        if claim_id and plugin_id:
            return f"{plugin_id}:{claim_id}"
        if claim_id:
            return claim_id
        if plugin_id:
            return plugin_id
        raise ValueError("INVALID_CLAIM_FORMAT")
    raise ValueError("INVALID_CLAIM_FORMAT")


def _normalize_claim_plugin(claim: Any) -> str:
    try:
        text = _normalize_claim(claim)
    except ValueError:
        text = _safe_str(claim)
    if ":" in text:
        return text.split(":", 1)[0]
    return text


def _safe_datetime_iso(payload: Any) -> str:
    dt = _parse_dt(payload)
    if dt is None:
        return _utcnow_iso()
    return dt.replace(microsecond=0).isoformat()


def _parse_dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _normalize_topic(value: Any) -> str:
    topic = str(value or "").strip().lower()
    if topic in {"career", "work", "job", "事业", "事业发展"}:
        return "career"
    if topic in {"relationship", "love", "情感", "伴侣", "感情"}:
        return "relationship"
    if topic in {"wealth", "money", "财运", "财富", "money_income"}:
        return "wealth"
    if topic in {"health", "健康"}:
        return "health"
    return "wealth"


def _to_plain_terms(text: str, *, topic: str) -> List[str]:
    plain = str(text or "").strip()
    if plain:
        return [plain]
    if topic == "wealth":
        return [
            "靠能力把复杂问题变成可计费成果",
            "合作关系会影响收款节奏",
            "先把现金流承接机制做稳再谈放量",
        ]
    if topic == "career":
        return [
            "更适合先做可交付的项目化路径",
            "上级与制度节点会放大你的执行成本",
            "升迁窗口与能力展示时机强相关",
        ]
    if topic == "relationship":
        return [
            "关系中的沟通边界很重要",
            "承诺执行和时间边界决定稳定度",
            "情绪投入要和行动节奏对齐",
        ]
    if topic == "health":
        return [
            "先稳定睡眠、饮食、运动节奏",
            "压力管理会放大体感波动",
            "出现明显不适时尽早复盘与检查",
        ]
    return []


def _feedback_window_from_period(period: Dict[str, Any]) -> Dict[str, str]:
    now = datetime.now(timezone.utc)
    start = _parse_dt(period.get("start_at")) or now
    end = _parse_dt(period.get("end_at")) or (start + timedelta(days=180))
    if end < start:
        end = start
    return {
        "start": start.replace(microsecond=0).isoformat(),
        "end": end.replace(microsecond=0).isoformat(),
    }


def _as_dict(payload: Dict[str, Any], keys: List[str], *, required: bool = True) -> Optional[Dict[str, Any]]:
    out: Dict[str, Any] = {}
    for key in keys:
        if key not in payload:
            if required:
                return None
            continue
        out[key] = payload.get(key)
    return out


@dataclass
class RuleKernel:
    rule_id: str
    theory_family: str
    condition: Dict[str, Any]
    effect: Dict[str, float]
    priority: float
    evidence_strength: float
    conflict_policy: str
    version: str
    owner_plugin: str
    status: str
    content_hash: str
    knowledge_card_id: str = ""
    effect_scope: List[str] = field(default_factory=list)
    allowed_topics: List[str] = field(default_factory=list)
    created_by: str = ""
    created_by_user_id: int = 0
    approved_by: str = ""
    approved_by_user_id: int = 0
    approved_at: str = ""
    created_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "RuleKernel":
        required = [
            "rule_id",
            "theory_family",
            "condition",
            "effect",
            "priority",
            "evidence_strength",
            "conflict_policy",
            "version",
            "owner_plugin",
            "status",
            "effect_scope",
        ]
        missing = [k for k in required if k not in payload]
        if missing:
            raise ValueError(f"REQUIRED_FIELDS_MISSING: {','.join(missing)}")

        status = str(payload["status"]).strip()
        conflict_policy = str(payload["conflict_policy"]).strip()
        if status not in RULE_STATE_VALUES:
            raise ValueError("INVALID_RULE_STATUS")
        if conflict_policy not in RULE_CONFLICT_POLICIES:
            raise ValueError("INVALID_CONFLICT_POLICY")
        allowed_topics = _ensure_list(payload.get("allowed_topics"))
        if not allowed_topics:
            allowed_topics = _ensure_list(payload.get("effect_scope"))
        if not allowed_topics:
            allowed_topics = ["*"]

        candidate = {
            "rule_id": str(payload["rule_id"]).strip(),
            "theory_family": str(payload["theory_family"]).strip(),
            "condition": dict(payload.get("condition") or {}),
            "effect": dict(payload.get("effect") or {}),
            "priority": _safe_float(payload.get("priority"), 0.5),
            "evidence_strength": _safe_float(payload.get("evidence_strength"), 0.5),
            "conflict_policy": conflict_policy,
            "version": str(payload["version"]),
            "owner_plugin": str(payload["owner_plugin"]),
            "status": status,
            "effect_scope": _ensure_list(payload.get("effect_scope")),
            "allowed_topics": allowed_topics,
            "content_hash": _safe_str(payload.get("content_hash")) or "",
            "created_by": _safe_str(payload.get("created_by"), "system"),
            "created_by_user_id": _safe_int(payload.get("created_by_user_id"), 0),
            "approved_by": _safe_str(payload.get("approved_by"), ""),
            "approved_by_user_id": _safe_int(payload.get("approved_by_user_id"), 0),
            "approved_at": _safe_str(payload.get("approved_at"), ""),
            "created_at": _safe_str(payload.get("created_at"), _utcnow_iso()),
            "knowledge_card_id": _safe_str(payload.get("knowledge_card_id"), ""),
        }
        if not candidate["created_at"]:
            candidate["created_at"] = _utcnow_iso()
        candidate["content_hash"] = _rule_payload_fingerprint(candidate)

        return cls(
            **candidate,
        )


@dataclass
class RuleTestCase:
    case_id: str
    source: str = "synthetic"
    chart_snapshot: Dict[str, Any] = field(default_factory=dict)
    query_intent: Dict[str, Any] = field(default_factory=dict)
    expected_conclusions: List[Any] = field(default_factory=list)
    expected_evidence_patterns: List[str] = field(default_factory=list)
    forbidden_conclusions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=_utcnow_iso)
    scenario: str = ""
    expected_active: bool = False
    observed_active: bool = False
    baseline_confidence: float = -1.0
    max_confidence_drift: float = 0.35
    force_verifier_failure: bool = False
    features: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "RuleTestCase":
        case_id = _safe_str(payload.get("case_id"))
        if not case_id:
            raise ValueError("REQUIRED_FIELDS_MISSING: case_id")
        source = _safe_str(payload.get("source"), "synthetic").lower()
        if source not in RULE_TEST_CASE_SOURCES:
            raise ValueError("INVALID_RULE_TEST_CASE_SOURCE")
        return cls(
            case_id=case_id,
            source=source,
            chart_snapshot=dict(payload.get("chart_snapshot") or {}),
            query_intent=dict(payload.get("query_intent") or {}),
            expected_conclusions=_ensure_list(payload.get("expected_conclusions")),
            expected_evidence_patterns=[_safe_str(item) for item in _ensure_list(payload.get("expected_evidence_patterns")) if _safe_str(item)],
            forbidden_conclusions=[_safe_str(item) for item in _ensure_list(payload.get("forbidden_conclusions")) if _safe_str(item)],
            tags=[_safe_str(item) for item in _ensure_list(payload.get("tags")) if _safe_str(item)],
            created_at=_safe_str(payload.get("created_at"), _utcnow_iso()),
            scenario=_safe_str(payload.get("scenario"), source),
            expected_active=_safe_bool(payload.get("expected_active"), default=False),
            observed_active=_safe_bool(payload.get("observed_active"), default=False),
            baseline_confidence=_safe_float(payload.get("baseline_confidence"), -1.0),
            max_confidence_drift=_safe_float(payload.get("max_confidence_drift"), 0.35),
            force_verifier_failure=_safe_bool(payload.get("force_verifier_failure"), False),
            features=dict(payload.get("features") or {}),
        )


@dataclass
class RuleTestSuite:
    suite_id: str
    rule_id: str
    rule_version: str
    title: str
    description: str
    status: str
    version: str
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    content_hash: str = ""
    created_by: str = ""
    created_by_user_id: int = 0
    approved_by: str = ""
    approved_by_user_id: int = 0
    approved_at: str = ""
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "RuleTestSuite":
        required = ["suite_id", "rule_id", "title", "status", "version", "rule_version"]
        missing = [k for k in required if k not in payload]
        if missing:
            raise ValueError(f"REQUIRED_FIELDS_MISSING: {','.join(missing)}")

        status = str(payload["status"]).strip().lower()
        if status not in RULE_TEST_SUITE_STATES:
            raise ValueError("INVALID_RULE_TEST_SUITE_STATUS")

        raw_cases = _ensure_list(payload.get("test_cases") or payload.get("cases"))
        normalized_cases = []
        for item in raw_cases:
            if not isinstance(item, dict):
                continue
            case = dict(item)
            if not case.get("case_id"):
                continue
            normalized_cases.append(case)

        now = _utcnow_iso()
        content_hash = _safe_str(payload.get("content_hash"), "")
        if not content_hash:
            tmp_payload = dict(payload)
            tmp_payload["test_cases"] = normalized_cases
            content_hash = _rule_test_suite_payload_fingerprint(tmp_payload)

        return cls(
            suite_id=str(payload["suite_id"]).strip(),
            rule_id=str(payload["rule_id"]).strip(),
            rule_version=str(payload["rule_version"]).strip(),
            title=str(payload["title"]).strip(),
            description=str(payload.get("description") or "").strip(),
            status=status,
            version=str(payload["version"]),
            test_cases=normalized_cases,
            content_hash=content_hash,
            created_by=_safe_str(payload.get("created_by"), "system"),
            created_by_user_id=_safe_int(payload.get("created_by_user_id"), 0),
            approved_by=_safe_str(payload.get("approved_by"), ""),
            approved_by_user_id=_safe_int(payload.get("approved_by_user_id"), 0),
            approved_at=_safe_str(payload.get("approved_at"), ""),
            created_at=_safe_str(payload.get("created_at"), now),
            updated_at=_safe_str(payload.get("updated_at"), now),
        )


@dataclass
class KnowledgeCard:
    card_id: str
    knowledge_domain: str
    title: str
    summary: str
    status: str
    version: str
    source_refs: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    content: Dict[str, Any] = field(default_factory=dict)
    content_hash: str = ""
    created_by: str = ""
    created_by_user_id: int = 0
    approved_by: str = ""
    approved_by_user_id: int = 0
    approved_at: str = ""
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "KnowledgeCard":
        required = ["card_id", "knowledge_domain", "title", "summary", "status", "version"]
        missing = [k for k in required if k not in payload]
        if missing:
            raise ValueError(f"REQUIRED_FIELDS_MISSING: {','.join(missing)}")

        status = str(payload["status"]).strip().lower()
        if status not in KNOWLEDGE_CARD_STATES:
            raise ValueError("INVALID_KNOWLEDGE_CARD_STATUS")
        now = _utcnow_iso()
        content = dict(payload.get("content") or {})
        tags = _ensure_list(payload.get("tags"))
        source_refs = _ensure_list(payload.get("source_refs"))
        content_hash = _safe_str(payload.get("content_hash"), "")
        content_hash = content_hash if content_hash else _knowledge_card_content_fingerprint(payload)
        return cls(
            card_id=str(payload["card_id"]).strip(),
            knowledge_domain=str(payload["knowledge_domain"]).strip(),
            title=str(payload["title"]).strip(),
            summary=str(payload.get("summary") or "").strip(),
            status=status,
            version=str(payload["version"]),
            source_refs=source_refs,
            tags=tags,
            content=content,
            content_hash=content_hash,
            created_by=_safe_str(payload.get("created_by"), "system"),
            created_by_user_id=_safe_int(payload.get("created_by_user_id"), 0),
            approved_by=_safe_str(payload.get("approved_by"), ""),
            approved_by_user_id=_safe_int(payload.get("approved_by_user_id"), 0),
            approved_at=_safe_str(payload.get("approved_at"), ""),
            created_at=_safe_str(payload.get("created_at"), now),
            updated_at=_safe_str(payload.get("updated_at"), now),
        )


@dataclass
class BaziFeatureDefinition:
    feature_type: str
    domain: str
    title: str
    input_requirements: Dict[str, Any]
    detection_logic: Dict[str, Any]
    output_fields: List[str]
    effect_direction: str
    confidence_weight: float
    uncertainty_weight: float
    status: str = "reviewed"
    content_hash: str = ""
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "BaziFeatureDefinition":
        required = [
            "feature_type",
            "domain",
            "title",
            "input_requirements",
            "detection_logic",
            "output_fields",
            "effect_direction",
            "confidence_weight",
            "uncertainty_weight",
        ]
        missing = [key for key in required if key not in payload]
        if missing:
            raise ValueError(f"REQUIRED_FIELDS_MISSING: {','.join(missing)}")
        feature_type = _safe_str(payload.get("feature_type"))
        if feature_type not in BAZI_FEATURE_TYPES:
            raise ValueError("INVALID_BAZI_FEATURE_TYPE")
        domain = _safe_str(payload.get("domain"), "wealth")
        if domain not in BAZI_KNOWLEDGE_DOMAINS:
            raise ValueError("INVALID_BAZI_KNOWLEDGE_DOMAIN")
        status = _safe_str(payload.get("status"), "reviewed")
        if status not in BAZI_KNOWLEDGE_STATES:
            raise ValueError("INVALID_BAZI_KNOWLEDGE_STATUS")
        now = _utcnow_iso()
        content_hash = _safe_str(payload.get("content_hash")) or _feature_definition_content_fingerprint(payload)
        return cls(
            feature_type=feature_type,
            domain=domain,
            title=_safe_str(payload.get("title")),
            input_requirements=dict(payload.get("input_requirements") or {}),
            detection_logic=dict(payload.get("detection_logic") or {}),
            output_fields=[_safe_str(item) for item in _ensure_list(payload.get("output_fields")) if _safe_str(item)],
            effect_direction=_safe_str(payload.get("effect_direction")),
            confidence_weight=_safe_float(payload.get("confidence_weight"), 0.5),
            uncertainty_weight=_safe_float(payload.get("uncertainty_weight"), 0.3),
            status=status,
            content_hash=content_hash,
            created_at=_safe_str(payload.get("created_at"), now),
            updated_at=_safe_str(payload.get("updated_at"), now),
        )


@dataclass
class BaziKnowledgeUnit:
    knowledge_id: str
    domain: str
    category: str
    title: str
    statement: str
    classical_source: str
    modern_interpretation: str
    conditions: Dict[str, Any]
    feature_mapping: Dict[str, Any]
    effects: Dict[str, Any]
    risk_factors: List[str]
    uncertainty_factors: List[str]
    conflicts: List[str]
    confidence_prior: float
    status: str = "draft"
    created_by: str = "system"
    reviewed_by: str = ""
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)
    reviewed_at: str = ""
    content_hash: str = ""
    source_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "BaziKnowledgeUnit":
        required = [
            "knowledge_id",
            "domain",
            "category",
            "title",
            "statement",
            "classical_source",
            "modern_interpretation",
            "conditions",
            "feature_mapping",
            "effects",
            "risk_factors",
            "uncertainty_factors",
            "conflicts",
            "confidence_prior",
        ]
        missing = [key for key in required if key not in payload]
        if missing:
            raise ValueError(f"REQUIRED_FIELDS_MISSING: {','.join(missing)}")
        domain = _safe_str(payload.get("domain"))
        if domain not in BAZI_KNOWLEDGE_DOMAINS:
            raise ValueError("INVALID_BAZI_KNOWLEDGE_DOMAIN")
        category = _safe_str(payload.get("category"))
        if category not in BAZI_KNOWLEDGE_CATEGORIES:
            raise ValueError("INVALID_BAZI_KNOWLEDGE_CATEGORY")
        status = _safe_str(payload.get("status"), "draft")
        if status not in BAZI_KNOWLEDGE_STATES:
            raise ValueError("INVALID_BAZI_KNOWLEDGE_STATUS")
        feature_mapping = dict(payload.get("feature_mapping") or {})
        required_mapping = [
            "feature_type",
            "input_requirements",
            "detection_logic",
            "output_fields",
            "effect_direction",
            "confidence_weight",
            "uncertainty_weight",
        ]
        missing_mapping = [key for key in required_mapping if key not in feature_mapping]
        if missing_mapping:
            raise ValueError(f"FEATURE_MAPPING_FIELDS_MISSING: {','.join(missing_mapping)}")
        feature_type = _safe_str(feature_mapping.get("feature_type"))
        if feature_type not in BAZI_FEATURE_TYPES:
            raise ValueError("INVALID_BAZI_FEATURE_TYPE")
        now = _utcnow_iso()
        content_hash = _safe_str(payload.get("content_hash")) or _bazi_knowledge_content_fingerprint(payload)
        return cls(
            knowledge_id=_safe_str(payload.get("knowledge_id")),
            domain=domain,
            category=category,
            title=_safe_str(payload.get("title")),
            statement=_safe_str(payload.get("statement")),
            classical_source=_safe_str(payload.get("classical_source")),
            modern_interpretation=_safe_str(payload.get("modern_interpretation")),
            conditions=dict(payload.get("conditions") or {}),
            feature_mapping=feature_mapping,
            effects=dict(payload.get("effects") or {}),
            risk_factors=[_safe_str(item) for item in _ensure_list(payload.get("risk_factors")) if _safe_str(item)],
            uncertainty_factors=[_safe_str(item) for item in _ensure_list(payload.get("uncertainty_factors")) if _safe_str(item)],
            conflicts=[_safe_str(item) for item in _ensure_list(payload.get("conflicts")) if _safe_str(item)],
            confidence_prior=self_clamped(payload.get("confidence_prior"), 0.5),
            status=status,
            created_by=_safe_str(payload.get("created_by"), "system"),
            reviewed_by=_safe_str(payload.get("reviewed_by"), ""),
            created_at=_safe_str(payload.get("created_at"), now),
            updated_at=_safe_str(payload.get("updated_at"), now),
            reviewed_at=_safe_str(payload.get("reviewed_at"), ""),
            content_hash=content_hash,
            source_refs=[_safe_str(item) for item in _ensure_list(payload.get("source_refs")) if _safe_str(item)],
        )


def self_clamped(value: Any, fallback: float = 0.0) -> float:
    return max(0.0, min(1.0, _safe_float(value, fallback)))


def _energy_clamp_value(
    value: Any,
    *,
    fallback: float = 0.0,
    signed: bool = False,
) -> Dict[str, Any]:
    min_value = ENERGY_CLAMP_LIMITS["signed_min"] if signed else ENERGY_CLAMP_LIMITS["unsigned_min"]
    max_value = ENERGY_CLAMP_LIMITS["signed_max"] if signed else ENERGY_CLAMP_LIMITS["unsigned_max"]
    raw_abs_max = ENERGY_CLAMP_LIMITS["raw_abs_max"]
    reason = "ok"
    try:
        raw = float(value)
    except (TypeError, ValueError):
        raw = float(fallback)
        reason = "invalid_number"
    if not math.isfinite(raw):
        raw = float(fallback)
        reason = "non_finite"
    if abs(raw) > raw_abs_max:
        raw = max_value if raw > 0 else min_value
        reason = "overflow_guard"
    clamped = max(min_value, min(max_value, raw))
    if clamped != raw and reason == "ok":
        reason = "range_clamped"
    return {
        "value": round(clamped, 6),
        "clamped": reason != "ok",
        "reason": reason,
        "signed": signed,
        "limits": {
            "min": min_value,
            "max": max_value,
            "raw_abs_max": raw_abs_max,
        },
    }


def _bazi_feature_mapping(
    feature_type: str,
    *,
    input_requirements: List[str],
    detection_logic: Dict[str, Any],
    output_fields: List[str],
    effect_direction: str,
    confidence_weight: float,
    uncertainty_weight: float,
) -> Dict[str, Any]:
    return {
        "feature_type": feature_type,
        "input_requirements": input_requirements,
        "detection_logic": detection_logic,
        "output_fields": output_fields,
        "effect_direction": effect_direction,
        "confidence_weight": confidence_weight,
        "uncertainty_weight": uncertainty_weight,
    }


WEALTH_FEATURE_DEFINITIONS_V1: List[Dict[str, Any]] = [
    {
        "feature_type": "wealth_strength",
        "domain": "wealth",
        "title": "财星强弱",
        "input_requirements": {"required": ["ten_gods_runtime", "root_visibility", "season_strength"]},
        "detection_logic": {"score_from": ["正财", "偏财", "透干", "藏支", "有根"]},
        "output_fields": ["strength", "stability", "matched_facts", "wealth_relevance"],
        "effect_direction": "support_or_risk_by_body_strength",
        "confidence_weight": 0.78,
        "uncertainty_weight": 0.3,
    },
    {
        "feature_type": "wealth_vault_activation",
        "domain": "wealth",
        "title": "财库与库门状态",
        "input_requirements": {"required": ["earth_branches", "vault_branch", "relation_events"]},
        "detection_logic": {"score_from": ["辰戌丑未", "冲开", "被合", "透财"]},
        "output_fields": ["vault_state", "activation", "stability", "risk"],
        "effect_direction": "wealth_retention_and_timing",
        "confidence_weight": 0.72,
        "uncertainty_weight": 0.38,
    },
    {
        "feature_type": "wealth_vault_state",
        "domain": "wealth",
        "title": "财库状态",
        "input_requirements": {"required": ["relation_hits", "structure_effect_bundle", "vault_branch"]},
        "detection_logic": {"score_from": ["closed_storable", "closed_inactive", "opened_by_clash", "locked_by_combination", "blocked", "conflicted"]},
        "output_fields": ["vault_presence", "vault_state", "liquidity", "stability", "risk", "uncertainty"],
        "effect_direction": "wealth_storage_liquidity_and_release",
        "confidence_weight": 0.85,
        "uncertainty_weight": 0.15,
    },
    {
        "feature_type": "output_generate_wealth",
        "domain": "wealth",
        "title": "食伤生财",
        "input_requirements": {"required": ["食神", "伤官", "正财", "偏财", "body_strength"]},
        "detection_logic": {"score_from": ["食伤强度", "财星承接", "印星抑制", "身强身弱"]},
        "output_fields": ["output_strength", "wealth_channel", "risk", "uncertainty"],
        "effect_direction": "earning_opportunity",
        "confidence_weight": 0.74,
        "uncertainty_weight": 0.35,
    },
    {
        "feature_type": "wealth_constraint",
        "domain": "wealth",
        "title": "官杀与印比对财富结构的制约",
        "input_requirements": {"required": ["官杀", "印星", "比劫", "财星", "body_strength"]},
        "detection_logic": {"score_from": ["官杀制约", "印克食伤", "比劫夺财", "财官相生"]},
        "output_fields": ["constraint_type", "risk", "stability", "effect"],
        "effect_direction": "constraint_or_platform",
        "confidence_weight": 0.68,
        "uncertainty_weight": 0.42,
    },
    {
        "feature_type": "peer_competition",
        "domain": "wealth",
        "title": "比劫竞争与资源分配",
        "input_requirements": {"required": ["ten_god_mapping", "strength_model", "wealth_strength"]},
        "detection_logic": {"score_from": ["比肩", "劫财", "peer_strength", "competition_pressure", "resource_distribution_risk"]},
        "output_fields": ["peer_strength", "competition_pressure", "resource_distribution_risk", "cooperation_signal", "risk"],
        "effect_direction": "competition_or_distribution_modifier",
        "confidence_weight": 0.7,
        "uncertainty_weight": 0.3,
    },
    {
        "feature_type": "wealth_flow_activation",
        "domain": "wealth",
        "title": "大运流年引动",
        "input_requirements": {"required": ["luck_pillar", "flow_year", "natal_wealth_features"]},
        "detection_logic": {"score_from": ["财星引动", "财库引动", "合冲刑害触发"]},
        "output_fields": ["timing_activation", "flow_state", "risk", "stability"],
        "effect_direction": "timing_window",
        "confidence_weight": 0.64,
        "uncertainty_weight": 0.48,
    },
    {
        "feature_type": "wealth_stability",
        "domain": "wealth",
        "title": "财富稳定性",
        "input_requirements": {"required": ["relation_events", "cashflow_structure", "vault_state"]},
        "detection_logic": {"score_from": ["合局", "冲", "刑害", "库门状态"]},
        "output_fields": ["stability", "risk", "matched_facts"],
        "effect_direction": "stability_modifier",
        "confidence_weight": 0.62,
        "uncertainty_weight": 0.5,
    },
    {
        "feature_type": "wealth_risk",
        "domain": "wealth",
        "title": "财富风险来源",
        "input_requirements": {"required": ["conflict_events", "body_strength", "resource_constraints"]},
        "detection_logic": {"score_from": ["财旺身弱", "食伤太过", "比劫夺财", "刑害"]},
        "output_fields": ["risk", "risk_source", "uncertainty"],
        "effect_direction": "risk_modifier",
        "confidence_weight": 0.66,
        "uncertainty_weight": 0.52,
    },
]


def _wealth_kb_unit(
    suffix: str,
    *,
    category: str,
    title: str,
    statement: str,
    feature_type: str,
    conditions: Dict[str, Any],
    effects: Dict[str, Any],
    risk_factors: List[str],
    uncertainty_factors: List[str],
    conflicts: List[str],
    confidence_prior: float,
    classical_source: str = "古典八字通用规则",
    modern_interpretation: str = "",
) -> Dict[str, Any]:
    return {
        "knowledge_id": f"wealth.{suffix}",
        "domain": "wealth",
        "category": category,
        "title": title,
        "statement": statement,
        "classical_source": classical_source,
        "modern_interpretation": modern_interpretation or statement,
        "conditions": conditions,
        "feature_mapping": _bazi_feature_mapping(
            feature_type,
            input_requirements=["four_pillars", "ten_gods_runtime", "root_visibility", "luck_flow_context"],
            detection_logic={"category": category, "conditions": conditions},
            output_fields=["feature_id", "feature_type", "matched_facts", "strength", "stability", "effect", "risk", "uncertainty", "wealth_relevance"],
            effect_direction="support" if effects.get("wealth", 0) >= 0 else "risk",
            confidence_weight=confidence_prior,
            uncertainty_weight=max(0.05, round(1.0 - confidence_prior, 2)),
        ),
        "effects": effects,
        "risk_factors": risk_factors,
        "uncertainty_factors": uncertainty_factors,
        "conflicts": conflicts,
        "confidence_prior": confidence_prior,
        "status": "draft",
        "created_by": "wealth_kb_seed_v1",
        "source_refs": ["docs:bazi_knowledge/wealth/wealth_units_v1.md"],
    }


WEALTH_KNOWLEDGE_UNITS_V1: List[Dict[str, Any]] = [
    _wealth_kb_unit("001_wealth_star_strength", category="wealth_star", title="财星强弱", statement="财星强弱代表财富资源显隐与可承接程度，但必须结合身强身弱与根气判断。", feature_type="wealth_strength", conditions={"wealth_star": "visible_or_scored", "body_strength_required": True}, effects={"wealth": 0.62, "income_stability": 0.34}, risk_factors=["财旺身弱时承接压力增大"], uncertainty_factors=["需判断日主强弱", "需区分正财偏财"], conflicts=["比劫夺财", "印星过强"], confidence_prior=0.72),
    _wealth_kb_unit("002_wealth_star_visible_stem", category="wealth_star", title="财星透干", statement="财星透干通常表示财富议题更容易外显，收入机会更容易被看见。", feature_type="wealth_strength", conditions={"wealth_star": "heavenly_stem_visible"}, effects={"wealth": 0.58, "opportunity_visibility": 0.62}, risk_factors=["透而无根时稳定性不足"], uncertainty_factors=["需看地支根气", "需看是否被合克"], conflicts=["财星被合", "比劫透出"], confidence_prior=0.68),
    _wealth_kb_unit("003_wealth_star_hidden_branch", category="wealth_star", title="财星藏支", statement="财星藏支偏向潜在资源或内在财富结构，需要运岁或关系触发后更明显。", feature_type="wealth_strength", conditions={"wealth_star": "hidden_in_branch"}, effects={"wealth": 0.42, "timing_dependency": 0.56}, risk_factors=["机会不一定即时兑现"], uncertainty_factors=["需看是否透出", "需看运岁引动"], conflicts=["库门闭合", "冲动过强"], confidence_prior=0.62),
    _wealth_kb_unit("004_wealth_has_root", category="wealth_star", title="财星有根", statement="财星有根时财富信号更稳定，较容易形成可持续收入结构。", feature_type="wealth_strength", conditions={"wealth_star_root": "rooted"}, effects={"wealth": 0.68, "income_stability": 0.58}, risk_factors=["过旺时仍需身能承财"], uncertainty_factors=["根气强弱需量化"], conflicts=["财旺身弱", "冲根"], confidence_prior=0.74),
    _wealth_kb_unit("005_wealth_no_root", category="wealth_star", title="财星无根", statement="财星无根时财富机会可能存在，但稳定兑现与留存能力需要谨慎评估。", feature_type="wealth_risk", conditions={"wealth_star_root": "rootless"}, effects={"wealth": 0.24, "risk": 0.48, "income_stability": -0.28}, risk_factors=["机会虚浮", "回款不稳"], uncertainty_factors=["需看大运补根", "需看食伤承接"], conflicts=["大运引动财星"], confidence_prior=0.63),
    _wealth_kb_unit("006_wealth_vault", category="wealth_vault", title="财库", statement="财库代表财富储藏、资金沉淀或资产容器，但库本身不等于自动发财。", feature_type="wealth_vault_activation", conditions={"vault_branch": "辰戌丑未", "wealth_relation": "present"}, effects={"wealth_retention": 0.62, "income_stability": 0.42}, risk_factors=["库闭则兑现慢"], uncertainty_factors=["需判断库中所藏与日主关系"], conflicts=["财库被合", "冲开过烈"], confidence_prior=0.7),
    _wealth_kb_unit("007_wealth_vault_opened_by_clash", category="wealth_vault", title="财库冲开", statement="财库被适度冲开时可能带来资金流动或兑现窗口，但过冲也会增加波动。", feature_type="wealth_vault_activation", conditions={"vault_state": "opened_by_clash"}, effects={"wealth": 0.52, "timing_activation": 0.66, "risk": 0.36}, risk_factors=["过冲导致破库或资金外泄"], uncertainty_factors=["需看冲的力量与喜忌"], conflicts=["刑害同来", "身弱财旺"], confidence_prior=0.66),
    _wealth_kb_unit("008_wealth_vault_combined", category="wealth_vault", title="财库被合", statement="财库被合时财富结构可能被关系、合作或环境锁住，兑现节奏变慢。", feature_type="wealth_stability", conditions={"vault_state": "combined_or_locked"}, effects={"wealth_stability": -0.28, "risk": 0.42}, risk_factors=["资金被锁", "合作分配不清"], uncertainty_factors=["需看合化是否成立"], conflicts=["流年冲开", "透财有力"], confidence_prior=0.62),
    _wealth_kb_unit("009_output_generate_wealth", category="output_generate_wealth", title="食伤生财", statement="食伤能生财时，才华、输出、产品化能力可转化为赚钱路径。", feature_type="output_generate_wealth", conditions={"output_star": "strong", "wealth_star": "present"}, effects={"wealth": 0.72, "earning_opportunity": 0.72}, risk_factors=["食伤过强可能泄身"], uncertainty_factors=["需看财星承接", "需看身强身弱"], conflicts=["印星克制食伤", "财星无根"], confidence_prior=0.76),
    _wealth_kb_unit("010_excess_output_leaks_body", category="output_generate_wealth", title="食伤太过泄身", statement="食伤过旺而身弱时，输出很多但承财能力不足，容易劳多获少或现金流不稳。", feature_type="wealth_risk", conditions={"output_star": "excessive", "body_strength": "weak"}, effects={"wealth": -0.18, "risk": 0.58, "income_stability": -0.42}, risk_factors=["过度消耗", "变现效率低"], uncertainty_factors=["需看印比是否扶身"], conflicts=["身旺可任输出", "财星有根"], confidence_prior=0.69),
    _wealth_kb_unit("011_authority_constraint", category="constraint_structure", title="官杀制约财富", statement="官杀结构会影响财富路径的制度、平台、规则和压力边界。", feature_type="wealth_constraint", conditions={"authority_star": "active", "wealth_path": "present"}, effects={"wealth": 0.36, "constraint": 0.58, "risk": 0.34}, risk_factors=["制度压力", "合规成本"], uncertainty_factors=["需看官杀为喜为忌"], conflicts=["食神制杀", "财官相生"], confidence_prior=0.66),
    _wealth_kb_unit("012_resource_blocks_output", category="constraint_structure", title="印星克制食伤影响生财", statement="印星过强可能抑制食伤输出，使输出生财路径不顺或产品化受阻。", feature_type="wealth_constraint", conditions={"resource_star": "strong", "output_star": "blocked"}, effects={"earning_opportunity": -0.32, "risk": 0.42}, risk_factors=["想法多但交付慢", "表达受限"], uncertainty_factors=["需看印星是否为用"], conflicts=["伤官配印", "身弱喜印"], confidence_prior=0.64),
    _wealth_kb_unit("013_peer_robs_wealth", category="constraint_structure", title="比劫夺财", statement="比劫强而财星受压时，财富容易受到竞争、分利或人际消耗影响。", feature_type="wealth_risk", conditions={"peer_star": "strong", "wealth_star": "contested"}, effects={"wealth": -0.22, "risk": 0.64, "wealth_stability": -0.44}, risk_factors=["竞争分利", "合作消耗"], uncertainty_factors=["需看是否有官杀制比劫"], conflicts=["官杀制劫", "团队协作变现"], confidence_prior=0.71),
    _wealth_kb_unit("014_wealth旺_body_weak", category="wealth_star", title="财旺身弱", statement="财旺身弱表示财富机会或压力大于承接能力，宜关注风险控制。", feature_type="wealth_risk", conditions={"wealth_star": "strong", "body_strength": "weak"}, effects={"wealth": 0.18, "risk": 0.66, "income_stability": -0.36}, risk_factors=["机会过载", "负债或回款压力"], uncertainty_factors=["需看扶身运"], conflicts=["比印扶身", "财官结构清"], confidence_prior=0.73),
    _wealth_kb_unit("015_body_strong_wealth_weak", category="wealth_star", title="身旺财弱", statement="身旺财弱时行动力或承接力可能有余，但财富目标、资源入口或市场机会不足。", feature_type="wealth_strength", conditions={"body_strength": "strong", "wealth_star": "weak"}, effects={"wealth": 0.32, "opportunity_visibility": -0.24}, risk_factors=["忙而收益少", "资源入口窄"], uncertainty_factors=["需看食伤是否能生财"], conflicts=["大运见财", "食伤生财"], confidence_prior=0.65),
    _wealth_kb_unit("016_wealth_authority_mutual_support", category="constraint_structure", title="财官相生", statement="财官相生可表示财富与职位、平台、规则资源互相支持。", feature_type="wealth_constraint", conditions={"wealth_star": "present", "authority_star": "ordered"}, effects={"wealth": 0.56, "income_stability": 0.48}, risk_factors=["规则依赖强"], uncertainty_factors=["需看官杀清浊"], conflicts=["伤官见官", "比劫夺财"], confidence_prior=0.69),
    _wealth_kb_unit("017_luck_activates_wealth", category="luck_flow_activation", title="大运引动财星", statement="大运引动财星时，财富议题在该阶段更容易成为主线。", feature_type="wealth_flow_activation", conditions={"luck_pillar": "activates_wealth_star"}, effects={"wealth": 0.58, "timing_activation": 0.72}, risk_factors=["引动忌神财时压力增大"], uncertainty_factors=["需看原局承接条件"], conflicts=["财旺身弱", "比劫夺财"], confidence_prior=0.67),
    _wealth_kb_unit("018_flow_activates_vault", category="luck_flow_activation", title="流年引动财库", statement="流年引动财库可能形成资产、回款、储蓄或资金结构变化的窗口。", feature_type="wealth_flow_activation", conditions={"flow_year": "activates_wealth_vault"}, effects={"wealth_retention": 0.5, "timing_activation": 0.68, "risk": 0.28}, risk_factors=["冲合不稳时资金波动"], uncertainty_factors=["需看库门开合状态"], conflicts=["财库被合", "刑冲过重"], confidence_prior=0.64),
    _wealth_kb_unit("019_combination_changes_stability", category="combination_clash_stability", title="合局导致财富稳定性变化", statement="合局会改变财富结构的稳定性，可能形成合作承接，也可能锁住兑现。", feature_type="wealth_stability", conditions={"combination": "active", "wealth_related": True}, effects={"wealth_stability": 0.18, "risk": 0.32}, risk_factors=["合作绑定", "利益分配不清"], uncertainty_factors=["需看合化是否成立"], conflicts=["冲破合局", "比劫夺财"], confidence_prior=0.61),
    _wealth_kb_unit("020_clash_changes_liquidity", category="combination_clash_stability", title="冲导致财富流动性变化", statement="冲会带来财富结构流动性变化，可能打开机会，也可能造成损耗。", feature_type="wealth_stability", conditions={"clash": "wealth_related"}, effects={"wealth_stability": -0.22, "timing_activation": 0.42, "risk": 0.48}, risk_factors=["突发支出", "回款波动"], uncertainty_factors=["需看冲的位置与力量"], conflicts=["有制有化", "库门适度打开"], confidence_prior=0.62),
    _wealth_kb_unit("021_punishment_harm_risk", category="combination_clash_stability", title="刑害导致财富风险", statement="刑害更偏隐性摩擦、合同瑕疵或关系损耗，会提高财富风险。", feature_type="wealth_risk", conditions={"punishment_or_harm": "wealth_related"}, effects={"risk": 0.6, "wealth_stability": -0.38}, risk_factors=["暗耗", "争议", "信任成本"], uncertainty_factors=["需看是否成局与是否触发财星"], conflicts=["规则化合同", "官星约束"], confidence_prior=0.66),
    _wealth_kb_unit("022_wealth_in_spouse_palace", category="wealth_star", title="财在夫妻宫", statement="财在夫妻宫或伴侣位相关时，财富来源可能与伴侣、合作、客户关系更相关。", feature_type="wealth_strength", conditions={"wealth_position": "spouse_palace_or_partner_axis"}, effects={"wealth": 0.44, "relationship_wealth_link": 0.62}, risk_factors=["亲密关系与利益边界混合"], uncertainty_factors=["需看宫位受冲合"], conflicts=["夫妻宫受刑害", "比劫争财"], confidence_prior=0.6),
    _wealth_kb_unit("023_inside_outside_wealth_source", category="wealth_star", title="家内家外财富来源", statement="财星所在位置会影响财富来源偏家内资源、稳定薪酬、外部市场或远方机会。", feature_type="wealth_strength", conditions={"wealth_position": "inside_outside_axis"}, effects={"wealth": 0.4, "source_type_signal": 0.62}, risk_factors=["来源判断需避免单点决定"], uncertainty_factors=["需结合十神、宫位与大运"], conflicts=["流年迁移触发", "合冲改变位置含义"], confidence_prior=0.58),
]


def _reviewed_core_wealth_unit(
    suffix: str,
    *,
    category: str,
    title: str,
    statement: str,
    feature_type: str,
    output_fields: List[str],
    effect_direction: str,
    conditions: Dict[str, Any],
    effects: Dict[str, Any],
    risk_factors: List[str],
    uncertainty_factors: List[str],
    conflicts: List[str],
    confidence_prior: float,
) -> Dict[str, Any]:
    payload = _wealth_kb_unit(
        suffix,
        category=category,
        title=title,
        statement=statement,
        feature_type=feature_type,
        conditions={
            **conditions,
            "knowledge_version": "core_wealth_v1",
            "runtime_policy": "feature_evidence_only",
            "prediction_runtime": "disabled_until_rule_activation",
        },
        effects=effects,
        risk_factors=risk_factors,
        uncertainty_factors=uncertainty_factors,
        conflicts=conflicts,
        confidence_prior=confidence_prior,
        classical_source="owner-reviewed classical bazi wealth model",
        modern_interpretation=statement,
    )
    payload["status"] = "reviewed"
    payload["created_by"] = "owner_codex_reviewed_core_wealth_v1"
    payload["reviewed_by"] = "owner"
    payload["reviewed_at"] = "2026-04-28T00:00:00+00:00"
    payload["source_refs"] = ["docs:bazi_knowledge/wealth/wealth_units_v1.md#core-wealth-v1"]
    payload["feature_mapping"] = _bazi_feature_mapping(
        feature_type,
        input_requirements=["core_feature_bundle", "core_strength_bundle", "core_structure_effect_bundle"],
        detection_logic={
            "knowledge_id": payload["knowledge_id"],
            "knowledge_version": "core_wealth_v1",
            "mode": "structured_feature_mapping",
            "conditions": payload["conditions"],
            "no_direct_conclusion": True,
        },
        output_fields=output_fields,
        effect_direction=effect_direction,
        confidence_weight=confidence_prior,
        uncertainty_weight=max(0.05, round(1.0 - confidence_prior, 2)),
    )
    return payload


WEALTH_CORE_KNOWLEDGE_UNITS_V1: List[Dict[str, Any]] = [
    _reviewed_core_wealth_unit(
        "wealth_strength",
        category="wealth_star",
        title="财星强弱",
        statement="财星代表资源获取与价值交换能力，其状态决定财富潜力基础。",
        feature_type="wealth_strength",
        output_fields=["wealth_strength_score", "wealth_presence"],
        effect_direction="wealth_potential_foundation",
        conditions={"inputs": ["ten_god_mapping", "root_strength", "month_command"]},
        effects={"wealth_potential": 0.8, "structure_stability": 0.42},
        risk_factors=["财强身弱 → 承载风险", "latent → 机会难以转化"],
        uncertainty_factors=["依赖日主承载力", "依赖结构引动"],
        conflicts=["印星抑制", "比劫分夺"],
        confidence_prior=0.8,
    ),
    _reviewed_core_wealth_unit(
        "output_generate_wealth",
        category="output_generate_wealth",
        title="食伤生财",
        statement="食伤代表输出与创造，其与财的连接决定变现路径。",
        feature_type="output_generate_wealth",
        output_fields=["output_strength_score", "output_to_wealth_link_strength", "conversion_path"],
        effect_direction="earning_opportunity_and_conversion_path",
        conditions={"inputs": ["ten_god_mapping", "root_strength", "strength_model"]},
        effects={"earning_opportunity": 0.75, "conversion_support": 0.62},
        risk_factors=["输出强但 blocked → 有能力但无法变现", "输出过旺 → 泄身"],
        uncertainty_factors=["依赖财星是否存在", "依赖结构支持"],
        conflicts=["印抑制输出", "官杀限制表达"],
        confidence_prior=0.75,
    ),
    _reviewed_core_wealth_unit(
        "wealth_vault",
        category="wealth_vault",
        title="财库",
        statement="墓库结构决定财富的储存、流动与释放方式。",
        feature_type="wealth_vault_state",
        output_fields=["vault_presence", "vault_state"],
        effect_direction="wealth_storage_liquidity_and_release",
        conditions={"inputs": ["relation_hits", "structure_effect_bundle"]},
        effects={"wealth_retention": 0.85, "liquidity_modifier": 0.48, "uncertainty": 0.22},
        risk_factors=["冲过强 → 波动", "合过强 → 难变现"],
        uncertainty_factors=["合冲同时存在", "依赖岁运触发"],
        conflicts=["冲 vs 合", "多结构叠加"],
        confidence_prior=0.85,
    ),
    _reviewed_core_wealth_unit(
        "peer_competition",
        category="constraint_structure",
        title="比劫竞争",
        statement="比劫代表同类竞争与资源分配机制。",
        feature_type="peer_competition",
        output_fields=["peer_strength", "competition_pressure", "resource_distribution_risk"],
        effect_direction="competition_or_distribution_modifier",
        conditions={"inputs": ["ten_god_mapping", "strength_model"]},
        effects={"competition_pressure": 0.7, "resource_distribution_risk": 0.52},
        risk_factors=["competition_pressure 高 → 收入不稳定", "distribution_risk 高 → 财富分散"],
        uncertainty_factors=["合作 vs 竞争方向"],
        conflicts=["财星强 → 可抵消", "官杀 → 约束竞争"],
        confidence_prior=0.7,
    ),
    _reviewed_core_wealth_unit(
        "constraint_structure",
        category="constraint_structure",
        title="官杀制约财富",
        statement="官杀代表规则、约束与结构压力，对财富路径产生规范或限制作用。",
        feature_type="wealth_constraint",
        output_fields=["constraint_strength", "constraint_effects"],
        effect_direction="risk_stabilization_or_income_pressure",
        conditions={"inputs": ["ten_god_mapping", "strength_model"]},
        effects={"stabilize_risk": 0.56, "pressure_income": 0.42, "formalize_path": 0.48},
        risk_factors=["约束过强 → 收入压制", "约束过弱 → 风险增加"],
        uncertainty_factors=["官杀与日主关系", "是否形成制化"],
        conflicts=["食伤冲官", "印化官杀"],
        confidence_prior=0.75,
    ),
]

WEALTH_KNOWLEDGE_UNITS_V1.extend(WEALTH_CORE_KNOWLEDGE_UNITS_V1)
WEALTH_CORE_REVIEWED_KNOWLEDGE_UNIT_IDS: List[str] = [
    unit["knowledge_id"] for unit in WEALTH_CORE_KNOWLEDGE_UNITS_V1
]


@dataclass
class RuleKernelAuditEvent:
    rule_id: str
    event_type: str
    severity: str
    message: str
    actor_role: str
    actor_user_id: int
    created_at: str = field(default_factory=_utcnow_iso)
    source: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    event_hash: str = ""
    previous_event_hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RuleResolverInput:
    prediction_id: str
    topic: str
    plugin_claims: List[str]
    rule_candidates: List[Dict[str, Any]]
    runtime_context: Dict[str, Any]
    lifecycle_token: str = ""
    allow_sandbox: bool = False
    execution_mode: str = "runtime"
    target_version: str = ""

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "RuleResolverInput":
        required = ["prediction_id", "topic", "plugin_claims", "rule_candidates", "runtime_context"]
        missing = [k for k in required if k not in payload]
        if missing:
            raise ValueError(f"REQUIRED_FIELDS_MISSING: {','.join(missing)}")
        if "time_weight" not in payload.get("runtime_context", {}):
            raise ValueError("TIME_WEIGHT_MISSING")
        return cls(
            prediction_id=str(payload["prediction_id"]).strip(),
            topic=str(payload["topic"]).strip(),
            plugin_claims=_ensure_list(payload.get("plugin_claims")),
            rule_candidates=_ensure_list(payload.get("rule_candidates")),
            runtime_context=dict(payload.get("runtime_context") or {}),
            lifecycle_token=_safe_str(payload.get("lifecycle_token"), ""),
            allow_sandbox=bool(payload.get("allow_sandbox")),
            execution_mode=_safe_str(payload.get("execution_mode"), "runtime"),
            target_version=_safe_str(payload.get("target_version"), ""),
        )


@dataclass
class RuleResolverOutput:
    prediction_id: str
    status: str
    active_rules: List[str] = field(default_factory=list)
    suppressed_rules: List[str] = field(default_factory=list)
    resolved_effect: Dict[str, float] = field(default_factory=dict)
    resolver_snapshot: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PredictionContract:
    prediction_id: str
    topic: str
    chain_id: str
    causal_path: List[str]
    rule_ids: List[str]
    chain_state: str
    confidence: float
    period: Dict[str, Any]
    evidence_ids: List[str]
    verifiable_indicators: Dict[str, Any]
    risk_modes: List[str]
    data_sources: List[str]
    model_version: str
    schema_version: str
    display_policy: Dict[str, Any]
    resolver_snapshot: Dict[str, Any]
    uncertainty: Dict[str, Any] = field(default_factory=dict)
    feedback_window: Dict[str, Any] = field(default_factory=dict)
    user_query: str = ""
    normalized_intent: Dict[str, Any] = field(default_factory=dict)
    chart_snapshot: Dict[str, Any] = field(default_factory=dict)
    rule_evidence: List[Dict[str, Any]] = field(default_factory=list)
    inference_steps: List[Dict[str, Any]] = field(default_factory=list)
    conclusions: List[Dict[str, Any]] = field(default_factory=list)
    allowed_output_scope: Dict[str, Any] = field(default_factory=dict)
    engine_version: str = V18_1_SCHEMA_VERSION
    created_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "PredictionContract":
        required = [
            "prediction_id",
            "topic",
            "chain_id",
            "causal_path",
            "rule_ids",
            "chain_state",
            "confidence",
            "period",
            "evidence_ids",
            "verifiable_indicators",
            "risk_modes",
            "data_sources",
            "model_version",
            "schema_version",
            "display_policy",
            "resolver_snapshot",
        ]
        missing = [k for k in required if k not in payload]
        if missing:
            raise ValueError(f"REQUIRED_FIELDS_MISSING: {','.join(missing)}")

        confidence = _safe_float(payload.get("confidence"))
        if not (0.0 <= confidence <= 1.0):
            raise ValueError("INVALID_CONFIDENCE")

        return cls(
            prediction_id=str(payload["prediction_id"]).strip(),
            topic=str(payload["topic"]).strip(),
            chain_id=str(payload["chain_id"]).strip(),
            causal_path=_ensure_list(payload.get("causal_path")),
            rule_ids=_ensure_list(payload.get("rule_ids")),
            chain_state=str(payload["chain_state"]).strip(),
            confidence=confidence,
            period=dict(payload.get("period") or {}),
            evidence_ids=_ensure_list(payload.get("evidence_ids")),
            verifiable_indicators=dict(payload.get("verifiable_indicators") or {}),
            risk_modes=_ensure_list(payload.get("risk_modes")),
            data_sources=_ensure_list(payload.get("data_sources")),
            model_version=str(payload["model_version"]),
            schema_version=str(payload["schema_version"]),
            display_policy=dict(payload.get("display_policy") or {}),
            resolver_snapshot=dict(payload.get("resolver_snapshot") or {}),
            uncertainty=dict(payload.get("uncertainty") or {}),
            feedback_window=dict(payload.get("feedback_window") or {}),
            user_query=_safe_str(payload.get("user_query"), ""),
            normalized_intent=dict(payload.get("normalized_intent") or {}),
            chart_snapshot=dict(payload.get("chart_snapshot") or {}),
            rule_evidence=_ensure_list(payload.get("rule_evidence")),
            inference_steps=_ensure_list(payload.get("inference_steps")),
            conclusions=_ensure_list(payload.get("conclusions")),
            allowed_output_scope=dict(payload.get("allowed_output_scope") or {}),
            engine_version=_safe_str(payload.get("engine_version"), V18_1_SCHEMA_VERSION),
        )


@dataclass
class PredictionLedgerRecord:
    ledger_id: str
    prediction_id: str
    topic: str
    chain_id: str
    state: str
    contract: Dict[str, Any]
    prediction_hash: str
    contract_hash: str
    user_query: str
    normalized_intent: Dict[str, Any]
    chart_snapshot_hash: str
    conclusion_refs: List[str]
    evidence_refs: List[str]
    engine_version: str
    resolver_snapshot: Dict[str, Any]
    verifier_status: str
    feedback_state: str
    schema_version: str
    verifier_runs: List[Dict[str, Any]] = field(default_factory=list)
    feedback_events: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VerifierRun:
    run_id: str
    prediction_id: str
    checks: Dict[str, Any]
    result: str
    action: str
    verifier_version: str
    created_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FeedbackEvent:
    prediction_id: str
    feedback_type: str
    outcome: str
    evidence_of_outcome: List[str]
    notes: str
    observed_at: str
    feedback_window_valid: bool
    event_id: str
    created_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SyntheticCase:
    case_id: str
    scenario: str
    expected_active: bool
    observed_active: bool
    features: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RuleTestResult:
    rule_id: str
    rule_version: str
    test_suite: str
    total_cases: int
    hit_rate: float
    false_positive_rate: float
    false_negative_rate: float
    conflict_rate: float
    recommended_status: str
    suite_id: str
    suite_version: str
    run_id: str
    test_suite_run_id: str
    created_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RuleTestRun:
    run_id: str
    rule_candidate_id: str
    rule_id: str
    version: str
    test_case_ids: List[str]
    results: List[Dict[str, Any]]
    pass_count: int
    fail_count: int
    warning_count: int
    overall_status: str
    created_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AggregatedInsight:
    insight_id: str
    related_rule_ids: List[str]
    related_conclusions: List[str]
    signal_count: int
    hit_count: int
    miss_count: int
    partial_count: int
    dominant_failure_pattern: str
    confidence_trend: str
    suggested_action: str
    evidence_refs: List[str]
    created_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CandidateRuleSuggestion:
    suggestion_id: str
    based_on_insight_id: str
    suggested_rule_diff: Dict[str, Any]
    risk_level: str
    expected_improvement: str
    requires_human_review: bool = True
    created_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RuleQualityScore:
    score_id: str
    rule_id: str
    version: str
    rule_state: str
    sample_count: int
    hit_count: int
    miss_count: int
    partial_count: int
    test_pass_rate: float
    verifier_failure_count: int
    drift_warning_count: int
    confidence_calibration: str
    risk_score: float
    quality_score: float
    recommended_action: str
    evidence_refs: List[str]
    created_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExplanationRequest:
    prediction_id: str
    contract_id: str
    allowed_output_scope: Dict[str, Any]
    user_locale: str = "zh-CN"
    tone: str = "clear"
    explanation_level: str = "normal"
    include_uncertainty: bool = True
    include_evidence_trace: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExplanationResponse:
    prediction_id: str
    contract_id: str
    explanation: str
    safe_output: Dict[str, Any]
    verifier: Dict[str, Any]
    evidence_trace: List[Dict[str, Any]]
    created_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PredictiveServiceError(Exception):
    def __init__(self, code: str, message: str, status: int = 422):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)


class V18PredictiveStore:
    """
    Lightweight append-only runtime store for V18.1 skeleton.
    """

    def __init__(self) -> None:
        self._storage_dir = RUNTIME_DIR / "v18_1"
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._rule_file = self._storage_dir / "rule_kernels.json"
        self._active_rule_file = self._storage_dir / "active_rules.json"
        self._rule_audit_file = self._storage_dir / "rule_kernel_audit.json"
        self._knowledge_card_file = self._storage_dir / "knowledge_cards.json"
        self._knowledge_card_active_file = self._storage_dir / "active_knowledge_cards.json"
        self._ledger_file = self._storage_dir / "prediction_ledger.json"
        self._verifier_file = self._storage_dir / "verifier_runs.json"
        self._feedback_file = self._storage_dir / "feedback_events.json"
        self._learning_signal_file = self._storage_dir / "learning_signals.json"
        self._rule_candidate_file = self._storage_dir / "rule_candidates.json"
        self._agent_session_file = self._storage_dir / "agent_sessions.json"
        self._pr_queue_file = self._storage_dir / "knowledge_pr_queue.json"
        self._rule_test_file = self._storage_dir / "rule_test_results.json"
        self._rule_test_suite_file = self._storage_dir / "rule_test_suites.json"
        self._rule_test_suite_active_file = self._storage_dir / "active_rule_test_suites.json"
        self._rule_test_case_file = self._storage_dir / "rule_test_cases_v02.json"
        self._rule_test_run_file = self._storage_dir / "rule_test_runs_v02.json"
        self._learning_insight_file = self._storage_dir / "learning_insights.json"
        self._candidate_suggestion_file = self._storage_dir / "candidate_rule_suggestions.json"
        self._rule_quality_score_file = self._storage_dir / "rule_quality_scores.json"
        self._bazi_knowledge_unit_file = self._storage_dir / "bazi_knowledge_units.json"
        self._bazi_feature_definition_file = self._storage_dir / "bazi_feature_definitions.json"
        self._bazi_knowledge_source_file = self._storage_dir / "bazi_knowledge_sources.json"
        self._bazi_knowledge_conflict_file = self._storage_dir / "bazi_knowledge_conflicts.json"
        self._storage_backend = V18_STORAGE_BACKEND
        self._storage_adapter = _make_storage_adapter(self._storage_backend, V18_POSTGRES_DSN)
        self._redis = RedisAccelerator()

        self._rule_kernels: Dict[str, RuleKernel] = {}
        self._active_rules: Dict[str, str] = {}
        self._knowledge_cards: Dict[str, KnowledgeCard] = {}
        self._active_knowledge_cards: Dict[str, str] = {}
        self._rule_audit_events: List[RuleKernelAuditEvent] = []
        self._lifecycle_tokens: Dict[str, Dict[str, Any]] = {}
        self._ledger: Dict[str, Dict[str, Any]] = {}
        self._verifier_runs: Dict[str, List[Dict[str, Any]]] = {}
        self._feedback_events: Dict[str, List[Dict[str, Any]]] = {}
        self._learning_signals: Dict[str, List[Dict[str, Any]]] = {}
        self._rule_candidates: Dict[str, Dict[str, Any]] = {}
        self._agent_sessions: Dict[str, Dict[str, Any]] = {}
        self._knowledge_pr: Dict[str, Dict[str, Any]] = {}
        self._rule_test_results: Dict[str, List[Dict[str, Any]]] = {}
        self._rule_test_suites: Dict[str, RuleTestSuite] = {}
        self._active_rule_test_suites: Dict[str, str] = {}
        self._rule_test_cases: Dict[str, Dict[str, Any]] = {}
        self._rule_test_runs: Dict[str, Dict[str, Any]] = {}
        self._learning_insights: Dict[str, Dict[str, Any]] = {}
        self._candidate_rule_suggestions: Dict[str, Dict[str, Any]] = {}
        self._rule_quality_scores: Dict[str, Dict[str, Any]] = {}
        self._bazi_knowledge_units: Dict[str, BaziKnowledgeUnit] = {}
        self._bazi_feature_definitions: Dict[str, BaziFeatureDefinition] = {}
        self._bazi_knowledge_sources: Dict[str, Dict[str, Any]] = {}
        self._bazi_knowledge_conflicts: Dict[str, Dict[str, Any]] = {}

        self._load()
        self.seed_wealth_knowledge_base_v1(only_if_missing=True)
        self._auto_migrate_json_to_postgres_if_configured()

    def _auto_migrate_json_to_postgres_if_configured(self) -> None:
        if not should_auto_migrate_predictive_json_to_postgres():
            return
        try:
            self.migrate_json_to_postgres(V18_POSTGRES_DSN)
        except Exception as exc:
            self._append_audit_event(
                rule_id="predictive.storage",
                event_type="PREDICTIVE_POSTGRES_AUTO_MIGRATION_WARNING",
                severity="warning",
                message="PREDICTIVE_DATABASE_URL detected but JSON-to-Postgres projection did not complete",
                actor_role="system",
                actor_user_id=0,
                source="predictive.config",
                details={"error": _safe_str(exc), "backend": self._storage_backend},
            )
            try:
                self._persist()
            except Exception:
                pass

    def _snapshot(self) -> Dict[str, Any]:
        bazi_sources = dict(self._bazi_knowledge_sources)
        bazi_conflicts = dict(self._bazi_knowledge_conflicts)
        for unit in self._bazi_knowledge_units.values():
            for index, source_ref in enumerate(unit.source_refs):
                source_id = f"{unit.knowledge_id}:source:{index + 1}"
                bazi_sources.setdefault(
                    source_id,
                    {
                        "source_id": source_id,
                        "knowledge_id": unit.knowledge_id,
                        "source_type": "markdown" if source_ref.startswith("docs:") else "reference",
                        "title": source_ref,
                        "reference": source_ref,
                        "notes": "structured seed source reference",
                        "payload": {"source_ref": source_ref},
                        "created_at": unit.created_at,
                    },
                )
            for index, conflict in enumerate(unit.conflicts):
                conflict_id = f"{unit.knowledge_id}:conflict:{index + 1}"
                bazi_conflicts.setdefault(
                    conflict_id,
                    {
                        "conflict_id": conflict_id,
                        "knowledge_id": unit.knowledge_id,
                        "conflicts_with": conflict,
                        "conflict_type": "knowledge_boundary",
                        "resolution_policy": "manual_review_required",
                        "payload": {"conflict": conflict},
                        "created_at": unit.created_at,
                    },
                )
        return {
            "rules": {k: asdict(v) for k, v in self._rule_kernels.items()},
            "active_rules": dict(self._active_rules),
            "knowledge_cards": {k: asdict(v) for k, v in self._knowledge_cards.items()},
            "active_knowledge_cards": dict(self._active_knowledge_cards),
            "rule_candidates": dict(self._rule_candidates),
            "knowledge_pr_queue": dict(self._knowledge_pr),
            "prediction_ledger": dict(self._ledger),
            "verifier_runs": dict(self._verifier_runs),
            "feedback": dict(self._feedback_events),
            "learning_signals": dict(self._learning_signals),
            "aggregated_insights": dict(self._learning_insights),
            "candidate_rule_suggestions": dict(self._candidate_rule_suggestions),
            "rule_test_results": dict(self._rule_test_results),
            "rule_test_suites": {k: asdict(v) for k, v in self._rule_test_suites.items()},
            "active_rule_test_suites": dict(self._active_rule_test_suites),
            "rule_test_cases": dict(self._rule_test_cases),
            "rule_test_runs": dict(self._rule_test_runs),
            "rule_quality_scores": dict(self._rule_quality_scores),
            "agent_sessions": dict(self._agent_sessions),
            "audit_events": [event.to_dict() for event in self._rule_audit_events],
            "bazi_knowledge_units": {k: asdict(v) for k, v in self._bazi_knowledge_units.items()},
            "bazi_feature_definitions": {k: asdict(v) for k, v in self._bazi_feature_definitions.items()},
            "bazi_knowledge_sources": bazi_sources,
            "bazi_knowledge_conflicts": bazi_conflicts,
        }

    def _hydrate_from_snapshot(self, snapshot: Dict[str, Any]) -> None:
        for raw_key, payload in (snapshot.get("rules") or {}).items():
            if not isinstance(payload, dict):
                continue
            try:
                rule = RuleKernel.from_payload(dict(payload))
                key = _rule_storage_key(rule.rule_id, rule.version)
                self._rule_kernels[key] = rule
                if rule.status == "active":
                    self._active_rules[rule.rule_id] = rule.version
            except Exception:
                continue
        if isinstance(snapshot.get("active_rules"), dict):
            self._active_rules.update({k: _safe_str(v) for k, v in snapshot["active_rules"].items()})
        for raw_key, payload in (snapshot.get("knowledge_cards") or {}).items():
            if not isinstance(payload, dict):
                continue
            try:
                card = KnowledgeCard.from_payload(dict(payload))
                key = _rule_storage_key(card.card_id, card.version)
                self._knowledge_cards[key] = card
                if card.status == "active":
                    self._active_knowledge_cards[card.card_id] = card.version
            except Exception:
                continue
        if isinstance(snapshot.get("active_knowledge_cards"), dict):
            self._active_knowledge_cards.update({k: _safe_str(v) for k, v in snapshot["active_knowledge_cards"].items()})
        for item in snapshot.get("audit_events") or []:
            if isinstance(item, dict):
                self._rule_audit_events.append(
                    RuleKernelAuditEvent(
                        rule_id=_safe_str(item.get("rule_id")),
                        event_type=_safe_str(item.get("event_type"), "UNKNOWN"),
                        severity=_safe_str(item.get("severity"), "info"),
                        message=_safe_str(item.get("message")),
                        actor_role=_safe_str(item.get("actor_role"), "system"),
                        actor_user_id=_safe_int(item.get("actor_user_id"), 0),
                        created_at=_safe_datetime_iso(item.get("created_at")),
                        source=_safe_str(item.get("source"), RULE_GATEKEEPER_PROTOCOL),
                        details=dict(item.get("details") or {}),
                        event_hash=_safe_str(item.get("event_hash")),
                        previous_event_hash=_safe_str(item.get("previous_event_hash")),
                    )
                )
        mapping = {
            "_ledger": "prediction_ledger",
            "_verifier_runs": "verifier_runs",
            "_feedback_events": "feedback",
            "_learning_signals": "learning_signals",
            "_rule_candidates": "rule_candidates",
            "_agent_sessions": "agent_sessions",
            "_knowledge_pr": "knowledge_pr_queue",
            "_rule_test_results": "rule_test_results",
            "_rule_test_cases": "rule_test_cases",
            "_rule_test_runs": "rule_test_runs",
            "_learning_insights": "aggregated_insights",
            "_candidate_rule_suggestions": "candidate_rule_suggestions",
            "_rule_quality_scores": "rule_quality_scores",
            "_bazi_knowledge_sources": "bazi_knowledge_sources",
            "_bazi_knowledge_conflicts": "bazi_knowledge_conflicts",
        }
        for attr, key in mapping.items():
            value = snapshot.get(key)
            if isinstance(value, dict):
                setattr(self, attr, {k: v for k, v in value.items()})
        for knowledge_id, payload in (snapshot.get("bazi_knowledge_units") or {}).items():
            if not isinstance(payload, dict):
                continue
            try:
                unit = BaziKnowledgeUnit.from_payload(dict(payload))
                self._bazi_knowledge_units[unit.knowledge_id] = unit
            except Exception:
                continue
        for feature_type, payload in (snapshot.get("bazi_feature_definitions") or {}).items():
            if not isinstance(payload, dict):
                continue
            try:
                definition = BaziFeatureDefinition.from_payload(dict(payload))
                self._bazi_feature_definitions[definition.feature_type] = definition
            except Exception:
                continue
        for raw_key, payload in (snapshot.get("rule_test_suites") or {}).items():
            if not isinstance(payload, dict):
                continue
            try:
                suite = RuleTestSuite.from_payload(dict(payload))
                self._rule_test_suites[_rule_storage_key(suite.suite_id, suite.version)] = suite
                if suite.status == "active":
                    self._active_rule_test_suites[suite.suite_id] = suite.version
            except Exception:
                continue
        if isinstance(snapshot.get("active_rule_test_suites"), dict):
            self._active_rule_test_suites.update({k: _safe_str(v) for k, v in snapshot["active_rule_test_suites"].items()})

    def _load(self) -> None:
        if self._storage_backend == "postgres":
            self._hydrate_from_snapshot(self._storage_adapter.load_snapshot())
            return
        if self._rule_file.exists():
            try:
                raw = json.loads(self._rule_file.read_text(encoding="utf-8"))
                for raw_key, payload in (raw or {}).items():
                    try:
                        rule = RuleKernel.from_payload(dict(payload))
                        rid, version = _split_rule_key(raw_key)
                        version = _safe_str(version, _safe_str(rule.version))
                        key = _rule_storage_key(rule.rule_id, version)
                        self._rule_kernels[key] = rule
                        if rule.status == "active":
                            self._active_rules[rule.rule_id] = rule.version
                    except Exception:
                        pass
            except Exception:
                pass

        if self._active_rule_file.exists():
            try:
                raw_active = json.loads(self._active_rule_file.read_text(encoding="utf-8"))
                if isinstance(raw_active, dict):
                    for rid, version in raw_active.items():
                        if isinstance(rid, str) and isinstance(version, str):
                            self._active_rules[rid] = version
            except Exception:
                pass

        if self._rule_audit_file.exists():
            try:
                raw_audit = json.loads(self._rule_audit_file.read_text(encoding="utf-8"))
                if isinstance(raw_audit, list):
                    for item in raw_audit:
                        if not isinstance(item, dict):
                            continue
                        self._rule_audit_events.append(
                            RuleKernelAuditEvent(
                                rule_id=_safe_str(item.get("rule_id")),
                                event_type=_safe_str(item.get("event_type"), "UNKNOWN"),
                                severity=_safe_str(item.get("severity"), "info"),
                                message=_safe_str(item.get("message"), ""),
                                actor_role=_safe_str(item.get("actor_role"), "system"),
                                actor_user_id=_safe_int(item.get("actor_user_id"), 0),
                                created_at=_safe_datetime_iso(item.get("created_at")),
                                source=_safe_str(item.get("source"), RULE_GATEKEEPER_PROTOCOL),
                                details=dict(item.get("details") or {}),
                                event_hash=_safe_str(item.get("event_hash")),
                                previous_event_hash=_safe_str(item.get("previous_event_hash")),
                            )
                        )
            except Exception:
                pass

        if self._knowledge_card_file.exists():
            try:
                raw_cards = json.loads(self._knowledge_card_file.read_text(encoding="utf-8"))
                for raw_key, payload in (raw_cards or {}).items():
                    try:
                        card = KnowledgeCard.from_payload(dict(payload))
                        rid, version = _split_rule_key(raw_key)
                        version = _safe_str(version, card.version)
                        key = _rule_storage_key(card.card_id, version)
                        self._knowledge_cards[key] = card
                        if card.status == "active":
                            self._active_knowledge_cards[card.card_id] = card.version
                    except Exception:
                        pass
            except Exception:
                pass

        if self._knowledge_card_active_file.exists():
            try:
                raw_active = json.loads(self._knowledge_card_active_file.read_text(encoding="utf-8"))
                if isinstance(raw_active, dict):
                    for rid, version in raw_active.items():
                        if isinstance(rid, str) and isinstance(version, str):
                            self._active_knowledge_cards[rid] = version
            except Exception:
                pass

        if self._ledger_file.exists():
            try:
                raw = json.loads(self._ledger_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._ledger = {k: dict(v) for k, v in raw.items() if isinstance(k, str) and isinstance(v, dict)}
            except Exception:
                pass

        if self._verifier_file.exists():
            try:
                raw = json.loads(self._verifier_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._verifier_runs = {k: list(v) for k, v in raw.items() if isinstance(v, list)}
            except Exception:
                pass

        if self._feedback_file.exists():
            try:
                raw = json.loads(self._feedback_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._feedback_events = {k: list(v) for k, v in raw.items() if isinstance(v, list)}
            except Exception:
                pass

        if self._learning_signal_file.exists():
            try:
                raw = json.loads(self._learning_signal_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._learning_signals = {k: list(v) for k, v in raw.items() if isinstance(v, list)}
            except Exception:
                pass

        if self._rule_candidate_file.exists():
            try:
                raw = json.loads(self._rule_candidate_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._rule_candidates = {k: dict(v) for k, v in raw.items() if isinstance(v, dict)}
            except Exception:
                pass

        if self._agent_session_file.exists():
            try:
                raw = json.loads(self._agent_session_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._agent_sessions = {k: dict(v) for k, v in raw.items() if isinstance(v, dict)}
            except Exception:
                pass

        if self._pr_queue_file.exists():
            try:
                raw = json.loads(self._pr_queue_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._knowledge_pr = {k: dict(v) for k, v in raw.items() if isinstance(k, str) and isinstance(v, dict)}
            except Exception:
                pass

        if self._rule_test_file.exists():
            try:
                raw = json.loads(self._rule_test_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._rule_test_results = {k: list(v) for k, v in raw.items() if isinstance(k, str) and isinstance(v, list)}
            except Exception:
                pass

        if self._rule_test_case_file.exists():
            try:
                raw = json.loads(self._rule_test_case_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._rule_test_cases = {k: dict(v) for k, v in raw.items() if isinstance(k, str) and isinstance(v, dict)}
            except Exception:
                pass

        if self._rule_test_run_file.exists():
            try:
                raw = json.loads(self._rule_test_run_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._rule_test_runs = {k: dict(v) for k, v in raw.items() if isinstance(k, str) and isinstance(v, dict)}
            except Exception:
                pass

        if self._learning_insight_file.exists():
            try:
                raw = json.loads(self._learning_insight_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._learning_insights = {k: dict(v) for k, v in raw.items() if isinstance(k, str) and isinstance(v, dict)}
            except Exception:
                pass

        if self._candidate_suggestion_file.exists():
            try:
                raw = json.loads(self._candidate_suggestion_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._candidate_rule_suggestions = {k: dict(v) for k, v in raw.items() if isinstance(k, str) and isinstance(v, dict)}
            except Exception:
                pass

        if self._rule_quality_score_file.exists():
            try:
                raw = json.loads(self._rule_quality_score_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._rule_quality_scores = {k: dict(v) for k, v in raw.items() if isinstance(k, str) and isinstance(v, dict)}
            except Exception:
                pass

        if self._bazi_knowledge_unit_file.exists():
            try:
                raw = json.loads(self._bazi_knowledge_unit_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    for payload in raw.values():
                        if not isinstance(payload, dict):
                            continue
                        try:
                            unit = BaziKnowledgeUnit.from_payload(dict(payload))
                            self._bazi_knowledge_units[unit.knowledge_id] = unit
                        except Exception:
                            pass
            except Exception:
                pass

        if self._bazi_feature_definition_file.exists():
            try:
                raw = json.loads(self._bazi_feature_definition_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    for payload in raw.values():
                        if not isinstance(payload, dict):
                            continue
                        try:
                            definition = BaziFeatureDefinition.from_payload(dict(payload))
                            self._bazi_feature_definitions[definition.feature_type] = definition
                        except Exception:
                            pass
            except Exception:
                pass

        if self._bazi_knowledge_source_file.exists():
            try:
                raw = json.loads(self._bazi_knowledge_source_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._bazi_knowledge_sources = {k: dict(v) for k, v in raw.items() if isinstance(k, str) and isinstance(v, dict)}
            except Exception:
                pass

        if self._bazi_knowledge_conflict_file.exists():
            try:
                raw = json.loads(self._bazi_knowledge_conflict_file.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    self._bazi_knowledge_conflicts = {k: dict(v) for k, v in raw.items() if isinstance(k, str) and isinstance(v, dict)}
            except Exception:
                pass

        if self._rule_test_suite_file.exists():
            try:
                raw_suites = json.loads(self._rule_test_suite_file.read_text(encoding="utf-8"))
                for raw_key, payload in (raw_suites or {}).items():
                    try:
                        suite = RuleTestSuite.from_payload(dict(payload))
                        suite_id, version = _split_rule_key(raw_key)
                        version = _safe_str(version, suite.version)
                        key = self._rule_storage_key(suite.suite_id, version)
                        self._rule_test_suites[key] = suite
                        if suite.status == "active":
                            self._active_rule_test_suites[suite.suite_id] = suite.version
                    except Exception:
                        pass
            except Exception:
                pass

        if self._rule_test_suite_active_file.exists():
            try:
                raw_active = json.loads(self._rule_test_suite_active_file.read_text(encoding="utf-8"))
                if isinstance(raw_active, dict):
                    for sid, version in raw_active.items():
                        if isinstance(sid, str) and isinstance(version, str):
                            self._active_rule_test_suites[sid] = version
            except Exception:
                pass

    def _persist(self) -> None:
        if self._storage_backend == "postgres":
            self._storage_adapter.save_snapshot(self._snapshot())
            return
        def safe_dump(path: Path, payload: Any) -> None:
            try:
                path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass

        safe_dump(self._rule_file, {k: asdict(v) for k, v in self._rule_kernels.items()})
        safe_dump(self._active_rule_file, self._active_rules)
        safe_dump(self._rule_audit_file, [event.to_dict() for event in self._rule_audit_events[-2000:]])
        safe_dump(self._knowledge_card_file, {k: asdict(v) for k, v in self._knowledge_cards.items()})
        safe_dump(self._knowledge_card_active_file, self._active_knowledge_cards)
        safe_dump(self._ledger_file, self._ledger)
        safe_dump(self._verifier_file, self._verifier_runs)
        safe_dump(self._feedback_file, self._feedback_events)
        safe_dump(self._learning_signal_file, self._learning_signals)
        safe_dump(self._rule_candidate_file, self._rule_candidates)
        safe_dump(self._agent_session_file, self._agent_sessions)
        safe_dump(self._pr_queue_file, self._knowledge_pr)
        safe_dump(self._rule_test_file, self._rule_test_results)
        safe_dump(self._rule_test_suite_file, {k: asdict(v) for k, v in self._rule_test_suites.items()})
        safe_dump(self._rule_test_suite_active_file, self._active_rule_test_suites)
        safe_dump(self._rule_test_case_file, self._rule_test_cases)
        safe_dump(self._rule_test_run_file, self._rule_test_runs)
        safe_dump(self._learning_insight_file, self._learning_insights)
        safe_dump(self._candidate_suggestion_file, self._candidate_rule_suggestions)
        safe_dump(self._rule_quality_score_file, self._rule_quality_scores)
        safe_dump(self._bazi_knowledge_unit_file, {k: asdict(v) for k, v in self._bazi_knowledge_units.items()})
        safe_dump(self._bazi_feature_definition_file, {k: asdict(v) for k, v in self._bazi_feature_definitions.items()})
        safe_dump(self._bazi_knowledge_source_file, self._bazi_knowledge_sources)
        safe_dump(self._bazi_knowledge_conflict_file, self._bazi_knowledge_conflicts)

    def _normalize_rule_key(self, rule_id: str, version: str) -> str:
        return _rule_storage_key(rule_id, version)

    def _list_rule_keys(self, rule_id: str) -> List[str]:
        return [key for key in self._rule_kernels if _split_rule_key(key)[0] == rule_id]

    def _list_rule_versions(self, rule_id: str) -> List[str]:
        return [v for _, v in (_split_rule_key(k) for k in self._list_rule_keys(rule_id))]

    def _list_suite_keys(self, suite_id: str) -> List[str]:
        return [key for key in self._rule_test_suites if _split_rule_key(key)[0] == suite_id]

    def _list_suite_versions(self, suite_id: str) -> List[str]:
        return [v for _, v in (_split_rule_key(k) for k in self._list_suite_keys(suite_id))]

    def _append_audit_event(
        self,
        *,
        rule_id: str,
        event_type: str,
        severity: str,
        message: str,
        actor_role: str,
        actor_user_id: int,
        source: str = RULE_GATEKEEPER_PROTOCOL,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        previous_hash = _safe_str(self._rule_audit_events[-1].event_hash) if self._rule_audit_events else ""
        event = RuleKernelAuditEvent(
            rule_id=rule_id,
            event_type=event_type,
            severity=severity,
            message=message,
            actor_role=actor_role,
            actor_user_id=actor_user_id,
            source=source,
            details=dict(details or {}),
            previous_event_hash=previous_hash,
        )
        payload = event.to_dict()
        payload["event_hash"] = ""
        event.event_hash = _audit_event_hash(payload)
        self._rule_audit_events.append(event)

    def update_audit_event(self, *_args: Any, **_kwargs: Any) -> None:
        self._storage_adapter.update_audit_event(*_args, **_kwargs)

    def delete_audit_event(self, *_args: Any, **_kwargs: Any) -> None:
        self._storage_adapter.delete_audit_event(*_args, **_kwargs)

    def verify_audit_hash_chain(self) -> Dict[str, Any]:
        previous = ""
        broken: List[Dict[str, Any]] = []
        for index, event in enumerate(self._rule_audit_events):
            payload = event.to_dict()
            event_hash = _safe_str(payload.get("event_hash"))
            actual_previous = _safe_str(payload.get("previous_event_hash"))
            payload["event_hash"] = ""
            expected_hash = _audit_event_hash(payload)
            if actual_previous != previous or event_hash != expected_hash:
                broken.append(
                    {
                        "index": index,
                        "event_type": _safe_str(payload.get("event_type")),
                        "expected_previous_event_hash": previous,
                        "actual_previous_event_hash": actual_previous,
                        "expected_event_hash": expected_hash,
                        "actual_event_hash": event_hash,
                    }
                )
            previous = event_hash
        return {"ok": not broken, "event_count": len(self._rule_audit_events), "broken": broken}

    @contextmanager
    def transaction(self, _name: str = "default") -> Iterator[None]:
        snapshot = self._snapshot()
        try:
            with self._storage_adapter.transaction():
                yield
        except Exception:
            self._rule_kernels.clear()
            self._active_rules.clear()
            self._knowledge_cards.clear()
            self._active_knowledge_cards.clear()
            self._rule_audit_events.clear()
            self._ledger.clear()
            self._verifier_runs.clear()
            self._feedback_events.clear()
            self._learning_signals.clear()
            self._rule_candidates.clear()
            self._agent_sessions.clear()
            self._knowledge_pr.clear()
            self._rule_test_results.clear()
            self._rule_test_suites.clear()
            self._active_rule_test_suites.clear()
            self._rule_test_cases.clear()
            self._rule_test_runs.clear()
            self._learning_insights.clear()
            self._candidate_rule_suggestions.clear()
            self._rule_quality_scores.clear()
            self._bazi_knowledge_units.clear()
            self._bazi_feature_definitions.clear()
            self._bazi_knowledge_sources.clear()
            self._bazi_knowledge_conflicts.clear()
            self._hydrate_from_snapshot(snapshot)
            self._persist()
            raise

    def migrate_json_to_postgres(self, dsn: str | None = None) -> Dict[str, Any]:
        adapter = PostgresStorageAdapter(_safe_str(dsn or V18_POSTGRES_DSN))
        snapshot = self._snapshot()
        adapter.save_snapshot(snapshot)
        migrated = adapter.load_snapshot()
        return {
            "backend": "postgres",
            "collections": sorted(k for k in migrated.keys() if k in V18_STATE_COLLECTIONS),
            "rule_count": len(migrated.get("rules") or {}),
            "ledger_count": len(migrated.get("prediction_ledger") or {}),
            "audit_event_count": len(migrated.get("audit_events") or []),
            "idempotent": True,
        }

    def invalidate_cache(self, *keys: str) -> None:
        self._redis.delete(*keys)

    def _rule_audit_trace(self, rule: RuleKernel) -> Dict[str, Any]:
        return {
            "version": _safe_str(rule.version),
            "content_hash": _safe_str(rule.content_hash),
            "created_by": _safe_str(rule.created_by),
            "approved_by": _safe_str(rule.approved_by),
            "approved_at": _safe_str(rule.approved_at),
        }

    def _knowledge_card_audit_trace(self, card: KnowledgeCard) -> Dict[str, Any]:
        return {
            "version": _safe_str(card.version),
            "content_hash": _safe_str(card.content_hash),
            "created_by": _safe_str(card.created_by),
            "approved_by": _safe_str(card.approved_by),
            "approved_at": _safe_str(card.approved_at),
        }

    def _authorize_claim(self, rule: RuleKernel, plugin_claims: List[str]) -> bool:
        claims = {_normalize_claim_plugin(c) for c in plugin_claims}
        claims = {claim for claim in claims if claim}
        if not claims:
            return False
        if not rule.owner_plugin:
            return False
        owner = _safe_str(rule.owner_plugin)
        if owner in claims or "*" in claims:
            return True
        return any(
            claim.endswith(".*") and owner.startswith(f"{claim[:-2]}.")
            for claim in claims
        )

    def _clean_lifecycle_tokens(self) -> None:
        now = datetime.now(timezone.utc).timestamp()
        for token in list(self._lifecycle_tokens):
            if float(self._lifecycle_tokens.get(token, {}).get("expired_at", 0.0)) < now:
                self._lifecycle_tokens.pop(token, None)

    def issue_lifecycle_token(
        self,
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
        purpose: str = "runtime",
        ttl_seconds: int = RULE_RUNTIME_TOKEN_TTL_SECONDS,
        issuer: str = "direct",
    ) -> str:
        self._clean_lifecycle_tokens()
        token = token_urlsafe(24)
        now = datetime.now(timezone.utc).timestamp()
        self._lifecycle_tokens[token] = {
            "actor_role": _safe_str(actor_role, "system"),
            "actor_user_id": _safe_int(actor_user_id, 0),
            "purpose": _safe_str(purpose, "runtime"),
            "issuer": _safe_str(issuer, "direct"),
            "issued_at": now,
            "expired_at": now + _safe_int(ttl_seconds, RULE_RUNTIME_TOKEN_TTL_SECONDS),
        }
        return token

    def _assert_lifecycle(self, *, token: str, purpose: str, execution_mode: str) -> None:
        if not V18_1_STRICT_LIFECYCLE:
            return
        self._clean_lifecycle_tokens()
        if not token:
            self._append_audit_event(
                rule_id="",
                event_type=LIFECYCLE_BYPASS_CODE,
                severity="high",
                message="lifecycle token missing",
                actor_role="system",
                actor_user_id=0,
                source="rule-runtime",
                details={"purpose": purpose, "execution_mode": execution_mode},
            )
            self._persist()
            raise PredictiveServiceError(LIFECYCLE_BYPASS_CODE, "lifecycle token is required", 403)
        record = self._lifecycle_tokens.get(token)
        if not record or float(record.get("expired_at", 0.0)) < datetime.now(timezone.utc).timestamp():
            record = record or {}
            self._append_audit_event(
                rule_id="",
                event_type=LIFECYCLE_BYPASS_CODE,
                severity="high",
                message="lifecycle token invalid or expired",
                actor_role=_safe_str(record.get("actor_role"), "system"),
                actor_user_id=_safe_int(record.get("actor_user_id"), 0),
                source="rule-runtime",
                details={"purpose": purpose, "execution_mode": execution_mode},
            )
            self._persist()
            raise PredictiveServiceError(LIFECYCLE_BYPASS_CODE, "invalid lifecycle token", 403)
        if _safe_str(record.get("purpose"), "runtime") != purpose:
            self._append_audit_event(
                rule_id="",
                event_type=LIFECYCLE_BYPASS_CODE,
                severity="high",
                message="lifecycle context mismatch",
                actor_role=_safe_str(record.get("actor_role"), "system"),
                actor_user_id=_safe_int(record.get("actor_user_id"), 0),
                source="rule-runtime",
                details={"purpose": purpose, "execution_mode": execution_mode},
            )
            self._persist()
            raise PredictiveServiceError(LIFECYCLE_BYPASS_CODE, "invalid lifecycle context", 403)
        if purpose in {"retrieval", "runtime", "pilot", "test", "debug"} and _safe_str(record.get("issuer")) != "runtime_facade":
            self._append_audit_event(
                rule_id="",
                event_type=LIFECYCLE_BYPASS_CODE,
                severity="high",
                message="lifecycle token issuer is not runtime facade",
                actor_role=_safe_str(record.get("actor_role"), "system"),
                actor_user_id=_safe_int(record.get("actor_user_id"), 0),
                source="rule-runtime",
                details={
                    "purpose": purpose,
                    "execution_mode": execution_mode,
                    "issuer": _safe_str(record.get("issuer"), "direct"),
                },
            )
            self._persist()
            raise PredictiveServiceError(LIFECYCLE_BYPASS_CODE, "runtime facade is required", 403)

    def _raise_lifecycle_bypass(
        self,
        *,
        message: str,
        purpose: str,
        execution_mode: str,
        actor_role: str = "system",
        actor_user_id: int = 0,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._append_audit_event(
            rule_id="",
            event_type=LIFECYCLE_BYPASS_CODE,
            severity="high",
            message=message,
            actor_role=_safe_str(actor_role, "system"),
            actor_user_id=_safe_int(actor_user_id, 0),
            source="rule-runtime",
            details={
                "purpose": purpose,
                "execution_mode": execution_mode,
                **dict(details or {}),
            },
        )
        self._persist()
        raise PredictiveServiceError(LIFECYCLE_BYPASS_CODE, message, 403)

    def register_rule(
        self,
        payload: Dict[str, Any],
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
    ) -> Dict[str, Any]:
        requested_status = str(payload.get("status") or "").strip().lower()
        role = str(actor_role or "system").strip().lower()
        if requested_status in {"validated", "active", "deprecated"} and role not in {"manager", "admin", "system"}:
            raise PredictiveServiceError("FORBIDDEN", "validated/active/deprecated requires manager or admin", 403)
        if requested_status == "active":
            raise PredictiveServiceError("RULE_TRANSITION_INVALID", "active rules must be activated through activation API", 409)

        rule = RuleKernel.from_payload(payload)
        if not rule.rule_id:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "rule_id is required", 400)
        if rule.knowledge_card_id:
            self.get_knowledge_card(rule.knowledge_card_id, allow_inactive=True)

        key = self._normalize_rule_key(rule.rule_id, rule.version)
        if key in self._rule_kernels:
            raise PredictiveServiceError("RULE_VERSION_CONFLICT", f"Rule {rule.rule_id} version {rule.version} exists", 409)

        rule.created_by = _safe_str(actor_role, "system")
        rule.created_by_user_id = _safe_int(actor_user_id, 0)
        self._rule_kernels[key] = rule
        self._append_audit_event(
            rule_id=rule.rule_id,
            event_type="RULE_REGISTERED",
            severity="info",
            message="rule version registered",
            actor_role=role,
            actor_user_id=actor_user_id,
            details={
                "status": rule.status,
                "knowledge_card_id": rule.knowledge_card_id,
                **self._rule_audit_trace(rule),
            },
        )
        self._persist()
        return {
            "rule_id": rule.rule_id,
            "operation": "created",
            "version": rule.version,
            "content_hash": rule.content_hash,
            "created_by": rule.created_by,
            "approved_by": rule.approved_by,
            "approved_at": rule.approved_at,
        }

    def activate_rule(
        self,
        *,
        rule_id: str,
        target_version: str,
        actor_role: str = "system",
        actor_user_id: int = 0,
    ) -> RuleKernel:
        role = str(actor_role or "system").strip().lower()
        if role not in {"manager", "admin", "system"}:
            raise PredictiveServiceError("FORBIDDEN", "only reviewer roles can activate rules", 403)
        lock_key = f"lock:rule:{rule_id}"
        if not self._redis.acquire_lock(lock_key, ttl_seconds=30):
            raise PredictiveServiceError("LOCK_BUSY", "rule activation is already in progress", 409)

        try:
            target_version = _safe_str(target_version)
            if not target_version:
                raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "target_version required", 400)

            target_key = self._normalize_rule_key(rule_id, target_version)
            target = self._rule_kernels.get(target_key)
            if not target:
                raise PredictiveServiceError("RULE_NOT_FOUND", f"Rule {rule_id} version {target_version} not found", 404)
            if target.status != "validated":
                raise PredictiveServiceError("RULE_TRANSITION_INVALID", "only validated rules can be activated", 409)

            current_version = self._active_rules.get(rule_id)
            if current_version and current_version != target_version:
                old_key = self._normalize_rule_key(rule_id, current_version)
                old_rule = self._rule_kernels.get(old_key)
                if old_rule and old_rule.status == "active":
                    old_rule.status = "validated"
                    self._rule_kernels[old_key] = old_rule

            target.status = "active"
            target.approved_by = _safe_str(actor_role, "system")
            target.approved_by_user_id = _safe_int(actor_user_id, 0)
            target.approved_at = _utcnow_iso()
            self._active_rules[rule_id] = target_version
            self._rule_kernels[target_key] = target
            self._append_audit_event(
                rule_id=rule_id,
                event_type="RULE_ACTIVATED",
                severity="info",
                message="rule activated",
                actor_role=role,
                actor_user_id=actor_user_id,
                details={
                    "version": target_version,
                    **self._rule_audit_trace(target),
                },
            )
            self.invalidate_cache("cache:active_rules", "cache:rule_quality_scores")
            self._persist()
            return target
        finally:
            self._redis.release_lock(lock_key)

    def update_rule_status(
        self,
        rule_id: str,
        target_status: str,
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
        version: Optional[str] = None,
    ) -> RuleKernel:
        role = str(actor_role or "system").strip().lower()
        target_status = str(target_status or "").strip().lower()
        if target_status not in RULE_STATE_VALUES:
            raise PredictiveServiceError("INVALID_RULE_STATUS", "invalid target_status")
        if role not in {"manager", "admin", "system"}:
            raise PredictiveServiceError("FORBIDDEN", "only reviewer roles can update rule status", 403)
        if target_status == "active":
            return self.activate_rule(
                rule_id=rule_id,
                target_version=version or "",
                actor_role=actor_role,
                actor_user_id=actor_user_id,
            )

        rule = self.get_rule(rule_id, version=version, allow_inactive=True)
        if rule.status == "active":
            raise PredictiveServiceError(
                "RULE_IMMUTABLE",
                "active rule is immutable; submit a new rule version and activate it",
                409,
            )

        old_status = _safe_str(rule.status)
        rule.status = target_status
        if target_status in {"validated", "deprecated"} and _safe_str(old_status) != target_status:
            rule.approved_by = _safe_str(actor_role, "system")
            rule.approved_by_user_id = _safe_int(actor_user_id, 0)
            rule.approved_at = _utcnow_iso()
        self._rule_kernels[self._normalize_rule_key(rule.rule_id, rule.version)] = rule
        self._append_audit_event(
            rule_id=rule.rule_id,
            event_type="RULE_STATUS_UPDATED",
            severity="info",
            message=f"status changed {old_status} -> {target_status}",
            actor_role=role,
            actor_user_id=actor_user_id,
            details={
                "old_status": old_status,
                "status": target_status,
                **self._rule_audit_trace(rule),
            },
        )
        self._persist()
        return rule

    def get_rule(
        self,
        rule_id: str,
        *,
        version: Optional[str] = None,
        allow_inactive: bool = False,
    ) -> RuleKernel:
        if not rule_id:
            raise PredictiveServiceError("RULE_NOT_FOUND", "rule_id is required", 404)
        if version:
            rule = self._rule_kernels.get(self._normalize_rule_key(rule_id, version))
            if not rule:
                raise PredictiveServiceError("RULE_NOT_FOUND", f"Rule {rule_id} version {version} not found", 404)
            return rule
        active_version = self._active_rules.get(rule_id)
        if active_version:
            rule = self._rule_kernels.get(self._normalize_rule_key(rule_id, active_version))
            if rule:
                return rule
        if not allow_inactive:
            raise PredictiveServiceError("RULE_NOT_FOUND", f"Rule {rule_id} not found", 404)
        versions = self._list_rule_versions(rule_id)
        if versions:
            versions = sorted(versions, reverse=True)
            rule = self._rule_kernels.get(self._normalize_rule_key(rule_id, versions[0]))
            if rule:
                return rule
        raise PredictiveServiceError("RULE_NOT_FOUND", f"Rule {rule_id} not found", 404)

    def list_rules(self, *, effect_scope: Optional[str] = None, status: Optional[str] = None, owner_plugin: Optional[str] = None) -> List[RuleKernel]:
        out: List[RuleKernel] = []
        for key, rule in self._rule_kernels.items():
            rid, version = _split_rule_key(key)
            if status == "active" and self._active_rules.get(rid) != version:
                continue
            if status and status != "active" and rule.status != status:
                continue
            if effect_scope and effect_scope not in rule.effect_scope:
                continue
            if owner_plugin and rule.owner_plugin != owner_plugin:
                continue
            out.append(rule)
        return out

    def register_knowledge_card(
        self,
        payload: Dict[str, Any],
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
    ) -> Dict[str, Any]:
        requested_status = str(payload.get("status") or "").strip().lower()
        role = str(actor_role or "system").strip().lower()
        if requested_status in {"validated", "active", "deprecated"} and role not in {"manager", "admin", "system"}:
            raise PredictiveServiceError("FORBIDDEN", "validated/active/deprecated requires manager or admin", 403)
        if requested_status == "active":
            raise PredictiveServiceError("KNOWLEDGE_CARD_TRANSITION_INVALID", "active knowledge cards must be activated through activation API", 409)

        card = KnowledgeCard.from_payload(payload)
        if not card.card_id:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "card_id is required", 400)

        key = self._normalize_rule_key(card.card_id, card.version)
        if key in self._knowledge_cards:
            raise PredictiveServiceError("KNOWLEDGE_CARD_VERSION_CONFLICT", f"Knowledge card {card.card_id} version {card.version} exists", 409)

        card.created_by = _safe_str(role, "system")
        card.created_by_user_id = _safe_int(actor_user_id, 0)
        card.content_hash = _knowledge_card_payload_fingerprint(card.to_dict())
        self._knowledge_cards[key] = card
        self._append_audit_event(
            rule_id=card.card_id,
            event_type="KNOWLEDGE_CARD_REGISTERED",
            severity="info",
            message="knowledge card version registered",
            actor_role=role,
            actor_user_id=actor_user_id,
            details={
                "version": card.version,
                "status": card.status,
                **self._knowledge_card_audit_trace(card),
            },
        )
        self._persist()
        return {
            "card_id": card.card_id,
            "operation": "created",
            "version": card.version,
            "content_hash": card.content_hash,
            "created_by": card.created_by,
            "approved_by": card.approved_by,
            "approved_at": card.approved_at,
        }

    def activate_knowledge_card(
        self,
        *,
        card_id: str,
        target_version: str,
        actor_role: str = "system",
        actor_user_id: int = 0,
    ) -> KnowledgeCard:
        role = str(actor_role or "system").strip().lower()
        if role not in {"manager", "admin", "system"}:
            raise PredictiveServiceError("FORBIDDEN", "only reviewer roles can activate knowledge cards", 403)

        target_version = _safe_str(target_version)
        if not target_version:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "target_version required", 400)
        target_key = self._normalize_rule_key(card_id, target_version)
        target = self._knowledge_cards.get(target_key)
        if not target:
            raise PredictiveServiceError("KNOWLEDGE_CARD_NOT_FOUND", f"Knowledge card {card_id} version {target_version} not found", 404)
        if target.status != "validated":
            raise PredictiveServiceError("KNOWLEDGE_CARD_TRANSITION_INVALID", "only validated cards can be activated", 409)

        current_version = self._active_knowledge_cards.get(card_id)
        if current_version and current_version != target_version:
            old_key = self._normalize_rule_key(card_id, current_version)
            old_card = self._knowledge_cards.get(old_key)
            if old_card and old_card.status == "active":
                old_card.status = "validated"
                old_card.updated_at = _utcnow_iso()
                self._knowledge_cards[old_key] = old_card

        target.status = "active"
        target.approved_by = _safe_str(role, "system")
        target.approved_by_user_id = _safe_int(actor_user_id, 0)
        target.approved_at = _utcnow_iso()
        target.updated_at = _utcnow_iso()
        self._active_knowledge_cards[card_id] = target_version
        self._knowledge_cards[target_key] = target
        self._append_audit_event(
            rule_id=card_id,
            event_type="KNOWLEDGE_CARD_ACTIVATED",
            severity="info",
            message="knowledge card activated",
            actor_role=role,
            actor_user_id=actor_user_id,
            details={
                "version": target_version,
                **self._knowledge_card_audit_trace(target),
            },
        )
        self._persist()
        return target

    def update_knowledge_card_status(
        self,
        card_id: str,
        target_status: str,
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
        version: Optional[str] = None,
    ) -> KnowledgeCard:
        role = str(actor_role or "system").strip().lower()
        target_status = str(target_status or "").strip().lower()
        if target_status not in KNOWLEDGE_CARD_STATES:
            raise PredictiveServiceError("INVALID_KNOWLEDGE_CARD_STATUS", "invalid target_status")
        if role not in {"manager", "admin", "system"}:
            raise PredictiveServiceError("FORBIDDEN", "only reviewer roles can update knowledge card status", 403)
        if target_status == "active":
            return self.activate_knowledge_card(
                card_id=card_id,
                target_version=version or "",
                actor_role=actor_role,
                actor_user_id=actor_user_id,
            )

        if not _safe_str(card_id):
            raise PredictiveServiceError("KNOWLEDGE_CARD_NOT_FOUND", "card_id is required", 404)
        target = self.get_knowledge_card(card_id, version=version, allow_inactive=True)
        if target.status == "active":
            raise PredictiveServiceError(
                "KNOWLEDGE_CARD_IMMUTABLE",
                "active knowledge card is immutable; submit a new card version and activate it",
                409,
            )

        old_status = _safe_str(target.status)
        target.status = target_status
        if target_status in {"validated", "deprecated"} and _safe_str(old_status) != target_status:
            target.approved_by = _safe_str(role, "system")
            target.approved_by_user_id = _safe_int(actor_user_id, 0)
            target.approved_at = _utcnow_iso()
        target.updated_at = _utcnow_iso()
        self._knowledge_cards[self._normalize_rule_key(target.card_id, target.version)] = target
        self._append_audit_event(
            rule_id=card_id,
            event_type="KNOWLEDGE_CARD_STATUS_UPDATED",
            severity="info",
            message=f"status changed {old_status} -> {target_status}",
            actor_role=role,
            actor_user_id=actor_user_id,
            details={
                "old_status": old_status,
                "version": target.version,
                "status": target_status,
                **self._knowledge_card_audit_trace(target),
            },
        )
        self._persist()
        return target

    def get_knowledge_card(self, card_id: str, *, version: Optional[str] = None, allow_inactive: bool = False) -> KnowledgeCard:
        if not card_id:
            raise PredictiveServiceError("KNOWLEDGE_CARD_NOT_FOUND", "card_id is required", 404)
        if version:
            card = self._knowledge_cards.get(self._normalize_rule_key(card_id, version))
            if not card:
                raise PredictiveServiceError("KNOWLEDGE_CARD_NOT_FOUND", f"Knowledge card {card_id} version {version} not found", 404)
            return card
        active_version = self._active_knowledge_cards.get(card_id)
        if active_version:
            card = self._knowledge_cards.get(self._normalize_rule_key(card_id, active_version))
            if card:
                return card
        if not allow_inactive:
            raise PredictiveServiceError("KNOWLEDGE_CARD_NOT_FOUND", f"Knowledge card {card_id} not found", 404)
        versions = [v for _, v in (_split_rule_key(k) for k in self._knowledge_cards if _split_rule_key(k)[0] == card_id)]
        if versions:
            versions = sorted(versions, reverse=True)
            card = self._knowledge_cards.get(self._normalize_rule_key(card_id, versions[0]))
            if card:
                return card
        raise PredictiveServiceError("KNOWLEDGE_CARD_NOT_FOUND", f"Knowledge card {card_id} not found", 404)

    def list_knowledge_cards(
        self,
        *,
        knowledge_domain: Optional[str] = None,
        status: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[KnowledgeCard]:
        out: List[KnowledgeCard] = []
        for key, card in self._knowledge_cards.items():
            card_id, version = _split_rule_key(key)
            if status == "active" and self._active_knowledge_cards.get(card_id) != version:
                continue
            if status and status != "active" and card.status != status:
                continue
            if knowledge_domain and knowledge_domain != card.knowledge_domain:
                continue
            if tag and tag not in card.tags:
                continue
        out.append(card)
        return out

    def seed_wealth_knowledge_base_v1(self, *, only_if_missing: bool = True) -> Dict[str, Any]:
        inserted = 0
        skipped = 0
        for payload in WEALTH_FEATURE_DEFINITIONS_V1:
            try:
                definition = BaziFeatureDefinition.from_payload(payload)
            except Exception:
                continue
            if only_if_missing and definition.feature_type in self._bazi_feature_definitions:
                skipped += 1
                continue
            self._bazi_feature_definitions[definition.feature_type] = definition
            inserted += 1
        for payload in WEALTH_KNOWLEDGE_UNITS_V1:
            try:
                unit = BaziKnowledgeUnit.from_payload(payload)
            except Exception:
                continue
            if only_if_missing and unit.knowledge_id in self._bazi_knowledge_units:
                skipped += 1
                continue
            self._bazi_knowledge_units[unit.knowledge_id] = unit
            inserted += 1
        if inserted:
            self._persist()
        return {
            "seed_id": "wealth_kb_seed_v1",
            "domain": "wealth",
            "inserted": inserted,
            "skipped": skipped,
            "knowledge_unit_count": len([unit for unit in self._bazi_knowledge_units.values() if unit.domain == "wealth"]),
            "feature_definition_count": len([row for row in self._bazi_feature_definitions.values() if row.domain == "wealth"]),
        }

    def register_bazi_knowledge_unit(
        self,
        payload: Dict[str, Any],
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
    ) -> Dict[str, Any]:
        unit_payload = dict(payload or {})
        unit_payload.setdefault("created_by", _safe_str(actor_role, "system"))
        unit = BaziKnowledgeUnit.from_payload(unit_payload)
        existing = self._bazi_knowledge_units.get(unit.knowledge_id)
        if existing and existing.status == "reviewed":
            incoming_hash = _bazi_knowledge_content_fingerprint(unit_payload)
            if incoming_hash != existing.content_hash:
                raise PredictiveServiceError("BAZI_KNOWLEDGE_IMMUTABLE", "reviewed knowledge unit cannot be edited; create a new knowledge_id/version or deprecate it", 409)
        if existing and existing.status == "deprecated":
            raise PredictiveServiceError("BAZI_KNOWLEDGE_DEPRECATED", "deprecated knowledge unit cannot be overwritten", 409)
        if existing and existing.status == "draft":
            unit.created_at = existing.created_at
        unit.updated_at = _utcnow_iso()
        self._bazi_knowledge_units[unit.knowledge_id] = unit
        self._persist()
        return unit.to_dict()

    def list_bazi_knowledge_units(
        self,
        *,
        domain: str | None = None,
        category: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        items = [unit.to_dict() for unit in self._bazi_knowledge_units.values()]
        if domain:
            items = [item for item in items if _safe_str(item.get("domain")) == _safe_str(domain)]
        if category:
            items = [item for item in items if _safe_str(item.get("category")) == _safe_str(category)]
        if status:
            items = [item for item in items if _safe_str(item.get("status")) == _safe_str(status)]
        items = sorted(items, key=lambda item: (_safe_str(item.get("domain")), _safe_str(item.get("category")), _safe_str(item.get("knowledge_id"))))
        start = max(0, _safe_int(offset, 0))
        size = max(1, min(_safe_int(limit, 100), 500))
        return {"items": items[start : start + size], "total_matched": len(items), "total_returned": len(items[start : start + size]), "offset": start, "limit": size}

    def get_bazi_knowledge_unit(self, knowledge_id: str) -> Dict[str, Any]:
        unit = self._bazi_knowledge_units.get(_safe_str(knowledge_id))
        if not unit:
            raise PredictiveServiceError("BAZI_KNOWLEDGE_NOT_FOUND", f"knowledge unit {knowledge_id} not found", 404)
        return unit.to_dict()

    def review_bazi_knowledge_unit(
        self,
        knowledge_id: str,
        payload: Dict[str, Any],
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
    ) -> Dict[str, Any]:
        unit = self._bazi_knowledge_units.get(_safe_str(knowledge_id))
        if not unit:
            raise PredictiveServiceError("BAZI_KNOWLEDGE_NOT_FOUND", f"knowledge unit {knowledge_id} not found", 404)
        if unit.status == "deprecated":
            raise PredictiveServiceError("BAZI_KNOWLEDGE_DEPRECATED", "deprecated knowledge unit cannot be reviewed", 409)
        unit.status = "reviewed"
        unit.reviewed_by = _safe_str(payload.get("reviewed_by") or actor_role, "system")
        unit.reviewed_at = _utcnow_iso()
        unit.updated_at = unit.reviewed_at
        self._bazi_knowledge_units[unit.knowledge_id] = unit
        self._append_audit_event(
            rule_id=unit.knowledge_id,
            event_type="BAZI_KNOWLEDGE_REVIEWED",
            severity="info",
            message="bazi knowledge unit reviewed",
            actor_role=_safe_str(actor_role, "system"),
            actor_user_id=_safe_int(actor_user_id, 0),
            source="bazi-knowledge-base",
            details={"knowledge_id": unit.knowledge_id, "domain": unit.domain, "category": unit.category, "content_hash": unit.content_hash},
        )
        self._persist()
        return unit.to_dict()

    def deprecate_bazi_knowledge_unit(
        self,
        knowledge_id: str,
        payload: Dict[str, Any],
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
    ) -> Dict[str, Any]:
        unit = self._bazi_knowledge_units.get(_safe_str(knowledge_id))
        if not unit:
            raise PredictiveServiceError("BAZI_KNOWLEDGE_NOT_FOUND", f"knowledge unit {knowledge_id} not found", 404)
        unit.status = "deprecated"
        unit.reviewed_by = _safe_str(payload.get("reviewed_by") or actor_role, unit.reviewed_by)
        unit.updated_at = _utcnow_iso()
        self._bazi_knowledge_units[unit.knowledge_id] = unit
        self._append_audit_event(
            rule_id=unit.knowledge_id,
            event_type="BAZI_KNOWLEDGE_DEPRECATED",
            severity="warning",
            message=_safe_str(payload.get("reason"), "bazi knowledge unit deprecated"),
            actor_role=_safe_str(actor_role, "system"),
            actor_user_id=_safe_int(actor_user_id, 0),
            source="bazi-knowledge-base",
            details={"knowledge_id": unit.knowledge_id, "domain": unit.domain, "category": unit.category, "content_hash": unit.content_hash},
        )
        self._persist()
        return unit.to_dict()

    def apply_energy_clamp(self, value: Any, *, signed: bool = False, fallback: float = 0.0) -> Dict[str, Any]:
        return _energy_clamp_value(value, signed=signed, fallback=fallback)

    def compile_bazi_knowledge_rule_logic(self, unit_or_payload: BaziKnowledgeUnit | Dict[str, Any]) -> Dict[str, Any]:
        unit = unit_or_payload if isinstance(unit_or_payload, BaziKnowledgeUnit) else BaziKnowledgeUnit.from_payload(dict(unit_or_payload))
        mapping = dict(unit.feature_mapping or {})
        feature_type = _safe_str(mapping.get("feature_type"))
        if feature_type not in BAZI_FEATURE_TYPES:
            raise PredictiveServiceError("BAZI_KNOWLEDGE_COMPILER_INVALID", "feature_mapping.feature_type is not supported", 422)
        confidence = self.apply_energy_clamp(mapping.get("confidence_weight"), fallback=unit.confidence_prior)
        uncertainty = self.apply_energy_clamp(mapping.get("uncertainty_weight"), fallback=0.3)
        effects: Dict[str, Any] = {}
        effect_trace: Dict[str, Any] = {}
        for key, value in dict(unit.effects or {}).items():
            effect_key = _safe_str(key)
            if not effect_key:
                continue
            clamped = self.apply_energy_clamp(value, signed=True)
            effects[effect_key] = clamped["value"]
            effect_trace[effect_key] = clamped
        return {
            "compiler_version": "kb-rule-generator-v18.1-alpha",
            "logic_type": "feature_mapping_dsl",
            "runtime_scope": "sandbox_candidate_only",
            "decorators": [ENERGY_CLAMP_DECORATOR],
            "energy_clamp": {
                "decorator": ENERGY_CLAMP_DECORATOR,
                "limits": ENERGY_CLAMP_LIMITS,
                "applied_to": ["confidence_weight", "uncertainty_weight", "effects", "strength", "stability", "risk"],
                "overflow_policy": "clamp_and_flag",
            },
            "source_knowledge_id": unit.knowledge_id,
            "knowledge_category": unit.category,
            "feature_type": feature_type,
            "input_requirements": mapping.get("input_requirements"),
            "detection_logic": mapping.get("detection_logic"),
            "output_fields": _ensure_list(mapping.get("output_fields")),
            "effect_direction": _safe_str(mapping.get("effect_direction")),
            "weights": {
                "confidence_weight": confidence["value"],
                "uncertainty_weight": uncertainty["value"],
                "confidence_clamp": confidence,
                "uncertainty_clamp": uncertainty,
            },
            "bounded_effects": effects,
            "effect_clamp_trace": effect_trace,
            "dsl": {
                "op": "weighted_feature_match",
                "when": {
                    "all": _ensure_list(dict(unit.conditions or {}).get("requires"))
                    or [{"field": key, "expected": value} for key, value in dict(unit.conditions or {}).items()],
                    "detection_logic": mapping.get("detection_logic"),
                },
                "emit_feature": {
                    "feature_type": feature_type,
                    "effect": effects,
                    "confidence_weight": confidence["value"],
                    "uncertainty_weight": uncertainty["value"],
                },
                "guardrails": [ENERGY_CLAMP_DECORATOR, "SANDBOX_ONLY", "NO_DIRECT_CONCLUSION"],
            },
            "pseudo_code": f"{ENERGY_CLAMP_DECORATOR}(weighted_feature_match(feature_type='{feature_type}', source='{unit.knowledge_id}'))",
            "zero_leakage_policy": {
                "kb_does_not_enter_prediction_runtime": True,
                "requires_rule_test_engine": True,
                "requires_knowledge_pr": True,
                "requires_reviewer_activation": True,
            },
        }

    def bazi_knowledge_unit_to_rule_candidate(
        self,
        knowledge_id: str,
        payload: Dict[str, Any] | None = None,
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
    ) -> Dict[str, Any]:
        unit = self._bazi_knowledge_units.get(_safe_str(knowledge_id))
        if not unit:
            raise PredictiveServiceError("BAZI_KNOWLEDGE_NOT_FOUND", f"knowledge unit {knowledge_id} not found", 404)
        if unit.status == "deprecated":
            raise PredictiveServiceError("BAZI_KNOWLEDGE_DEPRECATED", "deprecated knowledge unit cannot be converted to rule candidate", 409)
        mapping = dict(unit.feature_mapping or {})
        feature_type = _safe_str(mapping.get("feature_type"))
        compiled_logic = self.compile_bazi_knowledge_rule_logic(unit)
        effects = {key: _safe_float(value, 0.0) for key, value in dict(unit.effects or {}).items() if _safe_str(key)}
        if "wealth" not in effects and unit.domain == "wealth":
            effects["wealth"] = max(0.05, min(1.0, unit.confidence_prior))
        safe_suffix = "".join(ch if ch.isalnum() else "_" for ch in unit.knowledge_id)[:72]
        rule_payload = {
            "rule_id": _safe_str((payload or {}).get("rule_id"), f"kb.{safe_suffix}"),
            "theory_family": "bazi_knowledge_base_wealth",
            "condition": {
                "source_knowledge_id": unit.knowledge_id,
                "knowledge_category": unit.category,
                "feature_type": feature_type,
                "input_requirements": mapping.get("input_requirements"),
                "detection_logic": mapping.get("detection_logic"),
                "conditions": unit.conditions,
                "compiled_feature_logic": compiled_logic,
                "compiler_guardrails": [ENERGY_CLAMP_DECORATOR, "SANDBOX_ONLY", "NO_DIRECT_CONCLUSION"],
            },
            "effect": dict(compiled_logic.get("bounded_effects") or effects),
            "priority": max(0.1, min(0.95, unit.confidence_prior)),
            "evidence_strength": max(0.1, min(0.95, _safe_float(dict(compiled_logic.get("weights") or {}).get("confidence_weight"), unit.confidence_prior))),
            "conflict_policy": "merge",
            "version": _safe_str((payload or {}).get("version"), f"sandbox-kb-{_safe_int(datetime.now(timezone.utc).timestamp())}"),
            "owner_plugin": "kb.bazi.wealth",
            "status": "experimental",
            "effect_scope": [unit.domain],
            "allowed_topics": [unit.domain],
        }
        candidate = self.build_sandbox_rule_candidate(
            {"rule_candidate": rule_payload},
            actor_role=actor_role,
            actor_user_id=actor_user_id,
        )
        candidate["source_knowledge_id"] = unit.knowledge_id
        candidate["source_knowledge_unit"] = unit.to_dict()
        candidate["feature_mapping"] = mapping
        candidate["compiled_rule_logic"] = compiled_logic
        candidate["conversion_policy"] = {
            "sandbox_only": True,
            "requires_rule_test": True,
            "requires_knowledge_pr": True,
            "requires_reviewer_activate": True,
            "kb_does_not_enter_prediction_runtime": True,
        }
        self._rule_candidates[candidate["candidate_id"]] = candidate
        self._persist()
        return candidate

    def bootstrap_wealth_core_rule_test_candidates_v1(
        self,
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
        suite_version: str = "v1",
        suite_status: str = "draft",
    ) -> Dict[str, Any]:
        role = str(actor_role or "system").strip().lower()
        suite_status = str(suite_status).strip().lower()
        if suite_status != "draft":
            raise PredictiveServiceError(
                "RULE_TEST_SUITE_TRANSITION_INVALID",
                "Wealth Core v1 test suites must be created in draft status",
                409,
            )

        candidate_outputs: List[Dict[str, Any]] = []
        suite_outputs: List[Dict[str, Any]] = []
        case_outputs: List[Dict[str, Any]] = []
        suite_candidates: List[Dict[str, str]] = []

        for knowledge_id in WEALTH_CORE_REVIEWED_KNOWLEDGE_UNIT_IDS:
            unit = self.get_bazi_knowledge_unit(knowledge_id)
            if unit.get("status") != "reviewed":
                raise PredictiveServiceError(
                    "BAZI_KNOWLEDGE_NOT_REVIEWED",
                    f"knowledge unit {knowledge_id} is not reviewed",
                    409,
                )

            safe_suffix = str(knowledge_id).replace(".", "_")
            candidate = self.bazi_knowledge_unit_to_rule_candidate(
                knowledge_id,
                {"rule_id": f"kb.core.{safe_suffix}", "version": suite_version},
                actor_role=role,
                actor_user_id=actor_user_id,
            )
            candidate_outputs.append(candidate)

            case = self.register_rule_test_case(
                {
                    "case_id": f"wealth_core_v1_{safe_suffix}_smoke",
                    "source": "synthetic",
                    "chart_snapshot": {"knowledge_id": knowledge_id},
                    "query_intent": {
                        "topic": "wealth",
                        "knowledge_id": knowledge_id,
                        "suite_version": suite_version,
                        "suite_status": suite_status,
                    },
                    "expected_conclusions": [],
                    "expected_evidence_patterns": [],
                    "forbidden_conclusions": [],
                    "tags": ["wealth", "core_wealth_v1", "rule_test_candidate_v1", knowledge_id],
                },
                actor_role=role,
                actor_user_id=actor_user_id,
            )
            case_outputs.append(case)

            suite = self.register_rule_test_suite(
                {
                    "suite_id": f"wealth_core_v1_{safe_suffix}_suite",
                    "rule_id": candidate["rule_payload"]["rule_id"],
                    "rule_version": candidate["rule_payload"]["version"],
                    "title": f"Wealth Core v1 Candidate Suite: {knowledge_id}",
                    "description": (
                        "Generated by bootstrap_wealth_core_rule_test_candidates_v1 for "
                        "wealth KB reviewed units."
                    ),
                    "status": suite_status,
                    "version": suite_version,
                    "test_cases": [case],
                },
                actor_role=role,
                actor_user_id=actor_user_id,
                require_rule_reference=False,
            )
            suite_out = self.get_rule_test_suite(
                suite["suite_id"],
                version=suite["version"],
                allow_inactive=True,
            ).to_dict()
            suite_outputs.append(suite_out)
            suite_candidates.append({"knowledge_id": knowledge_id, "suite_id": suite["suite_id"], "candidate_id": candidate["candidate_id"]})

        return {
            "candidate_count": len(candidate_outputs),
            "suite_count": len(suite_outputs),
            "case_count": len(case_outputs),
            "candidates": candidate_outputs,
            "suites": suite_outputs,
            "cases": case_outputs,
            "suite_candidates": suite_candidates,
        }

    def _bazi_audit_scenarios(self, unit: BaziKnowledgeUnit) -> List[Dict[str, Any]]:
        return [
            {
                "scenario_id": "vault_opened_by_clash",
                "description": "财库被冲开，机会流动性上升，但稳定性可能下降。",
                "expected_feedback": {"wealth_flow_activation": "positive", "wealth_stability": "mixed_or_negative", "risk": "positive"},
            },
            {
                "scenario_id": "vault_locked_by_combination",
                "description": "财库被合，财富承接可能被关系或环境锁住，兑现节奏变慢。",
                "expected_feedback": {"wealth_stability": "negative_or_delayed", "risk": "positive"},
            },
            {
                "scenario_id": "combination_forms_cooperation",
                "description": "合局形成合作承接时，稳定性可能提升，但分配风险需要单独标记。",
                "expected_feedback": {"wealth_stability": "conditional_positive", "risk": "conditional_positive"},
            },
            {
                "scenario_id": "punishment_harm_hidden_cost",
                "description": "刑害触发财务相关位置时，隐性摩擦、合同瑕疵或信任成本上升。",
                "expected_feedback": {"wealth_stability": "negative", "risk": "positive"},
            },
        ]

    def _call_qwen_kb_audit(
        self,
        *,
        unit: BaziKnowledgeUnit,
        compiled_logic: Dict[str, Any],
        scenarios: List[Dict[str, Any]],
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        runtime_llm = get_runtime_llm_config()
        env_model = (
            os.getenv("V18_KB_AUDIT_MODEL")
            or os.getenv("QWEN_AUDIT_MODEL")
            or ""
        ).strip()
        env_api_key = (
            os.getenv("V18_KB_AUDIT_API_KEY")
            or os.getenv("QWEN_AUDIT_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or ""
        ).strip()
        base_url = _safe_str(payload.get("base_url") or V18_KB_AUDIT_BASE_URL or runtime_llm.get("base_url"))
        if not base_url:
            raise PredictiveServiceError("KB_AUDIT_MODEL_UNCONFIGURED", "V18_KB_AUDIT_BASE_URL is not configured", 503)
        url = base_url.rstrip("/")
        if not url.endswith("/chat/completions"):
            url = f"{url}/chat/completions"
        model = _safe_str(payload.get("model") or env_model or runtime_llm.get("model") or V18_KB_AUDIT_MODEL, "qwen3.6.3.5")
        body = {
            "model": model,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "system",
                    "content": "你是八字财富知识库审计员。只返回 JSON，不生成预测结论。重点审计合冲刑害对 wealth_stability/risk 的正负反馈是否自洽。",
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "knowledge_unit": unit.to_dict(),
                            "compiled_rule_logic": compiled_logic,
                            "audit_scenarios": scenarios,
                            "required_json_shape": {
                                "conflicts": [
                                    {
                                        "conflict_type": "string",
                                        "severity": "low|medium|high",
                                        "conflicts_with": "string",
                                        "reason": "string",
                                        "recommended_resolution": "string",
                                    }
                                ]
                            },
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                },
            ],
        }
        headers = {"Content-Type": "application/json"}
        api_key = _safe_str(payload.get("api_key") or env_api_key or runtime_llm.get("api_key") or V18_KB_AUDIT_API_KEY)
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        timeout = max(3, min(_safe_int(payload.get("timeout_seconds"), 20), 90))
        req = urllib.request.Request(
            url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
        data = json.loads(raw)
        content = _safe_str(
            (((data.get("choices") or [{}])[0].get("message") or {}).get("content"))
            if isinstance(data, dict)
            else ""
        )
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = {"raw_model_response": content}
        parsed["model"] = model
        parsed["endpoint"] = url
        return parsed

    def _local_bazi_audit_conflicts(
        self,
        unit: BaziKnowledgeUnit,
        compiled_logic: Dict[str, Any],
        model_report: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        for item in _ensure_list((model_report or {}).get("conflicts")):
            if not isinstance(item, dict):
                continue
            findings.append(
                {
                    "conflict_type": _safe_str(item.get("conflict_type"), "model_detected_conflict"),
                    "severity": _safe_str(item.get("severity"), "medium"),
                    "conflicts_with": _safe_str(item.get("conflicts_with"), "model_audit"),
                    "reason": _safe_str(item.get("reason"), "model reported a logic conflict"),
                    "recommended_resolution": _safe_str(item.get("recommended_resolution"), "manual_review_required"),
                    "source": "qwen_audit",
                }
            )
        effects = dict(compiled_logic.get("bounded_effects") or {})
        risk = _safe_float(effects.get("risk"), 0.0)
        stability = _safe_float(effects.get("wealth_stability"), 0.0)
        if unit.category == "combination_clash_stability" or _safe_str(unit.feature_mapping.get("feature_type")) in {"wealth_stability", "wealth_risk"}:
            if unit.knowledge_id.endswith("019_combination_changes_stability"):
                findings.append(
                    {
                        "conflict_type": "stability_polarity_ambiguous",
                        "severity": "medium",
                        "conflicts_with": "vault_opened_by_clash_vs_vault_locked_by_combination",
                        "reason": "合局可形成合作承接，也可能锁住兑现；单一正向 wealth_stability 需要条件化。",
                        "recommended_resolution": "split positive cooperation and locked-liquidity branches before activation",
                        "source": "local_inflation_audit",
                    }
                )
            if risk >= 0.3 and stability > 0:
                findings.append(
                    {
                        "conflict_type": "mixed_signal_requires_uncertainty",
                        "severity": "low",
                        "conflicts_with": "positive_stability_and_positive_risk",
                        "reason": "稳定性支持与风险上升同时出现，Rule Candidate 必须保留 uncertainty/risk 分支。",
                        "recommended_resolution": "keep risk as separate evidence modifier; do not collapse into a positive conclusion",
                        "source": "local_inflation_audit",
                    }
                )
        if not findings:
            findings.append(
                {
                    "conflict_type": "no_blocking_conflict",
                    "severity": "info",
                    "conflicts_with": "none",
                    "reason": "未发现阻塞型冲突，但仍需 Rule Test Engine 与 reviewer 激活流程。",
                    "recommended_resolution": "continue sandbox test flow",
                    "source": "local_inflation_audit",
                }
            )
        return findings

    def dry_run_bazi_knowledge_audit(
        self,
        knowledge_id: str,
        payload: Dict[str, Any] | None = None,
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
    ) -> Dict[str, Any]:
        unit = self._bazi_knowledge_units.get(_safe_str(knowledge_id))
        if not unit:
            raise PredictiveServiceError("BAZI_KNOWLEDGE_NOT_FOUND", f"knowledge unit {knowledge_id} not found", 404)
        compiled_logic = self.compile_bazi_knowledge_rule_logic(unit)
        scenarios = self._bazi_audit_scenarios(unit)
        audit_payload = dict(payload or {})
        model_report: Dict[str, Any] = {}
        audit_status = "local_fallback"
        model_error = ""
        if not _safe_bool(audit_payload.get("skip_model"), False) and not _safe_bool(audit_payload.get("local_only"), False):
            try:
                model_report = self._call_qwen_kb_audit(
                    unit=unit,
                    compiled_logic=compiled_logic,
                    scenarios=scenarios,
                    payload=audit_payload,
                )
                audit_status = "model_completed"
            except Exception as exc:
                model_error = _safe_str(exc)
                audit_status = "model_failed_local_fallback"
        conflicts = self._local_bazi_audit_conflicts(unit, compiled_logic, model_report=model_report)
        now = _utcnow_iso()
        persisted: List[Dict[str, Any]] = []
        for finding in conflicts:
            conflict_seed = {
                "knowledge_id": unit.knowledge_id,
                "finding": finding,
                "compiled_hash": _payload_hash(compiled_logic),
            }
            conflict_id = f"{unit.knowledge_id}:audit:{_sha256(_canonical_json(conflict_seed))[:12]}"
            row = {
                "conflict_id": conflict_id,
                "knowledge_id": unit.knowledge_id,
                "conflicts_with": _safe_str(finding.get("conflicts_with"), "audit"),
                "conflict_type": _safe_str(finding.get("conflict_type"), "logic_audit"),
                "resolution_policy": "manual_review_required" if _safe_str(finding.get("severity")) != "info" else "continue_sandbox_flow",
                "payload": {
                    "audit_status": audit_status,
                    "severity": _safe_str(finding.get("severity"), "medium"),
                    "reason": _safe_str(finding.get("reason")),
                    "recommended_resolution": _safe_str(finding.get("recommended_resolution")),
                    "source": _safe_str(finding.get("source"), "local_inflation_audit"),
                    "model": _safe_str(model_report.get("model") or V18_KB_AUDIT_MODEL),
                    "model_error": model_error,
                    "compiled_rule_logic": compiled_logic,
                    "scenarios": scenarios,
                },
                "created_at": now,
            }
            self._bazi_knowledge_conflicts[conflict_id] = row
            persisted.append(row)
        self._append_audit_event(
            rule_id=unit.knowledge_id,
            event_type="BAZI_KB_AUDIT_DRY_RUN",
            severity="warning" if any(_safe_str(item.get("payload", {}).get("severity")) in {"medium", "high"} for item in persisted) else "info",
            message="bazi knowledge unit dry-run audit completed",
            actor_role=_safe_str(actor_role, "system"),
            actor_user_id=_safe_int(actor_user_id, 0),
            source="bazi-kb-rule-bridge",
            details={"knowledge_id": unit.knowledge_id, "audit_status": audit_status, "conflict_count": len(persisted)},
        )
        self._persist()
        return {
            "knowledge_id": unit.knowledge_id,
            "audit_status": audit_status,
            "model": _safe_str(model_report.get("model") or V18_KB_AUDIT_MODEL),
            "model_error": model_error,
            "compiled_rule_logic": compiled_logic,
            "scenarios": scenarios,
            "conflicts": persisted,
            "zero_leakage_policy": compiled_logic.get("zero_leakage_policy"),
        }

    def build_sandbox_rule_candidate(
        self,
        payload: Dict[str, Any],
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
    ) -> Dict[str, Any]:
        raw = dict(payload.get("rule_candidate") if isinstance(payload.get("rule_candidate"), dict) else payload)
        if "owner_plugin" not in raw and raw.get("plugin_id"):
            raw["owner_plugin"] = raw.get("plugin_id")
        if "version" not in raw or not _safe_str(raw.get("version")):
            raw["version"] = f"sandbox-{_safe_int(datetime.now(timezone.utc).timestamp())}"
        raw["status"] = "experimental"
        if "effect_scope" not in raw:
            raw["effect_scope"] = _ensure_list(raw.get("allowed_topics")) or [_normalize_topic(raw.get("topic"))]
        if "allowed_topics" not in raw:
            raw["allowed_topics"] = _ensure_list(raw.get("effect_scope"))
        if "knowledge_card_id" not in raw and payload.get("knowledge_card_id"):
            raw["knowledge_card_id"] = payload.get("knowledge_card_id")

        rule = RuleKernel.from_payload(raw)
        if rule.status == "active":
            raise PredictiveServiceError("RULE_TRANSITION_INVALID", "sandbox candidates cannot be active", 409)
        if rule.knowledge_card_id:
            self.get_knowledge_card(rule.knowledge_card_id, allow_inactive=True)
        rule.created_by = _safe_str(actor_role, "system")
        rule.created_by_user_id = _safe_int(actor_user_id, 0)
        rule.content_hash = _rule_payload_fingerprint(rule.to_dict())
        candidate = {
            "candidate_id": _rule_candidate_id(rule.to_dict()),
            "candidate_state": "sandbox",
            "sandbox": True,
            "rule_payload": rule.to_dict(),
            "created_at": _utcnow_iso(),
            "created_by": _safe_str(actor_role, "system"),
        }
        self._rule_candidates[candidate["candidate_id"]] = candidate
        self._persist()
        return candidate

    def query_rule_candidates(
        self,
        *,
        candidate_state: str | None = None,
        rule_id: str | None = None,
        knowledge_card_id: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        items = list(self._rule_candidates.values())
        if candidate_state:
            items = [item for item in items if _safe_str(item.get("candidate_state")) == _safe_str(candidate_state)]
        if rule_id:
            items = [item for item in items if _safe_str((item.get("rule_payload") or {}).get("rule_id")) == _safe_str(rule_id)]
        if knowledge_card_id:
            items = [item for item in items if _safe_str((item.get("rule_payload") or {}).get("knowledge_card_id")) == _safe_str(knowledge_card_id)]
        items = sorted(items, key=lambda item: _parse_dt(item.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        start = max(0, _safe_int(offset, 0))
        size = max(1, min(_safe_int(limit, 100), 500))
        return {"items": items[start : start + size], "total_matched": len(items), "total_returned": len(items[start : start + size]), "offset": start, "limit": size}

    def register_rule_test_case(
        self,
        payload: Dict[str, Any],
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
    ) -> Dict[str, Any]:
        case = RuleTestCase.from_payload(payload)
        item = case.to_dict()
        item["created_by"] = _safe_str(actor_role, "system")
        item["created_by_user_id"] = _safe_int(actor_user_id, 0)
        self._rule_test_cases[case.case_id] = item
        self._persist()
        return item

    def query_rule_test_cases(
        self,
        *,
        source: str | None = None,
        tag: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        items = list(self._rule_test_cases.values())
        if source:
            items = [item for item in items if _safe_str(item.get("source")) == _safe_str(source)]
        if tag:
            items = [item for item in items if _safe_str(tag) in [_safe_str(row) for row in _ensure_list(item.get("tags"))]]
        items = sorted(items, key=lambda item: _parse_dt(item.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        start = max(0, _safe_int(offset, 0))
        size = max(1, min(_safe_int(limit, 100), 500))
        return {"items": items[start : start + size], "total_matched": len(items), "total_returned": len(items[start : start + size]), "offset": start, "limit": size}

    def _rule_test_cases_for_payload(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        cases: List[Dict[str, Any]] = []
        for case_id in [_safe_str(item) for item in _ensure_list(payload.get("test_case_ids")) if _safe_str(item)]:
            if case_id not in self._rule_test_cases:
                raise PredictiveServiceError("RULE_TEST_CASE_NOT_FOUND", f"rule test case {case_id} not found", 404)
            cases.append(dict(self._rule_test_cases[case_id]))
        for raw in _ensure_list(payload.get("test_cases")):
            if not isinstance(raw, dict):
                continue
            cases.append(RuleTestCase.from_payload(raw).to_dict())
        if not cases:
            raise PredictiveServiceError("RULE_TEST_EMPTY", "test_case_ids or test_cases required")
        return cases

    def _rule_subject_for_test(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        candidate_id = _safe_str(payload.get("rule_candidate_id"))
        if candidate_id:
            candidate = self._rule_candidates.get(candidate_id)
            if not candidate:
                raise PredictiveServiceError("RULE_CANDIDATE_NOT_FOUND", f"rule candidate {candidate_id} not found", 404)
            rule_payload = dict(candidate.get("rule_payload") or {})
            return {
                "rule_candidate_id": candidate_id,
                "rule_payload": rule_payload,
                "rule_id": _safe_str(rule_payload.get("rule_id")),
                "version": _safe_str(rule_payload.get("version")),
                "subject_state": "sandbox_candidate",
            }

        rule_id = _safe_str(payload.get("rule_id"))
        if not rule_id:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "rule_candidate_id or rule_id required")
        rule = self.get_rule(rule_id, version=_safe_str(payload.get("version") or payload.get("rule_version")) or None, allow_inactive=True)
        return {
            "rule_candidate_id": "",
            "rule_payload": rule.to_dict(),
            "rule_id": rule.rule_id,
            "version": rule.version,
            "subject_state": rule.status,
        }

    def _candidate_test_contract_verification(self, rule_payload: Dict[str, Any], *, force_failure: bool = False) -> Dict[str, Any]:
        errors: List[str] = []
        if force_failure or _safe_bool(rule_payload.get("force_verifier_failure"), False):
            errors.append("FORCED_CONTRACT_VERIFIER_FAILURE")
        if not _safe_str(rule_payload.get("rule_id")) or not _safe_str(rule_payload.get("version")) or not _safe_str(rule_payload.get("content_hash")):
            errors.append("RULE_EVIDENCE_IDENTITY_MISSING")
        if _safe_str(rule_payload.get("status")) == "active":
            errors.append("SANDBOX_CANDIDATE_CANNOT_BE_ACTIVE")
        return {"result": "pass" if not errors else "fail", "errors": sorted(set(errors)), "verifier_version": "rule-test-contract-v02"}

    def _run_single_rule_test_case_v02(self, *, rule_payload: Dict[str, Any], case: Dict[str, Any]) -> Dict[str, Any]:
        rule_id = _safe_str(rule_payload.get("rule_id"))
        version = _safe_str(rule_payload.get("version"))
        content_hash = _safe_str(rule_payload.get("content_hash"))
        effect = dict(rule_payload.get("effect") or {})
        condition = dict(rule_payload.get("condition") or {})
        chart_snapshot = dict(case.get("chart_snapshot") or {})
        expected_patterns = [_safe_str(item) for item in _ensure_list(case.get("expected_evidence_patterns")) if _safe_str(item)]
        forbidden_patterns = [_safe_str(item) for item in _ensure_list(case.get("forbidden_conclusions")) if _safe_str(item)]
        expected_conclusions = _ensure_list(case.get("expected_conclusions"))
        evidence_text_parts = [
            _canonical_json(condition),
            _canonical_json(effect),
            _canonical_json(chart_snapshot),
            " ".join([_safe_str(item) for item in _ensure_list(case.get("tags"))]),
        ]
        evidence_text = " ".join(evidence_text_parts).lower()
        conclusion_claim = _safe_str(rule_payload.get("test_conclusion"))
        if not conclusion_claim:
            topic = _safe_str((case.get("query_intent") or {}).get("topic"), "general")
            effect_keys = ",".join(sorted(_safe_str(key) for key in effect.keys())) or "effect"
            conclusion_claim = f"{rule_id} supports {topic} via {effect_keys}"
        conclusion_text = " ".join([conclusion_claim, _canonical_json(effect)]).lower()
        failures: List[str] = []
        warnings: List[str] = []

        missing_patterns = [pattern for pattern in expected_patterns if pattern.lower() not in evidence_text]
        if missing_patterns:
            failures.append("EXPECTED_EVIDENCE_NOT_MATCHED:" + ",".join(missing_patterns))

        forbidden_hits = [pattern for pattern in forbidden_patterns if pattern.lower() in conclusion_text]
        if forbidden_hits:
            failures.append("FORBIDDEN_CONCLUSION_PRODUCED:" + ",".join(forbidden_hits))

        expected_text = " ".join(
            _canonical_json(item) if isinstance(item, dict) else _safe_str(item)
            for item in expected_conclusions
        ).lower()
        if expected_text and not any(token and token in conclusion_text for token in expected_text.replace(",", " ").split()):
            warnings.append("EXPECTED_CONCLUSION_WEAK_MATCH")

        raw_confidence = _safe_float(rule_payload.get("priority"), 0.5) * 0.45 + _safe_float(rule_payload.get("evidence_strength"), 0.5) * 0.55
        confidence = round(max(0.0, min(1.0, raw_confidence)), 3)
        baseline_confidence = None
        for item in expected_conclusions:
            if isinstance(item, dict) and "confidence" in item:
                baseline_confidence = _safe_float(item.get("confidence"))
                break
        if baseline_confidence is None:
            try:
                raw_baseline = float(case.get("baseline_confidence"))
            except (TypeError, ValueError):
                raw_baseline = -1.0
            if raw_baseline >= 0.0:
                baseline_confidence = raw_baseline
        if baseline_confidence is not None and abs(confidence - baseline_confidence) > _safe_float(case.get("max_confidence_drift"), 0.35):
            warnings.append("CONFIDENCE_DRIFT_WARNING")

        verification = self._candidate_test_contract_verification(
            rule_payload,
            force_failure=_safe_bool(case.get("force_verifier_failure"), False),
        )
        if verification.get("result") != "pass":
            failures.append("CONTRACT_VERIFIER_FAILED:" + ",".join(_ensure_list(verification.get("errors"))))

        status = "fail" if failures else ("warning" if warnings else "pass")
        evidence_id = f"ev_{rule_id}_{version}_{content_hash[:12]}"
        return {
            "case_id": _safe_str(case.get("case_id")),
            "status": status,
            "failures": failures,
            "warnings": warnings,
            "evidence_refs": [evidence_id] if content_hash else [],
            "conclusions": [
                {
                    "conclusion_id": f"conclusion_{_safe_str(case.get('case_id')) or 'case'}",
                    "claim": conclusion_claim,
                    "confidence": confidence,
                    "evidence_ids": [evidence_id] if content_hash else [],
                    "generated_by": "engine",
                }
            ],
            "confidence": confidence,
            "verifier": verification,
        }

    def run_rule_test_v02(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._assert_lifecycle(
            token=_safe_str(payload.get("lifecycle_token", "")),
            purpose="test",
            execution_mode="test",
        )
        role = _safe_str(payload.get("actor_role"), "system").lower()
        if role not in {"practitioner", "manager", "admin", "system"}:
            raise PredictiveServiceError("FORBIDDEN", "only practitioner/manager/admin can run rule tests", 403)
        subject = self._rule_subject_for_test(payload)
        cases = self._rule_test_cases_for_payload(payload)
        results = [
            self._run_single_rule_test_case_v02(rule_payload=dict(subject["rule_payload"]), case=case)
            for case in cases
        ]
        pass_count = sum(1 for item in results if item.get("status") == "pass")
        fail_count = sum(1 for item in results if item.get("status") == "fail")
        warning_count = sum(1 for item in results if item.get("status") == "warning")
        overall_status = "fail" if fail_count else ("warning" if warning_count else "pass")
        digest = _payload_hash(
            {
                "rule_candidate_id": subject["rule_candidate_id"],
                "rule_id": subject["rule_id"],
                "version": subject["version"],
                "test_case_ids": [_safe_str(item.get("case_id")) for item in cases],
                "results": results,
            }
        ).split(":", 1)[-1][:16]
        run = RuleTestRun(
            run_id=f"rule_test_run_{digest}",
            rule_candidate_id=subject["rule_candidate_id"],
            rule_id=subject["rule_id"],
            version=subject["version"],
            test_case_ids=[_safe_str(item.get("case_id")) for item in cases],
            results=results,
            pass_count=pass_count,
            fail_count=fail_count,
            warning_count=warning_count,
            overall_status=overall_status,
        ).to_dict()
        run["rule_test_engine"] = RULE_TEST_ENGINE_VERSION_V02
        run["subject_state"] = subject["subject_state"]
        self._rule_test_runs[run["run_id"]] = run
        self._persist()
        self._append_audit_event(
            rule_id=subject["rule_id"],
            event_type="RULE_TEST_ENGINE_V02_RUN",
            severity="info" if overall_status == "pass" else "warning",
            message="rule test engine v0.2 run completed",
            actor_role=role,
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
            details={
                "run_id": run["run_id"],
                "rule_candidate_id": subject["rule_candidate_id"],
                "version": subject["version"],
                "overall_status": overall_status,
                "pass_count": pass_count,
                "fail_count": fail_count,
                "warning_count": warning_count,
            },
        )
        return run

    def get_rule_test_run(self, run_id: str) -> Dict[str, Any]:
        run_id = _safe_str(run_id)
        if run_id not in self._rule_test_runs:
            raise PredictiveServiceError("RULE_TEST_RUN_NOT_FOUND", f"rule test run {run_id} not found", 404)
        return dict(self._rule_test_runs[run_id])

    def _has_recent_passing_rule_test(self, *, rule_candidate_id: str = "", rule_id: str = "", version: str = "") -> bool:
        runs = sorted(
            self._rule_test_runs.values(),
            key=lambda item: _parse_dt(item.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        for run in runs:
            if _safe_str(run.get("overall_status")) != "pass":
                continue
            if rule_candidate_id and _safe_str(run.get("rule_candidate_id")) == rule_candidate_id:
                return True
            if rule_id and version and _safe_str(run.get("rule_id")) == rule_id and _safe_str(run.get("version")) == version:
                return True
        return False

    def register_rule_test_suite(
        self,
        payload: Dict[str, Any],
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
        require_rule_reference: bool = True,
    ) -> Dict[str, Any]:
        requested_status = str(payload.get("status") or "").strip().lower()
        role = str(actor_role or "system").strip().lower()
        if requested_status in {"validated", "active", "deprecated"} and role not in {"manager", "admin", "system"}:
            raise PredictiveServiceError("FORBIDDEN", "validated/active/deprecated requires manager or admin", 403)
        if requested_status == "active":
            raise PredictiveServiceError("RULE_TEST_SUITE_TRANSITION_INVALID", "active suites must be activated through activation API", 409)

        suite = RuleTestSuite.from_payload(payload)
        if not suite.suite_id:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "suite_id is required", 400)
        if not suite.rule_id:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "rule_id is required", 400)
        if not require_rule_reference:
            if suite.status != "draft":
                raise PredictiveServiceError(
                    "RULE_TEST_SUITE_TRANSITION_INVALID",
                    "non-registered-rule suites must start as draft",
                    409,
                )
        else:
            self.get_rule(rule_id=suite.rule_id, version=suite.rule_version, allow_inactive=True)

        key = self._normalize_rule_key(suite.suite_id, suite.version)
        if key in self._rule_test_suites:
            raise PredictiveServiceError(
                "RULE_TEST_SUITE_VERSION_CONFLICT",
                f"Rule test suite {suite.suite_id} version {suite.version} exists",
                409,
            )

        suite.created_by = _safe_str(role, "system")
        suite.created_by_user_id = _safe_int(actor_user_id, 0)
        suite.content_hash = _rule_test_suite_payload_fingerprint(suite.to_dict())
        self._rule_test_suites[key] = suite
        self._append_audit_event(
            rule_id=suite.suite_id,
            event_type="RULE_TEST_SUITE_REGISTERED",
            severity="info",
            message="rule test suite version registered",
            actor_role=role,
            actor_user_id=actor_user_id,
            details={"rule_id": suite.rule_id, "version": suite.version, "status": suite.status},
        )
        self._persist()
        return {
            "suite_id": suite.suite_id,
            "operation": "created",
            "version": suite.version,
        }

    def activate_rule_test_suite(
        self,
        *,
        suite_id: str,
        target_version: str,
        actor_role: str = "system",
        actor_user_id: int = 0,
    ) -> RuleTestSuite:
        role = str(actor_role or "system").strip().lower()
        if role not in {"manager", "admin", "system"}:
            raise PredictiveServiceError("FORBIDDEN", "only reviewer roles can activate rule test suites", 403)

        target_version = _safe_str(target_version)
        if not target_version:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "target_version required", 400)

        target_key = self._normalize_rule_key(suite_id, target_version)
        target = self._rule_test_suites.get(target_key)
        if not target:
            raise PredictiveServiceError("RULE_TEST_SUITE_NOT_FOUND", f"Rule test suite {suite_id} version {target_version} not found", 404)
        if target.status != "validated":
            raise PredictiveServiceError("RULE_TEST_SUITE_TRANSITION_INVALID", "only validated suites can be activated", 409)

        current_version = self._active_rule_test_suites.get(suite_id)
        if current_version and current_version != target_version:
            old_key = self._normalize_rule_key(suite_id, current_version)
            old_suite = self._rule_test_suites.get(old_key)
            if old_suite and old_suite.status == "active":
                old_suite.status = "validated"
                old_suite.updated_at = _utcnow_iso()
                self._rule_test_suites[old_key] = old_suite

        target.status = "active"
        target.approved_by = _safe_str(role, "system")
        target.approved_by_user_id = _safe_int(actor_user_id, 0)
        target.approved_at = _utcnow_iso()
        target.updated_at = _utcnow_iso()
        self._active_rule_test_suites[suite_id] = target_version
        self._rule_test_suites[target_key] = target
        self._append_audit_event(
            rule_id=suite_id,
            event_type="RULE_TEST_SUITE_ACTIVATED",
            severity="info",
            message="rule test suite activated",
            actor_role=role,
            actor_user_id=actor_user_id,
            details={"rule_id": target.rule_id, "version": target_version},
        )
        self._persist()
        return target

    def update_rule_test_suite_status(
        self,
        suite_id: str,
        target_status: str,
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
        version: Optional[str] = None,
    ) -> RuleTestSuite:
        role = str(actor_role or "system").strip().lower()
        target_status = str(target_status or "").strip().lower()
        if target_status not in RULE_TEST_SUITE_STATES:
            raise PredictiveServiceError("INVALID_RULE_TEST_SUITE_STATUS", "invalid target_status")
        if role not in {"manager", "admin", "system"}:
            raise PredictiveServiceError("FORBIDDEN", "only reviewer roles can update rule test suite status", 403)
        if target_status == "active":
            return self.activate_rule_test_suite(
                suite_id=suite_id,
                target_version=version or "",
                actor_role=actor_role,
                actor_user_id=actor_user_id,
            )

        if not _safe_str(suite_id):
            raise PredictiveServiceError("RULE_TEST_SUITE_NOT_FOUND", "suite_id is required", 404)
        target = self.get_rule_test_suite(suite_id, version=version, allow_inactive=True)
        if target.status == "active":
            raise PredictiveServiceError(
                "RULE_TEST_SUITE_IMMUTABLE",
                "active rule test suite is immutable; submit a new suite version and activate it",
                409,
            )

        old_status = _safe_str(target.status)
        target.status = target_status
        if target_status in {"validated", "deprecated"} and _safe_str(old_status) != target_status:
            target.approved_by = _safe_str(role, "system")
            target.approved_by_user_id = _safe_int(actor_user_id, 0)
            target.approved_at = _utcnow_iso()
        target.updated_at = _utcnow_iso()
        self._rule_test_suites[self._normalize_rule_key(target.suite_id, target.version)] = target
        self._append_audit_event(
            rule_id=suite_id,
            event_type="RULE_TEST_SUITE_STATUS_UPDATED",
            severity="info",
            message=f"status changed {old_status} -> {target_status}",
            actor_role=role,
            actor_user_id=actor_user_id,
            details={"rule_id": target.rule_id, "version": target.version, "status": target_status},
        )
        self._persist()
        return target

    def deprecate_rule_test_suite(
        self,
        suite_id: str,
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
        version: Optional[str] = None,
    ) -> RuleTestSuite:
        return self.update_rule_test_suite_status(
            suite_id=suite_id,
            target_status="deprecated",
            actor_role=actor_role,
            actor_user_id=actor_user_id,
            version=version,
        )

    def get_rule_test_suite(self, suite_id: str, *, version: Optional[str] = None, allow_inactive: bool = False) -> RuleTestSuite:
        if not suite_id:
            raise PredictiveServiceError("RULE_TEST_SUITE_NOT_FOUND", "suite_id is required", 404)
        if version:
            suite = self._rule_test_suites.get(self._normalize_rule_key(suite_id, version))
            if not suite:
                raise PredictiveServiceError("RULE_TEST_SUITE_NOT_FOUND", f"Rule test suite {suite_id} version {version} not found", 404)
            return suite

        active_version = self._active_rule_test_suites.get(suite_id)
        if active_version:
            suite = self._rule_test_suites.get(self._normalize_rule_key(suite_id, active_version))
            if suite:
                return suite

        if not allow_inactive:
            raise PredictiveServiceError("RULE_TEST_SUITE_NOT_FOUND", f"Rule test suite {suite_id} not found", 404)

        versions = [v for _, v in (_split_rule_key(k) for k in self._rule_test_suites if _split_rule_key(k)[0] == suite_id)]
        if versions:
            versions = sorted(versions, reverse=True)
            suite = self._rule_test_suites.get(self._normalize_rule_key(suite_id, versions[0]))
            if suite:
                return suite

        raise PredictiveServiceError("RULE_TEST_SUITE_NOT_FOUND", f"Rule test suite {suite_id} not found", 404)

    def list_rule_test_suites(
        self,
        *,
        rule_id: Optional[str] = None,
        status: Optional[str] = None,
        suite_id: Optional[str] = None,
    ) -> List[RuleTestSuite]:
        out: List[RuleTestSuite] = []
        for key, suite in self._rule_test_suites.items():
            sid, version = _split_rule_key(key)
            if suite_id and suite_id != sid:
                continue
            if rule_id and rule_id != suite.rule_id:
                continue
            if status == "active" and self._active_rule_test_suites.get(sid) != version:
                continue
            if status and status != "active" and suite.status != status:
                continue
            out.append(suite)
        return out

    def retrieve_rules(
        self,
        prediction_id: str,
        topic: str,
        plugin_claims: List[str],
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
        execution_mode: str = "runtime",
        lifecycle_token: str = "",
    ) -> List[RuleKernel]:
        self._assert_lifecycle(
            token=_safe_str(lifecycle_token),
            purpose="retrieval",
            execution_mode=execution_mode,
        )
        if not prediction_id:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "prediction_id is required")
        if not topic:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "topic is required")
        topic_norm = str(topic).strip()
        if not plugin_claims:
            self._append_audit_event(
                rule_id="",
                event_type="GATEKEEPER_MISSING",
                severity="high",
                message="plugin claims required",
                actor_role=_safe_str(actor_role, "system"),
                actor_user_id=_safe_int(actor_user_id, 0),
                details={"execution_mode": execution_mode, "prediction_id": prediction_id},
            )
            raise PredictiveServiceError("GATEKEEPER_MISSING", "plugin claims required", 403)

        out: List[RuleKernel] = []
        for rid, version in self._active_rules.items():
            key = self._normalize_rule_key(rid, version)
            rule = self._rule_kernels.get(key)
            if not rule:
                continue
            if not self._authorize_claim(rule=rule, plugin_claims=plugin_claims):
                self._append_audit_event(
                    rule_id=rule.rule_id,
                    event_type="GATEKEEPER_DENIED",
                    severity="warning",
                    message="rule not authorized by claim",
                    actor_role=_safe_str(actor_role, "system"),
                    actor_user_id=_safe_int(actor_user_id, 0),
                    source=RULE_GATEKEEPER_PROTOCOL,
                    details={"rule_id": rule.rule_id, "version": version},
                )
                continue
            if rule.effect_scope and topic_norm not in rule.effect_scope:
                continue
            if rule.allowed_topics and topic_norm not in rule.allowed_topics:
                continue
            out.append(rule)
        return out

    def resolve_rules(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        input_obj = RuleResolverInput.from_payload(payload)
        actor_role = str(payload.get("actor_role") or "system").strip().lower()
        actor_user_id = _safe_int(payload.get("actor_user_id"), 0)
        self._assert_lifecycle(
            token=_safe_str(input_obj.lifecycle_token),
            purpose=_safe_str(input_obj.execution_mode, "runtime"),
            execution_mode=_safe_str(input_obj.execution_mode, "runtime"),
        )
        candidates = input_obj.rule_candidates
        if not input_obj.plugin_claims:
            self._append_audit_event(
                rule_id="",
                event_type="GATEKEEPER_MISSING",
                severity="high",
                message="plugin claims required",
                actor_role=_safe_str(actor_role, "system"),
                actor_user_id=_safe_int(actor_user_id, 0),
                details={"execution_mode": _safe_str(input_obj.execution_mode, "runtime")},
            )
            raise PredictiveServiceError("GATEKEEPER_MISSING", "plugin claims required", 403)

        if not candidates:
            raise PredictiveServiceError("RULE_SCOPE_VIOLATION", "No rule candidates", 409)

        time_weight = input_obj.runtime_context.get("time_weight") or {}
        if not isinstance(time_weight, dict) or not {"natal", "decade", "year"} <= set(time_weight.keys()):
            raise PredictiveServiceError("TIME_WEIGHT_MISSING", "time_weight must include natal/decade/year")

        candidate_rules: List[RuleKernel] = []
        for item in candidates:
            rule_id = str(item.get("rule_id", "")).strip()
            activation_score = _safe_float(item.get("activation_score"), 0.0)
            if not rule_id or activation_score <= 0.0:
                continue

            rule_version = _safe_str(item.get("version") or input_obj.target_version)
            rule: Optional[RuleKernel] = None
            if rule_version:
                try:
                    rule = self.get_rule(rule_id, version=rule_version, allow_inactive=input_obj.allow_sandbox)
                except PredictiveServiceError:
                    rule = None

            if rule is None and not input_obj.allow_sandbox:
                try:
                    rule = self.get_rule(rule_id, allow_inactive=False)
                except PredictiveServiceError:
                    rule = None

            if rule is None and input_obj.allow_sandbox:
                payload_rule = item.get("rule_payload")
                if isinstance(payload_rule, dict):
                    try:
                        rule = RuleKernel.from_payload(payload_rule)
                    except Exception:
                        rule = None

            if rule is None:
                continue

            if not self._authorize_claim(rule=rule, plugin_claims=input_obj.plugin_claims):
                self._append_audit_event(
                    rule_id=rule_id,
                    event_type="GATEKEEPER_DENIED",
                    severity="high",
                    message="rule denied by gatekeeper",
                    actor_role=_safe_str(actor_role, "system"),
                    actor_user_id=_safe_int(actor_user_id, 0),
                    details={"rule_id": rule_id, "version": rule.version},
                )
                raise PredictiveServiceError("GATEKEEPER_DENIED", "rule denied by gatekeeper", 403)

            if not input_obj.allow_sandbox and rule.status != "active":
                continue
            if rule.effect_scope and input_obj.topic not in rule.effect_scope:
                continue
            if rule.allowed_topics and input_obj.topic not in rule.allowed_topics:
                continue
            candidate_rules.append(rule)

        if not candidate_rules:
            raise PredictiveServiceError("RULE_SCOPE_VIOLATION", "No eligible rule for topic scope")

        forbidden_family_mix = input_obj.runtime_context.get("forbidden_family_mix")
        if isinstance(forbidden_family_mix, list) and all(isinstance(item, list) and len(item) == 2 for item in forbidden_family_mix):
            active_families = {r.theory_family for r in candidate_rules}
            for left, right in forbidden_family_mix:
                if str(left) in active_families and str(right) in active_families and len(candidate_rules) > 1:
                    raise PredictiveServiceError("RULE_CONFLICT_UNRESOLVED", "rule family conflict requires manual review")

        # v0 strategy: priority first, simple scope/conflict resolution
        ordered = sorted(candidate_rules, key=lambda item: (_safe_float(item.priority), _safe_float(item.evidence_strength)), reverse=True)
        active: List[RuleKernel] = []
        suppressed: List[str] = []
        decision_trace: List[Dict[str, Any]] = []
        conflict_actions: List[Dict[str, Any]] = []

        for rule in ordered:
            same_family = [r for r in active if r.theory_family == rule.theory_family]
            if not same_family:
                active.append(rule)
                decision_trace.append({"rule_id": rule.rule_id, "action": "apply", "weight": rule.priority})
                continue

            if rule.conflict_policy == "override":
                dropped = same_family[0]
                active.remove(dropped)
                suppressed.append(dropped.rule_id)
                conflict_actions.append(
                    {
                        "rule_id": dropped.rule_id,
                        "conflict_with": rule.rule_id,
                        "action": "suppress",
                        "reason": "family_override",
                    }
                )
                active.append(rule)
                decision_trace.append({"rule_id": rule.rule_id, "action": "override", "weight": rule.priority})
            elif rule.conflict_policy == "merge":
                active.append(rule)
                decision_trace.append({"rule_id": rule.rule_id, "action": "merge", "weight": rule.priority})
            elif rule.conflict_policy == "degrade":
                rule = RuleKernel(
                    rule_id=rule.rule_id,
                    theory_family=rule.theory_family,
                    condition=rule.condition,
                    effect=rule.effect,
                    priority=min(rule.priority, 0.5),
                    evidence_strength=rule.evidence_strength,
                    conflict_policy=rule.conflict_policy,
                    version=rule.version,
                    owner_plugin=rule.owner_plugin,
                    status=rule.status,
                    content_hash=rule.content_hash,
                    created_by=rule.created_by,
                    created_by_user_id=rule.created_by_user_id,
                    approved_by=rule.approved_by,
                    approved_by_user_id=rule.approved_by_user_id,
                    approved_at=rule.approved_at,
                    effect_scope=rule.effect_scope,
                    allowed_topics=rule.allowed_topics,
                    created_at=rule.created_at,
                )
                active.append(rule)
                decision_trace.append({"rule_id": rule.rule_id, "action": "degrade", "weight": rule.priority})
            elif rule.conflict_policy == "defer_manual_review":
                raise PredictiveServiceError("RULE_CONFLICT_UNRESOLVED", "manual review required")
            else:
                suppressed.append(rule.rule_id)
                decision_trace.append({"rule_id": rule.rule_id, "action": "suppress", "weight": rule.priority})

        resolved_effect: Dict[str, float] = {}
        for rule in active:
            for key, value in (rule.effect or {}).items():
                resolved_effect[key] = resolved_effect.get(key, 0.0) + _safe_float(value) * _safe_float(rule.priority)

        resolver_snapshot = {
            "resolver_version": "v18.1",
            "decision_rationale": decision_trace,
            "conflict_actions": conflict_actions,
            "time_weight": time_weight,
            "runtime_context": input_obj.runtime_context,
            "resolver_lifecycle": {
                "execution_mode": _safe_str(input_obj.execution_mode, "runtime"),
                "gatekeeper_protocol": RULE_GATEKEEPER_PROTOCOL,
                "lifecycle_enforced": V18_1_STRICT_LIFECYCLE,
                "plugin_claim_count": len(input_obj.plugin_claims),
            },
        }

        return RuleResolverOutput(
            prediction_id=input_obj.prediction_id,
            status="resolved",
            active_rules=[r.rule_id for r in active],
            suppressed_rules=suppressed,
            resolved_effect=resolved_effect,
            resolver_snapshot=resolver_snapshot,
        ).to_dict()

    def _evaluate_rule_test_v01(self, *, hit: int, fp: int, fn: int, tn: int) -> Dict[str, Any]:
        total_cases = max(0, hit + fp + fn + tn)
        safe_div = lambda p, q: _safe_float(p / q, 0.0) if q else 0.0

        precision = safe_div(hit, hit + fp)
        recall = safe_div(hit, hit + fn)
        fp_rate = safe_div(fp, total_cases)
        fn_rate = safe_div(fn, total_cases)
        hit_rate = safe_div(hit, total_cases)
        conflict_rate = safe_div(fp + fn, total_cases)
        quality_score = _safe_float((precision + recall) / 2.0, 0.0)
        quality_gate = "pass"

        rationale = []
        if total_cases < _safe_int(RULE_TEST_ENGINE_THRESHOLD_V01.get("min_cases"), 5):
            quality_gate = "review"
            rationale.append("sample_size_below_5")
            recommended_status = "experimental"
        elif (
            precision >= _safe_float(RULE_TEST_ENGINE_THRESHOLD_V01.get("precision_min"), 0.8)
            and recall >= _safe_float(RULE_TEST_ENGINE_THRESHOLD_V01.get("recall_min"), 0.8)
            and conflict_rate <= _safe_float(RULE_TEST_ENGINE_THRESHOLD_V01.get("conflict_max"), 0.2)
        ):
            recommended_status = "validated"
            rationale.append("precision_recall_pass")
        elif (
            precision <= _safe_float(RULE_TEST_ENGINE_THRESHOLD_V01.get("precision_deprecate_max"), 0.5)
            or recall <= _safe_float(RULE_TEST_ENGINE_THRESHOLD_V01.get("recall_deprecate_max"), 0.5)
            or conflict_rate >= _safe_float(RULE_TEST_ENGINE_THRESHOLD_V01.get("high_conflict_rate"), 0.6)
        ):
            recommended_status = "deprecated"
            rationale.append("precision_recall_fail")
        else:
            recommended_status = "experimental"
            rationale.append("mixed_signal")

        if quality_score < _safe_float(RULE_TEST_ENGINE_THRESHOLD_V01.get("quality_score_min"), 0.65):
            quality_gate = "review"
        elif conflict_rate > _safe_float(RULE_TEST_ENGINE_THRESHOLD_V01.get("needs_review_conflict_rate"), 0.35):
            quality_gate = "needs_review"

        return {
            "recommended_status": recommended_status,
            "quality_gate": quality_gate,
            "quality_score": quality_score,
            "precision": precision,
            "recall": recall,
            "hit_rate": hit_rate,
            "false_positive_rate": fp_rate,
            "false_negative_rate": fn_rate,
            "conflict_rate": conflict_rate,
            "total_cases": total_cases,
            "rationale": rationale,
        }

    def _rule_evidence_from_resolver(self, resolved_rules: Dict[str, Any], *, chart_snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        active_rule_ids = _ensure_list(resolved_rules.get("active_rules"))
        resolved_effect = dict(resolved_rules.get("resolved_effect") or {})
        facts = _ensure_list(chart_snapshot.get("matched_facts") or chart_snapshot.get("facts"))
        topic_hint = _normalize_topic(chart_snapshot.get("topic") or chart_snapshot.get("topic_hint") or chart_snapshot.get("detected_topic"))
        wealth_features = self._wealth_features_from_chart(chart_snapshot) if topic_hint in {"wealth", "general"} else []
        for rule_id in active_rule_ids:
            try:
                rule = self.get_rule(_safe_str(rule_id), allow_inactive=False)
            except PredictiveServiceError:
                continue
            if "wealth" in [_safe_str(item).lower() for item in _ensure_list(rule.allowed_topics)] or "wealth" in [_safe_str(item).lower() for item in _ensure_list(rule.effect_scope)]:
                for feature in wealth_features:
                    feature_id = _safe_str(feature.get("feature_id"))
                    if not feature_id:
                        continue
                    evidence_id = f"ev_{rule.rule_id}_{rule.version}_{feature_id}"[:180]
                    strength = _safe_float(feature.get("strength"), 0.0)
                    stability = _safe_float(feature.get("stability"), 0.5)
                    risk = _safe_float(feature.get("risk"), 0.0)
                    relevance = _safe_float(feature.get("wealth_relevance"), 0.0)
                    confidence_delta = max(0.0, min(1.0, strength * (0.45 + stability * 0.35) * relevance * (1.0 - min(0.7, risk) * 0.25)))
                    out.append(
                        {
                            "evidence_id": evidence_id,
                            "rule_id": rule.rule_id,
                            "version": rule.version,
                            "content_hash": rule.content_hash,
                            "feature_id": feature_id,
                            "feature_type": _safe_str(feature.get("feature_type")),
                            "feature_label": _safe_str(feature.get("feature_label") or feature.get("label")),
                            "evidence_type": "feature_evidence",
                            "semantic_type": _safe_str(feature.get("feature_type")),
                            "feature": feature,
                            "matched_facts": _ensure_list(feature.get("matched_facts")),
                            "effect": dict(feature.get("effect") or {}),
                            "risk": risk,
                            "stability": stability,
                            "strength": strength,
                            "uncertainty": _safe_float(feature.get("uncertainty"), 0.0),
                            "wealth_relevance": relevance,
                            "confidence_delta": round(confidence_delta, 4),
                            "resolved_effect": resolved_effect,
                            "evidence_source": "wealth_feature_engine_v1",
                        }
                    )
                continue
            evidence_id = f"ev_{rule.rule_id}_{rule.version}_{rule.content_hash[:12]}"
            out.append(
                {
                    "evidence_id": evidence_id,
                    "rule_id": rule.rule_id,
                    "version": rule.version,
                    "content_hash": rule.content_hash,
                    "matched_facts": facts,
                    "effect": dict(rule.effect or {}),
                    "confidence_delta": round(_safe_float(rule.priority) * _safe_float(rule.evidence_strength), 4),
                    "resolved_effect": resolved_effect,
                }
            )
        return out

    def _conclusions_from_evidence(self, *, topic: str, rule_evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if _normalize_topic(topic) == "wealth":
            return self._wealth_conclusions_from_feature_evidence(rule_evidence)
        if not rule_evidence:
            return []
        conclusions: List[Dict[str, Any]] = []
        for index, evidence in enumerate(rule_evidence):
            effect = dict(evidence.get("effect") or {})
            effect_key = next(iter(effect.keys()), _normalize_topic(topic))
            score = _safe_float(effect.get(effect_key), 0.0)
            conclusions.append(
                {
                    "conclusion_id": f"conclusion_{index + 1}",
                    "topic": _normalize_topic(topic),
                    "claim": f"{_normalize_topic(topic)} signal is supported by rule {evidence.get('rule_id')}",
                    "polarity": "support" if score >= 0.0 else "risk",
                    "confidence": min(1.0, _safe_float(evidence.get("confidence_delta"), 0.0)),
                    "evidence_ids": [_safe_str(evidence.get("evidence_id"))],
                    "generated_by": "engine",
                }
            )
        return conclusions

    def _clamped_float(self, value: Any, fallback: float = 0.0) -> float:
        return max(0.0, min(1.0, _safe_float(value, fallback)))

    def _normalize_wealth_feature(self, payload: Dict[str, Any], *, fallback_type: str = "wealth_signal") -> Dict[str, Any]:
        feature_id = _safe_str(payload.get("feature_id") or payload.get("id") or fallback_type)
        raw_feature_type = _safe_str(payload.get("feature_type") or payload.get("type") or fallback_type)
        type_aliases = {
            "wealth_star_state": "wealth_strength",
            "wealth_path_type": "wealth_strength",
            "wealth_vault_state": "wealth_vault",
            "output_to_wealth": "output_generate_wealth",
            "wealth_constraint": "constraint_structure",
            "authority_wealth_constraint": "constraint_structure",
            "luck_flow_activation": "flow_activation",
            "relationship_volatility": "stability_risk",
            "wealth_stability_risk": "stability_risk",
        }
        feature_type = type_aliases.get(raw_feature_type, raw_feature_type)
        strength = self._clamped_float(payload.get("strength") if "strength" in payload else payload.get("score"), 0.0)
        stability = self._clamped_float(payload.get("stability"), 0.62)
        risk = self._clamped_float(payload.get("risk"), 0.0)
        uncertainty = self._clamped_float(payload.get("uncertainty"), max(0.05, 1.0 - stability))
        relevance = self._clamped_float(payload.get("wealth_relevance"), 0.72)
        effect = dict(payload.get("effect") or {})
        if not effect and feature_type != "stability_risk":
            effect = {"wealth": round(strength * relevance, 3)}
        label = _safe_str(payload.get("label") or payload.get("plain_name") or payload.get("summary") or feature_type)
        return {
            "feature_id": feature_id.replace(" ", "_")[:96],
            "feature_type": feature_type,
            "matched_facts": [_safe_str(item) for item in _ensure_list(payload.get("matched_facts")) if _safe_str(item)][:8],
            "strength": round(strength, 3),
            "stability": round(stability, 3),
            "effect": effect,
            "risk": round(risk, 3),
            "uncertainty": round(uncertainty, 3),
            "wealth_relevance": round(relevance, 3),
            "label": label,
            "feature_label": label,
            "source": _safe_str(payload.get("source"), "wealth_engine_v1"),
            "source_knowledge_id": _safe_str(payload.get("source_knowledge_id")),
            "knowledge_mode": _safe_str(payload.get("knowledge_mode")),
            "experimental": _safe_bool(payload.get("experimental"), False),
        }

    def _wealth_features_from_chart(self, chart_snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        provided = _ensure_list(chart_snapshot.get("wealth_features") or chart_snapshot.get("structured_wealth_features"))
        out: List[Dict[str, Any]] = []
        for row in provided:
            if isinstance(row, dict):
                out.append(self._normalize_wealth_feature(row))
        wealth_domain = chart_snapshot.get("wealth_domain_bundle")
        if isinstance(wealth_domain, dict):
            for row in _ensure_list(wealth_domain.get("wealth_evidence")):
                if isinstance(row, dict):
                    out.append(self._normalize_wealth_feature(row, fallback_type="wealth_domain_evidence"))

        tensor = dict(chart_snapshot.get("physics_tensor") or chart_snapshot)
        meta = dict(tensor.get("meta") or {})
        wealth_code = dict(chart_snapshot.get("wealth_code") or meta.get("wealth_code") or {})
        wealth_profile = dict(chart_snapshot.get("wealth_profile") or meta.get("wealth_profile") or {})

        if not wealth_code and (tensor.get("ten_gods_runtime") or tensor.get("facts") or tensor.get("four_pillars")):
            try:
                from v17_rebirth.backend.logic.L0_physics_fields.bazi_image_core import resolve_bazi_image
                from v17_rebirth.backend.logic.L3_modern_narrative.wealth_code_core import resolve_wealth_code
                from v17_rebirth.backend.logic.L3_modern_narrative.wealth_profile_core import resolve_wealth_profile

                tensor = dict(tensor)
                meta = dict(tensor.get("meta") or {})
                if "bazi_image" not in meta:
                    meta["bazi_image"] = resolve_bazi_image(tensor).get("bazi_image", {})
                tensor["meta"] = meta
                if not wealth_profile:
                    wealth_profile = dict(resolve_wealth_profile(tensor).get("wealth_profile") or {})
                    meta["wealth_profile"] = wealth_profile
                    tensor["meta"] = meta
                wealth_code = dict(resolve_wealth_code(tensor).get("wealth_code") or {})
            except Exception:
                wealth_code = wealth_code or {}
                wealth_profile = wealth_profile or {}

        out.extend(self._wealth_features_from_existing_wealth_outputs(wealth_code, wealth_profile, tensor))

        matched_facts = [_safe_str(item) for item in _ensure_list(chart_snapshot.get("matched_facts") or chart_snapshot.get("facts")) if _safe_str(item)]
        fact_text = " ".join(matched_facts + [_safe_str(row.get("fact")) for row in _ensure_list(tensor.get("facts")) if isinstance(row, dict)])
        has_baseline_wealth = any(item in fact_text for item in {"wealth_visible", "complete_birth_fields", "output_visible", "cashflow_segment", "quality_visible", "durable_visible", "财", "收入", "食伤生财", "财星"})
        if has_baseline_wealth:
            out.extend(
                [
                self._normalize_wealth_feature(
                    {
                        "feature_id": "wealth_baseline_strength",
                        "feature_type": "wealth_strength",
                        "matched_facts": matched_facts or ["wealth_visible"],
                        "strength": 0.86,
                        "stability": 0.82,
                        "risk": 0.05,
                        "uncertainty": 0.18,
                        "wealth_relevance": 0.9,
                        "effect": {"wealth": 0.72},
                        "label": "财星强弱 / 财富基础信号",
                    }
                ),
                self._normalize_wealth_feature(
                    {
                        "feature_id": "wealth_baseline_flow_context",
                        "feature_type": "flow_activation",
                        "matched_facts": matched_facts or ["wealth_visible"],
                        "strength": 0.54,
                        "stability": 0.58,
                        "risk": 0.2,
                        "uncertainty": 0.42,
                        "wealth_relevance": 0.62,
                        "effect": {"timing_activation": 0.44, "wealth_stability": 0.18},
                        "label": "财富问题时间上下文",
                    }
                ),
                ]
            )

        if any(term in fact_text for term in {"合", "冲", "刑", "害", "冲合", "刑害", "volatile", "stability"}):
            out.append(
                self._normalize_wealth_feature(
                    {
                        "feature_id": "relationship_volatility_risk",
                        "feature_type": "stability_risk",
                        "matched_facts": matched_facts[:6] or ["relation_volatility"],
                        "strength": 0.42,
                        "stability": 0.35,
                        "risk": 0.62,
                        "uncertainty": 0.58,
                        "wealth_relevance": 0.38,
                        "effect": {"wealth_stability": -0.28, "risk": 0.62},
                        "label": "合冲刑害稳定性风险",
                    }
                )
            )

        unique: Dict[str, Dict[str, Any]] = {}
        for feature in out:
            feature_id = _safe_str(feature.get("feature_id"))
            if not feature_id:
                continue
            if feature_id not in unique or _safe_float(feature.get("strength"), 0.0) > _safe_float(unique[feature_id].get("strength"), 0.0):
                unique[feature_id] = feature
        return list(unique.values())[:12]

    def _wealth_features_from_existing_wealth_outputs(self, wealth_code: Dict[str, Any], wealth_profile: Dict[str, Any], tensor: Dict[str, Any]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        profile_evidence = _ensure_list(wealth_profile.get("evidence"))
        if wealth_profile:
            out.append(
                self._normalize_wealth_feature(
                    {
                        "feature_id": "wealth_star_strength",
                        "feature_type": "wealth_strength",
                        "matched_facts": profile_evidence[:6],
                        "strength": _safe_float(wealth_profile.get("score"), 0.0),
                        "stability": _safe_float(wealth_profile.get("confidence"), 0.58),
                        "risk": _safe_float(wealth_profile.get("risk"), 0.25),
                        "uncertainty": max(0.05, 1.0 - _safe_float(wealth_profile.get("confidence"), 0.58)),
                        "wealth_relevance": 0.9,
                        "effect": {"wealth": _safe_float(wealth_profile.get("score"), 0.0), "income_stability": 1.0 - _safe_float(wealth_profile.get("risk"), 0.25)},
                        "label": "财星状态",
                    }
                )
            )

        primary_path = dict(wealth_code.get("primary_wealth_path") or {})
        if primary_path:
            path_id = _safe_str(primary_path.get("id"), "primary_wealth_path")
            score = _safe_float(primary_path.get("score") or primary_path.get("path_graph_score") or wealth_code.get("score"), 0.0)
            out.append(
                self._normalize_wealth_feature(
                    {
                        "feature_id": f"wealth_path_{path_id}",
                        "feature_type": "wealth_strength",
                        "matched_facts": _ensure_list(primary_path.get("evidence")),
                        "strength": score,
                        "stability": _safe_float(wealth_code.get("confidence"), 0.62),
                        "risk": _safe_float(wealth_code.get("risk"), 0.22),
                        "uncertainty": 1.0 - _safe_float(wealth_code.get("confidence"), 0.62),
                        "wealth_relevance": 0.94,
                        "effect": {"wealth": score, "path_closure": score},
                        "label": _safe_str(primary_path.get("plain_name") or primary_path.get("plain_summary") or "财富路径类型"),
                    }
                )
            )
            if path_id in {"output_to_wealth", "output_work_to_money"} or "输出" in _safe_str(primary_path.get("plain_summary")):
                out.append(
                    self._normalize_wealth_feature(
                        {
                            "feature_id": "output_generates_wealth",
                            "feature_type": "output_generate_wealth",
                            "matched_facts": _ensure_list(primary_path.get("evidence")),
                            "strength": max(0.5, score),
                            "stability": _safe_float(wealth_code.get("confidence"), 0.62),
                            "risk": _safe_float(wealth_code.get("risk"), 0.22),
                            "uncertainty": 0.28,
                            "wealth_relevance": 0.9,
                            "effect": {"wealth": score, "income_stability": min(0.72, score)},
                            "label": "食伤生财 / 输出变现",
                        }
                    )
                )

        vault = dict(wealth_code.get("wealth_vault") or {})
        if vault and (vault.get("has_vault_signal") or vault.get("vault_state")):
            state = _safe_str(vault.get("vault_state"), "static")
            activated = state == "activated"
            out.append(
                self._normalize_wealth_feature(
                    {
                        "feature_id": "wealth_vault_state",
                        "feature_type": "wealth_vault",
                        "matched_facts": _ensure_list(vault.get("evidence")) or [_safe_str(vault.get("plain_summary"))],
                        "strength": 0.72 if activated else 0.56,
                        "stability": 0.7 if activated else 0.52,
                        "risk": 0.18 if activated else 0.32,
                        "uncertainty": 0.22 if activated else 0.42,
                        "wealth_relevance": 0.84,
                        "effect": {"wealth_retention": 0.72 if activated else 0.48, "income_stability": 0.56 if activated else 0.36},
                        "label": "财库状态",
                    }
                )
            )

        for row in _ensure_list(wealth_code.get("secondary_paths"))[:4]:
            if not isinstance(row, dict):
                continue
            path_id = _safe_str(row.get("id"))
            if path_id in {"output_controls_pressure", "wealth_officer_platform"}:
                out.append(
                    self._normalize_wealth_feature(
                        {
                            "feature_id": f"authority_constraint_{path_id}",
                            "feature_type": "constraint_structure",
                            "matched_facts": _ensure_list(row.get("evidence")),
                            "strength": _safe_float(row.get("score"), 0.48),
                            "stability": _safe_float(row.get("confidence"), 0.55),
                            "risk": _safe_float(row.get("risk"), 0.38),
                            "uncertainty": 0.35,
                            "wealth_relevance": 0.72,
                            "effect": {"wealth": _safe_float(row.get("score"), 0.48) * 0.55, "risk": _safe_float(row.get("risk"), 0.38)},
                            "label": "官杀制约财富",
                        }
                    )
                )

        watchlist = [row for row in _ensure_list(wealth_code.get("flow_year_watchlist")) if isinstance(row, dict)]
        if watchlist:
            top = watchlist[0]
            state = _safe_str(dict(top.get("mechanism_state_snapshot") or {}).get("top_state"))
            volatile = state in {"volatile", "leaking", "blocked"}
            out.append(
                self._normalize_wealth_feature(
                    {
                        "feature_id": "luck_flow_activation",
                        "feature_type": "flow_activation",
                        "matched_facts": [_safe_str(top.get("year")), _safe_str(top.get("focus")), _safe_str(state)],
                        "strength": _safe_float(top.get("path_score") or top.get("score"), 0.52),
                        "stability": 0.42 if volatile else 0.62,
                        "risk": 0.58 if volatile else 0.24,
                        "uncertainty": 0.46 if volatile else 0.28,
                        "wealth_relevance": 0.76,
                        "effect": {"timing_activation": 0.65, "wealth_stability": -0.18 if volatile else 0.22},
                        "label": "大运流年引动",
                    }
                )
            )

        leakage = [row for row in _ensure_list(wealth_code.get("leakage_points")) if isinstance(row, dict)]
        if leakage:
            out.append(
                self._normalize_wealth_feature(
                    {
                        "feature_id": "wealth_leakage_risk",
                        "feature_type": "stability_risk",
                        "matched_facts": [_safe_str(row.get("plain_summary") or row.get("id")) for row in leakage[:4]],
                        "strength": max([_safe_float(row.get("risk"), 0.45) for row in leakage] or [0.45]),
                        "stability": 0.38,
                        "risk": max([_safe_float(row.get("risk"), 0.45) for row in leakage] or [0.45]),
                        "uncertainty": 0.48,
                        "wealth_relevance": 0.68,
                        "effect": {"wealth_stability": -0.36, "risk": 0.62},
                        "label": "财富稳定性风险",
                    }
                )
            )
        return out

    def _wealth_conclusions_from_feature_evidence(self, rule_evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        feature_rows = [row for row in rule_evidence if isinstance(row, dict) and _safe_str(row.get("feature_id"))]
        if not feature_rows:
            return []
        support_types = {"wealth_strength", "wealth_vault", "output_generate_wealth", "constraint_structure", "flow_activation"}
        support = [
            row for row in feature_rows
            if _safe_str(row.get("feature_type")) in support_types and _safe_float(dict(row.get("effect") or {}).get("wealth"), 0.0) > 0.0
        ]
        if not support:
            return []
        risk_rows = [
            row for row in feature_rows
            if _safe_float(row.get("risk"), 0.0) >= 0.42 or _safe_float(row.get("stability"), 1.0) <= 0.45 or _safe_str(row.get("feature_type")) == "stability_risk"
        ]
        conclusions: List[Dict[str, Any]] = []
        top_support = sorted(support, key=lambda row: _safe_float(row.get("confidence_delta"), 0.0), reverse=True)[:4]
        support_ids = [_safe_str(row.get("evidence_id")) for row in top_support if _safe_str(row.get("evidence_id"))]
        labels = [_safe_str(dict(row.get("feature") or {}).get("label") or row.get("feature_type")) for row in top_support]
        avg_support = sum(_safe_float(row.get("confidence_delta"), 0.0) for row in top_support) / max(1, len(top_support))
        conclusions.append(
            {
                "conclusion_id": "conclusion_1",
                "topic": "wealth",
                "claim": f"财富判断由多条核心财富依据共同支持，当前主要依据是：{'、'.join(labels[:3])}。",
                "polarity": "support",
                "confidence": round(max(0.05, min(1.0, avg_support)), 3),
                "evidence_ids": support_ids,
                "generated_by": "engine",
                "composition": "multi_feature_wealth_evidence",
            }
        )
        stability_rows = [row for row in feature_rows if _safe_float(dict(row.get("effect") or {}).get("income_stability"), 0.0) or _safe_str(row.get("feature_type")) in {"wealth_vault", "flow_activation", "stability_risk"}]
        if stability_rows:
            selected = sorted(stability_rows, key=lambda row: abs(_safe_float(dict(row.get("effect") or {}).get("income_stability"), 0.0)) + _safe_float(row.get("risk"), 0.0), reverse=True)[:3]
            selected_ids = [_safe_str(row.get("evidence_id")) for row in selected if _safe_str(row.get("evidence_id"))]
            avg_stability = sum(_safe_float(row.get("stability"), 0.5) for row in selected) / max(1, len(selected))
            conclusions.append(
                {
                    "conclusion_id": "conclusion_2",
                    "topic": "wealth",
                    "claim": "收入稳定性需要结合财库、路径闭合和冲合波动一起看；当前稳定性不是单点规则决定。",
                    "polarity": "support" if avg_stability >= 0.5 else "risk",
                    "confidence": round(max(0.05, min(1.0, avg_stability * 0.72)), 3),
                    "evidence_ids": selected_ids,
                    "generated_by": "engine",
                    "composition": "stability_from_feature_evidence",
                }
            )
        if risk_rows:
            selected = sorted(risk_rows, key=lambda row: _safe_float(row.get("risk"), 0.0), reverse=True)[:3]
            selected_ids = [_safe_str(row.get("evidence_id")) for row in selected if _safe_str(row.get("evidence_id"))]
            max_risk = max([_safe_float(row.get("risk"), 0.0) for row in selected] or [0.0])
            conclusions.append(
                {
                    "conclusion_id": f"conclusion_{len(conclusions) + 1}",
                    "topic": "wealth",
                    "claim": "主要风险来自财富路径的稳定性扰动，尤其要关注合冲刑害、分利竞争或回款承接。",
                    "polarity": "risk",
                    "confidence": round(max(0.05, min(1.0, max_risk * 0.68)), 3),
                    "evidence_ids": selected_ids,
                    "generated_by": "engine",
                    "composition": "risk_from_feature_evidence",
                }
            )
        return conclusions

    def _contract_confidence_from_evidence(self, rule_evidence: List[Dict[str, Any]]) -> float:
        rows = [row for row in rule_evidence if isinstance(row, dict)]
        if not rows:
            return 0.0
        weighted = []
        for row in rows:
            strength = _safe_float(row.get("strength"), _safe_float(row.get("confidence_delta"), 0.0))
            stability = _safe_float(row.get("stability"), 0.55)
            risk = _safe_float(row.get("risk"), 0.0)
            relevance = _safe_float(row.get("wealth_relevance"), 0.7)
            weighted.append(max(0.0, min(1.0, strength * 0.42 + stability * 0.26 + relevance * 0.22 - risk * 0.12)))
        top = sorted(weighted, reverse=True)[:4]
        breadth_bonus = min(0.08, max(0, len(top) - 1) * 0.025)
        weighted_average = sum(top) / max(1, len(top))
        dominant_signal = max(top)
        return round(min(1.0, dominant_signal * 0.68 + weighted_average * 0.32 + breadth_bonus), 3)

    def _uncertainty_from_evidence(self, rule_evidence: List[Dict[str, Any]], conclusions: List[Dict[str, Any]], chart_snapshot: Dict[str, Any]) -> Dict[str, Any]:
        rows = [row for row in rule_evidence if isinstance(row, dict)]
        if not rows or not conclusions:
            return {"score": 1.0, "source": ["no_feature_backed_wealth_evidence"], "missing_assumptions": ["缺少可验证财富特征"], "sensitive_factors": ["补充命盘结构后再判断"]}
        avg_uncertainty = sum(_safe_float(row.get("uncertainty"), 0.25) for row in rows) / max(1, len(rows))
        max_risk = max([_safe_float(row.get("risk"), 0.0) for row in rows] or [0.0])
        low_stability = any(_safe_float(row.get("stability"), 0.7) < 0.46 for row in rows)
        sources = ["evidence_strength_stability"]
        if max_risk >= 0.45:
            sources.append("wealth_risk_pressure")
        if low_stability:
            sources.append("relation_or_timing_volatility")
        if not chart_snapshot.get("birth_time") and not chart_snapshot.get("birth_fields"):
            sources.append("limited_birth_detail")
        score = max(0.05, min(1.0, avg_uncertainty * 0.55 + max_risk * 0.3 + (0.18 if low_stability else 0.0)))
        return {
            "score": round(score, 3),
            "source": sources,
            "missing_assumptions": ["现实收入结构、职业选择和实际现金流仍需用户反馈校准"],
            "sensitive_factors": ["合冲刑害稳定性", "大运流年触发", "合作分利与回款节奏"],
        }

    def _risk_modes_from_evidence(self, rule_evidence: List[Dict[str, Any]]) -> List[str]:
        modes: List[str] = []
        for row in rule_evidence:
            if not isinstance(row, dict):
                continue
            ftype = _safe_str(row.get("feature_type"))
            risk = _safe_float(row.get("risk"), 0.0)
            if ftype == "stability_risk":
                modes.append("relation_volatility")
            if ftype == "stability_risk" or risk >= 0.5:
                modes.append("wealth_stability_risk")
            if ftype == "flow_activation":
                modes.append("timing_activation")
            if ftype == "constraint_structure":
                modes.append("rule_or_platform_constraint")
        return list(dict.fromkeys(modes)) or ["uncertainty"]

    def verify_prediction_contract(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        evidence_rows = [row for row in _ensure_list(contract.get("rule_evidence")) if isinstance(row, dict)]
        conclusions = [row for row in _ensure_list(contract.get("conclusions")) if isinstance(row, dict)]
        evidence_by_id = {
            _safe_str(row.get("evidence_id")): row
            for row in evidence_rows
            if _safe_str(row.get("evidence_id"))
        }
        errors: List[str] = []

        for row in evidence_rows:
            if not _safe_str(row.get("rule_id")) or not _safe_str(row.get("version")) or not _safe_str(row.get("content_hash")):
                errors.append("RULE_EVIDENCE_IDENTITY_MISSING")
                continue
            try:
                rule = self.get_rule(_safe_str(row.get("rule_id")), version=_safe_str(row.get("version")), allow_inactive=True)
                if _safe_str(rule.content_hash) != _safe_str(row.get("content_hash")):
                    errors.append("RULE_EVIDENCE_HASH_MISMATCH")
            except PredictiveServiceError:
                errors.append("RULE_EVIDENCE_RULE_NOT_FOUND")

        for row in conclusions:
            refs = [_safe_str(item) for item in _ensure_list(row.get("evidence_ids")) if _safe_str(item)]
            if not refs:
                errors.append("CONCLUSION_EVIDENCE_REQUIRED")
                continue
            if any(ref not in evidence_by_id for ref in refs):
                errors.append("CONCLUSION_EVIDENCE_NOT_FOUND")
            if _safe_str(row.get("generated_by"), "engine") != "engine":
                errors.append("CONCLUSION_NOT_ENGINE_GENERATED")

        if conclusions and not evidence_rows:
            errors.append("CONCLUSION_WITHOUT_EVIDENCE")

        return {
            "result": "pass" if not errors else "fail",
            "errors": sorted(set(errors)),
            "evidence_count": len(evidence_rows),
            "conclusion_count": len(conclusions),
            "verifier_version": "prediction-contract-v1",
        }

    def build_contract(self, payload: Dict[str, Any], *, resolved_rules: Dict[str, Any]) -> PredictionContract:
        if resolved_rules.get("status") != "resolved":
            raise PredictiveServiceError("RESOLVER_REQUIRED_MISSING", "resolver_snapshot missing or invalid")
        snapshot = resolved_rules.get("resolver_snapshot")
        lifecycle = snapshot.get("resolver_lifecycle") if isinstance(snapshot, dict) else {}
        if not isinstance(lifecycle, dict) or lifecycle.get("gatekeeper_protocol") != RULE_GATEKEEPER_PROTOCOL:
            self._raise_lifecycle_bypass(
                message="contract build requires resolver lifecycle snapshot",
                purpose="contract",
                execution_mode=_safe_str(payload.get("execution_mode"), "contract"),
                actor_role=_safe_str(payload.get("actor_role"), "system"),
                actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
                details={"prediction_id": _safe_str(payload.get("prediction_id"))},
            )
        if "rule_evidence" not in payload:
            payload = dict(payload)
            payload["rule_evidence"] = self._rule_evidence_from_resolver(
                resolved_rules,
                chart_snapshot=dict(payload.get("chart_snapshot") or {}),
            )
        if "conclusions" not in payload:
            payload = dict(payload)
            payload["conclusions"] = self._conclusions_from_evidence(
                topic=_safe_str(payload.get("topic"), "wealth"),
                rule_evidence=_ensure_list(payload.get("rule_evidence")),
            )
        if payload.get("conclusions") and not payload.get("rule_evidence"):
            raise PredictiveServiceError("CONTRACT_VERIFIER_FAILED", "conclusion requires rule_evidence", 422)
        verification = self.verify_prediction_contract(payload)
        if verification.get("result") != "pass":
            raise PredictiveServiceError("CONTRACT_VERIFIER_FAILED", ",".join(_ensure_list(verification.get("errors"))), 422)
        contract = PredictionContract.from_payload(payload)
        if not contract.evidence_ids and contract.conclusions:
            raise PredictiveServiceError("EVIDENCE_BINDING_FAILED", "evidence_ids are required", 422)
        if not contract.resolver_snapshot:
            raise PredictiveServiceError("RESOLVER_REQUIRED_MISSING", "resolver_snapshot is required", 422)
        return contract

    def run_rule_test_v0(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._assert_lifecycle(
            token=_safe_str(payload.get("lifecycle_token", "")),
            purpose="test",
            execution_mode="test",
        )
        role = str(payload.get("actor_role") or "user").strip().lower()
        if role not in {"practitioner", "manager", "admin", "system"}:
            raise PredictiveServiceError("FORBIDDEN", "only practitioner/manager/admin can run rule tests", 403)

        rule_id = str(payload.get("rule_id") or "").strip()
        suite_id = str(payload.get("suite_id") or "").strip()
        suite_version = _safe_str(payload.get("suite_version"))
        test_suite = str(payload.get("test_suite") or suite_id or "default_v0").strip()
        test_cases = payload.get("test_cases") if isinstance(payload.get("test_cases"), list) else []

        suite: Optional[RuleTestSuite] = None
        if suite_id:
            suite = self.get_rule_test_suite(suite_id, version=suite_version or None, allow_inactive=True)
            if suite.test_cases:
                if not test_cases:
                    test_cases = list(suite.test_cases)
            else:
                raise PredictiveServiceError("RULE_TEST_EMPTY", "selected suite has no test cases")
            if not rule_id:
                rule_id = suite.rule_id
            elif rule_id != suite.rule_id:
                raise PredictiveServiceError("RULE_TEST_INPUT_MISMATCH", "rule_id and suite.rule_id mismatch")

        if not rule_id:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "rule_id is required")
        if not test_cases:
            raise PredictiveServiceError("RULE_TEST_EMPTY", "test_cases is required")

        rule_version = _safe_str(payload.get("version") or payload.get("rule_version"))
        if suite and suite.rule_version and rule_version and rule_version != suite.rule_version:
            raise PredictiveServiceError("RULE_TEST_INPUT_MISMATCH", "rule_version and suite.rule_version mismatch")
        if suite and not rule_version:
            rule_version = suite.rule_version
        if suite:
            test_suite = suite.suite_id
        rule = self.get_rule(rule_id, version=rule_version, allow_inactive=True)
        total_cases = len(test_cases)
        hit = 0
        fp = 0
        fn = 0
        tn = 0
        records: List[Dict[str, Any]] = []

        for index, item in enumerate(test_cases):
            raw = item if isinstance(item, dict) else {}
            case = SyntheticCase(
                case_id=str(raw.get("case_id") or f"case_{index}"),
                scenario=str(raw.get("scenario") or "synthetic"),
                expected_active=_safe_bool(raw.get("expected_active"), default=False),
                observed_active=_safe_bool(raw.get("observed_active"), default=False),
                features=raw.get("features") if isinstance(raw.get("features"), dict) else {},
            )
            records.append(case.to_dict())
            if case.expected_active and case.observed_active:
                hit += 1
            elif not case.expected_active and case.observed_active:
                fp += 1
            elif case.expected_active and not case.observed_active:
                fn += 1
            else:
                tn += 1

        eval_result = self._evaluate_rule_test_v01(hit=hit, fp=fp, fn=fn, tn=tn)

        suite_id_for_result = suite.suite_id if suite else ""
        suite_version_for_result = suite.version if suite else ""
        execution_mode = _safe_str(payload.get("execution_mode"), "test")
        test_run_digest = _rule_test_run_payload_fingerprint(
            rule_id=rule_id,
            rule_version=rule.version,
            suite_id=suite_id_for_result,
            suite_version=suite_version_for_result,
            test_suite=test_suite,
            test_cases=records,
        )
        run_id = f"rule_test_{test_run_digest}"

        existing = None
        for item in self._rule_test_results.get(rule_id, []):
            if _safe_str(item.get("run_id")) == run_id:
                existing = dict(item)
                break

        if existing:
            self._append_audit_event(
                rule_id=rule_id,
                event_type="RULE_TEST_EXECUTED",
                severity="info",
                message="rule test run deduplicated by idempotent run_id",
                actor_role=role,
                actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
                details={
                    "run_id": run_id,
                    "rule_version": rule.version,
                    "suite_id": suite_id_for_result,
                    "suite_version": suite_version_for_result,
                    "deduplicated": True,
                },
            )
            existing["actor_context"] = {
                "actor_role": role,
                "actor_user_id": _safe_int(payload.get("actor_user_id"), 0),
            }
            return existing

        result = RuleTestResult(
            rule_id=rule_id,
            rule_version=rule.version,
            test_suite=test_suite,
            total_cases=eval_result["total_cases"],
            hit_rate=eval_result["hit_rate"],
            false_positive_rate=eval_result["false_positive_rate"],
            false_negative_rate=eval_result["false_negative_rate"],
            conflict_rate=eval_result["conflict_rate"],
            recommended_status=eval_result["recommended_status"],
            suite_id=suite_id_for_result,
            suite_version=suite_version_for_result,
            run_id=run_id,
            test_suite_run_id=run_id,
        )

        payload_out = {
            **result.to_dict(),
            "cases": records,
            "rule_test_engine": RULE_TEST_ENGINE_VERSION,
            "quality_gate": eval_result["quality_gate"],
            "quality_score": eval_result["quality_score"],
            "execution_mode": execution_mode,
            "summary": {
                "hit": hit,
                "false_positive": fp,
                "false_negative": fn,
                "true_negative": tn,
                "precision": eval_result["precision"],
                "recall": eval_result["recall"],
                "rationale": eval_result["rationale"],
            },
        }
        self._rule_test_results.setdefault(rule_id, []).append(payload_out)
        self._persist()
        payload_out["actor_context"] = {
            "actor_role": role,
            "actor_user_id": _safe_int(payload.get("actor_user_id")),
        }
        self._append_audit_event(
            rule_id=rule_id,
            event_type="RULE_TEST_EXECUTED",
            severity="info",
            message="rule test executed",
            actor_role=role,
            actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
            details={
                "run_id": run_id,
                "rule_version": rule.version,
                "suite_id": suite_id_for_result,
                "suite_version": suite_version_for_result,
                "test_suite": test_suite,
                "total_cases": total_cases,
                "rule_test_engine": RULE_TEST_ENGINE_VERSION,
                "execution_mode": execution_mode,
                "recommended_status": eval_result["recommended_status"],
                "quality_gate": eval_result["quality_gate"],
                "quality_score": eval_result["quality_score"],
                "precision": eval_result["precision"],
                "recall": eval_result["recall"],
            },
        )
        return payload_out

    def list_rule_test_results(
        self,
        rule_id: str | None = None,
        suite_id: str | None = None,
        run_id: str | None = None,
        offset: int = 0,
        limit: int = 50,
        quality_gate: str | None = None,
        min_quality_score: float | None = None,
        max_quality_score: float | None = None,
        sort: str = "desc",
    ) -> List[Dict[str, Any]]:
        return self.query_rule_test_results(
            rule_id=rule_id,
            suite_id=suite_id,
            run_id=run_id,
            quality_gate=quality_gate,
            min_quality_score=min_quality_score,
            max_quality_score=max_quality_score,
            offset=offset,
            limit=limit,
            sort=sort,
        )["items"]

    def query_rule_test_results(
        self,
        rule_id: str | None = None,
        suite_id: str | None = None,
        run_id: str | None = None,
        offset: int = 0,
        limit: int = 50,
        quality_gate: str | None = None,
        min_quality_score: float | None = None,
        max_quality_score: float | None = None,
        sort: str = "desc",
    ) -> Dict[str, Any]:
        out: List[Dict[str, Any]] = []

        if run_id:
            target_run_id = _safe_str(run_id)
            if rule_id:
                out = [
                    item
                    for item in self._rule_test_results.get(str(rule_id), [])
                    if _safe_str(item.get("run_id")) == target_run_id
                ]
            else:
                for v in self._rule_test_results.values():
                    out.extend(v)
                out = [item for item in out if _safe_str(item.get("run_id")) == target_run_id]

        elif rule_id:
            out = list(self._rule_test_results.get(str(rule_id), []))
        else:
            for v in self._rule_test_results.values():
                out.extend(v)

        if suite_id:
            out = [item for item in out if _safe_str(item.get("suite_id")) == _safe_str(suite_id)]
        if quality_gate:
            target_gate = _safe_str(quality_gate).lower()
            out = [item for item in out if _safe_str(item.get("quality_gate")) == target_gate]

        min_q = _safe_float(min_quality_score, -1.0)
        max_q = _safe_float(max_quality_score, 2.0)
        if min_q > -1.0:
            out = [item for item in out if _safe_float(item.get("quality_score"), 0.0) >= min_q]
        if max_q < 2.0:
            out = [item for item in out if _safe_float(item.get("quality_score"), 0.0) <= max_q]

        normalized_sort = _safe_str(sort, "desc").lower()
        reverse = normalized_sort != "asc"
        out = sorted(
            out,
            key=lambda item: _parse_dt(item.get("created_at")) or datetime.min,
            reverse=reverse,
        )
        start = max(0, _safe_int(offset, 0))
        size = _safe_int(limit, 50)
        if size <= 0:
            size = 50
        total_matched = len(out)
        items = out[start : start + size]
        return {
            "items": items,
            "total_matched": total_matched,
            "total_returned": len(items),
            "offset": start,
            "limit": size,
        }

    def get_rule_test_dashboard(
        self,
        rule_id: str | None = None,
        suite_id: str | None = None,
        quality_gate: str | None = None,
        execution_mode: str | None = None,
        min_quality_score: float | None = None,
        max_quality_score: float | None = None,
        start_at: str | None = None,
        end_at: str | None = None,
        granularity: str = "day",
        trend_points: int = 30,
        latest_runs_limit: int = 10,
    ) -> Dict[str, Any]:
        normalized_rule_id = _safe_str(rule_id)
        normalized_suite_id = _safe_str(suite_id)
        normalized_gate = _safe_str(quality_gate).lower()
        if normalized_gate:
            target_gate = normalized_gate
        else:
            target_gate = ""
        normalized_mode = _safe_str(execution_mode).lower()
        if normalized_mode:
            target_mode = normalized_mode
        else:
            target_mode = ""

        bucket_mode = _safe_str(granularity, "day").lower()
        if bucket_mode not in {"day", "week", "month"}:
            bucket_mode = "day"

        requested_points = _safe_int(trend_points, 30)
        if requested_points <= 0:
            requested_points = 30

        start_dt = _parse_dt(start_at)
        end_dt = _parse_dt(end_at)

        results = self.query_rule_test_results(
            rule_id=normalized_rule_id or None,
            suite_id=normalized_suite_id or None,
            quality_gate=target_gate or None,
            min_quality_score=min_quality_score,
            max_quality_score=max_quality_score,
            sort="asc",
            offset=0,
            limit=20000,
        )["items"]

        filtered: List[Dict[str, Any]] = []
        for item in results:
            item_dt = _parse_dt(item.get("created_at"))
            if start_dt and item_dt and item_dt < start_dt:
                continue
            if end_dt and item_dt and item_dt > end_dt:
                continue
            if target_mode and _safe_str(item.get("execution_mode")).lower() != target_mode:
                continue
            filtered.append(item)

        total_runs = len(filtered)
        if not filtered:
            return {
                "window": {
                    "rule_id": normalized_rule_id or "all",
                    "suite_id": normalized_suite_id or "all",
                    "quality_gate": target_gate or "all",
                    "start_at": start_at,
                    "end_at": end_at,
                    "granularity": bucket_mode,
                    "trend_points": requested_points,
                },
                "summary": {
                    "total_runs": 0,
                    "unique_rules": 0,
                    "trend_total_runs": 0,
                    "trend_empty_buckets": 0,
                    "avg_quality_score": 0.0,
                    "avg_precision": 0.0,
                    "avg_recall": 0.0,
                    "avg_conflict_rate": 0.0,
                    "total_cases": 0,
                    "gate_distribution": {},
                    "execution_mode_distribution": {},
                },
                "trend_meta": {
                    "granularity": bucket_mode,
                    "total_buckets": 0,
                    "empty_buckets": 0,
                    "trend_total_runs": 0,
                    "requested_points": requested_points,
                },
                "trend": [],
                "by_rule": [],
                "latest_runs": [],
            }

        gate_distribution: Dict[str, int] = {}
        mode_distribution: Dict[str, int] = {}
        rule_rollup: Dict[tuple[str, str], Dict[str, Any]] = {}
        trend_map: Dict[str, Dict[str, Any]] = {}
        total_quality_score = 0.0
        total_precision = 0.0
        total_recall = 0.0
        total_conflict = 0.0
        total_cases = 0

        for item in filtered:
            gate = _safe_str(item.get("quality_gate"), "unknown").lower()
            gate_distribution[gate] = gate_distribution.get(gate, 0) + 1
            mode = _safe_str(item.get("execution_mode"), "test").lower()
            mode_distribution[mode] = mode_distribution.get(mode, 0) + 1
            quality = _safe_float(item.get("quality_score"), 0.0)
            precision = _safe_float(item.get("summary", {}).get("precision"), _safe_float(item.get("precision"), 0.0))
            recall = _safe_float(item.get("summary", {}).get("recall"), _safe_float(item.get("recall"), 0.0))
            conflict = _safe_float(item.get("conflict_rate"), 0.0)
            cases = _safe_int(item.get("total_cases"), 0)
            total_quality_score += quality
            total_precision += precision
            total_recall += recall
            total_conflict += conflict
            total_cases += cases

            rid = _safe_str(item.get("rule_id"))
            rver = _safe_str(item.get("rule_version"))
            key = (rid, rver)
            entry = rule_rollup.get(key)
            if entry is None:
                entry = {
                    "rule_id": rid,
                    "rule_version": rver,
                    "suite_id": _safe_str(item.get("suite_id")),
                    "suite_version": _safe_str(item.get("suite_version")),
                    "runs": 0,
                    "execution_mode_distribution": {},
                    "total_quality_score": 0.0,
                    "total_precision": 0.0,
                    "total_recall": 0.0,
                    "total_conflict": 0.0,
                    "total_cases": 0,
                    "last_quality_gate": gate,
                    "latest_run_at": _safe_str(item.get("created_at")),
                    "latest_run_id": _safe_str(item.get("run_id")),
                    "last_execution_mode": mode,
                }
                rule_rollup[key] = entry
            entry["runs"] += 1
            entry["total_quality_score"] += quality
            entry["total_precision"] += precision
            entry["total_recall"] += recall
            entry["total_conflict"] += conflict
            entry["total_cases"] += cases
            entry["execution_mode_distribution"][mode] = entry["execution_mode_distribution"].get(mode, 0) + 1

            item_dt = _parse_dt(item.get("created_at"))
            if item_dt:
                if bucket_mode == "day":
                    bucket = item_dt.strftime("%Y-%m-%d")
                elif bucket_mode == "week":
                    bucket = item_dt.strftime("%G-%V")
                else:
                    bucket = item_dt.strftime("%Y-%m")
                trend = trend_map.setdefault(
                    bucket,
                    {
                        "bucket": bucket,
                        "runs": 0,
                        "is_empty": False,
                        "avg_quality_score": 0.0,
                        "avg_conflict_rate": 0.0,
                        "pass_rate": 0.0,
                        "review_rate": 0.0,
                        "needs_review_rate": 0.0,
                        "other_gate_rate": 0.0,
                        "gate_distribution": {},
                        "mode_distribution": {},
                    },
                )
                trend["runs"] += 1
                trend["avg_quality_score"] = (trend["avg_quality_score"] * (trend["runs"] - 1) + quality) / trend["runs"]
                trend["avg_conflict_rate"] = (trend["avg_conflict_rate"] * (trend["runs"] - 1) + conflict) / trend["runs"]
                trend["gate_distribution"][gate] = trend["gate_distribution"].get(gate, 0) + 1
                trend["mode_distribution"][mode] = trend["mode_distribution"].get(mode, 0) + 1

                trend_runs = trend["runs"]
                if trend_runs > 0:
                    trend["pass_rate"] = trend["gate_distribution"].get("pass", 0) / trend_runs
                    trend["review_rate"] = trend["gate_distribution"].get("review", 0) / trend_runs
                    trend["needs_review_rate"] = trend["gate_distribution"].get("needs_review", 0) / trend_runs
                    known_rates = (
                        trend["gate_distribution"].get("pass", 0)
                        + trend["gate_distribution"].get("review", 0)
                        + trend["gate_distribution"].get("needs_review", 0)
                    )
                    trend["other_gate_rate"] = max(0.0, (trend_runs - known_rates) / trend_runs)

            latest_dt = _parse_dt(entry["latest_run_at"]) or datetime.min.replace(tzinfo=timezone.utc)
            if not item_dt or item_dt <= latest_dt:
                continue
            entry["latest_run_at"] = _safe_str(item.get("created_at"))
            entry["latest_run_id"] = _safe_str(item.get("run_id"))
            entry["last_quality_gate"] = gate
            entry["last_execution_mode"] = mode

        trend_items = list(trend_map.values())
        trend_items.sort(key=lambda item: item["bucket"])
        if trend_items:
            def _parse_bucket_start(bucket: str) -> Optional[datetime]:
                if bucket_mode == "day":
                    return datetime.strptime(bucket, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if bucket_mode == "week":
                    try:
                        return datetime.strptime(f"{bucket}-1", "%G-%V-%u").replace(tzinfo=timezone.utc)
                    except ValueError:
                        return None
                if bucket_mode == "month":
                    return datetime.strptime(f"{bucket}-01", "%Y-%m-%d").replace(tzinfo=timezone.utc)
                return None

            def _add_bucket(start_dt: datetime, offset: int) -> str:
                if bucket_mode == "day":
                    dt = start_dt + timedelta(days=offset)
                    return dt.strftime("%Y-%m-%d")
                if bucket_mode == "week":
                    dt = start_dt + timedelta(weeks=offset)
                    return dt.strftime("%G-%V")
                dt = start_dt
                month_index = dt.year * 12 + dt.month - 1 + offset
                year = month_index // 12
                month = month_index % 12 + 1
                return f"{year:04d}-{month:02d}"

            min_boundary = trend_items[0]["bucket"]
            max_boundary = trend_items[-1]["bucket"]
            start_boundary = _parse_bucket_start(min_boundary)
            end_boundary = _parse_bucket_start(max_boundary)
            if start_boundary is None:
                start_boundary = _parse_dt(start_at)
            if end_boundary is None:
                end_boundary = _parse_dt(end_at)
            if start_boundary is None:
                start_boundary = _parse_dt(filtered[0].get("created_at"))
            if end_boundary is None and filtered:
                end_boundary = _parse_dt(filtered[-1].get("created_at"))

            if start_boundary and end_boundary:
                if end_boundary < start_boundary:
                    start_boundary, end_boundary = end_boundary, start_boundary
                existing = {item["bucket"]: item for item in trend_items}
                if bucket_mode == "day":
                    total_steps = (end_boundary.date() - start_boundary.date()).days + 1
                elif bucket_mode == "week":
                    total_steps = int((end_boundary - start_boundary).days / 7) + 1
                else:
                    total_steps = (end_boundary.year - start_boundary.year) * 12 + (end_boundary.month - start_boundary.month) + 1
                total_steps = max(1, total_steps)
                if total_steps <= 0:
                    total_steps = 1

                start_offset = 0
                if total_steps > requested_points:
                    start_offset = total_steps - requested_points

                trend_items = []
                for i in range(start_offset, total_steps):
                    bucket_key = _add_bucket(start_boundary, i)
                    trend_items.append(
                        existing.get(
                            bucket_key,
                            {
                                "bucket": bucket_key,
                                "runs": 0,
                                "is_empty": True,
                                "avg_quality_score": 0.0,
                                "avg_conflict_rate": 0.0,
                                "pass_rate": 0.0,
                                "review_rate": 0.0,
                                "needs_review_rate": 0.0,
                                "other_gate_rate": 0.0,
                                "gate_distribution": {},
                                "mode_distribution": {},
                            },
                        )
                    )
        trend_items.sort(key=lambda item: item["bucket"])
        if trend_items and len(trend_items) > requested_points:
            trend_items = trend_items[-requested_points:]

        for item in trend_items:
            if _safe_int(item.get("runs"), 0) <= 0:
                item["is_empty"] = True
            else:
                item["is_empty"] = _safe_bool(item.get("is_empty"), default=False)

        empty_trend_buckets = sum(1 for item in trend_items if _safe_int(item.get("runs"), 0) <= 0)

        by_rule = []
        for entry in rule_rollup.values():
            runs = _safe_int(entry.get("runs"), 0)
            by_rule.append(
                {
                    "rule_id": entry["rule_id"],
                    "rule_version": entry["rule_version"],
                    "suite_id": _safe_str(entry.get("suite_id")),
                    "suite_version": _safe_str(entry.get("suite_version")),
                    "runs": runs,
                    "total_cases": _safe_int(entry.get("total_cases"), 0),
                    "avg_quality_score": _safe_float(entry.get("total_quality_score"), 0.0) / runs if runs else 0.0,
                    "avg_precision": _safe_float(entry.get("total_precision"), 0.0) / runs if runs else 0.0,
                    "avg_recall": _safe_float(entry.get("total_recall"), 0.0) / runs if runs else 0.0,
                    "avg_conflict_rate": _safe_float(entry.get("total_conflict"), 0.0) / runs if runs else 0.0,
                    "latest_run_at": entry["latest_run_at"],
                    "latest_run_id": entry["latest_run_id"],
                    "last_quality_gate": entry["last_quality_gate"],
                    "last_execution_mode": entry["last_execution_mode"],
                    "execution_mode_distribution": entry.get("execution_mode_distribution") or {},
                }
            )
        by_rule.sort(key=lambda item: item["runs"], reverse=True)

        latest_runs = sorted(
            filtered,
            key=lambda item: _parse_dt(item.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        latest_runs_limit = max(1, min(_safe_int(latest_runs_limit, 10), 50))
        latest_runs = latest_runs[:latest_runs_limit]

        latest_runs_summary = []
        for item in latest_runs:
            latest_runs_summary.append(
                {
                    "run_id": _safe_str(item.get("run_id")),
                    "rule_id": _safe_str(item.get("rule_id")),
                    "rule_version": _safe_str(item.get("rule_version")),
                    "suite_id": _safe_str(item.get("suite_id")),
                    "suite_version": _safe_str(item.get("suite_version")),
                    "quality_gate": _safe_str(item.get("quality_gate")),
                    "quality_score": _safe_float(item.get("quality_score"), 0.0),
                    "recommended_status": _safe_str(item.get("recommended_status")),
                    "total_cases": _safe_int(item.get("total_cases"), 0),
                    "created_at": _safe_str(item.get("created_at")),
                    "test_suite": _safe_str(item.get("test_suite")),
                    "execution_mode": _safe_str(item.get("execution_mode"), "test"),
                }
            )

        return {
            "window": {
                "rule_id": normalized_rule_id or "all",
                "suite_id": normalized_suite_id or "all",
                "quality_gate": target_gate or "all",
                "start_at": start_at,
                "end_at": end_at,
                "granularity": bucket_mode,
                "trend_points": requested_points,
                "execution_mode": target_mode or "all",
            },
            "summary": {
                "total_runs": total_runs,
                "unique_rules": len(rule_rollup),
                "trend_total_runs": total_runs,
                "trend_empty_buckets": empty_trend_buckets,
                "avg_quality_score": total_quality_score / total_runs if total_runs else 0.0,
                "avg_precision": total_precision / total_runs if total_runs else 0.0,
                "avg_recall": total_recall / total_runs if total_runs else 0.0,
                "avg_conflict_rate": total_conflict / total_runs if total_runs else 0.0,
                "total_cases": total_cases,
                "gate_distribution": gate_distribution,
                "execution_mode_distribution": mode_distribution,
            },
            "trend_meta": {
                "granularity": bucket_mode,
                "total_buckets": len(trend_items),
                "empty_buckets": empty_trend_buckets,
                "trend_total_runs": total_runs,
                "requested_points": requested_points,
            },
            "trend": trend_items,
            "by_rule": by_rule,
            "latest_runs": latest_runs_summary,
        }

    def get_rule_test_engine_config(self, *, version: str | None = None) -> Dict[str, Any]:
        target_version = _safe_str(version or RULE_TEST_ENGINE_VERSION)
        if target_version != RULE_TEST_ENGINE_VERSION:
            raise PredictiveServiceError("RULE_TEST_ENGINE_NOT_FOUND", f"unsupported rule test engine version: {target_version}", 404)
        return {
            "engine": {
                "version": RULE_TEST_ENGINE_VERSION,
                "name": "Rule Test Engine",
                "status": "active",
                "thresholds": dict(RULE_TEST_ENGINE_THRESHOLD_V01),
            },
            "supported_versions": [RULE_TEST_ENGINE_VERSION],
        }

    def list_rule_audit_events(
        self,
        *,
        rule_id: str | None = None,
        event_type: str | None = None,
        actor_role: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        offset: int = 0,
        limit: int = 200,
        sort: str = "desc",
    ) -> List[Dict[str, Any]]:
        return self.query_rule_audit_events(
            rule_id=rule_id,
            event_type=event_type,
            actor_role=actor_role,
            created_after=created_after,
            created_before=created_before,
            offset=offset,
            limit=limit,
            sort=sort,
        )["items"]

    def query_rule_audit_events(
        self,
        *,
        rule_id: str | None = None,
        event_type: str | None = None,
        actor_role: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        offset: int = 0,
        limit: int = 200,
        sort: str = "desc",
    ) -> Dict[str, Any]:
        out = [event.to_dict() for event in self._rule_audit_events]
        after_dt = _parse_dt(created_after)
        before_dt = _parse_dt(created_before)
        rid = _safe_str(rule_id)
        if rid:
            out = [item for item in out if _safe_str(item.get("rule_id")) == rid]
        if event_type:
            out = [item for item in out if _safe_str(item.get("event_type")) == _safe_str(event_type)]
        if actor_role:
            out = [item for item in out if _safe_str(item.get("actor_role")) == _safe_str(actor_role).lower()]
        if after_dt:
            out = [
                item
                for item in out
                if _parse_dt(item.get("created_at")) is not None and _parse_dt(item.get("created_at")) >= after_dt
            ]
        if before_dt:
            out = [
                item
                for item in out
                if _parse_dt(item.get("created_at")) is not None and _parse_dt(item.get("created_at")) <= before_dt
            ]
        out = sorted(
            out,
            key=lambda item: _parse_dt(item.get("created_at")) or datetime.min,
            reverse=_safe_str(sort, "desc").lower() != "asc",
        )
        start = max(0, _safe_int(offset, 0))
        size = _safe_int(limit, 200)
        if size <= 0:
            size = 200
        total_matched = len(out)
        items = out[start : start + size]
        return {
            "items": items,
            "total_matched": total_matched,
            "total_returned": len(items),
            "offset": start,
            "limit": size,
        }

    def build_consumer_agent_bootstrap(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        birth_payload = payload.get("birth_payload") if isinstance(payload.get("birth_payload"), dict) else {}
        topics = _ensure_list(payload.get("topics")) or ["wealth", "career", "relationship", "health"]
        user_question_count = _safe_int(payload.get("auto_question_count"), 5)
        cards: List[Dict[str, Any]] = []

        topic_templates = {
            "wealth": {
                "title": "财富",
                "blocks": [
                    {"key": "wealth_sources", "label": "财富来源"},
                    {"key": "earnings_mode", "label": "赚钱方式"},
                    {"key": "cashflow_risk", "label": "现金流风险"},
                    {"key": "timing_window", "label": "适合年份"},
                    {"key": "action_plan", "label": "行动建议"},
                    {"key": "feedback", "label": "反馈入口"},
                ],
                "auto_questions": [
                    "未来一年财富机会在哪里？",
                    "今年更适合打工、创业还是项目制？",
                    "合作/合同类风险更可能发生在哪个环节？",
                    "现金流是否容易滞后？",
                    "哪几个月/季度最需要控险？",
                ],
            },
            "career": {
                "title": "事业",
                "blocks": [
                    {"key": "work_style", "label": "职业风格"},
                    {"key": "best_channels", "label": "适合平台"},
                    {"key": "promotion_window", "label": "升迁窗口"},
                    {"key": "conflict_risk", "label": "冲突风险"},
                    {"key": "pivot_signal", "label": "转型时机"},
                    {"key": "feedback", "label": "反馈入口"},
                ],
                "auto_questions": [
                    "接下来 12 个月更适合做岗位内深耕还是跨界转型？",
                    "你是否会遇到流程、制度或上级摩擦？",
                    "哪类能力能最快形成差异化？",
                    "哪类工作方式更容易持续出结果？",
                    "下一次更换赛道的窗口是否靠谱？",
                ],
            },
            "relationship": {
                "title": "感情",
                "blocks": [
                    {"key": "relationship_pattern", "label": "关系模式"},
                    {"key": "stability_risk", "label": "稳定性风险"},
                    {"key": "compatibility", "label": "伴侣匹配"},
                    {"key": "communication", "label": "沟通建议"},
                    {"key": "timing_window", "label": "关系窗口"},
                    {"key": "feedback", "label": "反馈入口"},
                ],
                "auto_questions": [
                    "关系里什么会先发难：沟通、边界还是承诺？",
                    "近期是否会遇到价值观冲突？",
                    "哪些行为容易造成误会放大？",
                    "先稳关系还是先抓机会？",
                    "是否适合在这段关系里提高投入？",
                ],
            },
            "health": {
                "title": "健康",
                "blocks": [
                    {"key": "energy_state", "label": "能量状态"},
                    {"key": "stress_signal", "label": "压力信号"},
                    {"key": "discipline", "label": "作息纪律"},
                    {"key": "risk_warning", "label": "风险预警"},
                    {"key": "improvement", "label": "行动建议"},
                    {"key": "feedback", "label": "反馈入口"},
                ],
                "auto_questions": [
                    "你近期更容易透支到哪种系统？",
                    "是什么时候开始明显掉线？",
                    "压力上来时你最先失控在哪个环节？",
                    "本季度最值得先修正的是作息还是社交？",
                    "是否需要先降负荷再做攻势？",
                ],
            },
        }

        seen = set()
        for topic in topics:
            norm_topic = _normalize_topic(topic)
            if norm_topic in seen:
                continue
            seen.add(norm_topic)
            template = topic_templates.get(norm_topic)
            if not template:
                continue
            cards.append(
                {
                    "topic": norm_topic,
                    "title": template["title"],
                    "blocks": template["blocks"],
                    "agent_questions": template["auto_questions"],
                    "plain_terms": _to_plain_terms("", topic=norm_topic),
                }
            )

        if not cards:
            cards.append(
                {
                    "topic": "wealth",
                    "title": "财富",
                    "blocks": topic_templates["wealth"]["blocks"],
                    "agent_questions": topic_templates["wealth"]["auto_questions"],
                    "plain_terms": _to_plain_terms("", topic="wealth"),
                }
            )

        discovery_questions = [
            "你最需要解决的是‘现金流、职业、关系’中的哪一个？",
            "你更关心3个月、6个月还是12个月结果？",
            "你有关键时点（跳槽、签约、融资）吗？",
            "目前最担心的是‘努力很多但结果慢’还是‘结果有但兑现慢’？",
        ]
        if cards:
            discovery_questions = [q for q in cards[0]["agent_questions"][:user_question_count]] + discovery_questions[: max(0, user_question_count - 3)]

        return {
            "session_id": str(payload.get("session_id") or f"agent_{int(datetime.now(timezone.utc).timestamp())}"),
            "source_hint": {
                "gender": str(birth_payload.get("gender") or "").strip() or "unknown",
                "calendar_type": str(birth_payload.get("calendar_type") or "").strip() or "unknown",
            },
            "agent_mode": "bootstrap",
            "discovery_questions": discovery_questions[:user_question_count],
            "topic_cards": cards,
            "next_step": "请在下条消息里选一个主题并给出关键场景",
            "actor_context": {
                "actor_role": str(payload.get("actor_role") or "user").strip().lower(),
                "actor_user_id": _safe_int(payload.get("actor_user_id")),
            },
        }

    def decompose_user_question(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        question = str(payload.get("question") or "").strip()
        if not question:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "question is required")
        raw_topic = _normalize_topic(payload.get("topic") or payload.get("topic_hint"))
        topic = raw_topic
        q = question.lower()
        if topic == "wealth" or any(word in q for word in ["财", "钱", "收入", "现金", "合作", "合同", "项目", "投资", "创业", "变现", "挣钱"]):
            topic = "wealth"
            followups = [
                {"code": "salary", "label": "工资收入", "hint": "优先问：固定薪酬占比、涨薪弹性、岗位稳定性"},
                {"code": "project", "label": "项目收入", "hint": "优先问：交付节奏、付款条件、回款比例"},
                {"code": "investment", "label": "投资收益", "hint": "优先问：波动阈值、止盈止损、现金替代成本"},
                {"code": "startup", "label": "创业现金流", "hint": "优先问：毛利率、客户转化、坏账率"},
                {"code": "partner", "label": "伴侣/合作带来财富", "hint": "优先问：分账边界、合同约束、交付与回撤机制"},
            ]
            translated = [
                "靠能力把复杂问题变成可计费成果",
                "合作关系会影响收款节奏",
                "先把现金流承接机制做稳再谈放量",
            ]
        elif topic == "career" or any(word in q for word in ["事业", "工作", "升职", "副业", "平台", "职业", "转型", "加薪", "跳槽"]):
            topic = "career"
            followups = [
                {"code": "job", "label": "打工发展", "hint": "先问：岗位边界、绩效节奏、上级关系"},
                {"code": "project", "label": "项目制", "hint": "先问：交付周期、合同约束、验收机制"},
                {"code": "platform", "label": "平台型合作", "hint": "先问：分账规则、平台政策、争议条款"},
                {"code": "promotion", "label": "升迁窗口", "hint": "先问：关键评估周期与展示里程碑"},
                {"code": "transition", "label": "职业转型", "hint": "先问：迁移成本、替代能力、失业窗口"},
            ]
            translated = [
                "先选一个能快速产生成果的职业动作",
                "提前对接制度边界与评估周期",
                "提升执行可见度而不是只追求“做了才算”",
            ]
        elif topic == "relationship" or any(word in q for word in ["感情", "恋爱", "伴侣", "婚姻", "关系", "家庭", "沟通"]):
            topic = "relationship"
            followups = [
                {"code": "stability", "label": "关系稳定性", "hint": "先问：边界定义、时间一致性"},
                {"code": "conflict", "label": "冲突点", "hint": "先问：争执常发在哪个场景"},
                {"code": "pace", "label": "节奏匹配", "hint": "先问：承诺落地速度和信号同步"},
                {"code": "compatibility", "label": "价值观匹配", "hint": "先问：对钱、时间、承诺的共识"},
                {"code": "partner", "label": "伴侣角色", "hint": "先问：合作边界和责任分工"},
            ]
            translated = [
                "关系中先处理沟通边界与承诺执行",
                "把关键风险提前量化，而不是靠猜测",
                "先做“可观察行动”，再谈长期承诺",
            ]
        elif topic == "health" or any(word in q for word in ["健康", "亚健康", "体力", "睡眠", "压力", "情绪", "焦虑"]):
            topic = "health"
            followups = [
                {"code": "fatigue", "label": "疲劳", "hint": "先问：连续疲劳窗口与工作负荷"},
                {"code": "stress", "label": "压力来源", "hint": "先问：压力来源与爆发阈值"},
                {"code": "rhythm", "label": "作息", "hint": "先问：可坚持最短循环节奏"},
                {"code": "focus", "label": "专注力", "hint": "先问：干扰源与恢复方式"},
                {"code": "rebuild", "label": "恢复与重建", "hint": "先问：可执行的恢复动作"},
            ]
            translated = [
                "先稳定睡眠与作息，再谈强度",
                "先观察压力触发点再做大幅计划调整",
                "把‘有体力但无输出’视为提前信号",
            ]
        else:
            followups = [
                {"code": "wealth", "label": "财富", "hint": "按现金流与可执行收益展开"},
                {"code": "career", "label": "事业", "hint": "按目标与行动窗口展开"},
                {"code": "relationship", "label": "感情", "hint": "按边界与沟通机制展开"},
                {"code": "health", "label": "健康", "hint": "先从可见症状与压力触发展开"},
            ]
            translated = []

        return {
            "detected_topic": topic,
            "original_question": question,
            "requires_followup": True if len(followups) > 0 else False,
            "followup_questions": followups,
            "plain_translation": translated,
            "next_action": "user_select_focus",
            "actor_context": {
                "actor_role": str(payload.get("actor_role") or "user").strip().lower(),
                "actor_user_id": _safe_int(payload.get("actor_user_id")),
            },
        }

    def build_agent_action_plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = _normalize_topic(payload.get("topic") or payload.get("detected_topic"))
        focus = str(payload.get("focus") or "").strip()
        period = str(payload.get("period") or "3个月")
        should_materialize = _safe_bool(payload.get("materialize"), False)
        prediction_id = str(payload.get("prediction_id") or "").strip()
        now = datetime.now(timezone.utc)

        horizon_days = 90
        if period in {"1个月", "1month", "30d", "30天"}:
            horizon_days = 30
        elif period in {"6个月", "6month", "180天"}:
            horizon_days = 180
        elif "12" in period or "一年" in period or period in {"1year", "12month"}:
            horizon_days = 365

        if topic == "wealth":
            do_items = [
                "先把收入链路拆成‘可计费产出—回款节点—现金回补’",
                "合同、分账、报价改成“能核算”的条款",
                "本月只做能形成现金回款的 2-3 个动作",
            ]
            avoid = [
                "先扩大规模再补回款机制",
                "把“对方会付钱”当作确定收益",
                "同时试太多模型导致现金压力更高",
            ]
            observe = [
                "每周回看项目到款率",
                "每月复核客户流失与成本漂移",
                "观察现金流是否明显滞后于订单增长",
            ]
        elif topic == "career":
            do_items = [
                "优先锁住可交付成果可见度",
                "先定下一段周期性的关键里程碑",
                "处理与上级/流程关系边界",
            ]
            avoid = [
                "同时开启三条高杠杆转型",
                "用‘全力冲刺’替代阶段目标",
                "忽略反馈周期与证据积累",
            ]
            observe = [
                "每两周复核目标产出与评价标准",
                "观察是否出现重复的制度摩擦",
                "追踪你是否在关键窗口被动",
            ]
        elif topic == "relationship":
            do_items = [
                "先把承诺写成可执行动作清单",
                "约定回应窗口与决策截止时间",
                "每次出现矛盾后做事实复盘",
            ]
            avoid = [
                "先猜对方意图再做大决策",
                "一次性抛出太多要求",
                "把沉默当作对方否定或确认",
            ]
            observe = [
                "一周内记录一次沟通后恢复状态",
                "观察承诺兑现率与时间差",
                "标记情绪放大周期并暂停高敏内容",
            ]
        else:
            do_items = [
                "先做小步恢复与可持续作息",
                "把“可承诺任务”压缩为可执行清单",
                "设定 1 周观察周期再下下一步",
            ]
            avoid = [
                "长期透支睡眠与注意力",
                "把所有问题一次性承接",
                "把感受当结论不做行为验证",
            ]
            observe = [
                "观察每 3 天是否能按时完成恢复动作",
                "记录触发疲惫的时间窗",
                "观察压力点是否下降",
            ]

        response: Dict[str, Any] = {
            "topic": topic,
            "focus": focus,
            "period": period,
            "do_now": do_items,
            "avoid_now": avoid,
            "what_to_observe": observe,
            "feedback_gate": {
                "outcome_collect_horizon": "30days",
                "expected_signals": [
                    "收入/任务/关系稳定度或疲劳恢复率出现显著变化",
                    "与上一轮相比可执行动作完成率上升",
                ],
                "feedback_prompt": "请在下次回访记录是否命中（hit/partial/miss/reverse/unverifiable）",
            },
            "actor_context": {
                "actor_role": str(payload.get("actor_role") or "user").strip().lower(),
                "actor_user_id": _safe_int(payload.get("actor_user_id")),
            },
            "feedback_event_template": {
                "prediction_id": str(payload.get("prediction_id") or ""),
                "feedback_type": "consumer_agent",
                "outcome": "collecting",
                "notes": f"topic={topic}, focus={focus}, period={period}, from_agent_action_plan",
            },
        }

        if not should_materialize:
            return response

        if not prediction_id:
            prediction_id = f"agent_pred_{_safe_int(now.timestamp())}_{topic}"

        verifiable_indicators = {
            "outcome": ["monthly_revenue", "net_cashflow", "contract_value"],
            "process": ["lead_conversion_rate", "customer_acquisition", "pricing_power"],
            "risk": ["cashflow_gap", "cost_spike", "client_loss", "policy_change"],
            "mechanism": ["output_energy", "conversion_efficiency", "wealth_retention"],
        }
        if topic == "career":
            verifiable_indicators = {
                "outcome": ["promotion_count", "project_completion", "salary_delta"],
                "process": ["work_visibility", "milestone_delivery", "manager_feedback"],
                "risk": ["conflict_cost", "policy_shift", "team_friction"],
                "mechanism": ["execution_rhythm", "authority_alignment", "effort_to_value"],
            }
        elif topic == "relationship":
            verifiable_indicators = {
                "outcome": ["conflict_resolution_rate", "communication_stability", "commitment_fulfillment"],
                "process": ["feedback_frequency", "shared_schedule_adherence", "expectation_sync"],
                "risk": ["expectation_drift", "boundary_break", "external_stress"],
                "mechanism": ["boundary_clarity", "response_timing", "repair_cycle"],
            }
        elif topic == "health":
            verifiable_indicators = {
                "outcome": ["sleep_quality", "recovery_rate", "fatigue_reduction"],
                "process": ["exercise_consistency", "diet_adherence", "focus_cycle"],
                "risk": ["burnout_signal", "work_overload", "sleep_debt"],
                "mechanism": ["rest_regulation", "stress_drain", "routine_stability"],
            }

        period_payload = {
            "type": "agent_window",
            "start_at": now.replace(microsecond=0).isoformat(),
            "end_at": (now + timedelta(days=horizon_days)).replace(microsecond=0).isoformat(),
            "timezone": "Asia/Seoul",
        }

        if topic == "wealth":
            causal_path = ["output_energy", "conversion_efficiency", "wealth_retention"]
            risk_modes = ["timing_gap", "liquidity_pressure"]
        elif topic == "career":
            causal_path = ["capability_display", "decision_friction_reduction", "milestone_closure"]
            risk_modes = ["role_conflict", "policy_drift"]
        elif topic == "relationship":
            causal_path = ["boundary_set", "signal_alignment", "conflict_repair"]
            risk_modes = ["expectation_drift", "trust_latency"]
        else:
            causal_path = ["rhythm_rebuild", "load_reduction", "recovery_feedback"]
            risk_modes = ["burnout_pressure", "depletion_cycle"]

        resolver_snapshot = {
            "resolver_version": "consumer-agent-v0",
            "decision_rationale": [
                {
                    "rule_id": f"agent_profile_{topic}",
                    "action": "agent_generated",
                    "weight": 0.8,
                }
            ],
            "conflict_actions": [],
            "time_weight": {"natal": 0.5, "decade": 0.3, "year": 0.2},
            "runtime_context": {
                "topic": topic,
                "focus": focus,
                "period": period,
                "horizon_days": horizon_days,
            },
        }

        contract_payload = {
            "prediction_id": prediction_id,
            "topic": topic,
            "chain_id": f"agent_{topic}_v1",
            "causal_path": causal_path,
            "rule_ids": [f"agent_profile_{topic}"],
            "chain_state": "partial",
            "confidence": _safe_float(payload.get("confidence"), 0.68),
            "period": period_payload,
            "evidence_ids": ["agent_input_focus"],
            "verifiable_indicators": verifiable_indicators,
            "risk_modes": risk_modes,
            "data_sources": ["consumer_agent_input", "self_reported_metrics"],
            "model_version": "v18.1",
            "schema_version": "v18.1",
            "display_policy": {
                "allow_llm_expression": True,
                "max_abs_language_level": "low",
                "require_evidence_tags": True,
            },
            "resolver_snapshot": resolver_snapshot,
            "uncertainty": {"source": ["user_goal_ambiguity", "limited_context"], "score": 0.35},
            "feedback_window": _feedback_window_from_period(period_payload),
        }

        resolved_rules = {
            "status": "resolved",
            "prediction_id": prediction_id,
            "active_rules": [f"agent_profile_{topic}"],
            "suppressed_rules": [],
            "resolved_effect": {},
            "resolver_snapshot": resolver_snapshot,
        }

        contract = self.build_contract(contract_payload, resolved_rules=resolved_rules)
        record = self.write_ledger_record({"prediction_id": prediction_id}, contract.to_dict())

        llm_output = {
            "text": (
                f"结论：{topic}主题在未来{period}有一个可执行观察窗口。\n"
                f"机制：{' > '.join(causal_path)}\n"
                f"建议动作：{';'.join(do_items)}\n"
                f"避免事项：{';'.join(avoid)}"
            ),
            "sections": {
                "conclusion": f"你可以先从 {'当前聚焦点' if not focus else focus} 开始执行，观察对应可测信号。",
                "evidence": contract_payload["evidence_ids"],
                "causal": causal_path,
                "risk": risk_modes,
                "suggestion": do_items[:2],
            },
            "sources": ["consumer_agent_input", "self_reported_metrics"],
        }

        verifier_result = self.run_verifier(
            {
                "prediction_id": prediction_id,
                "contract": contract.to_dict(),
                "llm_output": llm_output,
            }
        )

        response.update(
            {
                "prediction_contract": contract.to_dict(),
                "prediction_hash": record.prediction_hash,
                "verifier_result": verifier_result,
                "ledger_state": record.state,
                "feedback_event_template": {
                    **response["feedback_event_template"],
                    "prediction_id": prediction_id,
                },
            }
        )
        return response

    def review_knowledge_pr(self, payload: Dict[str, Any], actor_role: str = "system") -> Dict[str, Any]:
        role = str(actor_role or "system").strip().lower()
        if role not in {"manager", "admin", "system"}:
            raise PredictiveServiceError("FORBIDDEN", "only manager/admin can review PR", 403)

        pr_id = str(payload.get("pr_id") or "").strip()
        decision = str(payload.get("decision") or "").strip().lower()
        if not pr_id:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "pr_id is required")
        if decision not in {"approve", "reject"}:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "decision must be approve or reject")
        request_id = _safe_str(payload.get("request_id"))
        if request_id:
            cached = self._redis.idempotency_get(f"pr_approve:{request_id}")
            if cached:
                return cached
        lock_key = f"lock:pr:{pr_id}"
        if not self._redis.acquire_lock(lock_key, ttl_seconds=30):
            raise PredictiveServiceError("LOCK_BUSY", "PR review is already in progress", 409)
        try:
            return self._review_knowledge_pr_locked(payload, actor_role=actor_role, request_id=request_id, lock_key=lock_key)
        finally:
            self._redis.release_lock(lock_key)

    def _review_knowledge_pr_locked(self, payload: Dict[str, Any], actor_role: str = "system", request_id: str = "", lock_key: str = "") -> Dict[str, Any]:
        role = str(actor_role or "system").strip().lower()
        pr_id = str(payload.get("pr_id") or "").strip()
        decision = str(payload.get("decision") or "").strip().lower()
        if pr_id not in self._knowledge_pr:
            raise PredictiveServiceError("PR_NOT_FOUND", f"PR {pr_id} not found", 404)

        pr = dict(self._knowledge_pr[pr_id])
        if pr.get("review_state") in {"approved", "rejected"}:
            raise PredictiveServiceError("PR_LOCKED", "PR already reviewed")

        if decision == "approve":
            proposed = dict(pr.get("proposed_rule_payload") or {})
            target_status = str(payload.get("target_status") or pr.get("target_status") or proposed.get("status") or "").strip().lower()
            if target_status == "active":
                raise PredictiveServiceError("RULE_TRANSITION_INVALID", "PR approval cannot directly activate rules", 409)
            if proposed and pr.get("candidate_state") == "sandbox":
                candidate_id = _safe_str(pr.get("rule_candidate_id"))
                proposed_rule_id = _safe_str(proposed.get("rule_id") or pr.get("rule_id"))
                proposed_version = _safe_str(proposed.get("version") or pr.get("rule_version"))
                if not self._has_recent_passing_rule_test(
                    rule_candidate_id=candidate_id,
                    rule_id=proposed_rule_id,
                    version=proposed_version,
                ):
                    raise PredictiveServiceError(
                        "RULE_TEST_REQUIRED",
                        "Knowledge PR approval requires a passing Rule Test Engine v0.2 run",
                        409,
                    )
            if proposed:
                if target_status:
                    proposed["status"] = target_status
                registered = self.register_rule(
                    proposed,
                    actor_role=role,
                    actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
                )
                pr["materialized_rule"] = registered
                pr["rule_id"] = registered.get("rule_id") or pr.get("rule_id")
                pr["rule_version"] = registered.get("version") or pr.get("rule_version")
            elif target_status:
                rule = self.update_rule_status(
                    rule_id=str(pr.get("rule_id") or ""),
                    target_status=target_status,
                    actor_role=role,
                    actor_user_id=_safe_int(payload.get("actor_user_id"), 0),
                    version=_safe_str(payload.get("version") or pr.get("rule_version")) or None,
                )
                pr["materialized_rule"] = self._rule_audit_trace(rule)
            pr["review_state"] = "approved"
        else:
            pr["review_state"] = "rejected"

        pr["reviewer"] = str(payload.get("reviewer") or role or "system").strip()
        pr["review_note"] = str(payload.get("review_note") or "").strip()
        pr["reviewed_at"] = _utcnow_iso()
        self._knowledge_pr[pr_id] = pr
        self.invalidate_cache("cache:knowledge_pr_queue_ranking", "cache:rule_quality_scores")
        self._persist()
        if request_id:
            self._redis.idempotency_set(f"pr_approve:{request_id}", pr)
        return pr

    def run_shadow_compare(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self._assert_lifecycle(
            token=_safe_str(payload.get("lifecycle_token", "")),
            purpose="debug",
            execution_mode="debug",
        )
        topic = str(payload.get("topic") or "").strip()
        cases = payload.get("cases") if isinstance(payload.get("cases"), list) else []
        if not cases:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "cases is required")

        compare: List[Dict[str, Any]] = []
        total = len(cases)
        legacy_hit = 0
        new_hit = 0
        conflict = 0

        for item in cases:
            if not isinstance(item, dict):
                continue
            legacy = str(item.get("legacy_state") or "").strip().lower()
            new_state = str(item.get("new_state") or "").strip().lower()
            case_id = str(item.get("case_id") or "").strip()
            equal = bool(legacy and new_state and legacy == new_state)
            if legacy == "hit":
                legacy_hit += 1
            if new_state == "hit":
                new_hit += 1
            if legacy and new_state and legacy != new_state:
                conflict += 1
            compare.append({"case_id": case_id, "legacy_state": legacy, "new_state": new_state, "equal": equal})

        conflict_rate = _safe_float(conflict / total, 0.0) if total else 0.0
        return {
            "topic": topic,
            "total_cases": total,
            "status": "pass" if conflict_rate <= 0.3 else "needs_review",
            "legacy_hit_rate": _safe_float(legacy_hit / total, 0.0) if total else 0.0,
            "new_hit_rate": _safe_float(new_hit / total, 0.0) if total else 0.0,
            "conflict_rate": conflict_rate,
            "compare": compare,
            "run_id": f"shadow_{_safe_int(datetime.now(timezone.utc).timestamp())}",
        }

    def write_ledger_record(self, prediction: Dict[str, Any], contract: Dict[str, Any]) -> PredictionLedgerRecord:
        prediction_id = str(prediction["prediction_id"])
        if prediction_id in self._ledger:
            raise PredictiveServiceError("FEEDBACK_LOCKED", "prediction_id already exists and is immutable")

        contract_payload = contract
        snapshot = contract_payload.get("resolver_snapshot")
        if not isinstance(snapshot, dict):
            raise PredictiveServiceError("RESOLVER_REQUIRED_MISSING", "resolver_snapshot is required")
        lifecycle = snapshot.get("resolver_lifecycle")
        if not isinstance(lifecycle, dict) or lifecycle.get("gatekeeper_protocol") != RULE_GATEKEEPER_PROTOCOL:
            self._raise_lifecycle_bypass(
                message="ledger write requires resolver lifecycle snapshot",
                purpose="ledger",
                execution_mode=_safe_str(contract_payload.get("execution_mode"), "ledger"),
                actor_role=_safe_str(prediction.get("actor_role"), "system"),
                actor_user_id=_safe_int(prediction.get("actor_user_id"), 0),
                details={"prediction_id": prediction_id},
            )
        evidence_ids = _ensure_list(contract_payload.get("evidence_ids"))
        if not evidence_ids and _ensure_list(contract_payload.get("conclusions")):
            raise PredictiveServiceError("EVIDENCE_BINDING_FAILED", "evidence_ids required", 422)
        feedback_window = dict(contract_payload.get("feedback_window") or {})
        if not feedback_window:
            feedback_window = _feedback_window_from_period(dict(contract_payload.get("period") or {}))

        hash_payload = {
            "prediction_id": prediction_id,
            "topic": contract_payload.get("topic"),
            "chain_id": contract_payload.get("chain_id"),
            "rule_ids": _ensure_list(contract_payload.get("rule_ids")),
            "resolved_effect": contract_payload.get("resolved_effect", {}),
            "period": contract_payload.get("period", {}),
            "evidence_ids": evidence_ids,
            "causal_path": _ensure_list(contract_payload.get("causal_path")),
            "confidence": _safe_float(contract_payload.get("confidence")),
            "uncertainty": contract_payload.get("uncertainty", {}),
            "chain_state": contract_payload.get("chain_state"),
            "model_version": contract_payload.get("model_version"),
            "schema_version": contract_payload.get("schema_version"),
            "feedback_window": feedback_window,
        }
        prediction_hash = _prediction_hash(hash_payload)
        if prediction.get("prediction_hash") and str(prediction.get("prediction_hash")) != prediction_hash:
            raise PredictiveServiceError("PREDICTION_HASH_MISMATCH", "prediction_hash mismatch")

        contract_payload["feedback_window"] = feedback_window
        contract_payload.pop("contract_hash", None)
        contract_hash = _contract_hash(contract_payload)
        chart_snapshot_hash = _payload_hash(dict(contract_payload.get("chart_snapshot") or {}))
        conclusion_refs = [
            _safe_str(row.get("conclusion_id"))
            for row in _ensure_list(contract_payload.get("conclusions"))
            if isinstance(row, dict) and _safe_str(row.get("conclusion_id"))
        ]
        evidence_refs = [
            _safe_str(row.get("evidence_id"))
            for row in _ensure_list(contract_payload.get("rule_evidence"))
            if isinstance(row, dict) and _safe_str(row.get("evidence_id"))
        ]

        record = PredictionLedgerRecord(
            ledger_id=f"led_{prediction_id}",
            prediction_id=prediction_id,
            topic=str(contract_payload.get("topic")),
            chain_id=str(contract_payload.get("chain_id")),
            state="Recorded",
            contract=contract_payload,
            prediction_hash=prediction_hash,
            contract_hash=contract_hash,
            user_query=_safe_str(contract_payload.get("user_query")),
            normalized_intent=dict(contract_payload.get("normalized_intent") or {}),
            chart_snapshot_hash=chart_snapshot_hash,
            conclusion_refs=conclusion_refs,
            evidence_refs=evidence_refs,
            engine_version=_safe_str(contract_payload.get("engine_version") or contract_payload.get("model_version"), V18_1_SCHEMA_VERSION),
            resolver_snapshot=snapshot,
            verifier_status="pending",
            feedback_state="collecting",
            schema_version=str(contract_payload.get("schema_version", V18_1_SCHEMA_VERSION)),
        )
        self._ledger[prediction_id] = record.to_dict()
        self._verifier_runs[prediction_id] = []
        self._feedback_events[prediction_id] = []
        self._persist()
        return record

    def get_ledger(self, prediction_id: str) -> Dict[str, Any]:
        record = self._ledger.get(str(prediction_id))
        if not record:
            raise PredictiveServiceError("LEDGER_NOT_FOUND", f"prediction {prediction_id} not found", 404)
        record = dict(record)
        record["verifier_runs"] = list(self._verifier_runs.get(str(prediction_id), []))
        record["feedback_events"] = list(self._feedback_events.get(str(prediction_id), []))
        return record

    def replay_prediction(self, prediction_id: str) -> Dict[str, Any]:
        record = self.get_ledger(prediction_id)
        contract = dict(record.get("contract") or {})
        evidence = [row for row in _ensure_list(contract.get("rule_evidence")) if isinstance(row, dict)]
        drift_rows = []
        rule_drift = False
        for row in evidence:
            rid = _safe_str(row.get("rule_id"))
            version = _safe_str(row.get("version"))
            evidence_hash = _safe_str(row.get("content_hash"))
            current_hash = ""
            drift = False
            try:
                current_hash = self.get_rule(rid, version=version, allow_inactive=True).content_hash
                drift = bool(current_hash and evidence_hash and current_hash != evidence_hash)
            except PredictiveServiceError:
                drift = True
            rule_drift = rule_drift or drift
            drift_rows.append(
                {
                    "rule_id": rid,
                    "version": version,
                    "evidence_content_hash": evidence_hash,
                    "current_content_hash": current_hash,
                    "rule_drift": drift,
                }
            )
        return {
            "prediction_id": prediction_id,
            "ledger": record,
            "contract": contract,
            "evidence": evidence,
            "feedback": list(self._feedback_events.get(prediction_id, [])),
            "learning_signals": list(self._learning_signals.get(prediction_id, [])),
            "rule_drift": rule_drift,
            "rule_drift_details": drift_rows,
            "replay_mode": "contract_replay_only",
        }

    def public_replay_prediction(self, prediction_id: str) -> Dict[str, Any]:
        replay = self.replay_prediction(prediction_id)
        record = dict(replay.get("ledger") or {})
        contract = dict(replay.get("contract") or {})
        conclusions = [row for row in _ensure_list(contract.get("conclusions")) if isinstance(row, dict)]
        first_conclusion = conclusions[0] if conclusions else {}
        confidence = _safe_float(first_conclusion.get("confidence"), _safe_float(contract.get("confidence"), 0.0))
        uncertainty = dict(contract.get("uncertainty") or {})
        risk_modes = [_safe_str(item) for item in _ensure_list(contract.get("risk_modes")) if _safe_str(item)]

        evidence_summary = []
        for evidence in _ensure_list(replay.get("evidence")):
            if not isinstance(evidence, dict):
                continue
            effect = dict(evidence.get("effect") or {})
            evidence_summary.append(
                {
                    "rule_id": _safe_str(evidence.get("rule_id")),
                    "version": _safe_str(evidence.get("version")),
                    "feature_id": _safe_str(evidence.get("feature_id")),
                    "feature_type": _safe_str(evidence.get("feature_type")),
                    "feature_label": _safe_str(evidence.get("feature_label") or dict(evidence.get("feature") or {}).get("label")),
                    "evidence_type": _safe_str(evidence.get("evidence_type"), "feature_evidence" if evidence.get("feature_id") else "rule_evidence"),
                    "effect_keys": sorted([_safe_str(key) for key in effect.keys() if _safe_str(key)]),
                    "matched_fact_count": len(_ensure_list(evidence.get("matched_facts"))),
                    "confidence_delta": _safe_float(evidence.get("confidence_delta"), 0.0),
                    "risk": _safe_float(evidence.get("risk"), 0.0),
                    "stability": _safe_float(evidence.get("stability"), 0.0),
                }
            )

        return {
            "public_safe": True,
            "prediction_id_short": _safe_str(prediction_id)[:18],
            "topic": _safe_str(record.get("topic") or contract.get("topic")),
            "conclusion_summary": _safe_str(first_conclusion.get("claim"), "n/a"),
            "confidence": confidence,
            "uncertainty": {
                "score": _safe_float(uncertainty.get("score"), 0.0),
                "risk_modes": risk_modes[:4],
            },
            "verifier_status": _safe_str(record.get("verifier_status") or record.get("state"), "n/a"),
            "evidence_summary": evidence_summary[:5],
            "feedback_count": len(_ensure_list(replay.get("feedback"))),
            "learning_signal_count": len(_ensure_list(replay.get("learning_signals"))),
            "rule_drift": bool(replay.get("rule_drift")),
            "replay_mode": "public_redacted_replay",
            "redaction": {
                "public_safe": True,
                "notice": "此回放已隐藏个人信息",
                "full_record_notice": "完整记录仅本人登录后可见",
            },
        }

    def run_verifier(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prediction_id = str(payload.get("prediction_id") or "").strip()
        if not prediction_id:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "prediction_id required")
        record = self._ledger.get(prediction_id)
        if not record:
            raise PredictiveServiceError("LEDGER_NOT_FOUND", f"prediction {prediction_id} not found", 404)

        contract_data = payload.get("contract")
        llm_output = payload.get("llm_output") or {}
        if not isinstance(contract_data, dict) or not isinstance(llm_output, dict):
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "contract and llm_output required")

        checks: Dict[str, bool] = {}
        sections = llm_output.get("sections", {})
        evidence_ids = _ensure_list(contract_data.get("evidence_ids"))
        llm_evidence = _ensure_list(sections.get("evidence"))
        checks["evidence_binding"] = all(eid in llm_evidence for eid in evidence_ids) if evidence_ids else not _ensure_list(contract_data.get("conclusions"))

        contract_verification = self.verify_prediction_contract(contract_data)
        checks["prediction_contract_valid"] = contract_verification.get("result") == "pass"
        allowed_conclusion_ids = {
            _safe_str(row.get("conclusion_id"))
            for row in _ensure_list(contract_data.get("conclusions"))
            if isinstance(row, dict) and _safe_str(row.get("conclusion_id"))
        }
        llm_conclusion_ids = {
            _safe_str(item)
            for item in _ensure_list(sections.get("conclusion_ids") or llm_output.get("conclusion_ids"))
            if _safe_str(item)
        }
        checks["contract_conclusion_scope"] = llm_conclusion_ids.issubset(allowed_conclusion_ids) if llm_conclusion_ids else True
        if not allowed_conclusion_ids:
            text_for_insufficient = str(llm_output.get("text") or "")
            allowed_insufficient_terms = {"不足以判断", "证据不足", "insufficient evidence", "not enough evidence"}
            checks["empty_conclusion_scope"] = any(term in text_for_insufficient for term in allowed_insufficient_terms)
        else:
            checks["empty_conclusion_scope"] = True

        absolute_words = {"必然", "必定", "注定", "100%", "100", "绝对", "确定", "肯定"}
        text = str(llm_output.get("text") or "")
        checks["forbidden_absolute_wording"] = not any(word in text for word in absolute_words)

        contract_risks = _ensure_list(contract_data.get("risk_modes"))
        checks["risk_preservation"] = bool(not contract_risks or _ensure_list(sections.get("risk")))

        causal_path = _ensure_list(contract_data.get("causal_path"))
        llm_causal = _ensure_list(sections.get("causal"))
        checks["causal_consistency"] = all(
            any(step == path_step or path_step in llm_causal for path_step in causal_path)
            for step in causal_path
        ) if causal_path else True

        chain_step_ok = all(
            isinstance((sections or {}).get(key), (str, list))
            for key in ("conclusion", "evidence", "risk", "suggestion", "causal")
        )
        checks["chain_step"] = bool(chain_step_ok)

        allowed_sources = set(_ensure_list(contract_data.get("data_sources")))
        llm_sources = set(_ensure_list(llm_output.get("sources")))
        if llm_sources and allowed_sources:
            checks["unauthorized_source"] = llm_sources.issubset(allowed_sources)
        else:
            checks["unauthorized_source"] = True

        fatal_fail_keys = {
            "evidence_binding",
            "chain_step",
            "unauthorized_source",
            "prediction_contract_valid",
            "contract_conclusion_scope",
            "empty_conclusion_scope",
        }
        if any(not checks.get(key, False) for key in fatal_fail_keys):
            result = "fail"
            action = "BLOCKED"
        elif all(checks.values()):
            result = "pass"
            action = "DISPLAY"
        else:
            result = "pass_with_warning"
            action = "ALLOW_WARNING"

        run = VerifierRun(
            run_id=f"vrun_{prediction_id}_{_safe_int(len(self._verifier_runs.get(prediction_id, [])) + 1)}",
            prediction_id=prediction_id,
            checks=checks,
            result=result,
            action=action,
            verifier_version="v18.1",
        )
        self._verifier_runs.setdefault(prediction_id, []).append(run.to_dict())
        record = self._ledger.get(prediction_id, {})
        record["verifier_status"] = "pass" if result.startswith("pass") else "fail" if result == "fail" else record.get("verifier_status", "pending")
        record["state"] = "Verified"
        if result == "pass":
            record["state"] = "Displayed"
        elif result == "fail":
            record["state"] = "Blocked"
        record["updated_at"] = _utcnow_iso()
        self._ledger[prediction_id] = record

        self._persist()

        if result == "fail":
            return {
                "prediction_id": prediction_id,
                "result": result,
                "checks": checks,
                "action": action,
                "verifier_run_id": run.run_id,
                "degraded_fields": [key for key, passed in checks.items() if not passed],
            }

        return {
            "prediction_id": prediction_id,
            "result": result,
            "checks": checks,
            "action": action,
            "verifier_run_id": run.run_id,
            "degraded_fields": [key for key, passed in checks.items() if not passed],
        }

    def _explanation_request(self, prediction_id: str, payload: Dict[str, Any], contract: Dict[str, Any]) -> ExplanationRequest:
        contract_id = _safe_str(payload.get("contract_id"), f"contract_{prediction_id}")
        level = _safe_str(payload.get("explanation_level"), "normal")
        if level not in {"brief", "normal", "detailed"}:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "explanation_level must be brief/normal/detailed", 400)
        raw_scope = payload.get("allowed_output_scope") or contract.get("allowed_output_scope") or {}
        if isinstance(raw_scope, dict):
            allowed_output_scope = dict(raw_scope)
        else:
            scope_text = _safe_str(raw_scope)
            allowed_output_scope = {"scope": scope_text} if scope_text else {}
        return ExplanationRequest(
            prediction_id=prediction_id,
            contract_id=contract_id,
            allowed_output_scope=allowed_output_scope,
            user_locale=_safe_str(payload.get("user_locale"), "zh-CN"),
            tone=_safe_str(payload.get("tone"), "clear"),
            explanation_level=level,
            include_uncertainty=_safe_bool(payload.get("include_uncertainty"), True),
            include_evidence_trace=_safe_bool(payload.get("include_evidence_trace"), False),
        )

    def _contract_evidence_trace(self, contract: Dict[str, Any]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for evidence in _ensure_list(contract.get("rule_evidence")):
            if not isinstance(evidence, dict):
                continue
            rows.append(
                {
                    "evidence_id": _safe_str(evidence.get("evidence_id")),
                    "rule_id": _safe_str(evidence.get("rule_id")),
                    "version": _safe_str(evidence.get("version")),
                    "content_hash": _safe_str(evidence.get("content_hash")),
                    "feature_id": _safe_str(evidence.get("feature_id")),
                    "feature_type": _safe_str(evidence.get("feature_type")),
                    "feature_label": _safe_str(dict(evidence.get("feature") or {}).get("label")),
                    "matched_facts": _ensure_list(evidence.get("matched_facts")),
                    "effect": dict(evidence.get("effect") or {}),
                    "confidence_delta": _safe_float(evidence.get("confidence_delta"), 0.0),
                    "risk": _safe_float(evidence.get("risk"), 0.0),
                    "stability": _safe_float(evidence.get("stability"), 0.0),
                    "wealth_relevance": _safe_float(evidence.get("wealth_relevance"), 0.0),
                }
            )
        return rows

    def _build_explanation_output(self, contract: Dict[str, Any], request: ExplanationRequest) -> Dict[str, Any]:
        conclusions = [row for row in _ensure_list(contract.get("conclusions")) if isinstance(row, dict)]
        evidence_ids = [_safe_str(row.get("evidence_id")) for row in _ensure_list(contract.get("rule_evidence")) if isinstance(row, dict) and _safe_str(row.get("evidence_id"))]
        evidence_rows = [row for row in _ensure_list(contract.get("rule_evidence")) if isinstance(row, dict)]
        causal_path = [_safe_str(item) for item in _ensure_list(contract.get("causal_path")) if _safe_str(item)]
        risk_modes = [_safe_str(item) for item in _ensure_list(contract.get("risk_modes")) if _safe_str(item)]
        if not conclusions:
            text = "证据不足，不足以判断。当前 Prediction Contract 没有形成可引用的结论，需要补充信息或等待更多可验证证据。"
            return {
                "text": text,
                "is_prediction": False,
                "sections": {
                    "conclusion": [],
                    "conclusion_ids": [],
                    "evidence": [],
                    "causal": causal_path,
                    "risk": risk_modes,
                    "suggestion": ["补充关键排盘信息或更多可验证事实"],
                },
                "sources": _ensure_list(contract.get("data_sources")),
                "reasoning_adapter": {
                    "mode": "contract_bounded_v1",
                    "used_evidence_ids": [],
                    "constraints": ["no_new_conclusion", "no_confidence_change", "contract_evidence_only"],
                },
            }

        conclusion_lines: List[str] = []
        conclusion_ids: List[str] = []
        max_confidence = 0.0
        for conclusion in conclusions:
            conclusion_id = _safe_str(conclusion.get("conclusion_id"))
            claim = _safe_str(conclusion.get("claim"))
            confidence = _safe_float(conclusion.get("confidence"), _safe_float(contract.get("confidence"), 0.0))
            max_confidence = max(max_confidence, confidence)
            if conclusion_id:
                conclusion_ids.append(conclusion_id)
            if claim:
                conclusion_lines.append(f"{claim}（置信度约 {min(99, round(confidence * 100))}%）")
        uncertainty = dict(contract.get("uncertainty") or {})
        uncertainty_text = ""
        if request.include_uncertainty:
            uncertainty_score = _safe_float(uncertainty.get("score"), 0.0)
            uncertainty_text = f" uncertainty 需保留，当前 uncertainty score 约为 {min(99, round(uncertainty_score * 100))}%。"
        evidence_text = ""
        evidence_detail_text = ""
        if request.include_evidence_trace:
            labels = [
                _safe_str(dict(row.get("feature") or {}).get("label") or row.get("feature_label") or row.get("feature_type"))
                for row in evidence_rows
            ]
            labels = [item for item in labels if item]
            label_text = "、".join(labels[:4])
            evidence_text = f" 证据链引用 {len(evidence_ids)} 条 contract evidence。"
            if label_text:
                evidence_text += f"综合依据包括：{label_text}。"
            evidence_detail_lines = []
            for row in evidence_rows[:4]:
                label = _safe_str(dict(row.get("feature") or {}).get("label") or row.get("feature_label") or row.get("feature_type"))
                strength = _safe_float(row.get("strength"), _safe_float(row.get("confidence_delta"), 0.0))
                stability = _safe_float(row.get("stability"), 0.0)
                risk = _safe_float(row.get("risk"), 0.0)
                if label:
                    evidence_detail_lines.append(f"{label}: strength {round(strength * 100)}%, stability {round(stability * 100)}%, risk {round(risk * 100)}%")
            if evidence_detail_lines:
                evidence_detail_text = " 分项依据：" + "；".join(evidence_detail_lines) + "。"
        if request.explanation_level == "brief":
            text = "；".join(conclusion_lines[:1]) + uncertainty_text
        elif request.explanation_level == "detailed":
            text = "综合判断：" + "；".join(conclusion_lines) + "。机制：" + " > ".join(causal_path) + "。" + uncertainty_text + evidence_text + evidence_detail_text
        else:
            text = "综合判断：" + "；".join(conclusion_lines) + "。" + uncertainty_text + evidence_text + evidence_detail_text
        return {
            "text": text,
            "is_prediction": True,
            "max_confidence": max_confidence,
            "sections": {
                "conclusion": conclusion_lines,
                "conclusion_ids": conclusion_ids,
                "evidence": evidence_ids,
                "causal": causal_path,
                "risk": risk_modes,
                "suggestion": ["以上解释仅限 Prediction Contract 范围，不新增命理判断"],
            },
            "sources": _ensure_list(contract.get("data_sources")),
            "reasoning_adapter": {
                "mode": "contract_bounded_v1",
                "used_evidence_ids": evidence_ids,
                "constraints": ["no_new_conclusion", "no_confidence_change", "contract_evidence_only"],
            },
        }

    def _verify_explanation_output(self, contract: Dict[str, Any], request: ExplanationRequest, output: Dict[str, Any]) -> Dict[str, Any]:
        verifier = self.run_verifier({"prediction_id": request.prediction_id, "contract": contract, "llm_output": output})
        errors = list(verifier.get("degraded_fields") or [])
        allowed_evidence = {
            _safe_str(row.get("evidence_id"))
            for row in _ensure_list(contract.get("rule_evidence"))
            if isinstance(row, dict) and _safe_str(row.get("evidence_id"))
        }
        cited_evidence = {
            _safe_str(item)
            for item in _ensure_list((output.get("sections") or {}).get("evidence"))
            if _safe_str(item)
        }
        if not cited_evidence.issubset(allowed_evidence):
            errors.append("explanation_evidence_scope")
        allowed_conclusions = {
            _safe_str(row.get("conclusion_id"))
            for row in _ensure_list(contract.get("conclusions"))
            if isinstance(row, dict) and _safe_str(row.get("conclusion_id"))
        }
        cited_conclusions = {
            _safe_str(item)
            for item in _ensure_list((output.get("sections") or {}).get("conclusion_ids"))
            if _safe_str(item)
        }
        if not cited_conclusions.issubset(allowed_conclusions):
            errors.append("explanation_conclusion_scope")
        contract_confidence = max(
            [_safe_float(row.get("confidence"), _safe_float(contract.get("confidence"), 0.0)) for row in _ensure_list(contract.get("conclusions")) if isinstance(row, dict)]
            or [_safe_float(contract.get("confidence"), 0.0)]
        )
        output_confidence = _safe_float(output.get("max_confidence"), contract_confidence)
        if output_confidence > min(1.0, contract_confidence + 0.05):
            errors.append("confidence_exaggeration")
        if request.include_uncertainty and contract.get("uncertainty"):
            text = _safe_str(output.get("text"))
            if not any(term in text for term in {"不确定", "uncertainty", "证据不足", "需保留"}):
                errors.append("uncertainty_omitted")
        conclusions = [row for row in _ensure_list(contract.get("conclusions")) if isinstance(row, dict)]
        if not conclusions and output.get("is_prediction"):
            errors.append("clarification_masquerades_as_prediction")
        if errors or verifier.get("result") == "fail":
            verifier["result"] = "fail"
            verifier["action"] = "BLOCKED"
            verifier["degraded_fields"] = sorted(set(errors))
        return verifier

    def explain_prediction(self, prediction_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        prediction_id = _safe_str(prediction_id)
        record = self.get_ledger(prediction_id)
        contract = dict(record.get("contract") or {})
        verification = self.verify_prediction_contract(contract)
        if verification.get("result") != "pass":
            raise PredictiveServiceError("CONTRACT_VERIFIER_FAILED", ",".join(_ensure_list(verification.get("errors"))), 422)
        request = self._explanation_request(prediction_id, payload, contract)
        expected_contract_id = f"contract_{prediction_id}"
        if request.contract_id and request.contract_id != expected_contract_id:
            raise PredictiveServiceError("CONTRACT_ID_MISMATCH", "contract_id does not match prediction_id", 409)
        output = dict(payload.get("candidate_output") or payload.get("llm_output") or {})
        if not output:
            output = self._build_explanation_output(contract, request)
        verifier = self._verify_explanation_output(contract, request, output)
        if verifier.get("result") == "fail":
            raise PredictiveServiceError("EXPLANATION_VERIFIER_FAILED", ",".join(_ensure_list(verifier.get("degraded_fields"))), 422)
        evidence_trace = self._contract_evidence_trace(contract) if request.include_evidence_trace else []
        response = ExplanationResponse(
            prediction_id=prediction_id,
            contract_id=request.contract_id,
            explanation=_safe_str(output.get("text")),
            safe_output=output,
            verifier=verifier,
            evidence_trace=evidence_trace,
        )
        return response.to_dict()

    def append_feedback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prediction_id = str(payload.get("prediction_id") or "").strip()
        if not prediction_id:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "prediction_id required")
        if prediction_id not in self._ledger:
            raise PredictiveServiceError("LEDGER_NOT_FOUND", f"prediction {prediction_id} not found", 404)

        required = {"prediction_id", "feedback_type", "outcome"}
        missing = [k for k in required if not payload.get(k)]
        if missing:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", f"missing {','.join(missing)}")

        record = self._ledger[prediction_id]
        if record.get("feedback_state") in {"collected", "closed"}:
            raise PredictiveServiceError("FEEDBACK_LOCKED", "feedback state locked")

        contract_payload = record.get("contract", {})
        observed_at = str(payload.get("observed_at", _utcnow_iso()))
        feedback_window = dict(contract_payload.get("feedback_window") or {})
        window_start = _parse_dt(feedback_window.get("start"))
        window_end = _parse_dt(feedback_window.get("end"))
        observed_time = _parse_dt(observed_at)
        in_window = bool(window_start and window_end and observed_time and window_start <= observed_time <= window_end)
        outcome = str(payload.get("outcome"))
        if not in_window:
            outcome = "UNVERIFIABLE"

        event = FeedbackEvent(
            prediction_id=prediction_id,
            feedback_type=str(payload.get("feedback_type")),
            outcome=outcome,
            evidence_of_outcome=_ensure_list(payload.get("evidence_of_outcome")),
            notes=str(payload.get("notes", "")),
            observed_at=observed_at,
            feedback_window_valid=in_window,
            event_id=f"fb_{prediction_id}_{_safe_int(len(self._feedback_events.get(prediction_id, [])) + 1)}",
        )

        self._feedback_events.setdefault(prediction_id, []).append(event.to_dict())
        record["feedback_state"] = "feedback_collecting" if in_window else "closed"
        record["state"] = "Feedback_Collecting" if in_window else "Closed"
        record["updated_at"] = _utcnow_iso()
        self._ledger[prediction_id] = record
        self._persist()
        return {
            "prediction_id": prediction_id,
            "feedback_state": record.get("feedback_state"),
            "feedback_window_valid": in_window,
            "normalized_outcome": outcome,
            "feedback_event_id": event.event_id,
            "append_only": True,
        }

    def _learning_action_for_feedback(self, feedback_type: str) -> str:
        kind = _safe_str(feedback_type).lower()
        if kind == "hit":
            return "increase_confidence"
        if kind == "miss":
            return "review_rule"
        if kind == "partial":
            return "review_rule"
        return "observe"

    def append_prediction_feedback(self, prediction_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        prediction_id = _safe_str(prediction_id or payload.get("prediction_id"))
        if not prediction_id or prediction_id not in self._ledger:
            raise PredictiveServiceError("LEDGER_NOT_FOUND", f"prediction {prediction_id} not found", 404)
        request_id = _safe_str(payload.get("request_id"))
        if request_id:
            cached = self._redis.idempotency_get(f"feedback:{prediction_id}:{request_id}")
            if cached:
                return cached
        feedback_type = _safe_str(payload.get("feedback_type"), "user_comment").lower()
        if feedback_type not in {"hit", "miss", "partial", "unclear", "user_comment"}:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "invalid feedback_type", 400)

        record = self._ledger[prediction_id]
        contract = dict(record.get("contract") or {})
        conclusion_ref = _safe_str(payload.get("conclusion_id") or payload.get("conclusion_ref"))
        conclusion_ids = {
            _safe_str(row.get("conclusion_id"))
            for row in _ensure_list(contract.get("conclusions"))
            if isinstance(row, dict) and _safe_str(row.get("conclusion_id"))
        }
        if conclusion_ref and conclusion_ids and conclusion_ref not in conclusion_ids:
            raise PredictiveServiceError("CONCLUSION_NOT_FOUND", "feedback conclusion_ref not found", 404)
        feedback_id = f"fb_{prediction_id}_{_safe_int(len(self._feedback_events.get(prediction_id, [])) + 1)}"
        feedback = {
            "feedback_id": feedback_id,
            "prediction_id": prediction_id,
            "conclusion_id": conclusion_ref,
            "conclusion_ref": conclusion_ref,
            "feedback_type": feedback_type,
            "user_comment": _safe_str(payload.get("user_comment")),
            "observed_event": dict(payload.get("observed_event") or {}),
            "observed_at": _safe_str(payload.get("observed_at"), _utcnow_iso()),
            "created_at": _utcnow_iso(),
        }
        self._feedback_events.setdefault(prediction_id, []).append(feedback)

        evidence_refs: List[str] = []
        for conclusion in _ensure_list(contract.get("conclusions")):
            if isinstance(conclusion, dict) and (not conclusion_ref or _safe_str(conclusion.get("conclusion_id")) == conclusion_ref):
                evidence_refs.extend(_safe_str(item) for item in _ensure_list(conclusion.get("evidence_ids")) if _safe_str(item))
        suggested_action = self._learning_action_for_feedback(feedback_type)
        if feedback_type == "miss" and not evidence_refs:
            suggested_action = "create_candidate"
        signal = {
            "signal_id": f"ls_{prediction_id}_{_safe_int(len(self._learning_signals.get(prediction_id, [])) + 1)}",
            "prediction_id": prediction_id,
            "conclusion_ref": conclusion_ref,
            "rule_evidence_refs": sorted(set(evidence_refs)),
            "feedback_type": feedback_type,
            "suggested_action": suggested_action,
            "reason": f"feedback_type={feedback_type}",
            "created_at": _utcnow_iso(),
        }
        self._learning_signals.setdefault(prediction_id, []).append(signal)
        self.invalidate_cache("cache:rule_quality_scores", f"cache:prediction_replay:{prediction_id}", "cache:learning_insights")
        self._persist()
        result = {"feedback": feedback, "learning_signal": signal}
        if request_id:
            self._redis.idempotency_set(f"feedback:{prediction_id}:{request_id}", result)
        return result

    def query_feedback(self, *, prediction_id: str | None = None, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        if prediction_id:
            items = list(self._feedback_events.get(_safe_str(prediction_id), []))
        else:
            items = []
            for rows in self._feedback_events.values():
                items.extend(rows)
        items = sorted(items, key=lambda item: _parse_dt(item.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        start = max(0, _safe_int(offset, 0))
        size = max(1, min(_safe_int(limit, 100), 500))
        return {"items": items[start : start + size], "total_matched": len(items), "total_returned": len(items[start : start + size]), "offset": start, "limit": size}

    def query_learning_signals(self, *, prediction_id: str | None = None) -> List[Dict[str, Any]]:
        if prediction_id:
            return list(self._learning_signals.get(_safe_str(prediction_id), []))
        out: List[Dict[str, Any]] = []
        for rows in self._learning_signals.values():
            out.extend(rows)
        return out

    def query_trust_metrics(self) -> Dict[str, Any]:
        total_predictions = len(self._ledger)
        feedback_rows = [dict(item) for rows in self._feedback_events.values() for item in rows if isinstance(item, dict)]
        total_feedback = len(feedback_rows)

        feedback_distribution_counts = {"hit": 0, "partial": 0, "miss": 0, "unclear": 0}
        high_confidence_miss_count = 0
        verified_count = 0
        replay_count = 0

        for feedback in feedback_rows:
            feedback_type = _safe_str(feedback.get("feedback_type")).lower()
            if feedback_type in feedback_distribution_counts:
                feedback_distribution_counts[feedback_type] += 1

        for prediction_id, record in self._ledger.items():
            if isinstance(record, dict) and isinstance(record.get("contract"), dict):
                replay_count += 1
            if _safe_str(record.get("verifier_status")) in {"pass", "pass_with_warning"}:
                verified_count += 1

        for prediction_id, feedback_rows_for_prediction in self._feedback_events.items():
            record = dict(self._ledger.get(prediction_id, {}))
            contract = dict(record.get("contract") or {})
            confidence = _safe_float(contract.get("confidence"), 0.0)
            if confidence >= 0.7:
                high_confidence_miss_count += sum(
                    1
                    for feedback in _ensure_list(feedback_rows_for_prediction)
                    if isinstance(feedback, dict) and _safe_str(feedback.get("feedback_type")).lower() == "miss"
                )

        active_rules = self.list_rules(status="active")
        latest_rule_updated_at = ""
        latest_rule_update: Dict[str, Any] = {}
        latest_rule_updated_dt: datetime | None = None
        for rule in active_rules:
            rule_snapshot = rule.to_dict()
            for source in (
                _safe_str(rule.approved_at),
                _safe_str(rule_snapshot.get("approved_at")),
                _safe_str(rule_snapshot.get("updated_at")),
                _safe_str(rule_snapshot.get("created_at")),
            ):
                dt = _parse_dt(source)
                if dt is None:
                    continue
                if latest_rule_updated_dt is None or dt > latest_rule_updated_dt:
                    latest_rule_updated_dt = dt
                    latest_rule_update = {
                        "rule_id": rule.rule_id,
                        "version": rule.version,
                        "status": rule.status,
                        "updated_at": source,
                    }
        if latest_rule_updated_dt:
            latest_rule_updated_at = latest_rule_updated_dt.replace(microsecond=0).isoformat()

        insights_payload = self.aggregate_learning_insights()
        insights_generated = _safe_int(len(insights_payload.get("items") or []), 0)
        learning_signals_generated = sum(len(rows) for rows in self._learning_signals.values())
        suggestions_generated = len(self._candidate_rule_suggestions)

        feedback_distribution = {key: _safe_float(value / max(1, total_feedback), 0.0) for key, value in feedback_distribution_counts.items()}
        now = datetime.now(timezone.utc)
        day_ago = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)
        seven_days_ago = now - timedelta(days=7)
        prediction_last_24h = 0
        prediction_previous_24h = 0
        prediction_last_7d = 0
        active_users_last_7d: set[str] = set()
        for record in self._ledger.values():
            if not isinstance(record, dict):
                continue
            created = _parse_dt(record.get("created_at"))
            if created is None:
                continue
            if created >= seven_days_ago:
                prediction_last_7d += 1
                for key in ("user_id", "agent_session_id", "session_id", "created_by"):
                    value = _safe_str(record.get(key))
                    if value:
                        active_users_last_7d.add(value)
            if created >= day_ago:
                prediction_last_24h += 1
            elif created >= two_days_ago:
                prediction_previous_24h += 1
        feedback_last_24h = 0
        feedback_previous_24h = 0
        feedback_last_7d = 0
        feedback_hit_partial_last_7d = 0
        for feedback in feedback_rows:
            created = _parse_dt(feedback.get("created_at") or feedback.get("observed_at"))
            if created is None:
                continue
            if created >= seven_days_ago:
                feedback_last_7d += 1
                if _safe_str(feedback.get("feedback_type")).lower() in {"hit", "partial"}:
                    feedback_hit_partial_last_7d += 1
            if created >= day_ago:
                feedback_last_24h += 1
            elif created >= two_days_ago:
                feedback_previous_24h += 1
        last_7d_hit_partial_rate = _safe_float(feedback_hit_partial_last_7d / max(1, feedback_last_7d), 0.0)
        return {
            "total_predictions": total_predictions,
            "total_feedback": total_feedback,
            "feedback_distribution": feedback_distribution,
            "verified_explanations_rate": _safe_float(verified_count / max(1, total_predictions), 0.0),
            "replay_available_rate": _safe_float(replay_count / max(1, total_predictions), 0.0),
            "active_rules": len(active_rules),
            "rules_last_updated_at": latest_rule_updated_at,
            "high_confidence_miss_rate": _safe_float(high_confidence_miss_count / max(1, total_feedback), 0.0),
            "learning_signals_generated": learning_signals_generated,
            "insights_generated": insights_generated,
            "suggestions_generated": suggestions_generated,
            "last_7d_predictions": prediction_last_7d,
            "last_7d_feedback": feedback_last_7d,
            "last_7d_hit_partial_rate": last_7d_hit_partial_rate,
            "last_7d_active_users": len(active_users_last_7d),
            "last_rule_update_time": latest_rule_updated_at,
            "last_7d_metrics": {
                "predictions": prediction_last_7d,
                "feedback": feedback_last_7d,
                "hit_partial_rate": last_7d_hit_partial_rate,
                "active_users": len(active_users_last_7d),
                "last_rule_update_time": latest_rule_updated_at,
                "data_sufficient": prediction_last_7d >= 10 and feedback_last_7d >= 3,
            },
            "prediction_trend": {
                "last_24h": prediction_last_24h,
                "previous_24h": prediction_previous_24h,
                "delta": prediction_last_24h - prediction_previous_24h,
            },
            "feedback_trend": {
                "last_24h": feedback_last_24h,
                "previous_24h": feedback_previous_24h,
                "delta": feedback_last_24h - feedback_previous_24h,
            },
            "latest_rule_update": latest_rule_update,
            "learning_visibility": {
                "recent_feedback_count": feedback_last_24h,
                "learning_signal_count": learning_signals_generated,
                "note": "feedback influences learning signals and reviewer suggestions without directly mutating active rules",
            },
        }

    def _learning_rows_for_aggregation(self) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for prediction_id, signals in self._learning_signals.items():
            ledger = self._ledger.get(prediction_id)
            if not isinstance(ledger, dict):
                continue
            contract = dict(ledger.get("contract") or {})
            evidence_by_id = {
                _safe_str(item.get("evidence_id")): dict(item)
                for item in _ensure_list(contract.get("rule_evidence"))
                if isinstance(item, dict) and _safe_str(item.get("evidence_id"))
            }
            conclusion_by_id = {
                _safe_str(item.get("conclusion_id")): dict(item)
                for item in _ensure_list(contract.get("conclusions"))
                if isinstance(item, dict) and _safe_str(item.get("conclusion_id"))
            }
            feedback_rows = [
                dict(item)
                for item in self._feedback_events.get(prediction_id, [])
                if isinstance(item, dict)
            ]
            chart_snapshot = dict(contract.get("chart_snapshot") or {})
            matched_facts = [_safe_str(item) for item in _ensure_list(chart_snapshot.get("matched_facts")) if _safe_str(item)]
            chart_pattern = "|".join(sorted(matched_facts)) or _safe_str(ledger.get("chart_snapshot_hash"))
            uncertainty = dict(contract.get("uncertainty") or {})
            uncertainty_score = _safe_float(uncertainty.get("score"), 0.0)
            contract_confidence = _safe_float(contract.get("confidence"), 0.0)
            for signal in signals:
                if not isinstance(signal, dict):
                    continue
                conclusion_ref = _safe_str(signal.get("conclusion_ref"))
                related_feedback = [
                    item
                    for item in feedback_rows
                    if not conclusion_ref or _safe_str(item.get("conclusion_ref") or item.get("conclusion_id")) == conclusion_ref
                ]
                evidence_refs = [_safe_str(item) for item in _ensure_list(signal.get("rule_evidence_refs")) if _safe_str(item)]
                if not evidence_refs and conclusion_ref in conclusion_by_id:
                    evidence_refs = [
                        _safe_str(item)
                        for item in _ensure_list(conclusion_by_id[conclusion_ref].get("evidence_ids"))
                        if _safe_str(item)
                    ]
                related_rule_ids = sorted(
                    {
                        _safe_str(evidence_by_id.get(eid, {}).get("rule_id"))
                        for eid in evidence_refs
                        if _safe_str(evidence_by_id.get(eid, {}).get("rule_id"))
                    }
                )
                rows.append(
                    {
                        "signal": dict(signal),
                        "feedback": related_feedback,
                        "ledger": ledger,
                        "contract": contract,
                        "related_rule_ids": related_rule_ids,
                        "related_conclusion": conclusion_ref,
                        "evidence_refs": evidence_refs,
                        "chart_pattern": chart_pattern,
                        "uncertainty_score": uncertainty_score,
                        "contract_confidence": contract_confidence,
                        "prediction_id": prediction_id,
                    }
                )
        return rows

    def _dominant_failure_pattern(self, rows: List[Dict[str, Any]], *, miss_count: int, partial_count: int) -> str:
        pattern_counts: Dict[str, int] = {}
        high_uncertainty = 0
        high_confidence_miss = 0
        for row in rows:
            signal = dict(row.get("signal") or {})
            feedback_type = _safe_str(signal.get("feedback_type")).lower()
            chart_pattern = _safe_str(row.get("chart_pattern"), "unknown_chart")
            if feedback_type == "miss":
                pattern_counts[f"miss_chart:{chart_pattern}"] = pattern_counts.get(f"miss_chart:{chart_pattern}", 0) + 1
                if _safe_float(row.get("contract_confidence"), 0.0) >= 0.7:
                    high_confidence_miss += 1
            if feedback_type == "partial":
                pattern_counts[f"partial_condition:{chart_pattern}"] = pattern_counts.get(f"partial_condition:{chart_pattern}", 0) + 1
            if _safe_float(row.get("uncertainty_score"), 0.0) >= 0.5:
                high_uncertainty += 1
        if high_confidence_miss >= 2:
            return "high_confidence_miss"
        if miss_count >= 2 and pattern_counts:
            return sorted(pattern_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
        if partial_count >= 2 and pattern_counts:
            return sorted(pattern_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
        if high_uncertainty >= 2:
            return "high_uncertainty_evidence"
        return "no_dominant_failure"

    def _suggested_action_for_insight(self, *, related_rule_ids: List[str], hit_count: int, miss_count: int, partial_count: int, pattern: str) -> str:
        if not related_rule_ids and miss_count:
            return "create_new_rule"
        if pattern == "high_confidence_miss":
            return "adjust_confidence"
        if miss_count >= 3 and hit_count == 0:
            return "deprecate_rule"
        if miss_count >= 2 and partial_count >= 1:
            return "split_rule"
        if miss_count >= 2:
            return "refine_condition"
        if partial_count >= 2:
            return "refine_condition"
        if hit_count >= miss_count + partial_count:
            return "no_change"
        return "adjust_confidence"

    def aggregate_learning_insights(self) -> Dict[str, Any]:
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for row in self._learning_rows_for_aggregation():
            rule_key = ",".join(row.get("related_rule_ids") or []) or "unmapped_rule"
            conclusion = _safe_str(row.get("related_conclusion"), "unmapped_conclusion")
            key = f"{rule_key}::{conclusion}"
            grouped.setdefault(key, []).append(row)

        insights: Dict[str, Dict[str, Any]] = {}
        for key, rows in grouped.items():
            related_rule_ids = sorted({rid for row in rows for rid in _ensure_list(row.get("related_rule_ids")) if _safe_str(rid)})
            related_conclusions = sorted({_safe_str(row.get("related_conclusion")) for row in rows if _safe_str(row.get("related_conclusion"))})
            signal_count = len(rows)
            hit_count = sum(1 for row in rows if _safe_str((row.get("signal") or {}).get("feedback_type")).lower() == "hit")
            miss_count = sum(1 for row in rows if _safe_str((row.get("signal") or {}).get("feedback_type")).lower() == "miss")
            partial_count = sum(1 for row in rows if _safe_str((row.get("signal") or {}).get("feedback_type")).lower() == "partial")
            evidence_refs = sorted({eid for row in rows for eid in _ensure_list(row.get("evidence_refs")) if _safe_str(eid)})
            confidences = [_safe_float(row.get("contract_confidence"), 0.0) for row in rows]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            if miss_count > hit_count and avg_confidence >= 0.7:
                confidence_trend = "overconfident"
            elif hit_count > miss_count + partial_count:
                confidence_trend = "stable_positive"
            elif partial_count or miss_count:
                confidence_trend = "needs_review"
            else:
                confidence_trend = "neutral"
            pattern = self._dominant_failure_pattern(rows, miss_count=miss_count, partial_count=partial_count)
            suggested_action = self._suggested_action_for_insight(
                related_rule_ids=related_rule_ids,
                hit_count=hit_count,
                miss_count=miss_count,
                partial_count=partial_count,
                pattern=pattern,
            )
            digest = _payload_hash(
                {
                    "key": key,
                    "signals": sorted(_safe_str((row.get("signal") or {}).get("signal_id")) for row in rows),
                    "evidence_refs": evidence_refs,
                }
            ).split(":", 1)[-1][:16]
            insight = AggregatedInsight(
                insight_id=f"insight_{digest}",
                related_rule_ids=related_rule_ids,
                related_conclusions=related_conclusions,
                signal_count=signal_count,
                hit_count=hit_count,
                miss_count=miss_count,
                partial_count=partial_count,
                dominant_failure_pattern=pattern,
                confidence_trend=confidence_trend,
                suggested_action=suggested_action,
                evidence_refs=evidence_refs,
            ).to_dict()
            insight["source_signal_ids"] = sorted(_safe_str((row.get("signal") or {}).get("signal_id")) for row in rows)
            insight["source_prediction_ids"] = sorted(_safe_str(row.get("prediction_id")) for row in rows)
            insights[insight["insight_id"]] = insight
        self._learning_insights = insights
        self.invalidate_cache("cache:learning_insights")
        self._persist()
        return {"items": sorted(insights.values(), key=lambda item: _parse_dt(item.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True), "total": len(insights)}

    def get_learning_insight(self, insight_id: str) -> Dict[str, Any]:
        if not self._learning_insights:
            self.aggregate_learning_insights()
        insight_id = _safe_str(insight_id)
        insight = self._learning_insights.get(insight_id)
        if not insight:
            raise PredictiveServiceError("LEARNING_INSIGHT_NOT_FOUND", f"learning insight {insight_id} not found", 404)
        return dict(insight)

    def _suggestion_for_insight(self, insight: Dict[str, Any]) -> Dict[str, Any]:
        action = _safe_str(insight.get("suggested_action"), "no_change")
        risk_level = "low" if action == "no_change" else "medium"
        if action in {"deprecate_rule", "split_rule", "create_new_rule"}:
            risk_level = "high"
        diff = {
            "action": action,
            "target_rule_ids": _ensure_list(insight.get("related_rule_ids")),
            "target_conclusions": _ensure_list(insight.get("related_conclusions")),
            "dominant_failure_pattern": _safe_str(insight.get("dominant_failure_pattern")),
            "proposed_change": {
                "adjust_confidence": "lower confidence or widen uncertainty when the same pattern appears",
                "refine_condition": "add chart/evidence condition guardrails before firing this rule",
                "split_rule": "split broad condition into narrower sub-rules by chart pattern",
                "deprecate_rule": "consider deprecating after reviewer confirms repeated misses",
                "create_new_rule": "draft a new sandbox rule candidate from unmapped feedback evidence",
                "no_change": "keep current rule behavior and continue observing",
            }.get(action, "manual review required"),
        }
        digest = _payload_hash({"insight_id": insight.get("insight_id"), "diff": diff}).split(":", 1)[-1][:16]
        expected = "reduce repeated miss/partial feedback while preserving contract evidence trace"
        if action == "no_change":
            expected = "no immediate rule change; continue collecting feedback"
        return CandidateRuleSuggestion(
            suggestion_id=f"suggestion_{digest}",
            based_on_insight_id=_safe_str(insight.get("insight_id")),
            suggested_rule_diff=diff,
            risk_level=risk_level,
            expected_improvement=expected,
            requires_human_review=True,
        ).to_dict()

    def query_learning_insights(self) -> Dict[str, Any]:
        return self.aggregate_learning_insights()

    def query_candidate_rule_suggestions(self) -> Dict[str, Any]:
        insights = self.aggregate_learning_insights()["items"]
        suggestions = {
            suggestion["suggestion_id"]: suggestion
            for suggestion in (self._suggestion_for_insight(insight) for insight in insights)
            if suggestion.get("based_on_insight_id")
        }
        self._candidate_rule_suggestions = suggestions
        self.invalidate_cache("cache:learning_suggestions")
        self._persist()
        return {"items": list(suggestions.values()), "total": len(suggestions)}

    def create_knowledge_card_from_suggestion(
        self,
        suggestion_id: str,
        payload: Dict[str, Any],
        *,
        actor_role: str = "system",
        actor_user_id: int = 0,
    ) -> Dict[str, Any]:
        if not self._candidate_rule_suggestions:
            self.query_candidate_rule_suggestions()
        suggestion = self._candidate_rule_suggestions.get(_safe_str(suggestion_id))
        if not suggestion:
            raise PredictiveServiceError("RULE_SUGGESTION_NOT_FOUND", f"suggestion {suggestion_id} not found", 404)
        card_payload = {
            "card_id": _safe_str(payload.get("card_id"), f"kc_from_{suggestion_id}"),
            "knowledge_domain": _safe_str(payload.get("knowledge_domain"), "rule_learning"),
            "title": _safe_str(payload.get("title"), f"Learning suggestion {suggestion_id}"),
            "summary": _safe_str(payload.get("summary"), "Knowledge card drafted from a candidate rule suggestion."),
            "status": "draft",
            "version": _safe_str(payload.get("version"), "v1"),
            "source_refs": [suggestion_id, _safe_str(suggestion.get("based_on_insight_id"))],
            "tags": _ensure_list(payload.get("tags")) or ["learning_suggestion"],
            "content": {"candidate_rule_suggestion": suggestion, "sandbox_required": True},
        }
        return self.register_knowledge_card(card_payload, actor_role=actor_role, actor_user_id=actor_user_id)

    def _quality_subjects(self) -> Dict[str, Dict[str, Any]]:
        subjects: Dict[str, Dict[str, Any]] = {}
        for key, rule in self._rule_kernels.items():
            rid, version = _split_rule_key(key)
            subjects[_rule_storage_key(rid, version)] = {
                "rule_id": rule.rule_id,
                "version": rule.version,
                "rule_state": rule.status,
                "evidence_refs": [],
            }
        for candidate in self._rule_candidates.values():
            payload = dict(candidate.get("rule_payload") or {})
            rid = _safe_str(payload.get("rule_id"))
            version = _safe_str(payload.get("version"))
            if not rid or not version:
                continue
            subjects.setdefault(
                _rule_storage_key(rid, version),
                {
                    "rule_id": rid,
                    "version": version,
                    "rule_state": "candidate",
                    "evidence_refs": [],
                },
            )
        return subjects

    def _verifier_failures_by_rule(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for prediction_id, runs in self._verifier_runs.items():
            if not any(_safe_str(run.get("result")) == "fail" for run in runs if isinstance(run, dict)):
                continue
            contract = dict((self._ledger.get(prediction_id) or {}).get("contract") or {})
            for evidence in _ensure_list(contract.get("rule_evidence")):
                if not isinstance(evidence, dict):
                    continue
                key = _rule_storage_key(_safe_str(evidence.get("rule_id")), _safe_str(evidence.get("version")))
                counts[key] = counts.get(key, 0) + 1
        return counts

    def _feedback_stats_by_rule(self) -> Dict[str, Dict[str, Any]]:
        stats: Dict[str, Dict[str, Any]] = {}
        for prediction_id, feedback_rows in self._feedback_events.items():
            ledger = self._ledger.get(prediction_id)
            if not isinstance(ledger, dict):
                continue
            contract = dict(ledger.get("contract") or {})
            evidence_by_id = {
                _safe_str(item.get("evidence_id")): dict(item)
                for item in _ensure_list(contract.get("rule_evidence"))
                if isinstance(item, dict) and _safe_str(item.get("evidence_id"))
            }
            conclusion_by_id = {
                _safe_str(item.get("conclusion_id")): dict(item)
                for item in _ensure_list(contract.get("conclusions"))
                if isinstance(item, dict) and _safe_str(item.get("conclusion_id"))
            }
            for feedback in feedback_rows:
                if not isinstance(feedback, dict) or not _safe_str(feedback.get("feedback_id")):
                    continue
                feedback_type = _safe_str(feedback.get("feedback_type")).lower()
                conclusion_ref = _safe_str(feedback.get("conclusion_ref") or feedback.get("conclusion_id"))
                evidence_refs = []
                if conclusion_ref in conclusion_by_id:
                    evidence_refs = [_safe_str(item) for item in _ensure_list(conclusion_by_id[conclusion_ref].get("evidence_ids")) if _safe_str(item)]
                if not evidence_refs:
                    evidence_refs = [_safe_str(item) for item in _ensure_list(contract.get("evidence_ids")) if _safe_str(item)]
                rule_keys = {
                    _rule_storage_key(_safe_str(evidence_by_id.get(eid, {}).get("rule_id")), _safe_str(evidence_by_id.get(eid, {}).get("version")))
                    for eid in evidence_refs
                    if _safe_str(evidence_by_id.get(eid, {}).get("rule_id")) and _safe_str(evidence_by_id.get(eid, {}).get("version"))
                }
                for key in rule_keys:
                    item = stats.setdefault(key, {"sample_count": 0, "hit": 0, "miss": 0, "partial": 0, "evidence_refs": []})
                    item["sample_count"] += 1
                    if feedback_type in {"hit", "miss", "partial"}:
                        item[feedback_type] += 1
                    item["evidence_refs"].append(_safe_str(feedback.get("feedback_id")))
                    item["evidence_refs"].extend(evidence_refs)
        return stats

    def _test_stats_by_rule(self) -> Dict[str, Dict[str, Any]]:
        stats: Dict[str, Dict[str, Any]] = {}
        for run in self._rule_test_runs.values():
            if not isinstance(run, dict):
                continue
            key = _rule_storage_key(_safe_str(run.get("rule_id")), _safe_str(run.get("version")))
            if key == "::":
                continue
            item = stats.setdefault(key, {"runs": 0, "pass_runs": 0, "fail_runs": 0, "warning_runs": 0, "evidence_refs": []})
            item["runs"] += 1
            status = _safe_str(run.get("overall_status"))
            if status == "pass":
                item["pass_runs"] += 1
            elif status == "fail":
                item["fail_runs"] += 1
            elif status == "warning":
                item["warning_runs"] += 1
            item["evidence_refs"].append(_safe_str(run.get("run_id")))
        return stats

    def _insight_stats_by_rule(self) -> Dict[str, Dict[str, Any]]:
        insights = self.aggregate_learning_insights()["items"]
        stats: Dict[str, Dict[str, Any]] = {}
        for insight in insights:
            for rid in [_safe_str(item) for item in _ensure_list(insight.get("related_rule_ids")) if _safe_str(item)]:
                versions = self._list_rule_versions(rid) or [""]
                for version in versions:
                    key = _rule_storage_key(rid, version)
                    item = stats.setdefault(key, {"risk_patterns": 0, "drift": 0, "evidence_refs": []})
                    if _safe_str(insight.get("dominant_failure_pattern")) in {"high_confidence_miss", "high_uncertainty_evidence"} or _safe_str(insight.get("dominant_failure_pattern")).startswith(("miss_chart:", "partial_condition:")):
                        item["risk_patterns"] += 1
                    if _safe_str(insight.get("confidence_trend")) in {"overconfident", "needs_review"}:
                        item["drift"] += 1
                    item["evidence_refs"].append(_safe_str(insight.get("insight_id")))
                    item["evidence_refs"].extend([_safe_str(ref) for ref in _ensure_list(insight.get("evidence_refs")) if _safe_str(ref)])
        return stats

    def recompute_rule_quality_scores(self) -> Dict[str, Any]:
        subjects = self._quality_subjects()
        feedback_stats = self._feedback_stats_by_rule()
        test_stats = self._test_stats_by_rule()
        insight_stats = self._insight_stats_by_rule()
        verifier_failures = self._verifier_failures_by_rule()
        scores: Dict[str, Dict[str, Any]] = {}

        for key, subject in subjects.items():
            fb = feedback_stats.get(key, {})
            tests = test_stats.get(key, {})
            insights = insight_stats.get(key, {})
            sample_count = _safe_int(fb.get("sample_count"), 0)
            hit_count = _safe_int(fb.get("hit"), 0)
            miss_count = _safe_int(fb.get("miss"), 0)
            partial_count = _safe_int(fb.get("partial"), 0)
            test_runs = _safe_int(tests.get("runs"), 0)
            test_pass_rate = _safe_float(_safe_int(tests.get("pass_runs"), 0) / test_runs, 0.0) if test_runs else 0.0
            verifier_failure_count = _safe_int(verifier_failures.get(key), 0)
            drift_warning_count = _safe_int(insights.get("drift"), 0)
            risk_patterns = _safe_int(insights.get("risk_patterns"), 0)
            confidence_calibration = "insufficient_data" if sample_count < 3 else "calibrated"
            if miss_count > hit_count and sample_count >= 3:
                confidence_calibration = "overconfident"
            elif hit_count >= miss_count + partial_count and sample_count >= 3:
                confidence_calibration = "stable"
            risk_score = min(
                1.0,
                miss_count * 0.18
                + partial_count * 0.08
                + verifier_failure_count * 0.35
                + drift_warning_count * 0.12
                + risk_patterns * 0.12
                + _safe_int(tests.get("fail_runs"), 0) * 0.25,
            )
            positive = hit_count * 0.14 + test_pass_rate * 0.32
            penalty = miss_count * 0.12 + partial_count * 0.05 + verifier_failure_count * 0.28 + drift_warning_count * 0.08 + _safe_int(tests.get("fail_runs"), 0) * 0.18
            quality_score = max(0.0, min(1.0, 0.45 + positive - penalty))
            if verifier_failure_count or risk_score >= 0.72:
                recommended_action = "review"
            elif sample_count < 3 and test_runs == 0:
                recommended_action = "monitor"
            elif subject.get("rule_state") == "candidate" and quality_score >= 0.72 and test_pass_rate >= 0.8:
                recommended_action = "promote_review"
            elif subject.get("rule_state") == "candidate" and quality_score < 0.35:
                recommended_action = "deprecate_candidate"
            elif confidence_calibration == "overconfident":
                recommended_action = "reduce_confidence"
            elif risk_score >= 0.45:
                recommended_action = "review"
            else:
                recommended_action = "keep"
            evidence_refs = sorted(
                {
                    _safe_str(ref)
                    for ref in (
                        _ensure_list(fb.get("evidence_refs"))
                        + _ensure_list(tests.get("evidence_refs"))
                        + _ensure_list(insights.get("evidence_refs"))
                    )
                    if _safe_str(ref)
                }
            )
            digest = _payload_hash(
                {
                    "rule_id": subject["rule_id"],
                    "version": subject["version"],
                    "sample_count": sample_count,
                    "hit": hit_count,
                    "miss": miss_count,
                    "partial": partial_count,
                    "test_pass_rate": round(test_pass_rate, 4),
                    "verifier_failure_count": verifier_failure_count,
                    "drift_warning_count": drift_warning_count,
                }
            ).split(":", 1)[-1][:16]
            score = RuleQualityScore(
                score_id=f"rqs_{digest}",
                rule_id=subject["rule_id"],
                version=subject["version"],
                rule_state=_safe_str(subject.get("rule_state"), "unknown"),
                sample_count=sample_count,
                hit_count=hit_count,
                miss_count=miss_count,
                partial_count=partial_count,
                test_pass_rate=round(test_pass_rate, 3),
                verifier_failure_count=verifier_failure_count,
                drift_warning_count=drift_warning_count,
                confidence_calibration=confidence_calibration,
                risk_score=round(risk_score, 3),
                quality_score=round(quality_score, 3),
                recommended_action=recommended_action,
                evidence_refs=evidence_refs,
            ).to_dict()
            scores[key] = score
        self._rule_quality_scores = scores
        self._persist()
        ordered = sorted(scores.values(), key=lambda item: (_safe_float(item.get("quality_score")), -_safe_float(item.get("risk_score"))), reverse=True)
        return {"items": ordered, "total": len(ordered)}

    def query_rule_quality_scores(self) -> Dict[str, Any]:
        cached = self._redis.get_json("cache:rule_quality_scores")
        if cached:
            return cached
        result = self.recompute_rule_quality_scores()
        self._redis.set_json("cache:rule_quality_scores", result, ttl_seconds=300)
        return result

    def get_rule_quality_score(self, rule_id: str, version: str | None = None) -> Dict[str, Any]:
        scores = self.recompute_rule_quality_scores()["items"]
        matches = [
            item for item in scores
            if _safe_str(item.get("rule_id")) == _safe_str(rule_id)
            and (not version or _safe_str(item.get("version")) == _safe_str(version))
        ]
        if not matches:
            raise PredictiveServiceError("RULE_QUALITY_SCORE_NOT_FOUND", f"quality score for {rule_id} not found", 404)
        return sorted(matches, key=lambda item: _parse_dt(item.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)[0]

    def append_knowledge_pr(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prediction_id = str(payload.get("prediction_id") or payload.get("source_prediction_id") or "").strip()
        proposed = payload.get("proposed_rule_payload") if isinstance(payload.get("proposed_rule_payload"), dict) else {}
        rule_candidate_id = _safe_str(payload.get("rule_candidate_id"))
        if rule_candidate_id:
            candidate = self._rule_candidates.get(rule_candidate_id)
            if not candidate:
                raise PredictiveServiceError("RULE_CANDIDATE_NOT_FOUND", f"rule candidate {rule_candidate_id} not found", 404)
            proposed = dict(candidate.get("rule_payload") or {})
        if not proposed and isinstance(payload.get("rule_candidate"), dict):
            raw_candidate = payload.get("rule_candidate") or {}
            if raw_candidate.get("candidate_id") and isinstance(raw_candidate.get("rule_payload"), dict):
                rule_candidate_id = _safe_str(raw_candidate.get("candidate_id"))
                proposed = dict(raw_candidate.get("rule_payload") or {})
                self._rule_candidates.setdefault(rule_candidate_id, dict(raw_candidate))
            else:
                sandbox = self.build_sandbox_rule_candidate(
                    payload,
                    actor_role=_safe_str(payload.get("requested_by"), "system"),
                    actor_user_id=_safe_int(payload.get("requested_by_user_id"), 0),
                )
                rule_candidate_id = _safe_str(sandbox.get("candidate_id"))
                proposed = dict(sandbox.get("rule_payload") or {})
        rule_id = str(payload.get("rule_id") or proposed.get("rule_id") or "").strip()
        if not prediction_id and not rule_id:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "prediction_id or rule_candidate required")
        if not rule_id:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "rule_id required")
        pr_id = f"pr_{prediction_id}_{_safe_int(len(self._knowledge_pr) + 1)}"
        pr = {
            "pr_id": pr_id,
            "prediction_id": prediction_id,
            "rule_id": rule_id,
            "rule_version": _safe_str(payload.get("rule_version") or proposed.get("version")),
            "knowledge_card_id": _safe_str(payload.get("knowledge_card_id") or proposed.get("knowledge_card_id")),
            "change_type": str(payload.get("change_type", "rule_modify")),
            "requested_by": str(payload.get("requested_by", "system")),
            "target_status": _safe_str(payload.get("target_status") or proposed.get("status"), "experimental"),
            "proposed_rule_payload": proposed,
            "rule_candidate_id": rule_candidate_id,
            "evidence_packet": _as_dict(payload, ["evidence_packet"], required=False) or {},
            "created_at": _utcnow_iso(),
            "review_state": "pending_manual_review",
            "candidate_state": "sandbox" if proposed else "",
        }
        self._knowledge_pr[pr_id] = pr
        self._persist()
        return pr

    def query_knowledge_pr_queue(
        self,
        *,
        review_state: str | None = None,
        rule_id: str | None = None,
        knowledge_card_id: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        items = list(self._knowledge_pr.values())
        if review_state:
            items = [item for item in items if _safe_str(item.get("review_state")) == _safe_str(review_state)]
        if rule_id:
            items = [item for item in items if _safe_str(item.get("rule_id")) == _safe_str(rule_id)]
        if knowledge_card_id:
            items = [item for item in items if _safe_str(item.get("knowledge_card_id")) == _safe_str(knowledge_card_id)]
        score_by_key = {
            _rule_storage_key(_safe_str(score.get("rule_id")), _safe_str(score.get("version"))): score
            for score in self.recompute_rule_quality_scores()["items"]
        }
        enriched_items: List[Dict[str, Any]] = []
        for item in items:
            next_item = dict(item)
            score = score_by_key.get(_rule_storage_key(_safe_str(next_item.get("rule_id")), _safe_str(next_item.get("rule_version"))), {})
            quality_score = _safe_float(score.get("quality_score"), 0.0)
            risk_score = _safe_float(score.get("risk_score"), 0.0)
            recommended_action = _safe_str(score.get("recommended_action"), "monitor")
            if recommended_action in {"review", "reduce_confidence", "deprecate_candidate"} or risk_score >= 0.6:
                review_priority = "high"
            elif recommended_action == "promote_review" or risk_score >= 0.35 or quality_score >= 0.7:
                review_priority = "medium"
            else:
                review_priority = "low"
            next_item["quality_score"] = quality_score
            next_item["risk_score"] = risk_score
            next_item["recommended_action"] = recommended_action
            next_item["review_priority"] = review_priority
            enriched_items.append(next_item)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        items = sorted(
            enriched_items,
            key=lambda item: (
                priority_order.get(_safe_str(item.get("review_priority")), 9),
                -_safe_float(item.get("risk_score"), 0.0),
                -_safe_float(item.get("quality_score"), 0.0),
                -(_parse_dt(item.get("created_at")) or datetime.min.replace(tzinfo=timezone.utc)).timestamp(),
            ),
        )
        start = max(0, _safe_int(offset, 0))
        size = max(1, min(_safe_int(limit, 100), 500))
        return {
            "items": items[start : start + size],
            "total_matched": len(items),
            "total_returned": len(items[start : start + size]),
            "offset": start,
            "limit": size,
        }


class RuleRuntimeFacade:
    def __init__(self, service: V18PredictiveStore) -> None:
        self.service = service

    def _issue(self, *, actor_role: str, actor_user_id: int, purpose: str) -> str:
        return self.service.issue_lifecycle_token(
            actor_role=actor_role,
            actor_user_id=actor_user_id,
            purpose=purpose,
            issuer="runtime_facade",
        )

    def run_rule_retrieval(self, payload: Dict[str, Any], actor_role: str, actor_user_id: int) -> List[RuleKernel]:
        payload = dict(payload)
        token = self._issue(actor_role=actor_role, actor_user_id=actor_user_id, purpose="retrieval")
        payload["execution_mode"] = "retrieval"
        payload["lifecycle_token"] = token
        return self.service.retrieve_rules(
            prediction_id=_safe_str(payload.get("prediction_id")),
            topic=_safe_str(payload.get("topic")),
            plugin_claims=_ensure_list(payload.get("plugin_claims")),
            actor_role=actor_role,
            actor_user_id=actor_user_id,
            execution_mode="retrieval",
            lifecycle_token=token,
        )

    def run_resolver(self, payload: Dict[str, Any], actor_role: str, actor_user_id: int) -> Dict[str, Any]:
        payload = dict(payload)
        payload["actor_role"] = actor_role
        payload["actor_user_id"] = actor_user_id
        payload["lifecycle_token"] = self._issue(actor_role=actor_role, actor_user_id=actor_user_id, purpose="runtime")
        payload["execution_mode"] = "runtime"
        payload["allow_sandbox"] = False
        return self.service.resolve_rules(payload)

    def run_rule_test(self, payload: Dict[str, Any], actor_role: str, actor_user_id: int) -> Dict[str, Any]:
        payload = dict(payload)
        payload["lifecycle_token"] = self._issue(actor_role=actor_role, actor_user_id=actor_user_id, purpose="test")
        payload["execution_mode"] = "test"
        payload.setdefault("actor_role", actor_role)
        payload.setdefault("actor_user_id", actor_user_id)
        return self.service.run_rule_test_v0(payload)

    def run_rule_test_v02(self, payload: Dict[str, Any], actor_role: str, actor_user_id: int) -> Dict[str, Any]:
        payload = dict(payload)
        payload["lifecycle_token"] = self._issue(actor_role=actor_role, actor_user_id=actor_user_id, purpose="test")
        payload["execution_mode"] = "test"
        payload.setdefault("actor_role", actor_role)
        payload.setdefault("actor_user_id", actor_user_id)
        return self.service.run_rule_test_v02(payload)

    def run_shadow_compare(self, payload: Dict[str, Any], actor_role: str, actor_user_id: int) -> Dict[str, Any]:
        payload = dict(payload)
        payload["lifecycle_token"] = self._issue(actor_role=actor_role, actor_user_id=actor_user_id, purpose="debug")
        payload["execution_mode"] = "debug"
        return self.service.run_shadow_compare(payload)

    def run_wealth_pilot(self, payload: Dict[str, Any], actor_role: str, actor_user_id: int) -> Dict[str, Any]:
        now = str(int(_safe_int(datetime.now(timezone.utc).timestamp()) * 1000))
        prediction_id = _safe_str(payload.get("prediction_id"), f"pred_20260427_{now}")
        topic = _safe_str(payload.get("topic"), "wealth")
        chain_id = _safe_str(payload.get("chain_id"), "wealth_flowline_v1")
        period = payload.get("period") or {"type": "year", "start_at": "2026-01-01", "end_at": "2026-12-31", "timezone": "Asia/Seoul"}

        runtime_context = dict(payload.get("runtime_context") or {})
        runtime_context.setdefault(
            "time_weight",
            {"natal": 0.5, "decade": 0.3, "year": 0.2},
        )

        token = self._issue(actor_role=actor_role, actor_user_id=actor_user_id, purpose="pilot")
        plugin_claims = _ensure_list(payload.get("plugin_claims"))
        if not plugin_claims:
            self.service._append_audit_event(
                rule_id="",
                event_type="GATEKEEPER_MISSING",
                severity="high",
                message="plugin claims required",
                actor_role=actor_role,
                actor_user_id=actor_user_id,
                source="rule-runtime",
                details={"execution_mode": "pilot", "prediction_id": prediction_id},
            )
            raise PredictiveServiceError("GATEKEEPER_MISSING", "plugin claims required", 403)

        rule_candidates = _ensure_list(payload.get("rule_candidates"))
        if not rule_candidates:
            raise PredictiveServiceError(
                "RULE_CANDIDATES_REQUIRED",
                "wealth pilot requires explicit rule_candidates",
                409,
            )

        resolver_input = {
            "prediction_id": prediction_id,
            "topic": topic,
            "plugin_claims": plugin_claims,
            "rule_candidates": rule_candidates,
            "runtime_context": runtime_context,
            "lifecycle_token": token,
            "allow_sandbox": True,
            "execution_mode": "pilot",
            "target_version": "",
        }
        resolver_data = self.service.resolve_rules(resolver_input)

        contract_payload = dict(payload.get("contract_payload") or {})
        contract_payload.setdefault("prediction_id", prediction_id)
        contract_payload.setdefault("topic", topic)
        contract_payload.setdefault("chain_id", chain_id)
        contract_payload.setdefault("causal_path", payload.get("causal_path") or ["output_energy", "conversion_efficiency", "wealth_retention"])
        contract_payload.setdefault("rule_ids", resolver_data.get("active_rules", []))
        contract_payload.setdefault("chain_state", "partial")
        contract_payload.setdefault("confidence", _safe_float(payload.get("confidence"), 0.72))
        contract_payload.setdefault(
            "period",
            period,
        )
        contract_payload.setdefault("evidence_ids", ["ev_default_wealth"])
        contract_payload.setdefault(
            "verifiable_indicators",
            {
                "outcome": ["monthly_revenue", "net_cashflow", "contract_value"],
                "process": ["lead_conversion_rate", "customer_acquisition", "pricing_power"],
                "risk": ["cashflow_gap", "cost_spike", "client_loss", "policy_change"],
                "mechanism": ["output_energy", "conversion_efficiency", "wealth_retention"],
            },
        )
        contract_payload.setdefault("risk_modes", ["timing_gap", "liquidity_pressure"])
        contract_payload.setdefault("data_sources", ["bazi_chart_v18", "finance_metrics_v1"])
        contract_payload.setdefault("model_version", "v18.1")
        contract_payload.setdefault("schema_version", "v18.1")
        contract_payload.setdefault(
            "display_policy",
            {
                "allow_llm_expression": True,
                "max_abs_language_level": "low",
                "require_evidence_tags": True,
            },
        )
        contract_payload.setdefault(
            "uncertainty",
            {"source": ["rule_conflict", "low_evidence_strength"], "score": 0.28},
        )
        contract_payload.setdefault("resolver_snapshot", resolver_data.get("resolver_snapshot", {}))

        contract = self.service.build_contract(contract_payload, resolved_rules=resolver_data)
        record = self.service.write_ledger_record({"prediction_id": prediction_id}, contract.to_dict())

        llm_output = dict(payload.get("llm_output") or {})
        if not llm_output:
            contract_text = (
                "结论：财富趋势处于可观测提升窗口。\n"
                f"证据：{','.join(_ensure_list(contract_payload.get('evidence_ids')))}\n"
                f"机制：{' > '.join(_ensure_list(contract_payload.get('causal_path')))}\n"
                "风险：流动性压力与成本波动仍需关注。\n"
                "建议：优先抓住现金流可验证节点并观察订单转化。"
            )
            llm_output = {
                "text": contract_text,
                "sections": {
                    "conclusion": "财富窗口处于阶段性偏强。",
                    "evidence": _ensure_list(contract_payload.get("evidence_ids")),
                    "causal": _ensure_list(contract_payload.get("causal_path")),
                    "risk": _ensure_list(contract_payload.get("risk_modes")),
                    "suggestion": "先做轻量验证后再扩张。",
                },
                "sources": ["bazi_chart_v18", "finance_metrics_v1"],
            }

        verifier_result = self.service.run_verifier(
            {
                "prediction_id": prediction_id,
                "contract": contract.to_dict(),
                "llm_output": llm_output,
                "ledger_snapshot": record.prediction_hash,
            }
        )

        feedback_input = dict(payload.get("feedback") or {})
        feedback_result = None
        if feedback_input:
            feedback_payload = {
                "prediction_id": prediction_id,
                "feedback_type": feedback_input.get("feedback_type", "system"),
                "outcome": feedback_input.get("outcome", "collecting"),
                "evidence_of_outcome": _ensure_list(feedback_input.get("evidence_of_outcome")),
                "notes": _safe_str(feedback_input.get("notes"), ""),
                "observed_at": _safe_str(feedback_input.get("observed_at"), ""),
            }
            feedback_result = self.service.append_feedback(feedback_payload)

        ledger = self.service.get_ledger(prediction_id)
        return {
            "prediction_id": prediction_id,
            "contract": contract.to_dict(),
            "resolver_output": resolver_data,
            "ledger": {
                "state": ledger.get("state"),
                "prediction_hash": ledger.get("prediction_hash"),
                "schema_version": ledger.get("schema_version"),
                "feedback_state": ledger.get("feedback_state"),
            },
            "verifier": verifier_result,
            "feedback": feedback_result,
        }

    def run_prediction_contract_pipeline(self, payload: Dict[str, Any], actor_role: str, actor_user_id: int) -> Dict[str, Any]:
        request_id = _safe_str(payload.get("request_id"))
        if request_id:
            cached = self.service._redis.idempotency_get(f"contract_pipeline:{request_id}")
            if cached:
                return cached
        lock_key = f"lock:contract_pipeline:{request_id or _safe_str(payload.get('prediction_id'))}"
        if not self.service._redis.acquire_lock(lock_key, ttl_seconds=30):
            raise PredictiveServiceError("LOCK_BUSY", "contract pipeline request is already in progress", 409)
        try:
            result = self._run_prediction_contract_pipeline_locked(payload, actor_role, actor_user_id)
            if request_id:
                self.service._redis.idempotency_set(f"contract_pipeline:{request_id}", result)
            return result
        finally:
            self.service._redis.release_lock(lock_key)

    def _run_prediction_contract_pipeline_locked(self, payload: Dict[str, Any], actor_role: str, actor_user_id: int) -> Dict[str, Any]:
        prediction_id = _safe_str(payload.get("prediction_id"), f"pred_{_safe_int(datetime.now(timezone.utc).timestamp())}")
        user_query = _safe_str(payload.get("user_query") or payload.get("query"), "")
        topic = _normalize_topic(payload.get("topic") or payload.get("topic_hint") or user_query)
        debug = _safe_bool(payload.get("debug"), False)
        plugin_claims = _ensure_list(payload.get("plugin_claims"))
        if not plugin_claims:
            raise PredictiveServiceError("GATEKEEPER_MISSING", "plugin claims required", 403)

        normalized_intent = {
            "topic": topic,
            "user_query": user_query,
            "intent": _safe_str(payload.get("intent"), "prediction"),
        }
        chart_snapshot = dict(payload.get("chart_snapshot") or {})
        chart_snapshot.setdefault("matched_facts", _ensure_list(payload.get("matched_facts")))
        chart_snapshot.setdefault("topic", topic)
        runtime_context = dict(payload.get("runtime_context") or {})
        runtime_context.setdefault("time_weight", {"natal": 0.5, "decade": 0.3, "year": 0.2})
        wealth_domain_bundle: Dict[str, Any] = {}

        rule_candidates = _ensure_list(payload.get("rule_candidates"))
        if not rule_candidates:
            retrieved = self.run_rule_retrieval(
                {
                    "prediction_id": prediction_id,
                    "topic": topic,
                    "plugin_claims": plugin_claims,
                },
                actor_role,
                actor_user_id,
            )
            rule_candidates = [
                {"rule_id": rule.rule_id, "version": rule.version, "activation_score": 1.0}
                for rule in retrieved
            ]
        if not rule_candidates:
            raise PredictiveServiceError("RULE_SCOPE_VIOLATION", "No rule candidates", 409)

        resolved = self.run_resolver(
            {
                "prediction_id": prediction_id,
                "topic": topic,
                "plugin_claims": plugin_claims,
                "rule_candidates": rule_candidates,
                "runtime_context": runtime_context,
            },
            actor_role,
            actor_user_id,
        )
        if topic == "wealth":
            try:
                from v17_rebirth.backend.services.core_bazi_feature_layer import core_bazi_feature_service
                from v17_rebirth.backend.services.core_bazi_strength_model import core_bazi_strength_service
                from v17_rebirth.backend.services.core_bazi_structure_effect_layer import core_bazi_structure_effect_service
                from v17_rebirth.backend.services.core_bazi_wealth_domain import wealth_domain_service

                core_bundle = core_bazi_feature_service.extract_and_store({"chart_snapshot": chart_snapshot})
                strength_bundle = core_bazi_strength_service.evaluate_and_store({"core_feature_bundle": core_bundle})
                structure_bundle = core_bazi_structure_effect_service.evaluate_and_store(
                    {"core_feature_bundle": core_bundle, "core_strength_bundle": strength_bundle}
                )
                intent = _safe_str(payload.get("intent"), "wealth_prediction")
                if intent == "prediction":
                    intent = "wealth_prediction"
                wealth_domain_bundle = wealth_domain_service.evaluate_and_store(
                    {
                        "core_feature_bundle": core_bundle,
                        "core_strength_bundle": strength_bundle,
                        "structure_effect_bundle": structure_bundle,
                        "user_intent": intent,
                        "knowledge_mode": _safe_str(payload.get("knowledge_mode"), "baseline_only"),
                    }
                )
                chart_snapshot["core_feature_bundle_id"] = core_bundle.get("bundle_id")
                chart_snapshot["core_strength_bundle_id"] = strength_bundle.get("strength_bundle_id")
                chart_snapshot["core_structure_bundle_id"] = structure_bundle.get("structure_bundle_id")
                chart_snapshot["wealth_domain_bundle_id"] = wealth_domain_bundle.get("wealth_bundle_id")
                chart_snapshot["wealth_domain_bundle"] = wealth_domain_bundle
                chart_snapshot["wealth_features"] = _ensure_list(wealth_domain_bundle.get("wealth_evidence"))
                chart_snapshot["wealth_domain_knowledge_mode"] = _safe_str(wealth_domain_bundle.get("knowledge_mode"), "baseline_only")
                chart_snapshot["wealth_domain_experimental"] = _safe_bool(wealth_domain_bundle.get("experimental"), False)
            except PredictiveServiceError as exc:
                chart_snapshot["wealth_domain_status"] = "fallback_legacy_wealth_features"
                chart_snapshot["wealth_domain_error_code"] = exc.code
        rule_evidence = self.service._rule_evidence_from_resolver(resolved, chart_snapshot=chart_snapshot)
        conclusions = self.service._conclusions_from_evidence(topic=topic, rule_evidence=rule_evidence)
        evidence_ids = [_safe_str(row.get("evidence_id")) for row in rule_evidence if _safe_str(row.get("evidence_id"))]
        period = dict(payload.get("period") or {})
        now_dt = datetime.now(timezone.utc)
        period.setdefault("start_at", now_dt.replace(microsecond=0).isoformat())
        period.setdefault("end_at", (now_dt + timedelta(days=180)).replace(microsecond=0).isoformat())

        contract_payload = {
            "prediction_id": prediction_id,
            "user_query": user_query,
            "normalized_intent": normalized_intent,
            "chart_snapshot": chart_snapshot,
            "topic": topic,
            "chain_id": _safe_str(payload.get("chain_id"), f"{topic}_contract_v1"),
            "causal_path": _ensure_list(payload.get("causal_path")) or (
                ["wealth_feature_extraction", "multi_rule_composition", "contract_conclusion"]
                if topic == "wealth"
                else ["rule_match", "effect_resolution", "contract_conclusion"]
            ),
            "rule_ids": resolved.get("active_rules", []),
            "chain_state": "resolved" if conclusions else "insufficient_evidence",
            "confidence": self.service._contract_confidence_from_evidence(rule_evidence),
            "period": period,
            "evidence_ids": evidence_ids,
            "rule_evidence": rule_evidence,
            "inference_steps": [
                {"step": "intent_normalized", "output": normalized_intent},
                {"step": "rules_resolved", "output": resolved.get("active_rules", [])},
                {"step": "wealth_domain_evaluated", "output": _safe_str(wealth_domain_bundle.get("wealth_bundle_id"))} if wealth_domain_bundle else {"step": "wealth_domain_evaluated", "output": "not_available"},
                {"step": "evidence_collected", "output": evidence_ids},
                {"step": "conclusions_generated", "output": [_safe_str(row.get("conclusion_id")) for row in conclusions]},
            ],
            "conclusions": conclusions,
            "verifiable_indicators": dict(payload.get("verifiable_indicators") or {"outcome": [topic]}),
            "risk_modes": _ensure_list(payload.get("risk_modes")) or self.service._risk_modes_from_evidence(rule_evidence),
            "data_sources": _ensure_list(payload.get("data_sources")) or (
                [
                    "prediction_contract_engine",
                    "core_bazi_feature_layer_v1",
                    "core_strength_model_v1",
                    "core_structure_effect_layer_v1",
                    "wealth_domain_v1",
                    "wealth_feature_engine_v1",
                ]
                if wealth_domain_bundle
                else ["prediction_contract_engine", "wealth_feature_engine_v1"] if topic == "wealth" else ["prediction_contract_engine"]
            ),
            "model_version": V18_1_SCHEMA_VERSION,
            "schema_version": V18_1_SCHEMA_VERSION,
            "engine_version": V18_1_SCHEMA_VERSION,
            "display_policy": {
                "allow_llm_expression": True,
                "contract_only": True,
            },
            "allowed_output_scope": {
                "conclusion_ids": [_safe_str(row.get("conclusion_id")) for row in conclusions],
                "evidence_ids": evidence_ids,
                "topic": topic,
            },
            "resolver_snapshot": resolved.get("resolver_snapshot", {}),
            "uncertainty": dict(payload.get("uncertainty") or wealth_domain_bundle.get("uncertainty") or self.service._uncertainty_from_evidence(rule_evidence, conclusions, chart_snapshot)),
            "feedback_window": _feedback_window_from_period(period),
        }

        contract = self.service.build_contract(contract_payload, resolved_rules=resolved)
        record = self.service.write_ledger_record({"prediction_id": prediction_id}, contract.to_dict())
        if conclusions:
            safe_text = "；".join(_safe_str(row.get("claim")) for row in conclusions if _safe_str(row.get("claim")))
        else:
            safe_text = "证据不足，不足以判断。"
        llm_output = {
            "text": safe_text,
            "sections": {
                "conclusion": [_safe_str(row.get("claim")) for row in conclusions],
                "conclusion_ids": [_safe_str(row.get("conclusion_id")) for row in conclusions],
                "evidence": evidence_ids,
                "causal": contract.causal_path,
                "risk": contract.risk_modes,
                "suggestion": [],
            },
            "sources": contract.data_sources,
            "conclusion_ids": [_safe_str(row.get("conclusion_id")) for row in conclusions],
        }
        if wealth_domain_bundle:
            llm_output["wealth_profile"] = dict(wealth_domain_bundle.get("wealth_profile") or {})
            llm_output["wealth_evidence_summary"] = [
                {
                    "feature_id": _safe_str(row.get("feature_id")),
                    "feature_type": _safe_str(row.get("feature_type")),
                    "feature_label": _safe_str(row.get("feature_label") or row.get("label")),
                    "risk": _safe_float(row.get("risk"), 0.0),
                    "stability": _safe_float(row.get("stability"), 0.0),
                }
                for row in _ensure_list(wealth_domain_bundle.get("wealth_evidence"))[:5]
                if isinstance(row, dict)
            ]
        verifier = self.service.run_verifier(
            {
                "prediction_id": prediction_id,
                "contract": contract.to_dict(),
                "llm_output": llm_output,
            }
        )
        response = {
            "prediction_id": prediction_id,
            "contract_id": f"contract_{prediction_id}",
            "prediction_hash": record.prediction_hash,
            "safe_output": llm_output if verifier.get("action") != "BLOCKED" else {"text": "证据不足，不足以判断。"},
            "verifier": verifier,
            "minimal_trace": {
                "rule_ids": contract.rule_ids,
                "evidence_count": len(contract.rule_evidence),
                "conclusion_count": len(contract.conclusions),
            },
        }
        if debug:
            response["contract"] = contract.to_dict()
            response["resolver_output"] = resolved
        return response

    def create_agent_session(self, payload: Dict[str, Any], actor_role: str, actor_user_id: int) -> Dict[str, Any]:
        session_id = _safe_str(payload.get("agent_session_id") or payload.get("session_id"), f"agent_{_safe_int(datetime.now(timezone.utc).timestamp())}_{len(self.service._agent_sessions) + 1}")
        session = {
            "agent_session_id": session_id,
            "actor_role": _safe_str(actor_role, "user"),
            "actor_user_id": _safe_int(actor_user_id, 0),
            "birth_payload": dict(payload.get("birth_payload") or {}),
            "chart_snapshot": dict(payload.get("chart_snapshot") or {}),
            "agent_turns": [],
            "created_at": _utcnow_iso(),
            "updated_at": _utcnow_iso(),
        }
        self.service._agent_sessions[session_id] = session
        self.service._persist()
        return session

    def get_agent_session(self, session_id: str) -> Dict[str, Any]:
        session = self.service._agent_sessions.get(_safe_str(session_id))
        if not session:
            raise PredictiveServiceError("AGENT_SESSION_NOT_FOUND", f"agent session {session_id} not found", 404)
        return dict(session)

    def _agent_missing_fields(self, session: Dict[str, Any], payload: Dict[str, Any]) -> List[str]:
        birth_payload = dict(payload.get("birth_payload") or session.get("birth_payload") or {})
        chart_snapshot = dict(payload.get("chart_snapshot") or session.get("chart_snapshot") or {})
        if chart_snapshot.get("matched_facts") or chart_snapshot.get("four_pillars"):
            return []
        missing = []
        for key in ("year", "month", "day", "hour"):
            if not birth_payload.get(key):
                missing.append(key)
        return missing

    def _agent_capability_boundary(self, user_message: str, topic: str, has_explicit_rule_candidates: bool = False) -> Dict[str, Any]:
        q = _safe_str(user_message).lower()
        normalized_topic = _normalize_topic(topic or user_message)
        wealth_terms = [
            "财",
            "钱",
            "收入",
            "现金",
            "财富",
            "财运",
            "投资",
            "创业",
            "变现",
            "回款",
            "赚钱",
            "wealth",
            "financial",
            "finance",
            "money",
            "income",
            "revenue",
            "cash",
            "investment",
            "salary",
            "startup",
            "재물",
            "재운",
            "돈",
            "수입",
            "소득",
            "투자",
            "현금",
        ]
        unsupported_terms = [
            "感情",
            "恋爱",
            "婚姻",
            "伴侣",
            "健康",
            "疾病",
            "家庭",
            "子女",
            "父母",
            "完整命盘",
            "命盘结构",
            "解析命盘",
            "八字格局",
            "十神",
            "用神",
            "relationships",
            "relationship",
            "love",
            "marriage",
            "health",
            "family",
            "full chart",
            "chart interpretation",
            "natal chart",
            "연애",
            "결혼",
            "관계",
            "건강",
            "가족",
            "전체 명식",
            "명식 해석",
            "사주 해석",
        ]
        has_wealth_scope = normalized_topic == "wealth" or any(term in q for term in wealth_terms)
        has_unsupported_scope = normalized_topic in {"relationship", "health"} or any(term in q for term in unsupported_terms)
        if has_wealth_scope and not has_unsupported_scope:
            if has_explicit_rule_candidates:
                return {}
            active_rules = self.service.list_rules(status="active")
            covers_wealth = any(
                "wealth" in [str(item).strip().lower() for item in (getattr(rule, "allowed_topics", []) or [])]
                or "wealth" in [str(item).strip().lower() for item in (getattr(rule, "effect_scope", []) or [])]
                for rule in active_rules
            )
            if not covers_wealth:
                return {
                    "type": "capability_boundary",
                    "is_prediction": False,
                    "capability_boundary": True,
                    "message": "财富预测规则尚未启用。当前不会生成预测；请稍后再试，或由管理员初始化财富预测规则。",
                    "supported_scopes": ["财运趋势", "收入稳定性", "财富机会与风险"],
                    "unsupported_scopes": ["未启用 active wealth rule 时不会预测", "命盘结构解析", "感情 / 婚姻", "健康 / 家庭"],
                    "suggested_queries": ["我这两年财运如何？", "收入是否稳定？", "有没有明显投资或现金流风险？"],
                    "detected_topic": normalized_topic,
                    "active_rule_required": True,
                    "next_action": "initialize_active_wealth_rule",
                }
            return {}
        return {
            "type": "capability_boundary",
            "is_prediction": False,
            "capability_boundary": True,
            "message": "这个问题目前不在系统的可验证规则范围内。当前我可以帮助你分析财运趋势、收入稳定性、财富机会与风险。",
            "supported_scopes": ["财运趋势", "收入稳定性", "财富机会与风险"],
            "unsupported_scopes": ["命盘结构解析", "感情 / 婚姻", "健康 / 家庭"],
            "suggested_queries": ["我这两年财运如何？", "收入是否稳定？", "有没有明显投资或现金流风险？"],
            "detected_topic": normalized_topic,
            "next_action": "ask_supported_wealth_question",
        }

    def append_agent_turn(self, session_id: str, payload: Dict[str, Any], actor_role: str, actor_user_id: int) -> Dict[str, Any]:
        session = self.get_agent_session(session_id)
        user_message = _safe_str(payload.get("user_message") or payload.get("query") or payload.get("user_query"))
        normalized_intent = {
            "topic": _normalize_topic(payload.get("topic") or payload.get("topic_hint") or user_message),
            "intent": _safe_str(payload.get("intent"), "prediction"),
            "user_query": user_message,
        }
        missing_fields = self._agent_missing_fields(session, payload)
        turn = {
            "turn_id": f"turn_{len(session.get('agent_turns') or []) + 1}",
            "user_message": user_message,
            "normalized_intent": normalized_intent,
            "missing_fields": missing_fields,
            "contract_id": "",
            "prediction_id": "",
            "safe_output": {},
            "created_at": _utcnow_iso(),
        }
        capability_boundary = self._agent_capability_boundary(
            user_message,
            normalized_intent["topic"],
            has_explicit_rule_candidates=bool(_ensure_list(payload.get("rule_candidates"))),
        )
        if capability_boundary:
            normalized_intent["capability_boundary"] = True
            turn["capability_boundary"] = True
            turn["safe_output"] = capability_boundary
        elif missing_fields:
            turn["safe_output"] = {
                "type": "clarification_question",
                "text": f"请补充出生信息：{', '.join(missing_fields)}。",
                "is_prediction": False,
            }
        else:
            pipeline_payload = {
                **payload,
                "prediction_id": _safe_str(payload.get("prediction_id"), f"{session_id}_{turn['turn_id']}"),
                "user_query": user_message,
                "topic": normalized_intent["topic"],
                "chart_snapshot": dict(payload.get("chart_snapshot") or session.get("chart_snapshot") or {}),
                "plugin_claims": _ensure_list(payload.get("plugin_claims")),
                "rule_candidates": _ensure_list(payload.get("rule_candidates")),
                "debug": _safe_bool(payload.get("debug"), False),
            }
            result = self.run_prediction_contract_pipeline(pipeline_payload, actor_role, actor_user_id)
            turn["contract_id"] = _safe_str(result.get("contract_id"))
            turn["prediction_id"] = _safe_str(result.get("prediction_id"))
            turn["safe_output"] = dict(result.get("safe_output") or {})
            turn["minimal_trace"] = dict(result.get("minimal_trace") or {})
        session["agent_turns"] = list(session.get("agent_turns") or []) + [turn]
        if payload.get("birth_payload"):
            session["birth_payload"] = dict(payload.get("birth_payload") or {})
        if payload.get("chart_snapshot"):
            session["chart_snapshot"] = dict(payload.get("chart_snapshot") or {})
        session["updated_at"] = _utcnow_iso()
        self.service._agent_sessions[session_id] = session
        self.service._persist()
        return turn


predictive_runtime_facade = RuleRuntimeFacade(V18PredictiveStore())
predictive_service = predictive_runtime_facade.service
