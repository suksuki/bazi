from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from v30.contracts import V30Model
from v30.contracts import BirthInput
from v30.core.chart_context import build_chart_context_from_birth_input
from v30.presentation import build_presentation_model, build_role_locale_client_projection_matrix
from v30.hidden_factor import build_hidden_factor_state, hidden_factor_feedback_from_payload
from v30.portrait import build_macro_portrait_projection_views, summarize_macro_portrait_projection_views
from v30.runtime import attach_hidden_factor_state, attach_question_outcome, create_runtime_from_context, create_smoke_runtime
from v30.storage.diagnosis import diagnosis_storage_record
from v30.validation.bazi_llm_output_acceptance_readiness import run_bazi_llm_output_acceptance_readiness
from v30.validation.production_replay_metadata import build_production_replay_metadata


SyntheticCaseType = Literal[
    "positive_prototype",
    "negative_counter",
    "metamorphic_pair",
    "boundary_gradient",
    "composite_conflict",
]


class SyntheticBaziCase(V30Model):
    case_id: str
    case_type: SyntheticCaseType
    domain: str
    chart_input: dict[str, Any]
    expected_domains: set[str] = Field(default_factory=set)
    expected_anchor_ids: set[str] = Field(default_factory=set)
    negative_expectations: set[str] = Field(default_factory=set)
    expected_signal_types: set[str] = Field(default_factory=set)
    expected_mechanisms: set[str] = Field(default_factory=set)
    expected_top_topic: str = ""
    expected_min_policy_weight_by_topic: dict[str, float] = Field(default_factory=dict)
    expected_min_path_scores: dict[str, float] = Field(default_factory=dict)
    expected_min_question_graph_edges: int = 0
    expected_min_krp_unit_count: int = 0
    expected_krp_unit_ids: set[str] = Field(default_factory=set)
    expected_krp_pack_ids: set[str] = Field(default_factory=set)
    expected_krp_portrait_tags: set[str] = Field(default_factory=set)
    expected_macro_domains: set[str] = Field(default_factory=set)
    expected_macro_signal_domains: set[str] = Field(default_factory=set)
    expected_portrait_domains: set[str] = Field(default_factory=set)
    expected_hidden_factor_state_status: str = ""
    expected_chart_build_status: str = ""
    expected_day_master: str = ""
    expected_chart_build_source: str = ""
    expected_chart_build_pillars: dict[str, str] = Field(default_factory=dict)
    expected_boundary_flags: set[str] = Field(default_factory=set)
    expected_six_pillar_status: str = ""
    expected_practical_reading_status: str = ""
    expected_agent_question_stage: str = ""
    expected_interaction_stage: str = ""
    expected_selected_domain: str = ""
    expected_visible_next_question_id: str = ""
    expected_internal_next_question_id: str = ""
    expected_followup_reason_prefix: str = ""
    expected_answered_question_ids: set[str] = Field(default_factory=set)
    expected_selected_option_ids: set[str] = Field(default_factory=set)
    expected_constraint_valid: bool | None = None
    expected_invalid_retry_question_id: str = ""
    expected_interaction_brain_hidden_factor_allowed: bool | None = None
    expected_min_absorbed_signal_count: int = 0
    expected_min_rejected_signal_count: int = 0
    expect_visible_internal_split: bool = False
    expected_min_rule_confidence_by_kind: dict[str, float] = Field(default_factory=dict)
    expected_rule_weakens: dict[str, set[str]] = Field(default_factory=dict)
    expected_rule_states: dict[str, str] = Field(default_factory=dict)
    expected_ranked_primary_candidates: dict[str, str] = Field(default_factory=dict)
    expected_ranked_score_keys: dict[str, set[str]] = Field(default_factory=dict)
    expected_ranked_min_scores: dict[str, dict[str, float]] = Field(default_factory=dict)
    expected_ranked_basis_values: dict[str, dict[str, Any]] = Field(default_factory=dict)
    expected_model_signal_families: set[str] = Field(default_factory=set)
    expected_model_signal_energy_bands: dict[str, str] = Field(default_factory=dict)
    expected_min_model_signal_counts: dict[str, int] = Field(default_factory=dict)
    expected_base_fact_summary_keys: set[str] = Field(default_factory=set)
    expected_rbd_domains: set[str] = Field(default_factory=set)
    expected_min_rbd_rule_matches: int = 0
    expected_min_rbd_paths: int = 0
    expected_min_rbd_portraits: int = 0
    expected_min_rbd_claims: int = 0
    expected_max_rbd_generic_language_rate: float = 1.0
    expected_min_expression_bazi_terms: int = 2
    question_policy_override: dict[str, Any] = Field(default_factory=dict)
    question_outcome_answer: dict[str, Any] = Field(default_factory=dict)
    rule_policy_override: dict[str, Any] = Field(default_factory=dict)
    notes: str = ""


class SyntheticValidationResult(V30Model):
    case_id: str
    passed: bool
    failures: list[str] = Field(default_factory=list)
    observed: dict[str, Any] = Field(default_factory=dict)


class SyntheticValidationSuiteResult(V30Model):
    suite_id: str
    passed: bool
    case_count: int
    passed_count: int
    failed_count: int
    results: list[SyntheticValidationResult]


SYNTHETIC_SMOKE_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.core_spine.positive_001",
        case_type="positive_prototype",
        domain="core_spine",
        chart_input={"day_master": "甲"},
        expected_domains={"chart", "element", "ten_god", "time_context", "useful_god"},
        expected_anchor_ids={
            "q_v30_mainline_review",
            "q_v30_time_context_boundary",
            "q_v30_useful_god_candidate_review",
        },
        negative_expectations={"no_fixed_useful_god_verdict", "no_timing_prediction_without_time"},
        notes="Baseline current-spine case with missing time boundary.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.useful_god.negative_001",
        case_type="negative_counter",
        domain="useful_god",
        chart_input={"day_master": "甲"},
        expected_domains={"useful_god", "element"},
        expected_anchor_ids={"q_v30_useful_god_candidate_review"},
        negative_expectations={"no_fixed_useful_god_verdict"},
        notes="Useful-god must remain candidate review only.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.time_boundary.negative_001",
        case_type="negative_counter",
        domain="time_context",
        chart_input={"day_master": "甲"},
        expected_domains={"time_context"},
        expected_anchor_ids={"q_v30_time_context_boundary"},
        negative_expectations={"no_timing_prediction_without_time"},
        notes="Missing time must block timing prediction.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.hidden_factor.positive_001",
        case_type="positive_prototype",
        domain="hidden_factor",
        chart_input={"day_master": "甲"},
        expected_domains={"ten_god"},
        expected_anchor_ids={"q_v30_hidden_factor_boundary_discovery"},
        negative_expectations={"hidden_factor_requires_dialogue"},
        notes="Hidden factors must be dialogue probes, not deterministic conclusions.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.krp.positive_001",
        case_type="positive_prototype",
        domain="knowledge_rule_portrait",
        chart_input={"day_master": "甲"},
        expected_domains={"ten_god", "useful_god"},
        expected_signal_types={"knowledge", "rule", "portrait"},
        expected_mechanisms={
            "mechanism.ten_god_visibility_context",
            "mechanism.useful_god_candidate_gate",
            "mechanism.hidden_factor_dialogue_probe",
        },
        notes="V30-owned seed registry must emit bound knowledge/rule/portrait signals.",
    ),
)


_READY_BIRTH_INPUT = {
    "input_id": "synthetic-mainline-ready",
    "calendar_type": "solar",
    "birth_date": "1990-02-04",
    "birth_time": "23:30",
    "timezone": "Asia/Shanghai",
    "gender": "male",
}


