#!/usr/bin/env python3
"""
第 028 号工程指令：A-01 奇点英雄榜 (Hall of Singularities)
==========================================================
从全量索引中按各轴极端值筛选约 10 个「黄金样板」，调用 32B 为每个撰写深度物理剖析，
写入 registry/holographic_pattern/A-01_hall_of_fame.json。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.case_retriever import load_registry_benchmarks, _assign_subpattern_by_centroid, DIM_ORDER

AXIS_LABELS = {"E": "能量轴", "O": "秩序轴", "M": "财富轴", "S": "压力轴", "R": "关系轴"}


def _get_ollama():
    try:
        import ollama
        return ollama.Client()
    except ImportError:
        return None


def select_singularity_indices(points: np.ndarray, meta: list, top_per_axis: int = 2) -> list[int]:
    """每轴取 top_per_axis 个极值（最大），去重后按出现顺序返回最多 10 个索引。"""
    order = ["E", "O", "M", "S", "R"]
    axis_idx = {order[i]: i for i in range(5)}
    seen = set()
    result = []
    for ax in order:
        j = axis_idx[ax]
        idx = np.argsort(-points[:, j])[:top_per_axis]
        for i in idx:
            i = int(i)
            if i not in seen and len(result) < 10:
                seen.add(i)
                result.append(i)
    return result[:10]


def generate_singularity_analysis(ref: str, point: list, axis_highlight: str, model: str = "qwen2.5:32b") -> str:
    """调用 32B 为单个奇点生成深度物理剖析。"""
    client = _get_ollama()
    if not client:
        return ""
    axis_name = AXIS_LABELS.get(axis_highlight, axis_highlight)
    sys_prompt = (
        "你是命理学与物理建模专家。请根据命例的 5D 命运流形坐标，撰写一段「深度物理剖析」："
        "说明该命例在指定轴上的极端性及其在现实中的可能体现（性格、际遇、风险）。"
        "控制在 150 字以内，不要输出 JSON 或列表。"
    )
    user = f"【案例编号】{ref}\n【5D 坐标】E={point[0]:.2f}, O={point[1]:.2f}, M={point[2]:.2f}, S={point[3]:.2f}, R={point[4]:.2f}\n【极端轴】{axis_name}\n\n请撰写深度物理剖析："
    try:
        r = client.chat(model=model, messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user}], options={"num_predict": 280})
        content = r.get("message", {}).get("content") if isinstance(r, dict) else None
        return (content or "").strip()
    except Exception:
        return ""


def main():
    cache_dir = ROOT / "data_local"
    points_path = cache_dir / "a01_full_points.npz"
    meta_path = cache_dir / "a01_full_meta.json"
    if not points_path.exists() or not meta_path.exists():
        print("❌ 请先运行 scripts/build_a01_full_index.py 生成全量索引")
        sys.exit(1)

    points = np.load(points_path)["points"]
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    if len(meta) != len(points):
        print("❌ meta 与 points 长度不一致")
        sys.exit(1)

    _, centroids = load_registry_benchmarks(ROOT / "registry" / "holographic_pattern" / "A-01.json")
    indices = select_singularity_indices(points, meta)
    singularities = []
    for i in indices:
        m = meta[i]
        pt = points[i].tolist()
        ref = m.get("ref", f"A01-{i}")
        sp = _assign_subpattern_by_centroid(points[i], centroids) if centroids else ""
        # 确定该样本最突出的轴（与质心偏差最大的轴）
        if centroids:
            c = np.array(list(centroids.values())[0])
            diff = np.abs(points[i] - c)
            axis_highlight = DIM_ORDER[int(np.argmax(diff))]
        else:
            axis_highlight = DIM_ORDER[int(np.argmax(points[i]))]
        analysis = generate_singularity_analysis(ref, pt, axis_highlight)
        singularities.append({
            "ref": ref,
            "point": [round(x, 4) for x in pt],
            "subpattern": sp,
            "axis_highlight": axis_highlight,
            "analysis": analysis,
        })
        print(f"  ✅ {ref} ({axis_highlight})")

    out_path = ROOT / "registry" / "holographic_pattern" / "A-01_hall_of_fame.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": "1.0", "description": "A-01 奇点英雄榜，32B 深度物理剖析", "singularities": singularities}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"🎯 已写入 {out_path}")


if __name__ == "__main__":
    main()
