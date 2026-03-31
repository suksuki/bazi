#!/usr/bin/env python3
"""
第 030 号（补）/ 第 034 号：矩阵觉醒 — 奇点回溯法校准
=======================================================
从全量索引中提取奇点案例，将当前 TMM 与案例发给大模型，反推权重修正方案。
A-01: 输出 tensor_mapping_matrix_V5.0_ALPHA.json
A-02: 按 S 轴（应力）极值选取奇点，输出 tensor_mapping_matrix_A02_V5.1_CALIBRATED.json

用法:
  python scripts/matrix_backfitting_auditor.py [--top 50] [--model qwen2.5:32b]
  python scripts/matrix_backfitting_auditor.py --pattern_id A-02 --top 50
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
A02_CALIBRATED_PATH = PHYSICS_DIR / "tensor_mapping_matrix_A02_V5.1_CALIBRATED.json"
CACHE_DIR = ROOT / "data_local"
REGISTRY_PATH = ROOT / "registry" / "holographic_pattern" / "A-01.json"
A02_MANIFEST_PATH = ROOT / "registry" / "holographic_pattern" / "A-02" / "A-02_manifest.json"
DIM_ORDER = ["E", "O", "M", "S", "R"]
S_AXIS_INDEX = 3


def load_full_index(pattern_id: str = "A-01") -> Tuple[np.ndarray, List[Dict], Dict[str, List[float]]]:
    """加载全量索引与质心。pattern_id A-02 时加载 a02_*，无质心。"""
    prefix = pattern_id.strip().upper().replace("-", "").lower()
    points_path = CACHE_DIR / f"{prefix}_full_points.npz"
    meta_path = CACHE_DIR / f"{prefix}_full_meta.json"
    if not points_path.exists() or not meta_path.exists():
        raise FileNotFoundError(f"请先运行 build_a01_full_index.py --pattern {pattern_id} 生成 {points_path}")
    points = np.load(points_path)["points"]
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    centroids = {}
    if pattern_id.strip().upper() == "A-01":
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            reg = json.load(f)
        centroids_raw = (reg.get("data") or {}).get("feature_anchors", {}).get("subpattern_centroids", {})
        for k, v in centroids_raw.items():
            if isinstance(v, dict) and v.get("centroid_vector"):
                centroids[k] = v["centroid_vector"]
    return points, meta, centroids


def select_outlier_indices(
    points: np.ndarray,
    meta: List[Dict],
    centroids: Dict[str, List[float]],
    top_k: int,
    pattern_id: str = "A-01",
) -> List[int]:
    """A-01: 与质心距离最大；A-02: S 轴（应力）极值最大。"""
    if pattern_id.strip().upper() == "A-02":
        idx = np.argsort(-points[:, S_AXIS_INDEX])[:top_k]
        return idx.tolist()
    if not centroids:
        return list(range(min(top_k, len(points))))
    cen_list = np.array(list(centroids.values())[:2])
    dists = np.min(np.linalg.norm(points[:, None, :] - cen_list[None, :, :], axis=2), axis=1)
    idx = np.argsort(-dists)[:top_k]
    return idx.tolist()


def load_v4_tmm() -> Dict[str, Any]:
    if not V4_PATH.exists():
        raise FileNotFoundError(V4_PATH)
    with open(V4_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_tmm_for_pattern(pattern_id: str) -> Dict[str, Any]:
    """A-02 从 manifest 取 TMM；A-01 用 V4。"""
    if pattern_id.strip().upper() == "A-02":
        if not A02_MANIFEST_PATH.exists():
            raise FileNotFoundError(A02_MANIFEST_PATH)
        with open(A02_MANIFEST_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        tmm = data.get("tensor_mapping_matrix") or {}
        if not tmm.get("weights"):
            with open(V4_PATH, "r", encoding="utf-8") as f:
                v4 = json.load(f)
            tmm = {**v4, "weights": v4.get("weights", {})}
        return tmm
    return load_v4_tmm()


def get_ollama():
    try:
        import ollama
        from core.config_manager import ConfigManager
        host = ConfigManager().get("ollama_host", "http://localhost:11434") or "http://localhost:11434"
        if not host.startswith("http"):
            host = f"http://{host}"
        return ollama.Client(host=host)
    except ImportError:
        return None


def run_backfitting(
    points: np.ndarray,
    meta: List[Dict],
    indices: List[int],
    tmm_v4: Dict[str, Any],
    model: str,
    pattern_id: str = "A-01",
) -> Dict[str, Any]:
    """将当前矩阵与奇点案例发给大模型，请求权重修正方案。A-02 时强调 S 轴与 PG。"""
    client = get_ollama()
    if not client:
        return {"weights": tmm_v4.get("weights", {}), "error": "Ollama 不可用"}

    cases_text = []
    ref_prefix = pattern_id.strip().upper().replace("-", "")
    for i in indices:
        m = meta[i]
        pt = points[i].tolist()
        ref = m.get("ref", f"{ref_prefix}-{i}")
        cases_text.append(f"  - {ref}: E={pt[0]:.2f}, O={pt[1]:.2f}, M={pt[2]:.2f}, S={pt[3]:.2f}, R={pt[4]:.2f}")
    cases_block = "\n".join(cases_text[:50])

    weights_json = json.dumps(tmm_v4.get("weights", {}), ensure_ascii=False, indent=2)
    if pattern_id.strip().upper() == "A-02":
        sys_prompt = (
            "你是命理物理学家，专注七杀格（A-02）流形。任务：根据「S 轴（应力）极值」的 13.6w 样本中的 50 个奇点 5D 坐标，"
            "反推十神→五维(E/O/M/S/R)映射权重的修正建议。重点关注：PG（七杀）在 S 轴、O 轴的投影是否过激；"
            "为使分布更具法理意义（杀印相生、食神制杀），是否需微调 ZC/ZS 在 S 或 R 轴的权重。"
            "请仅输出一个 JSON 对象，键为十神代码(ZG,PG,ZR,PR,ZS,PS,ZC,PC,ZB,PB)，值为长度 5 的数组 [E,O,M,S,R]。不要解释，只输出 JSON。"
        )
        user_prompt = (
            "【当前 A-02 初始权重（V5.0-Initial）】\n" + weights_json + "\n\n"
            "【S 轴极值奇点样本（50 个）】\n" + cases_block + "\n\n"
            "请给出修正后的 weights JSON（完整对象）。若无需修改可保持原值。"
        )
    else:
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
    parser = argparse.ArgumentParser(description="矩阵奇点回溯校准（第 030/034 号）")
    parser.add_argument("--pattern_id", type=str, default="A-01", help="格局 ID，A-02 时按 S 轴极值选奇点并输出 A02_V5.1_CALIBRATED")
    parser.add_argument("--top", type=int, default=50, help="奇点样本数")
    try:
        from core.config_manager import ConfigManager
        _default_model = ConfigManager().get("selected_model_name", "qwen2.5:32b")
    except Exception:
        _default_model = "qwen2.5:32b"
    parser.add_argument("--model", type=str, default=_default_model, help="Ollama 模型名，缺省从 config/tuning_params.json 的 selected_model_name 读取")
    args = parser.parse_args()

    pattern_id = args.pattern_id.strip().upper()
    print(f"加载全量索引与 TMM（pattern={pattern_id}）...")
    points, meta, centroids = load_full_index(pattern_id)
    tmm = load_tmm_for_pattern(pattern_id)
    weights = tmm.get("weights", {})
    gods = tmm.get("ten_gods", list(weights.keys()))
    dims = tmm.get("dimensions", ["E", "O", "M", "S", "R"])

    indices = select_outlier_indices(points, meta, centroids, args.top, pattern_id=pattern_id)
    print(f"已选取 {len(indices)} 个奇点样本，请求大模型反推权重...")

    result = run_backfitting(points, meta, indices, tmm, args.model, pattern_id=pattern_id)
    if result.get("error"):
        print(f"  warning: {result['error']}，将保留原权重并写入输出文件。")

    if pattern_id == "A-02":
        out_path = A02_CALIBRATED_PATH
        payload = {
            "version": "5.1-CALIBRATED",
            "description": "A-02 七杀格奇点回溯法校准（Step 9），由 matrix_backfitting_auditor 生成",
            "ten_gods": gods,
            "dimensions": dims,
            "weights": result["weights"],
        }
    else:
        out_path = V5_PATH
        payload = {
            "version": "5.0-ALPHA",
            "description": "由 matrix_backfitting_auditor 奇点回溯法生成，供与 V4 对比切换",
            "ten_gods": gods,
            "dimensions": dims,
            "weights": result["weights"],
        }
    PHYSICS_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"已写入 {out_path}")


if __name__ == "__main__":
    main()