SYNTHETIC_CORE_CALCULATION_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.core_calculation.birth_solar_ready_001",
        case_type="positive_prototype",
        domain="core_calculation",
        chart_input={
            "birth_input": {
                "input_id": "synthetic-solar-ready",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "23:30",
                "timezone": "Asia/Shanghai",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_day_master="庚",
        expected_min_expression_bazi_terms=0,
        expected_domains={"chart", "element", "ten_god", "time_context", "useful_god"},
        negative_expectations={"no_fixed_useful_god_verdict"},
        notes="Solar BirthInput must produce deterministic four pillars and feed the normal runtime chain.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.core_calculation.birth_unknown_hour_001",
        case_type="negative_counter",
        domain="core_calculation",
        chart_input={
            "birth_input": {
                "input_id": "synthetic-unknown-hour",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "timezone": "Asia/Shanghai",
                "unknown_hour": True,
            }
        },
        expected_chart_build_status="pending",
        expected_chart_build_source="birth_input",
        expected_min_expression_bazi_terms=0,
        negative_expectations={"no_birth_input_fake_pillars"},
        notes="Unknown hour must block hour-pillar fabrication.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.core_calculation.birth_lunar_ready_001",
        case_type="positive_prototype",
        domain="core_calculation",
        chart_input={
            "birth_input": {
                "input_id": "synthetic-lunar",
                "calendar_type": "lunar",
                "birth_date": "1990-01-09",
                "birth_time": "09:00",
                "timezone": "Asia/Shanghai",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_day_master="庚",
        expected_min_expression_bazi_terms=0,
        expected_domains={"chart", "element", "ten_god", "time_context", "useful_god"},
        negative_expectations={"no_fixed_useful_god_verdict"},
        notes="Lunar BirthInput must produce deterministic four pillars through lunar_python without importing V20 runtime.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.core_calculation.birth_true_solar_ready_001",
        case_type="positive_prototype",
        domain="core_calculation",
        chart_input={
            "birth_input": {
                "input_id": "synthetic-true-solar",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "23:30",
                "timezone": "Asia/Seoul",
                "birth_place": "Seoul",
                "use_true_solar_time": True,
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_day_master="庚",
        expected_min_expression_bazi_terms=0,
        expected_domains={"chart", "element", "ten_god", "time_context", "useful_god"},
        negative_expectations={"no_fixed_useful_god_verdict"},
        notes="True-solar-time conversion uses deterministic longitude policy for known birth places.",
    ),
)


SYNTHETIC_M1_M2_BAZI_CALCULATION_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.m1_m2.solar_base_fact_ready_001",
        case_type="positive_prototype",
        domain="m1_m2_bazi_calculation",
        chart_input={
            "birth_input": {
                "input_id": "m1-m2-solar-base-fact-ready",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "23:30",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_day_master="庚",
        expected_six_pillar_status="ready",
        expected_base_fact_summary_keys={
            "visible_ten_god_counts",
            "hidden_ten_god_counts",
            "hidden_stem_summary",
            "relation_type_counts",
            "relation_families",
            "root_fact_summary",
            "element_distribution",
        },
        expected_min_expression_bazi_terms=0,
        negative_expectations={"no_fixed_useful_god_verdict"},
        notes="M1/M2 seal case: ready solar input must expose deterministic base facts and customer-facing fact explanations.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.m1_m2.lunar_leap_fact_boundary_001",
        case_type="boundary_gradient",
        domain="m1_m2_bazi_calculation",
        chart_input={
            "birth_input": {
                "input_id": "m1-m2-lunar-leap-boundary",
                "calendar_type": "lunar",
                "birth_date": "1990-05-01",
                "birth_time": "09:00",
                "timezone": "Asia/Shanghai",
                "gender": "female",
                "lunar_is_leap_month": True,
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_base_fact_summary_keys={"hidden_stem_summary", "relation_type_counts", "root_fact_summary", "element_distribution"},
        expected_min_expression_bazi_terms=0,
        notes="M1 boundary: leap-month lunar conversion must record deterministic conversion facts and still feed M2 base facts.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.m1_m2.true_solar_fact_boundary_001",
        case_type="boundary_gradient",
        domain="m1_m2_bazi_calculation",
        chart_input=SYNTHETIC_CORE_CALCULATION_CASES[3].chart_input,
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_day_master="庚",
        expected_base_fact_summary_keys={"visible_ten_god_counts", "hidden_ten_god_counts", "relation_families"},
        expected_min_expression_bazi_terms=0,
        notes="M1 boundary: true-solar conversion must remain deterministic and feed M2 summaries.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.m1_m2.unknown_hour_no_fake_fact_001",
        case_type="negative_counter",
        domain="m1_m2_bazi_calculation",
        chart_input=SYNTHETIC_CORE_CALCULATION_CASES[1].chart_input,
        expected_chart_build_status="pending",
        expected_chart_build_source="birth_input",
        expected_min_expression_bazi_terms=0,
        negative_expectations={"no_birth_input_fake_pillars"},
        notes="M1 guardrail: unknown hour blocks fabricated pillars and therefore M2 fact expansion.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.m1_m2.invalid_timezone_no_fake_fact_001",
        case_type="negative_counter",
        domain="m1_m2_bazi_calculation",
        chart_input={
            "birth_input": {
                "input_id": "m1-m2-invalid-timezone",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "23:30",
                "timezone": "Invalid/Timezone",
                "gender": "male",
            }
        },
        expected_chart_build_status="blocked",
        expected_chart_build_source="birth_input",
        expected_min_expression_bazi_terms=0,
        negative_expectations={"no_birth_input_fake_pillars"},
        notes="M1 guardrail: invalid timezone blocks chart facts instead of falling back to guessed pillars.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.m1_m2.solar_term_before_boundary_001",
        case_type="boundary_gradient",
        domain="m1_m2_bazi_calculation",
        chart_input={
            "birth_input": {
                "input_id": "m1-m2-solar-term-before",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "09:00",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_chart_build_pillars={"year": "己巳", "month": "丁丑"},
        expected_boundary_flags={"solar_term_year_month_boundary_recorded"},
        expected_base_fact_summary_keys={"root_fact_summary", "element_distribution"},
        expected_min_expression_bazi_terms=0,
        notes="M1 boundary: before the deterministic solar-term switch, year/month pillars remain previous-cycle facts.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.m1_m2.solar_term_after_boundary_001",
        case_type="boundary_gradient",
        domain="m1_m2_bazi_calculation",
        chart_input={
            "birth_input": {
                "input_id": "m1-m2-solar-term-after",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "11:00",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_chart_build_pillars={"year": "庚午", "month": "戊寅"},
        expected_boundary_flags={"solar_term_year_month_boundary_recorded"},
        expected_base_fact_summary_keys={"root_fact_summary", "element_distribution"},
        expected_min_expression_bazi_terms=0,
        notes="M1 boundary: after the deterministic solar-term switch, year/month pillars move to the next-cycle facts.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.m1_m2.real_solar_female_fact_001",
        case_type="positive_prototype",
        domain="m1_m2_bazi_calculation",
        chart_input={
            "birth_input": {
                "input_id": "m1-m2-real-solar-female",
                "calendar_type": "solar",
                "birth_date": "1988-08-18",
                "birth_time": "09:20",
                "timezone": "Asia/Shanghai",
                "gender": "female",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_chart_build_pillars={"year": "戊辰", "month": "庚申", "day": "乙巳", "hour": "辛巳"},
        expected_day_master="乙",
        expected_six_pillar_status="ready",
        expected_base_fact_summary_keys={"root_fact_summary", "hidden_stem_summary", "element_distribution"},
        expected_min_expression_bazi_terms=0,
        notes="M1/M2 real-case fact fixture: solar female input validates deterministic pillars and base facts.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.m1_m2.real_lunar_fact_001",
        case_type="positive_prototype",
        domain="m1_m2_bazi_calculation",
        chart_input={
            "birth_input": {
                "input_id": "m1-m2-real-lunar",
                "calendar_type": "lunar",
                "birth_date": "1990-01-09",
                "birth_time": "09:00",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_chart_build_pillars={"year": "己巳", "month": "丁丑", "day": "庚子", "hour": "辛巳"},
        expected_boundary_flags={"lunar_calendar_conversion_recorded"},
        expected_day_master="庚",
        expected_six_pillar_status="ready",
        expected_base_fact_summary_keys={"root_fact_summary", "hidden_stem_summary", "element_distribution"},
        expected_min_expression_bazi_terms=0,
        notes="M1/M2 real-case fact fixture: standard lunar input validates conversion and base fact projection.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.m1_m2.real_lunar_leap_fact_001",
        case_type="boundary_gradient",
        domain="m1_m2_bazi_calculation",
        chart_input={
            "birth_input": {
                "input_id": "m1-m2-real-lunar-leap",
                "calendar_type": "lunar",
                "birth_date": "1990-05-01",
                "birth_time": "09:00",
                "timezone": "Asia/Shanghai",
                "gender": "female",
                "lunar_is_leap_month": True,
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_chart_build_pillars={"year": "庚午", "month": "壬午", "day": "己未", "hour": "己巳"},
        expected_boundary_flags={"lunar_calendar_conversion_recorded", "lunar_leap_month_recorded"},
        expected_day_master="己",
        expected_six_pillar_status="ready",
        expected_base_fact_summary_keys={"root_fact_summary", "hidden_stem_summary", "element_distribution"},
        expected_min_expression_bazi_terms=0,
        notes="M1/M2 real-case fact fixture: leap-month lunar input validates boundary flags and base facts.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.m1_m2.real_true_solar_fact_001",
        case_type="boundary_gradient",
        domain="m1_m2_bazi_calculation",
        chart_input={
            "birth_input": {
                "input_id": "m1-m2-real-true-solar",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "23:30",
                "timezone": "Asia/Seoul",
                "birth_place": "Seoul",
                "use_true_solar_time": True,
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_chart_build_pillars={"year": "庚午", "month": "戊寅", "day": "庚子", "hour": "丁亥"},
        expected_boundary_flags={"true_solar_time_adjustment_recorded", "late_zi_hour_boundary_recorded"},
        expected_day_master="庚",
        expected_six_pillar_status="ready",
        expected_base_fact_summary_keys={"root_fact_summary", "hidden_stem_summary", "element_distribution"},
        expected_min_expression_bazi_terms=0,
        notes="M1/M2 real-case fact fixture: known-place true-solar input validates adjusted deterministic pillars.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.m1_m2.real_unknown_gender_fact_001",
        case_type="boundary_gradient",
        domain="m1_m2_bazi_calculation",
        chart_input={
            "birth_input": {
                "input_id": "m1-m2-real-unknown-gender",
                "calendar_type": "solar",
                "birth_date": "1995-11-12",
                "birth_time": "14:05",
                "timezone": "Asia/Shanghai",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_chart_build_pillars={"year": "乙亥", "month": "丁亥", "day": "丁未", "hour": "丁未"},
        expected_day_master="丁",
        expected_base_fact_summary_keys={"root_fact_summary", "hidden_stem_summary", "element_distribution"},
        expected_min_expression_bazi_terms=0,
        notes="M1/M2 real-case fact fixture: unknown gender keeps deterministic natal facts ready while luck direction remains partial.",
    ),
)


SYNTHETIC_PRACTICAL_MAINLINE_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.luck_cycle.ready_001",
        case_type="positive_prototype",
        domain="luck_cycle",
        chart_input={"birth_input": _READY_BIRTH_INPUT},
        expected_chart_build_status="ready",
        expected_six_pillar_status="ready",
        expected_anchor_ids={"q_v30_practical_domain_focus"},
        expected_min_expression_bazi_terms=0,
        notes="BirthInput with gender should produce current luck-cycle context.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.flow_timing.ready_001",
        case_type="positive_prototype",
        domain="flow_timing",
        chart_input={"birth_input": _READY_BIRTH_INPUT},
        expected_chart_build_status="ready",
        expected_six_pillar_status="ready",
        expected_min_expression_bazi_terms=0,
        notes="BirthInput should produce flow-year and flow-month context.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.six_pillar.ready_001",
        case_type="positive_prototype",
        domain="six_pillar_context",
        chart_input={"birth_input": _READY_BIRTH_INPUT},
        expected_chart_build_status="ready",
        expected_six_pillar_status="ready",
        expected_min_expression_bazi_terms=0,
        notes="Six-pillar context should combine natal four pillars, current luck, and flow year.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.ranked_decision.ready_001",
        case_type="positive_prototype",
        domain="strength_structure_useful_god",
        chart_input={"birth_input": _READY_BIRTH_INPUT},
        expected_chart_build_status="ready",
        expected_six_pillar_status="ready",
        expected_min_expression_bazi_terms=0,
        notes="Ranked decisions should exist for strength, structure pattern, and useful-god candidates.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.practical_reading.ready_001",
        case_type="positive_prototype",
        domain="practical_reading",
        chart_input={"birth_input": _READY_BIRTH_INPUT},
        expected_chart_build_status="ready",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        notes="Practical reading context should expose career, wealth, relationship, health, and timing summaries.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.agent_question_flow.ready_001",
        case_type="positive_prototype",
        domain="agent_question_flow",
        chart_input={"birth_input": _READY_BIRTH_INPUT},
        expected_chart_build_status="ready",
        expected_six_pillar_status="ready",
        expected_agent_question_stage="event_year_discovery",
        expected_anchor_ids={"q_v30_practical_domain_focus"},
        expected_min_expression_bazi_terms=0,
        notes="Agent question flow should expose the next practical reading question stage.",
    ),
)


SYNTHETIC_REAL_CASE_VALIDATION_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case.solar_male_ready_001",
        case_type="positive_prototype",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-case-solar-male-ready",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "23:30",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_agent_question_stage="event_year_discovery",
        expected_anchor_ids={"q_v30_practical_domain_focus"},
        expected_min_expression_bazi_terms=0,
        notes="Canonical user BirthInput should produce ready chart, six-pillar context, practical reading, and next question flow.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case.solar_female_ready_001",
        case_type="positive_prototype",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-case-solar-female-ready",
                "calendar_type": "solar",
                "birth_date": "1988-08-18",
                "birth_time": "09:20",
                "timezone": "Asia/Shanghai",
                "gender": "female",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_agent_question_stage="event_year_discovery",
        expected_anchor_ids={"q_v30_practical_domain_focus"},
        expected_min_expression_bazi_terms=0,
        notes="Canonical female BirthInput should exercise luck-direction handling without role or fact drift.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case.solar_unknown_gender_partial_001",
        case_type="boundary_gradient",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-case-unknown-gender-partial",
                "calendar_type": "solar",
                "birth_date": "1995-11-12",
                "birth_time": "14:05",
                "timezone": "Asia/Shanghai",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_practical_reading_status="natal_only",
        expected_min_expression_bazi_terms=0,
        notes="Unknown gender should keep luck-cycle direction pending while still producing usable chart and reading context.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case.invalid_timezone_blocked_001",
        case_type="negative_counter",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-case-invalid-timezone",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "23:30",
                "timezone": "Invalid/Timezone",
                "gender": "male",
            }
        },
        expected_chart_build_status="blocked",
        expected_chart_build_source="birth_input",
        expected_min_expression_bazi_terms=0,
        negative_expectations={"no_birth_input_fake_pillars"},
        notes="Invalid timezone must block real-case chart construction without fabricating pillars.",
    ),
)


SYNTHETIC_REAL_CASE_CALIBRATION_PACK_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.solar_ready_001",
        case_type="positive_prototype",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-solar-ready",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "23:30",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_agent_question_stage="event_year_discovery",
        expected_min_expression_bazi_terms=0,
        notes="Canonical solar fixture validates full runtime readiness without asserting final Bazi conclusions.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.lunar_ready_001",
        case_type="positive_prototype",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-lunar-ready",
                "calendar_type": "lunar",
                "birth_date": "1990-01-09",
                "birth_time": "09:00",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_agent_question_stage="event_year_discovery",
        expected_min_expression_bazi_terms=0,
        notes="Canonical lunar fixture validates lunar conversion through the normal runtime pipeline.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.lunar_leap_ready_001",
        case_type="positive_prototype",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-lunar-leap-ready",
                "calendar_type": "lunar",
                "birth_date": "1990-05-01",
                "birth_time": "09:00",
                "timezone": "Asia/Shanghai",
                "gender": "female",
                "lunar_is_leap_month": True,
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_agent_question_stage="event_year_discovery",
        expected_min_expression_bazi_terms=0,
        notes="Canonical leap-month lunar fixture validates leap-month boundary recording without conclusion snapshots.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.true_solar_ready_001",
        case_type="positive_prototype",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-true-solar-ready",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "23:30",
                "timezone": "Asia/Seoul",
                "birth_place": "Seoul",
                "use_true_solar_time": True,
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_agent_question_stage="event_year_discovery",
        expected_min_expression_bazi_terms=0,
        notes="Canonical true-solar fixture validates known-place adjustment and late-zi boundary recording.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.unknown_hour_pending_001",
        case_type="boundary_gradient",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-unknown-hour",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "timezone": "Asia/Shanghai",
                "gender": "male",
                "unknown_hour": True,
            }
        },
        expected_chart_build_status="pending",
        expected_chart_build_source="birth_input",
        expected_min_expression_bazi_terms=0,
        negative_expectations={"no_birth_input_fake_pillars"},
        notes="Unknown-hour fixture validates that the calibration pack never fabricates an hour pillar.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.unknown_gender_partial_001",
        case_type="boundary_gradient",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-unknown-gender",
                "calendar_type": "solar",
                "birth_date": "1995-11-12",
                "birth_time": "14:05",
                "timezone": "Asia/Shanghai",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_practical_reading_status="natal_only",
        expected_min_expression_bazi_terms=0,
        notes="Unknown-gender fixture validates partial luck-cycle context while keeping the customer loop usable.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m5_strength_weak_001",
        case_type="positive_prototype",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m5-weak",
                "calendar_type": "solar",
                "birth_date": "1988-08-18",
                "birth_time": "09:20",
                "timezone": "Asia/Shanghai",
                "gender": "female",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        expected_ranked_primary_candidates={
            "strength": "weak",
            "useful_god": "resource_or_self_support_review",
        },
        expected_ranked_score_keys={
            "strength": {"weak", "slightly_weak", "balanced", "slightly_strong", "strong"},
            "structure_pattern": {"follow_structure_boundary_review", "special_structure_boundary_review", "disputed_structure_review"},
            "useful_god": {"resource_or_self_support_review", "balance_review", "climate_regulation_review"},
        },
        expected_ranked_min_scores={
            "structure_pattern": {
                "follow_structure_boundary_review": 0.50,
                "special_structure_boundary_review": 0.50,
                "regulation_climate_boundary_review": 0.45,
                "disputed_structure_review": 0.50,
            },
            "useful_god": {"climate_regulation_review": 0.40},
        },
        expected_ranked_basis_values={
            "structure_pattern": {
                "follow_structure_boundary_signal": True,
                "disputed_structure_signal": True,
                "non_unique_candidate_signal": True,
            },
        },
        notes="M5 calibration fixture checks weak-strength scoring and support-oriented useful-god candidate family.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m5_strength_slightly_weak_001",
        case_type="positive_prototype",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m5-slightly-weak",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "23:30",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        expected_ranked_primary_candidates={
            "strength": "slightly_weak",
            "useful_god": "resource_or_self_support_review",
        },
        expected_ranked_score_keys={
            "strength": {"weak", "slightly_weak", "balanced", "slightly_strong", "strong"},
            "structure_pattern": {"ordinary_structure_review", "dynamic_structure_review", "special_structure_boundary_review", "follow_structure_boundary_review"},
        },
        notes="M5 calibration fixture checks slightly weak strength and structure score shape.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m5_strength_balanced_001",
        case_type="positive_prototype",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m5-balanced",
                "calendar_type": "solar",
                "birth_date": "1995-11-12",
                "birth_time": "14:05",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        expected_ranked_primary_candidates={
            "strength": "balanced",
            "useful_god": "balance_review",
        },
        expected_ranked_score_keys={
            "useful_god": {"balance_review", "resource_or_self_support_review", "output_or_wealth_release_review"},
        },
        notes="M5 calibration fixture checks balanced-strength scoring and non-support-only useful-god selection.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m5_strength_strong_001",
        case_type="positive_prototype",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m5-strong",
                "calendar_type": "solar",
                "birth_date": "1966-06-06",
                "birth_time": "06:06",
                "timezone": "Asia/Shanghai",
                "gender": "female",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        expected_ranked_primary_candidates={
            "strength": "strong",
            "useful_god": "output_or_wealth_release_review",
        },
        expected_ranked_score_keys={
            "strength": {"strong", "slightly_strong", "balanced", "slightly_weak", "weak"},
            "useful_god": {"output_or_wealth_release_review", "authority_regulation_review", "balance_review"},
        },
        notes="M5 calibration fixture checks strong-strength scoring and release/regulation useful-god candidates.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m5_follow_structure_boundary_001",
        case_type="boundary_gradient",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m5-follow-structure-boundary",
                "calendar_type": "solar",
                "birth_date": "1981-12-12",
                "birth_time": "12:12",
                "timezone": "Asia/Shanghai",
                "gender": "female",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        expected_ranked_primary_candidates={
            "strength": "weak",
            "useful_god": "resource_or_self_support_review",
        },
        expected_ranked_score_keys={
            "structure_pattern": {
                "ordinary_structure_review",
                "dynamic_structure_review",
                "follow_structure_boundary_review",
                "special_structure_boundary_review",
            },
        },
        expected_ranked_min_scores={
            "structure_pattern": {
                "follow_structure_boundary_review": 0.55,
                "special_structure_boundary_review": 0.55,
            },
        },
        expected_ranked_basis_values={
            "structure_pattern": {
                "follow_structure_boundary_signal": True,
                "special_structure_boundary_signal": True,
                "non_unique_candidate_signal": True,
            },
        },
        notes="M5 follow-structure boundary fixture keeps extreme imbalance as reviewable candidate evidence, not a fixed follow-structure verdict.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m5_disputed_structure_001",
        case_type="composite_conflict",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m5-disputed-structure",
                "calendar_type": "solar",
                "birth_date": "1978-05-05",
                "birth_time": "05:10",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        expected_ranked_primary_candidates={
            "strength": "balanced",
            "useful_god": "balance_review",
        },
        expected_ranked_score_keys={
            "structure_pattern": {
                "ordinary_structure_review",
                "dynamic_structure_review",
                "disputed_structure_review",
                "mediation_path_review",
            },
        },
        expected_ranked_min_scores={
            "structure_pattern": {"disputed_structure_review": 0.52},
            "useful_god": {"authority_regulation_review": 0.32},
        },
        expected_ranked_basis_values={
            "structure_pattern": {
                "disputed_structure_signal": True,
                "non_unique_candidate_signal": True,
            },
        },
        notes="M5 disputed-structure fixture preserves conflict and mediation candidates before any final structure conclusion.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m5_boundary_late_zi_001",
        case_type="boundary_gradient",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m5-late-zi",
                "calendar_type": "solar",
                "birth_date": "1984-02-04",
                "birth_time": "00:30",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        expected_ranked_primary_candidates={
            "strength": "weak",
        },
        expected_ranked_score_keys={
            "structure_pattern": {"ordinary_structure_review", "dynamic_structure_review", "regulation_climate_boundary_review"},
        },
        expected_ranked_min_scores={
            "structure_pattern": {
                "regulation_climate_boundary_review": 0.45,
                "special_structure_boundary_review": 0.35,
            },
            "useful_god": {"climate_regulation_review": 0.40},
        },
        notes="M5 boundary fixture combines late-zi boundary recording with ranked-decision score stability.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m5_disputed_useful_god_001",
        case_type="composite_conflict",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m5-disputed-useful-god",
                "calendar_type": "solar",
                "birth_date": "1999-09-09",
                "birth_time": "21:30",
                "timezone": "Asia/Shanghai",
                "gender": "female",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        expected_ranked_primary_candidates={
            "strength": "balanced",
            "useful_god": "balance_review",
        },
        expected_ranked_score_keys={
            "useful_god": {"balance_review", "output_or_wealth_release_review", "resource_or_self_support_review", "climate_regulation_review"},
        },
        expected_ranked_min_scores={
            "structure_pattern": {"regulation_climate_boundary_review": 0.45},
            "useful_god": {
                "output_or_wealth_release_review": 0.50,
                "climate_regulation_review": 0.40,
            },
        },
        notes="M5 disputed useful-god fixture keeps multiple candidate families visible instead of collapsing to one fixed conclusion.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m7_solar_spring_boundary_001",
        case_type="boundary_gradient",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m7-solar-spring-boundary",
                "calendar_type": "solar",
                "birth_date": "1990-02-03",
                "birth_time": "22:45",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        notes="M7 boundary fixture validates solar-term-adjacent readiness and practical reading boundaries without final fortune conclusions.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m7_solar_year_edge_001",
        case_type="boundary_gradient",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m7-solar-year-edge",
                "calendar_type": "solar",
                "birth_date": "1991-01-31",
                "birth_time": "23:10",
                "timezone": "Asia/Shanghai",
                "gender": "female",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        notes="M7 boundary fixture validates year-edge chart facts, timing context, ranked decisions, and M6 output contract.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m7_lunar_month_edge_001",
        case_type="boundary_gradient",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m7-lunar-month-edge",
                "calendar_type": "lunar",
                "birth_date": "1990-01-29",
                "birth_time": "07:30",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        notes="M7 lunar edge fixture validates lunar conversion and downstream reading boundaries.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m7_lunar_leap_evening_001",
        case_type="boundary_gradient",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m7-lunar-leap-evening",
                "calendar_type": "lunar",
                "birth_date": "1990-05-02",
                "birth_time": "18:40",
                "timezone": "Asia/Shanghai",
                "gender": "female",
                "lunar_is_leap_month": True,
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        notes="M7 leap-month variant keeps leap-month handling covered across a second hour and gender path.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m7_true_solar_seoul_morning_001",
        case_type="boundary_gradient",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m7-true-solar-seoul-morning",
                "calendar_type": "solar",
                "birth_date": "1992-03-21",
                "birth_time": "08:15",
                "timezone": "Asia/Seoul",
                "birth_place": "Seoul",
                "use_true_solar_time": True,
                "gender": "female",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        notes="M7 true-solar variant validates known-place adjustment beyond the original late-zi true-solar case.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m7_true_solar_shanghai_noon_001",
        case_type="boundary_gradient",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m7-true-solar-shanghai-noon",
                "calendar_type": "solar",
                "birth_date": "1986-07-16",
                "birth_time": "12:00",
                "timezone": "Asia/Shanghai",
                "birth_place": "Shanghai",
                "use_true_solar_time": True,
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        notes="M7 true-solar variant validates same-zone true-solar boundary and downstream module stability.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m7_unknown_hour_lunar_pending_001",
        case_type="boundary_gradient",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m7-unknown-hour-lunar",
                "calendar_type": "lunar",
                "birth_date": "1990-01-09",
                "timezone": "Asia/Shanghai",
                "gender": "female",
                "unknown_hour": True,
            }
        },
        expected_chart_build_status="pending",
        expected_chart_build_source="birth_input",
        expected_min_expression_bazi_terms=0,
        negative_expectations={"no_birth_input_fake_pillars"},
        notes="M7 pending fixture validates lunar unknown-hour path without fake pillars.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m7_unknown_hour_true_solar_pending_001",
        case_type="boundary_gradient",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m7-unknown-hour-true-solar",
                "calendar_type": "solar",
                "birth_date": "1992-03-21",
                "timezone": "Asia/Seoul",
                "birth_place": "Seoul",
                "use_true_solar_time": True,
                "gender": "male",
                "unknown_hour": True,
            }
        },
        expected_chart_build_status="pending",
        expected_chart_build_source="birth_input",
        expected_min_expression_bazi_terms=0,
        negative_expectations={"no_birth_input_fake_pillars"},
        notes="M7 pending fixture validates true-solar plus unknown-hour guardrail without fabricated timing facts.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m7_unknown_gender_lunar_partial_001",
        case_type="boundary_gradient",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m7-unknown-gender-lunar",
                "calendar_type": "lunar",
                "birth_date": "1990-01-09",
                "birth_time": "11:20",
                "timezone": "Asia/Shanghai",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_practical_reading_status="natal_only",
        expected_min_expression_bazi_terms=0,
        notes="M7 unknown-gender lunar fixture validates natal-only downstream output on converted lunar facts.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m7_unknown_gender_true_solar_partial_001",
        case_type="boundary_gradient",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m7-unknown-gender-true-solar",
                "calendar_type": "solar",
                "birth_date": "1986-07-16",
                "birth_time": "12:00",
                "timezone": "Asia/Shanghai",
                "birth_place": "Shanghai",
                "use_true_solar_time": True,
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_practical_reading_status="natal_only",
        expected_min_expression_bazi_terms=0,
        notes="M7 unknown-gender true-solar fixture validates partial timing context and M6 natal-only boundaries.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m7_career_domain_active_001",
        case_type="positive_prototype",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m7-career-domain-active",
                "calendar_type": "solar",
                "birth_date": "1978-05-05",
                "birth_time": "05:10",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        notes="M7 career-domain fixture checks M6 domain output remains evidence-bound on a disputed-structure case.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m7_wealth_domain_active_001",
        case_type="positive_prototype",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m7-wealth-domain-active",
                "calendar_type": "solar",
                "birth_date": "1988-08-18",
                "birth_time": "09:20",
                "timezone": "Asia/Shanghai",
                "gender": "female",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        notes="M7 wealth-domain fixture checks practical output boundaries on weak-strength and support-oriented useful-god candidates.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m7_relationship_domain_active_001",
        case_type="positive_prototype",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m7-relationship-domain-active",
                "calendar_type": "solar",
                "birth_date": "1999-09-09",
                "birth_time": "21:30",
                "timezone": "Asia/Shanghai",
                "gender": "female",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        notes="M7 relationship-domain fixture checks blocked relationship event claims and evidence-linked practical reading.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m7_health_domain_active_001",
        case_type="positive_prototype",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m7-health-domain-active",
                "calendar_type": "solar",
                "birth_date": "1981-12-12",
                "birth_time": "12:12",
                "timezone": "Asia/Shanghai",
                "gender": "female",
            }
        },
        expected_chart_build_status="ready",
        expected_chart_build_source="birth_input",
        expected_six_pillar_status="ready",
        expected_practical_reading_status="ready",
        expected_min_expression_bazi_terms=0,
        notes="M7 health-domain fixture checks stress/routine review boundaries, not medical diagnosis.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m7_invalid_date_blocked_001",
        case_type="negative_counter",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m7-invalid-date",
                "calendar_type": "solar",
                "birth_date": "1990-02-31",
                "birth_time": "09:00",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="blocked",
        expected_chart_build_source="birth_input",
        expected_min_expression_bazi_terms=0,
        negative_expectations={"no_birth_input_fake_pillars"},
        notes="M7 negative fixture validates invalid-date blocking and no fake chart facts.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_case_calibration.m7_invalid_time_blocked_001",
        case_type="negative_counter",
        domain="real_case_validation",
        chart_input={
            "birth_input": {
                "input_id": "real-calibration-m7-invalid-time",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "25:61",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="blocked",
        expected_chart_build_source="birth_input",
        expected_min_expression_bazi_terms=0,
        negative_expectations={"no_birth_input_fake_pillars"},
        notes="M7 negative fixture validates invalid-time blocking and no fake chart facts.",
    ),
)


SYNTHETIC_TEN_GOD_ENERGY_CALIBRATION_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.ten_god_energy_calibration.output_wealth_authority_001",
        case_type="positive_prototype",
        domain="ten_god_energy_calibration",
        chart_input={
            "birth_input": {
                "input_id": "ten-god-calibration-output-wealth-authority",
                "calendar_type": "solar",
                "birth_date": "1988-08-18",
                "birth_time": "09:20",
                "timezone": "Asia/Shanghai",
                "gender": "female",
            }
        },
        expected_chart_build_status="ready",
        expected_model_signal_families={"output", "wealth", "authority"},
        expected_model_signal_energy_bands={"伤官": "high", "正财": "high", "正官": "high"},
        expected_min_model_signal_counts={"energy_band": 3, "volatility_alert": 4, "stability_alert": 4},
        expected_min_expression_bazi_terms=0,
        notes="M4 calibration covers output/wealth/authority high energy with volatility review, without exposing raw scores.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.ten_god_energy_calibration.self_competition_001",
        case_type="positive_prototype",
        domain="ten_god_energy_calibration",
        chart_input={
            "birth_input": {
                "input_id": "ten-god-calibration-self-competition",
                "calendar_type": "solar",
                "birth_date": "1966-06-06",
                "birth_time": "06:06",
                "timezone": "Asia/Shanghai",
                "gender": "female",
            }
        },
        expected_chart_build_status="ready",
        expected_model_signal_families={"self", "authority"},
        expected_model_signal_energy_bands={"比肩": "high", "劫财": "high", "正官": "medium"},
        expected_min_model_signal_counts={"energy_band": 3, "volatility_alert": 3, "stability_alert": 5},
        expected_min_expression_bazi_terms=0,
        notes="M4 calibration covers self/peer competition with low-stability review.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.ten_god_energy_calibration.resource_authority_001",
        case_type="boundary_gradient",
        domain="ten_god_energy_calibration",
        chart_input={
            "birth_input": {
                "input_id": "ten-god-calibration-resource-authority",
                "calendar_type": "solar",
                "birth_date": "1981-12-12",
                "birth_time": "12:12",
                "timezone": "Asia/Shanghai",
                "gender": "female",
            }
        },
        expected_chart_build_status="ready",
        expected_model_signal_families={"resource", "authority", "self"},
        expected_model_signal_energy_bands={"正印": "high", "七杀": "high", "比肩": "medium"},
        expected_min_model_signal_counts={"energy_band": 3, "volatility_alert": 6, "stability_alert": 7},
        expected_min_expression_bazi_terms=0,
        notes="M4 calibration covers resource/authority pressure where volatility and low-stability both require review.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.ten_god_energy_calibration.balanced_self_authority_001",
        case_type="boundary_gradient",
        domain="ten_god_energy_calibration",
        chart_input={
            "birth_input": {
                "input_id": "ten-god-calibration-balanced-self-authority",
                "calendar_type": "solar",
                "birth_date": "1995-11-12",
                "birth_time": "14:05",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_model_signal_families={"self", "authority", "resource"},
        expected_model_signal_energy_bands={"比肩": "high", "正官": "medium", "正印": "medium"},
        expected_min_model_signal_counts={"energy_band": 3, "volatility_alert": 3, "stability_alert": 3},
        expected_min_expression_bazi_terms=0,
        notes="M4 calibration covers balanced self/authority/output bands and keeps low energy as a band, not a verdict.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.ten_god_energy_calibration.disputed_multi_family_001",
        case_type="composite_conflict",
        domain="ten_god_energy_calibration",
        chart_input={
            "birth_input": {
                "input_id": "ten-god-calibration-disputed-multi-family",
                "calendar_type": "solar",
                "birth_date": "1978-05-05",
                "birth_time": "05:10",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_model_signal_families={"self", "resource", "wealth"},
        expected_model_signal_energy_bands={"劫财": "high", "偏印": "high", "偏财": "high"},
        expected_min_model_signal_counts={"energy_band": 3, "dominant": 4, "volatility_alert": 5, "stability_alert": 4},
        expected_min_expression_bazi_terms=0,
        notes="M4 calibration covers multi-family high energy and disputed signal boundaries for M5 consumers.",
    ),
)


SYNTHETIC_M4_TEN_GOD_REAL_CASE_REPLAY_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.m4_ten_god_replay.solar_male_001",
        case_type="positive_prototype",
        domain="m4_ten_god_real_case_replay",
        chart_input={
            "birth_input": {
                "input_id": "m4-replay-solar-male",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "23:30",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_model_signal_families={"resource", "output", "authority"},
        expected_min_model_signal_counts={"energy_band": 3, "volatility_alert": 4, "stability_alert": 4},
        expected_min_expression_bazi_terms=0,
        notes="M4 real-case replay covers solar male model-signal interface and alert shape.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.m4_ten_god_replay.solar_female_001",
        case_type="positive_prototype",
        domain="m4_ten_god_real_case_replay",
        chart_input={
            "birth_input": {
                "input_id": "m4-replay-solar-female",
                "calendar_type": "solar",
                "birth_date": "1988-08-18",
                "birth_time": "09:20",
                "timezone": "Asia/Shanghai",
                "gender": "female",
            }
        },
        expected_chart_build_status="ready",
        expected_model_signal_families={"output", "wealth", "authority"},
        expected_model_signal_energy_bands={"伤官": "high", "正财": "high", "正官": "high"},
        expected_min_model_signal_counts={"energy_band": 3, "volatility_alert": 4, "stability_alert": 4},
        expected_min_expression_bazi_terms=0,
        notes="M4 real-case replay covers output/wealth/authority family shape.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.m4_ten_god_replay.lunar_001",
        case_type="positive_prototype",
        domain="m4_ten_god_real_case_replay",
        chart_input={
            "birth_input": {
                "input_id": "m4-replay-lunar",
                "calendar_type": "lunar",
                "birth_date": "1990-01-09",
                "birth_time": "09:00",
                "timezone": "Asia/Shanghai",
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_model_signal_families={"resource", "authority"},
        expected_min_model_signal_counts={"energy_band": 3, "dominant": 4},
        expected_min_expression_bazi_terms=0,
        notes="M4 real-case replay covers lunar conversion through model-signal interface.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.m4_ten_god_replay.lunar_leap_001",
        case_type="boundary_gradient",
        domain="m4_ten_god_real_case_replay",
        chart_input={
            "birth_input": {
                "input_id": "m4-replay-lunar-leap",
                "calendar_type": "lunar",
                "birth_date": "1990-05-01",
                "birth_time": "09:00",
                "timezone": "Asia/Shanghai",
                "gender": "female",
                "lunar_is_leap_month": True,
            }
        },
        expected_chart_build_status="ready",
        expected_model_signal_families={"self", "resource"},
        expected_min_model_signal_counts={"energy_band": 3, "dominant": 2, "volatility_alert": 2},
        expected_min_expression_bazi_terms=0,
        notes="M4 real-case replay covers leap-month lunar boundary in model signals.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.m4_ten_god_replay.true_solar_001",
        case_type="boundary_gradient",
        domain="m4_ten_god_real_case_replay",
        chart_input={
            "birth_input": {
                "input_id": "m4-replay-true-solar",
                "calendar_type": "solar",
                "birth_date": "1990-02-04",
                "birth_time": "23:30",
                "timezone": "Asia/Seoul",
                "birth_place": "Seoul",
                "use_true_solar_time": True,
                "gender": "male",
            }
        },
        expected_chart_build_status="ready",
        expected_model_signal_families={"resource", "authority"},
        expected_model_signal_energy_bands={"偏印": "high", "七杀": "high", "正官": "high"},
        expected_min_model_signal_counts={"energy_band": 3, "dominant": 4, "volatility_alert": 4},
        expected_min_expression_bazi_terms=0,
        notes="M4 real-case replay covers true-solar adjusted chart through model-signal interface.",
    ),
)


SYNTHETIC_INTERACTION_LOOP_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.interaction_loop.direct_question_click_001",
        case_type="positive_prototype",
        domain="interaction_loop",
        chart_input={"birth_input": _READY_BIRTH_INPUT},
        expected_chart_build_status="ready",
        expected_min_expression_bazi_terms=0,
        question_outcome_answer={
            "question_id": "q_v30_user_career_direction",
            "answer": "I want career direction first.",
            "outcome_status": "answered",
            "confidence": 0.8,
        },
        expected_interaction_stage="followup_question_selection",
        expected_selected_domain="career",
        expected_visible_next_question_id="q_v30_user_timing_pressure",
        expected_internal_next_question_id="q_v30_hidden_factor_boundary_discovery",
        expected_answered_question_ids={"q_v30_user_career_direction"},
        expect_visible_internal_split=True,
        notes="Direct user-question click must refresh the visible next question while internal calibration remains diagnosable only.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.interaction_loop.structured_domain_choice_001",
        case_type="positive_prototype",
        domain="interaction_loop",
        chart_input={"birth_input": _READY_BIRTH_INPUT},
        expected_chart_build_status="ready",
        expected_min_expression_bazi_terms=0,
        question_outcome_answer={
            "question_id": "q_v30_practical_domain_focus",
            "answer": "Career",
            "outcome_status": "answered",
            "selected_option": "domain:career",
            "confidence": 0.82,
        },
        expected_interaction_stage="followup_question_selection",
        expected_selected_domain="career",
        expected_visible_next_question_id="q_v30_user_career_direction",
        expected_internal_next_question_id="q_v30_user_career_direction",
        expected_followup_reason_prefix="selected_domain:career:",
        expected_answered_question_ids={"q_v30_practical_domain_focus"},
        expected_selected_option_ids={"domain:career"},
        notes="Structured domain option should steer follow-up strategy without mutating chart facts.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.interaction_loop.hidden_calibration_hidden_001",
        case_type="positive_prototype",
        domain="interaction_loop",
        chart_input={"day_master": "甲"},
        expected_min_expression_bazi_terms=0,
        question_outcome_answer={
            "question_id": "q_v30_hidden_factor_boundary_discovery",
            "answer": "2021 and 2024 repeated as career pressure years.",
            "outcome_status": "answered",
            "selected_option": "domain:career",
            "structured_payload": {
                "years": [2021, 2024],
                "state_tags": ["career_pressure"],
                "intensity": "medium",
                "recurrence": "repeated",
                "confidence": "approximate",
            },
            "confidence": 0.82,
            "feedback_tags": ["career", "hidden_factor_followup"],
        },
        expected_interaction_stage="followup_question_selection",
        expected_selected_domain="career",
        expected_visible_next_question_id="q_v30_user_career_direction",
        expected_internal_next_question_id="q_v30_user_career_direction",
        expected_followup_reason_prefix="selected_domain:career:",
        expected_answered_question_ids={"q_v30_hidden_factor_boundary_discovery"},
        expected_selected_option_ids={"domain:career"},
        negative_expectations={"hidden_factor_requires_dialogue"},
        notes="Hidden calibration may inform diagnostics and strategy but must project a user-facing next question.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.interaction_loop.initial_visible_internal_split_001",
        case_type="positive_prototype",
        domain="interaction_loop",
        chart_input={"birth_input": _READY_BIRTH_INPUT},
        expected_chart_build_status="ready",
        expected_min_expression_bazi_terms=0,
        expected_interaction_stage="initial_question_selection",
        expected_visible_next_question_id="q_v30_user_career_direction",
        expected_internal_next_question_id="q_v30_hidden_factor_boundary_discovery",
        expect_visible_internal_split=True,
        notes="Initial customer surface should show a product question while admin diagnostics retain the internal calibration candidate.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.interaction_loop.answer_api_state_001",
        case_type="positive_prototype",
        domain="interaction_loop",
        chart_input={"birth_input": _READY_BIRTH_INPUT},
        expected_chart_build_status="ready",
        expected_min_expression_bazi_terms=0,
        question_outcome_answer={
            "question_id": "q_v30_user_wealth_tendency",
            "answer": "I want to compare income growth and investment risk.",
            "outcome_status": "answered",
            "confidence": 0.78,
        },
        expected_interaction_stage="followup_question_selection",
        expected_selected_domain="wealth",
        expected_visible_next_question_id="q_v30_user_career_direction",
        expected_internal_next_question_id="q_v30_hidden_factor_boundary_discovery",
        expected_answered_question_ids={"q_v30_user_wealth_tendency"},
        expect_visible_internal_split=True,
        notes="Answer API-style outcome should return interaction state, visible next question, and answer context without fact mutation.",
    ),
)


SYNTHETIC_INTERACTION_BRAIN_STRUCTURED_CONSTRAINT_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.interaction_brain_structured_constraints.accepted_hidden_factor_001",
        case_type="positive_prototype",
        domain="interaction_brain_structured_constraints",
        chart_input={"day_master": "甲"},
        expected_min_expression_bazi_terms=0,
        question_outcome_answer={
            "question_id": "q_v30_hidden_factor_boundary_discovery",
            "answer": "2021 和 2024 都是事业压力和资质压力明显的年份。",
            "outcome_status": "answered",
            "selected_option": "domain:career",
            "structured_payload": {
                "years": [2021, 2024],
                "state_tags": ["career_pressure", "credential_pressure"],
                "intensity": "medium",
                "recurrence": "repeated",
                "confidence": "approximate",
            },
            "confidence": 0.84,
            "feedback_tags": ["structured_hidden_factor"],
        },
        expected_interaction_stage="followup_question_selection",
        expected_selected_domain="career",
        expected_visible_next_question_id="q_v30_user_career_direction",
        expected_answered_question_ids={"q_v30_hidden_factor_boundary_discovery"},
        expected_selected_option_ids={"domain:career"},
        expected_constraint_valid=True,
        expected_interaction_brain_hidden_factor_allowed=True,
        expected_min_absorbed_signal_count=3,
        negative_expectations={"hidden_factor_requires_dialogue"},
        notes="Accepted structured hidden-factor payload can tune question strategy and hidden-factor feedback, but cannot mutate chart facts.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.interaction_brain_structured_constraints.rejected_pollution_001",
        case_type="negative_counter",
        domain="interaction_brain_structured_constraints",
        chart_input={"day_master": "甲"},
        expected_min_expression_bazi_terms=0,
        question_outcome_answer={
            "question_id": "q_v30_hidden_factor_boundary_discovery",
            "answer": "自由发挥：我觉得所有年份都很糟，这段不能进权重。",
            "outcome_status": "answered",
            "selected_option": "",
            "structured_payload": {
                "years": [1888, "bad-year"],
                "state_tags": ["anything_i_want"],
            },
            "confidence": 0.55,
            "feedback_tags": ["free_text_pollution_attempt"],
        },
        expected_interaction_stage="followup_question_selection",
        expected_visible_next_question_id="q_v30_hidden_factor_boundary_discovery",
        expected_answered_question_ids={"q_v30_hidden_factor_boundary_discovery"},
        expected_constraint_valid=False,
        expected_invalid_retry_question_id="q_v30_hidden_factor_boundary_discovery",
        expected_interaction_brain_hidden_factor_allowed=False,
        expected_min_rejected_signal_count=3,
        negative_expectations={"hidden_factor_requires_dialogue"},
        notes="Unknown tags, invalid years, and free text must be rejected and routed to constrained retry.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.interaction_brain_structured_constraints.domain_followup_001",
        case_type="positive_prototype",
        domain="interaction_brain_structured_constraints",
        chart_input={"birth_input": _READY_BIRTH_INPUT},
        expected_chart_build_status="ready",
        expected_min_expression_bazi_terms=0,
        question_outcome_answer={
            "question_id": "q_v30_practical_domain_focus",
            "answer": "先看事业。",
            "outcome_status": "answered",
            "selected_option": "domain:career",
            "structured_payload": {"selected_domain": "career"},
            "confidence": 0.8,
            "feedback_tags": ["structured_domain_followup"],
        },
        expected_interaction_stage="followup_question_selection",
        expected_selected_domain="career",
        expected_visible_next_question_id="q_v30_user_career_direction",
        expected_internal_next_question_id="q_v30_user_career_direction",
        expected_answered_question_ids={"q_v30_practical_domain_focus"},
        expected_selected_option_ids={"domain:career"},
        expected_constraint_valid=True,
        expected_interaction_brain_hidden_factor_allowed=False,
        expected_min_absorbed_signal_count=1,
        notes="Domain follow-up can steer visible next question while remaining outside hidden-factor update.",
    ),
)


SYNTHETIC_CENTRAL_BRAIN_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.central_brain.guest_ready_chart_001",
        case_type="positive_prototype",
        domain="central_brain",
        chart_input={"birth_input": _READY_BIRTH_INPUT, "central_brain_role": "guest"},
        expected_chart_build_status="ready",
        expected_min_expression_bazi_terms=0,
        notes="Central brain must coordinate a ready guest chart without exposing diagnostics or mutating facts.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.central_brain.user_selected_option_001",
        case_type="positive_prototype",
        domain="central_brain",
        chart_input={"birth_input": _READY_BIRTH_INPUT, "central_brain_role": "user"},
        expected_chart_build_status="ready",
        expected_min_expression_bazi_terms=0,
        question_outcome_answer={
            "question_id": "q_v30_practical_domain_focus",
            "answer": "Career",
            "outcome_status": "answered",
            "selected_option": "domain:career",
            "confidence": 0.82,
        },
        expected_answered_question_ids={"q_v30_practical_domain_focus"},
        expected_selected_option_ids={"domain:career"},
        notes="Central brain must keep session memory and question strategy coherent after a structured user option.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.central_brain.practitioner_diagnostic_view_001",
        case_type="positive_prototype",
        domain="central_brain",
        chart_input={"birth_input": _READY_BIRTH_INPUT, "central_brain_role": "practitioner"},
        expected_chart_build_status="ready",
        expected_min_expression_bazi_terms=0,
        notes="Practitioner projection must expose central-brain diagnostics while keeping the coordinator read-only.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.central_brain.admin_hidden_factor_feedback_001",
        case_type="positive_prototype",
        domain="central_brain",
        chart_input={
            "day_master": "甲",
            "central_brain_role": "admin",
            "hidden_factor_user_calibrated": "true",
            "special_event_years": [2020, 2023],
            "repeated_states": ["career_pressure_repeat", "role_shift_repeat"],
        },
        expected_hidden_factor_state_status="amplifier_candidate",
        expected_min_expression_bazi_terms=0,
        negative_expectations={"hidden_factor_requires_dialogue"},
        notes="Admin diagnostics may see hidden-factor feedback state, but central brain still treats it as feedback-conditioned.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.central_brain.missing_time_boundary_001",
        case_type="negative_counter",
        domain="central_brain",
        chart_input={"day_master": "甲", "central_brain_role": "user"},
        expected_min_expression_bazi_terms=0,
        negative_expectations={"no_timing_prediction_without_time", "hidden_factor_requires_dialogue"},
        notes="Missing time remains an unknown-context route and cannot become a timing claim.",
    ),
)


SYNTHETIC_GRADIENT_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.time_context_weight_001",
        case_type="boundary_gradient",
        domain="question_policy",
        chart_input={"day_master": "甲"},
        expected_domains={"time_context"},
        expected_anchor_ids={"q_v30_time_context_boundary"},
        expected_top_topic="time_context",
        expected_min_policy_weight_by_topic={"time_context": 1.05},
        question_policy_override={
            "weights": {
                "topic_weights": {"time_context": 1.03},
                "intent_weights": {"confirm_missing_time_context": 1.02},
                "stage_weights": {"context_completion": 1.02},
            }
        },
        notes="Boundary gradient proves missing-time completion can be strengthened by policy weights.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.hidden_factor_weight_001",
        case_type="boundary_gradient",
        domain="hidden_factor",
        chart_input={"day_master": "甲"},
        expected_domains={"ten_god"},
        expected_anchor_ids={"q_v30_hidden_factor_boundary_discovery"},
        expected_top_topic="hidden_factor",
        expected_min_policy_weight_by_topic={"hidden_factor": 1.2},
        negative_expectations={"hidden_factor_requires_dialogue"},
        question_policy_override={
            "weights": {
                "topic_weights": {"hidden_factor": 1.25},
            }
        },
        notes="Feature-obvious hidden-factor sample should move dialogue discovery to the top without making a deterministic claim.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.structure_mechanism_threshold_001",
        case_type="boundary_gradient",
        domain="structure_dynamic",
        chart_input={"day_master": "甲"},
        expected_domains={"branch_relation", "ten_god", "useful_god"},
        expected_mechanisms={
            "mechanism.hidden_factor_dialogue_probe",
            "mechanism.ten_god_visibility_context",
            "mechanism.branch_relation_dynamic_review",
            "mechanism.useful_god_candidate_gate",
        },
        expected_min_path_scores={
            "mechanism_path_count": 4.0,
            "top_mechanism_score": 0.85,
            "structure_policy_weighted": 1.0,
        },
        notes="Structure dynamic gradient keeps mechanism path coverage above policy-tuned thresholds.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.structure_dynamic_graph_v2_001",
        case_type="boundary_gradient",
        domain="structure_dynamic_v2",
        chart_input={"day_master": "甲"},
        expected_domains={"rule", "ten_god", "branch_relation"},
        expected_min_path_scores={
            "dynamic_graph_node_count": 3.0,
            "dynamic_graph_edge_count": 3.0,
            "dynamic_path_count": 1.0,
            "top_dynamic_path_score": 0.2,
            "dynamic_competing_path_count": 1.0,
            "dynamic_suppressed_path_count": 1.0,
            "dynamic_conflict_family_count": 1.0,
            "dynamic_path_resolution_family_count": 1.0,
            "dynamic_branch_conflict_edge_count": 1.0,
            "dynamic_branch_alignment_edge_count": 1.0,
            "strength_pattern_review_count": 1.0,
            "dynamic_wealth_path_count": 1.0,
            "dynamic_wealth_competition_path_count": 1.0,
            "dynamic_wealth_output_generation_path_count": 1.0,
            "dynamic_wealth_authority_bridge_path_count": 1.0,
            "dynamic_career_path_count": 1.0,
            "dynamic_career_authority_pressure_path_count": 1.0,
            "dynamic_career_resource_resolution_path_count": 1.0,
            "dynamic_relationship_path_count": 1.0,
            "dynamic_relationship_conflict_path_count": 1.0,
            "dynamic_relationship_alignment_path_count": 1.0,
            "dynamic_relationship_marker_path_count": 1.0,
            "dynamic_health_review_path_count": 1.0,
            "dynamic_health_element_excess_review_count": 1.0,
            "dynamic_health_conflict_pressure_review_count": 1.0,
            "dynamic_useful_god_candidate_path_count": 1.0,
            "dynamic_useful_god_ranked_candidate_count": 1.0,
        },
        notes="Dynamic graph v2 must extract weighted nodes, competing/suppressed paths, and score explanations from current evidence.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.krp_consumption_001",
        case_type="composite_conflict",
        domain="knowledge_rule_portrait",
        chart_input={"day_master": "甲"},
        expected_signal_types={"knowledge", "rule", "portrait"},
        expected_min_path_scores={
            "knowledge_signal_count": 1.0,
            "rule_signal_count": 1.0,
            "portrait_signal_count": 1.0,
        },
        negative_expectations={"no_fixed_useful_god_verdict", "hidden_factor_requires_dialogue"},
        notes="Composite case keeps K/R/P signals consumed while useful-god and hidden-factor boundaries stay active.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.krp_library_expansion_001",
        case_type="boundary_gradient",
        domain="knowledge_rule_portrait",
        chart_input={"day_master": "甲"},
        expected_domains={"element", "time_context", "branch_relation", "ten_god", "useful_god"},
        expected_min_krp_unit_count=35,
        expected_krp_unit_ids={
            "v30.krp.chart.context_bound",
            "v30.krp.element.day_master_context",
            "v30.krp.time_context.missing_boundary",
            "v30.krp.element.balance_review",
            "v30.krp.branch_relation.dynamic_review",
            "v30.krp.branch_relation.conflict_family",
            "v30.krp.branch_relation.alignment_family",
            "v30.krp.hidden_factor.dialogue_boundary",
            "v30.krp.ten_god.hidden_stem_context",
            "v30.krp.ten_god.output_expression_review",
            "v30.krp.ten_god.self_competition_review",
            "v30.krp.strength.seasonal_review",
            "v30.krp.structure.pattern_candidate_review",
            "v30.krp.useful_god.family_candidate_review",
            "v30.krp.structure.path_resolution_review",
            "v30.krp.wealth.domain_path_review",
            "v30.krp.wealth.competition_path_review",
            "v30.krp.wealth.output_generation_path_review",
            "v30.krp.wealth.authority_bridge_path_review",
            "v30.krp.career.authority_path_review",
            "v30.krp.career.authority_pressure_path_review",
            "v30.krp.career.resource_resolution_path_review",
            "v30.krp.relationship.relation_path_review",
            "v30.krp.relationship.conflict_path_review",
            "v30.krp.relationship.alignment_path_review",
            "v30.krp.relationship.marker_path_review",
            "v30.krp.health.element_imbalance_review",
            "v30.krp.health.excess_review",
            "v30.krp.health.conflict_pressure_review",
            "v30.krp.useful_god.domain_path_candidate_review",
        },
        expected_krp_pack_ids={"v30.krp.pack.core_runtime"},
        expected_krp_portrait_tags={
            "chart_context_bound",
            "hidden_factor_dialogue_required",
            "branch_relation_dynamic_review",
            "branch_conflict_family",
            "output_expression_context",
            "seasonal_strength_review",
            "path_resolution_candidate",
            "wealth_rule_candidate",
            "career_rule_candidate",
            "relationship_rule_candidate",
            "health_rule_candidate",
        },
        expected_macro_domains={"foundation", "wealth", "career", "relationship", "romance", "health", "hidden_factor"},
        expected_macro_signal_domains={"foundation", "wealth", "career", "relationship", "romance", "health", "hidden_factor"},
        expected_portrait_domains={"wealth", "career", "relationship", "romance", "health", "hidden_factor"},
        negative_expectations={"no_timing_prediction_without_time", "hidden_factor_requires_dialogue"},
        notes="K/R/P library expansion must cover knowledge-pack metadata, boundaries, portrait tags, distribution, and dynamic review.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.question_dialogue_graph_001",
        case_type="boundary_gradient",
        domain="question_intelligence",
        chart_input={"day_master": "甲"},
        expected_domains={"time_context", "ten_god", "useful_god"},
        expected_anchor_ids={
            "q_v30_time_context_boundary",
            "q_v30_hidden_factor_boundary_discovery",
            "q_v30_useful_god_candidate_review",
        },
        expected_top_topic="time_context",
        expected_min_question_graph_edges=2,
        question_outcome_answer={
            "question_id": "q_v30_hidden_factor_boundary_discovery",
            "answer": "2021 and 2024 both had repeated career pressure.",
            "outcome_status": "answered",
            "confidence": 0.82,
            "feedback_tags": ["career", "hidden_factor_followup"],
        },
        negative_expectations={"hidden_factor_requires_dialogue", "no_timing_prediction_without_time"},
        notes="Question intelligence should expose a graph, not only a sorted list.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.mainline_stability_001",
        case_type="metamorphic_pair",
        domain="mainline",
        chart_input={"day_master": "丙"},
        expected_domains={"chart", "element", "ten_god", "time_context"},
        expected_anchor_ids={"q_v30_time_context_boundary"},
        expected_top_topic="time_context",
        negative_expectations={"no_timing_prediction_without_time"},
        notes="Changing day master should preserve missing-time boundary behavior.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.time_counterevidence_001",
        case_type="metamorphic_pair",
        domain="rule_counterevidence",
        chart_input={"day_master": "甲", "luck_pillar": "庚午"},
        expected_domains={"time_context", "rule"},
        expected_rule_states={"time_context": "countered"},
        expected_min_path_scores={"rule_countered_count": 1.0},
        notes="Explicit time layer should counter the missing-time blocking rule instead of deleting rule traceability.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.rule_policy_hidden_factor_001",
        case_type="boundary_gradient",
        domain="rule_policy",
        chart_input={"day_master": "甲"},
        expected_domains={"rule", "ten_god"},
        expected_anchor_ids={"q_v30_hidden_factor_boundary_discovery"},
        expected_min_rule_confidence_by_kind={"hidden_factor": 0.9},
        expected_rule_weakens={"hidden_factor": {"deterministic_hidden_factor_claim"}},
        negative_expectations={"hidden_factor_requires_dialogue"},
        rule_policy_override={
            "weights": {
                "rule_weights": {"v30.rule.hidden_factor.requires_dialogue": 1.25},
            }
        },
        notes="Rule policy can strengthen hidden-factor dialogue boundary without converting it into a deterministic claim.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.hidden_factor_feedback_counter_001",
        case_type="composite_conflict",
        domain="hidden_factor_feedback",
        chart_input={"day_master": "甲", "hidden_factor_user_calibrated": "true"},
        expected_domains={"feedback", "rule", "ten_god"},
        expected_rule_states={"hidden_factor": "countered"},
        expected_min_path_scores={"rule_countered_count": 1.0},
        expected_rule_weakens={"hidden_factor": {"deterministic_hidden_factor_claim"}},
        notes="User-confirmed boundary events counter the dialogue-blocking hidden-factor rule while preserving traceability.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.hidden_factor_persistent_state_001",
        case_type="composite_conflict",
        domain="hidden_factor_state",
        chart_input={
            "day_master": "甲",
            "hidden_factor_user_calibrated": "true",
            "special_event_year": "2023",
            "repeated_state": "career_pressure_repeat",
        },
        expected_domains={"feedback", "rule", "ten_god"},
        expected_rule_states={"hidden_factor": "countered"},
        expected_hidden_factor_state_status="amplifier_candidate",
        expected_min_path_scores={"rule_countered_count": 1.0},
        notes="Hidden-factor dialogue feedback should create an amplifier candidate state without mutating chart facts.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.hidden_factor_multi_year_state_001",
        case_type="boundary_gradient",
        domain="hidden_factor_state",
        chart_input={
            "day_master": "甲",
            "luck_pillar": "戊辰",
            "flow_year_pillar": "甲辰",
            "special_event_years": [2021, 2023, 2024],
            "repeated_states": ["career_pressure_repeat", "career_transition_repeat"],
        },
        expected_domains={"rule", "ten_god", "time_context"},
        expected_hidden_factor_state_status="amplifier_candidate",
        negative_expectations={"hidden_factor_requires_dialogue"},
        notes="Multi-year event alignment plus a narrow repeated career state should produce a stronger feedback-conditioned amplifier.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.hidden_factor_year_only_state_001",
        case_type="boundary_gradient",
        domain="hidden_factor_state",
        chart_input={
            "day_master": "甲",
            "special_event_year": "2022",
        },
        expected_domains={"rule", "ten_god"},
        expected_hidden_factor_state_status="dialogue_in_progress",
        negative_expectations={"hidden_factor_requires_dialogue"},
        notes="A special year alone advances dialogue but must not become an amplifier candidate.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.hidden_factor_repeated_state_only_001",
        case_type="boundary_gradient",
        domain="hidden_factor_state",
        chart_input={
            "day_master": "甲",
            "repeated_state": "relationship_repeat",
        },
        expected_domains={"rule", "ten_god"},
        expected_hidden_factor_state_status="dialogue_in_progress",
        negative_expectations={"hidden_factor_requires_dialogue"},
        notes="A repeated state alone advances dialogue but still needs special-year alignment.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.hidden_factor_denial_001",
        case_type="negative_counter",
        domain="hidden_factor_state",
        chart_input={
            "day_master": "甲",
            "confirmed": "false",
        },
        expected_domains={"rule", "ten_god"},
        expected_hidden_factor_state_status="user_denied",
        negative_expectations={"hidden_factor_requires_dialogue"},
        notes="User denial should lower hidden-factor status instead of forcing an amplifier candidate.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.hidden_factor_candidate_then_denial_001",
        case_type="composite_conflict",
        domain="hidden_factor_state",
        chart_input={
            "day_master": "甲",
            "feedback_sequence": [
                {
                    "feedback_id": "candidate-feedback",
                    "special_event_year": "2022",
                    "repeated_state": "wealth_pressure_repeat",
                },
                {
                    "feedback_id": "denial-feedback",
                    "feedback_status": "denied",
                },
            ],
        },
        expected_domains={"rule", "ten_god"},
        expected_hidden_factor_state_status="conflicting",
        negative_expectations={"hidden_factor_requires_dialogue"},
        notes="A denial after an amplifier candidate must win conflict priority and downgrade candidate use.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.useful_god_feedback_counter_001",
        case_type="composite_conflict",
        domain="useful_god_feedback",
        chart_input={"day_master": "甲", "useful_god_path_resolved": "true"},
        expected_domains={"feedback", "rule", "useful_god"},
        expected_rule_states={"useful_god": "countered"},
        expected_min_path_scores={"rule_countered_count": 1.0},
        expected_rule_weakens={"useful_god": {"fixed_useful_god_verdict"}},
        notes="Resolved useful-god path counters the candidate gate while keeping traceability and avoiding unbound verdicts.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.gradient.branch_relation_feedback_counter_001",
        case_type="composite_conflict",
        domain="branch_relation_feedback",
        chart_input={"day_master": "甲", "branch_single_factor_confirmed": "true"},
        expected_domains={"feedback", "rule", "branch_relation"},
        expected_rule_states={"branch_relation": "countered"},
        expected_min_path_scores={"rule_countered_count": 1.0},
        expected_rule_weakens={"branch_relation": {"single_factor_reading"}},
        notes="Confirmed single-factor branch reading counters the dynamic-review rule but remains feedback evidence, not chart fact.",
    ),
)


SYNTHETIC_TRAINING_PIPELINE_CASES = (
    SYNTHETIC_M1_M2_BAZI_CALCULATION_CASES
    + SYNTHETIC_PRACTICAL_MAINLINE_CASES
    + SYNTHETIC_TEN_GOD_ENERGY_CALIBRATION_CASES
    + SYNTHETIC_M4_TEN_GOD_REAL_CASE_REPLAY_CASES
    + SYNTHETIC_REAL_CASE_VALIDATION_CASES
    + SYNTHETIC_REAL_CASE_CALIBRATION_PACK_CASES
    + SYNTHETIC_INTERACTION_LOOP_CASES
    + SYNTHETIC_INTERACTION_BRAIN_STRUCTURED_CONSTRAINT_CASES
    + SYNTHETIC_CENTRAL_BRAIN_CASES
    + SYNTHETIC_GRADIENT_CASES
)


SYNTHETIC_BAZI_LLM_ACCEPTANCE_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.bazi_llm_acceptance.customer_accepted_001",
        case_type="positive_prototype",
        domain="bazi_llm_acceptance",
        chart_input={"day_master": "甲"},
        notes="Bazi LLM customer initial output must pass schema, role visibility, drift, and no-mutation gates.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.bazi_llm_acceptance.domain_followup_accepted_001",
        case_type="positive_prototype",
        domain="bazi_llm_acceptance",
        chart_input={"day_master": "甲"},
        notes="Bazi LLM domain follow-up output must pass domain schema and drift gates.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.bazi_llm_acceptance.schema_rejected_001",
        case_type="negative_counter",
        domain="bazi_llm_acceptance",
        chart_input={"day_master": "甲"},
        notes="Missing required Bazi LLM output schema fields must be rejected.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.bazi_llm_acceptance.role_leak_rejected_001",
        case_type="negative_counter",
        domain="bazi_llm_acceptance",
        chart_input={"day_master": "甲"},
        notes="Customer role diagnostics/policy/internal-id leakage must be rejected.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.bazi_llm_acceptance.drift_rejected_001",
        case_type="negative_counter",
        domain="bazi_llm_acceptance",
        chart_input={"day_master": "甲"},
        notes="Bazi LLM deterministic timing drift must be rejected before text replacement.",
    ),
)


