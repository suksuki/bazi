from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def audit_mingli_lab_foundation() -> dict[str, Any]:
    fixture_builder = _read("tools/fixtures/mingli_lab_c2a.py")
    lab_session = _read("packages/experience/lab.py")
    temporal_sandbox = _read("packages/experience/canvas.py")
    mechanism_sandbox = _read("packages/experience/experiments.py")
    theater_experiment = _read("apps/product/theater_experiment.py")
    theater_api = _read("apps/product/theater_api.py")
    experience_contracts = _read("packages/experience/contracts.py")

    implementations = [
        {
            "implementation_id": "lab_session",
            "classification": "canonical_non_authoritative_contract",
            "owner": "experience.lab.MingliLabSession",
            "runtime_route": False,
            "formal_write": False,
            "source_chain": "CanonicalProjectionEnvelope -> MingliLabSession",
            "disposition": "single lifecycle and source identity for every Lab experiment",
        },
        {
            "implementation_id": "temporal_canvas_sandbox",
            "classification": "lab_experiment_mode",
            "owner": "experience.canvas.TemporalSandboxState",
            "runtime_route": False,
            "formal_write": False,
            "source_chain": "MingliLabSession -> hypothetical temporal mutation -> Spec/Diff",
            "disposition": "retain as the temporal hypothesis mode",
        },
        {
            "implementation_id": "theater_structural_ablation",
            "classification": "internal_runtime",
            "owner": "product.theater_experiment.ProductMingliExperimentPort",
            "runtime_route": True,
            "formal_write": False,
            "source_chain": "CanonicalScene -> mechanism snapshot -> Lab session -> TopicExploration",
            "disposition": "retain as the mechanism ablation mode and evidence ledger proof",
        },
        {
            "implementation_id": "archived_c2a_fixture",
            "classification": "offline_legacy_evidence_tool",
            "owner": "tools.fixtures.mingli_lab_c2a",
            "runtime_route": False,
            "formal_write": False,
            "source_chain": "LifeCase -> anonymized archived fixture",
            "disposition": "kept outside the product runtime only for reproducible evidence",
        },
    ]

    invariants = [
        _check(
            "fixture_builder_is_outside_product_runtime",
            not (ROOT / "apps/product/mingli_lab_fixture_builder.py").exists()
            and all(
                token in fixture_builder
                for token in ('/ "archive"', '/ "proofs"', '/ "prototypes"', '/ "mingli-lab-c2a"')
            ),
        ),
        _check(
            "one_lab_session_owns_source_and_lifecycle",
            all(
                token in lab_session
                for token in (
                    "class MingliLabSession",
                    "scene_source_hash",
                    "disclosure_hash",
                    "base_snapshot_ref",
                    "revision",
                    "status",
                )
            ),
        ),
        _check(
            "lab_session_forbids_formal_writes_and_promotion",
            all(
                token in lab_session
                for token in (
                    "writes_chart: Literal[False]",
                    "writes_life_case: Literal[False]",
                    "promotes_candidate: Literal[False]",
                )
            ),
        ),
        _check(
            "temporal_and_mechanism_modes_share_lab_session",
            "lab_session: MingliLabSession" in temporal_sandbox
            and "lab_session: MingliLabSession" in mechanism_sandbox,
        ),
        _check(
            "saved_exploration_uses_shared_scene_identity",
            all(
                token in experience_contracts
                for token in (
                    "lab_session_id",
                    "scene_id",
                    "scene_source_hash",
                    "disclosure_hash",
                )
            )
            and "exploration_from_lab_session" in theater_experiment,
        ),
        _check(
            "runtime_experiment_consumes_canonical_scene",
            "scene_owner: CanonicalSceneOwner" in theater_experiment
            and "self.scene_owner.issue_scene" in theater_experiment
            and "envelope.source.source_hash != scene.identity.source_hash" in theater_experiment,
        ),
        _check(
            "runtime_experiment_requires_approved_cognition",
            "approved_active_cognition_required" in theater_experiment
            and "committed_path_not_exactly_available" in theater_experiment,
        ),
        _check(
            "runtime_experiment_events_are_participant_private",
            'event.scope == "participant_private"' in theater_experiment,
        ),
        _check(
            "lab_has_no_llm_or_reasoner_execution",
            '"llm_used": False' in theater_experiment
            and '"reasoner_used": False' in theater_experiment
            and '"llm_used": False' in theater_api
            and '"reasoner_used": False' in theater_api,
        ),
        _check(
            "lab_has_no_production_route_or_formal_write",
            "mingli-lab" not in theater_api
            and all(not item["formal_write"] for item in implementations),
        ),
    ]

    passed = all(item["passed"] for item in invariants)
    return {
        "schema_version": "deepbazi.mingli_lab_foundation_audit.v2",
        "status": "CLOSED_PASS" if passed else "BLOCKED",
        "formal_authority": "LifeCase",
        "scene_authority": "CanonicalSceneOwner",
        "lab_role": "non-authoritative experiment and evidence workspace mode",
        "implementations": implementations,
        "invariants": invariants,
        "gaps": [],
        "counts": {
            "implementations": len(implementations),
            "runtime_implementations": sum(item["runtime_route"] for item in implementations),
            "formal_write_paths": sum(item["formal_write"] for item in implementations),
            "invariants_passed": sum(item["passed"] for item in invariants),
            "gaps": 0,
        },
        "authorized_next": "six_pillar_relation_coverage_audit",
        "production_lab_authorized": False,
        "formal_state_modified": False,
        "llm_used": False,
    }


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _check(name: str, passed: bool) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the V50 Mingli Lab foundation")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_mingli_lab_foundation()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] != "BLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
