from __future__ import annotations

import re
from typing import List, Tuple

TERMINAL_TECH_RE = re.compile(
    r"(Fact_ID|VF_|sys\.core|logic|metadata|trace|v13\.\d+|标签|登记|收敛)",
    re.I,
)


def terminal_semantic_purge(verdict_body: str) -> Tuple[str, List[str]]:
    text = str(verdict_body or "")
    if not text.strip():
        return text, []
    hits = [m.group(0) for m in TERMINAL_TECH_RE.finditer(text)]
    if not hits:
        return text, []
    cleaned = text
    cleaned = re.sub(r"Fact_ID\s*[:=]?\s*[a-zA-Z0-9_-]*", "证据锚点", cleaned, flags=re.I)
    cleaned = re.sub(r"VF_[a-zA-Z0-9_-]*", "气象征候", cleaned, flags=re.I)
    cleaned = re.sub(r"sys\.core", "命盘内核", cleaned, flags=re.I)
    cleaned = re.sub(r"\blogic\b", "判势", cleaned, flags=re.I)
    cleaned = re.sub(r"\bmetadata\b", "盘面注记", cleaned, flags=re.I)
    cleaned = re.sub(r"\btrace\b", "脉络", cleaned, flags=re.I)
    cleaned = re.sub(r"v13\.\d+", "", cleaned, flags=re.I)
    cleaned = cleaned.replace("标签", "征候").replace("登记", "映照").replace("收敛", "定势")
    return cleaned.strip(), list(dict.fromkeys([str(x).strip() for x in hits if str(x).strip()]))
