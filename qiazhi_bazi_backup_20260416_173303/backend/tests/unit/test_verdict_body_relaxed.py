"""extract_verdict_body_relaxed：非严格 JSON 时仍能抽取 verdict_body。"""

from app.skills.final_verdict_parts.json_extract import coerce_verdict_body_display, extract_verdict_body_relaxed


def test_extract_verdict_body_relaxed_from_embedded_string() -> None:
    raw = '前缀\n{"verdict_body": "身强喜泄食伤", "change_log": {}}\n后缀'
    assert extract_verdict_body_relaxed(raw) == "身强喜泄食伤"


def test_extract_verdict_body_relaxed_plain_markdown() -> None:
    raw = "### 核心\n这是纯 Markdown 终判，没有 JSON 包裹。"
    out = extract_verdict_body_relaxed(raw)
    assert "纯 Markdown" in out


def test_coerce_verdict_body_display_strips_json_fence() -> None:
    raw = '```json\n{"verdict_body": "### 核心气象\\n正文", "change_log": {}}\n```'
    assert coerce_verdict_body_display(raw).startswith("### 核心气象")


def test_coerce_verdict_body_display_plain_unchanged() -> None:
    s = "### 核心\n仅 Markdown"
    assert coerce_verdict_body_display(s) == s
