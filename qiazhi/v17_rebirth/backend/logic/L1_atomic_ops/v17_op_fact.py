"""V17.13：Manifest / L1 算子事实行生成（仅命理学标签，禁止 Abs 分值上屏）。"""
from __future__ import annotations

import re
from typing import Iterable, Sequence

# 禁止进入用户可见事实的工程/分数字样（保守剔除）
_ABS_SCORE_PATTERNS = (
    re.compile(r"\bAbs\b", re.I),
    re.compile(r"absolute_energy", re.I),
    re.compile(r"\bVF\.[A-Za-z0-9_.]+\b"),
    re.compile(r"\d+\.\d{3,}"),  # 长小数常来自张量
)


_KIND_ZH = {
    "liu_chong": "地支六冲",
    "sanhe": "地支三合",
    "sanxing": "地支三刑",
    "liu_hai": "地支六害",
    "liu_po": "地支六破",
    "liu_he": "地支六合",
    "ban_he": "地支半合",
    "an_he": "地支暗合",
    "muku": "墓库门态",
    "status": "长生状态机",
    "geography": "地理方位场",
    "vertical_crush": "干支维轴",
    "core_conflict": "核心冲突",
    "stem_stuck": "天干五合·羁绊",
    "stem_transform": "天干五合·化气",
    "pattern": "格局",
    "blind_work": "盲派·做功",
}


def strip_score_noise(text: str) -> str:
    """剔除 Abs 及典型工程分数字样，保留中文与干支标签。"""
    t = str(text or "").strip()
    for rx in _ABS_SCORE_PATTERNS:
        t = rx.sub("", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def generate_v17_fact_from_op(
    *,
    kind: str,
    detail: str = "",
    branches: Sequence[str] | None = None,
) -> str:
    """
    生成单行命理标签，例如：「[地支三刑: 寅巳申]」「[天干五合·化气: 甲己→土]」。
    禁止写入数值型 Abs；detail / branches 仅允许干支与简短中文。
    """
    zh = _KIND_ZH.get(kind, kind)
    parts: list[str] = []
    if branches:
        parts.append("".join(str(b) for b in branches if b))
    extra = str(detail or "").strip()
    if extra:
        parts.append(extra)
    core = "·".join(p for p in parts if p) if parts else ""
    line = f"[{zh}: {core}]" if core else f"[{zh}]"
    return strip_score_noise(line)


def merge_fact_lines(lines: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in lines:
        t = strip_score_noise(str(raw))
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out
