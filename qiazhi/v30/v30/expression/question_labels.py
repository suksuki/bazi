from __future__ import annotations

from pydantic import Field

from v30.contracts import BaziQuestionAnchor, ClientKey, LocaleKey, RoleKey, V30Model
from v30.expression.style import resolve_style_profile


QUESTION_LABEL_RENDERER_VERSION = "v30.expression.question_labels.v1"
FORBIDDEN_LABEL_TOKENS = (
    "policy_effect",
    "question_policy",
    "dynamic_graph",
    "evidence-bound",
    "Current chart",
    "Quality gate",
)


class RenderedQuestionLabel(V30Model):
    label_id: str
    version: str = QUESTION_LABEL_RENDERER_VERSION
    question_id: str
    role_key: RoleKey
    locale: LocaleKey
    client: ClientKey
    label: str
    source: str = "expression_rendered_question_label"
    boundary: str = "question_label_is_presentation_text_not_chart_fact"
    source_anchor_label: str = ""
    diagnostics: dict[str, object] = Field(default_factory=dict)


def render_question_label(
    anchor: BaziQuestionAnchor,
    recommendation: dict[str, object] | None = None,
    *,
    role_key: str = "user",
    locale: str = "zh",
    client: str = "web",
) -> RenderedQuestionLabel:
    recommendation = recommendation or {}
    style = resolve_style_profile(role_key=role_key, locale=locale, client=client)
    topic = str(recommendation.get("topic") or _topic_from_anchor(anchor))
    stage = str(recommendation.get("stage") or _stage_from_anchor(anchor))
    label = _label_text(anchor, topic=topic, stage=stage, locale=style.locale, compact=style.density == "compact")
    fallback = False
    if not label.strip():
        label = anchor.why_this_question
        fallback = True
    label = _compact_text(label, max_chars=44 if style.density == "compact" else 72)
    forbidden_hits = _forbidden_hits(label)
    if forbidden_hits:
        label = _compact_text(_safe_fallback(topic, style.locale), max_chars=44 if style.density == "compact" else 72)
        fallback = True
        forbidden_hits = _forbidden_hits(label)
    return RenderedQuestionLabel(
        label_id=f"{anchor.question_id}:rendered-label:{style.role_key}:{style.client}:{style.locale}",
        question_id=anchor.question_id,
        role_key=style.role_key,
        locale=style.locale,
        client=style.client,
        label=label,
        source_anchor_label=anchor.why_this_question,
        diagnostics={
            "topic": topic,
            "stage": stage,
            "density": style.density,
            "fallback_used": fallback,
            "forbidden_token_hits": forbidden_hits,
        },
    )


def summarize_question_labels(labels: list[RenderedQuestionLabel]) -> dict[str, object]:
    return {
        "version": QUESTION_LABEL_RENDERER_VERSION,
        "label_count": len(labels),
        "roles": sorted({row.role_key for row in labels}),
        "clients": sorted({row.client for row in labels}),
        "locales": sorted({row.locale for row in labels}),
        "fallback_count": sum(1 for row in labels if bool(row.diagnostics.get("fallback_used"))),
        "forbidden_token_hits": sorted({
            str(hit)
            for row in labels
            for hit in row.diagnostics.get("forbidden_token_hits", [])
        }),
        "boundary": "question_label_is_presentation_text_not_chart_fact",
    }


def _label_text(anchor: BaziQuestionAnchor, *, topic: str, stage: str, locale: str, compact: bool) -> str:
    if locale == "en":
        return _label_en(anchor, topic=topic, stage=stage, compact=compact)
    if locale == "ko":
        return _label_ko(anchor, topic=topic, stage=stage, compact=compact)
    return _label_zh(anchor, topic=topic, stage=stage, compact=compact)


def _label_zh(anchor: BaziQuestionAnchor, *, topic: str, stage: str, compact: bool) -> str:
    if anchor.intent_id == "ask_user_career_direction":
        return "事业适合稳定发展还是转型突破？"
    if anchor.intent_id == "ask_user_wealth_tendency":
        return "财运更适合主动争取还是保守积累？"
    if anchor.intent_id == "ask_user_relationship_pattern":
        return "感情关系里最容易反复的问题是什么？"
    if anchor.intent_id == "ask_user_timing_pressure":
        return "当前大运和流年压力主要体现在哪里？"
    if anchor.intent_id == "ask_user_decision_blindspot":
        return "这个八字最需要注意的决策盲点是什么？"
    if topic == "time_context":
        return "先补齐时柱与时间层边界" if compact else "先补齐时柱与时间层边界，再进入大运流年判断"
    if topic == "hidden_factor":
        return "确认特殊年份与重复状态" if compact else "确认特殊年份与重复状态，只作为校准线索"
    if topic == "useful_god":
        return "复核用神候选路径" if compact else "复核用神候选路径，不直接下固定用神结论"
    if topic == "structure_dynamic":
        return "复核结构动态路径" if compact else "复核结构动态路径，先看证据链再看结论边界"
    if anchor.missing_requirements or stage == "context_completion":
        return "先补齐关键上下文" if compact else "先补齐关键上下文，避免未确认条件下的断语"
    return "复核当前主线" if compact else "沿当前主线复核盘面证据与表达边界"


