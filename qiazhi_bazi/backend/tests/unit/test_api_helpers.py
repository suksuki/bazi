import pytest
from fastapi import HTTPException

from app.api.admin_helpers import parse_allowed_param_update, strip_reasoning
from app.api.router_helpers import (
    coerce_alignment_score,
    guess_text_lang,
    sql_filter,
)


def test_guess_text_lang_supports_zh_en_ko():
    assert guess_text_lang("你好") == "ZH"
    assert guess_text_lang("hello world") == "EN"
    assert guess_text_lang("안녕하세요") == "KO"


def test_sql_filter_and_param_update_keep_allowed_sql_only():
    sql = "UPDATE physics_interaction_params SET param_value=0.15 WHERE param_key='CF_FLOATING_DECAY';"
    assert sql_filter(sql) == sql
    assert parse_allowed_param_update(sql) == ("CF_FLOATING_DECAY", 0.15)
    assert sql_filter("DELETE FROM physics_interaction_params;") == ""


def test_parse_allowed_param_accepts_default_interaction_keys():
    sql = "UPDATE physics_interaction_params SET param_value=0.88 WHERE param_key='governance_constraint_damping';"
    assert parse_allowed_param_update(sql) == ("governance_constraint_damping", 0.88)
    sql2 = "UPDATE physics_interaction_params SET param_value=1.05 WHERE param_key='L1_CLASH_INTENSITY';"
    assert parse_allowed_param_update(sql2) == ("L1_CLASH_INTENSITY", 1.05)
    sql3 = "UPDATE physics_interaction_params SET param_value=1.2 WHERE param_key='L1_OP_DEST_ETA';"
    assert parse_allowed_param_update(sql3) == ("L1_OP_DEST_ETA", 1.2)
    sql4 = "UPDATE physics_interaction_params SET param_value=0.5 WHERE param_key='INTERDIMENSIONAL_CONDUCTIVITY';"
    assert parse_allowed_param_update(sql4) == ("INTERDIMENSIONAL_CONDUCTIVITY", 0.5)


def test_parse_allowed_param_rejects_unknown_key():
    sql = "UPDATE physics_interaction_params SET param_value=0.5 WHERE param_key='not_a_real_physics_param';"
    with pytest.raises(HTTPException) as exc:
        parse_allowed_param_update(sql)
    assert "不允许更新参数" in str(exc.value.detail)


def test_reasoning_strip_and_alignment_coercion():
    assert strip_reasoning("Final Answer: 保持谨慎。") == "保持谨慎。"
    assert coerce_alignment_score(88, "存在异常") == 59.0
    assert coerce_alignment_score(45, "") == 45.0
