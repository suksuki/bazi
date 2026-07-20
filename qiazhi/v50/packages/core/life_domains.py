from __future__ import annotations

from enum import Enum

from pydantic import Field

from core.contracts.base import V50Model


class LifeDomain(str, Enum):
    WHOLE_CHART = "whole_chart"
    SELF = "self"
    TALENT_LEARNING = "talent_learning"
    CAREER = "career"
    WEALTH = "wealth"
    RELATIONSHIP = "relationship"
    FAMILY = "family"
    CHILDREN_LEGACY = "children_legacy"
    HEALTH_VITALITY = "health_vitality"
    SOCIAL_NETWORK = "social_network"
    MIGRATION_ENVIRONMENT = "migration_environment"
    LIFE_TIMING = "life_timing"


class DomainReadiness(str, Enum):
    LIVE = "live"
    PARTIAL = "partial"
    RESEARCH = "research"


class LifeDomainDefinition(V50Model):
    domain: LifeDomain
    name_zh: str
    user_jobs: list[str] = Field(default_factory=list)
    required_reasoning: list[str] = Field(default_factory=list)
    readiness: DomainReadiness
    publicly_available: bool = False
    boundary: str = ""


class DomainReasoningProtocol(V50Model):
    domain: LifeDomain
    core_questions: list[str]
    causal_focus: list[str]
    relevant_ziwei_palaces: list[str] = Field(default_factory=list)
    probe_goal: str
    forbidden_claims: list[str] = Field(default_factory=list)
    public_depth: str


DOMAIN_REGISTRY = (
    LifeDomainDefinition(domain=LifeDomain.WHOLE_CHART, name_zh="整盘命局", user_jobs=["理解命局重心", "理解主做功与整体矛盾"], required_reasoning=["bazi_pattern", "ziwei_lens", "hypothesis_comparison"], readiness=DomainReadiness.LIVE, publicly_available=True),
    LifeDomainDefinition(domain=LifeDomain.SELF, name_zh="自我与性情", user_jobs=["理解稳定人格模式", "理解压力下的反应方式"], required_reasoning=["whole_chart", "portrait", "probe"], readiness=DomainReadiness.PARTIAL, publicly_available=False),
    LifeDomainDefinition(domain=LifeDomain.TALENT_LEARNING, name_zh="天赋与学习", user_jobs=["理解优势能力", "选择学习与成长方式"], required_reasoning=["output_resource_analysis", "education_context"], readiness=DomainReadiness.RESEARCH, publicly_available=False),
    LifeDomainDefinition(domain=LifeDomain.CAREER, name_zh="事业与职业", user_jobs=["理解职业方向", "比较发展路径", "识别当前机会与压力"], required_reasoning=["whole_chart", "career_causal_chain", "timing"], readiness=DomainReadiness.LIVE, publicly_available=True),
    LifeDomainDefinition(domain=LifeDomain.WEALTH, name_zh="财富与资源", user_jobs=["理解财富形成方式", "理解承载、保留与风险"], required_reasoning=["whole_chart", "wealth_causal_chain", "timing"], readiness=DomainReadiness.LIVE, publicly_available=True),
    LifeDomainDefinition(domain=LifeDomain.RELATIONSHIP, name_zh="亲密关系", user_jobs=["理解关系模式", "理解互动需求与冲突条件"], required_reasoning=["whole_chart", "relationship_context", "counter_evidence"], readiness=DomainReadiness.RESEARCH, publicly_available=False, boundary="不输出婚期、离婚或配偶事件的确定断言"),
    LifeDomainDefinition(domain=LifeDomain.FAMILY, name_zh="家庭与原生关系", user_jobs=["理解家庭角色", "理解支持与责任结构"], required_reasoning=["whole_chart", "family_context"], readiness=DomainReadiness.RESEARCH, publicly_available=False),
    LifeDomainDefinition(domain=LifeDomain.CHILDREN_LEGACY, name_zh="子女与传承", user_jobs=["理解养育互动", "理解长期传承主题"], required_reasoning=["whole_chart", "family_context", "timing"], readiness=DomainReadiness.RESEARCH, publicly_available=False, boundary="不预测生育数量、性别或具体事件"),
    LifeDomainDefinition(domain=LifeDomain.HEALTH_VITALITY, name_zh="健康与生命力", user_jobs=["理解精力节奏", "识别生活方式风险"], required_reasoning=["whole_chart", "health_context", "medical_boundary"], readiness=DomainReadiness.RESEARCH, publicly_available=False, boundary="不诊断疾病，不替代医疗建议"),
    LifeDomainDefinition(domain=LifeDomain.SOCIAL_NETWORK, name_zh="社交与合作", user_jobs=["理解合作方式", "理解竞争、边界与资源网络"], required_reasoning=["whole_chart", "peer_network", "probe"], readiness=DomainReadiness.PARTIAL, publicly_available=False),
    LifeDomainDefinition(domain=LifeDomain.MIGRATION_ENVIRONMENT, name_zh="迁移与环境", user_jobs=["理解环境适配", "比较留守、迁移与外部发展"], required_reasoning=["whole_chart", "ziwei_migration", "timing"], readiness=DomainReadiness.PARTIAL, publicly_available=False),
    LifeDomainDefinition(domain=LifeDomain.LIFE_TIMING, name_zh="人生阶段与时机", user_jobs=["理解长期阶段", "识别行动窗口与等待条件"], required_reasoning=["base_chart", "luck", "year", "state_evolution"], readiness=DomainReadiness.PARTIAL, publicly_available=True, boundary="只输出条件性时机，不输出必然事件"),
)


