from __future__ import annotations

from typing import Any, Dict, Iterable, List, Set, Tuple

from v19.agent.structure import THREE_HARMONIES
from v19.bazi_rule_db import list_bazi_rules
from v19.core.chart import BRANCH_HIDDEN_STEMS, VAULT_BRANCHES, element_of_stem


QUESTION_REGISTRY_VERSION = "v19.question_registry.audit.v1"
QUESTION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "q_structure_overview": {
        "theme": "structure_basis",
        "depth": "beginner",
        "phase": "before_result",
        "intent": "structure_overview",
        "required": ["chart"],
        "required_facts": ["chart_anchor", "relations", "vaults", "time_context"],
        "answer_scope": "summarize_visible_structure_only",
        "score": 92,
        "related_questions": ["q_day_master_month_anchor", "q_hidden_stem_role", "q_branch_relation_detail", "q_income_stability"],
        "label": {
            "zh": "如果只看结构，这张命盘先呈现哪些特征？",
            "en": "Looking only at structure, what features appear first?",
            "ko": "구조만 보면 이 명식에서 먼저 보이는 특징은 무엇인가요?",
        },
    },
    "q_day_master_month_anchor": {
        "theme": "structure_basis",
        "depth": "beginner",
        "phase": "any",
        "intent": "metadata_boundary",
        "required": ["chart"],
        "required_facts": ["chart_anchor", "hidden_stems", "stem_elements"],
        "answer_scope": "explain_day_master_and_month_anchor_as_structure",
        "score": 90,
        "related_questions": ["q_structure_overview", "q_hidden_stem_role", "q_income_factors"],
        "label": {
            "zh": "这张命盘先看日主和月令，能读出什么结构基点？",
            "en": "Starting from the day master and month branch, what structural baseline appears?",
            "ko": "일간과 월지를 먼저 보면 어떤 구조 기준점이 보이나요?",
        },
    },
    "q_hidden_stem_role": {
        "theme": "structure_basis",
        "depth": "intermediate",
        "phase": "any",
        "intent": "metadata_boundary",
        "required": ["chart"],
        "required_facts": ["hidden_stems", "chart_anchor"],
        "answer_scope": "explain_hidden_stems_as_metadata_not_prediction",
        "score": 76,
        "related_questions": ["q_day_master_month_anchor", "q_structure_overview", "q_income_factors"],
        "label": {
            "zh": "藏干在这张命盘里只是补充信息，还是会影响结构理解？",
            "en": "Are hidden stems only supporting information here, or do they affect structural reading?",
            "ko": "지장간은 여기서 보조 정보일 뿐인가요, 아니면 구조 이해에 영향을 주나요?",
        },
    },
    "q_branch_relation_detail": {
        "theme": "structure_basis",
        "depth": "beginner",
        "phase": "any",
        "intent": "branch_relation",
        "required": ["branch_relation"],
        "required_facts": ["relations", "chart_anchor", "time_context"],
        "answer_scope": "separate_natal_luck_flow_branch_relations",
        "score": 88,
        "related_questions": ["q_combination_context", "q_time_context", "q_time_vs_natal_relation", "q_cautious_reading"],
        "label": {
            "zh": "当前看得到的冲合关系，分别发生在本命还是时间背景？",
            "en": "Do the visible clash/combination relations occur inside the natal chart or in timing context?",
            "ko": "현재 보이는 충합 관계는 원국 안에서 생기나요, 아니면 시간 배경에서 생기나요?",
        },
    },
    "q_combination_context": {
        "theme": "structure_basis",
        "depth": "intermediate",
        "phase": "any",
        "intent": "branch_relation",
        "required": ["branch_relation"],
        "required_facts": ["relations"],
        "answer_scope": "explain_combination_as_structural_link_only",
        "score": 74,
        "related_questions": ["q_branch_relation_detail", "q_structure_overview", "q_time_context_boundary"],
        "label": {
            "zh": "如果出现合或六合关系，它在这里只表示什么结构连接？",
            "en": "If a combination relation appears, what structural link does it indicate here?",
            "ko": "합 관계가 나타난다면 여기서는 어떤 구조 연결만 뜻하나요?",
        },
    },
    "q_three_harmony_context": {
        "theme": "structure_basis",
        "depth": "intermediate",
        "phase": "any",
        "intent": "branch_relation",
        "required": ["branch_relation"],
        "required_facts": ["relations"],
        "answer_scope": "explain_three_harmony_as_structural_link_only",
        "score": 72,
        "related_questions": ["q_branch_relation_detail", "q_structure_overview", "q_time_context_boundary"],
        "label": {
            "zh": "如果出现三合结构，它在这里只表示什么结构连接？",
            "en": "If a three-harmony structure appears, what structural link does it indicate here?",
            "ko": "삼합 구조가 나타난다면 여기서는 어떤 구조 연결만 뜻하나요?",
        },
    },
    "q_income_stability": {
        "theme": "income_stability",
        "depth": "beginner",
        "phase": "any",
        "intent": "income_structure",
        "required": ["chart"],
        "required_facts": ["income_signals", "chart_anchor", "relations"],
        "answer_scope": "explain_income_structure_signal_not_wealth_prediction",
        "score": 70,
        "related_questions": ["q_income_factors", "q_signal_combination", "follow_rule_basis"],
        "label": {
            "zh": "我的收入稳定性结构如何？",
            "en": "How is my income stability structure?",
            "ko": "나의 소득 안정성 구조는 어떤가요?",
        },
    },
    "q_income_factors": {
        "theme": "income_stability",
        "depth": "beginner",
        "phase": "any",
        "intent": "income_structure",
        "required": ["chart"],
        "required_facts": ["income_signals", "chart_anchor", "relations"],
        "answer_scope": "explain_income_factors_as_evidence_only",
        "score": 68,
        "related_questions": ["q_signal_combination", "q_income_continuity", "q_wealth_accessibility"],
        "label": {
            "zh": "当前结构中哪些因素影响收入稳定？",
            "en": "Which structure factors affect income stability?",
            "ko": "현재 구조에서 어떤 요소가 소득 안정성에 영향을 주나요?",
        },
    },
    "q_signal_combination": {
        "theme": "income_stability",
        "depth": "intermediate",
        "phase": "after_result",
        "intent": "income_structure",
        "required": ["result"],
        "required_facts": ["income_signals"],
        "answer_scope": "explain_signal_aggregation_without_prediction",
        "score": 62,
        "related_questions": ["q_primary_auxiliary_signals", "follow_rule_basis", "q_wealth_accessibility"],
        "label": {
            "zh": "这个结果主要由哪几个结构信号共同形成？",
            "en": "Which structure signals jointly form this result?",
            "ko": "이 결과는 어떤 구조 신호들이 함께 만든 것인가요?",
        },
    },
    "q_time_context": {
        "theme": "time_context",
        "depth": "beginner",
        "phase": "any",
        "intent": "time_boundary",
        "required": ["time_relation"],
        "required_facts": ["time_context", "relations"],
        "answer_scope": "explain_flow_year_as_context_only",
        "score": 82,
        "related_questions": ["q_branch_relation_detail", "q_time_vs_natal_relation", "q_time_context_boundary", "q_luck_flow_layers"],
        "label": {
            "zh": "这个流年只作为时间背景，会触发哪些结构关系？",
            "en": "As context only, what relations does this flow year trigger?",
            "ko": "예측이 아닌 시간 맥락으로서 이 세운은 어떤 구조 관계를 만들까요?",
        },
    },
    "q_time_context_boundary": {
        "theme": "time_context",
        "depth": "beginner",
        "phase": "any",
        "intent": "time_boundary",
        "required": ["time_relation"],
        "required_facts": ["time_context", "relations"],
        "answer_scope": "explain_time_context_boundary",
        "score": 78,
        "related_questions": ["q_time_context", "q_time_vs_natal_relation", "q_time_not_inference"],
        "label": {
            "zh": "哪些结构关系只是背景，不应该直接理解成预测？",
            "en": "Which relations are background only and should not be read as prediction?",
            "ko": "어떤 구조 관계가 배경일 뿐 예측으로 읽으면 안 되나요?",
        },
    },
    "q_luck_flow_layers": {
        "theme": "time_context",
        "depth": "intermediate",
        "phase": "any",
        "intent": "time_boundary",
        "required": ["time_relation"],
        "required_facts": ["time_context"],
        "answer_scope": "separate_luck_cycle_and_flow_year_layers",
        "score": 64,
        "related_questions": ["q_time_context_boundary", "q_time_vs_natal_relation", "q_time_not_inference"],
        "label": {
            "zh": "大运和流年在这里分别属于哪一层结构？",
            "en": "Which structural layer do luck cycle and flow year belong to here?",
            "ko": "여기서 대운과 세운은 각각 어떤 구조 층에 속하나요?",
        },
    },
    "q_time_vs_natal_relation": {
        "theme": "time_context",
        "depth": "intermediate",
        "phase": "any",
        "intent": "branch_relation",
        "required": ["time_relation"],
        "required_facts": ["time_context", "relations"],
        "answer_scope": "separate_timing_relations_from_natal_structure",
        "score": 72,
        "related_questions": ["q_time_context", "q_luck_flow_layers", "q_time_not_inference"],
        "label": {
            "zh": "大运、流年和本命发生关系时，哪些只算背景，哪些才算本命结构？",
            "en": "When luck/flow relates to the natal chart, what is only background and what belongs to natal structure?",
            "ko": "대운·세운이 원국과 관계를 만들 때 무엇은 배경이고 무엇은 원국 구조인가요?",
        },
    },
    "q_time_not_inference": {
        "theme": "time_context",
        "depth": "intermediate",
        "phase": "any",
        "intent": "time_boundary",
        "required": ["time_relation"],
        "required_facts": ["time_context", "income_signals"],
        "answer_scope": "explain_time_context_does_not_mutate_income_stability",
        "score": 60,
        "related_questions": ["q_time_context_boundary", "q_result_card_boundary"],
        "label": {
            "zh": "为什么当前时间结构不直接改变收入稳定性结果？",
            "en": "Why does the current time structure not directly change the income-stability result?",
            "ko": "왜 현재 시간 구조가 소득 안정성 결과를 직접 바꾸지 않나요?",
        },
    },
    "q_read_result_not_fortune": {
        "theme": "boundary",
        "depth": "beginner",
        "phase": "after_result",
        "intent": "result_boundary",
        "required": ["result"],
        "required_facts": ["income_signals", "guardrails"],
        "answer_scope": "explain_result_not_fortune_text",
        "score": 58,
        "related_questions": ["q_no_good_bad", "q_result_card_boundary", "follow_rule_basis"],
        "label": {
            "zh": "我应该如何阅读这个结果，而不是把它当成断语？",
            "en": "How should I read this result without treating it as a fortune statement?",
            "ko": "이 결과를 단정문이 아니라 어떻게 읽어야 하나요?",
        },
    },
    "q_no_good_bad": {
        "theme": "boundary",
        "depth": "beginner",
        "phase": "after_result",
        "intent": "result_boundary",
        "required": ["result"],
        "required_facts": ["guardrails"],
        "answer_scope": "explain_no_good_bad_boundary",
        "score": 50,
        "related_questions": ["q_result_card_boundary", "q_read_result_not_fortune"],
        "label": {
            "zh": "这个系统为什么不直接判断“好坏”？",
            "en": "Why does this system avoid direct good/bad judgments?",
            "ko": "왜 이 시스템은 직접적인 길흉 판단을 피하나요?",
        },
    },
    "q_result_card_boundary": {
        "theme": "boundary",
        "depth": "beginner",
        "phase": "after_result",
        "intent": "result_boundary",
        "required": ["result"],
        "required_facts": ["income_signals", "guardrails"],
        "answer_scope": "explain_result_card_boundary",
        "score": 48,
        "related_questions": ["q_read_result_not_fortune", "follow_rule_basis"],
        "label": {
            "zh": "为什么 ResultCard 不是传统断语？",
            "en": "Why is the ResultCard not traditional fortune text?",
            "ko": "왜 ResultCard는 전통식 단정문이 아닌가요?",
        },
    },
    "follow_rule_basis": {
        "theme": "structure_basis",
        "depth": "beginner",
        "phase": "after_result",
        "intent": "rule_basis",
        "required": ["result"],
        "required_facts": ["source_signal", "observed_facts"],
        "answer_scope": "explain_visible_rule_basis_without_internal_debug_dump",
        "score": 46,
        "related_questions": ["q_signal_combination", "q_read_result_not_fortune"],
        "label": {
            "zh": "查看这条判断的规则依据",
            "en": "Show the rule basis for this result",
            "ko": "이 결과의 규칙 근거 보기",
        },
    },
}


