from __future__ import annotations

from dataclasses import dataclass

from v20.answer.measurement_policy import domain_label, feature_public_summary
from v20.features.schema import BaziFeature, FeatureLayer
from v20.interaction.questions import QuestionCandidate
from v20.knowledge.schema import KnowledgeRef


@dataclass(frozen=True)
class DomainReadingSection:
    title: str
    body: str
    feature_ids: tuple[str, ...]
    domain: str
    section_type: str


DOMAIN_READING_BLUEPRINTS = {
    "strength": {
        "title": "日主承载力读法",
        "entry": "先看日主是否有承载结构，再决定后续取用、领域投影和时间触发能否展开。",
        "method": "读取扶助分、压力分、十神显隐和地支互动，判断当前盘面更适合先补证据还是先做领域投影。",
        "boundary": "这里不把承载力直接写成身强身弱定论，只给出进入下一步测算的结构门槛。",
    },
    "useful_god": {
        "title": "用神候选读法",
        "entry": "用神先作为候选路径处理，不能从单一元素或单一十神直接定死喜忌。",
        "method": "先看承载力，再看五行分布、十神材料和地支关系，最后用证据门槛筛选可继续复核的路径。",
        "boundary": "当前只输出候选和缺口，不输出固定喜忌。",
    },
    "ten_god": {
        "title": "十神结构读法",
        "entry": "十神用于说明角色、关系和主题入口，明透与藏干需要分层读取。",
        "method": "先分辨明透材料和藏干材料，再看它们是否被地支关系或时间层触发。",
        "boundary": "不凭单一十神推出人生结果，只说明这些十神能进入哪些测算主题。",
    },
    "element": {
        "title": "五行结构读法",
        "entry": "五行分布用于判断结构偏向和扶抑压力，是基础层材料。",
        "method": "先看相对集中与相对不足，再回到日主承载力和用神候选路径做交叉复核。",
        "boundary": "不把五行偏向直接写成吉凶或身体结论。",
    },
    "branch": {
        "title": "地支互动读法",
        "entry": "地支冲合刑害用于识别结构互动和层级变化。",
        "method": "先区分原局关系和时间层关系，再判断它们影响的是结构背景、主题入口还是触发边界。",
        "boundary": "只解释互动关系和证据层级，不把冲合直接写成好坏。",
    },
    "time": {
        "title": "时间触发读法",
        "entry": "时间层只在大运、流年、流月等干支已给出时进入测算。",
        "method": "先看时间干支对应十神，再看它与原局地支发生哪些关系，最后说明这些关系能触发哪些结构主题。",
        "boundary": "时间层是触发背景，不输出无证据支撑的具体时间点。",
    },
    "wealth": {
        "title": "财运结构读法",
        "entry": "财运先看财星材料是否可见，再看日主承载力和结构通道是否支持讨论收入主题。",
        "method": "财星显现时读取明透或藏干来源；财星不显时，转向十神、五行和地支路径复核可用材料。",
        "boundary": "只讨论财星材料、收入结构和候选路径，不判断具体收益结果。",
    },
    "career": {
        "title": "事业结构读法",
        "entry": "事业测算从角色结构进入，而不是直接断职业或职位变化。",
        "method": "先读十神显隐中的角色材料，再看日主承载力能否承接，地支互动则作为工作环境和结构压力的复核层。",
        "boundary": "只给出事业角色、工作结构和可继续追问的方向，不输出固定升降结果。",
    },
    "relationship": {
        "title": "关系结构读法",
        "entry": "关系测算先看互动结构，而不是直接断关系事件。",
        "method": "先读十神显隐中的关系材料，再看地支冲合是否形成互动张力或支持，日主承载力用于判断承接边界。",
        "boundary": "只说明关系互动结构和候选路径，不输出固定关系事件。",
    },
    "health": {
        "title": "健康边界读法",
        "entry": "健康相关问题只进入五行平衡和压力边界，不进入医学判断。",
        "method": "先看五行分布的相对集中与不足，再结合承载力和地支互动说明结构压力来源。",
        "boundary": "只给出命理结构层面的平衡提醒，不输出诊断或处理建议。",
    },
    "pattern": {
        "title": "格局审查读法",
        "entry": "格局只作为审查索引，必须回到特征、规则路径和证据包。",
        "method": "先看格局索引，再检查承载力、十神显隐、地支互动和用神候选是否共同支持。",
        "boundary": "不把格局索引直接写成成败高低。",
    },
}

