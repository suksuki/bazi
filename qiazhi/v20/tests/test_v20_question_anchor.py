from __future__ import annotations

from v20.interaction.question_anchor import bind_questions_to_bazi_context, build_question_anchor, render_question_display_title
from v20.interaction.questions import QuestionCandidate


def _question(domain: str = "useful_god", key: str = "q_useful_god_candidates") -> QuestionCandidate:
    return QuestionCandidate(
        question_key=key,
        title="用神方向先看扶身、通关、调候，还是顺着主线路泄秀？",
        domain=domain,
        score=0.8,
        source_feature_ids=("feature.useful_god.path",),
        boundary="只围绕当前八字证据追问。",
        measurement_topic="用神方向",
        measurement_stage="focus",
        next_question_atom_id="atom.user.focus.useful_god",
        next_question_topic="useful_god",
        next_question_stage="focus",
    )


def _frame(with_time: bool = True) -> dict[str, object]:
    return {
        "context_id": "v20.bazi_context.test",
        "natal_pillars": {"year": "丁巳", "month": "乙巳", "day": "乙丑", "hour": "乙酉"},
        "day_master": "乙",
        "day_master_element": "木",
        "time_layers": (
            {"layer_key": "luck", "pillar": "庚子", "ten_god": "正官"},
            {"layer_key": "flow_year", "pillar": "丙午", "ten_god": "伤官"},
        )
        if with_time
        else (),
    }


def _structure() -> dict[str, object]:
    return {
        "primary_dynamic_chain": {
            "chain_id": "chain.output_authority",
            "label": "食神制杀",
            "nodes": ({"label": "食神"}, {"label": "七杀"}, {"label": "日主"}),
        }
    }


def _mainline() -> dict[str, object]:
    return {"primary_mainline": {"domain": "career", "label": "事业压力与制化主线"}}


def test_v20_question_anchor_renders_bazi_bound_question_not_raw_template() -> None:
    question = _question()
    anchor = build_question_anchor(
        question,
        bazi_context_frame=_frame(),
        structure_dynamics=_structure(),
        mainline_arbitration=_mainline(),
        role_key="user",
    )
    title = render_question_display_title(question, anchor, role_key="user")

    assert anchor["anchor_status"] == "bound"
    assert anchor["day_master"] == "乙"
    assert anchor["primary_dynamic_chain_label"] == "食神制杀"
    assert title != question.title
    assert "乙日主" in title
    assert "食神制杀" in title
    assert "先扶身" not in title
    assert "先泄秀" not in title
    assert "还是顺着" not in title


def test_v20_time_question_is_hidden_without_time_context_for_user() -> None:
    question = _question(domain="time", key="q_time_relation_triggers")
    useful = _question()
    bound = bind_questions_to_bazi_context(
        (question, useful),
        bazi_context_frame=_frame(with_time=False),
        structure_dynamics=_structure(),
        mainline_arbitration=_mainline(),
        role_key="user",
    )

    assert all(row.domain != "time" for row in bound)
    assert bound[0].question_anchor["anchor_status"] == "bound"


def test_v20_question_anchor_keeps_admin_observability_for_missing_time() -> None:
    question = _question(domain="time", key="q_time_relation_triggers")
    bound = bind_questions_to_bazi_context(
        (question,),
        bazi_context_frame=_frame(with_time=False),
        structure_dynamics=_structure(),
        mainline_arbitration=_mainline(),
        role_key="admin",
    )

    assert bound[0].question_anchor["anchor_status"] == "missing_time"
    assert "luck_or_flow_year" in bound[0].question_anchor["missing_requirements"]
    assert "锚定问题" in bound[0].display_title


def test_v20_useful_god_display_question_asks_for_actual_direction_not_binary_diagnostic() -> None:
    question = _question()
    bound = bind_questions_to_bazi_context(
        (question,),
        bazi_context_frame=_frame(),
        structure_dynamics=_structure(),
        mainline_arbitration=_mainline(),
        role_key="user",
    )

    title = bound[0].display_title
    assert "用神和调节方向是什么" in title
    for bad in ("先扶身", "先泄秀", "扶身还是", "泄秀还是", "扶身、通关、调候"):
        assert bad not in title
