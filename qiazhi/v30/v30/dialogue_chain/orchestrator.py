from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from v30.contracts import CoreRuntimeResult
from v30.dialogue_chain.contracts import (
    BaziDialogueAnswer,
    BaziDialogueSeed,
    BaziDialogueSession,
    BaziDialogueTurn,
    DialogueMemory,
    DialogueQuestionCandidate,
)
from v30.dialogue_chain.seed_router import DOMAIN_LABELS, build_seed_suggestions, route_dialogue_seed
from v30.presentation import build_presentation_model


def build_dialogue_seed_suggestions(runtime: CoreRuntimeResult) -> list[dict[str, Any]]:
    return build_seed_suggestions(runtime)


def start_dialogue_session(
    runtime: CoreRuntimeResult,
    seed_text: str,
    *,
    source: str = "user",
    role_key: str = "user",
    locale: str = "zh",
    client: str = "web",
    stage_id: str = "",
) -> BaziDialogueSession:
    seed = route_dialogue_seed(runtime, seed_text, source=source, stage_id=stage_id)
    dialogue_id = _dialogue_id(runtime.reading_id, seed.seed_id)
    session = BaziDialogueSession(
        dialogue_id=dialogue_id,
        reading_id=runtime.reading_id,
        seed=seed,
        active_domain=seed.macro_domain,
        policy_state=_policy_state(runtime, role_key=role_key, locale=locale, client=client),
    )
    return append_dialogue_turn(
        runtime,
        session,
        text=seed_text,
        role_key=role_key,
        locale=locale,
        client=client,
        source=source,
        stage_id=stage_id,
    )


def append_dialogue_turn(
    runtime: CoreRuntimeResult,
    session: BaziDialogueSession,
    *,
    text: str = "",
    selected_option: str = "",
    structured_payload: dict[str, Any] | None = None,
    role_key: str = "user",
    locale: str = "zh",
    client: str = "web",
    source: str = "user",
    stage_id: str = "",
) -> BaziDialogueSession:
    user_text = _turn_text(text, selected_option, session)
    seed = route_dialogue_seed(
        runtime,
        user_text or session.seed.normalized_question,
        source=source,
        stage_id=stage_id or session.seed.stage_id,
    )
    surface = build_presentation_model(runtime, role_key=role_key, locale=locale, client=client).reading_surface
    turn_index = len(session.turns) + 1
    answer = _build_answer(runtime, surface, seed, turn_index=turn_index)
    candidates = _next_question_candidates(surface, seed, session, answer)
    selected_next = candidates[0] if candidates else None
    turn = BaziDialogueTurn(
        turn_id=f"{session.dialogue_id}:turn:{turn_index}",
        dialogue_id=session.dialogue_id,
        reading_id=runtime.reading_id,
        turn_index=turn_index,
        user_input={
            "text": text.strip(),
            "selected_option": selected_option.strip(),
            "structured_payload": structured_payload or {},
            "source": source,
            "stage_id": stage_id,
        },
        interpreted_seed=seed,
        answer_contract={
            "must_answer_user_seed": True,
            "answer_priority": seed.answer_priority,
            "uses_decision_verdicts": True,
            "uses_dialogue_memory": bool(session.turns),
            "llm_expression_only": True,
            "chart_fact_mutation_allowed": False,
            "boundary": "dialogue_answer_contract_preserves_runtime_verdict_authority",
        },
        answer=answer,
        next_question_candidates=candidates,
        selected_next_question=selected_next,
        training_signal=_training_signal(seed, answer, selected_next),
    )
    memory = _update_memory(session.memory_summary, turn)
    updated_turns = [*session.turns, turn]
    return session.model_copy(
        update={
            "turn_count": len(updated_turns),
            "active_domain": seed.macro_domain,
            "active_question_id": selected_next.question_id if selected_next else "",
            "unresolved_slots": _unresolved_slots(seed, answer),
            "memory_summary": memory,
            "policy_state": {
                **session.policy_state,
                "last_turn_id": turn.turn_id,
                "last_seed_domain": seed.macro_domain,
                "answer_first": seed.answer_priority == "answer_first",
                "chart_fact_mutation_allowed": False,
            },
            "turns": updated_turns,
            "updated_at": datetime.now(timezone.utc),
        }
    )


