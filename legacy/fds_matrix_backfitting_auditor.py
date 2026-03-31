#!/usr/bin/env python3
"""
FDS 矩阵逆向拟合审计器 (Matrix Back-Fitting Auditor)
====================================================
[Step 8 / 第019号工程指令] 利用 A-01 成格样本逆向评估「十神 → 5D」转化矩阵的精准度。

目标：
- 用古典逻辑筛出的 A-01 样本在 5D 空间中的聚类紧密度，评估当前 TMM 的「解释力」
- 敏感度分析：微调权重后观察簇内方差/平均距离变化，给出校准建议
- 输出热力图与 [MATRIX WARNING] 轴级预警

依赖: numpy, json-logic-quibble；可选 matplotlib（热力图）。
用法:
  python fds_matrix_backfitting_auditor.py --data ./data/holographic_universe_518k.jsonl
  python fds_matrix_backfitting_auditor.py --limit 50000 --out ./sop_output  # 快速测试
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

try:
    from json_logic import jsonLogic
except ImportError:
    jsonLogic = None

# 路径默认
PROJECT_ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = PROJECT_ROOT / "config" / "patterns" / "manifest_A01.json"
DEFAULT_DATA = PROJECT_ROOT / "data" / "holographic_universe_518k.jsonl"
DIMS = ["E", "O", "M", "S", "R"]


def load_manifest(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_weights_matrix(manifest: Dict[str, Any]) -> Tuple[np.ndarray, List[str], Dict[str, int]]:
    tmm = manifest["tensor_mapping_matrix"]
    gods = list(tmm["ten_gods"])
    matrix = np.array([tmm["weights"][g] for g in gods], dtype=float)
    god_index = {g: i for i, g in enumerate(gods)}
    return matrix, gods, god_index


def get_weights_matrix_from_file(path: Path) -> Tuple[np.ndarray, List[str], Dict[str, int]]:
    """从 V4.0-BETA 等外部矩阵 JSON 加载（含 version / ten_gods / weights）。"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    gods = list(data.get("ten_gods", []))
    weights_dict = data.get("weights", {})
    matrix = np.array([weights_dict[g] for g in gods], dtype=float)
    god_index = {g: i for i, g in enumerate(gods)}
    return matrix, gods, god_index


def ten_gods_to_vec(case_ten_gods: Dict[str, Any], god_index: Dict[str, int], n_gods: int) -> np.ndarray:
    vec = np.zeros(n_gods)
    for g, v in case_ten_gods.items():
        if g in god_index:
            try:
                vec[god_index[g]] = float(v)
            except (TypeError, ValueError):
                pass
    return vec


