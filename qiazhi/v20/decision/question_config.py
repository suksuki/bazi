from __future__ import annotations

from v20.interaction.question_seed_registry import SEED_QUESTION_STRATEGY


QUESTION_KEY_BY_DOMAIN = {
    "strength": "q_strength_assessment",
    "wealth": "q_income_stability",
    "career": "q_career_structure",
    "ten_god": "q_ten_god_focus",
    "branch": "q_branch_relation_detail",
    "time": "q_time_layer_context",
    "element": "q_element_balance",
    "useful_god": "q_useful_god_candidates",
    "pattern": "q_pattern_structure",
    "relationship": "q_relationship_structure",
    "health": "q_health_balance_boundary",
}

QUESTION_STRATEGY = {
    "default": "default",
    "decision_mainline": "mainline",
    "decision_hit": "decision_hit",
    "runtime_fusion": "runtime_fusion",
    "feature_hook": "feature_hook",
    "feature_context": "feature_context",
    "portrait_axis": "portrait_axis",
    "secondary": "secondary",
    "knowledge_output": "knowledge_output",
    "time_context": "time_context",
    "practitioner_refresh": "practitioner_refresh",
    "latent_event": "latent_event",
    "mainline_candidate": "mainline_candidate",
    "seed_registry": SEED_QUESTION_STRATEGY,
    "fallback": "fallback",
}

QUESTION_KEY_RULE_PREFIX = {
    "q_useful_god_candidates": "rule.useful_god.",
    "q_useful_god_evidence_gaps": "rule.useful_god.",
    "q_strength_assessment": "rule.strength.",
    "q_income_stability": "rule.wealth.",
    "q_income_factors": "rule.wealth.",
    "q_career_structure": "rule.career.",
    "q_ten_god_focus": "rule.ten_god.",
    "q_ten_god_metadata": "rule.ten_god.",
    "q_hidden_stem_role": "rule.ten_god.",
    "q_branch_relation_detail": "rule.branch.",
    "q_time_layer_context": "rule.time.",
    "q_time_relation_triggers": "rule.time.",
    "q_element_balance": "rule.element.",
    "q_element_support_pressure": "rule.element.",
    "q_pattern_structure": "rule.pattern.",
    "q_relationship_structure": "rule.relationship.",
    "q_health_balance_boundary": "rule.health.",
}

FEATURE_MATERIAL_MAX = 2

TECHNICAL_TERM_HINTS = (
    "证据",
    "evidence.",
    "decision.",
    "rulespec",
    "rule.",
    "应如何进入八字测算",
    "需复核",
    "条件成立",
    "材料",
    "反证",
    "边界",
    "纳入裁决",
    "先复核",
    "需要哪些证据",
    "Pattern review index",
    "Pattern",
    "review index",
    "ten-god",
    "ten god",
    "chart-specific",
    "focus is",
    "available",
)

CONTROL_DOMAIN = {
    "control.day_master_strength": "strength",
    "control.shang_guan_jian_guan": "career",
    "control.wealth_capacity": "wealth",
    "control.pattern_status": "pattern",
}

LATENT_SCENARIO_DOMAIN = {
    "latent.wealth_change": "wealth",
    "latent.career_transition": "career",
    "latent.relationship_shift": "relationship",
    "latent.relocation_environment": "time",
    "latent.stress_recovery": "health",
    "latent.action_result": "strength",
}