def _build_answer(
    runtime: CoreRuntimeResult,
    surface: dict[str, Any],
    seed: BaziDialogueSeed,
    *,
    turn_index: int,
) -> BaziDialogueAnswer:
    verdict = _domain_verdict(surface, seed.macro_domain)
    domain_card = _domain_card(surface, seed.macro_domain)
    final = surface.get("final_synthesis", {}) if isinstance(surface, dict) else {}
    final = final if isinstance(final, dict) else {}
    basic = surface.get("basic_assertions", []) if isinstance(surface, dict) else []
    basic = [row for row in basic if isinstance(row, dict)]
    domain_label = DOMAIN_LABELS.get(seed.macro_domain, seed.macro_domain)
    conclusions = _conclusion_items(runtime, seed, verdict, domain_card, final, basic)
    advice = _advice_items(seed, verdict, domain_card, final)
    uncertainty = _uncertainty_items(seed, verdict, domain_card)
    evidence = _evidence_items(seed, verdict, domain_card, basic)
    text = _display_text(seed, domain_label, conclusions, advice, uncertainty, evidence)
    return BaziDialogueAnswer(
        answer_id=f"{runtime.reading_id}:dialogue-answer:{turn_index}",
        verdict_refs=_verdict_refs(verdict, domain_card),
        conclusion_items=conclusions,
        advice_items=advice,
        uncertainty_items=uncertainty,
        evidence_items=evidence,
        display_text=text,
        visual_hint=_visual_hint(seed, verdict, domain_card),
        llm_metadata={
            "status": "not_required",
            "provider": "structured_central_orchestrator",
            "role": "expression_slot_reserved",
            "reason": "dialogue_chain_uses_runtime_verdicts_first_and_can_be_rewritten_by_llm_later",
            "boundary": "llm_expression_slot_does_not_mutate_dialogue_verdict_or_chart_facts",
        },
    )


def _conclusion_items(
    runtime: CoreRuntimeResult,
    seed: BaziDialogueSeed,
    verdict: dict[str, Any],
    domain_card: dict[str, Any],
    final: dict[str, Any],
    basic: list[dict[str, Any]],
) -> list[str]:
    rows: list[str] = []
    if seed.time_scope == "current_year":
        rows.append(_timing_intro(runtime))
    primary_text = str(verdict.get("primary_text") or domain_card.get("customer_takeaway") or domain_card.get("summary") or "")
    if primary_text:
        rows.append(_strip_prefix(primary_text))
    path_summary = str(domain_card.get("path_summary") or "")
    if path_summary:
        rows.append(path_summary)
    if not rows and final.get("conclusion"):
        rows.append(_strip_prefix(str(final.get("conclusion"))))
    if not rows:
        rows.extend(str(row.get("assertion") or "") for row in basic[:2] if row.get("assertion"))
    if seed.macro_domain == "wealth" and rows:
        rows[0] = _wealth_conclusion(rows[0], seed.time_scope)
    return _dedupe(rows)[:3]


def _advice_items(
    seed: BaziDialogueSeed,
    verdict: dict[str, Any],
    domain_card: dict[str, Any],
    final: dict[str, Any],
) -> list[str]:
    points = verdict.get("advice_points", [])
    rows = [str(row) for row in points if row] if isinstance(points, list) else []
    prompt = str(domain_card.get("action_prompt") or "")
    if prompt:
        rows.append(prompt.replace("确认当前最想看的", "下一步先确认"))
    if seed.macro_domain == "wealth":
        rows.append("财务动作先分成赚钱方式、风险边界和节奏三层，不要只用“好/不好”判断。")
    if seed.macro_domain == "career":
        rows.append("职业选择先看压力是否能被资质、平台或可交付成果承接。")
    if not rows and final.get("advice"):
        rows.append(_strip_prefix(str(final.get("advice"))))
    return _dedupe(rows)[:3]


def _uncertainty_items(
    seed: BaziDialogueSeed,
    verdict: dict[str, Any],
    domain_card: dict[str, Any],
) -> list[str]:
    rows: list[str] = []
    if verdict.get("has_alternative_branch"):
        rows.append("当前保留相近分支，需要用用户背景或命理师选择继续拉开权重。")
    for assertion in _list(domain_card.get("path_assertions"))[:2]:
        boundary = str(assertion.get("uncertainty_boundary") or "")
        if boundary:
            rows.append(boundary)
    if seed.time_scope == "current_year" and not _has_time_fact(domain_card):
        rows.append("年份判断只绑定当前命盘与时运入口，不能直接说成固定事件。")
    return _dedupe(rows)[:3]