def build_guided_question_context(agent_data: Dict[str, Any]) -> Dict[str, Any]:
    chart = dict(agent_data.get("chart") or {})
    time_context = dict(agent_data.get("time_context") or {})
    rules = [row for row in list_bazi_rules().get("items", []) if row.get("engine_enabled") is True]
    facts = _chart_facts(chart, time_context)
    signals: List[Dict[str, Any]] = []
    questions: List[Dict[str, Any]] = _registry_questions(facts)
    for rule in rules:
        match = _match_rule(rule, facts)
        if not match.get("matched"):
            continue
        signal = _signal_from_rule(rule, match)
        signals.append(signal)
        questions.extend(_questions_from_signal(signal, facts))
    questions = _dedupe_questions(questions)
    questions.sort(key=lambda row: int(row.get("score") or 0), reverse=True)
    return {
        "available": True,
        "runtime_scope": "guided_questions_only_no_inference_mutation",
        "rule_signal_count": len(signals),
        "question_count": len(questions),
        "signals": signals[:24],
        "questions": questions[:10],
        "question_registry": {
            "version": QUESTION_REGISTRY_VERSION,
            "single_source": True,
            "items": _registry_questions(facts),
        },
        "guardrails": [
            "RULE_DB_GUIDES_QUESTIONS_ONLY",
            "NO_RESULT_MUTATION",
            "NO_FORTUNE",
            "NO_TIME_AWARE_INFERENCE",
        ],
    }


def build_guided_question_answer(agent_data: Dict[str, Any], question_key: str = "", message: str = "") -> Dict[str, Any]:
    chart = dict(agent_data.get("chart") or {})
    time_context = dict(agent_data.get("time_context") or {})
    if not chart:
        return {
            "available": False,
            "reason": "chart_unavailable",
            "runtime_scope": "guided_question_answer_only_no_inference_mutation",
            "guardrails": ["NO_RESULT_MUTATION", "NO_FORTUNE", "NO_TIME_AWARE_INFERENCE"],
        }

    facts = _chart_facts(chart, time_context)
    inference_context = dict(agent_data.get("inference_context") or {})
    income_bundle = dict(inference_context.get("income_stability") or {})
    guided_context = dict(agent_data.get("guided_question_context") or {})
    clean_key = str(question_key or "").strip()
    clean_message = str(message or "").strip()
    source_question = _find_guided_question(guided_context, clean_key)
    source_signal = _source_signal_for_question(guided_context, source_question)
    intent = route_guided_question_intent(clean_key, clean_message, source_signal)
    answer_kind = str(intent.get("answer_kind") or "structure_overview")
    if not source_signal:
        source_signal = _source_signal_for_answer_kind(guided_context, answer_kind)
    intent["source_signal_id"] = source_signal.get("signal_id") if source_signal else ""
    intent["source_signal_category"] = source_signal.get("category") if source_signal else ""
    retrieved_facts = retrieve_guided_question_facts(intent, chart, time_context, facts, income_bundle, guided_context, source_question, source_signal)
    sections = _guided_answer_sections(answer_kind, chart, time_context, facts, income_bundle, guided_context, source_question, source_signal)
    summary = _guided_answer_summary(answer_kind, source_signal)
    result_relation = _l(
        "这条回答只解释当前问题命中的结构事实；不会改变 income_stability，也不会生成预测。",
        "This answer only explains the structural facts behind the current question; it does not change income_stability or generate prediction.",
        "이 답변은 현재 질문이 맞닿은 구조 사실만 설명하며 income_stability를 바꾸거나 예측을 만들지 않습니다.",
    )
    answer = {
        "available": True,
        "renderer": "v19.guided_question_answer.deterministic.v1",
        "question_key": clean_key,
        "question_text": clean_message,
        "question_contract": {
            "key": clean_key,
            "source": source_question.get("source") or ("question_registry" if _registry_question_for_key(clean_key) else "text_intent_router"),
            "registry_version": source_question.get("registry_version") or QUESTION_REGISTRY_VERSION,
            "intent": intent.get("answer_kind"),
            "required_facts": list(intent.get("fact_scopes") or []),
            "answer_scope": intent.get("answer_scope") or "",
            "supported": intent.get("supported") is not False,
        },
        "intent": intent,
        "retrieved_facts": retrieved_facts,
        "source_signal_id": source_signal.get("signal_id") if source_signal else "",
        "source_signal_category": source_signal.get("category") if source_signal else "",
        "answer_kind": answer_kind,
        "summary": summary,
        "sections": sections,
        "observed_facts": _guided_answer_observed_facts(chart, time_context, facts, income_bundle, source_question, source_signal, answer_kind),
        "composed_text": {"zh": compose_guided_question_answer(clean_message, intent, retrieved_facts, summary, result_relation)},
        "result_relation": result_relation,
        "runtime_scope": "guided_question_answer_only_no_inference_mutation",
        "guardrails": [
            "QUESTION_TO_ANSWER_WORKFLOW",
            "DETERMINISTIC_RENDERER",
            "NO_RESULT_MUTATION",
            "NO_FORTUNE",
            "NO_TIME_AWARE_INFERENCE",
        ],
    }
    answer["content"] = {
        "zh": guided_answer_to_text(answer, "zh").splitlines(),
        "en": guided_answer_to_text(answer, "en").splitlines(),
        "ko": guided_answer_to_text(answer, "ko").splitlines(),
    }
    return answer


def guided_answer_to_text(answer: Dict[str, Any], locale: str = "zh") -> str:
    lines = [_local_text(answer.get("summary"), locale)]
    for section in answer.get("sections") or []:
        if not isinstance(section, dict):
            continue
        title = _local_text(section.get("title"), locale)
        if title:
            lines.extend(["", title + ":"])
        for item in section.get("items") or []:
            if not isinstance(item, dict):
                continue
            label = _local_text(item.get("label"), locale)
            value = _local_text(item.get("value"), locale)
            note = _local_text(item.get("note"), locale)
            lines.append(f"- {label}: {value}" if label else f"- {value}")
            if note:
                lines.append(f"  {note}")
    relation = _local_text(answer.get("result_relation"), locale)
    if relation:
        lines.extend(["", relation])
    return "\n".join(line for line in lines if line is not None)


def guided_answer_to_plain_text(answer: Dict[str, Any], locale: str = "zh") -> str:
    composed = answer.get("composed_text")
    if isinstance(composed, dict):
        text = str(composed.get(locale) or composed.get("zh") or "").strip()
        if text:
            return text
    summary = _local_text(answer.get("summary"), locale).strip()
    relation = _local_text(answer.get("result_relation"), locale).strip()
    sentences = [summary] if summary else []
    for section in answer.get("sections") or []:
        if not isinstance(section, dict):
            continue
        title = _local_text(section.get("title"), locale).strip()
        items = []
        for item in section.get("items") or []:
            if not isinstance(item, dict):
                continue
            label = _local_text(item.get("label"), locale).strip()
            value = _local_text(item.get("value"), locale).strip()
            note = _local_text(item.get("note"), locale).strip()
            if label and value and note:
                items.append(f"{label}是{value}，{note}")
            elif label and value:
                items.append(f"{label}是{value}")
            elif value:
                items.append(value)
        if items:
            sentences.append((f"{title}里，" if title else "") + "；".join(items) + "。")
    if relation:
        sentences.append(relation)
    return "\n\n".join(sentence for sentence in sentences if sentence)


def _chart_facts(chart: Dict[str, Any], time_context: Dict[str, Any]) -> Dict[str, Any]:
    pillars = dict(chart.get("pillars") or {})
    branches = [str((pillars.get(name) or {}).get("branch") or "") for name in ["year", "month", "day", "hour"]]
    stems = [str((pillars.get(name) or {}).get("stem") or "") for name in ["year", "month", "day", "hour"]]
    branch_set = {branch for branch in branches if branch}
    stem_set = {stem for stem in stems if stem}
    stem_elements = {element_of_stem(stem) for stem in stem_set}
    if "" in stem_elements:
        stem_elements.remove("")

    relation_items = list((chart.get("relations") or {}).get("items") or [])
    relation_pairs_by_type, relation_types, relation_pairs = _collect_relation_pairs_from_items(relation_items)

    flow = dict((time_context.get("flow_year") or {}))
    luck = dict((time_context.get("luck_cycle") or {}))
    flow_rel = dict(flow.get("relations_with_natal") or {})
    luck_rel = dict(luck.get("relations_with_natal") or {})

    flow_pairs_by_type = _collect_relation_pairs_from_payload(flow_rel)
    luck_pairs_by_type = _collect_relation_pairs_from_payload(luck_rel)

    for relation_type, pairs in flow_pairs_by_type.items():
        relation_pairs_by_type.setdefault(relation_type, set()).update(pairs)
    for relation_type, pairs in luck_pairs_by_type.items():
        relation_pairs_by_type.setdefault(relation_type, set()).update(pairs)

    relation_pairs = set(relation_pairs)
    for pairs in flow_pairs_by_type.values():
        relation_pairs.update(pairs)
    for pairs in luck_pairs_by_type.values():
        relation_pairs.update(pairs)
    relation_types |= set(flow_pairs_by_type.keys())
    relation_types |= set(luck_pairs_by_type.keys())

    vault_branches = [branch for branch in branches if branch in VAULT_BRANCHES]
    flow_branch = str(((flow.get("pillar") or {}).get("branch")) or "")
    luck_branch = str(((luck.get("pillar") or {}).get("branch")) or "")
    flow_has_relation = bool(flow_rel)
    luck_has_relation = bool(luck_rel)
    return {
        "branches": branches,
        "stems": stems,
        "branch_set": sorted(branch_set),
        "stem_set": sorted(stem_set),
        "all_stems": sorted(stem_set | _hidden_stems_for_branches(branches)),
        "all_stem_elements": sorted({element_of_stem(stem) for stem in (stem_set | _hidden_stems_for_branches(branches)) if element_of_stem(stem)}),
        "vault_branches": sorted(set(vault_branches)),
        "has_vault": bool(vault_branches),
        "relations": relation_items,
        "has_branch_relation": bool(relation_items),
        "relation_pairs_by_type": relation_pairs_by_type,
        "relation_pairs": sorted(relation_pairs),
        "relation_types": relation_types,
        "has_clash": bool(relation_pairs_by_type.get("clash")),
        "has_combination": bool(relation_pairs_by_type.get("combination")),
        "has_harm": bool(relation_pairs_by_type.get("harm")),
        "has_break": bool(relation_pairs_by_type.get("break")),
        "has_three_harmony": _has_three_harmony(branches),
        "flow_branch": flow_branch,
        "luck_branch": luck_branch,
        "flow_is_vault": flow_branch in VAULT_BRANCHES,
        "luck_is_vault": luck_branch in VAULT_BRANCHES,
        "flow_relation_pairs_by_type": flow_pairs_by_type,
        "luck_relation_pairs_by_type": luck_pairs_by_type,
        "has_time_relation": bool(flow_has_relation or luck_has_relation),
    }


def _find_guided_question(guided_context: Dict[str, Any], question_key: str) -> Dict[str, Any]:
    for row in guided_context.get("questions") or []:
        if isinstance(row, dict) and str(row.get("key") or "") == question_key:
            return dict(row)
    return {}


def _source_signal_for_question(guided_context: Dict[str, Any], question: Dict[str, Any]) -> Dict[str, Any]:
    signal_id = str(question.get("source_signal_id") or "")
    if not signal_id:
        return {}
    for row in guided_context.get("signals") or []:
        if isinstance(row, dict) and str(row.get("signal_id") or "") == signal_id:
            return dict(row)
    return {}


def _registry_question_for_key(key: str) -> Dict[str, Any]:
    row = QUESTION_REGISTRY.get(str(key or ""))
    return dict(row) if isinstance(row, dict) else {}


