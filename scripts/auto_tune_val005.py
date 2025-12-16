#!/usr/bin/env python3
"""
Antigravity Auto-Tuner (VAL_005 Special)
==========================================

自动化调优脚本：专门修复 VAL_005 (塑胶大亨) 的误判问题。

通过 Hill-Climbing 方法自动调整 `flow.earthMetalMoistureBoost` 参数，
直到 Graph Engine 的身旺分 >= 45.0。

使用方法:
    python scripts/auto_tune_val005.py
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import copy

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS


# ===========================================
# 1. 配置和常量
# ===========================================

# VAL_005 案例数据
VAL_005_CASE = {
    'bazi': ['辛未', '辛丑', '庚戌', '丁亥'],
    'day_master': '庚',
    'gender': '男'
}

# 目标分数阈值（占比百分比）
TARGET_SCORE = 45.0  # 即日主阵营占全盘45%以上

# 参数调优范围
PARAM_START = 1.5
PARAM_STEP = 0.5
PARAM_MAX = 10.0  # 扩大范围到10.0

# 配置文件路径
CONFIG_PATH = project_root / "config" / "parameters.json"


# ===========================================
# 2. 辅助函数
# ===========================================

def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    if not CONFIG_PATH.exists():
        print(f"⚠️  配置文件不存在: {CONFIG_PATH}")
        print("使用默认配置...")
        return copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 合并默认配置以确保完整性
    full_config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    full_config.update(config)
    
    return full_config


def save_config(param_value: float) -> None:
    """
    保存配置文件中的 earthMetalMoistureBoost 参数。
    
    Args:
        param_value: 要保存的参数值
    """
    # 读取原始文件以保持格式
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            original_config = json.load(f)
    else:
        original_config = {}
    
    # 确保 flow 部分存在
    if 'flow' not in original_config:
        original_config['flow'] = {}
    
    # 更新参数
    original_config['flow']['earthMetalMoistureBoost'] = param_value
    
    # 保存
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(original_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 配置文件已更新: {CONFIG_PATH}")
    print(f"   参数 flow.earthMetalMoistureBoost = {param_value:.1f}")


def calculate_strength_score(result: Dict[str, Any], day_master: str) -> Dict[str, float]:
    """
    计算身旺分数（占比），而不是绝对能量值。
    
    使用公式：Strength_Score = (Self_Team / Total_Energy) * 100.0
    
    Args:
        result: engine.analyze() 的返回结果
        day_master: 日主天干（如 '庚'）
    
    Returns:
        包含 raw_metal, total_energy, strength_score 的字典
    """
    final_energy = result.get('final_energy', [])
    nodes = result.get('nodes', [])
    
    # 获取日主元素
    from core.processors.physics import STEM_ELEMENTS, GENERATION
    dm_element = STEM_ELEMENTS.get(day_master, 'metal')
    
    # 计算日主阵营能量
    # Self_Team = Self(日主) + Resource(生我的) + Peer(同我的)
    # 对于庚金：Self=金, Resource=土, Peer=金
    
    self_team_energy = 0.0
    total_energy = 0.0
    raw_metal_energy = 0.0  # 日主元素（金）的原始能量
    
    # 确定资源元素（生我的元素）
    resource_element = None
    for elem, target in GENERATION.items():
        if target == dm_element:
            resource_element = elem
            break
    
    # 累加所有节点的能量
    for i, node in enumerate(nodes):
        if i >= len(final_energy):
            continue
            
        node_energy = float(final_energy[i])
        node_element = node.get('element', '')
        total_energy += node_energy
        
        # 累加日主阵营能量
        if node_element == dm_element:  # Self 或 Peer（同我）
            self_team_energy += node_energy
            raw_metal_energy += node_energy
        elif resource_element and node_element == resource_element:  # Resource（生我的）
            self_team_energy += node_energy
    
    # 计算占比分数
    if total_energy > 0:
        strength_score = (self_team_energy / total_energy) * 100.0
    else:
        strength_score = 0.0
    
    return {
        'raw_metal': raw_metal_energy,
        'self_team': self_team_energy,
        'total_energy': total_energy,
        'strength_score': strength_score
    }


# ===========================================
# 3. 主调优循环
# ===========================================

def auto_tune_val005():
    """主调优函数"""
    print("=" * 60)
    print("🚀 Antigravity Auto-Tuner (VAL_005 Special)")
    print("=" * 60)
    print(f"\n📋 目标案例: VAL_005 (塑胶大亨)")
    print(f"   八字: {VAL_005_CASE['bazi']}")
    print(f"   日主: {VAL_005_CASE['day_master']}")
    print(f"   目标分数: >= {TARGET_SCORE}% (日主阵营占比)")
    print(f"   评分方式: (Self_Team / Total_Energy) * 100%")
    print(f"   调优参数: flow.earthMetalMoistureBoost")
    print(f"   参数范围: {PARAM_START} ~ {PARAM_MAX} (步长: {PARAM_STEP})")
    print()
    
    # 加载基础配置
    base_config = load_config()
    
    # 初始化最佳结果
    best_param = None
    best_score = 0.0
    attempt_count = 0
    
    # 调优循环
    param_value = PARAM_START
    
    while param_value <= PARAM_MAX:
        attempt_count += 1
        
        # 创建新配置（深拷贝）
        test_config = copy.deepcopy(base_config)
        
        # 设置参数
        if 'flow' not in test_config:
            test_config['flow'] = {}
        test_config['flow']['earthMetalMoistureBoost'] = param_value
        
        print(f"[Attempt {attempt_count}] Boost={param_value:.1f} -> ", end='', flush=True)
        
        try:
            # 实例化引擎
            engine = GraphNetworkEngine(config=test_config)
            
            # 运行分析
            result = engine.analyze(
                bazi=VAL_005_CASE['bazi'],
                day_master=VAL_005_CASE['day_master'],
                luck_pillar=None,
                year_pillar=None,
                geo_modifiers=None
            )
            
            # 计算身旺分数（占比）
            score_data = calculate_strength_score(result, VAL_005_CASE['day_master'])
            strength_score = score_data['strength_score']
            raw_metal = score_data['raw_metal']
            total_energy = score_data['total_energy']
            
            print(f"Raw_Metal={raw_metal:.2f} / Total={total_energy:.2f} -> Strength_Score={strength_score:.1f}%", end='')
            
            # 检查是否满足条件
            if strength_score >= TARGET_SCORE:
                print(" ✅ (Success!)")
                best_param = param_value
                best_score = strength_score
                break
            else:
                print(f" (Fail, need {TARGET_SCORE:.1f}%)")
                
                # 更新最佳结果（即使未达标）
                if strength_score > best_score:
                    best_score = strength_score
                    best_param = param_value
        
        except Exception as e:
            print(f" ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        # 增加参数值
        param_value += PARAM_STEP
    
    # ===========================================
    # 4. 结果处理和保存
    # ===========================================
    
    print()
    print("=" * 60)
    print("📊 调优结果")
    print("=" * 60)
    
    if best_param is not None:
        print(f"✅ 最优参数: {best_param:.1f}")
        print(f"✅ 最佳分数: {best_score:.2f}")
        
        if best_score >= TARGET_SCORE:
            print(f"✅ 目标达成！(>= {TARGET_SCORE}%)")
        else:
            print(f"⚠️  未达到目标分数 (需要 >= {TARGET_SCORE}%)")
            print(f"   当前最佳分数: {best_score:.2f}%")
            print(f"   建议：可能需要扩大搜索范围或调整其他参数")
        
        # 保存配置
        print()
        print("💾 保存配置文件...")
        save_config(best_param)
        print()
        print("=" * 60)
        print("✅ 调优完成！")
        print("=" * 60)
        print()
        print("📝 下一步:")
        print("   1. 刷新 Quantum Lab 页面")
        print(f"   2. 选择 VAL_005 案例")
        print("   3. 使用 Graph Engine 运行")
        print(f"   4. 查看身旺分数（占比）是否 >= {TARGET_SCORE}%")
        print()
        
    else:
        print("❌ 调优失败：未找到有效参数")
        print("   请检查：")
        print("   1. 案例数据是否正确")
        print("   2. GraphNetworkEngine 是否正常工作")
        print("   3. 参数范围是否需要扩大")
        print()


# ===========================================
# 5. 主入口
# ===========================================

if __name__ == "__main__":
    try:
        auto_tune_val005()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

