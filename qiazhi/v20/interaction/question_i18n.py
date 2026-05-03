from __future__ import annotations

from dataclasses import replace

from v20.interaction.questions import QuestionCandidate


DOMAIN_LABELS = {
    "zh": {
        "strength": "日主承载", "wealth": "财运", "career": "事业",
        "ten_god": "十神", "branch": "地支", "time": "大运流年",
        "element": "五行", "useful_god": "用神", "pattern": "格局",
        "relationship": "关系", "health": "身心平衡", "_": "命理主线",
    },
    "en": {
        "strength": "day-master capacity", "wealth": "wealth structure", "career": "career structure",
        "ten_god": "Ten Gods", "branch": "branch interactions", "time": "luck and timing",
        "element": "five-element balance", "useful_god": "useful-god direction", "pattern": "pattern review",
        "relationship": "relationship structure", "health": "wellbeing balance", "_": "Bazi structure",
    },
    "ko": {
        "strength": "일간 감당력", "wealth": "재운 구조", "career": "직업 구조",
        "ten_god": "십성", "branch": "지지 작용", "time": "대운과 세운",
        "element": "오행 균형", "useful_god": "용신 방향", "pattern": "격국 검토",
        "relationship": "관계 구조", "health": "심신 균형", "_": "사주 구조",
    },
}


QUESTION_TEMPLATES = {
    "zh": {
        "q_strength_assessment": "{domain}上，先判断承载力还是压力来源？",
        "q_useful_god_candidates": "{domain}上，扶身、通关还是调候更像主线？",
        "q_useful_god_evidence_gaps": "{domain}还缺哪类关键证据？",
        "q_ten_god_focus": "{domain}里，哪组十神关系最值得先看？",
        "q_ten_god_metadata": "{domain}信息应该怎么进入测算主线？",
        "q_element_balance": "{domain}现在更偏向补短板还是疏导过旺？",
        "q_element_support_pressure": "{domain}带来的优势和压力分别在哪里？",
        "q_hidden_stem_role": "藏干里有哪些容易被忽略的命理线索？",
        "q_branch_relation_detail": "{domain}里，冲合刑害哪条先牵动主线？",
        "q_time_vs_natal_relation": "原局和时间层应该怎样分开判断？",
        "q_time_layer_context": "{domain}会先牵动事业、财运还是关系？",
        "q_time_relation_triggers": "{domain}当前最容易触发哪条主线？",
        "q_structure_overview": "这个八字的整体结构主线是什么？",
        "q_income_stability": "{domain}上，先看机会、承接还是波动？",
        "q_income_factors": "{domain}的机会和限制分别在哪里？",
        "q_career_structure": "{domain}上，规则压力、个人表达和平台资源谁更主导？",
        "q_relationship_structure": "{domain}里，互动模式、现实承接还是边界更关键？",
        "q_health_balance_boundary": "{domain}上，主要提示哪类节律和压力边界？",
        "q_pattern_structure": "{domain}上，先看成形主轴还是破局点？",
        "_": "{domain}这条线，下一步先看机会、压力还是边界？",
    },
    "en": {
        "q_strength_assessment": "For {domain}, should we first read capacity or pressure?",
        "q_useful_god_candidates": "For {domain}, is support, mediation, or climate adjustment the clearer path?",
        "q_useful_god_evidence_gaps": "What evidence is still missing for {domain}?",
        "q_ten_god_focus": "Which Ten-God relationship should we read first?",
        "q_ten_god_metadata": "How should the Ten-God signals enter the reading?",
        "q_element_balance": "For {domain}, should we first balance the weak side or release excess pressure?",
        "q_element_support_pressure": "Where do the strengths and pressures of {domain} show up?",
        "q_hidden_stem_role": "Which hidden-stem signals are easy to miss in this chart?",
        "q_branch_relation_detail": "Within {domain}, which clash, combination, punishment, or harm matters first?",
        "q_time_vs_natal_relation": "How should we separate the natal chart from timing layers?",
        "q_time_layer_context": "Does {domain} first activate career, wealth, or relationships?",
        "q_time_relation_triggers": "Which main line is most likely to be activated by {domain}?",
        "q_structure_overview": "What is the main structural line of this Bazi chart?",
        "q_income_stability": "For {domain}, should we first read opportunity, capacity, or volatility?",
        "q_income_factors": "Where are the opportunities and limits in {domain}?",
        "q_career_structure": "For {domain}, what leads: rules, personal expression, or platform resources?",
        "q_relationship_structure": "For {domain}, is interaction style, real-world support, or boundary pressure more important?",
        "q_health_balance_boundary": "For {domain}, what rhythm or pressure boundary is most visible?",
        "q_pattern_structure": "For {domain}, should we first read the forming axis or the breaking point?",
        "_": "For {domain}, should we next read opportunity, pressure, or boundary?",
    },
    "ko": {
        "q_strength_assessment": "{domain}에서는 먼저 감당력과 압력 중 무엇을 봐야 할까요?",
        "q_useful_god_candidates": "{domain}에서는 부조, 통관, 조후 중 어느 길이 더 분명할까요?",
        "q_useful_god_evidence_gaps": "{domain} 판단에는 어떤 근거가 더 필요할까요?",
        "q_ten_god_focus": "{domain}에서 어떤 십성 관계를 먼저 봐야 할까요?",
        "q_ten_god_metadata": "십성 정보는 이 분석에 어떻게 들어가야 할까요?",
        "q_element_balance": "{domain}에서는 부족한 쪽 보완과 과한 쪽 소통 중 무엇이 먼저일까요?",
        "q_element_support_pressure": "{domain}의 장점과 압력은 각각 어디에 나타날까요?",
        "q_hidden_stem_role": "장간에서 놓치기 쉬운 사주 단서는 무엇일까요?",
        "q_branch_relation_detail": "{domain}에서 충, 합, 형, 해 중 어느 작용이 먼저일까요?",
        "q_time_vs_natal_relation": "원국과 시간층은 어떻게 나누어 봐야 할까요?",
        "q_time_layer_context": "{domain}는 직업, 재운, 관계 중 무엇을 먼저 건드릴까요?",
        "q_time_relation_triggers": "{domain}가 지금 가장 쉽게 촉발하는 주선은 무엇일까요?",
        "q_structure_overview": "이 사주의 전체 구조 주선은 무엇일까요?",
        "q_income_stability": "{domain}에서는 기회, 감당력, 변동성 중 무엇을 먼저 볼까요?",
        "q_income_factors": "{domain}의 기회와 제한은 각각 어디에 있을까요?",
        "q_career_structure": "{domain}에서는 규칙 압력, 자기 표현, 플랫폼 자원 중 무엇이 주도할까요?",
        "q_relationship_structure": "{domain}에서는 상호작용, 현실적 지지, 경계 압력 중 무엇이 핵심일까요?",
        "q_health_balance_boundary": "{domain}에서는 어떤 리듬과 압력 경계가 가장 뚜렷할까요?",
        "q_pattern_structure": "{domain}에서는 형성되는 축과 깨지는 지점 중 무엇을 먼저 볼까요?",
        "_": "{domain}에서는 다음에 기회, 압력, 경계 중 무엇을 먼저 볼까요?",
    },
}


