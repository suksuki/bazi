"""
FDS Dynamic Evolution Engine (A-01 全息动态演化)
================================================
时间流变（大运、流年→5D 增量）与空间耦合（地理方位→5D 修正），
合成动态位移轨迹。参数来自 config/dynamic_evolution.json，零硬编码。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DIM_KEYS = ["E", "O", "M", "S", "R"]
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "dynamic_evolution.json"

# 干支→五行（标准命理）
_GAN_WUXING = ["木", "木", "火", "火", "土", "土", "金", "金", "水", "水"]  # 甲乙丙丁戊己庚辛壬癸
_ZHI_WUXING = ["水", "土", "木", "木", "土", "火", "火", "土", "金", "金", "土", "水"]  # 子丑寅卯辰巳午未申酉戌亥


def _load_config() -> Dict[str, Any]:
    if not _CONFIG_PATH.exists():
        return {}
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("dynamic_evolution 配置加载失败: %s", e)
        return {}


def _get_wuxing_delta(wuxing: str, config: Dict) -> Dict[str, float]:
    m = (config.get("wuxing_to_5d_delta") or {}).get(wuxing)
    if isinstance(m, dict):
        return {k: float(m.get(k, 0)) for k in DIM_KEYS}
    return {k: 0.0 for k in DIM_KEYS}


def pillar_to_5d_delta(gan_zhi: str, config: Optional[Dict] = None) -> Dict[str, float]:
    """
    单柱干支 → 5D 增量向量。
    天干+地支各取五行，合并为一条增量（天干权重略高）。
    """
    config = config or _load_config()
    scale = float((config.get("time") or {}).get("scale_pillar", 1.0))
    if not gan_zhi or len(gan_zhi) < 2:
        return {k: 0.0 for k in DIM_KEYS}
    gan = gan_zhi[0]
    zhi = gan_zhi[1] if len(gan_zhi) > 1 else ""
    # 天干索引：甲0 乙1 ... 癸9
    try:
        gan_idx = "甲乙丙丁戊己庚辛壬癸".index(gan)
    except ValueError:
        gan_idx = 0
    try:
        zhi_idx = "子丑寅卯辰巳午未申酉戌亥".index(zhi)
    except ValueError:
        zhi_idx = 0
    w_gan = _GAN_WUXING[gan_idx]
    w_zhi = _ZHI_WUXING[zhi_idx]
    d_gan = _get_wuxing_delta(w_gan, config)
    d_zhi = _get_wuxing_delta(w_zhi, config)
    # 合并：天干 0.55，地支 0.45
    out = {}
    for k in DIM_KEYS:
        out[k] = (d_gan[k] * 0.55 + d_zhi[k] * 0.45) * scale
    return out


def get_time_delta(
    luck_gan_zhi: str,
    year_gan_zhi: str,
    weight_luck: Optional[float] = None,
    weight_year: Optional[float] = None,
    config: Optional[Dict] = None,
) -> Dict[str, float]:
    """
    大运 + 流年 → 时间 5D 增量（矢量合成）。
    """
    config = config or _load_config()
    t = config.get("time") or {}
    w_luck = weight_luck if weight_luck is not None else float(t.get("weight_luck", 0.4))
    w_year = weight_year if weight_year is not None else float(t.get("weight_year", 0.6))
    d_luck = pillar_to_5d_delta(luck_gan_zhi or "", config)
    d_year = pillar_to_5d_delta(year_gan_zhi or "", config)
    out = {}
    for k in DIM_KEYS:
        out[k] = d_luck[k] * w_luck + d_year[k] * w_year
    return out


def get_geo_factor(direction: str, config: Optional[Dict] = None) -> Dict[str, float]:
    """
    地理方位 → 5D 修正因子。
    东/南/西/北/中 对应 木/火/金/水/土 的增益。
    """
    config = config or _load_config()
    geo = config.get("geo_direction") or {}
    d = geo.get(direction) or geo.get("中") or {}
    if isinstance(d, dict):
        return {k: float(d.get(k, 0)) for k in DIM_KEYS}
    return {k: 0.0 for k in DIM_KEYS}


def calculate_dynamic_state(
    base_point: Dict[str, float],
    time_delta: Optional[Dict[str, float]] = None,
    geo_factor: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    合成动态状态：base_point + time_delta + geo_factor → dynamic_point。
    返回含 dynamic_point、time_delta、geo_factor、displacement 的字典。
    """
    time_delta = time_delta or {k: 0.0 for k in DIM_KEYS}
    geo_factor = geo_factor or {k: 0.0 for k in DIM_KEYS}
    dynamic = {}
    for k in DIM_KEYS:
        b = float(base_point.get(k, 0))
        t = float(time_delta.get(k, 0))
        g = float(geo_factor.get(k, 0))
        dynamic[k] = b + t + g
    displacement = {k: dynamic[k] - float(base_point.get(k, 0)) for k in DIM_KEYS}
    return {
        "base_point": dict(base_point),
        "dynamic_point": dynamic,
        "time_delta": dict(time_delta),
        "geo_factor": dict(geo_factor),
        "displacement": displacement,
    }


def build_dynamic_context_for_prompt(
    base_point: Dict[str, float],
    dynamic_point: Dict[str, float],
    time_delta: Dict[str, float],
    geo_factor: Dict[str, float],
    luck_gan_zhi: str = "",
    year_gan_zhi: str = "",
    direction: str = "",
) -> str:
    """供 AI 判词使用的「动态演化」上下文文本。"""
    parts = [
        "【原局 5D 坐标】",
        " ".join(f"{k}={base_point.get(k, 0):.2f}" for k in DIM_KEYS),
        "",
        "【动态 5D 坐标（大运+流年+地理后）】",
        " ".join(f"{k}={dynamic_point.get(k, 0):.2f}" for k in DIM_KEYS),
        "",
        "【时间增量 time_delta】",
        " ".join(f"{k}={time_delta.get(k, 0):+.2f}" for k in DIM_KEYS),
    ]
    if luck_gan_zhi or year_gan_zhi:
        parts.append(f"大运={luck_gan_zhi or '—'}，流年={year_gan_zhi or '—'}")
    if direction:
        parts.append(f"地理方位={direction}")
    if any(geo_factor.get(k, 0) != 0 for k in DIM_KEYS):
        parts.append("【地理修正 geo_factor】")
        parts.append(" ".join(f"{k}={geo_factor.get(k, 0):+.2f}" for k in DIM_KEYS))
    return "\n".join(parts)
