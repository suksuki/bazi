from __future__ import annotations

from hashlib import sha256
from typing import Any, Literal

from pydantic import Field

from core.contracts.base import V50Model
from core.mingli_agent.contracts import (
    DiscriminatingProbe,
    DomainCausalReading,
    MingliCognitiveRecord,
)


BenchmarkConfidence = Literal["low", "medium", "high", "unresolved"]


class BenchmarkHypothesis(V50Model):
    name: str
    thesis: str
    confidence: BenchmarkConfidence = "unresolved"
    supporting_evidence_refs: list[str] = Field(default_factory=list)
    counter_evidence_refs: list[str] = Field(default_factory=list)
    success_conditions: list[str] = Field(default_factory=list)
    failure_conditions: list[str] = Field(default_factory=list)


class BenchmarkConditionalRole(V50Model):
    candidate: str
    role: str
    conditions: list[str] = Field(default_factory=list)
    invalidating_conditions: list[str] = Field(default_factory=list)
    rationale: str = ""
    evidence_refs: list[str] = Field(default_factory=list)


class BenchmarkDomainReasoning(V50Model):
    causal_chain: list[str] = Field(default_factory=list)
    stable_tendencies: list[str] = Field(default_factory=list)
    favorable_conditions: list[str] = Field(default_factory=list)
    adverse_conditions: list[str] = Field(default_factory=list)
    prior_directions: list[str] = Field(default_factory=list)
    timing_note: str = ""
    unknowns: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class BenchmarkProbe(V50Model):
    question: str
    purpose: str
    options: list[str] = Field(default_factory=list)
    distinguishes: list[str] = Field(default_factory=list)


class CognitiveBenchmarkReading(V50Model):
    independent_first_look: str
    chart_center_of_gravity: str
    primary_hypothesis: BenchmarkHypothesis
    strongest_alternative: BenchmarkHypothesis
    why_primary_over_alternative: list[str]
    main_work_path: str
    secondary_or_blocked_paths: list[str]
    critical_nodes: list[str]
    pivot_candidates: list[str]
    bridge_or_support_candidates: list[str]
    body_function_relation: str
    conditional_useful_roles: list[BenchmarkConditionalRole]
    conditional_harmful_roles: list[BenchmarkConditionalRole]
    stable_portrait: list[str]
    hidden_attribute_candidates: list[str]
    career_reasoning: BenchmarkDomainReasoning
    wealth_reasoning: BenchmarkDomainReasoning
    prior_predictions: list[str]
    falsifiers: list[str]
    discriminating_probe: BenchmarkProbe
    known_uncertainties: list[str]
    evidence_refs: list[str]

    def cognitive_signature(self) -> str:
        material = "\n".join(
            [
                self.chart_center_of_gravity,
                self.primary_hypothesis.name,
                self.primary_hypothesis.thesis,
                self.main_work_path,
                self.body_function_relation,
                *self.critical_nodes,
                *self.pivot_candidates,
            ]
        )
        return sha256(material.encode("utf-8")).hexdigest()[:20]


def project_cognitive_record(
    *,
    record: MingliCognitiveRecord,
    career: DomainCausalReading | None,
    wealth: DomainCausalReading | None,
) -> CognitiveBenchmarkReading:
    cognition = record.cognition
    selected = next(
        (row for row in cognition.hypotheses if row.hypothesis_id == cognition.selected_hypothesis_id),
        cognition.hypotheses[0],
    )
    alternative = next(
        (row for row in cognition.hypotheses if row.hypothesis_id != selected.hypothesis_id),
        None,
    )
    if alternative is None:
        alternative_payload = BenchmarkHypothesis(
            name="未形成可靠替代假设",
            thesis="当前输出没有形成可比较的第二假设。",
            confidence="unresolved",
        )
    else:
        alternative_payload = _hypothesis(alternative)

    useful_roles: list[BenchmarkConditionalRole] = []
    harmful_roles: list[BenchmarkConditionalRole] = []
    for row in cognition.useful_god_reasoning:
        useful_roles.append(
            BenchmarkConditionalRole(
                candidate=row.candidate,
                role=row.role,
                conditions=row.applicable_conditions,
                invalidating_conditions=row.invalidating_conditions,
                rationale=row.why_useful,
                evidence_refs=row.evidence_refs,
            )
        )
        if row.when_harmful or row.invalidating_conditions:
            harmful_roles.append(
                BenchmarkConditionalRole(
                    candidate=row.candidate,
                    role=f"conditional_harm:{row.role}",
                    conditions=row.invalidating_conditions,
                    invalidating_conditions=row.applicable_conditions,
                    rationale=row.when_harmful,
                    evidence_refs=_unique([*row.evidence_refs, *row.counter_evidence_refs]),
                )
            )

    falsifiers = _unique(
        [
            *selected.failure_conditions,
            *(item for assertion in cognition.portrait for item in assertion.falsifiers),
            *(prediction.disconfirming_answer for prediction in cognition.prior_predictions),
        ]
    )
    critical_nodes = _unique(
        [
            *cognition.work_path.source,
            *cognition.work_path.transformations,
            *cognition.work_path.target,
            *(ref for row in cognition.useful_god_reasoning for ref in row.node_refs),
        ]
    )
    comparison = _unique(
        [
            *cognition.work_path.comparison_reasons,
            *(f"{item.name}: {item.rejection_reason}" for item in cognition.hypotheses if item.rejection_reason),
        ]
    )
    return CognitiveBenchmarkReading(
        independent_first_look=cognition.first_look,
        chart_center_of_gravity=cognition.whole_chart_thesis,
        primary_hypothesis=_hypothesis(selected),
        strongest_alternative=alternative_payload,
        why_primary_over_alternative=comparison or ["当前记录未显式保存假设比较理由。"],
        main_work_path=cognition.work_path.path_statement,
        secondary_or_blocked_paths=_unique(
            [*cognition.work_path.competing_path_refs, *cognition.work_path.failure_conditions]
        ),
        critical_nodes=critical_nodes,
        pivot_candidates=list(cognition.work_path.transformations),
        bridge_or_support_candidates=_unique(
            [row.candidate for row in cognition.useful_god_reasoning]
        ),
        body_function_relation=cognition.work_path.body_function_relation,
        conditional_useful_roles=useful_roles,
        conditional_harmful_roles=harmful_roles,
        stable_portrait=[row.claim for row in cognition.portrait],
        hidden_attribute_candidates=[
            row.claim
            for row in cognition.portrait
            if row.epistemic_status != "supported" or row.conditions
        ],
        career_reasoning=_domain(career),
        wealth_reasoning=_domain(wealth),
        prior_predictions=[row.claim for row in cognition.prior_predictions],
        falsifiers=falsifiers,
        discriminating_probe=_probe(cognition.next_probe),
        known_uncertainties=_unique(
            [
                *cognition.unresolved_questions,
                *([] if career is None else career.unknowns),
                *([] if wealth is None else wealth.unknowns),
            ]
        ),
        evidence_refs=_unique(
            [
                *cognition.evidence_refs,
                *([] if career is None else [ref for row in career.assertions for ref in row.evidence_refs]),
                *([] if wealth is None else [ref for row in wealth.assertions for ref in row.evidence_refs]),
            ]
        ),
    )


