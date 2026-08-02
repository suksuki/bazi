from __future__ import annotations

import re

from abu_v60.mingli.agent_adjudication import AgentHypothesis, AgentMethodRuling
from abu_v60.mingli.agent_contracts import AgentTimingCoordinate

_CHECK_LIMIT_COPY = {
    "SOURCE_AND_TARGET_SAME_LAYER": "食伤来源与官杀目标能否在同一层真正相接，仍需复核",
}


def method_bound_working_thesis(hypothesis: AgentHypothesis) -> str:
    """Express the selected path through its actual rulings, not model hyperbole."""

    support = [
        _clean_ruling_copy(item.rationale)
        for item in hypothesis.method_rulings
        if item.ruling == "SUPPORTS"
    ][:2]
    conditional = [
        _limit_ruling_copy(item)
        for item in hypothesis.method_rulings
        if item.ruling == "CONDITIONAL"
    ]
    unresolved = [
        _limit_ruling_copy(item)
        for item in hypothesis.method_rulings
        if item.ruling in {"UNRESOLVED", "OPPOSES"}
    ]
    limits = [*conditional[:1], *unresolved[:1]]
    if len(limits) < 2:
        limits.extend(conditional[1 : 3 - len(limits)])
    statement = f"暂以{hypothesis.name}作为整盘工作主线"
    if support:
        statement += f"：{'；'.join(support)}"
    if limits:
        statement += f"。但{'；'.join(limits)}"
    return f"{statement.rstrip('；。')}。"[:360]


def primary_limit(primary: AgentHypothesis) -> str:
    limiting = next(
        (
            item
            for item in primary.method_rulings
            if item.ruling in {"CONDITIONAL", "UNRESOLVED", "OPPOSES"}
        ),
        None,
    )
    if limiting is None:
        return f"仍需逐项验证{primary.name}的成立条件"
    return _limit_ruling_copy(limiting)


def method_bound_timing_statement(
    *,
    primary: AgentHypothesis,
    coordinate: AgentTimingCoordinate,
    period_label: str,
    period_scope: str,
) -> str:
    """Project the selected coordinate without inventing event or intensity."""

    return (
        f"{coordinate.pillar}{period_label}把{coordinate.ten_god_label}带到{period_scope}的明处，"
        f"相关议题会比原局更直接地接受检验。对“{primary.name}”而言，"
        f"这不等于结果已经发生；能否真正推动主线，仍取决于{primary_limit(primary)}。"
    )[:360]


def method_bound_timing_chain(
    *,
    primary: AgentHypothesis,
    coordinate: AgentTimingCoordinate,
    period_label: str,
) -> tuple[str, ...]:
    return (
        f"{coordinate.pillar}{period_label}进入",
        f"{coordinate.ten_god_label}在该层天干显露",
        f"检验{primary.name}的成立条件",
    )


def _clean_ruling_copy(value: str) -> str:
    value = value.replace(
        "原回答描述了阻断，却没有说明阻断如何解除；本项仍未决。",
        "当前命盘里，这项阻断尚未找到清楚的解除路径；因此仍需复核。",
    ).replace(
        "显藏或柱位事实不支持原判断；本项仍未决。",
        "显藏或柱位事实与这项判断冲突；因此仍需复核。",
    )
    value = re.sub(
        r"(?:此项(?:通过|成立条件明确|为关键限制点|为潜在弱点))。?",
        "",
        value,
    )
    return value.strip().strip("；。")


def _limit_ruling_copy(ruling: AgentMethodRuling) -> str:
    return _CHECK_LIMIT_COPY.get(
        ruling.check_code,
        _clean_ruling_copy(ruling.rationale),
    )
