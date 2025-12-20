"""
V79.0 自主优化流程（LSR/正则化框架）
====================================
五步自主优化流程，目标：找到 Level 1 算法中的最优普适参数集，使总成本 Cost_Total 最小化。

执行流程：
1. 步骤一：前置准备与代码逻辑修复（强制）
2. 步骤二：定义目标函数与成本计算
3. 步骤三：计算梯度与方向（优化引擎）
4. 步骤四：迭代更新参数并约束范围
5. 步骤五：收敛判定与最终报告
"""

import sys
import os
import json
import io
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from copy import deepcopy
from datetime import datetime

# Fix encoding issue for both Windows and WSL
import locale
try:
    # Try to set UTF-8 encoding
    if sys.stdout.encoding != 'utf-8':
        if sys.platform == 'win32':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        else:
            # For WSL/Linux, ensure UTF-8
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
except:
    pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine_v88 import EngineV88


class V79LSROptimizer:
    """
    V79.0 自主优化器（LSR/正则化框架）
    
    基于 V32.0 参数锚点，使用 LSR（Least Squares with Regularization）优化算法
    目标：最小化 Cost_Total = Cost_MAE + Cost_Plausibility
    """
    
    def __init__(self, config_path: str, cases_path: str = None):
        """
        初始化优化器
        
        Args:
            config_path: 配置文件路径（V32.0 锚点）
            cases_path: 校准案例路径
        """
        self.config_path = config_path
        self.cases_path = cases_path
        
        # 加载 V32.0 锚点配置
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.anchor_config = json.load(f)
        
        # 加载校准案例
        self.cases = []
        if cases_path and os.path.exists(cases_path):
            with open(cases_path, 'r', encoding='utf-8') as f:
                self.cases = json.load(f)
            print(f"✅ 加载了 {len(self.cases)} 个校准案例")
        else:
            print(f"⚠️  校准案例文件不存在: {cases_path}")
            print(f"   将使用空案例集进行优化（仅验证参数范围）")
        
        # TGD 初始值（作为优化锚点）
        self.tgd_anchor = {
            'T_Main': 7.5,
            'T_Stem': 5.0,
            'T_Mid': 3.0,
            'T_Minor': 1.5
        }
        
        # 正则化系数（可调）
        self.lambda_reg = 0.01
        
        # V80.0: 增加学习率以加速收敛
        self.learning_rate = 0.05  # 从 0.01 提升至 0.05
        
        # 收敛阈值
        self.mae_target = 5.0
        self.mae_change_threshold = 0.01
        self.convergence_window = 5  # 连续 N 次迭代
        
        # 定义 Level 1 参数集（约 45 个参数）
        self.level1_params = self._define_level1_params()
        
        # 优化历史
        self.optimization_history = []
        
        # V80.0: 统计解除正则化约束的参数
        no_reg_params = [name for name, info in self.level1_params.items() 
                        if info.get('no_regularization', False)]
        
        print(f"✅ 优化器初始化完成")
        print(f"   Level 1 参数数量: {len(self.level1_params)}")
        print(f"   正则化系数 λ: {self.lambda_reg}")
        print(f"   学习率: {self.learning_rate} (V80.0: 提升至 0.05)")
        print(f"   V80.0: 解除正则化约束的参数: {len(no_reg_params)} 个")
        print(f"   核心参数（无约束）: {', '.join(no_reg_params[:10])}")
    
    def _define_level1_params(self) -> Dict[str, Dict]:
        """
        步骤一：定义 Level 1 参数集（约 45 个参数）
        
        包括：
        - TGD 参数（4个）
        - ctl_imp, imp_base, imp_weak
        - pg_year, pg_month, pg_day, pg_hour
        - root_w, exposed_b, same_pill
        - 以及其他 Level 1 参数
        
        Returns:
            参数字典，包含参数名、当前值、范围、锚点值
        """
        config = self.anchor_config
        
        params = {}
        
        # ========== 1. 基础场域（Physics）- 4个参数 ==========
        pillar_weights = config.get('physics', {}).get('pillarWeights', {})
        # V80.0: 部分柱位权重解除正则化约束（pg_month 已达上限，保持约束）
        params['pg_year'] = {
            'value': pillar_weights.get('year', 1.0),
            'anchor': pillar_weights.get('year', 1.0),
            'range': (0.5, 1.5),
            'category': 'Physics',
            'no_regularization': True  # V80.0: 解除正则化约束
        }
        params['pg_month'] = {
            'value': pillar_weights.get('month', 1.8),
            'anchor': pillar_weights.get('month', 1.8),
            'range': (0.5, 2.0),
            'category': 'Physics'
            # pg_month 保持正则化约束（已达上限）
        }
        params['pg_day'] = {
            'value': pillar_weights.get('day', 1.5),
            'anchor': pillar_weights.get('day', 1.5),
            'range': (0.5, 1.5),
            'category': 'Physics',
            'no_regularization': True  # V80.0: 解除正则化约束
        }
        params['pg_hour'] = {
            'value': pillar_weights.get('hour', 1.2),
            'anchor': pillar_weights.get('hour', 1.2),
            'range': (0.5, 1.5),
            'category': 'Physics',
            'no_regularization': True  # V80.0: 解除正则化约束
        }
        
        # ========== 2. 粒子动态（Structure）- 3个参数 ==========
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
        params['same_pill'] = {
            'value': 2.5,
            'anchor': 2.5,
            'range': (1.0, 3.0),  # 扩展范围以允许优化
            'category': 'Structure'
        }
        
        # ========== 3. 几何交互（Interactions）- 10个参数 ==========
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
        
        # 六合加成
        params['sixHarmony'] = {
            'value': 5.0,
            'anchor': 5.0,
            'range': (0.0, 20.0),
            'category': 'Interactions'
        }
        
        # ========== 4. 能量流转（Flow）- 7个参数 ==========
        flow_config = config.get('flow', {})
        resource_impedance = flow_config.get('resourceImpedance', {})
        # V80.0: imp_base 解除正则化约束
        params['imp_base'] = {
            'value': resource_impedance.get('base', 0.20),
            'anchor': resource_impedance.get('base', 0.20),
            'range': (0.0, 0.9),
            'category': 'Flow',
            'no_regularization': True  # V80.0: 标记为无正则化约束
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
        
        # V80.0: 强制修正 ctl_imp 锚点从 1.25 到 0.90
        params['ctl_imp'] = {
            'value': flow_config.get('controlImpact', 1.25),
            'anchor': 0.90,  # V80.0: 强制修正锚点为 0.90（而非 V32.0 的 1.25）
            'range': (0.1, 2.0),  # 扩展范围以允许优化
            'category': 'Flow',
            'no_regularization': True  # V80.0: 标记为无正则化约束
        }
        
        params['sys_ent'] = {
            'value': 0.05,
            'anchor': 0.05,
            'range': (0.0, 0.2),
            'category': 'Flow'
        }
        
        # ========== 5. TGD 参数（4个） ==========
        # V80.0: TGD 参数解除正则化约束
        for tgd_name, tgd_value in self.tgd_anchor.items():
            params[tgd_name] = {
                'value': tgd_value,
                'anchor': tgd_value,
                'range': (tgd_value * 0.5, tgd_value * 1.5),  # ±50% 范围
                'category': 'TGD',
                'no_regularization': True  # V80.0: 标记为无正则化约束
            }
        
        # ========== 6. 其他 Level 1 参数 ==========
        # 能量阈值
        params['energy_strong'] = {
            'value': 3.5,
            'anchor': 3.5,
            'range': (2.0, 5.0),
            'category': 'Thresholds'
        }
        params['energy_weak'] = {
            'value': 2.0,
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
        
        # 基础事件分数
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
    
    def _calculate_mae(self, config: Dict) -> Tuple[float, Dict]:
        """
        步骤二：计算 Cost_MAE（拟合成本）
        
        运行批量校准脚本，计算所有案例的平均绝对误差（MAE）
        
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
            
            # 构建 case_data
            bazi = case.get('bazi', [])
            day_master = case.get('day_master', '')
            
            if not bazi or not day_master:
                continue
            
            # 处理 gender 格式（可能是字符串 '男'/'女' 或数字 1/0）
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
            # 优先使用 ground_truth，如果没有则使用 v_real
            target_v = case.get('ground_truth', case.get('v_real', {}))
            if case.get("dynamic_checks"):
                p = case["dynamic_checks"][0]
                d_ctx = {"year": p.get('year', "2024"), "luck": p.get('luck', "default")}
                if 'v_real_dynamic' in p:
                    target_v = p['v_real_dynamic']
            
            # 计算得分
            try:
                result = engine.calculate_energy(case_data, d_ctx)
                # 检查结果是否包含必要的键
                if not isinstance(result, dict):
                    print(f"⚠️  案例 {case_id} 返回结果格式错误: {type(result)}")
                    continue
                if 'career' not in result or 'wealth' not in result or 'relationship' not in result:
                    print(f"⚠️  案例 {case_id} 返回结果缺少必要键: {list(result.keys())}")
                    continue
            except KeyError as e:
                print(f"⚠️  案例 {case_id} 计算失败 (KeyError): {e}")
                import traceback
                traceback.print_exc()
                continue
            except Exception as e:
                print(f"⚠️  案例 {case_id} 计算失败: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                continue
            
            # 计算误差
            for dimension in ['career', 'wealth', 'relationship']:
                # 尝试多种可能的键名
                gt_value = None
                for key in [f'{dimension}_score', dimension, f'{dimension}_gt']:
                    if key in target_v:
                        gt_value = target_v[key]
                        break
                
                if gt_value is None or gt_value == 0:
                    continue
                
                pred_value = result.get(dimension, 0.0)
                
                # 如果预测值是 0-10 范围（从测试看是 7.9, 9.8, 7.5），转换为 0-100 范围
                if pred_value > 0 and pred_value < 20:
                    pred_value = pred_value * 10.0
                
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
        步骤二：计算 Cost_Plausibility（正则化成本）
        
        计算当前参数集与优化锚点之间的偏差惩罚
        Formula: λ * Σ(Parameter - Anchor)²
        
        V80.0: 核心参数（TGD, ctl_imp, imp_base, 部分柱位权重）解除正则化约束
        
        Args:
            params: 参数字典
            
        Returns:
            正则化惩罚值
        """
        penalty = 0.0
        
        for param_name, param_value in params.items():
            if param_name in self.level1_params:
                param_info = self.level1_params[param_name]
                # V80.0: 检查是否标记为无正则化约束
                if param_info.get('no_regularization', False):
                    continue  # 跳过核心参数的正则化惩罚
                
                anchor_value = param_info['anchor']
                # L2 正则化：惩罚偏离锚点的值
                deviation = param_value - anchor_value
                penalty += (deviation ** 2)
        
        return self.lambda_reg * penalty
    
    def _calculate_total_cost(self, params: Dict[str, float]) -> Tuple[float, float, float]:
        """
        步骤二：计算总成本 Cost_Total
        
        Args:
            params: 参数字典
            
        Returns:
            (Cost_Total, Cost_MAE, Cost_Plausibility)
        """
        # 应用参数到配置
        config = self._apply_params_to_config(params)
        
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
        步骤三：计算梯度（偏导数）
        
        计算 Cost_Total 相对于某个参数的偏导数
        
        Args:
            params: 当前参数字典
            param_name: 参数名
            
        Returns:
            梯度值
        """
        if param_name not in self.level1_params:
            return 0.0
        
        param_info = self.level1_params[param_name]
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
        步骤三和步骤四：计算梯度并更新参数
        
        Args:
            params: 当前参数字典
            
        Returns:
            更新后的参数字典
        """
        updated_params = params.copy()
        
        # 计算每个参数的梯度并更新
        for param_name in self.level1_params.keys():
            param_info = self.level1_params[param_name]
            current_value = params[param_name]
            param_range = param_info['range']
            
            # 计算梯度
            gradient = self._calculate_gradient(params, param_name)
            
            # 步骤四：沿负梯度方向更新参数
            new_value = current_value - self.learning_rate * gradient
            
            # 步骤四：范围硬约束
            new_value = max(param_range[0], min(param_range[1], new_value))
            
            updated_params[param_name] = new_value
        
        return updated_params
    
    def _check_convergence(self, history: List[Dict]) -> Tuple[bool, str]:
        """
        步骤五：收敛判定
        
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
    
    def optimize(self, max_iterations: int = 500) -> Dict:  # V80.0: 默认迭代次数提升至 500
        """
        执行完整的五步自主优化流程
        
        Args:
            max_iterations: 最大迭代次数
            
        Returns:
            优化结果
        """
        print("=" * 80)
        print("V80.0 自主优化流程（LSR/正则化框架 - 解除核心约束版本）启动")
        print("=" * 80)
        print("V80.0 任务 124：解除核心 Level 1 参数正则化并进行深度优化")
        
        print(f"\n优化配置:")
        print(f"  最大迭代次数: {max_iterations}")
        print(f"  学习率: {self.learning_rate}")
        print(f"  正则化系数 λ: {self.lambda_reg}")
        print(f"  优化参数数量: {len(self.level1_params)}")
        print(f"  校准案例数量: {len(self.cases)}")
        print(f"  目标 MAE: < {self.mae_target}")
        
        # 步骤一：初始化参数值（从锚点开始）
        current_params = {name: info['value'] for name, info in self.level1_params.items()}
        
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
            # 步骤三和步骤四：计算梯度并更新参数
            current_params = self._update_parameters(current_params)
            
            # 步骤二：计算当前成本
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
            
            # 步骤五：收敛检查
            is_converged, reason = self._check_convergence(self.optimization_history)
            if is_converged:
                print(f"\n🎉 收敛达成！")
                print(f"  原因: {reason}")
                break
        
        # 步骤五：最终报告
        final_config = self._apply_params_to_config(best_params)
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
        print(f"\n最优参数摘要（前 10 个变化最大的参数）:")
        param_changes = []
        for param_name in self.level1_params.keys():
            anchor = self.level1_params[param_name]['anchor']
            optimal = best_params[param_name]
            change = abs(optimal - anchor)
            if change > 0.001:  # 只显示有显著变化的参数
                param_changes.append((param_name, anchor, optimal, change))
        
        param_changes.sort(key=lambda x: x[3], reverse=True)
        for param_name, anchor, optimal, change in param_changes[:10]:
            print(f"  {param_name}: {anchor:.4f} → {optimal:.4f} (变化: {change:.4f})")
        
        return {
            'best_mae': best_mae,
            'best_params': best_params,
            'best_config': final_config,
            'initial_mae': initial_mae,
            'improvement': initial_mae - best_mae,
            'iterations': len(self.optimization_history),
            'history': self.optimization_history,
            'final_details': final_details,
            'converged': is_converged,
            'convergence_reason': reason if is_converged else "达到最大迭代次数"
        }


def main():
    """主函数"""
    # 配置文件路径
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "parameters.json"
    )
    
    # 校准案例路径（尝试多个可能的路径）
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
    optimizer = V79LSROptimizer(config_path, cases_path)
    
    # V80.0: 执行深度优化（500 次迭代）
    result = optimizer.optimize(max_iterations=500)
    
    # 保存结果
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"V79_OPTIMIZATION_RESULT_{timestamp}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n优化结果已保存至: {output_path}")


if __name__ == "__main__":
    main()

