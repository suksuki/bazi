"""NarrativeSanitizer: convert engineering jargon into natural language."""
from __future__ import annotations

import re
from typing import List

_RULES: List[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bVF\.[A-Za-z0-9_.-]*", re.IGNORECASE), "已验证关键线索"),
    (re.compile(r"Abs档", re.IGNORECASE), "能量层级"),
    (re.compile(r"Fact_ID[=:]?[A-Za-z0-9_-]*", re.IGNORECASE), "证据锚点"),
    (re.compile(r"\bseed\b", re.IGNORECASE), "结构线索"),
    (re.compile(r"\bnode_id\b", re.IGNORECASE), "推演节点"),
    (re.compile(r"\bverified_fact_lines\b", re.IGNORECASE), "已验证事实"),
]


def sanitize_fragment_text(text: str) -> str:
    s = str(text or "").strip()
    if not s:
        return ""
    for pat, rep in _RULES:
        s = pat.sub(rep, s)
    return re.sub(r"\s+", " ", s).strip()

