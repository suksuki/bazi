#!/usr/bin/env python3
"""
FDS-V1.1 Step 3-5 拟合脚本：A-03 羊刃架杀
执行多维特征提取、方程拟合、动态扩展与全息注册
"""

import sys
from pathlib import Path
import json
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from controllers.holographic_pattern_controller import HolographicPatternController
from core.trinity.core.unified_arbitrator_master import QuantumUniversalFramework
from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FDSV11FittingEngine:
    """
    FDS-V1.1 拟合引擎
    执行Step 3-5的拟合工作
    """
    
    def __init__(self, pattern_id: str):
        self.pattern_id = pattern_id
        self.controller = HolographicPatternController()
        self.framework = QuantumUniversalFramework()
        self.pattern = self.controller.get_pattern_by_id(pattern_id)
        
        if not self.pattern:
            raise ValueError(f"格局 {pattern_id} 不存在")
        
        logger.info(f"初始化FDS-V1.1拟合引擎: {pattern_id}")
    
    def step3_modeling(self, samples: List[Dict]) -> Dict[str, Any]:
        """
        Step 3: 多维特征提取与方程拟合
        
        Args:
            samples: Tier A标准集样本
            
        Returns:
            拟合结果字典
        """
        logger.info("=" * 70)
        logger.info("Step 3: 多维特征提取与方程拟合")
        logger.info("=" * 70)
        
        results = []
        sai_values = []
        total = len(samples)
        
        print(f"处理 {total} 个样本...")
        
        for i, sample in enumerate(samples):
            if (i + 1) % 50 == 0:
                print(f"  进度: {i+1}/{total} ({(i+1)/total*100:.1f}%)")
            chart = sample['chart']
            day_master = sample['day_master']
            
            try:
                # 计算SAI和场强
                binfo = {'day_master': day_master}
                ctx = {'scenario': 'default'}
                result = self.framework.arbitrate_bazi(chart, binfo, ctx)
                
                # 从正确的位置提取SAI
                # SAI在physics.stress.SAI或verdict.structure中
                sai = 0.0
                if 'physics' in result and 'stress' in result['physics']:
                    sai = result['physics']['stress'].get('SAI', 0.0)
                elif 'verdict' in result and 'structure' in result['verdict']:
                    # 从"熵=2.26 | SAI=1.76 | IC=0.00"格式中提取
                    structure_str = result['verdict']['structure']
                    import re
                    match = re.search(r'SAI=([\d.]+)', structure_str)
                    if match:
                        sai = float(match.group(1))
                
                sai_values.append(sai)
                
                # 获取场强（十神能量）- 需要通过LogicArbitrator计算
                from core.trinity.core.intelligence.logic_arbitrator import LogicArbitrator
                arbitrator = LogicArbitrator()
                intensities = arbitrator.calculate_field_intensities(
                    pillars=chart,
                    day_master=day_master,
                    phase_progress=0.5,
                    dispersion_engine=None,
                    geo_factor=1.0
                )
                
                # Step 3.1: 频率转化 - 将干支字符转化为物理频率向量
                # 简化实现：使用十神能量作为频率向量
                frequency_vector = {
                    '比劫': intensities.get('比肩', 0.0) + intensities.get('劫财', 0.0),
                    '食伤': intensities.get('食神', 0.0) + intensities.get('伤官', 0.0),
                    '财星': intensities.get('正财', 0.0) + intensities.get('偏财', 0.0),
                    '官杀': intensities.get('正官', 0.0) + intensities.get('七杀', 0.0),
                    '印枭': intensities.get('正印', 0.0) + intensities.get('偏印', 0.0)
                }
                
                # Step 3.2: 计算核心方程：S_balance = E_blade / E_kill
                yang_ren_energy = 0.0  # 羊刃能量
                qi_sha_energy = intensities.get('七杀', 0.0) + intensities.get('正官', 0.0)
                
                # 计算羊刃能量（从比劫能量中提取，羊刃是比劫的强化版）
                bi_jian_energy = intensities.get('比肩', 0.0) + intensities.get('劫财', 0.0)
                yang_ren_energy = bi_jian_energy * 1.5  # 羊刃能量 = 比劫能量 * 1.5
                
                if qi_sha_energy > 0:
                    s_balance = yang_ren_energy / qi_sha_energy
                else:
                    s_balance = 0.0
                
                # Step 3.3: 非线性激活 - Sigmoid函数（阈值效应）
                # 使用Sigmoid模拟"压死骆驼的最后一根稻草"效应
                def sigmoid(x, k=1.0, x0=0.8):
                    """Sigmoid激活函数"""
                    import math
                    return 1.0 / (1.0 + math.exp(-k * (x - x0)))
                
                # 对SAI应用Sigmoid激活
                activation_params = self.pattern['tensor_operator'].get('activation_function', {}).get('parameters', {})
                k = activation_params.get('k', 1.0)
                x0 = activation_params.get('collapse_threshold', 0.8)
                sai_activated = sigmoid(sai, k, x0)
                
                # Step 3.4: 相变判定
                # 量子隧穿 (Tunneling)：遇冲爆发
                # 结构坍缩 (Collapse)：遇冲崩盘
                phase_state = "STABLE"
                if sai > x0 * 1.2:  # 高能级
                    phase_state = "TUNNELING_RISK"  # 可能隧穿
                elif sai < x0 * 0.5:  # 低能级
                    phase_state = "COLLAPSE_RISK"  # 可能坍缩
                
                # 计算五维投影
                weights = self.pattern['tensor_operator']['weights']
                projection = {
                    'E': sai * weights.get('E', 0.0),
                    'O': sai * weights.get('O', 0.0),
                    'M': sai * weights.get('M', 0.0),
                    'S': sai * weights.get('S', 0.0),
                    'R': sai * weights.get('R', 0.0)
                }
                
                results.append({
                    'sample_index': i,
                    'chart': chart,
                    'day_master': day_master,
                    'sai': sai,
                    'sai_activated': sai_activated,  # Sigmoid激活后的SAI
                    's_balance': s_balance,
                    'yang_ren_energy': yang_ren_energy,
                    'qi_sha_energy': qi_sha_energy,
                    'frequency_vector': frequency_vector,  # 频率向量
                    'phase_state': phase_state,  # 相变状态
                    'projection': projection,
                    'intensities': intensities
                })
                
            except Exception as e:
                logger.error(f"处理样本 {i} 失败: {e}")
                continue
        
        # 统计分析
        if sai_values:
            sai_mean = np.mean(sai_values)
            sai_std = np.std(sai_values)
            sai_min = np.min(sai_values)
            sai_max = np.max(sai_values)
        else:
            sai_mean = sai_std = sai_min = sai_max = 0.0
        
        print(f"✅ Step 3完成: 处理了 {len(results)} 个样本")
        print(f"SAI统计: 均值={sai_mean:.4f}, 标准差={sai_std:.4f}, 范围=[{sai_min:.4f}, {sai_max:.4f}]")
        
        return {
            'step': 3,
            'samples_processed': len(results),
            'sai_statistics': {
                'mean': float(sai_mean),
                'std': float(sai_std),
                'min': float(sai_min),
                'max': float(sai_max)
            },
            'results': results
        }
    
    def step4_dynamic_simulation(self, step3_results: Dict) -> Dict[str, Any]:
        """
        Step 4: 动态扩展与张量耦合
        
        Args:
            step3_results: Step 3的拟合结果
            
        Returns:
            动态仿真结果
        """
        logger.info("=" * 70)
        logger.info("Step 4: 动态扩展与张量耦合")
        logger.info("=" * 70)
        
        # 选择前10个样本进行动态仿真（演示）
        demo_samples = step3_results['results'][:10]
        
        dynamic_results = []
        
        for sample_data in demo_samples:
            chart = sample_data['chart']
            day_master = sample_data['day_master']
            
            # 模拟大运和流年
            # 简化：使用随机大运和流年进行演示
            engine = SyntheticBaziEngine()
            luck_pillars = list(engine.JIA_ZI[:10])  # 前10个大运
            year_pillars = list(engine.JIA_ZI[:5])   # 前5个流年
            
            sample_dynamic = []
            
            for luck_pillar in luck_pillars[:3]:  # 只测试3个大运
                for year_pillar in year_pillars[:2]:  # 每个大运测试2个流年
                    try:
                        binfo = {'day_master': day_master}
                        ctx = {
                            'luck_pillar': luck_pillar,
                            'annual_pillar': year_pillar,
                            'scenario': 'dynamic'
                        }
                        
                        result = self.framework.arbitrate_bazi(chart, binfo, ctx)
                        sai = result.get('sai', 0.0)
                        
                        # 计算五维投影
                        weights = self.pattern['tensor_operator']['weights']
                        projection = {
                            'E': sai * weights.get('E', 0.0),
                            'O': sai * weights.get('O', 0.0),
                            'M': sai * weights.get('M', 0.0),
                            'S': sai * weights.get('S', 0.0),
                            'R': sai * weights.get('R', 0.0)
                        }
                        
                        sample_dynamic.append({
                            'luck_pillar': luck_pillar,
                            'year_pillar': year_pillar,
                            'sai': sai,
                            'projection': projection
                        })
                    except Exception as e:
                        logger.warning(f"动态仿真失败: {e}")
                        continue
            
            dynamic_results.append({
                'sample_index': sample_data['sample_index'],
                'chart': chart,
                'base_sai': sample_data['sai'],
                'dynamic_simulations': sample_dynamic
            })
        
        print(f"✅ Step 4完成: 对 {len(demo_samples)} 个样本进行了动态仿真")
        
        return {
            'step': 4,
            'samples_simulated': len(dynamic_results),
            'results': dynamic_results
        }
    
    def step5_registry(self, step3_results: Dict, step4_results: Dict) -> Dict[str, Any]:
        """
        Step 5: 专题封卷与全息注册
        
        Args:
            step3_results: Step 3的拟合结果
            step4_results: Step 4的动态仿真结果
            
        Returns:
            注册结果
        """
        logger.info("=" * 70)
        logger.info("Step 5: 专题封卷与全息注册")
        logger.info("=" * 70)
        
        # 获取SAI基准
        sai_mean = step3_results['sai_statistics']['mean']
        
        # 更新注册表
        registry_path = self.controller.registry_path
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        
        pattern = registry['patterns'][self.pattern_id]
        
        # 更新audit_trail
        if 'audit_trail' not in pattern:
            pattern['audit_trail'] = {}
        
        pattern['audit_trail'].update({
            'fds_fitting': {
                'status': 'completed',
                'completed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'step3_results': {
                    'samples_processed': step3_results['samples_processed'],
                    'sai_mean': sai_mean,
                    'sai_std': step3_results['sai_statistics']['std']
                },
                'step4_results': {
                    'samples_simulated': step4_results['samples_simulated']
                }
            },
            'sai_baseline': sai_mean,
            'sai_description': f"基于{step3_results['samples_processed']}个Tier A样本的SAI均值"
        })
        
        # 保存注册表
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Step 5完成: 已更新注册表，SAI基准={sai_mean:.4f}")
        
        return {
            'step': 5,
            'sai_baseline': sai_mean,
            'registry_updated': True
        }