SYNTHETIC_UI_CORE_READING_PRODUCT_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.ui_core_reading_product.metal_resource_pressure_001",
        case_type="positive_prototype",
        domain="ui_core_reading_product",
        chart_input={"day_master": "庚", "day_master_element": "metal", "luck_pillar": "戊寅", "flow_year_pillar": "庚子"},
        notes="Product reading must expose concrete assertions, features, portraits, paths, role adaptation, and compact LLM context.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.ui_core_reading_product.wood_growth_conflict_001",
        case_type="composite_conflict",
        domain="ui_core_reading_product",
        chart_input={"day_master": "甲", "day_master_element": "wood", "luck_pillar": "辛巳", "flow_year_pillar": "甲辰"},
        notes="Product reading must avoid template language while showing structure and career/wealth routing.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.ui_core_reading_product.fire_output_wealth_001",
        case_type="positive_prototype",
        domain="ui_core_reading_product",
        chart_input={"day_master": "丙", "day_master_element": "fire", "luck_pillar": "己卯", "flow_year_pillar": "辛丑"},
        notes="Product reading validates domain card path summaries and customer-facing Bazi feature density.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.ui_core_reading_product.hidden_factor_boundary_001",
        case_type="boundary_gradient",
        domain="ui_core_reading_product",
        chart_input={"day_master": "庚", "hidden_factor_user_calibrated": "true", "luck_pillar": "戊寅", "flow_year_pillar": "丙午"},
        negative_expectations={"hidden_factor_requires_dialogue"},
        notes="Hidden factor can steer product reading and questions but must remain a feedback clue, not a chart fact.",
    ),
)


