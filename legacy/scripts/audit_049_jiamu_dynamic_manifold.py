#!/usr/bin/env python3
"""
第 049/050 号 · 甲木日主「伤官大运 + 七杀流年」专项动态流形审计
========================================================================
审计场景：甲木身旺、正官格基底；大运丁卯（伤官）、流年庚子（七杀）；月令午（子午冲）。
输出：位移轨迹、格局捕获、对撞预警、RAG 判词红线（脊背发凉版）。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.physics.dynamic_engine import (
    compute_dynamic_tensor,
    manifold_capture,
    collision_warning,
    load_config,
)

DIM_ORDER = ["E", "O", "M", "S", "R"]


def run_audit() -> None:
    # 甲木日主，身旺正官格基底：能量略高、秩序偏强、压力可控
    natal_5d = {
        "E": 0.62,
        "O": 0.72,
        "M": 0.38,
        "S": 0.32,
        "R": 0.48,
    }
    day_master = "甲"
    month_branch = "午"   # 月令午 → 流年支子与月支 子午冲，S 轴应力脉冲
    major_pillar = "丁卯" # 伤官大运：丁火泄身，O 轴下拉、E 波动
    annual_pillar = "庚子" # 七杀流年：庚金克身，S 轴骤升；子午冲再推 S
    geo_region = "中"

    config = load_config()
    tensor = compute_dynamic_tensor(
        natal_5d,
        major_pillar=major_pillar,
        annual_pillar=annual_pillar,
        geo_region=geo_region,
        month_branch=month_branch,
        day_master=day_master,
        config=config,
    )
    dynamic_point = tensor["dynamic_point"]
    manifold_result = manifold_capture(dynamic_point, natal_5d, config=config)
    collision = collision_warning(dynamic_point, manifold_result=manifold_result, config=config)

    # ---------- 报告输出 ----------
    print()
    print("=" * 72)
    print("  FDS 第 049/050 号 · 甲木日主「伤官大运 + 七杀流年」动态流形审计报告")
    print("=" * 72)
    print()
    print("【审计场景】")
    print("  日主: 甲木  月令: 午  大运: 丁卯（伤官）  流年: 庚子（七杀）  地域: 中")
    print("  物理: 伤官泄秀 → O 轴下拉、秩序松动；七杀攻身 + 子午冲 → S 轴应力脉冲。")
    print()
    print("【1. 位移轨迹】")
    disp = tensor.get("displacement", {})
    for d in DIM_ORDER:
        v = disp.get(d, 0)
        arrow = "↑" if v > 0 else "↓" if v < 0 else "→"
        print(f"  {d} 轴位移: {v:+.3f} {arrow}")
    print()
    print("  原局 5D:", "  ".join(f"{d}={natal_5d.get(d,0):.2f}" for d in DIM_ORDER))
    print("  动态 5D:", "  ".join(f"{d}={dynamic_point.get(d,0):.2f}" for d in DIM_ORDER))
    print()
    print("  解读: 伤官大运将 O 轴下拉（秩序弱化、名利浮现而实操转虚）；")
    print("        七杀流年 + 子午冲将 S 轴大幅推高，进入高压对撞区。")
    print()
    print("【2. 引透与刑冲】")
    print("  流年透月令 (tougan_triggered):", tensor.get("tougan_triggered", False))
    print("  大运透月令 (major_tougan_triggered):", tensor.get("major_tougan_triggered", False))
    for it in tensor.get("interaction_deltas", []):
        print("  交互:", it.get("pair"), "→ delta 已叠加")
    print()
    print("【3. 流形捕获】")
    print("  当前归属格局:", manifold_result.get("pattern_id") or "—")
    print("  次近格局:", manifold_result.get("second_pattern_id") or "—")
    print("  格局对撞态 (is_double_capture):", manifold_result.get("is_double_capture", False))
    dv = manifold_result.get("displacement_vector") or {}
    print("  位移矢量 (原局→动态):", "  ".join(f"{k}={dv.get(k,0):+.2f}" for k in DIM_ORDER))
    print()
    print("  轨迹解读: displacement_vector 符号指示「正在逃离秩序」或「被迫回归体制」；")
    print("            O 负向 = 逃离秩序，O 正向 = 回归体制；S 正向 = 压力骤增。")
    print()
    print("【4. 对撞预警】")
    print("  进入对撞区:", collision.get("in_collision_zone", False))
    print("  S 轴当前值:", collision.get("s_value"), "  阈值:", collision.get("s_threshold"))
    print("  source_pattern:", collision.get("source_pattern"))
    print("  target_pattern:", collision.get("target_pattern"))
    print("  collision_type:", collision.get("collision_type"))
    print("  message:", collision.get("message", ""))
    print()
    print("【5. RAG 判词红线】")
    if tensor.get("major_tougan_triggered"):
        print("  · 大运透月令：埋藏的欲望被时代唤醒 → 必须给出「名利浮现，实操转虚」定性。")
    if manifold_result.get("is_double_capture"):
        print("  · 格局对撞态：禁止模棱两可；必须指出流形不稳定性带来的内耗代价（决策摇摆/多重人格冲突）。")
    if collision.get("in_collision_zone"):
        if collision.get("s_value", 0) > (collision.get("s_threshold") or 1.8):
            print("  · 子午冲应力脉冲致 S 轴突破阈值 → 必须启动「紧急避险建议」与应灾指引。")
        else:
            print("  · 进入对撞区 → 调 RAG 应灾指引。")
    # 子午冲应力测试说明：配置中 子午冲 delta S=1.2，原局 S 略高或再叠它冲即可破 1.8
    if not collision.get("in_collision_zone") and (disp.get("S") or 0) > 1.0:
        print("  · 子午冲已叠加，S 轴位移 +1.2；本例未破 1.8。若原局 S 更高或再遇它冲，必触发紧急避险。")
    print()
    print("=" * 72)
    print("  第 049/050 号指令 · 甲木伤官大运七杀流年专项审计完成")
    print("=" * 72)
    print()


if __name__ == "__main__":
    run_audit()
