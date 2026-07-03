from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from v30.contracts import RoleKey, V30Model
from v30.engines.contracts import EngineKey
from v30.training.mingli_training import (
    EngineTrainingExample,
    MingliGoldenCase,
    MingliTrainingQualityGate,
    build_mingli_training_quality_gate,
    load_phase1_mingli_golden_cases,
)


MINGLI_TRAINING_PHASE2_VERSION = "v30.mingli_training_phase2.v1"

ReplayPriority = Literal["low", "medium", "high", "critical"]
LabelDecision = Literal["accept", "revise", "reject", "needs_more_context"]
Phase2GateStatus = Literal["passed", "blocked", "review"]


class MingliReplayQueueItem(V30Model):
    version: str = "v30.mingli_replay_queue_item.v1"
    replay_id: str
    case_id: str
    reading_id: str
    example_id: str
    failed_reasons: list[str] = Field(default_factory=list)
    priority: ReplayPriority = "medium"
    rerun_plan: list[str] = Field(default_factory=list)
    trainable_targets: list[str] = Field(default_factory=list)
    blocked_targets: list[str] = Field(default_factory=list)
    promotion_blocked: bool = True
    boundary: str = "mingli_replay_queue_routes_failed_examples_without_promoting_policy"

    @model_validator(mode="after")
    def _replay_item_requires_failure_material(self) -> "MingliReplayQueueItem":
        if not self.failed_reasons:
            raise ValueError("MingliReplayQueueItem requires failed_reasons")
        if not self.promotion_blocked:
            raise ValueError("Replay queue item must block promotion")
        return self


class PractitionerLabel(V30Model):
    version: str = "v30.practitioner_label.v1"
    label_id: str
    case_id: str
    reading_id: str
    role_key: RoleKey = "practitioner"
    decision: LabelDecision = "accept"
    accepted_verdict_domains: list[str] = Field(default_factory=list)
    rejected_verdict_domains: list[str] = Field(default_factory=list)
    advice_tags: list[str] = Field(default_factory=list)
    quality_overrides: dict[str, float] = Field(default_factory=dict)
    correction_notes: list[str] = Field(default_factory=list)
    chart_fact_mutation_allowed: bool = False
    production_policy_write_allowed: bool = False
    boundary: str = "practitioner_label_trains_policy_projection_not_chart_facts"

    @model_validator(mode="after")
    def _label_is_training_projection_only(self) -> "PractitionerLabel":
        if self.role_key not in {"practitioner", "admin", "lab"}:
            raise ValueError("PractitionerLabel requires practitioner/admin/lab role")
        if not self.accepted_verdict_domains and self.decision == "accept":
            raise ValueError("Accepted PractitionerLabel requires accepted_verdict_domains")
        if self.chart_fact_mutation_allowed:
            raise ValueError("PractitionerLabel cannot allow chart fact mutation")
        if self.production_policy_write_allowed:
            raise ValueError("PractitionerLabel cannot write production policy")
        return self


class PractitionerLabelProjection(V30Model):
    version: str = "v30.practitioner_label_projection.v1"
    projection_id: str
    case_id: str
    reading_id: str
    label_count: int = Field(default=0, ge=0)
    accepted_domain_count: int = Field(default=0, ge=0)
    rejected_domain_count: int = Field(default=0, ge=0)
    label_alignment_score: float = Field(default=0.0, ge=0.0, le=1.0)
    quality_overrides: dict[str, float] = Field(default_factory=dict)
    trainable_targets: list[str] = Field(default_factory=list)
    blocked_targets: list[str] = Field(default_factory=lambda: ["chart_facts", "production_policy_pointer"])
    chart_fact_mutation_allowed: bool = False
    production_policy_write_allowed: bool = False
    boundary: str = "practitioner_label_projection_updates_training_labels_not_runtime_verdict"


