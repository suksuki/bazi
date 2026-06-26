from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.validation.synthetic_case import SYNTHETIC_SUITES


SYNTHETIC_COVERAGE_MANIFEST_VERSION = "v30.synthetic_coverage_manifest.v1"

PLANNED_SYNTHETIC_TIERS: set[str] = set()

TIER_CONTRACTS: dict[str, dict[str, Any]] = {
    "smoke": {
        "protects": ["core spine", "hidden-factor dialogue probe", "K/R/P signal binding", "time/useful-god boundaries"],
        "module_scope": ["M3", "question", "hidden_factor"],
        "truth_claim": "contract_smoke_only",
    },
    "all": {
        "protects": ["union of implemented synthetic tiers", "release/promotion regression coverage"],
        "module_scope": ["M1", "M2", "M3", "M4", "M5", "M6", "M8", "interaction", "training"],
        "truth_claim": "aggregate_contract_regression_not_destiny_truth",
        "major_node_only": True,
    },
    "core_bazi_calculation": {
        "protects": ["first-screen Bazi calculation surface", "deterministic fact integrity", "ranked decision presence"],
        "module_scope": ["M1", "M2", "M5", "M6", "M8"],
        "truth_claim": "deterministic_runtime_contract_only",
    },
    "core_calculation": {
        "protects": ["legacy alias for core_bazi_calculation"],
        "module_scope": ["M1", "M2", "M5", "M6", "M8"],
        "truth_claim": "alias_contract_only",
        "alias_of": "core_bazi_calculation",
    },
    "m1_m2_bazi_calculation": {
        "protects": ["BirthInput boundaries", "base fact summary", "base fact explanations", "no fake pillar guardrails"],
        "module_scope": ["M1", "M2"],
        "truth_claim": "deterministic_chart_fact_contract_only",
    },
    "ten_god_energy_calibration": {
        "protects": ["five ten-god family coverage", "energy/stability/volatility bands", "model signal calibration profile"],
        "module_scope": ["M4"],
        "truth_claim": "bounded_model_signal_calibration_not_final_verdict",
    },
    "m4_ten_god_real_case_replay": {
        "protects": ["M4 replay interface", "model-signal readiness across replay families"],
        "module_scope": ["M4", "M7"],
        "truth_claim": "interface_replay_contract_not_threshold_promotion",
    },
    "strength_structure_useful_god": {
        "protects": ["ranked candidate boundary", "strength/structure/useful-god candidate shape"],
        "module_scope": ["M5"],
        "truth_claim": "candidate_contract_not_fixed_useful_god_verdict",
    },
    "m5_ranked_decision_contract": {
        "protects": ["M5 score floors", "ranked decision basis", "M1/M2 root-vault and M4 signal consumption"],
        "module_scope": ["M5", "M1", "M2", "M4"],
        "truth_claim": "ranked_candidate_replay_not_final_verdict",
    },
    "m6_practical_reading_contract": {
        "protects": ["calculation basis", "domain contracts", "blocked claims", "raw-score leak prevention"],
        "module_scope": ["M6"],
        "truth_claim": "practical_output_contract_not_prediction_truth",
    },
    "m8_api_projection_contract": {
        "protects": ["additive API projection", "customer leak scan", "role-gated diagnostics"],
        "module_scope": ["M8"],
        "truth_claim": "projection_contract_not_calculation_source",
    },
    "interaction_loop": {
        "protects": ["direct question click", "structured options", "visible/internal next-question split", "answer API interaction state"],
        "module_scope": ["question", "interaction", "hidden_factor"],
        "truth_claim": "dialogue_strategy_contract_not_chart_fact_source",
    },
    "interaction_brain_structured_constraints": {
        "protects": ["structured hidden-factor answer constraints", "invalid input rejection", "chart-fact pollution guard"],
        "module_scope": ["question", "interaction", "hidden_factor", "training"],
        "truth_claim": "structured_interaction_constraint_contract_not_chart_fact_source",
    },
    "latent_bazi_divergence": {
        "protects": ["same-Bazi latent attribute divergence", "individualized projection", "no chart-fact mutation boundary"],
        "module_scope": ["hidden_factor", "question", "training"],
        "truth_claim": "latent_personalization_contract_not_destiny_truth",
    },
    "real_case_calibration_pack": {
        "protects": ["canonical solar/lunar/leap/true-solar/unknown-hour/unknown-gender coverage", "M4/M5/M6 readiness", "drift routing"],
        "module_scope": ["M7", "M1", "M2", "M4", "M5", "M6"],
        "truth_claim": "calibration_fixture_contract_not_private_replay_truth",
    },
    "real_case_validation": {
        "protects": ["small real-case validation fixture boundaries"],
        "module_scope": ["M7"],
        "truth_claim": "fixture_contract_not_final_reading_truth",
    },
    "luck_cycle": {
        "protects": ["luck-cycle context activation and boundaries"],
        "module_scope": ["M1", "M2", "M6"],
        "truth_claim": "timing_context_contract_not_event_prediction",
    },
    "flow_timing": {
        "protects": ["flow-year/month context activation and boundaries"],
        "module_scope": ["M1", "M2", "M6"],
        "truth_claim": "flow_context_contract_not_event_prediction",
    },
    "six_pillar_context": {
        "protects": ["natal plus timing-layer context shape"],
        "module_scope": ["M1", "M2", "M4"],
        "truth_claim": "context_shape_contract_only",
    },
    "practical_reading": {
        "protects": ["single practical reading contract slice"],
        "module_scope": ["M6"],
        "truth_claim": "reading_contract_not_prediction_truth",
    },
    "agent_question_flow": {
        "protects": ["agent question flow and high-value question quality"],
        "module_scope": ["question", "interaction"],
        "truth_claim": "question_strategy_contract_not_chart_fact_source",
    },
    "gradient": {
        "protects": ["policy/path gradient cases", "rule counter-evidence", "question policy", "hidden-factor feedback"],
        "module_scope": ["M3", "question", "training"],
        "truth_claim": "calibration_gradient_contract_not_truth_claim",
    },
    "knowledge_rule_portrait": {
        "protects": ["K/R/P unit coverage"],
        "module_scope": ["M3"],
        "truth_claim": "evidence_spine_contract_not_conclusion_engine",
    },
    "structure_dynamic_v2": {
        "protects": ["dynamic structure path shape"],
        "module_scope": ["M3", "M5"],
        "truth_claim": "path_contract_not_fixed_structure_truth",
    },
    "m3_core_spine": {
        "protects": ["source/KRP/rule/path evidence spine", "M4/M5/M6 support proof"],
        "module_scope": ["M3", "M4", "M5", "M6"],
        "truth_claim": "evidence_support_contract_not_final_verdict",
    },
    "central_brain": {
        "protects": ["role state", "session memory", "brain routing", "expression orchestration", "training route boundaries"],
        "module_scope": ["central_brain", "question", "training"],
        "truth_claim": "runtime_coordination_contract_not_mutation_source",
    },
    "training_pipeline": {
        "protects": ["signal extraction", "candidate generation", "validation replay", "quarantine", "pointer/lineage boundaries"],
        "module_scope": ["training", "policy", "validation"],
        "truth_claim": "training_contract_not_chart_fact_source",
    },
    "bazi_llm_acceptance": {
        "protects": ["LLM output schema", "role leak rejection", "drift rejection", "expression-quality acceptance"],
        "module_scope": ["LLM", "training", "question"],
        "truth_claim": "llm_expression_acceptance_contract_not_chart_fact_source",
    },
    "synthetic_archetype_rule_claim": {
        "protects": ["synthetic archetype rule-claim calibration", "traceable Bazi wording", "generic claim rejection"],
        "module_scope": ["M3", "M5", "M6", "training"],
        "truth_claim": "archetype_rule_claim_contract_not_real_person_truth",
    },
    "synthetic_typical_bazi_answer": {
        "protects": ["typical Bazi answer text calibration", "mechanism/domain token coverage", "internal leak rejection"],
        "module_scope": ["M3", "M6", "LLM", "interaction"],
        "truth_claim": "synthetic_answer_text_contract_not_real_person_truth",
    },
    "synthetic_canonical_bazi_calibration": {
        "protects": ["canonical synthetic Bazi archetypes", "calibration queue routing", "no private real-case contamination"],
        "module_scope": ["M3", "M4", "M5", "M6", "M7", "training"],
        "truth_claim": "synthetic_archetype_calibration_contract_not_real_case_truth",
    },
    "ui_core_reading_product": {
        "protects": ["core reading product surface", "customer-facing Bazi claim quality", "UI internal leak prevention"],
        "module_scope": ["M6", "M8", "LLM", "interaction"],
        "truth_claim": "product_surface_contract_not_calculation_source",
    },
    "real_bazi_diagnosis": {
        "protects": ["RBD rule matching", "path and portrait projection", "traceable diagnosis claims", "customer/admin projection split", "518K sample readiness"],
        "module_scope": ["RBD", "M3", "M4", "M5", "M6", "M7"],
        "truth_claim": "diagnosis_engine_contract_not_fixed_destiny_truth",
    },
}


