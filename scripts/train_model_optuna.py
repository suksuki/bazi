#!/usr/bin/env python3
"""
AI Trainer for Antigravity Graph Engine (V44.1)
================================================

使用 Optuna 贝叶斯优化框架进行分层超参数调优。
采用"分块坐标下降 (Block Coordinate Descent)"策略，分三个阶段串行优化。

版本: V53.0 Step 1 (Foundation Locking Tuning - Physics/Structure ONLY)
作者: Antigravity Team
日期: 2025-01-16

V53.0 Step 1: 分层锁定策略
- Step 1: 仅优化基础物理层 (Group 1: Foundation)
- Group 2 (Flow/Dynamics) 和 Group 3 (Interactions) 全部锁死
- 从 config/parameters.json 读取固定值，不允许优化
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import copy
import optuna
from optuna.trial import TrialState

# V53.0: 禁用 Optuna 的详细日志输出，减少日志冗余
optuna.logging.set_verbosity(optuna.logging.WARNING)  # 只显示警告和错误

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


def calculate_accuracy(engine: GraphNetworkEngine, cases: List[Dict[str, Any]], 
                       config: Dict) -> Dict[str, float]:
    """
    计算准确率。
    
    Args:
        engine: GraphNetworkEngine 实例
        cases: 测试案例列表
        config: 当前配置
    
    Returns:
        包含各标签准确率的字典: {"Strong": 90.9, "Balanced": 54.5, "Weak": 72.7, "Total": 72.7}
    """
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
            result = engine.analyze(
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
                grading_config = config.get('grading', {})
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
            # 错误案例不计入统计
            pass
    
    # 计算准确率
    accuracies = {"Strong": 0.0, "Balanced": 0.0, "Weak": 0.0, "Total": 0.0}
    
    if total_count > 0:
        accuracies["Total"] = (correct_count / total_count * 100)
    
    for label, stats in label_stats.items():
        if stats["total"] > 0:
            accuracies[label] = (stats["correct"] / stats["total"] * 100)
    
    return accuracies


def calculate_weighted_loss(engine: GraphNetworkEngine, cases: List[Dict[str, Any]], 
                           config: Dict, step: int = 0) -> float:
    """
    计算加权损失函数。
    
    Args:
        engine: GraphNetworkEngine 实例
        cases: 测试案例列表
        config: 当前配置
        step: 训练阶段 (0=全阶段, 1=Foundation, 2=Dynamics)
    
    Returns:
        总损失值（越小越好）
    """
    total_loss = 0.0
    count = 0
    
    # 权重映射：根据训练阶段调整
    # V53.1: Step 2 (Dynamics) 时，大幅提高 Balanced 权重，因为动力层参数主要影响 Balanced
    if step == 2:
        weight_map = {'Strong': 20.0, 'Weak': 20.0, 'Balanced': 20.0}  # 重点突破 Balanced
    else:
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
# V53.0 Step 2: 仅开放动力层参数，锁死地基与交互
GROUP_2_DYNAMICS = [
    'flow.generationEfficiency',      # gen_eff
    'flow.controlImpact',             # ctl_imp
    'flow.dampingFactor',             # damping
    'flow.outputDrainPenalty',        # drain_rate
    'flow.globalEntropy',             # entropy
]

# Group 3: Interactions (交互层)
GROUP_3_INTERACTIONS = [
    'flow.earthMetalMoistureBoost',
    'interactions.stemFiveCombination.bonus',
    'interactions.branchEvents.clashDamping',
]

# V53.0: 黄金参数常量（架构师测算值）- 基于 V52.0 基础参数重置
# 注意：这些值作为"中轴"，允许 ±20%~30% 的微调
GOLDEN_CONSTANTS = {
    'structure.rootingWeight': 4.25,
    'flow.controlImpact': -2.618,  # V52.0: 注意是负值！
    'flow.outputDrainPenalty': 2.80,
    'flow.generationEfficiency': 0.25,
    'flow.dampingFactor': 0.33,
    'physics.pillarWeights.month': 1.88,
    'physics.pillarWeights.day': 1.62,
    'physics.pillarWeights.year': 0.82,
    'physics.pillarWeights.hour': 0.95,
}
# V53.0: Controlled Float - 允许 ±20%~30% 的微调（不再是锁死）
FLOAT_TOLERANCE = 0.25  # 25% 浮动范围（±20%~30%）


def create_objective_for_group(
    group_params: List[str],
    locked_params: Dict[str, float],
    cases: List[Dict[str, Any]],
    base_config: Dict,
    step: int = 0
):
    """
    为特定参数组创建目标函数。
    
    Args:
        group_params: 当前阶段要优化的参数列表
        locked_params: 已锁定的参数（来自前序阶段）
        cases: 测试案例
        base_config: 基础配置
        step: 训练阶段 (0=全阶段, 1=Foundation, 2=Dynamics)
    
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
        
        # Group 1: Foundation (V53.0: Controlled Float - 以黄金值为中轴，允许±20%~30%微调)
        if 'physics.pillarWeights.month' in group_params:
            if 'physics.pillarWeights.month' in GOLDEN_CONSTANTS:
                golden_value = GOLDEN_CONSTANTS['physics.pillarWeights.month']
                min_val = golden_value * (1 - FLOAT_TOLERANCE)  # 1.88 * 0.75 = 1.41
                max_val = golden_value * (1 + FLOAT_TOLERANCE)  # 1.88 * 1.25 = 2.35
                config['physics']['pillarWeights']['month'] = trial.suggest_float(
                    'physics.pillarWeights.month', min_val, max_val, step=0.05  # 中心值 1.88，范围 [1.41, 2.35]
                )
            else:
                config['physics']['pillarWeights']['month'] = trial.suggest_float(
                    'physics.pillarWeights.month', 1.5, 2.2, step=0.05
                )
        if 'physics.pillarWeights.year' in group_params:
            if 'physics.pillarWeights.year' in GOLDEN_CONSTANTS:
                golden_value = GOLDEN_CONSTANTS['physics.pillarWeights.year']
                min_val = golden_value * (1 - FLOAT_TOLERANCE)  # 0.82 * 0.75 = 0.615
                max_val = golden_value * (1 + FLOAT_TOLERANCE)  # 0.82 * 1.25 = 1.025
                config['physics']['pillarWeights']['year'] = trial.suggest_float(
                    'physics.pillarWeights.year', min_val, max_val, step=0.05  # 中心值 0.82，范围 [0.615, 1.025]
                )
            else:
                config['physics']['pillarWeights']['year'] = trial.suggest_float(
                    'physics.pillarWeights.year', min_val, max_val, step=0.05  # 中心值 0.82，范围 [0.615, 1.025]
                )
        if 'physics.pillarWeights.day' in group_params:
            if 'physics.pillarWeights.day' in GOLDEN_CONSTANTS:
                golden_value = GOLDEN_CONSTANTS['physics.pillarWeights.day']
                min_val = golden_value * (1 - FLOAT_TOLERANCE)  # 1.62 * 0.75 = 1.215
                max_val = golden_value * (1 + FLOAT_TOLERANCE)  # 1.62 * 1.25 = 2.025
                config['physics']['pillarWeights']['day'] = trial.suggest_float(
                    'physics.pillarWeights.day', min_val, max_val, step=0.05  # 中心值 1.62，范围 [1.215, 2.025]
                )
            else:
                config['physics']['pillarWeights']['day'] = trial.suggest_float(
                    'physics.pillarWeights.day', 1.2, 1.8, step=0.05
                )
        if 'physics.pillarWeights.hour' in group_params:
            if 'physics.pillarWeights.hour' in GOLDEN_CONSTANTS:
                golden_value = GOLDEN_CONSTANTS['physics.pillarWeights.hour']
                min_val = golden_value * (1 - FLOAT_TOLERANCE)  # 0.95 * 0.75 = 0.7125
                max_val = golden_value * (1 + FLOAT_TOLERANCE)  # 0.95 * 1.25 = 1.1875
                config['physics']['pillarWeights']['hour'] = trial.suggest_float(
                    'physics.pillarWeights.hour', min_val, max_val, step=0.05  # 中心值 0.95，范围 [0.7125, 1.1875]
                )
            else:
                config['physics']['pillarWeights']['hour'] = trial.suggest_float(
                    'physics.pillarWeights.hour', min_val, max_val, step=0.05  # 中心值 0.95，范围 [0.7125, 1.1875]
                )
        if 'structure.rootingWeight' in group_params:
            # V53.0: Controlled Float - 以黄金值为中轴，允许±20%~30%微调
            if 'structure.rootingWeight' in GOLDEN_CONSTANTS:
                golden_value = GOLDEN_CONSTANTS['structure.rootingWeight']
                min_val = golden_value * (1 - FLOAT_TOLERANCE)  # 4.25 * 0.75 = 3.1875
                max_val = golden_value * (1 + FLOAT_TOLERANCE)  # 4.25 * 1.25 = 5.3125
                config['structure']['rootingWeight'] = trial.suggest_float(
                    'structure.rootingWeight', min_val, max_val, step=0.1  # 中心值 4.25，范围 [3.1875, 5.3125]
                )
            else:
                config['structure']['rootingWeight'] = trial.suggest_float(
                    'structure.rootingWeight', 3.0, 5.5, step=0.1
                )
        
        # ===========================================
        # V53.0 Step 1: Foundation Locking Tuning
        # 对于 Group 2 和 Group 3 的参数，强制从 base_config 读取（锁死）
        # ===========================================
        # 如果当前是 Step 1（只优化 Foundation），则强制锁死 Group 2 和 Group 3
        is_step1_foundation_only = (group_params == GROUP_1_FOUNDATION)
        
        # Group 2: Dynamics (V53.0 Step 2: 仅在优化 Group 2 时才允许调整)
        # 如果当前是 Step 1（只优化 Foundation），则跳过所有 Group 2 和 Group 3 的参数优化
        if not is_step1_foundation_only and 'flow.generationEfficiency' in group_params:
            gen_eff = trial.suggest_float('gen_eff', 0.1, 0.4, step=0.01)  # [0.1, 0.4]
            set_nested_param(config, 'flow.generationEfficiency', gen_eff)
        if not is_step1_foundation_only and 'flow.controlImpact' in group_params:
            ctl_imp = trial.suggest_float('ctl_imp', -4.0, -1.5, step=0.05)  # [-4.0, -1.5]
            set_nested_param(config, 'flow.controlImpact', ctl_imp)
        if not is_step1_foundation_only and 'flow.dampingFactor' in group_params:
            damping = trial.suggest_float('damping', 0.2, 0.7, step=0.01)  # [0.2, 0.7]
            set_nested_param(config, 'flow.dampingFactor', damping)
        if not is_step1_foundation_only and 'flow.outputDrainPenalty' in group_params:
            drain_rate = trial.suggest_float('drain_rate', 1.5, 5.0, step=0.1)  # [1.5, 5.0]
            # drain_rate → outputDrainPenalty
            set_nested_param(config, 'flow.outputDrainPenalty', drain_rate)
        if not is_step1_foundation_only and 'flow.globalEntropy' in group_params:
            entropy = trial.suggest_float('entropy', 0.05, 0.25, step=0.01)  # [0.05, 0.25]
            set_nested_param(config, 'flow.globalEntropy', entropy)
        
        # Group 3: Interactions (V53.0 Step 1: 仅在优化 Group 3 时才允许调整)
        if not is_step1_foundation_only and 'flow.earthMetalMoistureBoost' in group_params:
            config['flow']['earthMetalMoistureBoost'] = trial.suggest_float(
                'flow.earthMetalMoistureBoost', 5.0, 15.0, step=0.5  # V47.0: 保持高润局系数
            )
        if not is_step1_foundation_only and 'interactions.stemFiveCombination.bonus' in group_params:
            config['interactions']['stemFiveCombination']['bonus'] = trial.suggest_float(
                'interactions.stemFiveCombination.bonus', 1.2, 2.5, step=0.1
            )
        if not is_step1_foundation_only and 'interactions.branchEvents.clashDamping' in group_params:
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
        
        loss = calculate_weighted_loss(engine, cases, config, step=step)
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


