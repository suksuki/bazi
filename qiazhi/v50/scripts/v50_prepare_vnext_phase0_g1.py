from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from core.mingli_agent.phase0_governance import (
    build_formal_run_lock_candidate,
    load_json,
    validate_phase0_assets,
)


ROOT = Path(__file__).resolve().parents[1]
PHASE0 = ROOT / "data" / "validation" / "phase0"
DEFAULT_OUTPUT = ROOT / "reports" / "vnext-phase0-g1" / "v1"
ASSET_PATHS = {
    "development_set": PHASE0 / "vnext_phase0_development_set_v1.json",
    "development_fixture_pack": PHASE0 / "vnext_phase0_development_fixture_pack_v1.json",
    "model_selection_set": PHASE0 / "vnext_phase0_model_policy_selection_set_v1.json",
    "model_selection_fixture_pack": PHASE0 / "vnext_phase0_model_policy_selection_fixture_pack_v1.json",
    "formal_manifest": PHASE0 / "vnext_phase0_sealed_formal_manifest_v1.json",
    "expert_reference": PHASE0 / "vnext_phase0_expert_reference_space_v1.json",
    "reality_evidence": PHASE0 / "vnext_phase0_reality_evidence_v1.json",
    "lane_policy": ROOT / "config" / "vnext_phase0_lane_policy_v1.json",
    "frontier_policy": ROOT / "config" / "vnext_phase0_frontier_policy_v1.json",
    "go_no_go": ROOT / "config" / "vnext_phase0_go_no_go_v1.json",
    "holistic_synthesis_policy": ROOT / "config" / "vnext_phase0_holistic_synthesis_policy_v1.json",
    "modality_policy": ROOT / "config" / "vnext_phase0_modality_policy_v1.json",
    "dependency_lock": ROOT / "config" / "vnext_phase0_dependencies_v1.txt",
    "benchmark_contract": ROOT / "packages" / "core" / "mingli_agent" / "benchmark.py",
    "context_compiler": ROOT / "packages" / "core" / "mingli_agent" / "context.py",
    "cognitive_reasoner": ROOT / "packages" / "core" / "mingli_agent" / "reasoner.py",
    "fact_review": ROOT / "packages" / "core" / "mingli_agent" / "fact_review.py",
    "fact_engine": ROOT / "packages" / "core" / "mingli_agent" / "world.py",
    "benchmark_runner": ROOT / "scripts" / "v50_run_vnext_phase0_benchmark.py",
}


