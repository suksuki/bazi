from __future__ import annotations

import re
from typing import Dict

_FACT_ID_PATTERN = re.compile(r"Fact_ID\s*[:=]\s*([A-Za-z0-9_-]+)")
_SEMANTIC_ALIAS_LEXICON = {
    "yin_si": "检测到寅巳交互",
    "zi_wu": "检测到子午交互",
    "sanhe": "检测到三合交互",
    "clash": "检测到冲克交互",
}


def get_semantic_alias(fact_id: str) -> str:
    raw = str(fact_id or "").strip()
    if not raw:
        return "检测到未知物理交互"
    low = raw.lower()
    for k, alias in _SEMANTIC_ALIAS_LEXICON.items():
        if k in low:
            return alias
    # Semantic fallback pool: never return empty; always return an evidence seed.
    return f"检测到{raw}交互"


def alias_fact_ids_in_text(text: str) -> str:
    s = str(text or "")
    cache: Dict[str, str] = {}

    def _repl(m: re.Match[str]) -> str:
        fid = str(m.group(1) or "").strip()
        if fid not in cache:
            # V13.35: 必须通过 get_semantic_alias 生成语义别名。
            cache[fid] = get_semantic_alias(fid)
        return cache[fid]

    return _FACT_ID_PATTERN.sub(_repl, s)

