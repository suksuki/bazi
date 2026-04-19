#!/usr/bin/env python3
"""V17.11 极端碰撞压力测试：三合/三刑/空亡/长生等同时满足阈值时，插件链路与耗时。"""
from __future__ import annotations

import os
import sys
import time

# 从仓库根 qiazhi 运行：PYTHONPATH=. python v17_rebirth/scripts/stress_plugin_collision.py
# …/qiazhi/v17_rebirth/scripts → qiazhi 根目录
_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from v17_rebirth.backend.logic import plugin_discovery as pd  # noqa: E402
from v17_rebirth.backend.services.verdict_orchestrator import VerdictOrchestrator  # noqa: E402


def _run_case(label: str, raw: dict, orch: VerdictOrchestrator) -> None:
    pd.clear_logic_module_cache()
    snap = orch.snapshot_frame(raw_physics=raw)
    payload = snap.get("payload") or {}
    hits = (payload.get("debug_trace") or {}).get("hits") or []
    facts = (payload.get("debug_trace") or {}).get("facts") or []
    order = pd.plugin_execution_order_map()
    # 抽样：manifest L1 与 L2 格局的执行序应随 registry 单调
    sample_ids = [
        "l1.physics.op_branch_sanxing",
        "l1.physics.op_branch_liuchong",
        "classical.pattern.axis.v1",
        "classical.blind.work_axis.v1",
    ]
    order_snippet = {pid: order.get(pid) for pid in sample_ids if pid in order}
    print(f"--- {label} ---")
    print(f"  plugin_hits: {len(hits)} → {hits}")
    print(f"  facts: {len(facts)}")
    print(f"  execution_order (sample): {order_snippet}")


def main() -> None:
    pd.clear_logic_module_cache()
    raw_complex = {
        "four_pillars": {"year": "丙寅", "month": "癸巳", "day": "戊申", "hour": "甲寅"},
        "luck_pillar": "庚午",
        "flow_pillar": "甲辰",
        "deity_scores": {
            "食神": 45.0,
            "正财": 20.0,
            "偏财": 15.0,
            "比肩": 25.0,
            "劫财": 10.0,
            "正官": 25.0,
            "偏印": 30.0,
            "伤官": 22.0,
        },
    }
    raw_simple = {
        "four_pillars": {"year": "甲子", "month": "甲子", "day": "甲子", "hour": "甲子"},
        "luck_pillar": "乙丑",
        "flow_pillar": "丙寅",
        "deity_scores": dict(raw_complex["deity_scores"]),
    }
    orch = VerdictOrchestrator(repo_root=_REPO)

    t0 = time.perf_counter()
    n = 80
    for _ in range(n):
        orch.snapshot_frame(raw_physics=raw_complex)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0 / n

    print("=== V17.13 stress_plugin_collision ===")
    print(f"avg VerdictOrchestrator.snapshot_frame over {n} runs (complex): {elapsed_ms:.3f} ms")
    _run_case("复杂四柱（寅巳申/冲害合等）", raw_complex, orch)
    _run_case("简单四柱（四同柱，交互较少）", raw_simple, orch)
    snap = orch.snapshot_frame(raw_physics=raw_complex)
    payload = snap.get("payload") or {}
    decisions = payload.get("pending_decisions") or []
    print("Decision Inbox items (complex, backend cap 64):", len(decisions))
    for d in decisions[:12]:
        print(f"  - [{d.get('source')}] {str(d.get('label', ''))[:48]}...")
    if elapsed_ms > 50.0:
        print("WARN: average > 50ms budget")
    else:
        print("OK: under 50ms average budget")
    print("Note: LLM 长判词缝合走 narrator_frames / RealtimeNarrativePipeline，本脚本未调用异步 LLM。")


if __name__ == "__main__":
    main()