def _label_en(anchor: BaziQuestionAnchor, *, topic: str, stage: str, compact: bool) -> str:
    if anchor.intent_id == "ask_user_career_direction":
        return "Is my career better suited to stability or transition?"
    if anchor.intent_id == "ask_user_wealth_tendency":
        return "Should I pursue wealth actively or accumulate conservatively?"
    if anchor.intent_id == "ask_user_relationship_pattern":
        return "What relationship pattern is most likely to repeat?"
    if anchor.intent_id == "ask_user_timing_pressure":
        return "Where does current timing pressure show up most?"
    if anchor.intent_id == "ask_user_decision_blindspot":
        return "What decision blind spot should I watch most?"
    if topic == "time_context":
        return "Bind time context first" if compact else "Bind the hour and time-layer context before timing review"
    if topic == "hidden_factor":
        return "Check special years and repeats" if compact else "Check special years and repeated states as calibration clues"
    if topic == "useful_god":
        return "Review useful-god paths" if compact else "Review useful-god candidate paths without making a fixed verdict"
    if topic == "structure_dynamic":
        return "Review dynamic structure paths" if compact else "Review dynamic structure paths before drawing conclusions"
    if anchor.missing_requirements or stage == "context_completion":
        return "Complete key context first" if compact else "Complete key context before bounded interpretation"
    return "Review the current mainline" if compact else "Review the current mainline with evidence and boundaries"


def _label_ko(anchor: BaziQuestionAnchor, *, topic: str, stage: str, compact: bool) -> str:
    if anchor.intent_id == "ask_user_career_direction":
        return "커리어는 안정이 좋을까요, 전환이 좋을까요?"
    if anchor.intent_id == "ask_user_wealth_tendency":
        return "재물은 적극적으로 움직일까요, 보수적으로 쌓을까요?"
    if anchor.intent_id == "ask_user_relationship_pattern":
        return "관계에서 반복되기 쉬운 패턴은 무엇일까요?"
    if anchor.intent_id == "ask_user_timing_pressure":
        return "현재 운의 압박은 어디에 나타날까요?"
    if anchor.intent_id == "ask_user_decision_blindspot":
        return "가장 주의할 의사결정 맹점은 무엇일까요?"
    if topic == "time_context":
        return "시간 경계 먼저 확인" if compact else "시주와 시간 층위를 먼저 확인한 뒤 흐름을 봅니다"
    if topic == "hidden_factor":
        return "특수 연도와 반복 상태 확인" if compact else "특수 연도와 반복 상태를 보정 단서로 확인합니다"
    if topic == "useful_god":
        return "용신 후보 경로 검토" if compact else "용신 후보 경로를 검토하되 고정 결론은 내리지 않습니다"
    if topic == "structure_dynamic":
        return "구조 동역학 경로 검토" if compact else "구조 동역학 경로를 증거와 함께 검토합니다"
    if anchor.missing_requirements or stage == "context_completion":
        return "핵심 맥락 먼저 보완" if compact else "핵심 맥락을 먼저 보완해 단정을 피합니다"
    return "현재 주 흐름 검토" if compact else "현재 주 흐름을 증거와 경계 안에서 검토합니다"


def _topic_from_anchor(anchor: BaziQuestionAnchor) -> str:
    if anchor.intent_id == "discover_hidden_factor_amplifier":
        return "hidden_factor"
    if anchor.intent_id == "review_useful_god_candidate_paths":
        return "useful_god"
    if anchor.missing_requirements:
        return "time_context"
    return "mainline"


def _stage_from_anchor(anchor: BaziQuestionAnchor) -> str:
    if anchor.intent_id == "discover_hidden_factor_amplifier":
        return "dialogue_discovery"
    if anchor.missing_requirements:
        return "context_completion"
    if anchor.intent_id == "review_useful_god_candidate_paths":
        return "candidate_review"
    return "mainline_review"


def _safe_fallback(topic: str, locale: str) -> str:
    if locale == "en":
        return f"Review {topic.replace('_', ' ')} with boundaries"
    if locale == "ko":
        return "경계 안에서 질문을 검토합니다"
    return "在边界内复核这个问题"


def _compact_text(text: str, *, max_chars: int) -> str:
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    return text[: max(1, max_chars - 1)].rstrip() + "…"


def _forbidden_hits(text: str) -> list[str]:
    lower = text.lower()
    return [token for token in FORBIDDEN_LABEL_TOKENS if token.lower() in lower]
