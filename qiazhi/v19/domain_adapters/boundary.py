from __future__ import annotations

from typing import Any, Dict, List, Mapping

from v19.core.inference_schema import validate_inference_bundle
from v19.mapping_registry import MappingRegistry, default_mapping_registry
from v19.mapping_registry.schema import SOURCE_SIGNAL_DEFINITIONS, WEALTH_TARGET_SIGNALS


DOMAIN_ADAPTER_BOUNDARY_VERSION = "v19.domain_adapter_boundary.v1"
SIGNAL_VALUE_SETS = {
    "competition_pressure": {"none", "low", "medium", "high"},
    "competition_direction": {
        "none",
        "peer_overwhelms_wealth",
        "wealth_resists_peer",
        "balanced_peer_wealth_tension",
    },
    "stability": {"unknown", "low", "medium", "high", "active", "locked"},
    "activation": {"low", "high"},
    "output_to_wealth_flow": {"none", "weak", "medium", "strong"},
}
FORBIDDEN_ADAPTER_KEYS = {"wealth_type", "score", "conclusion", "prediction", "evidence", "narrative", "free_text", "domain_conclusion"}


def _require_valid_inference(bundle: Mapping[str, Any]) -> None:
    validation = validate_inference_bundle(bundle)
    if not validation["valid"]:
        raise ValueError("V19_DOMAIN_ADAPTER_INPUT_INVALID: " + "; ".join(validation["errors"]))


def _conflict(bundle: Mapping[str, Any], conflict_type: str) -> Dict[str, Any]:
    for row in bundle.get("internal_conflicts", []):
        if isinstance(row, Mapping) and row.get("type") == conflict_type:
            return dict(row)
    return {}


def _flow(bundle: Mapping[str, Any], source: str, target: str, flow_type: str) -> Dict[str, Any]:
    for row in bundle.get("energy_flow", []):
        if not isinstance(row, Mapping):
            continue
        if row.get("from") == source and row.get("to") == target and row.get("type") == flow_type:
            return dict(row)
    return {}


def _source_value_and_sources(inference_bundle: Mapping[str, Any], source_signal: str) -> tuple[str, List[str]]:
    if source_signal == "internal_conflicts.peer_vs_wealth":
        row = _conflict(inference_bundle, "peer_vs_wealth")
        return str(row.get("severity") or "none"), list(row.get("sources") or ["ten_god_weights"])
    if source_signal == "internal_conflicts.peer_vs_wealth.direction":
        row = _conflict(inference_bundle, "peer_vs_wealth")
        return str(row.get("direction") or "none"), list(row.get("sources") or ["ten_god_weights"])
    if source_signal == "structural_stability.state":
        row = dict(inference_bundle.get("structural_stability") or {})
        return str(row.get("state") or "unknown"), list(row.get("sources") or ["structure_effects"])
    if source_signal == "structural_stability.signals.flow_activation":
        row = dict(inference_bundle.get("structural_stability") or {})
        value = "present" if "flow_activation" in set(row.get("signals") or []) else "absent"
        return value, list(row.get("sources") or ["structure_effects"])
    if source_signal == "energy_flow.output_to_wealth":
        row = _flow(inference_bundle, "output", "wealth", "generate")
        return str(row.get("strength") or "none"), list(row.get("sources") or ["ten_god_weights"])
    raise ValueError(f"V19_MAPPING_SOURCE_SIGNAL_UNSUPPORTED: {source_signal}")


def _apply_mapping(inference_bundle: Mapping[str, Any], mapping) -> Dict[str, Any]:
    source_value, sources = _source_value_and_sources(inference_bundle, mapping.source_signal)
    if source_value not in mapping.value_map:
        raise ValueError(f"V19_MAPPING_VALUE_UNMAPPED: {mapping.mapping_id}:{source_value}")
    return {
        "value": mapping.value_map[source_value],
        "source_signal": mapping.source_signal,
        "sources": sources,
        "operation": mapping.mapping_type,
        "mapping_id": mapping.mapping_id,
        "mapping_version": mapping.version,
    }


