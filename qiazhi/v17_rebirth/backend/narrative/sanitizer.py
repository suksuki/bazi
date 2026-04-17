from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class NarrativeSanitizer:
    """Hard filter for engineering jargon before narrative fusion."""

    _banned: tuple[re.Pattern[str], ...] = (
        re.compile(r"\bVF\.[A-Za-z0-9_.-]*", re.IGNORECASE),
        re.compile(r"\bAbs\b|\bABS\b|Abs档", re.IGNORECASE),
        re.compile(r"Fact_ID[=:]?[A-Za-z0-9_-]*", re.IGNORECASE),
    )
    _replacements: tuple[tuple[re.Pattern[str], str], ...] = (
        (re.compile(r"η\s*=\s*[0-9.]+", re.IGNORECASE), "当前能量流转的灵敏度"),
        (re.compile(r"\bnode_id\b|\bseed\b|\bverified_fact_lines\b", re.IGNORECASE), ""),
        (re.compile(r"勾选此项以修复", re.IGNORECASE), "建议调整此项以优化"),
        (re.compile(r"赛博|极客|激光", re.IGNORECASE), ""),
    )

    def sanitize(self, text: str) -> str:
        output = str(text or "").strip()
        if not output:
            return ""
        for rule in self._banned:
            output = rule.sub("", output)
        for pattern, replacement in self._replacements:
            output = pattern.sub(replacement, output)
        output = re.sub(r"\s+", " ", output).strip()
        return output
