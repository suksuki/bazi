"""
Phase 1 自动校准器 (Auto Calibrator) - V13.1 重写版
====================================================

V13.1 核心改进：
- 从离散的 Pass/Fail 判定改为连续损失函数（解决概率陷阱）
- 使用模拟退火算法（Simulated Annealing）替代贪心算法（跳出局部死锁）
- 添加先验物理约束（防止物理倒挂）
- 实时 Loss 曲线可视化

版本: V13.1
作者: Antigravity Team
日期: 2025-01-XX
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from copy import deepcopy
import logging
import random

logger = logging.getLogger(__name__)

# V13.1: 参数硬约束（防止越界）
# V13.2: 提升 samePillarBonus 下限，确保自坐强根优势足够明显
PARAM_BOUNDS = {
    'pillarWeights': {
        'year': (0.5, 2.0),
        'month': (0.5, 2.0),
        'day': (0.5, 2.0),
        'hour': (0.5, 2.0),
    },
    'seasonWeights': {
        'wang': (0.5, 2.0),
        'xiang': (0.5, 2.0),
        'xiu': (0.5, 2.0),
        'qiu': (0.5, 2.0),
        'si': (0.5, 2.0),
    },
    'rootingWeight': (1.0, 3.0),
    'samePillarBonus': (1.0, 3.0),  # V10.0: 归一化后，范围调整为 [1.0, 3.0]
    # V13.1: 已删除 season_dominance_boost（参数清洗）
}


def clamp_param(param_path: str, value: float) -> float:
    """
    V13.1: 限制参数在硬约束范围内
    V13.2: 支持4层嵌套参数（如 seasonWeights.xiu）
    
    Args:
        param_path: 参数路径（如 'pillarWeights.day' 或 'seasonWeights.xiu'）
        value: 参数值
        
    Returns:
        限制后的参数值
    """
    parts = param_path.split('.')
    if len(parts) == 1:
        # 简单参数（如 'rootingWeight', 'samePillarBonus'）
        bounds = PARAM_BOUNDS.get(param_path)
        if bounds:
            low, high = bounds
            return max(low, min(high, value))
    elif len(parts) == 2:
        # 嵌套参数（如 'pillarWeights.day' 或 'seasonWeights.xiu'）
        parent = PARAM_BOUNDS.get(parts[0])
        if parent and isinstance(parent, dict):
            bounds = parent.get(parts[1])
            if bounds:
                low, high = bounds
                return max(low, min(high, value))
    return value


class Phase1AutoCalibrator:
    """
    Phase 1 参数自动校准器 (V13.1 重写版)
    
    使用模拟退火算法和连续损失函数，自动调整参数直到所有规则验证通过。
    """
    
    def __init__(self, config: Dict, test_cases: Dict, default_config: Dict = None):
        """
        初始化校准器
        
        Args:
            config: 当前配置
            test_cases: Phase 1 测试案例数据
            default_config: 默认配置（用于正则化计算）
        """
        self.config = deepcopy(config)
        self.test_cases = test_cases
        self.default_config = default_config or deepcopy(config)
        self.optimization_history = []
        
        # V13.1: 正则化系数
        self.lambda_reg = 0.05  # 正则化权重（降低，让优化器更自由）
        
    def calculate_loss(self, config: Dict) -> Tuple[float, Dict]:
        """
        V13.1: 计算连续损失函数
        
        包含三个部分：
        1. Rule Loss: 基于概率的平方惩罚
        2. Regularization Loss: 防止参数偏离默认值过多
        3. Prior Constraints: 先验物理约束（如 Day >= Hour）
        
        Args:
            config: 当前配置
            
        Returns:
            (总损失, 损失详情)
        """
        from core.math import prob_compare
        
        # 1. 运行验证获取能量值
        verification_result = self.run_verification(config)
        
        loss_details = {
            'rule_loss': 0.0,
            'regularization_loss': 0.0,
            'prior_constraint_loss': 0.0,
            'total_loss': 0.0,
            'violations': []
        }
        
        # 2. Rule Loss: 遍历所有规则，计算概率损失
        rule_loss = 0.0
        threshold = 0.75  # V10.0: 参数平滑后，降低区分度阈值要求
        
        # Group A: 月令敏感度测试
        if 'group_a_results' in verification_result:
            group_a_results = verification_result['group_a_results']
            for i in range(len(group_a_results) - 1):
                curr = group_a_results[i]
                next_case = group_a_results[i + 1]
                
                curr_energy = curr.get('self_team_energy_prob', curr.get('self_team_energy', 0.0))
                next_energy = next_case.get('self_team_energy_prob', next_case.get('self_team_energy', 0.0))
                
                # 确保是 ProbValue
                from core.math import ProbValue
                if not isinstance(curr_energy, ProbValue):
                    curr_energy = ProbValue(float(curr_energy), std_dev_percent=0.1)
                if not isinstance(next_energy, ProbValue):
                    next_energy = ProbValue(float(next_energy), std_dev_percent=0.1)
                
                # 计算 P(A > B)
                passed, prob = prob_compare(curr_energy, next_energy, threshold=threshold)
                
                # V13.1: 连续损失（平方惩罚）
                if prob < threshold:
                    # 损失 = (目标 - 当前)^2 * 权重
                    gap = threshold - prob
                    rule_loss += (gap ** 2) * 100  # 平方惩罚，权重 100
                # 如果 P >= 0.75，损失为 0（无痛）
        
        # Group B: 通根有效性测试
        if 'group_b_results' in verification_result:
            group_b_results = verification_result['group_b_results']
            for i in range(len(group_b_results) - 1):
                curr = group_b_results[i]
                next_case = group_b_results[i + 1]
                
                curr_energy = curr.get('self_team_energy_prob', curr.get('self_team_energy', 0.0))
                next_energy = next_case.get('self_team_energy_prob', next_case.get('self_team_energy', 0.0))
                
                from core.math import ProbValue
                if not isinstance(curr_energy, ProbValue):
                    curr_energy = ProbValue(float(curr_energy), std_dev_percent=0.1)
                if not isinstance(next_energy, ProbValue):
                    next_energy = ProbValue(float(next_energy), std_dev_percent=0.1)
                
                passed, prob = prob_compare(curr_energy, next_energy, threshold=threshold)
                
                if prob < threshold:
                    gap = threshold - prob
                    rule_loss += (gap ** 2) * 100
        
        # Group C: 宫位距离测试
        if 'group_c_results' in verification_result:
            group_c_results = verification_result['group_c_results']
            for i in range(len(group_c_results) - 1):
                curr = group_c_results[i]
                next_case = group_c_results[i + 1]
                
                curr_energy = curr.get('self_team_energy_prob', curr.get('self_team_energy', 0.0))
                next_energy = next_case.get('self_team_energy_prob', next_case.get('self_team_energy', 0.0))
                
                from core.math import ProbValue
                if not isinstance(curr_energy, ProbValue):
                    curr_energy = ProbValue(float(curr_energy), std_dev_percent=0.1)
                if not isinstance(next_energy, ProbValue):
                    next_energy = ProbValue(float(next_energy), std_dev_percent=0.1)
                
                passed, prob = prob_compare(curr_energy, next_energy, threshold=threshold)
                
                if prob < threshold:
                    gap = threshold - prob
                    rule_loss += (gap ** 2) * 100
        
        loss_details['rule_loss'] = rule_loss
        
        # 3. Regularization Loss: 防止参数偏离默认值过多
        reg_loss = 0.0
        physics_config = config.get('physics', {})
        default_physics = self.default_config.get('physics', {})
        structure_config = config.get('structure', {})
        default_structure = self.default_config.get('structure', {})
        
        # 宫位权重
        pillar_weights = physics_config.get('pillarWeights', {})
        default_pillar_weights = default_physics.get('pillarWeights', {})
        for key in ['year', 'month', 'day', 'hour']:
            curr_val = pillar_weights.get(key, 1.0)
            default_val = default_pillar_weights.get(key, 1.0)
            reg_loss += 0.05 * ((curr_val - default_val) ** 2)
        
        # V13.1: 已删除 season_dominance_boost（参数清洗）
        
        # 通根系数
        rooting_weight = structure_config.get('rootingWeight', 1.0)
        default_rooting = default_structure.get('rootingWeight', 1.0)
        reg_loss += 0.05 * ((rooting_weight - default_rooting) ** 2)
        
        # 自坐强根加成
        # V13.2: 默认值已提升到3.0，允许优化器探索2.0-4.0范围
        same_pillar_bonus = structure_config.get('samePillarBonus', 1.5)
        default_same = default_structure.get('samePillarBonus', 1.5)
        reg_loss += 0.05 * ((same_pillar_bonus - default_same) ** 2)
        
        loss_details['regularization_loss'] = reg_loss
        
        # 4. Prior Constraints: 先验物理约束
        prior_loss = 0.0
        
        # 约束1: Day >= Hour（日支必须 >= 时支）
        day_weight = pillar_weights.get('day', 1.0)
        hour_weight = pillar_weights.get('hour', 0.9)
        if day_weight < hour_weight:
            prior_loss += 10000  # 重罚！物理倒挂不可接受
            loss_details['violations'].append({
                'type': 'prior_constraint',
                'message': f'Day_Weight ({day_weight:.2f}) < Hour_Weight ({hour_weight:.2f}) - 物理倒挂！'
            })
        
        # 约束2: Month >= Day（V13.3 皇权约束：月令必须 >= 日柱）
        month_weight = pillar_weights.get('month', 1.2)
        if month_weight < day_weight:
            # V13.3: 严厉惩罚权重倒挂（月令是皇帝，必须最高）
            penalty = (day_weight - month_weight) * 5000
            prior_loss += penalty
            loss_details['violations'].append({
                'type': 'prior_constraint',
                'message': f'Month_Weight ({month_weight:.2f}) < Day_Weight ({day_weight:.2f}) - 皇权倒挂！月令必须最高！'
            })
        
        # 约束3: Month >= 0.8（月令不能太低）
        if month_weight < 0.8:
            prior_loss += 5000
            loss_details['violations'].append({
                'type': 'prior_constraint',
                'message': f'Month_Weight ({month_weight:.2f}) < 0.8 - 月令权重过低！'
            })
        
        loss_details['prior_constraint_loss'] = prior_loss
        
        # 总损失
        total_loss = rule_loss + self.lambda_reg * reg_loss + prior_loss
        loss_details['total_loss'] = total_loss
        loss_details['violations'].extend(verification_result.get('violations', []))
        
        return total_loss, loss_details
    
    def run_verification(self, config: Dict) -> Dict:
        """
        运行规则验证，返回验证结果（包含详细能量数据）
        
        Args:
            config: 配置参数
            
        Returns:
            验证结果字典，包含：
            - group_a_passed: Group A 是否通过
            - group_b_passed: Group B 是否通过
            - group_c_passed: Group C 是否通过
            - all_passed: 是否全部通过
            - violations: 违反规则的详细信息
            - group_a_results: Group A 详细结果（包含能量值）
            - group_b_results: Group B 详细结果
            - group_c_results: Group C 详细结果
        """
        from core.engine_graph import GraphNetworkEngine
        from core.processors.physics import GENERATION
        from core.math import ProbValue, prob_compare
        
        temp_engine = GraphNetworkEngine(config=config)
        results = {
            'group_a_passed': True,
            'group_b_passed': True,
            'group_c_passed': True,
            'all_passed': True,
            'violations': [],
            'group_a_results': [],
            'group_b_results': [],
            'group_c_results': []
        }
        
        threshold = 0.75  # V10.0: 参数平滑后，降低区分度阈值要求
        
        # 验证 Group A: 月令敏感度测试
        group_a = self.test_cases.get('group_a_seasonality', [])
        if group_a:
            group_a_results = []
            
            for case in group_a:
                bazi_list = case['bazi']
                day_master = case['day_master']
                
                temp_engine.initialize_nodes(bazi_list, day_master)
                
                dm_element = temp_engine.STEM_ELEMENTS.get(day_master, 'wood')
                
                self_team_energy_prob = ProbValue(0.0, std_dev_percent=0.1)
                
                resource_element = None
                for elem, target in GENERATION.items():
                    if target == dm_element:
                        resource_element = elem
                        break
                
                for node in temp_engine.nodes:
                    node_energy = node.initial_energy
                    if not isinstance(node_energy, ProbValue):
                        node_energy = ProbValue(float(node_energy), std_dev_percent=0.1)
                    
                    if node.element == dm_element:
                        self_team_energy_prob = self_team_energy_prob + node_energy
                    elif resource_element and node.element == resource_element:
                        self_team_energy_prob = self_team_energy_prob + node_energy
                
                group_a_results.append({
                    'id': case['id'],
                    'self_team_energy': float(self_team_energy_prob),
                    'self_team_energy_prob': self_team_energy_prob,
                    'expected_order': case.get('expected_order', 0)
                })
            
            group_a_results.sort(key=lambda x: x['expected_order'])
            results['group_a_results'] = group_a_results
            
            # 验证规则
            for i in range(len(group_a_results) - 1):
                curr = group_a_results[i]
                next_case = group_a_results[i + 1]
                
                curr_energy = curr.get('self_team_energy_prob', ProbValue(curr['self_team_energy'], std_dev_percent=0.1))
                next_energy = next_case.get('self_team_energy_prob', ProbValue(next_case['self_team_energy'], std_dev_percent=0.1))
                
                passed, prob = prob_compare(curr_energy, next_energy, threshold=threshold)
                
                if not passed:
                    results['group_a_passed'] = False
                    results['violations'].append({
                        'group': 'A',
                        'message': f"{curr['id']} vs {next_case['id']}: P({curr['id']} > {next_case['id']}) = {prob:.1%} < {threshold:.0%}"
                    })
        
        # 验证 Group B: 通根有效性测试
        group_b = self.test_cases.get('group_b_rooting', [])
        if group_b:
            group_b_results = []
            
            for case in group_b:
                bazi_list = case['bazi']
                day_master = case['day_master']
                
                temp_engine.initialize_nodes(bazi_list, day_master)
                
                dm_element = temp_engine.STEM_ELEMENTS.get(day_master, 'wood')
                
                self_team_energy_prob = ProbValue(0.0, std_dev_percent=0.1)
                
                resource_element = None
                for elem, target in GENERATION.items():
                    if target == dm_element:
                        resource_element = elem
                        break
                
                for node in temp_engine.nodes:
                    node_energy = node.initial_energy
                    if not isinstance(node_energy, ProbValue):
                        node_energy = ProbValue(float(node_energy), std_dev_percent=0.1)
                    
                    if node.element == dm_element:
                        self_team_energy_prob = self_team_energy_prob + node_energy
                    elif resource_element and node.element == resource_element:
                        self_team_energy_prob = self_team_energy_prob + node_energy
                
                group_b_results.append({
                    'id': case['id'],
                    'self_team_energy': float(self_team_energy_prob),
                    'self_team_energy_prob': self_team_energy_prob,
                    'expected_order': case.get('expected_order', 0)
                })
            
            group_b_results.sort(key=lambda x: x['expected_order'])
            results['group_b_results'] = group_b_results
            
            # 验证规则
            for i in range(len(group_b_results) - 1):
                curr = group_b_results[i]
                next_case = group_b_results[i + 1]
                
                curr_energy = curr.get('self_team_energy_prob', ProbValue(curr['self_team_energy'], std_dev_percent=0.1))
                next_energy = next_case.get('self_team_energy_prob', ProbValue(next_case['self_team_energy'], std_dev_percent=0.1))
                
                passed, prob = prob_compare(curr_energy, next_energy, threshold=threshold)
                
                if not passed:
                    results['group_b_passed'] = False
                    results['violations'].append({
                        'group': 'B',
                        'message': f"{curr['id']} vs {next_case['id']}: P({curr['id']} > {next_case['id']}) = {prob:.1%} < {threshold:.0%}"
                    })
        
        # 验证 Group C: 宫位距离测试
        group_c = self.test_cases.get('group_c_location', [])
        if group_c:
            group_c_results = []
            
            for case in group_c:
                bazi_list = case['bazi']
                day_master = case['day_master']
                
                temp_engine.initialize_nodes(bazi_list, day_master)
                
                dm_element = temp_engine.STEM_ELEMENTS.get(day_master, 'wood')
                
                self_team_energy_prob = ProbValue(0.0, std_dev_percent=0.1)
                
                resource_element = None
                for elem, target in GENERATION.items():
                    if target == dm_element:
                        resource_element = elem
                        break
                
                for node in temp_engine.nodes:
                    node_energy = node.initial_energy
                    if not isinstance(node_energy, ProbValue):
                        node_energy = ProbValue(float(node_energy), std_dev_percent=0.1)
                    
                    if node.element == dm_element:
                        self_team_energy_prob = self_team_energy_prob + node_energy
                    elif resource_element and node.element == resource_element:
                        self_team_energy_prob = self_team_energy_prob + node_energy
                
                group_c_results.append({
                    'id': case['id'],
                    'self_team_energy': float(self_team_energy_prob),
                    'self_team_energy_prob': self_team_energy_prob,
                    'expected_order': case.get('expected_order', 0)
                })
            
            group_c_results.sort(key=lambda x: x['expected_order'])
            results['group_c_results'] = group_c_results
            
            # 验证规则
            for i in range(len(group_c_results) - 1):
                curr = group_c_results[i]
                next_case = group_c_results[i + 1]
                
                curr_energy = curr.get('self_team_energy_prob', ProbValue(curr['self_team_energy'], std_dev_percent=0.1))
                next_energy = next_case.get('self_team_energy_prob', ProbValue(next_case['self_team_energy'], std_dev_percent=0.1))
                
                passed, prob = prob_compare(curr_energy, next_energy, threshold=threshold)
                
                if not passed:
                    results['group_c_passed'] = False
                    results['violations'].append({
                        'group': 'C',
                        'message': f"{curr['id']} vs {next_case['id']}: P({curr['id']} > {next_case['id']}) = {prob:.1%} < {threshold:.0%}"
                    })
        
        results['all_passed'] = (
            results['group_a_passed'] and 
            results['group_b_passed'] and 
            results['group_c_passed']
        )
        
        return results
    
    def calibrate(self, max_iterations: int = 100, initial_temperature: float = 100.0, 
                  cooling_rate: float = 0.95, perturbation_scale: float = 0.1) -> Tuple[Dict, Dict, List[Dict]]:
        """
        V13.1: 模拟退火优化器
        
        核心循环：
        1. 扰动 (Perturb): 随机选择一个参数，加上高斯噪声
        2. 计算新 Loss: calculate_loss(new_config)
        3. 接受准则 (Metropolis Criterion):
           - 如果 new_loss < current_loss: 接受（变好了）
           - 如果 new_loss > current_loss: 以概率 P = exp(-(new_loss - current_loss) / T) 接受（赌一把）
        4. 降温: Temperature *= cooling_rate
        
        Args:
            max_iterations: 最大迭代次数
            initial_temperature: 初始温度（越高，越容易接受坏解）
            cooling_rate: 降温速率（0.95 表示每次迭代温度降 5%）
            perturbation_scale: 扰动幅度（高斯噪声的标准差）
            
        Returns:
            (优化后的配置, 最终验证结果, 优化历史)
        """
        current_config = deepcopy(self.config)
        best_config = deepcopy(current_config)
        best_loss, _ = self.calculate_loss(best_config)
        
        temperature = initial_temperature
        history = []
        
        # 计算初始损失
        current_loss, initial_loss_details = self.calculate_loss(current_config)
        logger.info(f"V13.1 模拟退火开始: 初始损失 = {current_loss:.4f}")
        logger.info(f"  规则损失: {initial_loss_details['rule_loss']:.2f}")
        logger.info(f"  正则化损失: {initial_loss_details['regularization_loss']:.4f}")
        logger.info(f"  先验约束损失: {initial_loss_details['prior_constraint_loss']:.2f}")
        
        # 可调参数列表
        # V13.1: 参数清洗 - 已删除 season_dominance_boost
        # V13.2: 聚焦核心参数，samePillarBonus 范围提升到 [2.0, 4.0]
        tunable_params = [
            ('physics.pillarWeights.month', 'month'),
            ('physics.pillarWeights.day', 'day'),
            ('physics.pillarWeights.hour', 'hour'),
            ('physics.pillarWeights.year', 'year'),
            ('physics.seasonWeights.xiu', 'xiu'),  # V13.2: 添加季节权重调优
            ('physics.seasonWeights.si', 'si'),      # V13.2: 添加季节权重调优
            ('structure.rootingWeight', 'rooting'),
            ('structure.samePillarBonus', 'same'),   # V13.2: 重点优化，范围 [2.0, 4.0]
        ]
        
        for iteration in range(max_iterations):
            # 计算当前损失
            current_loss, loss_details = self.calculate_loss(current_config)
            verification_result = self.run_verification(current_config)
            
            # 记录历史
            history.append({
                'iteration': iteration + 1,
                'temperature': temperature,
                'loss': current_loss,
                'loss_details': loss_details,
                'config': deepcopy(current_config),
                'result': verification_result,
                'accepted': False
            })
            
            # 如果全部通过且损失足够低，提前返回
            if verification_result['all_passed'] and current_loss < 0.5:
                logger.info(f"✅ V13.1 校准成功！迭代次数: {iteration + 1}, 最终损失: {current_loss:.4f}")
                return current_config, verification_result, history
            
            # 如果找到更好的配置，更新最佳配置
            if current_loss < best_loss:
                best_config = deepcopy(current_config)
                best_loss = current_loss
                logger.debug(f"迭代 {iteration + 1}: 损失改善 {best_loss:.4f} (温度: {temperature:.2f})")
            
            # 1. 扰动: 随机选择一个参数，加上高斯噪声
            new_config = deepcopy(current_config)
            param_path, param_name = random.choice(tunable_params)
            
            # 解析参数路径
            parts = param_path.split('.')
            if len(parts) == 4:
                # physics.seasonWeights.xiu
                parent = new_config.get(parts[0], {})
                child = parent.get(parts[1], {})
                grandchild = child.get(parts[2], {})
                current_val = grandchild.get(parts[3], 1.0)
                
                # 添加高斯噪声
                noise = np.random.normal(0, perturbation_scale)
                new_val = current_val + noise
                
                # 硬约束
                new_val = clamp_param(f"{parts[1]}.{parts[3]}", new_val)
                grandchild[parts[3]] = new_val
                child[parts[2]] = grandchild
                parent[parts[1]] = child
                new_config[parts[0]] = parent
            elif len(parts) == 3:
                # physics.pillarWeights.month
                parent = new_config.get(parts[0], {})
                child = parent.get(parts[1], {})
                current_val = child.get(parts[2], 1.0)
                
                # 添加高斯噪声
                noise = np.random.normal(0, perturbation_scale)
                new_val = current_val + noise
                
                # 硬约束
                new_val = clamp_param(f"{parts[1]}.{parts[2]}", new_val)
                child[parts[2]] = new_val
                parent[parts[1]] = child
                new_config[parts[0]] = parent
            elif len(parts) == 2:
                # structure.rootingWeight, structure.samePillarBonus
                parent = new_config.get(parts[0], {})
                current_val = parent.get(parts[1], 1.0)
                
                noise = np.random.normal(0, perturbation_scale)
                new_val = current_val + noise
                new_val = clamp_param(parts[1], new_val)
                parent[parts[1]] = new_val
                new_config[parts[0]] = parent
            
            # 2. 计算新 Loss
            new_loss, new_loss_details = self.calculate_loss(new_config)
            
            # 3. Metropolis 接受准则
            accept = False
            if new_loss < current_loss:
                # 变好了，直接接受
                accept = True
            else:
                # 变差了，以一定概率接受（为了跳出局部死锁）
                delta_loss = new_loss - current_loss
                if delta_loss > 0:
                    # 计算接受概率: P = exp(-delta_loss / T)
                    accept_prob = np.exp(-delta_loss / temperature)
                    if random.random() < accept_prob:
                        accept = True
            
            # 4. 如果接受，更新当前配置
            if accept:
                current_config = new_config
                current_loss = new_loss
                history[-1]['accepted'] = True
                logger.debug(f"迭代 {iteration + 1}: 接受新配置 (损失: {new_loss:.4f}, 温度: {temperature:.2f})")
            
            # 5. 降温
            temperature *= cooling_rate
        
        # 返回最佳配置
        final_result = self.run_verification(best_config)
        final_loss, _ = self.calculate_loss(best_config)
        logger.warning(f"⚠️ V13.1 校准完成: 最佳损失 = {final_loss:.4f}, 迭代次数 = {max_iterations}")
        return best_config, final_result, history
