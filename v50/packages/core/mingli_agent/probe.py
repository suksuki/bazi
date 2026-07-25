from __future__ import annotations

import re
from typing import Literal

from pydantic import Field

from core.contracts.base import V50Model
from core.life_domains import LifeDomain
from core.mingli_agent.contracts import DiscriminatingProbe, MingliCognitiveRecord


ExperienceMode = Literal["guest", "member", "practitioner", "research"]
ProbeScenario = Literal["recognition", "domain", "timing", "falsification", "decision"]
BeliefDelta = Literal["strengthen", "weaken", "unchanged"]
EvidenceKind = Literal["behavior", "historical_timeline", "counter_evidence", "professional_observation"]
InformationBand = Literal["low", "medium", "high"]


class ProbeOption(V50Model):
    option_id: str
    label: str
    hypothesis_updates: dict[str, BeliefDelta] = Field(default_factory=dict)
    assertion_updates: dict[str, BeliefDelta] = Field(default_factory=dict)
    hidden_attribute_observations: dict[str, str] = Field(default_factory=dict)
    evidence_strength: Literal["weak", "medium", "strong"] = "medium"


class ProbeInformationValue(V50Model):
    discrimination: InformationBand
    observability: InformationBand
    falsifiability: InformationBand
    source_quality: InformationBand
    role_fit: InformationBand
    overall: InformationBand
    reasons: list[str] = Field(default_factory=list)


class ProbePlan(V50Model):
    version: str = "deepbazi.probe_plan.v2"
    plan_id: str
    source_probe_id: str
    role_mode: ExperienceMode
    scenario: ProbeScenario
    domain: LifeDomain
    question: str
    purpose: str
    options: list[ProbeOption]
    target_hypothesis_ids: list[str]
    target_assertion_ids: list[str] = Field(default_factory=list)
    expected_information_gain: Literal["low", "medium", "high"]
    information_value: ProbeInformationValue
    evidence_kind: EvidenceKind = "behavior"
    hidden_attribute_targets: list[str] = Field(default_factory=list)
    time_anchors: list[int] = Field(default_factory=list)
    response_shape: Literal["single_choice", "timeline_choice"] = "single_choice"
    professional_note: str = ""
    claim_refs: list[str] = Field(default_factory=list)
    allowed_case_updates: list[str] = Field(default_factory=lambda: ["hypothesis_belief", "case_assertion_status", "hidden_attribute_belief", "case_revision"])
    forbidden_updates: list[str] = Field(default_factory=lambda: ["chart_facts", "global_theory", "runtime_rules", "model_weights"])


class ProbePlanner:
    """Projects one epistemic probe into the active user task without new Mingli judgment."""

    def plan(
        self,
        *,
        record: MingliCognitiveRecord,
        role_mode: ExperienceMode,
        scenario: ProbeScenario = "recognition",
        domain: LifeDomain = LifeDomain.WHOLE_CHART,
        source_override: DiscriminatingProbe | None = None,
    ) -> ProbePlan:
        domain = LifeDomain(domain)
        exploration = record.domain_explorations.get(domain)
        source = source_override or (exploration.reading.next_probe if exploration and exploration.reading.next_probe else record.cognition.next_probe)
        hypotheses = {item.hypothesis_id: item for item in record.cognition.hypotheses}
        domain_assertions = exploration.reading.assertions if exploration else []
        assertion_ids = {item.assertion_id for item in domain_assertions}
        assertion_targets = [item for item in source.distinguishes_hypothesis_refs if item in assertion_ids]
        if domain is not LifeDomain.WHOLE_CHART and not assertion_targets:
            assertion_targets = [item.assertion_id for item in domain_assertions[:2]]
        targets: list[str] = []
        if not assertion_targets:
            targets = [item for item in source.distinguishes_hypothesis_refs if item in hypotheses]
            if record.cognition.selected_hypothesis_id not in targets:
                targets.insert(0, record.cognition.selected_hypothesis_id)
            alternatives = [item.hypothesis_id for item in record.cognition.hypotheses if item.hypothesis_id != targets[0]]
            if len(targets) < 2 and alternatives:
                targets.append(alternatives[0])
            targets = targets[:3]

        labels = [_project_option_label(label, role_mode=role_mode) for label in source.options[:3]]
        attribute_targets = _hidden_attribute_targets(scenario=scenario, domain=domain)
        options = [
            ProbeOption(
                option_id=f"{source.probe_id}:option:{index + 1}",
                label=label,
                hypothesis_updates=_option_updates(index=index, target_ids=targets, label=label) if targets else {},
                assertion_updates=_option_updates(index=index, target_ids=assertion_targets, label=label) if assertion_targets else {},
                hidden_attribute_observations=_attribute_observations(index=index, label=label, targets=attribute_targets),
                evidence_strength=_option_evidence_strength(index=index, label=label, scenario=scenario),
            )
            for index, label in enumerate(labels)
        ]
        assertion_names = {item.assertion_id: item.claim for item in domain_assertions}
        primary_name = hypotheses[targets[0]].name if targets else assertion_names.get(assertion_targets[0], "当前领域判断") if assertion_targets else "当前主假设"
        alternative_name = hypotheses[targets[1]].name if len(targets) > 1 else assertion_names.get(assertion_targets[1], "另一种领域解释") if len(assertion_targets) > 1 else "替代解释"
        question, purpose, note = _project_copy(
            role_mode=role_mode,
            scenario=scenario,
            source_question=source.question,
            source_purpose=source.purpose,
            primary_name=primary_name,
            alternative_name=alternative_name,
            target_kind="assertion" if assertion_targets else "hypothesis",
        )
        time_anchors = _extract_years(" ".join([source.question, *source.options]))
        evidence_kind: EvidenceKind = (
            "historical_timeline" if scenario == "timing" or time_anchors
            else "counter_evidence" if scenario == "falsification"
            else "professional_observation" if role_mode in {"practitioner", "research"}
            else "behavior"
        )
        information_value = _probe_information_value(
            role_mode=role_mode,
            question=question,
            options=options,
            target_count=len(targets or assertion_targets),
            evidence_kind=evidence_kind,
            scenario=scenario,
            time_anchors=time_anchors,
        )
        return ProbePlan(
            plan_id=f"probe-plan:{record.case_id}:{source.probe_id}:{role_mode}:{scenario}:{domain.value}",
            source_probe_id=source.probe_id,
            role_mode=role_mode,
            scenario=scenario,
            domain=domain,
            question=question,
            purpose=purpose,
            options=options,
            target_hypothesis_ids=targets,
            target_assertion_ids=assertion_targets,
            expected_information_gain=information_value.overall,
            information_value=information_value,
            evidence_kind=evidence_kind,
            hidden_attribute_targets=attribute_targets,
            time_anchors=time_anchors,
            response_shape="timeline_choice" if evidence_kind == "historical_timeline" else "single_choice",
            professional_note=note,
            claim_refs=[item.prediction_id for item in record.cognition.prior_predictions],
        )


