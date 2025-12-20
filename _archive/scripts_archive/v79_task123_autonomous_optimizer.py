"""
V79.0 Task 123: 自主优化器（基于V32.0锚点）
===========================================
使用正则化LSL算法，优化Level 1参数，目标MAE < 5.0
"""

import sys
import os
import json
import io
import numpy as np
from typing import Dict, List, Tuple, Any
from copy import deepcopy

# Fix Windows encoding issue
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.getcwd())

from core.engine_v88 import EngineV88

class V79AutonomousOptimizer:
    """
    V79.0 自主优化器
    基于V32.0参数锚点，使用正则化优化算法
    """
    
    def __init__(self, config_path: str, cases_path: str = None):
        """
        初始化优化器
        
        Args:
            config_path: 配置文件路径
            cases_path: 校准案例路径（可选）
        """
        self.config_path = config_path
        self.cases_path = cases_path
        
        # 加载V32.0锚点配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.anchor_config = json.load(f)
        
        # 加载校准案例
        self.cases = []
        if cases_path and os.path.exists(cases_path):
            with open(cases_path, 'r', encoding='utf-8') as f:
                self.cases = json.load(f)
        
        # TGD初始值（作为优化锚点）
        self.tgd_anchor = {
            'T_Main': 7.5,
            'T_Stem': 5.0,
            'T_Mid': 3.0,
            'T_Minor': 1.5
        }
        
        # 定义Level 1参数集（约45个参数）
        self.level1_params = self._define_level1_params()
        
        # 优化历史
        self.optimization_history = []
        
    def _define_level1_params(self) -> Dict[str, Dict]:
        """
        定义Level 1参数集（约45个参数）
        
        Returns:
            参数字典，包含参数名、当前值、范围、锚点值
        """
        config = self.anchor_config
        
        params = {}
        
        # 1. 基础场域（Physics）- 4个参数
        pillar_weights = config.get('physics', {}).get('pillarWeights', {})
        params['pg_year'] = {
            'value': pillar_weights.get('year', 1.0),
            'anchor': pillar_weights.get('year', 1.0),
            'range': (0.5, 1.5),
            'category': 'Physics'
        }
        params['pg_month'] = {
            'value': pillar_weights.get('month', 1.8),
            'anchor': pillar_weights.get('month', 1.8),
            'range': (0.5, 2.0),
            'category': 'Physics'
        }
        params['pg_day'] = {
            'value': pillar_weights.get('day', 1.5),
            'anchor': pillar_weights.get('day', 1.5),
            'range': (0.5, 1.5),
            'category': 'Physics'
        }
        params['pg_hour'] = {
            'value': pillar_weights.get('hour', 1.2),
            'anchor': pillar_weights.get('hour', 1.2),
            'range': (0.5, 1.5),
            'category': 'Physics'
        }
        
        # 2. 粒子动态（Structure）- 3个参数
        # 注意：same_pill在config中可能不存在，使用默认值
        params['same_pill'] = {
            'value': 2.5,
            'anchor': 2.5,
            'range': (1.0, 2.0),
            'category': 'Structure'
        }
        params['root_w'] = {
            'value': 1.0,
            'anchor': 1.0,
            'range': (0.5, 2.0),
            'category': 'Structure'
        }
        params['exposed_b'] = {
            'value': 1.5,
            'anchor': 1.5,
            'range': (1.0, 3.0),
            'category': 'Structure'
        }
        
        # 3. 几何交互（Interactions）- 10个参数
        branch_events = config.get('interactions', {}).get('branchEvents', {})
        params['clashScore'] = {
            'value': branch_events.get('clashScore', -3.0),
            'anchor': branch_events.get('clashScore', -3.0),
            'range': (-20.0, 0.0),
            'category': 'Interactions'
        }
        params['harmPenalty'] = {
            'value': branch_events.get('harmPenalty', -2.0),
            'anchor': branch_events.get('harmPenalty', -2.0),
            'range': (-20.0, 0.0),
            'category': 'Interactions'
        }
        params['punishmentPenalty'] = {
            'value': branch_events.get('punishmentPenalty', -3.0),
            'anchor': branch_events.get('punishmentPenalty', -3.0),
            'range': (-20.0, 0.0),
            'category': 'Interactions'
        }
        params['clashDamping'] = {
            'value': branch_events.get('clashDamping', 0.7),
            'anchor': branch_events.get('clashDamping', 0.7),
            'range': (0.1, 1.0),
            'category': 'Interactions'
        }
        
        combo_physics = config.get('interactions', {}).get('comboPhysics', {})
        params['trineBonus'] = {
            'value': combo_physics.get('trineBonus', 1.2),
            'anchor': combo_physics.get('trineBonus', 1.2),
            'range': (1.0, 3.0),
            'category': 'Interactions'
        }
        params['halfBonus'] = {
            'value': combo_physics.get('halfBonus', 1.5),
            'anchor': combo_physics.get('halfBonus', 1.5),
            'range': (1.0, 3.0),
            'category': 'Interactions'
        }
        params['archBonus'] = {
            'value': combo_physics.get('archBonus', 1.1),
            'anchor': combo_physics.get('archBonus', 1.1),
            'range': (1.0, 3.0),
            'category': 'Interactions'
        }
        params['directionalBonus'] = {
            'value': combo_physics.get('directionalBonus', 1.3),
            'anchor': combo_physics.get('directionalBonus', 1.3),
            'range': (1.0, 3.0),
            'category': 'Interactions'
        }
        params['resolutionCost'] = {
            'value': combo_physics.get('resolutionCost', 0.4),
            'anchor': combo_physics.get('resolutionCost', 0.4),
            'range': (0.0, 0.5),
            'category': 'Interactions'
        }
        
        # 六合加成（从代码中推断，默认5.0）
        params['sixHarmony'] = {
            'value': 5.0,
            'anchor': 5.0,
            'range': (0.0, 20.0),
            'category': 'Interactions'
        }
        
        # 4. 能量流转（Flow）- 7个参数
        flow_config = config.get('flow', {})
        resource_impedance = flow_config.get('resourceImpedance', {})
        params['imp_base'] = {
            'value': resource_impedance.get('base', 0.20),
            'anchor': resource_impedance.get('base', 0.20),
            'range': (0.0, 0.9),
            'category': 'Flow'
        }
        params['imp_weak'] = {
            'value': resource_impedance.get('weaknessPenalty', 0.75),
            'anchor': resource_impedance.get('weaknessPenalty', 0.75),
            'range': (0.0, 1.0),
            'category': 'Flow'
        }
        
        output_viscosity = flow_config.get('outputViscosity', {})
        params['vis_rate'] = {
            'value': output_viscosity.get('maxDrainRate', 0.35),
            'anchor': output_viscosity.get('maxDrainRate', 0.35),
            'range': (0.1, 1.0),
            'category': 'Flow'
        }
        params['vis_fric'] = {
            'value': output_viscosity.get('drainFriction', 0.3),
            'anchor': output_viscosity.get('drainFriction', 0.3),
            'range': (0.0, 0.5),
            'category': 'Flow'
        }
        params['vis_visc'] = {
            'value': output_viscosity.get('viscosity', 0.95),
            'anchor': output_viscosity.get('viscosity', 0.95),
            'range': (0.0, 1.0),
            'category': 'Flow'
        }
        
        params['ctl_imp'] = {
            'value': flow_config.get('controlImpact', 1.25),
            'anchor': flow_config.get('controlImpact', 1.25),
            'range': (0.1, 2.0),  # 扩展范围以允许优化
            'category': 'Flow'
        }
        
        params['sys_ent'] = {
            'value': 0.05,
            'anchor': 0.05,
            'range': (0.0, 0.2),
            'category': 'Flow'
        }
        
        # 5. TGD参数（4个）
        for tgd_name, tgd_value in self.tgd_anchor.items():
            params[tgd_name] = {
                'value': tgd_value,
                'anchor': tgd_value,
                'range': (tgd_value * 0.5, tgd_value * 1.5),  # ±50%范围
                'category': 'TGD'
            }
        
        # 6. 其他Level 1参数
        # 能量阈值
        physics_config = config.get('physics', {})
        params['energy_strong'] = {
            'value': 3.5,  # 默认值
            'anchor': 3.5,
            'range': (2.0, 5.0),
            'category': 'Thresholds'
        }
        params['energy_weak'] = {
            'value': 2.0,  # 默认值
            'anchor': 2.0,
            'range': (1.0, 3.0),
            'category': 'Thresholds'
        }
        
        # 墓库物理
        vault_physics = config.get('interactions', {}).get('vaultPhysics', {})
        params['vp_threshold'] = {
            'value': vault_physics.get('threshold', 15.0),
            'anchor': vault_physics.get('threshold', 15.0),
            'range': (10.0, 50.0),
            'category': 'Vault'
        }
        params['vp_openBonus'] = {
            'value': vault_physics.get('openBonus', 1.3),
            'anchor': vault_physics.get('openBonus', 1.3),
            'range': (1.0, 3.0),
            'category': 'Vault'
        }
        params['vp_sealedPenalty'] = {
            'value': vault_physics.get('sealedPenalty', -5.0),
            'anchor': vault_physics.get('sealedPenalty', -5.0),
            'range': (-10.0, 0.0),
            'category': 'Vault'
        }
        
        # 基础事件分数（从config_rules推断）
        params['score_skull_crash'] = {
            'value': -50.0,
            'anchor': -50.0,
            'range': (-100.0, 0.0),
            'category': 'Events'
        }
        params['score_treasury_bonus'] = {
            'value': 20.0,
            'anchor': 20.0,
            'range': (0.0, 50.0),
            'category': 'Events'
        }
        params['score_treasury_penalty'] = {
            'value': -20.0,
            'anchor': -20.0,
            'range': (-50.0, 0.0),
            'category': 'Events'
        }
        params['score_general_open'] = {
            'value': 5.0,
            'anchor': 5.0,
            'range': (0.0, 20.0),
            'category': 'Events'
        }
        params['score_sanhe_bonus'] = {
            'value': 10.0,
            'anchor': 10.0,
            'range': (0.0, 30.0),
            'category': 'Events'
        }
        params['score_liuhe_bonus'] = {
            'value': 5.0,
            'anchor': 5.0,
            'range': (0.0, 20.0),
            'category': 'Events'
        }
        
        return params
    
    def _calculate_mae(self, config: Dict) -> Tuple[float, Dict]:
        """
        计算当前配置的MAE
        
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
            v_real = case.get('v_real', {})
            
            if not bazi or not day_master:
                continue
            
            # 构建case_data
            case_data = {
                'year': bazi[0] if len(bazi) > 0 else '',
                'month': bazi[1] if len(bazi) > 1 else '',
                'day': bazi[2] if len(bazi) > 2 else '',
                'hour': bazi[3] if len(bazi) > 3 else '',
                'day_master': day_master,
                'gender': case.get('gender', 1),
                'case_id': case_id
            }
            
            # 计算得分
            result = engine.calculate_energy(case_data)
            
            # 计算误差
            for dimension in ['career', 'wealth', 'relationship']:
                gt_key = f'{dimension}_score'
                gt_value = v_real.get(gt_key, v_real.get(dimension, 0))
                pred_value = result.get(dimension, 0.0) * 10.0  # 转换为原始得分
                
                if gt_value > 0:
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
    
    def _apply_params_to_config(self, params: Dict[str, float]) -> Dict:
        """
        将优化后的参数应用到配置
        
        Args:
            params: 参数字典 {param_name: value}
            
        Returns:
            更新后的配置
        """
        config = deepcopy(self.anchor_config)
        
        # 应用参数到配置
        for param_name, param_value in params.items():
            if param_name.startswith('pg_'):
                pillar = param_name.split('_')[1]
                config.setdefault('physics', {}).setdefault('pillarWeights', {})[pillar] = param_value
            elif param_name == 'clashScore':
                config.setdefault('interactions', {}).setdefault('branchEvents', {})['clashScore'] = param_value
            elif param_name == 'harmPenalty':
                config.setdefault('interactions', {}).setdefault('branchEvents', {})['harmPenalty'] = param_value
            elif param_name == 'punishmentPenalty':
                config.setdefault('interactions', {}).setdefault('branchEvents', {})['punishmentPenalty'] = param_value
            elif param_name == 'clashDamping':
                config.setdefault('interactions', {}).setdefault('branchEvents', {})['clashDamping'] = param_value
            elif param_name in ['trineBonus', 'halfBonus', 'archBonus', 'directionalBonus', 'resolutionCost']:
                config.setdefault('interactions', {}).setdefault('comboPhysics', {})[param_name] = param_value
            elif param_name == 'imp_base':
                config.setdefault('flow', {}).setdefault('resourceImpedance', {})['base'] = param_value
            elif param_name == 'imp_weak':
                config.setdefault('flow', {}).setdefault('resourceImpedance', {})['weaknessPenalty'] = param_value
            elif param_name == 'vis_rate':
                config.setdefault('flow', {}).setdefault('outputViscosity', {})['maxDrainRate'] = param_value
            elif param_name == 'vis_fric':
                config.setdefault('flow', {}).setdefault('outputViscosity', {})['drainFriction'] = param_value
            elif param_name == 'vis_visc':
                config.setdefault('flow', {}).setdefault('outputViscosity', {})['viscosity'] = param_value
            elif param_name == 'ctl_imp':
                config.setdefault('flow', {})['controlImpact'] = param_value
            elif param_name == 'vp_threshold':
                config.setdefault('interactions', {}).setdefault('vaultPhysics', {})['threshold'] = param_value
            elif param_name == 'vp_openBonus':
                config.setdefault('interactions', {}).setdefault('vaultPhysics', {})['openBonus'] = param_value
            elif param_name == 'vp_sealedPenalty':
                config.setdefault('interactions', {}).setdefault('vaultPhysics', {})['sealedPenalty'] = param_value
        
        return config
    
    def _regularization_penalty(self, params: Dict[str, float]) -> float:
        """
        计算正则化惩罚项
        
        Args:
            params: 参数字典
            
        Returns:
            正则化惩罚值
        """
        penalty = 0.0
        lambda_reg = 0.01  # 正则化系数
        
        for param_name, param_value in params.items():
            if param_name in self.level1_params:
                anchor_value = self.level1_params[param_name]['anchor']
                # L2正则化：惩罚偏离锚点的值
                deviation = param_value - anchor_value
                penalty += lambda_reg * (deviation ** 2)
        
        return penalty
    
    def _objective_function(self, params: Dict[str, float]) -> float:
        """
        目标函数：MAE + 正则化惩罚
        
        Args:
            params: 参数字典
            
        Returns:
            目标函数值
        """
        # 应用参数到配置
        config = self._apply_params_to_config(params)
        
        # 计算MAE
        mae, _ = self._calculate_mae(config)
        
        # 计算正则化惩罚
        reg_penalty = self._regularization_penalty(params)
        
        # 总目标函数
        objective = mae + reg_penalty
        
        return objective
    
    def optimize(self, max_iterations: int = 50, learning_rate: float = 0.01) -> Dict:
        """
        执行自主优化
        
        Args:
            max_iterations: 最大迭代次数
            learning_rate: 学习率
            
        Returns:
            优化结果
        """
        print("=" * 80)
        print("V79.0 Task 123: 自主优化器启动")
        print("=" * 80)
        
        print(f"\n优化配置:")
        print(f"  最大迭代次数: {max_iterations}")
        print(f"  学习率: {learning_rate}")
        print(f"  优化参数数量: {len(self.level1_params)}")
        print(f"  校准案例数量: {len(self.cases)}")
        
        # 初始化参数值
        current_params = {name: info['value'] for name, info in self.level1_params.items()}
        
        # 计算初始MAE
        initial_config = self._apply_params_to_config(current_params)
        initial_mae, _ = self._calculate_mae(initial_config)
        print(f"\n初始状态:")
        print(f"  初始MAE: {initial_mae:.2f}")
        
        best_mae = initial_mae
        best_params = current_params.copy()
        
        # 优化迭代
        for iteration in range(max_iterations):
            # 数值梯度下降
            improved = False
            
            for param_name in self.level1_params.keys():
                param_info = self.level1_params[param_name]
                current_value = current_params[param_name]
                anchor_value = param_info['anchor']
                param_range = param_info['range']
                
                # 计算梯度（数值方法）
                epsilon = 0.01
                temp_params_plus = current_params.copy()
                temp_params_plus[param_name] = min(current_value + epsilon, param_range[1])
                obj_plus = self._objective_function(temp_params_plus)
                
                temp_params_minus = current_params.copy()
                temp_params_minus[param_name] = max(current_value - epsilon, param_range[0])
                obj_minus = self._objective_function(temp_params_minus)
                
                # 梯度
                gradient = (obj_plus - obj_minus) / (2 * epsilon)
                
                # 更新参数
                new_value = current_value - learning_rate * gradient
                new_value = max(param_range[0], min(param_range[1], new_value))  # 约束到范围
                
                current_params[param_name] = new_value
            
            # 计算当前MAE
            current_config = self._apply_params_to_config(current_params)
            current_mae, _ = self._calculate_mae(current_config)
            
            # 记录历史
            self.optimization_history.append({
                'iteration': iteration + 1,
                'mae': current_mae,
                'params': current_params.copy()
            })
            
            # 更新最佳值
            if current_mae < best_mae:
                best_mae = current_mae
                best_params = current_params.copy()
                improved = True
            
            # 输出进度
            if (iteration + 1) % 10 == 0 or improved:
                print(f"\n迭代 {iteration + 1}/{max_iterations}:")
                print(f"  当前MAE: {current_mae:.2f}")
                print(f"  最佳MAE: {best_mae:.2f}")
                if improved:
                    print(f"  ✅ 发现更优解！")
            
            # 收敛检查
            if best_mae < 5.0:
                print(f"\n🎉 达到目标！MAE < 5.0")
                break
        
        # 最终结果
        final_config = self._apply_params_to_config(best_params)
        final_mae, final_details = self._calculate_mae(final_config)
        
        print(f"\n" + "=" * 80)
        print("优化完成")
        print("=" * 80)
        print(f"\n最终结果:")
        print(f"  最佳MAE: {best_mae:.2f}")
        print(f"  目标: MAE < 5.0")
        print(f"  状态: {'✅ 达成' if best_mae < 5.0 else '❌ 未达成'}")
        
        return {
            'best_mae': best_mae,
            'best_params': best_params,
            'best_config': final_config,
            'initial_mae': initial_mae,
            'improvement': initial_mae - best_mae,
            'iterations': len(self.optimization_history),
            'history': self.optimization_history,
            'final_details': final_details
        }

def main():
    """主函数"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "parameters.json")
    # 尝试多个可能的路径
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "calibration_cases.json"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "calibration_cases.json"),
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
    
    if not os.path.exists(cases_path):
        print(f"⚠️  校准案例文件不存在: {cases_path}")
        print(f"   将使用空案例集进行优化（仅验证参数范围）")
        cases_path = None
    
    # 创建优化器
    optimizer = V79AutonomousOptimizer(config_path, cases_path)
    
    # 执行优化
    result = optimizer.optimize(max_iterations=50, learning_rate=0.01)
    
    # 保存结果
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "V79_TASK123_OPTIMIZATION_RESULT.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n优化结果已保存至: {output_path}")

if __name__ == "__main__":
    main()

