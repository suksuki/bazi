from __future__ import annotations

from collections.abc import Callable, Iterable

from v20.core.schemas import TimeContext
from v20.features.schema import FeatureLayer
from v20.interaction.questions import QuestionCandidate
from v20.decision.question_config import QUESTION_KEY_BY_DOMAIN, QUESTION_STRATEGY


MakeQuestion = Callable[
    [str, str, str, float, FeatureLayer, dict[str, object] | None, str],
    QuestionCandidate,
]
AlignQuestion = Callable[[QuestionCandidate], QuestionCandidate | None]
QuestionTitle = Callable[[dict[str, object], FeatureLayer], str]
StateBoost = Callable[[str], float]


def mainline_questions(
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
    *,
    make_question: MakeQuestion,
    align_question: AlignQuestion,
    question_title: QuestionTitle,
    state_boost: StateBoost,
) -> list[QuestionCandidate]:
    rows: list[QuestionCandidate] = []
    mainlines = [row for row in decision_report.get("mainlines", ()) if isinstance(row, dict)]
    decision_by_key = {
        str(row.get("decision_key", "")): row
        for row in decision_report.get("decisions", ())
        if isinstance(row, dict)
    }
    used_domains: set[str] = set()
    for index, mainline in enumerate(mainlines[:4]):
        domain = str(mainline.get("domain", ""))
        key = QUESTION_KEY_BY_DOMAIN.get(domain)
        if not key:
            continue
        source_decision_keys = tuple(str(row) for row in mainline.get("source_decision_keys", ()) if str(row))
        source_decisions = tuple(
            decision_by_key[row_key]
            for row_key in source_decision_keys
            if row_key in decision_by_key
        )
        is_rulespec = _is_rulespec_mainline(mainline)
        if is_rulespec and domain in used_domains:
            continue
        if is_rulespec and not _mainline_needs_rulespec_prompt(mainline, decision_by_key.values()):
            continue
        title = _mainline_title(mainline, source_decisions, feature_layer, question_title=question_title)
        score = float(mainline.get("score", 0.0))
        status = str(mainline.get("status", ""))
        title = _decorate_mainline_title(title, str(mainline.get("title", "")), status)
        candidate = make_question(
            key,
            title,
            domain,
            round(score + 0.09 - index * 0.01 + state_boost(status), 3),
            feature_layer,
            source_decisions[0] if source_decisions else mainline,
            QUESTION_STRATEGY["mainline_candidate"],
        )
        aligned = align_question(candidate)
        if aligned:
            rows.append(aligned)
        used_domains.add(domain)
    return rows


def time_context_questions(
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
    time_context: TimeContext,
    *,
    make_question: MakeQuestion,
    align_question: AlignQuestion,
) -> list[QuestionCandidate]:
    rows: list[QuestionCandidate] = []
    if not isinstance(time_context, TimeContext):
        return rows
    if not time_context.layers:
        return rows
    layer_descriptions = [
        f"{row.layer_key}:{row.pillar.display} ({row.ten_god.label})"
        for row in time_context.layers
        if row is not None
    ]
    relation_count = len(time_context.relation_hits)
    base = 0.86 + min(0.09, len(time_context.layers) * 0.03 + relation_count * 0.015)
    source_decision = _time_context_decision(decision_report)

    rows.append(
        make_question(
            "q_time_layer_context",
            f"{layer_descriptions[0]}是否先牵动事业、财运、关系中的哪条线？",
            "time",
            round(base, 3),
            feature_layer,
            source_decision,
            QUESTION_STRATEGY["time_context"],
        )
    )

    if relation_count:
        trigger = _time_trigger_hint(time_context)
        rows.append(
            make_question(
                "q_time_relation_triggers",
                f"{trigger}是否优先先触发了哪种交互？",
                "time",
                round(base - 0.01, 3),
                feature_layer,
                source_decision,
                QUESTION_STRATEGY["time_context"],
            )
        )
    else:
        rows.append(
            make_question(
                "q_time_relation_triggers",
                "大运流年更容易先触发哪类关系交互？",
                "time",
                round(base - 0.01, 3),
                feature_layer,
                source_decision,
                QUESTION_STRATEGY["time_context"],
            )
        )
    rows.append(
        make_question(
            "q_branch_relation_detail",
            "地支冲合刑害里哪些关系互动更值得先拆？",
            "branch",
            round(base - 0.09, 3),
            feature_layer,
            source_decision,
            QUESTION_STRATEGY["time_context"],
        )
    )
    return [row for row in (align_question(row) for row in rows) if row is not None]


