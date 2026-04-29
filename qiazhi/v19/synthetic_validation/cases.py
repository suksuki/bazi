from __future__ import annotations

from v19.synthetic_validation.schema import SyntheticCase


DEFAULT_FORBIDDEN_OUTPUTS = [
    "wealth_type",
    "score",
    "conclusion",
    "narrative",
    "free_text",
    "domain_conclusion",
]


DEFAULT_DOMAIN_EXPECTATIONS = {
    "kind": "DomainAdapterInput",
    "domain": "wealth",
    "wealth_signals.competition_pressure.source_signal": "internal_conflicts.peer_vs_wealth",
    "wealth_signals.stability.source_signal": "structural_stability.state",
    "guardrails": {"contains": "NO_NEW_INFERENCE"},
}


DEFAULT_SYNTHETIC_CASES = [
    SyntheticCase(
        case_id="synthetic.strong_day_master",
        chart={
            "chart_id": "synthetic.strong_day_master",
            "four_pillars": {"year": "戊辰", "month": "丁巳", "day": "戊午", "hour": "丙辰"},
        },
        expected_inference_signals={
            "day_master_state.tendency": {"in": ["strong", "leaning_strong"]},
            "ten_god_structure.peer.strength": {"in": ["medium", "strong"]},
        },
        expected_domain_adapter_outputs=DEFAULT_DOMAIN_EXPECTATIONS,
        forbidden_outputs=DEFAULT_FORBIDDEN_OUTPUTS,
        tags=["strength", "strong_day_master", "身强"],
    ),
    SyntheticCase(
        case_id="synthetic.weak_day_master",
        chart={
            "chart_id": "synthetic.weak_day_master",
            "four_pillars": {"year": "甲寅", "month": "壬子", "day": "戊申", "hour": "癸亥"},
        },
        expected_inference_signals={
            "day_master_state.tendency": {"in": ["weak", "leaning_weak", "following_tendency_possible"]},
            "ten_god_structure.officer.strength": {"in": ["medium", "strong"]},
        },
        expected_domain_adapter_outputs=DEFAULT_DOMAIN_EXPECTATIONS,
        forbidden_outputs=DEFAULT_FORBIDDEN_OUTPUTS,
        tags=["strength", "weak_day_master", "身弱"],
    ),
    SyntheticCase(
        case_id="synthetic.strong_wealth_weak_body",
        chart={
            "chart_id": "synthetic.strong_wealth_weak_body",
            "four_pillars": {"year": "壬子", "month": "癸亥", "day": "戊子", "hour": "壬子"},
        },
        expected_inference_signals={
            "day_master_state.tendency": {"in": ["weak", "leaning_weak", "following_tendency_possible"]},
            "ten_god_structure.wealth.strength": {"in": ["medium", "strong"]},
        },
        expected_domain_adapter_outputs=DEFAULT_DOMAIN_EXPECTATIONS,
        forbidden_outputs=DEFAULT_FORBIDDEN_OUTPUTS,
        tags=["wealth_signal", "weak_day_master", "财旺但日主弱"],
    ),
    SyntheticCase(
        case_id="synthetic.peer_over_wealth",
        chart={
            "chart_id": "synthetic.peer_over_wealth",
            "four_pillars": {"year": "甲子", "month": "丙辰", "day": "戊午", "hour": "壬戌"},
            "luck_pillar": "癸亥",
            "flow_pillar": "甲辰",
        },
        expected_inference_signals={
            "internal_conflicts.type": {"contains": "peer_vs_wealth"},
            "internal_conflicts.direction": {"contains_any": ["peer_overwhelms_wealth", "balanced_peer_wealth_tension"]},
        },
        expected_domain_adapter_outputs={
            **DEFAULT_DOMAIN_EXPECTATIONS,
            "wealth_signals.competition_pressure.value": {"in": ["medium", "high"]},
        },
        forbidden_outputs=DEFAULT_FORBIDDEN_OUTPUTS,
        tags=["conflict", "peer_vs_wealth", "比劫压财"],
    ),
    SyntheticCase(
        case_id="synthetic.output_generates_wealth",
        chart={
            "chart_id": "synthetic.output_generates_wealth",
            "four_pillars": {"year": "庚申", "month": "壬子", "day": "戊申", "hour": "辛酉"},
        },
        expected_inference_signals={
            "energy_flow": {"contains_item": {"from": "output", "to": "wealth", "type": "generate"}},
            "ten_god_structure.output.presence": {"in": ["present", "dominant"]},
            "ten_god_structure.wealth.presence": {"in": ["present", "dominant"]},
        },
        expected_domain_adapter_outputs={
            **DEFAULT_DOMAIN_EXPECTATIONS,
            "wealth_signals.output_to_wealth_flow.value": {"in": ["weak", "medium", "strong"]},
        },
        forbidden_outputs=DEFAULT_FORBIDDEN_OUTPUTS,
        tags=["energy_flow", "output_to_wealth", "食伤生财路径存在"],
    ),
    SyntheticCase(
        case_id="synthetic.seal_vs_output",
        chart={
            "chart_id": "synthetic.seal_vs_output",
            "four_pillars": {"year": "丙午", "month": "庚申", "day": "戊午", "hour": "辛酉"},
        },
        expected_inference_signals={
            "internal_conflicts.type": {"contains": "seal_vs_output"},
            "internal_conflicts.direction": {"contains_any": ["seal_blocks_output", "balanced_seal_output_tension", "output_drains_seal"]},
        },
        expected_domain_adapter_outputs=DEFAULT_DOMAIN_EXPECTATIONS,
        forbidden_outputs=DEFAULT_FORBIDDEN_OUTPUTS,
        tags=["conflict", "seal_vs_output", "印克食伤"],
    ),
    SyntheticCase(
        case_id="synthetic.officer_pressure",
        chart={
            "chart_id": "synthetic.officer_pressure",
            "four_pillars": {"year": "甲寅", "month": "乙卯", "day": "戊子", "hour": "甲寅"},
        },
        expected_inference_signals={
            "day_master_state.tendency": {"in": ["weak", "leaning_weak", "following_tendency_possible"]},
            "ten_god_structure.officer.strength": {"in": ["medium", "strong"]},
        },
        expected_domain_adapter_outputs=DEFAULT_DOMAIN_EXPECTATIONS,
        forbidden_outputs=DEFAULT_FORBIDDEN_OUTPUTS,
        tags=["pressure", "officer", "官杀压力"],
    ),
    SyntheticCase(
        case_id="synthetic.clash_and_combination",
        chart={
            "chart_id": "synthetic.clash_and_combination",
            "four_pillars": {"year": "甲子", "month": "己丑", "day": "戊午", "hour": "庚申"},
        },
        expected_inference_signals={
            "structural_stability.signals": {"contains": "mixed_clash_and_combination"},
            "internal_conflicts.type": {"contains": "clash_vs_combination"},
            "internal_conflicts.direction": {"contains_any": ["clash_disrupts_combination", "combination_locks_clash_activation"]},
        },
        expected_domain_adapter_outputs={
            **DEFAULT_DOMAIN_EXPECTATIONS,
            "wealth_signals.stability.value": "low",
        },
        forbidden_outputs=DEFAULT_FORBIDDEN_OUTPUTS,
        tags=["structure", "clash_combination", "合冲并见"],
    ),
    SyntheticCase(
        case_id="synthetic.structural_stable",
        chart={
            "chart_id": "synthetic.structural_stable",
            "four_pillars": {"year": "甲寅", "month": "丁亥", "day": "戊午", "hour": "丙卯"},
        },
        expected_inference_signals={
            "structural_stability.signals": {"contains": "combination"},
            "structural_stability.signals": {"not_contains": "clash"},
            "structural_stability.state": {"in": ["stable", "mixed", "activated"]},
        },
        expected_domain_adapter_outputs=DEFAULT_DOMAIN_EXPECTATIONS,
        forbidden_outputs=DEFAULT_FORBIDDEN_OUTPUTS,
        tags=["structure", "stable_structure", "结构稳定"],
    ),
    SyntheticCase(
        case_id="synthetic.structural_conflict",
        chart={
            "chart_id": "synthetic.structural_conflict",
            "four_pillars": {"year": "甲子", "month": "丙午", "day": "戊寅", "hour": "乙卯"},
        },
        expected_inference_signals={
            "structural_stability.signals": {"contains": "clash"},
            "structural_stability.state": {"in": ["unstable", "conflicted"]},
        },
        expected_domain_adapter_outputs={
            **DEFAULT_DOMAIN_EXPECTATIONS,
            "wealth_signals.stability.value": "low",
        },
        forbidden_outputs=DEFAULT_FORBIDDEN_OUTPUTS,
        tags=["structure", "conflict_structure", "结构冲突"],
    ),
]
