from __future__ import annotations

from typing import Any, Dict, List, Mapping


INFERENCE_SCHEMA_VERSION = "v19.inference_schema.v1"

TEN_GOD_KEYS = ("wealth", "officer", "seal", "output", "peer")

TOP_LEVEL_KEYS = {
    "version",
    "schema_version",
    "chart_id",
    "day_master_state",
    "ten_god_structure",
    "energy_flow",
    "structural_stability",
    "internal_conflicts",
    "uncertainty_sources",
    "guardrails",
}

DAY_MASTER_TENDENCIES = {
    "strong",
    "leaning_strong",
    "balanced",
    "leaning_weak",
    "weak",
    "following_tendency_possible",
}

PRESENCE_VALUES = {"absent", "latent", "present", "dominant"}
STRENGTH_VALUES = {"none", "weak", "medium", "strong"}
ACTIVITY_VALUES = {"inactive", "low", "active", "high"}

FLOW_NODE_VALUES = set(TEN_GOD_KEYS)
FLOW_TYPE_VALUES = {"generate", "control", "drain", "support", "pressure"}

STRUCTURAL_STABILITY_STATES = {"stable", "unstable", "mixed", "activated", "locked", "conflicted"}
STRUCTURE_SIGNAL_VALUES = {
    "none",
    "clash",
    "combination",
    "harm",
    "vault_opened",
    "vault_locked",
    "vault_closed",
    "flow_activation",
    "mixed_clash_and_combination",
}

CONFLICT_TYPE_VALUES = {
    "output_vs_officer",
    "peer_vs_wealth",
    "seal_vs_output",
    "clash_vs_combination",
    "support_vs_pressure",
}

CONFLICT_DIRECTION_VALUES = {
    "output_challenges_officer",
    "officer_suppresses_output",
    "balanced_output_officer_tension",
    "peer_overwhelms_wealth",
    "wealth_resists_peer",
    "balanced_peer_wealth_tension",
    "seal_blocks_output",
    "output_drains_seal",
    "balanced_seal_output_tension",
    "clash_disrupts_combination",
    "combination_locks_clash_activation",
    "support_over_pressure",
    "pressure_over_support",
}

SEVERITY_VALUES = {"low", "medium", "high"}

UNCERTAINTY_TYPE_VALUES = {
    "missing_luck_flow",
    "ambiguous_structure",
    "mixed_clash_and_combination",
    "unknown_mapping",
    "weak_signal",
    "requires_domain_mapping",
    "following_tendency_possible",
}

SOURCE_VALUES = {
    "day_master",
    "ten_god_mapping",
    "hidden_stems",
    "root_strength",
    "month_command",
    "support_pressure",
    "relation_hits",
    "structure_effects",
    "vault_effects",
    "flow_effects",
    "element_weights",
    "ten_god_weights",
}

FORBIDDEN_TEXT_KEYS = {
    "text",
    "summary",
    "description",
    "narrative",
    "free_text",
    "explanation",
    "message",
    "label",
    "reason",
    "notes",
    "domain_conclusion",
}


def _error(errors: List[str], path: str, message: str) -> None:
    errors.append(f"{path}: {message}")