SYNTHETIC_REAL_BAZI_DIAGNOSIS_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.real_bazi_diagnosis.ready_geng_luck_flow_001",
        case_type="positive_prototype",
        domain="real_bazi_diagnosis",
        chart_input={"day_master": "庚", "luck_pillar": "戊寅", "flow_year_pillar": "庚子"},
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=30,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=20,
        expected_min_rbd_claims=45,
        expected_max_rbd_generic_language_rate=0.35,
        notes="RBD must turn M3/M4/M5 evidence into concrete, traceable Bazi diagnosis claims with luck/flow context.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_bazi_diagnosis.missing_time_boundary_001",
        case_type="negative_counter",
        domain="real_bazi_diagnosis",
        chart_input={"day_master": "甲"},
        expected_rbd_domains={"career", "wealth", "structure", "useful_god"},
        expected_min_rbd_rule_matches=20,
        expected_min_rbd_paths=5,
        expected_min_rbd_portraits=12,
        expected_min_rbd_claims=25,
        expected_max_rbd_generic_language_rate=0.45,
        negative_expectations={"no_timing_prediction_without_time", "no_fixed_useful_god_verdict"},
        notes="RBD must still diagnose visible structures while keeping unknown-time and useful-god boundaries.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_bazi_diagnosis.hidden_factor_feedback_001",
        case_type="composite_conflict",
        domain="real_bazi_diagnosis",
        chart_input={"day_master": "庚", "hidden_factor_user_calibrated": "true"},
        expected_rbd_domains={"hidden_factor", "structure", "useful_god", "career"},
        expected_min_rbd_rule_matches=25,
        expected_min_rbd_paths=6,
        expected_min_rbd_portraits=15,
        expected_min_rbd_claims=30,
        expected_max_rbd_generic_language_rate=0.4,
        negative_expectations={"hidden_factor_requires_dialogue"},
        notes="Hidden-factor material can route and calibrate diagnosis but cannot become a deterministic chart fact.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.real_bazi_diagnosis.customer_projection_001",
        case_type="positive_prototype",
        domain="real_bazi_diagnosis",
        chart_input={"day_master": "庚", "luck_pillar": "戊寅", "flow_year_pillar": "庚子"},
        expected_rbd_domains={"career", "wealth", "timing"},
        expected_min_rbd_rule_matches=30,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=20,
        expected_min_rbd_claims=45,
        expected_max_rbd_generic_language_rate=0.35,
        notes="Customer surface should expose diagnosis statements, not RBD internals or raw traces.",
    ),
)


SYNTHETIC_ARCHETYPE_RULE_CLAIM_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.archetype_rule_claim.metal_resource_pressure_001",
        case_type="positive_prototype",
        domain="real_bazi_diagnosis",
        chart_input={"day_master": "庚", "day_master_element": "metal", "luck_pillar": "戊寅", "flow_year_pillar": "庚子"},
        expected_ranked_primary_candidates={
            "strength": "weak",
            "useful_god": "resource_or_self_support_review",
        },
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=20,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=20,
        expected_min_rbd_claims=50,
        expected_max_rbd_generic_language_rate=0.2,
        expected_min_expression_bazi_terms=0,
        notes="SYN-CAL1 archetype: metal resource/responsibility pressure checks M3/M5/M6 rule-claim trace without real-person truth labels.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.archetype_rule_claim.wood_growth_conflict_001",
        case_type="positive_prototype",
        domain="real_bazi_diagnosis",
        chart_input={"day_master": "甲", "day_master_element": "wood", "luck_pillar": "戊寅", "flow_year_pillar": "庚子"},
        expected_ranked_primary_candidates={
            "strength": "strong",
            "useful_god": "output_or_wealth_release_review",
        },
        expected_rbd_domains={"career", "wealth", "relationship", "structure", "useful_god", "hidden_factor"},
        expected_min_rbd_rule_matches=20,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=20,
        expected_min_rbd_claims=50,
        expected_max_rbd_generic_language_rate=0.2,
        expected_min_expression_bazi_terms=0,
        notes="SYN-CAL1 archetype: wood growth/output conflict checks release-oriented ranked decision and claim coverage.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.archetype_rule_claim.fire_expression_wealth_001",
        case_type="positive_prototype",
        domain="real_bazi_diagnosis",
        chart_input={"day_master": "丙", "day_master_element": "fire", "luck_pillar": "己卯", "flow_year_pillar": "辛丑"},
        expected_ranked_primary_candidates={
            "strength": "weak",
            "useful_god": "resource_or_self_support_review",
        },
        expected_rbd_domains={"career", "wealth", "relationship", "structure", "useful_god"},
        expected_min_rbd_rule_matches=20,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=20,
        expected_min_rbd_claims=50,
        expected_max_rbd_generic_language_rate=0.2,
        expected_min_expression_bazi_terms=0,
        notes="SYN-CAL1 archetype: fire expression/wealth review checks bounded resource-support claim trace.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.archetype_rule_claim.water_flow_timing_001",
        case_type="positive_prototype",
        domain="real_bazi_diagnosis",
        chart_input={"day_master": "壬", "day_master_element": "water", "luck_pillar": "甲辰", "flow_year_pillar": "丙午"},
        expected_ranked_primary_candidates={
            "strength": "balanced",
            "useful_god": "balance_review",
        },
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=20,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=20,
        expected_min_rbd_claims=50,
        expected_max_rbd_generic_language_rate=0.2,
        expected_min_expression_bazi_terms=0,
        notes="SYN-CAL1 archetype: water balanced timing review checks stage/timing claims without fixed event prediction.",
    ),
)


SYNTHETIC_TYPICAL_BAZI_ANSWER_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.typical_answer.metal_career_001",
        case_type="positive_prototype",
        domain="synthetic_typical_bazi_answer",
        chart_input={"day_master": "庚", "day_master_element": "metal", "luck_pillar": "戊寅", "flow_year_pillar": "庚子"},
        expected_domains={"ten_god", "useful_god", "branch_relation"},
        expected_anchor_ids={"q_v30_user_career_direction"},
        expected_min_expression_bazi_terms=2,
        negative_expectations={"no_fixed_useful_god_verdict"},
        notes="CORE-CAL-S1 companion synthetic tier: metal day-master career answer calibration.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.typical_answer.metal_wealth_001",
        case_type="positive_prototype",
        domain="synthetic_typical_bazi_answer",
        chart_input={"day_master": "庚", "day_master_element": "metal", "luck_pillar": "戊寅", "flow_year_pillar": "庚子"},
        expected_domains={"ten_god", "useful_god", "branch_relation"},
        expected_anchor_ids={"q_v30_user_wealth_tendency"},
        expected_min_expression_bazi_terms=2,
        negative_expectations={"no_fixed_useful_god_verdict"},
        notes="CORE-CAL-S1 companion synthetic tier: wealth answer calibration surface.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.typical_answer.hidden_feedback_001",
        case_type="positive_prototype",
        domain="synthetic_typical_bazi_answer",
        chart_input={"day_master": "庚", "day_master_element": "metal", "luck_pillar": "戊寅", "flow_year_pillar": "庚子"},
        expected_domains={"ten_god", "useful_god", "branch_relation"},
        expected_anchor_ids={"q_v30_hidden_factor_boundary_discovery"},
        expected_min_expression_bazi_terms=2,
        negative_expectations={"hidden_factor_requires_dialogue"},
        notes="CORE-CAL-S1 companion synthetic tier: hidden attribute feedback boundary.",
    ),
)


SYNTHETIC_CANONICAL_BAZI_CALIBRATION_CASES = (
    SyntheticBaziCase(
        case_id="v30.synthetic.canonical_bazi.wealth_flow_geng_001",
        case_type="positive_prototype",
        domain="synthetic_canonical_bazi_calibration",
        chart_input={"day_master": "庚", "luck_pillar": "戊寅", "flow_year_pillar": "庚子"},
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=40,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=45,
        expected_min_rbd_claims=55,
        expected_max_rbd_generic_language_rate=0.2,
        notes="Synthetic canonical wealth/timing case validates traceable wealth and timing diagnosis paths without asserting real fortune truth.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.canonical_bazi.career_officer_jia_001",
        case_type="positive_prototype",
        domain="synthetic_canonical_bazi_calibration",
        chart_input={"day_master": "甲", "luck_pillar": "辛巳", "flow_year_pillar": "甲辰"},
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=40,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=45,
        expected_min_rbd_claims=55,
        expected_max_rbd_generic_language_rate=0.2,
        notes="Synthetic canonical career/officer-pressure case validates career and structure routing without importing unverifiable biography.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.canonical_bazi.resource_balance_ding_001",
        case_type="positive_prototype",
        domain="synthetic_canonical_bazi_calibration",
        chart_input={"day_master": "丁", "luck_pillar": "壬午", "flow_year_pillar": "乙巳"},
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=40,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=40,
        expected_min_rbd_claims=55,
        expected_max_rbd_generic_language_rate=0.2,
        notes="Synthetic canonical resource/fire balance case validates profile and health-structure evidence density.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.canonical_bazi.earth_structure_wu_001",
        case_type="positive_prototype",
        domain="synthetic_canonical_bazi_calibration",
        chart_input={"day_master": "戊", "luck_pillar": "戊寅", "flow_year_pillar": "甲辰"},
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=40,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=45,
        expected_min_rbd_claims=55,
        expected_max_rbd_generic_language_rate=0.2,
        notes="Synthetic canonical earth/structure case validates dynamic structure and useful-god candidate evidence.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.canonical_bazi.water_timing_ren_001",
        case_type="positive_prototype",
        domain="synthetic_canonical_bazi_calibration",
        chart_input={"day_master": "壬", "luck_pillar": "辛巳", "flow_year_pillar": "庚子"},
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=40,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=45,
        expected_min_rbd_claims=55,
        expected_max_rbd_generic_language_rate=0.2,
        notes="Synthetic canonical water/timing case validates flow-year and luck-cycle triggered diagnosis paths without fixed-event prediction.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.canonical_bazi.hidden_factor_feedback_geng_001",
        case_type="composite_conflict",
        domain="synthetic_canonical_bazi_calibration",
        chart_input={"day_master": "庚", "hidden_factor_user_calibrated": "true", "luck_pillar": "戊寅"},
        expected_rbd_domains={"career", "wealth", "hidden_factor", "structure", "useful_god"},
        expected_min_rbd_rule_matches=40,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=40,
        expected_min_rbd_claims=55,
        expected_max_rbd_generic_language_rate=0.2,
        negative_expectations={"hidden_factor_requires_dialogue"},
        notes="Synthetic hidden-factor feedback case verifies hidden factors remain calibration clues, not deterministic chart facts.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.canonical_bazi.weak_body_many_wealth_yi_001",
        case_type="composite_conflict",
        domain="synthetic_canonical_bazi_calibration",
        chart_input={"day_master": "乙", "luck_pillar": "戊寅", "flow_year_pillar": "庚子"},
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=40,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=45,
        expected_min_rbd_claims=55,
        expected_max_rbd_generic_language_rate=0.2,
        notes="Expansion: 财多身弱候选. Validates wealth pressure and useful-god candidate routing as structural expectation only.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.canonical_bazi.output_generates_wealth_bing_001",
        case_type="positive_prototype",
        domain="synthetic_canonical_bazi_calibration",
        chart_input={"day_master": "丙", "luck_pillar": "辛巳", "flow_year_pillar": "乙巳"},
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=40,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=45,
        expected_min_rbd_claims=55,
        expected_max_rbd_generic_language_rate=0.2,
        notes="Expansion: 食伤生财候选. Validates output-to-wealth path detection without final profit verdict.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.canonical_bazi.mixed_officer_killing_xin_001",
        case_type="composite_conflict",
        domain="synthetic_canonical_bazi_calibration",
        chart_input={"day_master": "辛", "luck_pillar": "壬午", "flow_year_pillar": "甲辰"},
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=40,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=45,
        expected_min_rbd_claims=55,
        expected_max_rbd_generic_language_rate=0.2,
        notes="Expansion: 官杀混杂候选. Validates pressure/role-boundary routing without fixed career outcome.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.canonical_bazi.resource_peer_heavy_gui_001",
        case_type="composite_conflict",
        domain="synthetic_canonical_bazi_calibration",
        chart_input={"day_master": "癸", "luck_pillar": "辛巳", "flow_year_pillar": "庚子"},
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=40,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=45,
        expected_min_rbd_claims=55,
        expected_max_rbd_generic_language_rate=0.2,
        notes="Expansion: 印比过重候选. Validates resource/peer density path and action-boundary expression.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.canonical_bazi.wealth_officer_resource_chain_ji_001",
        case_type="positive_prototype",
        domain="synthetic_canonical_bazi_calibration",
        chart_input={"day_master": "己", "luck_pillar": "戊寅", "flow_year_pillar": "甲辰"},
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=40,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=45,
        expected_min_rbd_claims=55,
        expected_max_rbd_generic_language_rate=0.2,
        notes="Expansion: 财官印相生候选. Validates chained domain evidence without declaring final success.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.canonical_bazi.cold_hot_dry_wet_imbalance_ding_001",
        case_type="boundary_gradient",
        domain="synthetic_canonical_bazi_calibration",
        chart_input={"day_master": "丁", "luck_pillar": "辛巳", "flow_year_pillar": "庚子"},
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=40,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=40,
        expected_min_rbd_claims=55,
        expected_max_rbd_generic_language_rate=0.2,
        notes="Expansion: 寒热燥湿偏枯候选. Validates health/structure language as bounded tendency, not medical prediction.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.canonical_bazi.clash_combine_harm_mao_you_001",
        case_type="boundary_gradient",
        domain="synthetic_canonical_bazi_calibration",
        chart_input={"day_master": "庚", "luck_pillar": "壬午", "flow_year_pillar": "乙巳"},
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=40,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=45,
        expected_min_rbd_claims=55,
        expected_max_rbd_generic_language_rate=0.2,
        notes="Expansion: 刑冲合害明显候选. Validates dynamic relation routing without fixed incident prediction.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.canonical_bazi.follow_strong_candidate_jia_001",
        case_type="boundary_gradient",
        domain="synthetic_canonical_bazi_calibration",
        chart_input={"day_master": "甲", "luck_pillar": "戊寅", "flow_year_pillar": "乙巳", "useful_god_path_resolved": "true"},
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=40,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=45,
        expected_min_rbd_claims=55,
        expected_max_rbd_generic_language_rate=0.2,
        negative_expectations={"no_fixed_useful_god_verdict"},
        notes="Expansion: 从强候选边界. Validates candidate framing and avoids fixed useful-god verdict.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.canonical_bazi.luck_cycle_structure_shift_wu_001",
        case_type="metamorphic_pair",
        domain="synthetic_canonical_bazi_calibration",
        chart_input={"day_master": "戊", "luck_pillar": "辛巳", "flow_year_pillar": "甲辰"},
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=40,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=45,
        expected_min_rbd_claims=55,
        expected_max_rbd_generic_language_rate=0.2,
        notes="Expansion: 大运触发结构变化. Validates luck-cycle evidence in diagnosis paths.",
    ),
    SyntheticBaziCase(
        case_id="v30.synthetic.canonical_bazi.flow_year_domain_trigger_ren_001",
        case_type="metamorphic_pair",
        domain="synthetic_canonical_bazi_calibration",
        chart_input={"day_master": "壬", "luck_pillar": "戊寅", "flow_year_pillar": "庚子"},
        expected_rbd_domains={"career", "wealth", "relationship", "health", "timing", "structure", "useful_god"},
        expected_min_rbd_rule_matches=40,
        expected_min_rbd_paths=8,
        expected_min_rbd_portraits=45,
        expected_min_rbd_claims=55,
        expected_max_rbd_generic_language_rate=0.2,
        notes="Expansion: 流年触发领域主题. Validates flow-year evidence and timing domain without event certainty.",
    ),
)


SYNTHETIC_SUITES: dict[str, tuple[SyntheticBaziCase, ...]] = {
    "smoke": SYNTHETIC_SMOKE_CASES,
    "core_calculation": SYNTHETIC_CORE_CALCULATION_CASES,
    "core_bazi_calculation": SYNTHETIC_CORE_CALCULATION_CASES,
    "m1_m2_bazi_calculation": SYNTHETIC_M1_M2_BAZI_CALCULATION_CASES,
    "luck_cycle": SYNTHETIC_PRACTICAL_MAINLINE_CASES[:1],
    "flow_timing": SYNTHETIC_PRACTICAL_MAINLINE_CASES[1:2],
    "six_pillar_context": SYNTHETIC_PRACTICAL_MAINLINE_CASES[2:3],
    "strength_structure_useful_god": SYNTHETIC_PRACTICAL_MAINLINE_CASES[3:4],
    "m5_ranked_decision_contract": SYNTHETIC_REAL_CASE_CALIBRATION_PACK_CASES,
    "m6_practical_reading_contract": SYNTHETIC_REAL_CASE_CALIBRATION_PACK_CASES,
    "m8_api_projection_contract": SYNTHETIC_REAL_CASE_CALIBRATION_PACK_CASES,
    "ten_god_energy_calibration": SYNTHETIC_TEN_GOD_ENERGY_CALIBRATION_CASES,
    "m4_ten_god_real_case_replay": SYNTHETIC_M4_TEN_GOD_REAL_CASE_REPLAY_CASES,
    "practical_reading": SYNTHETIC_PRACTICAL_MAINLINE_CASES[4:5],
    "agent_question_flow": SYNTHETIC_PRACTICAL_MAINLINE_CASES[5:],
    "real_case_validation": SYNTHETIC_REAL_CASE_VALIDATION_CASES,
    "real_case_calibration_pack": SYNTHETIC_REAL_CASE_CALIBRATION_PACK_CASES,
    "interaction_loop": SYNTHETIC_INTERACTION_LOOP_CASES,
    "interaction_brain_structured_constraints": SYNTHETIC_INTERACTION_BRAIN_STRUCTURED_CONSTRAINT_CASES,
    "central_brain": SYNTHETIC_CENTRAL_BRAIN_CASES,
    "bazi_llm_acceptance": SYNTHETIC_BAZI_LLM_ACCEPTANCE_CASES,
    "ui_core_reading_product": SYNTHETIC_UI_CORE_READING_PRODUCT_CASES,
    "real_bazi_diagnosis": SYNTHETIC_REAL_BAZI_DIAGNOSIS_CASES,
    "synthetic_archetype_rule_claim": SYNTHETIC_ARCHETYPE_RULE_CLAIM_CASES,
    "synthetic_typical_bazi_answer": SYNTHETIC_TYPICAL_BAZI_ANSWER_CASES,
    "synthetic_canonical_bazi_calibration": SYNTHETIC_CANONICAL_BAZI_CALIBRATION_CASES,
    "latent_bazi_divergence": (),
    "training_pipeline": SYNTHETIC_TRAINING_PIPELINE_CASES,
    "gradient": SYNTHETIC_GRADIENT_CASES,
    "knowledge_rule_portrait": tuple(
        row for row in SYNTHETIC_GRADIENT_CASES
        if row.domain == "knowledge_rule_portrait"
    ),
    "structure_dynamic_v2": tuple(
        row for row in SYNTHETIC_GRADIENT_CASES
        if row.domain == "structure_dynamic_v2"
    ),
    "m3_core_spine": (
        SYNTHETIC_GRADIENT_CASES[0:3]
        + SYNTHETIC_GRADIENT_CASES[5:6]
        + SYNTHETIC_GRADIENT_CASES[9:11]
        + SYNTHETIC_GRADIENT_CASES[-2:]
    ),
    "all": (
        SYNTHETIC_SMOKE_CASES
        + SYNTHETIC_CORE_CALCULATION_CASES
        + SYNTHETIC_M1_M2_BAZI_CALCULATION_CASES
        + SYNTHETIC_PRACTICAL_MAINLINE_CASES
        + SYNTHETIC_TEN_GOD_ENERGY_CALIBRATION_CASES
        + SYNTHETIC_M4_TEN_GOD_REAL_CASE_REPLAY_CASES
        + SYNTHETIC_REAL_CASE_VALIDATION_CASES
        + SYNTHETIC_REAL_CASE_CALIBRATION_PACK_CASES
        + SYNTHETIC_INTERACTION_LOOP_CASES
        + SYNTHETIC_INTERACTION_BRAIN_STRUCTURED_CONSTRAINT_CASES
        + SYNTHETIC_CENTRAL_BRAIN_CASES
        + SYNTHETIC_UI_CORE_READING_PRODUCT_CASES
        + SYNTHETIC_GRADIENT_CASES
        + SYNTHETIC_REAL_BAZI_DIAGNOSIS_CASES
        + SYNTHETIC_CANONICAL_BAZI_CALIBRATION_CASES
    ),
}


