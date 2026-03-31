#!/usr/bin/env python3
"""
第 041 号工程指令 · 对撞引擎 + 判词 压力测试
============================================
模拟约 10 个并发请求调用「多格局对撞 + 混合 5D 上下文」，
可选叠加 32B 判词生成，统计延迟与缓存效果。

用法（需在项目 venv 下执行，确保依赖已安装）:
  python scripts/stress_test_collider_verdict.py              # 仅对撞 + 混合上下文（无 Ollama）
  python scripts/stress_test_collider_verdict.py --with-verdict  # 含判词生成（需本地 Ollama）
  python scripts/stress_test_collider_verdict.py -n 20        # 并发数
  python scripts/stress_test_collider_verdict.py --rounds 3   # 轮数（第2轮起同八字测缓存）
"""
from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


# 测试用八字（年柱 月柱 日柱 时柱），日主取日柱天干
TEST_CHARTS = [
    (["甲子", "丙寅", "戊辰", "庚午"], "戊"),
    (["乙丑", "丁卯", "己巳", "辛未"], "己"),
    (["庚午", "壬申", "甲戌", "丙子"], "甲"),
    (["辛未", "癸酉", "乙亥", "丁丑"], "乙"),
    (["丙子", "戊寅", "庚辰", "壬午"], "庚"),
    (["丁丑", "己卯", "辛巳", "癸未"], "辛"),
    (["壬午", "甲申", "丙戌", "戊子"], "丙"),
    (["癸未", "乙酉", "丁亥", "己丑"], "丁"),
    (["戊子", "庚寅", "壬辰", "甲午"], "壬"),
    (["己丑", "辛卯", "癸巳", "乙未"], "癸"),
]


def run_one_context(controller, chart: list, day_master: str, temperature: float = 1.0) -> float:
    """单次 get_mixed_pattern_context，返回耗时（秒）。"""
    t0 = time.perf_counter()
    controller.get_mixed_pattern_context(chart, day_master, temperature=temperature)
    return time.perf_counter() - t0


def run_one_verdict(controller, chart: list, day_master: str) -> float:
    """单次对撞 + 判词生成（含 32B 调用），返回耗时（秒）。"""
    from core.ai_engine import generate_combined_pattern_verdict
    t0 = time.perf_counter()
    ctx = controller.get_mixed_pattern_context(chart, day_master)
    patterns = ctx.get("probabilistic_patterns") or []
    point_5d = ctx.get("point_5d") or {}
    ten_gods = controller._chart_to_ten_gods(chart, day_master)
    dominant = patterns[0].get("pattern_id") if patterns else None
    generate_combined_pattern_verdict(
        probabilistic_patterns=patterns,
        point_5d=point_5d,
        ten_gods=ten_gods,
        dominant_pattern_id=dominant,
    )
    return time.perf_counter() - t0


def _percentile(sorted_times: list, p: float) -> float:
    if not sorted_times:
        return 0.0
    i = min(int((len(sorted_times) - 1) * p / 100.0), len(sorted_times) - 1)
    return sorted_times[i]


def main():
    parser = argparse.ArgumentParser(description="对撞 + 判词 压力测试（第 041 号）")
    parser.add_argument("-n", "--concurrency", type=int, default=10, help="并发数")
    parser.add_argument("--with-verdict", action="store_true", help="同时压测 32B 判词生成（需 Ollama）")
    parser.add_argument("--rounds", type=int, default=2, help="轮数：第1轮多八字冷启动，第2轮同八字测缓存")
    args = parser.parse_args()

    from controllers.holographic_pattern_controller import HolographicPatternController

    controller = HolographicPatternController()
    n = min(args.concurrency, len(TEST_CHARTS))
    charts = TEST_CHARTS[:n]
    mode = "对撞+判词" if args.with_verdict else "对撞+混合上下文"

    print(f"第 041 号 · 压力测试：{mode}，并发数={n}，轮数={args.rounds}\n")

    all_times: list[float] = []
    for round_no in range(1, args.rounds + 1):
        if round_no == 1:
            # 第一轮：不同八字，冷启动 / 缓存未命中
            tasks = [(c, dm) for c, dm in charts]
            label = "冷启动（多八字）"
        else:
            # 第二轮：同一八字重复请求，测缓存命中
            c, dm = charts[0]
            tasks = [(c, dm)] * n
            label = "缓存命中（同八字×%d）" % n

        times: list[float] = []
        with ThreadPoolExecutor(max_workers=n) as ex:
            if args.with_verdict:
                futures = {ex.submit(run_one_verdict, controller, c, dm): i for i, (c, dm) in enumerate(tasks)}
            else:
                futures = {ex.submit(run_one_context, controller, c, dm): i for i, (c, dm) in enumerate(tasks)}
            for fut in as_completed(futures):
                try:
                    elapsed = fut.result()
                    times.append(elapsed)
                except Exception as e:
                    print(f"  请求失败: {e}")
        times.sort()
        all_times.extend(times)
        if not times:
            continue
        p50 = _percentile(times, 50)
        p95 = _percentile(times, 95)
        print(f"  轮 {round_no} [{label}]  min={min(times):.3f}s  max={max(times):.3f}s  avg={sum(times)/len(times):.3f}s  p50={p50:.3f}s  p95={p95:.3f}s")

    if all_times:
        all_times.sort()
        print(f"\n  汇总: 总请求数={len(all_times)}  整体 p50={_percentile(all_times, 50):.3f}s  p95={_percentile(all_times, 95):.3f}s")
    print("\n✅ 第 041 号压力测试完成。")
    if args.rounds >= 2 and len(all_times) >= 2 * n:
        cold_avg = sum(all_times[:n]) / n if n else 0
        warm_len = min(n, len(all_times) - n)
        warm_avg = sum(all_times[n : n + warm_len]) / warm_len if warm_len else 0
        if cold_avg > 0:
            print(f"   缓存效果: 同八字第二轮平均耗时约为第一轮的 {100 * warm_avg / cold_avg:.0f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
