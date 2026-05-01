from __future__ import annotations

import re

FORBIDDEN_LITERAL_TERMS = (
    "发财",
    "破财",
    "疾病",
    "官非",
    "灾祸",
    "应期",
    "必然",
    "一定",
    "改运",
    "guaranteed",
    "must happen",
    "destined to",
    "will definitely",
    "확실히",
    "반드시",
)

FORBIDDEN_TEXT_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"你.{0,8}会.{0,6}发.{0,2}财",
        r"你.{0,8}必.{0,6}(富|赚|升|婚|病|灾)",
        r"必定.{0,12}(成功|发财|结婚|离婚|升职)",
        r"guaranteed.{0,24}(wealth|rich|marriage|promotion|illness)",
        r"you.{0,16}will.{0,16}(be rich|get rich|marry|divorce|get promoted)",
    )
)

INTERNAL_MARKERS = ("feature.", "rulepath.", "core.", "v20.")


def hard_enforce_text(text: str) -> dict[str, object]:
    failures: list[str] = []
    if not text.strip():
        failures.append("empty_output")
    if any(term in text for term in FORBIDDEN_LITERAL_TERMS):
        failures.append("forbidden_literal")
    if any(pattern.search(text) for pattern in FORBIDDEN_TEXT_PATTERNS):
        failures.append("forbidden_semantic_pattern")
    if any(marker in text for marker in INTERNAL_MARKERS):
        failures.append("internal_id_leak")
    return {
        "ok": not failures,
        "failures": failures,
        "guardrails": [
            "HARD_TEXT_ENFORCEMENT",
            "REGEX_AND_LITERAL_SCAN",
            "DETERMINISTIC_FALLBACK_REQUIRED_ON_FAILURE",
        ],
    }
