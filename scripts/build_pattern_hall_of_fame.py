#!/usr/bin/env python3
"""
第 033 号工程指令：全格局奇点英雄榜引擎 (Hall of Fame Engine)
================================================================
从全量索引中按各轴极端值筛选「奇点英雄」，调用 32B 为每个撰写深度物理剖析，
写入 registry/holographic_pattern/{pattern_id}/{pattern_id}_hall_of_fame.json。

支持 A-01、A-02 及后续格局。A-02 特例：S 轴（应力）为奇点选取第一优先级，
且提示词要求分析「高压应力（S）转化为权柄（Power）」的路径。

用法:
  python scripts/build_pattern_hall_of_fame.py --pattern_id A-01
  python scripts/build_pattern_hall_of_fame.py --pattern_id A-02
  python scripts/build_pattern_hall_of_fame.py --pattern_id A-02 --top_s 4
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 可选：A-01 质心与子格局归属
try:
    from core.case_retriever import (
        DIM_ORDER,
        _assign_subpattern_by_centroid,
        load_registry_benchmarks,
    )
except ImportError:
    DIM_ORDER = ["E", "O", "M", "S", "R"]
    load_registry_benchmarks = None
    _assign_subpattern_by_centroid = None

AXIS_LABELS = {"E": "能量轴", "O": "秩序轴", "M": "财富轴", "S": "压力轴", "R": "关系轴"}

# S 轴在 5D 中的下标（A-02 应力轴）
S_AXIS_INDEX = 3


def _get_ollama():
    try:
        import ollama
        return ollama.Client()
    except ImportError:
        return None


def resolve_pattern_paths(pattern_id: str) -> Tuple[Path, Path, Path]:
    """返回 (manifest_path, points_path, meta_path)。"""
    pid = pattern_id.strip().upper()
    prefix = pid.lower().replace("-", "")
    reg_dir = ROOT / "registry" / "holographic_pattern"
    data_dir = ROOT / "data_local"
    # manifest: 优先子目录 {pattern_id}/{pattern_id}_manifest.json，否则根目录 {pattern_id}.json
    manifest_path = reg_dir / pid / f"{pid}_manifest.json"
    if not manifest_path.exists():
        manifest_path = reg_dir / f"{pid}.json"
    points_path = data_dir / f"{prefix}_full_points.npz"
    meta_path = data_dir / f"{prefix}_full_meta.json"
    return manifest_path, points_path, meta_path


def load_manifest(manifest_path: Path) -> dict:
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_centroids_for_pattern(pattern_id: str, manifest: dict, manifest_path: Path) -> Dict[str, List[float]]:
    """从 manifest 或旧版 registry JSON 加载子格局质心；无则返回 {}。"""
    centroids_raw = manifest.get("centroids") or (manifest.get("data") or {}).get("feature_anchors") or {}
    if isinstance(centroids_raw, dict):
        sub_centroids = centroids_raw.get("subpattern_centroids") or centroids_raw
    else:
        sub_centroids = {}
    centroids = {}
    for k, v in (sub_centroids or {}).items():
        if isinstance(v, dict):
            c = v.get("centroid_vector")
        else:
            c = v
        if c is not None and len(c) == 5:
            centroids[k] = list(map(float, c))
    if centroids:
        return centroids
    # A-01 兼容：从 A-01.json 读
    if pattern_id.upper() == "A-01":
        reg_path = ROOT / "registry" / "holographic_pattern" / "A-01.json"
        if reg_path.exists() and load_registry_benchmarks:
            _, cents = load_registry_benchmarks(reg_path)
            return cents
    return {}


def select_singularity_indices(
    points: np.ndarray,
    meta: list,
    pattern_id: str,
    top_per_axis: int = 2,
    top_s_first: Optional[int] = None,
) -> List[int]:
    """
    每轴取极值（最大），去重后返回最多约 10 个索引。
    A-02：S 轴（应力）为第一优先级，可多取 top_s_first 个 S 轴极值。
    """
    pid = pattern_id.strip().upper()
    order = list(DIM_ORDER)
    axis_idx = {order[i]: i for i in range(5)}
    seen = set()
    result = []

    # A-02：先取 S 轴极值
    if pid == "A-02" and (top_s_first or 0) > 0:
        j = axis_idx["S"]
        idx = np.argsort(-points[:, j])[: top_s_first]
        for i in idx:
            i = int(i)
            if i not in seen:
                seen.add(i)
                result.append(i)
        if len(result) >= 10:
            return result[:10]

    # 轴顺序：A-02 时 S 放最前
    if pid == "A-02":
        order = ["S", "E", "O", "M", "R"]
    for ax in order:
        j = axis_idx.get(ax, order.index(ax) if ax in order else 0)
        idx = np.argsort(-points[:, j])[:top_per_axis]
        for i in idx:
            i = int(i)
            if i not in seen and len(result) < 10:
                seen.add(i)
                result.append(i)
    return result[:10]


def generate_singularity_analysis(
    ref: str,
    point: list,
    axis_highlight: str,
    pattern_id: str,
    manifest: dict,
    model: str = "qwen2.5:32b",
) -> str:
    """调用 32B 为单个奇点生成深度物理剖析。A-02 时强制注入「应力转权柄」分析要求。"""
    client = _get_ollama()
    if not client:
        return ""
    axis_name = AXIS_LABELS.get(axis_highlight, axis_highlight)
    pid = pattern_id.strip().upper()

    if pid == "A-02":
        sys_prompt = (
            "你是命理学与 FDS 流形体系的专家。七杀格的核心是「应力转化、秩序重构、爆发动能」。"
            "请根据命例的 5D 坐标，撰写一段深度剖析：**重点分析该样本如何将高压应力（S 轴）转化为权柄（Power）**，"
            "即现实中可能体现的「以压力为动力、化杀为权」的路径与风险。控制在 150 字以内，不要输出 JSON 或列表。"
        )
        user = (
            f"【案例编号】{ref}\n【5D 坐标】E={point[0]:.2f}, O={point[1]:.2f}, M={point[2]:.2f}, S={point[3]:.2f}, R={point[4]:.2f}\n"
            f"【极端轴】{axis_name}\n【要求】请分析：该样本如何转化高压应力（S）为权柄？\n\n请撰写深度物理剖析："
        )
    else:
        sys_prompt = (
            "你是命理学与物理建模专家。请根据命例的 5D 命运流形坐标，撰写一段「深度物理剖析」："
            "说明该命例在指定轴上的极端性及其在现实中的可能体现（性格、际遇、风险）。"
            "控制在 150 字以内，不要输出 JSON 或列表。"
        )
        user = (
            f"【案例编号】{ref}\n【5D 坐标】E={point[0]:.2f}, O={point[1]:.2f}, M={point[2]:.2f}, S={point[3]:.2f}, R={point[4]:.2f}\n"
            f"【极端轴】{axis_name}\n\n请撰写深度物理剖析："
        )

    try:
        r = client.chat(
            model=model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user},
            ],
            options={"num_predict": 280},
        )
        content = r.get("message", {}).get("content") if isinstance(r, dict) else None
        return (content or "").strip()
    except Exception:
        return ""


def run(
    pattern_id: str,
    data_dir: Optional[Path] = None,
    top_per_axis: int = 2,
    top_s_first: Optional[int] = None,
    model: str = "qwen2.5:32b",
) -> Dict[str, Any]:
    """
    执行英雄榜构建。返回 payload 与写入路径。
    """
    manifest_path, points_path, meta_path = resolve_pattern_paths(pattern_id)
    data_dir = data_dir or ROOT / "data_local"
    points_path = data_dir / points_path.name
    meta_path = data_dir / meta_path.name

    if not points_path.exists() or not meta_path.exists():
        raise FileNotFoundError(
            f"未找到全量索引：{points_path} 或 {meta_path}。请先运行 build_a01_full_index.py --pattern {pattern_id}。"
        )

    points = np.load(points_path)["points"]
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    if len(meta) != len(points):
        raise ValueError("meta 与 points 长度不一致")

    manifest = load_manifest(manifest_path) if manifest_path.exists() else {}
    centroids = load_centroids_for_pattern(pattern_id, manifest, manifest_path)

    indices = select_singularity_indices(
        points, meta, pattern_id, top_per_axis=top_per_axis, top_s_first=top_s_first
    )
    singularities: List[Dict[str, Any]] = []
    pid = pattern_id.strip().upper()

    for i in indices:
        m = meta[i]
        pt = points[i].tolist()
        ref = m.get("ref", f"{pid}-{i}")
        if centroids and _assign_subpattern_by_centroid:
            sp = _assign_subpattern_by_centroid(points[i], centroids)
        else:
            sp = m.get("subpattern", "")
        if centroids:
            c = np.array(list(centroids.values())[0])
            diff = np.abs(points[i] - c)
            axis_highlight = DIM_ORDER[int(np.argmax(diff))]
        else:
            # A-02 优先标 S；否则取最大坐标轴
            if pid == "A-02":
                axis_highlight = "S" if points[i][S_AXIS_INDEX] >= np.max(points[i]) else DIM_ORDER[int(np.argmax(points[i]))]
            else:
                axis_highlight = DIM_ORDER[int(np.argmax(points[i]))]
        analysis = generate_singularity_analysis(ref, pt, axis_highlight, pattern_id, manifest, model=model)
        singularities.append({
            "ref": ref,
            "point": [round(x, 4) for x in pt],
            "subpattern": sp,
            "axis_highlight": axis_highlight,
            "analysis": analysis,
        })
        print(f"  ✅ {ref} ({axis_highlight})")

    out_dir = ROOT / "registry" / "holographic_pattern" / pid
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{pid}_hall_of_fame.json"
    meta_info = (manifest.get("meta_info") or {})
    chinese_name = meta_info.get("chinese_name") or meta_info.get("display_name") or pid
    payload = {
        "version": "1.0",
        "pattern_id": pid,
        "description": f"{chinese_name} 奇点英雄榜，32B 深度物理剖析（第 033 号工程指令）",
        "singularities": singularities,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return {"payload": payload, "out_path": out_path}


def main():
    parser = argparse.ArgumentParser(
        description="全格局奇点英雄榜引擎（第 033 号工程指令）",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--pattern_id", type=str, default="A-01", help="格局 ID，如 A-01、A-02")
    parser.add_argument("--data_dir", type=Path, default=None, help="全量索引目录，默认 data_local")
    parser.add_argument("--top_per_axis", type=int, default=2, help="每轴选取极值个数")
    parser.add_argument("--top_s_first", type=int, default=None, help="A-02 时 S 轴优先选取个数（未设则用 top_per_axis）")
    parser.add_argument("--model", type=str, default="qwen2.5:32b", help="Ollama 模型名")
    args = parser.parse_args()

    pattern_id = args.pattern_id.strip().upper()
    top_s_first = args.top_s_first
    if pattern_id == "A-02" and top_s_first is None:
        top_s_first = 4  # 审计师要求：A-02 时 S 轴优先取 4 个

    print(f"🎯 奇点英雄榜引擎 · 格局 {pattern_id}")
    try:
        result = run(
            pattern_id,
            data_dir=args.data_dir,
            top_per_axis=args.top_per_axis,
            top_s_first=top_s_first,
            model=args.model,
        )
        print(f"🎯 已写入 {result['out_path']}")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ {e}")
        raise


if __name__ == "__main__":
    main()
