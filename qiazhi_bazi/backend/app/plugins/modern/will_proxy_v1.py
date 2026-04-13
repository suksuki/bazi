"""
V10.0–V10.1 WILL_PROXY：L3 意志代理。根据 ``user_intention`` 生成 ``parameter_overrides`` 与
``pattern_affinity_multipliers``，由编排器在物理推断前合并数值参数字典，并在 ``on_physics_complete``
阶段写入 ``physics_tensor.meta.intention_context`` 供 L2 法典乘算亲和度与红线/门控重塑。

V10.1：求财抬财星轴有效能量、放宽比劫夺财红线；避险抬高官杀门控 min_energy、收紧食伤/印类红线；
拓扑节点可带 ``pre_will_energy``（见 ``EnergyTopologySkill``）。
"""
from __future__ import annotations

from typing import Any, Dict, List, MutableMapping

# 与 PhysicsConfig / 前端 WillIntentionSelector 对齐
VALID_USER_INTENTIONS = frozenset({"seek_stability", "seek_wealth", "seek_fame"})

# 物理侧「补丁」：在编排器内与 DEFAULT_PHYSICS_SETTINGS 基线相加后夹紧（键须存在于 physics_settings）
_INTENTION_PHYSICS_DELTAS: Dict[str, Dict[str, float]] = {
    "seek_stability": {
        "HIGH_IMBALANCE_RISK": -0.05,
        "BASE_BACKFIRE_RISK": -0.04,
        "STEM_RESONANCE_BOOST": -0.06,
        # 枭神夺食等：略抬高食伤阻尼，与 L2 Seal/Output 红线收紧配套
        "L1_OWL_FOOD_DAMPING": 0.04,
        "SGJG_COORDINATE_DISTORTION_DECAY": -0.06,
    },
    "seek_wealth": {
        "WORK_MIN_THRESHOLD": -0.06,
        "STEM_RESONANCE_BOOST": 0.08,
        "L1_OP_PROD_ETA": 0.05,
        # 比劫夺财敏感度：略降分配损耗（约 10% 量级，对齐 DEFAULT 0.18）
        "L1_ROBBER_WEALTH_ALLOC_LOSS": -0.018,
    },
    "seek_fame": {
        "CLIMATE_INTENSITY": 0.04,
        "INTERDIMENSIONAL_CONDUCTIVITY": 0.08,
        "L1_OP_CONN_ETA": 0.04,
    },
}

# L2 亲和度乘子（在 exclusion 之后、写入 progress/affinity_score 之前应用）
_PATTERN_AFFINITY_MULTIPLIERS: Dict[str, Dict[str, float]] = {
    "seek_stability": {
        "GOV_PATTERN": 1.10,
        "KILL_PATTERN": 1.06,
        "WEALTH_PATTERN": 0.88,
        "FOLLOW_WEALTH": 0.90,
    },
    "seek_wealth": {
        "WEALTH_PATTERN": 1.14,
        "FOLLOW_WEALTH": 1.10,
        "GOV_PATTERN": 0.90,
        "KILL_PATTERN": 0.92,
    },
    "seek_fame": {
        "GOV_PATTERN": 1.05,
        "KILL_PATTERN": 1.04,
        "WEALTH_PATTERN": 1.04,
        "FOLLOW_WEALTH": 1.03,
        "JIANLU": 1.05,
    },
}


def normalize_user_intention(raw: Any) -> str:
    s = str(raw or "").strip()
    return s if s in VALID_USER_INTENTIONS else ""


def build_parameter_overrides(intention: str) -> Dict[str, float]:
    return dict(_INTENTION_PHYSICS_DELTAS.get(intention, {}))


def build_pattern_affinity_multipliers(intention: str) -> Dict[str, float]:
    return dict(_PATTERN_AFFINITY_MULTIPLIERS.get(intention, {}))


def apply_intention_physics_to_cfg(cfg: MutableMapping[str, Any], intention: str) -> None:
    """在 ``resolve_physics_settings`` 之前，把意志增量合并进 ``physics_config`` 工作副本。"""
    if not intention:
        return
    from app.core.config.physics_settings import DEFAULT_PHYSICS_SETTINGS

    for k, delta in build_parameter_overrides(intention).items():
        prev = cfg.get(k)
        base = float(prev) if prev is not None else float(DEFAULT_PHYSICS_SETTINGS.get(k, 0.0) or 0.0)
        cfg[k] = max(0.0, min(5.0, base + float(delta)))


def run_will_proxy_v1(**ctx: Any) -> Dict[str, Any]:
    """Registry ``on_physics_complete``：写入 ``meta.intention_context``（L2 引擎读取）。"""
    physics_tensor = ctx.get("physics_tensor") or {}
    if not isinstance(physics_tensor, dict):
        return {"verdict": "", "evidence": [], "confidence_score": 1.0}
    meta = physics_tensor.setdefault("meta", {})
    if not isinstance(meta, dict):
        return {"verdict": "", "evidence": [], "confidence_score": 1.0}

    md = ctx.get("metadata") if isinstance(ctx.get("metadata"), dict) else {}
    intention = normalize_user_intention(md.get("user_intention"))
    if not intention:
        meta.pop("intention_context", None)
        return {"verdict": "", "evidence": [], "confidence_score": 1.0}

    po = build_parameter_overrides(intention)
    mults = build_pattern_affinity_multipliers(intention)
    intent_ctx: Dict[str, Any] = {
        "version": "will_proxy_v1",
        "active_intention": intention,
        "parameter_overrides": po,
        "pattern_affinity_multipliers": mults,
    }
    # V10.1：L2 引擎内读写的标量（非法典 JSON，避免改 manifest）
    if intention == "seek_wealth":
        intent_ctx["l2_wealth_axis_eff_scale"] = 1.15
        intent_ctx["l2_robber_exclusion_relax_factor"] = 1.10
        intent_ctx["topology_node_will_inverse_factor"] = 1.06
    elif intention == "seek_stability":
        intent_ctx["l2_officer_min_energy_scale"] = 1.06
        intent_ctx["l2_output_seal_exclusion_tight_factor"] = 0.80
        intent_ctx["topology_node_will_inverse_factor"] = 0.97
    elif intention == "seek_fame":
        intent_ctx["topology_node_will_inverse_factor"] = 1.02
    meta["intention_context"] = intent_ctx
    evidence: List[str] = [
        f"will_proxy.active_intention={intention}",
        f"will_proxy.pattern_affinity_multipliers={mults}",
    ]
    return {
        "verdict": f"意志代理：{intention}",
        "evidence": evidence,
        "confidence_score": 1.0,
        "intention_context": dict(intent_ctx),
    }
