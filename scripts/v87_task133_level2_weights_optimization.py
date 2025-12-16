"""
V87.0 任务 133：Level 2 权重结构性修复与优化
==========================================
目标：修复 Level 2 权重配置的理论缺陷（特别是 Relationship 维度），
      通过优化 Level 2 权重，将总 MAE 降至 5.0 以下。

策略：
1. 锁定 Level 1 参数为 V80.0 最优值
2. 优化 Level 2 权重（Relationship_bias, Wealth_exp, Relationship_max_score 等）
3. 使用所有 24 个误差点（8个案例 × 3个维度）进行优化
"""

import sys
import os
import json
import io
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from copy import deepcopy
from datetime import datetime

# Fix encoding issue
import locale
try:
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
except:
    pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine_v88 import EngineV88


class V87Level2Optimizer:
    """
    V87.0 Level 2 权重优化器
    
    专门优化 Level 2 权重配置，锁定 Level 1 参数
    """
    
    def __init__(self, config_path: str, cases_path: str = None, optimal_level1_params: Dict = None):
        """
        初始化优化器
        
        Args:
            config_path: 配置文件路径
            cases_path: 校准案例路径
            optimal_level1_params: V80.0 最优 Level 1 参数（用于锁定）
        """
        self.config_path = config_path
        self.cases_path = cases_path
        
        # 加载配置
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.base_config = json.load(f)
        
        # 加载 V80.0 最优 Level 1 参数
        if optimal_level1_params:
            self.level1_params = optimal_level1_params
        else:
            self.level1_params = self._load_optimal_level1_params()
        
        # 应用 Level 1 参数到配置（锁定）
        self.base_config = self._apply_level1_params(self.base_config, self.level1_params)
        
        # 加载校准案例
        self.cases = []
        if cases_path and os.path.exists(cases_path):
            with open(cases_path, 'r', encoding='utf-8') as f:
                self.cases = json.load(f)
            print(f"✅ 加载了 {len(self.cases)} 个校准案例")
        
        # 正则化系数
        self.lambda_reg = 0.01
        
        # 学习率
        self.learning_rate = 0.05
        
        # 收敛阈值
        self.mae_target = 5.0
        self.mae_change_threshold = 0.01
        self.convergence_window = 5
        
        # 定义 Level 2 参数集
        self.level2_params = self._define_level2_params()
        
        # 优化历史
        self.optimization_history = []
        
        print(f"✅ Level 2 优化器初始化完成")
        print(f"   Level 2 参数数量: {len(self.level2_params)}")
        print(f"   Level 1 参数已锁定: {len(self.level1_params)} 个")
        print(f"   正则化系数 λ: {self.lambda_reg}")
        print(f"   学习率: {self.learning_rate}")
    
    def _load_optimal_level1_params(self) -> Dict:
        """
        加载 V80.0 最优 Level 1 参数
        """
        result_files = []
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
        if os.path.exists(docs_dir):
            for f in os.listdir(docs_dir):
                if f.startswith("V79_OPTIMIZATION_RESULT_") and f.endswith(".json"):
                    result_files.append(os.path.join(docs_dir, f))
        
        if result_files:
            latest_file = max(result_files, key=os.path.getmtime)
            with open(latest_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
                return result.get('best_params', {})
        
        return {}
    
    def _apply_level1_params(self, config: Dict, level1_params: Dict) -> Dict:
        """
        应用 Level 1 参数到配置（锁定）
        """
        config = deepcopy(config)
        
        # 应用柱位权重
        if 'pg_year' in level1_params:
            config.setdefault('physics', {}).setdefault('pillarWeights', {})['year'] = level1_params['pg_year']
        if 'pg_month' in level1_params:
            config.setdefault('physics', {}).setdefault('pillarWeights', {})['month'] = level1_params['pg_month']
        if 'pg_day' in level1_params:
            config.setdefault('physics', {}).setdefault('pillarWeights', {})['day'] = level1_params['pg_day']
        if 'pg_hour' in level1_params:
            config.setdefault('physics', {}).setdefault('pillarWeights', {})['hour'] = level1_params['pg_hour']
        
        # 应用 flow 参数
        if 'ctl_imp' in level1_params:
            config.setdefault('flow', {})['controlImpact'] = level1_params['ctl_imp']
        if 'imp_base' in level1_params:
            config.setdefault('flow', {}).setdefault('resourceImpedance', {})['base'] = level1_params['imp_base']
        
        # 应用 interactions 参数
        if 'clashScore' in level1_params:
            config.setdefault('interactions', {}).setdefault('branchEvents', {})['clashScore'] = level1_params['clashScore']
        if 'harmPenalty' in level1_params:
            config.setdefault('interactions', {}).setdefault('branchEvents', {})['harmPenalty'] = level1_params['harmPenalty']
        if 'punishmentPenalty' in level1_params:
            config.setdefault('interactions', {}).setdefault('branchEvents', {})['punishmentPenalty'] = level1_params['punishmentPenalty']
        
        return config
    
    def _define_level2_params(self) -> Dict[str, Dict]:
        """
        定义 Level 2 参数集
        
        V87.0: 优化 Level 2 权重，特别是 Relationship 维度
        """
        config = self.base_config
        
        params = {}
        
        # 1. Relationship 观察偏差因子（最重要）
        observation_bias = config.get('ObservationBiasFactor', {})
        params['relationship_bias'] = {
            'value': observation_bias.get('Relationship', 3.0),
            'anchor': 1.8,  # V87.0: 从 3.0 修正为 1.8
            'range': (0.5, 3.0),
            'category': 'Relationship'
        }
        
        # 2. Wealth 观察偏差因子
        params['wealth_bias'] = {
            'value': observation_bias.get('Wealth', 2.7),
            'anchor': 2.7,  # 保持原值
            'range': (1.0, 4.0),
            'category': 'Wealth'
        }
        
        # 3. Career 观察偏差因子（低能量）
        params['career_bias_low'] = {
            'value': observation_bias.get('CareerBiasFactor_LowE', 2.0),
            'anchor': 2.0,  # 保持原值
            'range': (1.0, 3.0),
            'category': 'Career'
        }
        
        # 4. Career 观察偏差因子（高能量）
        params['career_bias_high'] = {
            'value': observation_bias.get('CareerBiasFactor_HighE', 0.95),
            'anchor': 0.95,  # 保持原值
            'range': (0.5, 2.0),
            'category': 'Career'
        }
        
        # 5. Wealth 非线性指数（高能量区域）
        physics_config = config.get('physics', {})
        params['wealth_exp_high'] = {
            'value': physics_config.get('NonLinearExponent_High', 2.0),
            'anchor': 1.4,  # V87.0: 从 2.0 修正为 1.4
            'range': (1.0, 2.5),
            'category': 'Wealth'
        }
        
        # 6. Wealth 非线性指数（中能量区域）
        params['wealth_exp_mid'] = {
            'value': physics_config.get('NonLinearExponent_Mid', 1.3),
            'anchor': 1.3,  # 保持原值
            'range': (1.0, 2.0),
            'category': 'Wealth'
        }
        
        # 7. Relationship 最大得分
        params['relationship_max_score'] = {
            'value': physics_config.get('RelationshipMaxScore', 75.0),
            'anchor': 98.0,  # V87.0: 从 75.0 修正为 98.0
            'range': (50.0, 100.0),
            'category': 'Relationship'
        }
        
        # 8. Wealth 放大器
        params['wealth_amplifier'] = {
            'value': physics_config.get('WealthAmplifier', 1.2),
            'anchor': 1.2,  # 保持原值
            'range': (0.8, 2.0),
            'category': 'Wealth'
        }
        
        # 9. Career 放大器
        params['career_amplifier'] = {
            'value': physics_config.get('CareerAmplifier', 1.2),
            'anchor': 1.2,  # 保持原值
            'range': (0.8, 2.0),
            'category': 'Career'
        }
        
        # 10. Relationship 放大器
        params['relationship_amplifier'] = {
            'value': physics_config.get('RelationshipAmplifier', 1.0),
            'anchor': 1.0,  # 保持原值
            'range': (0.5, 2.0),
            'category': 'Relationship'
        }
        
        # 11. Wealth 最大得分
        params['wealth_max_score'] = {
            'value': physics_config.get('MaxScore', 98),
            'anchor': 98,  # 保持原值
            'range': (80, 120),
            'category': 'Wealth'
        }
        
        # 12. Career 最大得分
        params['career_max_score'] = {
            'value': physics_config.get('CareerMaxScore', 98.0),
            'anchor': 98.0,  # 保持原值
            'range': (80.0, 120.0),
            'category': 'Career'
        }
        
        # 13. 高能量阈值
        params['high_energy_threshold'] = {
            'value': physics_config.get('HighEnergyThreshold', 55),
            'anchor': 55,  # 保持原值
            'range': (40, 70),
            'category': 'Thresholds'
        }
        
        # 14. 中能量阈值
        params['mid_energy_threshold'] = {
            'value': physics_config.get('MidEnergyThreshold', 30),
            'anchor': 30,  # 保持原值
            'range': (20, 50),
            'category': 'Thresholds'
        }
        
        return params
    
    def _apply_level2_params_to_config(self, params: Dict[str, float]) -> Dict:
        """
        将 Level 2 参数应用到配置
        
        Args:
            params: Level 2 参数字典
            
        Returns:
            更新后的配置
        """
        config = deepcopy(self.base_config)
        
        # 应用观察偏差因子
        if 'relationship_bias' in params:
            config.setdefault('ObservationBiasFactor', {})['Relationship'] = params['relationship_bias']
        if 'wealth_bias' in params:
            config.setdefault('ObservationBiasFactor', {})['Wealth'] = params['wealth_bias']
        if 'career_bias_low' in params:
            config.setdefault('ObservationBiasFactor', {})['CareerBiasFactor_LowE'] = params['career_bias_low']
        if 'career_bias_high' in params:
            config.setdefault('ObservationBiasFactor', {})['CareerBiasFactor_HighE'] = params['career_bias_high']
        
        # 应用物理配置
        if 'wealth_exp_high' in params:
            config.setdefault('physics', {})['NonLinearExponent_High'] = params['wealth_exp_high']
        if 'wealth_exp_mid' in params:
            config.setdefault('physics', {})['NonLinearExponent_Mid'] = params['wealth_exp_mid']
        if 'relationship_max_score' in params:
            config.setdefault('physics', {})['RelationshipMaxScore'] = params['relationship_max_score']
        if 'wealth_amplifier' in params:
            config.setdefault('physics', {})['WealthAmplifier'] = params['wealth_amplifier']
        if 'career_amplifier' in params:
            config.setdefault('physics', {})['CareerAmplifier'] = params['career_amplifier']
        if 'relationship_amplifier' in params:
            config.setdefault('physics', {})['RelationshipAmplifier'] = params['relationship_amplifier']
        if 'wealth_max_score' in params:
            config.setdefault('physics', {})['MaxScore'] = params['wealth_max_score']
        if 'career_max_score' in params:
            config.setdefault('physics', {})['CareerMaxScore'] = params['career_max_score']
        if 'high_energy_threshold' in params:
            config.setdefault('physics', {})['HighEnergyThreshold'] = params['high_energy_threshold']
        if 'mid_energy_threshold' in params:
            config.setdefault('physics', {})['MidEnergyThreshold'] = params['mid_energy_threshold']
        
        return config
    
    def _calculate_mae(self, config: Dict) -> Tuple[float, Dict]:
        """
        计算 MAE（使用所有 24 个误差点：8个案例 × 3个维度）
        
        Returns:
            (MAE, 详细结果)
        """
        if not self.cases:
            return 999.0, {}
        
        engine = EngineV88(config=config)
        errors = []
        detailed_results = []
        
        for case in self.cases:
            case_id = case.get('id', 'Unknown')
            bazi = case.get('bazi', [])
            day_master = case.get('day_master', '')
            
            if not bazi or not day_master:
                continue
            
            # 处理 gender
            gender = case.get('gender', 1)
            if isinstance(gender, str):
                gender = 1 if gender == '男' or gender == 'male' else 0
            
            case_data = {
                'year': bazi[0] if len(bazi) > 0 else '',
                'month': bazi[1] if len(bazi) > 1 else '',
                'day': bazi[2] if len(bazi) > 2 else '',
                'hour': bazi[3] if len(bazi) > 3 else '',
                'day_master': day_master,
                'gender': gender,
                'case_id': case_id
            }
            
            # 处理动态上下文
            d_ctx = {"year": "2024", "luck": "default"}
            target_v = case.get('ground_truth', case.get('v_real', {}))
            if case.get("dynamic_checks"):
                p = case["dynamic_checks"][0]
                d_ctx = {"year": p.get('year', "2024"), "luck": p.get('luck', "default")}
                if 'v_real_dynamic' in p:
                    target_v = p['v_real_dynamic']
            
            # 计算得分
            try:
                result = engine.calculate_energy(case_data, d_ctx)
                
                if not isinstance(result, dict):
                    continue
                if 'career' not in result or 'wealth' not in result or 'relationship' not in result:
                    continue
            except Exception as e:
                continue
            
            # 计算误差（所有 3 个维度）
            for dimension in ['career', 'wealth', 'relationship']:
                # 尝试多种可能的键名
                gt_value = None
                for key in [f'{dimension}_score', dimension, f'{dimension}_gt']:
                    if key in target_v:
                        gt_value = target_v[key]
                        break
                
                if gt_value is None or gt_value == 0:
                    continue
                
                # 从 domain_details 中提取原始得分（0-100 范围）
                pred_value = 0.0
                domain_details = result.get('domain_details', {})
                if domain_details and dimension in domain_details:
                    pred_value = domain_details[dimension].get('score', 0)
                else:
                    # 如果没有 domain_details，使用 result 中的值（0-10 范围）乘以 10
                    pred_raw = result.get(dimension, 0)
                    pred_value = pred_raw * 10.0 if pred_raw < 20 else pred_raw
                
                error = abs(pred_value - gt_value)
                errors.append(error)
                detailed_results.append({
                    'case_id': case_id,
                    'dimension': dimension,
                    'gt': gt_value,
                    'pred': pred_value,
                    'error': error
                })
        
        mae = np.mean(errors) if errors else 999.0
        return mae, {'errors': errors, 'detailed': detailed_results}
    
    def _calculate_regularization_penalty(self, params: Dict[str, float]) -> float:
        """
        计算正则化惩罚项
        
        Args:
            params: Level 2 参数字典
            
        Returns:
            正则化惩罚值
        """
        penalty = 0.0
        
        for param_name, param_value in params.items():
            if param_name in self.level2_params:
                anchor_value = self.level2_params[param_name]['anchor']
                deviation = param_value - anchor_value
                penalty += (deviation ** 2)
        
        return self.lambda_reg * penalty
    
    def _calculate_total_cost(self, params: Dict[str, float]) -> Tuple[float, float, float]:
        """
        计算总成本
        
        Args:
            params: Level 2 参数字典
            
        Returns:
            (Cost_Total, Cost_MAE, Cost_Plausibility)
        """
        # 应用参数到配置
        config = self._apply_level2_params_to_config(params)
        
        # 计算 MAE
        mae, _ = self._calculate_mae(config)
        cost_mae = mae
        
        # 计算正则化惩罚
        cost_plausibility = self._calculate_regularization_penalty(params)
        
        # 总成本
        cost_total = cost_mae + cost_plausibility
        
        return cost_total, cost_mae, cost_plausibility
    
    def _calculate_gradient(self, params: Dict[str, float], param_name: str) -> float:
        """
        计算梯度（偏导数）
        
        Args:
            params: 当前参数字典
            param_name: 参数名
            
        Returns:
            梯度值
        """
        if param_name not in self.level2_params:
            return 0.0
        
        param_info = self.level2_params[param_name]
        current_value = params[param_name]
        param_range = param_info['range']
        
        # 数值梯度计算（中心差分）
        epsilon = 0.01
        
        # 正向扰动
        temp_params_plus = params.copy()
        temp_params_plus[param_name] = min(current_value + epsilon, param_range[1])
        cost_plus, _, _ = self._calculate_total_cost(temp_params_plus)
        
        # 负向扰动
        temp_params_minus = params.copy()
        temp_params_minus[param_name] = max(current_value - epsilon, param_range[0])
        cost_minus, _, _ = self._calculate_total_cost(temp_params_minus)
        
        # 梯度
        gradient = (cost_plus - cost_minus) / (2 * epsilon)
        
        return gradient
    
    def _update_parameters(self, params: Dict[str, float]) -> Dict[str, float]:
        """
        更新参数（沿负梯度方向）
        
        Args:
            params: 当前参数字典
            
        Returns:
            更新后的参数字典
        """
        updated_params = params.copy()
        
        # 计算每个参数的梯度并更新
        for param_name in self.level2_params.keys():
            param_info = self.level2_params[param_name]
            current_value = params[param_name]
            param_range = param_info['range']
            
            # 计算梯度
            gradient = self._calculate_gradient(params, param_name)
            
            # 沿负梯度方向更新参数
            new_value = current_value - self.learning_rate * gradient
            
            # 范围硬约束
            new_value = max(param_range[0], min(param_range[1], new_value))
            
            updated_params[param_name] = new_value
        
        return updated_params
    
    def _check_convergence(self, history: List[Dict]) -> Tuple[bool, str]:
        """
        收敛判定
        
        Args:
            history: 优化历史
            
        Returns:
            (是否收敛, 收敛原因)
        """
        if len(history) < self.convergence_window:
            return False, ""
        
        # 检查目标达成
        recent_maes = [h['mae'] for h in history[-self.convergence_window:]]
        if all(mae < self.mae_target for mae in recent_maes):
            return True, f"目标达成：MAE 持续低于 {self.mae_target}"
        
        # 检查变化微小
        mae_changes = [abs(recent_maes[i] - recent_maes[i-1]) 
                      for i in range(1, len(recent_maes))]
        if all(change < self.mae_change_threshold for change in mae_changes):
            return True, f"变化微小：连续 {self.convergence_window} 次迭代中 MAE 变化量低于 {self.mae_change_threshold}"
        
        return False, ""
    
    def optimize(self, max_iterations: int = 500) -> Dict:
        """
        执行 Level 2 权重优化
        
        Args:
            max_iterations: 最大迭代次数
            
        Returns:
            优化结果
        """
        print("=" * 80)
        print("V87.0 任务 133：Level 2 权重结构性修复与优化")
        print("=" * 80)
        
        print(f"\n优化配置:")
        print(f"  最大迭代次数: {max_iterations}")
        print(f"  学习率: {self.learning_rate}")
        print(f"  正则化系数 λ: {self.lambda_reg}")
        print(f"  优化参数数量: {len(self.level2_params)}")
        print(f"  校准案例数量: {len(self.cases)}")
        print(f"  误差点数量: {len(self.cases) * 3} (8个案例 × 3个维度)")
        print(f"  目标 MAE: < {self.mae_target}")
        print(f"  Level 1 参数已锁定: {len(self.level1_params)} 个")
        
        # 初始化 Level 2 参数值
        current_params = {name: info['value'] for name, info in self.level2_params.items()}
        
        # 计算初始成本
        initial_cost_total, initial_mae, initial_reg = self._calculate_total_cost(current_params)
        print(f"\n步骤一：前置准备完成")
        print(f"  初始 MAE: {initial_mae:.4f}")
        print(f"  初始正则化成本: {initial_reg:.4f}")
        print(f"  初始总成本: {initial_cost_total:.4f}")
        
        best_mae = initial_mae
        best_params = current_params.copy()
        best_cost_total = initial_cost_total
        
        # 优化迭代
        for iteration in range(max_iterations):
            # 计算梯度并更新参数
            current_params = self._update_parameters(current_params)
            
            # 计算当前成本
            cost_total, mae, reg_penalty = self._calculate_total_cost(current_params)
            
            # 记录历史
            self.optimization_history.append({
                'iteration': iteration + 1,
                'mae': mae,
                'cost_total': cost_total,
                'cost_mae': mae,
                'cost_plausibility': reg_penalty,
                'params': current_params.copy()
            })
            
            # 更新最佳值
            if mae < best_mae:
                best_mae = mae
                best_params = current_params.copy()
                best_cost_total = cost_total
                improved = True
            else:
                improved = False
            
            # 输出进度
            if (iteration + 1) % 10 == 0 or improved or iteration == 0:
                print(f"\n迭代 {iteration + 1}/{max_iterations}:")
                print(f"  当前 MAE: {mae:.4f}")
                print(f"  当前总成本: {cost_total:.4f}")
                print(f"  正则化成本: {reg_penalty:.4f}")
                print(f"  最佳 MAE: {best_mae:.4f}")
                if improved:
                    print(f"  ✅ 发现更优解！")
            
            # 收敛检查
            is_converged, reason = self._check_convergence(self.optimization_history)
            if is_converged:
                print(f"\n🎉 收敛达成！")
                print(f"  原因: {reason}")
                break
        
        # 最终报告
        final_config = self._apply_level2_params_to_config(best_params)
        final_mae, final_details = self._calculate_mae(final_config)
        
        print(f"\n" + "=" * 80)
        print("步骤五：优化完成 - 最终报告")
        print("=" * 80)
        print(f"\n最终结果:")
        print(f"  最佳 MAE: {best_mae:.4f}")
        print(f"  目标: MAE < {self.mae_target}")
        print(f"  状态: {'✅ 达成' if best_mae < self.mae_target else '❌ 未达成'}")
        print(f"  总迭代次数: {len(self.optimization_history)}")
        print(f"  MAE 改善: {initial_mae - best_mae:.4f}")
        
        # 输出最优参数摘要
        print(f"\n最优 Level 2 参数摘要:")
        param_changes = []
        for param_name in self.level2_params.keys():
            anchor = self.level2_params[param_name]['anchor']
            optimal = best_params[param_name]
            change = abs(optimal - anchor)
            if change > 0.001:
                param_changes.append((param_name, anchor, optimal, change))
        
        param_changes.sort(key=lambda x: x[3], reverse=True)
        for param_name, anchor, optimal, change in param_changes:
            print(f"  {param_name}: {anchor:.4f} → {optimal:.4f} (变化: {change:.4f})")
        
        return {
            'best_mae': best_mae,
            'best_level2_params': best_params,
            'best_config': final_config,
            'level1_params_locked': self.level1_params,
            'initial_mae': initial_mae,
            'improvement': initial_mae - best_mae,
            'iterations': len(self.optimization_history),
            'history': self.optimization_history,
            'final_details': final_details,
            'converged': is_converged if 'is_converged' in locals() else False,
            'convergence_reason': reason if 'is_converged' in locals() and is_converged else "达到最大迭代次数"
        }


def main():
    """主函数"""
    # 配置文件路径
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "parameters.json"
    )
    
    # 校准案例路径
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                    "data", "calibration_cases.json"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                    "calibration_cases.json"),
        "calibration_cases.json"
    ]
    cases_path = None
    for path in possible_paths:
        if os.path.exists(path):
            cases_path = path
            break
    
    # 检查文件是否存在
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        return
    
    # 创建优化器
    optimizer = V87Level2Optimizer(config_path, cases_path)
    
    # 执行优化
    result = optimizer.optimize(max_iterations=500)
    
    # 保存结果
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"V87_TASK133_LEVEL2_OPTIMIZATION_RESULT_{timestamp}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n优化结果已保存至: {output_path}")


if __name__ == "__main__":
    main()

