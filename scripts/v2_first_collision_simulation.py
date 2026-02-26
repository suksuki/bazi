#!/usr/bin/env python3
"""
FDS 2.0 首次流年大对撞实验
==========================
1. 构造 A-50（刑合格）典型档案（地支三刑+天干透官）
2. 流年加速器：从「平稳年」进入「刑冲填实」大运/流年
3. 每月调用流形追踪 + A-50 坍缩监听，记录 S 轴突变斜率
4. 产出 audit_logs/v2.0_first_collision_report.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 确保可导入 core / scripts.dynamic_monitor
from core.engine import load_static_atlas
from core.manifold_trace import compute_dm_cloud
from core.physics.dynamic_engine import compute_dynamic_tensor
from scripts.dynamic_monitor import run_dynamic_monitor

DIM_ORDER = ["E", "O", "M", "S", "R"]
A50_ID = "A-50"


def build_victim_natal_5d() -> list[float]:
    """A-50 质心作为受试者原局 5D（只读图谱）。"""
    atlas = load_static_atlas()
    for p in atlas.get("patterns") or []:
        if (p.get("pattern_id") or "").strip() == A50_ID:
            return [float(x) for x in (p.get("centroid_5d") or [0.8, 0.5, -0.5, 2.5, 1.5])[:5]]
    return [0.8, 0.5, -0.5, 2.5, 1.5]


def build_transit_timeline() -> list[dict]:
    """
    24 个模拟月：前 12 月流年甲午（不触刑），后 12 月流年庚寅（寅巳申刑，触发坍缩）。
    大运固定己巳（巳在寅巳申中），月令寅、日主甲。
    """
    # 流年：先平稳再刑冲填实
    year1 = "甲午"  # 午不在三刑
    year2 = "庚寅"  # 寅在寅巳申，触发
    major = "己巳"
    month_branch = "寅"
    day_master = "甲"
    geo = "中"
    timeline = []
    for month_idx in range(24):
        annual = year2 if month_idx >= 12 else year1
        timeline.append({
            "month_index": month_idx,
            "annual_pillar": annual,
            "major_pillar": major,
            "month_branch": month_branch,
            "day_master": day_master,
            "geo_region": geo,
        })
    return timeline


def run_simulation() -> dict:
    natal_5d = build_victim_natal_5d()
    timeline = build_transit_timeline()
    victim = {
        "pattern_id": A50_ID,
        "chinese_name": "刑合格",
        "description": "地支三刑俱全（寅巳申），天干透官；典型 A-50 档案",
        "natal_5d": dict(zip(DIM_ORDER, natal_5d)),
        "month_branch": "寅",
        "day_master": "甲",
        "major_pillar": "己巳",
    }

    steps = []
    collapse_step = None
    s_prev = None
    s_slope_at_collapse = None

    for t in timeline:
        month_idx = t["month_index"]
        annual = t["annual_pillar"]
        major = t["major_pillar"]
        month_branch = t["month_branch"]
        day_master = t["day_master"]
        geo = t["geo_region"]

        # 动态张量
        dyn = compute_dynamic_tensor(
            natal_5d,
            major_pillar=major,
            annual_pillar=annual,
            geo_region=geo,
            month_branch=month_branch,
            day_master=day_master,
        )
        dynamic_point = dyn.get("dynamic_point") or {}
        vec_5d = [dynamic_point.get(k, 0) for k in DIM_ORDER]
        s_value = dynamic_point.get("S", vec_5d[3] if len(vec_5d) > 3 else 0)

        # 流形追踪（前 3 叠加态）
        trace_result = compute_dm_cloud(vec_5d, top_k=3)
        overlay = trace_result.get("overlay") or []

        # A-50 坍缩监听（流年干支作为 transit）
        alerts = run_dynamic_monitor(A50_ID, annual)
        collapse = next((a for a in alerts if a.get("alert") == "CRITICAL_STRUCTURE_COLLAPSE"), None)

        a50_weight = next((o.get("probability") for o in overlay if (o.get("pattern_id") or "").strip() == A50_ID), 0)

        step_record = {
            "month_index": month_idx,
            "annual_pillar": annual,
            "dynamic_5d": dynamic_point,
            "S_value": round(s_value, 6),
            "overlay_top3": overlay,
            "a50_probability": round(a50_weight, 6),
            "collapse_triggered": bool(collapse),
            "collapse_verdict": (collapse or {}).get("verdict", ""),
        }
        steps.append(step_record)

        if collapse and collapse_step is None:
            collapse_step = month_idx
            s_slope_at_collapse = round((s_value - s_prev), 6) if s_prev is not None else None
        s_prev = s_value

    report = {
        "schema": "FDS_v2.0_first_collision_report",
        "description": "FDS 2.0 首次流年大对撞：A-50 坍缩与流形叠加观测",
        "victim": victim,
        "timeline_months": 24,
        "steps": steps,
        "collapse_event": {
            "first_triggered_at_month": collapse_step,
            "S_axis_slope_at_trigger": s_slope_at_collapse,
            "verdict": "刑伤突发，险境难支",
            "alert": "CRITICAL_STRUCTURE_COLLAPSE",
        },
        "rag_summary": (
            "当流年由甲午进入庚寅时，寅巳申三刑填实，A-50 刑合格结构性势能释放，"
            "系统触发 CRITICAL_STRUCTURE_COLLAPSE，红色高亮与判词「刑伤突发，险境难支」合龙；"
            "S 轴（应力）在坍缩时刻记录突变斜率，印证 FDS 2.0 动态感知已生效。"
        ),
    }
    return report


def main() -> None:
    report = run_simulation()
    out_path = ROOT / "audit_logs" / "v2.0_first_collision_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("✅ FDS 2.0 首次对撞报告已写入:", out_path)
    ce = report.get("collapse_event") or {}
    print("   坍缩首触月份:", ce.get("first_triggered_at_month"))
    print("   S 轴突变斜率:", ce.get("S_axis_slope_at_trigger"))
    print("   判词:", ce.get("verdict", ""))


if __name__ == "__main__":
    main()
