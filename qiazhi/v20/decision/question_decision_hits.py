from __future__ import annotations

from collections.abc import Callable

from v20.features.schema import FeatureLayer
from v20.interaction.questions import QuestionCandidate
from v20.decision.question_config import QUESTION_KEY_BY_DOMAIN, QUESTION_STRATEGY


MakeQuestion = Callable[
    [str, str, str, float, FeatureLayer, dict[str, object] | None, str],
    QuestionCandidate,
]
AlignQuestion = Callable[[QuestionCandidate], QuestionCandidate | None]
CleanToken = Callable[[str], str]
NormalizeToken = Callable[[str], str]


def decision_hit_questions(
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
    *,
    make_question: MakeQuestion,
    align_question: AlignQuestion,
    clean_token: CleanToken,
    normalize_token: NormalizeToken,
    max_per_domain: int = 3,
    max_total: int = 14,
) -> list[QuestionCandidate]:
    rows: list[QuestionCandidate] = []
    hits = [row for row in decision_report.get("hits", ()) if isinstance(row, dict)]
    if not hits:
        return rows

    decisions = [row for row in decision_report.get("decisions", ()) if isinstance(row, dict)]
    by_rule = _decision_lookup_by_rule(decisions)

    counted: dict[str, int] = {}
    for hit in sorted(hits, key=lambda row: float(row.get("score", 0.0)), reverse=True):
        if len(rows) >= max_total:
            break
        domain = str(hit.get("domain", ""))
        key = QUESTION_KEY_BY_DOMAIN.get(domain)
        if not key:
            continue
        if counted.get(key, 0) >= max_per_domain:
            continue
        if str(hit.get("score", 0.0)) and float(hit.get("score", 0.0)) < 0.18:
            continue
        decision = by_rule.get(str(hit.get("rule_key", "")), None)
        title = _hit_question_title(hit, decision, clean_token=clean_token, normalize_token=normalize_token)
        if not title:
            continue
        count = max(float(hit.get("score", 0.0)), 0.0) + 0.01
        candidate = make_question(
            key,
            title,
            domain,
            round(count, 3),
            feature_layer,
            decision,
            QUESTION_STRATEGY["decision_hit"],
        )
        aligned = align_question(candidate)
        if aligned is None:
            continue
        rows.append(aligned)
        counted[key] = counted.get(key, 0) + 1
    return rows


def _decision_lookup_by_rule(decisions: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    lookup: dict[str, dict[str, object]] = {}
    for decision in decisions:
        rule_key = str(decision.get("rule_key", ""))
        if rule_key:
            lookup[rule_key] = decision
    return lookup


def _hit_question_title(
    hit: dict[str, object],
    source_decision: dict[str, object] | None,
    *,
    clean_token: CleanToken,
    normalize_token: NormalizeToken,
) -> str:
    status = str(hit.get("status", ""))
    label = str(hit.get("label", "")).strip()
    if not label:
        return ""
    material = _hit_focus_material(hit, clean_token=clean_token, normalize_token=normalize_token)
    domain = str(hit.get("domain", ""))
    boundary = "结构" if not material else material
    base = f"{label}里{boundary}更明显时"
    if source_decision is None and status in {"confirmed", "weakened_by_resource", "weak_candidate", "chain_candidate"}:
        if domain == "career":
            return f"{base}，先看事业主线顺序如何？"
        if domain == "wealth":
            return f"{base}，先看财运承载和通道优先级。"
        if domain == "strength":
            return f"{base}，日主承载与泄耗谁先成立？"
        if domain == "branch" or domain == "relationship":
            return f"{base}，先看先后牵发顺序。"
        if domain == "health":
            return f"{base}，平衡压力在哪个层面先看？"
        return f"{base}，先看关键结构再定顺序。"

    if source_decision is not None:
        decision_title = _append_mainline_tail(str(source_decision.get("label", "")), status)
        if decision_title:
            return f"{base}，{decision_title}"

    return _append_mainline_tail(base, status)


def _append_mainline_tail(text: str, state: str) -> str:
    if "地支互动" in text and "冲合刑害" not in text:
        text = text.replace("地支互动", "地支冲合刑害")
    if "地支关系" in text and "冲合刑害" not in text:
        text = text.replace("地支关系", "地支冲合刑害")
    suffix = {
        "confirmed": "直接可作为首轮测算链路。",
        "weak_candidate": "先确认可复核边界。",
        "candidate": "先看支持证据是否连续。",
        "chain_candidate": "先看链条先后。",
        "volatile": "先看岁运触发顺序。",
        "requires_review": "先补齐反向约束。",
        "chain_review": "先做冲突优先级排序。",
        "mixed": "先按主次拆开比较。",
    }.get(state, "先看可复核动作。")
    return f"{text}{text.endswith('。') and '' or '，'}{suffix}" if not text.endswith("？") else text


def _hit_focus_material(
    hit: dict[str, object],
    *,
    clean_token: CleanToken,
    normalize_token: NormalizeToken,
) -> str:
    materials: list[str] = []
    for token in tuple(hit.get("evidence", ())):
        text = normalize_token(str(token))
        text = clean_token(text)
        if not text:
            continue
        if text not in materials:
            materials.append(text)
        if len(materials) >= 2:
            break
    if not materials:
        return ""
    return "、".join(materials)
