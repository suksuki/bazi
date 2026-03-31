#!/usr/bin/env python3
"""
第 043 号工程指令：混合格局 IoU 与稳定性审计（伤官见官专项）
================================================================
当命盘同时触发 A-07（伤官）与 A-01（正官）时，审计：
1. 综合 O 轴（秩序）是否跌破该格局质心 μ_O - 2σ_O；
2. 伤官见官样本的 D_M（马氏距离）离散度；
3. 输出物理溢出报告摘要，供 Step 6 验收与判词验收标准（通关神/手术刀式建议）对照。

用法:
  python scripts/audit_mixed_iou_stability.py
  python scripts/audit_mixed_iou_stability.py --data data/holographic_universe_518k.jsonl --limit 100000
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

try:
    from json_logic import jsonLogic
except ImportError:
    print("❌ 需要 json-logic-qubit。pip install json-logic-qubit")
    sys.exit(1)

from build_a01_full_index import (
    load_manifest,
    get_weights_matrix,
    calculate_5d_tensor,
    normalize_case_for_logic,
    resolve_manifest_for_pattern,
)

DIM_ORDER = ["E", "O", "M", "S", "R"]
O_IDX = 1


def load_manifold_stats(npz_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """从格局 npz 计算质心 μ 与协方差 Σ。"""
    data = np.load(npz_path)
    points = data["points"]
    mu = np.mean(points, axis=0)
    if points.shape[0] > 1:
        cov = np.cov(points.T)
    else:
        cov = np.eye(5) * 0.01
    return mu, cov


def mahalanobis_d(point: np.ndarray, mu: np.ndarray, cov: np.ndarray) -> float:
    """马氏距离。"""
    delta = point - mu
    try:
        inv = np.linalg.pinv(cov)
        d_sq = float(delta.T @ inv @ delta)
        return float(np.sqrt(max(0.0, d_sq)))
    except Exception:
        return float(np.linalg.norm(delta))


def run_audit(
    data_path: Path,
    out_dir: Path,
    limit: int | None = None,
) -> dict:
    """
    筛选「伤官见官」样本（同时满足 A-07 与 A-01 pipeline），
    用 A-07 的 TMM 投影 5D，相对 A-07 流形算 D_M 与 O 轴统计。
    """
    manifest_a07_path = resolve_manifest_for_pattern("A-07")
    manifest_a01_path = resolve_manifest_for_pattern("A-01")
    if not manifest_a07_path.exists() or not manifest_a01_path.exists():
        raise FileNotFoundError("A-07 或 A-01 manifest 不存在")
    m07 = load_manifest(manifest_a07_path)
    m01 = load_manifest(manifest_a01_path)
    w07, gods07 = get_weights_matrix(m07, manifest_a07_path)
    god_index = {g: i for i, g in enumerate(gods07)}
    expr07 = (m07.get("classical_logic_rules") or {}).get("pipeline_expression") or (m07.get("classical_logic_rules") or {}).get("expression")
    expr01 = (m01.get("classical_logic_rules") or {}).get("pipeline_expression") or (m01.get("classical_logic_rules") or {}).get("expression")
    if not expr07 or not expr01:
        raise ValueError("A-07 或 A-01 缺少 pipeline_expression")

    npz07 = out_dir / "a07_full_points.npz"
    if not npz07.exists():
        raise FileNotFoundError(f"A-07 索引不存在: {npz07}，请先运行 fds_pattern_scanner --target A-07")
    mu07, cov07 = load_manifold_stats(npz07)
    mu_O = float(mu07[O_IDX])
    sigma_O = float(np.sqrt(cov07[O_IDX, O_IDX])) if cov07[O_IDX, O_IDX] > 0 else 0.1
    threshold_O_low = mu_O - 2 * sigma_O

    dual_hit_points: list[np.ndarray] = []
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
                dual_hit_points.append(tensor)
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
            if total % 100000 == 0 and total > 0:
                print(f"   已扫描 {total:,} 行, 伤官见官: {len(dual_hit_points):,}", end="\r")

    if not dual_hit_points:
        return {
            "phenomenon": "伤官见官",
            "total_scanned": total,
            "dual_hit_count": 0,
            "o_axis": {},
            "d_m": {},
            "o_below_2sigma_count": 0,
            "conclusion": "无伤官见官双命中样本，无法进行 O 轴坍缩审计。",
        }

    points = np.array(dual_hit_points, dtype=np.float64)
    o_vals = points[:, O_IDX]
    d_m_vals = np.array([mahalanobis_d(p, mu07, cov07) for p in points], dtype=np.float64)

    o_below = int(np.sum(o_vals < threshold_O_low))
    o_mean = float(np.mean(o_vals))
    o_std = float(np.std(o_vals))
    dm_mean = float(np.mean(d_m_vals))
    dm_std = float(np.std(d_m_vals))

    report = {
        "phenomenon": "伤官见官 (A-07 & A-01)",
        "total_scanned": total,
        "dual_hit_count": len(points),
        "abundance_pct": round(100.0 * len(points) / total, 4),
        "o_axis": {
            "mean": round(o_mean, 4),
            "std": round(o_std, 4),
            "mu_manifold_A07": round(mu_O, 4),
            "sigma_manifold_A07": round(sigma_O, 4),
            "threshold_2sigma_below": round(threshold_O_low, 4),
            "count_below_2sigma": o_below,
            "pct_below_2sigma": round(100.0 * o_below / len(points), 2),
        },
        "d_m": {
            "mean": round(dm_mean, 4),
            "std": round(dm_std, 4),
        },
        "o_below_2sigma_count": o_below,
        "conclusion": (
            f"伤官见官样本 {len(points):,} 例（丰度 {100*len(points)/total:.2f}%）。"
            f"O 轴均值 {o_mean:.3f}，{o_below} 例（{100*o_below/len(points):.1f}%）低于 μ_O-2σ_O={threshold_O_low:.3f}，"
            f"存在秩序轴坍缩倾向。D_M 均值 {dm_mean:.3f}（离散度 σ={dm_std:.3f}）。"
            "判词验收：须识别「挑战权威的代价」与「才华变现的出口」，并给出通关神（如财星）建议。"
        ),
    }
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="伤官见官混合格局 IoU/稳定性审计")
    parser.add_argument("--data", type=Path, default=None, help="518k jsonl 路径")
    parser.add_argument("--out", type=Path, default=None, help="data_local 目录")
    parser.add_argument("--limit", type=int, default=None, help="最多扫描行数（测试用）")
    parser.add_argument("--write", type=Path, default=None, help="写出报告 JSON 路径")
    args = parser.parse_args()

    data_path = args.data or ROOT / "data" / "holographic_universe_518k.jsonl"
    if not data_path.exists():
        data_path = ROOT / "data_local" / "holographic_universe_518k.jsonl"
    if not data_path.exists():
        print(f"❌ 未找到数据: {data_path}")
        sys.exit(1)
    out_dir = args.out or ROOT / "data_local"

    print("--- 伤官见官 (A-07 vs A-01) 物理坍缩审计 ---")
    report = run_audit(data_path, out_dir, limit=args.limit)
    print()
    print("【审计结果】")
    print(f"  扫描行数: {report['total_scanned']:,}")
    print(f"  伤官见官双命中: {report['dual_hit_count']:,} ({report.get('abundance_pct', 0):.2f}%)")
    if report["dual_hit_count"] > 0:
        o = report["o_axis"]
        print(f"  O 轴: 均值={o['mean']}, 标准差={o['std']}, 低于 μ-2σ 样本数={o['count_below_2sigma']} ({o['pct_below_2sigma']}%)")
        print(f"  D_M: 均值={report['d_m']['mean']}, 离散度 σ={report['d_m']['std']}")
    print()
    print("【结论】")
    print("  ", report["conclusion"])

    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        with open(args.write, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n报告已写入: {args.write}")


if __name__ == "__main__":
    main()
