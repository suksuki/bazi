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

    def sanitize(self, text: str) -> str:
        output = str(text or "").strip()
        if not output:
            return ""
        for rule in self._banned:
            output = rule.sub("", output)
        output = re.sub(r"\s+", " ", output).strip()
        return output
