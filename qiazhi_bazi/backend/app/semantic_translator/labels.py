from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

_TEN_DEITIES = ("比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀", "正印", "偏印")

# 分界从 physics_settings 读取（见 DEFAULT_PHYSICS_SETTINGS）
_DEFAULT_TIERS: Tuple[float, ...] = (0.15, 1.0, 2.5, 5.0, 12.0)
_DEFAULT_TIER_LABELS: Tuple[str, ...] = ("全无/可忽略", "极弱", "偏弱", "中庸可用", "偏强", "独强/执拗")


def _deity_abs_label(abs_energy: float, settings: Dict[str, float]) -> str:
    t1 = float(settings.get("SEMANTIC_DEITY_ABS_T1", _DEFAULT_TIERS[0]))
    t2 = float(settings.get("SEMANTIC_DEITY_ABS_T2", _DEFAULT_TIERS[1]))
    t3 = float(settings.get("SEMANTIC_DEITY_ABS_T3", _DEFAULT_TIERS[2]))
    t4 = float(settings.get("SEMANTIC_DEITY_ABS_T4", _DEFAULT_TIERS[3]))
    t5 = float(settings.get("SEMANTIC_DEITY_ABS_T5", _DEFAULT_TIERS[4]))
    if abs_energy < t1:
        return _DEFAULT_TIER_LABELS[0]
    if abs_energy < t2:
        return _DEFAULT_TIER_LABELS[1]
    if abs_energy < t3:
        return _DEFAULT_TIER_LABELS[2]
    if abs_energy < t4:
        return _DEFAULT_TIER_LABELS[3]
    if abs_energy < t5:
        return _DEFAULT_TIER_LABELS[4]
    return _DEFAULT_TIER_LABELS[5]


def _param_eta_tag(key: str, value: float, baseline: float | None, settings: Dict[str, float]) -> str:
    if baseline is None or baseline <= 0.0:
        return f"{key}=已设定"
    lo = float(settings.get("SEMANTIC_PARAM_REL_LOW", 0.97))
    hi = float(settings.get("SEMANTIC_PARAM_REL_HIGH", 1.03))
    ratio = value / baseline
    if ratio < lo:
        return f"{key}=相对基线偏紧(η↓)"
    if ratio > hi:
        return f"{key}=相对基线偏松(η↑)"
    return f"{key}=相对基线中性"


def _entropy_tier(val: float, settings: Dict[str, float]) -> str:
    low = float(settings.get("SEMANTIC_ENTROPY_LOW", 0.35))
    high = float(settings.get("SEMANTIC_ENTROPY_HIGH", 0.65))
    if val < low:
        return "全局熵=低(场相对有序)"
    if val > high:
        return "全局熵=高(场相对混沌)"
    return "全局熵=中(场势均衡)"


def _confidence_tier(val: float) -> str:
    if val < 0.45:
        return "物理置信=偏低"
    if val < 0.72:
        return "物理置信=中等"
    return "物理置信=偏高"


def build_semantic_label_bundle(
    *,
    physics_tensor: Dict[str, Any],
    physics_settings: Dict[str, float],
) -> Dict[str, Any]:
    """产出可 JSON 序列化的标签包 + verified_fact_lines（无数值）。"""
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    params = meta.get("params") if isinstance(meta.get("params"), dict) else {}
    axes = pt.get("deity_energy_axes") if isinstance(pt.get("deity_energy_axes"), dict) else {}
    abs_nodes = pt.get("abs_nodes") if isinstance(pt.get("abs_nodes"), dict) else {}

    deity_tags: Dict[str, str] = {}
    deity_lines: List[str] = []
    for d in _TEN_DEITIES:
        abs_energy: float | None = None
        ax = axes.get(d) if isinstance(axes, dict) else None
        if isinstance(ax, dict):
            try:
                abs_energy = float(ax.get("absolute_energy") or 0.0)
            except (TypeError, ValueError):
                abs_energy = None
        if abs_energy is None:
            raw = abs_nodes.get(d)
            if isinstance(raw, (int, float)):
                try:
                    abs_energy = float(raw)
                except (TypeError, ValueError):
                    abs_energy = None
        if abs_energy is None:
            continue
        tier = _deity_abs_label(abs_energy, physics_settings)
        deity_tags[d] = tier
        deity_lines.append(f"VF·十神.{d}.Abs档={tier}")

    param_tags: Dict[str, str] = {}
    param_lines: List[str] = []
    for key, raw in params.items():
        k = str(key)
        if not k:
            continue
        try:
            v = float(raw)
        except (TypeError, ValueError):
            continue
        baseline = physics_settings.get(k)
        tag = _param_eta_tag(k, v, float(baseline) if baseline is not None else None, physics_settings)
        param_tags[k] = tag
        param_lines.append(f"VF·交互参数.{tag}")

    ge_raw = meta.get("global_entropy")
    entropy_line = ""
    entropy_tag = ""
    try:
        ge = float(ge_raw) if ge_raw is not None else None
    except (TypeError, ValueError):
        ge = None
    if ge is not None:
        entropy_tag = _entropy_tier(ge, physics_settings)
        entropy_line = f"VF·{entropy_tag}"

    conf_raw = pt.get("confidence")
    conf_line = ""
    try:
        cf = float(conf_raw) if conf_raw is not None else None
    except (TypeError, ValueError):
        cf = None
    if cf is not None:
        conf_line = f"VF·{_confidence_tier(cf)}"

    verified_fact_lines: List[str] = []
    verified_fact_lines.extend(deity_lines[:20])
    verified_fact_lines.extend(param_lines[:24])
    if entropy_line:
        verified_fact_lines.append(entropy_line)
    if conf_line:
        verified_fact_lines.append(conf_line)

    return {
        "schema": "semantic_label_bundle.v1",
        "deity_abs_tags": deity_tags,
        "interaction_param_tags": param_tags,
        "global_entropy_tag": entropy_tag,
        "confidence_tag": conf_line,
        "verified_fact_lines": verified_fact_lines,
    }


def attach_semantic_labels_to_physics_meta(
    physics_tensor: Dict[str, Any],
    *,
    physics_settings: Dict[str, float],
) -> None:
    if not isinstance(physics_tensor, dict):
        return
    physics_tensor.setdefault("meta", {})
    meta = physics_tensor["meta"]
    if not isinstance(meta, dict):
        physics_tensor["meta"] = {}
        meta = physics_tensor["meta"]
    meta["semantic_label_bundle_v1"] = build_semantic_label_bundle(
        physics_tensor=physics_tensor,
        physics_settings=physics_settings,
    )


def format_bundle_for_first_observation(bundle: Dict[str, Any]) -> str:
    lines = bundle.get("verified_fact_lines") if isinstance(bundle.get("verified_fact_lines"), list) else []
    safe = [str(x).strip() for x in lines if str(x).strip()]
    if not safe:
        return ""
    try:
        return "[Verified Facts·语义标签-only]\n" + json.dumps(safe, ensure_ascii=False)
    except (TypeError, ValueError):
        return ""
