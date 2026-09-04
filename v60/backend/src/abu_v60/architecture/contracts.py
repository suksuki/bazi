from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ModuleKind(StrEnum):
    AUTHORITY = "AUTHORITY"
    ENGINE = "ENGINE"
    PRODUCT_UNIT = "PRODUCT_UNIT"
    PLATFORM = "PLATFORM"


class ModuleStatus(StrEnum):
    ACTIVE = "ACTIVE"
    BOUNDED = "BOUNDED"
    RESERVED = "RESERVED"


class ProductUnitRole(StrEnum):
    CORE_TRUTH_PRODUCT = "CORE_TRUTH_PRODUCT"
    RESEARCH_IMPROVEMENT_LOOP = "RESEARCH_IMPROVEMENT_LOOP"
    NATIVE_EXPRESSION_LAYER = "NATIVE_EXPRESSION_LAYER"


class RuntimeModule(BaseModel):
    model_config = ConfigDict(frozen=True)

    module_id: str = Field(min_length=1)
    kind: ModuleKind
    version: str = Field(min_length=1)
    status: ModuleStatus
    owns_schemas: tuple[str, ...] = ()
    reads_from: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    writes_canonical_state: bool = False


class ProductUnitPlacement(BaseModel):
    model_config = ConfigDict(frozen=True)

    unit_id: str = Field(min_length=1)
    priority: int = Field(ge=1)
    role: ProductUnitRole
    boundary: str = Field(min_length=1)


class RuntimeArchitecture(BaseModel):
    model_config = ConfigDict(frozen=True)

    architecture_version: str = Field(min_length=1)
    modules: tuple[RuntimeModule, ...]
    product_units: tuple[str, ...]
    product_core: str
    priority_breakthrough: str
    unit_placements: tuple[ProductUnitPlacement, ...]
    default_locale: str = "zh-CN"
    localization_status: str = "RESERVED"

    def validate_boundaries(self) -> None:
        module_ids = {module.module_id for module in self.modules}
        if len(module_ids) != len(self.modules):
            raise ValueError("duplicate_runtime_module_id")

        schema_owners: dict[str, str] = {}
        for module in self.modules:
            for dependency in module.reads_from:
                if dependency not in module_ids:
                    raise ValueError(f"unknown_module_dependency:{dependency}")
            for schema in module.owns_schemas:
                existing = schema_owners.get(schema)
                if existing is not None:
                    raise ValueError(
                        f"duplicate_schema_owner:{schema}:{existing}:{module.module_id}"
                    )
                schema_owners[schema] = module.module_id

        for unit_id in self.product_units:
            module = next(
                (item for item in self.modules if item.module_id == unit_id),
                None,
            )
            if module is None or module.kind is not ModuleKind.PRODUCT_UNIT:
                raise ValueError(f"invalid_product_unit:{unit_id}")
        if self.product_core not in self.product_units:
            raise ValueError("product_core_must_be_product_unit")
        if self.priority_breakthrough not in self.product_units:
            raise ValueError("priority_breakthrough_must_be_product_unit")
        placement_ids = tuple(item.unit_id for item in self.unit_placements)
        priorities = tuple(item.priority for item in self.unit_placements)
        if set(placement_ids) != set(self.product_units):
            raise ValueError("product_unit_placements_must_cover_product_units")
        if len(placement_ids) != len(set(placement_ids)):
            raise ValueError("duplicate_product_unit_placement")
        if len(priorities) != len(set(priorities)):
            raise ValueError("duplicate_product_unit_priority")

    def public_manifest(self) -> dict[str, object]:
        self.validate_boundaries()
        return {
            "architecture_version": self.architecture_version,
            "default_locale": self.default_locale,
            "localization_status": self.localization_status,
            "product_units": list(self.product_units),
            "product_core": self.product_core,
            "priority_breakthrough": self.priority_breakthrough,
            "unit_placements": [
                {
                    "unit_id": item.unit_id,
                    "priority": item.priority,
                    "role": item.role.value,
                    "boundary": item.boundary,
                }
                for item in sorted(
                    self.unit_placements,
                    key=lambda placement: placement.priority,
                )
            ],
            "modules": [
                {
                    "module_id": module.module_id,
                    "kind": module.kind.value,
                    "version": module.version,
                    "status": module.status.value,
                    "owns_schemas": list(module.owns_schemas),
                    "reads_from": list(module.reads_from),
                    "capabilities": list(module.capabilities),
                    "writes_canonical_state": module.writes_canonical_state,
                }
                for module in self.modules
            ],
        }