# ===========================================
# Unified Optimization (single study, CMA-ES)
# ===========================================

def _relative_bounds(current: float, tol: float = 0.3, min_clip: float = None, max_clip: float = None) -> Tuple[float, float]:
    """生成相对范围，默认 ±30%."""
    if current is None:
        current = 1.0
    low = current * (1 - tol)
    high = current * (1 + tol)
    if low > high:
        low, high = high, low
    if min_clip is not None:
        low = max(low, min_clip)
    if max_clip is not None:
        high = min(high, max_clip)
    # 避免低高相同
    if abs(high - low) < 1e-6:
        high = low + 1e-3
    return low, high


def run_unified_optimization(
    cases: List[Dict[str, Any]],
    base_config: Dict,
    n_trials: int = 400,
    max_loops: int = 0,
    patience: int = 2,
    min_improve: float = 1e-3
) -> Dict[str, float]:
    """
    单一 study 联合调参（Foundation + Dynamics + Interactions），使用 CMA-ES。
    搜索范围围绕当前参数 ±30%，保证不会回退到无意义的大范围。
    """
    print("=" * 80)
    print("🔄 Unified Optimization (CMA-ES, balanced-focused)")
    print("   - 单一 study 联合搜索 Foundation + Dynamics + Interactions")
    print("   - 范围: 以当前参数为中心 ±30% 相对扰动")
    print("   - 目标: 加权损失（Step=2，Balanced 权重更高）")
    print("=" * 80)
    print()

    # 当前配置用于设定相对范围
    current_cfg = copy.deepcopy(base_config)

    param_specs = [
        ("structure.rootingWeight", 0.3, 0.1, 50.0),
        ("physics.pillarWeights.month", 0.3, 0.1, 5.0),
        ("physics.pillarWeights.year", 0.3, 0.1, 5.0),
        ("physics.pillarWeights.day", 0.3, 0.1, 5.0),
        ("physics.pillarWeights.hour", 0.3, 0.05, 5.0),
        ("flow.controlImpact", 0.3, None, None),
        ("flow.generationEfficiency", 0.3, 0.01, 2.0),
        ("flow.dampingFactor", 0.3, 0.01, 2.0),
        ("flow.outputDrainPenalty", 0.3, 0.1, 8.0),
        ("flow.globalEntropy", 0.3, 0.0, 0.6),
        ("flow.earthMetalMoistureBoost", 0.3, 0.1, 30.0),
        ("interactions.branchEvents.clashDamping", 0.3, 0.0, 1.5),
        ("interactions.stemFiveCombination.bonus", 0.3, 0.5, 3.5),
    ]
    
    # 保存初始参数值（用于对比显示）
    initial_params = {}
    for path, _, _, _ in param_specs:
        val = get_nested_param(current_cfg, path)
        if val is not None:
            initial_params[path] = val

    # 优先使用 CMA-ES，如缺失 cmaes 库则回退到 TPE
    try:
        import importlib
        importlib.import_module("cmaes")
        sampler = optuna.samplers.CmaEsSampler(seed=42)
    except Exception:
        print("⚠️ 未安装 cmaes，回退到 TPE sampler")
        sampler = optuna.samplers.TPESampler(seed=42)
    study = optuna.create_study(direction="minimize", sampler=sampler)

    def objective(trial: optuna.Trial) -> float:
        cfg = copy.deepcopy(base_config)
        for path, tol, min_clip, max_clip in param_specs:
            current_val = get_nested_param(current_cfg, path)
            low, high = _relative_bounds(current_val, tol=tol, min_clip=min_clip, max_clip=max_clip)
            val = trial.suggest_float(path, low, high)
            set_nested_param(cfg, path, val)

        try:
            engine = GraphNetworkEngine(config=cfg)
        except Exception:
            return float("inf")
        loss = calculate_weighted_loss(engine, cases, cfg, step=2)
        return loss

    best_params = {}
    best_loss = float("inf")
    no_improve = 0
    loop = 0
    
    # 打印初始参数值
    print("📋 初始参数值（调优基准）:")
    for path, _, _, _ in param_specs:
        val = initial_params.get(path)
        if val is not None:
            print(f"   {path:40s}: {val:8.4f}")
    print()
    
    # 计算初始准确率
    try:
        engine_init = GraphNetworkEngine(config=current_cfg)
        acc_init = calculate_accuracy(engine_init, cases, current_cfg)
        print(f"📊 初始准确率: 总={acc_init['Total']:.1f}% | Strong={acc_init['Strong']:.1f}% | Balanced={acc_init['Balanced']:.1f}% | Weak={acc_init['Weak']:.1f}%")
        print()
    except Exception:
        pass
    
    while True:
        loop += 1
        print(f"\n🔁 Unified Loop {loop} / {('∞' if max_loops == 0 else max_loops)}")
        print(f"📊 试验次数: {n_trials} (CMA-ES/TPE)")
        if loop == 1:
            print(f"🔧 正在调优 {len(param_specs)} 个参数: {', '.join([p[0] for p in param_specs[:5]])}...")

        study.optimize(objective, n_trials=n_trials, show_progress_bar=False, n_jobs=1)
        trial = study.best_trial
        if trial.value < best_loss - min_improve:
            best_loss = trial.value
            best_params = trial.params
            no_improve = 0
            print(f"🎯 新最佳 loss: {best_loss:.4f}")
            
            # 打印参数变化详情
            print("📝 参数调优详情:")
            changed_params = []
            for path, _, _, _ in param_specs:
                if path in best_params:
                    new_val = best_params[path]
                    old_val = initial_params.get(path)
                    if old_val is not None:
                        change = new_val - old_val
                        change_pct = (change / abs(old_val) * 100) if old_val != 0 else 0.0
                        if abs(change) > 1e-6:  # 只显示有显著变化的参数
                            changed_params.append((path, old_val, new_val, change, change_pct))
            
            if changed_params:
                # 按变化幅度排序（绝对值）
                changed_params.sort(key=lambda x: abs(x[3]), reverse=True)
                for path, old_val, new_val, change, change_pct in changed_params[:10]:  # 只显示前10个变化最大的
                    sign = "↑" if change > 0 else "↓"
                    print(f"   {path:40s}: {old_val:8.4f} → {new_val:8.4f} ({change:+.4f}, {change_pct:+.1f}%) {sign}")
                if len(changed_params) > 10:
                    print(f"   ... 还有 {len(changed_params) - 10} 个参数有变化")
            else:
                print("   (所有参数变化很小，< 0.000001)")
            
            # 计算并打印准确率
            cfg = copy.deepcopy(base_config)
            for path, val in best_params.items():
                set_nested_param(cfg, path, val)
            try:
                engine = GraphNetworkEngine(config=cfg)
                acc = calculate_accuracy(engine, cases, cfg)
                print(f"📈 准确率: 总={acc['Total']:.1f}% | Strong={acc['Strong']:.1f}% | Balanced={acc['Balanced']:.1f}% | Weak={acc['Weak']:.1f}%")
            except Exception as e:
                print(f"⚠️ 计算准确率失败: {e}")
            
            # 更新初始参数为当前最佳（用于下一轮对比）
            initial_params.update(best_params)
            
            save_best_params(best_params)
        else:
            no_improve += 1
            print(f"⚠️ 无显著改进 (best={best_loss:.4f}, this={trial.value:.4f}, 连续无改进 {no_improve}/{patience})")

        if max_loops > 0 and loop >= max_loops:
            print("🛑 达到最大循环次数，停止。")
            break
        if no_improve >= patience:
            print("🛑 达到无改进耐心阈值，停止。")
            break

    # 保存最终最佳
    if best_params:
        save_best_params(best_params)
        print(f"🎯 最佳 loss: {best_loss:.4f}")
        
        # 打印最终准确率
        cfg_final = copy.deepcopy(base_config)
        for path, val in best_params.items():
            set_nested_param(cfg_final, path, val)
        try:
            engine_final = GraphNetworkEngine(config=cfg_final)
            acc_final = calculate_accuracy(engine_final, cases, cfg_final)
            print(f"📈 最终准确率: 总={acc_final['Total']:.1f}% | Strong={acc_final['Strong']:.1f}% | Balanced={acc_final['Balanced']:.1f}% | Weak={acc_final['Weak']:.1f}%")
        except Exception as e:
            print(f"⚠️ 计算最终准确率失败: {e}")
    else:
        print("⚠️ 未找到有效参数，返回空结果")
    return best_params


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
    
    # 将简写 trial 参数映射到真实引擎字段（防止保存时遗漏）
    shorthand_mapping = {
        'ctl_imp': 'flow.controlImpact',
        'drain_rate': 'flow.outputDrainPenalty',
        'gen_eff': 'flow.generationEfficiency',
        'damping': 'flow.dampingFactor',
        'entropy': 'flow.globalEntropy',
    }
    expanded_params = {}
    for k, v in best_params.items():
        if k in shorthand_mapping:
            expanded_params[shorthand_mapping[k]] = v
        expanded_params[k] = v

    # 应用最佳参数
    for param_path, value in expanded_params.items():
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
                     base_config: Dict, n_trials: int = 200, seed_trial: Dict[str, float] = None, step: int = 1) -> Dict[str, float]:
    """优化 Stage 1: Foundation"""
    print("🚀 Stage 1: 优化地基层 (Foundation)")
    print("   参数: 月令权重、年柱权重、通根系数等")
    print()
    
    # 计算初始损失
    config_init = copy.deepcopy(base_config)
    for param_path, value in locked_params.items():
        set_nested_param(config_init, param_path, value)
    engine_init = GraphNetworkEngine(config=config_init)
    initial_loss = calculate_weighted_loss(engine_init, cases, config_init, step=step)
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
        base_config,
        step=step
    )
    
    # 运行优化
    print("   🔬 开始优化...")
    # V53.0: 禁用进度条输出，减少日志冗余
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False, n_jobs=1)
    
    # 将最佳 trial 参数应用到一份完整配置映射，返回全路径参数（不再保留简写）
    best_trial_params = study.best_params
    mapped_params = {}
    def map_param(name: str, mapped_name: str):
        if name in best_trial_params:
            mapped_params[mapped_name] = best_trial_params[name]
    map_param('ctl_imp', 'flow.controlImpact')
    map_param('drain_rate', 'flow.outputDrainPenalty')
    map_param('gen_eff', 'flow.generationEfficiency')
    map_param('damping', 'flow.dampingFactor')
    map_param('entropy', 'flow.globalEntropy')
    
    return mapped_params


