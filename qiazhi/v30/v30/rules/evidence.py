from __future__ import annotations

from pydantic import Field

from v30.contracts import FeatureEvidence, V30Model


RULE_EVIDENCE_VERSION = "v30.rule_evidence.v1"


class RuleEvidenceSpec(V30Model):
    rule_id: str
    domain: str
    title: str
    condition_supports: list[str] = Field(default_factory=list)
    condition_domains: list[str] = Field(default_factory=list)
    emits_supports: list[str] = Field(default_factory=list)
    emits_weakens: list[str] = Field(default_factory=list)
    counter_weakens: list[str] = Field(default_factory=list)
    boundary: str
    decision_state: str = "support"
    runtime_allowed: bool = True
    base_confidence: float = 0.5


RULE_EVIDENCE_SPECS = (
    RuleEvidenceSpec(
        rule_id="v30.rule.chart.bound_context_no_rewrite",
        domain="chart",
        title="Bound chart context blocks downstream rewriting of pillars, day master, and deterministic facts.",
        condition_supports=["chart_context_bound", "element_context_bound"],
        emits_supports=["rule_chart_fact_boundary"],
        emits_weakens=["chart_fact_mutation", "llm_chart_fact_generation", "training_chart_fact_generation"],
        boundary="rule_boundary_chart_context_is_read_only",
        decision_state="blocked",
        base_confidence=0.86,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.chart.output_requires_fact_basis",
        domain="chart",
        title="Any public reading must keep deterministic chart facts as the calculation basis.",
        condition_supports=["chart_context_bound", "structure_pattern_candidate", "useful_god_candidate_question"],
        emits_supports=["rule_chart_basis_required"],
        emits_weakens=["unsupported_reading_output", "fixed_bazi_verdict"],
        boundary="rule_boundary_reading_output_requires_chart_fact_basis",
        decision_state="requires_review",
        base_confidence=0.78,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.element.balance_context_not_strength_verdict",
        domain="element",
        title="Element balance and seasonal state are review inputs, not fixed strength verdicts.",
        condition_supports=["element_balance_review", "wang_xiang_xiu_qiu_si_review"],
        emits_supports=["rule_element_balance_review_boundary"],
        emits_weakens=["fixed_strength_verdict", "single_factor_reading"],
        boundary="rule_boundary_element_balance_not_strength_verdict",
        decision_state="requires_review",
        base_confidence=0.76,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.element.seasonal_state_requires_counterforce",
        domain="element",
        title="Seasonal element state requires counterforce and path evidence before interpretation.",
        condition_supports=["seasonal_state:xiang", "season_element:water", "seasonal_indirect_context:day_master"],
        emits_supports=["rule_seasonal_state_counterforce_review"],
        emits_weakens=["fixed_strength_verdict", "fixed_geju_verdict"],
        boundary="rule_boundary_seasonal_state_requires_counterforce_review",
        decision_state="requires_review",
        base_confidence=0.74,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.foundation.core_chain_requires_m1_m2_m3",
        domain="foundation",
        title="The core calculation chain must preserve M1/M2 facts before M3 judgment evidence.",
        condition_supports=["chart_context_bound", "element_context_bound", "rule_chart_fact_boundary"],
        emits_supports=["rule_foundation_m1_m2_m3_chain"],
        emits_weakens=["unsupported_reading_output", "chart_fact_mutation"],
        boundary="rule_boundary_foundation_chain_preserves_deterministic_facts",
        decision_state="blocked",
        base_confidence=0.84,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.time_context.blocks_timing_claim",
        domain="time_context",
        title="Missing explicit luck or flow context blocks timing claims.",
        condition_domains=["time_context"],
        emits_supports=["rule_time_boundary"],
        emits_weakens=["timing_claim", "special_year_claim"],
        counter_weakens=["time_activation_review"],
        boundary="rule_boundary_no_timing_prediction_without_explicit_time_layer",
        decision_state="blocked",
        base_confidence=0.82,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.useful_god.candidate_gate",
        domain="useful_god",
        title="Useful-god remains candidate review until evidence paths are resolved.",
        condition_supports=["useful_god_candidate_question"],
        emits_supports=["rule_useful_god_candidate_gate"],
        emits_weakens=["fixed_useful_god_verdict"],
        counter_weakens=["fixed_useful_god_verdict"],
        boundary="rule_boundary_useful_god_candidate_only",
        decision_state="requires_review",
        base_confidence=0.76,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.hidden_factor.requires_dialogue",
        domain="hidden_factor",
        title="Hidden stems can become amplifier hypotheses only through dialogue calibration.",
        condition_supports=["hidden_stem_context"],
        emits_supports=["rule_hidden_factor_dialogue_boundary"],
        emits_weakens=["deterministic_hidden_factor_claim"],
        counter_weakens=["special_event_confirmed", "hidden_factor_user_calibrated"],
        boundary="rule_boundary_hidden_factor_requires_user_feedback",
        decision_state="requires_dialogue",
        base_confidence=0.72,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.branch_relation.requires_dynamic_review",
        domain="branch_relation",
        title="Branch relations require dynamic structure review instead of single-factor reading.",
        condition_supports=["structure_dynamic_review"],
        emits_supports=["rule_structure_dynamic_review"],
        emits_weakens=["single_factor_reading"],
        counter_weakens=["single_factor_reading"],
        boundary="rule_boundary_branch_relation_requires_dynamic_review",
        decision_state="requires_review",
        base_confidence=0.7,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.structure_pattern.month_command_candidate_gate",
        domain="structure_pattern",
        title="Month-command and pattern signals remain candidate review until counter-force and path evidence are checked.",
        condition_supports=["month_command_review", "structure_pattern_candidate"],
        emits_supports=["rule_month_command_pattern_gate"],
        emits_weakens=["fixed_geju_verdict", "fixed_strength_verdict"],
        counter_weakens=["pattern_path_resolved"],
        boundary="rule_boundary_month_command_pattern_candidate_only",
        decision_state="requires_review",
        base_confidence=0.74,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.useful_god.climate_review_gate",
        domain="useful_god",
        title="Climate regulation can rank useful-god candidates but cannot finalize useful-god.",
        condition_supports=["climate_regulation_review", "tiaohou_candidate_path"],
        emits_supports=["rule_tiaohou_candidate_gate"],
        emits_weakens=["fixed_useful_god_verdict"],
        counter_weakens=["useful_god_path_resolved"],
        boundary="rule_boundary_tiaohou_candidate_not_final_useful_god",
        decision_state="requires_review",
        base_confidence=0.73,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.useful_god.bingyao_review_gate",
        domain="useful_god",
        title="Disease-medicine review supplies support and weakening evidence without overriding chart facts.",
        condition_supports=["bingyao_blockage_review", "bingyao_remedy_candidate_path"],
        emits_supports=["rule_bingyao_review_gate"],
        emits_weakens=["fixed_useful_god_verdict"],
        counter_weakens=["useful_god_path_resolved"],
        boundary="rule_boundary_bingyao_review_not_fixed_useful_god",
        decision_state="requires_review",
        base_confidence=0.72,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.domain.blocks_outcome_claims",
        domain="domain_rule",
        title="Domain paths block wealth, career, relationship, and health outcome claims without enough evidence.",
        condition_supports=["domain_rule_review_candidate"],
        emits_supports=["rule_domain_outcome_boundary"],
        emits_weakens=[
            "fixed_wealth_outcome_claim",
            "fixed_career_outcome_claim",
            "fixed_relationship_outcome_claim",
            "fixed_health_outcome_claim",
        ],
        boundary="rule_boundary_domain_paths_not_life_outcome_verdicts",
        decision_state="blocked",
        base_confidence=0.76,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.domain.requires_subfamily_evidence",
        domain="domain_rule",
        title="Domain reading paths require subfamily evidence before customer-facing emphasis.",
        condition_supports=[
            "domain_rule_family:wealth_pressure",
            "domain_rule_family:career_authority_path",
            "domain_rule_family:relationship_relation_path",
            "domain_rule_family:health_element_imbalance_review",
        ],
        emits_supports=["rule_domain_subfamily_evidence_required"],
        emits_weakens=[
            "fixed_wealth_outcome_claim",
            "fixed_career_outcome_claim",
            "fixed_relationship_outcome_claim",
            "fixed_health_outcome_claim",
        ],
        boundary="rule_boundary_domain_subfamilies_required_before_outcome_language",
        decision_state="requires_review",
        base_confidence=0.75,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.romance.blocks_private_fact_claims",
        domain="romance",
        title="Romance/relationship signals cannot become private relationship facts or event claims.",
        condition_supports=[
            "domain_rule_family:relationship_relation_path",
            "domain_rule_family:relationship_authority_or_wealth_marker_path",
            "palace_position_review",
        ],
        emits_supports=["rule_romance_private_fact_boundary"],
        emits_weakens=["fixed_relationship_outcome_claim", "private_relationship_fact_claim"],
        boundary="rule_boundary_romance_path_not_private_fact_or_event_claim",
        decision_state="blocked",
        base_confidence=0.8,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.rule_counterevidence.requires_trace",
        domain="rule_counterevidence",
        title="Counter-evidence can change rule state only when the original evidence trace remains visible.",
        condition_supports=["rule_decision_state:countered", "counter_evidence"],
        emits_supports=["rule_counterevidence_trace_required"],
        emits_weakens=["silent_rule_override", "untracked_policy_override"],
        boundary="rule_boundary_counterevidence_preserves_original_trace",
        decision_state="requires_review",
        base_confidence=0.78,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.rule_counterevidence.blocks_silent_policy_override",
        domain="rule_counterevidence",
        title="Policy weights and training candidates cannot silently replace rule evidence.",
        condition_supports=["rule_counterevidence_trace_required", "rule_decision_state:countered", "rule_chart_fact_boundary"],
        emits_supports=["rule_silent_policy_override_blocked"],
        emits_weakens=["silent_rule_override", "untracked_policy_override", "training_chart_fact_generation"],
        boundary="rule_boundary_policy_override_must_be_traceable",
        decision_state="blocked",
        base_confidence=0.8,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.structure_pattern.requires_rescue_and_failure_review",
        domain="structure_pattern",
        title="Pattern review must check success, failure, rescue, and counterforce before naming a structure.",
        condition_supports=["month_command_review", "structure_pattern_candidate", "rule_month_command_pattern_gate"],
        emits_supports=["rule_pattern_success_failure_rescue_review"],
        emits_weakens=["fixed_geju_verdict", "fixed_strength_verdict"],
        boundary="rule_boundary_pattern_success_failure_rescue_before_structure_language",
        decision_state="requires_review",
        base_confidence=0.77,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.time_context.requires_explicit_time_layer",
        domain="time_context",
        title="Timing language requires explicit luck, flow-year, or flow-month time-layer evidence.",
        condition_supports=["rule_time_boundary"],
        condition_domains=["time_context"],
        emits_supports=["rule_explicit_time_layer_required"],
        emits_weakens=["timing_claim", "special_year_claim", "flow_month_claim_without_context"],
        counter_weakens=["time_activation_review"],
        boundary="rule_boundary_time_layer_required_for_timing_language",
        decision_state="blocked",
        base_confidence=0.82,
    ),
    RuleEvidenceSpec(
        rule_id="v30.rule.branch_relation.arbitration_gate",
        domain="branch_relation",
        title="Branch relations with conflict or alignment require relation arbitration before public interpretation.",
        condition_supports=["branch_relation_arbitration_review"],
        emits_supports=["rule_branch_arbitration_gate"],
        emits_weakens=["single_factor_reading"],
        counter_weakens=["single_factor_reading"],
        boundary="rule_boundary_branch_relation_arbitration_required",
        decision_state="requires_review",
        base_confidence=0.72,
    ),
)


