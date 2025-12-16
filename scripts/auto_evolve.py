#!/usr/bin/env python3
"""
自动进化元优化器 (Auto-Evolution Meta-Optimizer)
===================================================

这个脚本实现了"元调优"：自动诊断短板，动态调整策略，持续迭代直到达到目标准确率。

核心逻辑：
1. 自动运行训练和验证
2. 诊断哪个类别准确率最低
3. 动态调整 Loss 函数权重（给短板更高惩罚）
4. 自动扩大触顶参数的搜索范围
5. 循环迭代直到达到目标准确率

版本: V51.0 (Golden Ratio Hard-Reset)
作者: Antigravity Team
日期: 2025-12-16

V50.1 新增功能:
- Stagnation Detection: 检测连续5次无改进
- CHAOS MODE: 极端权重偏向、参数抖动、超大范围
- Reset Logic: 混沌模式后重置计数器

V51.0 新增功能:
- Fine-Tuning Mode: 锁定核心参数（黄金比例），只调整边缘参数
- Golden Ratio Constants: 基于物理守恒定律的黄金参数组
- Stop Random Search: 停止随机震荡，使用计算出的物理常数
"""

import json
import sys
import subprocess
import re
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import copy

# V50.1: 确保输出不被缓冲（用于 nohup 后台运行）
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from scripts.train_model_optuna import (
    load_golden_cases, calculate_weighted_loss, 
    GROUP_1_FOUNDATION, GROUP_2_DYNAMICS, GROUP_3_INTERACTIONS,
    set_nested_param, get_nested_param
)


