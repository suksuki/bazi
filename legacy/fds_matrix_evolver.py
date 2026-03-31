#!/usr/bin/env python3
"""
FDS 矩阵自动化迭代 (Matrix Evolver)
===================================
[第020号工程指令] 将 Step 8 审计报告中的校准建议安全应用到 TMM，产出 V4.0-BETA 真理矩阵。

- 读取 sop_output/matrix_backfitting_report.json 的 calibration_suggestions
- 将前 10 条建议按「减少权重」应用，单次微调不超过原权重的 10%
- 输出 config/physics/tensor_mapping_matrix_V4.0_BETA.json
- 可选 --verify：用新矩阵重跑审计并写入 matrix_evolution_result.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent
REPORT_PATH = PROJECT_ROOT / "sop_output" / "matrix_backfitting_report.json"
MANIFEST_PATH = PROJECT_ROOT / "config" / "patterns" / "manifest_A01.json"
OUTPUT_MATRIX_PATH = PROJECT_ROOT / "config" / "physics" / "tensor_mapping_matrix_V4.0_BETA.json"
EVOLUTION_RESULT_PATH = PROJECT_ROOT / "sop_output" / "matrix_evolution_result.json"
DIMS = ["E", "O", "M", "S", "R"]
MAX_ADJUST_PCT = 0.10  # 单次微调幅度不超过原权重的 10%


def load_report(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_manifest(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_suggestions(
    weights: Dict[str, List[float]],
    suggestions: List[Dict[str, Any]],
    top_n: int = 10,
    adjust_pct: float = MAX_ADJUST_PCT,
) -> Dict[str, List[float]]:
    """
    应用前 top_n 条建议；每条「减少」对应权重 *= (1 - adjust_pct)。
    同一 (ten_god, axis) 只应用一次（取首次出现）。
    """
    out = {g: list(v) for g, v in weights.items()}
    applied = set()  # (ten_god, axis)
    for s in suggestions[:top_n]:
        god, axis, direction = s["ten_god"], s["axis"], s.get("direction", "-")
        key = (god, axis)
        if key in applied:
            continue
        if god not in out or axis not in DIMS:
            continue
        idx = DIMS.index(axis)
        old = out[god][idx]
        if direction == "-":
            # 减少：新值 = 原值 * (1 - adjust_pct)，保持符号
            new = old * (1.0 - adjust_pct)
        else:
            new = old * (1.0 + adjust_pct)
        out[god][idx] = round(new, 6)
        applied.add(key)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="FDS 矩阵进化：从 Step 8 报告生成 V4.0-BETA 矩阵")
    parser.add_argument("--report", type=Path, default=REPORT_PATH, help="审计报告 JSON 路径")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH, help="A-01 manifest 路径")
    parser.add_argument("--out", type=Path, default=OUTPUT_MATRIX_PATH, help="输出矩阵 JSON 路径")
    parser.add_argument("--top", type=int, default=10, help="应用前 N 条建议")
    parser.add_argument("--pct", type=float, default=MAX_ADJUST_PCT, help="单次微调比例 (0.1 = 10%%)")
    parser.add_argument("--verify", action="store_true", help="用新矩阵重跑审计并写入 matrix_evolution_result.json")
    args = parser.parse_args()

    if not args.report.exists():
        print(f"❌ 报告不存在: {args.report}")
        sys.exit(1)
    if not args.manifest.exists():
        print(f"❌ Manifest 不存在: {args.manifest}")
        sys.exit(1)

    report = load_report(args.report)
    manifest = load_manifest(args.manifest)
    tmm = manifest.get("tensor_mapping_matrix", {})
    weights = dict(tmm.get("weights", {}))
    ten_gods = list(tmm.get("ten_gods", []))
    dimensions = list(tmm.get("dimensions", DIMS))
    if not weights or not ten_gods:
        print("❌ Manifest 中缺少 tensor_mapping_matrix.weights / ten_gods")
        sys.exit(1)

    suggestions = report.get("calibration_suggestions", [])
    if not suggestions:
        print("❌ 报告中无 calibration_suggestions")
        sys.exit(1)
    old_mean_dist = report.get("base_mean_distance_to_centroid")

    new_weights = apply_suggestions(weights, suggestions, top_n=args.top, adjust_pct=args.pct)
    payload = {
        "version": "4.0-BETA",
        "source": "fds_matrix_evolver from Step 8 matrix_backfitting_report",
        "ten_gods": ten_gods,
        "dimensions": dimensions,
        "weights": new_weights,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"✅ V4.0-BETA 矩阵已写入: {args.out}")

    if args.verify:
        # 使用新矩阵重跑审计（仅算 mean_distance，不写完整报告）
        auditor_script = PROJECT_ROOT / "fds_matrix_backfitting_auditor.py"
        if not auditor_script.exists():
            print("⚠️ 未找到 fds_matrix_backfitting_auditor.py，跳过二次验证")
            return
        cmd = [
            sys.executable,
            str(auditor_script),
            "--data", str(PROJECT_ROOT / "data" / "holographic_universe_518k.jsonl"),
            "--out", str(PROJECT_ROOT / "sop_output" / "matrix_backfitting_report_V4.json"),
            "--no-heatmap",
            "--weights", str(args.out),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=str(PROJECT_ROOT))
            if result.returncode != 0:
                print("⚠️ 审计器运行失败:", result.stderr[:500] if result.stderr else result.stdout[:500])
                return
            # 解析新报告中的 base_mean_distance_to_centroid
            v4_report_path = PROJECT_ROOT / "sop_output" / "matrix_backfitting_report_V4.json"
            if v4_report_path.exists():
                v4_report = load_report(v4_report_path)
                new_mean_dist = v4_report.get("base_mean_distance_to_centroid")
                if new_mean_dist is not None and old_mean_dist and old_mean_dist > 0:
                    improvement_pct = (1.0 - new_mean_dist / old_mean_dist) * 100.0
                    evolution = {
                        "matrix_version": "4.0-BETA",
                        "previous_mean_distance": round(old_mean_dist, 6),
                        "new_mean_distance": round(new_mean_dist, 6),
                        "improvement_pct": round(improvement_pct, 2),
                        "verification": "PASS" if new_mean_dist < old_mean_dist else "NO_IMPROVEMENT",
                    }
                    EVOLUTION_RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
                    with open(EVOLUTION_RESULT_PATH, "w", encoding="utf-8") as f:
                        json.dump(evolution, f, indent=2, ensure_ascii=False)
                    print(f"✅ 二次验证完成: 新距离 {new_mean_dist:.4f}，解释力提升 {improvement_pct:.2f}%")
                    print(f"   结果已写入: {EVOLUTION_RESULT_PATH}")
                else:
                    print("⚠️ 无法从新报告中读取 base_mean_distance_to_centroid")
        except subprocess.TimeoutExpired:
            print("⚠️ 审计器运行超时")
        except Exception as e:
            print(f"⚠️ 验证过程异常: {e}")


if __name__ == "__main__":
    main()
