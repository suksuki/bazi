"""
第 038 号工程指令：流形可视化工具
为雷达图提供格局标准流形带（μ±σ）及轴语义说明，零硬编码。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DIM_ORDER = ["E", "O", "M", "S", "R"]

# 5D 轴悬停说明（与 HKB/AI 一致）
AXIS_HOVER = {
    "E": "能量轴：身强/身弱、生命力能级",
    "O": "秩序轴：社会地位、克制力、法律边界",
    "M": "财富轴：资源拥有度、物质丰盈度",
    "S": "应力轴：环境应力、危机感、权力转化",
    "R": "关系轴：逻辑深度、精神高度、人际与悟性",
}


def get_axis_hover_text(axis: str) -> str:
    return AXIS_HOVER.get(axis, axis)


def get_manifold_band_for_pattern(
    pattern_id: str,
    sigma_scale: float = 1.0,
) -> Optional[Dict[str, Any]]:
    """
    返回格局的标准流形带（均值 μ 与标准差 σ），供雷达图背景层绘制 μ±σ 区域。
    从 registry 的 benchmarks 或 feature_anchors.standard_manifold / npz 计算。
    """
    pid = (pattern_id or "").strip().upper()
    reg_path = ROOT / "registry" / "holographic_pattern" / f"{pid}.json"
    if reg_path.exists():
        try:
            with open(reg_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            data = raw.get("data") or raw
            anchors = (data.get("feature_anchors") or {}).get("standard_manifold") or {}
            mu_list = anchors.get("mean_vector")
            cov = anchors.get("covariance_matrix")
            if mu_list and len(mu_list) == 5:
                mu = {DIM_ORDER[i]: float(mu_list[i]) for i in range(5)}
                if cov and np.array(cov).shape >= (5, 5):
                    cov_arr = np.array(cov, dtype=float)
                    std_arr = np.sqrt(np.maximum(np.diag(cov_arr), 0))
                    std = {DIM_ORDER[i]: float(std_arr[i] * sigma_scale) for i in range(5)}
                else:
                    benchmarks = data.get("benchmarks") or []
                    pts = [b.get("t") for b in benchmarks if isinstance(b.get("t"), (list, tuple)) and len(b.get("t")) == 5]
                    if pts:
                        arr = np.array(pts, dtype=float)
                        std = {DIM_ORDER[i]: float(np.std(arr[:, i]) * sigma_scale) for i in range(5)}
                    else:
                        std = {k: 0.5 for k in DIM_ORDER}
                return {"mean": mu, "std": std, "pattern_id": pid}
            benchmarks = data.get("benchmarks") or []
            pts = [b.get("t") for b in benchmarks if isinstance(b.get("t"), (list, tuple)) and len(b.get("t")) == 5]
            if pts:
                arr = np.array(pts, dtype=float)
                mu = {DIM_ORDER[i]: float(np.mean(arr[:, i])) for i in range(5)}
                std = {DIM_ORDER[i]: float(np.std(arr[:, i]) * sigma_scale) for i in range(5)}
                return {"mean": mu, "std": std, "pattern_id": pid}
        except Exception as e:
            logger.debug("get_manifold_band %s from registry failed: %s", pid, e)
    npz_path = ROOT / "data_local" / f"{pid.replace('-', '').lower()}_full_points.npz"
    if npz_path.exists():
        try:
            data = np.load(npz_path)
            pts = data["points"]
            if len(pts) > 0:
                mu = {DIM_ORDER[i]: float(np.mean(pts[:, i])) for i in range(5)}
                std = {DIM_ORDER[i]: float(np.std(pts[:, i]) * sigma_scale) for i in range(5)}
                return {"mean": mu, "std": std, "pattern_id": pid}
        except Exception as e:
            logger.debug("get_manifold_band %s from npz failed: %s", pid, e)
    return None
