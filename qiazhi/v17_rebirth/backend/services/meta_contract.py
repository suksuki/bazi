from __future__ import annotations

from typing import Any


META_CONTRACT_VERSION = "v17.meta_contract.v1"

PUBLIC_META_KEYS: tuple[str, ...] = (
    "projection_bridge_protocol",
    "runtime_field_protocol",
    "relation_formation_summary",
    "relation_dynamics_summary",
    "algorithm_execution_policy",
    "algorithm_execution_audit",
    "climate_field",
    "climate_modifier_layer",
    "god_ring_authority",
    "blind_theme",
    "climate_theme",
    "xiangfa_theme",
    "macro_theme",
    "wealth_profile",
    "plugin_execution_status",
    "plugin_governance_manifest",
    "decision_bucket_contract",
    "l1_manifest_hits",
)

SOLVER_TRACE_KEYS: tuple[str, ...] = (
    "algorithm_execution_trace",
    "plugin_modifier_proposals",
    "plugin_claims",
    "plugin_claim_schema",
    "plugin_conflicts",
    "plugin_conflict_resolutions",
    "plugin_conflict_settlement_meta",
    "knowledge_snapshot",
    "master_reasoning",
    "plugin_recompute_contributions",
    "plugin_auto_ratio_totals",
    "plugin_auto_settlement_signatures",
    "flow_topology",
    "clash_stress_map",
)

LEARNING_SIGNAL_KEYS: tuple[str, ...] = (
    "algorithm_execution_trace",
    "algorithm_execution_audit",
    "algorithm_execution_policy",
    "plugin_claims",
    "plugin_conflicts",
    "plugin_conflict_resolutions",
    "knowledge_snapshot",
    "master_reasoning",
    "plugin_execution_status",
    "relation_formation_summary",
    "relation_dynamics_summary",
    "climate_modifier_layer",
    "macro_theme",
    "wealth_profile",
)


def build_meta_contract(meta: dict[str, Any]) -> dict[str, Any]:
    """Summarize the public/trace boundary without duplicating heavy metadata."""
    source = meta if isinstance(meta, dict) else {}
    public_present = [key for key in PUBLIC_META_KEYS if key in source]
    solver_present = [key for key in SOLVER_TRACE_KEYS if key in source]
    learning_present = [key for key in LEARNING_SIGNAL_KEYS if key in source]
    heavy_counts = {
        key: _value_size_hint(source.get(key))
        for key in [*public_present, *solver_present]
    }
    return {
        "protocol": META_CONTRACT_VERSION,
        "public_meta_keys": public_present,
        "solver_trace_keys": solver_present,
        "learning_signal_keys": learning_present,
        "public_key_count": len(public_present),
        "solver_trace_key_count": len(solver_present),
        "learning_signal_key_count": len(learning_present),
        "heavy_value_size_hints": heavy_counts,
        "boundary": {
            "public_meta_contract": "stable fields safe for UI, Prompt, Admin, and cross-service consumers",
            "solver_trace_meta": "debugging and learning signals; not a source of physical truth by itself",
            "rule": "new metadata must declare whether it is public contract, solver trace, or transient internal state",
        },
    }


def _value_size_hint(value: Any) -> int:
    if isinstance(value, dict):
        return len(value)
    if isinstance(value, (list, tuple, set)):
        return len(value)
    if value is None:
        return 0
    return 1
