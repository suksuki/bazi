from __future__ import annotations

from v20.tests.support_paths import read_v20_text


def test_v20_full_knowledge_content_doc_covers_l0_to_l12() -> None:
    text = read_v20_text("docs/bazi_knowledge/catalog/v20_knowledge_full_content_zh_v1.md")

    assert "V20 八字知识库完整内容 v1" in text
    for index in range(13):
        assert f"## L{index} " in text
    for phrase in (
        "十神为比肩、劫财、食神、伤官、偏财、正财、七杀、正官、偏印、正印",
        "做功关注谁对谁作用",
        "财富财星材料",
        "TopicProjection",
        "LLM 不裁决用神格局",
    ):
        assert phrase in text


def test_v20_decision_and_portrait_model_doc_records_system_driven_chain() -> None:
    text = read_v20_text("docs/v20/V20_DECISION_AND_PORTRAIT_MODEL.md")

    assert "V20 裁决链路与画像层模型" in text
    assert "V20 Bazi Defeasible Decision Model" in text
    assert "RuleSpec Runtime" in text
    assert "Defeasible ArgumentNode" in text
    assert "PortraitProjection" in text
    assert "LLM 直接裁决格局" in text


def test_v20_feature_question_interaction_model_doc_records_system_chain() -> None:
    text = read_v20_text("docs/v20/V20_FEATURE_QUESTION_INTERACTION_MODEL.md")

    assert "V20 八字特征、智能问题与交互系统模型" in text
    assert "FeatureState" in text
    assert "QuestionIntent" in text
    assert "InteractionSignal" in text
    assert "Utility-based Question Ranking" in text
    assert "直接改 RuleSpec" in text