def _probe_information_value(
    *,
    role_mode: ExperienceMode,
    question: str,
    options: list[ProbeOption],
    target_count: int,
    evidence_kind: EvidenceKind,
    scenario: ProbeScenario,
    time_anchors: list[int],
) -> ProbeInformationValue:
    update_signatures = {
        tuple(sorted([*option.hypothesis_updates.items(), *option.assertion_updates.items()]))
        for option in options
    }
    discrimination: InformationBand = (
        "high" if target_count >= 2 and len(update_signatures) >= 2
        else "medium" if target_count >= 1 and len(update_signatures) >= 2
        else "low"
    )
    public_jargon = ("格局", "用神", "做功", "十神", "从格", "制杀", "命宫", "四化", "AST", "节点")
    has_public_jargon = role_mode in {"guest", "member"} and any(token in question for token in public_jargon)
    unclear = any(token in question for token in ("你觉得呢", "是否准确", "准不准"))
    observability: InformationBand = "low" if has_public_jargon or unclear else "high" if len(options) >= 2 else "medium"

    negative_tokens = ("没有发生", "没有明显", "未发生", "无明显", "两者都不是", "不符合")
    has_disconfirming_option = any(any(token in option.label for token in negative_tokens) for option in options)
    falsifiability: InformationBand = (
        "high" if has_disconfirming_option or scenario == "falsification"
        else "medium" if len(update_signatures) >= 2
        else "low"
    )
    source_quality: InformationBand = (
        "high" if evidence_kind == "historical_timeline" and bool(time_anchors)
        else "medium" if evidence_kind in {"counter_evidence", "professional_observation"}
        else "low"
    )
    role_fit: InformationBand = (
        "low" if has_public_jargon
        else "high" if role_mode in {"guest", "member"} or evidence_kind == "professional_observation"
        else "medium"
    )
    overall: InformationBand = (
        "high"
        if discrimination == "high" and observability != "low" and falsifiability in {"medium", "high"}
        else "medium"
        if discrimination in {"medium", "high"} and observability != "low"
        else "low"
    )
    reasons = [
        f"targets:{target_count}",
        f"distinct_update_paths:{len(update_signatures)}",
        f"evidence_kind:{evidence_kind}",
        f"role_mode:{role_mode}",
    ]
    if has_disconfirming_option:
        reasons.append("explicit_disconfirming_option")
    if time_anchors:
        reasons.append(f"historical_anchors:{','.join(map(str, time_anchors))}")
    if has_public_jargon:
        reasons.append("public_jargon_penalty")
    return ProbeInformationValue(
        discrimination=discrimination,
        observability=observability,
        falsifiability=falsifiability,
        source_quality=source_quality,
        role_fit=role_fit,
        overall=overall,
        reasons=reasons,
    )


