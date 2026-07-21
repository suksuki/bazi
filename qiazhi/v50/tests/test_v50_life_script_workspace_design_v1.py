from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "apps/product/static/experience/design-studies/life-script-workspace-v1"
XIANGFA_APP = ROOT / "apps/product/static/experience/active/xiangfa-generation-v1/app.js"
EXECUTION_STATE = ROOT / "config/v50_execution_state.yaml"
BLUEPRINT = ROOT / "docs/product/V50_LIFE_SCRIPT_CASE_WORKSPACE_AND_MINGLI_LAB_BLUEPRINT_V1.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_execution_state_keeps_target_separate_from_current_product() -> None:
    state = yaml.safe_load(read(EXECUTION_STATE))

    assert state["product"]["canonical_product_target"] == "Life Script Case Workspace"
    assert state["product"]["current_product_surface"] == "legacy_l5_plus_experience_shell"
    assert state["product"]["case_workspace_status"] == (
        "ISOLATED_DESIGN_STUDY_IMPLEMENTED_PRODUCTION_NOT_STARTED"
    )
    assert state["phase"]["global_product_freeze"] == "LIFTED"
    assert state["phase"]["name"] == "V50_FRAMEWORK_ALIGNMENT_AND_MINGLI_LAB"
    assert state["gates"]["git_source_baseline"] == "PASS"
    assert state["gates"]["r1_human_product_gate"] == "CANCELED_NO_SCHEDULE"
    assert state["gates"]["architecture_consolidation_gate"] == "CLOSED_PASS"
    assert state["gates"]["cag_03_canonical_scene"] == "CLOSED_PASS_HARDENED"
    assert state["gates"]["cag_04_relation_path_provenance"] == (
        "CLOSED_PASS_RECONCILED"
    )
    assert state["gates"]["public_professional_release"] == "BLOCKED"
    assert state["protected_boundaries"]["r1_role"] == (
        "immutable_regression_reference_not_global_freeze"
    )
    assert "production_workspace_migration" in state["blocked"]
    assert "mingli_lab_public_release" in state["blocked"]
    assert state["gates"]["cag_05_schema_module_ownership"] == "CLOSED_PASS"
    assert state["gates"]["cal_01_late_zi_five_rats_consistency"] == "CLOSED_PASS"
    assert [item["id"] for item in state["authorized_now"]] == [
        "NEXT_FRAMEWORK_ALIGNMENT"
    ]
    assert state["next_architecture_slice"]["id"] == (
        "MINGLI_LAB_FOUNDATION_AUDIT"
    )
    assert state["validation_policy"]["new_platform_or_product_subsystem"] == "FORBIDDEN"
    assert "self_healing_loop" not in state


def test_machine_execution_state_markdown_is_in_sync() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/sync_execution_state.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_blueprint_names_one_case_and_multiple_projections_without_claiming_implementation() -> None:
    content = read(BLUEPRINT)

    assert "Life Script Case Workspace" in content
    assert "one canonical Mingli world" in content
    for mode in ["Overview", "OneCanvas", "Xiangfa", "Theater", "Mingli Lab"]:
        assert mode in content
    assert "ISOLATED DESIGN STUDY" in content
    assert "not an active product route" in content
    assert "Production adoption: `BLOCKED`" in content


def test_design_study_contains_one_workspace_and_mobile_navigation() -> None:
    html = read(STUDY / "index.html")

    for mode in ["overview", "onecanvas", "xiangfa", "theater", "lab"]:
        assert f'data-mode-panel="{mode}"' in html
        assert f'data-mode-target="{mode}"' in html
    assert 'class="mode-nav mobile-mode-nav"' in html
    assert 'id="roleSelect"' in html
    assert 'class="abu-companion"' in html
    assert 'id="xiangfaFrame"' in html


def test_design_study_consumes_locked_scene_without_becoming_a_reasoner() -> None:
    app = read(STUDY / "app.js")
    combined = read(STUDY / "index.html") + app

    assert 'from "../../shared/s0-v12-shared/scene-runtime.js"' in app
    assert "loadScene()" in app
    assert "scenePillars(source)" in app
    assert "source.observed_natal_path" in app
    assert "source.temporal_stages" in app
    assert "fetch(" not in app
    assert "/api/" not in app
    assert "formal_state_write" not in app
    for forbidden in [
        "系统最佳路径",
        "算法唯一最优路径",
        "已获专业格局定论",
        "整体吉凶",
        "必然人生结局",
    ]:
        assert forbidden not in combined


def test_shared_selection_and_role_boundaries_are_explicit() -> None:
    app = read(STUDY / "app.js")
    xiangfa = read(XIANGFA_APP)

    assert "selectedRef: state.selectedRef" in app
    assert 'type: "deepbazi:xiangfa-state"' in app
    assert 'event.data.interaction === "hotspot"' in app
    assert "PROFESSIONAL_ROLES.has(state.role)" in app
    assert 'if (mode === "lab" && !PROFESSIONAL_ROLES.has(state.role))' in app
    assert 'inspect(selectedRef, {notify: false, reveal: false})' in xiangfa


def test_responsive_and_epistemic_visual_contracts_exist() -> None:
    css = read(STUDY / "styles.css")

    assert "@media (max-width: 760px)" in css
    assert "grid-template-columns: repeat(3, minmax(90px, 1fr))" in css
    assert ".mobile-mode-nav" in css
    assert "--wood-yang" in css and "--wood-yin" in css
    assert "--fire-yang" in css and "--fire-yin" in css
    assert "--metal-yang" in css and "--metal-yin" in css
    assert '.workspace[data-role="member"] [data-mode-target="lab"]' in css
    assert "@media (prefers-reduced-motion: reduce)" in css