class RealityProbeVerdictDiff(V30Model):
    version: str = "v30.reality_probe_verdict_diff.v1"
    diff_id: str
    case_id: str
    reading_id: str
    answer_signal_count: int = Field(default=0, ge=0)
    matched_verdict_domains: list[str] = Field(default_factory=list)
    contradicted_verdict_domains: list[str] = Field(default_factory=list)
    alignment_score: float = Field(default=0.0, ge=0.0, le=1.0)
    manifestation_updates: list[dict[str, Any]] = Field(default_factory=list)
    requires_followup: bool = False
    boundary: str = "reality_probe_verdict_diff_updates_manifestation_not_chart_facts"


class MingliPhase2Gate(V30Model):
    version: str = "v30.mingli_phase2_gate.v1"
    status: Phase2GateStatus
    phase1_status: str
    example_count: int = Field(default=0, ge=0)
    replay_queue_count: int = Field(default=0, ge=0)
    practitioner_label_projection_count: int = Field(default=0, ge=0)
    ziwei_golden_case_count: int = Field(default=0, ge=0)
    reality_probe_diff_count: int = Field(default=0, ge=0)
    replay_queue: list[MingliReplayQueueItem] = Field(default_factory=list)
    practitioner_projections: list[PractitionerLabelProjection] = Field(default_factory=list)
    reality_probe_diffs: list[RealityProbeVerdictDiff] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    chart_fact_mutation_allowed: bool = False
    production_policy_write_allowed: bool = False
    boundary: str = "mingli_phase2_gate_prepares_replay_and_labels_without_policy_promotion"

    @model_validator(mode="after")
    def _phase2_gate_is_safe(self) -> "MingliPhase2Gate":
        if self.chart_fact_mutation_allowed:
            raise ValueError("MingliPhase2Gate cannot allow chart fact mutation")
        if self.production_policy_write_allowed:
            raise ValueError("MingliPhase2Gate cannot write production policy")
        return self


def load_phase2_ziwei_golden_cases() -> list[MingliGoldenCase]:
    return [
        MingliGoldenCase(
            case_id="mtl-phase2-ziwei-career-authority",
            title="紫微事业权责旁路观察",
            user_question="事业压力主要来自权责还是平台？",
            target_domains=["career"],
            expected_verdict_domains=["career"],
            expected_advice_directions=["权责", "平台", "资质"],
            forbidden_assertions=["必然升职", "一定掌权", "紫微直接定论"],
            required_engines=[EngineKey.BAZI, EngineKey.ZIWEI, EngineKey.REALITY_PROBE],
            ziwei_matched_rule_ids=["ZW-CAREER-02", "ZW-CAREER-04"],
            reality_probe_answers=[
                {"answer_id": "rp-career-authority", "domains": ["career"], "supports": ["career"], "selected_option": "权责压力"}
            ],
        ),
        MingliGoldenCase(
            case_id="mtl-phase2-ziwei-wealth-partnership",
            title="紫微财务合作分配旁路观察",
            user_question="财运更适合主动争取还是保守积累？",
            target_domains=["wealth"],
            expected_verdict_domains=["wealth"],
            expected_advice_directions=["合作", "分配", "风险"],
            forbidden_assertions=["保证暴富", "稳赚不赔", "紫微直接定论"],
            required_engines=[EngineKey.BAZI, EngineKey.ZIWEI, EngineKey.REALITY_PROBE],
            ziwei_matched_rule_ids=["ZW-WEALTH-02", "ZW-WEALTH-05"],
            reality_probe_answers=[
                {"answer_id": "rp-wealth-peer", "domains": ["wealth"], "supports": ["wealth"], "selected_option": "合作分配压力"}
            ],
        ),
        MingliGoldenCase(
            case_id="mtl-phase2-ziwei-relationship-pressure",
            title="紫微关系阻塞旁路观察",
            user_question="感情关系里最容易反复的问题是什么？",
            target_domains=["relationship"],
            expected_verdict_domains=["relationship"],
            expected_advice_directions=["边界", "情绪", "反复"],
            forbidden_assertions=["必然离婚", "一定复合", "紫微直接定论"],
            required_engines=[EngineKey.BAZI, EngineKey.ZIWEI, EngineKey.REALITY_PROBE],
            ziwei_matched_rule_ids=["ZW-REL-02", "ZW-REL-03"],
            reality_probe_answers=[
                {"answer_id": "rp-rel-boundary", "domains": ["relationship"], "supports": ["relationship"], "selected_option": "边界反复"}
            ],
        ),
    ]