def run_synthetic_case(
    case: SyntheticBaziCase,
    *,
    policy_payload_overrides: dict[str, dict[str, object]] | None = None,
    active_policy_version_overrides: dict[str, str] | None = None,
) -> SyntheticValidationResult:
    policy_payloads = dict(policy_payload_overrides or {})
    active_policy_versions = dict(active_policy_version_overrides or {})
    if case.question_policy_override:
        policy_payloads["question_policy"] = case.question_policy_override
        active_policy_versions["question_policy"] = "question_policy.synthetic_override"
    if case.rule_policy_override:
        policy_payloads["rule_policy"] = case.rule_policy_override
        active_policy_versions["rule_policy"] = "rule_policy.synthetic_override"
    runtime, chart_build = _runtime_from_case(
        case,
        policy_payloads=policy_payloads,
        active_policy_versions=active_policy_versions,
    )
    if chart_build is not None and case.expected_chart_build_status:
        if chart_build["status"] != case.expected_chart_build_status:
            return SyntheticValidationResult(
                case_id=case.case_id,
                passed=False,
                failures=[f"chart_build_status:{chart_build['status']}!={case.expected_chart_build_status}"],
                observed={"chart_build": chart_build},
            )
    if runtime is None:
        failures = []
        if not case.expected_chart_build_status:
            failures.append("runtime_missing_without_expected_chart_build_status")
        if "no_birth_input_fake_pillars" in case.negative_expectations and chart_build:
            if chart_build.get("pillars"):
                failures.append("birth_input_fake_pillars_present")
        real_case_fixture = _real_case_fixture_observation(case, chart_build=chart_build)
        return SyntheticValidationResult(
            case_id=case.case_id,
            passed=not failures,
            failures=failures,
            observed={
                "case_domain": case.domain,
                "chart_build": chart_build or {},
                "birth_chart_conversion_boundary": _birth_chart_conversion_boundary_observation(chart_build),
                "real_case_fixture": real_case_fixture,
                "production_replay_metadata": build_production_replay_metadata(real_case_fixture),
            },
        )
    domains = {row.domain for row in runtime.feature_evidence}
    anchor_ids = {row.question_id for row in runtime.question_anchors}
    failures: list[str] = []
    missing_domains = sorted(case.expected_domains - domains)
    missing_anchors = sorted(case.expected_anchor_ids - anchor_ids)
    if missing_domains:
        failures.append("missing_domains:" + ",".join(missing_domains))
    if missing_anchors:
        failures.append("missing_anchors:" + ",".join(missing_anchors))
    if case.expected_chart_build_status:
        status = str((chart_build or {}).get("status") or "")
        if status != case.expected_chart_build_status:
            failures.append(f"chart_build_status:{status}!={case.expected_chart_build_status}")
    if case.expected_chart_build_source:
        source = str((chart_build or {}).get("chart_build_source", {}).get("source_type") or "")
        if source != case.expected_chart_build_source:
            failures.append(f"chart_build_source:{source}!={case.expected_chart_build_source}")
    if case.expected_chart_build_pillars:
        pillars = (chart_build or {}).get("pillars", {})
        pillars = pillars if isinstance(pillars, dict) else {}
        for pillar_key, expected_pillar in case.expected_chart_build_pillars.items():
            observed_pillar = str(pillars.get(pillar_key) or "")
            if observed_pillar != expected_pillar:
                failures.append(f"chart_build_pillar:{pillar_key}:{observed_pillar}!={expected_pillar}")
    if case.expected_boundary_flags:
        observed_flags = set(
            str(flag)
            for flag in (chart_build or {}).get("conversion_trace", {}).get("boundary_flags", [])
        ) if isinstance((chart_build or {}).get("conversion_trace", {}), dict) else set()
        missing_flags = sorted(case.expected_boundary_flags - observed_flags)
        if missing_flags:
            failures.append("boundary_flags_missing:" + ",".join(missing_flags))
    if case.expected_day_master and runtime.chart_context.day_master != case.expected_day_master:
        failures.append(f"day_master:{runtime.chart_context.day_master}!={case.expected_day_master}")
    six_context = runtime.chart_context.time_layers.get("six_pillar_context", {})
    if case.expected_six_pillar_status:
        status = str(six_context.get("status") if isinstance(six_context, dict) else "")
        if status != case.expected_six_pillar_status:
            failures.append(f"six_pillar_status:{status}!={case.expected_six_pillar_status}")
    if "no_fixed_useful_god_verdict" in case.negative_expectations:
        useful_evidence = [row for row in runtime.feature_evidence if row.domain == "useful_god"]
        if not useful_evidence or any("fixed_useful_god_verdict" not in row.weakens for row in useful_evidence):
            failures.append("fixed_useful_god_boundary_missing")
    if "no_timing_prediction_without_time" in case.negative_expectations:
        time_evidence = [row for row in runtime.feature_evidence if row.domain == "time_context"]
        if not time_evidence or any("timing_claim" not in row.weakens for row in time_evidence):
            failures.append("timing_boundary_missing")
    if "hidden_factor_requires_dialogue" in case.negative_expectations:
        hidden_recommendations = [
            row for row in runtime.question_plan.recommended_questions
            if row.get("topic") == "hidden_factor"
        ]
        hidden_probes = runtime.question_plan.hidden_factor_probes
        if not hidden_recommendations:
            failures.append("hidden_factor_recommendation_missing")
        if not hidden_probes or hidden_probes[0].get("status") != "needs_dialogue":
            failures.append("hidden_factor_probe_dialogue_boundary_missing")
    if case.expected_signal_types:
        signal_types = {
            str(row.get("signal_type")) for row in runtime.question_plan.knowledge_rule_portrait_signals
        }
        missing_signal_types = sorted(case.expected_signal_types - signal_types)
        if missing_signal_types:
            failures.append("missing_signal_types:" + ",".join(missing_signal_types))
        if not any(row.startswith("rule_signal:") for row in runtime.mainline_state.supporting_mainlines):
            failures.append("krp_rule_signal_not_consumed_by_mainline")
        if runtime.structure_state.path_scores.get("knowledge_signal_count", 0.0) < 1.0:
            failures.append("krp_knowledge_signal_not_consumed_by_structure")
        recommendation_reasons = {
            str(reason)
            for row in runtime.question_plan.recommended_questions
            for reason in row.get("reasons", [])
        }
        if "rule_signal_blocks_fixed_useful_god" not in recommendation_reasons:
            failures.append("krp_rule_signal_not_consumed_by_question_recommender")
        if not any(reason.startswith("macro_dimension_context:") for reason in recommendation_reasons):
            failures.append("macro_dimension_signal_not_consumed_by_question_recommender")
    if case.expected_mechanisms:
        mechanism_ids = {
            str(node.get("node_id"))
            for node in runtime.structure_state.graph_nodes
            if node.get("kind") == "mechanism_path"
        }
        missing_mechanisms = sorted(case.expected_mechanisms - mechanism_ids)
        if missing_mechanisms:
            failures.append("missing_mechanisms:" + ",".join(missing_mechanisms))
        if runtime.structure_state.path_scores.get("mechanism_path_count", 0.0) < len(case.expected_mechanisms):
            failures.append("mechanism_path_count_too_low")
    recommendations = runtime.question_plan.recommended_questions
    if case.expected_top_topic:
        observed_top_topic = str(recommendations[0].get("topic")) if recommendations else ""
        if observed_top_topic != case.expected_top_topic:
            failures.append(f"top_topic_mismatch:{observed_top_topic}!={case.expected_top_topic}")
    for topic, minimum in case.expected_min_policy_weight_by_topic.items():
        weights = [
            float(row.get("policy_weight", 1.0))
            for row in recommendations
            if row.get("topic") == topic
        ]
        if not weights or max(weights) < minimum:
            failures.append(f"policy_weight_below_min:{topic}:{max(weights, default=0.0)}<{minimum}")
    for path_score, minimum in case.expected_min_path_scores.items():
        observed = float(runtime.structure_state.path_scores.get(path_score, 0.0))
        if observed < minimum:
            failures.append(f"path_score_below_min:{path_score}:{observed}<{minimum}")
    hidden_factor_state = {}
    if case.expected_hidden_factor_state_status:
        from v30.hidden_factor import HiddenFactorCalibration

        state = _build_case_hidden_factor_state(
            runtime=runtime,
            calibration=HiddenFactorCalibration.model_validate(
                runtime.question_plan.policy_effect["hidden_factor_calibration"]
            ),
            chart_input=case.chart_input,
        )
        hidden_factor_state = state.model_dump(mode="json")
        if state.status != case.expected_hidden_factor_state_status:
            failures.append(f"hidden_factor_state_status:{state.status}!={case.expected_hidden_factor_state_status}")
        runtime = attach_hidden_factor_state(runtime, hidden_factor_state)
    if case.question_outcome_answer:
        outcome_payload = dict(case.question_outcome_answer)
        outcome_question_id = str(outcome_payload.pop("question_id", "") or (recommendations[0].get("question_id") if recommendations else ""))
        runtime = attach_question_outcome(runtime, outcome_question_id, outcome_payload)
        recommendations = runtime.question_plan.recommended_questions
    question_graph = runtime.question_plan.policy_effect.get("question_dialogue_graph", {})
    interaction_state = runtime.question_plan.policy_effect.get("interaction_state", {})
    central_brain_trace = runtime.question_plan.policy_effect.get("central_brain_trace", {})
    adaptive_question_diagnostics = runtime.question_plan.policy_effect.get("adaptive_question_diagnostics", {})
    expression_quality = _expression_quality(runtime.question_plan.policy_effect)
    llm_contract_quality = _llm_contract_quality(runtime.question_plan.policy_effect)
    practical_reading = runtime.question_plan.policy_effect.get("practical_reading_context", {})
    ranked_decisions = runtime.question_plan.policy_effect.get("ranked_decisions", {})
    agent_question_flow = runtime.question_plan.policy_effect.get("agent_question_flow", {})
    real_bazi_diagnosis = runtime.question_plan.policy_effect.get("real_bazi_diagnosis", {})
    model_signal_summary = runtime.question_plan.policy_effect.get("model_signal_summary", {})
    model_signal_bands = (
        model_signal_summary.get("energy_bands", [])
        if isinstance(model_signal_summary, dict) and isinstance(model_signal_summary.get("energy_bands", []), list)
        else []
    )
    if case.expected_model_signal_families:
        observed_families = {
            str(row.get("family"))
            for row in model_signal_bands
            if isinstance(row, dict) and row.get("family")
        }
        missing_families = sorted(case.expected_model_signal_families - observed_families)
        if missing_families:
            failures.append("model_signal_families_missing:" + ",".join(missing_families))
    if case.expected_model_signal_energy_bands:
        observed_band_by_label = {
            str(row.get("label")): str(row.get("energy_band") or "")
            for row in model_signal_bands
            if isinstance(row, dict) and row.get("label")
        }
        for label, expected_band in case.expected_model_signal_energy_bands.items():
            observed_band = observed_band_by_label.get(label, "")
            if observed_band != expected_band:
                failures.append(f"model_signal_energy_band:{label}:{observed_band}!={expected_band}")
    if case.expected_min_model_signal_counts:
        count_sources = {
            "energy_band": len(model_signal_bands),
            "dominant": len(model_signal_summary.get("dominant_ten_gods", [])) if isinstance(model_signal_summary, dict) and isinstance(model_signal_summary.get("dominant_ten_gods", []), list) else 0,
            "volatility_alert": len(model_signal_summary.get("volatility_alerts", [])) if isinstance(model_signal_summary, dict) and isinstance(model_signal_summary.get("volatility_alerts", []), list) else 0,
            "stability_alert": len(model_signal_summary.get("stability_alerts", [])) if isinstance(model_signal_summary, dict) and isinstance(model_signal_summary.get("stability_alerts", []), list) else 0,
        }
        for key, minimum in case.expected_min_model_signal_counts.items():
            observed_count = int(count_sources.get(key, 0))
            if observed_count < int(minimum):
                failures.append(f"model_signal_count_below_min:{key}:{observed_count}<{minimum}")
    if case.expected_practical_reading_status:
        status = str(practical_reading.get("status") if isinstance(practical_reading, dict) else "")
        if status != case.expected_practical_reading_status:
            failures.append(f"practical_reading_status:{status}!={case.expected_practical_reading_status}")
    if case.expected_agent_question_stage:
        stage = str(agent_question_flow.get("next_stage") if isinstance(agent_question_flow, dict) else "")
        if stage != case.expected_agent_question_stage:
            failures.append(f"agent_question_stage:{stage}!={case.expected_agent_question_stage}")
    if case.expected_ranked_primary_candidates:
        for decision_domain, expected_primary in case.expected_ranked_primary_candidates.items():
            decision = ranked_decisions.get(decision_domain, {}) if isinstance(ranked_decisions, dict) else {}
            observed_primary = str(decision.get("primary_candidate") if isinstance(decision, dict) else "")
            if observed_primary != expected_primary:
                failures.append(
                    f"ranked_primary_candidate:{decision_domain}:{observed_primary}!={expected_primary}"
                )
    if case.expected_ranked_score_keys:
        for decision_domain, expected_keys in case.expected_ranked_score_keys.items():
            decision = ranked_decisions.get(decision_domain, {}) if isinstance(ranked_decisions, dict) else {}
            scores = decision.get("candidate_scores", {}) if isinstance(decision, dict) else {}
            observed_keys = set(scores) if isinstance(scores, dict) else set()
            missing_keys = sorted(expected_keys - observed_keys)
            if missing_keys:
                failures.append(f"ranked_score_keys_missing:{decision_domain}:{','.join(missing_keys)}")
    if case.expected_ranked_min_scores:
        for decision_domain, expected_scores in case.expected_ranked_min_scores.items():
            decision = ranked_decisions.get(decision_domain, {}) if isinstance(ranked_decisions, dict) else {}
            scores = decision.get("candidate_scores", {}) if isinstance(decision, dict) else {}
            if not isinstance(scores, dict):
                failures.append(f"ranked_score_payload_missing:{decision_domain}")
                continue
            for candidate_id, expected_min in expected_scores.items():
                observed_score = scores.get(candidate_id)
                if not isinstance(observed_score, (int, float)):
                    failures.append(f"ranked_score_missing:{decision_domain}:{candidate_id}")
                elif float(observed_score) < float(expected_min):
                    failures.append(
                        f"ranked_score_below_min:{decision_domain}:{candidate_id}:{observed_score}<{expected_min}"
                    )
    if case.expected_ranked_basis_values:
        for decision_domain, expected_values in case.expected_ranked_basis_values.items():
            decision = ranked_decisions.get(decision_domain, {}) if isinstance(ranked_decisions, dict) else {}
            basis = decision.get("scoring_basis", {}) if isinstance(decision, dict) else {}
            if not isinstance(basis, dict):
                failures.append(f"ranked_scoring_basis_missing:{decision_domain}")
                continue
            for key, expected_value in expected_values.items():
                observed_value = basis.get(key)
                if observed_value != expected_value:
                    failures.append(
                        f"ranked_basis_value:{decision_domain}:{key}:{observed_value}!={expected_value}"
                    )
    if case.domain == "strength_structure_useful_god":
        required_decision_domains = {"strength", "structure_pattern", "useful_god"}
        if not isinstance(ranked_decisions, dict) or not required_decision_domains.issubset(ranked_decisions):
            failures.append("ranked_decision_domains_missing")
        else:
            for decision_domain in sorted(required_decision_domains):
                decision = ranked_decisions.get(decision_domain, {})
                if not isinstance(decision, dict):
                    failures.append(f"ranked_decision_payload_missing:{decision_domain}")
                    continue
                scores = decision.get("candidate_scores", {})
                basis = decision.get("scoring_basis", {})
                primary = str(decision.get("primary_candidate") or "")
                if not isinstance(scores, dict) or not scores:
                    failures.append(f"ranked_decision_candidate_scores_missing:{decision_domain}")
                elif primary not in scores:
                    failures.append(f"ranked_decision_primary_not_scored:{decision_domain}")
                if not isinstance(basis, dict) or basis.get("version") != "v30.ranked_decision_scoring_basis.v1":
                    failures.append(f"ranked_decision_scoring_basis_missing:{decision_domain}")
    if expression_quality["forbidden_token_hits"]:
        failures.append("expression_forbidden_token_hits:" + ",".join(expression_quality["forbidden_token_hits"]))
    if int(expression_quality["bazi_term_count"]) < case.expected_min_expression_bazi_terms:
        failures.append(
            f"expression_bazi_term_count_below_min:{expression_quality['bazi_term_count']}<{case.expected_min_expression_bazi_terms}"
        )
    if not expression_quality["has_boundary_language"]:
        failures.append("expression_boundary_language_missing")
    if llm_contract_quality["validation_status"] != "passed":
        failures.append("llm_output_contract_failed")
    if case.expected_min_question_graph_edges:
        edge_count = len(question_graph.get("edges", [])) if isinstance(question_graph, dict) else 0
        if edge_count < case.expected_min_question_graph_edges:
            failures.append(
                f"question_graph_edges_below_min:{edge_count}<{case.expected_min_question_graph_edges}"
            )
    krp_units = runtime.question_plan.policy_effect.get("krp_library_units", [])
    krp_summary = runtime.question_plan.policy_effect.get("krp_library_summary", {})
    macro_summary = runtime.question_plan.policy_effect.get("core_macro_pack_summary", {})
    macro_signals = runtime.question_plan.policy_effect.get("macro_dimension_signals", [])
    portrait_projections = runtime.question_plan.policy_effect.get("macro_portrait_projections", [])
    user_portrait_views = runtime.question_plan.policy_effect.get("macro_portrait_projection_views", [])
    guest_portrait_views = build_macro_portrait_projection_views(
        [row for row in portrait_projections if isinstance(row, dict)],
        role_key="guest",
        client="web",
    )
    admin_portrait_views = build_macro_portrait_projection_views(
        [row for row in portrait_projections if isinstance(row, dict)],
        role_key="admin",
        client="admin",
    )
    if any(row.domain == "hidden_factor" for row in guest_portrait_views):
        failures.append("portrait_view_guest_hidden_factor_visible")
    if portrait_projections and not any(row.domain == "hidden_factor" for row in admin_portrait_views):
        failures.append("portrait_view_admin_hidden_factor_missing")
    if portrait_projections and not user_portrait_views:
        failures.append("portrait_view_user_default_missing")
    presentation = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")
    admin_presentation = build_presentation_model(runtime, role_key="admin", locale="zh", client="admin").model_dump(mode="json")
    projection_matrix = build_role_locale_client_projection_matrix(runtime)
    reading_surface = presentation.get("reading_surface", {})
    projection_contract = presentation.get("projection_contract", {})
    admin_projection_contract = admin_presentation.get("projection_contract", {})
    guest_presentation = build_presentation_model(runtime, role_key="guest", locale="zh", client="mobile").model_dump(mode="json")
    practitioner_presentation = build_presentation_model(runtime, role_key="practitioner", locale="zh", client="web").model_dump(mode="json")
    guest_diagnostics = guest_presentation.get("diagnostics", {})
    practitioner_diagnostics = practitioner_presentation.get("diagnostics", {})
    rendered_label_summary = presentation.get("layout", {}).get("rendered_question_label_summary", {})
    rendered_questions = presentation.get("questions", [])
    forbidden_label_tokens = {"policy_effect", "question_policy", "dynamic_graph", "evidence-bound", "Current chart", "Quality gate"}
    if not isinstance(rendered_label_summary, dict) or rendered_label_summary.get("label_count", 0) <= 0:
        failures.append("rendered_question_labels_missing")
    if any(
        token in str(question.get("label", ""))
        for question in rendered_questions
        if isinstance(question, dict)
        for token in forbidden_label_tokens
    ):
        failures.append("rendered_question_label_forbidden_token")
    if not isinstance(reading_surface, dict) or reading_surface.get("surface_type") != "customer_reading_loop":
        failures.append("customer_reading_surface_missing")
    if not isinstance(projection_contract, dict) or projection_contract.get("version") != "v30.api_projection_contract.v1":
        failures.append("api_projection_contract_missing")
    elif not projection_contract.get("leak_scan", {}).get("passed", False):
        failures.append("api_projection_contract_leak_scan_failed")
    if isinstance(projection_contract, dict):
        order = projection_contract.get("customer_surface_order", [])
        if order[:2] != ["core_bazi_reading", "domain_cards"]:
            failures.append("api_projection_contract_core_order_missing")
        core_first = projection_contract.get("core_first_projection", {})
        if not isinstance(core_first, dict) or core_first.get("calculation_before_questions") is not True:
            failures.append("api_projection_core_first_policy_missing")
        surface_contract = projection_contract.get("customer_surface_contract", {})
        if not isinstance(surface_contract, dict) or surface_contract.get("surface_prefix_ready") is not True:
            failures.append("api_projection_customer_surface_contract_missing")
        forbidden_policy = projection_contract.get("customer_forbidden_fields", {})
        if not isinstance(forbidden_policy, dict) or "raw_score" not in forbidden_policy.get("fields", []):
            failures.append("api_projection_forbidden_field_policy_missing")
        additive_policy = projection_contract.get("additive_api_policy", {})
        must_preserve = additive_policy.get("must_preserve", []) if isinstance(additive_policy, dict) else []
        if not {"core_bazi_reading", "domain_cards", "internal_next_question_id", "actor_context", "llm_runtime_status"} <= set(must_preserve):
            failures.append("api_projection_additive_policy_incomplete")
    if isinstance(admin_projection_contract, dict):
        if not admin_projection_contract.get("diagnostics_visible"):
            failures.append("api_projection_admin_diagnostics_missing")
    if case.domain == "central_brain":
        _validate_central_brain_synthetic_case(
            case=case,
            runtime=runtime,
            central_brain_trace=central_brain_trace,
            expression_quality=expression_quality,
            guest_diagnostics=guest_diagnostics if isinstance(guest_diagnostics, dict) else {},
            practitioner_diagnostics=practitioner_diagnostics if isinstance(practitioner_diagnostics, dict) else {},
            admin_diagnostics=admin_presentation.get("diagnostics", {}) if isinstance(admin_presentation.get("diagnostics", {}), dict) else {},
            failures=failures,
        )
    core_bazi_reading = reading_surface.get("core_bazi_reading", {}) if isinstance(reading_surface, dict) else {}
    if not isinstance(core_bazi_reading, dict) or core_bazi_reading.get("surface_type") != "core_bazi_calculation":
        failures.append("core_bazi_reading_missing")
    elif runtime is not None:
        if len(core_bazi_reading.get("four_pillars", [])) < 4:
            failures.append("core_bazi_four_pillars_missing")
        ranked_projection = core_bazi_reading.get("ranked_decisions", {})
        if not isinstance(ranked_projection, dict) or not {"strength", "structure_pattern", "useful_god"}.issubset(ranked_projection):
            failures.append("core_bazi_ranked_decisions_missing")
        summary = core_bazi_reading.get("base_fact_summary", {})
        summary = summary if isinstance(summary, dict) else {}
        if case.expected_base_fact_summary_keys:
            missing_summary_keys = sorted(case.expected_base_fact_summary_keys - set(summary))
            if missing_summary_keys:
                failures.append("base_fact_summary_keys_missing:" + ",".join(missing_summary_keys))
        if case.domain == "m1_m2_bazi_calculation":
            integrity = core_bazi_reading.get("fact_integrity", {})
            integrity = integrity if isinstance(integrity, dict) else {}
            explanations = core_bazi_reading.get("base_fact_explanations", {})
            explanations = explanations if isinstance(explanations, dict) else {}
            if integrity.get("deterministic") is not True:
                failures.append("core_fact_integrity_not_deterministic")
            if integrity.get("llm_generated") or integrity.get("training_generated") or integrity.get("feedback_generated"):
                failures.append("core_fact_integrity_non_deterministic_source")
            if summary.get("status") != "ready":
                failures.append("base_fact_summary_not_ready")
            if summary.get("pillar_count") != 4:
                failures.append(f"base_fact_pillar_count:{summary.get('pillar_count')}!=4")
            if int(summary.get("visible_ten_god_count", 0) or 0) < 3:
                failures.append("base_fact_visible_ten_god_count_too_low")
            if int(summary.get("hidden_ten_god_count", 0) or 0) <= 0:
                failures.append("base_fact_hidden_ten_god_count_missing")
            if not isinstance(summary.get("element_distribution"), dict) or not summary.get("element_distribution"):
                failures.append("base_fact_element_distribution_missing")
            if explanations.get("boundary") != "base_fact_explanations_are_deterministic_context_not_ranked_decisions":
                failures.append("base_fact_explanation_boundary_missing")
            root_summary = summary.get("root_fact_summary", {})
            if not isinstance(root_summary, dict) or root_summary.get("boundary") != "root_vault_summary_records_presence_without_strength_or_useful_god_verdict":
                failures.append("root_fact_summary_boundary_missing")
    if case.expected_interaction_stage:
        stage = str(interaction_state.get("interaction_stage") if isinstance(interaction_state, dict) else "")
        if stage != case.expected_interaction_stage:
            failures.append(f"interaction_stage:{stage}!={case.expected_interaction_stage}")
    if case.expected_selected_domain:
        selected_domain = str(interaction_state.get("selected_domain") if isinstance(interaction_state, dict) else "")
        if selected_domain != case.expected_selected_domain:
            failures.append(f"selected_domain:{selected_domain}!={case.expected_selected_domain}")
        surface_domain = str(reading_surface.get("selected_domain") if isinstance(reading_surface, dict) else "")
        if surface_domain != case.expected_selected_domain:
            failures.append(f"surface_selected_domain:{surface_domain}!={case.expected_selected_domain}")
    if case.expected_visible_next_question_id:
        visible_id = str(interaction_state.get("visible_next_question_id") if isinstance(interaction_state, dict) else "")
        if visible_id != case.expected_visible_next_question_id:
            failures.append(f"visible_next_question_id:{visible_id}!={case.expected_visible_next_question_id}")
        surface_visible_id = str(reading_surface.get("visible_next_question_id") if isinstance(reading_surface, dict) else "")
        if surface_visible_id != case.expected_visible_next_question_id:
            failures.append(f"surface_visible_next_question_id:{surface_visible_id}!={case.expected_visible_next_question_id}")
    if case.expected_internal_next_question_id:
        internal_id = str(interaction_state.get("internal_next_question_id") if isinstance(interaction_state, dict) else "")
        if internal_id != case.expected_internal_next_question_id:
            failures.append(f"internal_next_question_id:{internal_id}!={case.expected_internal_next_question_id}")
    if case.expected_followup_reason_prefix:
        reason = str(interaction_state.get("followup_reason") if isinstance(interaction_state, dict) else "")
        if not reason.startswith(case.expected_followup_reason_prefix):
            failures.append(f"followup_reason_prefix:{reason}!={case.expected_followup_reason_prefix}")
    if case.expected_answered_question_ids:
        answered_ids = {
            str(row)
            for row in interaction_state.get("answered_question_ids", [])
        } if isinstance(interaction_state, dict) and isinstance(interaction_state.get("answered_question_ids"), list) else set()
        missing_answered = sorted(case.expected_answered_question_ids - answered_ids)
        if missing_answered:
            failures.append("missing_answered_question_ids:" + ",".join(missing_answered))
    if case.expected_selected_option_ids:
        selected_option_ids = {
            str(row)
            for row in interaction_state.get("selected_option_ids", [])
        } if isinstance(interaction_state, dict) and isinstance(interaction_state.get("selected_option_ids"), list) else set()
        missing_options = sorted(case.expected_selected_option_ids - selected_option_ids)
        if missing_options:
            failures.append("missing_selected_option_ids:" + ",".join(missing_options))
    if case.expected_invalid_retry_question_id:
        retry_id = str(interaction_state.get("invalid_retry_question_id") if isinstance(interaction_state, dict) else "")
        if retry_id != case.expected_invalid_retry_question_id:
            failures.append(f"invalid_retry_question_id:{retry_id}!={case.expected_invalid_retry_question_id}")
    if case.expected_constraint_valid is not None:
        outcomes = runtime.question_plan.session_state.get("question_outcomes", [])
        latest_outcome = outcomes[-1] if isinstance(outcomes, list) and outcomes and isinstance(outcomes[-1], dict) else {}
        observed_valid = latest_outcome.get("constraint_valid") if isinstance(latest_outcome, dict) else None
        if observed_valid is not case.expected_constraint_valid:
            failures.append(f"constraint_valid:{observed_valid}!={case.expected_constraint_valid}")
    interaction_brain_result = runtime.question_plan.policy_effect.get("interaction_brain_result", {})
    if case.expected_interaction_brain_hidden_factor_allowed is not None:
        allowed = (
            interaction_brain_result.get("allowed_to_update_hidden_factor")
            if isinstance(interaction_brain_result, dict)
            else None
        )
        if allowed is not case.expected_interaction_brain_hidden_factor_allowed:
            failures.append(
                "interaction_brain_hidden_factor_allowed:"
                f"{allowed}!={case.expected_interaction_brain_hidden_factor_allowed}"
            )
    if case.expected_min_absorbed_signal_count:
        absorbed = (
            interaction_brain_result.get("absorbed_signals", [])
            if isinstance(interaction_brain_result, dict)
            else []
        )
        absorbed_count = len(absorbed) if isinstance(absorbed, list) else 0
        if absorbed_count < case.expected_min_absorbed_signal_count:
            failures.append(
                f"absorbed_signal_count:{absorbed_count}<{case.expected_min_absorbed_signal_count}"
            )
    if case.expected_min_rejected_signal_count:
        rejected = (
            interaction_brain_result.get("rejected_signals", [])
            if isinstance(interaction_brain_result, dict)
            else []
        )
        rejected_count = len(rejected) if isinstance(rejected, list) else 0
        if rejected_count < case.expected_min_rejected_signal_count:
            failures.append(
                f"rejected_signal_count:{rejected_count}<{case.expected_min_rejected_signal_count}"
            )
    if case.expect_visible_internal_split and isinstance(interaction_state, dict):
        if interaction_state.get("visible_next_question_id") == interaction_state.get("internal_next_question_id"):
            failures.append("visible_internal_next_question_not_split")
    customer_payload_text = str({
        "reading_surface": reading_surface,
        "questions": rendered_questions,
    })
    leaked_tokens = [
        token for token in ("feature_evidence_count", "structure_paths", "policy_payloads", "macro_portrait_projections")
        if token in customer_payload_text
    ]
    if leaked_tokens:
        failures.append("customer_surface_internal_context_leak:" + ",".join(leaked_tokens))
    if any(
        not isinstance(question.get("expected_information_gain"), dict)
        or not question.get("expected_information_gain", {}).get("primary_gain")
        for question in rendered_questions
        if isinstance(question, dict)
    ):
        failures.append("recommended_question_information_gain_missing")
    if case.expected_min_krp_unit_count:
        if len(krp_units) < case.expected_min_krp_unit_count:
            failures.append(f"krp_unit_count_below_min:{len(krp_units)}<{case.expected_min_krp_unit_count}")
    if case.expected_krp_unit_ids:
        unit_ids = {str(row.get("unit_id")) for row in krp_units if isinstance(row, dict)}
        missing_units = sorted(case.expected_krp_unit_ids - unit_ids)
        if missing_units:
            failures.append("missing_krp_units:" + ",".join(missing_units))
    if case.expected_krp_pack_ids:
        pack_ids = set(krp_summary.get("pack_ids", [])) if isinstance(krp_summary, dict) else set()
        missing_pack_ids = sorted(case.expected_krp_pack_ids - {str(row) for row in pack_ids})
        if missing_pack_ids:
            failures.append("missing_krp_pack_ids:" + ",".join(missing_pack_ids))
    if case.expected_krp_portrait_tags:
        portrait_tags = set(krp_summary.get("portrait_tags", [])) if isinstance(krp_summary, dict) else set()
        missing_tags = sorted(case.expected_krp_portrait_tags - {str(row) for row in portrait_tags})
        if missing_tags:
            failures.append("missing_krp_portrait_tags:" + ",".join(missing_tags))
    m3_completion_summary = runtime.question_plan.policy_effect.get("m3_completion_summary", {})
    if case.domain in {"m3_core_spine", "knowledge_rule_portrait", "structure_dynamic_v2", "structure_dynamic"}:
        if not isinstance(m3_completion_summary, dict) or m3_completion_summary.get("version") != "v30.m3_completion_summary.v1":
            failures.append("m3_completion_summary_missing")
        elif m3_completion_summary.get("status") != "ready":
            failures.append("m3_completion_summary_not_ready")
        elif m3_completion_summary.get("acts_as_conclusion_engine") is not False:
            failures.append("m3_completion_summary_conclusion_engine_boundary_failed")
    if case.expected_macro_domains:
        macro_domains = set(macro_summary.get("domains", [])) if isinstance(macro_summary, dict) else set()
        missing_macro_domains = sorted(case.expected_macro_domains - {str(row) for row in macro_domains})
        if missing_macro_domains:
            failures.append("missing_macro_domains:" + ",".join(missing_macro_domains))
    if case.expected_macro_signal_domains:
        signal_domains = {
            str(row.get("domain"))
            for row in macro_signals
            if isinstance(row, dict)
        }
        missing_signal_domains = sorted(case.expected_macro_signal_domains - signal_domains)
        if missing_signal_domains:
            failures.append("missing_macro_signal_domains:" + ",".join(missing_signal_domains))
    if case.expected_portrait_domains:
        portrait_domains = {
            str(row.get("domain"))
            for row in portrait_projections
            if isinstance(row, dict)
        }
        missing_portrait_domains = sorted(case.expected_portrait_domains - portrait_domains)
        if missing_portrait_domains:
            failures.append("missing_portrait_domains:" + ",".join(missing_portrait_domains))
    rule_evidence = [row for row in runtime.feature_evidence if row.domain == "rule"]
    for kind, minimum in case.expected_min_rule_confidence_by_kind.items():
        confidence = max((row.confidence for row in rule_evidence if row.kind == kind), default=0.0)
        if confidence < minimum:
            failures.append(f"rule_confidence_below_min:{kind}:{confidence}<{minimum}")
    for kind, expected_weakens in case.expected_rule_weakens.items():
        weakens = {
            item
            for row in rule_evidence
            if row.kind == kind
            for item in row.weakens
        }
        missing_weakens = sorted(expected_weakens - weakens)
        if missing_weakens:
            failures.append(f"missing_rule_weakens:{kind}:{','.join(missing_weakens)}")
    for kind, expected_state in case.expected_rule_states.items():
        states = {
            support.removeprefix("rule_decision_state:")
            for row in rule_evidence
            if row.kind == kind
            for support in row.supports
            if support.startswith("rule_decision_state:")
        }
        if expected_state not in states:
            failures.append(f"missing_rule_state:{kind}:{expected_state}")
    real_case_fixture = _real_case_fixture_observation(
        case,
        chart_build=chart_build or {
            "status": runtime.chart_context.input_pillars.get("chart_build_source", {}).get("status"),
            "chart_build_source": runtime.chart_context.input_pillars.get("chart_build_source", {}),
            "conversion_trace": runtime.chart_context.input_pillars.get("conversion_trace", {}),
        },
        runtime=runtime,
        practical_reading=practical_reading,
        agent_question_flow=agent_question_flow,
    )
    bazi_llm_acceptance_quality = _bazi_llm_output_acceptance_quality(case)
    real_bazi_diagnosis_quality = _real_bazi_diagnosis_quality(
        case,
        real_bazi_diagnosis,
        reading_surface=reading_surface,
        admin_presentation=admin_presentation,
    )
    ui_core_reading_product_quality = _ui_core_reading_product_quality(
        case,
        user_presentation=presentation,
        practitioner_presentation=practitioner_presentation,
    )
    if case.domain in {"real_bazi_diagnosis", "synthetic_canonical_bazi_calibration"}:
        if real_bazi_diagnosis_quality.get("status") != "ready":
            failures.append("real_bazi_diagnosis_not_ready")
        if int(real_bazi_diagnosis_quality.get("rule_match_count") or 0) < case.expected_min_rbd_rule_matches:
            failures.append(
                f"rbd_rule_match_count_below_min:{real_bazi_diagnosis_quality.get('rule_match_count')}<{case.expected_min_rbd_rule_matches}"
            )
        if int(real_bazi_diagnosis_quality.get("path_count") or 0) < case.expected_min_rbd_paths:
            failures.append(
                f"rbd_path_count_below_min:{real_bazi_diagnosis_quality.get('path_count')}<{case.expected_min_rbd_paths}"
            )
        if int(real_bazi_diagnosis_quality.get("portrait_count") or 0) < case.expected_min_rbd_portraits:
            failures.append(
                f"rbd_portrait_count_below_min:{real_bazi_diagnosis_quality.get('portrait_count')}<{case.expected_min_rbd_portraits}"
            )
        if int(real_bazi_diagnosis_quality.get("claim_count") or 0) < case.expected_min_rbd_claims:
            failures.append(
                f"rbd_claim_count_below_min:{real_bazi_diagnosis_quality.get('claim_count')}<{case.expected_min_rbd_claims}"
            )
        missing_rbd_domains = sorted(case.expected_rbd_domains - set(real_bazi_diagnosis_quality.get("domain_claims", [])))
        if missing_rbd_domains:
            failures.append("rbd_domains_missing:" + ",".join(missing_rbd_domains))
        if real_bazi_diagnosis_quality.get("untraceable_claim_count"):
            failures.append(f"rbd_untraceable_claims:{real_bazi_diagnosis_quality.get('untraceable_claim_count')}")
        if real_bazi_diagnosis_quality.get("llm_generated_claim_count"):
            failures.append(f"rbd_llm_generated_claims:{real_bazi_diagnosis_quality.get('llm_generated_claim_count')}")
        if real_bazi_diagnosis_quality.get("chart_fact_mutation_claim_count"):
            failures.append(
                f"rbd_chart_fact_mutation_claims:{real_bazi_diagnosis_quality.get('chart_fact_mutation_claim_count')}"
            )
        if real_bazi_diagnosis_quality.get("fixed_event_prediction_claim_count"):
            failures.append(
                f"rbd_fixed_event_prediction_claims:{real_bazi_diagnosis_quality.get('fixed_event_prediction_claim_count')}"
            )
        if float(real_bazi_diagnosis_quality.get("generic_language_rate") or 0.0) > case.expected_max_rbd_generic_language_rate:
            failures.append(
                f"rbd_generic_language_rate_too_high:{real_bazi_diagnosis_quality.get('generic_language_rate')}>{case.expected_max_rbd_generic_language_rate}"
            )
        if real_bazi_diagnosis_quality.get("customer_internal_leak_count"):
            failures.append(
                f"rbd_customer_internal_leak:{real_bazi_diagnosis_quality.get('customer_internal_leak_count')}"
            )
        if real_bazi_diagnosis_quality.get("admin_diagnostics_visible") is not True:
            failures.append("rbd_admin_diagnostics_missing")
        if real_bazi_diagnosis_quality.get("storage_authoritative_facts_stored_here") is not False:
            failures.append("rbd_storage_authoritative_fact_boundary_failed")
    if case.domain == "bazi_llm_acceptance":
        if bazi_llm_acceptance_quality.get("readiness_ready") is not True:
            failures.append("bazi_llm_acceptance_readiness_not_ready")
        if int(bazi_llm_acceptance_quality.get("accepted_count") or 0) < 2:
            failures.append("bazi_llm_acceptance_accepted_count_below_min")
        if int(bazi_llm_acceptance_quality.get("rejected_count") or 0) < 3:
            failures.append("bazi_llm_acceptance_rejected_count_below_min")
        if bazi_llm_acceptance_quality.get("live_llm_required") is not False:
            failures.append("bazi_llm_acceptance_live_llm_required")
        if bazi_llm_acceptance_quality.get("chart_fact_mutation_allowed") is not False:
            failures.append("bazi_llm_acceptance_chart_fact_mutation_allowed")
    if case.domain == "ui_core_reading_product":
        if ui_core_reading_product_quality.get("product_ready") is not True:
            failures.append("ui_core_reading_product_not_ready")
        if int(ui_core_reading_product_quality.get("basic_assertion_count") or 0) < 5:
            failures.append("ui_basic_assertion_count_below_min")
        if int(ui_core_reading_product_quality.get("feature_count") or 0) < 4:
            failures.append("ui_bazi_feature_count_below_min")
        if int(ui_core_reading_product_quality.get("portrait_count") or 0) < 4:
            failures.append("ui_bazi_portrait_count_below_min")
        if int(ui_core_reading_product_quality.get("path_count") or 0) < 3:
            failures.append("ui_bazi_path_count_below_min")
        if int(ui_core_reading_product_quality.get("domain_card_path_summary_count") or 0) < 3:
            failures.append("ui_domain_card_path_summary_count_below_min")
        if int(ui_core_reading_product_quality.get("domain_card_path_assertion_count") or 0) < 3:
            failures.append("ui_domain_card_path_assertion_count_below_min")
        if ui_core_reading_product_quality.get("role_answer_differentiated") is not True:
            failures.append("ui_role_answer_not_differentiated")
        if ui_core_reading_product_quality.get("llm_context_required_layers_present") is not True:
            failures.append("ui_llm_context_layers_missing")
        if ui_core_reading_product_quality.get("generic_language_hit_count"):
            failures.append(f"ui_generic_language_hits:{ui_core_reading_product_quality.get('generic_language_hit_count')}")
        if ui_core_reading_product_quality.get("internal_leak_count"):
            failures.append(f"ui_internal_leak_hits:{ui_core_reading_product_quality.get('internal_leak_count')}")
    return SyntheticValidationResult(
        case_id=case.case_id,
        passed=not failures,
        failures=failures,
        observed={
            "domains": sorted(domains),
            "anchor_ids": sorted(anchor_ids),
            "recommended_topics": sorted({
                str(row.get("topic")) for row in runtime.question_plan.recommended_questions
            }),
            "top_question_id": str(recommendations[0].get("question_id")) if recommendations else "",
            "top_topic": str(recommendations[0].get("topic")) if recommendations else "",
            "policy_weights_by_topic": {
                str(row.get("topic")): float(row.get("policy_weight", 1.0))
                for row in recommendations
            },
            "rule_confidence_by_kind": {
                row.kind: row.confidence for row in runtime.feature_evidence if row.domain == "rule"
            },
            "rule_weakens_by_kind": {
                row.kind: row.weakens for row in runtime.feature_evidence if row.domain == "rule"
            },
            "rule_states_by_kind": {
                row.kind: [
                    support.removeprefix("rule_decision_state:")
                    for support in row.supports
                    if support.startswith("rule_decision_state:")
                ]
                for row in runtime.feature_evidence
                if row.domain == "rule"
            },
            "hidden_factor_probe_count": len(runtime.question_plan.hidden_factor_probes),
            "knowledge_rule_portrait_signal_types": sorted({
                str(row.get("signal_type")) for row in runtime.question_plan.knowledge_rule_portrait_signals
            }),
            "structure_path_scores": runtime.structure_state.path_scores,
            "mechanism_ids": sorted({
                str(node.get("node_id"))
                for node in runtime.structure_state.graph_nodes
                if node.get("kind") == "mechanism_path"
            }),
            "supporting_mainlines": runtime.mainline_state.supporting_mainlines,
            "mainline_quality_gate": runtime.mainline_state.quality_gate,
            "question_dialogue_graph": question_graph,
            "central_brain_trace": central_brain_trace,
            "central_brain_synthetic_summary": _central_brain_synthetic_summary(
                central_brain_trace=central_brain_trace,
                guest_diagnostics=guest_diagnostics if isinstance(guest_diagnostics, dict) else {},
                practitioner_diagnostics=practitioner_diagnostics if isinstance(practitioner_diagnostics, dict) else {},
                admin_diagnostics=admin_presentation.get("diagnostics", {}) if isinstance(admin_presentation.get("diagnostics", {}), dict) else {},
                expression_quality=expression_quality,
            ),
            "adaptive_question_diagnostics": adaptive_question_diagnostics,
            "central_brain_training_signal_domains": [
                str(row.get("target_signal_domain"))
                for row in central_brain_trace.get("training_signal_routes", [])
                if isinstance(central_brain_trace, dict) and isinstance(row, dict)
            ] if isinstance(central_brain_trace, dict) else [],
            "case_domain": case.domain,
            "expression_quality": expression_quality if case.domain != "core_calculation" else {},
            "llm_output_contract_quality": llm_contract_quality,
            "llm_answer_draft_call": runtime.question_plan.policy_effect.get("llm_answer_draft_call", {}),
            "bazi_llm_output_acceptance_quality": bazi_llm_acceptance_quality,
            "ui_core_reading_product_quality": ui_core_reading_product_quality,
            "real_bazi_diagnosis_quality": real_bazi_diagnosis_quality,
            "krp_library_unit_ids": [
                str(row.get("unit_id")) for row in krp_units if isinstance(row, dict)
            ],
            "krp_library_summary": krp_summary,
            "m3_completion_summary": m3_completion_summary,
            "core_macro_pack_summary": macro_summary,
            "macro_dimension_signal_domains": [
                str(row.get("domain")) for row in macro_signals if isinstance(row, dict)
            ],
            "macro_portrait_domains": [
                str(row.get("domain")) for row in portrait_projections if isinstance(row, dict)
            ],
            "macro_portrait_view_domains": [
                str(row.get("domain")) for row in user_portrait_views if isinstance(row, dict)
            ],
            "macro_portrait_view_summary": runtime.question_plan.policy_effect.get("macro_portrait_view_summary", {}),
            "macro_portrait_role_contrast": {
                "guest": summarize_macro_portrait_projection_views(guest_portrait_views),
                "admin": summarize_macro_portrait_projection_views(admin_portrait_views),
            },
            "rendered_question_label_summary": rendered_label_summary,
            "rendered_question_labels": [
                {
                    "question_id": str(row.get("question_id")),
                    "label": str(row.get("label")),
                    "label_source": str(row.get("label_source")),
                    "label_boundary": str(row.get("label_boundary")),
                    "question_value": str(row.get("question_value")),
                    "expected_information_gain": row.get("expected_information_gain", {}),
                }
                for row in rendered_questions
                if isinstance(row, dict)
            ],
            "customer_reading_surface": reading_surface,
            "api_projection_contract": projection_contract,
            "admin_api_projection_contract": admin_projection_contract,
            "core_bazi_reading": core_bazi_reading,
            "m1_m2_base_fact_contract": _m1_m2_base_fact_contract_observation(case, core_bazi_reading),
            "interaction_state": interaction_state,
            "interaction_brain_result": runtime.question_plan.policy_effect.get("interaction_brain_result", {}),
            "high_value_question_quality": _high_value_question_observation(
                rendered_questions,
                runtime.question_plan.recommended_questions,
            ),
            "role_locale_client_projection_matrix": projection_matrix,
            "hidden_factor_state": hidden_factor_state,
            "question_outcomes": runtime.question_plan.session_state.get("question_outcomes", []),
            "chart_build": chart_build or runtime.chart_context.input_pillars.get("chart_build_source", {}),
            "birth_chart_conversion_boundary": _birth_chart_conversion_boundary_observation(
                chart_build or {
                    "status": runtime.chart_context.input_pillars.get("chart_build_source", {}).get("status"),
                    "chart_build_source": runtime.chart_context.input_pillars.get("chart_build_source", {}),
                    "conversion_trace": runtime.chart_context.input_pillars.get("conversion_trace", {}),
                }
            ),
            "luck_cycle_context": runtime.chart_context.time_layers.get("luck_cycle_context", {}),
            "flow_context": runtime.chart_context.time_layers.get("flow_context", {}),
            "six_pillar_context": runtime.chart_context.time_layers.get("six_pillar_context", {}),
            "model_signal_summary": model_signal_summary,
            "ten_god_energy_calibration": _ten_god_energy_calibration_observation(case, model_signal_summary),
            "m4_ten_god_real_case_replay": _m4_ten_god_real_case_replay_observation(case, model_signal_summary),
            "ranked_decisions": ranked_decisions,
            "practical_reading_context": practical_reading,
            "agent_question_flow": agent_question_flow,
            "real_case_fixture": real_case_fixture,
            "production_replay_metadata": build_production_replay_metadata(
                real_case_fixture,
                api_projection_contract=projection_contract,
            ),
        },
    )


