#!/usr/bin/env python3
"""
FDS-V1.4 Step 6: 动态盲测 (Dynamic Blind Test)
验证A-03在流年周期中的动态识别与相变能力

测试案例：甲申 庚午 甲申 乙亥
测试周期：2024 (甲辰) - 2035 (乙卯)
监测指标：
1. Pattern Match Score (相似度)
2. Integrity Alpha (完整度)
3. 5D Tensor变化
4. 成格/破格状态
"""

import sys
from pathlib import Path
import json
from typing import Dict, List, Any
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.registry_loader import RegistryLoader
from core.math_engine import project_tensor_with_matrix, tensor_normalize
from core.physics_engine import compute_energy_flux, check_trigger, calculate_integrity_alpha
from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine

# 流年干支映射（2024-2035）
YEAR_GANZHI_MAP = {
    2024: "甲辰",
    2025: "乙巳",
    2026: "丙午",
    2027: "丁未",
    2028: "戊申",
    2029: "己酉",
    2030: "庚戌",
    2031: "辛亥",
    2032: "壬子",
    2033: "癸丑",
    2034: "甲寅",
    2035: "乙卯"
}


class A03DynamicTester:
    """
    A-03动态测试器
    验证格局在流年周期中的动态识别与相变
    """
    
    def __init__(self):
        self.registry_loader = RegistryLoader()
        self.pattern_id = 'A-03'
        self.pattern = self.registry_loader.get_pattern(self.pattern_id)
        
        if not self.pattern:
            raise ValueError(f"格局 {self.pattern_id} 不存在")
        
        # 获取transfer_matrix
        physics_kernel = self.pattern.get('physics_kernel', {})
        self.transfer_matrix = physics_kernel.get('transfer_matrix')
        
        if not self.transfer_matrix:
            raise ValueError("格局缺少transfer_matrix配置")
        
        # 获取feature_anchors
        self.feature_anchors = self.pattern.get('feature_anchors', {})
        self.standard_centroid = self.feature_anchors.get('standard_centroid', {}).get('vector', {})
    
    def calculate_frequency_vector(self, chart: List[str], day_master: str) -> Dict[str, float]:
        """计算十神频率向量"""
        parallel = compute_energy_flux(chart, day_master, "比肩") + \
                   compute_energy_flux(chart, day_master, "劫财")
        resource = compute_energy_flux(chart, day_master, "正印") + \
                   compute_energy_flux(chart, day_master, "偏印")
        power = compute_energy_flux(chart, day_master, "七杀") + \
                compute_energy_flux(chart, day_master, "正官")
        wealth = compute_energy_flux(chart, day_master, "正财") + \
                 compute_energy_flux(chart, day_master, "偏财")
        output = compute_energy_flux(chart, day_master, "食神") + \
                 compute_energy_flux(chart, day_master, "伤官")
        
        return {
            "parallel": parallel,
            "resource": resource,
            "power": power,
            "wealth": wealth,
            "output": output
        }
    
    def _check_pattern_state_internal(
        self,
        chart: List[str],
        day_master: str,
        day_branch: str,
        luck_pillar: str,
        year_pillar: str,
        alpha: float
    ) -> Dict[str, Any]:
        """
        检查成格/破格状态（内部实现）
        """
        dynamic_states = self.pattern.get('dynamic_states', {})
        collapse_rules = dynamic_states.get('collapse_rules', [])
        crystallization_rules = dynamic_states.get('crystallization_rules', [])
        integrity_threshold = self.pattern.get('physics_kernel', {}).get('integrity_threshold', 0.45)
        
        # 构建context
        energy_flux = {
            "wealth": compute_energy_flux(chart, day_master, "偏财") + 
                      compute_energy_flux(chart, day_master, "正财"),
            "resource": compute_energy_flux(chart, day_master, "正印") + 
                       compute_energy_flux(chart, day_master, "偏印")
        }
        
        context = {
            "chart": chart,
            "day_master": day_master,
            "day_branch": day_branch,
            "luck_pillar": luck_pillar,
            "year_pillar": year_pillar,
            "energy_flux": energy_flux
        }
        
        # 检查破格条件
        for rule in collapse_rules:
            trigger_name = rule.get('trigger')
            if trigger_name and check_trigger(trigger_name, context):
                return {
                    "state": "COLLAPSED",
                    "alpha": alpha,
                    "matrix": rule.get('fallback_matrix', 'Standard'),
                    "trigger": trigger_name,
                    "action": rule.get('action')
                }
        
        # 检查成格条件
        for rule in crystallization_rules:
            condition_name = rule.get('condition')
            if condition_name and check_trigger(condition_name, context):
                return {
                    "state": "CRYSTALLIZED",
                    "alpha": alpha,
                    "matrix": rule.get('target_matrix', self.pattern_id),
                    "trigger": condition_name,
                    "action": rule.get('action'),
                    "validity": rule.get('validity', 'Permanent')
                }
        
        # 根据alpha判断
        if alpha < integrity_threshold:
            return {
                "state": "COLLAPSED",
                "alpha": alpha,
                "matrix": "Standard",
                "trigger": "Low_Integrity"
            }
        
        return {
            "state": "STABLE",
            "alpha": alpha,
            "matrix": self.pattern_id
        }
    
    def calculate_tensor_with_matrix(
        self,
        chart: List[str],
        day_master: str,
        luck_pillar: str = "",
        year_pillar: str = ""
    ) -> Dict[str, Any]:
        """
        使用transfer_matrix计算5维张量
        
        Args:
            chart: 四柱八字
            day_master: 日主
            luck_pillar: 大运（可选）
            year_pillar: 流年（可选）
            
        Returns:
            包含projection、alpha、pattern_state等的字典
        """
        # 构建六柱（原局+大运+流年）用于计算
        # 注意：这里简化处理，实际应该考虑流年对原局的影响
        extended_chart = chart.copy()
        if luck_pillar:
            extended_chart.append(luck_pillar)
        if year_pillar:
            extended_chart.append(year_pillar)
        
        # 计算十神频率向量（基于原局，但考虑流年影响）
        # 简化：流年主要影响能量流，不改变原局结构
        frequency_vector = self.calculate_frequency_vector(chart, day_master)
        
        # 如果流年有影响，可以在这里调整frequency_vector
        # 例如：流年透杀，增加power；流年透印，增加resource
        if year_pillar:
            year_stem = year_pillar[0]
            from core.trinity.core.nexus.definitions import BaziParticleNexus
            year_ten_god = BaziParticleNexus.get_shi_shen(year_stem, day_master)
            
            # 流年影响调整（简化：流年透干有影响）
            if year_ten_god in ['七杀', '正官']:
                frequency_vector['power'] += 0.5  # 流年透杀，增加官杀能量
            elif year_ten_god in ['正印', '偏印']:
                frequency_vector['resource'] += 0.3  # 流年透印，增加印星能量
            elif year_ten_god in ['比肩', '劫财']:
                frequency_vector['parallel'] += 0.3  # 流年透比劫，增加比劫能量
        
        # 使用transfer_matrix计算5维投影
        projection = project_tensor_with_matrix(frequency_vector, self.transfer_matrix)
        
        # 归一化投影
        normalized_projection = tensor_normalize(projection)
        
        # 计算结构完整性alpha
        day_branch = chart[2][1] if len(chart) > 2 and len(chart[2]) >= 2 else ""
        
        # 计算能量流（用于alpha计算）
        energy_flux = {
            "wealth": compute_energy_flux(chart, day_master, "偏财") + 
                      compute_energy_flux(chart, day_master, "正财"),
            "resource": compute_energy_flux(chart, day_master, "正印") + 
                       compute_energy_flux(chart, day_master, "偏印")
        }
        
        alpha = calculate_integrity_alpha(
            chart, day_master, day_branch,
            luck_pillar=luck_pillar,
            year_pillar=year_pillar,
            energy_flux=energy_flux
        )
        
        # 检查成格/破格状态（直接实现逻辑）
        pattern_state = self._check_pattern_state_internal(
            chart, day_master, day_branch,
            luck_pillar, year_pillar, alpha
        )
        
        # 格局识别（Step 6）
        recognition_result = self.registry_loader.pattern_recognition(
            normalized_projection, self.pattern_id
        )
        
        return {
            'projection': normalized_projection,
            'raw_projection': projection,
            'alpha': alpha,
            'pattern_state': pattern_state,
            'recognition': recognition_result,
            'frequency_vector': frequency_vector
        }
    
    def simulate_year_cycle(
        self,
        natal_chart: List[str],
        day_master: str,
        start_year: int = 2024,
        end_year: int = 2035,
        luck_pillar: str = ""
    ) -> List[Dict[str, Any]]:
        """
        模拟流年周期
        
        Args:
            natal_chart: 四柱八字
            day_master: 日主
            start_year: 起始年份
            end_year: 结束年份
            luck_pillar: 大运（可选）
            
        Returns:
            每年的计算结果列表
        """
        results = []
        
        for year in range(start_year, end_year + 1):
            year_pillar = YEAR_GANZHI_MAP.get(year, "")
            
            if not year_pillar:
                continue
            
            # 计算该年的张量
            tensor_result = self.calculate_tensor_with_matrix(
                natal_chart, day_master,
                luck_pillar=luck_pillar,
                year_pillar=year_pillar
            )
            
            # 提取关键指标
            result = {
                'year': year,
                'year_pillar': year_pillar,
                'projection': tensor_result['projection'],
                'alpha': tensor_result['alpha'],
                'pattern_state': tensor_result['pattern_state'],
                'recognition': tensor_result['recognition'],
                'sai': sum(abs(v) for v in tensor_result['raw_projection'].values())
            }
            
            results.append(result)
        
        return results
    
    def analyze_dynamic_changes(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析动态变化
        
        Returns:
            分析结果字典
        """
        analysis = {
            'alpha_changes': [],
            'pattern_state_changes': [],
            'recognition_changes': [],
            's_axis_changes': [],
            'o_axis_changes': [],
            'critical_years': []
        }
        
        prev_alpha = None
        prev_state = None
        prev_recognition = None
        
        for result in results:
            year = result['year']
            alpha = result['alpha']
            state = result['pattern_state']
            recognition = result['recognition']
            projection = result['projection']
            
            # Alpha变化
            if prev_alpha is not None:
                alpha_change = alpha - prev_alpha
                analysis['alpha_changes'].append({
                    'year': year,
                    'change': alpha_change,
                    'alpha': alpha
                })
                
                # 关键年份：Alpha大幅下降
                if alpha_change < -0.2:
                    analysis['critical_years'].append({
                        'year': year,
                        'type': 'ALPHA_COLLAPSE',
                        'alpha': alpha,
                        'change': alpha_change
                    })
            
            # 状态变化
            if prev_state and prev_state.get('state') != state.get('state'):
                analysis['pattern_state_changes'].append({
                    'year': year,
                    'from': prev_state.get('state'),
                    'to': state.get('state'),
                    'trigger': state.get('trigger')
                })
            
            # 识别变化
            if prev_recognition and prev_recognition.get('matched') != recognition.get('matched'):
                analysis['recognition_changes'].append({
                    'year': year,
                    'from_matched': prev_recognition.get('matched'),
                    'to_matched': recognition.get('matched'),
                    'similarity': recognition.get('similarity')
                })
            
            # S轴和O轴变化
            analysis['s_axis_changes'].append({
                'year': year,
                'value': projection.get('S', 0.0)
            })
            analysis['o_axis_changes'].append({
                'year': year,
                'value': projection.get('O', 0.0)
            })
            
            prev_alpha = alpha
            prev_state = state
            prev_recognition = recognition
        
        return analysis


def main():
    print("=" * 70)
    print("🧪 FDS-V1.4 Step 6: 动态盲测 (Dynamic Blind Test)")
    print("=" * 70)
    print()
    
    # 测试案例：甲申 庚午 甲申 乙亥
    natal_chart = ["甲申", "庚午", "甲申", "乙亥"]
    day_master = "甲"
    
    print("【测试案例】")
    print("-" * 70)
    print(f"八字: {' '.join(natal_chart)}")
    print(f"日主: {day_master}")
    print(f"测试周期: 2024-2035 (12年)")
    print()
    
    # 初始化测试器
    tester = A03DynamicTester()
    
    # 模拟流年周期
    print("【开始模拟流年周期...】")
    print("-" * 70)
    results = tester.simulate_year_cycle(natal_chart, day_master, 2024, 2035)
    
    # 分析动态变化
    analysis = tester.analyze_dynamic_changes(results)
    
    # 输出结果
    print()
    print("=" * 70)
    print("📊 动态识别结果")
    print("=" * 70)
    print()
    
    print("【年度张量变化】")
    print("-" * 70)
    for result in results:
        year = result['year']
        year_pillar = result['year_pillar']
        alpha = result['alpha']
        state = result['pattern_state'].get('state', 'UNKNOWN')
        recognition = result['recognition']
        projection = result['projection']
        
        matched = "✅" if recognition.get('matched') else "❌"
        similarity = recognition.get('similarity', 0.0)
        
        print(f"{year} ({year_pillar}):")
        print(f"  Alpha: {alpha:.4f} | 状态: {state} | 匹配: {matched} ({similarity:.4f})")
        print(f"  5D投影: E={projection.get('E', 0):.4f}, O={projection.get('O', 0):.4f}, "
              f"M={projection.get('M', 0):.4f}, S={projection.get('S', 0):.4f}, R={projection.get('R', 0):.4f}")
        print()
    
    print("【关键变化分析】")
    print("-" * 70)
    
    # Alpha变化
    if analysis['alpha_changes']:
        print("Alpha变化:")
        for change in analysis['alpha_changes']:
            if abs(change['change']) > 0.1:
                print(f"  {change['year']}: {change['change']:+.4f} (Alpha: {change['alpha']:.4f})")
        print()
    
    # 状态变化
    if analysis['pattern_state_changes']:
        print("格局状态变化:")
        for change in analysis['pattern_state_changes']:
            print(f"  {change['year']}: {change['from']} → {change['to']} (触发: {change.get('trigger', 'N/A')})")
        print()
    
    # 关键年份
    if analysis['critical_years']:
        print("⚠️  关键年份（Alpha大幅下降）:")
        for critical in analysis['critical_years']:
            print(f"  {critical['year']}: Alpha={critical['alpha']:.4f} (变化: {critical['change']:.4f})")
        print()
    
    # S轴和O轴趋势
    print("【S轴和O轴趋势】")
    print("-" * 70)
    s_values = [r['value'] for r in analysis['s_axis_changes']]
    o_values = [r['value'] for r in analysis['o_axis_changes']]
    
    print(f"S轴范围: [{min(s_values):.4f}, {max(s_values):.4f}]")
    print(f"O轴范围: [{min(o_values):.4f}, {max(o_values):.4f}]")
    print()
    
    # 验证预期
    print("【验证预期】")
    print("-" * 70)
    
    # 检查2028和2029年（申/酉年，可能冲克）
    for result in results:
        if result['year'] in [2028, 2029]:
            year = result['year']
            alpha = result['alpha']
            s_value = result['projection'].get('S', 0.0)
            state = result['pattern_state'].get('state', 'UNKNOWN')
            
            print(f"{year}年:")
            print(f"  Alpha: {alpha:.4f} {'⚠️ 下降' if alpha < 0.4 else '✅稳定'}")
            print(f"  S轴: {s_value:.4f} {'⚠️ 飙升' if s_value > 0.2 else '✅正常'}")
            print(f"  状态: {state}")
            print()
    
    # 保存结果
    output_file = project_root / "data" / "holographic_pattern" / "A-03_DynamicTest_Results.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        'test_case': {
            'chart': natal_chart,
            'day_master': day_master,
            'period': '2024-2035'
        },
        'results': results,
        'analysis': analysis,
        'test_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print("=" * 70)
    print("✅ 动态测试完成")
    print("=" * 70)
    print(f"结果已保存: {output_file}")
    print()


if __name__ == '__main__':
    main()