def _hidden_attribute_targets(*, scenario: ProbeScenario, domain: LifeDomain) -> list[str]:
    if scenario == "timing":
        return ["timing_response_pattern"]
    if scenario == "decision":
        return ["decision_style"]
    if scenario == "falsification":
        return ["manifestation_consistency"]
    domain_targets = {
        LifeDomain.CAREER: "execution_conversion",
        LifeDomain.WEALTH: "resource_stewardship",
        LifeDomain.RELATIONSHIP: "conflict_response",
        LifeDomain.FAMILY: "family_boundary_response",
        LifeDomain.HEALTH_VITALITY: "recovery_pattern",
        LifeDomain.SOCIAL_NETWORK: "cooperation_response",
        LifeDomain.MIGRATION_ENVIRONMENT: "environment_adaptation",
        LifeDomain.TALENT_LEARNING: "learning_conversion",
        LifeDomain.LIFE_TIMING: "timing_response_pattern",
    }
    return [domain_targets.get(domain, "pressure_response_pattern")]


def _attribute_observations(*, index: int, label: str, targets: list[str]) -> dict[str, str]:
    uncertain_tokens = ("不确定", "难以", "都有", "两者", "混合", "记不清")
    negative_tokens = ("没有发生", "没有明显", "未发生", "无明显")
    if any(token in label for token in uncertain_tokens + negative_tokens):
        return {}
    return {target: _attribute_state(index=index, label=label) for target in targets}


def _attribute_state(*, index: int, label: str) -> str:
    if index == 0:
        return f"primary:{label}"
    if index == 1:
        return f"alternative:{label}"
    return "mixed_or_uncertain"


def _option_evidence_strength(*, index: int, label: str, scenario: ProbeScenario) -> Literal["weak", "medium", "strong"]:
    if any(token in label for token in ("没有发生", "没有明显", "未发生", "无明显")):
        return "strong"
    if any(token in label for token in ("不确定", "难以", "都有", "两者", "混合", "记不清")):
        return "weak"
    if scenario == "timing":
        return "strong"
    return "medium" if index < 2 else "weak"


def _extract_years(text: str) -> list[int]:
    return list(dict.fromkeys(int(item) for item in re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", text)))[:4]


def _option_updates(*, index: int, target_ids: list[str], label: str = "") -> dict[str, BeliefDelta]:
    if not target_ids:
        return {}
    output: dict[str, BeliefDelta] = {item: "unchanged" for item in target_ids}
    if any(token in label for token in ("没有发生", "没有明显", "未发生", "无明显")):
        output = {item: "weaken" for item in target_ids}
    elif index == 0:
        output[target_ids[0]] = "strengthen"
        for item in target_ids[1:]:
            output[item] = "weaken"
    elif index == 1 and len(target_ids) > 1:
        output[target_ids[0]] = "weaken"
        output[target_ids[1]] = "strengthen"
    return output


def _project_option_label(label: str, *, role_mode: ExperienceMode) -> str:
    if role_mode not in {"guest", "member"}:
        return label
    text = label
    while "（" in text and "）" in text and text.index("（") < text.index("）"):
        start = text.index("（")
        end = text.index("）", start)
        text = f"{text[:start]}{text[end + 1:]}"
    while "(" in text and ")" in text and text.index("(") < text.index(")"):
        start = text.index("(")
        end = text.index(")", start)
        text = f"{text[:start]}{text[end + 1:]}"
    return text.strip(" ：:，,；;") or label


def _project_copy(
    *,
    role_mode: ExperienceMode,
    scenario: ProbeScenario,
    source_question: str,
    source_purpose: str,
    primary_name: str,
    alternative_name: str,
    target_kind: Literal["hypothesis", "assertion"],
) -> tuple[str, str, str]:
    if role_mode == "guest":
        if scenario in {"domain", "timing"}:
            public_question = source_question.replace("命主", "你").replace("您", "你")
            return (
                public_question,
                "这能帮助 Abu 判断当前专题里的两种解释，哪一种更接近你的真实经历。",
                "",
            )
        return (
            "遇到这类压力时，哪一种更像你平时真实的处理方式？",
            "你的选择只用来判断 Abu 第一眼抓到的方向是否贴近你。",
            "",
        )
    if role_mode == "member":
        return (source_question, "这会帮助 Abu 区分你的稳定模式和当前情境反应。", "")
    if role_mode == "practitioner":
        update_note = "选择结果只更新当前案例的领域断言，不修改整盘假设或原局事实。" if target_kind == "assertion" else "选择结果只更新当前案例的假设权重，不修改原局事实。"
        return (
            f"作为案例鉴别，请确认：{source_question}",
            f"专业鉴别：区分“{primary_name}”与“{alternative_name}”。{source_purpose}",
            update_note,
        )
    research_target = "领域断言" if target_kind == "assertion" else "案例假设"
    return (
        f"在案例证据中，哪项表现更接近事实？用于检验“{primary_name}”是否应让位于“{alternative_name}”。",
        f"反证任务：{source_purpose}",
        f"本轮只校准{research_target}。请保留不符合两者的异常表现，作为独立反例，而不是强行归类。",
    )