def _evidence_items(
    seed: BaziDialogueSeed,
    verdict: dict[str, Any],
    domain_card: dict[str, Any],
    basic: list[dict[str, Any]],
) -> list[str]:
    rows: list[str] = []
    if verdict.get("verdict_id"):
        rows.append(str(verdict.get("verdict_id")))
    for claim in _list(domain_card.get("diagnosis_claims"))[:2]:
        if claim.get("claim_id"):
            rows.append(str(claim.get("claim_id")))
    for item in basic[:2]:
        if item.get("title") and item.get("assertion"):
            rows.append(f"{item.get('title')}：{item.get('assertion')}")
    rows.extend(seed.evidence_binding[:2])
    return _dedupe(rows)[:5]


def _next_question_candidates(
    surface: dict[str, Any],
    seed: BaziDialogueSeed,
    session: BaziDialogueSession,
    answer: BaziDialogueAnswer,
) -> list[DialogueQuestionCandidate]:
    asked = set(session.memory_summary.asked_question_ids)
    domain = seed.macro_domain
    rows = [_candidate_from_domain(domain, seed, answer)]
    conflict = _domain_conflict(surface, domain)
    if conflict.get("needed_question"):
        rows.append(
            DialogueQuestionCandidate(
                question_id=_question_id(domain, str(conflict.get("needed_question"))),
                label=str(conflict.get("needed_question")),
                macro_domain=domain,
                user_intent="verify_event",
                prompt_text=str(conflict.get("needed_question")),
                options=_default_options(domain),
                expected_information_gain=0.78,
                priority=88,
                reason="用于拉开当前相近分支的权重。",
            )
        )
    rows.append(_cross_domain_candidate(seed))
    deduped: list[DialogueQuestionCandidate] = []
    seen: set[str] = set()
    for row in rows:
        if row.question_id in seen or row.question_id in asked:
            continue
        seen.add(row.question_id)
        deduped.append(row)
    return sorted(deduped, key=lambda row: (row.priority, row.expected_information_gain), reverse=True)[:3]


def _candidate_from_domain(
    domain: str,
    seed: BaziDialogueSeed,
    answer: BaziDialogueAnswer,
) -> DialogueQuestionCandidate:
    labels = {
        "wealth": "你的财务更偏主动争取、合作分配，还是保守积累？",
        "career": "当前事业压力更来自职责扩大、平台规则，还是转型机会？",
        "relationship": "关系里最反复的是表达冲突、距离边界，还是承诺节奏？",
        "health": "最近更明显的是压力消耗、作息紊乱，还是身体反馈？",
        "family": "家庭压力主要落在父母、子女，还是资源分配？",
        "useful_god": "用神取向更需要验证承接、通关，还是泄秀？",
        "structure": "当前更能印证身强、身弱，还是中和待复核？",
        "decision": "这个决策最难的是风险边界、资源承接，还是时机？",
        "timing": "当前时运更像机会触发、压力触发，还是关系触发？",
    }
    label = labels.get(domain, "你最想继续看事业、财务、关系，还是时运？")
    return DialogueQuestionCandidate(
        question_id=_question_id(domain, label),
        label=label,
        macro_domain=seed.macro_domain,
        user_intent="verify_event" if answer.uncertainty_items else "ask_advice",
        prompt_text=label,
        options=_default_options(domain),
        expected_information_gain=0.72,
        priority=82,
        reason="延续本轮结论，补一个能提升下一轮判断质量的背景。",
    )


def _cross_domain_candidate(seed: BaziDialogueSeed) -> DialogueQuestionCandidate:
    if seed.macro_domain == "wealth":
        label = "财务判断要不要同时看事业承接路径？"
        domain = "career"
    elif seed.macro_domain == "career":
        label = "事业变化会不会牵动财务节奏？"
        domain = "wealth"
    else:
        label = "要不要把这个问题放回事业、财务和关系三条主线一起看？"
        domain = "overview"
    return DialogueQuestionCandidate(
        question_id=_question_id(domain, label),
        label=label,
        macro_domain=domain,  # type: ignore[arg-type]
        user_intent="ask_advice",
        prompt_text=label,
        options=_default_options(domain),
        expected_information_gain=0.58,
        priority=62,
        reason="把单点问题接回全局测算主线。",
    )


