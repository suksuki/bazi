"""
命运轨迹模拟器 (Fate Trajectory Simulator)
实时计算用户在时间序列中的命运演化轨迹

从测试脚本中提取的核心逻辑，用于UI实时演算
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.registry_loader import RegistryLoader
from core.math_engine import project_tensor_with_matrix, tensor_normalize
from core.physics_engine import compute_energy_flux, check_trigger, calculate_integrity_alpha
from core.trinity.core.nexus.definitions import BaziParticleNexus

logger = logging.getLogger(__name__)


class FateSimulator:
    """
    命运轨迹模拟器
    计算用户在时间序列中的命运演化
    """
    
    def __init__(self):
        self.registry_loader = RegistryLoader()
    
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
        pattern: Dict[str, Any],
        chart: List[str],
        day_master: str,
        day_branch: str,
        luck_pillar: str,
        year_pillar: str,
        alpha: float
    ) -> Dict[str, Any]:
        """检查成格/破格状态（内部实现）"""
        dynamic_states = pattern.get('dynamic_states', {})
        collapse_rules = dynamic_states.get('collapse_rules', [])
        crystallization_rules = dynamic_states.get('crystallization_rules', [])
        integrity_threshold = pattern.get('physics_kernel', {}).get('integrity_threshold', 0.45)
        
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
                    "matrix": rule.get('target_matrix', pattern.get('id')),
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
            "matrix": pattern.get('id', 'Standard')
        }
    
    def calculate_tensor_for_year(
        self,
        pattern_id: str,
        chart: List[str],
        day_master: str,
        year: int,
        year_pillar: str,
        luck_pillar: str = ""
    ) -> Dict[str, Any]:
        """
        计算指定年份的5维张量
        
        Args:
            pattern_id: 格局ID（如'A-03'）
            chart: 四柱八字
            day_master: 日主
            year: 年份
            year_pillar: 流年干支
            luck_pillar: 大运干支（可选）
            
        Returns:
            包含projection、alpha、pattern_state等的字典
        """
        pattern = self.registry_loader.get_pattern(pattern_id)
        if not pattern:
            # 如果格局不存在，使用标准矩阵
            pattern = {'id': 'Standard', 'physics_kernel': {}, 'dynamic_states': {}}
        
        # 获取transfer_matrix
        physics_kernel = pattern.get('physics_kernel', {})
        transfer_matrix = physics_kernel.get('transfer_matrix')
        
        if not transfer_matrix:
            # 如果没有transfer_matrix，使用简化计算
            frequency_vector = self.calculate_frequency_vector(chart, day_master)
            # 简化投影（如果没有矩阵，使用默认映射）
            projection = {
                'E': frequency_vector.get('parallel', 0.0) * 0.3,
                'O': frequency_vector.get('power', 0.0) * 0.4,
                'M': frequency_vector.get('wealth', 0.0) * 0.1,
                'S': abs(frequency_vector.get('power', 0.0) - frequency_vector.get('resource', 0.0)) * 0.15,
                'R': frequency_vector.get('output', 0.0) * 0.05
            }
            normalized_projection = tensor_normalize(projection)
        else:
            # 使用transfer_matrix计算
            frequency_vector = self.calculate_frequency_vector(chart, day_master)
            
            # 如果流年有影响，调整frequency_vector
            if year_pillar:
                year_stem = year_pillar[0]
                year_ten_god = BaziParticleNexus.get_shi_shen(year_stem, day_master)
                
                if year_ten_god in ['七杀', '正官']:
                    frequency_vector['power'] += 0.5
                elif year_ten_god in ['正印', '偏印']:
                    frequency_vector['resource'] += 0.3
                elif year_ten_god in ['比肩', '劫财']:
                    frequency_vector['parallel'] += 0.3
            
            projection = project_tensor_with_matrix(frequency_vector, transfer_matrix)
            normalized_projection = tensor_normalize(projection)
        
        # 计算结构完整性alpha
        day_branch = chart[2][1] if len(chart) > 2 and len(chart[2]) >= 2 else ""
        
        energy_flux = {
            "wealth": compute_energy_flux(chart, day_master, "偏财") + 
                      compute_energy_flux(chart, day_master, "正财"),
            "resource": compute_energy_flux(chart, day_master, "正印") + 
                       compute_energy_flux(chart, day_master, "偏印")
        }
        
        # 检测事件（简化：基于流年判断）
        flux_events = []
        if year_pillar:
            year_branch = year_pillar[1] if len(year_pillar) >= 2 else ""
            # 检查日支是否被冲
            from core.physics_engine import check_clash
            if check_clash(day_branch, year_branch):
                flux_events.append("Day_Branch_Clash")
            # 检查是否有合
            from core.physics_engine import check_combination
            if check_combination(day_branch, year_branch):
                flux_events.append("Blade_Combined_Transformation")
        
        alpha = calculate_integrity_alpha(
            natal_chart=chart,
            day_master=day_master,
            day_branch=day_branch,
            flux_events=flux_events,
            luck_pillar=luck_pillar,
            year_pillar=year_pillar,
            energy_flux=energy_flux
        )
        
        # 检查成格/破格状态
        pattern_state = self._check_pattern_state_internal(
            pattern, chart, day_master, day_branch,
            luck_pillar, year_pillar, alpha
        )
        
        # 格局识别
        recognition_result = self.registry_loader.pattern_recognition(
            normalized_projection, pattern_id
        )
        
        return {
            'year': year,
            'year_pillar': year_pillar,
            'projection': normalized_projection,
            'raw_projection': projection,
            'alpha': alpha,
            'pattern_state': pattern_state,
            'recognition': recognition_result,
            'frequency_vector': frequency_vector
        }
    
    def simulate_trajectory(
        self,
        chart: List[str],
        day_master: str,
        pattern_id: str = 'A-03',
        start_year: int = 2024,
        duration: int = 12,
        luck_pillar: str = ""
    ) -> List[Dict[str, Any]]:
        """
        模拟命运轨迹
        
        Args:
            chart: 四柱八字
            day_master: 日主
            pattern_id: 格局ID（如果用户不是该格局，会使用Standard矩阵）
            start_year: 起始年份
            duration: 持续时间（年）
            luck_pillar: 大运干支（可选）
            
        Returns:
            时间序列数据列表
        """
        from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine
        
        engine = SyntheticBaziEngine()
        results = []
        
        # 流年干支映射（简化：使用60甲子循环）
        jia_zi = engine.JIA_ZI
        
        for i in range(duration):
            year = start_year + i
            # 计算流年干支（简化：基于年份计算）
            year_idx = (year - 1984) % 60  # 1984是甲子年
            year_pillar = jia_zi[year_idx] if 0 <= year_idx < 60 else jia_zi[0]
            
            # 计算该年的张量
            tensor_result = self.calculate_tensor_for_year(
                pattern_id=pattern_id,
                chart=chart,
                day_master=day_master,
                year=year,
                year_pillar=year_pillar,
                luck_pillar=luck_pillar
            )
            
            results.append(tensor_result)
        
        return results


def simulate_trajectory(
    chart: List[str],
    day_master: str,
    pattern_id: str = 'A-03',
    start_year: int = 2024,
    duration: int = 12,
    luck_pillar: str = ""
) -> List[Dict[str, Any]]:
    """
    便捷函数：模拟命运轨迹
    
    Args:
        chart: 四柱八字
        day_master: 日主
        pattern_id: 格局ID
        start_year: 起始年份
        duration: 持续时间（年）
        luck_pillar: 大运干支（可选）
        
    Returns:
        时间序列数据列表
    """
    simulator = FateSimulator()
    return simulator.simulate_trajectory(
        chart=chart,
        day_master=day_master,
        pattern_id=pattern_id,
        start_year=start_year,
        duration=duration,
        luck_pillar=luck_pillar
    )

