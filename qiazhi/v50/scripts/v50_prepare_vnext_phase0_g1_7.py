from __future__ import annotations

import argparse
import inspect
import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from core.contracts import BirthInputCanonical
from core.mingli_agent import compile_chart_world
from core.mingli_agent.benchmark import direct_power_user_prompt
from core.mingli_agent.fact_review import classify_claim_modality, deterministic_fact_conflicts
from core.mingli_agent.phase0_governance import load_json, validate_phase0_assets
from scripts.v50_prepare_vnext_phase0_g1 import ASSET_PATHS, prepare
from scripts.v50_prepare_vnext_phase0_g1_6 import audit_nonsealed_resource_access, audit_pairwise_contract


ROOT = Path(__file__).resolve().parents[1]
PHASE0 = ROOT / "data" / "validation" / "phase0"
DEFAULT_OUTPUT = ROOT / "reports" / "vnext-phase0-g1" / "phase0-g1-7-freeze-v1"


def prepare_g1_7(
    *,
    run_id: str,
    output_dir: Path,
    git_state_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    direct = audit_direct_power_user_policy()
    repair = audit_p0_repair_authority()
    modality = audit_modality_policy()
    nonsealed = audit_nonsealed_resource_access(output_dir=output_dir / "nonsealed-access-probe")
    pairwise = audit_pairwise_contract()
    reference = audit_human_reference_freeze()
    frontier = audit_frontier_policy_freeze()

    lock_dir = output_dir / "formal-lock-candidate"
    prepare(
        run_id=f"{run_id}-lock-candidate",
        output_dir=lock_dir,
        git_state_override=git_state_override,
    )
    lock = load_json(lock_dir / "FORMAL_RUN_LOCK_CANDIDATE.json")
    snapshot = {
        "status": "passed" if lock["git_state"]["v50_snapshot_tracked"] else "pending_clean_committed_snapshot",
        "git_commit": lock["git_commit"],
        "dirty_tree": lock["dirty_tree"],
        "v50_snapshot_tracked": lock["git_state"]["v50_snapshot_tracked"],
        "v50_status": lock["git_state"]["v50_status"],
    }

    machine_gates = {
        "direct_power_user_policy": direct["status"] == "passed",
        "p0_repair_authority": repair["status"] == "passed",
        "modality_policy": modality["status"] == "passed",
        "sealed_non_access": nonsealed["status"] == "passed",
        "pairwise_contract": pairwise["status"] == "passed",
    }
    external_gates = {
        "human_expert_reference": reference["status"] == "frozen",
        "true_frontier_policy": frontier["status"] == "frozen",
        "clean_committed_snapshot": snapshot["status"] == "passed",
    }
    machine_ready = all(machine_gates.values())
    external_ready = all(external_gates.values())
    preflight = {
        "status": "authorized_but_not_run" if machine_ready and external_ready else "prohibited_pending_gates",
        "run_performed": False,
        "required_explicit_human_approval": True,
        "sealed_formal_manifest_access_allowed": False,
        "reason": (
            "A final non-sealed live preflight needs a separate explicit approval even after all freeze gates close."
            if machine_ready and external_ready
            else "Human Reference, true Frontier policy, and clean committed snapshot must all close first."
        ),
    }
    blockers = [
        *[name for name, passed in machine_gates.items() if not passed],
        *[name for name, passed in external_gates.items() if not passed],
        *lock["blockers"],
    ]
    blockers = _unique(blockers)
    report = {
        "version": "deepbazi.vnext_phase0.g1_7_freeze.v1",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "machine_preparation_passed_external_freeze_pending" if machine_ready else "machine_revision_required",
        "ready_for_p0_g2": False,
        "formal_run_started": False,
        "sealed_chart_accessed": False,
        "machine_gates": machine_gates,
        "external_gates": external_gates,
        "observed_data": {
            "direct_power_user_policy": direct,
            "p0_repair_authority": repair,
            "modality_policy": modality,
            "sealed_non_access": nonsealed,
            "pairwise_contract": pairwise,
            "human_expert_reference": reference,
            "frontier_policy": frontier,
            "snapshot": snapshot,
            "formal_lock_status": lock["status"],
            "formal_lock_blockers": lock["blockers"],
            "final_nonsealed_live_preflight": preflight,
        },
        "observed_interpretation_recommendation": {
            "observed": (
                "The Direct lanes now use a strong one-shot power-user request, P0 Agent lanes preserve semantic output, "
                "and the seven-way modality taxonomy prevents questions and timing conditions from becoming natal facts."
            ),
            "interpretation": (
                "Machine governance is ready for human/external freeze work, but no professional Mingli quality result exists yet."
            ),
            "recommendation": (
                "Human-freeze the ten-chart acceptable cognition space, select a reproducible true Frontier policy on only the "
                "five selection charts, then create a clean committed snapshot. Do not run P0-G2 before explicit approval."
            ),
        },
        "blockers": blockers,
        "boundary_status": {
            "training_performed": False,
            "weights_modified": False,
            "production_runtime_rules_modified": False,
            "brain_logic_modified": False,
            "mingli_algorithm_modified": False,
            "theory_modified": False,
            "product_runtime_modified": False,
            "ui_modified": False,
            "semantic_repair_allowed_in_p0": False,
            "raw_cognitive_output_immutable": True,
            "review_annotations_separate": True,
            "local_llm_repair_used": False,
            "expert_reference_authored_by_llm": False,
            "frontier_policy_fabricated": False,
            "live_preflight_run": False,
            "sealed_outputs_generated": False,
            "p0_g2_started": False,
        },
    }

    _write_json(output_dir / "DIRECT_POWER_USER_POLICY_AUDIT.json", direct)
    _write_json(output_dir / "P0_REPAIR_AUTHORITY_AUDIT.json", repair)
    _write_json(output_dir / "MODALITY_POLICY_AUDIT.json", modality)
    _write_json(output_dir / "HUMAN_EXPERT_REFERENCE_FREEZE_STATUS.json", reference)
    _write_json(output_dir / "FRONTIER_POLICY_FREEZE_STATUS.json", frontier)
    _write_json(output_dir / "FORMAL_RUN_LOCK_CANDIDATE.json", lock)
    _write_json(output_dir / "MASTER_AUDIT_REPORT.json", report)
    (output_dir / "MASTER_AUDIT_REPORT.md").write_text(_master_markdown(report), encoding="utf-8")
    (output_dir / "ANALYST_REVIEW_PACKET.md").write_text(_analyst_packet(report), encoding="utf-8")
    (output_dir / "HUMAN_EXPERT_REFERENCE_FREEZE_GUIDE.md").write_text(_human_reference_guide(), encoding="utf-8")
    (output_dir / "FRONTIER_POLICY_SELECTION_GUIDE.md").write_text(_frontier_guide(), encoding="utf-8")
    files = sorted(path for path in output_dir.iterdir() if path.is_file())
    _write_json(
        output_dir / "ARTIFACT_MANIFEST.json",
        {
            "version": "deepbazi.vnext_phase0.g1_7_artifact_manifest.v1",
            "run_id": run_id,
            "files": [{"path": path.name, "sha256": sha256(path.read_bytes()).hexdigest()} for path in files],
        },
    )
    return report


def audit_direct_power_user_policy() -> dict[str, Any]:
    prompt = direct_power_user_prompt(
        chart_payload={"pillars": ["甲子", "乙丑", "丙寅", "丁卯"], "gender": "unknown"}
    )
    forbidden = (
        "Graph",
        "Path",
        "Role",
        "Ablation",
        "Challenge Pack",
        "Expert Reference",
        "Reality Evidence",
        "事实账本",
        "七步",
        "步骤一",
        "逐阶段",
    )
    found = [token for token in forbidden if token in prompt]
    allowed_targets = ("命局重心", "主解释", "替代解释", "主要做功", "条件性用忌", "事业", "财富", "可推翻", "现实问题")
    missing_targets = [token for token in allowed_targets if token not in prompt]
    runner_source = (ROOT / "scripts" / "v50_run_vnext_phase0_benchmark.py").read_text(encoding="utf-8")
    runner_bound = runner_source.count("direct_power_user=True") >= 3
    passed = not found and not missing_targets and runner_bound
    return {
        "version": "deepbazi.vnext_phase0.direct_power_user_policy_audit.v1",
        "status": "passed" if passed else "failed",
        "policy": "strong_direct_power_user_one_shot_v1",
        "internal_protocol_tokens_found": found,
        "required_output_targets_missing": missing_targets,
        "runner_direct_lane_bindings_present": runner_bound,
        "prompt_sha256": sha256(prompt.encode("utf-8")).hexdigest(),
        "deepbazi_fact_ledger_supplied": False,
        "internal_seven_stage_protocol_supplied": False,
    }


def audit_p0_repair_authority() -> dict[str, Any]:
    lane_policy = load_json(ASSET_PATHS["lane_policy"])
    runner_source = (ROOT / "scripts" / "v50_run_vnext_phase0_benchmark.py").read_text(encoding="utf-8")
    reasoner_source = inspect.getsource(__import__("core.mingli_agent.reasoner", fromlist=["MingliAgent"]).MingliAgent)
    checks = {
        "lane_policy_forbids_semantic_repair": lane_policy["execution_policy"].get("semantic_repair_allowed") is False,
        "runner_enables_p0_audit_only": "p0_audit_only=True" in runner_source,
        "reasoner_has_isolated_p0_mode": "self.p0_audit_only" in reasoner_source,
        "raw_output_field_present": '"raw_cognitive_output"' in runner_source,
        "raw_output_hash_present": '"raw_cognitive_output_sha256"' in runner_source,
        "review_annotations_separate": '"review_annotations"' in runner_source,
    }
    return {
        "version": "deepbazi.vnext_phase0.repair_authority_audit.v1",
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "p0_allowed_repairs": [
            "json_object_extraction",
            "schema_validation",
            "whitespace_key_normalization",
            "declared_alias_or_enum_normalization",
        ],
        "p0_forbidden_repairs": [
            "hypothesis_rewrite",
            "work_path_rewrite",
            "useful_or_harmful_role_rewrite",
            "domain_claim_rewrite",
            "causal_rewrite",
            "confidence_rewrite",
            "counterevidence_rewrite",
            "local_llm_repair",
        ],
        "production_repair_behavior_changed": False,
    }


def audit_modality_policy() -> dict[str, Any]:
    policy = load_json(ASSET_PATHS["modality_policy"])
    fixtures = load_json(ASSET_PATHS["development_fixture_pack"])
    birth = dict(fixtures["cases"][0]["birth_input"])
    birth["birth_time"] = "12:00"
    world = compile_chart_world(
        reading_id="g1-7-modality-audit",
        birth_input=BirthInputCanonical.model_validate(birth),
        include_research_fixture_prior=False,
    )
    samples = {
        "命局明确存在子午冲。": "asserted_natal_fact",
        "因此可见命局存在子午冲。": "derived_natal_claim",
        "这可能形成子午冲。": "hypothesis",
        "如果形成子午冲，则需要观察。": "counterfactual",
        "流年遇午可能引动子午冲。": "timing_condition",
        "是否存在子午冲？": "question",
        "用户说：“命局存在子午冲。”": "quoted_claim",
    }
    rows = []
    for text, expected in samples.items():
        actual = classify_claim_modality(text=text, start=text.index("子午冲"))
        conflicts = deterministic_fact_conflicts(text=text, world=world)
        rows.append({"text": text, "expected": expected, "actual": actual, "fact_conflicts": conflicts})
    eligible = set(policy["natal_fact_conflict_eligible"])
    passed = (
        all(row["expected"] == row["actual"] for row in rows)
        and all(bool(row["fact_conflicts"]) == (row["expected"] in eligible) for row in rows)
        and set(policy["modalities"]) == {row["expected"] for row in rows}
    )
    return {
        "version": "deepbazi.vnext_phase0.modality_policy_audit.v1",
        "status": "passed" if passed else "failed",
        "policy_status": policy["status"],
        "natal_fact_conflict_eligible": sorted(eligible),
        "fixed_regression_cases": rows,
    }


def audit_human_reference_freeze() -> dict[str, Any]:
    validation = _asset_validation()
    expert = load_json(ASSET_PATHS["expert_reference"])
    frozen_rows = [row["chart_id"] for row in expert["references"] if row.get("status") == "frozen"]
    return {
        "version": "deepbazi.vnext_phase0.human_reference_freeze_status.v1",
        "status": "frozen" if validation["expert_reference_frozen"] else "pending_human_freeze",
        "human_authorship_required": True,
        "llm_authorship_allowed": False,
        "formal_chart_count": len(validation["formal_ids"]),
        "frozen_chart_count": len(frozen_rows),
        "frozen_chart_ids": frozen_rows,
        "reality_evidence_present": False,
        "source_outputs_visible_to_author": False,
    }


def audit_frontier_policy_freeze() -> dict[str, Any]:
    policy = load_json(ASSET_PATHS["frontier_policy"])
    selection = load_json(ASSET_PATHS["model_selection_set"])
    frozen = policy.get("status") == "frozen" and bool(policy.get("selected_policy"))
    return {
        "version": "deepbazi.vnext_phase0.frontier_policy_freeze_status.v1",
        "status": "frozen" if frozen else "pending_true_frontier_selection",
        "selected_policy": policy.get("selected_policy"),
        "candidate_count": len(policy.get("candidate_policies", [])),
        "selection_chart_count": len(selection["cases"]),
        "selection_chart_ids": [row["case_id"] for row in selection["cases"]],
        "formal_or_development_charts_allowed": False,
        "local_open_stress_promoted": False,
    }


def _asset_validation() -> dict[str, Any]:
    return validate_phase0_assets(
        taxonomy_path=ROOT / "data" / "validation" / "fixtures" / "synthetic_chart_taxonomy_v2.json",
        development_path=ASSET_PATHS["development_set"],
        model_selection_path=ASSET_PATHS["model_selection_set"],
        formal_manifest_path=ASSET_PATHS["formal_manifest"],
        expert_reference_path=ASSET_PATHS["expert_reference"],
        reality_evidence_path=ASSET_PATHS["reality_evidence"],
    )


def _master_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# VNext Phase 0 P0-G1.7 Master Audit Report",
            "",
            f"- Status: `{report['status']}`",
            "- Ready for P0-G2: `false`",
            "- Formal run started: `false`",
            "- Sealed chart accessed: `false`",
            "",
            "## Machine Gates",
            "",
            *[f"- {name}: `{'passed' if value else 'failed'}`" for name, value in report["machine_gates"].items()],
            "",
            "## External Freeze Gates",
            "",
            *[f"- {name}: `{'passed' if value else 'pending'}`" for name, value in report["external_gates"].items()],
            "",
            "## Blockers",
            "",
            *[f"- `{item}`" for item in report["blockers"]],
            "",
            "## Data, Interpretation, Recommendation",
            "",
            f"- Observed: {report['observed_interpretation_recommendation']['observed']}",
            f"- Interpretation: {report['observed_interpretation_recommendation']['interpretation']}",
            f"- Recommendation: {report['observed_interpretation_recommendation']['recommendation']}",
            "",
            "## Boundary Status",
            "",
            "```json",
            json.dumps(report["boundary_status"], ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )


def _analyst_packet(report: dict[str, Any]) -> str:
    reference = report["observed_data"]["human_expert_reference"]
    frontier = report["observed_data"]["frontier_policy"]
    snapshot = report["observed_data"]["snapshot"]
    return f"""# Analyst Review Packet - P0-G1.7

## Resolved policy decisions

```yaml
direct_frontier_prompt: strong_direct_power_user_one_shot_v1
direct_receives_internal_seven_stage_protocol: false
p0_semantic_repair_allowed: false
raw_cognitive_output_immutable: true
review_annotations_separate: true
modality_taxonomy_frozen: true
```

## Remaining hard gates

```yaml
human_reference: {reference['status']}
human_reference_frozen_charts: {reference['frozen_chart_count']}/{reference['formal_chart_count']}
frontier_policy: {frontier['status']}
frontier_candidates: {frontier['candidate_count']}
clean_snapshot: {snapshot['status']}
final_nonsealed_live_preflight: {report['observed_data']['final_nonsealed_live_preflight']['status']}
p0_g2_started: false
```

No professional winner or VNext capability claim is authorized by this packet.
"""


def _human_reference_guide() -> str:
    return """# Human Expert Reference Freeze Guide - P0-G1.7

The ten-chart file is an acceptable cognition space, not a canonical report. Only a human Mingli expert may author its semantic content.

For each chart, freeze: must-notice structure, acceptable primary hypotheses, strongest alternative, rejected interpretations, plausible and blocked work paths, conditional useful/harmful roles, portrait distinctions, career/wealth prior expectations, unsupported claims, and unresolved disputes.

Every expectation needs a reason and a chart-fact reference. Reality evidence, model outputs, Probe answers, known occupations, historical years, and LLM-authored professional content remain prohibited. The machine may validate completeness and hashes only.
"""


def _frontier_guide() -> str:
    return """# Frontier Policy Selection Guide - P0-G1.7

Use only the five isolated model-policy selection charts. Compare complete reproducible policies, not model names alone: provider/model version, prompt hash, reasoning mode, sampling, token/context budget, timeout, retry, structured output, mechanical repair, raw retention, latency, and cost.

Direct Frontier receives only pillars, gender, and the frozen strong power-user request. It receives no DeepBazi fact ledger, Graph/Path/Role/Ablation, retrieval, examples, Challenge Pack, Expert Reference, Reality Evidence, or staged state. Selection requires human judgment of professional cognition and three-run stability; schema compliance alone cannot select a policy.
"""


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _unique(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        if value not in output:
            output.append(value)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare VNext Phase 0 P0-G1.7 freeze gates without live execution.")
    parser.add_argument("--run-id", default="phase0-g1-7-freeze-v1")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    report = prepare_g1_7(run_id=args.run_id, output_dir=Path(args.output_dir))
    print(json.dumps({"status": report["status"], "ready_for_p0_g2": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
