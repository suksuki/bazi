from __future__ import annotations

from v40.contracts.base import RoleKey, Topic
from v40.contracts.decision import AdvicePlan, DecisionVerdict
from v40.contracts.output import (
    AcceptanceResult,
    ConversationSeed,
    ConversationTurn,
    ExpressionTelemetry,
    LLMExpressionResult,
    LLMExpressionTask,
)
from v40.contracts.runtime import RuntimeResult
from v40.conversation.seeds import build_conversation_seeds
from v40.expression import (
    accept_expression_result,
    build_expression_telemetry,
    render_ollama_prompt_expression_result,
)


CONVERSATION_SYSTEM = (
    "You are Qiazhi V40's bounded Bazi conversation layer. "
    "Answer only from the supplied runtime verdicts, advice, probes, and accepted report context. "
    "Do not create new pillars, luck cycles, flow years, hidden facts, event years, or guaranteed promises. "
    "Do not expose engineering terms. Return customer-visible Chinese text."
)


def build_conversation_turn(
    *,
    turn_id: str,
    runtime: RuntimeResult,
    question: str,
    seed_id: str = "",
    selected_option: str = "",
    role_key: RoleKey | None = None,
    topic: Topic | None = None,
    execution_mode: str = "local",
    provider_text: str = "",
    provider: str = "local_conversation_adapter",
    model: str = "v40.conversation.contract.v1",
    raw_thinking: str = "",
) -> tuple[ConversationTurn, LLMExpressionTask, LLMExpressionResult, AcceptanceResult, ExpressionTelemetry]:
    clean_question = question.strip()
    if not clean_question:
        raise ValueError("Conversation turn requires question")
    source_seed = _find_seed(runtime=runtime, seed_id=seed_id, question=clean_question)
    resolved_role = role_key or runtime.request.role_key
    resolved_topic = topic or _infer_topic(question=clean_question, runtime=runtime, source_seed=source_seed)
    verdicts = _relevant_verdicts(runtime=runtime, topic=resolved_topic, source_seed=source_seed)
    advice_plans = _relevant_advice(runtime=runtime, topic=resolved_topic, source_seed=source_seed)
    task = _build_turn_task(
        turn_id=turn_id,
        runtime=runtime,
        question=clean_question,
        selected_option=selected_option,
        role_key=resolved_role,
        topic=resolved_topic,
        source_seed=source_seed,
        verdicts=verdicts,
        advice_plans=advice_plans,
    )
    if execution_mode == "provider_text":
        result = LLMExpressionResult(
            result_id=f"result:{turn_id}",
            task_id=task.task_id,
            reading_id=runtime.reading_id,
            text=provider_text,
            raw_thinking=raw_thinking,
            provider=provider,
            model=model,
        )
    elif execution_mode == "ollama":
        result = render_ollama_prompt_expression_result(
            result_id=f"result:{turn_id}",
            task=task,
            prompt=build_conversation_prompt(
                runtime=runtime,
                question=clean_question,
                selected_option=selected_option,
                source_seed=source_seed,
                verdicts=verdicts,
                advice_plans=advice_plans,
                role_key=resolved_role,
            ),
            system_content=CONVERSATION_SYSTEM,
        )
    else:
        result = LLMExpressionResult(
            result_id=f"result:{turn_id}",
            task_id=task.task_id,
            reading_id=runtime.reading_id,
            text=render_local_conversation_answer(
                runtime=runtime,
                question=clean_question,
                selected_option=selected_option,
                source_seed=source_seed,
                verdicts=verdicts,
                advice_plans=advice_plans,
                role_key=resolved_role,
            ),
            raw_thinking="",
            provider=provider,
            model=model,
        )
    acceptance = accept_expression_result(
        result_id=f"acceptance:{turn_id}",
        task=task,
        result=result,
        runtime=runtime,
    )
    telemetry = build_expression_telemetry(
        telemetry_id=f"telemetry:{turn_id}",
        task=task,
        result=result,
        acceptance=acceptance,
        execution_mode=execution_mode,
    )
    accepted = acceptance.status.value == "accepted"
    answer_text = acceptance.accepted_text if accepted else ""
    next_seeds = _next_seeds(
        runtime=runtime,
        accepted_text=answer_text,
        role_key=resolved_role,
        source_seed=source_seed,
        question=clean_question,
    )
    turn = ConversationTurn(
        turn_id=turn_id,
        reading_id=runtime.reading_id,
        role_key=resolved_role,
        topic=resolved_topic,
        question=clean_question,
        selected_option=selected_option,
        source_seed_id=source_seed.seed_id if source_seed else seed_id,
        source_probe_ids=source_seed.source_probe_ids if source_seed else [],
        source_verdict_ids=[verdict.verdict_id for verdict in verdicts],
        source_advice_ids=[advice.advice_id for advice in advice_plans],
        answer_text=answer_text,
        raw_thinking=result.raw_thinking,
        provider=result.provider,
        model=result.model,
        accepted=accepted,
        acceptance_status=acceptance.status,
        next_seeds=next_seeds,
    )
    return turn, task, result, acceptance, telemetry


