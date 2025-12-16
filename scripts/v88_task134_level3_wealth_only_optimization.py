"""
V88.0 任务 134：Level 3 动态权重优化（严格财富隔离）
==========================================
目标：优化 Level 3 动态权重（LuckPillarWeight, AnnualPillarWeight），
      严格只计算 Wealth 维度的 MAE，使 MAE_Wealth < 5.0

策略：
1. 锁定 Level 2 所有参数为 V87.0 最优值
2. 严格隔离 MAE：只使用 Wealth 维度的误差点
3. 使用 8 个静态案例的 Wealth 维度 + 3 个动态案例（C15-C17）
4. 只优化 Level 3 参数：LuckPillarWeight, AnnualPillarWeight
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


class V88Level3WealthOptimizer:
    """
    V88.0 Level 3 动态权重优化器（严格财富隔离）
    
    只优化 Level 3 动态权重，只计算 Wealth 维度的 MAE
    """
    
    def __init__(self, config_path: str, static_cases_path: str = None, 
                 dynamic_cases: List[Dict] = None, optimal_level2_params: Dict = None):
        """
        初始化优化器
        
        Args:
            config_path: 配置文件路径
            static_cases_path: 静态校准案例路径（8 个案例）
            dynamic_cases: 动态案例列表（C15-C17）
            optimal_level2_params: V87.0 最优 Level 2 参数（用于锁定）
        """
        self.config_path = config_path
        self.static_cases_path = static_cases_path
        self.dynamic_cases = dynamic_cases or []
        
        # 加载配置
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.base_config = json.load(f)
        
        # 加载 V87.0 最优 Level 2 参数
        if optimal_level2_params:
            self.level2_params = optimal_level2_params
        else:
            self.level2_params = self._load_optimal_level2_params()
        
        # 应用 Level 2 参数到配置（锁定）
        self.base_config = self._apply_level2_params(self.base_config, self.level2_params)
        
        # 加载静态校准案例
        self.static_cases = []
        if static_cases_path and os.path.exists(static_cases_path):
            with open(static_cases_path, 'r', encoding='utf-8') as f:
                self.static_cases = json.load(f)
            print(f"✅ 加载了 {len(self.static_cases)} 个静态校准案例")
        
        # 合并所有案例（静态 + 动态）
        self.all_cases = self.static_cases + self.dynamic_cases
        print(f"✅ 总案例数: {len(self.all_cases)} (静态: {len(self.static_cases)}, 动态: {len(self.dynamic_cases)})")
        
        # 正则化系数
        self.lambda_reg = 0.01
        
        # 学习率
        self.learning_rate = 0.05
        
        # 收敛阈值
        self.mae_target = 5.0
        self.mae_change_threshold = 0.01
        self.convergence_window = 5
        
        # 定义 Level 3 参数集
        self.level3_params = self._define_level3_params()
        
        # 优化历史
        self.optimization_history = []
        
        print(f"✅ Level 3 优化器初始化完成")
        print(f"   Level 3 参数数量: {len(self.level3_params)}")
        print(f"   Level 2 参数已锁定: {len(self.level2_params)} 个")
        print(f"   正则化系数 λ: {self.lambda_reg}")
        print(f"   学习率: {self.learning_rate}")
        print(f"   ⚠️  严格财富隔离：只计算 Wealth 维度的 MAE")
    
    def _load_optimal_level2_params(self) -> Dict:
        """
        加载 V87.0 最优 Level 2 参数
        """
        result_files = []
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
        if os.path.exists(docs_dir):
            for f in os.listdir(docs_dir):
                if f.startswith("V87_TASK133_LEVEL2_OPTIMIZATION_RESULT_") and f.endswith(".json"):
                    result_files.append(os.path.join(docs_dir, f))
        
        if result_files:
            latest_file = max(result_files, key=os.path.getmtime)
            with open(latest_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
                return result.get('best_level2_params', {})
        
        return {}
    
    def _apply_level2_params(self, config: Dict, level2_params: Dict) -> Dict:
        """
        应用 Level 2 参数到配置（锁定）
        """
        config = deepcopy(config)
        
        # 应用观察偏差因子
        if 'relationship_bias' in level2_params:
            config.setdefault('ObservationBiasFactor', {})['Relationship'] = level2_params['relationship_bias']
        if 'wealth_bias' in level2_params:
            config.setdefault('ObservationBiasFactor', {})['Wealth'] = level2_params['wealth_bias']
        if 'career_bias_low' in level2_params:
            config.setdefault('ObservationBiasFactor', {})['CareerBiasFactor_LowE'] = level2_params['career_bias_low']
        if 'career_bias_high' in level2_params:
            config.setdefault('ObservationBiasFactor', {})['CareerBiasFactor_HighE'] = level2_params['career_bias_high']
        
        # 应用物理配置
        if 'wealth_exp_high' in level2_params:
            config.setdefault('physics', {})['NonLinearExponent_High'] = level2_params['wealth_exp_high']
        if 'wealth_exp_mid' in level2_params:
            config.setdefault('physics', {})['NonLinearExponent_Mid'] = level2_params['wealth_exp_mid']
        if 'relationship_max_score' in level2_params:
            config.setdefault('physics', {})['RelationshipMaxScore'] = level2_params['relationship_max_score']
        if 'wealth_amplifier' in level2_params:
            config.setdefault('physics', {})['WealthAmplifier'] = level2_params['wealth_amplifier']
        if 'career_amplifier' in level2_params:
            config.setdefault('physics', {})['CareerAmplifier'] = level2_params['career_amplifier']
        if 'relationship_amplifier' in level2_params:
            config.setdefault('physics', {})['RelationshipAmplifier'] = level2_params['relationship_amplifier']
        if 'wealth_max_score' in level2_params:
            config.setdefault('physics', {})['MaxScore'] = level2_params['wealth_max_score']
        if 'career_max_score' in level2_params:
            config.setdefault('physics', {})['CareerMaxScore'] = level2_params['career_max_score']
        if 'high_energy_threshold' in level2_params:
            config.setdefault('physics', {})['HighEnergyThreshold'] = level2_params['high_energy_threshold']
        if 'mid_energy_threshold' in level2_params:
            config.setdefault('physics', {})['MidEnergyThreshold'] = level2_params['mid_energy_threshold']
        
        return config
    
    def _define_level3_params(self) -> Dict[str, Dict]:
        """
        定义 Level 3 参数集（只优化动态权重）
        """
        config = self.base_config
        
        params = {}
        
        # 1. LuckPillarWeight（大运权重）
        spacetime = config.get('physics', {}).get('SpacetimeCorrector', {})
        params['luck_pillar_weight'] = {
            'value': spacetime.get('LuckPillarWeight', 0.6),
            'anchor': 0.6,  # 保持原值
            'range': (0.0, 1.0),
            'category': 'Level3'
        }
        
        # 2. AnnualPillarWeight（流年权重）
        params['annual_pillar_weight'] = {
            'value': spacetime.get('AnnualPillarWeight', 0.4),
            'anchor': 0.4,  # 保持原值
            'range': (0.0, 1.0),
            'category': 'Level3'
        }
        
        return params
    
    def _apply_level3_params_to_config(self, params: Dict[str, float]) -> Dict:
        """
        将 Level 3 参数应用到配置
        
        Args:
            params: Level 3 参数字典
            
        Returns:
            更新后的配置
        """
        config = deepcopy(self.base_config)
        
        # 应用 Level 3 参数
        if 'luck_pillar_weight' in params:
            config.setdefault('physics', {}).setdefault('SpacetimeCorrector', {})['LuckPillarWeight'] = params['luck_pillar_weight']
        if 'annual_pillar_weight' in params:
            config.setdefault('physics', {}).setdefault('SpacetimeCorrector', {})['AnnualPillarWeight'] = params['annual_pillar_weight']
        
        return config
    
    def _calculate_mae_wealth_only(self, config: Dict) -> Tuple[float, Dict]:
        """
        计算 MAE（严格只计算 Wealth 维度）
        
        Returns:
            (MAE_Wealth, 详细结果)
        """
        if not self.all_cases:
            return 999.0, {}
        
        engine = EngineV88(config=config)
        errors = []
        detailed_results = []
        
        for case in self.all_cases:
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
            
            # 对于动态案例，使用特定的年份和流年
            if case.get("dynamic_checks") or case.get("target_year"):
                if case.get("dynamic_checks"):
                    p = case["dynamic_checks"][0]
                    d_ctx = {"year": p.get('year', "2024"), "luck": p.get('luck', "default")}
                    if 'v_real_dynamic' in p:
                        target_v = p['v_real_dynamic']
                elif case.get("target_year"):
                    d_ctx = {"year": str(case.get("target_year")), "luck": "default"}
                    if 'target_wealth' in case:
                        target_v = {'wealth_score': case.get('target_wealth')}
            
            # 计算得分
            try:
                result = engine.calculate_energy(case_data, d_ctx)
                
                if not isinstance(result, dict):
                    continue
                if 'wealth' not in result:
                    continue
            except Exception as e:
                continue
            
            # 只计算 Wealth 维度的误差
            gt_value = None
            for key in ['wealth_score', 'wealth', 'wealth_gt']:
                if key in target_v:
                    gt_value = target_v[key]
                    break
            
            if gt_value is None or gt_value == 0:
                continue
            
            # 从 domain_details 中提取原始得分（0-100 范围）
            pred_value = 0.0
            domain_details = result.get('domain_details', {})
            if domain_details and 'wealth' in domain_details:
                pred_value = domain_details['wealth'].get('score', 0)
            else:
                # 如果没有 domain_details，使用 result 中的值（0-10 范围）乘以 10
                pred_raw = result.get('wealth', 0)
                pred_value = pred_raw * 10.0 if pred_raw < 20 else pred_raw
            
            error = abs(pred_value - gt_value)
            errors.append(error)
            detailed_results.append({
                'case_id': case_id,
                'dimension': 'wealth',
                'gt': gt_value,
                'pred': pred_value,
                'error': error,
                'year': d_ctx.get('year', 'N/A')
            })
        
        mae = np.mean(errors) if errors else 999.0
        return mae, {'errors': errors, 'detailed': detailed_results}
    
    def _calculate_regularization_penalty(self, params: Dict[str, float]) -> float:
        """
        计算正则化惩罚项
        
        Args:
            params: Level 3 参数字典
            
        Returns:
            正则化惩罚值
        """
        penalty = 0.0
        
        for param_name, param_value in params.items():
            if param_name in self.level3_params:
                anchor_value = self.level3_params[param_name]['anchor']
                deviation = param_value - anchor_value
                penalty += (deviation ** 2)
        
        return self.lambda_reg * penalty
    
    def _calculate_total_cost(self, params: Dict[str, float]) -> Tuple[float, float, float]:
        """
        计算总成本（只考虑 Wealth 维度）
        
        Args:
            params: Level 3 参数字典
            
        Returns:
            (Cost_Total, Cost_MAE, Cost_Plausibility)
        """
        # 应用参数到配置
        config = self._apply_level3_params_to_config(params)
        
        # 计算 MAE（只计算 Wealth）
        mae, _ = self._calculate_mae_wealth_only(config)
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
        if param_name not in self.level3_params:
            return 0.0
        
        param_info = self.level3_params[param_name]
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
        for param_name in self.level3_params.keys():
            param_info = self.level3_params[param_name]
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
            return True, f"目标达成：MAE_Wealth 持续低于 {self.mae_target}"
        
        # 检查变化微小
        mae_changes = [abs(recent_maes[i] - recent_maes[i-1]) 
                      for i in range(1, len(recent_maes))]
        if all(change < self.mae_change_threshold for change in mae_changes):
            return True, f"变化微小：连续 {self.convergence_window} 次迭代中 MAE 变化量低于 {self.mae_change_threshold}"
        
        return False, ""
    
    def optimize(self, max_iterations: int = 500) -> Dict:
        """
        执行 Level 3 动态权重优化（严格财富隔离）
        
        Args:
            max_iterations: 最大迭代次数
            
        Returns:
            优化结果
        """
        print("=" * 80)
        print("V88.0 任务 134：Level 3 动态权重优化（严格财富隔离）")
        print("=" * 80)
        
        print(f"\n优化配置:")
        print(f"  最大迭代次数: {max_iterations}")
        print(f"  学习率: {self.learning_rate}")
        print(f"  正则化系数 λ: {self.lambda_reg}")
        print(f"  优化参数数量: {len(self.level3_params)}")
        print(f"  静态案例数量: {len(self.static_cases)}")
        print(f"  动态案例数量: {len(self.dynamic_cases)}")
        print(f"  总案例数量: {len(self.all_cases)}")
        print(f"  ⚠️  严格财富隔离：只计算 Wealth 维度的误差点")
        print(f"  目标 MAE_Wealth: < {self.mae_target}")
        print(f"  Level 2 参数已锁定: {len(self.level2_params)} 个")
        
        # 初始化 Level 3 参数值
        current_params = {name: info['value'] for name, info in self.level3_params.items()}
        
        # 计算初始成本
        initial_cost_total, initial_mae, initial_reg = self._calculate_total_cost(current_params)
        print(f"\n步骤一：前置准备完成")
        print(f"  初始 MAE_Wealth: {initial_mae:.4f}")
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
                print(f"  当前 MAE_Wealth: {mae:.4f}")
                print(f"  当前总成本: {cost_total:.4f}")
                print(f"  正则化成本: {reg_penalty:.4f}")
                print(f"  最佳 MAE_Wealth: {best_mae:.4f}")
                if improved:
                    print(f"  ✅ 发现更优解！")
            
            # 收敛检查
            is_converged, reason = self._check_convergence(self.optimization_history)
            if is_converged:
                print(f"\n🎉 收敛达成！")
                print(f"  原因: {reason}")
                break
        
        # 最终报告
        final_config = self._apply_level3_params_to_config(best_params)
        final_mae, final_details = self._calculate_mae_wealth_only(final_config)
        
        print(f"\n" + "=" * 80)
        print("步骤五：优化完成 - 最终报告")
        print("=" * 80)
        print(f"\n最终结果:")
        print(f"  最佳 MAE_Wealth: {best_mae:.4f}")
        print(f"  目标: MAE_Wealth < {self.mae_target}")
        print(f"  状态: {'✅ 达成' if best_mae < self.mae_target else '❌ 未达成'}")
        print(f"  总迭代次数: {len(self.optimization_history)}")
        print(f"  MAE_Wealth 改善: {initial_mae - best_mae:.4f}")
        
        # 输出最优参数摘要
        print(f"\n最优 Level 3 参数摘要:")
        for param_name in self.level3_params.keys():
            anchor = self.level3_params[param_name]['anchor']
            optimal = best_params[param_name]
            change = abs(optimal - anchor)
            print(f"  {param_name}: {anchor:.4f} → {optimal:.4f} (变化: {change:.4f})")
        
        return {
            'best_mae_wealth': best_mae,
            'best_level3_params': best_params,
            'best_config': final_config,
            'level2_params_locked': self.level2_params,
            'initial_mae_wealth': initial_mae,
            'improvement': initial_mae - best_mae,
            'iterations': len(self.optimization_history),
            'history': self.optimization_history,
            'final_details': final_details,
            'converged': is_converged if 'is_converged' in locals() else False,
            'convergence_reason': reason if 'is_converged' in locals() and is_converged else "达到最大迭代次数"
        }


def create_dynamic_cases() -> List[Dict]:
    """
    创建动态案例（C15-C17）
    
    C15: 李嘉诚 - 1958年（戊戌流年）财富爆发
    C16: 比尔·盖茨 - 1975年（乙卯流年）微软成立
    C17: 破财案例 - 2007年（丁亥流年）投资失利
    """
    cases = []
    
    # C15: 李嘉诚
    cases.append({
        'id': 'C15',
        'bazi': ['丁', '卯', '未', '辰', '庚', '辰', '庚', '辰'],  # 丁卯 丁未 庚辰 庚辰
        'day_master': '庚',
        'gender': 1,
        'target_year': 1958,
        'target_wealth': 95,  # 财富爆发，目标值较高
        'description': '李嘉诚 - 1958年塑胶花厂腾飞，财富爆发元年'
    })
    
    # C16: 比尔·盖茨
    cases.append({
        'id': 'C16',
        'bazi': ['乙', '未', '丁', '亥', '丙', '午', '甲', '午'],  # 乙未 丁亥 丙午 甲午
        'day_master': '丙',
        'gender': 1,
        'target_year': 1975,
        'target_wealth': 90,  # 微软成立，财富奠定基石
        'description': '比尔·盖茨 - 1975年微软成立，财富奠定基石'
    })
    
    # C17: 破财案例
    cases.append({
        'id': 'C17',
        'bazi': ['辛', '丑', '戊', '戌', '癸', '卯', '癸', '亥'],  # 辛丑 戊戌 癸卯 癸亥
        'day_master': '癸',
        'gender': 1,
        'target_year': 2007,
        'target_wealth': 20,  # 投资失利，财富大幅下降
        'description': '破财案例 - 2007年重大投资失利/破财'
    })
    
    return cases


def main():
    """主函数"""
    # 配置文件路径
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "parameters.json"
    )
    
    # 静态校准案例路径
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                    "data", "calibration_cases.json"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                    "calibration_cases.json"),
        "calibration_cases.json"
    ]
    static_cases_path = None
    for path in possible_paths:
        if os.path.exists(path):
            static_cases_path = path
            break
    
    # 检查文件是否存在
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        return
    
    # 创建动态案例
    dynamic_cases = create_dynamic_cases()
    print(f"✅ 创建了 {len(dynamic_cases)} 个动态案例")
    
    # 创建优化器
    optimizer = V88Level3WealthOptimizer(config_path, static_cases_path, dynamic_cases)
    
    # 执行优化
    result = optimizer.optimize(max_iterations=500)
    
    # 保存结果
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"V88_TASK134_LEVEL3_WEALTH_OPTIMIZATION_RESULT_{timestamp}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n优化结果已保存至: {output_path}")


if __name__ == "__main__":
    main()

