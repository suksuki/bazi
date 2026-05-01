from __future__ import annotations

from v20.answer.plan import AnswerPlan
from v20.i18n.terminology import localized_section_body, localized_section_title


def compose_answer(plan: AnswerPlan, *, locale: str = "zh") -> str:
    if locale.startswith("zh"):
        return _compose_zh(plan)
    if locale.startswith("ko"):
        return _compose_ko(plan)
    return _compose_en(plan)


def _compose_en(plan: AnswerPlan) -> str:
    lines = ["Bazi measurement focus: structure, evidence, and bounded candidate paths."]
    for section in plan.sections:
        lines.append(f"{localized_section_title(section, 'en')}: {localized_section_body(section, 'en')}")
    lines.append("No certain event, fixed fortune verdict, or unsupported timing claim is produced.")
    return "\n\n".join(lines)


def _compose_zh(plan: AnswerPlan) -> str:
    lines = ["八字测算重点：结构、证据与有边界的候选路径。"]
    for section in plan.sections:
        lines.append(f"{section.title}: {section.body}")
    lines.append("不生成确定事件、固定吉凶或无时间层支持的具体时间点。")
    return "\n\n".join(lines)


def _compose_ko(plan: AnswerPlan) -> str:
    lines = ["사주 측산의 초점은 구조, 근거, 경계가 있는 후보 경로입니다."]
    for section in plan.sections:
        lines.append(f"{localized_section_title(section, 'ko')}: {localized_section_body(section, 'ko')}")
    lines.append("확정 사건, 고정된 길흉 판단, 시간층 근거가 없는 구체적 시기는 생성하지 않습니다.")
    return "\n\n".join(lines)
