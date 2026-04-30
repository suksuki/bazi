from __future__ import annotations

from typing import Any, Dict, Iterable, List, Set, Tuple

from v19.agent.structure import THREE_HARMONIES
from v19.bazi_rule_db import build_structural_rule_signals
from v19.core.chart import BRANCH_HIDDEN_STEMS, VAULT_BRANCHES, element_of_stem, ten_god
from v19.guided_evidence_pack import build_guided_answer_evidence_pack, evidence_pack_summary
from v19.rule_graph_orchestrator import (
    audit_selected_paths_for_answer,
    orchestrate_rule_graph_paths,
    rule_graph_paths_to_signals,
)


QUESTION_REGISTRY_VERSION = "v19.question_registry.p9.structural_rule_signals.v1"
THREE_MEETINGS = [("寅", "卯", "辰"), ("巳", "午", "未"), ("申", "酉", "戌"), ("亥", "子", "丑")]
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
    "q_strength_assessment": {
        "theme": "strength_structure",
        "depth": "beginner",
        "phase": "any",
        "intent": "strength_assessment",
        "required": ["chart"],
        "required_facts": ["chart_anchor", "hidden_stems", "stem_elements"],
        "answer_scope": "explain_day_master_strength_as_evidence_bundle_not_verdict",
        "score": 88,
        "related_questions": ["q_day_master_month_anchor", "q_month_command_anchor", "q_useful_god_candidates"],
        "label": {
            "zh": "这个八字的日主强弱，应该先看哪些证据？",
            "en": "Which evidence should be checked first for day-master strength?",
            "ko": "이 사주의 일간 강약은 어떤 근거를 먼저 봐야 하나요?",
        },
    },
    "q_useful_god_candidates": {
        "theme": "useful_god_boundary",
        "depth": "intermediate",
        "phase": "after_structure",
        "intent": "useful_god_boundary",
        "required": ["chart"],
        "required_facts": ["chart_anchor", "hidden_stems", "stem_elements", "relations"],
        "answer_scope": "explain_useful_god_as_candidate_path_requiring_strength_and_structure_gate",
        "score": 82,
        "related_questions": ["q_strength_assessment", "q_favorable_elements_boundary", "q_unfavorable_god_boundary"],
        "label": {
            "zh": "这张命盘的用神，当前只能先形成哪些候选路径？",
            "en": "What useful-god candidate paths can be formed at this stage?",
            "ko": "이 명식의 용신은 현재 어떤 후보 경로로만 볼 수 있나요?",
        },
    },
    "q_unfavorable_god_boundary": {
        "theme": "useful_god_boundary",
        "depth": "intermediate",
        "phase": "after_structure",
        "intent": "useful_god_boundary",
        "required": ["chart"],
        "required_facts": ["chart_anchor", "hidden_stems", "stem_elements", "relations"],
        "answer_scope": "explain_unfavorable_god_as_boundary_not_remedy_advice",
        "score": 76,
        "related_questions": ["q_useful_god_candidates", "q_strength_assessment", "q_read_result_not_fortune"],
        "label": {
            "zh": "忌神问题现在应该如何只按结构边界回答？",
            "en": "How should unfavorable-god questions be answered only as structural boundaries?",
            "ko": "기신 질문은 현재 구조 경계로만 어떻게 답해야 하나요?",
        },
    },
    "q_favorable_elements_boundary": {
        "theme": "useful_god_boundary",
        "depth": "intermediate",
        "phase": "after_structure",
        "intent": "useful_god_boundary",
        "required": ["chart"],
        "required_facts": ["chart_anchor", "stem_elements", "hidden_stems"],
        "answer_scope": "explain_favorable_elements_as_candidate_not_remedy",
        "score": 74,
        "related_questions": ["q_useful_god_candidates", "q_unfavorable_god_boundary", "q_element_flow_metadata"],
        "label": {
            "zh": "喜什么五行这类问题，当前能回答到什么边界？",
            "en": "For favorable-element questions, what boundary can be answered now?",
            "ko": "희신 오행 질문은 현재 어느 경계까지 답할 수 있나요?",
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
        "score": 83,
        "related_questions": ["q_day_master_month_anchor", "q_structure_overview", "q_income_factors"],
        "label": {
            "zh": "藏干在这张命盘里只是补充信息，还是会影响结构理解？",
            "en": "Are hidden stems only supporting information here, or do they affect structural reading?",
            "ko": "지장간은 여기서 보조 정보일 뿐인가요, 아니면 구조 이해에 영향을 주나요?",
        },
    },
    "q_month_command_anchor": {
        "theme": "structure_basis",
        "depth": "beginner",
        "phase": "any",
        "intent": "metadata_boundary",
        "required": ["chart"],
        "required_facts": ["chart_anchor", "hidden_stems", "stem_elements"],
        "answer_scope": "explain_month_branch_as_structure_anchor",
        "score": 84,
        "related_questions": ["q_day_master_month_anchor", "q_structure_overview", "q_hidden_stem_role"],
        "label": {
            "zh": "月令在这张命盘里先提供了什么结构背景？",
            "en": "What structural background does the month branch provide here?",
            "ko": "월지는 이 명식에서 어떤 구조 배경을 먼저 제공하나요?",
        },
    },
    "q_ten_god_metadata": {
        "theme": "structure_basis",
        "depth": "intermediate",
        "phase": "any",
        "intent": "metadata_boundary",
        "required": ["chart"],
        "required_facts": ["chart_anchor", "hidden_stems", "stem_elements"],
        "answer_scope": "explain_ten_god_as_relationship_metadata",
        "score": 84,
        "related_questions": ["q_hidden_stem_role", "q_income_factors", "q_read_result_not_fortune"],
        "label": {
            "zh": "十神标签在这里为什么只是关系元数据，而不是断语？",
            "en": "Why are Ten God labels relationship metadata here rather than verdicts?",
            "ko": "여기서 십성 라벨은 왜 단정이 아니라 관계 메타데이터인가요?",
        },
    },
    "q_vault_structure": {
        "theme": "structure_basis",
        "depth": "intermediate",
        "phase": "any",
        "intent": "vault",
        "required": ["chart"],
        "required_facts": ["vaults", "hidden_stems", "time_context"],
        "answer_scope": "explain_vault_branch_as_structural_storage_not_verdict",
        "score": 79,
        "related_questions": ["q_hidden_stem_role", "q_structure_overview", "q_time_context_boundary"],
        "label": {
            "zh": "这张命盘里的墓库结构，应该如何只按结构层阅读？",
            "en": "How should the vault structure in this chart be read only at the structural layer?",
            "ko": "이 명식의 묘고 구조는 구조 층에서만 어떻게 읽어야 하나요?",
        },
    },
    "q_pattern_structure": {
        "theme": "pattern_structure",
        "depth": "intermediate",
        "phase": "after_structure",
        "intent": "pattern_structure",
        "required": ["chart"],
        "required_facts": ["chart_anchor", "hidden_stems", "relations"],
        "answer_scope": "explain_pattern_as_structure_index_not_fate_verdict",
        "score": 80,
        "related_questions": ["q_strength_assessment", "q_ten_god_focus", "q_read_result_not_fortune"],
        "label": {
            "zh": "这个八字的格局，应该先按哪些结构入口判断？",
            "en": "Which structural entries should be checked first for chart pattern?",
            "ko": "이 사주의 격국은 어떤 구조 입구부터 봐야 하나요?",
        },
    },
    "q_ten_god_focus": {
        "theme": "structure_basis",
        "depth": "intermediate",
        "phase": "after_structure",
        "intent": "metadata_boundary",
        "required": ["chart"],
        "required_facts": ["chart_anchor", "hidden_stems", "stem_elements"],
        "answer_scope": "explain_primary_ten_god_focus_as_visible_structure_not_verdict",
        "score": 78,
        "related_questions": ["q_ten_god_metadata", "q_pattern_structure", "q_income_factors"],
        "label": {
            "zh": "财、官、印、食伤里，当前哪些十神关系更值得先看？",
            "en": "Among wealth, officer, resource, and output, which Ten God relations deserve first attention?",
            "ko": "재성·관성·인성·식상 중 어떤 십성 관계를 먼저 봐야 하나요?",
        },
    },
    "q_career_structure": {
        "theme": "career_structure",
        "depth": "beginner",
        "phase": "any",
        "intent": "career_structure",
        "required": ["chart"],
        "required_facts": ["chart_anchor", "relations", "source_signal"],
        "answer_scope": "explain_career_as_structure_boundary_not_outcome",
        "score": 72,
        "related_questions": ["q_ten_god_metadata", "q_structure_overview", "q_time_context_boundary"],
        "label": {
            "zh": "这张命盘的事业结构，应该先看哪些结构路径？",
            "en": "Which structural paths should be checked first for career structure in this chart?",
            "ko": "이 명식의 직업 구조는 어떤 구조 경로를 먼저 봐야 하나요?",
        },
    },
    "q_relationship_structure": {
        "theme": "relationship_structure",
        "depth": "beginner",
        "phase": "any",
        "intent": "relationship_structure",
        "required": ["chart"],
        "required_facts": ["chart_anchor", "relations", "source_signal", "time_context"],
        "answer_scope": "explain_relationship_as_structure_boundary_not_outcome",
        "score": 70,
        "related_questions": ["q_branch_relation_detail", "q_ten_god_metadata", "q_time_context_boundary"],
        "label": {
            "zh": "这张命盘的关系结构，应该如何只按结构层阅读？",
            "en": "How should relationship structure in this chart be read only at the structural layer?",
            "ko": "이 명식의 관계 구조는 구조 층에서만 어떻게 읽어야 하나요?",
        },
    },
    "q_health_structure": {
        "theme": "health_structure",
        "depth": "beginner",
        "phase": "any",
        "intent": "health_structure",
        "required": ["chart"],
        "required_facts": ["chart_anchor", "relations", "source_signal", "time_context"],
        "answer_scope": "explain_health_as_structure_boundary_not_body_verdict",
        "score": 68,
        "related_questions": ["q_day_master_month_anchor", "q_branch_relation_detail", "q_time_context_boundary"],
        "label": {
            "zh": "这张命盘的健康结构，只能读到哪些结构边界？",
            "en": "Which structural boundaries can be read for health structure in this chart?",
            "ko": "이 명식의 건강 구조에서는 어떤 구조 경계만 읽을 수 있나요?",
        },
    },
    "q_element_flow_metadata": {
        "theme": "structure_basis",
        "depth": "intermediate",
        "phase": "any",
        "intent": "metadata_boundary",
        "required": ["chart"],
        "required_facts": ["chart_anchor", "stem_elements", "hidden_stems"],
        "answer_scope": "explain_element_generation_control_as_structure_metadata",
        "score": 69,
        "related_questions": ["q_day_master_month_anchor", "q_ten_god_metadata", "q_income_factors"],
        "label": {
            "zh": "五行生克在这里应该怎样只按结构关系阅读？",
            "en": "How should element generation/control be read only as structural relation here?",
            "ko": "오행 생극은 여기서 구조 관계로만 어떻게 읽어야 하나요?",
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
        "score": 89,
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
    "q_income_path_structure": {
        "theme": "income_stability",
        "depth": "intermediate",
        "phase": "after_result",
        "intent": "income_structure",
        "required": ["result"],
        "required_facts": ["income_signals", "chart_anchor", "relations"],
        "answer_scope": "explain_income_path_as_structure_not_prediction",
        "score": 66,
        "related_questions": ["q_income_factors", "q_wealth_accessibility", "q_signal_combination"],
        "label": {
            "zh": "如果只按结构看，收入路径是被哪些信号组织起来的？",
            "en": "Structurally, which signals organize the income path?",
            "ko": "구조만 보면 소득 경로는 어떤 신호들로 조직되나요?",
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
        "score": 83,
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
            "zh": "为什么结果卡不是传统断语？",
            "en": "Why is the result card not traditional fortune text?",
            "ko": "왜 결과 카드는 전통식 단정문이 아닌가요?",
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
    inference_context = dict(agent_data.get("inference_context") or {})
    facts = _chart_facts(chart, time_context)
    signals: List[Dict[str, Any]] = []
    questions: List[Dict[str, Any]] = _baseline_questions(facts)
    for signal in _structural_signals_from_facts(facts):
        signals.append(signal)
        questions.extend(_questions_for_structural_signal(signal, facts))
    rule_signal_report = build_structural_rule_signals(chart, time_context, inference_context)
    for signal in rule_signal_report.get("signals") or []:
        if not isinstance(signal, dict):
            continue
        signals.append(signal)
        questions.extend(_questions_from_signal(signal, facts))
    rule_graph_context = orchestrate_rule_graph_paths(agent_data, limit=8)
    for signal in rule_graph_paths_to_signals(rule_graph_context, limit=6):
        signals.append(signal)
        for question in _questions_from_signal(signal, facts):
            graph_question = dict(question)
            graph_question["source"] = "rule_graph_dynamic_question"
            graph_question["score"] = min(int(graph_question.get("score") or 0), 54)
            graph_question["runtime_scope"] = "rule_graph_question_hint_only_no_result_mutation"
            graph_question["guardrails"] = list(graph_question.get("guardrails") or []) + ["RULE_GRAPH_HINT_ONLY"]
            questions.append(graph_question)
    runtime_rule_graph_context = dict(agent_data.get("rule_graph_runtime_context") or {})
    if runtime_rule_graph_context:
        runtime_signal_report = {"selected_paths": runtime_rule_graph_context.get("selected_paths") or []}
        for signal in rule_graph_paths_to_signals(runtime_signal_report, limit=14):
            signals.append(signal)
            for question in _questions_from_signal(signal, facts):
                graph_question = dict(question)
                graph_question["source"] = "rule_graph_dynamic_question"
                graph_question["score"] = min(int(graph_question.get("score") or 0), 58)
                graph_question["runtime_scope"] = "runtime_rule_graph_question_hint_only_no_result_mutation"
                graph_question["guardrails"] = list(graph_question.get("guardrails") or []) + ["RUNTIME_RULE_GRAPH_HINT_ONLY"]
                questions.append(graph_question)
    personalization_context = _question_personalization_context(agent_data, facts, rule_graph_context)
    questions = _personalize_questions(questions, personalization_context)
    questions = _dedupe_questions(questions)
    ranked_questions = _rank_questions_for_chart(questions, personalization_context)
    return {
        "available": True,
        "runtime_scope": "guided_questions_only_no_inference_mutation",
        "rule_signal_count": len(signals),
        "structure_portrait": _compact_structure_portrait(agent_data.get("structure_portrait") or {}),
        "rule_signal_adapter": {
            "version": rule_signal_report.get("version") or "",
            "count": rule_signal_report.get("count") or 0,
            "runtime_scope": rule_signal_report.get("runtime_scope") or "",
        },
        "question_count": len(questions),
        "signals": _prioritize_context_signals(signals)[:30],
        "rule_graph_context": rule_graph_context,
        "question_personalization_context": personalization_context,
        "questions": ranked_questions[:10],
        "question_registry": {
            "version": QUESTION_REGISTRY_VERSION,
            "single_source": True,
            "items": _registry_questions(facts),
        },
        "guardrails": [
            "RULE_DB_GUIDES_QUESTIONS_ONLY",
            "RULE_GRAPH_PATH_SELECTION",
            "RULE_GRAPH_PERSONALIZED_QUESTION_RANKING",
            "NO_RESULT_MUTATION",
            "NO_FORTUNE",
            "NO_TIME_AWARE_INFERENCE",
        ],
    }


def _prioritize_context_signals(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    legacy = [row for row in signals if str(row.get("source") or "") != "rule_graph_orchestrator"]
    graph = [row for row in signals if str(row.get("source") or "") == "rule_graph_orchestrator"]
    graph = sorted(graph, key=lambda row: int(row.get("score") or 0), reverse=True)
    return legacy[:24] + graph[:6] + legacy[24:]


def _compact_structure_portrait(portrait: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(portrait, dict) or not portrait:
        return {}
    labels = [dict(row) for row in portrait.get("labels") or [] if isinstance(row, dict)]
    judgements = [dict(row) for row in portrait.get("candidate_judgements") or [] if isinstance(row, dict)]
    return {
        "version": portrait.get("version") or "",
        "status": portrait.get("status") or "",
        "runtime_scope": portrait.get("runtime_scope") or "",
        "vectors": dict(portrait.get("vectors") or {}),
        "dominant_label_ids": [str(row.get("label_id") or "") for row in labels[:5]],
        "candidate_judgement_ids": [str(row.get("judgement_id") or "") for row in judgements[:5]],
        "question_bias": dict(portrait.get("question_bias") or {}),
    }


def _merge_portrait_bucket_order(route_bucket_order: List[str], portrait_bias: Dict[str, Any]) -> List[str]:
    ordered = [str(item) for item in route_bucket_order if str(item)]
    bucket_boosts = dict(portrait_bias.get("bucket_boosts") or {})
    boosted = [key for key, _value in sorted(bucket_boosts.items(), key=lambda row: float(row[1] or 0), reverse=True) if str(key)]
    # Portrait scores are a secondary bias. They may add missing buckets, but
    # must not override the Rule Graph bucket order for explicit chart hits.
    for bucket in boosted[:3]:
        if bucket not in ordered:
            ordered.append(bucket)
    out: List[str] = []
    for bucket in ordered:
        if bucket not in out:
            out.append(bucket)
    return out[:8]


def _question_personalization_context(agent_data: Dict[str, Any], facts: Dict[str, Any], rule_graph_context: Dict[str, Any]) -> Dict[str, Any]:
    runtime_context = dict(agent_data.get("rule_graph_runtime_context") or {})
    structure_portrait = dict(agent_data.get("structure_portrait") or {})
    selected_paths = [dict(row) for row in runtime_context.get("selected_paths") or [] if isinstance(row, dict)]
    if not selected_paths:
        selected_paths = [dict(row) for row in rule_graph_context.get("selected_paths") or [] if isinstance(row, dict)]
    lane_counts = dict((runtime_context.get("knowledge_route") or {}).get("by_topic_lane") or {})
    if not lane_counts:
        lane_counts = _count_values(str(row.get("topic_lane") or "") for row in selected_paths)
    domain_counts = dict((runtime_context.get("knowledge_route") or {}).get("by_domain") or {})
    if not domain_counts:
        domain_counts = _count_values(str(row.get("domain") or "") for row in selected_paths)
    route_bucket_order = _route_bucket_order(lane_counts, facts)
    portrait_bias = dict(structure_portrait.get("question_bias") or {})
    route_bucket_order = _merge_portrait_bucket_order(route_bucket_order, portrait_bias)
    selected_knowledge_ids = [str(row.get("knowledge_id") or "") for row in selected_paths if row.get("knowledge_id")]
    return {
        "version": "v19.p48.question_personalization.v1",
        "status": "ready" if selected_paths else "fallback_without_rule_graph_paths",
        "runtime_scope": "question_ranking_only_no_inference_mutation",
        "source": "rule_graph_runtime_context" if runtime_context else "rule_graph_context",
        "route_bucket_order": route_bucket_order,
        "route_lane_counts": lane_counts,
        "route_domain_counts": domain_counts,
        "selected_knowledge_ids": selected_knowledge_ids[:12],
        "selected_route_count": int(runtime_context.get("route_count") or 0),
        "structure_portrait_status": structure_portrait.get("status") or "",
        "portrait_vector_summary": dict(structure_portrait.get("vectors") or {}),
        "portrait_question_bias": portrait_bias,
        "guardrails": [
            "PERSONALIZE_QUESTION_ORDER_ONLY",
            "STRUCTURE_PORTRAIT_RANKING_BIAS_ONLY",
            "KEEP_BASELINE_ENTRY",
            "NO_RESULT_MUTATION",
            "NO_FORTUNE",
        ],
    }


def _personalize_questions(rows: List[Dict[str, Any]], personalization_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    selected_ids = set(str(item) for item in personalization_context.get("selected_knowledge_ids") or [] if str(item))
    bucket_order = [str(item) for item in personalization_context.get("route_bucket_order") or [] if str(item)]
    bucket_rank = {bucket: index for index, bucket in enumerate(bucket_order)}
    lane_counts = dict(personalization_context.get("route_lane_counts") or {})
    domain_counts = dict(personalization_context.get("route_domain_counts") or {})
    portrait_bias = dict(personalization_context.get("portrait_question_bias") or {})
    portrait_bucket_boosts = dict(portrait_bias.get("bucket_boosts") or {})
    portrait_question_boosts = dict(portrait_bias.get("question_boosts") or {})
    for row in rows:
        item = dict(row)
        bucket = _question_bucket(item)
        route_boost = 0
        route_reasons: List[str] = []
        if bucket in bucket_rank:
            route_boost += max(4, 18 - bucket_rank[bucket] * 2)
            route_reasons.append(f"bucket:{bucket}")
        knowledge_id = str(item.get("source_knowledge_id") or "")
        if knowledge_id and knowledge_id in selected_ids:
            route_boost += 10
            route_reasons.append(f"knowledge:{knowledge_id}")
        source_category = str(item.get("source_signal_category") or "")
        if _category_matches_route(source_category, lane_counts, domain_counts):
            route_boost += 6
            route_reasons.append(f"category:{source_category}")
        portrait_boost = float(portrait_bucket_boosts.get(bucket) or 0) + float(portrait_question_boosts.get(str(item.get("key") or "")) or 0)
        if portrait_boost:
            route_boost += min(18, int(round(portrait_boost)))
            route_reasons.append("structure_portrait")
        route_boost = min(route_boost, 34)
        base_score = int(item.get("score") or 0)
        item["personalized_score"] = base_score + route_boost
        item["personalization"] = {
            "applied": route_boost > 0,
            "route_boost": route_boost,
            "bucket": bucket,
            "reasons": route_reasons[:4],
            "source": personalization_context.get("source") or "",
            "runtime_scope": "question_ranking_only_no_result_mutation",
        }
        out.append(item)
    return out


def _structural_signals_from_facts(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    signals: List[Dict[str, Any]] = []
    relations = sorted(str(item) for item in facts.get("relation_types") or [] if str(item))
    relation_pairs = [str(item) for item in facts.get("relation_pairs") or [] if str(item)]
    if relations or relation_pairs:
        branch_question_keys = _branch_relation_question_keys(facts)
        signals.append(
            _structural_signal(
                "struct.branch_relations",
                "branch_relation",
                relation_pairs or relations,
                ["relations"],
                "命盘或时间背景存在可见地支关系，适合先解释发生在哪一层。",
                branch_question_keys,
                86,
            )
        )
    vaults = [str(item) for item in facts.get("vault_branches") or [] if str(item)]
    if facts.get("luck_is_vault"):
        vaults.append(str(facts.get("luck_branch") or ""))
    if facts.get("flow_is_vault"):
        vaults.append(str(facts.get("flow_branch") or ""))
    vaults = sorted({item for item in vaults if item})
    if vaults:
        signals.append(
            _structural_signal(
                "struct.vaults",
                "vault",
                vaults,
                ["vaults", "hidden_stems"],
                "命盘或时间背景出现墓库支，适合解释位置、藏干和阅读边界。",
                ["q_vault_structure", "q_hidden_stem_role", "q_structure_overview"],
                80,
            )
        )
    if facts.get("day_stem") or facts.get("month_branch"):
        observed = [str(item) for item in [facts.get("day_stem"), facts.get("month_branch")] if str(item)]
        signals.append(
            _structural_signal(
                "struct.anchor",
                "structure_anchor",
                observed,
                ["chart_anchor", "stem_elements"],
                "日主和月令构成结构阅读的入口，适合先回答结构基点。",
                ["q_strength_assessment", "q_day_master_month_anchor", "q_useful_god_candidates", "q_pattern_structure", "q_month_command_anchor", "q_structure_overview"],
                78,
            )
        )
    hidden = facts.get("hidden_stems_by_branch") if isinstance(facts.get("hidden_stems_by_branch"), dict) else {}
    if hidden:
        observed = []
        for branch, stems in hidden.items():
            if not stems:
                continue
            stem_list = stems if isinstance(stems, list) else [stems]
            observed.append(f"{branch}藏{'/'.join([str(stem) for stem in stem_list if str(stem)])}")
        signals.append(
            _structural_signal(
                "struct.hidden_stems",
                "hidden_stem",
                observed[:8],
                ["hidden_stems"],
                "藏干用于说明结构来源，不直接等于断语。",
                ["q_hidden_stem_role", "q_ten_god_metadata", "q_element_flow_metadata"],
                70,
            )
        )
    return signals


def _branch_relation_question_keys(facts: Dict[str, Any]) -> List[str]:
    if facts.get("has_time_relation") and not facts.get("has_branch_relation"):
        keys = ["q_time_vs_natal_relation", "q_branch_relation_detail"]
    elif facts.get("has_three_harmony") or facts.get("has_three_meeting") or "three_harmony" in (facts.get("relation_types") or set()) or "three_meeting" in (facts.get("relation_types") or set()):
        keys = ["q_three_harmony_context", "q_branch_relation_detail"]
    elif facts.get("has_combination"):
        keys = ["q_combination_context", "q_branch_relation_detail"]
    elif facts.get("has_harm") or facts.get("has_break") or facts.get("has_clash"):
        keys = ["q_branch_relation_detail", "q_time_vs_natal_relation"]
    else:
        keys = ["q_branch_relation_detail"]
    if facts.get("has_time_relation") and "q_time_vs_natal_relation" not in keys:
        keys.append("q_time_vs_natal_relation")
    return keys[:3]


def _structural_signal(signal_id: str, category: str, observed: List[str], fact_scopes: List[str], reason: str, question_keys: List[str], score: int) -> Dict[str, Any]:
    return {
        "signal_id": signal_id,
        "source": "structural_rule_signal",
        "version": "p5.structural_signals.v1",
        "domain": "structure",
        "category": category,
        "observed": [str(item) for item in observed if str(item)],
        "fact_scopes": fact_scopes,
        "reason": reason,
        "question_keys": question_keys,
        "score": score,
        "mutates_result": False,
    }


def _questions_for_structural_signal(signal: Dict[str, Any], facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    observed = [str(item) for item in signal.get("observed") or [] if str(item)]
    for key in signal.get("question_keys") or []:
        contract = QUESTION_REGISTRY.get(str(key) or "")
        if not contract:
            continue
        label = _structural_question_label(key, contract, signal, observed)
        rows.append(
            {
                "key": key,
                "source": "structural_rule_signal",
                "registry_version": QUESTION_REGISTRY_VERSION,
                "label": label,
                "theme": contract.get("theme") or signal.get("category") or "structure_basis",
                "intent": contract.get("intent") or signal.get("category") or "structure_overview",
                "answer_scope": contract.get("answer_scope") or "",
                "required_facts": list(contract.get("required_facts") or signal.get("fact_scopes") or []),
                "score": int(signal.get("score") or contract.get("score") or 0),
                "question_basis": _signal_user_label(str(signal.get("category") or "")),
                "source_signal_category": signal.get("category") or "",
                "basis_text": _l(
                    str(signal.get("reason") or "当前命盘有可解释的结构事实。"),
                    "The chart has structural facts that can be explained.",
                    "명식에 설명 가능한 구조 사실이 있습니다.",
                ),
                "source_signal_id": "" if key in {"q_ten_god_metadata", "q_month_command_anchor"} else signal.get("signal_id") or "",
                "observed": observed[:6],
                "runtime_scope": "question_recommendation_only_no_result_mutation",
            }
        )
    return rows


def _structural_question_label(key: str, contract: Dict[str, Any], signal: Dict[str, Any], observed: List[str]) -> Dict[str, str]:
    fallback = contract.get("label") if isinstance(contract.get("label"), dict) else {}
    text = "、".join(observed[:4])
    category = str(signal.get("category") or "")
    if key == "q_branch_relation_detail" and text:
        return _l(
            f"当前命中的{text}关系，分别发生在本命还是时间背景？",
            f"Do the visible relations {text} occur in the natal chart or timing context?",
            f"보이는 관계 {text}는 원국 안인가요, 시간 배경인가요?",
        )
    if key == "q_combination_context" and text:
        return _l(
            f"这里的{text}关系，只能说明什么结构连接？",
            f"What structural link can the relation {text} indicate here?",
            f"여기서 {text} 관계는 어떤 구조 연결만 뜻하나요?",
        )
    if key == "q_three_harmony_context" and text:
        return _l(
            f"这里的{text}成组关系，只能说明什么结构连接？",
            f"What structural link can the grouped relation {text} indicate here?",
            f"여기서 {text} 묶음 관계는 어떤 구조 연결만 뜻하나요?",
        )
    if key == "q_time_vs_natal_relation" and text:
        return _l(
            f"{text}这类关系，哪些属于本命，哪些只是时间背景？",
            f"For relations like {text}, what belongs to natal structure and what is timing context?",
            f"{text} 같은 관계에서 무엇은 원국이고 무엇은 시간 배경인가요?",
        )
    if key == "q_day_master_month_anchor" and text:
        return _l(
            f"日主、月令这组结构基点（{text}）先看什么？",
            f"What should be read first from this day-master/month anchor ({text})?",
            f"일간·월령 기준점({text})에서 먼저 무엇을 보나요?",
        )
    if key == "q_strength_assessment" and text:
        return _l(
            f"日主强弱要围绕{text}先看哪些证据？",
            f"For day-master strength around {text}, which evidence comes first?",
            f"{text}를 중심으로 일간 강약은 어떤 근거를 먼저 보나요?",
        )
    if key == "q_useful_god_candidates" and text:
        return _l(
            f"在{text}这个结构入口下，用神只能先形成哪些候选？",
            f"Under the structural entry {text}, what useful-god candidates can be formed first?",
            f"{text} 구조 입구에서 용신은 어떤 후보로만 볼 수 있나요?",
        )
    if key == "q_pattern_structure" and text:
        return _l(
            f"从{text}开始，这个八字的格局应该先看哪些条件？",
            f"Starting from {text}, which conditions should be checked first for pattern?",
            f"{text}에서 시작할 때 이 사주의 격국은 어떤 조건을 먼저 보나요?",
        )
    if key == "q_month_command_anchor" and text:
        return _l(
            f"月令相关的结构背景（{text}）先提供了什么？",
            f"What structural background does the month-command context ({text}) provide?",
            f"월령 관련 구조 배경({text})은 먼저 무엇을 제공하나요?",
        )
    if key == "q_hidden_stem_role" and text:
        return _l(
            f"{text}这些藏干信息，会怎样影响结构理解？",
            f"How do these hidden-stem clues ({text}) affect structural reading?",
            f"이 지장간 정보({text})는 구조 이해에 어떻게 영향을 주나요?",
        )
    if key == "q_ten_god_metadata":
        return _l(
            "这里的十神标签为什么只是关系元数据，而不是断语？",
            "Why are the Ten God labels here relational metadata rather than verdicts?",
            "여기서 십성 라벨은 왜 단정이 아니라 관계 메타데이터인가요?",
        )
    if key == "q_structure_overview" and text and category:
        return _l(
            f"从{text}开始看，这张命盘先呈现哪些结构特征？",
            f"Starting from {text}, what structural features appear first?",
            f"{text}에서 시작하면 이 명식의 구조 특징은 무엇인가요?",
        )
    return dict(fallback)


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
    if not source_question:
        registered_question = _registry_question_for_key(clean_key)
        if registered_question:
            source_question = _registry_question(clean_key, registered_question)
    source_signal = _source_signal_for_question(guided_context, source_question)
    intent = route_guided_question_intent(clean_key, clean_message, source_signal)
    answer_kind = str(intent.get("answer_kind") or "structure_overview")
    if intent.get("supported") is False:
        source_signal = {}
    if not source_signal:
        source_signal = _source_signal_for_question_or_kind(guided_context, source_question, answer_kind)
    if intent.get("supported") is False:
        source_signal = {}
    intent["source_signal_id"] = source_signal.get("signal_id") if source_signal else ""
    intent["source_signal_category"] = source_signal.get("category") if source_signal else ""
    rule_graph_context = orchestrate_rule_graph_paths(
        agent_data,
        question_key=clean_key,
        message=clean_message,
        answer_kind=answer_kind,
        limit=6,
    )
    rule_graph_answer_audit = audit_selected_paths_for_answer(rule_graph_context.get("selected_paths") or [])
    knowledge_context = dict(agent_data.get("knowledge_context") or {})
    applied_knowledge = _select_answer_knowledge(knowledge_context, answer_kind, clean_key, clean_message, source_signal)
    applied_knowledge = _merge_rule_graph_answer_knowledge(applied_knowledge, rule_graph_context)
    retrieved_facts = retrieve_guided_question_facts(intent, chart, time_context, facts, income_bundle, guided_context, source_question, source_signal)
    retrieved_facts["knowledge_context"] = {
        "applied_ids": [str(item.get("knowledge_id") or "") for item in applied_knowledge if item.get("knowledge_id")],
        "items": applied_knowledge,
        "runtime_scope": "answer_composer_context_only",
    }
    retrieved_facts["rule_graph_context"] = {
        "selected_path_ids": [str(item.get("path_id") or "") for item in rule_graph_context.get("selected_paths") or []],
        "selected_knowledge_ids": [str(item.get("knowledge_id") or "") for item in rule_graph_context.get("selected_paths") or []],
        "answer_audit_status": rule_graph_answer_audit.get("status"),
        "runtime_scope": "answer_pre_audit_context_only_no_mutation",
    }
    runtime_context = dict(agent_data.get("rule_graph_runtime_context") or {})
    if runtime_context:
        retrieved_facts["rule_graph_runtime_context"] = {
            "status": runtime_context.get("status") or "",
            "selected_knowledge_ids": list((runtime_context.get("knowledge_route") or {}).get("selected_knowledge_ids") or [])[:8],
            "selected_rule_ids": list((runtime_context.get("knowledge_route") or {}).get("selected_rule_ids") or [])[:8],
            "route_count": runtime_context.get("route_count") or 0,
            "answer_audit_status": (runtime_context.get("answer_audit") or {}).get("status") or "",
            "runtime_scope": "measurement_route_pack_context_only_no_mutation",
        }
    structure_portrait = dict(agent_data.get("structure_portrait") or {})
    if structure_portrait:
        retrieved_facts["structure_portrait"] = _compact_structure_portrait(structure_portrait)
    evidence_pack = build_guided_answer_evidence_pack(
        question_key=clean_key,
        question_text=clean_message,
        answer_kind=answer_kind,
        intent=intent,
        source_signal=source_signal,
        retrieved_facts=retrieved_facts,
        applied_knowledge=applied_knowledge,
        knowledge_context=knowledge_context,
        rule_graph_context=rule_graph_context,
        rule_graph_runtime_context=runtime_context,
    )
    retrieved_facts["evidence_pack"] = evidence_pack_summary(evidence_pack)
    sections = _guided_answer_sections(answer_kind, chart, time_context, facts, income_bundle, guided_context, source_question, source_signal)
    summary = _guided_answer_summary(answer_kind, source_signal)
    result_relation = _l("", "", "")
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
        "knowledge_context": knowledge_context,
        "rule_graph_context": rule_graph_context,
        "rule_graph_runtime_context": runtime_context,
        "structure_portrait": _compact_structure_portrait(structure_portrait),
        "rule_graph_answer_audit": rule_graph_answer_audit,
        "evidence_pack": evidence_pack,
        "applied_knowledge": applied_knowledge,
        "observed_facts": _guided_answer_observed_facts(chart, time_context, facts, income_bundle, source_question, source_signal, answer_kind),
        "composed_text": {"zh": compose_guided_question_answer(clean_message, intent, retrieved_facts, summary, result_relation, applied_knowledge)},
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
    locale = _normalize_locale(locale)
    intent = dict(answer.get("intent") or {})
    if intent.get("supported") is False:
        return _unsupported_plain_text(str(intent.get("unsupported_reason") or ""), locale)
    composed = answer.get("composed_text")
    if isinstance(composed, dict):
        text = str(composed.get(locale) or (composed.get("zh") if locale == "zh" else "") or "").strip()
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
            if locale == "en":
                if label and value and note:
                    items.append(f"{label}: {value}. {note}")
                elif label and value:
                    items.append(f"{label}: {value}")
                elif value:
                    items.append(value)
            elif locale == "ko":
                if label and value and note:
                    items.append(f"{label}: {value}. {note}")
                elif label and value:
                    items.append(f"{label}: {value}")
                elif value:
                    items.append(value)
            elif label and value and note:
                items.append(f"{label}是{value}，{note}")
            elif label and value:
                items.append(f"{label}是{value}")
            elif value:
                items.append(value)
        if items:
            if locale == "en":
                sentences.append((f"In {title}: " if title else "") + "; ".join(items) + ".")
            elif locale == "ko":
                sentences.append((f"{title}: " if title else "") + "; ".join(items) + ".")
            else:
                sentences.append((f"{title}里，" if title else "") + "；".join(items) + "。")
    if relation:
        sentences.append(relation)
    return "\n\n".join(sentence for sentence in sentences if sentence)


def _normalize_locale(value: str) -> str:
    clean = str(value or "zh").strip().lower()
    if clean in {"en", "en-us", "english"}:
        return "en"
    if clean in {"ko", "ko-kr", "kr", "korean"}:
        return "ko"
    return "zh"


def _unsupported_plain_text(reason: str, locale: str) -> str:
    reason = str(reason or "")
    locale = _normalize_locale(locale)
    if reason.startswith("smalltalk:greeting"):
        return {
            "zh": "你好。我可以继续帮你看这张命盘，但需要你问一个和结构有关的问题。比如可以问：这张命盘先看哪些结构特征、日主和月令怎么读、藏干代表什么、或者收入稳定性结构如何。",
            "en": "Hello. I can keep reading this chart, but I need a structure-related question. You can ask what structural features appear first, how to read the day master and month branch, what hidden stems mean, or how the income-stability structure looks.",
            "ko": "안녕하세요. 이 명식을 계속 볼 수 있지만 구조와 관련된 질문이 필요합니다. 먼저 보이는 구조 특징, 일간과 월령 읽기, 지장간의 의미, 소득 안정성 구조 등을 물어볼 수 있습니다.",
        }[locale]
    return {
        "zh": "这个问题当前不在系统支持的结构分析范围内，所以我不会硬编答案。目前可以可靠回答的是：四柱结构、日主和月令、藏干、地支冲合、墓库、大运和流年作为时间背景，以及收入、事业、关系、健康这几类结构边界信号。",
        "en": "This question is outside the currently supported structural-reading scope, so I will not invent an answer. The reliable scope now covers pillar structure, day master and month branch, hidden stems, branch relations, vault branches, luck cycle and flow year as timing context, plus income, career, relationship, and health structural-boundary signals.",
        "ko": "이 질문은 현재 지원하는 구조 분석 범위를 벗어나므로 답을 지어내지 않습니다. 현재 안정적으로 답할 수 있는 범위는 사주 구조, 일간과 월령, 지장간, 지지 충합, 묘고, 대운과 세운의 시간 배경, 그리고 소득·직업·관계·건강의 구조 경계 신호입니다.",
    }[locale]


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
        "day_stem": str((pillars.get("day") or {}).get("stem") or ""),
        "day_branch": str((pillars.get("day") or {}).get("branch") or ""),
        "month_stem": str((pillars.get("month") or {}).get("stem") or ""),
        "month_branch": str((pillars.get("month") or {}).get("branch") or ""),
        "hidden_stems_by_branch": {
            branch: [stem for stem, _ in BRANCH_HIDDEN_STEMS.get(branch, [])]
            for branch in sorted(branch_set)
            if BRANCH_HIDDEN_STEMS.get(branch)
        },
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
        "has_combination": bool(relation_pairs_by_type.get("combination") or relation_pairs_by_type.get("three_harmony") or relation_pairs_by_type.get("three_meeting")),
        "has_harm": bool(relation_pairs_by_type.get("harm")),
        "has_break": bool(relation_pairs_by_type.get("break")),
        "has_three_harmony": _has_three_harmony(branches),
        "has_three_meeting": _has_three_meeting(branches),
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


def _baseline_questions(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    keys = ["q_income_stability"]
    if facts.get("day_stem") or facts.get("month_branch"):
        keys.extend(["q_strength_assessment", "q_useful_god_candidates", "q_pattern_structure", "q_ten_god_focus"])
    if not facts.get("day_stem") and not facts.get("month_branch"):
        keys.append("q_structure_overview")
    rows = []
    for key in keys:
        spec = QUESTION_REGISTRY.get(key)
        if not spec:
            continue
        row = _registry_question(key, spec)
        row["source"] = "baseline_question_fallback"
        row["score"] = min(int(row.get("score") or 0), 82)
        row["question_basis"] = _l("基础问题入口", "Baseline question entry", "기본 질문 진입점")
        row["basis_text"] = _l(
            "用于保证用户始终有一个可回答的结构问题；排序会让命盘命中的结构问题优先。",
            "Keeps one answerable structural question available while chart-matched questions rank first.",
            "항상 답변 가능한 구조 질문을 남기되, 명식에 맞는 질문을 우선합니다.",
        )
        rows.append(row)
    return rows


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
        "strength_assessment": {"strength_model", "structure_anchor", "stem_branch_attribute"},
        "useful_god_boundary": {"strength_model", "five_element_relation", "structure_anchor", "stem_branch_attribute"},
        "pattern_structure": {"pattern_structure", "ten_god_interaction", "strength_model", "structure_anchor"},
        "metadata_boundary": {"ten_god", "ten_god_interaction", "hidden_stem", "hidden_stems", "structure_anchor", "stem_branch_attribute", "five_element_relation", "stem_relation", "strength_model"},
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


def _source_signal_for_question_or_kind(guided_context: Dict[str, Any], question: Dict[str, Any], answer_kind: str) -> Dict[str, Any]:
    key = str(question.get("key") or "")
    preferred = _preferred_signal_categories_for_question(key, answer_kind)
    if preferred:
        signal = _first_signal_by_category(guided_context, preferred)
        if signal:
            return signal
    return _source_signal_for_answer_kind(guided_context, answer_kind)


def _preferred_signal_categories_for_question(question_key: str, answer_kind: str) -> List[str]:
    key = str(question_key or "")
    if key == "q_month_command_anchor":
        return ["strength_model", "structure_anchor", "stem_branch_attribute"]
    if key == "q_day_master_month_anchor":
        return ["structure_anchor", "strength_model", "stem_branch_attribute"]
    if key in {"q_strength_assessment", "q_useful_god_candidates", "q_unfavorable_god_boundary", "q_favorable_elements_boundary"}:
        return ["strength_model", "structure_anchor", "five_element_relation", "stem_branch_attribute"]
    if key == "q_pattern_structure":
        return ["pattern_structure", "ten_god_interaction", "structure_anchor", "strength_model"]
    if key == "q_ten_god_focus":
        return ["ten_god_interaction", "ten_god", "wealth_boundary", "strength_model"]
    if key == "q_hidden_stem_role":
        return ["hidden_stem", "hidden_stems"]
    if key == "q_ten_god_metadata":
        return ["ten_god_interaction", "ten_god", "wealth_boundary"]
    if key == "q_element_flow_metadata":
        return ["five_element_relation", "stem_relation", "stem_branch_attribute"]
    if answer_kind == "metadata_boundary":
        return ["ten_god_interaction", "structure_anchor", "hidden_stem", "hidden_stems", "ten_god", "strength_model"]
    return []


def _first_signal_by_category(guided_context: Dict[str, Any], categories: List[str]) -> Dict[str, Any]:
    priority = {category: index for index, category in enumerate(categories)}
    candidates: List[Tuple[int, int, Dict[str, Any]]] = []
    for index, row in enumerate(guided_context.get("signals") or []):
        if not isinstance(row, dict):
            continue
        category = str(row.get("category") or row.get("domain") or "")
        if category in priority:
            candidates.append((priority[category], index, dict(row)))
    if not candidates:
        return {}
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][2]


def route_guided_question_intent(question_key: str, message: str, source_signal: Dict[str, Any] | None = None) -> Dict[str, Any]:
    key = str(question_key or "").strip()
    text = str(message or "").strip()
    registered = _registry_question_for_key(key)
    signal_kind = _guided_answer_kind_from_signal(source_signal or {})
    unsupported_reason = _unsupported_question_reason(text)
    answer_kind = "unsupported" if unsupported_reason else str(registered.get("intent") or signal_kind or _guided_answer_kind(key, text))
    intent_map = {
        "unsupported": ("intent.unsupported_question", "boundary", []),
        "branch_relation": ("intent.branch_relation", "structural_relation", ["pillars", "natal_relations", "time_relations"]),
        "vault": ("intent.vault_structure", "structural_relation", ["pillars", "vault_branches", "hidden_stems"]),
        "time_boundary": ("intent.time_context_boundary", "time_structure", ["pillars", "luck_cycle", "flow_year", "time_relations"]),
        "income_structure": ("intent.income_structure", "income_stability", ["income_signals", "pillars", "relations"]),
        "strength_assessment": ("intent.strength_assessment", "strength_structure", ["pillars", "month_branch", "hidden_stems", "stem_elements"]),
        "useful_god_boundary": ("intent.useful_god_boundary", "useful_god", ["pillars", "month_branch", "hidden_stems", "stem_elements", "relations"]),
        "pattern_structure": ("intent.pattern_structure", "pattern", ["pillars", "month_branch", "ten_god_metadata", "relations"]),
        "career_structure": ("intent.career_structure", "career_structure", ["pillars", "relations", "source_signal"]),
        "relationship_structure": ("intent.relationship_structure", "relationship_structure", ["pillars", "relations", "source_signal", "time_context"]),
        "health_structure": ("intent.health_structure", "health_structure", ["pillars", "relations", "source_signal", "time_context"]),
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
        "question_key": key,
        "question_text": text,
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


def compose_guided_question_answer(
    question_text: str,
    intent: Dict[str, Any],
    facts: Dict[str, Any],
    summary: Dict[str, str],
    result_relation: Dict[str, str],
    applied_knowledge: List[Dict[str, Any]] | None = None,
) -> str:
    if intent.get("supported") is False:
        if str(intent.get("unsupported_reason") or "").startswith("smalltalk:greeting"):
            return (
                "你好。我可以继续帮你看这张命盘，但需要你问一个和结构有关的问题。"
                "比如可以问：这张命盘先看哪些结构特征、日主和月令怎么读、藏干代表什么、或者收入稳定性结构如何。"
            )
        return (
            "这个问题当前不在系统支持的结构分析范围内，所以我不会硬编答案。"
            "目前可以可靠回答的是：四柱结构、日主和月令、藏干、地支冲合、墓库、大运和流年作为时间背景，以及收入、事业、关系、健康这几类结构边界信号。"
            "你可以换成上方推荐问题，或把问题改成“这张命盘先看哪些结构特征？”这类结构问题。"
        )
    answer_kind = str(intent.get("answer_kind") or "structure_overview")
    anchor = dict(facts.get("chart_anchor") or {})
    relations = list(facts.get("relations") or [])
    vaults = list(facts.get("vaults") or [])
    time_context = dict(facts.get("time_context") or {})
    income_signals = dict(facts.get("income_signals") or {})
    knowledge_items = list(applied_knowledge or [])
    source_signal = dict(facts.get("source_signal") or {})
    paragraphs: List[str] = []

    if answer_kind == "branch_relation":
        if relations:
            relation_text = "；".join(_relation_fact_sentence(row) for row in relations[:6])
            boundary = "如果出现刑、害、破，也先按关系名处理，不能从名称直接扩写成冲突或灾祸。" if any(str(row.get("type") or "") in {"harm", "break"} for row in relations) or _knowledge_has(knowledge_items, "penalty_harm_break") else "这里的重点不是判断好坏，而是看哪些地支之间产生了连接、牵动或张力。"
            paragraphs.append(f"你问的是地支关系。当前可见的结构关系主要是：{relation_text}。{boundary}")
        else:
            paragraphs.append("你问的是地支关系。当前可取到的命盘事实里没有明确的关系条目，所以这里不能硬说某个关系已经触发；最多只能回到四柱本身继续看结构。")
        paragraphs.append(_time_context_sentence(time_context))
    elif answer_kind == "vault":
        if vaults:
            vault_text = "；".join(f"{row.get('branch')}在{row.get('locations')}，藏干是{row.get('hidden_stems')}" for row in vaults[:4])
            paragraphs.append(f"你问的是墓库结构。当前实际看到的是：{vault_text}。这类信息适合用来说明结构里哪里有收束、储藏或承载的节点。")
        else:
            paragraphs.append("你问的是墓库结构。当前事实检索没有找到明确墓库支，所以不能为了回答而补一个不存在的墓库判断。")
    elif answer_kind == "time_boundary":
        paragraphs.append(_time_context_sentence(time_context))
        paragraphs.append("读这类信息时，先看它属于大运、流年还是本命内部，再看它和哪一柱发生关系；不要把一个时间背景词直接读成结果。")
    elif answer_kind == "income_structure":
        if income_signals:
            signal_text = "；".join(f"{_income_signal_label(key)}是{value}" for key, value in income_signals.items() if key and value)
            paragraphs.append(f"你问的是收入稳定性结构。当前可见的相关信号是：{signal_text}。这些信号说明结构状态；具体财富事件需要另按时间与事实条件分析。")
        else:
            paragraphs.append("你问的是收入稳定性结构，但当前没有取到可用的收入结构信号，所以这里不能硬生成结论。")
    elif answer_kind in {"career_structure", "relationship_structure", "health_structure"}:
        label = _domain_answer_label(answer_kind)
        focus = _domain_answer_focus(answer_kind, knowledge_items, source_signal)
        paragraphs.append(f"你问的是{label}。这里先按结构边界读：{focus}")
        paragraphs.append(_domain_answer_boundary(answer_kind))
    elif answer_kind == "metadata_boundary":
        day = anchor.get("day_pillar") or "日柱未取到"
        day_stem = anchor.get("day_stem") or ""
        month = anchor.get("month_pillar") or "月柱未取到"
        month_branch = anchor.get("month_branch") or ""
        hidden = dict(facts.get("hidden_stems") or {})
        hidden_text = "；".join(f"{branch}藏{stems}" for branch, stems in hidden.items()) or "当前没有可展开的藏干信息"
        focus = _metadata_focus(intent, question_text)
        source_signal = dict(facts.get("source_signal") or {})
        if focus == "month_command":
            hidden_month = _hidden_stems_label(month_branch) if month_branch else "-"
            paragraphs.append(f"你问的是月令。当前月柱是{month}，月支{month_branch or '未取到'}先提供的是日主所处的季节和结构背景；这个月支本身藏干是{hidden_month}。")
            paragraphs.append(f"所以它适合先回答“环境从哪里来”：日柱{day}要放回月令背景里读，再和透出的天干、藏干、地支关系一起看；月令不能单独推出身强、身弱或好坏。")
        elif focus == "ten_god":
            if source_signal.get("category") == "ten_god_interaction":
                title = str(source_signal.get("title") or "十神组合").replace("组合存在", "")
                observed = "、".join(_plain_observed_values(list(source_signal.get("observed") or []))) or "当前命中的十神组合"
                paragraphs.append(f"你问的是{title}。当前实际命中的组合事实是：{observed}。")
                paragraphs.append("这一层只确认哪些十神关系同时出现、来自可见天干还是其他结构来源；它还不能直接推出事件、好坏或具体结果。")
            else:
                visible_text = _visible_ten_god_text(anchor)
                visible_fallback = f"日主{day_stem or '未取到'}周围的可见天干需要逐一映射"
                paragraphs.append("你问的是十神标签。它在这里先按五类关系读：比劫是同类关系，食伤是输出关系，财是日主所克的对象关系，官杀是约束关系，印是来源支持关系。")
                paragraphs.append(f"当前要先分层：{visible_text or visible_fallback}；藏干层面看到：{hidden_text}。这些标签说明关系来源，不单独当结论。")
        elif focus == "hidden_stems":
            paragraphs.append(f"你问的是藏干。当前藏干层面看到：{hidden_text}。它会影响结构理解，因为它说明某个五行或关系是直接透出，还是藏在地支里面。")
            paragraphs.append(f"所以这里先把来源层分清：日柱{day}和月柱{month}是入口，藏干只是补足结构来源，不直接替代结果判断。")
        else:
            paragraphs.append(f"你问的是十神、藏干或日主月令这类结构信息。当前结构基点可以先看日柱{day}和月柱{month}；藏干层面看到：{hidden_text}。")
            paragraphs.append("这些内容的作用是解释关系来源，比如某个五行或关系从哪里出现；它本身不是一句断语，也不直接等于某个结果。")
    elif answer_kind == "rule_basis":
        signal = dict(facts.get("source_signal") or {})
        observed = "、".join(_plain_observed_values(signal.get("observed") or [])) or "当前可见结构事实"
        paragraphs.append(f"这条判断可以先看它用了哪些事实：{observed}。对用户来说，重点是这些事实是否在命盘或时间背景中真实出现，而不是去看编号。")
    else:
        day = anchor.get("day_pillar") or "日柱未取到"
        month = anchor.get("month_pillar") or "月柱未取到"
        relation_text = "；".join(_relation_fact_sentence(row) for row in relations[:3]) if relations else "当前没有明确地支关系条目"
        vault_text = "、".join(str(row.get("branch")) for row in vaults) if vaults else "未见明确墓库支"
        paragraphs.append(f"如果只看结构，这张命盘可以先抓三个入口：日柱是{day}，月柱是{month}，地支关系是{relation_text}，墓库观察是{vault_text}。")
        paragraphs.append("这些入口只是帮你建立阅读顺序：先知道结构事实在哪里，再讨论某个主题是否有足够证据。")

    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph and paragraph.strip())


def _select_answer_knowledge(
    knowledge_context: Dict[str, Any],
    answer_kind: str,
    question_key: str,
    question_text: str,
    source_signal: Dict[str, Any],
) -> List[Dict[str, Any]]:
    rows = [dict(row) for row in knowledge_context.get("items") or [] if isinstance(row, dict)]
    if not rows:
        return []
    focus_text = " ".join(
        [
            str(answer_kind or ""),
            str(question_key or ""),
            str(question_text or ""),
            str(source_signal.get("knowledge_id") or ""),
            str(source_signal.get("category") or ""),
        ]
    )
    selected: List[Dict[str, Any]] = []
    style_rows: List[Dict[str, Any]] = []
    for row in rows:
        domain = str(row.get("domain") or "")
        knowledge_id = str(row.get("knowledge_id") or "")
        blob = _norm_text(" ".join([knowledge_id, domain, str(row.get("title") or ""), str(row.get("statement") or "")]))
        if domain == "answer_expression":
            style_rows.append(_compact_knowledge_item(row))
            continue
        if _knowledge_relevant_to_answer(blob, focus_text):
            selected.append(_compact_knowledge_item(row))
    selected.extend(style_rows[:2])
    return selected[:6]


def _merge_rule_graph_answer_knowledge(applied_knowledge: List[Dict[str, Any]], rule_graph_context: Dict[str, Any], *, limit: int = 12) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen = set()
    for row in applied_knowledge:
        if not isinstance(row, dict):
            continue
        knowledge_id = str(row.get("knowledge_id") or "")
        if knowledge_id and knowledge_id in seen:
            continue
        if knowledge_id:
            seen.add(knowledge_id)
        merged.append(dict(row))
    for path in rule_graph_context.get("selected_paths") or []:
        if not isinstance(path, dict):
            continue
        knowledge_id = str(path.get("knowledge_id") or "")
        if not knowledge_id or knowledge_id in seen:
            continue
        seen.add(knowledge_id)
        merged.append(_compact_rule_graph_knowledge_item(path))
        if len(merged) >= limit:
            break
    return merged[:limit]


def _compact_rule_graph_knowledge_item(path: Dict[str, Any]) -> Dict[str, Any]:
    reason = str(path.get("reason") or "当前命盘结构路径选中该知识；只作为回答证据，不作为结论。")
    return {
        "knowledge_id": path.get("knowledge_id") or "",
        "domain": path.get("domain") or "",
        "title": path.get("title") or path.get("knowledge_id") or "",
        "statement": reason,
        "evidence_type": "rule_graph_route_evidence",
        "match_score": path.get("score"),
        "route_match_score": path.get("score"),
        "route_match_reasons": ["rule_graph_selected_path"],
        "topic_lane": path.get("topic_lane") or "",
        "framework_state": path.get("framework_state") or "",
        "runtime_allowed": path.get("runtime_allowed") is True,
    }


def _compact_knowledge_item(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "knowledge_id": row.get("knowledge_id"),
        "domain": row.get("domain"),
        "title": row.get("title"),
        "statement": row.get("statement"),
        "evidence_type": row.get("evidence_type"),
        "match_score": row.get("match_score"),
        "route_match_score": row.get("route_match_score"),
        "route_match_reasons": list(row.get("route_match_reasons") or []),
    }


def _knowledge_relevant_to_answer(knowledge_blob: str, focus_text: str) -> bool:
    focus = _norm_text(focus_text)
    pairs = [
        ("月令", "month_command"),
        ("月支", "month_command"),
        ("身强", "month_command"),
        ("身弱", "month_command"),
        ("十神", "ten_god"),
        ("财星", "ten_god"),
        ("官杀", "ten_god"),
        ("印星", "ten_god"),
        ("藏干", "hidden_stem"),
        ("透干", "hidden_stem"),
        ("刑", "penalty_harm_break"),
        ("害", "penalty_harm_break"),
        ("破", "penalty_harm_break"),
        ("三会", "three_meeting"),
        ("墓库", "vault"),
        ("地支关系", "branch_relation"),
        ("冲", "branch_relation"),
        ("合", "branch_relation"),
        ("收入", "income"),
        ("财富", "income"),
    ]
    for user_token, knowledge_token in pairs:
        if user_token in focus and knowledge_token in knowledge_blob:
            return True
    return False


def _knowledge_has(rows: List[Dict[str, Any]], needle: str) -> bool:
    target = str(needle or "")
    if not target:
        return False
    return any(target in str(row.get("knowledge_id") or "") or target in str(row.get("statement") or "") for row in rows)


def _metadata_focus(intent: Dict[str, Any], question_text: str) -> str:
    text = _norm_text(
        " ".join(
            [
                str(intent.get("question_key") or ""),
                str(intent.get("answer_scope") or ""),
                str(question_text or ""),
                " ".join(str(item) for item in intent.get("detected_terms") or []),
            ]
        )
    )
    if "月令" in text or "月支" in text or "month_command" in text:
        return "month_command"
    if "十神" in text or "ten_god" in text:
        return "ten_god"
    if "藏干" in text or "hidden_stem" in text:
        return "hidden_stems"
    return "metadata"


def _visible_ten_god_text(anchor: Dict[str, Any]) -> str:
    day_stem = str(anchor.get("day_stem") or "")
    if not day_stem:
        return ""
    rows = []
    for item in anchor.get("pillar_order") or []:
        if not isinstance(item, dict):
            continue
        stem = str(item.get("stem") or "")
        display = str(item.get("display") or stem)
        if not stem:
            continue
        rows.append(f"{display}的{stem}是{_ten_god_family_label(ten_god(day_stem, stem))}")
    return "、".join(rows[:4])


def _ten_god_family_label(value: str) -> str:
    labels = {
        "peer": "同类关系",
        "output": "输出关系",
        "wealth": "日主所克的对象关系",
        "officer": "约束关系",
        "seal": "来源支持关系",
    }
    return labels.get(str(value or ""), "待确认关系")


def _plain_observed_values(values: List[Any]) -> List[str]:
    rows = []
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        if "=" in text:
            key, raw_value = text.split("=", 1)
            rows.append(f"{_income_signal_label(key)}是{_plain_signal_value(raw_value)}")
        elif text == "relation_metadata":
            rows.append("关系标签")
        elif text.startswith("gen:"):
            rows.append(text.replace("gen:", "相生关系 "))
        elif text.startswith("ctrl:"):
            rows.append(text.replace("ctrl:", "相克关系 "))
        else:
            rows.append(text.replace("group:", "组合"))
    return rows


def _plain_signal_value(value: str) -> str:
    labels = {
        "none": "无",
        "low": "低",
        "medium": "中",
        "high": "高",
        "not_applicable": "不适用",
        "unstable": "不稳定",
        "stable": "稳定",
        "mixed": "混合",
    }
    return labels.get(str(value or ""), str(value or "未知"))


def _norm_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _detected_intent_terms(text: str) -> List[str]:
    terms = []
    for token in ["冲", "合", "刑", "害", "破", "六合", "三合", "三会", "墓库", "藏干", "透干", "十神", "日主", "月令", "月支", "大运", "流年", "时间", "收入", "财富", "规则依据"]:
        if token in text:
            terms.append(token)
    return _dedupe_keep_order(terms)


def _unsupported_question_reason(text: str) -> str:
    clean = str(text or "")
    compact = "".join(clean.split()).lower()
    greetings = {"你好", "您好", "hello", "hi", "hey", "嗨", "哈喽", "在吗", "早", "早上好", "晚上好"}
    if compact in greetings:
        return "smalltalk:greeting"
    hard_unsupported_terms = ["疾病", "子女", "父母", "官司", "升职", "考试", "什么时候", "哪一年", "发财", "破财", "好不好", "会不会"]
    for term in hard_unsupported_terms:
        if term in clean:
            return f"unsupported_topic:{term}"
    if _is_supported_domain_structure_question(clean):
        return ""
    unsupported_terms = ["婚姻", "感情", "健康"]
    for term in unsupported_terms:
        if term in clean:
            return f"unsupported_topic:{term}"
    return ""


def _is_supported_domain_structure_question(text: str) -> bool:
    clean = str(text or "")
    domain_tokens = ["事业", "职业", "工作", "感情", "关系", "婚姻", "伴侣", "配偶", "健康", "身体"]
    boundary_tokens = ["结构", "边界", "信号", "路径", "怎么看", "如何看", "如何读", "只按结构", "需要注意"]
    return any(token in clean for token in domain_tokens) and any(token in clean for token in boundary_tokens)


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
    return f"{row.get('layer')}{_relation_type_phrase(str(row.get('type') or ''))}{pair}"


def _relation_type_phrase(value: str) -> str:
    labels = {
        "clash": "出现冲：",
        "combination": "出现合：",
        "three_harmony": "出现三合：",
        "three_meeting": "出现三会：",
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
    luck_rel = _relation_map_text(dict(luck.get("relations") or luck.get("relations_with_natal") or {}))
    flow_rel = _relation_map_text(dict(flow.get("relations") or flow.get("relations_with_natal") or {}))
    return f"时间背景上，当前大运显示为{luck_pillar}，流年显示为{flow_year}{flow_pillar}；大运关系是{luck_rel}，流年关系是{flow_rel}。这些先作为时间背景阅读。"


def _relation_map_text(relations: Dict[str, List[str]]) -> str:
    parts = []
    for relation_type, pairs in relations.items():
        for pair in pairs:
            parts.append(f"{_relation_type_phrase(str(relation_type)).replace('出现', '').replace('：', '')}{str(pair).replace('-', '')}")
    return "、".join(parts) if parts else "未见明确地支关系条目"


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
    if category == "strength_model" or domain in {"strength", "day_master_element"}:
        return "strength_assessment"
    if category in {"useful_god", "useful_god_boundary"} or domain == "useful_god":
        return "useful_god_boundary"
    if category in {"ten_god", "ten_god_interaction", "hidden_stem", "stem_branch_attribute", "five_element_relation", "stem_relation"}:
        return "metadata_boundary"
    if category == "pattern_structure":
        return "pattern_structure"
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
    lowered = text.lower()
    if key == "q_career_structure" or "career" in key or any(token in lowered for token in ["career", "work", "job"]) or any(token in text for token in ["事业", "职业", "工作", "직업", "커리어"]):
        return "career_structure"
    if key == "q_relationship_structure" or "relationship" in key or any(token in lowered for token in ["relationship", "partner", "marriage"]) or any(token in text for token in ["感情", "伴侣", "配偶", "婚姻", "관계", "연애", "배우자", "결혼"]):
        return "relationship_structure"
    if key == "q_health_structure" or "health" in key or any(token in lowered for token in ["health", "body"]) or any(token in text for token in ["健康", "身体", "건강", "몸"]):
        return "health_structure"
    if key in {"q_branch_relation_detail", "q_time_vs_natal_relation", "q_combination_context", "q_three_harmony_context"} or "branch_relation" in key or key == "q_time_context" or any(token in lowered for token in ["branch relation", "clash", "combination"]) or any(token in text for token in ["冲合", "冲", "合", "刑", "害", "破", "关系", "三合", "三会", "六合", "충", "합"]):
        return "branch_relation"
    if "vault" in key or "vault" in lowered or any(token in text for token in ["墓库", "묘고"]):
        return "vault"
    if key in {"q_time_context_boundary", "q_luck_flow_layers", "q_time_not_inference"} or any(token in lowered for token in ["time context", "luck cycle", "flow year"]) or any(token in text for token in ["时间结构", "大运", "流年", "대운", "세운"]):
        return "time_boundary"
    if key == "q_strength_assessment" or any(token in lowered for token in ["strong", "weak", "strength"]) or any(token in text for token in ["身强", "身弱", "强弱", "旺衰", "日主强", "日主弱"]):
        return "strength_assessment"
    if key in {"q_useful_god_candidates", "q_unfavorable_god_boundary", "q_favorable_elements_boundary"} or any(token in lowered for token in ["useful god", "favorable element", "unfavorable"]) or any(token in text for token in ["用神", "忌神", "喜神", "喜用", "喜什么五行", "忌什么五行"]):
        return "useful_god_boundary"
    if key == "q_pattern_structure" or any(token in lowered for token in ["pattern"]) or any(token in text for token in ["格局", "成格", "破格", "从格", "化格"]):
        return "pattern_structure"
    if key in {
        "q_income_stability",
        "q_income_factors",
        "q_income_continuity",
        "q_wealth_accessibility",
        "q_accessibility_signals",
        "q_signal_combination",
        "q_primary_auxiliary_signals",
        "q_volatility_factors",
    } or "income" in key or "wealth" in key or any(token in lowered for token in ["income", "wealth"]) or any(token in text for token in ["收入", "财富", "소득", "수입", "재물"]):
        return "income_structure"
    if key in {"q_read_result_not_fortune", "q_no_good_bad", "q_result_card_boundary", "q_cautious_reading"}:
        return "result_boundary"
    if key in {"q_day_master_month_anchor", "q_hidden_stem_role", "q_ten_god_focus"} or "ten_god" in key or any(token in lowered for token in ["ten god", "day master", "month branch", "hidden stem"]) or any(token in text for token in ["十神", "藏干", "日主", "月令", "财官印", "食伤", "십성", "일간", "월지", "지장간"]):
        return "metadata_boundary"
    if key == "follow_rule_basis" or "规则依据" in text:
        return "rule_basis"
    return "structure_overview"


def _guided_answer_summary(answer_kind: str, source_signal: Dict[str, Any] | None = None) -> Dict[str, str]:
    observed = _signal_observed_values(source_signal or {})
    observed_text = "、".join(observed)
    summaries = {
        "branch_relation": _l(
            f"可以先这样看：这题问的是地支之间有没有连接或张力。当前可见的是{observed_text or '命盘里已检测到的冲合关系'}，重点不是下结论，而是分清它发生在本命、大运还是流年这一层。",
            f"Read it this way: the question asks whether branches form links or tension. The visible basis is {observed_text or 'the detected branch relations'}, and the key is to separate natal, luck-cycle, and flow-year layers.",
            f"이렇게 보면 됩니다. 이 질문은 지지 사이의 연결이나 긴장이 있는지를 묻습니다. 현재 보이는 근거는 {observed_text or '감지된 지지 관계'}이며, 핵심은 원국·대운·세운 층을 나누는 것입니다.",
        ),
        "vault": _l(
            f"这题适合先看“位置”。当前命中的墓库线索是{observed_text or '墓库支'}：它们在哪里出现、里面藏了什么，是结构信息；不要直接把它翻译成一句吉凶。",
            f"This question starts from location. The vault clue is {observed_text or 'vault branches'}: where it appears and what hidden stems it contains are structural facts, not a good/bad verdict.",
            f"이 질문은 먼저 위치를 봅니다. 묘고 단서는 {observed_text or '묘고 지지'}이며, 어디에 있고 어떤 지장간을 품는지가 구조 정보입니다.",
        ),
        "time_boundary": _l(
            "这里要先把层级分开：大运和流年是时间背景层。它们可以帮助你看见某些关系为什么被提出来，但不会自动变成当前结构结果。",
            "Separate the layers first: luck cycle and flow year are time-context layers. They can explain why a relation is worth asking about, but they do not automatically become the current structural result.",
            "먼저 층을 나눠야 합니다. 대운과 세운은 시간 배경층이며, 어떤 관계를 질문해야 하는지 설명할 수 있지만 현재 구조 결과로 자동 전환되지는 않습니다.",
        ),
        "income_structure": _l(
            "收入稳定性这里按结构读：重点是承载力、财富结构出现度、可达性、波动和牵制这些信号怎样组合，而不是判断你会不会发财。",
            "Income stability is read structurally here: the system looks at capacity, wealth-structure presence, accessibility, volatility, and constraints, not whether someone will become rich.",
            "여기서 소득 안정성은 구조로 읽습니다. 수용력, 재성 구조의 출현, 접근성, 변동성, 견제가 어떻게 조합되는지를 보는 것이지 재물운을 예측하는 것이 아닙니다.",
        ),
        "strength_assessment": _l(
            "日主强弱不能只靠一个字下结论。这里先看月令、透出、藏干、根气和克泄耗支持，形成强弱承载证据，而不是直接给一句身强身弱断语。",
            "Day-master strength cannot be concluded from one character. This first checks month command, visible stems, hidden stems, roots, support, and pressure as evidence, not as a one-line verdict.",
            "일간 강약은 한 글자만으로 단정하지 않습니다. 월령, 투간, 지장간, 뿌리, 지지와 압력을 근거로 보며 단정문으로 처리하지 않습니다.",
        ),
        "useful_god_boundary": _l(
            "用神、忌神这里先作为候选路径处理：必须先有强弱承载、结构病点和调候/通关/扶抑等证据，不够时只能说候选，不能直接给补救建议。",
            "Useful or unfavorable gods are handled as candidate paths here. Strength evidence, structural issue, and balancing path are required; otherwise the answer stays at candidate level with no remedy advice.",
            "용신·기신은 여기서 후보 경로로만 다룹니다. 강약 근거, 구조 문제, 조후·통관·부억 경로가 필요하며 부족하면 후보로만 말합니다.",
        ),
        "pattern_structure": _l(
            "格局问题先按结构索引读：看月令来源、透干、藏干、成格条件和破格因素是否同层成立，不直接把格局名翻译成命运结论。",
            "Pattern questions are read as structural indexing: month source, visible stems, hidden stems, formation conditions, and breaking factors must align; a pattern name is not a fate verdict.",
            "격국 질문은 구조 색인으로 읽습니다. 월령 출처, 투간, 지장간, 성격 조건과 파격 요소가 같은 층에서 성립하는지 봅니다.",
        ),
        "career_structure": _l(
            "事业问题先按结构读：看约束、输出、承载、格局和时间层是否形成可解释路径，不直接推出职业成败。",
            "Career questions are read structurally: constraints, output, capacity, pattern, and timing context are checked as explainable paths, not as success/failure verdicts.",
            "직업 질문은 구조로 읽습니다. 제약, 표현, 수용력, 격국, 시간층이 설명 가능한 경로를 이루는지 보며 성패 단정은 하지 않습니다.",
        ),
        "relationship_structure": _l(
            "关系问题先按结构读：看关系符号、宫位线索、十神互动和时间层牵动，不直接推出感情结果。",
            "Relationship questions are read structurally: relationship symbols, palace clues, Ten God interaction, and timing triggers are checked, not relationship outcomes.",
            "관계 질문은 구조로 읽습니다. 관계 기호, 궁위 단서, 십성 상호작용, 시간층 작용을 보며 결과를 단정하지 않습니다.",
        ),
        "health_structure": _l(
            "健康问题先按结构读：看承载、偏枯、冲合牵动和时间层压力，不输出身体结论。",
            "Health questions are read structurally: capacity, imbalance, branch movement, and timing pressure are checked, with no body-condition verdict.",
            "건강 질문은 구조로 읽습니다. 수용력, 치우침, 충합 작용, 시간층 압력을 보며 신체 상태를 단정하지 않습니다.",
        ),
        "result_boundary": _l(
            "结果卡只是一张结构摘要：它告诉你当前支持的结构主题怎么归类，不负责给人生下判断。",
            "The result card is a structural summary: it classifies the supported structural domain, not a life verdict.",
            "결과 카드는 구조 요약입니다. 현재 규칙이 지원하는 구조 영역을 분류할 뿐 인생 판단을 내리지 않습니다.",
        ),
        "metadata_boundary": _l(
            "十神、藏干、五行在这里像“关系说明书”：它们告诉你某个结构从哪里来、和谁有关，但单独拿出来不能当结论。",
            "Ten God, hidden stems, and elements work like relationship notes here: they tell where a structure comes from and what it relates to, but they are not standalone conclusions.",
            "십성, 지장간, 오행은 여기서 관계 설명서에 가깝습니다. 구조가 어디서 나오고 무엇과 관련되는지 말해 주지만, 단독 결론은 아닙니다.",
        ),
        "rule_basis": _l(
            "规则依据可以看成可读理由：用了哪些结构输入、命中了哪些事实、为什么足以支持这条回答。用户侧先看事实，不需要看编号。",
            "The rule basis can be shown, but users should see readable reasons: which structural inputs were used, which facts matched, and why they support the answer. Internal IDs stay in audit.",
            "규칙 근거는 볼 수 있지만 사용자에게는 읽을 수 있는 이유만 보여야 합니다. 어떤 구조 입력과 사실이 쓰였는지 설명하고 내부 ID는 감사에 남깁니다.",
        ),
        "structure_overview": _l(
            "只看结构时，先别急着问好坏。先把日主、月令、四柱地支、可见关系和时间背景摆清楚，后面的回答才不会跳步。",
            "When reading structure, do not start with good or bad. First lay out day master, month branch, pillar branches, visible relations, and time context so the answer does not skip steps.",
            "구조를 볼 때는 길흉부터 묻지 않습니다. 일간, 월지, 사주 지지, 보이는 관계와 시간 배경을 먼저 정리해야 답이 건너뛰지 않습니다.",
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
            _section("结果卡边界", "Result-card boundary", "결과 카드 경계", _boundary_items("time")),
        ]
    if answer_kind == "income_structure":
        return source_section + [
            _section("当前结构信号", "Current structural signals", "현재 구조 신호", _income_answer_items(income_bundle)),
            _section("结果卡边界", "Result-card boundary", "결과 카드 경계", _boundary_items("income")),
        ]
    if answer_kind == "strength_assessment":
        return source_section + [
            _section("强弱承载证据", "Strength-capacity evidence", "강약 수용 근거", _strength_answer_items(chart, facts, source_signal or {})),
            _section("回答边界", "Answer boundary", "답변 경계", _boundary_items("strength")),
        ]
    if answer_kind == "useful_god_boundary":
        return source_section + [
            _section("用神/忌神候选路径", "Useful/unfavorable-god candidate paths", "용신/기신 후보 경로", _useful_god_answer_items(chart, facts, source_signal or {})),
            _section("回答边界", "Answer boundary", "답변 경계", _boundary_items("useful_god")),
        ]
    if answer_kind == "pattern_structure":
        return source_section + [
            _section("格局结构入口", "Pattern structural entries", "격국 구조 입구", _pattern_answer_items(chart, facts, source_signal or {})),
            _section("回答边界", "Answer boundary", "답변 경계", _boundary_items("pattern")),
        ]
    if answer_kind == "career_structure":
        return source_section + [
            _section("事业结构路径", "Career structure path", "직업 구조 경로", _domain_answer_items("career_structure", source_signal or {})),
            _section("阅读边界", "Reading boundary", "읽기 경계", _boundary_items("career")),
        ]
    if answer_kind == "relationship_structure":
        return source_section + [
            _section("关系结构路径", "Relationship structure path", "관계 구조 경로", _domain_answer_items("relationship_structure", source_signal or {})),
            _section("阅读边界", "Reading boundary", "읽기 경계", _boundary_items("relationship")),
        ]
    if answer_kind == "health_structure":
        return source_section + [
            _section("健康结构路径", "Health structure path", "건강 구조 경로", _domain_answer_items("health_structure", source_signal or {})),
            _section("阅读边界", "Reading boundary", "읽기 경계", _boundary_items("health")),
        ]
    if answer_kind == "result_boundary":
        return source_section + [
            _section("如何读结果卡", "How to read the result card", "결과 카드 읽는 법", _result_boundary_items(income_bundle)),
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
            _l("这里用可读分类说明它属于哪一类结构。", "This names the readable structural category.", "읽을 수 있는 구조 분류로 표시합니다."),
        ),
    ]
    if observed:
        items.append(
            _item(
                _l("观察到的结构", "Observed structure", "관찰된 구조"),
                _l("、".join(observed), " / ".join(observed), " / ".join(observed)),
                _l("后续回答会围绕这些事实展开。", "The answer should stay around these observed facts.", "이 관찰 사실을 중심으로 답합니다."),
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
    relation_labels = [
        ("clashes", _relation_type_label("six_clash")),
        ("combinations", _relation_type_label("six_combination")),
        ("harm", _relation_type_label("harm")),
        ("break", _relation_type_label("break")),
        ("three_harmony", _relation_type_label("three_harmony")),
        ("three_meeting", _relation_type_label("three_meeting")),
    ]
    for key, relation_label in relation_labels:
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
            _l("它说明时间层也出现了可观察的墓库支，读法仍先看所在层级和藏干。", "It means a vault branch is visible in the timing layer; read its layer and hidden stems first.", "시간층에 관찰 가능한 묘고 지지가 보이며, 먼저 층위와 지장간을 봅니다."),
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
                _l("这里先只说明时间层有没有形成关系。", "This first names whether the timing layer forms a relation.", "먼저 시간층 관계 여부만 설명합니다."),
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
        items.append(_item(_l(zh, en, ko), _value_l(value), _l("来自当前结构信号汇总。", "Comes from the current structural signal summary.", "현재 구조 신호 요약에서 온 값입니다.")))
    return items


def _strength_answer_items(chart: Dict[str, Any], facts: Dict[str, Any], source_signal: Dict[str, Any]) -> List[Dict[str, Any]]:
    day_stem = str(facts.get("day_stem") or "")
    month_branch = str(facts.get("month_branch") or "")
    hidden = facts.get("hidden_stems_by_branch") if isinstance(facts.get("hidden_stems_by_branch"), dict) else {}
    hidden_text = "；".join(f"{branch}藏{'/'.join(str(stem) for stem in stems)}" for branch, stems in hidden.items() if stems)
    observed = "、".join(_plain_observed_values(source_signal.get("observed") or []))
    return [
        _item(_l("日主", "Day master", "일간"), _l(day_stem or "未见", day_stem or "not detected", day_stem or "감지 없음"), _l("它是强弱承载问题的观察中心。", "It is the observation center for strength-capacity questions.", "강약 수용 질문의 관찰 중심입니다.")),
        _item(_l("月令", "Month branch", "월지"), _l(month_branch or "未见", month_branch or "not detected", month_branch or "감지 없음"), _l("月令先提供季节和环境背景，不能单独推出强弱结论。", "The month branch gives seasonal/context evidence; it cannot decide strength alone.", "월지는 계절과 환경 근거를 제공하지만 단독으로 강약을 정하지 않습니다.")),
        _item(_l("藏干来源", "Hidden-stem sources", "지장간 출처"), _l(hidden_text or "未见可用藏干映射", hidden_text or "no hidden-stem mapping detected", hidden_text or "지장간 매핑 없음"), _l("藏干只补充来源层，不能替代完整强弱判断。", "Hidden stems supplement the source layer and do not replace full strength judgment.", "지장간은 출처층 보조이며 전체 강약 판단을 대체하지 않습니다.")),
        _item(_l("当前命中", "Current match", "현재 일치"), _l(observed or "日主/月令结构入口", observed or "day-master/month-command entry", observed or "일간/월령 구조 입구"), _l("这里只形成证据束，不输出身强身弱断语。", "This forms an evidence bundle, not a strong/weak verdict.", "근거 묶음만 만들며 강약 단정을 출력하지 않습니다.")),
    ]


def _useful_god_answer_items(chart: Dict[str, Any], facts: Dict[str, Any], source_signal: Dict[str, Any]) -> List[Dict[str, Any]]:
    elements = [str(item) for item in facts.get("all_stem_elements") or [] if str(item)]
    observed = "、".join(_plain_observed_values(source_signal.get("observed") or []))
    return [
        _item(_l("候选前提", "Candidate prerequisite", "후보 전제"), _l("先完成强弱承载证据", "Strength-capacity evidence first", "강약 수용 근거가 먼저 필요합니다"), _l("没有承载证据时，不直接给用神或忌神。", "Without capacity evidence, useful/unfavorable gods are not assigned directly.", "수용 근거 없이 용신·기신을 바로 정하지 않습니다.")),
        _item(_l("可见五行", "Visible elements", "보이는 오행"), _l("、".join(elements) if elements else "未见", ", ".join(elements) if elements else "none detected", ", ".join(elements) if elements else "감지 없음"), _l("这些只是候选素材，不等于喜忌结论。", "These are candidate materials, not favorable/unfavorable conclusions.", "이는 후보 자료일 뿐 희기 결론이 아닙니다.")),
        _item(_l("当前路径", "Current path", "현재 경로"), _l(observed or "强弱、调候、通关、扶抑都待证据确认", observed or "strength, seasonal balance, mediation, and support/control still require evidence", observed or "강약·조후·통관·부억은 근거 확인이 필요합니다"), _l("只回答候选路径和边界，不提供补救建议。", "Only candidate paths and boundaries are answered; no remedy advice is given.", "후보 경로와 경계만 답하고 처방 조언은 하지 않습니다.")),
    ]


def _pattern_answer_items(chart: Dict[str, Any], facts: Dict[str, Any], source_signal: Dict[str, Any]) -> List[Dict[str, Any]]:
    month_branch = str(facts.get("month_branch") or "")
    stems = [str(item) for item in facts.get("stems") or [] if str(item)]
    relation_types = sorted(str(item) for item in facts.get("relation_types") or [] if str(item))
    observed = "、".join(_plain_observed_values(source_signal.get("observed") or []))
    return [
        _item(_l("月令来源", "Month-command source", "월령 출처"), _l(month_branch or "未见", month_branch or "not detected", month_branch or "감지 없음"), _l("格局先看月令和结构来源。", "Pattern first checks month command and structural source.", "격국은 먼저 월령과 구조 출처를 봅니다.")),
        _item(_l("透出天干", "Visible stems", "투간"), _l("、".join(stems) if stems else "未见", ", ".join(stems) if stems else "none detected", ", ".join(stems) if stems else "감지 없음"), _l("透出只是成格条件的一部分。", "Visible stems are only part of formation conditions.", "투간은 성격 조건의 일부입니다.")),
        _item(_l("结构扰动", "Structural disturbance", "구조 교란"), _l("、".join(relation_types) if relation_types else "未见明确冲合刑害", ", ".join(relation_types) if relation_types else "no clear relations detected", ", ".join(relation_types) if relation_types else "명확한 관계 없음"), _l("冲合刑害可能影响成格或破格，但不能单独下结论。", "Relations may affect formation or breaking, but cannot decide alone.", "충합형해는 성격/파격에 영향을 줄 수 있지만 단독 결론은 아닙니다.")),
        _item(_l("当前索引", "Current index", "현재 색인"), _l(observed or "格局候选仍需同层条件验证", observed or "pattern candidate still needs same-layer validation", observed or "격국 후보는 같은 층 조건 검증이 필요합니다"), _l("这里只作为结构目录，不输出命运判断。", "This is a structural catalog only, not a fate judgement.", "구조 목록일 뿐 운명 판단이 아닙니다.")),
    ]


def _domain_answer_label(answer_kind: str) -> str:
    return {
        "career_structure": "事业结构",
        "relationship_structure": "关系结构",
        "health_structure": "健康结构",
    }.get(str(answer_kind or ""), "领域结构")


def _domain_answer_focus(answer_kind: str, knowledge_items: List[Dict[str, Any]], source_signal: Dict[str, Any]) -> str:
    observed = "、".join(_plain_observed_values(source_signal.get("observed") or []))
    domains = _dedupe_keep_order([str(row.get("domain") or "") for row in knowledge_items if str(row.get("domain") or "") and str(row.get("domain") or "") != "answer_expression"])
    if observed:
        basis = f"当前命中的结构事实是{observed}"
    elif domains:
        basis = "当前证据集中在" + "、".join(_domain_readable_name(item) for item in domains[:4])
    else:
        basis = "当前先取四柱、地支关系、十神和时间背景作为入口"
    detail = {
        "career_structure": "重点看约束关系、输出关系、承载力和格局线索有没有形成同一条解释路径。",
        "relationship_structure": "重点看关系符号、宫位线索、十神互动和时间层牵动是否只是结构连接。",
        "health_structure": "重点看承载力、偏枯、冲合牵动和时间层压力是否只是结构压力信号。",
    }.get(str(answer_kind or ""), "重点看结构事实是否足以支持当前问题。")
    return f"{basis}；{detail}"


def _domain_answer_boundary(answer_kind: str) -> str:
    return {
        "career_structure": "所以这里能回答“哪些事业相关结构值得先看”，不能回答职业成败、升迁时间或外部结果。",
        "relationship_structure": "所以这里能回答“关系结构从哪里出现、被什么牵动”，不能回答婚恋结果或具体事件。",
        "health_structure": "所以这里能回答“健康主题下有哪些结构压力或边界”，不能回答身体状态或医学结论。",
    }.get(str(answer_kind or ""), "所以这里只回答结构边界，不扩写成结果。")


def _domain_answer_items(answer_kind: str, source_signal: Dict[str, Any]) -> List[Dict[str, Any]]:
    observed = "、".join(_plain_observed_values(source_signal.get("observed") or []))
    configs = {
        "career_structure": [
            ("事业入口", "Career entry", "직업 입구", "官杀、食伤、财星和格局路径", "Constraints, output, wealth link, and pattern path", "관살, 식상, 재성 연결, 격국 경로"),
            ("可解释内容", "Explainable content", "설명 가능한 내용", "哪些结构因素支持这个问题被提出", "Which structural factors support asking this question", "이 질문을 제기하게 한 구조 요소"),
        ],
        "relationship_structure": [
            ("关系入口", "Relationship entry", "관계 입구", "关系符号、宫位线索、十神互动和时间牵动", "Relationship symbols, palace clues, Ten God interaction, and timing movement", "관계 기호, 궁위 단서, 십성 상호작용, 시간 작용"),
            ("可解释内容", "Explainable content", "설명 가능한 내용", "关系结构从哪里出现、在哪一层被牵动", "Where the relationship structure appears and which layer moves it", "관계 구조가 어디서 나타나고 어느 층에서 움직이는지"),
        ],
        "health_structure": [
            ("健康入口", "Health entry", "건강 입구", "承载力、偏枯、冲合牵动和时间层压力", "Capacity, imbalance, branch movement, and timing pressure", "수용력, 치우침, 충합 작용, 시간층 압력"),
            ("可解释内容", "Explainable content", "설명 가능한 내용", "哪些结构压力被看见，以及它们属于本命还是时间背景", "Which structural pressures are visible and whether they are natal or timing context", "어떤 구조 압력이 보이며 원국인지 시간 배경인지"),
        ],
    }
    rows = configs.get(str(answer_kind or ""), [])
    items = [
        _item(_l(zh, en, ko), _l(value_zh, value_en, value_ko), _l("只作为结构阅读路径。", "Used only as a structural reading path.", "구조 읽기 경로로만 사용됩니다."))
        for zh, en, ko, value_zh, value_en, value_ko in rows
    ]
    if observed:
        items.insert(0, _item(_l("当前命中", "Current match", "현재 일치"), _l(observed, observed, observed), _l("来自当前问题背后的结构信号。", "Comes from the structural signal behind the current question.", "현재 질문 뒤의 구조 신호에서 온 값입니다.")))
    return items or [_item(_l("结构入口", "Structural entry", "구조 입구"), _l("四柱、关系、时间背景", "Pillars, relations, and timing context", "사주, 관계, 시간 배경"), _l("只说明阅读顺序。", "Only explains reading order.", "읽기 순서만 설명합니다."))]


def _domain_readable_name(domain: str) -> str:
    return {
        "career": "事业",
        "relationship": "关系",
        "health": "健康",
        "wealth": "财富",
        "ten_god": "十神",
        "interaction": "结构互动",
        "pattern": "格局",
        "core_structure": "基础结构",
        "strength": "强弱承载",
        "luck_flow": "时间背景",
        "palace": "宫位",
    }.get(str(domain or ""), str(domain or "结构"))


def _result_boundary_items(income_bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    signals = _income_signal_map(income_bundle)
    return [
        _item(_l("结果卡用途", "Purpose of result card", "결과 카드의 용도"), _l("展示当前支持主题的结构摘要", "Shows a structure summary for the currently supported topic", "현재 지원 영역의 구조 요약을 표시합니다"), _l("它不是对每个引导问题的完整回答。", "It is not the complete answer to every guided question.", "모든 안내 질문에 대한 전체 답변은 아닙니다.")),
        _item(_l("当前摘要值", "Current summary value", "현재 요약값"), _value_l(str(signals.get("income_stability") or "unknown")), _l("这个值来自收入稳定性结构信号。", "This value comes from the income-stability structural signal.", "이 값은 소득 안정성 구조 신호에서 온 것입니다.")),
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
        _item(_l("可读依据", "Readable basis", "읽을 수 있는 근거"), _l("结构输入和事实摘要", "Structural input and fact summary", "구조 입력과 사실 요약"), _l("用户侧先看事实，不需要看编号。", "Users can read the facts without IDs.", "사용자는 번호 없이 사실을 볼 수 있습니다.")),
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
        items.append(_item(category, _l(value, value, value), _l("这解释为什么这个问题值得问。", "This explains why the question is worth asking.", "이 질문을 추천한 이유를 설명합니다.")))
    if not items:
        items.append(_item(_l("推荐背景", "Recommendation background", "추천 배경"), _l("来自当前命盘结构预览", "From the current chart-structure preview", "현재 명식 구조 미리보기에서 옴"), _l("用于引导提问。", "Used to guide questions.", "질문 안내에 사용됩니다.")))
    return items


def _boundary_items(kind: str) -> List[Dict[str, Any]]:
    common = _item(
        _l("当前边界", "Current boundary", "현재 경계"),
        _l("结构解释，不是预测", "Structural explanation, not prediction", "구조 설명이며 예측 아님"),
        _l("不输出好坏、财富得失、今年运势等判断。", "No good/bad, wealth gain/loss, or this-year fortune judgement is produced.", "길흉, 재물 득실, 올해 운세 판단을 출력하지 않습니다."),
    )
    result = _item(
        _l("和结果卡的关系", "Relation to result card", "결과 카드와의 관계"),
        _l("先解释当前问题", "Explains the current question first", "현재 질문을 먼저 설명"),
        _l("如果要看收入稳定性，应回到对应结果卡和它自己的结构证据。", "For income stability, read the dedicated result card and its own structural evidence.", "소득 안정성은 해당 결과 카드와 자체 구조 근거에서 확인합니다."),
    )
    if kind == "time":
        return [result, common]
    if kind == "strength":
        return [
            _item(_l("强弱边界", "Strength boundary", "강약 경계"), _l("证据束，不是一句断语", "Evidence bundle, not a one-line verdict", "근거 묶음이며 단정문 아님"), _l("强弱要看月令、透藏、根气、克泄耗和扶助是否共同成立。", "Strength requires month command, visible/hidden sources, roots, pressure, and support to align.", "강약은 월령, 투장, 뿌리, 압력과 지지가 함께 성립해야 합니다.")),
            common,
        ]
    if kind == "useful_god":
        return [
            _item(_l("用神边界", "Useful-god boundary", "용신 경계"), _l("候选路径，不是补救建议", "Candidate path, not remedy advice", "후보 경로이며 처방 조언 아님"), _l("没有完整结构证据时，不输出喜用、忌神或补救建议。", "Without full structural evidence, no favorable/unfavorable-god or remedy advice is output.", "완전한 구조 근거 없이 희용·기신이나 처방 조언을 출력하지 않습니다.")),
            common,
        ]
    if kind == "pattern":
        return [
            _item(_l("格局边界", "Pattern boundary", "격국 경계"), _l("结构索引，不是命运判断", "Structural index, not fate judgement", "구조 색인이며 운명 판단 아님"), _l("格局名必须回到月令、透干、藏干和破格条件里验证。", "Pattern names must be validated against month command, visible stems, hidden stems, and breaking factors.", "격국명은 월령, 투간, 지장간, 파격 조건으로 검증해야 합니다.")),
            common,
        ]
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
    if normalized == "three_harmony":
        return _l("三合", "Three harmony", "삼합")
    if normalized == "three_meeting":
        return _l("三会", "Three meeting", "삼회")
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
        "ten_god_interaction": _l("十神组合", "Ten-God interaction", "십성 조합"),
        "hidden_stem": _l("藏干结构", "Hidden-stem structure", "지장간 구조"),
        "five_element_relation": _l("五行关系", "Five-element relation", "오행 관계"),
        "stem_relation": _l("天干关系", "Stem relation", "천간 관계"),
        "strength_model": _l("日主环境证据", "Day-master context evidence", "일간 환경 근거"),
        "structure_anchor": _l("结构基点", "Structure anchor", "구조 기준점"),
        "time_boundary": _l("时间结构边界", "Time boundary", "시간 구조 경계"),
        "wealth_boundary": _l("财星边界", "Wealth-star boundary", "재성 경계"),
        "adapter_boundary": _l("规则信号边界", "Rule-signal boundary", "규칙 신호 경계"),
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
    if category in {"core_symbol", "stem_branch_attribute", "hidden_stem", "five_element_relation", "stem_relation", "strength_model", "useful_god", "useful_god_boundary"} or domain in {"strength", "useful_god", "day_master_element"}:
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
    source_rule_category = str(signal.get("source_rule_category") or "")
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
                    "zh": "当前命中的冲合关系，哪些发生在命盘或时间背景，它们在结构层代表什么？",
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
    elif category == "strength_model" or domain in {"strength", "day_master_element"}:
        questions.append(
            _question(
                "q_strength_assessment",
                "strength_structure",
                "beginner",
                92,
                {
                    "zh": "这个八字的日主强弱，应该先看哪些结构证据？",
                    "en": "Which structural evidence comes first for day-master strength?",
                    "ko": "이 사주의 일간 강약은 어떤 구조 근거를 먼저 봐야 하나요?",
                },
                signal,
                ["q_day_master_month_anchor", "q_month_command_anchor", "q_useful_god_candidates"],
            )
        )
    elif category in {"useful_god", "useful_god_boundary"} or domain == "useful_god":
        questions.append(
            _question(
                "q_useful_god_candidates",
                "useful_god_boundary",
                "intermediate",
                90,
                {
                    "zh": "这张命盘的用神忌神，当前只能先形成哪些候选路径？",
                    "en": "What useful or unfavorable-god candidate paths can be formed now?",
                    "ko": "이 명식의 용신·기신은 현재 어떤 후보 경로로만 볼 수 있나요?",
                },
                signal,
                ["q_strength_assessment", "q_favorable_elements_boundary", "q_unfavorable_god_boundary"],
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
    elif category == "ten_god_interaction":
        observed = "、".join(_signal_observed_values(signal)[:4]) or "十神组合"
        questions.append(
            _question(
                "kbq_ten_god_interaction_boundary",
                "structure_basis",
                "intermediate",
                88,
                {
                    "zh": f"当前命中的{observed}，应该如何只按结构层阅读？",
                    "en": "How should this Ten-God interaction be read at the structural layer only?",
                    "ko": "현재 확인된 십성 조합은 구조층에서만 어떻게 읽어야 하나요?",
                },
                signal,
                ["q_ten_god_metadata", "q_signal_combination", "q_read_result_not_fortune"],
            )
        )
    elif category == "structure_anchor":
        questions.append(
            _question(
                "kbq_structure_anchor_chain",
                "structure_basis",
                "beginner",
                86,
                {
                    "zh": "这张命盘应该先从日主、月令和四柱位置怎样建立结构基点？",
                    "en": "How should this chart establish its structural baseline from day master, month command, and pillar positions?",
                    "ko": "이 명식은 일간, 월령, 사주 위치에서 구조 기준을 어떻게 세워야 하나요?",
                },
                signal,
                ["q_day_master_month_anchor", "q_month_command_anchor", "q_structure_overview"],
            )
        )
    elif category in {"time_boundary", "timing_context"}:
        questions.append(
            _question(
                "kbq_time_layer_boundary",
                "time_context",
                "beginner",
                82,
                {
                    "zh": "当前大运或流年属于哪一层时间背景，为什么不直接改结果？",
                    "en": "Which time-context layer does the current luck or flow year belong to, and why does it not directly change the result?",
                    "ko": "현재 대운 또는 세운은 어떤 시간 배경층이며 왜 결과를 직접 바꾸지 않나요?",
                },
                signal,
                ["q_time_context_boundary", "q_time_not_inference", "q_luck_flow_layers"],
            )
        )
    elif category == "wealth_boundary":
        questions.append(
            _question(
                "kbq_wealth_metadata_boundary",
                "income_stability",
                "intermediate",
                74,
                {
                    "zh": "财星在这里为什么先读作关系元数据，而不是财富断语？",
                    "en": "Why is the wealth star read first as relationship metadata here, not a wealth verdict?",
                    "ko": "여기서 재성은 왜 재물 단정이 아니라 관계 메타데이터로 먼저 읽나요?",
                },
                signal,
                ["q_ten_god_metadata", "q_income_path_structure", "q_read_result_not_fortune"],
            )
        )
    elif domain == "income_stability":
        if source_rule_category in {"income_path", "wealth_path"}:
            questions.append(
                _question(
                    "kbq_income_path_route",
                    "income_stability",
                    "intermediate",
                    86,
                    {
                        "zh": "当前命中的收入路径线索，如何只作为结构转换路径阅读？",
                        "en": "How should the matched income-path clue be read only as a structural conversion path?",
                        "ko": "현재 확인된 소득 경로 단서는 구조 전환 경로로만 어떻게 읽어야 하나요?",
                    },
                    signal,
                    ["q_income_path_structure", "q_income_factors", "follow_rule_basis"],
                )
            )
        elif source_rule_category in {"income_collision", "wealth_collision", "income_constraint"}:
            questions.append(
                _question(
                    "kbq_income_collision_route",
                    "income_stability",
                    "intermediate",
                    86,
                    {
                        "zh": "当前命中的收入牵制线索，如何只作为稳定性归因而不是财富断语？",
                        "en": "How should the matched income-constraint clue be used only as stability attribution, not a wealth verdict?",
                        "ko": "현재 확인된 소득 제약 단서는 재물 단정이 아니라 안정성 귀인으로만 어떻게 써야 하나요?",
                    },
                    signal,
                    ["q_signal_combination", "q_income_factors", "follow_rule_basis"],
                )
            )
        elif source_rule_category in {"wealth_boundary", "wealth_feature", "wealth_mechanism"}:
            questions.append(
                _question(
                    "kbq_wealth_access_route",
                    "income_stability",
                    "intermediate",
                    84,
                    {
                        "zh": "当前命中的财星可见性或可达性线索，如何只作为收入结构证据？",
                        "en": "How should the matched wealth visibility or accessibility clue be used only as income-structure evidence?",
                        "ko": "현재 확인된 재성의 가시성 또는 접근성 단서는 소득 구조 근거로만 어떻게 써야 하나요?",
                    },
                    signal,
                    ["q_wealth_accessibility", "q_income_factors", "follow_rule_basis"],
                )
            )
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
        "source_signal_category": signal.get("category") or "",
        "source_rule_category": signal.get("source_rule_category") or "",
        "source_topic_lane": signal.get("topic_lane") or "",
        "source_framework_state": signal.get("framework_state") or "",
        "source_engine_enabled": signal.get("engine_enabled") is True,
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
        "strength_assessment": (["chart_anchor", "month_branch", "hidden_stems", "stem_elements"], "explain_day_master_strength_as_evidence_bundle_not_verdict"),
        "useful_god_boundary": (["chart_anchor", "month_branch", "hidden_stems", "stem_elements", "relations"], "explain_useful_god_as_candidate_path_requiring_strength_and_structure_gate"),
        "pattern_structure": (["chart_anchor", "month_branch", "hidden_stems", "relations"], "explain_pattern_as_structure_index_not_fate_verdict"),
        "metadata_boundary": (["chart_anchor", "hidden_stems"], "explain_metadata_boundary"),
        "result_boundary": (["income_signals", "guardrails"], "explain_result_boundary"),
        "rule_basis": (["source_signal", "observed_facts"], "explain_rule_basis"),
        "structure_overview": (["chart_anchor", "relations", "vaults"], "summarize_visible_structure_only"),
    }
    required_facts, answer_scope = fallback.get(kind, fallback["structure_overview"])
    return {"intent": kind, "required_facts": required_facts, "answer_scope": answer_scope}


def _dedupe_questions(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_key: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        key = str(row.get("key") or "")
        if not key:
            continue
        current = by_key.get(key)
        if not current or _question_preference(row) > _question_preference(current):
            by_key[key] = row
    return list(by_key.values())


def _question_preference(row: Dict[str, Any]) -> Tuple[int, int, int]:
    source = str(row.get("source") or "")
    source_rank = {
        "rule_db_dynamic_question": 4,
        "structural_rule_signal": 3,
        "baseline_question_fallback": 2,
        "rule_graph_dynamic_question": 1,
        "question_registry": 1,
    }.get(source, 0)
    return (_question_source_match_rank(row), int(row.get("personalized_score") or row.get("score") or 0), source_rank)


def _question_source_match_rank(row: Dict[str, Any]) -> int:
    key = str(row.get("key") or "")
    category = str(row.get("source_signal_category") or "")
    signal_id = str(row.get("source_signal_id") or "")
    source_blob = f"{category} {signal_id}"
    rank = 0
    if "hidden_stem" in key and ("hidden_stem" in source_blob or "hidden_stems" in source_blob):
        rank = 8
    elif "ten_god" in key and "ten_god" in source_blob:
        rank = 8
    elif "month_command" in key and ("structure_anchor" in source_blob or "strength_model" in source_blob):
        rank = 8
    elif "day_master" in key and ("structure_anchor" in source_blob or "strength_model" in source_blob):
        rank = 8
    elif "vault" in key and "vault" in source_blob:
        rank = 8
    elif any(token in key for token in ["branch_relation", "combination", "harmony", "disruption"]) and "branch_relation" in source_blob:
        rank = 8
    elif "time" in key and ("timing_context" in source_blob or "time" in source_blob):
        rank = 8
    elif ("income" in key or "wealth" in key) and ("wealth" in source_blob or "income" in source_blob):
        rank = 8
    elif row.get("source") == "baseline_question_fallback":
        rank = 2
    if row.get("source") == "rule_graph_dynamic_question":
        return min(rank, 1)
    return rank


def _rank_questions_for_chart(rows: List[Dict[str, Any]], personalization_context: Dict[str, Any] | None = None, limit: int = 10) -> List[Dict[str, Any]]:
    sorted_rows = sorted(rows, key=lambda row: _question_runtime_preference(row, personalization_context), reverse=True)
    selected: List[Dict[str, Any]] = []
    used = set()
    bucket_counts: Dict[str, int] = {}
    category_counts: Dict[str, int] = {}

    for row in sorted_rows:
        if len(selected) >= min(limit, 5):
            break
        key = row.get("key")
        if key in used or _question_effective_specificity_score(row, personalization_context) < 18:
            continue
        bucket = _question_bucket(row)
        category = _question_category_key(row)
        if bucket_counts.get(bucket, 0) >= 2:
            continue
        if category_counts.get(category, 0) >= 1:
            continue
        selected.append(row)
        used.add(key)
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1

    anchor_keys = [
        "kbq_income_collision_route",
        "kbq_income_path_route",
        "kbq_wealth_access_route",
        "q_strength_assessment",
        "q_useful_god_candidates",
        "q_pattern_structure",
        "q_income_stability",
        "q_branch_relation_detail",
        "kbq_vault_structure",
        "kbq_ten_god_interaction_boundary",
        "q_ten_god_focus",
        "kbq_time_vs_natal_relation",
        "q_month_command_anchor",
        "q_ten_god_metadata",
        "q_hidden_stem_role",
    ]
    for key in anchor_keys:
        if not _anchor_question_allowed_by_portrait(key, personalization_context):
            continue
        pick = next((row for row in sorted_rows if row.get("key") == key and row.get("key") not in used), None)
        if pick:
            selected.append(pick)
            used.add(pick.get("key"))
            bucket = _question_bucket(pick)
            bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
        if len(selected) >= limit:
            break

    for row in sorted_rows:
        if row.get("key") in used:
            continue
        bucket = _question_bucket(row)
        if bucket_counts.get(bucket, 0) >= 3 and len(selected) < limit - 2:
            continue
        selected.append(row)
        used.add(row.get("key"))
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
        if len(selected) >= limit:
            break
    return selected


def _anchor_question_allowed_by_portrait(key: str, personalization_context: Dict[str, Any] | None) -> bool:
    vectors = dict((personalization_context or {}).get("portrait_vector_summary") or {})
    if key in {"kbq_wealth_access_route", "kbq_income_path_route"} and vectors:
        return float(vectors.get("wealth_visibility") or 0) >= 0.2
    return True


def _question_runtime_preference(row: Dict[str, Any], personalization_context: Dict[str, Any] | None = None) -> Tuple[int, int, int, int, int]:
    specificity = _question_effective_specificity_score(row, personalization_context)
    return (
        _question_bucket_priority(row, personalization_context),
        specificity,
        _question_source_match_rank(row),
        int(row.get("personalized_score") or row.get("score") or 0),
        _question_source_priority(row),
    )


def _question_effective_specificity_score(row: Dict[str, Any], personalization_context: Dict[str, Any] | None = None) -> int:
    specificity = _question_specificity_score(row)
    vectors = dict((personalization_context or {}).get("portrait_vector_summary") or {})
    key = str(row.get("key") or "")
    if (key.startswith("kbq_wealth") or key in {"kbq_income_path_route"}) and vectors and float(vectors.get("wealth_visibility") or 0) < 0.2:
        specificity -= 24
    return specificity


def _question_bucket_priority(row: Dict[str, Any], personalization_context: Dict[str, Any] | None = None) -> int:
    bucket = _question_bucket(row)
    order = [str(item) for item in (personalization_context or {}).get("route_bucket_order") or [] if str(item)]
    if bucket in order:
        return max(1, 30 - order.index(bucket) * 3)
    return 0


def _question_category_key(row: Dict[str, Any]) -> str:
    return str(row.get("source_rule_category") or row.get("source_signal_category") or _question_bucket(row) or row.get("key") or "")


def _question_source_priority(row: Dict[str, Any]) -> int:
    return {
        "structural_rule_signal": 6,
        "rule_db_dynamic_question": 5,
        "rule_graph_dynamic_question": 4,
        "baseline_question_fallback": 2,
        "question_registry": 1,
    }.get(str(row.get("source") or ""), 0)


def _question_specificity_score(row: Dict[str, Any]) -> int:
    key = str(row.get("key") or "")
    category = str(row.get("source_signal_category") or "")
    source_rule_category = str(row.get("source_rule_category") or "")
    signal_id = str(row.get("source_signal_id") or "")
    source = str(row.get("source") or "")
    observed = [str(item) for item in row.get("observed") or [] if str(item)]
    bucket = _question_bucket(row)
    score = 0
    if observed:
        score += 14 + min(10, len(observed) * 2)
    if signal_id:
        score += 10
    if source == "structural_rule_signal":
        score += 10
    elif source == "rule_db_dynamic_question":
        score += 7
    elif source == "baseline_question_fallback":
        score -= 8
    if category in {"branch_relation", "hidden_stem", "vault", "ten_god_interaction", "timing_context", "wealth_metadata", "wealth_boundary", "wealth_feature", "wealth_mechanism"}:
        score += 8
    if source_rule_category in {"income_path", "income_collision", "wealth_boundary", "wealth_feature", "wealth_mechanism"}:
        score += 16
    if bucket in {"branch_relation", "time_context", "metadata", "ten_god_interaction"}:
        score += 4
    if bucket == "vault":
        score += 2 if len(observed) >= 2 else -4
    if key in {"q_strength_assessment", "q_useful_god_candidates", "q_pattern_structure"}:
        score += 20
    if key == "q_ten_god_focus":
        score += 16
    if key in {"q_structure_overview", "kbq_structure_anchor_chain"} and not observed:
        score -= 8
    if key == "q_income_stability":
        score += 6
    return score


def _question_bucket(row: Dict[str, Any]) -> str:
    key = str(row.get("key") or "")
    theme = str(row.get("theme") or "")
    intent = str(row.get("intent") or "")
    answer_scope = str(row.get("answer_scope") or "")
    category = str(row.get("source_signal_category") or "")
    if category == "ten_god_interaction":
        return "ten_god_interaction"
    if "vault" in key or intent == "vault" or "vault" in answer_scope:
        return "vault"
    if "branch_relation" in key or intent == "branch_relation" or "combination" in key or "harmony" in key:
        return "branch_relation"
    if theme == "time_context" or "time" in key or intent == "time_boundary":
        return "time_context"
    if theme == "income_stability" or "income" in key or "wealth" in key:
        return "income_stability"
    if key in {"q_strength_assessment", "q_useful_god_candidates", "q_unfavorable_god_boundary", "q_favorable_elements_boundary"} or theme in {"strength_structure", "useful_god_boundary"} or intent in {"strength_assessment", "useful_god_boundary"}:
        return "strength_useful_god"
    if key == "q_pattern_structure" or theme == "pattern_structure" or intent == "pattern_structure":
        return "pattern_structure"
    if intent == "metadata_boundary" or any(token in key for token in ["hidden", "ten_god", "month_command", "day_master", "metadata"]):
        return "metadata"
    if theme == "boundary" or intent == "result_boundary":
        return "boundary"
    return "structure_basis"


def _route_bucket_order(lane_counts: Dict[str, int], facts: Dict[str, Any]) -> List[str]:
    lane_to_buckets = {
        "branch_time_activation": ["branch_relation", "time_context", "vault"],
        "ten_god_mechanism": ["ten_god_interaction", "metadata", "income_stability", "structure_basis"],
        "wealth_career_bridge": ["income_stability", "metadata", "structure_basis"],
        "core_strength_foundation": ["strength_useful_god", "metadata", "structure_basis"],
        "pattern_structure": ["pattern_structure", "strength_useful_god", "structure_basis", "boundary"],
        "blind_lifa_palace": ["vault", "branch_relation", "structure_basis"],
    }
    ordered: List[str] = []
    for lane, _count in sorted(lane_counts.items(), key=lambda item: (-int(item[1] or 0), str(item[0]))):
        for bucket in lane_to_buckets.get(str(lane), []):
            if bucket not in ordered:
                ordered.append(bucket)
    if facts.get("has_branch_relation"):
        _prepend_once(ordered, "branch_relation")
    if facts.get("has_time_relation") and "time_context" not in ordered:
        ordered.insert(min(3, len(ordered)), "time_context")
    if facts.get("has_vault") or facts.get("flow_is_vault") or facts.get("luck_is_vault"):
        if not facts.get("has_time_relation") and not facts.get("has_branch_relation"):
            _prepend_once(ordered, "vault")
        elif "vault" not in ordered:
            ordered.insert(min(2, len(ordered)), "vault")
    for bucket in ["strength_useful_god", "income_stability", "metadata", "structure_basis", "boundary"]:
        if bucket not in ordered:
            ordered.append(bucket)
    return ordered[:7]


def _prepend_once(rows: List[str], value: str) -> None:
    if value in rows:
        rows.remove(value)
    rows.insert(0, value)


def _category_matches_route(category: str, lane_counts: Dict[str, int], domain_counts: Dict[str, int]) -> bool:
    active_lanes = {str(key) for key, value in lane_counts.items() if int(value or 0) > 0}
    active_domains = {str(key) for key, value in domain_counts.items() if int(value or 0) > 0}
    if category in {"wealth_feature", "wealth_mechanism", "wealth_boundary"}:
        return bool(active_lanes & {"wealth_career_bridge", "ten_god_mechanism"} or active_domains & {"wealth", "income_stability"})
    if category in {"branch_relation", "timing_context", "vault"}:
        return "branch_time_activation" in active_lanes or "luck_flow" in active_domains
    if category in {"ten_god", "ten_god_interaction", "hidden_stem", "hidden_stems"}:
        return "ten_god_mechanism" in active_lanes or active_domains & {"ten_god", "interaction"}
    if category in {"strength_model", "structure_anchor", "stem_branch_attribute", "five_element_relation"}:
        return "core_strength_foundation" in active_lanes or active_domains & {"core_structure", "five_element", "strength"}
    if category in {"pattern_structure", "core_symbol"}:
        return bool(active_lanes & {"pattern_structure", "core_strength_foundation"})
    return False


def _count_values(values: Iterable[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for value in values:
        clean = str(value or "")
        if not clean:
            continue
        counts[clean] = counts.get(clean, 0) + 1
    return counts


def _has_three_harmony(branches: List[str]) -> bool:
    present = set(branches)
    return any(set(group) <= present for group in THREE_HARMONIES)


def _has_three_meeting(branches: List[str]) -> bool:
    present = set(branches)
    return any(set(group) <= present for group in THREE_MEETINGS)


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
    if raw_type in {"six_combination", "combination", "combinations"}:
        return "combination"
    if raw_type in {"three_harmony"}:
        return "three_harmony"
    if raw_type in {"three_meeting"}:
        return "three_meeting"
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
