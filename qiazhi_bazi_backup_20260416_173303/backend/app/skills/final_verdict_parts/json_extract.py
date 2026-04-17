from __future__ import annotations

import json
import re
from typing import Any, Dict

from app.utils.json_extract import extract_llm_json_dict


def extract_json_from_llm_text(raw: str) -> Dict[str, Any]:
    """终判等：统一走 app.utils.json_extract 多策略抽取。"""
    return extract_llm_json_dict(raw)


def _unescape_json_string_fragment(s: str) -> str:
    return (
        s.replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace('\\"', '"')
        .replace("\\\\", "\\")
    )


def extract_verdict_body_relaxed(raw: str) -> str:
    """当 JSON 解析失败或 verdict_body 为空时，从原始 LLM 文本中尽力抽取终判正文。"""
    text = (raw or "").strip()
    if not text:
        return ""
    m = re.search(r'"verdict_body"\s*:\s*"((?:[^"\\]|\\.)*)"', text, re.DOTALL)
    if m:
        return _unescape_json_string_fragment(m.group(1)).strip()[:20000]
    fm = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
    if fm:
        try:
            obj = json.loads(fm.group(1))
            if isinstance(obj, dict):
                vb = str(obj.get("verdict_body") or "").strip()
                if vb:
                    return vb[:20000]
        except Exception:
            pass
    stripped = text.lstrip()
    if stripped and not stripped.startswith("{"):
        return text[:20000]
    return ""


def coerce_verdict_body_display(raw: str, _depth: int = 0) -> str:
    """
    剥离误入 verdict 正文 / 断言行的 ```json 契约壳或整段裸 JSON，避免 metadata 与前端展示代码块。
    """
    if _depth > 6:
        return str(raw or "")[:20000]
    s = str(raw or "").strip()
    if not s:
        return ""
    loosen = extract_verdict_body_relaxed(s)
    if loosen and loosen.strip() and "```" not in loosen[:32]:
        if loosen.strip() != s.strip():
            return coerce_verdict_body_display(loosen, _depth + 1)[:20000]
        return loosen.strip()[:20000]
    lh = s[:200].lower()
    if "```json" in lh or lh.startswith("```"):
        core = re.sub(r"^```(?:json)?\s*", "", s, count=1, flags=re.IGNORECASE).strip()
        core = re.sub(r"\s*```\s*$", "", core).strip()
        if core and core != s:
            return coerce_verdict_body_display(core, _depth + 1)[:20000]
    if s.startswith("{") and '"verdict_body"' in s[:8000]:
        o = extract_json_from_llm_text(s)
        if isinstance(o, dict):
            vb = str(o.get("verdict_body") or "").strip()
            if vb and vb != s:
                return coerce_verdict_body_display(vb, _depth + 1)[:20000]
    return s[:20000]
