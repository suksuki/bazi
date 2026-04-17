"""物理预判骨架：将 VF 脱水行折叠为简短 Markdown，供断言区与终判前置展示。"""
from __future__ import annotations

import re
from typing import List, Sequence

# 分类关键词（中文子平 + 部分英文 token，与 VF 行常见写法对齐）
_STRUCTURE_KEYS = (
    "三合",
    "三会",
    "六合",
    "六冲",
    "六穿",
    "刑",
    "害",
    "破",
    "合局",
    "合化",
    "暗合",
    "芯片·冲突",
    "结构·",
    "神煞·",
    "因果流通",
    "VF:",
)
_STRUCTURE_KEYS_LOWER = ("clash", "combine", "punish", "harm", "sanhe", "liuhe")

_STATE_KEYS = (
    "无根",
    "有根",
    "虚浮",
    "通根",
    "日主",
    "衰减",
    "旺衰",
    "印比",
    "食伤",
    "财官",
    "Self_Abs",
    "structure.self_abs",
    "structure.root",
    "四柱快照",
)

_WILL_KEYS = (
    "止损",
    "获利",
    "补丁",
    "意志",
    "优先",
    "能量补丁",
    "manual",
    "用户",
    "已确认",
    "归档",
)


def _normalize_line(s: str) -> str:
    t = str(s or "").strip()
    t = re.sub(r"\s+", " ", t)
    return t[:220]


def _bucket(lines: Sequence[str]) -> tuple[List[str], List[str], List[str]]:
    struct: List[str] = []
    state: List[str] = []
    will: List[str] = []
    other: List[str] = []
    for raw in lines:
        s = _normalize_line(raw)
        if not s:
            continue
        low = s.lower()
        if any(k in s for k in _STRUCTURE_KEYS) or any(k in low for k in _STRUCTURE_KEYS_LOWER):
            struct.append(s)
        elif any(k in s for k in _STATE_KEYS):
            state.append(s)
        elif any(k in s for k in _WILL_KEYS):
            will.append(s)
        else:
            other.append(s)
    if other:
        # 未分类行并入「状态」侧，避免丢失物理语义（仍保持简练上限）
        state.extend(other[:8])
    return struct, state, will


def _join_bullets(items: List[str], *, max_items: int = 4, empty_label: str) -> str:
    if not items:
        return empty_label
    out: List[str] = []
    for p in items[:max_items]:
        if len(p) > 80:
            out.append(p[:77] + "…")
        else:
            out.append(p)
    return "；".join(out)


def _build_core_skeleton(verified_fact_lines: Sequence[str]) -> str:
    lines = [_normalize_line(x) for x in verified_fact_lines if _normalize_line(x)]
    if not lines:
        return (
            "### 核心气象 (物理预判)\n\n"
            "* **结构：** （暂无 VF 结构标签）\n"
            "* **状态：** （暂无 VF 状态标签）\n"
            "* **意志：** （暂无与 VF 对齐的意志标签）\n"
        )

    struct, state, will = _bucket(lines)

    struct_text = _join_bullets(struct, max_items=5, empty_label="（VF 未显式结构标签）")
    state_text = _join_bullets(state, max_items=5, empty_label="（VF 未显式状态标签）")
    will_text = _join_bullets(will, max_items=4, empty_label="（暂无与 VF 对齐的意志/补丁标签）")

    return (
        "### 核心气象 (物理预判)\n\n"
        f"* **结构：** {struct_text}\n"
        f"* **状态：** {state_text}\n"
        f"* **意志：** {will_text}\n"
    )


def _append_risk_and_temporal(
    core: str,
    *,
    risk_lines: Sequence[str] | None,
    temporal_warnings: Sequence[str] | None,
) -> str:
    risk = [str(x).strip() for x in (risk_lines or []) if str(x).strip()]
    temp = [str(x).strip() for x in (temporal_warnings or []) if str(x).strip()]
    if not risk and not temp:
        return (
            core
            + "### 风险预警 (意志对垒)\n\n"
            + "* **张力：** （本轮未检出显著意志—引擎冲突启发式；仍以 VF 与审计 LLM 为准）\n"
        )
    bullets: List[str] = []
    bullets.extend(f"* **张力：** {x}" for x in risk[:6])
    bullets.extend(f"* **时序：** {x}" for x in temp[:4])
    return core + "### 风险预警 (意志对垒)\n\n" + "\n".join(bullets) + "\n"


def build_verdict_skeleton(
    verified_fact_lines: Sequence[str],
    *,
    risk_lines: Sequence[str] | None = None,
    temporal_warnings: Sequence[str] | None = None,
) -> str:
    """
    将 VF 标签行压成一段 Markdown 骨架（无 LLM）。

    输出含「结构 / 状态 / 意志」与可选「风险预警」模块（意志对垒 + 大运锚漂移）。
    """
    core = _build_core_skeleton(verified_fact_lines)
    return _append_risk_and_temporal(core, risk_lines=risk_lines, temporal_warnings=temporal_warnings)
