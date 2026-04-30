from __future__ import annotations

from typing import Any, Dict, List


P64_INTERACTIVE_CALIBRATION_DESIGN_VERSION = "v19.p64.interactive_calibration_design.v1"
P64_INTERACTIVE_CALIBRATION_REGRESSION_VERSION = "v19.p64.interactive_calibration_design_regression.v1"

P64_FORBIDDEN_QUESTION_TEXT = [
    "一定",
    "必然",
    "发财",
    "破财",
    "离婚",
    "疾病",
    "寿命",
    "诊断",
    "治疗",
    "灾祸",
    "应期",
]

P64_BLOCKED_USES = [
    "core_rule_truth_update",
    "production_rule_activation",
    "user_feedback_direct_rule_update",
    "answer_conclusion_update",
    "domain_prediction_update",
    "medical_or_lifespan_inference",
]

P64_GUARDRAILS = [
    "P64_INTERACTIVE_CALIBRATION_DESIGN",
    "CALIBRATION_SPEC_ONLY",
    "USER_EVENT_EVIDENCE_ONLY",
    "NO_CORE_RULE_TRUTH_UPDATE",
    "NO_USER_FEEDBACK_DIRECT_RULE_UPDATE",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_RESULT_MUTATION",
    "NO_ANSWER_MUTATION",
    "NO_MEDICAL_OR_LIFESPAN_INFERENCE",
    "NO_BLACK_BOX_CORE_INFERENCE",
]


