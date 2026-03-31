#!/usr/bin/env python3
"""
FDS 2.0 动态监听器
==================
- A-50（刑合格）CRITICAL_STRUCTURE_COLLAPSE：流年触发刑局且破坏合局时，强制红色高亮与 RAG 判词。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent

# 三刑组（与 pattern_scanner_v61 一致）
SAN_XING_BRANCHES = [{"寅", "巳", "申"}, {"丑", "戌", "未"}, {"子", "卯"}]
CRITICAL_STRUCTURE_COLLAPSE_VERDICT = "刑伤突发，险境难支"


def _transit_triggers_xing(transit_branch: str) -> bool:
    """流年/大运地支是否参与三刑（寅巳申/丑戌未/子卯）。"""
    if not transit_branch or len(transit_branch) < 1:
        return False
    zhi = transit_branch[-1] if isinstance(transit_branch, str) else transit_branch
    for s in SAN_XING_BRANCHES:
        if zhi in s:
            return True
    return False


def _transit_breaks_he(transit_stem: str, transit_branch: str, config: Optional[Dict[str, Any]] = None) -> bool:
    """
    简化判定：流年干支是否「破坏合局」。
    刑合格依赖地支三刑+天干透官；若流年再引动刑（如寅巳申中一字）且天干克合官星，视为破坏。
    此处简化为：流年地支参与刑且天干为日主之官杀（加重官杀则易崩）。
    """
    # 若需严格「破坏合局天干」可在此扩展；当前采用「触刑即可能崩」的保守逻辑
    return True


def check_a50_collapse(
    current_pattern: str,
    transit_pillar: str,
    *,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    A-50 刑合格坍缩监听。
    条件：current_pattern == 'A-50' 且 transit_pillar 触发刑局且破坏合局。
    返回：{ "triggered": bool, "alert": "CRITICAL_STRUCTURE_COLLAPSE", "verdict": str, "ui_highlight": "red" }。
    """
    out = {
        "triggered": False,
        "alert": "",
        "verdict": "",
        "ui_highlight": "",
    }
    if (current_pattern or "").strip().upper() != "A-50":
        return out
    if not transit_pillar or len(transit_pillar) < 2:
        return out
    stem, branch = transit_pillar[0], transit_pillar[1]
    if not _transit_triggers_xing(branch):
        return out
    if not _transit_breaks_he(stem, branch, config):
        return out
    out["triggered"] = True
    out["alert"] = "CRITICAL_STRUCTURE_COLLAPSE"
    out["verdict"] = CRITICAL_STRUCTURE_COLLAPSE_VERDICT
    out["ui_highlight"] = "red"
    return out


def run_dynamic_monitor(
    current_pattern: str,
    transit_pillar: str,
    *,
    config_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    运行所有动态监听项，返回触发的告警列表。
    UI 层可据此弹出红色高亮并调用 RAG 注入判词。
    """
    config = {}
    path = config_path or ROOT / "config" / "dynamic_manifold.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            pass
    alerts = []
    a50 = check_a50_collapse(current_pattern, transit_pillar, config=config)
    if a50.get("triggered"):
        alerts.append(a50)
    return alerts


if __name__ == "__main__":
    # 命令行快速测试
    import sys
    pattern = sys.argv[1] if len(sys.argv) > 1 else "A-50"
    transit = sys.argv[2] if len(sys.argv) > 2 else "庚寅"
    r = check_a50_collapse(pattern, transit)
    print(json.dumps(r, ensure_ascii=False, indent=2))
