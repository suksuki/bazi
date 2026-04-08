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


def test_reasoning_strip_and_alignment_coercion():
    assert strip_reasoning("Final Answer: 保持谨慎。") == "保持谨慎。"
    assert coerce_alignment_score(88, "存在异常") == 59.0
    assert coerce_alignment_score(45, "") == 45.0
