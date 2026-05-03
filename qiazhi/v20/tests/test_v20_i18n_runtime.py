from __future__ import annotations

from v20.api.runtime import run_runtime_from_pillars


def test_runtime_localizes_questions_and_answer_for_english() -> None:
    result = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        flow_year_pillar="庚子",
        user_text="I want to read career and wealth",
        locale="en",
        llm_mode="deterministic",
        input_id="v20.i18n.en",
    )

    assert result["locale"] == "en"
    assert result["selected_question"]["title"]
    assert not _contains_han(result["selected_question"]["title"])
    assert all(not _contains_han(row["title"]) for row in result["questions"][:8])
    assert "主线" not in result["answer_text"]
    assert "复核" not in result["answer_text"]


def test_runtime_localizes_questions_and_answer_for_korean() -> None:
    result = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        flow_year_pillar="庚子",
        user_text="직업과 재운을 보고 싶어요",
        locale="ko",
        llm_mode="deterministic",
        input_id="v20.i18n.ko",
    )

    assert result["locale"] == "ko"
    assert result["selected_question"]["title"]
    assert not _contains_han(result["selected_question"]["title"])
    assert all(not _contains_han(row["title"]) for row in result["questions"][:8])
    assert "主线" not in result["answer_text"]
    assert "复核" not in result["answer_text"]


def _contains_han(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in str(text or ""))
