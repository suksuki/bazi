from __future__ import annotations

import re

from v20.answer.plan import AnswerPlan
from v20.i18n.terminology import localized_section_body, localized_section_title

_NON_USER_VISIBLE_SECTION_TYPES = {
    "measurement_scope",
    "decision_knowledge_support",
    "decision_next_step",
}


def compose_answer(plan: AnswerPlan, *, locale: str = "zh") -> str:
    if locale.startswith("zh"):
        return _compose_zh(plan)
    if locale.startswith("ko"):
        return _compose_ko(plan)
    return _compose_en(plan)


def _compose_en(plan: AnswerPlan) -> str:
    lines = ["Bazi measurement focus: structure, evidence, and bounded candidate paths."]
    for section in plan.sections:
        if section.section_type in _NON_USER_VISIBLE_SECTION_TYPES:
            continue
        if section.section_type == "prediction_boundary":
            continue
        lines.append(f"{localized_section_title(section, 'en')}: {localized_section_body(section, 'en')}")
    lines.append("No certain event, fixed fortune verdict, or unsupported timing claim is produced.")
    return "\n\n".join(lines)


def _compose_zh(plan: AnswerPlan) -> str:
    lines = []
    question = _question_title_from_plan(plan)
    opening = _opening_from_plan(plan, question)
    if opening:
        lines.append(opening)
    direct_answer = _direct_answer_from_plan(plan, question)
    if direct_answer:
        lines.append(direct_answer)
    for section in plan.sections:
        if section.section_type in _NON_USER_VISIBLE_SECTION_TYPES:
            continue
        if section.section_type == "prediction_boundary":
            continue
        body = _clean_zh_body(section.body)
        if not body:
            continue
        if section.section_type == "portrait_projection_reading":
            lines.append(f"当前命局可见：{body}")
        else:
            lines.append(f"{section.title}：{body}")
    boundary = _boundary_from_plan(plan)
    if boundary:
        lines.append(f"边界：{boundary}")
    return "\n\n".join(lines)


def _compose_ko(plan: AnswerPlan) -> str:
    lines = ["사주 분석의 초점은 구조, 근거, 경계가 있는 후보 경로입니다."]
    for section in plan.sections:
        if section.section_type in _NON_USER_VISIBLE_SECTION_TYPES:
            continue
        if section.section_type == "prediction_boundary":
            continue
        lines.append(f"{localized_section_title(section, 'ko')}: {localized_section_body(section, 'ko')}")
    lines.append("확정 사건, 고정된 길흉 판단, 시간층 근거가 없는 구체적 시기는 생성하지 않습니다.")
    return "\n\n".join(lines)


def _question_title_from_plan(plan: AnswerPlan) -> str:
    for section in plan.sections:
        if section.section_type != "measurement_scope":
            continue
        match = re.search(r"「([^」]+)」", section.body)
        if match:
            return match.group(1)
    return ""


def _opening_from_plan(plan: AnswerPlan, question: str) -> str:
    domain = ""
    for section in plan.sections:
        if section.domain:
            domain = section.domain
            break
    if domain == "wealth":
        return "财运先看两件事：财星有没有形成机会，日主能不能承接。"
    if domain == "career":
        return "事业先看官杀、食伤表达和印星缓冲，判断压力、规则和发挥空间。"
    if domain == "relationship":
        return "关系先看配偶星、日支和冲合刑害，判断互动方式和需要复核的位置。"
    if domain == "health":
        return "健康只看五行偏枯和结构压力，不把命局线索写成医疗结论。"
    if domain == "time":
        return "大运流年先看时间层牵动原局哪一块，再判断它服务于哪条主线。"
    if domain == "useful_god":
        return "用神先看扶抑、通关和调候的候选方向，不直接定喜忌。"
    if domain == "strength":
        return "日主强弱先看月令、根气、生扶和压力，不靠单一十神下结论。"
    if domain == "branch":
        return "结构互动先看地支冲合刑害落在哪些柱，再看牵动的主题。"
    if domain == "element":
        return "五行分布先看偏显和偏弱，再回到日主承载与用神候选。"
    if question:
        return f"围绕「{question}」，先看当前盘已经成立的命局线索。"
    return "先看当前盘已经成立的命局线索。"