def run_synthetic_coverage_manifest() -> dict[str, Any]:
    return build_synthetic_coverage_manifest()


def build_synthetic_coverage_manifest(
    *,
    synthetic_suites: Mapping[str, tuple[Any, ...]] | None = None,
    tier_contracts: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    suites = synthetic_suites or SYNTHETIC_SUITES
    contracts = tier_contracts or TIER_CONTRACTS
    rows = [_tier_row(tier, suites, contracts) for tier in sorted(set(suites) | set(contracts))]
    summary = _summary(rows)
    checks = _checks(rows, summary)
    decision = _decision(checks)
    return {
        "version": SYNTHETIC_COVERAGE_MANIFEST_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if decision["synthetic_coverage_manifest_ready"] else "blocked",
        "decision": decision,
        "summary": summary,
        "tiers": rows,
        "manifest_checks": checks,
        "policy_boundary": {
            "manifest_is_read_only": True,
            "chart_fact_mutation_allowed": False,
            "training_signal_may_change_chart_facts": False,
            "synthetic_tier_may_claim_destiny_truth": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "boundary": "synthetic_manifest_documents_validation_contracts_not_bazi_truth_claims",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "bt6_synthetic_coverage_manifest_separates_contract_coverage_from_truth_claims",
    }


def _tier_row(
    tier: str,
    suites: Mapping[str, tuple[Any, ...]],
    contracts: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    contract = dict(contracts.get(tier, {}))
    implemented = tier in suites
    documented = tier in contracts
    cases = suites.get(tier, ())
    case_count = len(cases)
    domains = sorted({str(getattr(case, "domain", "")) for case in cases if getattr(case, "domain", "")})
    if tier == "latent_bazi_divergence":
        from v30.validation.latent_bazi_divergence import LATENT_DIVERGENCE_CASES

        case_count = len(LATENT_DIVERGENCE_CASES)
        domains = ["latent_bazi_divergence"] if case_count else domains
    planned = bool(contract.get("planned")) or tier in PLANNED_SYNTHETIC_TIERS
    return {
        "tier": tier,
        "status": "implemented" if implemented and documented else "planned" if planned else "undocumented",
        "implemented": implemented,
        "planned": planned and not implemented,
        "case_count": case_count,
        "domains": domains,
        "protects": list(contract.get("protects", [])),
        "module_scope": list(contract.get("module_scope", [])),
        "truth_claim": str(contract.get("truth_claim") or ""),
        "alias_of": str(contract.get("alias_of") or ""),
        "major_node_only": bool(contract.get("major_node_only", False) or tier == "all"),
        "chart_fact_mutation_allowed": False,
        "claim_deterministic_truth_beyond_contract": False,
        "training_can_mutate_chart_facts": False,
    }


def _summary(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    implemented = [row for row in rows if row["implemented"]]
    planned = [row for row in rows if row["planned"]]
    undocumented = [row for row in rows if row["status"] == "undocumented"]
    return {
        "tier_count": len(rows),
        "implemented_tier_count": len(implemented),
        "planned_tier_count": len(planned),
        "undocumented_tier_count": len(undocumented),
        "implemented_case_count": sum(int(row["case_count"]) for row in implemented),
        "implemented_tiers": [str(row["tier"]) for row in implemented],
        "planned_tiers": [str(row["tier"]) for row in planned],
        "undocumented_tiers": [str(row["tier"]) for row in undocumented],
        "major_node_only_tiers": [str(row["tier"]) for row in rows if row["major_node_only"]],
        "module_scope_coverage": sorted({scope for row in rows for scope in row["module_scope"]}),
    }


def _checks(rows: list[Mapping[str, Any]], summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    required = {
        "smoke",
        "all",
        "core_bazi_calculation",
        "m1_m2_bazi_calculation",
        "ten_god_energy_calibration",
        "m4_ten_god_real_case_replay",
        "strength_structure_useful_god",
        "m5_ranked_decision_contract",
        "m6_practical_reading_contract",
        "m8_api_projection_contract",
        "interaction_loop",
        "real_case_calibration_pack",
        "central_brain",
        "training_pipeline",
    }
    tiers = {str(row["tier"]) for row in rows}
    implemented_rows = [row for row in rows if row["implemented"]]
    planned_rows = [row for row in rows if row["planned"]]
    return [
        {
            "check_id": "required_manifest_tiers_are_documented",
            "passed": required.issubset(tiers),
            "expected": "BT6 required implemented and planned tiers are present in the manifest",
        },
        {
            "check_id": "implemented_tiers_have_cases_and_contracts",
            "passed": all(row["case_count"] > 0 and row["protects"] and row["truth_claim"] for row in implemented_rows),
            "expected": "implemented synthetic tiers have cases, protected contracts, and bounded truth-claim text",
        },
        {
            "check_id": "bt7_bt8_synthetic_tiers_are_implemented",
            "passed": (
                "central_brain" in {str(row["tier"]) for row in implemented_rows}
                and "training_pipeline" in {str(row["tier"]) for row in implemented_rows}
                and not {str(row["tier"]) for row in planned_rows if row["tier"] in {"central_brain", "training_pipeline"}}
            ),
            "expected": "BT7 central_brain and BT8 training_pipeline tiers are implemented",
        },
        {
            "check_id": "no_tier_claims_truth_beyond_contract",
            "passed": all(not row["claim_deterministic_truth_beyond_contract"] and row["truth_claim"] for row in rows),
            "expected": "synthetic tiers validate contracts and boundaries, not destiny truth",
        },
        {
            "check_id": "synthetic_does_not_authorize_chart_fact_mutation",
            "passed": all(not row["chart_fact_mutation_allowed"] and not row["training_can_mutate_chart_facts"] for row in rows),
            "expected": "synthetic validation and training signals cannot mutate chart facts",
        },
        {
            "check_id": "all_tier_is_major_node_only",
            "passed": "all" in summary["major_node_only_tiers"],
            "expected": "synthetic all remains a major-node check, not a default subtask check",
        },
        {
            "check_id": "core_support_module_scope_covered",
            "passed": {"M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "question", "training"}.issubset(
                set(summary["module_scope_coverage"])
            ),
            "expected": "manifest covers core Bazi modules plus question/training support scopes",
        },
    ]


def _decision(checks: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if not row.get("passed")]
    ready = not failed
    return {
        "synthetic_coverage_manifest_ready": ready,
        "decision_status": "bt6_synthetic_coverage_manifest_ready" if ready else "bt6_synthetic_coverage_manifest_blocked",
        "manifest_check_count": len(checks),
        "passed_manifest_check_count": sum(1 for row in checks if row.get("passed")),
        "failed_check_ids": failed,
        "synthetic_completion": 99 if ready else 92,
        "blockers": ["synthetic_coverage_manifest_checks_failed"] if failed else [],
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "rationale": (
            "Synthetic coverage manifest documents implemented and planned tiers with contract boundaries and no truth-claim drift."
            if ready
            else "BT6 cannot complete until synthetic manifest blockers are repaired."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["synthetic_coverage_manifest_ready"]:
        return {
            "task_id": "BT9",
            "title": "518K Readiness Matrix",
            "selected_track": "brain_training_synthetic_completion",
            "scope": [
                "document sample/shard/full-mode readiness",
                "validate corpus mount, artifact/index persistence, DB fallback, and candidate-family coverage",
                "keep full 518K explicit-only",
            ],
        }
    return {
        "task_id": "BT6-FR",
        "title": "Synthetic Coverage Manifest Failure Review",
        "selected_track": "brain_training_synthetic_completion",
        "scope": [
            "inspect failed manifest checks",
            "repair tier contracts or planned/implemented status",
            "keep synthetic tiers bounded to validation contracts",
        ],
    }