def build_rule_evidence(
    evidence: list[FeatureEvidence],
    rule_policy: dict[str, object] | None = None,
) -> list[FeatureEvidence]:
    rows: list[FeatureEvidence] = []
    for spec in RULE_EVIDENCE_SPECS:
        matched = _matched_evidence(spec, evidence)
        if not matched:
            continue
        policy_weight = _rule_policy_weight(rule_policy or {}, rule_id=spec.rule_id, domain=spec.domain)
        confidence = min(1.0, (spec.base_confidence + len(matched) * 0.02) * policy_weight)
        counters = _counter_evidence(spec, evidence)
        decision_state = "countered" if counters else spec.decision_state
        supports = [*spec.emits_supports, f"rule_id:{spec.rule_id}", f"rule_domain:{spec.domain}"]
        supports.append(f"rule_decision_state:{decision_state}")
        supports.extend(f"counter_evidence:{row.evidence_id}" for row in counters)
        if policy_weight != 1.0:
            supports.append(f"rule_policy_weight:{policy_weight}")
        rows.append(
            FeatureEvidence(
                evidence_id=f"{matched[0].source}:rule:{spec.rule_id.rsplit('.', 1)[-1]}",
                domain="rule",
                kind=spec.domain,
                label=f"{spec.rule_id}:{spec.title}",
                source=matched[0].source,
                confidence=round(confidence, 3),
                supports=supports,
                weakens=[*spec.emits_weakens, *[f"countered_by:{row.evidence_id}" for row in counters]],
                boundary=spec.boundary,
            )
        )
    return rows


