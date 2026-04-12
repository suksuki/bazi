"""用户意志对物理参的注塑（Will Injection）与叙事刷新信号。

解析 persistence_layer.confirmed_verdicts 与 history_context.confirmed_verdicts
中 kinds/decision_kinds 含 UPDATE_PHYSICS_PARAM 的 payload，拆分写入 physics_config
与 interaction consensus 覆盖路径。
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Tuple, TypedDict

from app.api.contracts import PhysicsConfig
from app.schemas.bazi_metadata import BaziMetadata
from app.skills.physics_rules import DEFAULT_INTERACTION_PARAMS

UPDATE_PHYSICS_PARAM = "UPDATE_PHYSICS_PARAM"

_PHYSICS_KEYS = frozenset(PhysicsConfig.model_fields.keys())
_INTERACTION_KEYS = frozenset(DEFAULT_INTERACTION_PARAMS.keys())
_CORE_DEITIES = frozenset(
    ("比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印")
)


class WillInjectionOutcome(TypedDict, total=False):
    applied: bool
    interaction_overrides: Dict[str, float]


class EnergyStateSnapshot(TypedDict, total=False):
    global_entropy: Optional[float]
    deity_tiers: Dict[str, str]
    """按绝对能量轴分档：Abs_T1..Abs_T4（用于 T3→T4 跃迁强制叙事刷新）"""
    deity_abs_tiers: Dict[str, str]


def _kinds_from_obj(obj: Mapping[str, Any]) -> List[str]:
    raw = obj.get("kinds")
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    one = obj.get("kind")
    if isinstance(one, str) and one.strip():
        return [one.strip()]
    return []


def _payload_from_obj(obj: Mapping[str, Any]) -> Dict[str, Any]:
    p = obj.get("payload")
    if isinstance(p, dict):
        return dict(p)
    p2 = obj.get("physics_param_payload")
    if isinstance(p2, dict):
        return dict(p2)
    return {}


def collect_will_physics_param_merges(metadata_obj: BaziMetadata) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """汇总所有 UPDATE_PHYSICS_PARAM 的 payload，拆分为 physics_config 与 interaction 键。"""
    physics_out: Dict[str, Any] = {}
    interaction_out: Dict[str, float] = {}

    pl = metadata_obj.persistence_layer
    if pl is not None:
        for entry in pl.confirmed_verdicts or []:
            if hasattr(entry, "model_dump"):
                ed = entry.model_dump()
            elif isinstance(entry, dict):
                ed = entry
            else:
                continue
            kinds = list(ed.get("kinds") or _kinds_from_obj(ed))
            if UPDATE_PHYSICS_PARAM not in kinds:
                continue
            blob = dict(ed.get("payload") or _payload_from_obj(ed))
            _merge_split_payload(blob, physics_out, interaction_out)

    for rec in metadata_obj.history_context.confirmed_verdicts or []:
        kinds = list(rec.decision_kinds or [])
        if UPDATE_PHYSICS_PARAM not in kinds:
            continue
        _merge_split_payload(dict(rec.physics_param_payload or {}), physics_out, interaction_out)

    return physics_out, interaction_out


def _merge_split_payload(
    payload: Mapping[str, Any],
    physics_out: Dict[str, Any],
    interaction_out: Dict[str, float],
) -> None:
    for k_raw, v in payload.items():
        k = str(k_raw or "").strip()
        if not k:
            continue
        if k in _PHYSICS_KEYS:
            physics_out[k] = _coerce_physics_config_value(k, v)
        if k in _INTERACTION_KEYS:
            try:
                interaction_out[k] = float(v)
            except (TypeError, ValueError):
                continue


def _coerce_physics_config_value(key: str, v: Any) -> Any:
    if v is None:
        return None
    if key == "user_target_direction":
        return str(v)
    if isinstance(v, bool):
        return v
    try:
        return float(v)
    except (TypeError, ValueError):
        return v


def will_temporal_anchor_blocks_injection(
    metadata_obj: BaziMetadata,
    *,
    request_dayun: Optional[str],
) -> bool:
    """意志归档大运锚与当前请求大运不一致且有 UPDATE_PHYSICS_PARAM 时，禁止静默应用物理补丁。"""
    phys, inter = collect_will_physics_param_merges(metadata_obj)
    if not phys and not inter:
        return False
    tc = metadata_obj.temporal_context if isinstance(metadata_obj.temporal_context, dict) else {}
    effective = (request_dayun or "").strip() or str(tc.get("dayun_ganzhi") or tc.get("dayun") or "").strip()
    if not effective:
        return False
    pl = metadata_obj.persistence_layer
    anchor = (pl.will_temporal_anchor_dayun or "").strip() if pl is not None else ""
    if not anchor:
        return False
    return anchor != effective


def inject_user_decisions(
    metadata_obj: BaziMetadata,
    physics_config: Dict[str, Any],
    *,
    request_dayun: Optional[str] = None,
) -> WillInjectionOutcome:
    """将意志注塑合并进 physics_config；返回需并入 consensus_overrides 的 interaction 键。"""
    phys, inter = collect_will_physics_param_merges(metadata_obj)
    if not phys and not inter:
        return {"applied": False, "interaction_overrides": {}}
    if will_temporal_anchor_blocks_injection(metadata_obj, request_dayun=request_dayun):
        return {"applied": False, "interaction_overrides": {}}
    for k, v in phys.items():
        physics_config[k] = v
    return {"applied": True, "interaction_overrides": dict(inter)}


def _abs_energy_tier_label(abs_energy: Optional[float]) -> str:
    """与引擎 Abs 轴量级对齐的四档映射（仅用于跃迁检测，阈值可后续迁入 runtime_config）。"""
    if abs_energy is None or not isinstance(abs_energy, (int, float)) or not math.isfinite(float(abs_energy)):
        return "Abs_T0"
    a = abs(float(abs_energy))
    if a < 2.0:
        return "Abs_T1"
    if a < 4.5:
        return "Abs_T2"
    if a < 7.0:
        return "Abs_T3"
    return "Abs_T4"


def snapshot_energy_state(physics_tensor: Dict[str, Any]) -> EnergyStateSnapshot:
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    ge_raw = meta.get("global_entropy") if isinstance(meta, dict) else None
    ge: Optional[float] = None
    if isinstance(ge_raw, (int, float)) and math.isfinite(float(ge_raw)):
        ge = float(ge_raw)
    ds = physics_tensor.get("deity_scores") if isinstance(physics_tensor.get("deity_scores"), dict) else {}
    axes = physics_tensor.get("deity_energy_axes") if isinstance(physics_tensor.get("deity_energy_axes"), dict) else {}
    tiers: Dict[str, str] = {}
    abs_tiers: Dict[str, str] = {}
    vals: Dict[str, float] = {}
    for name, raw in ds.items():
        if str(name) not in _CORE_DEITIES:
            continue
        try:
            vals[str(name)] = float(raw)
        except (TypeError, ValueError):
            continue
    if vals:
        mx = max(abs(v) for v in vals.values()) or 1.0
        for name, v in vals.items():
            n = abs(v) / mx
            if n < 0.35:
                tiers[name] = "偏弱"
            elif n < 0.65:
                tiers[name] = "中庸"
            else:
                tiers[name] = "偏强"
    for name in _CORE_DEITIES:
        ax = axes.get(name) if isinstance(axes, dict) else None
        abs_e = None
        if isinstance(ax, dict):
            raw_abs = ax.get("absolute_energy")
            if isinstance(raw_abs, (int, float)) and math.isfinite(float(raw_abs)):
                abs_e = float(raw_abs)
        abs_tiers[name] = _abs_energy_tier_label(abs_e)
    return {"global_entropy": ge, "deity_tiers": tiers, "deity_abs_tiers": abs_tiers}


def _produce_tensor_with_interactions(
    *,
    metadata_obj: BaziMetadata,
    physics_config: Dict[str, Any],
    physics_skill: Any,
    session_id: Optional[int],
    dayun: Optional[str],
    liunian: Optional[str],
    consensus_extra: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    consumed = physics_skill.consume(
        {
            "metadata": metadata_obj,
            "session_id": session_id,
            "dayun": dayun,
            "liunian": liunian,
            "physics_config": dict(physics_config or {}),
        }
    )
    if consensus_extra:
        co = dict(consumed.get("consensus_overrides") or {})
        co.update(consensus_extra)
        consumed["consensus_overrides"] = co
    pt: Dict[str, Any] = physics_skill.produce(consumed)
    from app.services.helpers.interaction_pipeline import evaluate_interactions

    evaluate_interactions(
        physics_tensor=pt,
        metadata=metadata_obj,
        interaction_params=physics_skill.get_interaction_params(),
        physics_config=dict(physics_config or {}),
    )
    return pt


def narrative_refresh_needed(before: EnergyStateSnapshot, after: EnergyStateSnapshot) -> bool:
    """全局熵相对变动 >5%、相对档位跃迁，或任一核心十神 Abs_T3→Abs_T4 跃迁则要求终判叙事刷新。"""
    ge0, ge1 = before.get("global_entropy"), after.get("global_entropy")
    if ge0 is not None and ge1 is not None and math.isfinite(ge0) and math.isfinite(ge1):
        base = max(abs(ge0), 1e-6)
        if abs(ge1 - ge0) / base > 0.05:
            return True
    t0 = before.get("deity_tiers") or {}
    t1 = after.get("deity_tiers") or {}
    for k, tier1 in t1.items():
        tier0 = t0.get(k)
        if tier0 and tier1 and tier0 != tier1:
            return True
    a0 = before.get("deity_abs_tiers") or {}
    a1 = after.get("deity_abs_tiers") or {}
    for deity in _CORE_DEITIES:
        if a0.get(deity) == "Abs_T3" and a1.get(deity) == "Abs_T4":
            return True
    return False


def compute_energy_snapshot(
    *,
    metadata_obj: BaziMetadata,
    physics_config: Dict[str, Any],
    physics_skill: Any,
    session_id: Optional[int],
    dayun: Optional[str],
    liunian: Optional[str],
) -> EnergyStateSnapshot:
    """跑一遍 consume→produce→evaluate_interactions 后取能量快照（与 orchestrator 首段一致）。"""
    pt = _produce_tensor_with_interactions(
        metadata_obj=metadata_obj,
        physics_config=physics_config,
        physics_skill=physics_skill,
        session_id=session_id,
        dayun=dayun,
        liunian=liunian,
    )
    return snapshot_energy_state(pt)


def compute_pre_injection_physics_bundle(
    *,
    metadata_obj: BaziMetadata,
    physics_config: Dict[str, Any],
    physics_skill: Any,
    session_id: Optional[int],
    dayun: Optional[str],
    liunian: Optional[str],
) -> tuple[EnergyStateSnapshot, Dict[str, Any]]:
    """注塑前完整一帧：能量快照 + 十神展示字典（供 UI 虚线锚点）。"""
    pt = _produce_tensor_with_interactions(
        metadata_obj=metadata_obj,
        physics_config=physics_config,
        physics_skill=physics_skill,
        session_id=session_id,
        dayun=dayun,
        liunian=liunian,
    )
    scores = pt.get("deity_scores") if isinstance(pt.get("deity_scores"), dict) else {}
    axes = pt.get("deity_energy_axes") if isinstance(pt.get("deity_energy_axes"), dict) else {}
    out_scores: Dict[str, float] = {}
    for k, v in scores.items():
        try:
            out_scores[str(k)] = float(v)
        except (TypeError, ValueError):
            continue
    return snapshot_energy_state(pt), {"deity_scores": out_scores, "deity_energy_axes": dict(axes)}


def temporal_will_stale_warnings(
    metadata_obj: BaziMetadata,
    *,
    request_dayun: Optional[str],
) -> List[str]:
    """大运环境支与意志归档锚不一致时提示复核（不自动丢弃意志）。"""
    tc = metadata_obj.temporal_context if isinstance(metadata_obj.temporal_context, dict) else {}
    effective = (request_dayun or "").strip() or str(tc.get("dayun_ganzhi") or tc.get("dayun") or "").strip()
    if not effective:
        return []
    pl = metadata_obj.persistence_layer
    anchor = (pl.will_temporal_anchor_dayun or "").strip() if pl is not None else ""
    if not anchor:
        return []

    has_will = False
    if pl is not None:
        for entry in pl.confirmed_verdicts or []:
            ed = entry.model_dump() if hasattr(entry, "model_dump") else entry
            if not isinstance(ed, dict):
                continue
            kinds = list(ed.get("kinds") or _kinds_from_obj(ed))
            if UPDATE_PHYSICS_PARAM in kinds:
                has_will = True
                break
    if not has_will:
        for r in metadata_obj.history_context.confirmed_verdicts or []:
            if UPDATE_PHYSICS_PARAM in list(r.decision_kinds or []):
                has_will = True
                break
    if not has_will:
        return []
    if anchor != effective:
        return [
            f"[警告] 当前环境已由 {anchor} 变为 {effective}，历史意志补丁可能失效，请重新裁决。"
        ]
    return []
