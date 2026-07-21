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
    canonical_scene = _read("packages/experience/canonical_scene.py")
    narration = _read("apps/product/abu_narration.py")
    mechanism_sandbox = _read("packages/experience/experiments.py")
    temporal_sandbox = _read("packages/experience/canvas.py")
    belief_state = _read("packages/core/mingli_agent/workspace.py")
    workspace = _read("packages/experience/workspace.py")
    lab = _read("packages/experience/lab.py")
    life_case = _read("packages/core/life_case/contracts.py")

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
            manifest["module_ownership"]["abu_narration"],
            ["apps/product/abu_narration.py"],
            "explanation and narration from the Abu projection",
        ),
        _surface(
            "sandbox",
            "scoped_non_authoritative",
            manifest["module_ownership"]["mingli_lab_session"],
            ["packages/experience/experiments.py", "packages/experience/canvas.py"],
            "mechanism and temporal experiments share one lifecycle identity",
        ),
        _surface(
            "lab",
            "canonical_consumer",
            manifest["module_ownership"]["mingli_lab_session"],
            ["packages/experience/lab.py"],
            "non-authoritative experiment and evidence lifecycle",
        ),
        _surface(
            "workspace",
            "canonical_consumer",
            manifest["module_ownership"]["workspace_ui_state"],
            ["packages/experience/workspace.py"],
            "shared UI state bound to one canonical projection",
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
                token in canonical_scene
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
            "canonical_abu_projection_required" in narration,
        ),
        _check(
            "one_lab_session_owns_both_sandbox_lifecycles",
            "lab_session: MingliLabSession" in mechanism_sandbox
            and "lab_session: MingliLabSession" in temporal_sandbox,
        ),
        _check(
            "lab_session_cannot_write_or_promote",
            all(
                token in lab
                for token in (
                    "writes_chart: Literal[False]",
                    "writes_life_case: Literal[False]",
                    "promotes_candidate: Literal[False]",
                )
            ),
        ),
        _check(
            "belief_state_is_cognitive_and_locked",
            manifest["module_ownership"]["case_belief_state"]
            == "core.mingli_agent.workspace.CaseBeliefState"
            and "class CaseBeliefState" in belief_state
            and "chart_facts_locked: bool = True" in belief_state
            and "global_update_allowed: bool = False" in belief_state,
        ),
        _check(
            "workspace_state_has_one_non_cognitive_owner",
            manifest["formal_data_authority"]["workspace_ui_state"]
            == "experience.workspace.CaseWorkspaceState (non-cognitive)"
            and "class CaseWorkspaceState" in workspace
            and "class CaseWorkspaceState" not in life_case,
        ),
        _check(
            "workspace_is_bound_to_canonical_projection",
            "projection: CanonicalProjectionEnvelope" in workspace
            and "case_workspace_scene_identity_mismatch" in workspace
            and "case_workspace_selection_not_disclosed" in workspace,
        ),
        _check(
            "fixture_builders_are_outside_product_runtime",
            not (ROOT / "apps/product/mingli_lab_fixture_builder.py").exists()
            and not (ROOT / "apps/product/onecanvas_fixture_builder.py").exists()
            and (ROOT / "tools/fixtures/mingli_lab_c2a.py").exists()
            and (ROOT / "tools/fixtures/onecanvas_r1.py").exists(),
        ),
        _check(
            "mingli_lab_has_no_production_route",
            not _production_route_mentions("mingli-lab"),
        ),
    ]

    passed = all(item["passed"] for item in invariants)
    return {
        "schema_version": "deepbazi.next_framework_alignment_audit.v2",
        "status": "CLOSED_PASS" if passed else "BLOCKED",
        "surfaces": surfaces,
        "invariants": invariants,
        "gaps": [],
        "counts": {
            "surfaces": len(surfaces),
            "canonical_or_canonical_consumer": sum(
                item["classification"] in {"canonical", "canonical_consumer"}
                for item in surfaces
            ),
            "scoped_non_authoritative": sum(
                item["classification"] == "scoped_non_authoritative"
                for item in surfaces
            ),
            "invariants_passed": sum(item["passed"] for item in invariants),
            "gaps": 0,
        },
        "next_sequence": [
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
