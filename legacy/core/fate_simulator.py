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
        [V1.5.2] 计算指定年份的5维张量 - 全面切换至 RegistryLoader 统一计算链
        """
        # 构建计算上下文
        context = {
            'annual_pillar': year_pillar,
            'luck_pillar': luck_pillar,
            'calculation_year': year
        }
        
        # 使用 RegistryLoader 进行高精度计算 (含路由、矩阵投影、格局识别)
        result = self.registry_loader.calculate_tensor_projection_from_registry(
            pattern_id=pattern_id,
            chart=chart,
            day_master=day_master,
            context=context
        )
        
        if 'error' in result:
            logger.error(f"⚠️ {year}年计算异常: {result['error']}")
            return {
                'year': year,
                'year_pillar': year_pillar,
                'projection': {'E': 0, 'O': 0, 'M': 0, 'S': 0, 'R': 0},
                'alpha': 0.0,
                'pattern_state': {'state': 'ERROR'},
                'error': result['error']
            }
            
        # 兼容性包装：返回 UI 渲染所需的数据结构
        return {
            'year': year,
            'year_pillar': year_pillar,
            'projection': result.get('projection', {}),
            'raw_projection': result.get('raw_projection', {}),
            'alpha': result.get('alpha', 0.5),
            'pattern_state': result.get('pattern_state', {}),
            'recognition': result.get('recognition', {}),
            'frequency_vector': result.get('frequency_vector', {}),
            'sub_id': result.get('sub_id')
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
        import time
        from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine
        
        start_time = time.time()
        engine = SyntheticBaziEngine()
        results = []
        
        # 流年干支映射（简化：使用60甲子循环）
        jia_zi = engine.JIA_ZI
        
        logger.info(f"🚀 开始模拟轨迹: pattern_id={pattern_id}, duration={duration}, start_year={start_year}")
        logger.info(f"   八字: {chart}, 日主: {day_master}")
        
        for i in range(duration):
            year = start_year + i
            # 计算流年干支（简化：基于年份计算）
            year_idx = (year - 1984) % 60  # 1984是甲子年
            year_pillar = jia_zi[year_idx] if 0 <= year_idx < 60 else jia_zi[0]
            
            # 强制输出进度日志（每3年一次，确保能看到）
            if i % 3 == 0 or i == 0:
                logger.info(f"📊 演算进度: {i+1}/{duration}年 (当前: {year}年 {year_pillar})")
            
            try:
                # 计算该年的张量
                year_start = time.time()
                logger.debug(f"  计算年份 {year} ({year_pillar})...")
                
                tensor_result = self.calculate_tensor_for_year(
                    pattern_id=pattern_id,
                    chart=chart,
                    day_master=day_master,
                    year=year,
                    year_pillar=year_pillar,
                    luck_pillar=luck_pillar
                )
                year_elapsed = time.time() - year_start
                
                if year_elapsed > 1.0:
                    logger.warning(f"⚠️ 年份 {year} 计算耗时较长: {year_elapsed:.2f}秒")
                elif i % 3 == 0:  # 每3年输出一次正常日志
                    logger.info(f"✅ 年份 {year} 计算完成: {year_elapsed:.3f}秒")
                
                results.append(tensor_result)
            except Exception as e:
                logger.error(f"计算年份 {year} 时出错: {e}", exc_info=True)
                # 添加一个错误标记的结果，避免中断整个流程
                results.append({
                    'year': year,
                    'year_pillar': year_pillar,
                    'error': str(e),
                    'projection': {'E': 0, 'O': 0, 'M': 0, 'S': 0, 'R': 0},
                    'alpha': 0.0,
                    'pattern_state': {'state': 'ERROR'}
                })
        
        total_elapsed = time.time() - start_time
        logger.info(f"轨迹模拟完成: 共{duration}年，耗时{total_elapsed:.2f}秒，平均{total_elapsed/duration:.3f}秒/年")
        
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