def prepare(*, run_id: str, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    validation = validate_phase0_assets(
        taxonomy_path=ROOT / "data" / "validation" / "fixtures" / "synthetic_chart_taxonomy_v2.json",
        development_path=ASSET_PATHS["development_set"],
        model_selection_path=ASSET_PATHS["model_selection_set"],
        formal_manifest_path=ASSET_PATHS["formal_manifest"],
        expert_reference_path=ASSET_PATHS["expert_reference"],
        reality_evidence_path=ASSET_PATHS["reality_evidence"],
    )
    lock = build_formal_run_lock_candidate(
        root=ROOT,
        run_id=run_id,
        asset_paths=ASSET_PATHS,
        asset_validation=validation,
    )
    report = {
        "version": "deepbazi.vnext_phase0.g1_5_readiness_audit.v1",
        "run_id": run_id,
        "status": "passed_machine_preparation" if validation["valid"] else "failed",
        "decision": (
            "g1_ready_for_human_and_external_freeze"
            if validation["valid"] and lock["status"] == "candidate_blocked"
            else "g1_formal_run_lock_frozen"
            if lock["status"] == "frozen"
            else "g1_revision_required"
        ),
        "ready_for_formal_run": lock["status"] == "frozen",
        "observed_data": {
            "development_case_count": len(validation["development_ids"]),
            "model_selection_case_count": len(validation["model_selection_ids"]),
            "sealed_formal_case_count": len(validation["formal_ids"]),
            "sets_are_disjoint": validation["valid"],
            "expert_reference_frozen": validation["expert_reference_frozen"],
            "reality_evidence_frozen": validation["reality_evidence_frozen"],
            "formal_lock_status": lock["status"],
            "formal_lock_blockers": lock["blockers"],
            "formal_lane_ids": [row["lane_id"] for row in lock["lane_definitions"]],
            "historical_v30_required": False,
        },
        "interpretation": {
            "observed": "Phase 0 development, model-selection, and formal sets are isolated and hashable.",
            "inference": "The machine-side G1 assets are ready, but no professional cognition result has been established.",
            "recommendation": "Human-freeze the Round 1 reference space, configure and select a true Frontier policy on the selection set, and commit an immutable V50 snapshot before formal execution. Historical V30 is optional and does not block P0-G2.",
        },
        "boundary_status": {
            "training_performed": False,
            "weights_modified": False,
            "production_runtime_rules_modified": False,
            "brain_logic_modified": False,
            "mingli_algorithm_modified": False,
            "theory_modified": False,
            "ui_modified": False,
            "formal_outputs_generated": False,
            "expert_gold_fabricated": False,
            "professional_winner_claimed": False,
            "phase0_g1_governance_only": True,
        },
    }
    (output_dir / "P0_G1_READINESS_AUDIT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "FORMAL_RUN_LOCK_CANDIDATE.json").write_text(
        json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "P0_G1_READINESS_AUDIT.md").write_text(
        _readiness_markdown(report=report), encoding="utf-8"
    )
    (output_dir / "EXPERT_REFERENCE_FREEZE_PACKET.md").write_text(
        _expert_packet(validation=validation), encoding="utf-8"
    )
    (output_dir / "FRONTIER_POLICY_SELECTION_REPORT.md").write_text(
        _frontier_report(), encoding="utf-8"
    )
    (output_dir / "DRY_RUN_RECLASSIFICATION.md").write_text(
        _dry_run_reclassification(), encoding="utf-8"
    )
    (output_dir / "FORMAL_REVIEW_PROTOCOL.md").write_text(
        _review_protocol(), encoding="utf-8"
    )
    return report


def _readiness_markdown(*, report: dict[str, Any]) -> str:
    observed = report["observed_data"]
    return "\n".join(
        [
            "# VNext Phase 0 P0-G1 Readiness Audit",
            "",
            f"- Status: `{report['status']}`",
            f"- Decision: `{report['decision']}`",
            f"- Ready for formal run: `{str(report['ready_for_formal_run']).lower()}`",
            "",
            "## Observed Data",
            "",
            f"- Development cases: `{observed['development_case_count']}`",
            f"- Model-policy selection cases: `{observed['model_selection_case_count']}`",
            f"- Sealed formal cases: `{observed['sealed_formal_case_count']}`",
            f"- Sets are disjoint: `{str(observed['sets_are_disjoint']).lower()}`",
            f"- Expert reference frozen: `{str(observed['expert_reference_frozen']).lower()}`",
            f"- Reality evidence frozen: `{str(observed['reality_evidence_frozen']).lower()}`",
            f"- Formal lock: `{observed['formal_lock_status']}`",
            f"- Formal lanes: `{', '.join(observed['formal_lane_ids'])}`",
            f"- Historical V30 required: `{str(observed['historical_v30_required']).lower()}`",
            "",
            "## Formal Run Blockers",
            "",
            *[f"- `{item}`" for item in observed["formal_lock_blockers"]],
            "",
            "## Interpretation",
            "",
            f"- Observed: {report['interpretation']['observed']}",
            f"- Interpretation: {report['interpretation']['inference']}",
            f"- Recommendation: {report['interpretation']['recommendation']}",
            "",
            "## Boundary Status",
            "",
            "```json",
            json.dumps(report["boundary_status"], ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )


def _expert_packet(*, validation: dict[str, Any]) -> str:
    manifest = load_json(ASSET_PATHS["formal_manifest"])
    expert = load_json(ASSET_PATHS["expert_reference"])
    refs = {row["chart_id"]: row for row in expert["references"]}
    taxonomy = load_json(ROOT / "data" / "validation" / "fixtures" / "synthetic_chart_taxonomy_v2.json")
    fixtures = {row["case_id"]: row for row in taxonomy["cases"]}
    lines = [
        "# VNext Phase 0 Expert Reference Space Freeze Packet",
        "",
        "本包冻结的是可接受认知空间，不是唯一标准报告。不得读取模型输出或 Round 2 现实经历后再填写。",
        "",
        "LLM 只可帮助排版，不得代替人类专家提供内容。冻结后只能通过版本化 Erratum 修正。",
        "",
    ]
    for index, case in enumerate(manifest["cases"], start=1):
        case_id = case["case_id"]
        birth = fixtures[case_id]["birth_input"]
        pillars = " · ".join(birth[key] for key in ("year_pillar", "month_pillar", "day_pillar", "hour_pillar"))
        ref = refs[case_id]
        lines.extend(
            [
                f"## ER-{index:02d}",
                "",
                f"- Chart ID: `{case_id}`",
                f"- 四柱：`{pillars}`",
                f"- Benchmark role: `{case['benchmark_role']}`",
                f"- Chart fact hash: `{validation['chart_fact_hashes'][case_id]}`",
                f"- Current status: `{ref['status']}`",
                "",
                "```yaml",
                "must_notice: []",
                "acceptable_primary_hypotheses: []",
                "strongest_alternatives: []",
                "unacceptable_or_unsupported_hypotheses: []",
                "critical_relations: []",
                "critical_node_candidates: []",
                "plausible_work_paths: []",
                "blocked_or_failed_paths: []",
                "conditional_useful_roles: []",
                "conditional_harmful_roles: []",
                "unresolved_role_disputes: []",
                "required_domain_distinctions: []",
                "career_prior_expectations: []",
                "wealth_prior_expectations: []",
                "unsupported_claims: []",
                "unresolved_disagreements: []",
                "unresolved_questions: []",
                "author: ''",
                "frozen_at: ''",
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def _frontier_report() -> str:
    policy = load_json(ASSET_PATHS["frontier_policy"])
    selection = load_json(ASSET_PATHS["model_selection_set"])
    return "\n".join(
        [
            "# VNext Phase 0 Frontier Policy Selection Report",
            "",
            f"- Status: `{policy['status']}`",
            "- Selected true Frontier policy: `none`",
            "- `qwen3.6:27b` classification: `Local Open Stress Baseline`",
            "- Direct Frontier eligibility: `false`",
            "",
            "## Selection Set",
            "",
            *[f"- `{row['case_id']}` — {row['selection_role']}" for row in selection["cases"]],
            "",
            "## Freeze Requirement",
            "",
            "A strong user-accessible general model must be configured and compared here before any sealed formal chart is run. The frozen policy includes provider, model version, prompt, reasoning mode, temperature, context, output budget, timeout, retry, and schema policy.",
            "",
            "This report intentionally does not promote a convenient local model into the Direct Frontier lane.",
            "",
        ]
    )


def _dry_run_reclassification() -> str:
    return """# Phase 0 Dry Run Reclassification

The 2026-07-13 two-chart run remains valid as a harness test only.

- `c2.output_to_wealth.01` and `c2.mixed_no_obvious_main_path.01` are now Development Set cases.
- Their outputs may inform harness and model-policy debugging.
- They may not contribute to formal professional scoring.
- `qwen3.6:27b` results are Local Open Stress Baseline observations, not Direct Frontier evidence.
- No Lane from that run is a professional winner.
"""


def _review_protocol() -> str:
    return """# VNext Phase 0 Formal Review Protocol

## Layer 1 — 180 immutable outputs

Every output receives automatic safety/reliability audit and a compact blinded expert score for salience, hypothesis quality, work-path coherence, conditional roles, portrait specificity, career/wealth causality, falsifiability, and professional utility.

## Layer 2 — per-chart Lane comparison

After three repeats are aggregated, the expert ranks the six blinded Lanes and records pairwise preferences, primary strengths, primary failures, and whether each result resembles a real professional Mingli judgment.

## Separation

Factual safety and professional cognition are reported separately. Zero fact conflicts never implies professional value. If only one expert adjudicates, the report must say `single-expert adjudicated benchmark`.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare and audit VNext Phase 0 P0-G1 assets.")
    parser.add_argument("--run-id", default="phase0-g1-v1")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    report = prepare(run_id=args.run_id, output_dir=Path(args.output_dir))
    print(json.dumps({"status": report["status"], "decision": report["decision"]}, ensure_ascii=False))
    return 0 if report["status"] == "passed_machine_preparation" else 2


if __name__ == "__main__":
    raise SystemExit(main())
