from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from v30.contracts import V30Model
from v30.engines.contracts import EngineKey, MultiEngineRunResult


MINGLI_TRAINING_PHASE1_VERSION = "v30.mingli_training_phase1.v1"

MingliCaseSource = Literal["golden", "synthetic", "runtime_feedback", "practitioner_label"]
MingliGateStatus = Literal["passed", "blocked", "review"]


class MingliGoldenCase(V30Model):
    version: str = "v30.mingli_golden_case.v1"
    case_id: str
    source: MingliCaseSource = "golden"
    title: str
    user_question: str
    target_domains: list[str] = Field(default_factory=list)
    expected_verdict_domains: list[str] = Field(default_factory=list)
    expected_advice_directions: list[str] = Field(default_factory=list)
    forbidden_assertions: list[str] = Field(default_factory=list)
    required_engines: list[EngineKey] = Field(default_factory=lambda: [EngineKey.BAZI])
    ziwei_matched_rule_ids: list[str] = Field(default_factory=list)
    reality_probe_answers: list[dict[str, Any]] = Field(default_factory=list)
    min_quality_score: float = Field(default=0.68, ge=0.0, le=1.0)
    min_evidence_binding: float = Field(default=0.72, ge=0.0, le=1.0)
    min_advice_actionability: float = Field(default=0.62, ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)
    chart_fact_mutation_allowed: bool = False
    boundary: str = "mingli_golden_case_defines_expected_outputs_not_runtime_policy"

    @model_validator(mode="after")
    def _case_is_trainable_and_safe(self) -> "MingliGoldenCase":
        if not self.case_id.strip():
            raise ValueError("MingliGoldenCase requires case_id")
        if not self.user_question.strip():
            raise ValueError("MingliGoldenCase requires user_question")
        if not self.expected_verdict_domains:
            raise ValueError("MingliGoldenCase requires expected_verdict_domains")
        if not self.forbidden_assertions:
            raise ValueError("MingliGoldenCase requires forbidden_assertions")
        if self.chart_fact_mutation_allowed:
            raise ValueError("MingliGoldenCase cannot allow chart fact mutation")
        return self


class ReadingQualityScore(V30Model):
    version: str = "v30.reading_quality_score.v1"
    case_id: str
    reading_id: str
    engine_signal_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    verdict_domain_alignment: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_binding: float = Field(default=0.0, ge=0.0, le=1.0)
    advice_actionability: float = Field(default=0.0, ge=0.0, le=1.0)
    forbidden_assertion_safety: float = Field(default=0.0, ge=0.0, le=1.0)
    template_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    overclaim_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    reality_probe_alignment: float = Field(default=0.0, ge=0.0, le=1.0)
    ziwei_sidecar_alignment: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    passed: bool = False
    failed_reasons: list[str] = Field(default_factory=list)
    metric_notes: dict[str, Any] = Field(default_factory=dict)
    chart_fact_mutation_allowed: bool = False
    boundary: str = "reading_quality_score_evaluates_outputs_without_mutating_chart_facts"

    @model_validator(mode="after")
    def _score_is_safe(self) -> "ReadingQualityScore":
        if self.chart_fact_mutation_allowed:
            raise ValueError("ReadingQualityScore cannot allow chart fact mutation")
        return self


class EngineTrainingExample(V30Model):
    version: str = "v30.engine_training_example.v1"
    example_id: str
    case_id: str
    reading_id: str
    source: MingliCaseSource = "golden"
    user_question: str
    engine_plan: dict[str, Any] = Field(default_factory=dict)
    engine_contributions: list[dict[str, Any]] = Field(default_factory=list)
    signal_registry_summary: dict[str, Any] = Field(default_factory=dict)
    verdict_summary: list[dict[str, Any]] = Field(default_factory=list)
    quality_score: ReadingQualityScore
    labels: dict[str, Any] = Field(default_factory=dict)
    trainable_targets: list[str] = Field(default_factory=list)
    blocked_targets: list[str] = Field(
        default_factory=lambda: [
            "chart_facts",
            "calendar_conversion",
            "pillar_calculation",
            "ziwei_raw_fact_without_standard",
            "llm_fact_injection",
            "production_policy_pointer",
        ]
    )
    chart_fact_mutation_allowed: bool = False
    production_policy_write_allowed: bool = False
    boundary: str = "engine_training_example_trains_weights_and_policy_candidates_not_chart_facts"

    @model_validator(mode="after")
    def _example_is_safe_training_material(self) -> "EngineTrainingExample":
        if not self.example_id.strip():
            raise ValueError("EngineTrainingExample requires example_id")
        if self.chart_fact_mutation_allowed:
            raise ValueError("EngineTrainingExample cannot allow chart fact mutation")
        if self.production_policy_write_allowed:
            raise ValueError("EngineTrainingExample cannot write production policy")
        if "chart_facts" in self.trainable_targets:
            raise ValueError("EngineTrainingExample cannot train chart_facts")
        return self