QUESTION_READING_OVERRIDES = {
    "q_income_stability": "wealth",
    "q_income_factors": "wealth",
    "q_career_structure": "career",
    "q_relationship_structure": "relationship",
    "q_health_balance_boundary": "health",
    "q_time_layer_context": "time",
    "q_time_relation_triggers": "time",
    "q_hidden_stem_role": "ten_god",
    "q_useful_god_candidates": "useful_god",
    "q_useful_god_evidence_gaps": "useful_god",
}

KNOWLEDGE_LABELS_ZH = {
    "v20.core.strength_boundary": "日主强弱证据边界",
    "v20.core.branch_relation_boundary": "地支关系分层边界",
    "v20.core.time_layer_boundary": "时间层触发边界",
    "v20.core.wealth_material_boundary": "财星材料边界",
    "v20.applied.career_projection_boundary": "事业投影边界",
    "v20.applied.relationship_projection_boundary": "关系投影边界",
    "v20.applied.health_projection_boundary": "健康边界投影",
    "v20.core.useful_god_gate": "用神证据门槛",
    "v20.core.useful_god_candidate_paths": "用神候选路径",
    "v20.core.ten_god_boundary": "十神解释边界",
    "v20.core.element_distribution_boundary": "五行分布边界",
    "v20.core.pattern_review_boundary": "格局审查边界",
}


def build_domain_reading_sections(
    question: QuestionCandidate,
    selected_features: tuple[BaziFeature, ...],
    feature_layer: FeatureLayer,
    knowledge_refs: tuple[KnowledgeRef, ...] = (),
) -> tuple[DomainReadingSection, ...]:
    domain = QUESTION_READING_OVERRIDES.get(question.question_key, question.domain)
    blueprint = DOMAIN_READING_BLUEPRINTS.get(domain)
    if not blueprint:
        return ()
    feature_ids = _domain_feature_ids(domain, selected_features, feature_layer)
    material = _material_sentence(domain, selected_features, feature_layer)
    knowledge = _knowledge_sentence(domain, knowledge_refs)
    body = (
        f"{blueprint['entry']} "
        f"{blueprint['method']} "
        f"{material} "
        f"{knowledge} "
        f"{blueprint['boundary']}"
    ).strip()
    return (
        DomainReadingSection(
            title=blueprint["title"],
            body=body,
            feature_ids=feature_ids,
            domain=domain,
            section_type="domain_measurement_path",
        ),
        DomainReadingSection(
            title="知识依据",
            body=_knowledge_detail_sentence(domain, knowledge_refs),
            feature_ids=feature_ids,
            domain=domain,
            section_type="knowledge_evidence_support",
        ),
        DomainReadingSection(
            title="下一步复核",
            body=_next_step_sentence(domain, question),
            feature_ids=feature_ids,
            domain=domain,
            section_type="measurement_next_step",
        ),
    )


def _domain_feature_ids(
    domain: str,
    selected_features: tuple[BaziFeature, ...],
    feature_layer: FeatureLayer,
) -> tuple[str, ...]:
    selected = [feature.feature_id for feature in selected_features if feature.domain == domain]
    if selected:
        return tuple(dict.fromkeys(selected))
    related = [
        feature.feature_id
        for feature in feature_layer.features
        if feature.domain in _support_domains(domain)
    ]
    return tuple(dict.fromkeys(related[:6]))


def _material_sentence(
    domain: str,
    selected_features: tuple[BaziFeature, ...],
    feature_layer: FeatureLayer,
) -> str:
    material_features = [
        feature
        for feature in (*selected_features, *feature_layer.features)
        if feature.domain in _support_domains(domain)
    ]
    summaries = []
    seen: set[str] = set()
    for feature in material_features:
        if feature.feature_id in seen:
            continue
        seen.add(feature.feature_id)
        summary = feature_public_summary(feature)
        if summary:
            summaries.append(summary.rstrip("。"))
    if not summaries:
        return f"当前以{domain_label(domain)}的已编译特征作为测算材料。"
    return "已接入材料：" + "；".join(summaries[:3]) + "。"


