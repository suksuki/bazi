#!/usr/bin/env python3
"""
第 028 号工程指令：全量样本索引构建（支持 A-01 / A-02）
========================================================
从 holographic_universe_518k.jsonl 中按格局 JsonLogic 筛选样本，计算 5D 张量并导出为
可被 case_retriever 加载的缓存（.npz + .json），便于 KDTree 检索与 UI 流畅加载。

用法:
  python scripts/build_a01_full_index.py [--pattern A-01] [--data path/to/518k.jsonl] [--out dir]
  python scripts/build_a01_full_index.py --pattern A-02 [--data path/to/518k.jsonl] [--out dir]
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


def get_weights_matrix(manifest: dict, manifest_path: Path | None = None) -> tuple:
    """从 manifest 取 TMM；若 weights 为空（如 A-02 待分析师提供），则回退到 config/physics V4.0-BETA。"""
    tmm = manifest["tensor_mapping_matrix"]
    gods = tmm["ten_gods"]
    weights = tmm.get("weights") or {}
    if not weights and manifest_path and "A-02" in str(manifest_path):
        v4_path = ROOT / "config" / "physics" / "tensor_mapping_matrix_V4.0_BETA.json"
        if v4_path.exists():
            with open(v4_path, "r", encoding="utf-8") as f:
                v4 = json.load(f)
            weights = v4.get("weights", {})
            print("⚠️ A-02 manifest 未提供 weights，已回退使用 config/physics/tensor_mapping_matrix_V4.0_BETA.json")
    matrix = [weights[g] for g in gods]
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


# A-13 月劫格：仅用「月支 == 日干劫财之禄」作 L1 宽门（第 046 号松绑）
JIE_CAI_LU = {
    "甲": "卯", "乙": "寅", "丙": "午", "丁": "巳",
    "戊": "午", "己": "巳", "庚": "酉", "辛": "申",
    "壬": "子", "癸": "亥",
}


def is_yue_jie_basic(case: dict) -> bool:
    """月劫格基础 L1：月支为日干劫财之禄（异性同五行）。不做清纯度/官杀强制校验。"""
    bazi = case.get("bazi")
    if not bazi or not isinstance(bazi, dict):
        return False
    month_pillar = bazi.get("month")
    day_pillar = bazi.get("day")
    month_branch = ""
    day_master = ""
    if isinstance(month_pillar, str) and len(month_pillar) >= 2:
        month_branch = month_pillar[1]
    elif isinstance(month_pillar, dict):
        month_branch = (month_pillar.get("zhi") or month_pillar.get("branch") or "")
    if isinstance(day_pillar, str) and len(day_pillar) >= 1:
        day_master = day_pillar[0]
    elif isinstance(day_pillar, dict):
        day_master = (day_pillar.get("gan") or day_pillar.get("stem") or "")
    if not day_master or not month_branch:
        return False
    return JIE_CAI_LU.get(day_master.strip()) == month_branch.strip()


def use_classical_tougan_l1(pattern_id: str) -> bool:
    """第 048 号：A-01～A-10 启用提纲+透干古典硬约束；A-11～A-13 不强制。"""
    pid = (pattern_id or "").strip().upper()
    return pid in (
        "A-01", "A-02", "A-03", "A-04", "A-05", "A-06", "A-07", "A-08", "A-09", "A-10",
    )


def resolve_manifest_for_pattern(pattern_id: str) -> Path:
    """按格局 ID 解析 manifest 路径。A-02、A-03 等走 registry 子目录。"""
    pid = pattern_id.strip().upper()
    if pid not in ("A-01",):
        p = ROOT / "registry" / "holographic_pattern" / pid / f"{pid}_manifest.json"
        if p.exists():
            return p
    return ROOT / "config" / "patterns" / "manifest_A01.json"


def use_classical_tougan_l1(pattern_id: str) -> bool:
    """第 048 号：A-01～A-10 启用提纲+透干古典硬约束；A-11～A-13 不强制。"""
    pid = (pattern_id or "").strip().upper()
    return pid in (
        "A-01", "A-02", "A-03", "A-04", "A-05", "A-06", "A-07", "A-08", "A-09", "A-10",
    )


def build_full_index(
    data_path: Path,
    manifest_path: Path,
    out_dir: Path,
    limit: int | None = None,
    pattern_id: str = "A-01",
    use_048_tougan: bool = True,
) -> tuple[int, Path, Path]:
    """
    扫描 jsonl，按格局 JsonLogic 筛选样本，导出 points.npz 与 meta.json。
    第 048 号：use_048_tougan 且 A-01～A-10 时先过「提纲+透干」古典硬约束再过 JsonLogic。
    返回 (样本数, points_path, meta_path)。
    """
    manifest = load_manifest(manifest_path)
    weights, gods = get_weights_matrix(manifest, manifest_path)
    god_index_map = {g: i for i, g in enumerate(gods)}
    rules = manifest.get("classical_logic_rules") or {}
    logic_expr = rules.get("pipeline_expression") or rules.get("expression")
    prefix = pattern_id.lower().replace("-", "")  # a01 / a02

    try:
        from core.classical_tougan import enrich_case_with_classical_l1, is_classical_pattern_achieved
    except ImportError:
        enrich_case_with_classical_l1 = None
        is_classical_pattern_achieved = None
    apply_048 = use_048_tougan and use_classical_tougan_l1(pattern_id) and is_classical_pattern_achieved is not None

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
                if apply_048:
                    if enrich_case_with_classical_l1:
                        case = enrich_case_with_classical_l1(case)
                    if not is_classical_pattern_achieved(case, pattern_id):
                        continue
                # A-13 月劫格：L1 宽门，仅「月支=劫财禄」；不做清纯度强制（第 046 号松绑）
                if pattern_id == "A-13":
                    if not is_yue_jie_basic(case):
                        continue
                else:
                    if not jsonLogic(logic_expr, case):
                        continue
                matched += 1
                tensor = calculate_5d_tensor(case["ten_gods"], weights, god_index_map)
                points_list.append(tensor)
                uid = case.get("uid") or case.get("id") or case.get("case_id") or f"{pattern_id}-{i}"
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

    print(f"\n✅ {pattern_id} 匹配: {matched:,} / {total:,}")

    points = np.array(points_list, dtype=np.float64)
    points_path = out_dir / f"{prefix}_full_points.npz"
    meta_path = out_dir / f"{prefix}_full_meta.json"
    np.savez_compressed(points_path, points=points)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_list, f, ensure_ascii=False, indent=0)
    print(f"   已写入: {points_path}, {meta_path}")
    return len(points_list), points_path, meta_path


def main():
    parser = argparse.ArgumentParser(description="全量样本索引构建（A-01 / A-02）")
    parser.add_argument("--pattern", type=str, default="A-01", help="格局 ID，如 A-01、A-02")
    parser.add_argument("--data", type=Path, default=None, help="518k jsonl 路径")
    parser.add_argument("--out", type=Path, default=None, help="输出目录，默认 data_local")
    parser.add_argument("--limit", type=int, default=None, help="最多导出样本数（测试用）")
    args = parser.parse_args()

    pattern_id = args.pattern.strip().upper()

    data_path = args.data or ROOT / "data" / "holographic_universe_518k.jsonl"
    if not data_path.exists():
        data_path = ROOT / "data_local" / "holographic_universe_518k.jsonl"
    if not data_path.exists():
        print(f"❌ 未找到数据文件: {args.data or 'data/ 或 data_local/'}")
        sys.exit(1)

    manifest_path = resolve_manifest_for_pattern(pattern_id)
    if not manifest_path.exists():
        print(f"❌ 未找到 manifest: {manifest_path}")
        sys.exit(1)

    out_dir = args.out or ROOT / "data_local"
    n, p, m = build_full_index(
        data_path, manifest_path, out_dir, limit=args.limit, pattern_id=pattern_id
    )
    print(f"🎯 全量索引构建完成: {n:,} 条。请使用 CaseRetriever(cache_dir={out_dir}) 加载。")


if __name__ == "__main__":
    main()
