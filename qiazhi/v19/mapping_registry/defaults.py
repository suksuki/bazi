from __future__ import annotations

from v19.mapping_registry.registry import MappingRegistry
from v19.mapping_registry.schema import MappingUnit


DEFAULT_MAPPING_TIMESTAMP = "2026-04-28T00:00:00+00:00"


DEFAULT_WEALTH_MAPPING_UNITS = [
    MappingUnit(
        mapping_id="wealth.peer_vs_wealth.competition_pressure",
        domain="wealth",
        source_signal="internal_conflicts.peer_vs_wealth",
        target_signal="competition_pressure",
        mapping_type="lookup",
        value_map={"none": "none", "low": "low", "medium": "medium", "high": "high"},
        version="v1",
        status="reviewed",
        created_by="system",
        reviewed_by="system",
        created_at=DEFAULT_MAPPING_TIMESTAMP,
        updated_at=DEFAULT_MAPPING_TIMESTAMP,
    ),
    MappingUnit(
        mapping_id="wealth.peer_vs_wealth.competition_direction",
        domain="wealth",
        source_signal="internal_conflicts.peer_vs_wealth.direction",
        target_signal="competition_direction",
        mapping_type="lookup",
        value_map={
            "none": "none",
            "peer_overwhelms_wealth": "peer_overwhelms_wealth",
            "wealth_resists_peer": "wealth_resists_peer",
            "balanced_peer_wealth_tension": "balanced_peer_wealth_tension",
        },
        version="v1",
        status="reviewed",
        created_by="system",
        reviewed_by="system",
        created_at=DEFAULT_MAPPING_TIMESTAMP,
        updated_at=DEFAULT_MAPPING_TIMESTAMP,
    ),
    MappingUnit(
        mapping_id="wealth.structural_stability.stability",
        domain="wealth",
        source_signal="structural_stability.state",
        target_signal="stability",
        mapping_type="bounded_value_mapping",
        value_map={
            "stable": "high",
            "mixed": "medium",
            "activated": "active",
            "locked": "locked",
            "conflicted": "low",
            "unstable": "low",
            "unknown": "unknown",
        },
        version="v1",
        status="reviewed",
        created_by="system",
        reviewed_by="system",
        created_at=DEFAULT_MAPPING_TIMESTAMP,
        updated_at=DEFAULT_MAPPING_TIMESTAMP,
    ),
    MappingUnit(
        mapping_id="wealth.structural_stability.activation",
        domain="wealth",
        source_signal="structural_stability.signals.flow_activation",
        target_signal="activation",
        mapping_type="bounded_value_mapping",
        value_map={"present": "high", "absent": "low"},
        version="v1",
        status="reviewed",
        created_by="system",
        reviewed_by="system",
        created_at=DEFAULT_MAPPING_TIMESTAMP,
        updated_at=DEFAULT_MAPPING_TIMESTAMP,
    ),
    MappingUnit(
        mapping_id="wealth.energy_flow.output_to_wealth",
        domain="wealth",
        source_signal="energy_flow.output_to_wealth",
        target_signal="output_to_wealth_flow",
        mapping_type="lookup",
        value_map={"none": "none", "weak": "weak", "medium": "medium", "strong": "strong"},
        version="v1",
        status="reviewed",
        created_by="system",
        reviewed_by="system",
        created_at=DEFAULT_MAPPING_TIMESTAMP,
        updated_at=DEFAULT_MAPPING_TIMESTAMP,
    ),
]


def default_mapping_registry() -> MappingRegistry:
    return MappingRegistry(DEFAULT_WEALTH_MAPPING_UNITS)