def _next_step_sentence(domain: str, question: QuestionCandidate) -> str:
    if domain == "wealth":
        return "建议继续追问财星来源、承载力和时间层触发三件事，避免只看单一财星标签。"
    if domain == "career":
        return "建议继续追问十神角色、承载力和地支互动，先确定事业测算的主轴。"
    if domain == "relationship":
        return "建议继续追问关系互动、地支冲合和十神来源层，先拆清结构再谈应用。"
    if domain == "health":
        return "建议继续追问五行分布和压力来源，只保留命理结构层面的平衡边界。"
    if domain == "time":
        return "建议继续追问时间干支、对应十神和与原局的关系，先确认触发层级。"
    if domain == "useful_god":
        return "建议继续追问候选路径缺口，让规则图和证据门槛参与裁决。"
    if domain == "ten_god":
        return "建议继续追问明透与藏干分别承担的主题入口，再看是否被地支或时间层触发。"
    return f"建议继续围绕「{question.title}」补充证据来源和结构边界。"


def _knowledge_sentence(domain: str, knowledge_refs: tuple[KnowledgeRef, ...]) -> str:
    labels = _knowledge_labels(domain, knowledge_refs)[:4]
    if not labels:
        return "知识依据：当前仅使用 feature spine 的结构材料，等待更多已审查知识补充。"
    return f"知识依据：已选取 {len(labels)} 条已审查知识边界，包括" + "、".join(labels[:3]) + "。"


def _knowledge_detail_sentence(domain: str, knowledge_refs: tuple[KnowledgeRef, ...]) -> str:
    refs = _relevant_knowledge_refs(domain, knowledge_refs)
    if not refs:
        return "当前没有匹配到该领域的已审查知识条目，回答只保留结构材料和测算边界。"
    rows = []
    for ref in refs[:4]:
        label = KNOWLEDGE_LABELS_ZH.get(ref.knowledge_id, ref.title)
        rows.append(f"{label}：{_knowledge_usage(ref)}")
    return "；".join(rows) + "。"


def _knowledge_labels(domain: str, knowledge_refs: tuple[KnowledgeRef, ...]) -> list[str]:
    return [
        KNOWLEDGE_LABELS_ZH.get(ref.knowledge_id, ref.title)
        for ref in _relevant_knowledge_refs(domain, knowledge_refs)
    ]


def _knowledge_usage(ref: KnowledgeRef) -> str:
    if ref.domain == "wealth":
        return "只支持财星材料、来源层和收入结构边界"
    if ref.domain == "career":
        return "只支持事业角色、工作结构和候选主轴"
    if ref.domain == "relationship":
        return "只支持关系互动结构和候选张力"
    if ref.domain == "health":
        return "只支持五行平衡和结构压力边界"
    if ref.domain == "time":
        return "只支持已给定时间干支与原局互动"
    if ref.domain == "useful_god":
        return "只支持候选路径和证据缺口复核"
    if ref.domain == "ten_god":
        return "只支持十神来源层和结构主题入口"
    if ref.domain == "branch":
        return "只支持地支关系名称和层级边界"
    if ref.domain == "element":
        return "只支持五行分布和结构偏向"
    if ref.domain == "strength":
        return "只支持承载力证据和扶抑压力边界"
    if ref.domain == "pattern":
        return "只支持格局审查索引"
    return "只作为已审查证据边界使用"


def _relevant_knowledge_refs(domain: str, knowledge_refs: tuple[KnowledgeRef, ...]) -> tuple[KnowledgeRef, ...]:
    support_domains = _support_domains(domain)
    domains = set(support_domains)
    exact = [ref for ref in knowledge_refs if ref.domain == domain]
    related = sorted(
        [ref for ref in knowledge_refs if ref.domain in domains and ref.domain != domain],
        key=lambda ref: (support_domains.index(ref.domain), ref.knowledge_id),
    )
    return tuple(dict.fromkeys([*exact, *related]))


def _support_domains(domain: str) -> tuple[str, ...]:
    if domain == "wealth":
        return ("wealth", "ten_god", "strength", "branch", "time", "useful_god")
    if domain == "career":
        return ("ten_god", "strength", "branch", "pattern", "useful_god", "time")
    if domain == "relationship":
        return ("ten_god", "branch", "strength", "time")
    if domain == "health":
        return ("element", "strength", "branch", "pattern")
    if domain == "time":
        return ("time", "branch", "ten_god")
    if domain == "useful_god":
        return ("useful_god", "strength", "element", "ten_god", "branch")
    if domain == "ten_god":
        return ("ten_god", "branch", "time")
    return (domain,)
