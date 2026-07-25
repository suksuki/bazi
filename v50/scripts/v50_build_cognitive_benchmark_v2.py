from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/validation/fixtures/synthetic_chart_taxonomy_v2.json"
TARGET = ROOT / "data/validation/fixtures/cognitive_benchmark_matrix_v2.json"


DEVELOPMENT_FAMILIES = [
    "archetype.month_command_dominant",
    "archetype.bridge_node_dominant",
    "archetype.converter_dominant",
    "archetype.day_branch_anchor",
    "archetype.hidden_stem_dark_line",
    "archetype.output_to_wealth",
    "archetype.output_controls_pressure",
    "archetype.resource_disrupts_output",
    "archetype.mixed_officer_killing_with_control",
    "archetype.wealth_generates_officer",
    "archetype.peer_competes_for_wealth",
    "archetype.mixed_no_obvious_main_path",
]

HOLDOUT_FAMILIES = [
    "archetype.complete_triple_combination",
    "archetype.broken_triple_combination",
    "archetype.clash_breaks_main_path",
    "archetype.half_triple_combination",
    "archetype.resource_peer_overload_output_blocked",
    "archetype.climate_regulation_dominant",
    "archetype.mediation_path",
    "archetype.month_risk_pulse",
]

CHALLENGE_FAMILIES = [
    "archetype.luck_changes_main_path",
    "archetype.year_activates_key_node",
    "archetype.timing_insufficient",
    "archetype.unsupported_relationship_domain",
    "archetype.unsupported_health_domain",
]


def build_matrix() -> dict[str, object]:
    taxonomy = json.loads(SOURCE.read_text(encoding="utf-8"))
    cases = taxonomy["cases"]
    by_family: dict[str, list[str]] = {}
    for case in cases:
        by_family.setdefault(case["structure_archetype_id"], []).append(case["case_id"])

    expected_families = {*DEVELOPMENT_FAMILIES, *HOLDOUT_FAMILIES, *CHALLENGE_FAMILIES}
    if set(by_family) != expected_families:
        missing = sorted(set(by_family) - expected_families)
        unknown = sorted(expected_families - set(by_family))
        raise ValueError(f"benchmark family assignment mismatch: unassigned={missing}, unknown={unknown}")
    if any(len(case_ids) != 3 for case_ids in by_family.values()):
        raise ValueError("v2 requires exactly three controlled hour variants per family")

    def split(families: list[str]) -> dict[str, object]:
        return {
            "family_ids": families,
            "case_ids": [case_id for family in families for case_id in sorted(by_family[family])],
        }

    return {
        "version": "deepbazi.cognitive_benchmark_matrix.v2",
        "source_fixture": SOURCE.name,
        "split_policy": "structure_family_isolation",
        "development": split(DEVELOPMENT_FAMILIES),
        "holdout": split(HOLDOUT_FAMILIES),
        "challenge": split(CHALLENGE_FAMILIES),
        "controlled_variant_groups": [
            {
                "family_id": family,
                "case_ids": sorted(case_ids),
                "variation_axis": "hour_pillar_controlled_variant",
                "expected_invariant": "family-level candidate contract",
                "allowed_changes": ["hour_pillar_facts", "hour_derived_relations", "path_and_attention_details"],
            }
            for family, case_ids in sorted(by_family.items())
        ],
        "capability_matrix": [
            {"capability_id": "fact_fidelity", "method": "deterministic_fact_check", "hard_gate": True},
            {"capability_id": "synthetic_answer_isolation", "method": "context_leak_scan", "hard_gate": True},
            {"capability_id": "pattern_attention", "method": "attention_receipt_and_expert_review", "hard_gate": False},
            {"capability_id": "competing_hypotheses", "method": "schema_and_omission_review", "hard_gate": True},
            {"capability_id": "causal_work_path", "method": "fact_grounded_causal_chain_review", "hard_gate": True},
            {"capability_id": "counter_evidence", "method": "falsifier_and_alternative_check", "hard_gate": True},
            {"capability_id": "closed_domain_boundary", "method": "challenge_cases", "hard_gate": True},
            {"capability_id": "semantic_specificity", "method": "cross_case_repetition_and_claim_specificity", "hard_gate": False},
        ],
        "blind_gate": {
            "expected_contract_visible_to_model": False,
            "same_structure_family_may_cross_splits": False,
            "candidate_contract_counts_as_expert_gold": False,
            "expert_gold_count": 0,
            "ready_for_weight_training": False,
            "allowed_training_now": ["knowledge_curation", "retrieval_calibration", "algorithm_calibration"],
        },
        "boundaries": {
            "engine_mutation_allowed_during_benchmark": False,
            "prompt_tuning_on_holdout_allowed": False,
            "automatic_theory_promotion_allowed": False,
            "training_performed": False,
        },
    }


def main() -> None:
    matrix = build_matrix()
    TARGET.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "written", "path": str(TARGET)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