def _adapter_errors(adapter_input: Mapping[str, Any], inference_bundle: Mapping[str, Any]) -> List[str]:
    errors: List[str] = []
    if adapter_input.get("kind") != "DomainAdapterInput":
        errors.append("kind must be DomainAdapterInput")
    if adapter_input.get("domain") != "wealth":
        errors.append("domain must be wealth")
    if adapter_input.get("source_schema_version") != inference_bundle.get("schema_version"):
        errors.append("source_schema_version must match inference schema_version")

    def walk(payload: Any, path: str = "adapter_input") -> None:
        if isinstance(payload, Mapping):
            for key, value in payload.items():
                if str(key) in FORBIDDEN_ADAPTER_KEYS:
                    errors.append(f"{path}.{key}: forbidden adapter key")
                walk(value, f"{path}.{key}")
        elif isinstance(payload, list):
            for index, item in enumerate(payload):
                walk(item, f"{path}[{index}]")

    walk(adapter_input)

    allowed_operations = set(adapter_input.get("allowed_operations") or [])
    signals = adapter_input.get("wealth_signals")
    if not isinstance(signals, Mapping):
        errors.append("wealth_signals must be an object")
        return errors

    actual_signal_keys = set(signals.keys())
    for key in sorted(actual_signal_keys - WEALTH_TARGET_SIGNALS):
        errors.append(f"wealth_signals.{key}: undefined target signal")
    for key in sorted(WEALTH_TARGET_SIGNALS - actual_signal_keys):
        errors.append(f"wealth_signals.{key}: missing target signal")

    inference_roots = set(inference_bundle.keys())
    for signal_key, row in signals.items():
        if not isinstance(row, Mapping):
            errors.append(f"wealth_signals.{signal_key}: signal row must be an object")
            continue
        row_keys = set(row.keys())
        expected = {"value", "source_signal", "sources", "operation", "mapping_id", "mapping_version"}
        for key in sorted(expected - row_keys):
            errors.append(f"wealth_signals.{signal_key}: missing key {key}")
        for key in sorted(row_keys - expected):
            errors.append(f"wealth_signals.{signal_key}.{key}: unexpected key")
        if signal_key in SIGNAL_VALUE_SETS and row.get("value") not in SIGNAL_VALUE_SETS[signal_key]:
            errors.append(f"wealth_signals.{signal_key}.value: unsupported value {row.get('value')}")
        source_signal = str(row.get("source_signal") or "")
        if source_signal not in SOURCE_SIGNAL_DEFINITIONS:
            errors.append(f"wealth_signals.{signal_key}.source_signal: unknown source_signal {source_signal}")
        elif source_signal.split(".")[0] not in inference_roots:
            errors.append(f"wealth_signals.{signal_key}.source_signal: source root does not exist")
        operation = str(row.get("operation") or "")
        if operation not in allowed_operations:
            errors.append(f"wealth_signals.{signal_key}.operation: unsupported operation {operation}")
        sources = row.get("sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"wealth_signals.{signal_key}.sources: must be a non-empty list")
    return errors


def validate_domain_adapter_input(adapter_input: Mapping[str, Any], inference_bundle: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(adapter_input, Mapping):
        return {"valid": False, "version": DOMAIN_ADAPTER_BOUNDARY_VERSION, "errors": ["adapter_input must be an object"]}
    if not isinstance(inference_bundle, Mapping):
        return {"valid": False, "version": DOMAIN_ADAPTER_BOUNDARY_VERSION, "errors": ["inference_bundle must be an object"]}
    return {
        "valid": not _adapter_errors(adapter_input, inference_bundle),
        "version": DOMAIN_ADAPTER_BOUNDARY_VERSION,
        "errors": _adapter_errors(adapter_input, inference_bundle),
    }


def map_wealth_adapter_input(inference_bundle: Mapping[str, Any], mapping_registry: MappingRegistry | None = None) -> Dict[str, Any]:
    _require_valid_inference(inference_bundle)
    registry = mapping_registry or default_mapping_registry()
    mapping_units = registry.require_reviewed_domain_units("wealth")

    wealth_signals = {
        target_signal: _apply_mapping(inference_bundle, mapping_units[target_signal])
        for target_signal in sorted(WEALTH_TARGET_SIGNALS)
    }
    adapter_input = {
        "version": DOMAIN_ADAPTER_BOUNDARY_VERSION,
        "kind": "DomainAdapterInput",
        "domain": "wealth",
        "source_schema_version": str(inference_bundle.get("schema_version") or ""),
        "wealth_signals": wealth_signals,
        "allowed_operations": ["lookup", "bounded_value_mapping", "rename"],
        "guardrails": [
            "ADAPTER_ONLY",
            "CONSUME_INFERENCE_SIGNALS_ONLY",
            "NO_NEW_INFERENCE",
            "NO_SCORE",
            "NO_RULE_CALL",
            "NO_LLM_REASONING",
            "NO_DOMAIN_CONCLUSION",
        ],
    }
    validation = validate_domain_adapter_input(adapter_input, inference_bundle)
    if not validation["valid"]:
        raise ValueError("V19_DOMAIN_ADAPTER_OUTPUT_INVALID: " + "; ".join(validation["errors"]))
    return adapter_input


def build_domain_adapter_input(
    inference_bundle: Mapping[str, Any],
    domain: str = "wealth",
    mapping_registry: MappingRegistry | None = None,
) -> Dict[str, Any]:
    if domain != "wealth":
        raise ValueError("V19_DOMAIN_ADAPTER_UNSUPPORTED_DOMAIN")
    return map_wealth_adapter_input(inference_bundle, mapping_registry=mapping_registry)
