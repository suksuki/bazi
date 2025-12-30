#!/usr/bin/env python3
"""
增强 FRAMEWORK_UTILITIES 模块的算法实现路径
"""

import json
from pathlib import Path

# 读取注册表
registry_path = Path(__file__).parent.parent / "core" / "subjects" / "framework_utilities" / "registry.json"
with open(registry_path, 'r', encoding='utf-8') as f:
    registry = json.load(f)

# 定义每个模块的算法实现路径
module_algorithms = {
    "MOD_19_BAZI_UTILITIES": {
        "reverse_calculator": {
            "function": "core.bazi_reverse_calculator.BaziReverseCalculator.reverse_calculate",
            "description": "从四柱反推出生日期",
            "parameters": {
                "precision": "high|medium|low",
                "consider_lichun": True
            }
        },
        "virtual_profile": {
            "function": "core.bazi_profile.VirtualBaziProfile",
            "description": "虚拟八字档案，从四柱反推并计算大运",
            "parameters": {}
        },
        "bazi_profile": {
            "function": "core.bazi_profile.BaziProfile",
            "description": "八字档案对象，封装排盘、大运、流年映射",
            "parameters": {}
        },
        "particle_nexus": {
            "function": "core.trinity.core.nexus.definitions.BaziParticleNexus",
            "description": "八字粒子连接定义，包含天干、地支、藏干等基础映射",
            "parameters": {}
        }
    },
    "MOD_20_SYS_CONFIG": {
        "config_manager": {
            "function": "core.config_manager.ConfigManager",
            "description": "系统配置管理器，加载和保存配置",
            "parameters": {}
        },
        "profile_manager": {
            "function": "core.profile_manager.ProfileManager",
            "description": "用户档案管理器，管理用户档案的持久化",
            "parameters": {}
        },
        "logic_registry": {
            "function": "core.logic_registry.LogicRegistry",
            "description": "逻辑注册表，管理主题和模块注册",
            "parameters": {}
        }
    },
    "MOD_21_INFLUENCE_BUS": {
        "influence_bus": {
            "function": "core.trinity.core.middleware.influence_bus.InfluenceBus",
            "description": "影响因子总线，注册和协调环境因子",
            "parameters": {}
        },
        "influence_factor": {
            "function": "core.trinity.core.middleware.influence_bus.InfluenceFactor",
            "description": "影响因子定义",
            "parameters": {}
        },
        "nonlinear_type": {
            "function": "core.trinity.core.middleware.influence_bus.NonlinearType",
            "description": "非线性类型枚举",
            "parameters": {}
        },
        "physics_tensor": {
            "function": "core.trinity.core.middleware.influence_bus.PhysicsTensor",
            "description": "物理张量，支持相位和频率",
            "parameters": {}
        }
    },
    "MOD_22_STATISTICAL_AUDIT": {
        "statistical_auditor": {
            "function": "core.statistical_audit.StatisticalAuditor",
            "description": "统计审计器主类",
            "parameters": {}
        },
        "detect_outliers": {
            "function": "core.statistical_audit.StatisticalAuditor.detect_outliers",
            "description": "离群值检测（Z-Score、IQR）",
            "parameters": {}
        },
        "check_gradient": {
            "function": "core.statistical_audit.StatisticalAuditor.check_gradient_vanishing",
            "description": "梯度消失判定",
            "parameters": {}
        },
        "distribution_stats": {
            "function": "core.statistical_audit.StatisticalAuditor.calculate_distribution_stats",
            "description": "分布统计计算",
            "parameters": {}
        },
        "singularity_verification": {
            "function": "core.statistical_audit.StatisticalAuditor.verify_singularity_existence",
            "description": "奇点存在性验证",
            "parameters": {}
        }
    }
}

# 更新每个模块的 algorithm_implementation
for module_id, algorithms in module_algorithms.items():
    if module_id in registry["patterns"]:
        pattern = registry["patterns"][module_id]
        
        # 更新 algorithm_implementation
        algo_impl = {
            "registry_loader": {
                "class": "core.registry_loader.RegistryLoader",
                "description": "读取本 JSON 配置并驱动上述引擎，实现100%算法复原"
            },
            "paths": {}
        }
        
        # 添加所有算法
        for algo_name, algo_data in algorithms.items():
            algo_impl[algo_name] = algo_data
            algo_impl["paths"][algo_name] = algo_data["function"]
        
        pattern["algorithm_implementation"] = algo_impl
        print(f"✅ 已更新 {module_id} 的算法实现路径 ({len(algorithms)} 个算法)")

# 保存
with open(registry_path, 'w', encoding='utf-8') as f:
    json.dump(registry, f, ensure_ascii=False, indent=2)

print(f"\n✅ 完成！已更新所有模块的算法实现路径")

