from __future__ import annotations

import hashlib
import re
from typing import Any

from v30.contracts import CoreRuntimeResult
from v30.dialogue_chain.contracts import BaziDialogueSeed, MacroDomain


DOMAIN_KEYWORDS: dict[MacroDomain, tuple[str, ...]] = {
    "wealth": ("财", "钱", "收入", "赚钱", "投资", "现金流", "分配", "正财", "偏财", "财运"),
    "career": ("事业", "工作", "职业", "岗位", "升职", "创业", "转型", "平台", "职责"),
    "relationship": ("感情", "婚姻", "爱情", "伴侣", "关系", "桃花", "相处"),
    "health": ("健康", "身体", "疾病", "病", "睡眠", "压力", "消耗"),
    "family": ("家庭", "父母", "子女", "亲情", "家里", "长辈"),
    "timing": ("今年", "明年", "最近", "什么时候", "哪年", "大运", "流年", "月份"),
    "decision": ("选择", "决策", "盲点", "注意", "该不该", "适不适合", "风险"),
    "useful_god": ("用神", "忌神", "喜神", "取用", "调候"),
    "structure": ("格局", "旺衰", "身强", "身弱", "结构", "十神"),
    "overview": ("总体", "整体", "命盘", "八字", "综合"),
}

DOMAIN_LABELS: dict[str, str] = {
    "wealth": "财务",
    "career": "事业",
    "relationship": "关系",
    "health": "健康",
    "family": "亲情",
    "timing": "时运",
    "decision": "决策",
    "useful_god": "用神",
    "structure": "结构",
    "overview": "总览",
}

DEFAULT_SEED_TEXTS: tuple[tuple[MacroDomain, str], ...] = (
    ("wealth", "我今年财运如何？"),
    ("career", "事业适合稳定发展还是转型突破？"),
    ("relationship", "感情关系里最容易反复的问题是什么？"),
    ("useful_god", "这个八字的用神和忌神重点在哪里？"),
    ("decision", "这个八字最需要注意的决策盲点是什么？"),
)


def route_dialogue_seed(
    runtime: CoreRuntimeResult,
    raw_text: str,
    *,
    source: str = "user",
    stage_id: str = "",
) -> BaziDialogueSeed:
    text = _normalize_text(raw_text)
    domain = _detect_domain(text)
    topics = _detect_bazi_topics(text, domain)
    time_scope = _detect_time_scope(text)
    user_intent = _detect_user_intent(text)
    answer_priority = "calibrate_first" if "hidden_factor" in topics else "answer_first"
    if user_intent == "open_chat" and len(text) < 4:
        answer_priority = "clarify_first"
    return BaziDialogueSeed(
        seed_id=_seed_id(runtime.reading_id, text, source),
        reading_id=runtime.reading_id,
        source=_source(source),
        raw_text=raw_text.strip(),
        normalized_question=_normalize_question(text, domain),
        macro_domain=domain,
        bazi_topics=topics,
        time_scope=time_scope,
        user_intent=user_intent,
        answer_priority=answer_priority,
        confidence=_confidence(text, domain),
        evidence_binding=_evidence_binding(runtime, domain),
        stage_id=stage_id,
    )


def build_seed_suggestions(runtime: CoreRuntimeResult) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    for domain, text in DEFAULT_SEED_TEXTS:
        seed = route_dialogue_seed(runtime, text, source="system")
        suggestions.append(
            {
                "seed_id": seed.seed_id,
                "label": text,
                "macro_domain": domain,
                "domain_label": DOMAIN_LABELS.get(domain, domain),
                "time_scope": seed.time_scope,
                "user_intent": seed.user_intent,
                "priority": _seed_priority(runtime, domain),
                "boundary": "dialogue_seed_suggestion_starts_session_not_chart_fact",
            }
        )
    return sorted(suggestions, key=lambda row: float(row.get("priority") or 0), reverse=True)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").strip())


def _detect_domain(text: str) -> MacroDomain:
    if not text:
        return "overview"
    hits: dict[str, int] = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score:
            hits[domain] = score
    if "财" in text and ("今年" in text or "流年" in text):
        return "wealth"
    if "创业" in text and "财" in text:
        return "wealth"
    if not hits:
        return "overview"
    priority = ["wealth", "career", "relationship", "health", "family", "useful_god", "structure", "decision", "timing", "overview"]
    return max(hits, key=lambda domain: (hits[domain], -priority.index(domain) if domain in priority else -999))  # type: ignore[return-value]


def _detect_bazi_topics(text: str, domain: MacroDomain) -> list[str]:
    topics: list[str] = []
    if any(token in text for token in ("十神", "正财", "偏财", "官杀", "印星", "食伤", "比劫")):
        topics.append("ten_god")
    if any(token in text for token in ("用神", "忌神", "喜神", "调候")) or domain == "useful_god":
        topics.append("useful_god")
    if any(token in text for token in ("格局", "旺衰", "身强", "身弱", "结构")) or domain == "structure":
        topics.append("structure")
    if any(token in text for token in ("路径", "做功", "流向", "承接")):
        topics.append("path")
    if "大运" in text:
        topics.append("luck_cycle")
    if "流年" in text or "今年" in text or "明年" in text:
        topics.append("flow_year")
    if any(token in text for token in ("隐藏", "明珠暗投", "反复", "校准")):
        topics.append("hidden_factor")
    if domain in ("wealth", "career", "relationship", "health", "family", "decision"):
        topics.append("verdict")
    return list(dict.fromkeys(topics or ["verdict"]))


def _detect_time_scope(text: str) -> str:
    if "今年" in text or "流年" in text or re.search(r"20\d{2}", text):
        return "current_year"
    if "大运" in text:
        return "current_luck"
    if "月" in text:
        return "month"
    return "natal"


def _detect_user_intent(text: str) -> str:
    if not text:
        return "open_chat"
    if any(token in text for token in ("适合", "还是", "该不该", "选", "创业")):
        return "compare_options"
    if any(token in text for token in ("建议", "注意", "怎么", "怎么办", "如何做")):
        return "ask_advice"
    if any(token in text for token in ("验证", "过去", "发生", "哪年")):
        return "verify_event"
    return "ask_conclusion"


def _normalize_question(text: str, domain: MacroDomain) -> str:
    if text:
        return text if text.endswith(("？", "?")) else f"{text}？"
    return f"继续看{DOMAIN_LABELS.get(domain, '八字')}？"


def _source(value: str) -> str:
    return value if value in {"system", "user", "practitioner", "training"} else "user"


def _seed_id(reading_id: str, text: str, source: str) -> str:
    digest = hashlib.sha1(f"{reading_id}|{source}|{text}".encode("utf-8")).hexdigest()[:10]
    return f"dlg_seed_{digest}"


def _confidence(text: str, domain: MacroDomain) -> float:
    if not text:
        return 0.42
    if domain != "overview":
        return 0.82
    return 0.62


def _evidence_binding(runtime: CoreRuntimeResult, domain: MacroDomain) -> list[str]:
    rows: list[str] = []
    for evidence in runtime.feature_evidence:
        if evidence.domain in {domain, "structure"}:
            rows.append(evidence.evidence_id)
    if runtime.mainline_state.domain == domain:
        rows.extend(runtime.mainline_state.evidence_ids)
    return list(dict.fromkeys(rows))[:8]


def _seed_priority(runtime: CoreRuntimeResult, domain: MacroDomain) -> float:
    if runtime.mainline_state.domain == domain:
        return 0.92
    if domain in {"wealth", "career", "relationship"}:
        return 0.82
    if domain == "useful_god":
        return 0.78
    return 0.68
