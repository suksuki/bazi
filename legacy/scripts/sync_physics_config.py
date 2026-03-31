import json
import sys
from pathlib import Path

# 添加路径以导入 core
sys.path.append(str(Path(__file__).parent.parent))

from core.config import config

def sync_config_to_ui_json():
    """
    V3.1 物理同步器 (全量最终版)
    将 core/config.py (Master) 完整编译为 core/config.json (UI Slave)
    """
    target_path = Path("core/config.json")
    
    # 1. 构建 UI 所需的完整 JSON 结构
    ui_data = {
        "physics_version": "3.1.2",
        "generated_by": "Antigravity V3.1.2 Ultra Sync Protocol",
        
        # --- 全局物理常数 (对应 @config.physics.*) ---
        "physics": {
            "weights": {
                "similarity": config.Physics.weights.similarity,
                "distance": config.Physics.weights.distance
            },
            "gaussian_sigma": config.Physics.gaussian_sigma,
            "energy_gate_k": config.Physics.energy_gate_k,
            "rooting_weights": config.Physics.rooting_weights,
            "projection_bonus": config.Physics.projection_bonus,
            "spatial_decay": config.Physics.spatial_decay,
            "global_entropy": config.Physics.global_entropy,
            "k_factor": config.Physics.k_factor
        },

        # --- 安全门控标准 (对应 @config.gating.*) ---
        "gating": {
            "min_self_energy": config.Gating.min_self_energy,
            "weak_self": config.Gating.weak_self,
            "weak_self_limit": config.Gating.weak_self_limit,
            "max_relation": config.Gating.max_relation,
            "min_wealth_level": config.Gating.min_wealth_level
        },

        # --- 能量传导 (对应 @config.flow.*) ---
        "flow": {
            "generation_efficiency": config.Flow.generation_efficiency,
            "control_impact": config.Flow.control_impact
        },
        
        # --- 交互作用 (对应 @config.interactions.*) ---
        "interactions": {
            "clash_damping": config.Interactions.clash_damping
        },
        
        # --- 通关机制 (对应 @config.mediation.*) ---
        "mediation": {
            "threshold": config.Mediation.threshold
        },

        # --- 奇点参数 (对应 @config.singularity.*) ---
        "singularity": {
            "distance_threshold": config.Singularity.distance_threshold,
            "threshold": config.Singularity.threshold
        },
        
        # --- 聚类参数 (对应 @config.clustering.*) ---
        "clustering": {
            "min_samples": config.Clustering.min_samples
        },
        
        # --- 完整性参数 (对应 @config.integrity.*) ---
        "integrity": {
            "threshold": config.Integrity.threshold
        },

        # --- 时空参数 (对应 @config.spacetime.*) ---
        "spacetime": {
            "macro_bonus": config.Spacetime.macro_bonus,
            "latitude_coefficients": config.Spacetime.latitude_coefficients,
            "invert_seasons": config.Spacetime.invert_seasons,
            "solar_time_correction": config.Spacetime.solar_time_correction
        },

        # --- 墓库参数 (对应 @config.vault.*) ---
        "vault": {
            "threshold": config.Vault.threshold,
            "sealed_damping": config.Vault.sealed_damping,
            "open_bonus": config.Vault.open_bonus,
            "collapse_penalty": config.Vault.collapse_penalty
        },

        # --- 格局特异性参数 (对应 @config.patterns.*) ---
        "patterns": {}
    }

    # --- A-03 映射逻辑 ---
    a03_conf = config.Patterns.a03
    ui_data["patterns"]["a03"] = {
        "mahalanobis_threshold": a03_conf.mahalanobis_threshold,
        "integrity_threshold": a03_conf.integrity_threshold,
        "alliance_e_min": a03_conf.alliance_e_min,
        "alliance_s_min": a03_conf.alliance_s_min,
        "alliance_r_min": a03_conf.alliance_r_min,
        "standard_e_min": a03_conf.standard_e_min,
        "standard_s_min": a03_conf.standard_s_min,
        "standard_o_max": a03_conf.standard_o_max
    }

    # --- D-02 映射逻辑 ---
    if hasattr(config.Patterns, "d02"):
        d02_conf = config.Patterns.d02
        ui_data["patterns"]["d02"] = {
             "syndicate_r_limit": getattr(d02_conf, "syndicate_r_limit", 0.0),
             "syndicate_m_limit": getattr(d02_conf, "syndicate_m_limit", 0.0),
             "collider_e_min": getattr(d02_conf, "collider_e_min", 0.0),
             "collider_m_min": getattr(d02_conf, "collider_m_min", 0.0),
             "collider_s_min": getattr(d02_conf, "collider_s_min", 0.0),
             "syndicate_e_min": getattr(d02_conf, "syndicate_e_min", 0.0),
             "syndicate_m_min": getattr(d02_conf, "syndicate_m_min", 0.0),
             "syndicate_r_min": getattr(d02_conf, "syndicate_r_min", 0.0),
        }

    # --- B-01 映射逻辑 ---
    if hasattr(config.Patterns, "b01"):
        b01_conf = config.Patterns.b01
        ui_data["patterns"]["b01"] = {
            "mahalanobis_threshold": b01_conf.mahalanobis_threshold,
            "integrity_threshold": b01_conf.integrity_threshold,
            "rejection_s_max": getattr(b01_conf, "rejection_s_max", 0.0),
            "rejection_e_min": getattr(b01_conf, "rejection_e_min", 0.0),
            "accrual_m_min": getattr(b01_conf, "accrual_m_min", 0.0),
        }

    # 2. 写入文件
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(ui_data, f, indent=4, ensure_ascii=False)
        print(f"✅ [Physics Sync] Ultra Universe Synced -> {target_path}")
    except Exception as e:
        print(f"❌ [Physics Sync] Failed: {e}")

if __name__ == "__main__":
    sync_config_to_ui_json()
