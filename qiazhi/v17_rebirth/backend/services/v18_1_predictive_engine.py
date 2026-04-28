from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from secrets import token_urlsafe
from typing import Any, Dict, List, Optional

from v17_rebirth.paths import RUNTIME_DIR


V18_1_SCHEMA_VERSION = "v18.1"
V18_1_SECRET = os.getenv("V18_1_SECRET", "v18.1-predictive-secret")
RULE_STATE_VALUES = {"experimental", "validated", "active", "deprecated"}
KNOWLEDGE_CARD_STATES = {"draft", "validated", "active", "deprecated", "archived"}
RULE_TEST_SUITE_STATES = {"draft", "validated", "active", "deprecated", "archived"}
RULE_CONFLICT_POLICIES = {"override", "merge", "suppress", "degrade", "defer_manual_review"}
RULE_GATEKEEPER_PROTOCOL = "v18.1.gatekeeper"
RULE_RUNTIME_TOKEN_TTL_SECONDS = 300
LIFECYCLE_BYPASS_CODE = "LIFECYCLE_BYPASS_ATTEMPT"
RULE_TEST_ENGINE_VERSION = "v0.1"
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
    scenario: str
    expected_active: bool
    observed_active: bool
    features: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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
        )


@dataclass
class PredictionLedgerRecord:
    prediction_id: str
    topic: str
    chain_id: str
    state: str
    contract: Dict[str, Any]
    prediction_hash: str
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
        self._pr_queue_file = self._storage_dir / "knowledge_pr_queue.json"
        self._rule_test_file = self._storage_dir / "rule_test_results.json"
        self._rule_test_suite_file = self._storage_dir / "rule_test_suites.json"
        self._rule_test_suite_active_file = self._storage_dir / "active_rule_test_suites.json"

        self._rule_kernels: Dict[str, RuleKernel] = {}
        self._active_rules: Dict[str, str] = {}
        self._knowledge_cards: Dict[str, KnowledgeCard] = {}
        self._active_knowledge_cards: Dict[str, str] = {}
        self._rule_audit_events: List[RuleKernelAuditEvent] = []
        self._lifecycle_tokens: Dict[str, Dict[str, Any]] = {}
        self._ledger: Dict[str, Dict[str, Any]] = {}
        self._verifier_runs: Dict[str, List[Dict[str, Any]]] = {}
        self._feedback_events: Dict[str, List[Dict[str, Any]]] = {}
        self._knowledge_pr: Dict[str, Dict[str, Any]] = {}
        self._rule_test_results: Dict[str, List[Dict[str, Any]]] = {}
        self._rule_test_suites: Dict[str, RuleTestSuite] = {}
        self._active_rule_test_suites: Dict[str, str] = {}

        self._load()

    def _load(self) -> None:
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
        safe_dump(self._pr_queue_file, self._knowledge_pr)
        safe_dump(self._rule_test_file, self._rule_test_results)
        safe_dump(self._rule_test_suite_file, {k: asdict(v) for k, v in self._rule_test_suites.items()})
        safe_dump(self._rule_test_suite_active_file, self._active_rule_test_suites)

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
        self._rule_audit_events.append(
            RuleKernelAuditEvent(
                rule_id=rule_id,
                event_type=event_type,
                severity=severity,
                message=message,
                actor_role=actor_role,
                actor_user_id=actor_user_id,
                source=source,
                details=dict(details or {}),
            )
        )

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
        self._persist()
        return target

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

    def register_rule_test_suite(
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
            raise PredictiveServiceError("RULE_TEST_SUITE_TRANSITION_INVALID", "active suites must be activated through activation API", 409)

        suite = RuleTestSuite.from_payload(payload)
        if not suite.suite_id:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "suite_id is required", 400)
        if not suite.rule_id:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "rule_id is required", 400)

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
        contract = PredictionContract.from_payload(payload)
        if not contract.evidence_ids:
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
        if pr_id not in self._knowledge_pr:
            raise PredictiveServiceError("PR_NOT_FOUND", f"PR {pr_id} not found", 404)

        pr = dict(self._knowledge_pr[pr_id])
        if pr.get("review_state") in {"approved", "rejected"}:
            raise PredictiveServiceError("PR_LOCKED", "PR already reviewed")

        if decision == "approve":
            target_status = str(pr.get("target_status") or payload.get("target_status") or "").strip().lower()
            if target_status:
                self.update_rule_status(rule_id=str(pr.get("rule_id") or ""), target_status=target_status, actor_role=role)
            pr["review_state"] = "approved"
        else:
            pr["review_state"] = "rejected"

        pr["reviewer"] = str(payload.get("reviewer") or role or "system").strip()
        pr["review_note"] = str(payload.get("review_note") or "").strip()
        pr["reviewed_at"] = _utcnow_iso()
        self._knowledge_pr[pr_id] = pr
        self._persist()
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
        if not evidence_ids:
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

        record = PredictionLedgerRecord(
            prediction_id=prediction_id,
            topic=str(contract_payload.get("topic")),
            chain_id=str(contract_payload.get("chain_id")),
            state="Recorded",
            contract=contract_payload,
            prediction_hash=prediction_hash,
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
        checks["evidence_binding"] = all(eid in llm_evidence for eid in evidence_ids) if evidence_ids else bool(llm_evidence)

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

        fatal_fail_keys = {"evidence_binding", "chain_step", "unauthorized_source"}
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

    def append_knowledge_pr(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prediction_id = str(payload.get("prediction_id") or "").strip()
        if not prediction_id:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "prediction_id required")
        rule_id = str(payload.get("rule_id") or "").strip()
        if not rule_id:
            raise PredictiveServiceError("CONTRACT_SCHEMA_INVALID", "rule_id required")
        pr_id = f"pr_{prediction_id}_{_safe_int(len(self._knowledge_pr) + 1)}"
        pr = {
            "pr_id": pr_id,
            "prediction_id": prediction_id,
            "rule_id": rule_id,
            "change_type": str(payload.get("change_type", "rule_modify")),
            "requested_by": str(payload.get("requested_by", "system")),
            "proposed_rule_payload": _as_dict(payload, ["proposed_rule_payload"], required=False) or {},
            "evidence_packet": _as_dict(payload, ["evidence_packet"], required=False) or {},
            "created_at": _utcnow_iso(),
            "review_state": "pending_manual_review",
        }
        self._knowledge_pr[pr_id] = pr
        self._persist()
        return pr


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
        payload.setdefault("allow_sandbox", False)
        return self.service.resolve_rules(payload)

    def run_rule_test(self, payload: Dict[str, Any], actor_role: str, actor_user_id: int) -> Dict[str, Any]:
        payload = dict(payload)
        payload["lifecycle_token"] = self._issue(actor_role=actor_role, actor_user_id=actor_user_id, purpose="test")
        payload["execution_mode"] = "test"
        payload.setdefault("actor_role", actor_role)
        payload.setdefault("actor_user_id", actor_user_id)
        return self.service.run_rule_test_v0(payload)

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


predictive_runtime_facade = RuleRuntimeFacade(V18PredictiveStore())
predictive_service = predictive_runtime_facade.service
