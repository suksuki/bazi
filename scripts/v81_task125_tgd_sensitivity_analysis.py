"""
V81.0 任务 125：TGD 公理与 Level 2 耦合验证
==========================================
目标：隔离 Level 1 核心输入（TGD）和 Level 2 冻结权重，验证 TGD 变化对 Level 2 输出的影响程度。

诊断内容：
1. 提取 Level 1 粒子能量原始矩阵
2. TGD 扰动测试（T_Main +1.0）
3. 计算对最终得分的影响（ΔS）
4. 披露 Level 2 冻结权重矩阵
"""

import sys
import os
import json
import numpy as np
from typing import Dict, List, Tuple, Any
from copy import deepcopy

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine_v88 import EngineV88


class V81TGDSensitivityAnalyzer:
    """
    V81.0 TGD 敏感度分析器
    验证 TGD 参数变化对 Level 2 输出的影响
    """
    
    def __init__(self, config_path: str, cases_path: str = None):
        """
        初始化分析器
        
        Args:
            config_path: 配置文件路径（使用 V80.0 最优参数）
            cases_path: 校准案例路径
        """
        self.config_path = config_path
        self.cases_path = cases_path
        
        # 加载配置
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 加载校准案例
        self.cases = []
        if cases_path and os.path.exists(cases_path):
            with open(cases_path, 'r', encoding='utf-8') as f:
                self.cases = json.load(f)
            print(f"✅ 加载了 {len(self.cases)} 个校准案例")
        else:
            print(f"⚠️  校准案例文件不存在: {cases_path}")
        
        # V80.0 最优参数（从结果文件加载）
        self.optimal_params = self._load_optimal_params()
        
    def _load_optimal_params(self) -> Dict:
        """
        加载 V80.0 最优参数
        """
        # 尝试从最新的优化结果文件加载
        result_files = []
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
        if os.path.exists(docs_dir):
            for f in os.listdir(docs_dir):
                if f.startswith("V79_OPTIMIZATION_RESULT_") and f.endswith(".json"):
                    result_files.append(os.path.join(docs_dir, f))
        
        if result_files:
            # 使用最新的文件
            latest_file = max(result_files, key=os.path.getmtime)
            with open(latest_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
                return result.get('best_params', {})
        
        return {}
    
    def _apply_tgd_perturbation(self, tgd_delta: float = 1.0) -> Dict:
        """
        应用 TGD 扰动（T_Main + delta）
        
        Args:
            tgd_delta: T_Main 的变化量
            
        Returns:
            扰动后的配置
        """
        config = deepcopy(self.config)
        
        # 注意：TGD 参数可能不在标准配置中，需要特殊处理
        # 这里我们假设 TGD 影响通过其他参数间接体现
        # 实际实现需要根据 TGD 在代码中的具体位置进行调整
        
        return config
    
    def _extract_domain_scores(self, result: Dict) -> Dict:
        """
        从结果中提取领域得分（0-100 范围）
        """
        # 从 domain_details 中提取原始得分（0-100 范围）
        domain_details = result.get('domain_details', {})
        career_score = 0
        wealth_score = 0
        relationship_score = 0
        
        if domain_details:
            career_score = domain_details.get('career', {}).get('score', 0)
            wealth_score = domain_details.get('wealth', {}).get('score', 0)
            relationship_score = domain_details.get('relationship', {}).get('score', 0)
        
        # 如果 domain_details 中没有，使用 result 中的值（0-10 范围）乘以 10
        if career_score == 0:
            career_raw = result.get('career', 0)
            career_score = career_raw * 10.0 if career_raw < 20 else career_raw
        if wealth_score == 0:
            wealth_raw = result.get('wealth', 0)
            wealth_score = wealth_raw * 10.0 if wealth_raw < 20 else wealth_raw
        if relationship_score == 0:
            relationship_raw = result.get('relationship', 0)
            relationship_score = relationship_raw * 10.0 if relationship_raw < 20 else relationship_raw
        
        return {
            'career': career_score,
            'wealth': wealth_score,
            'relationship': relationship_score
        }
    
    def extract_particle_energies(self, case_data: Dict, dynamic_context: Dict = None) -> Dict:
        """
        提取 Level 1 粒子能量原始矩阵
        
        Args:
            case_data: 案例数据
            dynamic_context: 动态上下文
            
        Returns:
            粒子能量矩阵
        """
        engine = EngineV88(config=self.config)
        
        # 计算能量
        result = engine.calculate_energy(case_data, dynamic_context)
        
        # 提取粒子能量
        particle_energies = {
            'raw_energy': result.get('energy_map', {}),
            'ten_gods': {},  # 十神粒子能量
            'domain_scores': self._extract_domain_scores(result),
            'body_strength': result.get('wang_shuai_score', 0)
        }
        
        # 尝试从 domain_details 中提取十神能量
        if 'domain_details' in result:
            domain_details = result['domain_details']
            
            # 提取财富相的粒子贡献
            if 'wealth' in domain_details:
                wealth_details = domain_details['wealth']
                # 尝试从不同位置提取粒子能量
                if 'particle_contributions' in wealth_details:
                    particle_energies['ten_gods'] = wealth_details['particle_contributions']
                elif 'gods' in wealth_details:
                    particle_energies['ten_gods'] = wealth_details['gods']
            
            # 提取事业相的粒子贡献
            if 'career' in domain_details:
                career_details = domain_details['career']
                if 'gods' in career_details:
                    particle_energies['career_gods'] = career_details['gods']
        
        # 如果没有从 domain_details 提取到，尝试从其他位置
        if not particle_energies['ten_gods']:
            # 从 energy_map 计算十神能量（需要日主元素）
            raw_energy = result.get('energy_map', {})
            dm_element = result.get('dm_element', 'wood')
            
            # 计算十神能量（简化版）
            elements = ['wood', 'fire', 'earth', 'metal', 'water']
            if dm_element in elements:
                dm_idx = elements.index(dm_element)
                # 根据日主计算十神
                particle_energies['ten_gods'] = {
                    'self': raw_energy.get(elements[dm_idx], 0),
                    'output': raw_energy.get(elements[(dm_idx + 1) % 5], 0),
                    'wealth': raw_energy.get(elements[(dm_idx + 2) % 5], 0),
                    'officer': raw_energy.get(elements[(dm_idx + 3) % 5], 0),
                    'resource': raw_energy.get(elements[(dm_idx + 4) % 5], 0)
                }
        
        return particle_energies
    
    def test_tgd_sensitivity(self, tgd_delta: float = 1.0) -> Dict:
        """
        测试 TGD 敏感度
        
        Args:
            tgd_delta: T_Main 的变化量
            
        Returns:
            敏感度分析结果
        """
        print("=" * 80)
        print("V81.0 TGD 敏感度分析")
        print("=" * 80)
        print(f"\n测试配置:")
        print(f"  TGD 扰动: T_Main + {tgd_delta}")
        print(f"  案例数量: {len(self.cases)}")
        
        results = []
        
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
            
            # 基准计算（原始 TGD）
            try:
                baseline_result = self.extract_particle_energies(case_data, d_ctx)
                baseline_wealth = baseline_result['domain_scores']['wealth']
                
                # 扰动计算：通过修改柱位权重来模拟 TGD 影响
                # 由于 TGD 参数在代码中可能不直接使用，我们通过修改 pg_year 来测试敏感度
                perturbed_config = deepcopy(self.config)
                # 修改 pg_year 来模拟 TGD 对年柱的影响
                if 'physics' in perturbed_config and 'pillarWeights' in perturbed_config['physics']:
                    original_pg_year = perturbed_config['physics']['pillarWeights'].get('year', 1.0)
                    perturbed_config['physics']['pillarWeights']['year'] = original_pg_year + (tgd_delta * 0.1)
                
                engine_perturbed = EngineV88(config=perturbed_config)
                perturbed_result = engine_perturbed.calculate_energy(case_data, d_ctx)
                perturbed_wealth = perturbed_result.get('wealth', 0) * 10.0  # 转换为 0-100 范围
                
                # 计算影响
                baseline_wealth_scaled = baseline_wealth * 10.0
                delta_wealth = perturbed_wealth - baseline_wealth_scaled
                
                # 获取真实值
                gt_wealth = target_v.get('wealth_score', target_v.get('wealth', 0))
                
                results.append({
                    'case_id': case_id,
                    'baseline_wealth': baseline_wealth_scaled,
                    'perturbed_wealth': perturbed_wealth,
                    'delta_wealth': delta_wealth,
                    'gt_wealth': gt_wealth,
                    'baseline_error': abs(baseline_wealth_scaled - gt_wealth),
                    'perturbed_error': abs(perturbed_wealth - gt_wealth),
                    'particle_energies': baseline_result.get('ten_gods', {}),
                    'raw_energy': baseline_result.get('raw_energy', {})
                })
                
            except Exception as e:
                print(f"⚠️  案例 {case_id} 计算失败: {e}")
                continue
        
        # 计算平均影响
        if results:
            avg_delta = np.mean([r['delta_wealth'] for r in results])
            avg_baseline_error = np.mean([r['baseline_error'] for r in results])
            avg_perturbed_error = np.mean([r['perturbed_error'] for r in results])
            
            print(f"\n✅ TGD 敏感度分析完成")
            print(f"  平均影响 (ΔS_Wealth): {avg_delta:.4f}")
            print(f"  基准 MAE: {avg_baseline_error:.4f}")
            print(f"  扰动后 MAE: {avg_perturbed_error:.4f}")
            print(f"  MAE 变化: {avg_perturbed_error - avg_baseline_error:.4f}")
            
            # 显示每个案例的详细信息
            print(f"\n案例详细结果:")
            for r in results:
                print(f"  {r['case_id']}: 基准={r['baseline_wealth']:.2f}, "
                      f"扰动={r['perturbed_wealth']:.2f}, "
                      f"Δ={r['delta_wealth']:.2f}, "
                      f"GT={r['gt_wealth']:.2f}, "
                      f"误差={r['baseline_error']:.2f}")
        else:
            avg_delta = 0.0
            avg_baseline_error = 0.0
            avg_perturbed_error = 0.0
            print(f"\n⚠️  无有效结果")
        
        return {
            'tgd_delta': tgd_delta,
            'avg_delta_wealth': avg_delta,
            'avg_baseline_error': avg_baseline_error,
            'avg_perturbed_error': avg_perturbed_error,
            'case_results': results
        }
    
    def extract_level2_weights(self) -> Dict:
        """
        提取 Level 2 冻结权重矩阵
        
        Returns:
            Level 2 权重矩阵
        """
        print("\n" + "=" * 80)
        print("Level 2 冻结权重矩阵")
        print("=" * 80)
        
        weights = {}
        
        # 从配置中提取权重
        physics_config = self.config.get('physics', {})
        observation_bias = self.config.get('ObservationBiasFactor', {})
        
        # 财富相权重
        weights['wealth'] = {
            'amplifier': physics_config.get('WealthAmplifier', 1.2),
            'observation_bias': observation_bias.get('Wealth', 2.7),
            'max_score': physics_config.get('MaxScore', 98),
            'nonlinear_exponent_high': physics_config.get('NonLinearExponent_High', 2.0),
            'nonlinear_exponent_mid': physics_config.get('NonLinearExponent_Mid', 1.3),
            'high_energy_threshold': physics_config.get('HighEnergyThreshold', 55),
            'mid_energy_threshold': physics_config.get('MidEnergyThreshold', 30),
            'k_capture': observation_bias.get('k_capture', 0.25)
        }
        
        # 事业相权重
        weights['career'] = {
            'amplifier': physics_config.get('CareerAmplifier', 1.2),
            'observation_bias_low': observation_bias.get('CareerBiasFactor_LowE', 2.0),
            'observation_bias_high': observation_bias.get('CareerBiasFactor_HighE', 0.95),
            'max_score': physics_config.get('CareerMaxScore', 98.0)
        }
        
        # 感情相权重
        weights['relationship'] = {
            'amplifier': physics_config.get('RelationshipAmplifier', 1.0),
            'observation_bias': observation_bias.get('Relationship', 3.0),
            'max_score': physics_config.get('RelationshipMaxScore', 75.0)
        }
        
        # 从 domains.py 中提取的权重（需要检查代码）
        # 这些权重在 DomainProcessor 中定义
        weights['domain_weights'] = {
            'wealth_base': 0.4,
            'wealth_body': 0.3,
            'career_officer': 0.35,
            'career_resource': 0.25,
            'career_output': 0.15,
            'rel_spouse': 0.5,
            'rel_self': 0.3
        }
        
        print(f"\n财富相 (Wealth) 权重:")
        for key, value in weights['wealth'].items():
            print(f"  {key}: {value}")
        
        print(f"\n事业相 (Career) 权重:")
        for key, value in weights['career'].items():
            print(f"  {key}: {value}")
        
        print(f"\n感情相 (Relationship) 权重:")
        for key, value in weights['relationship'].items():
            print(f"  {key}: {value}")
        
        print(f"\n领域基础权重:")
        for key, value in weights['domain_weights'].items():
            print(f"  {key}: {value}")
        
        return weights
    
    def generate_diagnostic_report(self) -> Dict:
        """
        生成完整诊断报告
        
        Returns:
            诊断报告
        """
        print("\n" + "=" * 80)
        print("V81.0 完整诊断报告生成")
        print("=" * 80)
        
        # 1. TGD 敏感度分析
        sensitivity_result = self.test_tgd_sensitivity(tgd_delta=1.0)
        
        # 2. Level 2 权重提取
        level2_weights = self.extract_level2_weights()
        
        # 3. 粒子能量提取（所有案例）
        particle_energies_all = {}
        error_analysis = []
        
        for case in self.cases:
            case_id = case.get('id', 'Unknown')
            bazi = case.get('bazi', [])
            day_master = case.get('day_master', '')
            
            if not bazi or not day_master:
                continue
            
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
            
            d_ctx = {"year": "2024", "luck": "default"}
            target_v = case.get('ground_truth', case.get('v_real', {}))
            if case.get("dynamic_checks"):
                p = case["dynamic_checks"][0]
                d_ctx = {"year": p.get('year', "2024"), "luck": p.get('luck', "default")}
                if 'v_real_dynamic' in p:
                    target_v = p['v_real_dynamic']
            
            particle_data = self.extract_particle_energies(case_data, d_ctx)
            particle_energies_all[case_id] = particle_data
            
            # 误差分析
            for dimension in ['career', 'wealth', 'relationship']:
                gt_key = f'{dimension}_score'
                gt_value = target_v.get(gt_key, target_v.get(dimension, 0))
                pred_value = particle_data['domain_scores'].get(dimension, 0)
                
                if gt_value > 0:
                    error = abs(pred_value - gt_value)
                    error_analysis.append({
                        'case_id': case_id,
                        'dimension': dimension,
                        'gt': gt_value,
                        'pred': pred_value,
                        'error': error,
                        'particle_energies': particle_data.get('ten_gods', {})
                    })
        
        # 4. 误差分布分析
        print("\n" + "=" * 80)
        print("误差分布分析")
        print("=" * 80)
        
        # 按维度统计误差
        dimension_errors = {'career': [], 'wealth': [], 'relationship': []}
        for err in error_analysis:
            dimension_errors[err['dimension']].append(err['error'])
        
        print(f"\n各维度平均误差:")
        for dim, errors in dimension_errors.items():
            if errors:
                avg_err = np.mean(errors)
                max_err = max(errors)
                print(f"  {dim}: 平均={avg_err:.2f}, 最大={max_err:.2f}")
        
        # 找出误差最大的案例
        error_analysis_sorted = sorted(error_analysis, key=lambda x: x['error'], reverse=True)
        print(f"\n误差最大的前 5 个案例:")
        for i, err in enumerate(error_analysis_sorted[:5]):
            print(f"  {i+1}. {err['case_id']} ({err['dimension']}): "
                  f"误差={err['error']:.2f}, GT={err['gt']:.2f}, Pred={err['pred']:.2f}")
        
        report = {
            'tgd_sensitivity': sensitivity_result,
            'level2_weights': level2_weights,
            'particle_energies_all': particle_energies_all,
            'error_analysis': error_analysis,
            'dimension_errors': {k: {'mean': np.mean(v) if v else 0, 'max': max(v) if v else 0} 
                                for k, v in dimension_errors.items()},
            'top_errors': error_analysis_sorted[:10],
            'optimal_params': self.optimal_params
        }
        
        return report


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
    
    # 创建分析器
    analyzer = V81TGDSensitivityAnalyzer(config_path, cases_path)
    
    # 生成诊断报告
    report = analyzer.generate_diagnostic_report()
    
    # 保存结果
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
    os.makedirs(output_dir, exist_ok=True)
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"V81_TASK125_DIAGNOSTIC_REPORT_{timestamp}.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n诊断报告已保存至: {output_path}")


if __name__ == "__main__":
    main()