BOUNDARY_TEXT = {
    "zh": "只回答当前八字结构里已经看到的线索，不直接下固定吉凶。",
    "en": "This question stays within visible Bazi structure and does not make fixed fortune claims.",
    "ko": "이 질문은 보이는 사주 구조 안에서만 답하며 고정된 길흉 단정은 하지 않습니다.",
}


def localize_question_candidates(
    questions: tuple[QuestionCandidate, ...],
    *,
    locale: str = "zh",
) -> tuple[QuestionCandidate, ...]:
    lang = _locale_key(locale)
    return tuple(localize_question_candidate(row, locale=lang, index=index) for index, row in enumerate(questions))


def localize_question_candidate(
    question: QuestionCandidate,
    *,
    locale: str = "zh",
    index: int = 0,
) -> QuestionCandidate:
    lang = _locale_key(locale)
    if lang == "zh":
        return replace(
            question,
            boundary=_clean_zh_boundary(question.boundary),
            measurement_topic=_domain_label(question.domain, lang),
        )
    title = _localized_title(question, lang, index)
    return replace(
        question,
        title=title,
        boundary=BOUNDARY_TEXT[lang],
        measurement_topic=_domain_label(question.domain, lang),
        bazi_focus=BOUNDARY_TEXT[lang] if question.bazi_focus else "",
        source_decision_status="",
        source_decision_label="",
        question_strategy=_localized_strategy(question.question_strategy, lang),
    )


def _localized_title(question: QuestionCandidate, lang: str, index: int) -> str:
    domain = _domain_label(question.domain, lang)
    templates = QUESTION_TEMPLATES[lang]
    template = templates.get(question.question_key, templates["_"])
    title = template.format(domain=domain)
    if question.question_strategy == "agent_followup":
        return _followup_title(question.domain, lang, index)
    return title


def _followup_title(domain: str, lang: str, index: int) -> str:
    labels = DOMAIN_LABELS[lang]
    domain_label = labels.get(domain, labels["_"])
    if lang == "en":
        rows = (
            f"For {domain_label}, what should we confirm next?",
            f"Which evidence would make the {domain_label} reading clearer?",
            f"Should the next step focus on structure or timing for {domain_label}?",
        )
    elif lang == "ko":
        rows = (
            f"{domain_label}에서 다음으로 무엇을 확인할까요?",
            f"{domain_label} 판단을 더 분명하게 할 근거는 무엇일까요?",
            f"{domain_label}는 구조와 시기 중 무엇을 먼저 볼까요?",
        )
    else:
        rows = (
            f"{domain_label}这条线，下一步先确认什么？",
            f"{domain_label}还需要哪类证据来定重点？",
            f"{domain_label}继续看结构主轴还是时间触发？",
        )
    return rows[index % len(rows)]


def _domain_label(domain: str, lang: str) -> str:
    labels = DOMAIN_LABELS[lang]
    return labels.get(domain, labels["_"])


def _localized_strategy(strategy: str, lang: str) -> str:
    if lang == "en":
        return "recommended"
    if lang == "ko":
        return "추천"
    return strategy


def _clean_zh_boundary(boundary: str) -> str:
    text = str(boundary or "").strip()
    if not text or any(token in text.lower() for token in ("feature spine", "rule.", "evidence.")):
        return BOUNDARY_TEXT["zh"]
    return text


def _locale_key(locale: str) -> str:
    value = str(locale or "zh").lower()
    if value.startswith("en"):
        return "en"
    if value.startswith("ko"):
        return "ko"
    return "zh"