def _real_bazi_diagnosis_quality(
    case: SyntheticBaziCase,
    diagnosis: object,
    *,
    reading_surface: dict[str, Any],
    admin_presentation: dict[str, Any],
) -> dict[str, Any]:
    if case.domain not in {"real_bazi_diagnosis", "synthetic_canonical_bazi_calibration"}:
        return {}
    payload = diagnosis if isinstance(diagnosis, dict) else {}
    claims = [row for row in payload.get("claims", []) if isinstance(row, dict)]
    paths = [row for row in payload.get("paths", []) if isinstance(row, dict)]
    portraits = [row for row in payload.get("portraits", []) if isinstance(row, dict)]
    rules = [row for row in payload.get("matched_rules", []) if isinstance(row, dict)]
    public_projection = payload.get("public_projection", {})
    public_projection = public_projection if isinstance(public_projection, dict) else {}
    summaries = payload.get("summaries", {})
    summaries = summaries if isinstance(summaries, dict) else {}
    domain_summaries = public_projection.get("domain_summaries", {})
    domain_summaries = domain_summaries if isinstance(domain_summaries, dict) else {}
    domain_claims = sorted({
        str(row.get("domain"))
        for row in claims
        if row.get("domain")
    })
    traceable_claims = [
        row for row in claims
        if row.get("evidence_ids") or row.get("rule_ids") or row.get("path_ids") or row.get("portrait_ids")
    ]
    generic_tokens = (
        "Current chart",
        "supports strength and pattern candidate review",
        "可以进入具体问题",
        "套路",
        "泛泛",
        "general",
        "fallback",
    )
    claim_texts = [str(row.get("claim_text") or "") for row in claims]
    summary_texts = [str(text) for text in domain_summaries.values()]
    generic_hit_count = sum(
        1 for text in claim_texts + summary_texts
        if any(token in text for token in generic_tokens)
    )
    text_count = len(claim_texts) + len(summary_texts)
    surface_text = str(reading_surface)
    storage_record = diagnosis_storage_record(payload) if payload.get("reading_id") else {}
    internal_tokens = (
        "policy_effect",
        "matched_rules",
        "rule_match_id",
        "raw_score",
        "feature_evidence",
        "storage_policy",
    )
    storage_record = storage_record if isinstance(storage_record, dict) else {}
    admin_diagnostics = admin_presentation.get("diagnostics", {})
    admin_diagnostics = admin_diagnostics if isinstance(admin_diagnostics, dict) else {}
    graph_summary = summaries.get("graph", {})
    graph_summary = graph_summary if isinstance(graph_summary, dict) else {}
    claim_summary = summaries.get("claims", {})
    claim_summary = claim_summary if isinstance(claim_summary, dict) else {}
    return {
        "version": "v30.real_bazi_diagnosis.synthetic_quality.v1",
        "case_id": case.case_id,
        "status": str(payload.get("status") or ""),
        "rule_match_count": len(rules),
        "path_count": len(paths),
        "portrait_count": len(portraits),
        "claim_count": len(claims),
        "graph_node_count": int(graph_summary.get("node_count", 0) or 0),
        "graph_edge_count": int(graph_summary.get("edge_count", 0) or 0),
        "top_claim_count": int(claim_summary.get("top_claim_count", 0) or 0),
        "domain_claims": domain_claims,
        "domain_summary_domains": sorted(domain_summaries),
        "traceable_claim_count": len(traceable_claims),
        "untraceable_claim_count": len(claims) - len(traceable_claims),
        "llm_generated_claim_count": sum(1 for row in claims if row.get("llm_generated")),
        "chart_fact_mutation_claim_count": sum(1 for row in claims if row.get("chart_fact_mutation_allowed")),
        "fixed_event_prediction_claim_count": sum(1 for row in claims if row.get("fixed_event_prediction")),
        "generic_language_hit_count": generic_hit_count,
        "generic_language_rate": round(generic_hit_count / text_count, 3) if text_count else 0.0,
        "customer_has_diagnosis_overview": bool(reading_surface.get("diagnosis_overview")),
        "customer_domain_cards_with_diagnosis": sum(
            1 for row in reading_surface.get("domain_cards", [])
            if isinstance(row, dict) and row.get("diagnosis_summary")
        ) if isinstance(reading_surface.get("domain_cards"), list) else 0,
        "customer_internal_leak_count": sum(1 for token in internal_tokens if token in surface_text),
        "admin_diagnostics_visible": "real_bazi_diagnosis" in admin_diagnostics,
        "storage_record_version": str(storage_record.get("version") or ""),
        "storage_claim_count": int(storage_record.get("claim_count", 0) or 0),
        "storage_rule_match_count": int(storage_record.get("rule_match_count", 0) or 0),
        "storage_authoritative_facts_stored_here": bool(storage_record.get("authoritative_facts_stored_here")),
        "readiness_518k_sample": {
            "version": "v30.real_bazi_diagnosis.518k_readiness.v1",
            "sample_limit_default": 8,
            "full_518k_explicit_only": True,
            "checks": [
                "rule_match_count",
                "path_count",
                "portrait_count",
                "claim_count",
                "generic_language_rate",
                "traceable_claim_count",
            ],
            "ready_for_sample_replay": len(claims) >= case.expected_min_rbd_claims
            and len(paths) >= case.expected_min_rbd_paths
            and len(rules) >= case.expected_min_rbd_rule_matches
            and not (len(claims) - len(traceable_claims)),
        },
        "boundary": "real_bazi_diagnosis_synthetic_quality_validates_diagnosis_engine_not_destiny_truth",
    }


