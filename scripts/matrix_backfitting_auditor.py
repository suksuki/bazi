#!/usr/bin/env python3
"""
第 030 号（补）：矩阵觉醒 — 奇点回溯法校准
============================================
从 A-01 全量索引中提取「坐标与法理不一致」的奇点案例，将当前 TMM 与案例发给大模型，
反推权重修正方案并生成 tensor_mapping_matrix_V5.0_ALPHA.json。

用法:
  python scripts/matrix_backfitting_auditor.py [--top 50] [--model qwen2.5:32b]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PHYSICS_DIR = ROOT / "config" / "physics"
V4_PATH = PHYSICS_DIR / "tensor_mapping_matrix_V4.0_BETA.json"
V5_PATH = PHYSICS_DIR / "tensor_mapping_matrix_V5.0_ALPHA.json"
CACHE_DIR = ROOT / "data_local"
REGISTRY_PATH = ROOT / "registry" / "holographic_pattern" / "A-01.json"
DIM_ORDER = ["E", "O", "M", "S", "R"]


def load_full_index() -> Tuple[np.ndarray, List[Dict], Dict[str, List[float]]]:
    """加载全量索引与质心。"""
    points_path = CACHE_DIR / "a01_full_points.npz"
    meta_path = CACHE_DIR / "a01_full_meta.json"
    if not points_path.exists() or not meta_path.exists():
        raise FileNotFoundError(f"请先运行 build_a01_full_index.py 生成 {CACHE_DIR}")
    points = np.load(points_path)["points"]
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        reg = json.load(f)
    centroids_raw = (reg.get("data") or {}).get("feature_anchors", {}).get("subpattern_centroids", {})
    centroids = {}
    for k, v in centroids_raw.items():
        if isinstance(v, dict) and v.get("centroid_vector"):
            centroids[k] = v["centroid_vector"]
    return points, meta, centroids


def select_outlier_indices(
    points: np.ndarray,
    meta: List[Dict],
    centroids: Dict[str, List[float]],
    top_k: int,
) -> List[int]:
    """选取与质心距离最大的 top_k 个样本作为「坐标与法理可能不一致」的奇点。"""
    if not centroids:
        return list(range(min(top_k, len(points))))
    cen_list = np.array(list(centroids.values())[:2])
    # 到最近质心的距离
    dists = np.min(np.linalg.norm(points[:, None, :] - cen_list[None, :, :], axis=2), axis=1)
    idx = np.argsort(-dists)[:top_k]
    return idx.tolist()


def load_v4_tmm() -> Dict[str, Any]:
    if not V4_PATH.exists():
        raise FileNotFoundError(V4_PATH)
    with open(V4_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_ollama():
    try:
        import ollama
        return ollama.Client()
    except ImportError:
        return None


def run_backfitting(
    points: np.ndarray,
    meta: List[Dict],
    indices: List[int],
    tmm_v4: Dict[str, Any],
    model: str,
) -> Dict[str, Any]:
    """将 V4 矩阵与 50 个奇点案例发给大模型，请求权重修正方案。"""
    client = get_ollama()
    if not client:
        return {"weights": tmm_v4.get("weights", {}), "error": "Ollama 不可用"}

    cases_text = []
    for i in indices:
        m = meta[i]
        pt = points[i].tolist()
        ref = m.get("ref", f"A01-{i}")
        cases_text.append(f"  - {ref}: E={pt[0]:.2f}, O={pt[1]:.2f}, M={pt[2]:.2f}, S={pt[3]:.2f}, R={pt[4]:.2f}")
    cases_block = "\n".join(cases_text[:50])

    weights_json = json.dumps(tmm_v4.get("weights", {}), ensure_ascii=False, indent=2)
    sys_prompt = (
        "你是命理物理学家。任务：根据「与质心偏离较大的 A-01 样本」的 5D 坐标，反推十神→五维(E/O/M/S/R)映射权重的修正建议。"
        "请仅输出一个 JSON 对象，键为十神代码(ZG,PG,ZR,PR,ZS,PS,ZC,PC,ZB,PB)，值为长度为 5 的数组 [E,O,M,S,R] 的权重。"
        "不要输出任何解释，只输出 JSON。若某神无需修改，可保持原值。"
    )
    user_prompt = (
        "【当前 V4 权重】\n" + weights_json + "\n\n"
        "【奇点样本（与质心距离较大）】\n" + cases_block + "\n\n"
        "请给出修正后的 weights JSON（完整对象，不要省略键）。"
    )

    try:
        r = client.chat(
            model=model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"num_predict": 2000},
        )
        content = (r.get("message") or {}).get("content", "") if isinstance(r, dict) else ""
        if not content:
            content = getattr(getattr(r, "message", None), "content", None) or ""
        content = (content or "").strip()
        # 尝试从回复中提取 JSON
        weights_new = parse_weights_from_response(content, tmm_v4.get("weights", {}))
        return {"weights": weights_new, "raw_preview": content[:800]}
    except Exception as e:
        return {"weights": tmm_v4.get("weights", {}), "error": str(e)}


def parse_weights_from_response(content: str, fallback: Dict[str, List[float]]) -> Dict[str, List[float]]:
    """从大模型回复中解析 weights 对象。"""
    # 尝试 ```json ... ``` 或直接 { ... }
    for pattern in [r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", r"(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})"]:
        m = re.search(pattern, content)
        if m:
            try:
                data = json.loads(m.group(1))
                w = data.get("weights", data)
                if isinstance(w, dict) and w:
                    out = {}
                    gods = list(fallback.keys())
                    for g in gods:
                        row = w.get(g)
                        if isinstance(row, list) and len(row) >= 5:
                            out[g] = [float(x) for x in row[:5]]
                        else:
                            out[g] = list(fallback.get(g, [0] * 5)[:5])
                    return out
            except json.JSONDecodeError:
                continue
    return fallback


def main():
    parser = argparse.ArgumentParser(description="矩阵奇点回溯校准（第 030 号补）")
    parser.add_argument("--top", type=int, default=50, help="奇点样本数")
    parser.add_argument("--model", type=str, default="qwen2.5:32b")
    args = parser.parse_args()

    print("加载全量索引与 V4 矩阵...")
    points, meta, centroids = load_full_index()
    tmm_v4 = load_v4_tmm()
    weights_v4 = tmm_v4.get("weights", {})
    gods = tmm_v4.get("ten_gods", list(weights_v4.keys()))
    dims = tmm_v4.get("dimensions", ["E", "O", "M", "S", "R"])

    indices = select_outlier_indices(points, meta, centroids, args.top)
    print(f"已选取 {len(indices)} 个奇点样本，请求大模型反推权重...")

    result = run_backfitting(points, meta, indices, tmm_v4, args.model)
    if result.get("error"):
        print(f"  warning: {result['error']}，将保留 V4 权重并写入 V5 文件。")

    payload = {
        "version": "5.0-ALPHA",
        "description": "由 matrix_backfitting_auditor 奇点回溯法生成，供与 V4 对比切换",
        "ten_gods": gods,
        "dimensions": dims,
        "weights": result["weights"],
    }
    PHYSICS_DIR.mkdir(parents=True, exist_ok=True)
    with open(V5_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"已写入 {V5_PATH}")


if __name__ == "__main__":
    main()