def project_to_5d(vectors_10: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """vectors_10: (N, 10), weights: (10, 5) -> (N, 5)"""
    return vectors_10 @ weights


def collect_a01_samples(
    data_path: Path,
    logic_expression: Dict[str, Any],
    god_index: Dict[str, int],
    n_gods: int,
    limit: int | None = None,
) -> Tuple[np.ndarray, int, int]:
    """
    遍历 jsonl，用古典逻辑筛出 A-01 样本，返回 10 维向量矩阵 (N, 10) 以及 total/matched 计数。
    """
    if jsonLogic is None:
        raise RuntimeError("需要安装 json-logic-quibble 以执行古典逻辑筛选。pip install json-logic-quibble")
    if not data_path.exists():
        raise FileNotFoundError(f"数据文件不存在: {data_path}")
    rows: List[np.ndarray] = []
    total, matched = 0, 0
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            total += 1
            if limit and total > limit:
                break
            try:
                raw = json.loads(line)
                # 仅保留逻辑所需字段并转为纯 dict，避免部分 json_logic 实现对 dict_keys 等报错
                case = {
                    "ten_gods": dict(raw.get("ten_gods", {})),
                    "self_energy": dict(raw.get("self_energy", {})),
                }
                if not jsonLogic(logic_expression, case):
                    continue
                matched += 1
                vec = ten_gods_to_vec(case["ten_gods"], god_index, n_gods)
                rows.append(vec)
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
            if total % 50000 == 0:
                print(f"   进度: {total:,} 行，A-01 匹配: {matched:,}", end="\r")
    print()
    if not rows:
        raise ValueError("未找到任何 A-01 成格样本，无法进行矩阵审计。")
    return np.array(rows), total, matched


def cluster_metrics(points_5d: np.ndarray) -> Dict[str, Any]:
    """points_5d: (N, 5). 返回质心、各轴标准差、平均到质心欧氏距离。"""
    centroid = np.mean(points_5d, axis=0)
    std_per_axis = np.std(points_5d, axis=0)
    dists = np.linalg.norm(points_5d - centroid, axis=1)
    mean_dist = float(np.mean(dists))
    return {
        "centroid": centroid,
        "std_per_axis": dict(zip(DIMS, std_per_axis.tolist())),
        "mean_distance_to_centroid": mean_dist,
        "sample_count": points_5d.shape[0],
    }


def sensitivity_analysis(
    vectors_10: np.ndarray,
    base_weights: np.ndarray,
    gods: List[str],
    base_mean_dist: float,
    step_pct: float = 0.10,
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    对每个 (十神, 轴) 微调 ±step_pct，观察 mean_distance 变化。
    返回 (efficacy 热力图矩阵 10x5, 校准建议列表)。
    """
    n_gods, n_dims = base_weights.shape
    efficacy = np.zeros((n_gods, n_dims))  # 正数表示增加该权重可减小距离
    suggestions: List[Dict[str, Any]] = []
    for g in range(n_gods):
        for d in range(n_dims):
            w0 = base_weights[g, d]
            for mult, direction in [(1.0 + step_pct, "increase"), (1.0 - step_pct, "decrease")]:
                W = base_weights.copy()
                W[g, d] = w0 * mult
                points_5d = project_to_5d(vectors_10, W)
                centroid = np.mean(points_5d, axis=0)
                mean_d = float(np.mean(np.linalg.norm(points_5d - centroid, axis=1)))
                delta = base_mean_dist - mean_d  # 正 => 该方向使簇更紧
                if direction == "increase":
                    efficacy[g, d] = delta
                    if delta > 0:
                        suggestions.append({
                            "ten_god": gods[g],
                            "axis": DIMS[d],
                            "direction": "+",
                            "suggested_note": f"增加 {gods[g]} 对 {DIMS[d]} 轴权重约 {int(step_pct*100)}% 可提升聚类紧度",
                            "improvement": round(delta, 6),
                        })
                else:
                    if delta > 0:
                        suggestions.append({
                            "ten_god": gods[g],
                            "axis": DIMS[d],
                            "direction": "-",
                            "suggested_note": f"减少 {gods[g]} 对 {DIMS[d]} 轴权重约 {int(step_pct*100)}% 可提升聚类紧度",
                            "improvement": round(delta, 6),
                        })
    suggestions.sort(key=lambda x: -x["improvement"])
    return efficacy, suggestions


def axis_warnings(std_per_axis: Dict[str, float], threshold_median_mult: float = 1.5) -> List[str]:
    stds = list(std_per_axis.values())
    median_std = float(np.median(stds)) if stds else 0.0
    warnings = []
    for dim, s in std_per_axis.items():
        if median_std > 0 and s >= threshold_median_mult * median_std:
            warnings.append(
                f"[MATRIX WARNING] {dim}-Axis mapping shows low correlation with A-01 pattern label "
                f"(high variance {s:.4f} vs median {median_std:.4f})."
            )
    return warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="FDS 矩阵逆向拟合审计：基于 A-01 成格样本评估 TMM 并输出校准建议",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH, help="A-01 manifest 路径")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA, help="518k 样本 jsonl 路径")
    parser.add_argument("--limit", type=int, default=None, help="仅处理前 N 行（用于快速测试）")
    parser.add_argument("--step", type=float, default=0.10, help="权重微调步长比例，默认 0.10 即 ±10%%")
    parser.add_argument("--out", type=Path, default=None, help="报告与热力图数据输出路径（目录或 .json）")
    parser.add_argument("--no-heatmap", action="store_true", help="不生成热力图（仅文本报告）")
    parser.add_argument("--weights", type=Path, default=None, help="覆盖矩阵 JSON（如 V4.0-BETA），用于二次验证")
    args = parser.parse_args()
    out_path = args.out or (PROJECT_ROOT / "sop_output" / "matrix_backfitting_report.json")

    print("FDS 矩阵逆向拟合审计器 (Step 8)")
    print("=" * 60)
    if jsonLogic is None:
        print("❌ 需要安装 json-logic-quibble 以执行古典逻辑筛选。")
        sys.exit(1)

    manifest = load_manifest(args.manifest)
    logic = manifest.get("classical_logic_rules", {}).get("expression")
    if not logic:
        print("❌ Manifest 中未找到 classical_logic_rules.expression")
        sys.exit(1)
    if args.weights and args.weights.exists():
        weights, gods, god_index = get_weights_matrix_from_file(args.weights)
        print(f"✅ 已加载覆盖矩阵（V4.0-BETA 等）: {args.weights}")
    else:
        weights, gods, god_index = get_weights_matrix(manifest)
    n_gods = len(gods)
    print(f"✅ TMM：{n_gods} 十神 × 5 维")

    print("📊 正在扫描 A-01 成格样本...")
    vectors_10, total, matched = collect_a01_samples(
        args.data, logic, god_index, n_gods, limit=args.limit
    )
    print(f"✅ 总行数: {total:,}，A-01 匹配: {matched:,}")

    points_5d = project_to_5d(vectors_10, weights)
    metrics = cluster_metrics(points_5d)
    base_mean_dist = metrics["mean_distance_to_centroid"]
    print(f"\n📐 当前矩阵下 A-01 簇指标:")
    print(f"   质心 (5D): {metrics['centroid'].tolist()}")
    print(f"   各轴标准差: {metrics['std_per_axis']}")
    print(f"   平均到质心距离 (越小越紧): {base_mean_dist:.4f}")

    warnings = axis_warnings(metrics["std_per_axis"])
    for w in warnings:
        print(f"   ⚠️ {w}")

    print("\n🔬 敏感度分析（权重 ±{}%）...".format(int(args.step * 100)))
    efficacy, suggestions = sensitivity_analysis(
        vectors_10, weights, gods, base_mean_dist, step_pct=args.step
    )
    print("✅ 敏感度分析完成")

    # 文本报告：校准建议
    print("\n" + "=" * 60)
    print("📋 校准建议（按改进量排序，取前 10）")
    print("=" * 60)
    for s in suggestions[:10]:
        print(f"  • {s['suggested_note']} (改进 ≈ {s['improvement']:.4f})")

    # 热力图数据与输出
    report = {
        "pattern_id": "A-01",
        "data_path": str(args.data),
        "total_rows_scanned": total,
        "a01_matched_count": matched,
        "base_mean_distance_to_centroid": round(base_mean_dist, 6),
        "centroid_5d": metrics["centroid"].tolist(),
        "std_per_axis": metrics["std_per_axis"],
        "axis_warnings": warnings,
        "efficacy_heatmap": {
            "rows": gods,
            "cols": DIMS,
            "matrix": efficacy.tolist(),
        },
        "calibration_suggestions": suggestions[:20],
    }
    out_file = out_path if out_path.suffix == ".json" else out_path / "matrix_backfitting_report.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 报告已写入: {out_file}")

    if not args.no_heatmap:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 6))
            im = ax.imshow(efficacy, cmap="RdYlGn", aspect="auto", vmin=-0.02, vmax=0.02)
            ax.set_xticks(range(len(DIMS)))
            ax.set_xticklabels(DIMS)
            ax.set_yticks(range(len(gods)))
            ax.set_yticklabels(gods)
            ax.set_xlabel("5D Axis")
            ax.set_ylabel("Ten-God")
            plt.colorbar(im, ax=ax, label="Improvement when +10% weight")
            plt.title("A-01 Matrix Back-Fitting: Efficacy (green = increase weight helps)")
            heatmap_path = out_file.with_suffix(".heatmap.png")
            plt.savefig(heatmap_path, dpi=120, bbox_inches="tight")
            plt.close()
            print(f"✅ 热力图已保存: {heatmap_path}")
        except ImportError:
            print("   (未安装 matplotlib，跳过热力图生成；报告中的 efficacy_heatmap 已含数据)")


if __name__ == "__main__":
    main()
