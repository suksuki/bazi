#!/usr/bin/env python3
"""
V10.2 MCP Server: 为LLM/Cursor提供调优工具接口
================================================

MCP (Model Context Protocol) 工具函数：
1. run_physics_diagnosis() - 运行全量回归测试，返回诊断报告
2. configure_optimization_strategy() - 设定Optuna搜索空间
3. execute_optuna_study() - 启动Optuna优化

这些函数可以被LLM/Cursor通过MCP协议调用，实现"对话式调优"。
"""

import json
import sys
import copy
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.strength_parameter_tuning import StrengthParameterTuner
from scripts.v10_2_optuna_tuner import (
    StrengthOptimizationObjective,
    OptimizationConfig,
    run_optuna_study
)
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@dataclass
class DiagnosisReport:
    """诊断报告"""
    current_match_rate: float
    total_cases: int
    matched_cases: int
    main_issues: List[Dict[str, Any]]  # 主要问题列表
    violation_summary: Dict[str, Any]  # 物理约束违反摘要
    recommendations: List[str]  # 优化建议
    physics_consistency: Dict[str, Any] = None  # [V10.2] 物理一致性指标
    physics_consistency: Dict[str, Any]  # 📊 物理一致性指标（新增）


class MCPTuningServer:
    """
    MCP调优服务器
    
    提供三个核心工具函数，供LLM/Cursor调用
    """
    
    def __init__(self):
        self.tuner = StrengthParameterTuner()
        self.base_config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
        self.current_config = copy.deepcopy(self.base_config)
    
    def run_physics_diagnosis(self) -> Dict[str, Any]:
        """
        MCP工具1: 运行全量回归测试，返回诊断报告
        
        Returns:
            诊断报告字典，包含：
            - current_match_rate: 当前匹配率
            - main_issues: 主要问题列表（如"乔丹误判为弱"）
            - violation_summary: 物理约束违反摘要（如"月令<时柱"）
            - recommendations: 优化建议
        """
        logger.info("🔍 运行物理诊断...")
        
        # 1. 评估当前配置
        result = self.tuner.evaluate_parameter_set(self.current_config)
        
        # 2. 分析误判案例
        case_results = result.get('case_results', [])
        error_cases = [r for r in case_results if not r['match']]
        
        # 3. 统计误判模式
        error_patterns = {}
        for case in error_cases:
            pattern_key = f"{case['predicted']} → {case['ground_truth']}"
            if pattern_key not in error_patterns:
                error_patterns[pattern_key] = []
            error_patterns[pattern_key].append({
                'name': case['name'],
                'score': case['score']
            })
        
        # 4. 识别主要问题
        main_issues = []
        for pattern, cases in sorted(error_patterns.items(), key=lambda x: len(x[1]), reverse=True):
            if len(cases) >= 3:  # 至少3个案例才认为是主要问题
                main_issues.append({
                    'pattern': pattern,
                    'count': len(cases),
                    'examples': cases[:3]  # 只显示前3个例子
                })
        
        # 5. 检查物理约束违反
        violation_summary = self._check_physics_violations(self.current_config)
        
        # 6. 📊 计算物理一致性指标（仪表盘）
        physics_consistency = self._calculate_physics_consistency(result)
        
        # 7. 生成优化建议
        recommendations = self._generate_recommendations(
            result, main_issues, violation_summary, physics_consistency
        )
        
        # 8. 构建诊断报告
        report = DiagnosisReport(
            current_match_rate=result.get('match_rate', 0.0),
            total_cases=result.get('total_cases', 0),
            matched_cases=result.get('matched_cases', 0),
            main_issues=main_issues,
            violation_summary=violation_summary,
            recommendations=recommendations,
            physics_consistency=physics_consistency
        )
        
        # 添加到报告（如果还没有）
        if report.physics_consistency is None:
            report.physics_consistency = physics_consistency
        
        # 转换为字典（便于JSON序列化）
        report_dict = asdict(report)
        
        # 添加自然语言描述（供LLM理解）
        report_dict['nl_description'] = self._format_nl_description(report)
        
        logger.info(f"✅ 诊断完成: 匹配率={report.current_match_rate:.1f}%")
        
        return report_dict
    
    def _check_physics_violations(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """检查物理约束违反"""
        violations = []
        
        # 检查月令与时柱权重
        pillar_weights = config.get('physics', {}).get('pillarWeights', {})
        month_weight = pillar_weights.get('month', 1.2)
        hour_weight = pillar_weights.get('hour', 0.9)
        
        if hour_weight > month_weight:
            violations.append({
                'type': 'pillar_weight',
                'description': f'时柱权重({hour_weight:.3f}) > 月令权重({month_weight:.3f})，违反物理直觉',
                'severity': 'high'
            })
        
        # 检查通根权重
        structure = config.get('structure', {})
        rooting_weight = structure.get('rootingWeight', 1.2)
        if rooting_weight > 3.0:
            violations.append({
                'type': 'rooting_weight',
                'description': f'通根权重({rooting_weight:.3f}) > 3.0，可能过高',
                'severity': 'medium'
            })
        
        # 检查同柱加成
        same_pillar_bonus = structure.get('samePillarBonus', 1.6)
        if same_pillar_bonus > 2.5:
            violations.append({
                'type': 'same_pillar_bonus',
                'description': f'同柱加成({same_pillar_bonus:.3f}) > 2.5，可能过高',
                'severity': 'medium'
            })
        
        return {
            'has_violations': len(violations) > 0,
            'violations': violations,
            'count': len(violations)
        }
    
    def _calculate_physics_consistency(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        📊 计算物理一致性指标（仪表盘）
        
        指标：
        1. Month Dominance Ratio: 平均月令权重 / 平均时柱权重（应 > 1.5）
        2. Rooting Impact Factor: 有根者的平均得分 / 无根者的平均得分（应 > 2.0）
        
        Args:
            result: evaluate_parameter_set的返回结果
            
        Returns:
            物理一致性指标字典
        """
        config = self.current_config
        
        # 1. Month Dominance Ratio
        pillar_weights = config.get('physics', {}).get('pillarWeights', {})
        month_weight = pillar_weights.get('month', 1.2)
        hour_weight = pillar_weights.get('hour', 0.9)
        month_dominance_ratio = month_weight / hour_weight if hour_weight > 0 else 0.0
        
        # 2. Rooting Impact Factor（需要分析案例结果）
        case_results = result.get('case_results', [])
        
        # 简单估算：分析score分布来判断通根影响
        # （实际应该从引擎内部获取有根/无根信息，这里简化处理）
        scores = [r.get('score', 0.0) for r in case_results]
        if scores:
            avg_score = sum(scores) / len(scores)
            # 高score案例（可能有根）vs 低score案例（可能无根）
            high_scores = [s for s in scores if s >= 50.0]
            low_scores = [s for s in scores if s < 30.0]
            if low_scores and high_scores:
                avg_high = sum(high_scores) / len(high_scores)
                avg_low = sum(low_scores) / len(low_scores)
                rooting_impact_factor = avg_high / avg_low if avg_low > 0 else 0.0
            else:
                rooting_impact_factor = 1.0  # 无法计算
        else:
            rooting_impact_factor = 1.0
        
        # 3. 结构参数合理性
        structure = config.get('structure', {})
        rooting_weight = structure.get('rootingWeight', 1.2)
        same_pillar_bonus = structure.get('samePillarBonus', 1.6)
        
        # 判断指标健康状态
        month_dominance_healthy = month_dominance_ratio >= 1.5
        rooting_impact_healthy = rooting_impact_factor >= 2.0
        
        return {
            'month_dominance_ratio': month_dominance_ratio,
            'month_dominance_healthy': month_dominance_healthy,
            'rooting_impact_factor': rooting_impact_factor,
            'rooting_impact_healthy': rooting_impact_healthy,
            'rooting_weight': rooting_weight,
            'same_pillar_bonus': same_pillar_bonus,
            'overall_health': month_dominance_healthy and rooting_impact_healthy,
            'warnings': [
                f"月令支配比: {month_dominance_ratio:.2f} ({'✅' if month_dominance_healthy else '⚠️  应≥1.5'})",
                f"通根影响因子: {rooting_impact_factor:.2f} ({'✅' if rooting_impact_healthy else '⚠️  应≥2.0'})"
            ]
        }
    
    def _generate_recommendations(self, 
                                  result: Dict[str, Any],
                                  main_issues: List[Dict[str, Any]],
                                  violation_summary: Dict[str, Any],
                                  physics_consistency: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        # 基于误判模式生成建议
        for issue in main_issues:
            pattern = issue['pattern']
            if 'Follower' in pattern:
                recommendations.append(
                    f"从格判定问题: {pattern} ({issue['count']}个案例)。建议：调优follower_threshold或改进从格判定逻辑"
                )
            elif 'Strong → Weak' in pattern:
                recommendations.append(
                    f"身强误判为弱: {pattern} ({issue['count']}个案例)。建议：降低energy_threshold_center或提高samePillarBonus"
                )
            elif 'Weak → Strong' in pattern:
                recommendations.append(
                    f"身弱误判为强: {pattern} ({issue['count']}个案例)。建议：提高energy_threshold_center"
                )
        
        # 基于物理约束违反生成建议
        if violation_summary['has_violations']:
            for violation in violation_summary['violations']:
                if violation['severity'] == 'high':
                    recommendations.append(
                        f"物理约束违反: {violation['description']}。建议：调整参数或使用soft约束模式"
                    )
        
        # 📊 基于物理一致性指标生成建议
        if not physics_consistency.get('overall_health', True):
            if not physics_consistency.get('month_dominance_healthy', True):
                recommendations.append(
                    f"物理一致性警告: 月令支配比({physics_consistency['month_dominance_ratio']:.2f})偏低，应≥1.5。"
                    f"建议：增加month_weight或降低hour_weight"
                )
            if not physics_consistency.get('rooting_impact_healthy', True):
                recommendations.append(
                    f"物理一致性警告: 通根影响因子({physics_consistency['rooting_impact_factor']:.2f})偏低，应≥2.0。"
                    f"建议：检查rootingWeight参数或从格判定逻辑"
                )
        
        # 如果没有具体建议，给出通用建议
        if not recommendations:
            match_rate = result.get('match_rate', 0.0)
            if match_rate < 50.0:
                recommendations.append("当前匹配率较低，建议进行全量参数调优")
            else:
                recommendations.append("当前配置表现良好，可进行微调优化")
        
        return recommendations
    
    def _format_nl_description(self, report: DiagnosisReport) -> str:
        """格式化自然语言描述"""
        desc_parts = [
            f"当前匹配率: {report.current_match_rate:.1f}% ({report.matched_cases}/{report.total_cases})"
        ]
        
        if report.main_issues:
            desc_parts.append("\n主要问题:")
            for issue in report.main_issues[:3]:  # 只显示前3个
                desc_parts.append(f"  - {issue['pattern']}: {issue['count']}个案例")
        
        if report.violation_summary['has_violations']:
            desc_parts.append("\n物理约束违反:")
            for violation in report.violation_summary['violations']:
                desc_parts.append(f"  - {violation['description']}")
        
        # 📊 添加物理一致性指标
        if report.physics_consistency:
            desc_parts.append("\n物理一致性指标:")
            for warning in report.physics_consistency.get('warnings', []):
                desc_parts.append(f"  - {warning}")
        
        if report.recommendations:
            desc_parts.append("\n优化建议:")
            for rec in report.recommendations[:3]:  # 只显示前3个
                desc_parts.append(f"  - {rec}")
        
        return "\n".join(desc_parts)
    
    def configure_optimization_strategy(self,
                                       focus_layer: str = "all",
                                       constraints: str = "soft",
                                       target_case_type: str = "all",
                                       use_cross_validation: bool = False) -> Dict[str, Any]:
        """
        MCP工具2: 设定Optuna搜索空间
        
        Args:
            focus_layer: "physics" | "structure" | "threshold" | "all"
            constraints: "strict" | "soft"
            target_case_type: "classic" | "modern" | "all"
            
        Returns:
            配置确认信息
        """
        logger.info(f"⚙️  配置优化策略: layer={focus_layer}, constraints={constraints}, case_type={target_case_type}")
        
        # 保存配置（供后续execute_optuna_study使用）
        self.optimization_config = OptimizationConfig(
            focus_layer=focus_layer,
            constraints=constraints,
            target_case_type=target_case_type,
            n_trials=50,  # 默认50次试验
            verbose=True,
            use_cross_validation=False,  # 默认关闭，可通过参数启用
            cv_train_ratio=0.7
        )
        
        return {
            'status': 'configured',
            'config': {
                'focus_layer': focus_layer,
                'constraints': constraints,
                'target_case_type': target_case_type
            },
            'message': f'优化策略已配置: 将优化{focus_layer}层，约束模式={constraints}'
        }
    
    def execute_optuna_study(self, n_trials: int = 50, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        MCP工具3: 启动Optuna优化
        
        Args:
            n_trials: Optuna试验次数
            timeout: 超时时间（秒）
            
        Returns:
            优化结果字典
        """
        if not hasattr(self, 'optimization_config'):
            # 如果没有配置，使用默认配置
            self.optimization_config = OptimizationConfig()
        
        # 更新试验次数
        self.optimization_config.n_trials = n_trials
        self.optimization_config.timeout = timeout
        
        logger.info(f"🚀 启动Optuna优化: {n_trials}次试验")
        
        # 运行优化
        opt_result = run_optuna_study(
            self.tuner,
            self.optimization_config,
            self.current_config
        )
        
        # 更新当前配置为最佳配置
        self.current_config = opt_result['best_config']
        
        # 返回结果
        return {
            'status': 'completed',
            'best_match_rate': opt_result['best_match_rate'],
            'best_loss': opt_result['best_loss'],
            'best_params': opt_result['best_params'],
            'improvement': opt_result['best_match_rate'] - self._get_baseline_match_rate(),
            'message': f'优化完成: 最佳匹配率={opt_result["best_match_rate"]:.1f}%'
        }
    
    def _get_baseline_match_rate(self) -> float:
        """获取基线匹配率"""
        result = self.tuner.evaluate_parameter_set(self.base_config)
        return result.get('match_rate', 0.0)
    
    def tune_specific_layer(self, layer_name: str, n_trials: int = 50) -> Dict[str, Any]:
        """
        便捷方法: 调优指定层
        
        Args:
            layer_name: "physics" | "structure" | "threshold"
            n_trials: 试验次数
            
        Returns:
            优化结果
        """
        # 配置策略
        self.configure_optimization_strategy(focus_layer=layer_name)
        
        # 执行优化
        return self.execute_optuna_study(n_trials=n_trials)


def main():
    """测试MCP服务器功能"""
    server = MCPTuningServer()
    
    print("="*80)
    print("🔧 MCP调优服务器测试")
    print("="*80)
    
    # 1. 运行诊断
    print("\n1️⃣  运行物理诊断...")
    diagnosis = server.run_physics_diagnosis()
    print(diagnosis['nl_description'])
    
    # 2. 配置策略
    print("\n2️⃣  配置优化策略...")
    config_result = server.configure_optimization_strategy(
        focus_layer="threshold",
        constraints="soft"
    )
    print(config_result['message'])
    
    # 3. 执行优化（小规模测试）
    print("\n3️⃣  执行优化（5次试验，用于测试）...")
    opt_result = server.execute_optuna_study(n_trials=5)
    print(f"   最佳匹配率: {opt_result['best_match_rate']:.1f}%")
    print(f"   提升: {opt_result['improvement']:.1f}%")
    
    print("\n✅ 测试完成！")


if __name__ == '__main__':
    main()