class MingliTrainingQualityGate(V30Model):
    version: str = "v30.mingli_training_quality_gate.v1"
    status: MingliGateStatus
    case_count: int = Field(default=0, ge=0)
    passed_case_count: int = Field(default=0, ge=0)
    average_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    min_quality_score: float = Field(default=0.68, ge=0.0, le=1.0)
    failed_case_ids: list[str] = Field(default_factory=list)
    examples: list[EngineTrainingExample] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    chart_fact_mutation_allowed: bool = False
    production_policy_write_allowed: bool = False
    boundary: str = "mingli_training_quality_gate_blocks_low_quality_training_without_mutating_runtime_policy"

    @model_validator(mode="after")
    def _gate_is_observational(self) -> "MingliTrainingQualityGate":
        if self.chart_fact_mutation_allowed:
            raise ValueError("MingliTrainingQualityGate cannot allow chart fact mutation")
        if self.production_policy_write_allowed:
            raise ValueError("MingliTrainingQualityGate cannot write production policy")
        return self


def load_phase1_mingli_golden_cases() -> list[MingliGoldenCase]:
    return [
        MingliGoldenCase(
            case_id="mtl-phase1-career-pressure",
            title="事业压力与资质承接",
            user_question="事业适合稳定发展还是转型突破？",
            target_domains=["career"],
            expected_verdict_domains=["career"],
            expected_advice_directions=["资质", "平台", "职责", "可交付"],
            forbidden_assertions=["必然升职", "一定发财", "无需努力"],
            required_engines=[EngineKey.BAZI, EngineKey.REALITY_PROBE],
            ziwei_matched_rule_ids=["ZW-CAREER-02"],
            min_quality_score=0.7,
        ),
        MingliGoldenCase(
            case_id="mtl-phase1-wealth-current-year",
            title="年度财务机会与分配风险",
            user_question="我今年财运如何？",
            target_domains=["wealth", "timing"],
            expected_verdict_domains=["wealth", "timing"],
            expected_advice_directions=["财务", "风险", "分配", "节奏"],
            forbidden_assertions=["保证暴富", "稳赚不赔", "立刻投资"],
            required_engines=[EngineKey.BAZI, EngineKey.ZIWEI, EngineKey.REALITY_PROBE],
            ziwei_matched_rule_ids=["ZW-WEALTH-02", "ZW-WEALTH-05"],
            min_quality_score=0.68,
        ),
        MingliGoldenCase(
            case_id="mtl-phase1-relationship-boundary",
            title="关系反复与边界校准",
            user_question="感情关系里最容易反复的问题是什么？",
            target_domains=["relationship"],
            expected_verdict_domains=["relationship"],
            expected_advice_directions=["边界", "沟通", "反复", "节奏"],
            forbidden_assertions=["必然离婚", "一定复合", "对方绝对有问题"],
            required_engines=[EngineKey.BAZI, EngineKey.REALITY_PROBE],
            ziwei_matched_rule_ids=["ZW-REL-03"],
            min_quality_score=0.68,
        ),
    ]


