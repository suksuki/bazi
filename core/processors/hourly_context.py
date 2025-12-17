"""
流时修正处理器 (Hourly Context Processor)
V9.3 MCP: 动态实时上下文 - 计算当前小时的干支（流时）与日主之间的作用力
"""

from datetime import datetime
from typing import Dict, Any, Optional
from core.processors.base import BaseProcessor

# 时干计算表（根据日干和时支计算时干）
HOUR_STEM_TABLE = {
    '甲': {'子': '甲', '丑': '乙', '寅': '丙', '卯': '丁', '辰': '戊', '巳': '己',
           '午': '庚', '未': '辛', '申': '壬', '酉': '癸', '戌': '甲', '亥': '乙'},
    '乙': {'子': '丙', '丑': '丁', '寅': '戊', '卯': '己', '辰': '庚', '巳': '辛',
           '午': '壬', '未': '癸', '申': '甲', '酉': '乙', '戌': '丙', '亥': '丁'},
    '丙': {'子': '戊', '丑': '己', '寅': '庚', '卯': '辛', '辰': '壬', '巳': '癸',
           '午': '甲', '未': '乙', '申': '丙', '酉': '丁', '戌': '戊', '亥': '己'},
    '丁': {'子': '庚', '丑': '辛', '寅': '壬', '卯': '癸', '辰': '甲', '巳': '乙',
           '午': '丙', '未': '丁', '申': '戊', '酉': '己', '戌': '庚', '亥': '辛'},
    '戊': {'子': '壬', '丑': '癸', '寅': '甲', '卯': '乙', '辰': '丙', '巳': '丁',
           '午': '戊', '未': '己', '申': '庚', '酉': '辛', '戌': '壬', '亥': '癸'},
    '己': {'子': '甲', '丑': '乙', '寅': '丙', '卯': '丁', '辰': '戊', '巳': '己',
           '午': '庚', '未': '辛', '申': '壬', '酉': '癸', '戌': '甲', '亥': '乙'},
    '庚': {'子': '丙', '丑': '丁', '寅': '戊', '卯': '己', '辰': '庚', '巳': '辛',
           '午': '壬', '未': '癸', '申': '甲', '酉': '乙', '戌': '丙', '亥': '丁'},
    '辛': {'子': '戊', '丑': '己', '寅': '庚', '卯': '辛', '辰': '壬', '巳': '癸',
           '午': '甲', '未': '乙', '申': '丙', '酉': '丁', '戌': '戊', '亥': '己'},
    '壬': {'子': '庚', '丑': '辛', '寅': '壬', '卯': '癸', '辰': '甲', '巳': '乙',
           '午': '丙', '未': '丁', '申': '戊', '酉': '己', '戌': '庚', '亥': '辛'},
    '癸': {'子': '壬', '丑': '癸', '寅': '甲', '卯': '乙', '辰': '丙', '巳': '丁',
           '午': '戊', '未': '己', '申': '庚', '酉': '辛', '戌': '壬', '亥': '癸'},
}

# 时支对应表（根据小时计算时支）
HOUR_BRANCH_TABLE = [
    ('子', 23, 1),   # 23:00-01:00
    ('丑', 1, 3),    # 01:00-03:00
    ('寅', 3, 5),    # 03:00-05:00
    ('卯', 5, 7),    # 05:00-07:00
    ('辰', 7, 9),    # 07:00-09:00
    ('巳', 9, 11),   # 09:00-11:00
    ('午', 11, 13),  # 11:00-13:00
    ('未', 13, 15),  # 13:00-15:00
    ('申', 15, 17),  # 15:00-17:00
    ('酉', 17, 19),  # 17:00-19:00
    ('戌', 19, 21),  # 19:00-21:00
    ('亥', 21, 23),  # 21:00-23:00
]


