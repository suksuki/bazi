from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def ensure_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return list(value)
    if value is None:
        return []
    return [value]


def safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        raw = float(value)
    except (TypeError, ValueError):
        return default
    if raw != raw:
        return default
    return raw


class KnowledgeKernelError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class KnowledgeStatus(str, Enum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    DEPRECATED = "deprecated"


class KnowledgeDomain(str, Enum):
    CORE_STRUCTURE = "core_structure"
    TEN_GOD = "ten_god"
    FIVE_ELEMENT = "five_element"
    STRENGTH = "strength"
    LUCK_FLOW = "luck_flow"
    THEME_MAPPING = "theme_mapping"
    WEALTH = "wealth"
    CAREER = "career"
    RELATIONSHIP = "relationship"
    HEALTH = "health"
    PERSONALITY = "personality"
    FAMILY = "family"
    STUDY = "study"


def knowledge_content_hash(payload: Dict[str, Any]) -> str:
    normalized = {
        "knowledge_id": safe_str(payload.get("knowledge_id")),
        "domain": safe_str(payload.get("domain")),
        "title": safe_str(payload.get("title")),
        "statement": safe_str(payload.get("statement")),
        "conditions": dict(payload.get("conditions") or {}),
        "feature_mapping": dict(payload.get("feature_mapping") or {}),
        "effects": dict(payload.get("effects") or {}),
        "risks": ensure_list(payload.get("risks")),
        "uncertainty": ensure_list(payload.get("uncertainty")),
        "conflicts": ensure_list(payload.get("conflicts")),
        "source_refs": ensure_list(payload.get("source_refs")),
        "confidence_prior": safe_float(payload.get("confidence_prior"), 0.0),
        "version": safe_str(payload.get("version"), "v1"),
    }
    return "sha256:" + sha256(canonical_json(normalized))


@dataclass
class KnowledgeUnit:
    knowledge_id: str
    domain: str
    title: str
    statement: str
    conditions: Dict[str, Any]
    feature_mapping: Dict[str, Any]
    effects: Dict[str, Any]
    risks: List[str]
    uncertainty: List[str]
    conflicts: List[str]
    source_refs: List[str]
    confidence_prior: float
    status: str = KnowledgeStatus.DRAFT.value
    version: str = "v1"
    created_by: str = "system"
    reviewed_by: str = ""
    reviewed_at: str = ""
    created_at: str = field(default_factory=utcnow_iso)
    updated_at: str = field(default_factory=utcnow_iso)
    content_hash: str = ""

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "KnowledgeUnit":
        knowledge_id = safe_str(payload.get("knowledge_id"))
        if not knowledge_id:
            raise KnowledgeKernelError("KNOWLEDGE_ID_REQUIRED", "knowledge_id is required")
        domain = safe_str(payload.get("domain"))
        if domain not in {item.value for item in KnowledgeDomain}:
            raise KnowledgeKernelError("KNOWLEDGE_DOMAIN_INVALID", "domain is not supported")
        status = safe_str(payload.get("status"), KnowledgeStatus.DRAFT.value)
        if status not in {item.value for item in KnowledgeStatus}:
            raise KnowledgeKernelError("KNOWLEDGE_STATUS_INVALID", "status is not supported")
        unit = cls(
            knowledge_id=knowledge_id,
            domain=domain,
            title=safe_str(payload.get("title")),
            statement=safe_str(payload.get("statement")),
            conditions=dict(payload.get("conditions") or {}),
            feature_mapping=dict(payload.get("feature_mapping") or {}),
            effects=dict(payload.get("effects") or {}),
            risks=[safe_str(item) for item in ensure_list(payload.get("risks")) if safe_str(item)],
            uncertainty=[safe_str(item) for item in ensure_list(payload.get("uncertainty")) if safe_str(item)],
            conflicts=[safe_str(item) for item in ensure_list(payload.get("conflicts")) if safe_str(item)],
            source_refs=[safe_str(item) for item in ensure_list(payload.get("source_refs")) if safe_str(item)],
            confidence_prior=max(0.0, min(1.0, safe_float(payload.get("confidence_prior"), 0.5))),
            status=status,
            version=safe_str(payload.get("version"), "v1"),
            created_by=safe_str(payload.get("created_by"), "system"),
            reviewed_by=safe_str(payload.get("reviewed_by")),
            reviewed_at=safe_str(payload.get("reviewed_at")),
            created_at=safe_str(payload.get("created_at"), utcnow_iso()),
            updated_at=safe_str(payload.get("updated_at"), utcnow_iso()),
            content_hash=safe_str(payload.get("content_hash")),
        )
        unit.content_hash = unit.content_hash or knowledge_content_hash(unit.to_dict(include_hash=False))
        return unit

    def to_dict(self, *, include_hash: bool = True) -> Dict[str, Any]:
        payload = asdict(self)
        if not include_hash:
            payload.pop("content_hash", None)
        return payload


@dataclass
class EvidenceTemplate:
    template_id: str
    knowledge_id: str
    domain: str
    evidence_type: str
    input_requirements: List[str]
    detection_logic: Dict[str, Any]
    output_fields: List[str]
    effects: Dict[str, Any]
    confidence_prior: float
    provenance: Dict[str, Any]
    guardrails: List[str]
    runtime_scope: str = "evidence_template_only"
    created_at: str = field(default_factory=utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
