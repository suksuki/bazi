from __future__ import annotations

from v20.answer.plan import AnswerSection

TOPIC_LABELS = {
    "zh": {
        "strength": "日主强弱",
        "useful_god": "用神候选",
        "ten_god": "十神结构",
        "element": "五行分布",
        "branch": "地支关系",
        "time": "时间层与流年触发",
        "wealth": "财星与收入结构",
        "career": "事业角色与工作结构",
        "relationship": "关系互动结构",
        "health": "五行平衡与健康边界",
        "pattern": "格局审查",
    },
    "en": {
        "strength": "day-master capacity",
        "useful_god": "useful-god candidates",
        "ten_god": "ten-god structure",
        "element": "five-element distribution",
        "branch": "branch relations",
        "time": "time layer and flow triggers",
        "wealth": "wealth material and income structure",
        "career": "career role and work structure",
        "relationship": "relationship interaction structure",
        "health": "five-element balance boundary",
        "pattern": "pattern review",
    },
    "ko": {
        "strength": "일간 강약",
        "useful_god": "용신 후보",
        "ten_god": "십성 구조",
        "element": "오행 분포",
        "branch": "지지 관계",
        "time": "시간층과 세운 촉발",
        "wealth": "재성 재료와 수입 구조",
        "career": "직업 역할과 업무 구조",
        "relationship": "관계 상호작용 구조",
        "health": "오행 균형 경계",
        "pattern": "격국 검토",
    },
}

SECTION_TITLES = {
    "en": {
        "measurement_scope": "Measurement Scope",
        "domain_measurement_path": "Professional Reading Path",
        "knowledge_evidence_support": "Knowledge Evidence",
        "portrait_projection_reading": "Topic Projection Portrait",
        "mainline_decision": "Mainline Decision",
        "portrait_profile_summary": "Portrait Snapshot",
        "decision_knowledge_support": "Knowledge Evidence",
        "decision_next_step": "Next Question",
        "measurement_next_step": "Next Review Step",
        "feature_measurement": "Feature Reading",
        "prediction_boundary": "Prediction Boundary",
    },
    "ko": {
        "measurement_scope": "분석 범위",
        "domain_measurement_path": "전문 해석 경로",
        "knowledge_evidence_support": "지식 근거",
        "portrait_projection_reading": "주제 투사 프로필",
        "mainline_decision": "주요 판단",
        "portrait_profile_summary": "프로필 요약",
        "decision_knowledge_support": "지식 근거",
        "decision_next_step": "다음 질문",
        "measurement_next_step": "다음 검토 단계",
        "feature_measurement": "특징 해석",
        "prediction_boundary": "예측 경계",
    },
}


def locale_key(locale: str) -> str:
    if locale.startswith("ko"):
        return "ko"
    if locale.startswith("en"):
        return "en"
    return "zh"


def localized_topic(domain: str, locale: str) -> str:
    key = locale_key(locale)
    return TOPIC_LABELS.get(key, TOPIC_LABELS["zh"]).get(domain, domain)


def localized_section_title(section: AnswerSection, locale: str) -> str:
    key = locale_key(locale)
    if key == "zh":
        return section.title
    title = SECTION_TITLES[key].get(section.section_type, "Measurement Detail")
    topic = localized_topic(section.domain, locale) if section.domain else ""
    return f"{title}: {topic}" if topic and section.section_type == "feature_measurement" else title


def localized_section_body(section: AnswerSection, locale: str) -> str:
    key = locale_key(locale)
    topic = localized_topic(section.domain, locale) if section.domain else localized_topic("", locale)
    source_count = len(section.feature_ids)
    if key == "zh":
        return section.body
    if key == "ko":
        return _body_ko(section, topic, source_count)
    return _body_en(section, topic, source_count)


def _body_en(section: AnswerSection, topic: str, source_count: int) -> str:
    if section.section_type == "measurement_scope":
        return f"This answer uses the selected question as an entry into {topic}, with structure, evidence, and boundaries kept together."
    if section.section_type == "domain_measurement_path":
        return f"The professional reading path stays within {topic}, using only compiled Bazi features and reviewed evidence."
    if section.section_type == "knowledge_evidence_support":
        return f"Reviewed knowledge is used only as evidence support for {topic}, not as rule truth."
    if section.section_type == "portrait_projection_reading":
        return f"The topic projection for {topic} comes from current-chart decision states, not static corpus labels."
    if section.section_type == "portrait_profile_summary":
        return f"{topic} snapshot is compiled from current-chart portrait tags, decision states, and review pressure."
    if section.section_type == "mainline_decision":
        return f"The mainline decision for {topic} weighs supporting evidence, counter-evidence, and structural priority before answering."
    if section.section_type == "decision_knowledge_support":
        return f"Reviewed knowledge supports terms and boundaries for {topic}; it does not override decisions."
    if section.section_type == "decision_next_step":
        return f"Suggested next questions stay within the current decision evidence for {topic}."
    if section.section_type == "measurement_next_step":
        return f"The next review step is to deepen {topic} through source features rather than a fixed verdict."
    if section.section_type == "prediction_boundary":
        return "The answer gives structural reading and candidate paths only; it does not turn features into fixed events, fixed fortune verdicts, or unsupported timing."
    return f"Measurement focus stays on {topic}. The section is supported by {source_count} compiled source feature(s) and remains evidence-bounded."


def _body_ko(section: AnswerSection, topic: str, source_count: int) -> str:
    if section.section_type == "measurement_scope":
        return f"선택된 질문을 {topic} 분석의 입구로 삼고, 구조와 근거와 경계를 함께 유지합니다."
    if section.section_type == "domain_measurement_path":
        return f"전문 해석 경로는 {topic} 안에서 유지되며, 컴파일된 사주 특징과 검토된 근거만 사용합니다."
    if section.section_type == "knowledge_evidence_support":
        return f"검토된 지식은 {topic}의 근거 보조로만 사용되며 규칙 진실로 쓰지 않습니다."
    if section.section_type == "portrait_projection_reading":
        return f"{topic}의 주제 투사는 현재 명식의 판정 상태에서 나오며 정적 말뭉치 라벨이 아닙니다."
    if section.section_type == "portrait_profile_summary":
        return f"{topic} 요약은 현재 명식의 프로필 태그, 판정 상태, 검토 압력을 함께 엮어 만든 것입니다."
    if section.section_type == "mainline_decision":
        return f"{topic}의 주요 판정은 지지 근거, 반대 근거, 구조 우선순위를 함께 비교한 뒤 답변합니다."
    if section.section_type == "decision_knowledge_support":
        return f"검토된 지식은 {topic}의 용어와 경계를 보조하며 판정을 대체하지 않습니다."
    if section.section_type == "decision_next_step":
        return f"추천 후속 질문은 {topic}의 현재 판정 근거 안에서 유지됩니다."
    if section.section_type == "measurement_next_step":
        return f"다음 검토는 고정 판단이 아니라 출처 특징을 통해 {topic}을 더 깊게 읽는 것입니다."
    if section.section_type == "prediction_boundary":
        return "이 답변은 구조 해석과 후보 경로만 제시하며, 특징을 확정 사건이나 고정된 길흉 또는 근거 없는 시기로 바꾸지 않습니다."
    return f"분석 초점은 {topic}에 머무릅니다. 이 단락은 컴파일된 출처 특징 {source_count}개로 뒷받침되며 근거 경계를 유지합니다."
