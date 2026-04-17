from __future__ import annotations

from typing import List

from app.skills.final_verdict_parts.constants import (
    IMMUTABLE_WILL_TAGS,
    PRIMARY_WILL_TAGS,
    WILL_PRESERVATION_WINDOW,
)


def clean_context_lines(lines: List[str], max_tokens: int = 4000) -> List[str]:
    """
    ContextCleaner:
    - 避免逻辑证据无限膨胀导致断言中断
    - 超阈值后仅保留核心 L1/L2 旗标 + 最近片段
    """
    cleaned = [str(x).strip() for x in (lines or []) if str(x).strip()]
    ranked: List[tuple[int, str]] = []
    for x in cleaned:
        priority = 0
        if any(tag in x for tag in PRIMARY_WILL_TAGS):
            priority = 2_147_483_647
        if any(tag in x for tag in IMMUTABLE_WILL_TAGS):
            priority = 2_147_483_647
        elif (
            "L1_Junction" in x
            or "SHANG_GUAN_JIAN_GUAN" in x
            or "插件.conflict_zone" in x
            or "插件.tension_level" in x
            or "四柱=" in x
        ):
            priority = 200
        ranked.append((priority, x))
    primary_will_lines = [x for p, x in ranked if p == 2_147_483_647]
    if len(primary_will_lines) > WILL_PRESERVATION_WINDOW:
        primary_will_lines = primary_will_lines[-WILL_PRESERVATION_WINDOW:]
    approx_tokens = sum(max(1, len(x) // 2) for x in cleaned)
    if approx_tokens <= max_tokens:
        merged_full: List[str] = []
        seen_full = set()
        for item in [*primary_will_lines, *cleaned]:
            if item in seen_full:
                continue
            seen_full.add(item)
            merged_full.append(item)
        return merged_full
    keep_prefix = [x for p, x in ranked if p >= 200 and p < 2_147_483_647][:18]
    tail = cleaned[-60:]
    merged: List[str] = []
    seen = set()
    for item in [*primary_will_lines, *keep_prefix, *tail]:
        if item in seen:
            continue
        seen.add(item)
        merged.append(item)
    return merged
