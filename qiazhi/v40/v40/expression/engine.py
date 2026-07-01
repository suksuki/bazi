from __future__ import annotations

import re

from v40.contracts.base import RoleKey, Topic
from v40.contracts.output import (
    AcceptanceResult,
    AcceptanceStatus,
    ExpressionTelemetry,
    LLMExpressionResult,
    LLMExpressionTask,
)
from v40.contracts.runtime import RuntimeResult


LEAKAGE_TOKENS = [
    "policy_key",
    "training_target",
    "runtime_debug",
    "claim_key",
    "conflict_group_id",
    "DecisionEngine",
    "RuntimeSignal",
    "EvaluationRun",
    "release_gate",
    "source_ref",
]

OVERCLAIM_TOKENS = [
    "保证",
    "一定发财",
    "必然升职",
    "稳赚不赔",
    "百分百",
    "绝对会",
]

CHART_FACT_TOKENS = [
    "新增四柱",
    "改四柱",
    "出生时间应改为",
    "日主改为",
    "月令改为",
]


def build_expression_task_from_runtime(
    *,
    task_id: str,
    runtime: RuntimeResult,
    role_key: RoleKey | None = None,
    topic: Topic | None = None,
) -> LLMExpressionTask:
    projection = runtime.product_projection
    card_ids: list[str] = []
    if projection:
        card_ids.extend(card.card_id for card in projection.verdict_cards)
        card_ids.extend(card.card_id for card in projection.advice_cards)
        if (role_key or runtime.request.role_key) == "practitioner":
            card_ids.extend(card.card_id for card in projection.branch_cards)
    allowed_assertions = _allowed_assertions(runtime)
    forbidden_assertions = _forbidden_assertions(runtime)
    requested_topic = topic or runtime.request.topic
    locale_context = runtime.request.runtime_context.locale_context
    return LLMExpressionTask(
        task_id=task_id,
        reading_id=runtime.reading_id,
        role_key=role_key or runtime.request.role_key,
        locale_context=locale_context,
        output_language=locale_context.output_language,
        topic=requested_topic,
        input_card_ids=card_ids,
        instruction=_instruction(role_key=role_key or runtime.request.role_key),
        allowed_assertions=allowed_assertions,
        forbidden_assertions=forbidden_assertions,
    )


def render_local_expression_result(
    *,
    result_id: str,
    task: LLMExpressionTask,
    runtime: RuntimeResult,
    provider: str = "local_expression_adapter",
    model: str = "v40.expression.contract.v1",
) -> LLMExpressionResult:
    text = _render_text(runtime=runtime, role_key=task.role_key)
    return LLMExpressionResult(
        result_id=result_id,
        task_id=task.task_id,
        reading_id=runtime.reading_id,
        text=text,
        output_language=task.output_language,
        raw_thinking="",
        provider=provider,
        model=model,
    )


def accept_expression_result(
    *,
    result_id: str,
    task: LLMExpressionTask,
    result: LLMExpressionResult,
    runtime: RuntimeResult,
) -> AcceptanceResult:
    text = result.text
    leakage_hits = _hits(text, LEAKAGE_TOKENS)
    overclaim_hits = _hits(text, [*OVERCLAIM_TOKENS, *task.forbidden_assertions])
    chart_fact_mutation = bool(_hits(text, CHART_FACT_TOKENS))
    verdict_mutation = _verdict_mutation_detected(task=task, text=text)
    repair_reasons: list[str] = []
    if leakage_hits:
        repair_reasons.append("expression_leaked_internal_terms")
    if overclaim_hits:
        repair_reasons.append("expression_overclaimed_beyond_verdict")
    if verdict_mutation:
        repair_reasons.append("expression_did_not_preserve_allowed_assertions")
    if chart_fact_mutation:
        repair_reasons.append("expression_attempted_chart_fact_mutation")
    status = AcceptanceStatus.ACCEPTED
    accepted_text = text
    if leakage_hits or overclaim_hits or chart_fact_mutation:
        status = AcceptanceStatus.HARD_REJECT
        accepted_text = ""
    elif verdict_mutation:
        status = AcceptanceStatus.REPAIR
        accepted_text = ""
    return AcceptanceResult(
        result_id=result_id,
        reading_id=runtime.reading_id,
        status=status,
        accepted_text=accepted_text,
        repair_reasons=repair_reasons,
        leakage_hits=leakage_hits,
        overclaim_hits=overclaim_hits,
        verdict_mutation_detected=verdict_mutation,
        chart_fact_mutation_detected=chart_fact_mutation,
    )