def build_replay_queue(examples: list[EngineTrainingExample]) -> list[MingliReplayQueueItem]:
    items: list[MingliReplayQueueItem] = []
    for example in examples:
        if example.quality_score.passed:
            continue
        reasons = example.quality_score.failed_reasons or ["quality_score_not_passed"]
        items.append(
            MingliReplayQueueItem(
                replay_id=f"replay:{example.case_id}:{example.reading_id}",
                case_id=example.case_id,
                reading_id=example.reading_id,
                example_id=example.example_id,
                failed_reasons=reasons,
                priority=_priority(reasons),
                rerun_plan=_rerun_plan(reasons),
                trainable_targets=example.trainable_targets,
                blocked_targets=example.blocked_targets,
            )
        )
    return items


def build_practitioner_label_projection(
    *,
    example: EngineTrainingExample,
    labels: list[PractitionerLabel],
) -> PractitionerLabelProjection:
    matched = [label for label in labels if label.case_id == example.case_id and label.reading_id == example.reading_id]
    accepted = sorted({domain for label in matched for domain in label.accepted_verdict_domains})
    rejected = sorted({domain for label in matched for domain in label.rejected_verdict_domains})
    verdict_domains = {str(row.get("domain") or "") for row in example.verdict_summary}
    alignment = round(len(set(accepted) & verdict_domains) / max(1, len(accepted)), 3) if accepted else 0.0
    overrides: dict[str, float] = {}
    for label in matched:
        for key, value in label.quality_overrides.items():
            overrides[key] = round(max(0.0, min(1.0, float(value))), 3)
    return PractitionerLabelProjection(
        projection_id=f"practitioner-label:{example.case_id}:{example.reading_id}",
        case_id=example.case_id,
        reading_id=example.reading_id,
        label_count=len(matched),
        accepted_domain_count=len(accepted),
        rejected_domain_count=len(rejected),
        label_alignment_score=alignment,
        quality_overrides=overrides,
        trainable_targets=[
            "practitioner_label_alignment",
            "verdict_domain_alignment",
            "advice_tag_weight",
            "quality_override_calibration",
        ] if matched else [],
    )


def build_reality_probe_verdict_diff(
    *,
    golden_case: MingliGoldenCase,
    example: EngineTrainingExample,
) -> RealityProbeVerdictDiff:
    verdict_domains = {str(row.get("domain") or "") for row in example.verdict_summary}
    answer_domains = sorted({
        str(domain)
        for answer in golden_case.reality_probe_answers
        for domain in _as_list(answer.get("domains") or answer.get("supports") or answer.get("feedback_tags"))
        if str(domain)
    })
    contradicted = sorted({
        str(domain)
        for answer in golden_case.reality_probe_answers
        for domain in _as_list(answer.get("contradicts") or answer.get("contradicted_domains"))
        if str(domain)
    })
    matched = sorted(set(answer_domains) & verdict_domains)
    alignment = round(len(matched) / max(1, len(answer_domains)), 3) if answer_domains else 0.0
    return RealityProbeVerdictDiff(
        diff_id=f"reality-probe-diff:{example.case_id}:{example.reading_id}",
        case_id=example.case_id,
        reading_id=example.reading_id,
        answer_signal_count=len(golden_case.reality_probe_answers),
        matched_verdict_domains=matched,
        contradicted_verdict_domains=sorted(set(contradicted) & verdict_domains),
        alignment_score=alignment,
        manifestation_updates=[
            {
                "domain": domain,
                "status": "supported_by_reality_probe" if domain in matched else "needs_followup",
                "boundary": "manifestation_update_does_not_mutate_chart_facts",
            }
            for domain in sorted(set(answer_domains) | set(contradicted))
        ],
        requires_followup=bool(set(contradicted) & verdict_domains) or alignment < 0.5,
    )


