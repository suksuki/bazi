#!/usr/bin/env python3
"""
AI Trainer for Antigravity Graph Engine (V44.1)
================================================

使用 Optuna 贝叶斯优化框架进行分层超参数调优。
采用"分块坐标下降 (Block Coordinate Descent)"策略，分三个阶段串行优化。

版本: V44.1 (Hierarchical Tuning)
作者: Antigravity Team
日期: 2025-01-16
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import copy
import optuna
from optuna.trial import TrialState

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS


def load_golden_cases(data_path: Path = None) -> List[Dict[str, Any]]:
    """加载测试案例"""
    if data_path is None:
        data_path = project_root / "data" / "golden_cases.json"
    
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)
            return cases
    return []


def predict_strength(strength_score: float, 
                     strong_threshold: float = 60.0,
                     weak_threshold: float = 40.0) -> str:
    """根据占比分数预测身强身弱"""
    if strength_score >= strong_threshold:
        return "Strong"
    elif strength_score >= weak_threshold:
        return "Balanced"
    else:
        return "Weak"


def calculate_weighted_loss(engine: GraphNetworkEngine, cases: List[Dict[str, Any]], 
                           config: Dict) -> float:
    """
    计算加权损失函数。
    
    Args:
        engine: GraphNetworkEngine 实例
        cases: 测试案例列表
        config: 当前配置
    
    Returns:
        总损失值（越小越好）
    """
    total_loss = 0.0
    count = 0
    
    # 权重映射：重点关注 Balanced 和 Weak 案例
    # V49.0: 提升 Weak 权重到 4.0，解决虚高问题；Balanced 保持 4.0
    weight_map = {'Strong': 20.0, 'Weak': 20.0, 'Balanced': 20.0}
    
    # 目标分数
    target_scores = {"Strong": 85.0, "Weak": 20.0, "Balanced": 50.0}
    
    for case in cases:
        true_label = case.get('true_label')
        if not true_label:
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
            strength_label = result.get('strength_label', 'Unknown')
            
            # 使用引擎返回的标签（可能包含Special_Strong）
            if strength_label in ["Strong", "Balanced", "Weak", "Special_Strong"]:
                pred_label = strength_label
            else:
                # 如果引擎没有返回有效标签，使用阈值判断
                grading_config = config.get('grading', {})
                strong_threshold = grading_config.get('strong_threshold', 60.0)
                weak_threshold = grading_config.get('weak_threshold', 40.0)
                pred_label = predict_strength(strength_score, strong_threshold, weak_threshold)
            
            # 特殊格局例外处理
            is_correct = (pred_label == true_label)
            if not is_correct:
                if pred_label == "Special_Strong" and true_label in ["Balanced", "Strong"]:
                    is_correct = True
            
            # 计算损失
            weight = weight_map.get(true_label, 1.0)
            target_score = target_scores.get(true_label, 50.0)
            
            if is_correct:
                # 预测正确，但分数可能不够理想（小惩罚）
                score_error = abs(strength_score - target_score)
                loss = score_error * 0.1 * weight
            else:
                # 预测错误：高惩罚
                score_error = abs(strength_score - target_score)
                loss = (100.0 + score_error) * weight
            
            total_loss += loss
            count += 1
        
        except Exception as e:
            # 错误案例：极高惩罚
            total_loss += 1000.0 * weight_map.get(true_label, 1.0)
            count += 1
    
    # V47.0: 移除 L2 正则化，相信物理规律
    # 如果参数需要很大（如润局系数），那就让它大，不要为了数学上的"美观"去惩罚它
    return total_loss / max(count, 1)  # 纯物理损失，无正则化


# ===========================================
# 参数分组定义
# ===========================================

# Group 1: Foundation (地基层)
GROUP_1_FOUNDATION = [
    'physics.pillarWeights.month',
    'physics.pillarWeights.year',
    'physics.pillarWeights.day',
    'physics.pillarWeights.hour',
    'structure.rootingWeight',
]

# Group 2: Dynamics (动力层)
GROUP_2_DYNAMICS = [
    'flow.generationEfficiency',
    'flow.controlImpact',
    'flow.dampingFactor',
    'flow.globalEntropy',
    'flow.outputDrainPenalty',
]

# Group 3: Interactions (交互层)
GROUP_3_INTERACTIONS = [
    'flow.earthMetalMoistureBoost',
    'interactions.stemFiveCombination.bonus',
    'interactions.branchEvents.clashDamping',
]


def create_objective_for_group(
    group_params: List[str],
    locked_params: Dict[str, float],
    cases: List[Dict[str, Any]],
    base_config: Dict
):
    """
    为特定参数组创建目标函数。
    
    Args:
        group_params: 当前阶段要优化的参数列表
        locked_params: 已锁定的参数（来自前序阶段）
        cases: 测试案例
        base_config: 基础配置
    
    Returns:
        objective 函数
    """
    def objective(trial: optuna.Trial) -> float:
        # 加载基础配置
        config = copy.deepcopy(base_config)
        
        # 应用已锁定的参数
        for param_path, value in locked_params.items():
            set_nested_param(config, param_path, value)
        
        # ===========================================
        # 定义当前组的搜索空间
        # ===========================================
        
        # Group 1: Foundation (V45.0: 扩大搜索空间)
        if 'physics.pillarWeights.month' in group_params:
            config['physics']['pillarWeights']['month'] = trial.suggest_float(
                'physics.pillarWeights.month', 0.8, 2.0, step=0.05
            )
        if 'physics.pillarWeights.year' in group_params:
            config['physics']['pillarWeights']['year'] = trial.suggest_float(
                'physics.pillarWeights.year', 0.5, 1.8, step=0.05
            )
        if 'physics.pillarWeights.day' in group_params:
            config['physics']['pillarWeights']['day'] = trial.suggest_float(
                'physics.pillarWeights.day', 1.0, 1.8, step=0.05  # V49.0: 适当回调日主本气权重
            )
        if 'physics.pillarWeights.hour' in group_params:
            config['physics']['pillarWeights']['hour'] = trial.suggest_float(
                'physics.pillarWeights.hour', 0.5, 1.5, step=0.05
            )
        if 'structure.rootingWeight' in group_params:
            config['structure']['rootingWeight'] = trial.suggest_float(
                'structure.rootingWeight', 3.0, 6.0, step=0.1  # V49.0: 收紧上限到 6.0，防止微根变巨根
            )
        
        # Group 2: Dynamics (V45.0: 扩大搜索空间，特别是 controlImpact)
        if 'flow.generationEfficiency' in group_params:
            config['flow']['generationEfficiency'] = trial.suggest_float(
                'flow.generationEfficiency', 0.1, 0.4, step=0.05  # V47.0: 限制范围
            )
        if 'flow.controlImpact' in group_params:
            # V49.0: 保持高克制（保持重锤）
            # 代码中: return -0.3 * control_impact
            # 要得到 -3.0 的克制强度: -0.3 * x = -3.0 => x = 10.0
            # 要得到 -1.5 的克制强度: -0.3 * x = -1.5 => x = 5.0
            # 范围 [5.0, 10.0] 对应克制强度 [-1.5, -3.0]
            config['flow']['controlImpact'] = trial.suggest_float(
                'flow.controlImpact', 5.0, 10.0, step=0.1  # V49.0: 保持高强度克制（对应 -1.5 到 -3.0）
            )
        if 'flow.dampingFactor' in group_params:
            config['flow']['dampingFactor'] = trial.suggest_float(
                'flow.dampingFactor', 0.0, 0.4, step=0.05
            )
        if 'flow.globalEntropy' in group_params:
            config['flow']['globalEntropy'] = trial.suggest_float(
                'flow.globalEntropy', 0.05, 0.15, step=0.01  # V49.0: 适当增加全局损耗
            )
        if 'flow.outputDrainPenalty' in group_params:
            config['flow']['outputDrainPenalty'] = trial.suggest_float(
                'flow.outputDrainPenalty', 1.5, 3.0, step=0.1  # V49.0: 大幅提升食伤泄身力度
            )
        
        # Group 3: Interactions (V45.0: 扩大搜索空间)
        if 'flow.earthMetalMoistureBoost' in group_params:
            config['flow']['earthMetalMoistureBoost'] = trial.suggest_float(
                'flow.earthMetalMoistureBoost', 5.0, 15.0, step=0.5  # V47.0: 保持高润局系数
            )
        if 'interactions.stemFiveCombination.bonus' in group_params:
            config['interactions']['stemFiveCombination']['bonus'] = trial.suggest_float(
                'interactions.stemFiveCombination.bonus', 1.2, 2.5, step=0.1
            )
        if 'interactions.branchEvents.clashDamping' in group_params:
            config['interactions']['branchEvents']['clashDamping'] = trial.suggest_float(
                'interactions.branchEvents.clashDamping', 0.2, 0.8, step=0.1  # V45.0: 调整范围
            )
        
        # ===========================================
        # 运行模拟并计算损失
        # ===========================================
        
        if not cases:
            return float('inf')
        
        try:
            engine = GraphNetworkEngine(config=config)
        except Exception as e:
            return float('inf')
        
        loss = calculate_weighted_loss(engine, cases, config)
        return loss
    
    return objective


def set_nested_param(config: Dict, param_path: str, value: float):
    """
    设置嵌套参数值。
    
    Args:
        config: 配置字典
        param_path: 参数路径，如 'flow.generationEfficiency'
        value: 参数值
    """
    keys = param_path.split('.')
    current = config
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def get_nested_param(config: Dict, param_path: str) -> Optional[float]:
    """
    获取嵌套参数值。
    
    Args:
        config: 配置字典
        param_path: 参数路径
    
    Returns:
        参数值，如果不存在则返回 None
    """
    keys = param_path.split('.')
    current = config
    try:
        for key in keys[:-1]:
            current = current[key]
        return current[keys[-1]]
    except (KeyError, TypeError):
        return None


def save_best_params(best_params: Dict[str, float], output_path: Path = None):
    """
    保存最佳参数到配置文件。
    
    Args:
        best_params: Optuna 返回的最佳参数字典
        output_path: 输出文件路径
    """
    if output_path is None:
        output_path = project_root / "config" / "parameters.json"
    
    # 加载现有配置
    config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    # 如果存在现有配置文件，先加载它
    if output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            existing_config = json.load(f)
            def deep_merge(base, update):
                for key, value in update.items():
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        deep_merge(base[key], value)
                    else:
                        base[key] = value
            deep_merge(config, existing_config)
    
    # 应用最佳参数
    for param_path, value in best_params.items():
        set_nested_param(config, param_path, value)
    
    # 保存配置
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 最佳参数已保存到: {output_path}")


def print_stage_report(stage_name: str, initial_loss: float, final_loss: float,
                      best_params: Dict[str, float], previous_params: Dict[str, float] = None):
    """
    打印阶段报告。
    
    Args:
        stage_name: 阶段名称
        initial_loss: 初始损失
        final_loss: 最终损失
        best_params: 最佳参数
        previous_params: 前序阶段的参数（用于对比）
    """
    print("\n" + "=" * 80)
    print(f"📊 {stage_name} 阶段报告")
    print("=" * 80)
    print()
    
    improvement = initial_loss - final_loss
    improvement_pct = (improvement / initial_loss * 100) if initial_loss > 0 else 0.0
    
    print(f"损失变化: {initial_loss:.2f} → {final_loss:.2f}")
    print(f"改进幅度: {improvement:+.2f} ({improvement_pct:+.1f}%)")
    print()
    
    if previous_params:
        print("关键参数变化:")
        print("-" * 80)
        for param_name in best_params.keys():
            old_value = previous_params.get(param_name, None)
            new_value = best_params[param_name]
            if old_value is not None and abs(old_value - new_value) > 0.01:
                change = new_value - old_value
                print(f"  {param_name:40s}: {old_value:.3f} → {new_value:.3f} ({change:+.3f})")
        print()
    else:
        print("最佳参数:")
        print("-" * 80)
        for param_name, param_value in best_params.items():
            print(f"  {param_name:40s} = {param_value:.6f}")
        print()


def optimize_stage_1(locked_params: Dict[str, float], cases: List[Dict[str, Any]], 
                     base_config: Dict, n_trials: int = 200, seed_trial: Dict[str, float] = None) -> Dict[str, float]:
    """优化 Stage 1: Foundation"""
    print("🚀 Stage 1: 优化地基层 (Foundation)")
    print("   参数: 月令权重、年柱权重、通根系数等")
    print()
    
    # 计算初始损失
    config_init = copy.deepcopy(base_config)
    for param_path, value in locked_params.items():
        set_nested_param(config_init, param_path, value)
    engine_init = GraphNetworkEngine(config=config_init)
    initial_loss = calculate_weighted_loss(engine_init, cases, config_init)
    print(f"   初始损失: {initial_loss:.2f}")
    print()
    
    # 创建 Study
    study = optuna.create_study(
        direction="minimize",
        study_name="stage1_foundation",
        sampler=optuna.samplers.TPESampler(seed=42)
    )
    
    # V47.0: 种子初始化 - 注入 V45.0 最佳参数
    if seed_trial:
        study.enqueue_trial(seed_trial)
        print("   🌱 已注入种子参数（V45.0 最佳配置）")
    
    # 创建目标函数
    objective = create_objective_for_group(
        GROUP_1_FOUNDATION,
        {k: v for k, v in locked_params.items() if k not in GROUP_1_FOUNDATION},
        cases,
        base_config
    )
    
    # 运行优化
    print("   🔬 开始优化...")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True, n_jobs=1)
    
    # 返回最佳参数
    return study.best_params


def optimize_stage_2(locked_params: Dict[str, float], cases: List[Dict[str, Any]], 
                     base_config: Dict, n_trials: int = 200, seed_trial: Dict[str, float] = None) -> Dict[str, float]:
    """优化 Stage 2: Dynamics"""
    print("🚀 Stage 2: 优化动力层 (Dynamics)")
    print("   参数: 生克传导率、阻尼系数、熵增等")
    print()
    
    # 计算初始损失
    config_init = copy.deepcopy(base_config)
    for param_path, value in locked_params.items():
        set_nested_param(config_init, param_path, value)
    engine_init = GraphNetworkEngine(config=config_init)
    initial_loss = calculate_weighted_loss(engine_init, cases, config_init)
    print(f"   初始损失: {initial_loss:.2f}")
    print()
    
    # 创建 Study
    study = optuna.create_study(
        direction="minimize",
        study_name="stage2_dynamics",
        sampler=optuna.samplers.TPESampler(seed=42)
    )
    
    # V47.0: 种子初始化
    if seed_trial:
        study.enqueue_trial(seed_trial)
        print("   🌱 已注入种子参数")
    
    # 创建目标函数
    objective = create_objective_for_group(
        GROUP_2_DYNAMICS,
        locked_params,
        cases,
        base_config
    )
    
    # 运行优化
    print("   🔬 开始优化...")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True, n_jobs=1)
    
    # 返回最佳参数
    return study.best_params


def optimize_stage_3(locked_params: Dict[str, float], cases: List[Dict[str, Any]], 
                     base_config: Dict, n_trials: int = 200, seed_trial: Dict[str, float] = None) -> Dict[str, float]:
    """优化 Stage 3: Interactions"""
    print("🚀 Stage 3: 优化交互层 (Interactions)")
    print("   参数: 润局系数、合化加成、冲克阻尼等")
    print()
    
    # 计算初始损失
    config_init = copy.deepcopy(base_config)
    for param_path, value in locked_params.items():
        set_nested_param(config_init, param_path, value)
    engine_init = GraphNetworkEngine(config=config_init)
    initial_loss = calculate_weighted_loss(engine_init, cases, config_init)
    print(f"   初始损失: {initial_loss:.2f}")
    print()
    
    # 创建 Study
    study = optuna.create_study(
        direction="minimize",
        study_name="stage3_interactions",
        sampler=optuna.samplers.TPESampler(seed=42)
    )
    
    # V47.0: 种子初始化
    if seed_trial:
        study.enqueue_trial(seed_trial)
        print("   🌱 已注入种子参数")
    
    # 创建目标函数
    objective = create_objective_for_group(
        GROUP_3_INTERACTIONS,
        locked_params,
        cases,
        base_config
    )
    
    # 运行优化
    print("   🔬 开始优化...")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True, n_jobs=1)
    
    # 返回最佳参数
    return study.best_params


def run_cyclic_optimization(cases: List[Dict[str, Any]], base_config: Dict, 
                           cycles: int = 3) -> Dict[str, float]:
    """
    V45.0: 循环迭代优化
    
    Args:
        cases: 测试案例
        base_config: 基础配置
        cycles: 循环次数
    
    Returns:
        最终最佳参数
    """
    print("=" * 80)
    print("🔄 Antigravity Cyclic AI Trainer (V45.0)")
    print("   Cyclic Optimization Strategy")
    print("=" * 80)
    print()
    
    # 初始化锁定参数（从基础配置中提取）
    locked_params = {}
    all_params = GROUP_1_FOUNDATION + GROUP_2_DYNAMICS + GROUP_3_INTERACTIONS
    for param_path in all_params:
        value = get_nested_param(base_config, param_path)
        if value is not None:
            locked_params[param_path] = value
    
    # 计算初始损失
    config_init = copy.deepcopy(base_config)
    for param_path, value in locked_params.items():
        set_nested_param(config_init, param_path, value)
    engine_init = GraphNetworkEngine(config=config_init)
    initial_loss = calculate_weighted_loss(engine_init, cases, config_init)
    print(f"📊 初始损失: {initial_loss:.2f}")
    print()
    
    best_loss = initial_loss
    best_params = locked_params.copy()
    
    # V47.0: 计算总试验次数（减少到每轮 200）
    total_trials = cycles * (200 + 200 + 200)  # Foundation + Dynamics + Interactions
    print(f"📊 训练规模: {cycles} 个循环 × (200 + 200 + 200) = {total_trials} 次试验")
    print(f"   预计耗时: 约 {total_trials * 0.015:.0f} 秒")
    print()
    
    # V49.0: 准备种子参数（基于 V48.0，但调整泄耗参数）
    seed_params_v49 = {
        'structure.rootingWeight': 6.5,  # V48.0 的最佳值
        'physics.pillarWeights.day': 2.25,  # V48.0 的最佳值（会被限制到 1.8 以下）
        'flow.controlImpact': 9.7,  # V48.0: 高克制（对应 -2.91 的克制强度）
        'flow.earthMetalMoistureBoost': 5.5,  # V48.0 的最佳值
        'flow.generationEfficiency': 0.15,
        'flow.dampingFactor': 0.25,
        'flow.globalEntropy': 0.06,  # 会增加
        'flow.outputDrainPenalty': 1.0,  # 会增加
        'interactions.stemFiveCombination.bonus': 2.4,
        'interactions.branchEvents.clashDamping': 0.6,
    }
    
    # 循环优化
    for cycle in range(cycles):
        print("\n" + "=" * 80)
        print(f"🔄 Cycle {cycle + 1}/{cycles}")
        print("=" * 80)
        print()
        
        cycle_start_loss = best_loss
        
        # Round 1: Foundation
        print(f"--- Cycle {cycle + 1} - Stage 1: Foundation ---")
        # V49.0: 准备种子参数（只包含当前组的参数）
        seed_stage1 = {k: v for k, v in seed_params_v49.items() if k in GROUP_1_FOUNDATION}
        stage1_params = optimize_stage_1(best_params, cases, base_config, n_trials=200, seed_trial=seed_stage1)  # V49.0: 保持 200
        best_params.update(stage1_params)
        
        # 计算 Stage 1 后的损失
        config_s1 = copy.deepcopy(base_config)
        for param_path, value in best_params.items():
            set_nested_param(config_s1, param_path, value)
        engine_s1 = GraphNetworkEngine(config=config_s1)
        loss_s1 = calculate_weighted_loss(engine_s1, cases, config_s1)
        print(f"   Stage 1 后损失: {loss_s1:.2f}")
        print()
        
        # Round 2: Dynamics
        print(f"--- Cycle {cycle + 1} - Stage 2: Dynamics ---")
        # V49.0: 准备种子参数（只包含当前组的参数）
        seed_stage2 = {k: v for k, v in seed_params_v49.items() if k in GROUP_2_DYNAMICS}
        stage2_params = optimize_stage_2(best_params, cases, base_config, n_trials=200, seed_trial=seed_stage2)  # V49.0: 保持 200
        best_params.update(stage2_params)
        
        # 计算 Stage 2 后的损失
        config_s2 = copy.deepcopy(base_config)
        for param_path, value in best_params.items():
            set_nested_param(config_s2, param_path, value)
        engine_s2 = GraphNetworkEngine(config=config_s2)
        loss_s2 = calculate_weighted_loss(engine_s2, cases, config_s2)
        print(f"   Stage 2 后损失: {loss_s2:.2f}")
        print()
        
        # Round 3: Interactions
        print(f"--- Cycle {cycle + 1} - Stage 3: Interactions ---")
        # V49.0: 准备种子参数（只包含当前组的参数）
        seed_stage3 = {k: v for k, v in seed_params_v49.items() if k in GROUP_3_INTERACTIONS}
        stage3_params = optimize_stage_3(best_params, cases, base_config, n_trials=200, seed_trial=seed_stage3)  # V49.0: 保持 200
        best_params.update(stage3_params)
        
        # 计算 Stage 3 后的损失
        config_s3 = copy.deepcopy(base_config)
        for param_path, value in best_params.items():
            set_nested_param(config_s3, param_path, value)
        engine_s3 = GraphNetworkEngine(config=config_s3)
        loss_s3 = calculate_weighted_loss(engine_s3, cases, config_s3)
        print(f"   Stage 3 后损失: {loss_s3:.2f}")
        print()
        
        # 更新最佳损失
        if loss_s3 < best_loss:
            best_loss = loss_s3
        
        # 打印 Cycle 报告
        cycle_improvement = cycle_start_loss - loss_s3
        cycle_improvement_pct = (cycle_improvement / cycle_start_loss * 100) if cycle_start_loss > 0 else 0.0
        
        print("=" * 80)
        print(f"📊 Cycle {cycle + 1} 报告")
        print("=" * 80)
        print(f"损失变化: {cycle_start_loss:.2f} → {loss_s3:.2f}")
        print(f"改进幅度: {cycle_improvement:+.2f} ({cycle_improvement_pct:+.1f}%)")
        print()
        
        # Checkpoint: 保存当前最佳参数
        save_best_params(best_params)
        print(f"✅ Cycle {cycle + 1} 最佳参数已保存")
        print()
    
    return best_params


def main():
    """主函数：执行循环优化"""
    print("=" * 80)
    print("🤖 Antigravity Cyclic AI Trainer (V49.0)")
    print("   The Leakage Valve: Precision Drain for Weak Cases")
    print("=" * 80)
    print()
    
    # 加载测试案例
    print("📋 加载测试案例...")
    cases = load_golden_cases()
    print(f"   已加载 {len(cases)} 个案例")
    print()
    
    if not cases:
        print("❌ 错误: 未找到测试案例")
        return
    
    # 加载基础配置
    base_config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    # 如果存在现有配置文件，先加载它
    config_path = project_root / "config" / "parameters.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            existing_config = json.load(f)
            def deep_merge(base, update):
                for key, value in update.items():
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        deep_merge(base[key], value)
                    else:
                        base[key] = value
            deep_merge(base_config, existing_config)
        print("📂 已加载现有配置文件作为起点")
        print()
    
    # ===========================================
    # V45.0: 循环迭代优化
    # ===========================================
    best_params = run_cyclic_optimization(cases, base_config, cycles=3)  # V47.0: 减少到 3 个循环（区间已精准）
    
    # ===========================================
    # 最终报告
    # ===========================================
    print("\n" + "=" * 80)
    print("📊 最终训练报告")
    print("=" * 80)
    print()
    
    # 计算最终损失
    config_final = copy.deepcopy(base_config)
    for param_path, value in best_params.items():
        set_nested_param(config_final, param_path, value)
    engine_final = GraphNetworkEngine(config=config_final)
    final_loss = calculate_weighted_loss(engine_final, cases, config_final)
    
    print(f"最终损失: {final_loss:.2f}")
    print()
    
    print("最终最佳参数:")
    print("-" * 80)
    for param_name, param_value in sorted(best_params.items()):
        print(f"  {param_name:40s} = {param_value:.6f}")
    print()
    
    # 保存最佳参数
    print("💾 保存最终最佳参数...")
    save_best_params(best_params)
    print()
    
    # 生成改进报告（准确率）
    print("=" * 80)
    print("📈 准确率报告")
    print("=" * 80)
    print()
    
    correct_count = 0
    total_count = 0
    label_stats = {"Strong": {"correct": 0, "total": 0}, 
                   "Balanced": {"correct": 0, "total": 0},
                   "Weak": {"correct": 0, "total": 0}}
    
    for case in cases:
        true_label = case.get('true_label')
        if not true_label:
            continue
        
        try:
            result = engine_final.analyze(
                bazi=case['bazi'],
                day_master=case['day_master'],
                luck_pillar=None,
                year_pillar=None,
                geo_modifiers=None
            )
            
            strength_score = result.get('strength_score', 0.0)
            strength_label = result.get('strength_label', 'Unknown')
            
            # 使用引擎返回的标签
            if strength_label in ["Strong", "Balanced", "Weak", "Special_Strong"]:
                pred_label = strength_label
            else:
                grading_config = config_final.get('grading', {})
                strong_threshold = grading_config.get('strong_threshold', 60.0)
                weak_threshold = grading_config.get('weak_threshold', 40.0)
                pred_label = predict_strength(strength_score, strong_threshold, weak_threshold)
            
            # 特殊格局例外处理
            is_correct = (pred_label == true_label)
            if not is_correct:
                if pred_label == "Special_Strong" and true_label in ["Balanced", "Strong"]:
                    is_correct = True
            
            total_count += 1
            if is_correct:
                correct_count += 1
            
            if true_label in label_stats:
                label_stats[true_label]["total"] += 1
                if is_correct:
                    label_stats[true_label]["correct"] += 1
        
        except Exception as e:
            print(f"⚠️  案例 {case.get('id')} 出错: {e}")
    
    # 打印统计
    accuracy = (correct_count / total_count * 100) if total_count > 0 else 0.0
    print(f"总准确率: {accuracy:.1f}% ({correct_count}/{total_count})")
    print()
    
    print("按标签分类的准确率:")
    print("-" * 80)
    for label, stats in label_stats.items():
        if stats["total"] > 0:
            label_accuracy = (stats["correct"] / stats["total"] * 100)
            print(f"  {label:10s}: {label_accuracy:.1f}% ({stats['correct']}/{stats['total']})")
    print()
    
    print("=" * 80)
    print("✅ 循环 AI 训练完成")
    print("=" * 80)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