def build_conversation_prompt(
    *,
    runtime: RuntimeResult,
    question: str,
    selected_option: str,
    source_seed: ConversationSeed | None,
    verdicts: list[DecisionVerdict],
    advice_plans: list[AdvicePlan],
    role_key: RoleKey,
) -> str:
    accepted_report = runtime.acceptance_result.accepted_text if runtime.acceptance_result else ""
    seed_context = source_seed.question if source_seed else ""
    option_context = selected_option.strip() or "无"
    return "\n".join(
        [
            "你是掐指一算 V40 的智能对话表达层。",
            "你只能消费本轮提供的 verdict/advice/probe/report，不得新增命盘事实，不得改变 verdict。",
            "普通用户只看结论、依据、建议、下一问；命理师可以看分支校准语言，但不要暴露工程字段。",
            "必须逐字保留一条“允许表达的断言”或一条“建议”，证明没有改写核心判断。",
            "",
            f"用户角色: {role_key}",
            f"用户问题: {question}",
            f"用户选择: {option_context}",
            f"种子问题: {seed_context or '无'}",
            "",
            "允许表达的断言:",
            *_bullet_lines(_allowed_assertions(verdicts=verdicts, advice_plans=advice_plans)),
            "",
            "禁止表达的断言:",
            *_bullet_lines(_forbidden_assertions(verdicts=verdicts)),
            "",
            "当前已通过验收的报告:",
            accepted_report or "无",
            "",
            "本轮相关结论:",
            *_bullet_lines([verdict.headline for verdict in verdicts]),
            "",
            "本轮相关建议:",
            *_bullet_lines(_advice_lines(advice_plans)),
            "",
            "可继续追问的问题:",
            *_bullet_lines([probe.question for probe in runtime.probes[:5]]),
            "",
            "输出格式:",
            "结论",
            "- ...",
            "依据",
            "- ...",
            "建议",
            "- ...",
            "下一问",
            "- ...",
        ]
    )


def render_local_conversation_answer(
    *,
    runtime: RuntimeResult,
    question: str,
    selected_option: str,
    source_seed: ConversationSeed | None,
    verdicts: list[DecisionVerdict],
    advice_plans: list[AdvicePlan],
    role_key: RoleKey,
) -> str:
    lines = ["结论"]
    if selected_option.strip():
        lines.append(f"- 你选择的是“{selected_option.strip()}”，本轮先沿这个方向细化。")
    if verdicts:
        for verdict in verdicts[:2]:
            lines.append(f"- {verdict.headline}")
    else:
        lines.append("- 这轮问题暂时没有足够的命盘素材支撑，先回到已形成的结论继续追问。")
    lines.append("依据")
    if source_seed:
        lines.append(f"- 这轮追问来自“{source_seed.question}”，只补这一条判断的关键背景。")
    if runtime.signal_registry:
        lines.append("- 当前已结合命局结构、做功路径和领域建议，不另起新的命盘事实。")
    if verdicts and verdicts[0].evidence_refs:
        lines.append("- 判断主要来自命局结构、做功路径和领域建议的共同指向。")
    lines.append("建议")
    advice_rows = _advice_lines(advice_plans)
    if advice_rows:
        for row in advice_rows[:4]:
            lines.append(f"- {row}")
    else:
        lines.append("- 先把问题收窄到事业、财运、关系、健康或用神，再继续追问。")
    probe_questions = [probe.question for probe in runtime.probes if probe.question and probe.topic == (source_seed.topic if source_seed else runtime.request.topic)]
    if not probe_questions:
        probe_questions = [probe.question for probe in runtime.probes if probe.question]
    if probe_questions:
        lines.append("下一问")
        lines.append(f"- {probe_questions[0]}")
    if role_key == "practitioner":
        lines.append("命理师校准")
        lines.append("- 若本轮答案与真实反馈不一致，可把该分支降权或转成下一轮追问。")
    return "\n".join(lines)


def _build_turn_task(
    *,
    turn_id: str,
    runtime: RuntimeResult,
    question: str,
    selected_option: str,
    role_key: RoleKey,
    topic: Topic,
    source_seed: ConversationSeed | None,
    verdicts: list[DecisionVerdict],
    advice_plans: list[AdvicePlan],
) -> LLMExpressionTask:
    source_ids: list[str] = []
    if source_seed:
        source_ids.extend(source_seed.source_verdict_ids)
        source_ids.extend(source_seed.source_advice_ids)
        source_ids.extend(source_seed.source_probe_ids)
    instruction = (
        "回答用户这一轮八字追问，只使用当前 runtime 的结论、建议、报告和追问种子。"
        "输出必须简洁、可执行、通俗，不出现工程字段。"
        f" 用户问题：{question}"
    )
    if selected_option.strip():
        instruction += f" 用户选择：{selected_option.strip()}"
    return LLMExpressionTask(
        task_id=f"task:{turn_id}",
        reading_id=runtime.reading_id,
        role_key=role_key,
        topic=topic,
        input_card_ids=source_ids,
        instruction=instruction,
        allowed_assertions=_allowed_assertions(verdicts=verdicts, advice_plans=advice_plans),
        forbidden_assertions=_forbidden_assertions(verdicts=verdicts),
    )


