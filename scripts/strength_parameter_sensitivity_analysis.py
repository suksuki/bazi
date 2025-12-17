#!/usr/bin/env python3
"""
旺衰判定模块参数敏感度分析
==========================

针对"旺衰判定模块"的参数敏感度分析报告
分析哪些基础参数对身强/身弱的判定影响最大

作者: Antigravity Team
版本: V10.0
日期: 2025-12-17
"""

import sys
import json
import sys
import json
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# 配置日志（必须在导入模块之前）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# matplotlib 可选依赖
try:
    import matplotlib
    matplotlib.use('Agg')  # 非交互式后端
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logger.warning("matplotlib 未安装，将跳过可视化图表生成")

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.strength_probability_wave import StrengthProbabilityWave
from core.gat_strength_attention import GATStrengthAttention
from core.bayesian_strength_calibration import BayesianStrengthCalibration
from core.bayesian_optimization import HyperparameterSensitivityAnalyzer


class StrengthParameterSensitivityAnalyzer:
    """
    旺衰参数敏感度分析器
    """
    
    def __init__(self):
        """初始化分析器"""
        self.test_cases = self._load_test_cases()
    
    def _load_test_cases(self) -> List[Dict]:
        """加载测试案例"""
        # 使用 Jason 案例作为测试数据
        case_file = project_root / "data" / "jason_d_case.json"
        if case_file.exists():
            with open(case_file, 'r', encoding='utf-8') as f:
                case_data = json.load(f)
                return [case_data]
        else:
            # 使用模拟数据
            return [
                {
                    'name': 'Test Case 1',
                    'energy_sum': 2.5,  # 身弱
                    'real_wealth': 50.0
                },
                {
                    'name': 'Test Case 2',
                    'energy_sum': 3.5,  # 身强
                    'real_wealth': 100.0
                },
                {
                    'name': 'Test Case 3',
                    'energy_sum': 3.0,  # 中性
                    'real_wealth': 75.0
                }
            ]
    
    def analyze_threshold_center_sensitivity(self) -> Dict:
        """
        分析激活函数中心点 (energy_threshold_center) 的敏感度
        """
        logger.info("=" * 80)
        logger.info("📊 分析激活函数中心点敏感度")
        logger.info("=" * 80)
        
        threshold_range = np.linspace(1.0, 5.0, 20)
        losses = []
        
        for threshold in threshold_range:
            total_loss = 0.0
            for case in self.test_cases:
                energy_sum = case.get('energy_sum', 3.0)
                real_wealth = case.get('real_wealth', 75.0)
                
                # 计算旺衰概率
                strength_prob, _ = StrengthProbabilityWave.calculate_strength_probability(
                    energy_sum=energy_sum,
                    threshold_center=threshold,
                    phase_transition_width=10.0
                )
                
                # 简化的财富预测（基于旺衰概率）
                predicted_wealth = strength_prob * 100.0
                
                # 计算误差
                error = (predicted_wealth - real_wealth) ** 2
                total_loss += error
            
            avg_loss = total_loss / len(self.test_cases)
            losses.append(avg_loss)
        
        # 找到最优值
        optimal_idx = np.argmin(losses)
        optimal_threshold = threshold_range[optimal_idx]
        optimal_loss = losses[optimal_idx]
        
        # 计算敏感度（梯度）
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
        
        logger.info(f"✅ 最优激活函数中心点: {optimal_threshold:.4f}")
        logger.info(f"   最优损失: {optimal_loss:.4f}")
        logger.info(f"   敏感度范围: [{np.min(sensitivity):.4f}, {np.max(sensitivity):.4f}]")
        
        return result
    
    def analyze_phase_transition_width_sensitivity(self) -> Dict:
        """
        分析相变宽度 (phase_transition_width / strength_beta) 的敏感度
        """
        logger.info("=" * 80)
        logger.info("📊 分析相变宽度敏感度")
        logger.info("=" * 80)
        
        width_range = np.linspace(1.0, 20.0, 20)
        losses = []
        
        for width in width_range:
            total_loss = 0.0
            for case in self.test_cases:
                energy_sum = case.get('energy_sum', 3.0)
                real_wealth = case.get('real_wealth', 75.0)
                
                # 计算旺衰概率
                strength_prob, _ = StrengthProbabilityWave.calculate_strength_probability(
                    energy_sum=energy_sum,
                    threshold_center=3.0,
                    phase_transition_width=width
                )
                
                # 简化的财富预测
                predicted_wealth = strength_prob * 100.0
                
                # 计算误差
                error = (predicted_wealth - real_wealth) ** 2
                total_loss += error
            
            avg_loss = total_loss / len(self.test_cases)
            losses.append(avg_loss)
        
        # 找到最优值
        optimal_idx = np.argmin(losses)
        optimal_width = width_range[optimal_idx]
        optimal_loss = losses[optimal_idx]
        
        # 计算敏感度
        sensitivity = np.gradient(losses, width_range)
        
        result = {
            'parameter_name': 'phase_transition_width',
            'parameter_range': width_range.tolist(),
            'losses': losses,
            'sensitivity': sensitivity.tolist(),
            'optimal_value': float(optimal_width),
            'optimal_loss': float(optimal_loss),
            'sensitivity_range': [float(np.min(sensitivity)), float(np.max(sensitivity))]
        }
        
        logger.info(f"✅ 最优相变宽度: {optimal_width:.4f}")
        logger.info(f"   最优损失: {optimal_loss:.4f}")
        logger.info(f"   敏感度范围: [{np.min(sensitivity):.4f}, {np.max(sensitivity):.4f}]")
        
        return result
    
    def analyze_attention_dropout_sensitivity(self) -> Dict:
        """
        分析注意力稀疏度 (attention_dropout) 的敏感度
        """
        logger.info("=" * 80)
        logger.info("📊 分析注意力稀疏度敏感度")
        logger.info("=" * 80)
        
        dropout_range = np.linspace(0.0, 0.5, 20)
        losses = []
        
        for dropout in dropout_range:
            total_loss = 0.0
            gat_attention = GATStrengthAttention(dropout=dropout)
            
            for case in self.test_cases:
                energy_sum = case.get('energy_sum', 3.0)
                real_wealth = case.get('real_wealth', 75.0)
                
                # 计算动态权重
                bazi_features = {'has_vault': True, 'clash_count': 1}
                weights = gat_attention.calculate_dynamic_strength_weights(
                    bazi_features=bazi_features,
                    pattern_type='wealth_vault'
                )
                
                # 简化的财富预测（基于权重）
                avg_weight = np.mean(list(weights.values()))
                predicted_wealth = avg_weight * 100.0
                
                # 计算误差
                error = (predicted_wealth - real_wealth) ** 2
                total_loss += error
            
            avg_loss = total_loss / len(self.test_cases)
            losses.append(avg_loss)
        
        # 找到最优值
        optimal_idx = np.argmin(losses)
        optimal_dropout = dropout_range[optimal_idx]
        optimal_loss = losses[optimal_idx]
        
        # 计算敏感度
        sensitivity = np.gradient(losses, dropout_range)
        
        result = {
            'parameter_name': 'attention_dropout',
            'parameter_range': dropout_range.tolist(),
            'losses': losses,
            'sensitivity': sensitivity.tolist(),
            'optimal_value': float(optimal_dropout),
            'optimal_loss': float(optimal_loss),
            'sensitivity_range': [float(np.min(sensitivity)), float(np.max(sensitivity))]
        }
        
        logger.info(f"✅ 最优注意力稀疏度: {optimal_dropout:.4f}")
        logger.info(f"   最优损失: {optimal_loss:.4f}")
        logger.info(f"   敏感度范围: [{np.min(sensitivity):.4f}, {np.max(sensitivity):.4f}]")
        
        return result
    
    def generate_sensitivity_report(self, output_dir: Path = None) -> Dict:
        """
        生成完整的敏感度分析报告
        
        Args:
            output_dir: 输出目录（可选）
        
        Returns:
            完整的分析报告字典
        """
        logger.info("\n" + "=" * 80)
        logger.info("🎯 开始生成旺衰判定模块参数敏感度分析报告")
        logger.info("=" * 80)
        
        # 分析三个元参数
        threshold_result = self.analyze_threshold_center_sensitivity()
        width_result = self.analyze_phase_transition_width_sensitivity()
        dropout_result = self.analyze_attention_dropout_sensitivity()
        
        # 生成报告
        report = {
            'analysis_date': str(Path(__file__).stat().st_mtime),
            'test_cases_count': len(self.test_cases),
            'parameters': {
                'energy_threshold_center': threshold_result,
                'phase_transition_width': width_result,
                'attention_dropout': dropout_result
            },
            'summary': {
                'most_sensitive_parameter': self._find_most_sensitive_parameter([
                    threshold_result,
                    width_result,
                    dropout_result
                ]),
                'recommendations': self._generate_recommendations([
                    threshold_result,
                    width_result,
                    dropout_result
                ])
            }
        }
        
        # 保存报告
        if output_dir is None:
            output_dir = project_root / "reports"
        output_dir.mkdir(exist_ok=True)
        
        report_file = output_dir / "strength_parameter_sensitivity_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 报告已保存到: {report_file}")
        
        # 生成可视化图表（如果可能）
        if HAS_MATPLOTLIB:
            try:
                self._plot_sensitivity_curves(report, output_dir)
            except Exception as e:
                logger.warning(f"无法生成可视化图表: {e}")
        else:
            logger.info("跳过可视化图表生成（matplotlib 未安装）")
        
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
            
            if max_sens > 10.0:
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
    
    def _plot_sensitivity_curves(self, report: Dict, output_dir: Path):
        """绘制敏感度曲线"""
        fig, axes = plt.subplots(3, 1, figsize=(10, 12))
        
        parameters = ['energy_threshold_center', 'phase_transition_width', 'attention_dropout']
        titles = ['激活函数中心点', '相变宽度', '注意力稀疏度']
        
        for idx, (param, title) in enumerate(zip(parameters, titles)):
            ax = axes[idx]
            param_data = report['parameters'][param]
            
            # 绘制损失曲线
            ax.plot(param_data['parameter_range'], param_data['losses'], 
                   'b-', label='损失', linewidth=2)
            ax.axvline(param_data['optimal_value'], color='r', linestyle='--', 
                      label=f"最优值: {param_data['optimal_value']:.4f}")
            
            ax.set_xlabel(title)
            ax.set_ylabel('损失值')
            ax.set_title(f'{title} 敏感度分析')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot_file = output_dir / "strength_parameter_sensitivity_curves.png"
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✅ 可视化图表已保存到: {plot_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='旺衰判定模块参数敏感度分析')
    parser.add_argument('--output', type=str, default=None,
                       help='输出目录路径（默认: reports/）')
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = StrengthParameterSensitivityAnalyzer()
    
    # 生成报告
    output_dir = Path(args.output) if args.output else None
    report = analyzer.generate_sensitivity_report(output_dir=output_dir)
    
    # 输出总结
    print("\n" + "=" * 80)
    print("📊 敏感度分析总结")
    print("=" * 80)
    print(f"最敏感参数: {report['summary']['most_sensitive_parameter']}")
    print("\n调优建议:")
    for rec in report['summary']['recommendations']:
        print(f"  - {rec}")
    print("\n✅ 分析完成！")


if __name__ == '__main__':
    main()

