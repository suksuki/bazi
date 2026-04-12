"""从 LLM 混排文本中抽出单个 JSON 对象（终判等）；失败时用括号平衡与宽松正则兜底。"""
from __future__ import annotations

import json
import re
from typing import Any, Dict


def _strip_md_fences(s: str) -> str:
    t = (s or "").strip()
    t = re.sub(r"^```(?:json)?\s*", "", t, count=1, flags=re.IGNORECASE).strip()
    t = re.sub(r"\s*```\s*$", "", t).strip()
    return t


def _balanced_object_from(text: str, start: int) -> str | None:
    """从 text[start]=='{' 起，按字符串转义规则扫描到匹配的 '}'。"""
    if start < 0 or start >= len(text) or text[start] != "{":
        return None
    depth = 0
    in_str = False
    esc = False
    quote = ""
    i = start
    while i < len(text):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == quote:
                in_str = False
                quote = ""
            i += 1
            continue
        if c in "\"'":
            in_str = True
            quote = c
            i += 1
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
        i += 1
    return None


def extract_llm_json_dict(raw: str) -> Dict[str, Any]:
    """
    尽力从「Here is the JSON…」等混排输出中解析出最外层 JSON 对象。
    顺序：去围栏 → greedy 大括号块 → DOTALL 宽正则 → 自第一个左花括号做括号平衡扫描。
    """
    text = _strip_md_fences(raw or "")
    if not text:
        return {}

    candidates: list[str] = []
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        candidates.append(m.group(0))
    m2 = re.search(r"(\{.*\})", text, re.DOTALL)
    if m2:
        g = m2.group(1)
        if g not in candidates:
            candidates.append(g)

    idx = 0
    while True:
        j = text.find("{", idx)
        if j < 0:
            break
        bal = _balanced_object_from(text, j)
        if bal and bal not in candidates:
            candidates.append(bal)
        idx = j + 1

    for chunk in candidates:
        try:
            obj = json.loads(chunk)
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue
    return {}
