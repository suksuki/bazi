"""
Antigravity Auto-Tuning Regression Script (Hill Climbing)
==========================================================

基于《Antigravity 核心调优总纲 V1.0》实现的自动参数优化脚本。

核心功能：
1. 使用爬山算法（Hill Climbing）自动调整 Layer 1 和 Layer 2 参数
2. 最小化预测结果与真实案例之间的误差
3. 支持微调多个关键参数，自动保存最优配置

作者: Antigravity Team
版本: V1.0
日期: 2025-01-16
"""

import sys
import os
import json
import copy
import random
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.engine_v91 import EngineV91
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.config_rules import (
    ENERGY_THRESHOLD_STRONG, ENERGY_THRESHOLD_WEAK,
    SCORE_TREASURY_BONUS, SCORE_SKULL_CRASH
)


# ===========================================
# 1. Mock Data Loader (测试案例加载器)
# ===========================================

def load_test_cases(data_path: str = None) -> List[Dict]:
    """
    加载测试案例数据。
    
    Args:
        data_path: 数据文件路径，默认为 data/golden_cases.json
    
    Returns:
        测试案例列表，每个案例包含 id, bazi, labels 等信息
    """
    if data_path is None:
        project_root = Path(__file__).parent.parent
        data_path = project_root / "data" / "golden_cases.json"
    
    # 如果文件不存在，尝试使用 calibration_cases.json
    if not os.path.exists(data_path):
        fallback_path = project_root / "calibration_cases.json"
        if os.path.exists(fallback_path):
            data_path = fallback_path
            print(f"⚠️  golden_cases.json 不存在，使用 {fallback_path}")
        else:
            raise FileNotFoundError(f"无法找到测试数据文件: {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    # 标准化数据格式
    normalized_cases = []
    for case in cases:
        # 提取必要字段
        normalized_case = {
            'id': case.get('id', 'unknown'),
            'bazi': case.get('bazi', []),
            'day_master': case.get('day_master', '甲'),
            'gender': case.get('gender', '男'),
        }
        
        # 提取标签（Ground Truth）
        gt = case.get('ground_truth', {})
        labels = {
            'strength': gt.get('strength', 'Unknown'),  # "Strong" / "Weak" / "Follower"
            'wealth_score': gt.get('wealth_score', 0.0),
            'career_score': gt.get('career_score', 0.0),
            'relationship_score': gt.get('relationship_score', 0.0),
        }
        normalized_case['labels'] = labels
        
        # 添加出生信息（如果有）
        if 'birth_date' in case:
            normalized_case['birth_date'] = case['birth_date']
        if 'birth_time' in case:
            normalized_case['birth_time'] = case['birth_time']
        
        normalized_cases.append(normalized_case)
    
    return normalized_cases


# ===========================================
# 2. Parameter Manager (参数管理器)
# ===========================================

class ParameterManager:
    """管理算法参数的加载、修改和保存"""
    
    def __init__(self, config_path: str = None):
        """
        初始化参数管理器。
        
        Args:
            config_path: 配置文件路径，默认使用 DEFAULT_FULL_ALGO_PARAMS
        """
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.params = json.load(f)
        else:
            # 使用默认配置
            self.params = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
        
        # 定义可调参数及其范围（基于 QUANTUM_LAB_SIDEBAR_PARAMETERS_CONFIG.md）
        self.tunable_params = {
            # Layer 1: 基础场域 (Physics)
            ('physics', 'pillarWeights', 'year'): (0.5, 1.5, 0.1),
            ('physics', 'pillarWeights', 'month'): (0.5, 2.0, 0.1),
            ('physics', 'pillarWeights', 'day'): (0.5, 1.5, 0.1),
            ('physics', 'pillarWeights', 'hour'): (0.5, 1.5, 0.1),
            
            # Layer 1: 粒子动态 (Structure)
            ('structure', 'rootingWeight'): (0.5, 2.0, 0.1),
            ('structure', 'exposedBoost'): (1.0, 3.0, 0.1),
            ('structure', 'samePillarBonus'): (1.0, 2.0, 0.1),
            ('structure', 'voidPenalty'): (0.0, 1.0, 0.1),
            
            # Layer 1: 几何交互 - 天干五合
            ('interactions', 'stemFiveCombination', 'threshold'): (0.5, 1.0, 0.05),
            ('interactions', 'stemFiveCombination', 'bonus'): (1.0, 3.0, 0.1),
            ('interactions', 'stemFiveCombination', 'penalty'): (0.0, 1.0, 0.1),
            
            # Layer 1: 几何交互 - 地支成局
            ('interactions', 'comboPhysics', 'trineBonus'): (1.5, 5.0, 0.1),
            ('interactions', 'comboPhysics', 'halfBonus'): (1.0, 3.0, 0.1),
            ('interactions', 'comboPhysics', 'directionalBonus'): (2.0, 6.0, 0.1),
            
            # Layer 1: 几何交互 - 墓库物理（关键参数）
            ('interactions', 'vaultPhysics', 'threshold'): (10.0, 50.0, 5.0),
            ('interactions', 'vaultPhysics', 'openBonus'): (1.0, 3.0, 0.1),  # vp_ob
            ('interactions', 'vaultPhysics', 'sealedDamping'): (0.0, 1.0, 0.1),
            ('interactions', 'vaultPhysics', 'breakPenalty'): (0.0, 1.0, 0.1),
            
            # Layer 1: 能量流转
            ('flow', 'resourceImpedance', 'base'): (0.0, 0.9, 0.05),
            ('flow', 'resourceImpedance', 'weaknessPenalty'): (0.0, 1.0, 0.1),  # imp_weak
            ('flow', 'outputViscosity', 'maxDrainRate'): (0.1, 1.0, 0.05),
            ('flow', 'controlImpact'): (0.1, 1.0, 0.1),
            ('flow', 'globalEntropy'): (0.0, 0.2, 0.01),
            
            # Layer 1: 能量阈值
            ('global_logic', 'energy_threshold_strong'): (0.0, 10.0, 0.5),
            ('global_logic', 'energy_threshold_weak'): (0.0, 10.0, 0.5),
            
            # Layer 2: 时空修正
            ('spacetime', 'luckPillarWeight'): (0.0, 1.0, 0.1),
        }
        # 格式: (path_tuple): (min_value, max_value, step_size)
    
    def get_param(self, *path: str) -> Any:
        """获取参数值"""
        value = self.params
        for key in path:
            value = value.get(key, {})
        return value
    
    def set_param(self, value: Any, *path: str):
        """设置参数值"""
        target = self.params
        for key in path[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[path[-1]] = value
    
    def get_params(self) -> Dict:
        """获取完整参数配置"""
        return copy.deepcopy(self.params)
    
    def set_params(self, params: Dict):
        """设置完整参数配置"""
        self.params = copy.deepcopy(params)
    
    def perturb_param(self, *path: str, delta: float = None) -> bool:
        """
        对指定参数进行微调（扰动）。
        
        Args:
            *path: 参数路径（如 'physics', 'pillarWeights', 'month'）
            delta: 扰动值，如果为 None 则使用参数的 step_size
        
        Returns:
            是否成功扰动（参数在范围内）
        """
        if path not in self.tunable_params:
            return False
        
        min_val, max_val, step = self.tunable_params[path]
        current_val = self.get_param(*path)
        
        if delta is None:
            delta = step * random.choice([-1, 1])  # 随机增加或减少
        
        new_val = current_val + delta
        new_val = max(min_val, min(max_val, new_val))  # 限制在范围内
        
        # 如果新值等于旧值（边界情况），尝试反向扰动
        if abs(new_val - current_val) < 0.001:
            delta = -delta
            new_val = current_val + delta
            new_val = max(min_val, min(max_val, new_val))
        
        if abs(new_val - current_val) < 0.001:
            return False  # 无法扰动
        
        self.set_param(new_val, *path)
        return True
    
    def save(self, output_path: str):
        """保存参数到文件"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.params, f, indent=2, ensure_ascii=False)


# ===========================================
# 3. Engine Wrapper (引擎封装器)
# ===========================================

class EngineWrapper:
    """封装引擎调用，支持参数注入"""
    
    def __init__(self):
        self.engine = EngineV91()
    
    def calculate_score(self, case: Dict, params: Dict) -> Dict:
        """
        使用给定参数计算案例的得分。
        
        Args:
            case: 测试案例（包含 bazi, day_master 等）
            params: 参数配置
        
        Returns:
            预测结果字典，包含 strength, wealth, career, relationship 等
        """
        # 注入参数到引擎
        if hasattr(self.engine, 'update_full_config'):
            self.engine.update_full_config(params)
        elif hasattr(self.engine, 'config'):
            # EngineV91 使用 config 属性
            self.engine.config = copy.deepcopy(params)
            # 如果引擎内部使用了 processors，也需要更新它们的配置
            if hasattr(self.engine, 'physics') and hasattr(self.engine.physics, 'config'):
                self.engine.physics.config = params.get('physics', {})
        else:
            # 如果引擎不支持动态配置，使用默认配置
            pass
        
        try:
            bazi = case['bazi']
            day_master = case['day_master']
            
            # 构建 case_data 格式
            case_data = {
                'id': case.get('id', 'unknown'),
                'year': bazi[0] if len(bazi) > 0 else '甲子',
                'month': bazi[1] if len(bazi) > 1 else '甲子',
                'day': bazi[2] if len(bazi) > 2 else '甲子',
                'hour': bazi[3] if len(bazi) > 3 else '甲子',
                'day_master': day_master,
                'gender': case.get('gender', '男'),
            }
            
            # 调用引擎计算
            result = self.engine.calculate_energy(case_data)
            
            # 提取预测值
            strength_str = result.get('wang_shuai', 'Unknown')
            strength_score = result.get('wang_shuai_score', 0.0)
            
            # 将 strength 字符串转换为数值（用于损失计算）
            is_strong = 1.0 if 'Strong' in strength_str else 0.0
            
            # 提取宏观得分（0-100 范围，需要转换为 0-100）
            wealth = result.get('wealth', 0.0) * 10.0  # 假设引擎返回 0-10，转换为 0-100
            career = result.get('career', 0.0) * 10.0
            relationship = result.get('relationship', 0.0) * 10.0
            
            return {
                'strength': is_strong,
                'strength_str': strength_str,
                'strength_score': strength_score,
                'wealth': wealth,
                'career': career,
                'relationship': relationship,
            }
            
        except Exception as e:
            print(f"⚠️  计算案例 {case.get('id', 'unknown')} 时出错: {e}")
            # 返回默认值
            return {
                'strength': 0.5,
                'strength_str': 'Unknown',
                'strength_score': 0.0,
                'wealth': 50.0,
                'career': 50.0,
                'relationship': 50.0,
            }


# ===========================================
# 4. Loss Function (损失函数)
# ===========================================

def calculate_loss(predictions: List[Dict], true_labels: List[Dict], 
                   weights: Dict[str, float] = None) -> float:
    """
    计算总损失（均方误差）。
    
    Args:
        predictions: 预测结果列表
        true_labels: 真实标签列表
        weights: 损失权重 {'strength': 1.0, 'wealth': 1.0, 'career': 1.0, 'relationship': 1.0}
    
    Returns:
        总损失值（越小越好）
    """
    if weights is None:
        weights = {
            'strength': 1.0,
            'wealth': 0.5,
            'career': 0.5,
            'relationship': 0.3,
        }
    
    total_loss = 0.0
    count = 0
    
    for pred, true in zip(predictions, true_labels):
        # Strength loss（需要转换 true 标签）
        true_strength = 1.0 if true.get('strength') == 'Strong' else 0.0
        strength_loss = (pred['strength'] - true_strength) ** 2
        total_loss += weights['strength'] * strength_loss
        
        # Wealth loss
        wealth_loss = (pred['wealth'] - true.get('wealth_score', 50.0)) ** 2
        total_loss += weights['wealth'] * wealth_loss
        
        # Career loss
        career_loss = (pred['career'] - true.get('career_score', 50.0)) ** 2
        total_loss += weights['career'] * career_loss
        
        # Relationship loss
        rel_loss = (pred['relationship'] - true.get('relationship_score', 50.0)) ** 2
        total_loss += weights['relationship'] * rel_loss
        
        count += 1
    
    return total_loss / count if count > 0 else float('inf')


# ===========================================
# 5. Optimizer Loop (优化循环)
# ===========================================

class HillClimbingOptimizer:
    """爬山算法优化器"""
    
    def __init__(self, param_manager: ParameterManager, engine_wrapper: EngineWrapper,
                 test_cases: List[Dict], loss_weights: Dict[str, float] = None):
        self.param_manager = param_manager
        self.engine_wrapper = engine_wrapper
        self.test_cases = test_cases
        self.loss_weights = loss_weights or {
            'strength': 1.0,
            'wealth': 0.5,
            'career': 0.5,
            'relationship': 0.3,
        }
        
        # 提取真实标签
        self.true_labels = [case['labels'] for case in test_cases]
    
    def evaluate(self, params: Dict) -> float:
        """评估当前参数的总损失"""
        predictions = []
        for case in self.test_cases:
            pred = self.engine_wrapper.calculate_score(case, params)
            predictions.append(pred)
        
        loss = calculate_loss(predictions, self.true_labels, self.loss_weights)
        return loss
    
    def optimize(self, max_iterations: int = 100, verbose: bool = True) -> Tuple[Dict, float, List[Dict]]:
        """
        执行爬山算法优化。
        
        Args:
            max_iterations: 最大迭代次数
            verbose: 是否打印详细信息
        
        Returns:
            (最优参数, 最优损失, 优化历史)
        """
        # 初始化
        best_params = self.param_manager.get_params()
        best_loss = self.evaluate(best_params)
        current_params = copy.deepcopy(best_params)
        current_loss = best_loss
        
        history = [{'iteration': 0, 'loss': best_loss, 'improvement': 0.0}]
        
        if verbose:
            print(f"🚀 开始优化...")
            print(f"   初始损失: {best_loss:.4f}")
            print(f"   测试案例数: {len(self.test_cases)}")
            print(f"   可调参数数: {len(self.param_manager.tunable_params)}")
            print()
        
        improved_count = 0
        
        for iteration in range(1, max_iterations + 1):
            # 随机选择一个参数进行扰动
            tunable_list = list(self.param_manager.tunable_params.keys())
            if not tunable_list:
                break
            
            param_path = random.choice(tunable_list)
            
            # 保存当前参数状态
            saved_params = copy.deepcopy(current_params)
            self.param_manager.set_params(saved_params)
            
            # 尝试扰动
            if not self.param_manager.perturb_param(*param_path):
                continue  # 无法扰动，跳过
            
            # 评估新参数
            new_params = self.param_manager.get_params()
            new_loss = self.evaluate(new_params)
            
            # 判断是否改进
            if new_loss < current_loss:
                # 改进：保留新参数
                improvement = current_loss - new_loss
                current_params = new_params
                current_loss = new_loss
                improved_count += 1
                
                # 更新最优值
                if new_loss < best_loss:
                    best_params = copy.deepcopy(new_params)
                    best_loss = new_loss
                    improvement_msg = f"✅ 新的最优值！"
                else:
                    improvement_msg = f"✅ 局部改进"
                
                if verbose:
                    param_name = '/'.join(str(p) for p in param_path)
                    current_val = self.param_manager.get_param(*param_path)
                    print(f"   [{iteration}/{max_iterations}] {improvement_msg}")
                    print(f"      参数: {param_name}")
                    print(f"      值: {current_val:.3f}")
                    print(f"      损失: {new_loss:.4f} (改进: {improvement:.4f})")
                    print()
            else:
                # 未改进：回滚
                current_params = saved_params
                current_loss = self.evaluate(current_params)
            
            # 记录历史
            history.append({
                'iteration': iteration,
                'loss': current_loss,
                'best_loss': best_loss,
                'improvement': best_loss - history[0]['loss'],
            })
        
        if verbose:
            print(f"🎯 优化完成！")
            print(f"   总迭代次数: {max_iterations}")
            print(f"   改进次数: {improved_count}")
            print(f"   最优损失: {best_loss:.4f}")
            print(f"   损失下降: {history[0]['loss'] - best_loss:.4f} ({((history[0]['loss'] - best_loss) / history[0]['loss'] * 100):.1f}%)")
            print()
        
        return best_params, best_loss, history


# ===========================================
# 6. Main Function (主函数)
# ===========================================

def main():
    """主函数：执行自动调优"""
    print("=" * 60)
    print("🤖 Antigravity Auto-Tuning Regression Script (V1.0)")
    print("   基于爬山算法的参数自动优化")
    print("=" * 60)
    print()
    
    # 1. 加载测试数据
    print("📚 加载测试数据...")
    try:
        test_cases = load_test_cases()
        print(f"   ✅ 成功加载 {len(test_cases)} 个测试案例")
    except Exception as e:
        print(f"   ❌ 加载失败: {e}")
        print()
        print("💡 提示：请创建 data/golden_cases.json 文件，格式如下：")
        print(json.dumps([
            {
                "id": "MA_YUN",
                "bazi": ["甲子", "丙子", "丁丑", "戊寅"],
                "day_master": "丁",
                "labels": {
                    "strength": "Weak",
                    "wealth_score": 95.0,
                    "career_score": 90.0,
                    "relationship_score": 40.0
                }
            }
        ], indent=2, ensure_ascii=False))
        return
    
    if len(test_cases) == 0:
        print("   ⚠️  测试案例为空，无法进行优化")
        return
    
    print()
    
    # 2. 初始化参数管理器
    print("⚙️  初始化参数管理器...")
    param_manager = ParameterManager()
    print(f"   ✅ 加载 {len(param_manager.tunable_params)} 个可调参数")
    print()
    
    # 3. 初始化引擎封装器
    print("🔧 初始化引擎...")
    engine_wrapper = EngineWrapper()
    print("   ✅ 引擎就绪")
    print()
    
    # 4. 初始化优化器
    optimizer = HillClimbingOptimizer(param_manager, engine_wrapper, test_cases)
    
    # 5. 计算 Baseline 损失
    print("📊 计算 Baseline 损失...")
    baseline_params = param_manager.get_params()
    baseline_loss = optimizer.evaluate(baseline_params)
    print(f"   Baseline 损失: {baseline_loss:.4f}")
    print()
    
    # 6. 执行优化
    print("🚀 开始优化循环...")
    print()
    
    best_params, best_loss, history = optimizer.optimize(
        max_iterations=100,  # 可调整
        verbose=True
    )
    
    # 7. 保存结果
    print("💾 保存优化结果...")
    project_root = Path(__file__).parent.parent
    output_path = project_root / "config" / "optimized_parameters.json"
    
    param_manager.set_params(best_params)
    param_manager.save(str(output_path))
    print(f"   ✅ 已保存到: {output_path}")
    print()
    
    # 8. 生成优化报告
    print("📋 优化报告")
    print("=" * 60)
    print(f"初始损失: {history[0]['loss']:.4f}")
    print(f"最优损失: {best_loss:.4f}")
    print(f"损失下降: {history[0]['loss'] - best_loss:.4f}")
    print(f"相对改进: {((history[0]['loss'] - best_loss) / history[0]['loss'] * 100):.1f}%")
    print(f"总迭代次数: {len(history) - 1}")
    print()
    
    # 显示关键参数的变化
    print("🔍 关键参数值（优化后）：")
    key_params = [
        (('physics', 'pillarWeights', 'month'), '月令权重 (pg_month)'),
        (('interactions', 'vaultPhysics', 'openBonus'), '开库爆发 (vp_ob)'),
        (('flow', 'resourceImpedance', 'weaknessPenalty'), '虚不受补 (imp_weak)'),
        (('global_logic', 'energy_threshold_strong'), '身旺线'),
        (('global_logic', 'energy_threshold_weak'), '身弱线'),
    ]
    
    for param_path, param_name in key_params:
        if param_path in param_manager.tunable_params:
            value = param_manager.get_param(*param_path)
            print(f"   {param_name}: {value:.3f}")
    
    print()
    print("=" * 60)
    print("✅ 优化完成！")


if __name__ == "__main__":
    main()

