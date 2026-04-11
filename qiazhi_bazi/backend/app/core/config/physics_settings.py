"""Centralized configurable physics constants for runtime injection."""
from __future__ import annotations

from typing import Any, Dict

DEFAULT_PHYSICS_SETTINGS: Dict[str, float] = {
    "WEIGHT_LUCK": 0.4,
    "WEIGHT_YEAR": 0.2,
    "BASE_BACKFIRE_RISK": 0.20,
    "HIGH_IMBALANCE_RISK": 0.35,
    "TOMB_LOCK_RATE": 0.90,
    "GRAVE_BURST_MULTIPLIER": 1.3,
    "ENABLE_CLIMATE_HARD_FACTOR": 1.0,
    "CLIMATE_INTENSITY": 1.0,
    "STEM_RESONANCE_BOOST": 1.5,
    "TRANSFER_DISTANCE_DECAY": 0.1,
    "WORK_MIN_THRESHOLD": 0.5,
    "SHOW_WEAK_WORK_PATHS": 0.0,
    # 盲派六穿（害）：η 下限，高于普通「害」档（见 blind_work_evaluator.ETA_MAP）
    "MANGPAI_SIX_HARM_ETA": 0.99,
    # 盲派微模块 η：可独立调参（pierce 默认与 MANGPAI_SIX_HARM_ETA 对齐）
    "MANGPAI_ETA_PIERCE": 0.99,
    # 默认与 TOMB_LOCK_RATE 一致；可在 overrides 中单独覆盖 MANGPAI_ETA_TOMB
    "MANGPAI_ETA_TOMB": 0.90,
    "MANGPAI_ETA_HOST_GUEST": 1.0,
    # 伤官见官 L1：余气通道 Abs 损耗率上限；干支坐标畸变基准与衰减系数
    "SGJG_MINOR_ABS_LOSS_CAP_RATIO": 0.02,
    "SGJG_COORDINATE_DISTORTION_BASE": 1.0,
    "SGJG_COORDINATE_DISTORTION_DECAY": 0.3,
    # L1 核心冲突：双侧均为「藏」通道时，对基础 Abs 控制项应用的衰减系数（与明面 Surface 区分）
    "L1_DEEP_VISIBILITY_ABS_DECAY": 0.2,
    # Decision Inbox：低于该 Abs 损耗估计且无 CRITICAL 时不推送判词观察项
    "GLOBAL_DECISION_ABS_THRESHOLD": 5.0,
    # L1 base_physics 原子算子 η（与 plugins/base_physics/core_operators 对齐）
    "L1_OP_PROD_ETA": 1.0,
    "L1_OP_DEST_ETA": 1.0,
    "L1_OP_CONN_ETA": 1.0,
    # 跨柱干支维度：人工传导灵敏度（0=仅物理 Conductivity；2≈向全传导插值）
    "INTERDIMENSIONAL_CONDUCTIVITY": 0.0,
    # 维轴算子：屏蔽强度、跨柱传导衰减、虚态阻尼
    "INTERDIMENSIONAL_BARRIER_STRENGTH": 1.0,
    "CONDUCTIVITY_DECAY_RATE": 0.7,
    "GHOST_ENERGY_DAMPING": 0.3,
    # 盖头截脚 η、通根透干谐振倍率（与 StemBranchCouplingEngine 对齐）
    "MANGPAI_ETA_DIMENSIONAL_CRUSH": 0.6,
    "MANGPAI_ROOT_RESONANCE": 1.2,
    # 子开关：1=启用，0=关闭（由前端 physics_config 写入）
    "INTERDIMENSIONAL_SHIELD_ENABLE": 1.0,
    "STEM_BRANCH_ROOT_RESONANCE_ENABLE": 1.0,
    "STEM_BRANCH_VERTICAL_CRUSH_ENABLE": 1.0,
    # Chronos（月令司令 / 余气进气 meta，见 plugins/chronos）
    "CHRONOS_COMMAND_LEVER": 0.0,
    "CHRONOS_RESIDUAL_LEVER": 0.12,
    # 十二长生状态算子（见 op_status + manifests/l1_status_manifest.json）
    "L1_STATUS_OP_ENABLE": 1.0,
    "STATUS_BOOST_MULTIPLIER": 1.15,
    "STATUS_DRAIN_MULTIPLIER": 0.85,
}


def resolve_physics_settings(overrides: Dict[str, Any] | None) -> Dict[str, float]:
    settings = dict(DEFAULT_PHYSICS_SETTINGS)
    for key in settings.keys():
        if overrides and key in overrides:
            try:
                settings[key] = float(overrides[key])
            except Exception:
                # Ignore invalid override and keep default.
                pass
    # 墓库微模块 η 未单独覆盖时，与全局 TOMB_LOCK_RATE 对齐
    if not overrides or "MANGPAI_ETA_TOMB" not in overrides:
        settings["MANGPAI_ETA_TOMB"] = float(settings["TOMB_LOCK_RATE"])
    # 穿局 η 未单独覆盖时，与兼容键 MANGPAI_SIX_HARM_ETA 对齐
    if not overrides or "MANGPAI_ETA_PIERCE" not in overrides:
        settings["MANGPAI_ETA_PIERCE"] = float(settings["MANGPAI_SIX_HARM_ETA"])
    # L1 op_* 对应 skill 的演化 η（因果基因库），在 Lab / 默认 resolve 之后覆盖
    from app.core.evolution.dna_registry import merge_evolved_physics_from_dna

    return merge_evolved_physics_from_dna(settings)