def _registry_questions(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [_registry_question(key, spec) for key, spec in QUESTION_REGISTRY.items()]


def _registry_question(key: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "key": key,
        "theme": spec.get("theme") or "structure_basis",
        "required": list(spec.get("required") or ["chart"]),
        "required_facts": list(spec.get("required_facts") or []),
        "answer_scope": spec.get("answer_scope") or "",
        "intent": spec.get("intent") or "structure_overview",
        "depth": spec.get("depth") or "beginner",
        "phase": spec.get("phase") or "any",
        "related_questions": list(spec.get("related_questions") or []),
        "forbidden_prediction": True,
        "score": int(spec.get("score") or 0),
        "label": dict(spec.get("label") or {}),
        "source": "question_registry",
        "registry_version": QUESTION_REGISTRY_VERSION,
        "guardrails": ["QUESTION_REGISTRY_CONTRACT", "NO_FORTUNE", "NO_RESULT_MUTATION"],
    }


def _source_signal_for_answer_kind(guided_context: Dict[str, Any], answer_kind: str) -> Dict[str, Any]:
    preferred = {
        "branch_relation": {"branch_relation"},
        "vault": {"vault"},
        "time_boundary": {"timing_context"},
        "income_structure": {"wealth_feature", "wealth_mechanism"},
        "metadata_boundary": {"ten_god", "hidden_stem", "stem_branch_attribute", "five_element_relation", "stem_relation", "strength_model"},
        "result_boundary": {"pattern_structure"},
        "rule_basis": {"branch_relation", "vault", "timing_context", "wealth_feature", "wealth_mechanism"},
        "structure_overview": {"branch_relation", "vault", "core_symbol", "hidden_stem", "stem_branch_attribute"},
    }.get(str(answer_kind or ""), set())
    fallback: Dict[str, Any] = {}
    for row in guided_context.get("signals") or []:
        if not isinstance(row, dict):
            continue
        if not fallback:
            fallback = dict(row)
        if str(row.get("category") or "") in preferred:
            return dict(row)
    return fallback


def route_guided_question_intent(question_key: str, message: str, source_signal: Dict[str, Any] | None = None) -> Dict[str, Any]:
    key = str(question_key or "").strip()
    text = str(message or "").strip()
    registered = _registry_question_for_key(key)
    signal_kind = _guided_answer_kind_from_signal(source_signal or {})
    answer_kind = str(registered.get("intent") or signal_kind or _guided_answer_kind(key, text))
    unsupported_reason = _unsupported_question_reason(text)
    intent_map = {
        "branch_relation": ("intent.branch_relation", "structural_relation", ["pillars", "natal_relations", "time_relations"]),
        "vault": ("intent.vault_structure", "structural_relation", ["pillars", "vault_branches", "hidden_stems"]),
        "time_boundary": ("intent.time_context_boundary", "time_structure", ["pillars", "luck_cycle", "flow_year", "time_relations"]),
        "income_structure": ("intent.income_structure", "income_stability", ["income_signals", "pillars", "relations"]),
        "result_boundary": ("intent.result_boundary", "boundary", ["income_signals", "guardrails"]),
        "metadata_boundary": ("intent.structure_metadata", "metadata", ["pillars", "hidden_stems", "stem_elements"]),
        "rule_basis": ("intent.rule_basis", "rule_explanation", ["source_signal", "observed_facts"]),
        "structure_overview": ("intent.structure_overview", "structure_basis", ["pillars", "relations", "vault_branches", "time_context"]),
    }
    intent_id, domain, scopes = intent_map.get(answer_kind, intent_map["structure_overview"])
    terms = _detected_intent_terms(key + " " + text)
    return {
        "intent_id": intent_id,
        "domain": domain,
        "answer_kind": answer_kind,
        "supported": not bool(unsupported_reason),
        "unsupported_reason": unsupported_reason,
        "confidence": 0.92 if signal_kind else (0.78 if terms else 0.58),
        "detected_terms": terms,
        "fact_scopes": list(registered.get("required_facts") or scopes),
        "answer_scope": registered.get("answer_scope") or "",
        "router": "v19.intent_router.rule_keyword_and_signal.v1",
        "guardrails": ["ROUTE_TO_FACTS_ONLY", "NO_RESULT_MUTATION", "NO_FORTUNE"],
    }


def retrieve_guided_question_facts(
    intent: Dict[str, Any],
    chart: Dict[str, Any],
    time_context: Dict[str, Any],
    facts: Dict[str, Any],
    income_bundle: Dict[str, Any],
    guided_context: Dict[str, Any],
    source_question: Dict[str, Any],
    source_signal: Dict[str, Any],
) -> Dict[str, Any]:
    if intent.get("supported") is False:
        return {
            "retriever": "v19.fact_retriever.intent_scoped.v1",
            "intent_id": intent.get("intent_id"),
            "unsupported_reason": intent.get("unsupported_reason"),
            "fact_scopes": list(intent.get("fact_scopes") or []),
            "guardrails": ["UNSUPPORTED_INTENT_NO_FACT_INVENTION", "NO_FORTUNE"],
        }
    pillars = dict(chart.get("pillars") or {})
    luck = dict(time_context.get("luck_cycle") or {})
    flow = dict(time_context.get("flow_year") or {})
    relation_rows = _retrieved_relation_facts(chart, facts)
    vault_rows = _retrieved_vault_facts(facts)
    return {
        "retriever": "v19.fact_retriever.intent_scoped.v1",
        "intent_id": intent.get("intent_id"),
        "fact_scopes": list(intent.get("fact_scopes") or []),
        "source_question": {
            "key": source_question.get("key") or "",
            "label": _source_question_label(source_question),
        },
        "source_signal": {
            "signal_id": source_signal.get("signal_id") or "",
            "rule_id": source_signal.get("rule_id") or "",
            "knowledge_id": source_signal.get("knowledge_id") or "",
            "category": source_signal.get("category") or "",
            "title": source_signal.get("title") or "",
            "reason": source_signal.get("reason") or "",
            "observed": list(source_signal.get("observed") or []),
        },
        "chart_anchor": {
            "day_pillar": (pillars.get("day") or {}).get("display") or "",
            "day_stem": (pillars.get("day") or {}).get("stem") or "",
            "month_pillar": (pillars.get("month") or {}).get("display") or "",
            "month_branch": (pillars.get("month") or {}).get("branch") or "",
            "pillar_order": [
                {
                    "position": key,
                    "display": (pillars.get(key) or {}).get("display") or "",
                    "stem": (pillars.get(key) or {}).get("stem") or "",
                    "branch": (pillars.get(key) or {}).get("branch") or "",
                }
                for key in ["year", "month", "day", "hour"]
            ],
        },
        "relations": relation_rows,
        "vaults": vault_rows,
        "hidden_stems": {
            branch: _hidden_stems_label(branch)
            for branch in facts.get("branch_set") or []
            if _hidden_stems_label(branch)
        },
        "time_context": {
            "luck_cycle": {
                "pillar": ((luck.get("pillar") or {}).get("display")) or "",
                "age_range": f"{luck.get('start_age', '')}-{luck.get('end_age', '')}".strip("-"),
                "relations": _serializable_relation_map(facts.get("luck_relation_pairs_by_type") or {}),
            },
            "flow_year": {
                "year": flow.get("year") or "",
                "pillar": ((flow.get("pillar") or {}).get("display")) or "",
                "relations": _serializable_relation_map(facts.get("flow_relation_pairs_by_type") or {}),
            },
            "scope": "time_context_only_no_income_stability_mutation",
        },
        "income_signals": {
            str(row.get("key") or ""): row.get("value")
            for row in income_bundle.get("signals", [])
            if isinstance(row, dict) and row.get("key")
        },
        "available_question_count": len(guided_context.get("questions") or []),
        "guardrails": ["FACTS_ARE_INPUTS_NOT_PREDICTIONS", "TIME_CONTEXT_DOES_NOT_MUTATE_RESULT"],
    }


def compose_guided_question_answer(question_text: str, intent: Dict[str, Any], facts: Dict[str, Any], summary: Dict[str, str], result_relation: Dict[str, str]) -> str:
    if intent.get("supported") is False:
        return (
            "这个问题当前不在系统支持的结构分析范围内，所以我不会硬编答案。"
            "目前可以可靠回答的是：四柱结构、日主和月令、藏干、地支冲合、墓库、大运和流年作为时间背景，以及收入稳定性这一项结构信号。"
            "你可以换成上方推荐问题，或把问题改成“这张命盘先看哪些结构特征？”这类结构问题。"
        )
    answer_kind = str(intent.get("answer_kind") or "structure_overview")
    anchor = dict(facts.get("chart_anchor") or {})
    relations = list(facts.get("relations") or [])
    vaults = list(facts.get("vaults") or [])
    time_context = dict(facts.get("time_context") or {})
    income_signals = dict(facts.get("income_signals") or {})
    paragraphs: List[str] = []

    if answer_kind == "branch_relation":
        if relations:
            relation_text = "；".join(_relation_fact_sentence(row) for row in relations[:6])
            paragraphs.append(f"你问的是冲合关系。当前可见的结构关系主要是：{relation_text}。这里的重点不是判断好坏，而是看哪些地支之间产生了连接、牵动或张力。")
        else:
            paragraphs.append("你问的是冲合关系。当前可取到的命盘事实里没有明确的冲合条目，所以这里不能硬说某个关系已经触发；最多只能回到四柱本身继续看结构。")
        paragraphs.append(_time_context_sentence(time_context))
    elif answer_kind == "vault":
        if vaults:
            vault_text = "；".join(f"{row.get('branch')}在{row.get('locations')}，藏干是{row.get('hidden_stems')}" for row in vaults[:4])
            paragraphs.append(f"你问的是墓库结构。当前实际看到的是：{vault_text}。这类信息适合用来说明结构里哪里有收束、储藏或承载的节点。")
        else:
            paragraphs.append("你问的是墓库结构。当前事实检索没有找到明确墓库支，所以不能为了回答而补一个不存在的墓库判断。")
    elif answer_kind == "time_boundary":
        paragraphs.append(_time_context_sentence(time_context))
        paragraphs.append("这部分只能说明大运、流年和本命之间有没有形成背景关系；它不会在当前版本里直接改写收入稳定性结果。")
    elif answer_kind == "income_structure":
        if income_signals:
            signal_text = "；".join(f"{_income_signal_label(key)}是{value}" for key, value in income_signals.items() if key and value)
            paragraphs.append(f"你问的是收入稳定性结构。当前确定性规则给出的相关信号是：{signal_text}。这些信号说明结构状态，不等同于财运预测。")
        else:
            paragraphs.append("你问的是收入稳定性结构，但当前没有取到可用的收入结构信号，所以这里不能硬生成结论。")
    elif answer_kind == "metadata_boundary":
        day = anchor.get("day_pillar") or "日柱未取到"
        month = anchor.get("month_pillar") or "月柱未取到"
        hidden = dict(facts.get("hidden_stems") or {})
        hidden_text = "；".join(f"{branch}藏{stems}" for branch, stems in hidden.items()) or "当前没有可展开的藏干信息"
        paragraphs.append(f"你问的是十神、藏干或日主月令这类元数据。当前结构基点可以先看日柱{day}和月柱{month}；藏干层面看到：{hidden_text}。")
        paragraphs.append("这些内容的作用是解释关系来源，比如某个五行或关系从哪里出现；它本身不是一句断语，也不直接等于某个结果。")
    elif answer_kind == "rule_basis":
        signal = dict(facts.get("source_signal") or {})
        observed = "、".join(str(item) for item in signal.get("observed") or []) or "当前结构事实"
        paragraphs.append(f"这条回答的依据来自规则库命中的结构信号：{observed}。用户端只需要知道它对应了哪些可见事实，内部规则编号留给 Lab 审核。")
    else:
        day = anchor.get("day_pillar") or "日柱未取到"
        month = anchor.get("month_pillar") or "月柱未取到"
        relation_text = "；".join(_relation_fact_sentence(row) for row in relations[:3]) if relations else "当前没有明确冲合条目"
        vault_text = "、".join(str(row.get("branch")) for row in vaults) if vaults else "未见明确墓库支"
        paragraphs.append(f"如果只看结构，这张命盘可以先抓三个入口：日柱是{day}，月柱是{month}，地支关系是{relation_text}，墓库观察是{vault_text}。")
        paragraphs.append("这些入口只是帮你建立阅读顺序：先知道结构事实在哪里，再讨论某个主题是否有足够证据。")

    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph and paragraph.strip())


