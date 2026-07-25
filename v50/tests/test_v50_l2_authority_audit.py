from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / "packages"
APPS = ROOT / "apps"
ONECANVAS = APPS / "product/static/experience/active/onecanvas-r1"


def _python_sources() -> list[Path]:
    return [*PACKAGES.rglob("*.py"), *APPS.rglob("*.py")]


def test_only_canonical_temporal_service_calls_low_level_dayun_algorithms() -> None:
    owners = []
    pattern = re.compile(r"(?:from|import) core\.engines\.bazi\.dayun")
    for path in _python_sources():
        if pattern.search(path.read_text(encoding="utf-8")):
            owners.append(path.relative_to(ROOT).as_posix())
    assert owners == ["packages/core/engines/bazi/temporal_service.py"]


def test_production_modules_do_not_import_fixture_builder_implementation() -> None:
    offenders = []
    for path in _python_sources():
        if "fixture" in path.name:
            continue
        source = path.read_text(encoding="utf-8")
        if "fixture_builder import" in source or re.search(r"from product\..*_fixture", source):
            offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []


def test_deleted_authority_owners_cannot_reappear_silently() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in _python_sources())
    for symbol in (
        "def _onecanvas_timing_projection",
        "def _structural_timing_projection",
        "def _onecanvas_structural_variant",
        "def _prepare_variant_for_canvas",
        "def _pillar_nodes",
        "def _luck_direction",
        "def current_timing_material",
    ):
        assert symbol not in combined
    assert combined.count("def solve_chart_constraints(") == 1
    assert combined.count("class CanonicalTemporalService:") == 1


def test_browser_edits_target_draft_but_never_derives_mingli_facts() -> None:
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in ONECANVAS.glob("*.js")
    )
    for forbidden in (
        "FIVE_TIGERS",
        "FIVE_RATS",
        "JIAZI",
        "dayun_direction",
        "structural_dayun",
        "calculateLuck",
        "inferRelation",
        "cascadedPillars",
        "LifeCase.write",
        "ChartVersion.write",
        "五虎遁",
        "五鼠遁",
    ):
        assert forbidden not in sources
    assert "/api/v50/experience/onecanvas/target-compile" in sources
    assignments = re.findall(r"workingSnapshot\.variant\s*=\s*([^;]+);", sources)
    assert assignments
    assert set(assignments) == {"payload.variant"}


def test_onecanvas_adapter_is_projection_only() -> None:
    adapter = (APPS / "product/onecanvas_timing_adapter.py").read_text(encoding="utf-8")
    assert "CanonicalTemporalService" not in adapter
    assert "dayun_sequence" not in adapter
    assert "structural_dayun_sequence" not in adapter
    assert "project_canonical_timing" in adapter
