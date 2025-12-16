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

版本: V1.0
作者: Antigravity Team
日期: 2025-12-16
"""

import json
import sys
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import copy

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
                       current_weights: Dict[str, float]) -> Dict[str, float]:
    """
    根据准确率动态调整 Loss 权重。
    
    V50.0 改进：使用更激进的动态公式，准确率越低，权重越高。
    
    Args:
        accuracies: 当前准确率（0-100）
        current_weights: 当前权重
    
    Returns:
        更新后的权重
    """
    new_weights = copy.deepcopy(current_weights)
    
    # V50.0: 动态权重公式
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
                           current_ranges: Dict[str, Tuple[float, float]]) -> Dict[str, Tuple[float, float]]:
    """
    自动扩大触顶参数的搜索范围。
    
    Args:
        ceilings: 触顶检测结果
        current_ranges: 当前参数范围
    
    Returns:
        更新后的参数范围
    """
    new_ranges = copy.deepcopy(current_ranges)
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


def auto_evolve(target_accuracy: float = 75.0, 
                max_iterations: int = 10,
                trials_per_iteration: int = 200):
    """
    自动进化主循环。
    
    Args:
        target_accuracy: 目标总准确率
        max_iterations: 最大迭代次数
        trials_per_iteration: 每次迭代的试验次数
    """
    print("=" * 80)
    print("🤖 Antigravity 自动进化元优化器 (V50.0)")
    print("   Unattended Meta-Optimizer - The Golden Equilibrium Pusher")
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
    
    # V50.0: 参数范围（基于 V49.0，后续会根据触顶情况自动扩大）
    param_ranges = {
        'structure.rootingWeight': (3.0, 6.0),
        'physics.pillarWeights.day': (1.0, 1.8),
        'physics.pillarWeights.month': (0.8, 2.0),
        'physics.pillarWeights.year': (0.5, 1.8),
        'physics.pillarWeights.hour': (0.5, 1.5),
        'flow.controlImpact': (5.0, 10.0),
        'flow.generationEfficiency': (0.1, 0.4),
        'flow.dampingFactor': (0.0, 0.4),
        'flow.outputDrainPenalty': (1.5, 3.0),
        'flow.globalEntropy': (0.05, 0.15),
        'flow.earthMetalMoistureBoost': (5.0, 15.0),
        'interactions.stemFiveCombination.bonus': (1.2, 2.5),
        'interactions.branchEvents.clashDamping': (0.2, 0.8),
    }
    
    iteration = 0
    best_total_accuracy = 0.0
    no_improvement_count = 0  # 连续无改进次数
    max_no_improvement = 5  # 连续5次无改进则扩大搜索空间
    
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
        
        # V50.0: 运行训练脚本（train_model_optuna.py 会自动加载 config/parameters.json 作为种子）
        result = subprocess.run(
            ["python3", str(project_root / "scripts" / "train_model_optuna.py")],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode != 0:
            print(f"   ❌ 训练失败")
            error_preview = result.stderr[:500] if result.stderr else result.stdout[:500]
            print(f"   {error_preview}")
            print()
            print("   ⚠️  跳过本次迭代，继续下一轮...")
            # 继续下一轮迭代
            continue
        
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
        
        # 更新最佳准确率
        improved = False
        if accuracies['Total'] > best_total_accuracy:
            improvement = accuracies['Total'] - best_total_accuracy
            best_total_accuracy = accuracies['Total']
            improved = True
            no_improvement_count = 0
            print(f"   🎉 发现更好的配置！准确率提升 {improvement:.2f}%")
        else:
            no_improvement_count += 1
            print(f"   ⚠️  本次迭代未改进（连续 {no_improvement_count} 次无改进）")
        
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
        
        # 更新权重
        old_weights = copy.deepcopy(current_weights)
        current_weights = update_loss_weights(accuracies, current_weights)
        
        # 如果有权重变化，更新训练脚本
        if current_weights != old_weights:
            modify_train_script_weights(current_weights)
        
        # 提取最佳参数并检测触顶
        best_params = extract_best_params_from_config()
        if best_params:
            ceilings = detect_parameter_ceiling(best_params, param_ranges)
            
            # 扩大触顶参数的搜索范围
            old_ranges = copy.deepcopy(param_ranges)
            param_ranges = expand_parameter_ranges(ceilings, param_ranges)
            
            # 如果有范围变化，需要更新 train_model_optuna.py 中的参数范围
            # 这里简化处理，打印提示
            if param_ranges != old_ranges:
                print("   ⚠️  参数范围已更新，但需要手动修改 train_model_optuna.py 中的搜索范围")
                print("   更新后的参数范围:")
                for param_path, (min_val, max_val) in param_ranges.items():
                    if param_path in old_ranges:
                        old_min, old_max = old_ranges[param_path]
                        if abs(max_val - old_max) > 0.01:
                            print(f"      {param_path}: [{min_val:.2f}, {max_val:.2f}] (原: [{old_min:.2f}, {old_max:.2f}])")
                print()
        
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
    
    args = parser.parse_args()
    
    auto_evolve(
        target_accuracy=args.target,
        max_iterations=args.max_iter,
        trials_per_iteration=args.trials
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