def _find_seed(*, runtime: RuntimeResult, seed_id: str, question: str) -> ConversationSeed | None:
    clean_seed_id = seed_id.strip()
    for seed in runtime.conversation_seeds:
        if clean_seed_id and seed.seed_id == clean_seed_id:
            return seed
    for seed in runtime.conversation_seeds:
        if seed.question == question:
            return seed
    return None


def _infer_topic(*, question: str, runtime: RuntimeResult, source_seed: ConversationSeed | None) -> Topic:
    if source_seed and source_seed.topic != Topic.UNKNOWN:
        return source_seed.topic
    keyword_map = {
        Topic.CAREER: ("事业", "工作", "职业", "岗位", "升职", "转型"),
        Topic.WEALTH: ("财", "钱", "收入", "投资", "收益"),
        Topic.RELATIONSHIP: ("感情", "关系", "婚", "伴侣", "相处"),
        Topic.HEALTH: ("身体", "健康", "压力", "作息"),
        Topic.USEFUL_GOD: ("用神", "忌神", "喜神"),
        Topic.TIMING: ("今年", "流年", "大运", "年份", "什么时候"),
        Topic.HIDDEN_ATTRIBUTE: ("隐藏", "暗", "看不出来", "反复"),
    }
    for topic, keywords in keyword_map.items():
        if any(keyword in question for keyword in keywords):
            return topic
    return runtime.request.topic if runtime.request.topic != Topic.UNKNOWN else Topic.OVERVIEW


def _relevant_verdicts(
    *,
    runtime: RuntimeResult,
    topic: Topic,
    source_seed: ConversationSeed | None,
) -> list[DecisionVerdict]:
    source_ids = set(source_seed.source_verdict_ids if source_seed else [])
    if source_ids:
        rows = [verdict for verdict in runtime.verdicts if verdict.verdict_id in source_ids]
        if rows:
            return rows
    rows = [verdict for verdict in runtime.verdicts if verdict.topic == topic]
    return rows or runtime.verdicts[:2]


def _relevant_advice(
    *,
    runtime: RuntimeResult,
    topic: Topic,
    source_seed: ConversationSeed | None,
) -> list[AdvicePlan]:
    source_ids = set(source_seed.source_advice_ids if source_seed else [])
    if source_ids:
        rows = [advice for advice in runtime.advice_plans if advice.advice_id in source_ids]
        if rows:
            return rows
    verdict_ids = {verdict.verdict_id for verdict in _relevant_verdicts(runtime=runtime, topic=topic, source_seed=source_seed)}
    rows = [
        advice
        for advice in runtime.advice_plans
        if advice.topic == topic or verdict_ids.intersection(advice.source_verdict_ids)
    ]
    return rows or runtime.advice_plans[:2]


def _allowed_assertions(*, verdicts: list[DecisionVerdict], advice_plans: list[AdvicePlan]) -> list[str]:
    rows: list[str] = []
    for verdict in verdicts:
        rows.append(verdict.headline)
        rows.extend(verdict.allowed_assertions)
    rows.extend(_advice_lines(advice_plans))
    return _unique(rows)


def _forbidden_assertions(*, verdicts: list[DecisionVerdict]) -> list[str]:
    rows: list[str] = []
    for verdict in verdicts:
        rows.extend(verdict.forbidden_assertions)
    return _unique(rows)


def _advice_lines(advice_plans: list[AdvicePlan]) -> list[str]:
    rows: list[str] = []
    for advice in advice_plans:
        rows.extend(advice.action_points)
        rows.extend(f"注意：{point}" for point in advice.avoid_points)
        rows.extend(f"校准：{point}" for point in advice.condition_points)
    return _unique(rows)


def _next_seeds(
    *,
    runtime: RuntimeResult,
    accepted_text: str,
    role_key: RoleKey,
    source_seed: ConversationSeed | None,
    question: str,
) -> list[ConversationSeed]:
    rows = build_conversation_seeds(runtime=runtime, accepted_text=accepted_text, role_key=role_key, limit=6)
    blocked_questions = {question}
    blocked_seed_ids = {source_seed.seed_id} if source_seed else set()
    result: list[ConversationSeed] = []
    for seed in rows:
        if seed.seed_id in blocked_seed_ids or seed.question in blocked_questions:
            continue
        result.append(seed)
        if len(result) >= 3:
            break
    return result


def _bullet_lines(rows: list[str]) -> list[str]:
    return [f"- {row}" for row in rows if row.strip()] or ["- 无"]


def _unique(rows: list[str]) -> list[str]:
    result: list[str] = []
    for row in rows:
        clean = row.strip()
        if clean and clean not in result:
            result.append(clean)
    return result
