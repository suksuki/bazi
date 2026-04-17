from __future__ import annotations

from app.utils.json_extract import extract_llm_json_dict


def test_extract_llm_json_dict_after_english_preamble() -> None:
    raw = 'Here is the JSON output:\n{"verdict_body": "### 核心\\n正文", "change_log": {"physics_diff": [], "consensus_diff": [], "text_diff_hint": ""}, "assertions": []}\nThanks.'
    obj = extract_llm_json_dict(raw)
    assert obj.get("verdict_body", "").startswith("### 核心")


def test_extract_llm_json_dict_balanced_nested_string() -> None:
    raw = """prefix {"verdict_body": "He said \\"ok\\" and {fake}", "change_log": {}, "assertions": []} suffix"""
    obj = extract_llm_json_dict(raw)
    assert "verdict_body" in obj
