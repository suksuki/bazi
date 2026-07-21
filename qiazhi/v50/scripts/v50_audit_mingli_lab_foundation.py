from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def audit_mingli_lab_foundation() -> dict[str, Any]:
    fixture_builder = _read("apps/product/mingli_lab_fixture_builder.py")
    temporal_sandbox = _read("packages/experience/canvas.py")
    mechanism_sandbox = _read("packages/experience/experiments.py")
    theater_experiment = _read("apps/product/theater_experiment.py")
    theater_api = _read("apps/product/theater_api.py")
    experience_contracts = _read("packages/experience/contracts.py")

    implementations = [
        {
            "implementation_id": "archived_c2a_fixture",
            "classification": "legacy_evidence",
            "owner": "product.mingli_lab_fixture_builder",
            "runtime_route": False,
            "formal_write": False,
            "source_chain": "LifeCase -> ReadOnlySixPillarCanvasService -> anonymized fixture",
            "disposition": "retain only while archived OneCanvas fixtures depend on its helpers",
        },
        {
            "implementation_id": "temporal_canvas_sandbox",
            "classification": "contract_proof",
            "owner": "experience.canvas.TemporalSandboxState",
            "runtime_route": False,
            "formal_write": False,
            "source_chain": "Canvas compile input -> hypothetical temporal mutation -> Spec/Diff",
            "disposition": "input to future Lab temporal experiment mode",
        },
        {
            "implementation_id": "theater_structural_ablation",
            "classification": "internal_runtime",
            "owner": "product.theater_experiment.ProductMingliExperimentPort",
            "runtime_route": True,
            "formal_write": False,
            "source_chain": "approved LifeCase row -> mechanism snapshot -> private event -> TopicExploration",
            "disposition": "retain as the current experiment ledger proof",
        },
    ]

    invariants = [
        _check(
            "archived_fixture_has_no_product_route",
            "mingli-lab" not in theater_api
            and all(
                token in fixture_builder
                for token in ('/ "archive"', '/ "proofs"', '/ "prototypes"', '/ "mingli-lab-c2a"')
            ),
        ),
        _check(
            "temporal_sandbox_forbids_formal_writes",
            _class_block(temporal_sandbox, "TemporalSandboxState", "class MingliCanvasCompileRequest")
            .count("Literal[False]")
            >= 2,
        ),
        _check(
            "mechanism_sandbox_forbids_life_case_write",
            "writes_life_case: Literal[False]" in mechanism_sandbox,
        ),
        _check(
            "saved_exploration_forbids_life_case_write",
            "class TopicExploration" in experience_contracts
            and "writes_life_case: Literal[False]" in _class_block(
                experience_contracts,
                "TopicExploration",
                "class VoiceValidationCase",
            ),
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
            "runtime_experiment_explicitly_prohibits_life_case_mutation",
            '"modify_life_case" not in envelope.topic_scope.prohibited_capabilities'
            in theater_experiment
            and '"writes_life_case": False' in theater_experiment,
        ),
        _check(
            "lab_has_no_llm_or_reasoner_execution",
            '"llm_used": False' in theater_experiment
            and '"reasoner_used": False' in theater_experiment,
        ),
    ]

    gaps = [
        {
            "gap_id": "LAB-F01",
            "finding": "Temporal and mechanism sandboxes have separate lifecycle identities and no shared experiment envelope.",
            "risk": "future Lab modes could duplicate session, source, and evidence bookkeeping",
        },
        {
            "gap_id": "LAB-F02",
            "finding": "TemporalSandboxState has no persisted TopicExploration ledger path.",
            "risk": "temporal experiments cannot yet enter the same evidence lifecycle as ablation",
        },
        {
            "gap_id": "LAB-F03",
            "finding": "Archived C2A fixture generation helpers still live under the product namespace.",
            "risk": "legacy evidence can be mistaken for a production Lab owner",
        },
        {
            "gap_id": "LAB-F04",
            "finding": "Theater ablation reconstructs its snapshot from a case row instead of consuming a CanonicalScene projection.",
            "risk": "role disclosure and projection identity are enforced by parallel checks rather than the canonical scene envelope",
        },
    ]

    return {
        "schema_version": "deepbazi.mingli_lab_foundation_audit.v1",
        "status": "FOUNDATION_READY_WITH_GAPS"
        if all(item["passed"] for item in invariants)
        else "BLOCKED",
        "formal_authority": "LifeCase",
        "scene_authority": "CanonicalSceneOwner",
        "lab_role": "non-authoritative experiment and evidence workspace mode",
        "implementations": implementations,
        "invariants": invariants,
        "gaps": gaps,
        "counts": {
            "implementations": len(implementations),
            "runtime_implementations": sum(item["runtime_route"] for item in implementations),
            "formal_write_paths": sum(item["formal_write"] for item in implementations),
            "invariants_passed": sum(item["passed"] for item in invariants),
            "gaps": len(gaps),
        },
        "authorized_next": "six_pillar_relation_coverage_audit",
        "production_lab_authorized": False,
        "formal_state_modified": False,
        "llm_used": False,
    }


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _class_block(source: str, class_name: str, next_class: str) -> str:
    return source.split(f"class {class_name}", 1)[1].split(next_class, 1)[0]


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