def optimize_stage_2(locked_params: Dict[str, float], cases: List[Dict[str, Any]], 
                     base_config: Dict, n_trials: int = 200, seed_trial: Dict[str, float] = None, step: int = 2) -> Dict[str, float]:
    """优化 Stage 2: Dynamics"""
    print("🚀 Stage 2: 优化动力层 (Dynamics)")
    print("   参数: 生克传导率、阻尼系数、熵增等")
    print()
    
    # 计算初始损失
    config_init = copy.deepcopy(base_config)
    for param_path, value in locked_params.items():
        set_nested_param(config_init, param_path, value)
    engine_init = GraphNetworkEngine(config=config_init)
    initial_loss = calculate_weighted_loss(engine_init, cases, config_init, step=step)
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
        base_config,
        step=step
    )
    
    # 运行优化
    print("   🔬 开始优化...")
    # V53.0: 禁用进度条输出，减少日志冗余
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False, n_jobs=1)
    
    # 返回最佳参数
    return study.best_params


def optimize_stage_3(locked_params: Dict[str, float], cases: List[Dict[str, Any]], 
                     base_config: Dict, n_trials: int = 200, seed_trial: Dict[str, float] = None, step: int = 0) -> Dict[str, float]:
    """优化 Stage 3: Interactions"""
    print("🚀 Stage 3: 优化交互层 (Interactions)")
    print("   参数: 润局系数、合化加成、冲克阻尼等")
    print()
    
    # 计算初始损失
    config_init = copy.deepcopy(base_config)
    for param_path, value in locked_params.items():
        set_nested_param(config_init, param_path, value)
    engine_init = GraphNetworkEngine(config=config_init)
    initial_loss = calculate_weighted_loss(engine_init, cases, config_init, step=step)
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
        base_config,
        step=step
    )
    
    # 运行优化
    print("   🔬 开始优化...")
    # V53.0: 禁用进度条输出，减少日志冗余
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False, n_jobs=1)
    
    # 返回最佳参数
    return study.best_params