def build_expression_telemetry(
    *,
    telemetry_id: str,
    task: LLMExpressionTask,
    result: LLMExpressionResult,
    acceptance: AcceptanceResult,
    execution_mode: str,
) -> ExpressionTelemetry:
    return ExpressionTelemetry(
        telemetry_id=telemetry_id,
        reading_id=task.reading_id,
        task_id=task.task_id,
        result_id=result.result_id,
        execution_mode=execution_mode,
        provider=result.provider,
        model=result.model,
        accepted=acceptance.status == AcceptanceStatus.ACCEPTED,
        acceptance_status=acceptance.status,
        thinking_trace_available=bool(result.raw_thinking.strip()),
        thinking_trace_chars=len(result.raw_thinking),
        repair_reasons=acceptance.repair_reasons,
        leakage_hits=acceptance.leakage_hits,
        overclaim_hits=acceptance.overclaim_hits,
        verdict_mutation_detected=acceptance.verdict_mutation_detected,
        chart_fact_mutation_detected=acceptance.chart_fact_mutation_detected,
        llm_decision_authority=task.can_change_verdict or result.changed_verdict or task.can_create_chart_facts or result.created_chart_facts,
    )


def _render_text(*, runtime: RuntimeResult, role_key: RoleKey) -> str:
    projection = runtime.product_projection
    if projection is None:
        return "本次测算还没有形成可表达的结果。"
    lines = ["结论"]
    for card in projection.verdict_cards:
        lines.append(f"- {card.title}：{card.primary_text}")
    if projection.advice_cards:
        lines.append("建议")
        for card in projection.advice_cards:
            for point in card.action_points[:2]:
                lines.append(f"- {point}")
            for point in card.avoid_points[:1]:
                lines.append(f"- 注意：{point}")
            for point in card.condition_points[:1]:
                lines.append(f"- 校准：{point}")
    if role_key == "practitioner" and projection.branch_cards:
        lines.append("命理师校准")
        for card in projection.branch_cards[:3]:
            lines.append(f"- {card.title}：{card.practitioner_summary}")
    return "\n".join(lines)


def _allowed_assertions(runtime: RuntimeResult) -> list[str]:
    assertions: list[str] = []
    for verdict in runtime.verdicts:
        assertions.append(verdict.headline)
        assertions.extend(verdict.allowed_assertions)
    for advice in runtime.advice_plans:
        assertions.extend(advice.action_points)
        assertions.extend(advice.avoid_points)
        assertions.extend(advice.condition_points)
    return _unique(assertions)


def _forbidden_assertions(runtime: RuntimeResult) -> list[str]:
    assertions: list[str] = []
    for verdict in runtime.verdicts:
        assertions.extend(verdict.forbidden_assertions)
    return _unique(assertions)


def _instruction(*, role_key: RoleKey) -> str:
    base = (
        "只把输入卡片改写成用户可读中文。"
        "必须保留结论边界，不新增命盘事实，不新增年份断语，不改变 verdict。"
        "优先输出结论和建议，避免工程语言。"
    )
    if role_key == "practitioner":
        return base + "命理师模式可补充分支校准提示，但不能直接改全局权重。"
    return base + "普通用户模式不展示分支权重和内部校准字段。"


def _verdict_mutation_detected(*, task: LLMExpressionTask, text: str) -> bool:
    if not task.allowed_assertions:
        return False
    normalized = _normalize(text)
    for assertion in task.allowed_assertions:
        if _assertion_preserved(assertion=assertion, normalized_text=normalized):
            return False
    return True


def _assertion_preserved(*, assertion: str, normalized_text: str) -> bool:
    normalized_assertion = _normalize(assertion)
    if not normalized_assertion:
        return False
    if normalized_assertion in normalized_text:
        return True
    windows = _semantic_windows(normalized_assertion)
    if not windows:
        return False
    hits = sum(1 for window in windows if window in normalized_text)
    if len(normalized_assertion) <= 10:
        return hits >= max(2, int(len(windows) * 0.55))
    return hits >= max(5, int(len(windows) * 0.42))


def _semantic_windows(text: str) -> list[str]:
    compact = _remove_low_value_words(text)
    if len(compact) < 2:
        return []
    window_size = 2 if len(compact) <= 18 else 3
    return _unique([compact[index : index + window_size] for index in range(0, len(compact) - window_size + 1)])


def _remove_low_value_words(text: str) -> str:
    compact = _normalize(text)
    for word in (
        "建议",
        "当前",
        "目前",
        "可以",
        "需要",
        "如果",
        "后续",
        "这个",
        "一个",
        "不要",
        "直接",
        "等同于",
        "优先",
    ):
        compact = compact.replace(word, "")
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", compact)


def _hits(text: str, tokens: list[str]) -> list[str]:
    normalized = _normalize(text)
    hits = []
    for token in tokens:
        clean = _normalize(token)
        if clean and clean in normalized and token not in hits:
            hits.append(token)
    return hits


def _normalize(text: str) -> str:
    return "".join(str(text).split())


def _unique(rows: list[str]) -> list[str]:
    result: list[str] = []
    for row in rows:
        clean = row.strip()
        if clean and clean not in result:
            result.append(clean)
    return result