PUBLIC_PRODUCT_DOMAINS = frozenset({LifeDomain.WHOLE_CHART, LifeDomain.CAREER, LifeDomain.WEALTH, LifeDomain.LIFE_TIMING})


DOMAIN_PROTOCOLS = {
    LifeDomain.SELF: DomainReasoningProtocol(domain=LifeDomain.SELF, core_questions=["稳定的驱动力是什么", "压力下会如何反应"], causal_focus=["主做功如何变成行为偏好", "优势与防御是否来自同一结构"], relevant_ziwei_palaces=["命宫", "福德宫", "身宫"], probe_goal="区分稳定性情与当前情境反应", forbidden_claims=["人格定型", "道德评价"], public_depth="bounded_deep"),
    LifeDomain.TALENT_LEARNING: DomainReasoningProtocol(domain=LifeDomain.TALENT_LEARNING, core_questions=["什么信息最容易被吸收和转化", "能力如何形成可见成果"], causal_focus=["印与食伤的输入输出", "练习、表达和反馈环境"], relevant_ziwei_palaces=["命宫", "福德宫", "官禄宫"], probe_goal="区分理解型、实践型与反馈型学习", forbidden_claims=["智商高低", "考试必然结果"], public_depth="bounded"),
    LifeDomain.CAREER: DomainReasoningProtocol(domain=LifeDomain.CAREER, core_questions=["价值如何形成", "什么组织环境能承接"], causal_focus=["主做功到职业价值", "责任、规则、输出与资源"], relevant_ziwei_palaces=["官禄宫", "命宫", "迁移宫"], probe_goal="区分方向问题、环境问题和时机问题", forbidden_claims=["必然升职", "必然失业"], public_depth="deep"),
    LifeDomain.WEALTH: DomainReasoningProtocol(domain=LifeDomain.WEALTH, core_questions=["资源如何形成", "如何承载、保留与流失"], causal_focus=["能力到资源的转化", "财在主做功中是目标、工具、结果还是压力"], relevant_ziwei_palaces=["财帛宫", "田宅宫", "官禄宫"], probe_goal="区分收入形成、承载和风险问题", forbidden_claims=["保证收益", "具体金额", "投机结果"], public_depth="deep"),
    LifeDomain.RELATIONSHIP: DomainReasoningProtocol(domain=LifeDomain.RELATIONSHIP, core_questions=["如何进入亲密关系", "需要什么互动与边界"], causal_focus=["自我表达与承接关系", "控制、依赖、合作与冲突条件"], relevant_ziwei_palaces=["夫妻宫", "命宫", "福德宫"], probe_goal="区分稳定关系模式与单次关系经历", forbidden_claims=["具体婚期", "必然离婚", "配偶身份"], public_depth="bounded"),
    LifeDomain.FAMILY: DomainReasoningProtocol(domain=LifeDomain.FAMILY, core_questions=["在家庭中承担什么角色", "支持与责任如何流动"], causal_focus=["资源、规则与情感表达", "原生经验如何影响当前角色"], relevant_ziwei_palaces=["父母宫", "兄弟宫", "田宅宫"], probe_goal="区分原生结构与当前家庭现实", forbidden_claims=["亲属具体灾祸", "道德归因"], public_depth="bounded"),
    LifeDomain.CHILDREN_LEGACY: DomainReasoningProtocol(domain=LifeDomain.CHILDREN_LEGACY, core_questions=["如何表达养育与传承", "什么方式能让影响持续"], causal_focus=["输出、责任与长期承载", "控制和放手的平衡"], relevant_ziwei_palaces=["子女宫", "田宅宫", "福德宫"], probe_goal="区分养育、创作和传承主题", forbidden_claims=["生育数量", "子女性别", "具体生育事件"], public_depth="bounded"),
    LifeDomain.HEALTH_VITALITY: DomainReasoningProtocol(domain=LifeDomain.HEALTH_VITALITY, core_questions=["精力如何消耗和恢复", "什么生活节奏更可持续"], causal_focus=["五行偏态只映射精力与节奏", "压力与恢复条件"], relevant_ziwei_palaces=["疾厄宫", "福德宫", "命宫"], probe_goal="区分长期精力模式与当前健康事实", forbidden_claims=["疾病诊断", "器官病变", "寿命", "医疗结论"], public_depth="safety_bounded"),
    LifeDomain.SOCIAL_NETWORK: DomainReasoningProtocol(domain=LifeDomain.SOCIAL_NETWORK, core_questions=["如何建立合作", "竞争与资源边界在哪里"], causal_focus=["同类、规则和资源互动", "个人输出如何进入群体"], relevant_ziwei_palaces=["交友宫", "迁移宫", "官禄宫"], probe_goal="区分合作增益、同侪竞争和边界消耗", forbidden_claims=["他人恶意定性"], public_depth="bounded_deep"),
    LifeDomain.MIGRATION_ENVIRONMENT: DomainReasoningProtocol(domain=LifeDomain.MIGRATION_ENVIRONMENT, core_questions=["什么环境更能激活主做功", "变化与稳定如何权衡"], causal_focus=["环境对结构的承接", "迁移是机会、压力还是修复"], relevant_ziwei_palaces=["迁移宫", "命宫", "田宅宫"], probe_goal="区分主动拓展、被动逃离和时机激活", forbidden_claims=["必然移民", "具体地点吉凶"], public_depth="bounded_deep"),
    LifeDomain.LIFE_TIMING: DomainReasoningProtocol(domain=LifeDomain.LIFE_TIMING, core_questions=["当前阶段激活了什么", "什么时候适合行动或等待"], causal_focus=["原局不变项", "大运场", "流年激活与现实条件"], relevant_ziwei_palaces=["大限命宫", "流年命宫", "官禄宫", "财帛宫"], probe_goal="区分结构问题、时机问题和现实条件问题", forbidden_claims=["必然事件", "精确发财年份", "灾祸日期"], public_depth="bounded_deep"),
}


def domain_manifest() -> list[dict[str, object]]:
    return [item.model_dump(mode="json") for item in DOMAIN_REGISTRY]


def domain_definition(domain: LifeDomain | str) -> LifeDomainDefinition:
    key = LifeDomain(domain)
    return next(item for item in DOMAIN_REGISTRY if item.domain is key)


def domain_access_allowed(domain: LifeDomain | str, *, role_mode: str) -> bool:
    key = LifeDomain(domain)
    if role_mode in {"practitioner", "research"}:
        return True
    return key in PUBLIC_PRODUCT_DOMAINS and domain_definition(key).publicly_available


def domain_reasoning_protocol(domain: LifeDomain | str) -> DomainReasoningProtocol:
    key = LifeDomain(domain)
    if key is LifeDomain.WHOLE_CHART:
        raise ValueError("whole_chart_uses_whole_cognition")
    return DOMAIN_PROTOCOLS[key]
