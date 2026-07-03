from __future__ import annotations

ZIWEI_SYSTEM_STANDARD_VERSION = "v30.ziwei_system_standard.v1"
ZIWEI_FACT_LAYER_VERSION = "v30.ziwei_fact_layer.v0"
ZIWEI_SIGNAL_LAYER_VERSION = "v30.ziwei_signal_layer.v1"

ZIWEI_DECISION_WEIGHT_V1 = 0.0
ZIWEI_DECISION_WEIGHT_V2_INITIAL_RANGE = (0.05, 0.15)

CALENDAR_STANDARD = "solar_birth_input_converted_before_ziwei_charting"
LEAP_MONTH_POLICY = "leap_month_recorded_explicitly_no_silent_month_shift"
HOUR_BOUNDARY_POLICY = "standard_two_hour_branch_with_zi_hour_boundary_recorded"
TRUE_SOLAR_TIME_POLICY = "true_solar_time_flag_must_be_explicit_not_assumed"
LIFE_BODY_PALACE_METHOD = "ming_gong_shen_gong_standard_v1"
MAJOR_PERIOD_METHOD = "da_xian_direction_and_start_age_standard_v1"

TWELVE_PALACES = (
    "life",
    "siblings",
    "spouse",
    "children",
    "wealth",
    "health",
    "travel",
    "friends",
    "career",
    "property",
    "fortune",
    "parents",
)

FOURTEEN_MAIN_STARS = (
    "ziwei",
    "tianji",
    "taiyang",
    "wuqu",
    "tiantong",
    "lianzhen",
    "tianfu",
    "taiyin",
    "tanlang",
    "jumen",
    "tianxiang",
    "tianliang",
    "qisha",
    "pojun",
)

V1_AUXILIARY_STARS = (
    "zuofu",
    "youbi",
    "wenchang",
    "wenqu",
    "tiankui",
    "tianyue",
    "lucun",
    "tianma",
    "qingyang",
    "tuoluo",
    "huoxing",
    "lingxing",
    "dikong",
    "dijie",
)

V2_DEFERRED_STARS = (
    "hongluan",
    "tianxi",
    "xianchi",
    "guchen",
    "guasui",
    "tianyao",
    "jieshen",
    "fenggao",
    "taifu",
)

BIRTH_YEAR_TRANSFORMS_REQUIRED = ("lu", "quan", "ke", "ji")

ZIWEI_STANDARD_GUARDRAILS = (
    "ziwei_v0_outputs_chart_facts_only_no_judgment",
    "ziwei_v1_outputs_domain_signals_only_no_final_verdict",
    "ziwei_v1_decision_weight_is_zero",
    "ziwei_must_not_override_bazi_decision_engine_or_reality_probe",
    "ziwei_user_surface_hides_raw_star_details_by_default",
)