def _counter_evidence(spec: RuleEvidenceSpec, evidence: list[FeatureEvidence]) -> list[FeatureEvidence]:
    if not spec.counter_weakens:
        return []
    counters: list[FeatureEvidence] = []
    expected = set(spec.counter_weakens)
    for item in evidence:
        if expected & set(item.supports):
            counters.append(item)
    return counters


def _matched_evidence(spec: RuleEvidenceSpec, evidence: list[FeatureEvidence]) -> list[FeatureEvidence]:
    rows: list[FeatureEvidence] = []
    for item in evidence:
        if spec.condition_domains and item.domain in spec.condition_domains:
            rows.append(item)
            continue
        if spec.condition_supports and set(spec.condition_supports) & set(item.supports):
            rows.append(item)
    return rows


def _rule_policy_weight(payload: dict[str, object], *, rule_id: str, domain: str) -> float:
    weights = payload.get("weights")
    if not isinstance(weights, dict):
        return 1.0
    value = _lookup_weight(weights, "rule_weights", rule_id) * _lookup_weight(weights, "domain_weights", domain)
    return round(max(0.1, min(value, 2.0)), 3)


def _lookup_weight(weights: dict[object, object], bucket: str, key: str) -> float:
    raw_bucket = weights.get(bucket)
    if not isinstance(raw_bucket, dict):
        return 1.0
    value = raw_bucket.get(key, raw_bucket.get("*", 1.0))
    if isinstance(value, int | float):
        return float(value)
    return 1.0
