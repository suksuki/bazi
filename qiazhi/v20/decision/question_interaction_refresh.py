from __future__ import annotations

from collections.abc import Callable

from v20.features.schema import FeatureLayer
from v20.interaction.questions import QuestionCandidate
from v20.decision.question_config import CONTROL_DOMAIN, LATENT_SCENARIO_DOMAIN, QUESTION_STRATEGY


MakeQuestion = Callable[
    [str, str, str, float, FeatureLayer, dict[str, object] | None, str, str],
    QuestionCandidate,
]
AlignQuestion = Callable[[QuestionCandidate], QuestionCandidate | None]


def practitioner_selection_questions(
    selections: tuple[dict[str, object], ...],
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
    *,
    make_question: MakeQuestion,
    align_question: AlignQuestion,
) -> list[QuestionCandidate]:
    rows = []
    decisions = [row for row in decision_report.get("decisions", ()) if isinstance(row, dict)]
    for index, selection in enumerate(selections[:4]):
        control_key = str(selection.get("control_key", ""))
        option = str(selection.get("option", ""))
        domain = CONTROL_DOMAIN.get(control_key, "branch")
        question_key, title = _practitioner_question(control_key, option)
        source_decision_keys = tuple(str(row) for row in selection.get("source_decision_keys", ()) if str(row))
        source_decision = _source_decision_for_selection(decisions, source_decision_keys, domain)
        candidate = make_question(
            question_key,
            title,
            domain,
            round(1.2 - index * 0.03, 3),
            feature_layer,
            source_decision,
            QUESTION_STRATEGY["practitioner_refresh"],
            "practitioner_refresh",
        )
        aligned = align_question(candidate)
        if aligned:
            rows.append(aligned)
    return rows


def latent_event_questions(
    answers: tuple[dict[str, object], ...],
    decision_report: dict[str, object],
    feature_layer: FeatureLayer,
    *,
    make_question: MakeQuestion,
    align_question: AlignQuestion,
) -> list[QuestionCandidate]:
    rows = []
    decisions = [row for row in decision_report.get("decisions", ()) if isinstance(row, dict)]
    for index, answer in enumerate(answers[:4]):
        scenario_id = str(answer.get("scenario_id", ""))
        domain = LATENT_SCENARIO_DOMAIN.get(scenario_id, "")
        if not domain:
            continue
        question_key, title = _latent_event_question(scenario_id, str(answer.get("result_option", "")))
        source_decision = _source_decision_for_selection(decisions, tuple(), domain)
        candidate = make_question(
            question_key,
            title,
            domain,
            round(1.12 - index * 0.03, 3),
            feature_layer,
            source_decision,
            QUESTION_STRATEGY["latent_event"],
            "",
        )
        aligned = align_question(candidate)
        if aligned:
            rows.append(aligned)
    return rows


def _latent_event_question(scenario_id: str, result_option: str) -> tuple[str, str]:
    if scenario_id == "latent.wealth_change":
        if result_option in {"income_down", "resource_pressure"}:
            return "q_income_stability", "财务压力出现时，命局里先看承载力还是外部牵动？"
        return "q_income_factors", "财务变化明显时，命局里哪些线索最容易被放大？"
    if scenario_id == "latent.career_transition":
        return "q_career_structure", "职业变化明显时，事业主线先看规则、平台还是表达？"
    if scenario_id == "latent.relationship_shift":
        return "q_relationship_structure", "关系变化明显时，命局里先看互动、约束还是承接？"
    if scenario_id == "latent.relocation_environment":
        return "q_time_layer_context", "环境变化明显时，大运流年会先牵动哪条结构线？"
    if scenario_id == "latent.stress_recovery":
        return "q_health_balance_boundary", "压力恢复节奏明显时，命局里先看哪类平衡边界？"
    if scenario_id == "latent.action_result":
        return "q_strength_assessment", "行动结果节奏明显时，先看日主承载还是资源支持？"
    return "q_structure_overview", "结合人生节点后，这个八字先复核哪条主线？"


def _source_decision_for_selection(
    decisions: list[dict[str, object]],
    source_decision_keys: tuple[str, ...],
    domain: str,
) -> dict[str, object] | None:
    for decision in decisions:
        if source_decision_keys and str(decision.get("decision_key", "")) in source_decision_keys:
            return decision
    for decision in decisions:
        if str(decision.get("domain", "")) == domain:
            return decision
    return None


def _practitioner_question(control_key: str, option: str) -> tuple[str, str]:
    if control_key == "control.day_master_strength":
        return "q_strength_assessment", f"命理师判为「{option}」后，下一步先看扶助还是泄耗？"
    if control_key == "control.shang_guan_jian_guan":
        if option == "成立":
            return "q_career_structure", "伤官见官已判成立，先看冲突来源还是化解路径？"
        if option == "被印化":
            return "q_career_structure", "印星能否化解表达冲规则？"
        if option == "被财通关":
            return "q_income_factors", "财星能不能把表达和规则通起来？"
        if option == "不成立":
            return "q_career_structure", "不取伤官见官后，事业主线改看哪里？"
        return "q_career_structure", f"伤官见官判为「{option}」后，事业先复核哪条线？"
    if control_key == "control.wealth_capacity":
        if option == "需扶身":
            return "q_income_stability", "财运要先扶身，还是先看财星来源？"
        if option == "走通关":
            return "q_useful_god_candidates", "财运通关路径应该先看哪一类用神？"
        if option == "看大运":
            return "q_time_layer_context", "财运要不要先看大运流年是否接力？"
        return "q_income_factors", f"财星承载判为「{option}」后，机会和限制在哪里？"
    if control_key == "control.pattern_status":
        if option in {"成格", "破格"}:
            return "q_pattern_structure", f"格局判为「{option}」后，最关键的成败点是什么？"
        return "q_pattern_structure", f"格局仍是「{option}」时，先复核哪几个条件？"
    return "q_structure_overview", "命理师裁决后，下一步先复核哪条结构主线？"
