from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "apps/product/experience_shell/src"
STATIC = ROOT / "apps/product/static/experience"


def test_experience_shell_consumes_workspace_and_loads_case_surfaces_in_parallel() -> None:
    api = (SHELL / "api.ts").read_text(encoding="utf-8")
    main = (SHELL / "main.ts").read_text(encoding="utf-8")
    data = (SHELL / "experience_data.ts").read_text(encoding="utf-8")

    assert "/api/v50/scenes/cases/${encodeURIComponent(caseId)}/workspace" in api
    assert "Promise.allSettled" in data
    assert "loadCaseWorkspace(caseId)" in data
    assert "availableSurfaces.includes(surface)" in main
    assert "surface === \"onecanvas\"" in data
    assert "surface === \"theater\"" in data


def test_personal_workspace_exposes_only_case_bound_surfaces() -> None:
    source = (SHELL / "components.ts").read_text(encoding="utf-8")
    bundle = (STATIC / "app.js").read_text(encoding="utf-8")

    assert "命局概览" in source
    assert "阿布讲解" in source
    assert "xiangfa-generation-v1" not in source
    assert "abu-says-mingli-s0-v12" not in source
    assert "data-workspace-surface" in bundle
    assert "journey-nav" not in source


def test_workspace_projection_does_not_add_client_mingli_inference() -> None:
    source = "\n".join(
        (SHELL / name).read_text(encoding="utf-8")
        for name in ("api.ts", "main.ts", "components.ts", "state.ts")
    )

    assert "replace_year" not in source
    assert "relation.relation_type ===" not in source
    assert "writes_life_case" not in source
    assert "promote" not in source.lower()
