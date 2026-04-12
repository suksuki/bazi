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
    # 盲派贼捕做功：受制方十二长生分组 → Work_Intensity 标度（plugins/blind_school/op_work_logic.py）
    "BLIND_WORK_INTENSITY_DEAD_TOMB": 1.5,
    "BLIND_WORK_INTENSITY_GROWTH": 0.5,
    "BLIND_WORK_INTENSITY_NEUTRAL": 1.0,
    # 旺衰枢纽：self_abs 低于该阈值时用神池偏向印比，否则偏向食伤财官（op_pivot_defense）
    "WS_PIVOT_SELF_WEAK_THRESHOLD": 5.0,
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
    "CHRONOS_V2_TEMPORAL_ENABLE": 1.0,
    # 十二长生状态算子（见 op_status + manifests/l1_status_manifest.json）
    "L1_STATUS_OP_ENABLE": 1.0,
    "STATUS_BOOST_MULTIPLIER": 1.15,
    "STATUS_DRAIN_MULTIPLIER": 0.85,
    # 长生状态机 Work_Efficiency（与 op_status.status_work_efficiency 对齐；勿在算子内写死）
    "STATUS_EFFICIENCY_PEAK": 1.25,
    "STATUS_EFFICIENCY_VALLEY": 0.4,
    "STATUS_EFFICIENCY_TOMB": 0.72,
    "STATUS_EFFICIENCY_NEUTRAL": 1.0,
    "STATUS_EFFICIENCY_LIN_GUAN": 1.12,
    # 天干五合（邻柱；见 op_stem_fusion）
    "L1_STEM_FUSION_ENABLE": 1.0,
    "STEM_FUSION_BRANCH_SUPPORT_RATIO": 0.26,
    "STEM_FUSION_VECTOR_LEAK_RATIO": 0.12,
    # L1 核心冲突算子族（见 core_operators/op_*_*.py；总开关 L1_CORE_CONFLICT_OPS_ENABLE）
    "L1_CORE_CONFLICT_OPS_ENABLE": 1.0,
    "L1_OWL_FOOD_DAMPING": 0.15,
    "L1_WEALTH_SEAL_COLLAPSE": 0.22,
    "L1_WEALTH_SEAL_ROUTING_YIN_FACTOR": 0.82,
    "L1_WEALTH_SEAL_ROUTING_CAI_FACTOR": 1.08,
    "L1_BLADE_CLASH_INSTABILITY": 0.85,
    "L1_ROBBER_WEALTH_ALLOC_LOSS": 0.18,
    "L1_GOV_KILL_EFFICIENCY_LOSS": 0.35,
    # 全局熵：羊刃冲不稳定性进入 metrics 的权重与归一化参考
    "ENTROPY_W_BLADE": 0.25,
    "ENTROPY_BLADE_REF": 0.6,
    # 地理方位算子 L1_OP_GEOGRAPHY：场强增益比例（南→火、北→水）
    "L1_OP_GEOGRAPHY_ENABLE": 1.0,
    "GEOG_DIRECTION_ABS_BOOST": 0.15,
    # 五行相生流通审计：归一化场强阈值（两端均大于则段为 FLOWING）
    "FLOW_AUDITOR_ABS_THRESHOLD": 0.06,
    # 深度地支算子 L1_OP_SUB_BRANCH_INTERACTION（系数走配置，不在算子内写死）
    "L1_SUB_BRANCH_OP_ENABLE": 1.0,
    "SUB_BRANCH_SANHE_ABS_BOOST": 0.06,
    # 三合：中神（子午卯酉）须落月/日支才认聚能；合化后 Abs 增益的 α 泄漏
    "SUB_BRANCH_SANHE_REQ_WANG_ZHI": 0.0,
    # ≥0.5：大运/流年支并入三合判定池（interaction_pipeline._branch_map_extended）
    "SANHE_INCLUDE_TEMPORAL_BRANCHES": 1.0,
    # ≥0.5：旺支门控下中神可落在大运/流年键（dayun/liunian），与月日并列
    "SANHE_TEMPORAL_WANG_ZHI_BRIDGE": 1.0,
    "SANHE_ALPHA_LEAKAGE": 0.0,
    "SUB_BRANCH_LIUHE_ABS_BOOST": 0.04,
    "SUB_BRANCH_SANXING_ABS_DAMP": 0.97,
    "SUB_BRANCH_ANHE_ABS_DAMP": 0.985,
    # 半合（两支成局缺一支）：合化能量系数 Phi 与 Abs/向量微调（见 op_sub_branch_interaction）
    "SUB_BRANCH_BANHE_PHI": 0.6,
    "SUB_BRANCH_BANHE_ABS_BOOST": 0.02,
    "SUB_BRANCH_BANHE_VECTOR_BOOST": 0.028,
    # 六害 / 六破：Abs 阻尼极轻，但必须写入 branch_interaction_audit；ENABLE<0.5 时跳过害/破判定与 UI 标
    "SUB_BRANCH_LIUHAI_ENABLE": 1.0,
    "SUB_BRANCH_LIUPO_ENABLE": 1.0,
    "SUB_BRANCH_LIUHAI_ABS_DAMP": 0.998,
    "SUB_BRANCH_LIUPO_ABS_DAMP": 0.998,
    # 六冲：Abs 总乘子（默认 1.0 不改变既有行为）
    "SUB_BRANCH_LIUCHONG_ABS_DAMP": 1.0,
    "MUKU_DEITY_DAMPING": 0.8,
    # 格局识别：从格能量集中度阈值与路由 η 翻转增益
    "PATTERN_CONG_DOMINANCE": 0.52,
    "PATTERN_ETA_FLIP_GAIN": 1.12,
    # L0 原子层（藏干表走 DB，以下为标量乘子 / 柱位偏置，与 Admin L0 卡片对齐）
    "L0_HIDDEN_ENERGY_SCALE": 1.0,
    "L0_ROOT_BOOST_FACTOR": 1.0,
    "L0_YM_DH_WEIGHT_RATIO": 1.0,
    # semantic_translator：仅用于 LLM 语义标签（不参与力学）；Abs 档位分界与熵/参数相对档
    "SEMANTIC_DEITY_ABS_T1": 0.15,
    "SEMANTIC_DEITY_ABS_T2": 1.0,
    "SEMANTIC_DEITY_ABS_T3": 2.5,
    "SEMANTIC_DEITY_ABS_T4": 5.0,
    "SEMANTIC_DEITY_ABS_T5": 12.0,
    "SEMANTIC_PARAM_REL_LOW": 0.97,
    "SEMANTIC_PARAM_REL_HIGH": 1.03,
    "SEMANTIC_ENTROPY_LOW": 0.35,
    "SEMANTIC_ENTROPY_HIGH": 0.65,
}


def resolve_physics_settings(overrides: Dict[str, Any] | None) -> Dict[str, float]:
    from app.core.physics.settings_manager import apply_db_layer_to_settings

    settings = apply_db_layer_to_settings(dict(DEFAULT_PHYSICS_SETTINGS))
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
