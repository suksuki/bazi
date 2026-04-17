from __future__ import annotations

from app.semantic_translator.imagery_mapping import build_data_imagery_mapping_lines
from app.semantic_translator.imagery_mapping import build_pattern_specialized_prompt_lines
from app.semantic_translator.imagery_mapping import adapt_lines_for_style
from app.skills.prompts_registry import prompt_user_prefix, prompt_user_suffix


def _base_metadata() -> dict:
    return {
        "flow_state": "ready",
        "pillars": {
            "year": {"stem": "甲", "branch": "子"},
            "month": {"stem": "丙", "branch": "寅"},
            "day": {"stem": "戊", "branch": "午"},
            "hour": {"stem": "庚", "branch": "申"},
        },
        "conflict_matrix": {
            "points": [
                {"id": "cp_scan_0", "kind": "穿", "detail": "寅巳穿"},
            ]
        },
    }


def _base_physics() -> dict:
    return {
        "energy_axes": {"water": 12.0, "metal": 11.2},
        "meta": {
            "season": "winter",
            "hit_pattern_name": "官杀格",
            "tension_index": 0.41,
            "intention_context": {
                "active_intention": "稳健避险",
                "pattern_affinity_multipliers": {"FOLLOW_WEALTH": 1.65},
            },
        },
        "plugin_outputs": {},
    }


def test_prompt_user_head_has_data_pack_and_no_teaching_opening() -> None:
    user = prompt_user_prefix()
    first_line = user.splitlines()[0]
    assert first_line == "[命理核心数据包·即时裁决]"
    assert "thinking process" not in user.lower()
    assert "下面我来解释" not in user


def test_prompt_user_tail_has_no_thinking_process_directive() -> None:
    tail = prompt_user_suffix().strip()
    assert "禁止输出思考过程" in tail
    assert tail.endswith("禁止输出思考过程。")


def test_official_pattern_has_specialized_vocabulary() -> None:
    lines = build_pattern_specialized_prompt_lines(_base_physics())
    blob = "；".join(lines)
    assert "位序" in blob
    assert "代价" in blob


def test_semantic_translation_covers_yin_si_pierce() -> None:
    lines = build_data_imagery_mapping_lines(_base_physics(), _base_metadata())
    blob = "；".join(lines)
    assert ("效率折损" in blob) or ("内部损耗" in blob)


def test_critical_will_override_marker_present_when_weight_high() -> None:
    lines = build_data_imagery_mapping_lines(_base_physics(), _base_metadata())
    blob = "；".join(lines)
    assert "CRITICAL_WILL_OVERRIDE" in blob
    assert "宜收缩" in blob


def test_modern_workplace_style_replaces_qiji_term() -> None:
    cooked = adapt_lines_for_style(["盘局气机受阻，先稳后动。"], "modern_workplace")
    assert cooked and "气机" not in cooked[0]
    assert "能量结构" in cooked[0]


def test_modern_workplace_style_replaces_classical_terms() -> None:
    cooked = adapt_lines_for_style(["先化解冲克，再看大运切面。"], "modern_workplace")
    assert cooked
    s = cooked[0]
    assert "化解" not in s and "冲克" not in s and "大运" not in s
    assert "对冲策略" in s and "负向反馈" in s and "时间周期" in s