def _is_probability(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return 0.0 <= number <= 1.0


def _check_exact_keys(errors: List[str], path: str, payload: Mapping[str, Any], expected: set[str]) -> None:
    actual = set(payload.keys())
    for key in sorted(expected - actual):
        _error(errors, path, f"missing key {key}")
    for key in sorted(actual - expected):
        _error(errors, path, f"unexpected key {key}")


def _check_sources(errors: List[str], path: str, payload: Mapping[str, Any]) -> None:
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        _error(errors, path, "sources must be a non-empty list")
        return
    for index, source in enumerate(sources):
        if source not in SOURCE_VALUES:
            _error(errors, f"{path}.sources[{index}]", f"unsupported source {source}")


def _check_no_forbidden_text_keys(errors: List[str], path: str, payload: Any) -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if str(key) in FORBIDDEN_TEXT_KEYS:
                _error(errors, f"{path}.{key}", "free-text key is not allowed in inference bundle")
            _check_no_forbidden_text_keys(errors, f"{path}.{key}", value)
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            _check_no_forbidden_text_keys(errors, f"{path}[{index}]", item)


def _validate_day_master_state(errors: List[str], payload: Any) -> None:
    path = "day_master_state"
    if not isinstance(payload, Mapping):
        _error(errors, path, "must be an object")
        return
    _check_exact_keys(errors, path, payload, {"tendency", "confidence", "sources"})
    if payload.get("tendency") not in DAY_MASTER_TENDENCIES:
        _error(errors, f"{path}.tendency", f"unsupported value {payload.get('tendency')}")
    if not _is_probability(payload.get("confidence")):
        _error(errors, f"{path}.confidence", "must be a number between 0 and 1")
    _check_sources(errors, path, payload)


def _validate_ten_god_structure(errors: List[str], payload: Any) -> None:
    path = "ten_god_structure"
    if not isinstance(payload, Mapping):
        _error(errors, path, "must be an object")
        return
    _check_exact_keys(errors, path, payload, set(TEN_GOD_KEYS))
    for ten_god in TEN_GOD_KEYS:
        row = payload.get(ten_god)
        row_path = f"{path}.{ten_god}"
        if not isinstance(row, Mapping):
            _error(errors, row_path, "must be an object")
            continue
        _check_exact_keys(errors, row_path, row, {"presence", "strength", "activity", "sources"})
        if row.get("presence") not in PRESENCE_VALUES:
            _error(errors, f"{row_path}.presence", f"unsupported value {row.get('presence')}")
        if row.get("strength") not in STRENGTH_VALUES:
            _error(errors, f"{row_path}.strength", f"unsupported value {row.get('strength')}")
        if row.get("activity") not in ACTIVITY_VALUES:
            _error(errors, f"{row_path}.activity", f"unsupported value {row.get('activity')}")
        _check_sources(errors, row_path, row)


def _validate_energy_flow(errors: List[str], payload: Any) -> None:
    path = "energy_flow"
    if not isinstance(payload, list):
        _error(errors, path, "must be a list")
        return
    for index, row in enumerate(payload):
        row_path = f"{path}[{index}]"
        if not isinstance(row, Mapping):
            _error(errors, row_path, "must be an object")
            continue
        _check_exact_keys(errors, row_path, row, {"from", "to", "type", "strength", "sources"})
        if row.get("from") not in FLOW_NODE_VALUES:
            _error(errors, f"{row_path}.from", f"unsupported value {row.get('from')}")
        if row.get("to") not in FLOW_NODE_VALUES:
            _error(errors, f"{row_path}.to", f"unsupported value {row.get('to')}")
        if row.get("type") not in FLOW_TYPE_VALUES:
            _error(errors, f"{row_path}.type", f"unsupported value {row.get('type')}")
        if row.get("strength") not in STRENGTH_VALUES:
            _error(errors, f"{row_path}.strength", f"unsupported value {row.get('strength')}")
        _check_sources(errors, row_path, row)


def _validate_structural_stability(errors: List[str], payload: Any) -> None:
    path = "structural_stability"
    if not isinstance(payload, Mapping):
        _error(errors, path, "must be an object")
        return
    _check_exact_keys(errors, path, payload, {"state", "signals", "sources"})
    if payload.get("state") not in STRUCTURAL_STABILITY_STATES:
        _error(errors, f"{path}.state", f"unsupported value {payload.get('state')}")
    signals = payload.get("signals")
    if not isinstance(signals, list) or not signals:
        _error(errors, f"{path}.signals", "must be a non-empty list")
    else:
        for index, signal in enumerate(signals):
            if signal not in STRUCTURE_SIGNAL_VALUES:
                _error(errors, f"{path}.signals[{index}]", f"unsupported signal {signal}")
    _check_sources(errors, path, payload)


def _validate_internal_conflicts(errors: List[str], payload: Any) -> None:
    path = "internal_conflicts"
    if not isinstance(payload, list):
        _error(errors, path, "must be a list")
        return
    for index, row in enumerate(payload):
        row_path = f"{path}[{index}]"
        if not isinstance(row, Mapping):
            _error(errors, row_path, "must be an object")
            continue
        _check_exact_keys(errors, row_path, row, {"type", "direction", "severity", "sources"})
        if row.get("type") not in CONFLICT_TYPE_VALUES:
            _error(errors, f"{row_path}.type", f"unsupported value {row.get('type')}")
        if row.get("direction") not in CONFLICT_DIRECTION_VALUES:
            _error(errors, f"{row_path}.direction", f"unsupported value {row.get('direction')}")
        if row.get("severity") not in SEVERITY_VALUES:
            _error(errors, f"{row_path}.severity", f"unsupported value {row.get('severity')}")
        _check_sources(errors, row_path, row)


def _validate_uncertainty_sources(errors: List[str], payload: Any) -> None:
    path = "uncertainty_sources"
    if not isinstance(payload, list):
        _error(errors, path, "must be a list")
        return
    for index, row in enumerate(payload):
        row_path = f"{path}[{index}]"
        if not isinstance(row, Mapping):
            _error(errors, row_path, "must be an object")
            continue
        _check_exact_keys(errors, row_path, row, {"type", "sources"})
        if row.get("type") not in UNCERTAINTY_TYPE_VALUES:
            _error(errors, f"{row_path}.type", f"unsupported value {row.get('type')}")
        _check_sources(errors, row_path, row)


def validate_inference_bundle(bundle: Any) -> Dict[str, Any]:
    errors: List[str] = []
    if not isinstance(bundle, Mapping):
        return {"valid": False, "schema_version": INFERENCE_SCHEMA_VERSION, "errors": ["bundle must be an object"]}

    _check_exact_keys(errors, "bundle", bundle, TOP_LEVEL_KEYS)
    if bundle.get("schema_version") != INFERENCE_SCHEMA_VERSION:
        _error(errors, "schema_version", f"must be {INFERENCE_SCHEMA_VERSION}")
    if not isinstance(bundle.get("chart_id"), str) or not bundle.get("chart_id"):
        _error(errors, "chart_id", "must be a non-empty string")

    _validate_day_master_state(errors, bundle.get("day_master_state"))
    _validate_ten_god_structure(errors, bundle.get("ten_god_structure"))
    _validate_energy_flow(errors, bundle.get("energy_flow"))
    _validate_structural_stability(errors, bundle.get("structural_stability"))
    _validate_internal_conflicts(errors, bundle.get("internal_conflicts"))
    _validate_uncertainty_sources(errors, bundle.get("uncertainty_sources"))
    _check_no_forbidden_text_keys(errors, "bundle", bundle)

    return {"valid": not errors, "schema_version": INFERENCE_SCHEMA_VERSION, "errors": errors}
