from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping

from v19.mapping_registry.schema import DOMAIN_TARGET_SIGNALS, MappingUnit, validate_mapping_unit


class MappingRegistryError(ValueError):
    pass


class MappingRegistry:
    def __init__(self, units: Iterable[MappingUnit | Mapping[str, Any]] | None = None) -> None:
        self._units: Dict[str, MappingUnit] = {}
        for unit in units or []:
            self.register(unit)

    def register(self, unit: MappingUnit | Mapping[str, Any]) -> MappingUnit:
        mapping = unit if isinstance(unit, MappingUnit) else MappingUnit.from_mapping(unit)
        validation = validate_mapping_unit(mapping)
        if not validation["valid"]:
            raise MappingRegistryError("V19_MAPPING_UNIT_INVALID: " + "; ".join(validation["errors"]))
        if mapping.mapping_id in self._units:
            raise MappingRegistryError(f"V19_MAPPING_UNIT_DUPLICATE: {mapping.mapping_id}")
        self._units[mapping.mapping_id] = mapping
        return mapping

    def list_units(self, domain: str | None = None, status: str | None = None) -> List[MappingUnit]:
        units = list(self._units.values())
        if domain is not None:
            units = [unit for unit in units if unit.domain == domain]
        if status is not None:
            units = [unit for unit in units if unit.status == status]
        return sorted(units, key=lambda unit: unit.mapping_id)

    def reviewed_units(self, domain: str) -> List[MappingUnit]:
        return self.list_units(domain=domain, status="reviewed")

    def reviewed_units_by_target(self, domain: str) -> Dict[str, MappingUnit]:
        rows = {}
        for unit in self.reviewed_units(domain):
            rows[unit.target_signal] = unit
        return rows

    def require_reviewed_domain_units(self, domain: str) -> Dict[str, MappingUnit]:
        expected = DOMAIN_TARGET_SIGNALS.get(domain)
        if not expected:
            raise MappingRegistryError(f"V19_MAPPING_DOMAIN_UNSUPPORTED: {domain}")
        rows = self.reviewed_units_by_target(domain)
        missing = sorted(expected - set(rows))
        if missing:
            raise MappingRegistryError("V19_MAPPING_MISSING_REVIEWED_UNITS: " + ",".join(missing))
        return rows