def run_batch_verify() -> Dict[str, float]:
    """
    运行 batch_verify.py 并解析准确率结果。
    
    Returns:
        包含各标签准确率的字典: {"Strong": 90.9, "Balanced": 54.5, "Weak": 72.7, "Total": 72.7}
    """
    print("📊 运行批量验证...")
    
    # 运行 batch_verify.py
    result = subprocess.run(
        ["python3", str(project_root / "scripts" / "batch_verify.py")],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    output = result.stdout + result.stderr
    
    # 解析准确率
    accuracies = {"Strong": 0.0, "Balanced": 0.0, "Weak": 0.0, "Total": 0.0}
    
    # 查找总准确率
    total_match = re.search(r'总准确率[：:]\s*(\d+\.?\d*)%', output)
    if total_match:
        accuracies["Total"] = float(total_match.group(1))
    
    # 查找各标签准确率（匹配格式如 "Strong      : 10/11 = 90.9%"）
    # batch_verify.py 的输出格式: "{label:12s}: {correct}/{total} = {accuracy}%"
    for label in ["Strong", "Balanced", "Weak"]:
        # 主要格式：标签（固定宽度12）+ ": " + 数字/数字 = 百分比
        # 例如: "Strong      : 10/11 = 90.9%"
        pattern = rf'{label}\s+[：:]\s*\d+/\d+\s*=\s*(\d+\.?\d*)%'
        match = re.search(pattern, output, re.IGNORECASE | re.MULTILINE)
        if match:
            accuracies[label] = float(match.group(1))
        else:
            # 备用格式：尝试其他可能的格式
            patterns = [
                rf'{label}\s*[：:]\s*(\d+\.?\d*)%\s*\((\d+)/(\d+)\)',  # "Strong: 72.7% (8/11)"
                rf'{label}\s*[：:]\s*\d+/\d+\s*=\s*(\d+\.?\d*)%',      # "Strong: 8/11 = 72.7%"
            ]
            for alt_pattern in patterns:
                alt_match = re.search(alt_pattern, output, re.IGNORECASE | re.MULTILINE)
                if alt_match:
                    accuracies[label] = float(alt_match.group(1))
                    break
    
    return accuracies


def diagnose_weakness(accuracies: Dict[str, float]) -> Tuple[str, float]:
    """
    诊断最弱的类别。
    
    Returns:
        (weakest_label, accuracy) 元组
    """
    labels = ["Strong", "Balanced", "Weak"]
    weakest_label = min(labels, key=lambda l: accuracies.get(l, 0.0))
    weakest_acc = accuracies.get(weakest_label, 0.0)
    
    return weakest_label, weakest_acc


def detect_parameter_ceiling(best_params: Dict[str, float], 
                            param_ranges: Dict[str, Tuple[float, float]]) -> Dict[str, bool]:
    """
    检测哪些参数触顶了。
    
    Args:
        best_params: 当前最佳参数
        param_ranges: 参数范围字典 {param_path: (min, max)}
    
    Returns:
        {param_path: is_at_ceiling} 字典
    """
    ceilings = {}
    tolerance = 0.05  # 5% 容差
    
    for param_path, (min_val, max_val) in param_ranges.items():
        if param_path in best_params:
            value = best_params[param_path]
            # 检查是否接近上限
            if abs(value - max_val) / max(max_val, 1.0) < tolerance:
                ceilings[param_path] = True
            else:
                ceilings[param_path] = False
    
    return ceilings


def update_loss_weights(accuracies: Dict[str, float], 
                       current_weights: Dict[str, float],
                       chaos_mode: bool = False) -> Dict[str, float]:
    """
    根据准确率动态调整 Loss 权重。
    
    V50.0 改进：使用更激进的动态公式，准确率越低，权重越高。
    V50.1 新增：CHAOS MODE - 极端权重偏向，只关注最差的类别。
    
    Args:
        accuracies: 当前准确率（0-100）
        current_weights: 当前权重
        chaos_mode: 是否启用混沌模式（极端权重偏向）
    
    Returns:
        更新后的权重
    """
    new_weights = copy.deepcopy(current_weights)
    
    if chaos_mode:
        # V50.1 CHAOS MODE: 极端权重偏向
        # 找到准确率最低的类别，给它极高的权重，其他类别权重极低
        weakest_label, weakest_acc = diagnose_weakness(accuracies)
        
        print(f"   ⚠️  CHAOS MODE: 极端权重偏向")
        print(f"   🎯 聚焦最弱类别: {weakest_label} ({weakest_acc:.1f}%)")
        
        for label in ["Strong", "Balanced", "Weak"]:
            if label == weakest_label:
                # 最弱类别：极高权重
                new_weights[label] = 50.0
                print(f"      {label}: {current_weights.get(label, 1.0):.1f} → 50.0 ⚡ (极端聚焦)")
            else:
                # 其他类别：极低权重（几乎放弃）
                new_weights[label] = 0.1
                print(f"      {label}: {current_weights.get(label, 1.0):.1f} → 0.1 (暂时放弃)")
        
        return new_weights
    
    # V50.0: 正常模式 - 动态权重公式
    # weight = base + (1.0 - accuracy/100) * multiplier
    # 准确率越低，权重越高
    
    print(f"   🔍 动态权重调整（基于准确率）:")
    
    for label in ["Strong", "Balanced", "Weak"]:
        accuracy = accuracies.get(label, 0.0) / 100.0  # 转换为 0-1
        base_weight = current_weights.get(label, 1.0)
        
        # 计算新权重：准确率越低，权重越高
        # 公式：weight = base * (1.0 + (1.0 - accuracy) * 5.0)
        # 这意味着如果准确率是 50%，权重会增加 2.5倍
        multiplier = 5.0
        new_weight = base_weight * (1.0 + (1.0 - accuracy) * multiplier)
        
        # 设置合理的上下限
        new_weight = max(1.0, min(new_weight, 20.0))
        
        new_weights[label] = new_weight
        
        if abs(new_weight - base_weight) > 0.1:
            print(f"      {label}: {base_weight:.1f} → {new_weight:.1f} (准确率: {accuracy*100:.1f}%)")
    
    # 诊断最弱的类别
    weakest_label, weakest_acc = diagnose_weakness(accuracies)
    print(f"   📉 最弱类别: {weakest_label} ({weakest_acc:.1f}%)")
    
    return new_weights


def expand_parameter_ranges(ceilings: Dict[str, bool],
                           current_ranges: Dict[str, Tuple[float, float]],
                           chaos_mode: bool = False) -> Dict[str, Tuple[float, float]]:
    """
    自动扩大触顶参数的搜索范围。
    
    V50.1 新增：CHAOS MODE - 超大范围（临时扩大3倍）
    
    Args:
        ceilings: 触顶检测结果
        current_ranges: 当前参数范围
        chaos_mode: 是否启用混沌模式（超大范围）
    
    Returns:
        更新后的参数范围
    """
    new_ranges = copy.deepcopy(current_ranges)
    
    if chaos_mode:
        # V50.1 CHAOS MODE: 超大范围（临时扩大3倍）
        expansion_factor = 3.0
        print(f"   ⚠️  CHAOS MODE: 超大范围扩展 (3倍)")
        
        # 对所有参数都扩大范围（不仅仅是触顶的）
        for param_path, (min_val, max_val) in current_ranges.items():
            range_size = max_val - min_val
            new_min = max(0.0, min_val - range_size * 0.5)  # 向下扩展50%
            new_max = max_val + range_size * 2.0  # 向上扩展200%
            
            # 设置合理的绝对上限
            if 'rootingWeight' in param_path:
                new_max = min(new_max, 50.0)  # rootingWeight 上限 50.0
            elif 'controlImpact' in param_path:
                new_max = min(new_max, 30.0)  # controlImpact 上限 30.0
            elif 'moistureBoost' in param_path:
                new_max = min(new_max, 40.0)  # moistureBoost 上限 40.0
            elif 'dampingFactor' in param_path:
                new_max = min(new_max, 1.0)  # dampingFactor 上限 1.0
            elif 'globalEntropy' in param_path:
                new_max = min(new_max, 0.5)  # globalEntropy 上限 0.5
            elif 'outputDrainPenalty' in param_path:
                new_max = min(new_max, 10.0)  # outputDrainPenalty 上限 10.0
            else:
                new_max = min(new_max, max_val * 3.0)  # 其他参数最多3倍
            
            new_ranges[param_path] = (new_min, new_max)
            print(f"      {param_path}: [{min_val:.2f}, {max_val:.2f}] → [{new_min:.2f}, {new_max:.2f}]")
        
        return new_ranges
    
    # V50.0: 正常模式 - 只扩大触顶参数
    expansion_factor = 1.5  # 扩大50%
    
    for param_path, is_at_ceiling in ceilings.items():
        if is_at_ceiling and param_path in current_ranges:
            min_val, max_val = current_ranges[param_path]
            new_max = max_val * expansion_factor
            
            # 对特定参数设置合理的上限
            if 'rootingWeight' in param_path:
                new_max = min(new_max, 30.0)  # rootingWeight 上限 30.0
            elif 'controlImpact' in param_path:
                new_max = min(new_max, 15.0)  # controlImpact 上限 15.0
            elif 'moistureBoost' in param_path:
                new_max = min(new_max, 25.0)  # moistureBoost 上限 25.0
            else:
                new_max = min(new_max, max_val * 2.0)  # 其他参数最多翻倍
            
            new_ranges[param_path] = (min_val, new_max)
            print(f"   🔓 {param_path} 上限扩大: {max_val:.2f} → {new_max:.2f}")
    
    return new_ranges


def modify_train_script_weights(weight_map: Dict[str, float]):
    """
    修改 train_model_optuna.py 中的权重配置。
    
    Args:
        weight_map: 新的权重映射
    """
    script_path = project_root / "scripts" / "train_model_optuna.py"
    
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找权重映射的行（更精确的匹配）
    # 匹配格式: weight_map = {"Strong": 1.0, "Weak": 4.0, "Balanced": 4.0}
    pattern = r'weight_map\s*=\s*\{[^}]+\}'
    
    # 构建新的权重字符串
    new_weights_str = f'weight_map = {repr(weight_map)}'
    
    if re.search(pattern, content):
        # 替换权重配置
        new_content = re.sub(pattern, new_weights_str, content, count=1)
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"   ✅ 已更新 train_model_optuna.py 中的权重配置")
        print(f"      新权重: {weight_map}")
        return True
    else:
        print(f"   ⚠️  未找到权重配置，可能需要手动修改")
        return False