def _ui_core_reading_product_quality(
    case: SyntheticBaziCase,
    *,
    user_presentation: dict[str, Any],
    practitioner_presentation: dict[str, Any],
) -> dict[str, Any]:
    if case.domain != "ui_core_reading_product":
        return {}
    reading_surface = user_presentation.get("reading_surface", {})
    reading_surface = reading_surface if isinstance(reading_surface, dict) else {}
    practitioner_surface = practitioner_presentation.get("reading_surface", {})
    practitioner_surface = practitioner_surface if isinstance(practitioner_surface, dict) else {}
    basic_assertions = [
        row for row in reading_surface.get("basic_assertions", [])
        if isinstance(row, dict)
    ] if isinstance(reading_surface.get("basic_assertions"), list) else []
    features = [
        row for row in reading_surface.get("bazi_features", [])
        if isinstance(row, dict)
    ] if isinstance(reading_surface.get("bazi_features"), list) else []
    portraits = [
        row for row in reading_surface.get("bazi_portraits", [])
        if isinstance(row, dict)
    ] if isinstance(reading_surface.get("bazi_portraits"), list) else []
    paths = [
        row for row in reading_surface.get("bazi_paths", [])
        if isinstance(row, dict)
    ] if isinstance(reading_surface.get("bazi_paths"), list) else []
    domain_cards = [
        row for row in reading_surface.get("domain_cards", [])
        if isinstance(row, dict)
    ] if isinstance(reading_surface.get("domain_cards"), list) else []
    user_answer = user_presentation.get("answer_panel", {})
    user_answer = user_answer if isinstance(user_answer, dict) else {}
    practitioner_answer = practitioner_presentation.get("answer_panel", {})
    practitioner_answer = practitioner_answer if isinstance(practitioner_answer, dict) else {}
    llm_metadata = user_answer.get("llm_metadata", {})
    llm_metadata = llm_metadata if isinstance(llm_metadata, dict) else {}
    context_summary = llm_metadata.get("context_pack_summary", {})
    context_summary = context_summary if isinstance(context_summary, dict) else {}
    layers = {
        str(row)
        for row in context_summary.get("layers", [])
    } if isinstance(context_summary.get("layers"), list) else set()
    required_layers = {
        "basic_assertions",
        "bazi_features",
        "bazi_paths",
        "bazi_portraits",
        "domain_card",
        "role_contract",
        "time_context",
    }
    visible_text_parts: list[str] = [
        str(user_answer.get("text") or ""),
        str(user_answer.get("original_text") or ""),
        str(reading_surface.get("summary") or ""),
        str(reading_surface.get("diagnosis_overview") or ""),
    ]
    for row in basic_assertions:
        visible_text_parts.extend([
            str(row.get("title") or ""),
            str(row.get("text") or ""),
        ])
    for row in domain_cards:
        visible_text_parts.extend([
            str(row.get("title") or ""),
            str(row.get("summary") or ""),
            str(row.get("diagnosis_summary") or ""),
            str(row.get("path_summary") or ""),
        ])
        visible_text_parts.extend(str(item) for item in row.get("path_assertions", []) if isinstance(row.get("path_assertions"), list))
    for row in features:
        visible_text_parts.extend([
            str(row.get("title") or ""),
            str(row.get("summary") or ""),
            str(row.get("evidence_summary") or ""),
        ])
    for row in portraits:
        visible_text_parts.extend([
            str(row.get("title") or ""),
            str(row.get("summary") or ""),
            str(row.get("expression") or ""),
        ])
    for row in paths:
        visible_text_parts.extend([
            str(row.get("title") or ""),
            str(row.get("summary") or ""),
            str(row.get("action_boundary") or ""),
        ])
    visible_text = "\n".join(part for part in visible_text_parts if part)
    generic_tokens = (
        "Current chart",
        "supports strength and pattern candidate review",
        "可以进入具体问题",
        "仍按候选路径表达",
        "不做确定断语",
        "fallback",
    )
    internal_tokens = (
        "policy_effect",
        "raw_score",
        "feature_id",
        "portrait_id",
        "v30.krp.",
        "matched_rules",
        "rule_match_id",
    )
    domain_card_path_summary_count = sum(1 for row in domain_cards if row.get("path_summary"))
    domain_card_path_assertion_count = sum(
        len(row.get("path_assertions", []))
        for row in domain_cards
        if isinstance(row.get("path_assertions"), list)
    )
    role_adaptation = user_answer.get("role_adaptation", {})
    role_adaptation = role_adaptation if isinstance(role_adaptation, dict) else {}
    product_ready = (
        len(basic_assertions) >= 5
        and len(features) >= 4
        and len(portraits) >= 4
        and len(paths) >= 3
        and domain_card_path_summary_count >= 3
        and domain_card_path_assertion_count >= 3
        and str(user_answer.get("text") or "") != str(practitioner_answer.get("text") or "")
        and required_layers <= layers
        and not any(token in visible_text for token in generic_tokens)
        and not any(token in visible_text for token in internal_tokens)
    )
    return {
        "version": "v30.ui_core_reading_product.synthetic_quality.v1",
        "case_id": case.case_id,
        "product_ready": product_ready,
        "basic_assertion_count": len(basic_assertions),
        "feature_count": len(features),
        "portrait_count": len(portraits),
        "path_count": len(paths),
        "domain_card_count": len(domain_cards),
        "domain_card_path_summary_count": domain_card_path_summary_count,
        "domain_card_path_assertion_count": domain_card_path_assertion_count,
        "role_answer_differentiated": str(user_answer.get("text") or "") != str(practitioner_answer.get("text") or ""),
        "role_adaptation": role_adaptation,
        "llm_context_layers": sorted(layers),
        "llm_context_required_layers_present": required_layers <= layers,
        "missing_llm_context_layers": sorted(required_layers - layers),
        "generic_language_hit_count": sum(1 for token in generic_tokens if token in visible_text),
        "internal_leak_count": sum(1 for token in internal_tokens if token in visible_text),
        "boundary": "ui_core_reading_product_synthetic_validates_product_output_not_real_life_truth",
    }


def _high_value_question_observation(
    questions: object,
    source_questions: object | None = None,
) -> dict[str, object]:
    rows = [row for row in questions if isinstance(row, dict)] if isinstance(questions, list) else []
    source_rows = [
        row for row in source_questions
        if isinstance(row, dict)
    ] if isinstance(source_questions, list) else rows
    gains = [
        float(row.get("expected_information_gain", {}).get("score", 0.0))
        for row in rows
        if isinstance(row.get("expected_information_gain"), dict)
    ]
    primary_gains = sorted({
        str(row.get("expected_information_gain", {}).get("primary_gain"))
        for row in rows
        if isinstance(row.get("expected_information_gain"), dict)
        and row.get("expected_information_gain", {}).get("primary_gain")
    })
    model_signal_focus_reasons = [
        str(reason)
        for row in source_rows
        for reason in (row.get("reasons", []) if isinstance(row.get("reasons"), list) else [])
        if str(reason).startswith("model_signal_question_focus:")
    ]
    model_signal_focus_pairs = sorted({
        reason.split(":", 1)[1]
        for reason in model_signal_focus_reasons
        if ":" in reason
    })
    model_signal_focus_topics = sorted({
        str(row.get("topic"))
        for row in source_rows
        if any(
            str(reason).startswith("model_signal_question_focus:")
            for reason in (row.get("reasons", []) if isinstance(row.get("reasons"), list) else [])
        )
        and row.get("topic")
    })
    top_source = source_rows[0] if source_rows else {}
    top_source_reasons = top_source.get("reasons", []) if isinstance(top_source, dict) else []
    top_source_reasons = top_source_reasons if isinstance(top_source_reasons, list) else []
    return {
        "version": "v30.high_value_question_observation.v1",
        "question_count": len(rows),
        "average_expected_information_gain": round(sum(gains) / len(gains), 3) if gains else 0.0,
        "primary_gains": primary_gains,
        "questions_with_quality_contract": sum(
            1 for row in rows if isinstance(row.get("quality_contract"), dict)
        ),
        "model_signal_focus_reason_count": len(model_signal_focus_reasons),
        "model_signal_focus_pairs": model_signal_focus_pairs,
        "model_signal_focus_topics": model_signal_focus_topics,
        "top_question_id": str(top_source.get("question_id") or "") if isinstance(top_source, dict) else "",
        "top_question_topic": str(top_source.get("topic") or "") if isinstance(top_source, dict) else "",
        "top_question_model_signal_focused": any(
            str(reason).startswith("model_signal_question_focus:")
            for reason in top_source_reasons
        ),
        "boundary": "high_value_question_quality_trains_question_policy_not_chart_facts",
    }


def _runtime_from_case(
    case: SyntheticBaziCase,
    *,
    policy_payloads: dict[str, dict[str, object]],
    active_policy_versions: dict[str, str],
):
    birth_payload = case.chart_input.get("birth_input")
    if isinstance(birth_payload, dict):
        build = build_chart_context_from_birth_input(
            reading_id=case.case_id,
            birth_input=BirthInput.model_validate(birth_payload),
        )
        chart_build = build.four_pillar_result.model_dump(mode="json")
        if build.chart_context is None:
            return None, chart_build
        return create_runtime_from_context(
            build.chart_context,
            policy_payload_overrides=policy_payloads,
            active_policy_version_overrides=active_policy_versions,
            trace_suffix="synthetic-birth-input",
        ), chart_build
    return create_smoke_runtime(
        reading_id=case.case_id,
        day_master=case.chart_input.get("day_master", "甲"),
        luck_pillar=case.chart_input.get("luck_pillar", ""),
        flow_year_pillar=case.chart_input.get("flow_year_pillar", ""),
        hidden_factor_user_calibrated=case.chart_input.get("hidden_factor_user_calibrated") == "true",
        useful_god_path_resolved=case.chart_input.get("useful_god_path_resolved") == "true",
        branch_single_factor_confirmed=case.chart_input.get("branch_single_factor_confirmed") == "true",
        policy_payload_overrides=policy_payloads,
        active_policy_version_overrides=active_policy_versions,
    ), None


