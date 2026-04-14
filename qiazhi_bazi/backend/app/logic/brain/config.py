"""
V12 PSV：运行时可配置阈值（环境变量 + Arbiter 覆盖），无业务逻辑。

环境变量前缀 ``QIAZHI_PSV_`` + 字段名大写蛇形，例如
``QIAZHI_PSV_ROBBER_WEALTH_PIERCE_THRESHOLD=0.35``。
"""

from __future__ import annotations

import os
from typing import Any, Mapping, Optional

from pydantic import BaseModel, Field


def _env_float(name: str) -> Optional[float]:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


class PSVRuntimeConfig(BaseModel):
    """PSV 引擎全部可调比例；默认值与历史硬编码行为一致。"""

    model_config = {"extra": "forbid"}

    robber_wealth_pierce_threshold: float = Field(default=0.3, ge=0.0, le=50.0)
    robber_wealth_strong_threshold: float = Field(default=0.65, ge=0.0, le=50.0)
    robber_wealth_base_strong_negative: float = Field(default=0.55, ge=0.0, le=1.0)
    robber_wealth_base_mild_negative: float = Field(default=0.35, ge=0.0, le=1.0)
    robber_wealth_span_divisor: float = Field(default=0.7, gt=1e-12)
    robber_wealth_span_scale: float = Field(default=0.45, ge=0.0, le=1.0)
    robber_plugin_evidence_strength_bonus: float = Field(default=0.08, ge=0.0, le=1.0)
    robber_wealth_denominator_epsilon: float = Field(default=1e-9, gt=0.0, le=1.0)

    element_balance_spread_threshold: float = Field(default=0.22, ge=0.0, le=1.0)
    element_balance_mild_vs_strong_breakpoint: float = Field(default=0.35, ge=0.0, le=1.0)
    element_balance_strength_scale_divisor: float = Field(default=0.5, gt=1e-12)

    l2_affinity_strong_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    l2_affinity_unknown_cutoff: float = Field(default=0.15, ge=0.0, le=1.0)
    l2_primary_strength_floor: float = Field(default=0.2, ge=0.0, le=1.0)
    intention_officer_bonus: float = Field(default=0.06, ge=0.0, le=1.0)
    officer_seek_stability_affinity_floor: float = Field(default=0.55, ge=0.0, le=1.0)
    intention_wealth_pattern_bonus: float = Field(default=0.05, ge=0.0, le=1.0)


_ENV_KEY_MAP: dict[str, str] = {
    "robber_wealth_pierce_threshold": "QIAZHI_PSV_ROBBER_WEALTH_PIERCE_THRESHOLD",
    "robber_wealth_strong_threshold": "QIAZHI_PSV_ROBBER_WEALTH_STRONG_THRESHOLD",
    "robber_wealth_base_strong_negative": "QIAZHI_PSV_ROBBER_WEALTH_BASE_STRONG_NEGATIVE",
    "robber_wealth_base_mild_negative": "QIAZHI_PSV_ROBBER_WEALTH_BASE_MILD_NEGATIVE",
    "robber_wealth_span_divisor": "QIAZHI_PSV_ROBBER_WEALTH_SPAN_DIVISOR",
    "robber_wealth_span_scale": "QIAZHI_PSV_ROBBER_WEALTH_SPAN_SCALE",
    "robber_plugin_evidence_strength_bonus": "QIAZHI_PSV_ROBBER_PLUGIN_STRENGTH_BONUS",
    "robber_wealth_denominator_epsilon": "QIAZHI_PSV_ROBBER_WEALTH_DENOM_EPSILON",
    "element_balance_spread_threshold": "QIAZHI_PSV_ELEMENT_BALANCE_SPREAD_THRESHOLD",
    "element_balance_mild_vs_strong_breakpoint": "QIAZHI_PSV_ELEMENT_BALANCE_MILD_STRONG_BREAKPOINT",
    "element_balance_strength_scale_divisor": "QIAZHI_PSV_ELEMENT_BALANCE_STRENGTH_DIVISOR",
    "l2_affinity_strong_threshold": "QIAZHI_PSV_L2_AFFINITY_STRONG_THRESHOLD",
    "l2_affinity_unknown_cutoff": "QIAZHI_PSV_L2_AFFINITY_UNKNOWN_CUTOFF",
    "l2_primary_strength_floor": "QIAZHI_PSV_L2_PRIMARY_STRENGTH_FLOOR",
    "intention_officer_bonus": "QIAZHI_PSV_INTENTION_OFFICER_BONUS",
    "officer_seek_stability_affinity_floor": "QIAZHI_PSV_OFFICER_STABILITY_AFFINITY_FLOOR",
    "intention_wealth_pattern_bonus": "QIAZHI_PSV_INTENTION_WEALTH_PATTERN_BONUS",
}


def _apply_env_overrides(cfg: PSVRuntimeConfig) -> PSVRuntimeConfig:
    updates: dict[str, float] = {}
    for field_name, env_name in _ENV_KEY_MAP.items():
        v = _env_float(env_name)
        if v is not None:
            updates[field_name] = v
    if not updates:
        return cfg
    return cfg.model_copy(update=updates)


def _coerce_overrides(raw: Mapping[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    fields = set(PSVRuntimeConfig.model_fields.keys())
    for k, v in raw.items():
        if k not in fields:
            continue
        try:
            out[str(k)] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def load_psv_runtime_config(arbiter_bias: Optional[Mapping[str, Any]] = None) -> PSVRuntimeConfig:
    """
    加载顺序：默认值 → 环境变量 → ``arbiter_bias`` 内嵌覆盖。

    ``arbiter_bias`` 支持键：

    - ``psv_runtime_overrides``：与 ``PSVRuntimeConfig`` 同名字段的部分字典（裁决持久化可写入）。
    - ``psv_runtime_config``：同上别名。
    """
    cfg = PSVRuntimeConfig()
    cfg = _apply_env_overrides(cfg)
    if not arbiter_bias:
        return cfg
    nested = arbiter_bias.get("psv_runtime_overrides")
    if nested is None:
        nested = arbiter_bias.get("psv_runtime_config")
    if isinstance(nested, Mapping) and nested:
        merged = _coerce_overrides(nested)
        if merged:
            cfg = cfg.model_copy(update=merged)
    return cfg


def load_psv_runtime_config_for_tri(arbiter_bias_model: Any) -> PSVRuntimeConfig:
    """从 ``TriLayerMetadata.arbiter_bias``（Pydantic）读取覆盖。"""
    if arbiter_bias_model is None:
        return load_psv_runtime_config(None)
    dump = arbiter_bias_model.model_dump(mode="python") if hasattr(arbiter_bias_model, "model_dump") else {}
    return load_psv_runtime_config(dump)


__all__ = ["PSVRuntimeConfig", "load_psv_runtime_config", "load_psv_runtime_config_for_tri"]
