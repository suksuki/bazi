#!/usr/bin/env python3
"""
V10.0 全量推演系统 - Jason D (财库连冲) 案例
==============================================

整合五大模块进行完整推演：
1. GAT (Graph Attention Networks) - 多头注意力机制
2. 非线性激活 (Non-linear Soft-thresholding) - 相变仿真
3. Transformer 时序建模 - 长程依赖捕捉
4. 贝叶斯推理 (Bayesian Inference) - 概率分布生成
5. RLHF 反馈循环 - 自适应调优

使用方法:
    python3 scripts/v10_full_inference_jason_d.py --case JASON_D_T1961_1010 --mode v10_full_inference --plot wealth_hologram
"""

import sys
import json
import argparse
import logging
import copy
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np
import pandas as pd

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.bayesian_inference import BayesianInference
from core.bazi_profile import BaziProfile
from controllers.wealth_verification_controller import WealthVerificationController
from core.models.wealth_case_model import WealthCaseModel

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class V10FullInferenceEngine:
    """
    V10.0 全量推演引擎
    整合五大模块进行完整推演
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化 V10.0 推演引擎
        
        Args:
            config: 配置字典，如果为 None 则使用默认配置
        """
        if config is None:
            config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
        
        # 强制启用所有 V10.0 模块
        config['use_gat'] = True
        config['use_transformer'] = True
        config['use_rlhf'] = True
        config['probabilistic_energy'] = {'use_probabilistic_energy': True}
        
        self.config = config
        self.engine = GraphNetworkEngine(config=config)
        logger.info("✅ V10.0 全量推演引擎初始化完成")
        logger.info(f"   - GAT: {config.get('use_gat', False)}")
        logger.info(f"   - Transformer: {config.get('use_transformer', False)}")
        logger.info(f"   - RLHF: {config.get('use_rlhf', False)}")
        logger.info(f"   - 概率分布: {config.get('probabilistic_energy', {}).get('use_probabilistic_energy', False)}")
    
    def load_case_data(self, case_id: str) -> Dict[str, Any]:
        """
        加载案例数据
        
        Args:
            case_id: 案例ID
            
        Returns:
            案例数据字典
        """
        # 首先尝试从 data/jason_d_case.json 加载
        jason_file = project_root / "data" / "jason_d_case.json"
        if jason_file.exists():
            with open(jason_file, 'r', encoding='utf-8') as f:
                case_data = json.load(f)
                if case_data.get('id') == case_id:
                    logger.info(f"✅ 从 data/jason_d_case.json 加载案例: {case_data.get('name', case_id)}")
                    logger.info(f"   八字: {' '.join(case_data.get('bazi', []))}")
                    logger.info(f"   日主: {case_data.get('day_master', 'N/A')}")
                    return case_data
        
        # 从 calibration_cases.json 加载
        cases_file = project_root / "calibration_cases.json"
        if cases_file.exists():
            with open(cases_file, 'r', encoding='utf-8') as f:
                cases = json.load(f)
            
            # 查找指定案例
            case_data = None
            for case in cases:
                if case.get('id') == case_id:
                    case_data = case
                    break
            
            if case_data:
                logger.info(f"✅ 从 calibration_cases.json 加载案例: {case_data.get('name', case_id)}")
                logger.info(f"   八字: {' '.join(case_data.get('bazi', []))}")
                logger.info(f"   日主: {case_data.get('day_master', 'N/A')}")
                return case_data
        
        # 如果都找不到，使用 Jason D 的硬编码数据
        if case_id == 'JASON_D_T1961_1010':
            logger.warning("⚠️ 未找到案例文件，使用硬编码的 Jason D 数据")
            case_data = {
                "id": "JASON_D_T1961_1010",
                "name": "Jason D (财库连冲)",
                "bazi": ["辛丑", "丁酉", "庚辰", "丙戌"],
                "day_master": "庚",
                "gender": "男",
                "description": "来源: Internal_Mining_Protocol_V9.3, 标签: 身旺用官, 多财库, 丑未戌三刑",
                "timeline": [
                    {
                        "year": 1999,
                        "ganzhi": "己卯",
                        "dayun": "戊戌",
                        "type": "WEALTH",
                        "real_magnitude": 50.0,
                        "desc": "公司业务快速扩张，财富开始积累。"
                    },
                    {
                        "year": 2015,
                        "ganzhi": "乙未",
                        "dayun": "壬辰",
                        "type": "WEALTH",
                        "real_magnitude": 100.0,
                        "desc": "重大资产重组，财富暴增。算法焦点：丑未冲触发财库开启 (Open Vault)。"
                    },
                    {
                        "year": 2021,
                        "ganzhi": "辛丑",
                        "dayun": "壬辰",
                        "type": "WEALTH",
                        "real_magnitude": 100.0,
                        "desc": "投资获利，财富再次爆发。算法焦点：验证丑土与未土的连续冲动效应。"
                    }
                ]
            }
            logger.info(f"✅ 使用硬编码数据: {case_data.get('name', case_id)}")
            return case_data
        
        raise ValueError(f"未找到案例: {case_id}")
    
    def step1_context_injection(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        步骤1: 注入"地面真值"上下文
        
        Args:
            case_data: 案例数据
            
        Returns:
            上下文信息
        """
        logger.info("\n" + "="*60)
        logger.info("📂 步骤1: 注入地面真值上下文 (Context Injection)")
        logger.info("="*60)
        
        bazi = case_data.get('bazi', [])
        day_master = case_data.get('day_master', '')
        
        # 使用 GAT 网络分析节点特征
        analyze_result = self.engine.analyze(
            bazi=bazi,
            day_master=day_master,
            luck_pillar=None,
            year_pillar=None
        )
        
        # 提取关键信息
        context = {
            'bazi': bazi,
            'day_master': day_master,
            'strength_score': analyze_result.get('strength_score', 0.0),
            'strength_label': analyze_result.get('strength_label', 'Unknown'),
            'element_distribution': analyze_result.get('element_distribution', {}),
            'node_features': analyze_result.get('node_features', {}),
            'attention_weights': analyze_result.get('attention_weights', {})
        }
        
        # 检测财库
        vaults = []
        for zhi in ['丑', '辰', '未', '戌']:
            if any(zhi in pillar for pillar in bazi):
                vaults.append(zhi)
        
        context['wealth_vaults'] = vaults
        context['vault_count'] = len(vaults)
        
        logger.info(f"✅ 上下文注入完成")
        logger.info(f"   身强分数: {context['strength_score']:.2f} ({context['strength_label']})")
        logger.info(f"   财库数量: {context['vault_count']} ({', '.join(vaults) if vaults else '无'})")
        
        if context.get('attention_weights'):
            logger.info(f"   GAT 注意力权重已计算")
        
        return context
    
    def step2_nonlinear_simulation(self, context: Dict[str, Any], 
                                   target_year: int, year_pillar: str, 
                                   luck_pillar: str) -> Dict[str, Any]:
        """
        步骤2: 触发非线性隧穿仿真
        
        Args:
            context: 上下文信息
            target_year: 目标年份
            year_pillar: 流年干支
            luck_pillar: 大运干支
            
        Returns:
            非线性仿真结果
        """
        logger.info("\n" + "="*60)
        logger.info(f"⚡ 步骤2: 非线性隧穿仿真 (Non-linear Simulation) - {target_year}年")
        logger.info("="*60)
        
        bazi = context['bazi']
        day_master = context['day_master']
        
        # 计算财富指数（使用非线性激活）
        wealth_result = self.engine.calculate_wealth_index(
            bazi=bazi,
            day_master=day_master,
            gender='男',  # Jason D 是男性
            luck_pillar=luck_pillar,
            year_pillar=year_pillar
        )
        
        if isinstance(wealth_result, dict):
            wealth_index = wealth_result.get('wealth_index', 0.0)
            details = wealth_result.get('details', [])
            opportunity = wealth_result.get('opportunity', 0.0)
            wealth_distribution = wealth_result.get('wealth_distribution')
            
            # 检查关键机制
            vault_opened = any('冲开财库' in d or '🏆' in d for d in details)
            vault_collapsed = any('冲提纲' in d or '灾难' in d or '💀' in d for d in details)
            trine_effect = any('三刑' in d for d in details)
            
            simulation_result = {
                'year': target_year,
                'year_pillar': year_pillar,
                'luck_pillar': luck_pillar,
                'wealth_index': wealth_index,
                'opportunity': opportunity,
                'details': details,
                'vault_opened': vault_opened,
                'vault_collapsed': vault_collapsed,
                'trine_effect': trine_effect,
                'wealth_distribution': wealth_distribution
            }
            
            logger.info(f"✅ 非线性仿真完成")
            logger.info(f"   财富指数: {wealth_index:.2f}")
            logger.info(f"   机会能量: {opportunity:.2f}")
            logger.info(f"   财库状态: {'🏆 已冲开' if vault_opened else ('💀 已坍塌' if vault_collapsed else '🔒 未变化')}")
            logger.info(f"   三刑效应: {'✅ 是' if trine_effect else '❌ 否'}")
            
            if wealth_distribution:
                mean = wealth_distribution.get('mean', wealth_index)
                std = wealth_distribution.get('std', 0.0)
                logger.info(f"   概率分布: {mean:.2f} ± {std:.2f}")
            
            return simulation_result
        else:
            logger.warning(f"⚠️ 财富指数计算返回非字典类型: {type(wealth_result)}")
            return {
                'year': target_year,
                'year_pillar': year_pillar,
                'luck_pillar': luck_pillar,
                'wealth_index': float(wealth_result) if wealth_result else 0.0,
                'details': [],
                'vault_opened': False,
                'vault_collapsed': False,
                'trine_effect': False
            }
    
    def step3_bayesian_probability(self, simulation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        步骤3: 生成贝叶斯概率分布
        
        Args:
            simulation_result: 仿真结果
            
        Returns:
            贝叶斯概率分布结果
        """
        logger.info("\n" + "="*60)
        logger.info("🎲 步骤3: 生成贝叶斯概率分布 (Probabilistic Output)")
        logger.info("="*60)
        
        wealth_index = simulation_result.get('wealth_index', 0.0)
        wealth_distribution = simulation_result.get('wealth_distribution')
        
        if wealth_distribution:
            mean = wealth_distribution.get('mean', wealth_index)
            std = wealth_distribution.get('std', 0.0)
            percentiles = wealth_distribution.get('percentiles', {})
            
            # 计算置信区间
            confidence_interval = {
                'p25': percentiles.get('p25', mean - std),
                'p50': percentiles.get('p50', mean),
                'p75': percentiles.get('p75', mean + std)
            }
            
            # 计算不确定性因子
            uncertainty_factors = BayesianInference.estimate_uncertainty_factors(
                strength_normalized=0.5,  # 简化，实际应从上下文获取
                clash_intensity=1.0 if simulation_result.get('vault_opened') else 0.0,
                has_trine=simulation_result.get('trine_effect', False),
                has_mediation=False,
                has_help=False
            )
            
            probability_result = {
                'mean': mean,
                'std': std,
                'confidence_interval': confidence_interval,
                'uncertainty_factors': uncertainty_factors,
                'risk_level': 'high' if std > 20 else ('medium' if std > 10 else 'low')
            }
            
            logger.info(f"✅ 贝叶斯概率分布生成完成")
            logger.info(f"   均值: {mean:.2f}")
            logger.info(f"   标准差: {std:.2f}")
            logger.info(f"   置信区间: [{confidence_interval['p25']:.2f}, {confidence_interval['p75']:.2f}]")
            logger.info(f"   风险等级: {probability_result['risk_level']}")
            
            return probability_result
        else:
            logger.warning("⚠️ 未找到概率分布数据，跳过贝叶斯分析")
            return {}
    
    def step4_rlhf_feedback(self, case_data: Dict[str, Any], 
                          simulation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        步骤4: RLHF 闭环调优
        
        Args:
            case_data: 案例数据
            simulation_results: 所有仿真结果
            
        Returns:
            RLHF 反馈结果
        """
        logger.info("\n" + "="*60)
        logger.info("🔄 步骤4: RLHF 闭环调优 (Evolutionary Feedback)")
        logger.info("="*60)
        
        # 获取真实事件时间线
        timeline = case_data.get('timeline', [])
        
        if not timeline:
            logger.warning("⚠️ 案例无时间线数据，跳过 RLHF 反馈")
            return {}
        
        # 比对预测值与真实值
        feedback_data = []
        for event in timeline:
            year = event.get('year')
            real_magnitude = event.get('real_magnitude', 0.0)
            
            # 查找对应的仿真结果
            sim_result = next((r for r in simulation_results if r.get('year') == year), None)
            if sim_result:
                predicted = sim_result.get('wealth_index', 0.0)
                error = abs(predicted - real_magnitude)
                
                feedback_data.append({
                    'year': year,
                    'real': real_magnitude,
                    'predicted': predicted,
                    'error': error,
                    'is_correct': error <= 20.0
                })
        
        if not feedback_data:
            logger.warning("⚠️ 无匹配的反馈数据")
            return {}
        
        # 计算统计信息
        total_count = len(feedback_data)
        correct_count = sum(1 for f in feedback_data if f['is_correct'])
        avg_error = sum(f['error'] for f in feedback_data) / total_count
        hit_rate = (correct_count / total_count * 100) if total_count > 0 else 0.0
        
        rlhf_result = {
            'total_events': total_count,
            'correct_predictions': correct_count,
            'hit_rate': hit_rate,
            'avg_error': avg_error,
            'feedback_data': feedback_data,
            'recommendations': []
        }
        
        # 生成调优建议
        if avg_error > 20:
            rlhf_result['recommendations'].append("建议调整 breakPenalty 参数")
        if hit_rate < 50:
            rlhf_result['recommendations'].append("建议优化 controlImpact 参数")
        
        logger.info(f"✅ RLHF 反馈分析完成")
        logger.info(f"   总事件数: {total_count}")
        logger.info(f"   正确预测: {correct_count}")
        logger.info(f"   命中率: {hit_rate:.1f}%")
        logger.info(f"   平均误差: {avg_error:.2f}")
        
        if rlhf_result['recommendations']:
            logger.info(f"   调优建议: {', '.join(rlhf_result['recommendations'])}")
        
        return rlhf_result
    
    def run_full_inference(self, case_id: str, target_years: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        执行完整推演流程
        
        Args:
            case_id: 案例ID
            target_years: 目标年份列表，如果为 None 则使用案例时间线中的所有年份
            
        Returns:
            完整推演结果
        """
        logger.info("\n" + "="*80)
        logger.info("🚀 开始 V10.0 全量推演")
        logger.info("="*80)
        
        # 加载案例数据
        case_data = self.load_case_data(case_id)
        
        # 步骤1: 注入上下文
        context = self.step1_context_injection(case_data)
        
        # 确定目标年份
        if target_years is None:
            timeline = case_data.get('timeline', [])
            target_years = [event.get('year') for event in timeline if event.get('year')]
        
        if not target_years:
            logger.warning("⚠️ 未找到目标年份，使用默认年份")
            target_years = [2015]  # Jason D 的关键年份
        
        # 步骤2-3: 对每个目标年份进行非线性仿真和贝叶斯分析
        simulation_results = []
        probability_results = []
        
        for year in target_years:
            # 查找该年的事件信息
            event = next((e for e in case_data.get('timeline', []) if e.get('year') == year), None)
            if event:
                year_pillar = event.get('ganzhi', '')
                luck_pillar = event.get('dayun', '')
            else:
                # 如果没有事件信息，使用默认值
                logger.warning(f"⚠️ {year}年无事件信息，使用默认干支")
                year_pillar = ''
                luck_pillar = ''
            
            # 步骤2: 非线性仿真
            sim_result = self.step2_nonlinear_simulation(context, year, year_pillar, luck_pillar)
            simulation_results.append(sim_result)
            
            # 步骤3: 贝叶斯概率分布
            prob_result = self.step3_bayesian_probability(sim_result)
            if prob_result:
                probability_results.append({
                    'year': year,
                    **prob_result
                })
        
        # 步骤4: RLHF 反馈
        rlhf_result = self.step4_rlhf_feedback(case_data, simulation_results)
        
        # 汇总结果
        full_result = {
            'case_id': case_id,
            'case_name': case_data.get('name', ''),
            'context': context,
            'simulation_results': simulation_results,
            'probability_results': probability_results,
            'rlhf_feedback': rlhf_result,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("\n" + "="*80)
        logger.info("✅ V10.0 全量推演完成")
        logger.info("="*80)
        
        return full_result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='V10.0 全量推演系统')
    parser.add_argument('--case', type=str, default='JASON_D_T1961_1010',
                       help='案例ID (默认: JASON_D_T1961_1010)')
    parser.add_argument('--mode', type=str, default='v10_full_inference',
                       choices=['v10_full_inference'],
                       help='推演模式')
    parser.add_argument('--plot', type=str, default='wealth_hologram',
                       choices=['wealth_hologram', 'none'],
                       help='可视化类型')
    parser.add_argument('--years', type=str, default=None,
                       help='目标年份列表，用逗号分隔 (例如: 1999,2015,2021)')
    parser.add_argument('--output', type=str, default=None,
                       help='输出文件路径 (JSON格式)')
    
    args = parser.parse_args()
    
    # 解析目标年份
    target_years = None
    if args.years:
        target_years = [int(y.strip()) for y in args.years.split(',')]
    
    # 初始化推演引擎
    engine = V10FullInferenceEngine()
    
    # 执行推演
    result = engine.run_full_inference(args.case, target_years)
    
    # 保存结果
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 结果已保存到: {output_path}")
    else:
        # 默认保存到 reports 目录
        reports_dir = project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        output_path = reports_dir / f"v10_inference_{args.case}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 结果已保存到: {output_path}")
    
    # 打印关键结果摘要
    print("\n" + "="*80)
    print("📊 推演结果摘要")
    print("="*80)
    print(f"案例: {result['case_name']}")
    print(f"推演年份数: {len(result['simulation_results'])}")
    
    if result['rlhf_feedback']:
        rlhf = result['rlhf_feedback']
        print(f"命中率: {rlhf['hit_rate']:.1f}%")
        print(f"平均误差: {rlhf['avg_error']:.2f}")
    
    print("\n关键年份推演结果:")
    for sim in result['simulation_results']:
        year = sim.get('year', 'N/A')
        wealth = sim.get('wealth_index', 0.0)
        vault_status = '🏆' if sim.get('vault_opened') else ('💀' if sim.get('vault_collapsed') else '🔒')
        print(f"  {year}年: 财富指数={wealth:.2f} {vault_status}")
    
    print("\n" + "="*80)
    print("✅ 推演完成！详细结果请查看输出文件。")
    print("="*80)


if __name__ == '__main__':
    import copy
    main()

