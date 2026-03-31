#!/usr/bin/env python3
"""
第 043 号终极封卷：三专项语义对撞验收
======================================
第一专项：伤官见官 (A-07 vs A-01) — 随机抽 10 例 D_M>2.5，检查判词是否指出「财星/商业缓冲」。
第二专项：羊刃架杀 (A-02 vs A-10) — S≥1.5 时 BalanceAuditor 用神是否指向印星/R 轴。
第三专项：印星制伤 (A-07 vs A-08) — 判词是否出现「才华合法化包装」「学术沉淀化解批判」等。

用法:
  python scripts/seal_043_final_verification.py --data data/holographic_universe_518k.jsonl
  python scripts/seal_043_final_verification.py --run-verdict  # 对第一专项 10 例调用 32B 判词并做红线检查
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

try:
    from json_logic import jsonLogic
except ImportError:
    print("❌ 需要 json-logic-qubit")
    sys.exit(1)

from build_a01_full_index import (
    load_manifest,
    get_weights_matrix,
    calculate_5d_tensor,
    normalize_case_for_logic,
    resolve_manifest_for_pattern,
)

DIM_ORDER = ["E", "O", "M", "S", "R"]
O_IDX, S_IDX = 1, 3


def load_manifold_stats(npz_path: Path):
    data = np.load(npz_path)
    points = data["points"]
    mu = np.mean(points, axis=0)
    cov = np.cov(points.T) if points.shape[0] > 1 else np.eye(5) * 0.01
    return mu, cov


def mahalanobis_d(point: np.ndarray, mu: np.ndarray, cov: np.ndarray) -> float:
    delta = point - mu
    try:
        inv = np.linalg.pinv(cov)
        return float(np.sqrt(max(0.0, delta.T @ inv @ delta)))
    except Exception:
        return float(np.linalg.norm(delta))


def collect_shangguan_jian_guan_dm_above(
    data_path: Path,
    out_dir: Path,
    dm_threshold: float = 2.5,
    limit: int | None = None,
):
    """收集伤官见官且 D_M > dm_threshold 的 (line_index, case)。"""
    m07 = load_manifest(resolve_manifest_for_pattern("A-07"))
    m01 = load_manifest(resolve_manifest_for_pattern("A-01"))
    w07, gods07 = get_weights_matrix(m07, resolve_manifest_for_pattern("A-07"))
    god_index = {g: i for i, g in enumerate(gods07)}
    expr07 = (m07.get("classical_logic_rules") or {}).get("pipeline_expression") or (m07.get("classical_logic_rules") or {}).get("expression")
    expr01 = (m01.get("classical_logic_rules") or {}).get("pipeline_expression") or (m01.get("classical_logic_rules") or {}).get("expression")
    mu07, cov07 = load_manifold_stats(out_dir / "a07_full_points.npz")

    candidates = []
    total = 0
    with open(data_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            if limit and total >= limit:
                break
            total += 1
            try:
                case = json.loads(line)
                case = normalize_case_for_logic(case)
                if not jsonLogic(expr07, case) or not jsonLogic(expr01, case):
                    continue
                tensor = calculate_5d_tensor(case["ten_gods"], w07, god_index)
                d_m = mahalanobis_d(tensor, mu07, cov07)
                if d_m > dm_threshold:
                    candidates.append((i, case, float(d_m)))
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
    return candidates


def run_verdict_for_cases(cases_with_refs: list, n_sample: int = 10) -> list:
    """对抽样命例运行对撞+混合判词，返回 (ref, verdict_text, red_line_passed)。"""
    from core.pattern_collider import run_pattern_collision
    from core.ai_engine import generate_combined_pattern_verdict

    sampled = random.sample(cases_with_refs, min(n_sample, len(cases_with_refs)))
    results = []
    for line_index, case, d_m in sampled:
        ten_gods = case.get("ten_gods") or {}
        try:
            patterns = run_pattern_collision(ten_gods, temperature=1.0)
            point_5d = {"E": 0.0, "O": 0.0, "M": 0.0, "S": 0.0, "R": 0.0}
            total_w = 0.0
            for p in patterns:
                w = (p.get("confidence_pct") or 0) / 100.0
                pt = p.get("point_5d") or {}
                for k in point_5d:
                    point_5d[k] = point_5d[k] + w * float(pt.get(k, 0))
                total_w += w
            if total_w > 0:
                for k in point_5d:
                    point_5d[k] = round(point_5d[k] / total_w, 4)
            out = generate_combined_pattern_verdict(
                patterns, point_5d, ten_gods=ten_gods,
                dominant_pattern_id=patterns[0].get("pattern_id") if patterns else None,
            )
            text = (out.get("text") or "") + (out.get("error") or "")
            # 红线：判词须出现财星/商业/缓冲等，仅「口舌是非」为不合格
            has_cai = any(kw in text for kw in ("财", "商业", "缓冲", "变现", "通关", "财星"))
            only_koushe = "口舌" in text and not has_cai
            red_line_passed = has_cai and not (only_koushe and len(text) < 100)
        except Exception as e:
            text = f"[判词调用失败] {e}"
            red_line_passed = False
        results.append({
            "line_index": line_index,
            "case_id": case.get("case_id") or case.get("id") or str(line_index),
            "d_m": d_m,
            "verdict_snippet": (text[:400] + "…") if len(text) > 400 else text,
            "red_line_财星缓冲": red_line_passed,
        })
    return results


def main():
    import argparse
    p = argparse.ArgumentParser(description="第 043 号终极封卷三专项验收")
    p.add_argument("--data", type=Path, default=None)
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--limit", type=int, default=None, help="扫描行数上限（测试用）")
    p.add_argument("--run-verdict", action="store_true", help="对第一专项 10 例调用 32B 判词")
    p.add_argument("--dm-threshold", type=float, default=2.5)
    p.add_argument("--sample", type=int, default=10)
    args = p.parse_args()

    data_path = args.data or ROOT / "data" / "holographic_universe_518k.jsonl"
    if not data_path.exists():
        data_path = ROOT / "data_local" / "holographic_universe_518k.jsonl"
    if not data_path.exists():
        print("❌ 未找到 518k 数据")
        sys.exit(1)
    out_dir = args.out or ROOT / "data_local"

    print("--- 第一专项：伤官见官 D_M >", args.dm_threshold, "抽样 ---")
    candidates = collect_shangguan_jian_guan_dm_above(data_path, out_dir, dm_threshold=args.dm_threshold, limit=args.limit)
    print(f"   伤官见官且 D_M > {args.dm_threshold} 的样本数: {len(candidates)}")
    if not candidates:
        print("   无样本，请降低 --dm-threshold 或检查数据。")
        sys.exit(0)
    random.seed(43)
    sampled = random.sample(candidates, min(args.sample, len(candidates)))
    print(f"   随机抽取 {len(sampled)} 例: line_index =", [s[0] for s in sampled])

    if args.run_verdict:
        print("\n--- 判词验收（红线：须出现财星/商业/缓冲，仅「口舌是非」不合格）---")
        results = run_verdict_for_cases(candidates, n_sample=args.sample)
        for i, r in enumerate(results, 1):
            print(f"\n  [{i}] line={r['line_index']} D_M={r['d_m']:.3f} 红线通过={r['red_line_财星缓冲']}")
            print("  ", r["verdict_snippet"][:200].replace("\n", " "))
        passed = sum(1 for r in results if r["red_line_财星缓冲"])
        print(f"\n  合计: {passed}/{len(results)} 例通过红线。")
    else:
        print("\n  提示: 加 --run-verdict 可对上述 10 例调用 32B 判词并做红线检查。")

    print("\n--- 第二专项：羊刃架杀 (A-02 vs A-10) ---")
    print("  验收动作: 对 S 轴≥1.5 的命例观察 BalanceAuditor 用神是否指向印星(R 轴)。")
    print("  红线: 用神须体现「以柔克刚」；判词须体现「英雄主义的代价」「权力边缘的冒险」。")

    print("\n--- 第三专项：印星制伤 (A-07 vs A-08) ---")
    print("  语义验收: 判词须出现「才华的合法化包装」或「学术沉淀化解批判锋芒」等表述。")

    print("\n✅ 三专项验收清单已输出。完成人工抽检后执行: 审计报告归档 → 索引 ENFORCED → UI 默认白话。")


if __name__ == "__main__":
    main()