def build_p64_interactive_calibration_design() -> Dict[str, Any]:
    factors = _latent_factor_catalog()
    event_schema = _event_evidence_schema()
    inquiries = _calibration_inquiry_catalog()
    model_policy = _calibration_model_policy()
    return {
        "ok": True,
        "version": P64_INTERACTIVE_CALIBRATION_DESIGN_VERSION,
        "status": "interactive_calibration_design_ready_no_runtime_mutation",
        "runtime_scope": "architecture_and_schema_spec_only_no_runtime_mutation",
        "summary": {
            "latent_factor_count": len(factors),
            "event_required_field_count": len(event_schema["required_fields"]),
            "inquiry_count": len(inquiries),
            "domain_count": len({row["domain"] for row in inquiries}),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "architecture": {
            "position": "after_rule_graph_before_personalized_route_rerank",
            "pipeline": [
                "Rule Graph structural prior",
                "Calibration Inquiry Orchestrator",
                "User Event Evidence Ledger",
                "Latent Factor Estimator",
                "Personalized Route Re-ranker",
                "Answer and question recommendation",
            ],
            "principle": "chart_structure_is_prior_user_events_are_observations_calibration_is_per_profile_only",
        },
        "latent_factors": factors,
        "event_evidence_schema": event_schema,
        "calibration_inquiries": inquiries,
        "model_policy": model_policy,
        "privacy_policy": {
            "storage_scope": "per_profile_event_evidence_ledger",
            "aggregation_scope": "anonymous_synthetic_review_only",
            "sensitive_domains": ["health", "family", "relationship"],
            "retention_policy": "user_deletable_profile_bound_records",
            "blocked_collection": ["medical_diagnosis", "lifespan_claim", "precise_identity_sensitive_events"],
        },
        "guardrails": P64_GUARDRAILS,
    }


def run_p64_interactive_calibration_design_regression() -> Dict[str, Any]:
    design = build_p64_interactive_calibration_design()
    failures: List[Dict[str, str]] = []
    factors = [dict(row) for row in design.get("latent_factors") or [] if isinstance(row, dict)]
    inquiries = [dict(row) for row in design.get("calibration_inquiries") or [] if isinstance(row, dict)]
    schema = design.get("event_evidence_schema") or {}
    required_factor_ids = {
        "baseline_amplifier",
        "action_efficiency",
        "resource_support",
        "timing_sensitivity",
        "wealth_amplifier",
        "career_amplifier",
        "relationship_sensitivity",
        "health_safety_modifier",
    }
    observed_factor_ids = {str(row.get("factor_id") or "") for row in factors}
    if not required_factor_ids <= observed_factor_ids:
        failures.append(_failure("latent_factor_missing", ",".join(sorted(required_factor_ids - observed_factor_ids))))
    required_fields = {"event_domain", "event_type", "time_range", "date_precision", "valence", "intensity", "confidence", "allowed_use"}
    if not required_fields <= set(schema.get("required_fields") or []):
        failures.append(_failure("event_schema_required_fields_missing", ",".join(sorted(required_fields - set(schema.get("required_fields") or [])))))
    inquiry_domains = {str(row.get("domain") or "") for row in inquiries}
    if not {"wealth", "career", "relationship", "health", "relocation", "stress"}.issubset(inquiry_domains):
        failures.append(_failure("inquiry_domain_coverage_missing", ",".join(sorted(inquiry_domains))))
    for inquiry in inquiries:
        failures.extend(_inquiry_failures(inquiry))
    for factor in factors:
        blocked = set(factor.get("blocked_uses") or [])
        if not {"rule_truth_update", "deterministic_prediction", "user_visible_score"} <= blocked:
            failures.append(_failure("latent_factor_blocked_use_missing", str(factor.get("factor_id") or "")))
    blocked_policy = set((design.get("model_policy") or {}).get("blocked_models_now") or [])
    if not {"gnn_core_inference", "rl_core_rule_update", "user_feedback_to_rule_truth"} <= blocked_policy:
        failures.append(_failure("model_policy_block_missing", ",".join(sorted(blocked_policy))))
    summary = design.get("summary") or {}
    if int(summary.get("engine_enabled_count") or 0) != 0 or int(summary.get("answer_mutation_count") or 0) != 0 or summary.get("runtime_mutation") is True:
        failures.append(_failure("runtime_mutation_not_allowed", "P64 must remain design-only."))
    status = "pass" if not failures else "fail"
    return {
        "ok": status == "pass",
        "version": P64_INTERACTIVE_CALIBRATION_REGRESSION_VERSION,
        "status": status,
        "runtime_scope": "interactive_calibration_design_regression_no_runtime_mutation",
        "summary": {
            "latent_factor_count": len(factors),
            "inquiry_count": len(inquiries),
            "failure_count": len(failures),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "design": design,
        "failures": failures,
        "guardrails": P64_GUARDRAILS,
    }


def _latent_factor_catalog() -> List[Dict[str, Any]]:
    common_blocked = ["rule_truth_update", "deterministic_prediction", "user_visible_score", "medical_or_lifespan_inference"]
    common_allowed = ["personal_route_rerank", "question_priority", "calibration_posterior", "synthetic_profile_review"]
    return [
        _factor("baseline_amplifier", "基础兑现放大因子", "global", "同样结构下现实兑现的整体强弱。", common_allowed, common_blocked),
        _factor("action_efficiency", "行动效率", "global", "行动转结果的效率，不等同于吉凶。", common_allowed, common_blocked),
        _factor("resource_support", "资源支持", "global", "家庭、平台、人脉、地域资源对结构兑现的支持。", common_allowed, common_blocked),
        _factor("opportunity_access", "机会可达性", "global", "命主接触机会和进入平台的可达性。", common_allowed, common_blocked),
        _factor("risk_tolerance", "风险承受", "global", "路径波动承受度，用于问题排序和解释边界。", common_allowed, common_blocked),
        _factor("timing_sensitivity", "时间引动敏感度", "time", "大运流年触发时现实事件是否更明显。", common_allowed, common_blocked),
        _factor("wealth_amplifier", "财富兑现放大因子", "wealth", "财富相关结构在个人现实中的兑现强弱。", common_allowed, common_blocked),
        _factor("career_amplifier", "事业兑现放大因子", "career", "事业与角色变化在个人现实中的兑现强弱。", common_allowed, common_blocked),
        _factor("relationship_sensitivity", "关系事件敏感度", "relationship", "关系领域事件对结构路径的校准权重。", common_allowed, common_blocked),
        _factor("relocation_mobility", "迁移流动性", "relocation", "地域、迁移、工作环境变化对现实路径的影响。", common_allowed, common_blocked),
        _factor("stress_recovery_capacity", "压力恢复能力", "stress", "压力事件后的恢复和稳定能力。", common_allowed, common_blocked),
        _factor("health_safety_modifier", "健康安全边界修正", "health", "只用于健康安全提醒边界，不用于疾病、寿命或诊断推断。", common_allowed, common_blocked),
    ]


def _event_evidence_schema() -> Dict[str, Any]:
    return {
        "ledger_name": "User Event Evidence Ledger",
        "required_fields": [
            "event_domain",
            "event_type",
            "time_range",
            "date_precision",
            "valence",
            "intensity",
            "confidence",
            "allowed_use",
        ],
        "optional_fields": [
            "event_id",
            "profile_id",
            "source",
            "matched_time_nodes",
            "freeform_note",
            "privacy_level",
            "created_at",
        ],
        "allowed_domains": ["wealth", "career", "relationship", "health", "relocation", "family", "study", "stress"],
        "allowed_event_types": [
            "income_change",
            "career_transition",
            "relationship_status_change",
            "health_state_change",
            "relocation",
            "family_responsibility_change",
            "education_or_skill_change",
            "high_pressure_period",
        ],
        "allowed_date_precision": ["year", "year_range", "month", "quarter", "unknown"],
        "allowed_valence": ["positive", "neutral", "negative", "mixed", "unknown"],
        "allowed_use": ["personal_calibration_only"],
        "blocked_use": P64_BLOCKED_USES,
    }


def _calibration_inquiry_catalog() -> List[Dict[str, Any]]:
    return [
        _inquiry("calib.wealth.change_window", "wealth", "在你记得比较清楚的年份里，收入或资源状态有没有出现过明显变化？", ["wealth_amplifier", "timing_sensitivity"]),
        _inquiry("calib.career.transition_window", "career", "你的职业角色、岗位责任或工作平台，是否有过明显转换的阶段？", ["career_amplifier", "resource_support"]),
        _inquiry("calib.relationship.status_context", "relationship", "关系状态或亲密关系重心，是否有过比较明确的变化阶段？", ["relationship_sensitivity", "timing_sensitivity"]),
        _inquiry("calib.health.state_boundary", "health", "某些年份里，你的精力、压力承受或作息稳定性是否有明显变化？", ["health_safety_modifier", "stress_recovery_capacity"]),
        _inquiry("calib.relocation.environment_change", "relocation", "居住地、工作城市或长期环境是否有过明显变化？", ["relocation_mobility", "opportunity_access"]),
        _inquiry("calib.stress.recovery_pattern", "stress", "遇到压力较大的阶段时，你通常恢复得较快、较慢，还是波动较大？", ["stress_recovery_capacity", "action_efficiency"]),
        _inquiry("calib.resource.support_pattern", "global", "关键转折阶段里，外部资源支持更像是增强、减弱，还是变化不明显？", ["resource_support", "baseline_amplifier"]),
        _inquiry("calib.action.result_pattern", "global", "你投入行动后，结果通常来得较快、较慢，还是需要多次尝试？", ["action_efficiency", "baseline_amplifier"]),
    ]


def _calibration_model_policy() -> Dict[str, Any]:
    return {
        "active_models_now": [
            "rule_graph_structural_prior",
            "deterministic_factor_scoring",
            "bayesian_update_for_internal_posterior",
            "active_learning_question_selection",
        ],
        "reserved_models_later": {
            "factor_graph": "Use when event ledger has enough time-node observations.",
            "gnn": "Path embedding or rerank only after labeled synthetic calibration data exists.",
            "contextual_bandit": "Question ordering only after safe feedback metrics exist.",
            "rl": "Dialog policy only, not core rule truth.",
        },
        "blocked_models_now": [
            "gnn_core_inference",
            "rl_core_rule_update",
            "user_feedback_to_rule_truth",
            "black_box_domain_prediction",
        ],
        "user_visible_policy": "Never expose numeric luck scores or probability claims; surface only calibrated reading focus when needed.",
    }


def _factor(factor_id: str, label: str, domain: str, purpose: str, allowed_uses: List[str], blocked_uses: List[str]) -> Dict[str, Any]:
    return {
        "factor_id": factor_id,
        "label_zh": label,
        "domain": domain,
        "purpose": purpose,
        "prior": {"center": 0.0, "scale": 1.0, "range": [-2.0, 2.0]},
        "allowed_uses": list(allowed_uses),
        "blocked_uses": list(blocked_uses),
        "evidence_sources": ["user_event_evidence", "synthetic_user_calibration_eval"],
    }


def _inquiry(inquiry_id: str, domain: str, prompt_zh: str, target_factors: List[str]) -> Dict[str, Any]:
    return {
        "inquiry_id": inquiry_id,
        "domain": domain,
        "prompt_zh": prompt_zh,
        "response_type": "structured_choice_with_optional_time_range",
        "target_factors": target_factors,
        "allowed_use": "personal_calibration_only",
        "neutrality_policy": "ask_observation_without_implying_expected_event",
        "blocked_outputs": P64_FORBIDDEN_QUESTION_TEXT,
    }


def _inquiry_failures(inquiry: Dict[str, Any]) -> List[Dict[str, str]]:
    failures = []
    text = str(inquiry.get("prompt_zh") or "")
    for token in P64_FORBIDDEN_QUESTION_TEXT:
        if token in text:
            failures.append(_failure("inquiry_forbidden_text", f"{inquiry.get('inquiry_id')}:{token}"))
    if inquiry.get("allowed_use") != "personal_calibration_only":
        failures.append(_failure("inquiry_allowed_use_mismatch", str(inquiry.get("inquiry_id") or "")))
    if not inquiry.get("target_factors"):
        failures.append(_failure("inquiry_target_factors_missing", str(inquiry.get("inquiry_id") or "")))
    return failures


def _failure(failure_type: str, detail: str) -> Dict[str, str]:
    return {"failure_type": failure_type, "detail": detail}
