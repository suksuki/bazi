from __future__ import annotations

from v17_rebirth.backend.logic.L3_modern_narrative.wealth_profile_core import resolve_wealth_profile
from v17_rebirth.backend.logic.L3_modern_narrative.wealth_code_core import resolve_wealth_code
from v17_rebirth.backend.services.llm_prompt_contracts import (
    WEALTH_ASSERTION_PROMPT_VERSION,
    build_wealth_assertion_prompt_bundle,
    build_wealth_assertion_prompt_text,
)


def _tensor() -> dict:
    return {
        "gender": "male",
        "luck_pillar": "庚子",
        "flow_pillar": "丙午",
        "ten_gods_runtime": {
            "食神": 36.0,
            "伤官": 22.0,
            "正财": 30.0,
            "偏财": 20.0,
            "正官": 16.0,
            "七杀": 8.0,
            "正印": 10.0,
            "偏印": 6.0,
            "比肩": 10.0,
            "劫财": 8.0,
        },
        "facts": [
            {"fact": "格局候选：食伤生财，输出换财通道显性。", "plugin": "classical.pattern.shishen_shengcai.v1"},
            {"fact": "格局候选：正财格月令入口。", "plugin": "classical.pattern.wealth_star.v1"},
        ],
        "meta": {
            "god_ring_authority": {
                "use_gods": ["食神", "正财"],
                "taboo_gods": ["七杀"],
                "tongguan_gods": ["正官"],
                "confidence": 0.82,
            }
        },
    }


def test_wealth_assertion_prompt_bundle_preserves_profile_contract() -> None:
    profile = resolve_wealth_profile(_tensor())["wealth_profile"]
    bundle = build_wealth_assertion_prompt_bundle(wealth_profile=profile, output_language="zh")

    assert bundle["policy_version"] == WEALTH_ASSERTION_PROMPT_VERSION
    assert bundle["task_type"] == "wealth_topic_assertion"
    assert bundle["input_contract"] == "v17.topic.wealth_profile.v1"
    assert bundle["profile_present"] is True
    assert bundle["summary"]["usable_state"] == profile["usable_state"]
    assert bundle["summary"]["top_channel"]["id"] == profile["primary_channels"][0]["id"]
    assert "wealth_verdict" in bundle["output_contract"]["required_blocks"]
    assert "必发财" in bundle["output_contract"]["forbidden_claims"]
    assert bundle["wealth_profile"]["evidence"]


def test_wealth_assertion_prompt_text_is_domain_specific_and_bounded() -> None:
    profile = resolve_wealth_profile(_tensor())["wealth_profile"]
    text = build_wealth_assertion_prompt_text(wealth_profile=profile, output_language="zh")

    assert "V17 财富解读写作者" in text
    assert "没有 wealth_code 时，才退回使用 wealth_profile" in text
    assert "不得自由重读原始八字" in text
    assert "【总体判断】【钱怎么来】【能不能接住】【要避开的坑】【接下来怎么做】" in text
    assert "收入来源、赚钱方式、现金流" in text
    assert "用户正文里不要出现正财、偏财" in text
    assert "至少引用 2 条" in text
    assert "确定金额" in text
    assert "primary_channels" in text
    assert "plain_summary" in text


def test_wealth_assertion_prompt_prefers_wealth_code_contract() -> None:
    tensor = _tensor()
    code = resolve_wealth_code(tensor)["wealth_code"]

    bundle = build_wealth_assertion_prompt_bundle(wealth_code=code, output_language="zh")
    text = build_wealth_assertion_prompt_text(wealth_code=code, output_language="zh")

    assert bundle["input_contract"] == "v17.topic.wealth_code.v1"
    assert bundle["wealth_code_present"] is True
    assert bundle["material_present"] is True
    assert bundle["wealth_code"]["plain_summary"]["primary_path"]
    assert "财富密码" in text
    assert "至少引用 2 条 wealth_code.evidence" in text
    assert "ten_gods_runtime" not in text


def test_wealth_assertion_prompt_can_resolve_from_physics_tensor() -> None:
    bundle = build_wealth_assertion_prompt_bundle(physics_tensor=_tensor(), output_language="en")
    text = build_wealth_assertion_prompt_text(physics_tensor=_tensor(), output_language="en")

    assert "guaranteed fortune" in bundle["output_contract"]["forbidden_claims"]
    assert bundle["input_contract"] == "v17.topic.wealth_code.v1"
    assert "V17 wealth-topic assertion writer" in text
    assert "[Overall]" in text
    assert "do not read raw chart data freely" in text
    assert "wealth_profile" in text
    assert "guaranteed fortune" in text


def test_wealth_assertion_prompt_localizes_korean_boundary() -> None:
    profile = resolve_wealth_profile(_tensor())["wealth_profile"]
    bundle = build_wealth_assertion_prompt_bundle(wealth_profile=profile, output_language="ko")
    text = build_wealth_assertion_prompt_text(wealth_profile=profile, output_language="ko")

    assert "정확한 금액" in bundle["output_contract"]["forbidden_claims"]
    assert "재물 주제 단언 작성자" in text
    assert "[전체 판단]" in text
    assert "[돈이 들어오는 방식]" in text
    assert "정확한 금액" in text


def test_wealth_assertion_prompt_missing_profile_refuses_assertion() -> None:
    bundle = build_wealth_assertion_prompt_bundle(output_language="zh")
    text = build_wealth_assertion_prompt_text(output_language="zh")

    assert bundle["profile_present"] is False
    assert bundle["material_present"] is False
    assert "缺少 wealth_code 和 wealth_profile" in text
    assert "不能生成财富解读" in text