def build_default_practitioner_labels(examples: list[EngineTrainingExample]) -> list[PractitionerLabel]:
    labels: list[PractitionerLabel] = []
    for example in examples:
        domains = [str(row.get("domain") or "") for row in example.verdict_summary if row.get("domain")]
        labels.append(
            PractitionerLabel(
                label_id=f"label:{example.case_id}:{example.reading_id}",
                case_id=example.case_id,
                reading_id=example.reading_id,
                decision="accept" if example.quality_score.passed else "revise",
                accepted_verdict_domains=domains[:3] or ["overview"],
                rejected_verdict_domains=[] if example.quality_score.passed else ["low_quality"],
                advice_tags=["证据", "建议", "边界"],
                quality_overrides={"overall_quality": example.quality_score.overall_score},
            )
        )
    return labels


def build_mingli_phase2_gate(
    *,
    phase1_gate: MingliTrainingQualityGate,
    ziwei_examples: list[EngineTrainingExample],
    practitioner_labels: list[PractitionerLabel] | None = None,
    min_ziwei_cases: int = 3,
) -> MingliPhase2Gate:
    all_examples = [*phase1_gate.examples, *ziwei_examples]
    replay_queue = build_replay_queue(all_examples)
    labels = practitioner_labels or build_default_practitioner_labels(all_examples)
    projections = [
        build_practitioner_label_projection(example=example, labels=labels)
        for example in all_examples
    ]
    diffs = [
        build_reality_probe_verdict_diff(golden_case=case, example=example)
        for case, example in _case_example_pairs(load_phase2_ziwei_golden_cases(), ziwei_examples)
        if case.reality_probe_answers
    ]
    recommendations: list[str] = []
    if replay_queue:
        recommendations.append("先处理 replay queue，再进入策略晋级。")
    if len(ziwei_examples) < min_ziwei_cases:
        recommendations.append("补足紫微 golden cases 后再评估 Ziwei Domain Lens 稳定性。")
    if not diffs:
        recommendations.append("补充 Reality Probe answer-verdict diff。")
    if any(diff.requires_followup for diff in diffs):
        recommendations.append("Reality Probe 出现冲突，优先生成下一轮追问。")
    status: Phase2GateStatus = "passed"
    if phase1_gate.status != "passed" or replay_queue or len(ziwei_examples) < min_ziwei_cases or not diffs:
        status = "blocked"
    return MingliPhase2Gate(
        status=status,
        phase1_status=phase1_gate.status,
        example_count=len(all_examples),
        replay_queue_count=len(replay_queue),
        practitioner_label_projection_count=len(projections),
        ziwei_golden_case_count=len(ziwei_examples),
        reality_probe_diff_count=len(diffs),
        replay_queue=replay_queue,
        practitioner_projections=projections,
        reality_probe_diffs=diffs,
        recommendations=recommendations or ["Phase 2 gate passed; eligible for synthetic replay, not production pointer promotion."],
    )


def _priority(reasons: list[str]) -> ReplayPriority:
    if any(reason in {"forbidden_assertion_hit", "overclaim_risk_high"} for reason in reasons):
        return "critical"
    if any("evidence" in reason or "advice" in reason for reason in reasons):
        return "high"
    if "overall_score_below_case_threshold" in reasons:
        return "medium"
    return "low"


def _rerun_plan(reasons: list[str]) -> list[str]:
    actions = []
    if any("evidence" in reason for reason in reasons):
        actions.append("rerun_with_evidence_binding_audit")
    if any("advice" in reason for reason in reasons):
        actions.append("rerun_with_advice_actionability_prompt")
    if any(reason in {"forbidden_assertion_hit", "overclaim_risk_high"} for reason in reasons):
        actions.append("rerun_with_safety_boundary_gate")
    if not actions:
        actions.append("rerun_with_multi_engine_trace")
    return actions


def _case_example_pairs(cases: list[MingliGoldenCase], examples: list[EngineTrainingExample]) -> list[tuple[MingliGoldenCase, EngineTrainingExample]]:
    by_case = {example.case_id: example for example in examples}
    return [(case, by_case[case.case_id]) for case in cases if case.case_id in by_case]


def _as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple | set):
        return list(value)
    if value:
        return [value]
    return []
