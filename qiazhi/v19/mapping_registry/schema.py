from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping


MAPPING_UNIT_SCHEMA_VERSION = "v19.mapping_unit.v1"

MAPPING_STATUSES = {"draft", "reviewed", "deprecated"}
MAPPING_TYPES = {"lookup", "bounded_value_mapping", "aggregation"}
SUPPORTED_DOMAINS = {"wealth"}

WEALTH_TARGET_SIGNALS = {
    "competition_pressure",
    "competition_direction",
    "stability",
    "activation",
    "output_to_wealth_flow",
}

DOMAIN_TARGET_SIGNALS = {
    "wealth": WEALTH_TARGET_SIGNALS,
}

SOURCE_SIGNAL_DEFINITIONS = {
    "internal_conflicts.peer_vs_wealth",
    "internal_conflicts.peer_vs_wealth.direction",
    "structural_stability.state",
    "structural_stability.signals.flow_activation",
    "energy_flow.output_to_wealth",
}

FORBIDDEN_MAPPING_KEYS = {
    "score",
    "conclusion",
    "prediction",
    "narrative",
    "free_text",
    "domain_conclusion",
    "explanation",
    "message",
}


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class MappingUnit:
    mapping_id: str
    domain: str
    source_signal: str
    target_signal: str
    mapping_type: str
    value_map: Dict[str, str]
    conditions: Dict[str, Any] = field(default_factory=dict)
    version: str = "v1"
    status: str = "draft"
    created_by: str = "system"
    reviewed_by: str = ""
    created_at: str = field(default_factory=utcnow_iso)
    updated_at: str = field(default_factory=utcnow_iso)
    schema_version: str = MAPPING_UNIT_SCHEMA_VERSION

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "MappingUnit":
        return cls(
            mapping_id=str(payload.get("mapping_id") or ""),
            domain=str(payload.get("domain") or ""),
            source_signal=str(payload.get("source_signal") or ""),
            target_signal=str(payload.get("target_signal") or ""),
            mapping_type=str(payload.get("mapping_type") or ""),
            value_map={str(key): str(value) for key, value in dict(payload.get("value_map") or {}).items()},
            conditions=dict(payload.get("conditions") or {}),
            version=str(payload.get("version") or "v1"),
            status=str(payload.get("status") or "draft"),
            created_by=str(payload.get("created_by") or "system"),
            reviewed_by=str(payload.get("reviewed_by") or ""),
            created_at=str(payload.get("created_at") or utcnow_iso()),
            updated_at=str(payload.get("updated_at") or utcnow_iso()),
            schema_version=str(payload.get("schema_version") or MAPPING_UNIT_SCHEMA_VERSION),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "mapping_id": self.mapping_id,
            "domain": self.domain,
            "source_signal": self.source_signal,
            "target_signal": self.target_signal,
            "mapping_type": self.mapping_type,
            "value_map": dict(self.value_map),
            "conditions": dict(self.conditions),
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "reviewed_by": self.reviewed_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def _walk_forbidden_keys(payload: Any, path: str = "mapping_unit") -> List[str]:
    errors: List[str] = []
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if str(key) in FORBIDDEN_MAPPING_KEYS:
                errors.append(f"{path}.{key}: forbidden mapping key")
            errors.extend(_walk_forbidden_keys(value, f"{path}.{key}"))
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            errors.extend(_walk_forbidden_keys(item, f"{path}[{index}]"))
    return errors


def validate_mapping_unit(unit: MappingUnit | Mapping[str, Any]) -> Dict[str, Any]:
    mapping = unit if isinstance(unit, MappingUnit) else MappingUnit.from_mapping(unit)
    errors: List[str] = []
    if mapping.schema_version != MAPPING_UNIT_SCHEMA_VERSION:
        errors.append(f"schema_version must be {MAPPING_UNIT_SCHEMA_VERSION}")
    if not mapping.mapping_id:
        errors.append("mapping_id is required")
    if mapping.domain not in SUPPORTED_DOMAINS:
        errors.append(f"unsupported domain {mapping.domain}")
    if mapping.source_signal not in SOURCE_SIGNAL_DEFINITIONS:
        errors.append(f"source_signal does not exist in inference schema: {mapping.source_signal}")
    if mapping.target_signal not in DOMAIN_TARGET_SIGNALS.get(mapping.domain, set()):
        errors.append(f"target_signal is not defined for domain {mapping.domain}: {mapping.target_signal}")
    if mapping.target_signal in FORBIDDEN_MAPPING_KEYS:
        errors.append(f"target_signal is forbidden: {mapping.target_signal}")
    if mapping.mapping_type not in MAPPING_TYPES:
        errors.append(f"unsupported mapping_type {mapping.mapping_type}")
    if mapping.status not in MAPPING_STATUSES:
        errors.append(f"unsupported status {mapping.status}")
    if not isinstance(mapping.value_map, dict) or not mapping.value_map:
        errors.append("value_map must be a non-empty finite object")
    else:
        for key, value in mapping.value_map.items():
            if not isinstance(key, str) or not key:
                errors.append("value_map keys must be non-empty strings")
            if not isinstance(value, str) or not value:
                errors.append("value_map values must be non-empty strings")
            if key in FORBIDDEN_MAPPING_KEYS:
                errors.append(f"value_map key is forbidden: {key}")
            if value in FORBIDDEN_MAPPING_KEYS:
                errors.append(f"value_map value is forbidden: {value}")
    if not isinstance(mapping.conditions, dict):
        errors.append("conditions must be an object")
    errors.extend(_walk_forbidden_keys(mapping.conditions, "conditions"))
    return {"valid": not errors, "schema_version": MAPPING_UNIT_SCHEMA_VERSION, "errors": errors}
