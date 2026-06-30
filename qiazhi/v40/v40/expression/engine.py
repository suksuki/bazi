from __future__ import annotations

from v40.contracts.base import RoleKey, Topic
from v40.contracts.output import AcceptanceResult, AcceptanceStatus, LLMExpressionResult, LLMExpressionTask
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
    return LLMExpressionTask(
        task_id=task_id,
        reading_id=runtime.reading_id,
        role_key=role_key or runtime.request.role_key,
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
        tokens = _meaningful_tokens(assertion)
        if tokens and all(token in normalized for token in tokens[:3]):
            return False
    return True


def _meaningful_tokens(text: str) -> list[str]:
    normalized = _normalize(text)
    chunks = [
        chunk
        for separator in ["，", "。", "；", "、", "：", " ", "\n", "\t"]
        for chunk in normalized.split(separator)
    ]
    tokens = [chunk for chunk in chunks if len(chunk) >= 2]
    if tokens:
        return tokens[:4]
    return [normalized[:8]] if normalized else []


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
