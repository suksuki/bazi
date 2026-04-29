from __future__ import annotations

from v19.agent.income_stability import derive_income_stability
from v19.agent.renderers import render_income_stability_answer
from v19.agent.structure import build_agent_turn
from v19.bazi_guided_questions import build_guided_question_answer, build_guided_question_context, guided_answer_to_plain_text
from v19.bazi_rule_db import build_structural_rule_signals
from v19.knowledge_store import retrieve_knowledge
from v19.lab_interfaces import _default_label_contract


def _agent_data(message: str) -> dict:
    result = build_agent_turn(
        {
            "birth_input": {
                "year": 1990,
                "month": 4,
                "day": 15,
                "hour": 9,
                "minute": 0,
                "gender": "male",
                "calendar_type": "solar",
            },
            "selected_year": 2026,
            "message": message,
        }
    )
    data = dict(result["data"])
    data["inference_context"] = {
        "supported_theme": "income_stability",
        "income_stability": derive_income_stability(data["chart"]),
        "guardrails": [],
    }
    data["knowledge_context"] = retrieve_knowledge(data, message)
    data["guided_question_context"] = build_guided_question_context(data)
    return data


def test_p10_month_command_knowledge_reaches_answer_text() -> None:
    message = "月令在这张命盘里先提供了什么结构背景？"
    answer = build_guided_question_answer(_agent_data(message), "q_month_command_anchor", message)
    text = guided_answer_to_plain_text(answer, "zh")

    assert answer["source_signal_category"] == "strength_model"
    assert "p10.month_command_season_not_verdict" in {row["knowledge_id"] for row in answer["applied_knowledge"]}
    assert "月令不能单独推出身强、身弱或好坏" in text
    assert "income_stability" not in text
    assert "rule_id" not in text
    assert "signal_id" not in text


def test_p10_ten_god_and_hidden_stem_questions_keep_their_focus() -> None:
    ten_god_message = "十神标签在这里为什么只是关系元数据，而不是断语？"
    ten_god_answer = build_guided_question_answer(_agent_data(ten_god_message), "q_ten_god_metadata", ten_god_message)
    ten_god_text = guided_answer_to_plain_text(ten_god_answer, "zh")
    ten_god_ids = {row["knowledge_id"] for row in ten_god_answer["applied_knowledge"]}

    assert ten_god_answer["source_signal_category"] == "ten_god"
    assert {"p10.ten_god_five_family_plain_language", "p10.ten_god_visible_hidden_boundary"} <= ten_god_ids
    assert "五类关系" in ten_god_text
    assert "藏干层面" in ten_god_text

    hidden_message = "藏干在这张命盘里只是补充信息，还是会影响结构理解？"
    hidden_answer = build_guided_question_answer(_agent_data(hidden_message), "q_hidden_stem_role", hidden_message)
    hidden_text = guided_answer_to_plain_text(hidden_answer, "zh")

    assert hidden_answer["source_signal_category"] == "hidden_stem"
    assert "p10.branch_hidden_stem_complete_mapping" in {row["knowledge_id"] for row in hidden_answer["applied_knowledge"]}
    assert "直接透出，还是藏在地支里面" in hidden_text


def test_rule_db_structured_branch_rules_do_not_cross_trigger() -> None:
    data = _agent_data("当前看得到的冲合关系，分别发生在本命还是时间背景？")
    rules = [
        _branch_rule("sample.six_clash", {"pairs": [["辰", "戌"]]}),
        _branch_rule("sample.six_combination", {"pairs": [["午", "未"]]}),
        _branch_rule("sample.six_harm", {"six_harm": [["子", "未"]]}),
    ]

    report = build_structural_rule_signals(data["chart"], data["time_context"], data["inference_context"], rules=rules)
    by_id = {row["knowledge_id"]: row for row in report["signals"]}

    assert by_id["sample.six_clash"]["observed"] == ["戌辰"]
    assert by_id["sample.six_combination"]["observed"] == ["午未"]
    assert "sample.six_harm" not in by_id


def test_income_stability_renderer_is_user_facing_not_audit_log() -> None:
    data = _agent_data("我的收入稳定性结构如何？")
    text = render_income_stability_answer(data["inference_context"]["income_stability"])

    assert "这张命盘的收入稳定性结构先看作" in text
    assert "主要依据" in text
    for marker in [
        "income_stability",
        "rule_id",
        "is_prediction",
        "metrics",
        "inputs",
        "sources",
        "wealth_element",
        "touched_wealth_pillars",
        "deterministic",
        "P4",
        "P5",
        "good/bad",
        "发财",
        "破财",
    ]:
        assert marker not in text


def test_oracle_labels_do_not_expose_internal_terms() -> None:
    terms = _default_label_contract()["terms"]
    visible_text = "\n".join(
        str((terms[key]["label"]).get("zh", ""))
        for key in ["q_result_card_boundary", "income_stability_result", "evidence_summary", "source_summary", "deterministic"]
    )

    assert "ResultCard" not in visible_text
    assert "rule_id" not in visible_text
    assert "确定性规则" not in visible_text
    assert "结果卡" in visible_text


def _branch_rule(knowledge_id: str, structured_facts: dict) -> dict:
    return {
        "rule_id": "v19.rule." + knowledge_id,
        "knowledge_id": knowledge_id,
        "domain": "structural_relation",
        "category": "branch_relation",
        "risk_level": "R1",
        "title": knowledge_id,
        "status": "active_in_rule_db",
        "engine_enabled": True,
        "condition": {"structured_facts": structured_facts},
    }