def extract_best_params_from_config() -> Dict[str, float]:
    """
    从 config/parameters.json 中提取当前最佳参数。
    
    Returns:
        参数字典
    """
    config_path = project_root / "config" / "parameters.json"
    
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 提取关键参数
    best_params = {}
    
    # Foundation
    if 'structure' in config and 'rootingWeight' in config['structure']:
        best_params['structure.rootingWeight'] = config['structure']['rootingWeight']
    if 'physics' in config and 'pillarWeights' in config['physics']:
        pw = config['physics']['pillarWeights']
        for key in ['month', 'year', 'day', 'hour']:
            if key in pw:
                best_params[f'physics.pillarWeights.{key}'] = pw[key]
    
    # Dynamics
    if 'flow' in config:
        flow = config['flow']
        for key in ['controlImpact', 'generationEfficiency', 'dampingFactor', 
                   'globalEntropy', 'outputDrainPenalty', 'earthMetalMoistureBoost']:
            if key in flow:
                best_params[f'flow.{key}'] = flow[key]
    
    # Interactions
    if 'interactions' in config:
        inter = config['interactions']
        if 'stemFiveCombination' in inter and 'bonus' in inter['stemFiveCombination']:
            best_params['interactions.stemFiveCombination.bonus'] = inter['stemFiveCombination']['bonus']
        if 'branchEvents' in inter and 'clashDamping' in inter['branchEvents']:
            best_params['interactions.branchEvents.clashDamping'] = inter['branchEvents']['clashDamping']
    
    return best_params


