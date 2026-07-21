from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "apps/product/experience_shell/src"
STATIC = ROOT / "apps/product/static/experience"


def test_deepbeing_has_one_product_shell_and_workbench_owns_internal_surfaces() -> None:
    components = (SHELL / "components.ts").read_text(encoding="utf-8")
    state = (SHELL / "state.ts").read_text(encoding="utf-8")

    assert 'type ProductArea = "world" | "workbench" | "lab"' in state
    assert 'class="deepbeing-shell"' in components
    assert "我的生命世界" in components
    assert "命盘工作台" in components
    assert "Mingli Lab" in components
    assert "命局概览" in components
    assert "阿布讲解" in components
    assert "site-header" not in components
    assert "workspace-surface-intro" not in components


def test_area_switching_reuses_one_case_load_and_one_server_projection() -> None:
    main = (SHELL / "main.ts").read_text(encoding="utf-8")
    data = (SHELL / "experience_data.ts").read_text(encoding="utf-8")
    api = (SHELL / "api.ts").read_text(encoding="utf-8")
    combined = main + data + api

    assert data.count("loadWorkspaceBootstrap(selection)") == 1
    assert "Promise.allSettled" not in data
    assert main.count("loadReadOnlyCanvas(activeCaseId)") == 1
    assert main.count("loadNarration(activeCaseId)") == 1
    assert 'data-product-area' in (STATIC / "app.js").read_text(encoding="utf-8")
    assert "relation.relation_type ===" not in combined
    assert "writes_life_case" not in combined
    assert "promote" not in combined.lower()


def test_lab_is_role_disclosed_and_only_reads_canvas_relation_state() -> None:
    data = (SHELL / "experience_data.ts").read_text(encoding="utf-8")
    components = (SHELL / "components.ts").read_text(encoding="utf-8")

    assert 'bootstrap.workspace?.allowed_surfaces.includes("mingli_lab")' in data
    assert 'item.relation_state === "potential"' in components
    assert 'item.relation_state !== "potential"' in components
    assert "researchLens" in components
    assert "正式 Case 不在这里被改写" in components
    assert "replace_year" not in components
    assert "sandbox" not in components.lower()


def test_frozen_experience_api_role_alias_is_derived_from_canonical_account_role() -> None:
    account = (ROOT / "apps/product/product_account.py").read_text(encoding="utf-8")

    assert 'projected["role"] = str(projected.get("account_role") or "")' in account
    assert '"role": role' not in account


def test_responsive_shell_has_desktop_sidebar_mobile_bottom_nav_and_390_safe_pillars() -> None:
    css = (STATIC / "styles.css").read_text(encoding="utf-8")

    assert ".product-sidebar" in css
    assert ".mobile-product-navigation" in css
    assert "@media (max-width: 900px)" in css
    assert "@media (max-width: 620px)" in css
    assert "grid-template-columns: repeat(4, minmax(0, 1fr));" in css
    assert "bottom: calc(72px + env(safe-area-inset-bottom));" in css
    assert 'data-product-area-current="workbench"' in css
    assert '.abu-dock:not(.is-open) .abu-bubble' in css
