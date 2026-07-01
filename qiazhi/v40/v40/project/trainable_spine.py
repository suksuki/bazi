from __future__ import annotations

from v40.contracts.training import TrainableUnitType


IMMUTABLE_FACT_MODULES: tuple[str, ...] = (
    "bazi_four_pillars",
    "stems_branches",
    "ten_god_base_mapping",
    "hidden_stems",
    "solar_terms",
    "luck_cycles",
    "annual_flow",
    "branch_relations",
    "ziwei_palaces",
    "ziwei_stars",
    "ziwei_four_transformations",
)

TRAINABLE_MODULES: tuple[dict[str, object], ...] = (
    {
        "module": "rule_engine",
        "trainable": ["rule_weight", "source_weight", "condition_bonus", "condition_penalty"],
        "not_trainable": ["rule evidence facts", "chart facts"],
    },
    {
        "module": "path_engine",
        "trainable": ["path_weight", "path_edge_weight", "blocker_penalty", "bridge_bonus", "activation_bonus"],
        "not_trainable": ["original chart structure"],
    },
    {
        "module": "domain_verdict_adapter",
        "trainable": ["claim_score", "conflict_policy", "assertion_threshold", "domain branch ranking"],
        "not_trainable": ["final verdict authority outside DecisionEngine"],
    },
    {
        "module": "hidden_factor_probe_engine",
        "trainable": ["probe_voi", "probe_trigger_condition", "probe_option_mapping", "fatigue_cost"],
        "not_trainable": ["asking without information gain"],
    },
    {
        "module": "advice_engine",
        "trainable": ["advice_priority", "advice_domain_fit", "advice_actionability_score"],
        "not_trainable": ["advice detached from verdict evidence"],
    },
    {
        "module": "llm_expression",
        "trainable": ["llm_acceptance", "prompt_policy", "style_policy", "repair_strategy"],
        "not_trainable": ["verdict authority", "chart facts"],
    },
)


def build_trainable_runtime_spine_status() -> dict[str, object]:
    return {
        "version": "v40.trainable_runtime_spine_status.v1",
        "phase": "V40-RC2: Trainable Runtime Spine",
        "principle": "fact modules are validated, judgment modules train policy units only",
        "immutable_fact_modules": list(IMMUTABLE_FACT_MODULES),
        "trainable_unit_types": [unit_type.value for unit_type in TrainableUnitType],
        "trainable_modules": list(TRAINABLE_MODULES),
        "feedback_flow": [
            "RuntimeSignal emits trainable_refs",
            "TrainingLabelEvent records user/probe/practitioner/admin/real outcome feedback",
            "TrainingAttribution maps feedback to signals, branches, verdicts, advice, probes and trainable_refs",
            "LocalOverlay updates current reading first",
            "BatchTrainerV1 creates active policy versions immediately",
            "TrainingImpactDiff explains changed weights, thresholds, verdicts, advice and probes",
            "Previous registry and impact diff support rollback or corrective next training",
        ],
        "hard_gates": [
            "Do not train chart facts",
            "Do allow fast policy iteration, but always keep rollback and impact evidence",
            "Do not let LLM become the mingli training target",
            "Every active update must be replayable, explainable and rollbackable",
            "Every active policy should be continuously checked by golden, regression, overclaim, advice grounding, probe yield, leakage and LLM boundary gates",
        ],
        "contracts": [
            "TrainableUnit",
            "TrainablePolicyRegistry",
            "TrainingAttribution",
            "BatchTrainerV1Result",
            "RuntimeSignal.trainable_refs",
            "TrainingLabelEvent.affected_trainable_refs",
            "LocalOverlay",
            "TrainingImpactDiff",
            "ReleaseGateResult",
        ],
        "implemented_capabilities": [
            "BatchTrainerV1 deterministic active policy builder",
            "Active TrainablePolicyRegistry output",
            "TrainablePolicyRegistry persistence and Admin read model",
            "RuntimeResult policy_version_used trace",
            "Direct effect after training with rollback registry pointer",
            "TrainingImpactDiff output from aggregated attribution",
            "Fact refs skipped during batch training",
            "Local feedback downweighted until batch validation",
        ],
        "next_steps": [
            "Add before/after active policy diff to Acceptance Window",
            "Allow Admin to run BatchTrainerV1 from selected replay batches",
            "Add explicit rollback-to-previous-registry action",
        ],
        "boundary": "trainable_runtime_spine_trains_policy_not_facts",
    }