def _update_memory(memory: DialogueMemory, turn: BaziDialogueTurn) -> DialogueMemory:
    domain = turn.interpreted_seed.macro_domain
    counts = dict(memory.domain_counts)
    counts[domain] = counts.get(domain, 0) + 1
    selected = str(turn.user_input.get("selected_option") or "")
    next_ids = [
        row.question_id
        for row in [turn.selected_next_question]
        if row is not None
    ]
    latest = [
        *memory.last_user_inputs,
        str(turn.user_input.get("text") or turn.interpreted_seed.normalized_question),
    ][-6:]
    return memory.model_copy(
        update={
            "answered_seed_ids": [*memory.answered_seed_ids, turn.interpreted_seed.seed_id][-50:],
            "asked_question_ids": [*memory.asked_question_ids, *next_ids][-80:],
            "selected_options": ([*memory.selected_options, selected] if selected else list(memory.selected_options))[-50:],
            "domain_counts": counts,
            "last_user_inputs": latest,
            "summary": f"最近聚焦{DOMAIN_LABELS.get(domain, domain)}，已完成{turn.turn_index}轮问答。",
        }
    )


def _display_text(
    seed: BaziDialogueSeed,
    domain_label: str,
    conclusions: list[str],
    advice: list[str],
    uncertainty: list[str],
    evidence: list[str],
) -> str:
    parts = [f"围绕「{seed.normalized_question}」，先看{domain_label}这条线。"]
    if conclusions:
        parts.append("判断：" + "；".join(conclusions))
    if advice:
        parts.append("建议：" + "；".join(advice))
    if uncertainty:
        parts.append("需要保留的分支：" + "；".join(uncertainty))
    if evidence:
        parts.append("依据：" + "；".join(evidence[:3]))
    return "\n".join(parts)


def _policy_state(runtime: CoreRuntimeResult, *, role_key: str, locale: str, client: str) -> dict[str, Any]:
    return {
        "version": "v30.dialogue_policy_state.v1",
        "role_key": role_key,
        "locale": locale,
        "client": client,
        "mainline_id": runtime.mainline_state.mainline_id,
        "mainline_domain": runtime.mainline_state.domain,
        "chart_fact_mutation_allowed": False,
        "answer_strategy": "answer_first_then_next_question",
        "boundary": "dialogue_policy_state_routes_conversation_not_chart_facts",
    }


def _training_signal(
    seed: BaziDialogueSeed,
    answer: BaziDialogueAnswer,
    selected_next: DialogueQuestionCandidate | None,
) -> dict[str, Any]:
    return {
        "version": "v30.dialogue_training_signal.v1",
        "seed_domain": seed.macro_domain,
        "seed_intent": seed.user_intent,
        "answer_item_count": len(answer.conclusion_items) + len(answer.advice_items),
        "has_next_question": selected_next is not None,
        "next_question_id": selected_next.question_id if selected_next else "",
        "chart_fact_mutation_allowed": False,
        "boundary": "dialogue_training_signal_can_tune_policy_not_chart_facts",
    }


def _dialogue_id(reading_id: str, seed_id: str) -> str:
    digest = hashlib.sha1(f"{reading_id}|{seed_id}|{datetime.now(timezone.utc).isoformat()}".encode("utf-8")).hexdigest()[:10]
    return f"dlg_{digest}"


def _question_id(domain: str, label: str) -> str:
    digest = hashlib.sha1(f"{domain}|{label}".encode("utf-8")).hexdigest()[:8]
    return f"dlg_q_{domain}_{digest}"


def _turn_text(text: str, selected_option: str, session: BaziDialogueSession) -> str:
    clean = text.strip()
    if clean:
        return clean
    if selected_option and session.active_question_id:
        option_domain = selected_option.split(":", 1)[0] if ":" in selected_option else str(session.active_domain)
        label = DOMAIN_LABELS.get(option_domain, DOMAIN_LABELS.get(session.active_domain, "继续追问"))
        return f"{label}继续看{selected_option}"
    return session.seed.normalized_question


def _domain_verdict(surface: dict[str, Any], domain: str) -> dict[str, Any]:
    workbench = surface.get("decision_workbench", {}) if isinstance(surface, dict) else {}
    for row in _list(workbench.get("verdict_cards") if isinstance(workbench, dict) else []):
        if str(row.get("domain") or "") == domain:
            return row
    for row in _list(workbench.get("verdict_cards") if isinstance(workbench, dict) else []):
        if row:
            return row
    return {}


def _domain_conflict(surface: dict[str, Any], domain: str) -> dict[str, Any]:
    workbench = surface.get("decision_workbench", {}) if isinstance(surface, dict) else {}
    for row in _list(workbench.get("conflict_cards") if isinstance(workbench, dict) else []):
        if str(row.get("domain") or "") == domain:
            return row
    return {}