def _birth_chart_conversion_boundary_observation(chart_build: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(chart_build, dict):
        return {}
    trace = chart_build.get("conversion_trace", {})
    if not isinstance(trace, dict):
        trace = {}
    source = chart_build.get("chart_build_source", {})
    if not isinstance(source, dict):
        source = {}
    return {
        "status": str(chart_build.get("status") or ""),
        "source_type": str(source.get("source_type") or ""),
        "has_pillars": bool(chart_build.get("pillars")),
        "missing_pillars": [str(row) for row in chart_build.get("missing_pillars", [])] if isinstance(chart_build.get("missing_pillars"), list) else [],
        "boundary_flags": [str(row) for row in trace.get("boundary_flags", [])] if isinstance(trace.get("boundary_flags"), list) else [],
        "missing_requirements": [str(row) for row in trace.get("missing_requirements", [])] if isinstance(trace.get("missing_requirements"), list) else [],
        "calendar_type": str(trace.get("calendar_type") or ""),
        "timezone": str(trace.get("timezone") or ""),
    }


def _validate_central_brain_synthetic_case(
    *,
    case: SyntheticBaziCase,
    runtime,
    central_brain_trace: dict[str, Any],
    expression_quality: dict[str, Any],
    guest_diagnostics: dict[str, Any],
    practitioner_diagnostics: dict[str, Any],
    admin_diagnostics: dict[str, Any],
    failures: list[str],
) -> None:
    if not isinstance(central_brain_trace, dict) or central_brain_trace.get("version") != "v30.central_brain.v1":
        failures.append("central_brain_trace_missing")
        return
    brain_state = central_brain_trace.get("brain_state", {})
    session_memory = central_brain_trace.get("session_memory", {})
    role_state = central_brain_trace.get("role_state", {})
    runtime_plan = central_brain_trace.get("runtime_plan", {})
    question_strategy = central_brain_trace.get("question_strategy", {})
    expression = central_brain_trace.get("expression_orchestration", {})
    feedback = central_brain_trace.get("feedback_strategy", {})
    routes = central_brain_trace.get("training_signal_routes", [])
    boundaries = set(central_brain_trace.get("boundaries", []))
    route_domains = {
        str(row.get("target_signal_domain"))
        for row in routes
        if isinstance(row, dict) and row.get("target_signal_domain")
    }
    if not isinstance(brain_state, dict) or brain_state.get("reading_id") != runtime.reading_id:
        failures.append("central_brain_state_reading_id_mismatch")
    if not isinstance(session_memory, dict) or session_memory.get("memory_policy") != "runtime_memory_is_traceable_and_feedback_conditioned":
        failures.append("central_brain_session_memory_policy_missing")
    feedback_slots = set(session_memory.get("feedback_slots", [])) if isinstance(session_memory, dict) and isinstance(session_memory.get("feedback_slots"), list) else set()
    required_feedback_slots = {"question_answer_feedback", "expression_quality_feedback"}
    hidden_factor_focus = str(brain_state.get("hidden_factor_focus") or "")
    if hidden_factor_focus != "amplifier_candidate":
        required_feedback_slots.add("hidden_factor_boundary_feedback")
    if not required_feedback_slots <= {str(row) for row in feedback_slots}:
        failures.append("central_brain_feedback_slots_incomplete")
    if not isinstance(role_state, dict) or role_state.get("visibility") not in {"user_visible", "diagnostic_visible"}:
        failures.append("central_brain_role_state_visibility_missing")
    if not isinstance(runtime_plan, dict) or "record_feedback_for_training" not in runtime_plan.get("next_actions", []):
        failures.append("central_brain_runtime_plan_training_action_missing")
    if not isinstance(question_strategy, dict) or not question_strategy.get("selected_question_id"):
        failures.append("central_brain_question_strategy_missing")
    if not isinstance(expression, dict) or expression.get("surface_status") != "clean":
        failures.append("central_brain_expression_surface_not_clean")
    if expression_quality.get("forbidden_token_hits"):
        failures.append("central_brain_expression_forbidden_tokens")
    required_route_domains = {"question_intelligence", "expression"}
    if hidden_factor_focus != "amplifier_candidate":
        required_route_domains.add("hidden_factor")
    if not required_route_domains <= route_domains:
        failures.append("central_brain_training_routes_incomplete")
    if not isinstance(feedback, dict) or feedback.get("no_review_gate") is not True:
        failures.append("central_brain_feedback_no_review_gate_missing")
    if "central_brain_coordinates_only" not in boundaries:
        failures.append("central_brain_coordinates_only_boundary_missing")
    if "central_brain_does_not_write_database_or_redis_directly" not in boundaries:
        failures.append("central_brain_no_db_redis_write_boundary_missing")
    if "central_brain_does_not_mutate_chart_facts" not in boundaries:
        failures.append("central_brain_no_chart_fact_mutation_boundary_missing")
    if "central_brain" in guest_diagnostics:
        failures.append("central_brain_guest_diagnostics_visible")
    if "central_brain" not in practitioner_diagnostics:
        failures.append("central_brain_practitioner_diagnostics_missing")
    if "central_brain" not in admin_diagnostics:
        failures.append("central_brain_admin_diagnostics_missing")
    target_role = str(case.chart_input.get("central_brain_role") or "")
    if target_role == "admin":
        if brain_state.get("hidden_factor_focus") != "amplifier_candidate":
            failures.append("central_brain_admin_hidden_factor_focus_missing")
        if question_strategy.get("hidden_factor_mode") != "use_as_feedback_conditioned_amplifier":
            failures.append("central_brain_admin_hidden_factor_mode_missing")
    if target_role == "user" and case.question_outcome_answer:
        answered_ids = runtime.question_plan.policy_effect.get("interaction_state", {}).get("answered_question_ids", [])
        if case.question_outcome_answer.get("question_id") not in answered_ids:
            failures.append("central_brain_user_answered_question_not_in_session")
    if target_role == "practitioner":
        brain_diag = practitioner_diagnostics.get("central_brain", {})
        if not isinstance(brain_diag, dict) or brain_diag.get("version") != "v30.central_brain.v1":
            failures.append("central_brain_practitioner_diag_version_missing")
    if target_role == "guest":
        if guest_diagnostics:
            failures.append("central_brain_guest_projection_not_sanitized")
    if "missing_time_boundary" in case.case_id:
        unknown_context = set(brain_state.get("unknown_context", [])) if isinstance(brain_state, dict) and isinstance(brain_state.get("unknown_context"), list) else set()
        if "time_layer_boundary" not in {str(row) for row in unknown_context}:
            failures.append("central_brain_missing_time_unknown_context_missing")


def _central_brain_synthetic_summary(
    *,
    central_brain_trace: dict[str, Any],
    guest_diagnostics: dict[str, Any],
    practitioner_diagnostics: dict[str, Any],
    admin_diagnostics: dict[str, Any],
    expression_quality: dict[str, Any],
) -> dict[str, Any]:
    trace = central_brain_trace if isinstance(central_brain_trace, dict) else {}
    routes = trace.get("training_signal_routes", [])
    brain_state = trace.get("brain_state", {})
    role_state = trace.get("role_state", {})
    expression = trace.get("expression_orchestration", {})
    return {
        "version": trace.get("version", ""),
        "session_phase": brain_state.get("session_phase", "") if isinstance(brain_state, dict) else "",
        "hidden_factor_focus": brain_state.get("hidden_factor_focus", "") if isinstance(brain_state, dict) else "",
        "role_visibility": role_state.get("visibility", "") if isinstance(role_state, dict) else "",
        "expression_surface": expression.get("surface_status", "") if isinstance(expression, dict) else "",
        "training_route_domains": sorted({
            str(row.get("target_signal_domain"))
            for row in routes
            if isinstance(row, dict) and row.get("target_signal_domain")
        }),
        "guest_diagnostics_visible": "central_brain" in guest_diagnostics,
        "practitioner_diagnostics_visible": "central_brain" in practitioner_diagnostics,
        "admin_diagnostics_visible": "central_brain" in admin_diagnostics,
        "expression_forbidden_token_count": len(expression_quality.get("forbidden_token_hits", [])),
        "boundary_count": len(trace.get("boundaries", [])) if isinstance(trace.get("boundaries", []), list) else 0,
    }


def _m1_m2_base_fact_contract_observation(
    case: SyntheticBaziCase,
    core_bazi_reading: dict[str, Any],
) -> dict[str, Any]:
    if case.domain != "m1_m2_bazi_calculation":
        return {}
    if not isinstance(core_bazi_reading, dict):
        return {}
    summary = core_bazi_reading.get("base_fact_summary", {})
    summary = summary if isinstance(summary, dict) else {}
    explanations = core_bazi_reading.get("base_fact_explanations", {})
    explanations = explanations if isinstance(explanations, dict) else {}
    completion = core_bazi_reading.get("m1_m2_completion_summary", {})
    completion = completion if isinstance(completion, dict) else {}
    integrity = core_bazi_reading.get("fact_integrity", {})
    integrity = integrity if isinstance(integrity, dict) else {}
    birth_input = case.chart_input.get("birth_input", {})
    birth_input = birth_input if isinstance(birth_input, dict) else {}
    return {
        "status": str(summary.get("status") or ""),
        "calendar_type": str(birth_input.get("calendar_type") or "solar"),
        "gender_status": "known" if birth_input.get("gender") else "unknown",
        "use_true_solar_time": bool(birth_input.get("use_true_solar_time")),
        "lunar_is_leap_month": bool(birth_input.get("lunar_is_leap_month")),
        "deterministic": bool(integrity.get("deterministic")),
        "non_deterministic_source_count": sum(
            1 for key in ("llm_generated", "training_generated", "feedback_generated")
            if integrity.get(key)
        ),
        "pillar_count": int(summary.get("pillar_count", 0) or 0),
        "visible_ten_god_count": int(summary.get("visible_ten_god_count", 0) or 0),
        "hidden_ten_god_count": int(summary.get("hidden_ten_god_count", 0) or 0),
        "relation_count": int(summary.get("relation_count", 0) or 0),
        "summary_keys": sorted(summary),
        "relation_families": [
            str(row) for row in summary.get("relation_families", [])
        ] if isinstance(summary.get("relation_families"), list) else [],
        "root_fact_summary": summary.get("root_fact_summary", {}) if isinstance(summary.get("root_fact_summary"), dict) else {},
        "explanation_boundary": str(explanations.get("boundary") or ""),
        "completion_summary_version": str(completion.get("version") or ""),
        "completion_status": str(completion.get("status") or ""),
        "completion_required_key_coverage": float(completion.get("required_key_coverage", 0.0) or 0.0),
        "completion_explanation_coverage": float(completion.get("explanation_coverage", 0.0) or 0.0),
        "completion_downstream_consumption_ready": bool(completion.get("downstream_consumption_ready")),
        "completion_m5_uses_root_fact_summary_count": int(completion.get("m5_uses_root_fact_summary_count", 0) or 0),
        "completion_m6_uses_m1_m2_fact_count": int(completion.get("m6_uses_m1_m2_fact_count", 0) or 0),
        "completion_chart_fact_mutation_allowed": bool(completion.get("chart_fact_mutation_allowed")),
        "completion_boundary": str(completion.get("boundary") or ""),
        "guardrails": [
            str(row) for row in summary.get("guardrails", [])
        ] if isinstance(summary.get("guardrails"), list) else [],
        "boundary": "m1_m2_base_fact_contract_validates_deterministic_fact_layer_not_judgment",
    }


def _ten_god_energy_calibration_observation(
    case: SyntheticBaziCase,
    model_signal_summary: dict[str, Any],
) -> dict[str, Any]:
    if case.domain != "ten_god_energy_calibration":
        return {}
    if not isinstance(model_signal_summary, dict):
        model_signal_summary = {}
    bands = model_signal_summary.get("energy_bands", [])
    bands = bands if isinstance(bands, list) else []
    calibration_profile = model_signal_summary.get("calibration_profile", {})
    calibration_profile = calibration_profile if isinstance(calibration_profile, dict) else {}
    ranked_adjustments = calibration_profile.get("ranked_decision_adjustments", {})
    ranked_adjustments = ranked_adjustments if isinstance(ranked_adjustments, dict) else {}
    families = sorted({
        str(row.get("family"))
        for row in bands
        if isinstance(row, dict) and row.get("family")
    })
    energy_band_counts: dict[str, int] = {}
    stability_band_counts: dict[str, int] = {}
    volatility_band_counts: dict[str, int] = {}
    for row in bands:
        if not isinstance(row, dict):
            continue
        for target, key in (
            (energy_band_counts, "energy_band"),
            (stability_band_counts, "stability_band"),
            (volatility_band_counts, "volatility_band"),
        ):
            band = str(row.get(key) or "")
            if band:
                target[band] = target.get(band, 0) + 1
    return {
        "case_id": case.case_id,
        "status": str(model_signal_summary.get("status") or ""),
        "families": families,
        "energy_band_counts": energy_band_counts,
        "stability_band_counts": stability_band_counts,
        "volatility_band_counts": volatility_band_counts,
        "dominant_count": len(model_signal_summary.get("dominant_ten_gods", [])) if isinstance(model_signal_summary.get("dominant_ten_gods", []), list) else 0,
        "volatility_alert_count": len(model_signal_summary.get("volatility_alerts", [])) if isinstance(model_signal_summary.get("volatility_alerts", []), list) else 0,
        "stability_alert_count": len(model_signal_summary.get("stability_alerts", [])) if isinstance(model_signal_summary.get("stability_alerts", []), list) else 0,
        "calibration_flags": calibration_profile.get("calibration_flags", []) if isinstance(calibration_profile.get("calibration_flags", []), list) else [],
        "ranked_adjustment_version": str(ranked_adjustments.get("version") or ""),
        "ranked_adjustment_score_bias_keys": sorted((ranked_adjustments.get("score_bias", {}) or {}).keys())
        if isinstance(ranked_adjustments.get("score_bias"), dict) else [],
        "raw_score_visible": bool(model_signal_summary.get("raw_score_visible")),
        "boundary": "ten_god_energy_calibration_observes_bounded_model_signal_not_chart_fact",
    }


def _m4_ten_god_real_case_replay_observation(
    case: SyntheticBaziCase,
    model_signal_summary: dict[str, Any],
) -> dict[str, Any]:
    if case.domain != "m4_ten_god_real_case_replay":
        return {}
    if not isinstance(model_signal_summary, dict):
        model_signal_summary = {}
    bands = model_signal_summary.get("energy_bands", [])
    bands = bands if isinstance(bands, list) else []
    interface_contract = model_signal_summary.get("interface_contract", {})
    interface_contract = interface_contract if isinstance(interface_contract, dict) else {}
    calibration_profile = model_signal_summary.get("calibration_profile", {})
    calibration_profile = calibration_profile if isinstance(calibration_profile, dict) else {}
    ranked_adjustments = calibration_profile.get("ranked_decision_adjustments", {})
    ranked_adjustments = ranked_adjustments if isinstance(ranked_adjustments, dict) else {}
    forbidden_fields = set(interface_contract.get("forbidden_fields", [])) if isinstance(interface_contract.get("forbidden_fields", []), list) else set()
    leaked_forbidden = sorted({
        str(key)
        for band in bands
        if isinstance(band, dict)
        for key in band
        if str(key) in forbidden_fields
    })
    return {
        "case_id": case.case_id,
        "status": str(model_signal_summary.get("status") or ""),
        "family_coverage": calibration_profile.get("family_coverage", []) if isinstance(calibration_profile.get("family_coverage", []), list) else [],
        "family_coverage_count": int(calibration_profile.get("family_coverage_count", 0) or 0),
        "calibration_flags": calibration_profile.get("calibration_flags", []) if isinstance(calibration_profile.get("calibration_flags", []), list) else [],
        "ranked_adjustment_version": str(ranked_adjustments.get("version") or ""),
        "ranked_adjustment_score_bias_keys": sorted((ranked_adjustments.get("score_bias", {}) or {}).keys())
        if isinstance(ranked_adjustments.get("score_bias"), dict) else [],
        "interface_consumers": interface_contract.get("consumers", []) if isinstance(interface_contract.get("consumers", []), list) else [],
        "forbidden_field_leaks": leaked_forbidden,
        "raw_score_visible": bool(model_signal_summary.get("raw_score_visible")),
        "ranked_decision_domain_count": len(model_signal_summary.get("ranked_decision_inputs", {})) if isinstance(model_signal_summary.get("ranked_decision_inputs", {}), dict) else 0,
        "boundary": "m4_ten_god_real_case_replay_validates_interface_and_real_case_distribution_not_threshold_promotion",
    }


def _real_case_fixture_observation(
    case: SyntheticBaziCase,
    *,
    chart_build: dict[str, Any] | None,
    runtime: Any | None = None,
    practical_reading: Any | None = None,
    agent_question_flow: Any | None = None,
) -> dict[str, Any]:
    if case.domain != "real_case_validation":
        return {}
    chart_build = chart_build or {}
    birth_input = case.chart_input.get("birth_input", {})
    birth_input = birth_input if isinstance(birth_input, dict) else {}
    trace = chart_build.get("conversion_trace", {})
    trace = trace if isinstance(trace, dict) else {}
    six_context = runtime.chart_context.time_layers.get("six_pillar_context", {}) if runtime is not None else {}
    luck_context = runtime.chart_context.time_layers.get("luck_cycle_context", {}) if runtime is not None else {}
    flow_context = runtime.chart_context.time_layers.get("flow_context", {}) if runtime is not None else {}
    model_signal_summary = (
        runtime.question_plan.policy_effect.get("model_signal_summary", {})
        if runtime is not None else {}
    )
    ranked_decisions = (
        runtime.question_plan.policy_effect.get("ranked_decisions", {})
        if runtime is not None else {}
    )
    projection_matrix = (
        runtime.question_plan.policy_effect.get("role_locale_client_projection_matrix", {})
        if runtime is not None else {}
    )
    if not projection_matrix and runtime is not None:
        projection_matrix = build_role_locale_client_projection_matrix(runtime)
    domain_readings = (
        practical_reading.get("domain_readings", {})
        if isinstance(practical_reading, dict) and isinstance(practical_reading.get("domain_readings", {}), dict)
        else {}
    )
    practical_domain_contracts = {
        domain: {
            "version": str(payload.get("version", "")),
            "calculation_basis_version": str((payload.get("calculation_basis", {}) if isinstance(payload.get("calculation_basis", {}), dict) else {}).get("version", "")),
            "model_signal_context_version": str((payload.get("model_signal_context", {}) if isinstance(payload.get("model_signal_context", {}), dict) else {}).get("version", "")),
            "ranked_decision_link_count": len(payload.get("ranked_decision_links", {})) if isinstance(payload.get("ranked_decision_links", {}), dict) else 0,
            "evidence_id_count": len(payload.get("evidence_ids", [])) if isinstance(payload.get("evidence_ids", []), list) else 0,
            "explanation_unit_count": len(payload.get("explanation_units", [])) if isinstance(payload.get("explanation_units", []), list) else 0,
            "domain_insight_count": len(payload.get("domain_insights", [])) if isinstance(payload.get("domain_insights", []), list) else 0,
            "action_step_count": len(payload.get("action_steps", [])) if isinstance(payload.get("action_steps", []), list) else 0,
            "calibration_prompt_count": len(payload.get("calibration_prompts", [])) if isinstance(payload.get("calibration_prompts", []), list) else 0,
            "module_trace_version": str((payload.get("module_trace", {}) if isinstance(payload.get("module_trace", {}), dict) else {}).get("version", "")),
            "module_trace_uses_m1_m5": (
                (payload.get("module_trace", {}) if isinstance(payload.get("module_trace", {}), dict) else {}).get("uses_m1_m2_facts") is True
                and (payload.get("module_trace", {}) if isinstance(payload.get("module_trace", {}), dict) else {}).get("uses_m3_structure_evidence") is True
                and (payload.get("module_trace", {}) if isinstance(payload.get("module_trace", {}), dict) else {}).get("uses_m4_model_signal") is True
                and (payload.get("module_trace", {}) if isinstance(payload.get("module_trace", {}), dict) else {}).get("uses_m5_ranked_decisions") is True
            ),
            "blocked_claim_count": len(payload.get("blocked_claims", [])) if isinstance(payload.get("blocked_claims", []), list) else 0,
            "raw_score_leak": any(
                raw_key in payload
                for raw_key in ("raw_weight", "raw_score", "energy", "stability", "volatility")
            ),
        }
        for domain, payload in domain_readings.items()
        if isinstance(payload, dict)
    }
    observation = {
        "case_id": case.case_id,
        "case_type": case.case_type,
        "status": str(chart_build.get("status") or ""),
        "source_type": str(
            (chart_build.get("chart_build_source", {}) if isinstance(chart_build.get("chart_build_source", {}), dict) else {}).get("source_type") or ""
        ),
        "calendar_type": str(birth_input.get("calendar_type") or trace.get("calendar_type") or ""),
        "lunar_is_leap_month": bool(birth_input.get("lunar_is_leap_month", False)),
        "use_true_solar_time": bool(birth_input.get("use_true_solar_time", False)),
        "unknown_hour": bool(birth_input.get("unknown_hour", False)),
        "gender_status": "known" if birth_input.get("gender") else "unknown",
        "boundary_flags": [
            str(row) for row in trace.get("boundary_flags", [])
        ] if isinstance(trace.get("boundary_flags"), list) else [],
        "has_pillars": bool(chart_build.get("pillars")),
        "six_pillar_status": str(six_context.get("status") if isinstance(six_context, dict) else ""),
        "luck_cycle_status": str(luck_context.get("status") if isinstance(luck_context, dict) else ""),
        "flow_context_status": str(flow_context.get("status") if isinstance(flow_context, dict) else ""),
        "model_signal_ready": bool(model_signal_summary),
        "ranked_decision_count": len(ranked_decisions) if isinstance(ranked_decisions, dict) else 0,
        "ranked_primary_candidates": {
            domain: str(payload.get("primary_candidate") or "")
            for domain, payload in ranked_decisions.items()
            if isinstance(ranked_decisions, dict) and isinstance(payload, dict)
        } if isinstance(ranked_decisions, dict) else {},
        "ranked_score_key_count": {
            domain: len(payload.get("candidate_scores", {}))
            for domain, payload in ranked_decisions.items()
            if isinstance(ranked_decisions, dict)
            and isinstance(payload, dict)
            and isinstance(payload.get("candidate_scores", {}), dict)
        } if isinstance(ranked_decisions, dict) else {},
        "ranked_candidate_scores": {
            domain: {
                str(candidate_id): float(score)
                for candidate_id, score in payload.get("candidate_scores", {}).items()
                if isinstance(score, (int, float))
            }
            for domain, payload in ranked_decisions.items()
            if isinstance(ranked_decisions, dict)
            and isinstance(payload, dict)
            and isinstance(payload.get("candidate_scores", {}), dict)
        } if isinstance(ranked_decisions, dict) else {},
        "ranked_scoring_basis_signals": {
            domain: {
                "follow_structure_boundary_signal": bool(basis.get("follow_structure_boundary_signal")),
                "special_structure_boundary_signal": bool(basis.get("special_structure_boundary_signal")),
                "regulation_climate_boundary_signal": bool(basis.get("regulation_climate_boundary_signal")),
                "disputed_structure_signal": bool(basis.get("disputed_structure_signal")),
                "non_unique_candidate_signal": bool(basis.get("non_unique_candidate_signal")),
                "close_candidate_count": int(basis.get("close_candidate_count", 0) or 0),
            }
            for domain, payload in ranked_decisions.items()
            if isinstance(ranked_decisions, dict)
            and isinstance(payload, dict)
            and isinstance((basis := payload.get("scoring_basis", {})), dict)
        } if isinstance(ranked_decisions, dict) else {},
        "practical_reading_status": str(practical_reading.get("status") if isinstance(practical_reading, dict) else ""),
        "practical_domain_count": len(domain_readings),
        "practical_domain_contracts": practical_domain_contracts,
        "agent_question_stage": str(agent_question_flow.get("next_stage") if isinstance(agent_question_flow, dict) else ""),
        "projection_matrix_ready": bool(projection_matrix),
        "boundary": "canonical_real_case_fixture_validates_runtime_pipeline_not_chart_fact_source",
    }
    observation["calibration_drift_summary"] = _real_case_calibration_drift_summary(case, observation)
    observation["calibration_status"] = observation["calibration_drift_summary"]["calibration_status"]
    observation["calibration_drift_flags"] = observation["calibration_drift_summary"]["drift_flags"]
    observation["module_adjustment_targets"] = observation["calibration_drift_summary"]["module_adjustment_targets"]
    return observation


def _real_case_calibration_drift_summary(
    case: SyntheticBaziCase,
    observation: dict[str, Any],
) -> dict[str, Any]:
    expected_chart_status = case.expected_chart_build_status
    expected_six_status = case.expected_six_pillar_status
    expected_practical_status = case.expected_practical_reading_status
    chart_status = str(observation.get("status") or "")
    has_pillars = bool(observation.get("has_pillars"))
    ready_chart = chart_status == "ready" and has_pillars
    drift_flags: list[str] = []
    module_adjustment_targets: list[str] = []

    def add_flag(flag: str, module_id: str) -> None:
        if flag not in drift_flags:
            drift_flags.append(flag)
        if module_id not in module_adjustment_targets:
            module_adjustment_targets.append(module_id)

    if expected_chart_status and chart_status != expected_chart_status:
        add_flag("chart_build_status_mismatch", "M1_birth_input_chart_facts")
    if chart_status != "ready" and has_pillars:
        add_flag("blocked_or_pending_case_has_fake_pillars", "M1_birth_input_chart_facts")
    if expected_six_status and str(observation.get("six_pillar_status") or "") != expected_six_status:
        add_flag("six_pillar_status_mismatch", "M2_luck_flow_timing_context")
    if expected_practical_status and str(observation.get("practical_reading_status") or "") != expected_practical_status:
        add_flag("practical_reading_status_mismatch", "M6_practical_reading_output")
    if ready_chart and not bool(observation.get("model_signal_ready")):
        add_flag("model_signal_missing_for_ready_chart", "M4_ten_god_energy_model")
    if ready_chart and int(observation.get("ranked_decision_count", 0) or 0) < 3:
        add_flag("ranked_decisions_incomplete_for_ready_chart", "M5_ranked_decisions")
    if ready_chart and int(observation.get("practical_domain_count", 0) or 0) < 5:
        add_flag("practical_domains_incomplete_for_ready_chart", "M6_practical_reading_output")

    practical_contracts = (
        observation.get("practical_domain_contracts", {}).values()
        if isinstance(observation.get("practical_domain_contracts", {}), dict) else []
    )
    for contract in practical_contracts:
        if not isinstance(contract, dict):
            continue
        if contract.get("raw_score_leak"):
            add_flag("raw_model_score_leak_in_practical_contract", "M6_practical_reading_output")
        if contract.get("version") != "v30.practical_domain_reading.v2":
            add_flag("practical_domain_contract_version_mismatch", "M6_practical_reading_output")
        if int(contract.get("ranked_decision_link_count", 0) or 0) < 3:
            add_flag("practical_domain_missing_ranked_decision_links", "M6_practical_reading_output")
        if not contract.get("module_trace_uses_m1_m5"):
            add_flag("practical_domain_module_trace_incomplete", "M6_practical_reading_output")

    module_readiness = {
        "M1_birth_input_chart_facts": not any(flag in drift_flags for flag in (
            "chart_build_status_mismatch",
            "blocked_or_pending_case_has_fake_pillars",
        )),
        "M2_luck_flow_timing_context": "six_pillar_status_mismatch" not in drift_flags,
        "M4_ten_god_energy_model": "model_signal_missing_for_ready_chart" not in drift_flags,
        "M5_ranked_decisions": "ranked_decisions_incomplete_for_ready_chart" not in drift_flags,
        "M6_practical_reading_output": not any(flag in drift_flags for flag in (
            "practical_reading_status_mismatch",
            "practical_domains_incomplete_for_ready_chart",
            "raw_model_score_leak_in_practical_contract",
            "practical_domain_contract_version_mismatch",
            "practical_domain_missing_ranked_decision_links",
            "practical_domain_module_trace_incomplete",
        )),
        "M7_real_case_calibration": True,
    }
    return {
        "version": "v30.real_case_calibration_drift_summary.v1",
        "calibration_status": "stable" if not drift_flags else "needs_module_review",
        "drift_flags": drift_flags,
        "module_adjustment_targets": module_adjustment_targets,
        "module_readiness": module_readiness,
        "expected_statuses": {
            "chart_build": expected_chart_status,
            "six_pillar": expected_six_status,
            "practical_reading": expected_practical_status,
        },
        "observed_statuses": {
            "chart_build": chart_status,
            "six_pillar": str(observation.get("six_pillar_status") or ""),
            "practical_reading": str(observation.get("practical_reading_status") or ""),
        },
        "boundary": "real_case_calibration_drift_routes_to_module_adjustments_not_chart_fact_mutation",
    }


def _build_case_hidden_factor_state(*, runtime, calibration, chart_input: dict[str, Any]):
    from v30.hidden_factor import merge_hidden_factor_state

    sequence = chart_input.get("feedback_sequence")
    payloads = sequence if isinstance(sequence, list) else [chart_input]
    state = None
    for index, payload in enumerate(payloads):
        if not isinstance(payload, dict):
            continue
        feedback_payload = {**chart_input, **payload}
        feedback_payload.pop("feedback_sequence", None)
        feedback_payload.setdefault("feedback_id", f"{runtime.reading_id}:hidden-feedback:{index}")
        feedback = hidden_factor_feedback_from_payload(
            reading_id=runtime.reading_id,
            context_id=runtime.chart_context.context_id,
            payload=feedback_payload,
        )
        incoming = build_hidden_factor_state(
            reading_id=runtime.reading_id,
            context_id=runtime.chart_context.context_id,
            calibration=calibration,
            feedback=[feedback],
        )
        state = merge_hidden_factor_state(state, incoming)
    return state or build_hidden_factor_state(
        reading_id=runtime.reading_id,
        context_id=runtime.chart_context.context_id,
        calibration=calibration,
    )


def _expression_quality(policy_effect: dict[str, Any]) -> dict[str, Any]:
    rendered = policy_effect.get("rendered_narrative", {})
    expression_plan = policy_effect.get("expression_plan", {})
    text = str(rendered.get("text") or "") if isinstance(rendered, dict) else ""
    diagnostics = rendered.get("diagnostics", {}) if isinstance(rendered, dict) else {}
    style_profile = expression_plan.get("style_profile", {}) if isinstance(expression_plan, dict) else {}
    terms = ["日主", "格局", "原局", "大运", "流年", "藏干", "用神", "结构动态", "画像", "隐藏因子"]
    forbidden_hits = diagnostics.get("forbidden_token_hits", []) if isinstance(diagnostics, dict) else []
    return {
        "text_length": len(text),
        "bazi_term_count": sum(1 for term in terms if term in text),
        "forbidden_token_hits": [str(row) for row in forbidden_hits] if isinstance(forbidden_hits, list) else [],
        "has_boundary_language": any(term in text for term in ["未确认", "边界", "不把", "定论"]),
        "role_key": style_profile.get("role_key") if isinstance(style_profile, dict) else "",
        "voice": style_profile.get("voice") if isinstance(style_profile, dict) else "",
        "density": style_profile.get("density") if isinstance(style_profile, dict) else "",
    }


def _llm_contract_quality(policy_effect: dict[str, Any]) -> dict[str, Any]:
    summary = policy_effect.get("llm_output_contract_summary", {})
    contracts = policy_effect.get("llm_output_contracts", [])
    if not isinstance(summary, dict):
        summary = {}
    if not isinstance(contracts, list):
        contracts = []
    return {
        "version": str(summary.get("version") or ""),
        "contract_count": int(summary.get("contract_count") or 0),
        "task_types": [str(row) for row in summary.get("task_types", [])] if isinstance(summary.get("task_types"), list) else [],
        "validation_status": str(summary.get("validation_status") or "missing"),
        "drift_failures": [str(row) for row in summary.get("drift_failures", [])] if isinstance(summary.get("drift_failures"), list) else [],
        "contract_ids": [
            str(row.get("contract_id"))
            for row in contracts
            if isinstance(row, dict) and row.get("contract_id")
        ],
    }


def _bazi_llm_output_acceptance_quality(case: SyntheticBaziCase) -> dict[str, Any]:
    if case.domain != "bazi_llm_acceptance":
        return {}
    readiness = run_bazi_llm_output_acceptance_readiness(reading_id=case.case_id)
    decision = readiness.get("decision", {})
    acceptance_results = readiness.get("acceptance_results", {})
    accepted_count = sum(
        1 for row in acceptance_results.values()
        if isinstance(row, dict) and row.get("accepted") is True
    ) if isinstance(acceptance_results, dict) else 0
    rejected_count = sum(
        1 for row in acceptance_results.values()
        if isinstance(row, dict) and row.get("accepted") is False
    ) if isinstance(acceptance_results, dict) else 0
    role_failure_count = sum(
        len(row.get("role_failures", []))
        for row in acceptance_results.values()
        if isinstance(row, dict) and isinstance(row.get("role_failures"), list)
    ) if isinstance(acceptance_results, dict) else 0
    drift_rejected_count = sum(
        1 for row in acceptance_results.values()
        if isinstance(row, dict) and row.get("drift_passed") is False
    ) if isinstance(acceptance_results, dict) else 0
    schema_rejected_count = sum(
        1 for row in acceptance_results.values()
        if isinstance(row, dict) and row.get("missing_fields")
    ) if isinstance(acceptance_results, dict) else 0
    return {
        "version": "v30.synthetic.bazi_llm_acceptance_quality.v1",
        "readiness_version": readiness.get("version", ""),
        "decision_status": decision.get("decision_status") if isinstance(decision, dict) else "",
        "readiness_ready": decision.get("readiness_ready") if isinstance(decision, dict) else False,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "schema_rejected_count": schema_rejected_count,
        "role_failure_count": role_failure_count,
        "drift_rejected_count": drift_rejected_count,
        "live_llm_required": decision.get("live_llm_required") if isinstance(decision, dict) else True,
        "chart_fact_mutation_allowed": decision.get("chart_fact_mutation_allowed") if isinstance(decision, dict) else True,
        "target_training_domains": ["expression", "question_intelligence"],
        "forbidden_training_domains": ["chart_facts", "calendar_conversion", "luck_cycle", "flow_timing"],
        "boundary": "bazi_llm_acceptance_trains_expression_and_question_strategy_not_chart_facts",
    }


def run_synthetic_suite(
    cases: tuple[SyntheticBaziCase, ...] = SYNTHETIC_SMOKE_CASES,
    *,
    suite_id: str = "v30.synthetic.smoke",
    policy_payload_overrides: dict[str, dict[str, object]] | None = None,
    active_policy_version_overrides: dict[str, str] | None = None,
) -> SyntheticValidationSuiteResult:
    results = [
        run_synthetic_case(
            case,
            policy_payload_overrides=policy_payload_overrides,
            active_policy_version_overrides=active_policy_version_overrides,
        )
        for case in cases
    ]
    passed_count = sum(1 for result in results if result.passed)
    failed_count = len(results) - passed_count
    return SyntheticValidationSuiteResult(
        suite_id=suite_id,
        passed=failed_count == 0,
        case_count=len(results),
        passed_count=passed_count,
        failed_count=failed_count,
        results=results,
    )


def run_synthetic_tier(
    tier: str = "smoke",
    *,
    suite_id: str | None = None,
    policy_payload_overrides: dict[str, dict[str, object]] | None = None,
    active_policy_version_overrides: dict[str, str] | None = None,
) -> SyntheticValidationSuiteResult:
    if tier == "latent_bazi_divergence":
        from v30.validation.latent_bazi_divergence import run_latent_bazi_divergence_synthetic_suite

        result = run_latent_bazi_divergence_synthetic_suite()
        if suite_id and suite_id != result.suite_id:
            return result.model_copy(update={"suite_id": suite_id})
        return result
    cases = SYNTHETIC_SUITES[tier]
    return run_synthetic_suite(
        cases,
        suite_id=suite_id or f"v30.synthetic.{tier}",
        policy_payload_overrides=policy_payload_overrides,
        active_policy_version_overrides=active_policy_version_overrides,
    )