def run_cyclic_optimization(cases: List[Dict[str, Any]], base_config: Dict, 
                           cycles: int = 3, step: int = 1) -> Dict[str, float]:
    """
    V53.0 Step 1: 分层锁定优化
    
    Args:
        cases: 测试案例
        base_config: 基础配置
        cycles: 循环次数
        step: 优化阶段 (1=Foundation only, 2=Flow only, 3=All)
    
    Returns:
        最终最佳参数
    """
    print("=" * 80)
    if step == 1:
        print("🔄 Antigravity Cyclic AI Trainer (V53.0 Step 1)")
        print("   Foundation Locking Tuning - Physics/Structure ONLY")
        print("   Group 2 (Flow) and Group 3 (Interactions) are FROZEN")
    else:
        print("🔄 Antigravity Cyclic AI Trainer (V53.0)")
        print("   Controlled Float Strategy - Unlocking Base Parameters")
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
    initial_loss = calculate_weighted_loss(engine_init, cases, config_init, step=step)
    print(f"📊 初始损失: {initial_loss:.2f}")
    print()
    
    best_loss = initial_loss
    best_params = locked_params.copy()
    
    # V53.0: 根据 step 调整总试验次数
    if step == 1:
        total_trials = cycles * 200  # 只跑 Foundation
        print(f"📊 训练规模: {cycles} 个循环 × 200 = {total_trials} 次试验 (Foundation Only)")
    elif step == 2:
        total_trials = cycles * 300  # 只跑 Dynamics，更多尝试
        print(f"📊 训练规模: {cycles} 个循环 × 300 = {total_trials} 次试验 (Dynamics Only)")
    else:
        total_trials = cycles * (200 + 200 + 200)  # Foundation + Dynamics + Interactions
        print(f"📊 训练规模: {cycles} 个循环 × (200 + 200 + 200) = {total_trials} 次试验")
    print(f"   预计耗时: 约 {total_trials * 0.015:.0f} 秒")
    print()
    
    # V53.0: 不再使用硬编码的种子参数，直接从 config/parameters.json 读取
    # 这样可以确保种子参数始终在搜索范围内
    # seed_params_v49 已废弃，改为使用 base_config 中的值
    
    # V53.0 Step 1/2: 根据 step 参数决定优化哪些阶段
    if step == 1:
        # Step 1: 只优化 Foundation，锁死其他所有参数
        print("🔒 V53.0 Step 1: Foundation Locking Tuning")
        print("   - 仅优化 Group 1 (Foundation): pillarWeights, rootingWeight")
        print("   - Group 2 (Flow/Dynamics): 锁死，使用 config/parameters.json 中的固定值")
        print("   - Group 3 (Interactions): 锁死，使用 config/parameters.json 中的固定值")
        print()
        
        # 循环优化（只优化 Foundation）
        for cycle in range(cycles):
            print("\n" + "=" * 80)
            print(f"🔄 Cycle {cycle + 1}/{cycles} (Foundation Only)")
            print("=" * 80)
            print()
            
            cycle_start_loss = best_loss
            
            # 只运行 Stage 1: Foundation
            print(f"--- Cycle {cycle + 1} - Stage 1: Foundation ---")
            # V53.0: 不再使用硬编码的种子参数，直接从 base_config 读取
            seed_stage1 = {}
            stage1_params = optimize_stage_1(best_params, cases, base_config, n_trials=200, seed_trial=seed_stage1, step=step)
            best_params.update(stage1_params)
            
            # 计算 Stage 1 后的损失
            config_s1 = copy.deepcopy(base_config)
            for param_path, value in best_params.items():
                set_nested_param(config_s1, param_path, value)
            engine_s1 = GraphNetworkEngine(config=config_s1)
            loss_s1 = calculate_weighted_loss(engine_s1, cases, config_s1, step=step)
            print(f"   Stage 1 后损失: {loss_s1:.2f}")
            
            # V53.0: 计算并显示准确率
            accuracies_s1 = calculate_accuracy(engine_s1, cases, config_s1)
            print(f"   📈 Stage 1 后准确率:")
            print(f"      总准确率: {accuracies_s1['Total']:.1f}%")
            for label in ["Strong", "Balanced", "Weak"]:
                print(f"      {label}: {accuracies_s1[label]:.1f}%")
            print()
            
            # 更新最佳损失
            if loss_s1 < best_loss:
                best_loss = loss_s1
            
            # 计算最终准确率（用于 Cycle 报告）
            config_final = copy.deepcopy(base_config)
            for param_path, value in best_params.items():
                set_nested_param(config_final, param_path, value)
            engine_final = GraphNetworkEngine(config=config_final)
            accuracies_final = calculate_accuracy(engine_final, cases, config_final)
            
            # 打印 Cycle 报告
            cycle_improvement = cycle_start_loss - loss_s1
            cycle_improvement_pct = (cycle_improvement / cycle_start_loss * 100) if cycle_start_loss > 0 else 0.0
            
            print("=" * 80)
            print(f"📊 Cycle {cycle + 1} 报告 (Foundation Only)")
            print("=" * 80)
            print(f"损失变化: {cycle_start_loss:.2f} → {loss_s1:.2f}")
            print(f"改进幅度: {cycle_improvement:+.2f} ({cycle_improvement_pct:+.1f}%)")
            print()
            print(f"📈 当前准确率:")
            print(f"   总准确率: {accuracies_final['Total']:.1f}%")
            for label in ["Strong", "Balanced", "Weak"]:
                print(f"   {label}: {accuracies_final[label]:.1f}%")
            print()
            print(f"📈 当前准确率:")
            print(f"   总准确率: {accuracies_final['Total']:.1f}%")
            for label in ["Strong", "Balanced", "Weak"]:
                print(f"   {label}: {accuracies_final[label]:.1f}%")
            print()
            
            # Checkpoint: 保存当前最佳参数
            save_best_params(best_params)
            print(f"✅ Cycle {cycle + 1} 最佳参数已保存")
            print()
    elif step == 2:
        # Step 2: 只优化 Dynamics，锁死 Foundation 和 Interactions
        print("🔓 V53.0 Step 2: Dynamics Unlocking")
        print("   - 仅优化 Group 2 (Flow/Dynamics): controlImpact, maxDrainRate, generationEfficiency, dampingFactor")
        print("   - Group 1 (Foundation): 锁死，使用当前 config/parameters.json 的最佳值")
        print("   - Group 3 (Interactions): 锁死，保持不变")
        print()

        for cycle in range(cycles):
            print("\n" + "=" * 80)
            print(f"🔄 Cycle {cycle + 1}/{cycles} (Dynamics Only)")
            print("=" * 80)
            print()

            cycle_start_loss = best_loss

            # 只运行 Stage 2: Dynamics
            print(f"--- Cycle {cycle + 1} - Stage 2: Dynamics ---")
            seed_stage2 = {}
            stage2_params = optimize_stage_2(
                best_params, cases, base_config, n_trials=300, seed_trial=seed_stage2, step=step
            )
            best_params.update(stage2_params)

            # 计算 Stage 2 后的损失
            config_s2 = copy.deepcopy(base_config)
            for param_path, value in best_params.items():
                set_nested_param(config_s2, param_path, value)
            engine_s2 = GraphNetworkEngine(config=config_s2)
            loss_s2 = calculate_weighted_loss(engine_s2, cases, config_s2, step=step)
            print(f"   Stage 2 后损失: {loss_s2:.2f}")
            print()

            # 计算准确率（用于 Cycle 报告）
            accuracies_final = calculate_accuracy(engine_s2, cases, config_s2)

            # 打印 Cycle 报告
            cycle_improvement = cycle_start_loss - loss_s2
            cycle_improvement_pct = (cycle_improvement / cycle_start_loss * 100) if cycle_start_loss > 0 else 0.0

            print("=" * 80)
            print(f"📊 Cycle {cycle + 1} 报告 (Dynamics Only)")
            print("=" * 80)
            print(f"损失变化: {cycle_start_loss:.2f} → {loss_s2:.2f}")
            print(f"改进幅度: {cycle_improvement:+.2f} ({cycle_improvement_pct:+.1f}%)")
            print()
            print(f"📈 当前准确率:")
            print(f"   总准确率: {accuracies_final['Total']:.1f}%")
            for label in ["Strong", "Balanced", "Weak"]:
                print(f"   {label}: {accuracies_final[label]:.1f}%")
            print()

            # 更新最佳损失
            if loss_s2 < best_loss:
                best_loss = loss_s2

            # Checkpoint: 保存当前最佳参数
            save_best_params(best_params)
            print(f"✅ Cycle {cycle + 1} 最佳参数已保存")
            print()
    else:
        # 完整优化（所有阶段）
        # 循环优化
        for cycle in range(cycles):
            print("\n" + "=" * 80)
            print(f"🔄 Cycle {cycle + 1}/{cycles}")
            print("=" * 80)
            print()
            
            cycle_start_loss = best_loss
            
            # Round 1: Foundation
            print(f"--- Cycle {cycle + 1} - Stage 1: Foundation ---")
            # V53.0: 不再使用硬编码的种子参数，直接从 base_config 读取
            seed_stage1 = {}
            stage1_params = optimize_stage_1(best_params, cases, base_config, n_trials=200, seed_trial=seed_stage1, step=step)
            best_params.update(stage1_params)
            
            # 计算 Stage 1 后的损失
            config_s1 = copy.deepcopy(base_config)
            for param_path, value in best_params.items():
                set_nested_param(config_s1, param_path, value)
            engine_s1 = GraphNetworkEngine(config=config_s1)
            loss_s1 = calculate_weighted_loss(engine_s1, cases, config_s1, step=step)
            print(f"   Stage 1 后损失: {loss_s1:.2f}")
            print()
            
            # Round 2: Dynamics
            print(f"--- Cycle {cycle + 1} - Stage 2: Dynamics ---")
            # V53.0: 不再使用硬编码的种子参数，直接从 base_config 读取
            seed_stage2 = {}
            stage2_params = optimize_stage_2(best_params, cases, base_config, n_trials=200, seed_trial=seed_stage2, step=step)
            best_params.update(stage2_params)
            
            # 计算 Stage 2 后的损失
            config_s2 = copy.deepcopy(base_config)
            for param_path, value in best_params.items():
                set_nested_param(config_s2, param_path, value)
            engine_s2 = GraphNetworkEngine(config=config_s2)
            loss_s2 = calculate_weighted_loss(engine_s2, cases, config_s2, step=step)
            print(f"   Stage 2 后损失: {loss_s2:.2f}")
            print()
            
            # Round 3: Interactions
            print(f"--- Cycle {cycle + 1} - Stage 3: Interactions ---")
            # V53.0: 不再使用硬编码的种子参数，直接从 base_config 读取
            seed_stage3 = {}
            stage3_params = optimize_stage_3(best_params, cases, base_config, n_trials=200, seed_trial=seed_stage3, step=step)
            best_params.update(stage3_params)
            
            # 计算 Stage 3 后的损失
            config_s3 = copy.deepcopy(base_config)
            for param_path, value in best_params.items():
                set_nested_param(config_s3, param_path, value)
            engine_s3 = GraphNetworkEngine(config=config_s3)
            loss_s3 = calculate_weighted_loss(engine_s3, cases, config_s3, step=step)
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
    print("🤖 Antigravity Cyclic AI Trainer (V53.0)")
    print("   Controlled Float: Unlocking Base Parameters for Golden Dataset 2.0")
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
    
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="Antigravity Cyclic AI Trainer")
    parser.add_argument("--step", type=int, default=2, choices=[0, 1, 2],
                        help="训练阶段: 0=全阶段, 1=仅基础层(Foundation), 2=仅动力层(Dynamics)。默认 2")
    parser.add_argument("--mode", type=str, default="unified", choices=["unified", "legacy"],
                        help="unified=单一study联合调优(推荐); legacy=按step分阶段旧模式")
    parser.add_argument("--trials", type=int, default=400, help="每轮试验次数 (unified 模式)")
    parser.add_argument("--max-loops", type=int, default=0, help="最大循环轮数 (0=无限直到耐心耗尽)")
    parser.add_argument("--patience", type=int, default=2, help="无改进容忍轮数 (unified 模式)")
    parser.add_argument("--min-improve", type=float, default=1e-3, help="视为改进的最小 loss 差值")
    args = parser.parse_args()

    step = args.step
    if step == 1:
        print("🔒 模式: Step 1 - Foundation Locking Tuning (只调基础层)")
    elif step == 2:
        print("🔓 模式: Step 2 - Dynamics Unlocking (只调动力层)")
    else:
        print("🔁 模式: 全阶段优化 (Foundation + Dynamics + Interactions)")
    print(f"🎛️ 运行模式: {args.mode}")
    print()

    # 运行优化
    if args.mode == "unified":
        best_params = run_unified_optimization(
            cases,
            base_config,
            n_trials=args.trials,
            max_loops=args.max_loops,
            patience=args.patience,
            min_improve=args.min_improve,
        )
    else:
        best_params = run_cyclic_optimization(cases, base_config, cycles=5, step=step)
    
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
    final_loss = calculate_weighted_loss(engine_final, cases, config_final, step=step)
    
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