def _domain_card(surface: dict[str, Any], domain: str) -> dict[str, Any]:
    for row in _list(surface.get("domain_cards") if isinstance(surface, dict) else []):
        if str(row.get("domain") or "") == domain:
            return row
    return {}


def _verdict_refs(verdict: dict[str, Any], domain_card: dict[str, Any]) -> list[str]:
    refs = [str(verdict.get("verdict_id") or "")]
    refs.extend(str(row.get("claim_id") or "") for row in _list(domain_card.get("diagnosis_claims"))[:3])
    return [row for row in _dedupe(refs) if row]


def _visual_hint(seed: BaziDialogueSeed, verdict: dict[str, Any], domain_card: dict[str, Any]) -> dict[str, Any]:
    confidence = verdict.get("confidence")
    try:
        confidence_value = float(confidence)
    except (TypeError, ValueError):
        confidence_value = 0.55
    return {
        "kind": "dialogue_compass",
        "title": f"{DOMAIN_LABELS.get(seed.macro_domain, seed.macro_domain)}焦点",
        "chips": [
            DOMAIN_LABELS.get(seed.macro_domain, seed.macro_domain),
            str(domain_card.get("path_summary") or verdict.get("assertion_level") or "证据支持")[:18],
        ],
        "markers": [{"label": "结论强度", "value": round(confidence_value, 2)}],
        "boundary": "dialogue_visual_hint_summarizes_answer_not_chart_fact",
    }


def _default_options(domain: str) -> list[dict[str, Any]]:
    options = {
        "wealth": [("earning", "赚钱方式"), ("risk", "风险边界"), ("timing", "财务节奏")],
        "career": [("role", "职责压力"), ("platform", "平台规则"), ("change", "转型机会")],
        "relationship": [("pattern", "相处模式"), ("boundary", "边界问题"), ("timing", "关系节奏")],
        "health": [("stress", "压力消耗"), ("routine", "作息节奏"), ("signal", "身体反馈")],
        "useful_god": [("support", "承接"), ("bridge", "通关"), ("output", "泄秀")],
        "structure": [("strong", "身强"), ("weak", "身弱"), ("mixed", "中和")],
        "decision": [("risk", "风险"), ("resource", "资源"), ("timing", "时机")],
    }.get(domain, [("career", "事业"), ("wealth", "财务"), ("relationship", "关系")])
    return [
        {
            "option_id": f"{domain}:{value}",
            "label": label,
            "value": value,
            "option_type": "dialogue_followup",
            "boundary": "dialogue_option_records_user_focus_not_chart_fact",
        }
        for value, label in options
    ]


def _timing_intro(runtime: CoreRuntimeResult) -> str:
    layers = runtime.chart_context.time_layers if isinstance(runtime.chart_context.time_layers, dict) else {}
    flow = layers.get("flow_context", {}) if isinstance(layers.get("flow_context", {}), dict) else {}
    luck = layers.get("luck_cycle_context", {}) if isinstance(layers.get("luck_cycle_context", {}), dict) else {}
    flow_year = str(flow.get("flow_year_pillar") or "")
    luck_pillar = str(luck.get("current_luck_pillar") or "")
    if flow_year or luck_pillar:
        return f"当前时运入口先看{f'大运{luck_pillar}' if luck_pillar else '大运'}{f'、流年{flow_year}' if flow_year else ''}对原局主线的触发。"
    return "今年的问题先按当前命盘主线与可用时运入口判断，缺少明确流年数据时不直接落固定事件。"


def _wealth_conclusion(text: str, time_scope: str) -> str:
    prefix = "今年财运" if time_scope == "current_year" else "财运"
    if text.startswith(prefix):
        return text
    return f"{prefix}不是单看收入多少，而是看财星能否通过输出、职责或资源承接形成稳定转化；{text}"


def _strip_prefix(text: str) -> str:
    return text.replace("结论：", "").replace("建议：", "").strip(" ；。")


def _has_time_fact(domain_card: dict[str, Any]) -> bool:
    return str(domain_card.get("timing_status") or "") not in {"", "natal_only"}


def _unresolved_slots(seed: BaziDialogueSeed, answer: BaziDialogueAnswer) -> list[str]:
    rows = []
    if answer.uncertainty_items:
        rows.append(f"{seed.macro_domain}:branch_confirmation")
    if seed.time_scope in {"current_year", "current_luck"}:
        rows.append("timing:real_world_context")
    return rows


def _list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def _dedupe(rows: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for row in rows:
        clean = str(row or "").strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        result.append(clean)
    return result
