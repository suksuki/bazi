#!/usr/bin/env python3
"""
Antigravity Hierarchical Optimizer (V35.1)
===========================================

分层锁定调优系统：使用"顺序坐标下降法" (Sequential Coordinate Descent)
按照优先级顺序调优参数，避免"拆东墙补西墙"的问题。

使用方法:
    python scripts/auto_optimizer.py
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
import copy
import random
import math

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS


# ===========================================
# 1. 参数分组定义
# ===========================================

# Group 1: The Foundation (L1 - 核心物理层)
GROUP_L1_FOUNDATION = [
    ('physics', 'pillarWeights', 'month'),
    ('physics', 'pillarWeights', 'year'),
    ('physics', 'pillarWeights', 'day'),
    ('physics', 'pillarWeights', 'hour'),
    # 注意：structure 相关参数可能在 DEFAULT_FULL_ALGO_PARAMS 中
    # 如果不存在，可以在调优时跳过或使用默认值
]

# Group 2: The Dynamics (L2 - 能量流转层)
GROUP_L2_FLOW = [
    ('flow', 'generationEfficiency'),  # 生的传导率
    ('flow', 'controlImpact'),  # 克的阻尼率
    ('flow', 'dampingFactor'),  # 图网络全盘阻尼（如果存在）
    ('flow', 'spatialDecay', 'gap1'),  # 距离衰减（gap1）
    ('flow', 'spatialDecay', 'gap2'),  # 距离衰减（gap2）
    ('flow', 'globalEntropy'),  # [V42.1] 全局系统熵
    ('flow', 'outputDrainPenalty'),  # [V42.1] 食伤泄耗惩罚
]

# Group 3: The Modifiers (L3 - 交互修正层)
# 注意：阈值调优已移除，改为硬编码标准值（通过修复物理层来适配）
GROUP_L3_MODIFIERS = [
    ('flow', 'earthMetalMoistureBoost'),  # 润局系数（VAL_005专用）
    ('interactions', 'stemFiveCombination', 'bonus'),  # 合化增益
    ('interactions', 'branchEvents', 'clashDamping'),  # 冲战损耗
    # 阈值参数已移除：Strong >= 60.0, Weak <= 40.0 (硬编码)
]

# 参数边界定义
PARAM_BOUNDS = {
    # L1 参数边界
    ('physics', 'pillarWeights', 'month'): (0.5, 3.0),
    ('physics', 'pillarWeights', 'year'): (0.3, 2.0),
    ('physics', 'pillarWeights', 'day'): (0.5, 2.5),
    ('physics', 'pillarWeights', 'hour'): (0.3, 2.0),
    
    # L2 参数边界（V41.0: 解锁约束，适配化气/专旺逻辑）
    ('flow', 'generationEfficiency'): (0.1, 0.6),  # 允许适当的流通（解锁上限）
    ('flow', 'controlImpact'): (0.3, 1.5),  # 允许克的力量变化（降低下限，对应绝对值-0.8到-0.3）
    ('flow', 'dampingFactor'): (0.1, 0.7),  # 保持系统损耗约束
    ('flow', 'spatialDecay', 'gap1'): (0.3, 0.9),
    ('flow', 'spatialDecay', 'gap2'): (0.1, 0.6),
    
    # [V42.1] 新增熵增和泄耗参数
    ('flow', 'globalEntropy'): (0.03, 0.10),  # 全局系统熵（3%-10%每轮损耗）
    ('flow', 'outputDrainPenalty'): (1.0, 2.0),  # 食伤泄耗惩罚（1.0-2.0倍额外损耗）
    
    # L3 参数边界
    ('flow', 'earthMetalMoistureBoost'): (1.0, 5.0),
    ('interactions', 'stemFiveCombination', 'bonus'): (1.0, 3.0),
    ('interactions', 'branchEvents', 'clashDamping'): (0.1, 1.0),
}


# ===========================================
# 2. 辅助函数
# ===========================================

def load_test_cases() -> List[Dict[str, Any]]:
    """加载测试案例"""
    # 优先使用 golden_cases.json
    cases_path = project_root / "data" / "golden_cases.json"
    if cases_path.exists():
        with open(cases_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)
            print(f"✅ 已加载 {len(cases)} 个案例从 {cases_path}")
            return cases
    
    # Fallback: 使用 calibration_cases.json
    fallback_path = project_root / "data" / "calibration_cases.json"
    if fallback_path.exists():
        with open(fallback_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)
            print(f"⚠️  使用 fallback 数据源: {fallback_path}")
            return cases
    
    raise FileNotFoundError(f"无法找到测试数据文件")


def get_nested_value(config: Dict, path: Tuple) -> Any:
    """获取嵌套字典的值"""
    value = config
    for key in path:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value


def set_nested_value(config: Dict, path: Tuple, value: Any):
    """设置嵌套字典的值"""
    current = config
    for key in path[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    current[path[-1]] = value


def get_param_value(config: Dict, param_path: Tuple) -> Optional[float]:
    """获取参数值"""
    return get_nested_value(config, param_path)


def set_param_value(config: Dict, param_path: Tuple, value: float):
    """设置参数值（带边界检查）"""
    if param_path in PARAM_BOUNDS:
        min_val, max_val = PARAM_BOUNDS[param_path]
        value = max(min_val, min(max_val, value))
    set_nested_value(config, param_path, value)


def predict_strength(strength_score: float, 
                     strong_threshold: float = 60.0,
                     weak_threshold: float = 40.0) -> str:
    """根据占比分数预测身强身弱（使用动态阈值）"""
    if strength_score >= strong_threshold:
        return "Strong"
    elif strength_score >= weak_threshold:
        return "Balanced"
    else:
        return "Weak"


def calculate_loss(engine: GraphNetworkEngine, cases: List[Dict[str, Any]], 
                   target_labels: Optional[List[str]] = None,
                   config: Dict = None) -> float:
    """
    计算损失函数。
    
    Args:
        engine: GraphNetworkEngine 实例
        cases: 测试案例列表
        target_labels: 目标标签列表（None表示使用所有案例）
    
    Returns:
        总损失值（越小越好）
    """
    total_loss = 0.0
    count = 0
    
    for case in cases:
        true_label = case.get('true_label')
        if not true_label:
            continue
        
        if target_labels and true_label not in target_labels:
            continue
        
        try:
            result = engine.analyze(
                bazi=case['bazi'],
                day_master=case['day_master'],
                luck_pillar=None,
                year_pillar=None,
                geo_modifiers=None
            )
            
            strength_score = result.get('strength_score', 0.0)
            
            # 使用配置中的动态阈值
            if config:
                grading = config.get('grading', {})
                strong_threshold = grading.get('strong_threshold', 60.0)
                weak_threshold = grading.get('weak_threshold', 40.0)
            else:
                strong_threshold = 60.0
                weak_threshold = 40.0
            
            pred_label = predict_strength(strength_score, strong_threshold, weak_threshold)
            
            # 损失计算：预测错误惩罚 + 分数偏差（加权损失）
            # Balanced案例权重最高（3.0），因为最难算准
            weight_map = {"Strong": 1.0, "Weak": 1.0, "Balanced": 3.0}
            weight = weight_map.get(true_label, 1.0)
            
            if pred_label != true_label:
                # 错误预测：高惩罚
                if true_label == "Strong":
                    # 应该是Strong，但预测错了
                    target_score = 70.0
                    loss = (100.0 + abs(strength_score - target_score)) * weight
                elif true_label == "Weak":
                    # 应该是Weak，但预测错了
                    target_score = 30.0
                    loss = (100.0 + abs(strength_score - target_score)) * weight
                else:  # Balanced
                    # 应该是Balanced，但预测错了（最高惩罚）
                    target_score = 50.0
                    loss = (100.0 + abs(strength_score - target_score)) * weight
            else:
                # 预测正确，但分数可能不够理想
                if true_label == "Strong":
                    target_score = 70.0
                    loss = abs(strength_score - target_score) * 0.1 * weight
                elif true_label == "Weak":
                    target_score = 30.0
                    loss = abs(strength_score - target_score) * 0.1 * weight
                else:  # Balanced
                    target_score = 50.0
                    loss = abs(strength_score - target_score) * 0.1 * weight
            
            total_loss += loss
            count += 1
        
        except Exception as e:
            # 错误案例：高惩罚
            total_loss += 1000.0
            count += 1
    
    return total_loss / max(count, 1)  # 平均损失


# ===========================================
# 3. 分层调优逻辑
# ===========================================

def optimize_group(base_config: Dict, cases: List[Dict[str, Any]], 
                   param_group: List[Tuple], target_labels: List[str],
                   phase_name: str, epochs: int = 200, 
                   step_size: float = 0.05, patience: int = 50) -> Tuple[Dict, float]:
    """
    对指定参数组进行调优。
    
    Args:
        base_config: 基础配置（其他组已锁定）
        cases: 测试案例
        param_group: 参数组（参数路径列表）
        target_labels: 目标标签（如 ['Strong', 'Weak']）
        phase_name: 阶段名称
        epochs: 迭代次数
        step_size: 步长
        patience: 早停耐心值
    
    Returns:
        (最优配置, 最优损失)
    """
    print(f"\n{'='*80}")
    print(f"🔧 Phase: {phase_name}")
    print(f"{'='*80}")
    print(f"参数组: {len(param_group)} 个参数")
    print(f"目标标签: {target_labels}")
    print(f"迭代次数: {epochs}")
    print()
    
    # 过滤掉不存在的参数
    valid_params = []
    for param_path in param_group:
        if get_param_value(base_config, param_path) is not None:
            valid_params.append(param_path)
        else:
            print(f"⚠️  参数 {param_path} 不存在，跳过")
    
    if not valid_params:
        print("❌ 没有有效参数可调优")
        return base_config, calculate_loss(GraphNetworkEngine(base_config), cases, target_labels)
    
    print(f"✅ 有效参数: {len(valid_params)} 个")
    print()
    
    # 初始化
    best_config = copy.deepcopy(base_config)
    best_loss = calculate_loss(GraphNetworkEngine(best_config), cases, target_labels, best_config)
    no_improve_count = 0
    
    print(f"[初始] Loss: {best_loss:.2f}")
    print()
    
    # 迭代调优
    for epoch in range(epochs):
        improved = False
        
        # 随机选择一个参数进行调整
        param_path = random.choice(valid_params)
        current_value = get_param_value(best_config, param_path)
        
        if current_value is None:
            continue
        
        # 生成新值（在边界内）
        if param_path in PARAM_BOUNDS:
            min_val, max_val = PARAM_BOUNDS[param_path]
            range_size = max_val - min_val
            # 随机扰动（在合理范围内）
            perturbation = random.uniform(-step_size * range_size, step_size * range_size)
            new_value = current_value + perturbation
            new_value = max(min_val, min(max_val, new_value))
        else:
            # 如果没有边界，使用相对扰动
            perturbation = random.uniform(-step_size, step_size)
            new_value = current_value * (1 + perturbation)
        
        # 创建新配置
        test_config = copy.deepcopy(best_config)
        set_param_value(test_config, param_path, new_value)
        
        # 计算损失
        try:
            engine = GraphNetworkEngine(test_config)
            new_loss = calculate_loss(engine, cases, target_labels, test_config)
        except Exception as e:
            # 配置无效，跳过
            continue
        
        # 更新最优配置
        if new_loss < best_loss:
            best_config = test_config
            best_loss = new_loss
            improved = True
            no_improve_count = 0
            
            # 打印改进信息
            if (epoch + 1) % 10 == 0:
                print(f"[Epoch {epoch+1:4d}] Loss: {best_loss:.2f} | "
                      f"调整参数: {param_path[-1]} = {new_value:.3f} ✅")
        else:
            no_improve_count += 1
        
        # 早停
        if no_improve_count >= patience:
            print(f"\n⏸️  早停触发（{patience} 次无改进）")
            break
    
    print()
    print(f"✅ {phase_name} 完成")
    print(f"   最优 Loss: {best_loss:.2f}")
    print(f"   调优参数值:")
    for param_path in valid_params:
        value = get_param_value(best_config, param_path)
        if value is not None:
            print(f"      {'.'.join(param_path)} = {value:.3f}")
    
    return best_config, best_loss


def optimize_sequentially():
    """顺序分层调优主函数"""
    print("=" * 80)
    print("🚀 Antigravity Hierarchical Optimizer (V35.1)")
    print("=" * 80)
    print()
    
    # 1. 加载测试案例
    print("📋 加载测试案例...")
    cases = load_test_cases()
    print(f"   加载了 {len(cases)} 个案例")
    print()
    
    # 2. 加载基础配置
    print("🔧 加载配置...")
    base_config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    config_path = project_root / "config" / "parameters.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            # 深度合并配置
            def deep_merge(base, update):
                for key, value in update.items():
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        deep_merge(base[key], value)
                    else:
                        base[key] = value
            deep_merge(base_config, user_config)
        print(f"   ✅ 已加载用户配置: {config_path}")
    
    print()
    
    # 3. Phase 1: Calibrate Foundation (L1)
    print("=" * 80)
    print("📌 Phase 1: Calibrate Foundation (L1 - 核心物理层)")
    print("=" * 80)
    optimized_config, phase1_loss = optimize_group(
        base_config=base_config,
        cases=cases,
        param_group=GROUP_L1_FOUNDATION,
        target_labels=['Strong', 'Weak'],  # 重点关注极端案例
        phase_name="Foundation (L1)",
        epochs=500,  # 增加迭代次数
        step_size=0.03,  # 减小步长，更精细调优
        patience=100  # 增加耐心值
    )
    print(f"\n[Phase 1 Complete] Best Loss: {phase1_loss:.2f}. Locked Foundation Params.")
    
    # 4. Phase 2: Calibrate Flow (L2)
    print("\n" + "=" * 80)
    print("📌 Phase 2: Calibrate Flow (L2 - 能量流转层)")
    print("=" * 80)
    optimized_config, phase2_loss = optimize_group(
        base_config=optimized_config,  # 使用 Phase 1 的结果
        cases=cases,
        param_group=GROUP_L2_FLOW,
        target_labels=['Balanced'],  # 重点关注中和案例
        phase_name="Flow (L2)",
        epochs=500,  # 增加迭代次数，重点优化Balanced
        step_size=0.03,  # 减小步长
        patience=100  # 增加耐心值
    )
    print(f"\n[Phase 2 Complete] Best Loss: {phase2_loss:.2f}. Locked Flow Params.")
    
    # 5. Phase 3: Calibrate Edge Cases (L3)
    print("\n" + "=" * 80)
    print("📌 Phase 3: Calibrate Edge Cases (L3 - 交互修正层 + 动态阈值)")
    print("=" * 80)
    
    # [V41.0] Phase 3: 全量优化（使用所有案例和所有L3参数）
    optimized_config, phase3_loss = optimize_group(
        base_config=optimized_config,  # 使用 Phase 2 的结果
        cases=cases,  # 使用所有案例
        param_group=GROUP_L3_MODIFIERS,
        target_labels=None,  # 不限制标签，优化整体准确率
        phase_name="Modifiers (L3) - Post Logic Fix",
        epochs=500,  # 增加迭代次数
        step_size=0.05,  # 精细调优
        patience=100  # 增加耐心值
    )
    print(f"\n[Phase 3 Complete] Best Loss: {phase3_loss:.2f}. Locked Modifier Params.")
    
    # 6. 最终评估
    print("\n" + "=" * 80)
    print("📊 最终评估")
    print("=" * 80)
    
    final_engine = GraphNetworkEngine(optimized_config)
    final_loss = calculate_loss(final_engine, cases, target_labels=None, config=optimized_config)
    
    print(f"初始 Loss: {calculate_loss(GraphNetworkEngine(base_config), cases, None, base_config):.2f}")
    print(f"最终 Loss: {final_loss:.2f}")
    print(f"改进: {calculate_loss(GraphNetworkEngine(base_config), cases, None) - final_loss:.2f}")
    print()
    
    # 7. 保存优化后的配置
    print("💾 保存优化后的配置...")
    
    # 提取用户可配置的参数（不覆盖整个配置文件）
    output_config = {}
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            output_config = json.load(f)
    else:
        output_config = {}
    
    # 更新调优过的参数
    for param_group in [GROUP_L1_FOUNDATION, GROUP_L2_FLOW, GROUP_L3_MODIFIERS]:
        for param_path in param_group:
            value = get_param_value(optimized_config, param_path)
            if value is not None:
                set_param_value(output_config, param_path, value)
    
    # 保存
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(output_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 配置已保存到: {config_path}")
    print()
    print("=" * 80)
    print("✅ 分层调优完成！")
    print("=" * 80)
    print()
    print("📝 下一步:")
    print("   1. 刷新 Quantum Lab 页面")
    print("   2. 运行批量验证脚本查看准确率提升")
    print("   3. 如有需要，可再次运行调优以进一步优化")
    print()


# ===========================================
# 4. 主入口
# ===========================================

if __name__ == "__main__":
    try:
        optimize_sequentially()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