def main():
    print("=" * 70)
    print("🚀 FDS-V1.1 Step 3-5 拟合工作：A-03 羊刃架杀")
    print("=" * 70)
    print()
    
    # 加载Tier A标准集
    data_file = project_root / "data" / "holographic_pattern" / "A-03_Standard_Dataset.json"
    
    if not data_file.exists():
        print(f"❌ 标准集文件不存在: {data_file}")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    samples = data['samples']
    print(f"✅ 加载Tier A标准集: {len(samples)} 个样本")
    print()
    
    # 初始化拟合引擎
    fitting_engine = FDSV11FittingEngine('A-03')
    
    # Step 3: 多维特征提取与方程拟合
    print("开始Step 3...")
    step3_results = fitting_engine.step3_modeling(samples)
    print()
    
    # Step 4: 动态扩展与张量耦合
    print("开始Step 4...")
    step4_results = fitting_engine.step4_dynamic_simulation(step3_results)
    print()
    
    # Step 5: 专题封卷与全息注册
    print("开始Step 5...")
    step5_results = fitting_engine.step5_registry(step3_results, step4_results)
    print()
    
    # 保存拟合结果
    output_file = project_root / "data" / "holographic_pattern" / "A-03_FDS_Fitting_Results.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    fitting_summary = {
        'pattern_id': 'A-03',
        'pattern_name': '羊刃架杀',
        'fitting_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'fds_version': 'V1.1',
        'step3': step3_results,
        'step4': step4_results,
        'step5': step5_results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fitting_summary, f, ensure_ascii=False, indent=2)
    
    print("=" * 70)
    print("✅ FDS-V1.1 Step 3-5 拟合完成")
    print("=" * 70)
    print()
    print("【拟合结果摘要】")
    print("-" * 70)
    print(f"Step 3: 处理了 {step3_results['samples_processed']} 个样本")
    print(f"  SAI均值: {step3_results['sai_statistics']['mean']:.4f}")
    print(f"  SAI标准差: {step3_results['sai_statistics']['std']:.4f}")
    print()
    print(f"Step 4: 对 {step4_results['samples_simulated']} 个样本进行了动态仿真")
    print()
    print(f"Step 5: SAI基准已锁定: {step5_results['sai_baseline']:.4f}")
    print()
    print(f"✅ 拟合结果已保存: {output_file}")
    print()
    print("=" * 70)


if __name__ == '__main__':
    main()