class HourlyContextProcessor(BaseProcessor):
    """
    流时修正处理器
    计算当前小时的干支（流时）与日主之间的作用力
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Hourly Context Processor"
    
    @property
    def processor_name(self) -> str:
        return "Hourly Context"
    
    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理流时上下文
        
        Args:
            context: 包含以下字段：
                - day_master: 日主天干（如 '甲'）
                - current_time: 当前时间（datetime 对象，可选）
                - bazi: 八字列表（可选，用于计算日干）
        
        Returns:
            Dict 包含：
                - hourly_pillar: 流时干支（如 '甲子'）
                - hourly_stem: 时干
                - hourly_branch: 时支
                - interaction: 流时与日主的相互作用
                - recommendation: 短期决策建议
                - energy_boost: 能量加成（-1.0 到 1.0）
        """
        day_master = context.get('day_master')
        current_time = context.get('current_time', datetime.now())
        bazi = context.get('bazi', [])
        
        # 如果没有提供日主，尝试从八字中获取
        if not day_master and bazi and len(bazi) >= 2:
            # 日柱是第三柱（索引2）
            day_pillar = bazi[2] if len(bazi) > 2 else None
            if day_pillar and len(day_pillar) >= 1:
                day_master = day_pillar[0]
        
        if not day_master:
            return {
                'hourly_pillar': None,
                'error': '日主信息缺失'
            }
        
        # 计算当前小时的时支
        hour = current_time.hour
        hourly_branch = self._get_hour_branch(hour)
        
        # 根据日干和时支计算时干
        hourly_stem = HOUR_STEM_TABLE.get(day_master, {}).get(hourly_branch, '')
        
        if not hourly_stem:
            return {
                'hourly_pillar': None,
                'error': '无法计算时干'
            }
        
        hourly_pillar = hourly_stem + hourly_branch
        
        # 分析流时与日主的相互作用
        interaction = self._analyze_interaction(day_master, hourly_stem, hourly_branch)
        
        # 计算能量加成
        energy_boost = self._calculate_energy_boost(interaction)
        
        # 生成短期决策建议
        recommendation = self._generate_recommendation(interaction, energy_boost)
        
        return {
            'hourly_pillar': hourly_pillar,
            'hourly_stem': hourly_stem,
            'hourly_branch': hourly_branch,
            'interaction': interaction,
            'energy_boost': energy_boost,
            'recommendation': recommendation,
            'current_hour': hour
        }
    
    def _get_hour_branch(self, hour: int) -> str:
        """根据小时计算时支"""
        for branch, start, end in HOUR_BRANCH_TABLE:
            if start <= end:
                if start <= hour < end or (start == 23 and hour >= 23):
                    return branch
            else:  # 跨日情况（23:00-01:00）
                if hour >= start or hour < end:
                    return branch
        return '子'  # 默认
    
    def _analyze_interaction(self, day_master: str, hourly_stem: str, hourly_branch: str) -> Dict[str, Any]:
        """
        分析流时与日主的相互作用
        
        返回:
            - type: 作用类型（生、克、比、泄、耗）
            - strength: 作用强度（0-1）
            - description: 描述
        """
        from core.processors.physics import GENERATION, CONTROL
        
        # 获取日主元素
        day_element = self._get_element(day_master)
        hourly_stem_element = self._get_element(hourly_stem)
        hourly_branch_element = self._get_element(hourly_branch)
        
        # 分析天干作用
        stem_interaction = self._get_interaction_type(day_element, hourly_stem_element, GENERATION, CONTROL)
        
        # 分析地支作用
        branch_interaction = self._get_interaction_type(day_element, hourly_branch_element, GENERATION, CONTROL)
        
        # 构建流时干支用于描述
        hourly_pillar = hourly_stem + hourly_branch
        
        # 综合判断
        if stem_interaction['type'] == '生' or branch_interaction['type'] == '生':
            return {
                'type': '生',
                'strength': max(stem_interaction['strength'], branch_interaction['strength']),
                'description': f'流时{hourly_pillar}生助日主{day_master}，能量增强',
                'favorable': True
            }
        elif stem_interaction['type'] == '克' or branch_interaction['type'] == '克':
            return {
                'type': '克',
                'strength': max(stem_interaction['strength'], branch_interaction['strength']),
                'description': f'流时{hourly_pillar}克制日主{day_master}，能量减弱',
                'favorable': False
            }
        elif hourly_stem == day_master or hourly_branch in self._get_same_element_branches(day_master):
            return {
                'type': '比',
                'strength': 0.7,
                'description': f'流时{hourly_pillar}与日主{day_master}同类，能量稳定',
                'favorable': True
            }
        else:
            return {
                'type': '中性',
                'strength': 0.5,
                'description': f'流时{hourly_pillar}与日主{day_master}作用中性',
                'favorable': None
            }
    
    def _get_element(self, gan_or_zhi: str) -> str:
        """获取天干或地支的五行元素"""
        STEM_ELEMENTS = {
            '甲': 'wood', '乙': 'wood',
            '丙': 'fire', '丁': 'fire',
            '戊': 'earth', '己': 'earth',
            '庚': 'metal', '辛': 'metal',
            '壬': 'water', '癸': 'water',
        }
        BRANCH_ELEMENTS = {
            '子': 'water', '亥': 'water',
            '寅': 'wood', '卯': 'wood',
            '午': 'fire', '巳': 'fire',
            '申': 'metal', '酉': 'metal',
            '辰': 'earth', '戌': 'earth', '丑': 'earth', '未': 'earth',
        }
        
        if gan_or_zhi in STEM_ELEMENTS:
            return STEM_ELEMENTS[gan_or_zhi]
        elif gan_or_zhi in BRANCH_ELEMENTS:
            return BRANCH_ELEMENTS[gan_or_zhi]
        return 'earth'  # 默认
    
    def _get_interaction_type(self, day_element: str, hourly_element: str, 
                             GENERATION: Dict, CONTROL: Dict) -> Dict[str, Any]:
        """获取相互作用类型"""
        # 生：hourly 生 day
        if GENERATION.get(hourly_element) == day_element:
            return {'type': '生', 'strength': 0.8}
        # 克：hourly 克 day
        elif CONTROL.get(hourly_element) == day_element:
            return {'type': '克', 'strength': 0.8}
        # 泄：day 生 hourly
        elif GENERATION.get(day_element) == hourly_element:
            return {'type': '泄', 'strength': 0.6}
        # 耗：day 克 hourly
        elif CONTROL.get(day_element) == hourly_element:
            return {'type': '耗', 'strength': 0.6}
        else:
            return {'type': '中性', 'strength': 0.5}
    
    def _get_same_element_branches(self, day_master: str) -> list:
        """获取与日主同五行的地支"""
        element = self._get_element(day_master)
        BRANCH_ELEMENTS = {
            '子': 'water', '亥': 'water',
            '寅': 'wood', '卯': 'wood',
            '午': 'fire', '巳': 'fire',
            '申': 'metal', '酉': 'metal',
            '辰': 'earth', '戌': 'earth', '丑': 'earth', '未': 'earth',
        }
        return [branch for branch, elem in BRANCH_ELEMENTS.items() if elem == element]
    
    def _calculate_energy_boost(self, interaction: Dict[str, Any]) -> float:
        """计算能量加成"""
        if interaction.get('favorable') is True:
            return interaction.get('strength', 0.5) * 0.2  # 最大 +20%
        elif interaction.get('favorable') is False:
            return -interaction.get('strength', 0.5) * 0.2  # 最大 -20%
        else:
            return 0.0
    
    def _generate_recommendation(self, interaction: Dict[str, Any], energy_boost: float) -> str:
        """生成短期决策建议"""
        if energy_boost > 0.1:
            return f"✅ **最佳时机**: 当前流时能量增强 {energy_boost*100:.1f}%，适合重要决策、谈判、投资等。"
        elif energy_boost < -0.1:
            return f"⚠️ **谨慎时机**: 当前流时能量减弱 {abs(energy_boost)*100:.1f}%，建议推迟重要决策。"
        else:
            return "ℹ️ **中性时机**: 当前流时能量稳定，可正常进行日常活动。"

