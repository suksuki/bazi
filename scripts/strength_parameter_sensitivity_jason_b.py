#!/usr/bin/env python3
"""
Jason B (身弱用印) 参数敏感度分析
================================

针对"身弱用印"命局结构的参数敏感度分析
重点分析"印星帮身"机制为何未被充分激活

作者: Antigravity Team
版本: V10.0
日期: 2025-12-17
"""

import sys
import json
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.strength_probability_wave import StrengthProbabilityWave
from core.gat_strength_attention import GATStrengthAttention
from core.bayesian_strength_calibration import BayesianStrengthCalibration
from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
import copy


class JasonBParameterSensitivityAnalyzer:
    """
    Jason B (身弱用印) 参数敏感度分析器
    重点分析"印星帮身"机制
    """
    
    def __init__(self):
        """初始化分析器"""
        self.case_data = self._load_jason_b_case()
        logger.info(f"✅ 加载 Jason B 案例: {self.case_data['name']}")
    
    def _load_jason_b_case(self) -> Dict:
        """加载 Jason B 案例数据"""
        case_file = project_root / "calibration_cases.json"
        if case_file.exists():
            with open(case_file, 'r', encoding='utf-8') as f:
                cases = json.load(f)
                for case in cases:
                    if case.get('id', '').startswith('JASON_B'):
                        return case
        
        # 使用默认数据
        return {
            'id': 'JASON_B_T1964_0910',
            'name': 'Jason B (身弱用印)',
            'bazi': ['甲辰', '癸酉', '己亥', '戊辰'],
            'day_master': '己',
            'gender': '男',
            'description': '身弱用印，印星帮身',
            'timeline': [
                {
                    'year': 1999,
                    'ganzhi': '己卯',
                    'dayun': '丁丑',
                    'type': 'WEALTH',
                    'real_magnitude': 100.0,
                    'desc': '财富爆发'
                },
                {
                    'year': 2007,
                    'ganzhi': '丁亥',
                    'dayun': '戊寅',
                    'type': 'WEALTH',
                    'real_magnitude': 70.0,
                    'desc': '财富积累'
                },
                {
                    'year': 2014,
                    'ganzhi': '甲午',
                    'dayun': '己卯',
                    'type': 'WEALTH',
                    'real_magnitude': 100.0,
                    'desc': '财富再次爆发'
                }
            ]
        }
    
    def analyze_generation_efficiency_sensitivity(self) -> Dict:
        """
        分析"生的效率" (generationEfficiency) 的敏感度
        这是"印星帮身"机制的核心参数
        """
        logger.info("=" * 80)
        logger.info("📊 分析'生的效率' (generationEfficiency) 敏感度")
        logger.info("=" * 80)
        
        efficiency_range = np.linspace(0.1, 2.0, 20)
        losses = []
        
        for efficiency in efficiency_range:
            total_loss = 0.0
            for event in self.case_data['timeline']:
                year = event.get('year')
                real_wealth = event.get('real_magnitude', 0.0)
                year_pillar = event.get('ganzhi', '')
                luck_pillar = event.get('dayun', '')
                
                # 创建配置
                config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
                config['flow']['generationEfficiency'] = efficiency
                
                # 计算预测值
                engine = GraphNetworkEngine(config=config)
                result = engine.calculate_wealth_index(
                    bazi=self.case_data['bazi'],
                    day_master=self.case_data['day_master'],
                    gender=self.case_data['gender'],
                    luck_pillar=luck_pillar,
                    year_pillar=year_pillar
                )
                
                if isinstance(result, dict):
                    predicted = result.get('wealth_index', 0.0)
                else:
                    predicted = float(result)
                
                # 计算误差
                error = (predicted - real_wealth) ** 2
                total_loss += error
            
            avg_loss = total_loss / len(self.case_data['timeline'])
            losses.append(avg_loss)
        
        # 找到最优值
        optimal_idx = np.argmin(losses)
        optimal_efficiency = efficiency_range[optimal_idx]
        optimal_loss = losses[optimal_idx]
        
        # 计算敏感度
        sensitivity = np.gradient(losses, efficiency_range)
        
        result = {
            'parameter_name': 'generationEfficiency',
            'parameter_range': efficiency_range.tolist(),
            'losses': losses,
            'sensitivity': sensitivity.tolist(),
            'optimal_value': float(optimal_efficiency),
            'optimal_loss': float(optimal_loss),
            'sensitivity_range': [float(np.min(sensitivity)), float(np.max(sensitivity))]
        }
        
        logger.info(f"✅ 最优'生的效率': {optimal_efficiency:.4f}")
        logger.info(f"   最优损失: {optimal_loss:.4f}")
        logger.info(f"   敏感度范围: [{np.min(sensitivity):.4f}, {np.max(sensitivity):.4f}]")
        
        return result
    
    def analyze_strength_threshold_sensitivity(self) -> Dict:
        """
        分析旺衰阈值对"身弱用印"命局的影响
        """
        logger.info("=" * 80)
        logger.info("📊 分析旺衰阈值敏感度（身弱用印）")
        logger.info("=" * 80)
        
        threshold_range = np.linspace(2.0, 4.0, 20)
        losses = []
        
        for threshold in threshold_range:
            total_loss = 0.0
            for event in self.case_data['timeline']:
                year = event.get('year')
                real_wealth = event.get('real_magnitude', 0.0)
                year_pillar = event.get('ganzhi', '')
                luck_pillar = event.get('dayun', '')
                
                # 创建配置
                config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
                if 'strength' not in config:
                    config['strength'] = {}
                config['strength']['energy_threshold_center'] = threshold
                
                # 计算预测值
                engine = GraphNetworkEngine(config=config)
                result = engine.calculate_wealth_index(
                    bazi=self.case_data['bazi'],
                    day_master=self.case_data['day_master'],
                    gender=self.case_data['gender'],
                    luck_pillar=luck_pillar,
                    year_pillar=year_pillar
                )
                
                if isinstance(result, dict):
                    predicted = result.get('wealth_index', 0.0)
                else:
                    predicted = float(result)
                
                # 计算误差
                error = (predicted - real_wealth) ** 2
                total_loss += error
            
            avg_loss = total_loss / len(self.case_data['timeline'])
            losses.append(avg_loss)
        
        # 找到最优值
        optimal_idx = np.argmin(losses)
        optimal_threshold = threshold_range[optimal_idx]
        optimal_loss = losses[optimal_idx]
        
        # 计算敏感度
        sensitivity = np.gradient(losses, threshold_range)
        
        result = {
            'parameter_name': 'energy_threshold_center',
            'parameter_range': threshold_range.tolist(),
            'losses': losses,
            'sensitivity': sensitivity.tolist(),
            'optimal_value': float(optimal_threshold),
            'optimal_loss': float(optimal_loss),
            'sensitivity_range': [float(np.min(sensitivity)), float(np.max(sensitivity))]
        }
        
        logger.info(f"✅ 最优旺衰阈值: {optimal_threshold:.4f}")
        logger.info(f"   最优损失: {optimal_loss:.4f}")
        logger.info(f"   敏感度范围: [{np.min(sensitivity):.4f}, {np.max(sensitivity):.4f}]")
        
        return result
    
    def analyze_seal_boost_sensitivity(self) -> Dict:
        """
        分析"印星加成" (Seal Boost) 的敏感度
        这是"身弱用印"命局的关键机制
        """
        logger.info("=" * 80)
        logger.info("📊 分析'印星加成'敏感度")
        logger.info("=" * 80)
        
        # 查找配置中的印星相关参数
        # 通常印星加成可能在 physics 或 structure 中
        boost_range = np.linspace(0.5, 2.0, 20)
        losses = []
        
        for boost in boost_range:
            total_loss = 0.0
            for event in self.case_data['timeline']:
                year = event.get('year')
                real_wealth = event.get('real_magnitude', 0.0)
                year_pillar = event.get('ganzhi', '')
                luck_pillar = event.get('dayun', '')
                
                # 创建配置
                config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
                # 假设印星加成在 physics 中（需要根据实际配置调整）
                if 'sealBoost' not in config.get('physics', {}):
                    config.setdefault('physics', {})['sealBoost'] = boost
                else:
                    config['physics']['sealBoost'] = boost
                
                # 计算预测值
                engine = GraphNetworkEngine(config=config)
                result = engine.calculate_wealth_index(
                    bazi=self.case_data['bazi'],
                    day_master=self.case_data['day_master'],
                    gender=self.case_data['gender'],
                    luck_pillar=luck_pillar,
                    year_pillar=year_pillar
                )
                
                if isinstance(result, dict):
                    predicted = result.get('wealth_index', 0.0)
                else:
                    predicted = float(result)
                
                # 计算误差
                error = (predicted - real_wealth) ** 2
                total_loss += error
            
            avg_loss = total_loss / len(self.case_data['timeline'])
            losses.append(avg_loss)
        
        # 找到最优值
        optimal_idx = np.argmin(losses)
        optimal_boost = boost_range[optimal_idx]
        optimal_loss = losses[optimal_idx]
        
        # 计算敏感度
        sensitivity = np.gradient(losses, boost_range)
        
        result = {
            'parameter_name': 'sealBoost',
            'parameter_range': boost_range.tolist(),
            'losses': losses,
            'sensitivity': sensitivity.tolist(),
            'optimal_value': float(optimal_boost),
            'optimal_loss': float(optimal_loss),
            'sensitivity_range': [float(np.min(sensitivity)), float(np.max(sensitivity))]
        }
        
        logger.info(f"✅ 最优'印星加成': {optimal_boost:.4f}")
        logger.info(f"   最优损失: {optimal_loss:.4f}")
        logger.info(f"   敏感度范围: [{np.min(sensitivity):.4f}, {np.max(sensitivity):.4f}]")
        
        return result
    
    def analyze_weak_wealth_reversal_sensitivity(self) -> Dict:
        """
        分析"身弱财重反转"机制的敏感度
        这是"身弱用印"命局的关键逻辑
        """
        logger.info("=" * 80)
        logger.info("📊 分析'身弱财重反转'机制敏感度")
        logger.info("=" * 80)
        
        # 查找配置中的身弱财重反转参数
        # 通常在 wealth 或 interactions 中
        reversal_factor_range = np.linspace(-2.0, 0.0, 20)  # 负值表示反转
        losses = []
        
        for factor in reversal_factor_range:
            total_loss = 0.0
            for event in self.case_data['timeline']:
                year = event.get('year')
                real_wealth = event.get('real_magnitude', 0.0)
                year_pillar = event.get('ganzhi', '')
                luck_pillar = event.get('dayun', '')
                
                # 创建配置
                config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
                # 假设身弱财重反转在 wealth 中（需要根据实际配置调整）
                if 'weakWealthReversal' not in config.get('wealth', {}):
                    config.setdefault('wealth', {})['weakWealthReversal'] = factor
                else:
                    config['wealth']['weakWealthReversal'] = factor
                
                # 计算预测值
                engine = GraphNetworkEngine(config=config)
                result = engine.calculate_wealth_index(
                    bazi=self.case_data['bazi'],
                    day_master=self.case_data['day_master'],
                    gender=self.case_data['gender'],
                    luck_pillar=luck_pillar,
                    year_pillar=year_pillar
                )
                
                if isinstance(result, dict):
                    predicted = result.get('wealth_index', 0.0)
                else:
                    predicted = float(result)
                
                # 计算误差
                error = (predicted - real_wealth) ** 2
                total_loss += error
            
            avg_loss = total_loss / len(self.case_data['timeline'])
            losses.append(avg_loss)
        
        # 找到最优值
        optimal_idx = np.argmin(losses)
        optimal_factor = reversal_factor_range[optimal_idx]
        optimal_loss = losses[optimal_idx]
        
        # 计算敏感度
        sensitivity = np.gradient(losses, reversal_factor_range)
        
        result = {
            'parameter_name': 'weakWealthReversal',
            'parameter_range': reversal_factor_range.tolist(),
            'losses': losses,
            'sensitivity': sensitivity.tolist(),
            'optimal_value': float(optimal_factor),
            'optimal_loss': float(optimal_loss),
            'sensitivity_range': [float(np.min(sensitivity)), float(np.max(sensitivity))]
        }
        
        logger.info(f"✅ 最优'身弱财重反转因子': {optimal_factor:.4f}")
        logger.info(f"   最优损失: {optimal_loss:.4f}")
        logger.info(f"   敏感度范围: [{np.min(sensitivity):.4f}, {np.max(sensitivity):.4f}]")
        
        return result
    
    def generate_sensitivity_report(self, output_dir: Path = None) -> Dict:
        """
        生成完整的敏感度分析报告
        """
        logger.info("\n" + "=" * 80)
        logger.info("🎯 开始生成 Jason B (身弱用印) 参数敏感度分析报告")
        logger.info("=" * 80)
        
        # 分析关键参数
        efficiency_result = self.analyze_generation_efficiency_sensitivity()
        threshold_result = self.analyze_strength_threshold_sensitivity()
        seal_boost_result = self.analyze_seal_boost_sensitivity()
        reversal_result = self.analyze_weak_wealth_reversal_sensitivity()
        
        # 生成报告
        report = {
            'case_id': self.case_data['id'],
            'case_name': self.case_data['name'],
            'case_description': self.case_data.get('description', ''),
            'analysis_date': str(Path(__file__).stat().st_mtime),
            'test_events_count': len(self.case_data['timeline']),
            'parameters': {
                'generationEfficiency': efficiency_result,
                'energy_threshold_center': threshold_result,
                'sealBoost': seal_boost_result,
                'weakWealthReversal': reversal_result
            },
            'summary': {
                'most_sensitive_parameter': self._find_most_sensitive_parameter([
                    efficiency_result,
                    threshold_result,
                    seal_boost_result,
                    reversal_result
                ]),
                'recommendations': self._generate_recommendations([
                    efficiency_result,
                    threshold_result,
                    seal_boost_result,
                    reversal_result
                ])
            }
        }
        
        # 保存报告
        if output_dir is None:
            output_dir = project_root / "reports"
        output_dir.mkdir(exist_ok=True)
        
        report_file = output_dir / "jason_b_sensitivity_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 报告已保存到: {report_file}")
        
        return report
    
    def _find_most_sensitive_parameter(self, results: List[Dict]) -> str:
        """找到最敏感的参数"""
        max_sensitivity = 0.0
        most_sensitive = None
        
        for result in results:
            sensitivity_range = result.get('sensitivity_range', [0, 0])
            max_sens = max(abs(sensitivity_range[0]), abs(sensitivity_range[1]))
            if max_sens > max_sensitivity:
                max_sensitivity = max_sens
                most_sensitive = result['parameter_name']
        
        return most_sensitive or 'unknown'
    
    def _generate_recommendations(self, results: List[Dict]) -> List[str]:
        """生成调优建议"""
        recommendations = []
        
        for result in results:
            param_name = result['parameter_name']
            optimal_value = result['optimal_value']
            sensitivity_range = result.get('sensitivity_range', [0, 0])
            max_sens = max(abs(sensitivity_range[0]), abs(sensitivity_range[1]))
            
            if max_sens > 100.0:
                recommendations.append(
                    f"{param_name} 极高敏感，必须优先调优。当前最优值: {optimal_value:.4f}"
                )
            elif max_sens > 10.0:
                recommendations.append(
                    f"{param_name} 高度敏感，建议优先调优。当前最优值: {optimal_value:.4f}"
                )
            elif max_sens > 5.0:
                recommendations.append(
                    f"{param_name} 中等敏感，建议关注。当前最优值: {optimal_value:.4f}"
                )
            else:
                recommendations.append(
                    f"{param_name} 低敏感，可以保持默认值。当前最优值: {optimal_value:.4f}"
                )
        
        return recommendations


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Jason B (身弱用印) 参数敏感度分析')
    parser.add_argument('--output', type=str, default=None,
                       help='输出目录路径（默认: reports/）')
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = JasonBParameterSensitivityAnalyzer()
    
    # 生成报告
    output_dir = Path(args.output) if args.output else None
    report = analyzer.generate_sensitivity_report(output_dir=output_dir)
    
    # 输出总结
    print("\n" + "=" * 80)
    print("📊 Jason B (身弱用印) 敏感度分析总结")
    print("=" * 80)
    print(f"最敏感参数: {report['summary']['most_sensitive_parameter']}")
    print("\n调优建议:")
    for rec in report['summary']['recommendations']:
        print(f"  - {rec}")
    print("\n✅ 分析完成！")


if __name__ == '__main__':
    main()

