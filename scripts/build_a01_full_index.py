#!/usr/bin/env python3
"""
第 028 号工程指令：A-01 全量样本索引构建
==========================================
从 holographic_universe_518k.jsonl 中筛选 A-01 逻辑命中样本，计算 5D 张量并导出为
可被 case_retriever 加载的缓存（.npz + .json），便于 KDTree 检索与 UI 流畅加载。

用法:
  python scripts/build_a01_full_index.py [--data path/to/518k.jsonl] [--out dir]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

# 项目根
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from json_logic import jsonLogic
except ImportError:
    print("❌ 需要 json-logic-qubit。pip install json-logic-qubit")
    sys.exit(1)


def load_manifest(manifest_path: Path) -> dict:
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_weights_matrix(manifest: dict) -> tuple:
    tmm = manifest["tensor_mapping_matrix"]
    gods = tmm["ten_gods"]
    matrix = [tmm["weights"][g] for g in gods]
    return np.array(matrix), gods


def calculate_5d_tensor(
    case_ten_gods: dict,
    weights_matrix: np.ndarray,
    god_index_map: dict,
) -> np.ndarray:
    vec = np.zeros(10)
    for god, val in case_ten_gods.items():
        if god in god_index_map:
            vec[god_index_map[god]] = float(val)
    return np.dot(weights_matrix.T, vec)


def normalize_case_for_logic(case: dict) -> dict:
    """确保 case 含 ten_gods 与 self_energy，满足 manifest 表达式。"""
    if "self_energy" not in case or not isinstance(case["self_energy"], dict):
        case = {**case, "self_energy": {"E": 0.5}}
    if "ten_gods" not in case:
        case = {**case, "ten_gods": {}}
    return case


def build_full_index(
    data_path: Path,
    manifest_path: Path,
    out_dir: Path,
    limit: int | None = None,
) -> tuple[int, Path, Path]:
    """
    扫描 jsonl，筛选 A-01 样本，导出 points.npz 与 meta.json。
    返回 (样本数, points_path, meta_path)。
    """
    manifest = load_manifest(manifest_path)
    weights, gods = get_weights_matrix(manifest)
    god_index_map = {g: i for i, g in enumerate(gods)}
    logic_expr = manifest["classical_logic_rules"]["expression"]

    out_dir.mkdir(parents=True, exist_ok=True)
    points_list = []
    meta_list = []

    total = 0
    matched = 0
    with open(data_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            if limit and len(points_list) >= limit:
                break
            total += 1
            try:
                case = json.loads(line)
                case = normalize_case_for_logic(case)
                if not jsonLogic(logic_expr, case):
                    continue
                matched += 1
                tensor = calculate_5d_tensor(case["ten_gods"], weights, god_index_map)
                points_list.append(tensor)
                uid = case.get("uid") or case.get("id") or f"A01-{i}"
                meta_list.append({
                    "ref": str(uid),
                    "point": tensor.tolist(),
                    "subpattern": "",  # 由 case_retriever 按质心补全
                    "note": case.get("note", ""),
                    "line_index": i,
                })
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                continue
            if total % 50000 == 0:
                print(f"   进度: {total:,} 行, 匹配: {matched:,}", end="\r")

    print(f"\n✅ A-01 匹配: {matched:,} / {total:,}")

    points = np.array(points_list, dtype=np.float64)
    points_path = out_dir / "a01_full_points.npz"
    meta_path = out_dir / "a01_full_meta.json"
    np.savez_compressed(points_path, points=points)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_list, f, ensure_ascii=False, indent=0)
    print(f"   已写入: {points_path}, {meta_path}")
    return len(points_list), points_path, meta_path


def main():
    parser = argparse.ArgumentParser(description="A-01 全量样本索引构建")
    parser.add_argument("--data", type=Path, default=None, help="518k jsonl 路径")
    parser.add_argument("--out", type=Path, default=None, help="输出目录，默认 data_local")
    parser.add_argument("--limit", type=int, default=None, help="最多导出样本数（测试用）")
    args = parser.parse_args()

    data_path = args.data or ROOT / "data" / "holographic_universe_518k.jsonl"
    if not data_path.exists():
        data_path = ROOT / "data_local" / "holographic_universe_518k.jsonl"
    if not data_path.exists():
        print(f"❌ 未找到数据文件: {args.data or 'data/ 或 data_local/'}")
        sys.exit(1)

    manifest_path = ROOT / "config" / "patterns" / "manifest_A01.json"
    if not manifest_path.exists():
        print(f"❌ 未找到 manifest: {manifest_path}")
        sys.exit(1)

    out_dir = args.out or ROOT / "data_local"
    n, p, m = build_full_index(data_path, manifest_path, out_dir, limit=args.limit)
    print(f"🎯 全量索引构建完成: {n:,} 条。请使用 CaseRetriever(cache_dir={out_dir}) 加载。")


if __name__ == "__main__":
    main()
