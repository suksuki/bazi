from __future__ import annotations

from typing import Any, Dict, List

from v19.knowledge.schema import (
    EvidenceTemplate,
    KnowledgeKernelError,
    KnowledgeStatus,
    KnowledgeUnit,
    knowledge_content_hash,
    safe_str,
    utcnow_iso,
)


class KnowledgeKernel:
    def __init__(self) -> None:
        self._units: Dict[str, KnowledgeUnit] = {}
        self._templates: Dict[str, EvidenceTemplate] = {}

    def register_unit(self, payload: Dict[str, Any], *, actor: str = "system") -> Dict[str, Any]:
        incoming = dict(payload or {})
        incoming.setdefault("created_by", actor)
        unit = KnowledgeUnit.from_payload(incoming)
        existing = self._units.get(unit.knowledge_id)
        if existing and existing.status == KnowledgeStatus.REVIEWED.value:
            incoming_hash = knowledge_content_hash(unit.to_dict(include_hash=False))
            if incoming_hash != existing.content_hash:
                raise KnowledgeKernelError("REVIEWED_KNOWLEDGE_IMMUTABLE", "reviewed knowledge cannot be edited")
        if existing and existing.status == KnowledgeStatus.DEPRECATED.value:
            raise KnowledgeKernelError("DEPRECATED_KNOWLEDGE_LOCKED", "deprecated knowledge cannot be overwritten")
        if existing:
            unit.created_at = existing.created_at
        unit.updated_at = utcnow_iso()
        unit.content_hash = knowledge_content_hash(unit.to_dict(include_hash=False))
        self._units[unit.knowledge_id] = unit
        return unit.to_dict()

    def review_unit(self, knowledge_id: str, *, reviewer: str = "system") -> Dict[str, Any]:
        unit = self._get_unit(knowledge_id)
        if unit.status == KnowledgeStatus.DEPRECATED.value:
            raise KnowledgeKernelError("DEPRECATED_KNOWLEDGE_LOCKED", "deprecated knowledge cannot be reviewed")
        unit.status = KnowledgeStatus.REVIEWED.value
        unit.reviewed_by = reviewer
        unit.reviewed_at = utcnow_iso()
        unit.updated_at = unit.reviewed_at
        unit.content_hash = knowledge_content_hash(unit.to_dict(include_hash=False))
        self._units[unit.knowledge_id] = unit
        return unit.to_dict()

    def deprecate_unit(self, knowledge_id: str, *, reason: str = "") -> Dict[str, Any]:
        unit = self._get_unit(knowledge_id)
        unit.status = KnowledgeStatus.DEPRECATED.value
        unit.updated_at = utcnow_iso()
        self._units[unit.knowledge_id] = unit
        return {**unit.to_dict(), "deprecation_reason": reason}

    def get_unit(self, knowledge_id: str) -> Dict[str, Any]:
        return self._get_unit(knowledge_id).to_dict()

    def list_units(self, *, domain: str = "", status: str = "") -> List[Dict[str, Any]]:
        rows = [unit.to_dict() for unit in self._units.values()]
        if domain:
            rows = [row for row in rows if row["domain"] == domain]
        if status:
            rows = [row for row in rows if row["status"] == status]
        return sorted(rows, key=lambda row: row["knowledge_id"])

    def compile_evidence_template(self, knowledge_id: str) -> Dict[str, Any]:
        unit = self._get_unit(knowledge_id)
        if unit.status == KnowledgeStatus.DEPRECATED.value:
            raise KnowledgeKernelError("DEPRECATED_KNOWLEDGE_LOCKED", "deprecated knowledge cannot be compiled")
        if unit.status != KnowledgeStatus.REVIEWED.value:
            raise KnowledgeKernelError("KNOWLEDGE_REVIEW_REQUIRED", "knowledge must be reviewed before compilation")
        mapping = dict(unit.feature_mapping or {})
        evidence_type = safe_str(mapping.get("evidence_type") or mapping.get("feature_type"))
        if not evidence_type:
            raise KnowledgeKernelError("EVIDENCE_TYPE_REQUIRED", "feature_mapping.evidence_type is required")
        template = EvidenceTemplate(
            template_id=f"template.{unit.knowledge_id}.{unit.version}",
            knowledge_id=unit.knowledge_id,
            domain=unit.domain,
            evidence_type=evidence_type,
            input_requirements=[safe_str(item) for item in mapping.get("input_requirements", []) if safe_str(item)],
            detection_logic=dict(mapping.get("detection_logic") or {}),
            output_fields=[safe_str(item) for item in mapping.get("output_fields", []) if safe_str(item)],
            effects=dict(unit.effects or {}),
            confidence_prior=unit.confidence_prior,
            provenance={
                "source_refs": list(unit.source_refs),
                "content_hash": unit.content_hash,
                "reviewed_by": unit.reviewed_by,
                "reviewed_at": unit.reviewed_at,
            },
            guardrails=[
                "NO_DIRECT_PREDICTION",
                "NO_ACTIVE_RULE",
                "EVIDENCE_ONLY",
                "REQUIRES_CONTRACT_VERIFIER_FOR_OUTPUT",
            ],
        )
        self._templates[template.template_id] = template
        return template.to_dict()

    def list_templates(self) -> List[Dict[str, Any]]:
        return sorted([template.to_dict() for template in self._templates.values()], key=lambda row: row["template_id"])

    def _get_unit(self, knowledge_id: str) -> KnowledgeUnit:
        key = safe_str(knowledge_id)
        unit = self._units.get(key)
        if not unit:
            raise KnowledgeKernelError("KNOWLEDGE_NOT_FOUND", "knowledge unit not found")
        return unit