def _detected_intent_terms(text: str) -> List[str]:
    terms = []
    for token in ["冲", "合", "六合", "三合", "墓库", "藏干", "十神", "日主", "月令", "大运", "流年", "时间", "收入", "财富", "规则依据"]:
        if token in text:
            terms.append(token)
    return _dedupe_keep_order(terms)


def _unsupported_question_reason(text: str) -> str:
    clean = str(text or "")
    unsupported_terms = ["婚姻", "感情", "健康", "疾病", "子女", "父母", "官司", "升职", "考试", "什么时候", "哪一年", "发财", "破财", "好不好", "会不会"]
    for term in unsupported_terms:
        if term in clean:
            return f"unsupported_topic:{term}"
    return ""


def _retrieved_relation_facts(chart: Dict[str, Any], facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in (chart.get("relations") or {}).get("items") or []:
        if not isinstance(item, dict):
            continue
        relation_type = _normalize_relation_type(str(item.get("type") or item.get("relation_type") or ""))
        for relation_key in _relation_keys_from_row(item):
            rows.append(
                {
                    "layer": "命盘内部",
                    "type": relation_type,
                    "pair": relation_key,
                    "pillars": list(item.get("pillars") or []),
                    "raw_branches": str(item.get("branches") or ""),
                }
            )
    for relation_type, pairs in (facts.get("luck_relation_pairs_by_type") or {}).items():
        for pair in sorted(pairs):
            rows.append({"layer": "大运与本命", "type": str(relation_type), "pair": str(pair)})
    for relation_type, pairs in (facts.get("flow_relation_pairs_by_type") or {}).items():
        for pair in sorted(pairs):
            rows.append({"layer": "流年与本命", "type": str(relation_type), "pair": str(pair)})
    return rows


def _retrieved_vault_facts(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for branch in facts.get("vault_branches") or []:
        rows.append(
            {
                "branch": branch,
                "locations": _branch_locations_from_facts(branch, facts),
                "hidden_stems": _hidden_stems_label(branch),
            }
        )
    return rows


def _branch_locations_from_facts(branch: str, facts: Dict[str, Any]) -> str:
    labels = ["年柱", "月柱", "日柱", "时柱"]
    branches = list(facts.get("branches") or [])
    locations = [labels[index] for index, item in enumerate(branches[:4]) if str(item) == str(branch)]
    return "、".join(locations) if locations else "可见位置未定位"


def _relation_fact_sentence(row: Dict[str, Any]) -> str:
    pair = str(row.get("pair") or "").replace("-", "")
    return f"{row.get('layer')}{_relation_type_label(str(row.get('type') or ''))}{pair}"


def _relation_type_label(value: str) -> str:
    labels = {
        "clash": "出现冲：",
        "combination": "出现合：",
        "harm": "出现害：",
        "break": "出现破：",
        "unknown": "出现关系：",
    }
    return labels.get(value, "出现关系：")


def _time_context_sentence(time_context: Dict[str, Any]) -> str:
    luck = dict(time_context.get("luck_cycle") or {})
    flow = dict(time_context.get("flow_year") or {})
    luck_pillar = luck.get("pillar") or "未取到大运柱"
    flow_pillar = flow.get("pillar") or "未取到流年柱"
    flow_year = flow.get("year") or ""
    luck_rel = _relation_map_text(dict(luck.get("relations") or {}))
    flow_rel = _relation_map_text(dict(flow.get("relations") or {}))
    return f"时间背景上，当前大运显示为{luck_pillar}，流年显示为{flow_year}{flow_pillar}；大运关系是{luck_rel}，流年关系是{flow_rel}。这些只作为时间背景阅读。"


def _relation_map_text(relations: Dict[str, List[str]]) -> str:
    parts = []
    for relation_type, pairs in relations.items():
        for pair in pairs:
            parts.append(f"{_relation_type_label(str(relation_type)).replace('出现', '').replace('：', '')}{str(pair).replace('-', '')}")
    return "、".join(parts) if parts else "未见明确冲合条目"


def _income_signal_label(key: str) -> str:
    labels = {
        "self_capacity": "自我承载力",
        "wealth_presence": "财富结构出现度",
        "wealth_accessibility": "财富可达性",
        "volatility": "波动性",
        "structure_binding": "结构牵制",
        "income_stability": "收入稳定性结构信号",
    }
    return labels.get(str(key), str(key))


def _guided_answer_kind_from_signal(signal: Dict[str, Any]) -> str:
    if not signal:
        return ""
    category = str(signal.get("category") or "")
    domain = str(signal.get("domain") or "")
    if category == "vault":
        return "vault"
    if category == "branch_relation":
        return "branch_relation"
    if category == "timing_context" or domain == "time_structure":
        return "time_boundary"
    if category in {"wealth_feature", "wealth_mechanism"} or domain in {"income_stability", "wealth"}:
        return "income_structure"
    if category in {"ten_god", "hidden_stem", "stem_branch_attribute", "five_element_relation", "stem_relation", "strength_model"}:
        return "metadata_boundary"
    if category == "pattern_structure":
        return "result_boundary"
    return ""


def _guided_answer_observed_facts(
    chart: Dict[str, Any],
    time_context: Dict[str, Any],
    facts: Dict[str, Any],
    income_bundle: Dict[str, Any],
    source_question: Dict[str, Any],
    source_signal: Dict[str, Any],
    answer_kind: str,
) -> Dict[str, Any]:
    pillars = dict(chart.get("pillars") or {})
    luck = dict(time_context.get("luck_cycle") or {})
    flow = dict(time_context.get("flow_year") or {})
    return {
        "answer_kind": answer_kind,
        "source_question_key": source_question.get("key") or "",
        "source_signal_id": source_signal.get("signal_id") or "",
        "source_signal_category": source_signal.get("category") or "",
        "source_signal_observed": list(source_signal.get("observed") or []),
        "natal_pillars": {
            key: {
                "display": (pillars.get(key) or {}).get("display") or "",
                "stem": (pillars.get(key) or {}).get("stem") or "",
                "branch": (pillars.get(key) or {}).get("branch") or "",
            }
            for key in ["year", "month", "day", "hour"]
        },
        "vault_branches": list(facts.get("vault_branches") or []),
        "relation_types": sorted(str(item) for item in (facts.get("relation_types") or []) if str(item)),
        "relation_pairs": list(facts.get("relation_pairs") or []),
        "time_context": {
            "luck_cycle": {
                "pillar": ((luck.get("pillar") or {}).get("display")) or "",
                "relations": _serializable_relation_map(facts.get("luck_relation_pairs_by_type") or {}),
            },
            "flow_year": {
                "year": flow.get("year") or "",
                "pillar": ((flow.get("pillar") or {}).get("display")) or "",
                "relations": _serializable_relation_map(facts.get("flow_relation_pairs_by_type") or {}),
            },
        },
        "income_stability": {
            str(row.get("key") or ""): row.get("value")
            for row in income_bundle.get("signals", [])
            if isinstance(row, dict) and row.get("key")
        },
        "guardrail": "observed_facts_support_answer_only_no_result_mutation",
    }


def _serializable_relation_map(raw: Dict[str, Any]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for key, value in raw.items():
        if isinstance(value, set):
            out[str(key)] = sorted(str(item) for item in value if str(item))
        elif isinstance(value, list):
            out[str(key)] = [str(item) for item in value if str(item)]
    return out


def _guided_answer_kind(question_key: str, message: str) -> str:
    key = str(question_key or "")
    text = str(message or "")
    if key in {"q_branch_relation_detail", "q_time_vs_natal_relation", "q_combination_context", "q_three_harmony_context"} or "branch_relation" in key or key == "q_time_context" or any(token in text for token in ["冲合", "冲", "合", "关系", "三合", "六合"]):
        return "branch_relation"
    if "vault" in key or "墓库" in text:
        return "vault"
    if key in {"q_time_context_boundary", "q_luck_flow_layers", "q_time_not_inference"} or "时间结构" in text or "大运" in text or "流年" in text:
        return "time_boundary"
    if key in {
        "q_income_stability",
        "q_income_factors",
        "q_income_continuity",
        "q_wealth_accessibility",
        "q_accessibility_signals",
        "q_signal_combination",
        "q_primary_auxiliary_signals",
        "q_volatility_factors",
    } or "income" in key or "wealth" in key or "收入" in text or "财富" in text:
        return "income_structure"
    if key in {"q_read_result_not_fortune", "q_no_good_bad", "q_result_card_boundary", "q_cautious_reading"}:
        return "result_boundary"
    if key in {"q_day_master_month_anchor", "q_hidden_stem_role"} or "ten_god" in key or "十神" in text or "藏干" in text or "日主" in text or "月令" in text:
        return "metadata_boundary"
    if key == "follow_rule_basis" or "规则依据" in text:
        return "rule_basis"
    return "structure_overview"


def _guided_answer_summary(answer_kind: str, source_signal: Dict[str, Any] | None = None) -> Dict[str, str]:
    observed = _signal_observed_values(source_signal or {})
    observed_text = "、".join(observed)
    summaries = {
        "branch_relation": _l(
            f"这条问题命中的结构依据是{observed_text or '当前可见的冲合关系'}；它说明地支之间的连接或张力，只用于解释结构背景。",
            f"The structural basis behind this question is {observed_text or 'the visible branch relations'}; it describes branch links or tension as context only.",
            f"이 질문의 구조 근거는 {observed_text or '현재 보이는 지지 관계'}이며, 지지 사이의 연결이나 긴장을 배경으로만 설명합니다.",
        ),
        "vault": _l(
            f"这条问题命中的结构依据是{observed_text or '墓库支'}；下面只解释它们出现在哪里、藏干是什么、能读到哪一层。",
            f"The structural basis behind this question is {observed_text or 'vault branches'}; the answer explains where they appear, their hidden stems, and the reading boundary.",
            f"이 질문의 구조 근거는 {observed_text or '묘고 지지'}이며, 어디에 나타나는지와 지장간, 읽기 경계를 설명합니다.",
        ),
        "time_boundary": _l(
            "这条问题的直接回答：大运和流年目前只进入时间背景层；即使出现冲合，也只用于解释提问和展示背景，不参与当前结果聚合。",
            "Direct answer: luck cycle and flow year currently stay in the time-context layer; even when relations appear, they guide questions and display context only.",
            "직접 답변: 대운과 세운은 현재 시간 배경층에만 있으며, 충합이 나타나도 질문 안내와 배경 표시로만 사용됩니다.",
        ),
        "income_structure": _l(
            "这条问题的直接回答：收入稳定性由已生成的确定性结构信号组成；这些信号说明结构状态，不是财运预测。",
            "Direct answer: income stability is composed from existing deterministic structural signals; these describe structure state, not wealth prediction.",
            "직접 답변: 소득 안정성은 기존 결정론적 구조 신호로 구성되며, 이는 구조 상태 설명이지 재물운 예측이 아닙니다.",
        ),
        "result_boundary": _l(
            "这条问题的直接回答：Result 卡片是规则输出的结构摘要，只回答当前支持的结构域，不是传统断语。",
            "Direct answer: the Result card is a rule-produced structure summary for the supported domain, not traditional fortune text.",
            "직접 답변: Result 카드는 지원되는 구조 영역에 대한 규칙 기반 요약이며 전통식 단정문이 아닙니다.",
        ),
        "metadata_boundary": _l(
            "这条问题的直接回答：十神、藏干、五行属性在这里是关系元数据，用来解释结构来源，不直接成为结论。",
            "Direct answer: Ten God, hidden stems, and element attributes are relational metadata here; they explain structure sources and are not conclusions by themselves.",
            "직접 답변: 십성, 지장간, 오행 속성은 여기서 관계 메타데이터이며 구조 출처를 설명할 뿐 직접 결론은 아닙니다.",
        ),
        "rule_basis": _l(
            "这条问题的直接回答：规则依据来自结构输入和确定性规则摘要；用户端只展示可读摘要，内部 rule_id 留在 Lab 中审计。",
            "Direct answer: the rule basis comes from structural inputs and deterministic-rule summaries; the user view shows readable summaries while rule_id audit stays in Lab.",
            "직접 답변: 규칙 근거는 구조 입력과 결정론적 규칙 요약에서 오며, 사용자 화면에는 읽기 쉬운 요약만 표시됩니다.",
        ),
        "structure_overview": _l(
            "这条问题的直接回答：先看日主、月令、四柱地支、可见冲合和时间背景；这些都是结构事实，不是结果好坏。",
            "Direct answer: first read the day master, month structure, four-pillar branches, visible relations, and time context; these are structure facts, not good/bad outcomes.",
            "직접 답변: 먼저 일간, 월지 구조, 사주 지지, 보이는 관계와 시간 배경을 봅니다. 이는 구조 사실이지 길흉 판단이 아닙니다.",
        ),
    }
    return summaries.get(answer_kind, summaries["structure_overview"])


def _guided_answer_sections(
    answer_kind: str,
    chart: Dict[str, Any],
    time_context: Dict[str, Any],
    facts: Dict[str, Any],
    income_bundle: Dict[str, Any],
    guided_context: Dict[str, Any],
    source_question: Dict[str, Any] | None = None,
    source_signal: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    source_section = _source_signal_section(source_question or {}, source_signal or {})
    if answer_kind == "branch_relation":
        return source_section + [
            _section("实际触发的关系", "Actual triggered relations", "실제 트리거된 관계", _relation_answer_items(chart, time_context, source_signal or {})),
            _section("阅读边界", "Reading boundary", "읽기 경계", _boundary_items("relations")),
        ]
    if answer_kind == "vault":
        return source_section + [
            _section("实际命中的墓库结构", "Actual triggered vault structure", "실제 트리거된 묘고 구조", _vault_answer_items(chart, time_context, facts, source_signal or {})),
            _section("阅读边界", "Reading boundary", "읽기 경계", _boundary_items("vault")),
        ]
    if answer_kind == "time_boundary":
        return source_section + [
            _section("时间背景层", "Time-context layer", "시간 배경층", _time_answer_items(time_context)),
            _section("结果边界", "Result boundary", "결과 경계", _boundary_items("time")),
        ]
    if answer_kind == "income_structure":
        return source_section + [
            _section("当前确定性信号", "Current deterministic signals", "현재 결정론적 신호", _income_answer_items(income_bundle)),
            _section("结果边界", "Result boundary", "결과 경계", _boundary_items("income")),
        ]
    if answer_kind == "result_boundary":
        return source_section + [
            _section("如何读 Result", "How to read Result", "Result 읽는 법", _result_boundary_items(income_bundle)),
            _section("禁止外推", "Do not extrapolate", "확대 해석 금지", _boundary_items("result")),
        ]
    if answer_kind == "metadata_boundary":
        return source_section + [
            _section("结构元数据", "Structure metadata", "구조 메타데이터", _metadata_answer_items(chart)),
            _section("阅读边界", "Reading boundary", "읽기 경계", _boundary_items("metadata")),
        ]
    if answer_kind == "rule_basis":
        return source_section + [
            _section("规则摘要", "Rule summary", "규칙 요약", _rule_basis_items(income_bundle)),
            _section("审计边界", "Audit boundary", "감사 경계", _boundary_items("rule_basis")),
        ]
    return source_section + [
        _section("结构基点", "Structural anchors", "구조 기준점", _overview_answer_items(chart, facts)),
        _section("可见关系", "Visible relations", "보이는 관계", _relation_answer_items(chart, time_context)),
        _section("阅读边界", "Reading boundary", "읽기 경계", _boundary_items("overview")),
    ]


def _source_signal_section(question: Dict[str, Any], signal: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not signal:
        return []
    observed = _signal_observed_values(signal)
    label = _source_question_label(question)
    items = [
        _item(
            _l("当前问题", "Current question", "현재 질문"),
            label,
            _l("回答优先围绕这个问题背后的结构信号组织。", "The answer is organized around the structural signal behind this question.", "답변은 이 질문 뒤의 구조 신호를 중심으로 구성됩니다."),
        ),
        _item(
            _l("命中的结构依据", "Matched structural basis", "일치한 구조 근거"),
            _signal_user_label(str(signal.get("category") or signal.get("domain") or "")),
            _l("这是用户可读分类，不展示内部规则名。", "This is a user-facing category, not an internal rule name.", "이는 사용자용 분류이며 내부 규칙명이 아닙니다."),
        ),
    ]
    if observed:
        items.append(
            _item(
                _l("观察到的结构", "Observed structure", "관찰된 구조"),
                _l("、".join(observed), " / ".join(observed), " / ".join(observed)),
                _l("下面只解释这些已观察到的结构事实。", "The sections below explain only these observed structural facts.", "아래 내용은 관찰된 구조 사실만 설명합니다."),
            )
        )
    return [_section("这条问题为什么被回答", "Why this question is being answered", "이 질문을 답하는 이유", items)]


def _source_question_label(question: Dict[str, Any]) -> Dict[str, str]:
    label = question.get("label") if isinstance(question.get("label"), dict) else {}
    return _l(
        str(label.get("zh") or question.get("key") or "当前问题"),
        str(label.get("en") or label.get("zh") or question.get("key") or "Current question"),
        str(label.get("ko") or label.get("zh") or question.get("key") or "현재 질문"),
    )


def _relation_answer_items(chart: Dict[str, Any], time_context: Dict[str, Any], source_signal: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for row in (chart.get("relations") or {}).get("items") or []:
        if not isinstance(row, dict):
            continue
        relation_type = str(row.get("type") or "")
        branches = str(row.get("branches") or "-")
        pillars = row.get("pillars") if isinstance(row.get("pillars"), list) else []
        items.append(
            _item(
                _relation_type_label(relation_type),
                _l(branches, branches, branches),
                _l(
                    "本命四柱内部关系：" + (_pillar_names(pillars, "zh") or "-"),
                    "Natal four-pillar relation: " + (_pillar_names(pillars, "en") or "-"),
                    "본명 사주 내부 관계: " + (_pillar_names(pillars, "ko") or "-"),
                ),
            )
        )
    items.extend(_time_relation_items(time_context))
    observed = _signal_observed_values(source_signal or {})
    if observed:
        items.append(
            _item(
                _l("本题聚焦", "Question focus", "질문 초점"),
                _l("、".join(observed), " / ".join(observed), " / ".join(observed)),
                _l("这些是推荐该问题时命中的关系类别或关系对。", "These are the relation categories or pairs matched when recommending this question.", "이는 이 질문을 추천할 때 일치한 관계 범주 또는 관계쌍입니다."),
            )
        )
    if not items:
        items.append(
            _item(
                _l("当前检测", "Current detection", "현재 감지"),
                _l("未见已检测的本命或时间冲合关系", "No detected natal or time-context clash/combination relation", "감지된 본명 또는 시간 충합 관계가 없습니다"),
                _l("这只表示当前规则集未检测到关系，不代表没有其他传统体系会讨论的关系。", "This only means the current rule set detected none; other systems may discuss additional relations.", "이는 현재 규칙 세트에서 감지하지 못했다는 뜻이며 다른 체계의 관계 논의를 배제하지 않습니다."),
            )
        )
    return items


def _time_relation_items(time_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    _append_time_relation_items(items, "luck_cycle", time_context.get("luck_cycle"))
    _append_time_relation_items(items, "flow_year", time_context.get("flow_year"))
    return items


def _append_time_relation_items(items: List[Dict[str, Any]], scope: str, payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    rel = payload.get("relations_with_natal") if isinstance(payload.get("relations_with_natal"), dict) else {}
    pillar = (payload.get("pillar") or {}).get("display") if isinstance(payload.get("pillar"), dict) else ""
    scope_label = _l("当前大运" if scope == "luck_cycle" else "流年", "Current luck cycle" if scope == "luck_cycle" else "Flow year", "현재 대운" if scope == "luck_cycle" else "세운")
    for key, relation_label in [("clashes", _relation_type_label("six_clash")), ("combinations", _relation_type_label("six_combination"))]:
        for value in _as_list(rel.get(key)):
            text = str(value or "")
            if not text:
                continue
            items.append(
                _item(
                    scope_label,
                    _l(f"{_local_text(relation_label, 'zh')} {text}", f"{_local_text(relation_label, 'en')} {text}", f"{_local_text(relation_label, 'ko')} {text}"),
                    _l(
                        f"{pillar or '-'} 只作为时间背景层显示。",
                        f"{pillar or '-'} is displayed as time-context only.",
                        f"{pillar or '-'}는 시간 배경층으로만 표시됩니다.",
                    ),
                )
            )


def _vault_answer_items(chart: Dict[str, Any], time_context: Dict[str, Any], facts: Dict[str, Any], source_signal: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    observed = [item for item in _signal_observed_values(source_signal or {}) if item in VAULT_BRANCHES]
    natal = [str(item) for item in facts.get("vault_branches") or [] if str(item)]
    focus = observed or natal
    items = []
    for branch in focus:
        locations = _branch_locations(chart, time_context, branch)
        items.append(
            _item(
                _l(f"{branch} 墓库支", f"{branch} vault branch", f"{branch} 묘고 지지"),
                _l("、".join(locations) if locations else "位置未标记", " / ".join(locations) if locations else "Location not marked", " / ".join(locations) if locations else "위치 표시 없음"),
                _l(
                    f"藏干：{_hidden_stems_label(branch)}。这里只说明结构层位置和藏干背景。",
                    f"Hidden stems: {_hidden_stems_label(branch)}. This only describes structural location and hidden-stem background.",
                    f"지장간: {_hidden_stems_label(branch)}. 구조 위치와 지장간 배경만 설명합니다.",
                ),
            )
        )
    if not items:
        items.append(
            _item(
                _l("本命墓库支", "Natal vault branches", "본명 묘고 지지"),
                _l("未见", "None detected", "감지 없음"),
                _l("当前规则没有在本命四柱中检测到墓库支。", "The current rule set detected no natal vault branch.", "현재 규칙 세트는 본명 사주에서 묘고 지지를 감지하지 못했습니다."),
            )
        )
    time_vaults = []
    if facts.get("luck_is_vault"):
        time_vaults.append(str(facts.get("luck_branch") or ""))
    if facts.get("flow_is_vault"):
        time_vaults.append(str(facts.get("flow_branch") or ""))
    items.append(
        _item(
            _l("时间背景墓库支", "Time-context vault branches", "시간 배경 묘고 지지"),
            _l("、".join([item for item in time_vaults if item]) if time_vaults else "未见", ", ".join([item for item in time_vaults if item]) if time_vaults else "None detected", ", ".join([item for item in time_vaults if item]) if time_vaults else "감지 없음"),
            _l("即使时间背景出现墓库，也不直接改变当前 income_stability。", "Even if a time-context vault appears, it does not directly change current income_stability.", "시간 배경에 묘고가 나타나도 현재 income_stability를 직접 바꾸지 않습니다."),
        )
    )
    return items


def _time_answer_items(time_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = _time_relation_items(time_context)
    flow = time_context.get("flow_year") if isinstance(time_context.get("flow_year"), dict) else {}
    luck = time_context.get("luck_cycle") if isinstance(time_context.get("luck_cycle"), dict) else {}
    items.insert(
        0,
        _item(
            _l("当前时间背景", "Current time context", "현재 시간 배경"),
            _l(
                f"大运 {((luck.get('pillar') or {}).get('display') if isinstance(luck.get('pillar'), dict) else '-') or '-'}；流年 {flow.get('year') or '-'} {((flow.get('pillar') or {}).get('display') if isinstance(flow.get('pillar'), dict) else '') or ''}".strip(),
                f"Luck cycle {((luck.get('pillar') or {}).get('display') if isinstance(luck.get('pillar'), dict) else '-') or '-'}; flow year {flow.get('year') or '-'} {((flow.get('pillar') or {}).get('display') if isinstance(flow.get('pillar'), dict) else '') or ''}".strip(),
                f"대운 {((luck.get('pillar') or {}).get('display') if isinstance(luck.get('pillar'), dict) else '-') or '-'}; 세운 {flow.get('year') or '-'} {((flow.get('pillar') or {}).get('display') if isinstance(flow.get('pillar'), dict) else '') or ''}".strip(),
            ),
            _l("当前阶段仅作为上下文。", "At this stage this is context only.", "현재 단계에서는 맥락으로만 사용됩니다."),
        ),
    )
    if len(items) == 1:
        items.append(
            _item(
                _l("时间关系", "Time relations", "시간 관계"),
                _l("未见已检测的冲合关系", "No detected clash/combination relation", "감지된 충합 관계 없음"),
                _l("仍然不改变既有结果。", "The existing result remains unchanged.", "기존 결과는 바뀌지 않습니다."),
            )
        )
    return items


def _income_answer_items(income_bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    signals = _income_signal_map(income_bundle)
    order = [
        ("income_stability", "收入稳定性结构信号", "Income stability signal", "소득 안정성 구조 신호"),
        ("self_capacity", "自我承载力", "Self capacity", "자기 수용력"),
        ("wealth_presence", "财富结构出现度", "Wealth presence", "재성 출현도"),
        ("wealth_accessibility", "财富可达性", "Wealth accessibility", "재성 접근성"),
        ("volatility", "波动性", "Volatility", "변동성"),
        ("structure_binding", "结构牵制", "Structure binding", "구조 결속"),
    ]
    items = []
    for key, zh, en, ko in order:
        value = str(signals.get(key) or "unknown")
        items.append(_item(_l(zh, en, ko), _value_l(value), _l("来自既有确定性规则聚合。", "Comes from the existing deterministic rule aggregation.", "기존 결정론적 규칙 집계에서 온 값입니다.")))
    return items


def _result_boundary_items(income_bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    signals = _income_signal_map(income_bundle)
    return [
        _item(_l("Result 的用途", "Purpose of Result", "Result의 용도"), _l("展示当前支持域的结构摘要", "Shows a structure summary for the currently supported domain", "현재 지원 영역의 구조 요약을 표시합니다"), _l("它不是对每个引导问题的完整回答。", "It is not the complete answer to every guided question.", "모든 안내 질문에 대한 전체 답변은 아닙니다.")),
        _item(_l("当前结果值", "Current result value", "현재 결과값"), _value_l(str(signals.get("income_stability") or "unknown")), _l("该值保持由原 income_stability 推理生成。", "This value remains generated by the original income_stability inference.", "이 값은 기존 income_stability 추론에서 생성된 그대로입니다.")),
    ]


def _metadata_answer_items(chart: Dict[str, Any]) -> List[Dict[str, Any]]:
    pillars = dict(chart.get("pillars") or {})
    stems = [str((pillars.get(name) or {}).get("stem") or "") for name in ["year", "month", "day", "hour"]]
    branches = [str((pillars.get(name) or {}).get("branch") or "") for name in ["year", "month", "day", "hour"]]
    return [
        _item(_l("可见天干", "Visible stems", "보이는 천간"), _l("、".join([item for item in stems if item]) or "-", ", ".join([item for item in stems if item]) or "-", ", ".join([item for item in stems if item]) or "-"), _l("用于关系映射，不单独断事。", "Used for relation mapping; not a standalone judgement.", "관계 매핑에 사용되며 단독 판단이 아닙니다.")),
        _item(_l("可见地支", "Visible branches", "보이는 지지"), _l("、".join([item for item in branches if item]) or "-", ", ".join([item for item in branches if item]) or "-", ", ".join([item for item in branches if item]) or "-"), _l("用于结构检测和藏干背景。", "Used for structure detection and hidden-stem background.", "구조 감지와 지장간 배경에 사용됩니다.")),
    ]


def _rule_basis_items(income_bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    evidence = [str(item) for item in income_bundle.get("evidence_summary") or [] if str(item)]
    return [
        _item(_l("用户端依据", "User-facing basis", "사용자용 근거"), _l("结构输入 + 确定性规则摘要", "Structural input + deterministic-rule summary", "구조 입력 + 결정론적 규칙 요약"), _l("详细 rule_id 留在 Lab 侧审计。", "Detailed rule_id audit remains in Lab.", "상세 rule_id 감사는 Lab에 남습니다.")),
        _item(_l("证据摘要", "Evidence summary", "근거 요약"), _l("；".join(evidence) if evidence else "暂无额外摘要", "; ".join(evidence) if evidence else "No additional summary", "; ".join(evidence) if evidence else "추가 요약 없음"), _l("该摘要解释结果来源，不扩展成预测。", "This summary explains result sources and does not expand into prediction.", "이 요약은 결과 출처를 설명하며 예측으로 확장되지 않습니다.")),
    ]


def _overview_answer_items(chart: Dict[str, Any], facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    pillars = dict(chart.get("pillars") or {})
    day = (pillars.get("day") or {}).get("display") or "-"
    month = (pillars.get("month") or {}).get("display") or "-"
    return [
        _item(_l("日主结构基点", "Day-master anchor", "일간 기준점"), _l(str(day), str(day), str(day)), _l("日主是结构定位点，不是命运结论。", "The day master is a structural anchor, not a destiny conclusion.", "일간은 구조 기준점이지 운명 결론이 아닙니다.")),
        _item(_l("月令结构", "Month structure", "월지 구조"), _l(str(month), str(month), str(month)), _l("用于观察季节/月令背景。", "Used to observe seasonal/month-command background.", "계절/월령 배경을 보기 위해 사용됩니다.")),
        _item(_l("墓库提示", "Vault hint", "묘고 힌트"), _l("、".join(facts.get("vault_branches") or []) or "未见", ", ".join(facts.get("vault_branches") or []) or "None detected", ", ".join(facts.get("vault_branches") or []) or "감지 없음"), _l("仅作为结构标签。", "Structure label only.", "구조 라벨로만 사용됩니다.")),
    ]


def _signal_observed_values(signal: Dict[str, Any]) -> List[str]:
    values = []
    for item in signal.get("observed") or []:
        text = str(item or "").strip()
        if text:
            values.append(text)
    return _dedupe_keep_order(values)


def _branch_locations(chart: Dict[str, Any], time_context: Dict[str, Any], branch: str) -> List[str]:
    labels = {
        "year": "年柱",
        "month": "月柱",
        "day": "日柱",
        "hour": "时柱",
    }
    locations: List[str] = []
    pillars = dict(chart.get("pillars") or {})
    for key in ["year", "month", "day", "hour"]:
        pillar = pillars.get(key) if isinstance(pillars.get(key), dict) else {}
        if str(pillar.get("branch") or "") == branch:
            locations.append(f"{labels[key]} {pillar.get('display') or branch}")
    luck = time_context.get("luck_cycle") if isinstance(time_context.get("luck_cycle"), dict) else {}
    luck_pillar = luck.get("pillar") if isinstance(luck.get("pillar"), dict) else {}
    if str(luck_pillar.get("branch") or "") == branch:
        locations.append(f"当前大运 {luck_pillar.get('display') or branch}")
    flow = time_context.get("flow_year") if isinstance(time_context.get("flow_year"), dict) else {}
    flow_pillar = flow.get("pillar") if isinstance(flow.get("pillar"), dict) else {}
    if str(flow_pillar.get("branch") or "") == branch:
        locations.append(f"流年 {flow.get('year') or ''} {flow_pillar.get('display') or branch}".strip())
    return locations


def _hidden_stems_label(branch: str) -> str:
    stems = [stem for stem, _ in BRANCH_HIDDEN_STEMS.get(branch, [])]
    return " / ".join(stems) if stems else "-"


def _recommendation_items(guided_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    signals = [row for row in guided_context.get("signals") or [] if isinstance(row, dict)]
    items: List[Dict[str, Any]] = []
    seen = set()
    for signal in signals:
        observed = [str(item) for item in signal.get("observed") or [] if str(item)]
        category = _signal_user_label(str(signal.get("category") or signal.get("domain") or ""))
        reason = _signal_reason_user_label(str(signal.get("reason") or ""))
        key = (_local_text(category, "zh"), tuple(observed), _local_text(reason, "zh"))
        if key in seen:
            continue
        seen.add(key)
        if len(items) >= 3:
            break
        value = " / ".join(observed) if observed else _local_text(reason, "zh")
        items.append(_item(category, _l(value, value, value), _l("这只解释为什么推荐问题，不改变结果。", "This only explains why the question is recommended; it does not change the result.", "이는 질문 추천 이유만 설명하며 결과를 바꾸지 않습니다.")))
    if not items:
        items.append(_item(_l("推荐背景", "Recommendation background", "추천 배경"), _l("来自当前命盘结构预览", "From the current chart-structure preview", "현재 명식 구조 미리보기에서 옴"), _l("用于引导提问。", "Used to guide questions.", "질문 안내에 사용됩니다.")))
    return items


def _boundary_items(kind: str) -> List[Dict[str, Any]]:
    common = _item(
        _l("当前边界", "Current boundary", "현재 경계"),
        _l("结构解释，不是预测", "Structural explanation, not prediction", "구조 설명이며 예측 아님"),
        _l("不输出好坏、发财破财、今年运势等判断。", "No good/bad, wealth gain/loss, or this-year fortune judgement is produced.", "길흉, 재물 득실, 올해 운세 판단을 출력하지 않습니다."),
    )
    result = _item(
        _l("结果关系", "Relation to Result", "Result와의 관계"),
        _l("不改变 income_stability", "Does not change income_stability", "income_stability를 바꾸지 않음"),
        _l("当前答案层只解释问题，结果仍由原确定性规则生成。", "The answer layer only explains the question; the result remains generated by the original deterministic rules.", "현재 답변층은 질문만 설명하며 결과는 기존 결정론적 규칙에서 생성됩니다."),
    )
    if kind == "time":
        return [result, common]
    return [common, result]


def _income_signal_map(income_bundle: Dict[str, Any]) -> Dict[str, str]:
    return {str(row.get("key") or ""): str(row.get("value") or "") for row in income_bundle.get("signals") or [] if isinstance(row, dict)}


def _section(zh: str, en: str, ko: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"title": _l(zh, en, ko), "items": items}


def _item(label: Dict[str, str], value: Dict[str, str], note: Dict[str, str] | None = None) -> Dict[str, Any]:
    row = {"label": label, "value": value}
    if note:
        row["note"] = note
    return row


def _l(zh: str, en: str = "", ko: str = "") -> Dict[str, str]:
    return {"zh": zh, "en": en or zh, "ko": ko or zh}


def _local_text(value: Any, locale: str = "zh") -> str:
    if isinstance(value, dict):
        return str(value.get(locale) or value.get("zh") or value.get("en") or value.get("ko") or "")
    return str(value or "")


def _value_l(value: str) -> Dict[str, str]:
    labels = {
        "none": _l("无", "None", "없음"),
        "low": _l("低", "Low", "낮음"),
        "medium": _l("中", "Medium", "중간"),
        "high": _l("高", "High", "높음"),
        "clear": _l("清晰", "Clear", "명확"),
        "bound": _l("受限", "Bound", "묶임"),
        "disrupted": _l("被扰动", "Disrupted", "흔들림"),
        "conflicted": _l("冲合并见", "Mixed clash and combination", "충합 혼재"),
        "present": _l("存在", "Present", "존재"),
        "stable": _l("稳定", "Stable", "안정"),
        "unstable": _l("不稳定", "Unstable", "불안정"),
        "mixed": _l("混合", "Mixed", "혼합"),
        "unknown": _l("未知", "Unknown", "알 수 없음"),
    }
    return labels.get(str(value or "unknown"), _l(str(value or "unknown"), str(value or "unknown"), str(value or "unknown")))


def _relation_type_label(relation_type: str) -> Dict[str, str]:
    normalized = _normalize_relation_type(str(relation_type or ""))
    if normalized == "clash":
        return _l("冲", "Clash", "충")
    if normalized == "combination":
        return _l("合", "Combination", "합")
    if normalized == "harm":
        return _l("害", "Harm", "해")
    if normalized == "break":
        return _l("破/刑", "Break/penalty", "파/형")
    return _l("结构关系", "Structural relation", "구조 관계")


def _pillar_names(pillars: List[Any], locale: str = "zh") -> str:
    labels = {
        "year": _l("年柱", "year pillar", "년주"),
        "month": _l("月柱", "month pillar", "월주"),
        "day": _l("日柱", "day pillar", "일주"),
        "hour": _l("时柱", "hour pillar", "시주"),
    }
    return " / ".join(_local_text(labels.get(str(item), _l(str(item), str(item), str(item))), locale) for item in pillars)


def _signal_user_label(category: str) -> Dict[str, str]:
    labels = {
        "vault": _l("墓库结构", "Vault structure", "묘고 구조"),
        "branch_relation": _l("地支关系", "Branch relation", "지지 관계"),
        "timing_context": _l("时间结构边界", "Time boundary", "시간 구조 경계"),
        "wealth_feature": _l("收入结构候选", "Income-structure candidate", "소득 구조 후보"),
        "wealth_mechanism": _l("收入结构候选", "Income-structure candidate", "소득 구조 후보"),
        "income_stability": _l("收入稳定性证据", "Income-stability evidence", "소득 안정성 근거"),
        "ten_god": _l("关系元数据", "Relation metadata", "관계 메타데이터"),
        "hidden_stem": _l("藏干结构", "Hidden-stem structure", "지장간 구조"),
        "five_element_relation": _l("五行关系", "Five-element relation", "오행 관계"),
        "stem_relation": _l("天干关系", "Stem relation", "천간 관계"),
        "strength_model": _l("日主强弱证据", "Day-master strength evidence", "일간 강약 근거"),
    }
    return labels.get(category, _l("结构依据", "Structural basis", "구조 근거"))


def _signal_reason_user_label(reason: str) -> Dict[str, str]:
    labels = {
        "vault_present": _l("出现墓库支", "Vault branch appears", "묘고 지지가 나타남"),
        "branch_relation_present": _l("出现冲合结构", "Clash/combination relation appears", "충합 구조가 나타남"),
        "time_context_available": _l("存在时间背景", "Time context exists", "시간 배경이 있음"),
        "rule_structured_facts_matched": _l("命中可观察结构事实", "Matched observable structural facts", "관찰 가능한 구조 사실과 일치"),
        "income_stability_supported_theme": _l("当前主题支持收入稳定性阅读", "Current theme supports income-stability reading", "현재 주제는 소득 안정성 읽기를 지원"),
    }
    return labels.get(reason, _l("结构背景触发", "Structural background triggered", "구조 배경이 트리거됨"))


def _match_rule(rule: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    category = str(rule.get("category") or "")
    domain = str(rule.get("domain") or "")
    if not category and not domain:
        return {"matched": False, "reason": "no_category_or_domain", "observed": []}
    structured_facts = _extract_rule_structured_facts(rule)
    if structured_facts is not None:
        structured_match = _match_structured_facts(structured_facts, category, facts)
        if structured_match is not None:
            return structured_match

    if category == "vault":
        matched = facts["has_vault"] or facts["flow_is_vault"] or facts["luck_is_vault"]
        return {"matched": matched, "reason": "vault_present", "observed": facts["vault_branches"]}
    if category == "branch_relation":
        matched = facts["has_branch_relation"] or facts["has_time_relation"]
        observed = [item for item in ["clash" if facts["has_clash"] else "", "combination" if facts["has_combination"] else "", "harm" if facts["has_harm"] else "", "break" if facts["has_break"] else ""] if item]
        return {"matched": matched, "reason": "branch_relation_present", "observed": observed}
    if category == "ten_god":
        return {"matched": True, "reason": "ten_god_metadata_available", "observed": []}
    if category == "timing_context":
        return {"matched": True, "reason": "time_context_available", "observed": [facts.get("flow_branch"), facts.get("luck_branch")]}
    if category in {"core_symbol", "stem_branch_attribute", "hidden_stem", "five_element_relation", "stem_relation", "strength_model"}:
        # These may have richer structured-matching above; fallback remains permissive for continuity.
        return {"matched": bool(facts["branches"] or facts["stems"]), "reason": "core_structure_available", "observed": []}
    if category == "pattern_structure":
        return {"matched": True, "reason": "pattern_index_available_as_boundary", "observed": []}
    if category in {"timing_context", "pattern_structure"}:
        return {"matched": True, "reason": "boundary_structural_context", "observed": []}
    if domain in {"income_stability", "wealth"}:
        return {"matched": True, "reason": "income_stability_supported_theme", "observed": []}
    return {"matched": False, "reason": "no_structural_trigger", "observed": []}


def _extract_rule_structured_facts(rule: Dict[str, Any]) -> Dict[str, Any] | None:
    condition = rule.get("condition")
    if isinstance(condition, dict):
        structured_facts = condition.get("structured_facts")
        if isinstance(structured_facts, dict):
            return structured_facts
    raw_conditions = rule.get("conditions")
    if isinstance(raw_conditions, dict):
        legacy_structured_facts = raw_conditions.get("structured_facts")
        if isinstance(legacy_structured_facts, dict):
            return legacy_structured_facts
    if isinstance(rule.get("structured_facts"), dict):
        return dict(rule.get("structured_facts"))
    return None


def _match_structured_facts(structured_facts: Dict[str, Any], category: str, facts: Dict[str, Any]) -> Dict[str, Any] | None:
    branch_set = set(facts.get("branch_set") or [])
    visible_stems = set(facts.get("stem_set") or [])
    all_stems = set(facts.get("all_stems") or [])
    all_elements = set(facts.get("all_stem_elements") or [])
    relation_pairs_by_type = {str(key): set(value) for key, value in (facts.get("relation_pairs_by_type") or {}).items()}
    relevant = False
    observed: List[str] = []

    vault_branches = [str(item) for item in _string_list(structured_facts.get("vault_branches"))]
    if vault_branches:
        relevant = True
        matched_vault = sorted(set(vault_branches) & branch_set)
        if matched_vault:
            observed.extend(matched_vault)

    branches = [str(item) for item in _string_list(structured_facts.get("branches"))]
    if branches:
        relevant = True
        matched = sorted(set(branches) & branch_set)
        if matched:
            observed.extend(matched)

    stems = [str(item) for item in _string_list(structured_facts.get("stems"))]
    if stems:
        relevant = True
        matched = sorted(set(stems) & visible_stems)
        if matched:
            observed.extend(matched)

    if isinstance(structured_facts.get("attributes"), dict):
        relevant = True
        for key in structured_facts.get("attributes", {}).keys():
            stem = str(key)
            if stem in visible_stems:
                observed.append(stem)

    if isinstance(structured_facts.get("hidden_stems"), dict):
        relevant = True
        hidden_map = structured_facts.get("hidden_stems") or {}
        matched = sorted(set(str(item) for item in hidden_map.keys() if str(item) in branch_set))
        if matched:
            observed.extend(matched)

    groups = structured_facts.get("groups")
    if isinstance(groups, dict):
        relevant = True
        for group_name, group_items in groups.items():
            normalized_group = [str(item) for item in _string_list(group_items)]
            if normalized_group and all(item in branch_set for item in normalized_group[:3]):
                observed.append(f"group:{group_name}")

    pairs = structured_facts.get("pairs")
    if isinstance(pairs, list):
        relevant = True
        for raw_pair in pairs:
            pair = _parse_pair(raw_pair)
            if not pair:
                continue
            pair_key = _pair_key(pair[0], pair[1])
            if pair[0] in all_stems and pair[1] in all_stems:
                observed.append(f"stempair:{pair_key}")
            if pair[0] in branch_set and pair[1] in branch_set and _pair_present(relation_pairs_by_type, pair_key, allowed_types={"combination", "clash", "harm", "break"}):
                observed.append(f"relation:{pair_key}")

    if isinstance(structured_facts.get("six_harm"), list):
        relevant = True
        for raw_pair in structured_facts.get("six_harm", []):
            pair = _parse_pair(raw_pair)
            if pair and _pair_present(relation_pairs_by_type, _pair_key(*pair), allowed_types={"harm", "disruptive", "break"}):
                observed.append(f"harm:{_pair_key(*pair)}")

    if isinstance(structured_facts.get("six_break"), list):
        relevant = True
        for raw_pair in structured_facts.get("six_break", []):
            pair = _parse_pair(raw_pair)
            if pair and _pair_present(relation_pairs_by_type, _pair_key(*pair), allowed_types={"break", "disruptive", "harm"}):
                observed.append(f"break:{_pair_key(*pair)}")

    if isinstance(structured_facts.get("generation_cycle"), list):
        relevant = True
        for raw_pair in structured_facts.get("generation_cycle", []):
            pair = _parse_pair(raw_pair)
            if pair and pair[0] in all_elements and pair[1] in all_elements:
                observed.append(f"gen:{pair[0]}->{pair[1]}")

    if isinstance(structured_facts.get("control_cycle"), list):
        relevant = True
        for raw_pair in structured_facts.get("control_cycle", []):
            pair = _parse_pair(raw_pair)
            if pair and pair[0] in all_elements and pair[1] in all_elements:
                observed.append(f"ctrl:{pair[0]}x{pair[1]}")

    if isinstance(structured_facts.get("evidence_factors"), list):
        relevant = True
        if visible_stems:
            observed.append("evidence_model")

    if not relevant:
        return None

    if observed:
        return {"matched": True, "reason": "rule_structured_facts_matched", "observed": _dedupe_sorted(observed)}
    return {"matched": False, "reason": "rule_structured_facts_not_matched", "observed": []}


def _signal_from_rule(rule: Dict[str, Any], match: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "signal_id": "gqs." + str(rule.get("knowledge_id") or rule.get("rule_id") or "unknown"),
        "rule_id": rule.get("rule_id"),
        "knowledge_id": rule.get("knowledge_id"),
        "domain": rule.get("domain"),
        "category": rule.get("category"),
        "risk_level": rule.get("risk_level"),
        "title": rule.get("title"),
        "reason": match.get("reason"),
        "observed": match.get("observed") or [],
        "runtime_scope": "question_guidance_only",
    }


def _questions_from_signal(signal: Dict[str, Any], facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    category = str(signal.get("category") or "")
    domain = str(signal.get("domain") or "")
    questions: List[Dict[str, Any]] = []
    if category == "vault":
        observed = "、".join(facts.get("vault_branches") or []) or "墓库"
        questions.append(
            _question(
                "kbq_vault_structure",
                "structure_basis",
                "beginner",
                95,
                {
                    "zh": f"这张命盘里的{observed}墓库结构，应该如何只按结构层阅读？",
                    "en": "How should the vault structure in this chart be read structurally only?",
                    "ko": "이 명식의 묘고 구조를 구조층으로만 어떻게 읽어야 하나요?",
                },
                signal,
                ["q_structure_overview", "q_time_context_boundary", "follow_rule_basis"],
            )
        )
        if facts.get("flow_is_vault") or facts.get("luck_is_vault"):
            questions.append(
                _question(
                    "kbq_time_vault_context",
                    "time_context",
                    "intermediate",
                    88,
                    {
                        "zh": "大运或流年出现墓库时，哪些部分只是时间背景而不是预测结论？",
                        "en": "When a luck cycle or flow year shows a vault branch, what remains time context rather than prediction?",
                        "ko": "대운이나 세운에 묘고 지지가 나타날 때 무엇이 예측이 아니라 시간 배경인가요?",
                    },
                    signal,
                    ["q_time_context_boundary", "q_time_not_inference"],
                )
            )
    elif category == "branch_relation":
        questions.append(
            _question(
                "kbq_branch_relation_structure",
                "structure_basis",
                "beginner",
                84,
                {
                    "zh": "当前命盘或时间背景触发了哪些冲合关系，它们在结构层代表什么？",
                    "en": "Which clash or combination relations are triggered, and what do they mean structurally?",
                    "ko": "현재 명식이나 시간 배경에서 어떤 충합 관계가 나타나며 구조적으로 무엇을 뜻하나요?",
                },
                signal,
                ["q_time_context", "q_structure_overview", "follow_rule_basis"],
            )
        )
        if facts.get("has_time_relation"):
            questions.append(
                _question(
                    "kbq_time_vs_natal_relation",
                    "time_context",
                    "intermediate",
                    86,
                    {
                        "zh": "大运或流年和本命之间的关系，应该怎样分层阅读？",
                        "en": "How should relations between timing context and the natal chart be read by layer?",
                        "ko": "대운·세운과 원국 사이의 관계는 층위별로 어떻게 읽어야 하나요?",
                    },
                    signal,
                    ["q_time_context", "q_luck_flow_layers", "q_time_not_inference"],
                )
            )
        if facts.get("has_combination"):
            questions.append(
                _question(
                    "kbq_combination_context",
                    "structure_basis",
                    "intermediate",
                    83,
                    {
                        "zh": "当前出现的合或六合关系，在这里只能说明什么结构连接？",
                        "en": "What structural link can the current combination relation indicate here?",
                        "ko": "현재 나타난 합 관계는 여기서 어떤 구조 연결만 뜻하나요?",
                    },
                    signal,
                    ["q_branch_relation_detail", "q_structure_overview", "q_time_context_boundary"],
                )
            )
        if facts.get("has_three_harmony"):
            questions.append(
                _question(
                    "kbq_three_harmony_context",
                    "structure_basis",
                    "intermediate",
                    82,
                    {
                        "zh": "命盘里出现三合结构时，应该先看成哪类结构连接？",
                        "en": "When a three-harmony structure appears, what kind of structural link should it be read as first?",
                        "ko": "명식에 삼합 구조가 보이면 먼저 어떤 구조 연결로 읽어야 하나요?",
                    },
                    signal,
                    ["q_branch_relation_detail", "q_structure_overview", "q_time_context_boundary"],
                )
            )
        if facts.get("has_break") or facts.get("has_harm"):
            questions.append(
                _question(
                    "kbq_branch_disruption_structure",
                    "structure_basis",
                    "intermediate",
                    78,
                    {
                        "zh": "命盘中的冲害刑破属于哪类结构关系？为什么先读为结构提示？",
                        "en": "Which disruptive branch relations appear and why read them as structural signals first?",
                        "ko": "명식의 충·해·형·파는 어떤 구조 관계이며 왜 먼저 구조 신호로 읽어야 하나요?",
                    },
                    signal,
                    ["q_cautious_reading", "q_time_context_boundary", "q_read_result_not_fortune"],
                )
            )
    elif category == "ten_god":
        questions.append(
            _question(
                "kbq_ten_god_metadata",
                "structure_basis",
                "beginner",
                74,
                {
                    "zh": "十神标签在这里为什么只是关系元数据，而不是断语？",
                    "en": "Why are Ten God labels relational metadata here, not predictions?",
                    "ko": "여기서 십성 라벨은 왜 단정이 아니라 관계 메타데이터인가요?",
                },
                signal,
                ["q_income_factors", "q_read_result_not_fortune"],
            )
        )
    elif domain == "income_stability":
        questions.append(
            _question(
                "kbq_wealth_feature_boundary",
                "income_stability",
                "intermediate",
                72,
                {
                    "zh": "财星、食伤、比劫这些财富结构候选，如何只作为收入稳定性的证据来源？",
                    "en": "How do wealth, output, and peer structures serve only as evidence for income stability?",
                    "ko": "재성, 식상, 비겁 구조는 어떻게 소득 안정성의 증거로만 쓰이나요?",
                },
                signal,
                ["q_income_factors", "q_signal_combination", "follow_rule_basis"],
            )
        )
    elif category == "timing_context":
        questions.append(
            _question(
                "kbq_time_context_from_rule_db",
                "time_context",
                "beginner",
                70,
                {
                    "zh": "规则库中的时间结构为什么只用于引导提问，而不直接改变结果？",
                    "en": "Why does the time structure in the rule database guide questions without directly changing results?",
                    "ko": "규칙 DB의 시간 구조는 왜 질문 안내에만 쓰이고 결과를 직접 바꾸지 않나요?",
                },
                signal,
                ["q_time_context_boundary", "q_time_not_inference"],
            )
        )
    elif category == "pattern_structure":
        questions.append(
            _question(
                "kbq_pattern_index_boundary",
                "boundary",
                "intermediate",
                60,
                {
                    "zh": "格局索引为什么现在只作为结构目录，而不是命运判断？",
                    "en": "Why is the pattern index currently a structural catalog rather than fate judgement?",
                    "ko": "격국 색인은 왜 현재 운명 판단이 아니라 구조 목록인가요?",
                },
                signal,
                ["q_result_card_boundary", "q_read_result_not_fortune"],
            )
        )
    elif category == "core_symbol":
        questions.append(
            _question(
                "kbq_core_symbol_structure",
                "structure_basis",
                "beginner",
                58,
                {
                    "zh": "十天干、十二地支作为结构事实有哪些边界？",
                    "en": "What are the structural limits of heavenly stems and earthly branches?",
                    "ko": "천간·지지는 구조 사실로서 어떤 한계를 가지나요?",
                },
                signal,
                ["q_structure_overview", "q_read_result_not_fortune"],
            )
        )
    elif category in {"stem_relation", "five_element_relation"}:
        questions.append(
            _question(
                "kbq_relation_schema_boundary",
                "structure_basis",
                "intermediate",
                62,
                {
                    "zh": "五行生克、天干五合如何只作为关系结构提示？",
                    "en": "How should generation/control and stem-combination be used as relationship structure only?",
                    "ko": "오행 생극, 천간합은 왜 관계 구조로만 쓰이나요?",
                },
                signal,
                ["q_read_result_not_fortune", "q_time_context_boundary"],
            )
        )
    elif category in {"stem_branch_attribute", "hidden_stem", "strength_model"}:
        questions.append(
            _question(
                "kbq_core_structure_metadata",
                "structure_basis",
                "intermediate",
                56,
                {
                    "zh": "属性或藏干信息为何属于可解释性结构，而非直接结论？",
                    "en": "Why are attribute or hidden-stem signals still explanatory structure only?",
                    "ko": "속성 또는 천간·지장간 정보는 왜 직접 결론이 아니라 설명적 구조인지요?",
                },
                signal,
                ["q_structure_overview", "q_read_result_not_fortune"],
            )
        )

    return questions


def _question(key: str, theme: str, depth: str, score: int, label: Dict[str, str], signal: Dict[str, Any], related: List[str]) -> Dict[str, Any]:
    contract = _question_contract_from_signal(key, signal)
    return {
        "key": key,
        "theme": theme,
        "required": ["chart"],
        "required_facts": contract["required_facts"],
        "answer_scope": contract["answer_scope"],
        "intent": contract["intent"],
        "depth": depth,
        "phase": "any",
        "related_questions": related,
        "forbidden_prediction": True,
        "score": score,
        "label": label,
        "source_signal_id": signal.get("signal_id"),
        "source_rule_id": signal.get("rule_id"),
        "source_knowledge_id": signal.get("knowledge_id"),
        "risk_level": signal.get("risk_level"),
        "source": "rule_db_dynamic_question",
        "registry_version": QUESTION_REGISTRY_VERSION,
        "guardrails": ["DYNAMIC_GUIDED_QUESTION", "NO_FORTUNE", "NO_RESULT_MUTATION"],
    }


def _question_contract_from_signal(key: str, signal: Dict[str, Any]) -> Dict[str, Any]:
    registered = _registry_question_for_key(key)
    if registered:
        return {
            "intent": registered.get("intent") or "structure_overview",
            "required_facts": list(registered.get("required_facts") or []),
            "answer_scope": registered.get("answer_scope") or "",
        }
    kind = _guided_answer_kind_from_signal(signal) or "structure_overview"
    fallback = {
        "branch_relation": (["relations", "chart_anchor", "time_context"], "separate_branch_relations_by_layer"),
        "vault": (["vaults", "hidden_stems", "chart_anchor"], "explain_vault_structure_only"),
        "time_boundary": (["time_context", "relations"], "explain_time_context_only"),
        "income_structure": (["income_signals", "chart_anchor", "relations"], "explain_income_structure_signal_only"),
        "metadata_boundary": (["chart_anchor", "hidden_stems"], "explain_metadata_boundary"),
        "result_boundary": (["income_signals", "guardrails"], "explain_result_boundary"),
        "rule_basis": (["source_signal", "observed_facts"], "explain_rule_basis"),
        "structure_overview": (["chart_anchor", "relations", "vaults"], "summarize_visible_structure_only"),
    }
    required_facts, answer_scope = fallback.get(kind, fallback["structure_overview"])
    return {"intent": kind, "required_facts": required_facts, "answer_scope": answer_scope}


def _dedupe_questions(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out: List[Dict[str, Any]] = []
    for row in rows:
        key = row.get("key")
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def _has_three_harmony(branches: List[str]) -> bool:
    present = set(branches)
    return any(set(group) <= present for group in THREE_HARMONIES)


def _collect_relation_pairs_from_items(items: Iterable[Dict[str, Any]]) -> tuple[Dict[str, set[str]], Set[str], List[str]]:
    pairs_by_type: Dict[str, set[str]] = {}
    relation_types: Set[str] = set()
    relation_pairs: Set[str] = set()
    for row in items:
        relation_type = str(row.get("type") or row.get("relation_type") or "")
        keys = _relation_keys_from_row(row)
        if not keys:
            continue
        normalized_type = _normalize_relation_type(relation_type)
        relation_types.add(normalized_type)
        for pair_key in keys:
            pairs_by_type.setdefault(normalized_type, set()).add(pair_key)
            relation_pairs.add(pair_key)
    return pairs_by_type, relation_types, sorted(relation_pairs)


def _relation_keys_from_row(row: Dict[str, Any]) -> List[str]:
    left = str(row.get("left") or "").strip()
    right = str(row.get("right") or "").strip()
    pair = _parse_pair([left, right])
    if pair:
        return [_pair_key(pair[0], pair[1])]
    branches = str(row.get("branches") or "").strip()
    if not branches:
        return []
    known = set("子丑寅卯辰巳午未申酉戌亥")
    parts = [char for char in branches if char in known]
    if len(parts) == 2:
        return [_pair_key(parts[0], parts[1])]
    if len(parts) >= 3:
        return ["-".join(sorted(parts))]
    return []


def _collect_relation_pairs_from_payload(payload: Dict[str, Any]) -> Dict[str, set[str]]:
    if not isinstance(payload, dict):
        return {}
    out: Dict[str, set[str]] = {}
    for key, value in payload.items():
        normalized_type = _normalize_relation_type(str(key))
        for raw_pair in _as_list(value):
            pair = _parse_pair(raw_pair)
            if not pair:
                continue
            out.setdefault(normalized_type, set()).add(_pair_key(pair[0], pair[1]))
    return out


def _normalize_relation_type(raw: str) -> str:
    raw_type = str(raw or "").strip()
    if raw_type in {"six_clash", "clash", "clashes"}:
        return "clash"
    if raw_type in {"six_combination", "combination", "combinations", "three_harmony", "three_meeting"}:
        return "combination"
    if raw_type in {"six_harm", "harm"}:
        return "harm"
    if raw_type in {"break", "penalty", "punishment"}:
        return "break"
    return raw_type or "unknown"


def _parse_pair(raw: Any) -> tuple[str, str] | None:
    if raw is None:
        return None
    if isinstance(raw, (list, tuple)):
        if len(raw) != 2:
            return None
        left = str(raw[0]).strip()
        right = str(raw[1]).strip()
        if left and right:
            return _pair_sort(left, right)
        return None
    if isinstance(raw, str):
        text = str(raw).strip()
        if not text:
            return None
        if len(text) == 2:
            return _pair_sort(text[0], text[1])
        for sep in ["-", "_", ",", "、", " "]:
            if sep in text:
                parts = [part.strip() for part in text.split(sep) if part.strip()]
                if len(parts) == 2:
                    return _pair_sort(parts[0], parts[1])
        return None
    if isinstance(raw, dict):
        left = str(raw.get("left") or raw.get("a") or "").strip()
        right = str(raw.get("right") or raw.get("b") or "").strip()
        if left and right:
            return _pair_sort(left, right)
    return None


def _pair_sort(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


def _pair_key(left: str, right: str) -> str:
    a, b = _pair_sort(left, right)
    return f"{a}-{b}"


def _pair_present(relation_pairs_by_type: Dict[str, Set[str]], pair_key: str, allowed_types: Set[str] | None = None) -> bool:
    if allowed_types is None:
        return any(pair_key in pairs for pairs in relation_pairs_by_type.values())
    return any(pair_key in relation_pairs_by_type.get(relation_type, set()) for relation_type in allowed_types)


def _as_list(raw: Any) -> List[Any]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, tuple):
        return list(raw)
    return []


def _string_list(raw: Any) -> List[str]:
    return [str(item) for item in _as_list(raw) if str(item)]


def _dedupe_sorted(items: List[str]) -> List[str]:
    return sorted(set(items))


def _dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _hidden_stems_for_branches(branches: List[str]) -> Set[str]:
    stems: Set[str] = set()
    for branch in branches:
        stems.update(stem for stem, _ in BRANCH_HIDDEN_STEMS.get(branch, []))
    return stems