def benchmark_prompt(
    *,
    lane_label: str,
    chart_payload: dict[str, Any],
    context_payload: dict[str, Any] | None = None,
) -> str:
    context = context_payload or {}
    return f"""
你正在参加一项盲测。请独立完成一份专业八字整盘认知，不要写产品宣传或安全套话。

任务：
1. 先指出盘面第一重心，再形成主假设与一个真正有竞争力的替代假设。
2. 比较两者，解释为何当前优先 A 而不是 B。
3. 形成主做功、次要/受阻路径、体用关系和条件性用忌。
4. 在整盘认知基础上分别推演事业与财富因果链。
5. 必须给出先验预测、可推翻条件、鉴别性问题和已知未知。
6. 不能使用任何现实职业、性格、财富或经历信息；不能向用户索取本应先断的答案。
7. 事实只允许来自本题输入。解释性判断可以由你形成，但必须与事实区分。

Blind protocol: {lane_label}

命盘输入：
{chart_payload}

本 Lane 允许的附加上下文：
{context}
""".strip()


def direct_power_user_prompt(*, chart_payload: dict[str, Any]) -> str:
    """A strong one-shot request without DeepBazi's internal cognition protocol."""

    return f"""
请根据下面已经确认的四柱，独立完成一份专业、具体、可核查的八字整盘分析。

回答需要覆盖：命局重心、当前最合理的主解释、一个真正有竞争力的替代解释、主要做功、条件性用忌、事业与财富的先验判断、可推翻这些判断的信号，以及一个最有鉴别力的现实问题。

请区分原局事实、推导判断、假设、流年条件和提问。不要使用现实职业、收入、性格自述或已经发生的事件来倒推结论；不知道的部分明确保留不确定性。

命盘输入：
{chart_payload}
""".strip()


def _hypothesis(row: Any) -> BenchmarkHypothesis:
    return BenchmarkHypothesis(
        name=row.name,
        thesis=row.thesis,
        confidence=row.confidence,
        supporting_evidence_refs=row.supporting_evidence_refs,
        counter_evidence_refs=row.counter_evidence_refs,
        success_conditions=row.success_conditions,
        failure_conditions=row.failure_conditions,
    )


def _domain(reading: DomainCausalReading | None) -> BenchmarkDomainReasoning:
    if reading is None:
        return BenchmarkDomainReasoning(unknowns=["该 Lane 未形成独立领域因果推理。"])
    return BenchmarkDomainReasoning(
        causal_chain=reading.causal_chain,
        stable_tendencies=reading.stable_tendencies,
        favorable_conditions=_unique([*reading.favorable_environments, *reading.opportunity_conditions]),
        adverse_conditions=_unique([*reading.adverse_environments, *reading.risk_conditions]),
        prior_directions=reading.prior_directions,
        timing_note=reading.timing_note,
        unknowns=reading.unknowns,
        evidence_refs=_unique([ref for row in reading.assertions for ref in row.evidence_refs]),
    )


def _probe(probe: DiscriminatingProbe) -> BenchmarkProbe:
    return BenchmarkProbe(
        question=probe.question,
        purpose=probe.purpose,
        options=probe.options,
        distinguishes=probe.distinguishes_hypothesis_refs,
    )


def _unique(values: list[str]) -> list[str]:
    output: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in output:
            output.append(text)
    return output