def evaluate_reading_quality(
    *,
    golden_case: MingliGoldenCase,
    multi_engine_result: MultiEngineRunResult,
    runtime_payload: dict[str, Any],
) -> ReadingQualityScore:
    verdicts = _verdicts(runtime_payload)
    expected_domains = set(golden_case.expected_verdict_domains)
    verdict_domains = {str(row.get("domain") or "") for row in verdicts}
    expected_engine_values = {engine.value for engine in golden_case.required_engines}
    audit_by_engine = {row.engine.value: row for row in multi_engine_result.audit}
    engine_signal_coverage = _ratio(
        sum(1 for engine in expected_engine_values if engine in audit_by_engine and _engine_has_material(audit_by_engine[engine])),
        len(expected_engine_values),
    )
    verdict_domain_alignment = _ratio(len(expected_domains & verdict_domains), len(expected_domains))
    evidence_binding = _ratio(sum(1 for row in verdicts if row.get("evidence_refs")), len(verdicts))
    advice_actionability = _ratio(sum(1 for row in verdicts if _list(row.get("advice_points"))), len(verdicts))
    surface_text = _surface_text(runtime_payload, verdicts)
    forbidden_hits = [term for term in golden_case.forbidden_assertions if term and term in surface_text]
    forbidden_assertion_safety = 0.0 if forbidden_hits else 1.0
    template_hits = [term for term in _TEMPLATE_RISK_TERMS if term in surface_text]
    overclaim_hits = [term for term in _OVERCLAIM_RISK_TERMS if term in surface_text]
    template_risk = min(1.0, len(template_hits) / 4)
    overclaim_risk = min(1.0, len(overclaim_hits) / 4)
    reality_probe_alignment = 1.0 if _engine_probe_count(multi_engine_result, EngineKey.REALITY_PROBE) > 0 else 0.0
    ziwei_sidecar_alignment = _ziwei_alignment(golden_case, multi_engine_result)
    overall_score = round(
        engine_signal_coverage * 0.16
        + verdict_domain_alignment * 0.18
        + evidence_binding * 0.16
        + advice_actionability * 0.16
        + forbidden_assertion_safety * 0.12
        + (1.0 - template_risk) * 0.08
        + (1.0 - overclaim_risk) * 0.08
        + reality_probe_alignment * 0.04
        + ziwei_sidecar_alignment * 0.02,
        3,
    )
    failed_reasons = []
    if overall_score < golden_case.min_quality_score:
        failed_reasons.append("overall_score_below_case_threshold")
    if evidence_binding < golden_case.min_evidence_binding:
        failed_reasons.append("evidence_binding_below_case_threshold")
    if advice_actionability < golden_case.min_advice_actionability:
        failed_reasons.append("advice_actionability_below_case_threshold")
    if forbidden_hits:
        failed_reasons.append("forbidden_assertion_hit")
    if overclaim_risk >= 0.5:
        failed_reasons.append("overclaim_risk_high")
    return ReadingQualityScore(
        case_id=golden_case.case_id,
        reading_id=multi_engine_result.reading_id,
        engine_signal_coverage=engine_signal_coverage,
        verdict_domain_alignment=verdict_domain_alignment,
        evidence_binding=evidence_binding,
        advice_actionability=advice_actionability,
        forbidden_assertion_safety=forbidden_assertion_safety,
        template_risk=template_risk,
        overclaim_risk=overclaim_risk,
        reality_probe_alignment=reality_probe_alignment,
        ziwei_sidecar_alignment=ziwei_sidecar_alignment,
        overall_score=overall_score,
        passed=not failed_reasons,
        failed_reasons=failed_reasons,
        metric_notes={
            "expected_domains": sorted(expected_domains),
            "verdict_domains": sorted(verdict_domains),
            "forbidden_hits": forbidden_hits,
            "template_hits": template_hits,
            "overclaim_hits": overclaim_hits,
        },
    )


def build_engine_training_example(
    *,
    golden_case: MingliGoldenCase,
    multi_engine_result: MultiEngineRunResult,
    runtime_payload: dict[str, Any],
    example_id: str | None = None,
) -> EngineTrainingExample:
    quality = evaluate_reading_quality(
        golden_case=golden_case,
        multi_engine_result=multi_engine_result,
        runtime_payload=runtime_payload,
    )
    return EngineTrainingExample(
        example_id=example_id or f"{golden_case.case_id}:{multi_engine_result.reading_id}:engine-training",
        case_id=golden_case.case_id,
        reading_id=multi_engine_result.reading_id,
        source=golden_case.source,
        user_question=golden_case.user_question,
        engine_plan=multi_engine_result.plan.model_dump(mode="json"),
        engine_contributions=[
            {
                "engine": row.engine.value,
                "mode": row.mode.value,
                "status": row.status.value,
                "fact_count": row.fact_count,
                "feature_count": row.feature_count,
                "signal_count": row.signal_count,
                "registered_signal_count": row.registered_signal_count,
                "probe_candidate_count": row.probe_candidate_count,
            }
            for row in multi_engine_result.audit
        ],
        signal_registry_summary={
            "version": "v30.engine_training_signal_registry_summary.v1",
            "signal_count": len(multi_engine_result.signal_registry.signals),
            "validation_issue_count": len(multi_engine_result.signal_registry.validation_issues),
            "source_type_counts": _source_type_counts(multi_engine_result),
            "boundary": "engine_training_example_summarizes_signal_registry_without_mutating_signals",
        },
        verdict_summary=_verdict_summary(runtime_payload),
        quality_score=quality,
        labels={
            "overall_quality": quality.overall_score,
            "evidence_binding": quality.evidence_binding,
            "advice_actionability": quality.advice_actionability,
            "template_risk": quality.template_risk,
            "overclaim_risk": quality.overclaim_risk,
            "domain_alignment": quality.verdict_domain_alignment,
        },
        trainable_targets=[
            "engine_signal_weight",
            "decision_candidate_threshold",
            "verdict_domain_alignment",
            "advice_actionability",
            "reality_probe_question_policy",
            "ziwei_bazi_alignment_quality",
            "llm_expression_quality",
        ],
    )