def _direct_answer_from_plan(plan: AnswerPlan, question: str) -> str:
    portrait = _portrait_projection_body(plan)
    if not question or not portrait:
        return ""
    if "伤官见官" in question:
        if "伤官见官见印缓冲" in portrait or "印星缓冲" in portrait:
            return "这个盘不能只按伤官见官直接下结论，要先看印星是否真正形成缓冲，再判断事业上的表达、规则和化解路径。"
        return "这个盘需要先确认伤官和官星是否同时成势，再判断它对事业表达和规则压力的影响。"
    if "食伤生财" in question:
        if "食伤生财需先过承载关" in portrait:
            return "这个盘有食伤生财线索，但要先过日主承载关；承接不足时，财星机会容易先表现为压力或消耗。"
        if "食伤生财承载需裁决" in portrait:
            return "这个盘食伤生财接近分界，先裁决日主承载，再看输出能否稳定接到财星。"
        return "这个盘可以从食伤生财看财运通道，但要同时检查输出、财星来源和承载闭合。"
    if "日主" in question or "强弱" in question:
        if "日主偏弱需扶身复核" in portrait or "日主需先看扶身" in portrait:
            return "这个盘日主承载力要先按偏弱扶身复核处理，先找印星、比劫和通关条件，再讨论财官食伤能否承接。"
        if "日主强弱接近分界" in portrait or "日主强弱需先裁决" in portrait:
            return "这个盘日主强弱接近分界，不能急着定强弱，要先比较扶身材料和泄耗克制材料哪边更成势。"
        if "日主有根气与生扶支撑" in portrait or "日主有支撑可承接" in portrait:
            return "这个盘日主有支撑，可以继续看泄秀、财星通道或官杀约束，但仍要看这些线索是否有证据闭合。"
        return "日主强弱先作为承载力门槛处理，再决定财星、官杀和用神候选能不能往下推。"
    if "财星" in question or "财运" in question:
        if "财星可见但日主承接需扶助" in portrait:
            return "财星已经可见，但重点不是先断机会大小，而是先看日主能不能承接，以及是否需要扶身或通关。"
        if "食伤生财通道" in portrait:
            return "财运可以从食伤生财通道切入，但还要看输出是否能稳定转成财星路径。"
        return "财运问题先看财星来源、日主承接和是否有通道，不单看有没有财星。"
    if "事业" in question:
        if "官伤印三方需要合参" in portrait or "事业需裁决官伤印主次" in portrait:
            return "事业不能只看官星或伤官单点，要把官星规则、伤官表达和印星缓冲放在一起裁决主次。"
        if "印星缓冲" in portrait:
            return "事业主线先看官杀压力、食伤表达和印星缓冲三方，不宜只按压力或表达单点判断。"
        return "事业主线先看角色、规则压力和表达方式，再回到日主承载力复核。"
    return ""


def _portrait_projection_body(plan: AnswerPlan) -> str:
    for section in plan.sections:
        if section.section_type == "portrait_projection_reading":
            return section.body
    return ""


def _boundary_from_plan(plan: AnswerPlan) -> str:
    for section in plan.sections:
        if section.section_type == "prediction_boundary":
            return (
                section.body
                .replace("当前回答只说明命局里已经看到的关系和下一步可复核方向，", "")
                .replace("不把它写成确定事件、固定吉凶或具体时间点。", "只说明已见结构和可复核方向，不作固定吉凶或具体时间断语。")
            )
    return "只说明已见结构和可复核方向，不作固定吉凶或具体时间断语。"


def _clean_zh_body(body: str) -> str:
    text = str(body or "").strip()
    if not text:
        return ""
    text = text.replace("。这些画像来自当前八字的实时排盘和规则判断，不使用离线语料静态标签作为结论。", "。")
    text = text.replace("这些画像来自当前八字的实时排盘和规则判断，不使用离线语料静态标签作为结论。", "")
    clauses = [clause.strip(" ；。") for clause in text.split("；") if clause.strip(" ；。")]
    if not clauses:
        return text
    compact = [_compact_clause(clause) for clause in clauses[:4]]
    return "；".join(row for row in compact if row).rstrip("。") + "。"


def _compact_clause(clause: str) -> str:
    if "：" not in clause:
        return clause
    label, support = clause.split("：", 1)
    pieces = [piece.strip() for piece in support.split("、") if piece.strip()]
    if len(pieces) > 3:
        support = "、".join(pieces[:3]) + "等"
    return f"{label.strip()}：{support.strip()}"
