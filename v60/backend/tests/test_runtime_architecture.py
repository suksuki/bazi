from __future__ import annotations

from pathlib import Path

from abu_v60.architecture import runtime_architecture
from abu_v60.architecture.contracts import (
    ModuleKind,
    ModuleStatus,
    ProductUnitRole,
)

EXPECTED_MODULES = {
    "identity",
    "mingli",
    "knowledge",
    "cognition",
    "media",
    "migration",
    "unit-mingli",
    "unit-abu",
    "unit-lab",
}


def test_runtime_architecture_is_reduced_to_mingli_abu_and_internal_lab() -> None:
    architecture = runtime_architecture()
    modules = {module.module_id: module for module in architecture.modules}

    assert architecture.architecture_version == "v60.runtime-architecture.081"
    assert set(modules) == EXPECTED_MODULES
    assert architecture.product_units == ("unit-mingli", "unit-abu", "unit-lab")
    assert architecture.product_core == "unit-mingli"
    assert architecture.priority_breakthrough == "unit-abu"
    assert modules["unit-mingli"].status is ModuleStatus.ACTIVE
    assert modules["unit-abu"].status is ModuleStatus.ACTIVE
    assert modules["unit-lab"].status is ModuleStatus.BOUNDED
    assert modules["unit-lab"].writes_canonical_state is False
    assert modules["unit-lab"].owns_schemas == ()


def test_product_roles_match_the_reduced_release_boundary() -> None:
    placements = {
        item.unit_id: item for item in runtime_architecture().unit_placements
    }

    assert placements["unit-mingli"].priority == 1
    assert placements["unit-mingli"].role is ProductUnitRole.CORE_TRUTH_PRODUCT
    assert placements["unit-abu"].priority == 2
    assert placements["unit-abu"].role is ProductUnitRole.NATIVE_EXPRESSION_LAYER
    assert placements["unit-lab"].priority == 3
    assert placements["unit-lab"].role is ProductUnitRole.RESEARCH_IMPROVEMENT_LOOP
    assert "Internal-only" in placements["unit-lab"].boundary


def test_schema_ownership_and_dependencies_are_closed() -> None:
    architecture = runtime_architecture()
    architecture.validate_boundaries()
    modules = {module.module_id: module for module in architecture.modules}

    assert {
        schema: module.module_id
        for module in architecture.modules
        for schema in module.owns_schemas
    } == {
        "identity": "identity",
        "mingli": "mingli",
        "cognition": "cognition",
        "media": "media",
        "platform": "migration",
    }
    assert all(
        dependency in modules
        for module in architecture.modules
        for dependency in module.reads_from
    )
    assert all(
        module.kind is ModuleKind.PRODUCT_UNIT
        for module in architecture.modules
        if module.module_id in architecture.product_units
    )


def test_current_capabilities_keep_speech_and_six_pillar_sync() -> None:
    modules = {
        module.module_id: module for module in runtime_architecture().modules
    }

    assert "four_six_pillar_stage" in modules["unit-mingli"].capabilities
    assert "same_reading_expression" in modules["unit-abu"].capabilities
    assert (
        "subtitle_synchronized_six_pillar_animation"
        in modules["unit-abu"].capabilities
    )
    assert "internal_synthetic_method_lab" in modules["unit-lab"].capabilities


def test_retired_runtime_packages_are_physically_absent() -> None:
    source_root = Path(__file__).resolve().parents[1] / "src" / "abu_v60"
    retired_packages = {
        "context",
        "game",
        "runtime",
        "story",
        "theater",
        "world",
        "dre" + "am",
    }

    assert all(not (source_root / package).exists() for package in retired_packages)