def build_mingli_training_quality_gate(
    examples: list[EngineTrainingExample],
    *,
    min_case_count: int = 3,
    min_average_quality: float = 0.68,
) -> MingliTrainingQualityGate:
    case_count = len(examples)
    passed = [example for example in examples if example.quality_score.passed]
    failed = [example for example in examples if not example.quality_score.passed]
    average = round(sum(example.quality_score.overall_score for example in examples) / max(1, case_count), 3) if examples else 0.0
    recommendations = []
    if case_count < min_case_count:
        recommendations.append("补足 golden case 数量后再进入训练晋级。")
    if average < min_average_quality:
        recommendations.append("先修复低分案例的证据链、建议行动性和过度断言风险。")
    if failed:
        recommendations.append("失败案例必须进入 replay queue，不能直接提升策略。")
    status: MingliGateStatus = "passed"
    if case_count < min_case_count or average < min_average_quality or failed:
        status = "blocked"
    return MingliTrainingQualityGate(
        status=status,
        case_count=case_count,
        passed_case_count=len(passed),
        average_quality_score=average,
        min_quality_score=min_average_quality,
        failed_case_ids=[example.case_id for example in failed],
        examples=examples,
        recommendations=recommendations or ["Phase 1 gate passed; eligible for synthetic replay, not production pointer promotion."],
    )


_TEMPLATE_RISK_TERMS = ("evidence-bound", "debug", "fallback", "TODO", "LLM 返回", "工程", "section")
_OVERCLAIM_RISK_TERMS = ("必然", "一定", "绝对", "保证", "稳赚")


def _verdicts(runtime_payload: dict[str, Any]) -> list[dict[str, Any]]:
    central = _dict(_dict(_dict(runtime_payload.get("question_plan")).get("policy_effect")).get("central_reading_state"))
    decision = _dict(central.get("decision_result"))
    return [row for row in _list(decision.get("verdicts")) if isinstance(row, dict)]


def _verdict_summary(runtime_payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "verdict_id": str(row.get("verdict_id") or ""),
            "domain": str(row.get("domain") or ""),
            "assertion_level": str(row.get("assertion_level") or ""),
            "headline": str(row.get("headline") or ""),
            "evidence_count": len(_list(row.get("evidence_refs"))),
            "advice_count": len(_list(row.get("advice_points"))),
        }
        for row in _verdicts(runtime_payload)
    ]


def _surface_text(runtime_payload: dict[str, Any], verdicts: list[dict[str, Any]]) -> str:
    central = _dict(_dict(_dict(runtime_payload.get("question_plan")).get("policy_effect")).get("central_reading_state"))
    synthesis = _dict(central.get("final_synthesis"))
    pieces = [
        *(str(row.get("headline") or "") for row in verdicts),
        *(str(item) for row in verdicts for item in _list(row.get("advice_points"))),
        str(synthesis.get("conclusion") or ""),
        str(synthesis.get("advice") or ""),
    ]
    return "\n".join(pieces)


def _engine_has_material(audit_entry: Any) -> bool:
    return bool(audit_entry.signal_count or audit_entry.fact_count or audit_entry.feature_count or audit_entry.probe_candidate_count)


def _engine_probe_count(result: MultiEngineRunResult, engine: EngineKey) -> int:
    return sum(row.probe_candidate_count for row in result.audit if row.engine == engine)


def _ziwei_alignment(golden_case: MingliGoldenCase, result: MultiEngineRunResult) -> float:
    ziwei_entries = [row for row in result.audit if row.engine == EngineKey.ZIWEI]
    if not ziwei_entries:
        return 0.0 if EngineKey.ZIWEI in golden_case.required_engines else 1.0
    signal_count = sum(row.signal_count for row in ziwei_entries)
    probe_count = sum(row.probe_candidate_count for row in ziwei_entries)
    if golden_case.ziwei_matched_rule_ids:
        return 1.0 if signal_count >= 1 else 0.0
    return 1.0 if signal_count == 0 and probe_count >= 0 else 0.5


def _source_type_counts(result: MultiEngineRunResult) -> dict[str, int]:
    counts: dict[str, int] = {}
    for signal in result.signal_registry.signals:
        key = signal.source_type.value
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 1.0
    return round(max(0.0, min(1.0, numerator / denominator)), 3)


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []
