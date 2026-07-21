from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from experience.canonical_scene import CANONICAL_PROJECTION_KINDS


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/production_authority_manifest_v1.json"


def audit_framework_alignment() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    canonical_scene_source = _read("packages/experience/canonical_scene.py")
    narration_source = _read("apps/product/narrated_workspace.py")
    sandbox_source = _read("packages/experience/experiments.py")
    workspace_source = _read("packages/core/mingli_agent/workspace.py")
    life_case_source = _read("packages/core/life_case/contracts.py")

    surfaces = [
        _surface(
            "case",
            "canonical",
            manifest["module_ownership"]["formal_relation_path"],
            ["packages/core/life_case"],
            "formal facts and committed cognition",
        ),
        _surface(
            "scene",
            "canonical",
            manifest["module_ownership"]["canonical_scene"],
            ["packages/experience/canonical_scene.py", "apps/product/canonical_scene.py"],
            "single role-filtered scene identity",
        ),
        _surface(
            "projection",
            "canonical",
            "experience.canonical_scene.CanonicalProjectionEnvelope",
            ["packages/experience/canonical_scene.py"],
            "presentation only; never owns facts",
        ),
        _surface(
            "role",
            "canonical",
            "experience.canonical_scene.CanonicalRoleDisclosure",
            ["packages/experience/canonical_scene.py"],
            "server-side disclosure and density",
        ),
        _surface(
            "abu",
            "canonical_consumer",
            "product.narrated_workspace.NarratedWorkspaceService",
            ["apps/product/narrated_workspace.py"],
            "explanation and narration from the Abu canonical projection",
        ),
        _surface(
            "sandbox",
            "transitional_scoped",
            "experience.experiments.MingliSandboxState + experience.canvas.TemporalSandboxState",
            ["packages/experience/experiments.py", "packages/experience/canvas.py"],
            "isolated mechanism ablation and temporal hypothesis scopes",
        ),
        _surface(
            "lab",
            "design_fixture",
            "product.mingli_lab_fixture_builder",
            ["apps/product/mingli_lab_fixture_builder.py"],
            "internal fixture generation; no production authority",
        ),
        _surface(
            "workspace",
            "name_convergence_required",
            "LifeCase WorkspaceState + CaseCognitiveWorkspace + NarratedWorkspaceService",
            [
                "packages/core/life_case/contracts.py",
                "packages/core/mingli_agent/workspace.py",
                "apps/product/narrated_workspace.py",
            ],
            "separate UI state, cognitive deliberation state, and narration service",
        ),
    ]

    invariants = [
        _check(
            "five_projection_kinds_share_one_scene_contract",
            tuple(CANONICAL_PROJECTION_KINDS)
            == ("onecanvas", "abu", "theater", "xiangfa", "workspace"),
        ),
        _check(
            "projection_contract_forbids_formal_writes",
            all(
                token in canonical_scene_source
                for token in (
                    "creates_mingli_facts: Literal[False]",
                    "creates_mingli_claims: Literal[False]",
                    "writes_chart: Literal[False]",
                    "writes_life_case: Literal[False]",
                )
            ),
        ),
        _check(
            "abu_requires_canonical_projection",
            "canonical_abu_projection_required" in narration_source,
        ),
        _check(
            "mechanism_sandbox_cannot_write_life_case",
            "writes_life_case: Literal[False]" in sandbox_source,
        ),
        _check(
            "cognitive_workspace_locks_chart_facts",
            "chart_facts_locked: bool = True" in workspace_source,
        ),
        _check(
            "cognitive_workspace_forbids_global_update",
            "global_update_allowed: bool = False" in workspace_source,
        ),
        _check(
            "life_case_workspace_is_non_cognitive_ui_state",
            manifest["formal_data_authority"]["workspace_ui_state"]
            == "WorkspaceState (non-cognitive)"
            and "class WorkspaceState" in life_case_source,
        ),
        _check(
            "mingli_lab_has_no_production_route",
            not _production_route_mentions("mingli-lab"),
        ),
    ]

    gaps = [
        {
            "gap_id": "FRAME-01",
            "surface": "workspace",
            "finding": "Three different responsibilities still use the Workspace name.",
            "required_convergence": "Freeze distinct names and ownership without merging cognitive, UI, and narration state.",
        },
        {
            "gap_id": "LAB-01",
            "surface": "lab",
            "finding": "Mingli Lab is an internal fixture builder, not a canonical scene consumer with a formal experiment ledger.",
            "required_convergence": "Define the Lab experiment boundary and evidence lifecycle before production engineering.",
        },
        {
            "gap_id": "LAB-02",
            "surface": "sandbox",
            "finding": "Mechanism ablation and temporal hypothesis sandboxes are intentionally separate but lack one shared session envelope.",
            "required_convergence": "Introduce one non-authoritative session envelope only if it replaces duplicate lifecycle plumbing.",
        },
    ]

    return {
        "schema_version": "deepbazi.next_framework_alignment_audit.v1",
        "status": "READY_WITH_GAPS" if all(item["passed"] for item in invariants) else "BLOCKED",
        "surfaces": surfaces,
        "invariants": invariants,
        "gaps": gaps,
        "counts": {
            "surfaces": len(surfaces),
            "canonical_or_canonical_consumer": sum(
                item["classification"] in {"canonical", "canonical_consumer"}
                for item in surfaces
            ),
            "transitional_or_design": sum(
                item["classification"]
                in {"transitional_scoped", "design_fixture", "name_convergence_required"}
                for item in surfaces
            ),
            "invariants_passed": sum(item["passed"] for item in invariants),
            "gaps": len(gaps),
        },
        "next_sequence": [
            "Mingli Lab foundation audit",
            "six-pillar relation coverage audit",
            "RA1-RA3 controlled implementation",
            "synthetic validation and training",
            "Workspace and UI alignment",
        ],
        "formal_state_modified": False,
        "production_migration_performed": False,
        "llm_used": False,
    }


def _surface(
    surface: str,
    classification: str,
    owner: str,
    modules: list[str],
    responsibility: str,
) -> dict[str, Any]:
    return {
        "surface": surface,
        "classification": classification,
        "owner": owner,
        "modules": modules,
        "responsibility": responsibility,
    }


def _check(name: str, passed: bool) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed)}


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _production_route_mentions(token: str) -> bool:
    return any(
        token in path.read_text(encoding="utf-8")
        for path in (ROOT / "apps/product").glob("*_api.py")
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit V50 next-framework surface alignment")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_framework_alignment()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] != "BLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