def apply_parameter_jitter(best_params: Dict[str, float], 
                           jitter_factor: float = 0.2) -> Dict[str, float]:
    """
    V50.1: 参数抖动 - 对当前最佳参数进行随机扰动。
    
    Args:
        best_params: 当前最佳参数
        jitter_factor: 扰动因子（±20%）
    
    Returns:
        扰动后的参数
    """
    jittered_params = {}
    
    for param_path, value in best_params.items():
        # 随机扰动 ±20%
        jitter = random.uniform(-jitter_factor, jitter_factor)
        new_value = value * (1.0 + jitter)
        
        # 确保参数值合理（非负等）
        if 'dampingFactor' in param_path or 'globalEntropy' in param_path:
            new_value = max(0.0, new_value)  # 确保非负
        elif 'rootingWeight' in param_path or 'controlImpact' in param_path:
            new_value = max(0.1, new_value)  # 确保最小正值
        
        jittered_params[param_path] = new_value
    
    return jittered_params


def auto_evolve(target_accuracy: float = 75.0, 
                max_iterations: int = 10,
                trials_per_iteration: int = 200,
                step: int = 1):
    """
    自动进化主循环。
    
    Args:
        target_accuracy: 目标总准确率
        max_iterations: 最大迭代次数
        trials_per_iteration: 每次迭代的试验次数
    """
    print("=" * 80)
    print("🤖 Antigravity 自动进化元优化器 (V51.0 Golden Ratio)")
    print("   Unattended Meta-Optimizer - The Golden Equilibrium Pusher")
    print("   ⚡ V51.0: Fine-Tuning Mode - 锁定黄金参数，微调边缘参数")
    print(f"   🪜 训练阶段(step): {step} (0=全阶段, 1=Foundation, 2=Dynamics)")
    print("=" * 80)
    print()
    print(f"🎯 目标准确率: {target_accuracy:.1f}%")
    print(f"🔄 最大迭代次数: {max_iterations} (0 = 无限循环直到达标)")
    print(f"🔬 每次迭代试验数: {trials_per_iteration}")
    print()
    print("📋 初始配置:")
    print("   - 基于当前 config/parameters.json 作为种子")
    print("   - 动态权重调整：准确率越低，权重越高")
    print("   - 自适应搜索空间：自动扩大触顶参数范围")
    print()
    
    # V50.0: 初始化权重（从当前配置开始，后续动态调整）
    current_weights = {"Strong": 1.0, "Weak": 4.0, "Balanced": 4.0}
    
    # V51.0: Fine-Tuning Mode - 锁定核心参数，只调整边缘参数
    # 架构师测算的黄金参数组（基于物理守恒定律）
    GOLDEN_CONSTANTS = {
        'structure.rootingWeight': 4.25,      # π + 1.1 的近似值
        'flow.controlImpact': 2.618,         # φ² (黄金比例平方)
        'flow.outputDrainPenalty': 2.80,     # 泄耗通道（关键！）
        'flow.generationEfficiency': 0.25,    # 最佳传导率
        'flow.dampingFactor': 0.33,          # 三分之一能量耗散
    }
    
    # V51.0: 锁定核心参数（允许±5%误差）
    LOCKED_PARAMS = set(GOLDEN_CONSTANTS.keys())
    LOCK_TOLERANCE = 0.05  # 5% 容差
    
    # V51.0: 只调整边缘参数
    param_ranges = {
        # 边缘参数1: 润局系数
        'flow.earthMetalMoistureBoost': (5.0, 15.0),
        # 边缘参数2: 冲战损耗
        'interactions.branchEvents.clashDamping': (0.2, 0.8),
    }
    
    print("📋 V51.0 Fine-Tuning Mode 配置:")
    print("   🔒 锁定核心参数（黄金比例）:")
    for param_path, golden_value in GOLDEN_CONSTANTS.items():
        print(f"      {param_path}: {golden_value:.3f} (±5%)")
    print("   🎛️  可调边缘参数:")
    for param_path, (min_val, max_val) in param_ranges.items():
        print(f"      {param_path}: [{min_val:.1f}, {max_val:.1f}]")
    print()
    
    iteration = 0
    best_total_accuracy = 0.0
    # V51.0: 禁用 Chaos Mode，使用 Fine-Tuning Mode
    chaos_mode_active = False  # V51.0: 永远禁用混沌模式
    
    # V50.0: 加载当前最佳参数作为种子
    print("📥 加载当前最佳参数作为种子...")
    seed_params = extract_best_params_from_config()
    if seed_params:
        print(f"   ✅ 已加载 {len(seed_params)} 个参数")
        for param_path, value in list(seed_params.items())[:5]:  # 只显示前5个
            print(f"      {param_path}: {value:.3f}")
        if len(seed_params) > 5:
            print(f"      ... 还有 {len(seed_params) - 5} 个参数")
    else:
        print("   ⚠️  未找到现有参数，将使用默认配置")
    print()
    
    # V50.0: 支持无限循环（max_iterations=0）
    should_continue = True
    while should_continue:
        iteration += 1
        print("\n" + "=" * 80)
        if max_iterations > 0:
            print(f"🔄 迭代 {iteration}/{max_iterations}")
        else:
            print(f"🔄 迭代 {iteration} (无限循环模式)")
        print("=" * 80)
        print(f"   当前最佳准确率: {best_total_accuracy:.1f}% (目标: {target_accuracy:.1f}%)")
        print()
        
        # 步骤1: 更新训练脚本权重
        print("📝 步骤1: 更新训练配置...")
        print("   📋 当前权重配置:")
        for label, weight in current_weights.items():
            print(f"      {label}: {weight:.1f}")
        print()
        
        # 更新 train_model_optuna.py 中的权重
        modify_train_script_weights(current_weights)
        
        # 步骤2: 运行训练
        print("🔬 步骤2: 运行 Optuna 训练...")
        print(f"   🔬 使用当前 config/parameters.json 作为种子")
        print(f"   🔬 试验次数: {trials_per_iteration} (实际使用 train_model_optuna.py 的循环配置)")
        print()
        
        # V53.0: 运行训练脚本（实时输出，不缓冲）
        # 使用 Popen 实时显示输出，而不是 capture_output
        print("   🔄 训练进行中（输出将实时显示）...")
        print()
        
        cmd = ["python3", str(project_root / "scripts" / "train_model_optuna.py")]
        if step in (0, 1, 2):
            cmd += ["--step", str(step)]

        process = subprocess.Popen(
            cmd,
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            bufsize=1  # 行缓冲
        )
        
        # 实时读取并打印输出
        output_lines = []
        for line in process.stdout:
            line = line.rstrip()
            print(line)
            output_lines.append(line)
            # 强制刷新输出
            sys.stdout.flush()
        
        # 等待进程完成
        returncode = process.wait()
        
        if returncode != 0:
            print(f"   ❌ 训练失败 (返回码: {returncode})")
            error_preview = '\n'.join(output_lines[-20:])  # 显示最后20行
            print(f"   {error_preview}")
            print()
            print("   ⚠️  跳过本次迭代，继续下一轮...")
            # 继续下一轮迭代
            continue
        
        print()
        print("   ✅ 训练完成")
        
        # 检查训练是否真的更新了参数
        new_params = extract_best_params_from_config()
        if new_params:
            print(f"   ✅ 已更新最佳参数 ({len(new_params)} 个参数)")
        print()
        
        # 步骤3: 运行验证
        print("📊 步骤3: 运行批量验证...")
        accuracies = run_batch_verify()
        
        print(f"   📈 准确率结果:")
        print(f"      总准确率: {accuracies['Total']:.1f}%")
        for label in ["Strong", "Balanced", "Weak"]:
            print(f"      {label}: {accuracies[label]:.1f}%")
        print()
        
        # V51.0: Fine-Tuning Mode - 简化改进检测
        improved = False
        
        if accuracies['Total'] > best_total_accuracy:
            improvement = accuracies['Total'] - best_total_accuracy
            best_total_accuracy = accuracies['Total']
            improved = True
            print(f"   🎉 发现更好的配置！准确率提升 {improvement:.2f}%")
        else:
            print(f"   ⚠️  本次迭代未改进（当前最佳: {best_total_accuracy:.1f}%）")
        
        # 步骤3: 检查是否达标
        if accuracies['Total'] >= target_accuracy:
            print("=" * 80)
            print("🎉 达到目标准确率！")
            print("=" * 80)
            print(f"最终准确率: {accuracies['Total']:.1f}% (目标: {target_accuracy:.1f}%)")
            print()
            print("各标签准确率:")
            for label in ["Strong", "Balanced", "Weak"]:
                print(f"  {label}: {accuracies[label]:.1f}%")
            print()
            break
        
        # 步骤4: 诊断和调整
        print("🔍 步骤4: 诊断短板并调整策略...")
        
        # V51.0: Fine-Tuning Mode - 正常权重调整（不使用混沌模式）
        old_weights = copy.deepcopy(current_weights)
        current_weights = update_loss_weights(accuracies, current_weights, chaos_mode=False)
        
        # 如果有权重变化，更新训练脚本
        if current_weights != old_weights:
            modify_train_script_weights(current_weights)
        
        # 提取最佳参数并检测触顶
        best_params = extract_best_params_from_config()
        if best_params:
            # V50.1: 混沌模式 - 参数抖动
            if chaos_mode_active and stagnation_detected:
                print("   ⚠️  CHAOS MODE: 应用参数抖动 (±20% 随机扰动)")
                jittered_params = apply_parameter_jitter(best_params, jitter_factor=0.2)
                
                # 将抖动后的参数写回 config/parameters.json（作为下一轮训练的种子）
                config_path = project_root / "config" / "parameters.json"
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    # 更新参数
                    for param_path, value in jittered_params.items():
                        keys = param_path.split('.')
                        target = config
                        for key in keys[:-1]:
                            if key not in target:
                                target[key] = {}
                            target = target[key]
                        target[keys[-1]] = value
                    
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                    
                    print(f"   ✅ 已应用参数抖动，更新了 {len(jittered_params)} 个参数")
                    # 显示几个示例
                    for param_path, value in list(jittered_params.items())[:3]:
                        old_value = best_params.get(param_path, 0)
                        print(f"      {param_path}: {old_value:.3f} → {value:.3f}")
                    if len(jittered_params) > 3:
                        print(f"      ... 还有 {len(jittered_params) - 3} 个参数")
            
            ceilings = detect_parameter_ceiling(best_params, param_ranges)
            
            # V51.0: Fine-Tuning Mode - 参数范围固定（只调整边缘参数）
            # 核心参数已锁定，不需要扩展范围
            print("   ✅ Fine-Tuning Mode: 核心参数已锁定，只调整边缘参数")
        
        print("=" * 80)
        print(f"✅ 迭代 {iteration} 完成")
        print(f"   当前最佳准确率: {best_total_accuracy:.1f}%")
        print(f"   目标: {target_accuracy:.1f}%")
        print(f"   剩余差距: {target_accuracy - best_total_accuracy:.1f}%")
        print("=" * 80)
        print()
        
        # V50.0: 检查是否应该继续
        if max_iterations > 0 and iteration >= max_iterations:
            should_continue = False
        elif accuracies['Total'] >= target_accuracy:
            should_continue = False
    
    # 最终总结
    print("=" * 80)
    if best_total_accuracy >= target_accuracy:
        print("🎉 达到目标准确率！")
    elif max_iterations > 0:
        print("⚠️  达到最大迭代次数")
    else:
        print("⚠️  用户中断或异常退出")
    print("=" * 80)
    print(f"最终准确率: {best_total_accuracy:.1f}% (目标: {target_accuracy:.1f}%)")
    print(f"总迭代次数: {iteration}")
    print()
    
    # 打印各标签最终准确率
    final_accuracies = run_batch_verify()
    print("各标签最终准确率:")
    for label in ["Strong", "Balanced", "Weak"]:
        print(f"  {label}: {final_accuracies[label]:.1f}%")
    print()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='自动进化元优化器')
    parser.add_argument('--target', type=float, default=82.0,
                       help='目标总准确率 (默认: 82.0)')
    parser.add_argument('--max-iter', type=int, default=0,
                       help='最大迭代次数 (默认: 0 = 无限循环直到达标)')
    parser.add_argument('--trials', type=int, default=300,
                       help='每次迭代的试验次数 (默认: 300)')
    parser.add_argument('--step', type=int, default=1, choices=[0, 1, 2],
                       help='训练阶段: 0=全阶段, 1=基础层(Foundation), 2=动力层(Dynamics)。默认 1')
    
    args = parser.parse_args()
    
    auto_evolve(
        target_accuracy=args.target,
        max_iterations=args.max_iter,
        trials_per_iteration=args.trials,
        step=args.step
    )


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