def _is_rulespec_mainline(mainline: dict[str, object]) -> bool:
    if str(mainline.get("role", "")) == "primary_rulespec_bazi_mainline":
        return True
    return any(
        str(source).startswith("decision.rulespec.")
        for source in tuple(mainline.get("source_decision_keys", ()))
    )


def _mainline_needs_rulespec_prompt(
    mainline: dict[str, object],
    decisions: Iterable[object],
) -> bool:
    domain = str(mainline.get("domain", ""))
    if not domain:
        return True
    for row in decisions:
        if not isinstance(row, dict):
            continue
        if str(row.get("domain", "")) != domain:
            continue
        key = str(row.get("decision_key", "") or row.get("rule_key", ""))
        if key.startswith("decision.rulespec."):
            continue
        if str(row.get("role", "")) == "rulespec_context":
            continue
        return False
    return True


def _mainline_title(
    mainline: dict[str, object],
    source_decisions: tuple[dict[str, object], ...],
    feature_layer: FeatureLayer,
    *,
    question_title: QuestionTitle,
) -> str:
    seed = str(mainline.get("question_seed", "")).strip()
    if _is_rulespec_mainline(mainline) and source_decisions:
        for source in source_decisions:
            candidate = question_title(source, feature_layer)
            if candidate:
                return candidate
    if seed and _is_mainline_seed_ok(seed):
        return f"{seed}"
    if _is_rulespec_mainline(mainline):
        return _rulespec_mainline_template(str(mainline.get("domain", "")))
    title = str(mainline.get("title", "")).strip()
    if title:
        return f"{title}如何进入本次测算？"
    return "这个主线现在应从哪条证据先入手？"


def _is_mainline_seed_ok(seed: str) -> bool:
    return bool(seed) and "规则" not in seed and "明确成立" not in seed and "候选" not in seed


def _decorate_mainline_title(title: str, label: str, status: str) -> str:
    if not title:
        return title
    if status in {"chain_review", "requires_review"}:
        return f"{title}先做哪一步复核？"
    if status in {"countered", "blocked"}:
        return f"{title}有没有先级更高的牵引问题？"
    if not label:
        return title
    return title


def _rulespec_mainline_template(domain: str) -> str:
    if domain == "strength":
        return "日主强弱先看承载与泄耗？"
    if domain == "wealth":
        return "财运主线先看承接后看机会与通道？"
    if domain == "career":
        return "事业先看官星、伤官与印星谁主导？"
    if domain == "ten_god":
        return "十神结构先看明透或藏干？"
    if domain == "pattern":
        return "格局先复核哪些关键条件？"
    if domain == "branch":
        return "先看地支冲合刑害中的主要作用？"
    if domain == "time":
        return "先看大运流年是先触发哪条关系？"
    if domain == "useful_god":
        return "这个盘的用神和调节方向是什么？"
    if domain == "relationship":
        return "关系先看互动、承接还是约束？"
    if domain == "health":
        return "健康先看五行平衡边界吗？"
    if domain == "element":
        return "五行先看偏向与压力？"
    return "这条主线先从哪些结构切入？"


def _time_context_decision(decision_report: dict[str, object]) -> dict[str, object]:
    time_decisions = [
        row for row in decision_report.get("decisions", ())
        if isinstance(row, dict) and str(row.get("domain", "")) == "time"
    ]
    if time_decisions:
        return time_decisions[0]
    return {"feature_ids": (), "score": 0.66, "status": "candidate", "decision_key": "decision.time.synthetic"}


def _time_trigger_hint(time_context: TimeContext) -> str:
    if not time_context.relation_hits:
        return "时运层位置信息"
    first = list(time_context.relation_hits)[0]
    relation = str(first.relation_type or "关系变化")
    if "冲" in relation:
        return "地支冲合"
    if "合" in relation:
        return "合化"
    if "刑" in relation:
        return "刑害"
    if "害" in relation:
        return "三刑"
    return "关系变化"
