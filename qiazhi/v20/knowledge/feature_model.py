from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


DECISION_STATES: tuple[str, ...] = (
    "confirmed",
    "candidate",
    "weak_candidate",
    "blocked",
    "countered",
    "mixed",
    "volatile",
    "requires_review",
    "out_of_scope",
)


@dataclass(frozen=True)
class FactNode:
    node_id: str
    fact_type: str
    value: str
    pillar: str = ""
    position: str = ""
    source: str = "chart_facts"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceAtom:
    atom_id: str
    domain: str
    evidence_type: str
    title: str
    required_fact_types: tuple[str, ...]
    supports: tuple[str, ...] = field(default_factory=tuple)
    boundary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RulePath:
    path_id: str
    title: str
    domain: str
    evidence_atom_ids: tuple[str, ...]
    target_feature: str
    decision_state_policy: str
    counter_evidence_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MechanismPath:
    mechanism_id: str
    title: str
    mechanism_type: str
    source_feature_ids: tuple[str, ...]
    target_domains: tuple[str, ...]
    boundary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CounterEvidence:
    counter_id: str
    title: str
    blocks_or_downgrades: tuple[str, ...]
    required_evidence_atom_ids: tuple[str, ...]
    resulting_state: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionState:
    state: str
    title: str
    user_facing_policy: str
    can_project_to_topic: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TopicProjection:
    projection_id: str
    title: str
    topic_domain: str
    source_domains: tuple[str, ...]
    allowed_decision_states: tuple[str, ...]
    output_focus: tuple[str, ...]
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TraceNode:
    trace_id: str
    trace_type: str
    title: str
    source_ids: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_bazi_feature_graph_model_contract() -> dict[str, Any]:
    topic_projections = _topic_projections()
    decision_states = _decision_states()
    return {
        "version": "v20.bazi_feature_graph_model.v1",
        "status": "phase1_contract_ready",
        "model_name": "V20 Bazi Feature Graph Model",
        "core_principle": "find_bazi_features_before_portrait_question_or_answer",
        "implementation_strategy": "lightweight_typed_objects_before_heavy_property_graph",
        "runtime_mutation": False,
        "mainline_chain": (
            "ChartFacts",
            "CoreInference",
            "EvidenceAtom[]",
            "RulePath[]",
            "MechanismPath[]",
            "DecisionState[]",
            "TopicProjection[]",
            "BaziFeature[]",
            "QuestionCandidate[]",
            "EvidencePack",
            "AnswerPlan",
        ),
        "phase1_objects": (
            "FactNode",
            "EvidenceAtom",
            "RulePath",
            "MechanismPath",
            "CounterEvidence",
            "DecisionState",
            "TopicProjection",
            "BaziFeature",
            "TraceNode",
        ),
        "decision_states": [row.to_dict() for row in decision_states],
        "decision_state_keys": tuple(row.state for row in decision_states),
        "topic_projection_count": len(topic_projections),
        "topic_projections": [row.to_dict() for row in topic_projections],
        "product_contracts": (
            "BaziFeature[]",
            "QuestionCandidate[]",
            "EvidencePack",
            "AnswerPlan",
        ),
        "blocked_direct_consumers": (
            "ui_direct_fact_graph_consumption",
            "question_direct_decision_graph_consumption",
            "answer_direct_internal_debug_consumption",
            "llm_direct_arbitration",
        ),
        "p0_lanes": (
            "calendar_and_chart_facts_accuracy",
            "core_bazi_fact_extraction",
            "ten_god_hidden_stem_branch_relation_strength_evidence",
            "rule_path_to_bazi_feature",
            "bazi_feature_to_evidence_pack_and_answer_plan",
        ),
        "llm_allowed_roles": (
            "intent_understanding",
            "question_grouping",
            "followup_expression",
            "answer_plan_language_adapter",
            "feedback_summary",
        ),
        "llm_blocked_roles": (
            "chart_fact_generation",
            "useful_god_arbitration",
            "pattern_success_arbitration",
            "fortune_verdict_generation",
            "rule_graph_mutation",
            "evidence_pack_bypass",
        ),
        "guardrails": (
            "FEATURE_GRAPH_IS_INTERNAL_REASONING_MODEL",
            "FEATURE_SPINE_IS_PRODUCT_CONTRACT",
            "TOPIC_PROJECTION_REQUIRED_BEFORE_USER_FACING_OUTPUT",
            "DECISION_STATE_IS_STRUCTURAL_NOT_FATE_VERDICT",
            "PHASE1_USES_TYPED_OBJECTS_NOT_HEAVY_GRAPH_PLATFORM",
        ),
    }


def _decision_states() -> tuple[DecisionState, ...]:
    return (
        DecisionState("confirmed", "明确成立", "can_explain_with_evidence_boundary", True),
        DecisionState("candidate", "候选成立", "explain_as_candidate_not_final_verdict", True),
        DecisionState("weak_candidate", "弱候选", "ask_or_review_before_strong_projection", True),
        DecisionState("blocked", "被阻断", "explain_blocker_before_any_projection", False),
        DecisionState("countered", "有明显反证", "surface_counter_evidence_and_reduce_output", False),
        DecisionState("mixed", "成而不纯", "explain_both_support_and_impurity", True),
        DecisionState("volatile", "岁运引动后波动", "bind_projection_to_time_context", True),
        DecisionState("requires_review", "需要命理师复核", "route_to_review_or_followup_question", False),
        DecisionState("out_of_scope", "证据不足不输出", "suppress_user_facing_claim", False),
    )


def _topic_projections() -> tuple[TopicProjection, ...]:
    allowed = ("confirmed", "candidate", "weak_candidate", "mixed", "volatile")
    return (
        TopicProjection(
            "projection.wealth",
            "财富主题投射",
            "wealth",
            ("wealth", "strength", "ten_god", "branch", "time", "useful_god"),
            allowed,
            ("材料", "机会", "承接", "波动", "风险"),
            "不把财星存在直接表达为财运好。",
        ),
        TopicProjection(
            "projection.career",
            "事业主题投射",
            "career",
            ("career", "ten_god", "pattern", "strength", "branch", "time"),
            allowed,
            ("规则", "平台", "表达", "承接", "冲突"),
            "不把官杀或印星单点命中直接表达为事业成败。",
        ),
        TopicProjection(
            "projection.relationship",
            "关系主题投射",
            "relationship",
            ("relationship", "ten_god", "branch", "palace", "blind_lifa", "time"),
            allowed,
            ("互动", "合作", "竞争", "边界", "引动"),
            "关系主题必须保留宫位、十神互动和反证边界。",
        ),
        TopicProjection(
            "projection.romance",
            "感情主题投射",
            "romance",
            ("relationship", "palace", "ten_god", "branch", "time"),
            allowed,
            ("伴侣星", "夫妻宫", "合冲", "承接", "安全边界"),
            "感情主题在专属规则完成前沿用 relationship evidence domain。",
        ),
        TopicProjection(
            "projection.health",
            "健康主题投射",
            "health",
            ("health", "element", "strength", "time"),
            allowed,
            ("偏枯", "寒暖燥湿", "压力", "恢复", "禁断边界"),
            "健康只做结构和生活节律表达，不做医疗诊断。",
        ),
    )
