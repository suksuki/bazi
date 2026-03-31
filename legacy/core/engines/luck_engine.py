"""
core/engines/luck_engine.py
---------------------------
[V6.0 Sub-Engine] 动态运势引擎 (Luck Engine)
负责处理：大运计算、流年干支、运势周期判定
基于 V5.4 动态大运实现
"""
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class LuckEngine:
    """
    [V6.0 Sub-Engine] 动态运势引擎
    封装大运与流年的计算逻辑
    """
    
    # 天干
    STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    
    # 地支
    BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    # 基准年 (甲子年)
    BASE_YEAR = 1924

    def __init__(self):
        pass

    def get_year_ganzhi(self, year: int) -> str:
        """
        计算某年的干支
        :param year: 公历年份
        :return: 干支字符串 (e.g., '甲辰')
        """
        offset = year - self.BASE_YEAR
        stem = self.STEMS[offset % 10]
        branch = self.BRANCHES[offset % 12]
        return f"{stem}{branch}"

    def get_year_stem(self, year: int) -> str:
        """获取年干"""
        offset = year - self.BASE_YEAR
        return self.STEMS[offset % 10]

    def get_year_branch(self, year: int) -> str:
        """获取年支"""
        offset = year - self.BASE_YEAR
        return self.BRANCHES[offset % 12]

    def calculate_luck_start_age(self, birth_month: int, birth_day: int, 
                                  solar_term_day: int, gender: int, 
                                  year_stem: str) -> int:
        """
        计算起运年龄 (简化版)
        :param birth_month: 出生月
        :param birth_day: 出生日
        :param solar_term_day: 该月节气日 (简化为15)
        :param gender: 性别 (1=男, 0=女)
        :param year_stem: 年干
        :return: 起运年龄
        """
        # 判断阳年阴年
        yang_stems = {'甲', '丙', '戊', '庚', '壬'}
        is_yang_year = year_stem in yang_stems
        
        # 顺行/逆行
        # 男命阳年顺行，女命阳年逆行
        is_forward = (gender == 1 and is_yang_year) or (gender == 0 and not is_yang_year)
        
        # 简化计算：距离节气天数 / 3 = 起运年龄
        if is_forward:
            days_to_term = solar_term_day - birth_day
        else:
            days_to_term = birth_day
        
        start_age = max(1, abs(days_to_term) // 3)
        return start_age

    def get_luck_pillar_at_age(self, luck_cycles: List[Dict], age: int) -> Optional[str]:
        """
        根据年龄获取当前大运
        :param luck_cycles: 大运列表 (from BaziCalculator)
        :param age: 当前年龄
        :return: 大运干支 或 None
        """
        for cycle in luck_cycles:
            if cycle.get('start_age', 0) <= age <= cycle.get('end_age', 100):
                return cycle.get('gan_zhi')
        return None

    def get_luck_pillar_at_year(self, luck_cycles: List[Dict], year: int) -> Optional[str]:
        """
        根据年份获取当前大运
        :param luck_cycles: 大运列表
        :param year: 公历年份
        :return: 大运干支 或 None
        """
        for cycle in luck_cycles:
            if cycle.get('start_year', 0) <= year <= cycle.get('end_year', 9999):
                return cycle.get('gan_zhi')
        return None

    def is_handover_year(self, luck_cycles: List[Dict], year: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        检测是否为换运年
        :param luck_cycles: 大运列表
        :param year: 公历年份
        :return: (是否换运, 旧运, 新运)
        """
        current_luck = self.get_luck_pillar_at_year(luck_cycles, year)
        prev_luck = self.get_luck_pillar_at_year(luck_cycles, year - 1)
        
        if current_luck != prev_luck:
            return True, prev_luck, current_luck
        return False, None, None

    def generate_timeline(self, start_year: int, years: int = 12) -> List[Dict]:
        """
        生成流年时间线
        :param start_year: 起始年份
        :param years: 年数
        :return: 流年列表
        """
        timeline = []
        for i in range(years):
            y = start_year + i
            timeline.append({
                'year': y,
                'gan_zhi': self.get_year_ganzhi(y),
                'stem': self.get_year_stem(y),
                'branch': self.get_year_branch(y)
            })
        return timeline

    def get_luck_timeline(self, luck_cycles: List[Dict], start_year: int, 
                          years: int = 12, birth_year: int = None) -> List[Dict]:
        """
        生成包含大运信息的完整运势时间线
        :param luck_cycles: 大运列表 (from BaziProfile)
        :param start_year: 起始年份
        :param years: 年数
        :param birth_year: 出生年份 (用于计算年龄)
        :return: 带大运信息的流年列表
        """
        timeline = []
        for i in range(years):
            y = start_year + i
            
            # 获取当年大运
            current_luck = self.get_luck_pillar_at_year(luck_cycles, y)
            
            # 检测是否换运年
            is_handover, old_luck, new_luck = self.is_handover_year(luck_cycles, y)
            
            # 计算年龄 (如果提供了出生年份)
            age = (y - birth_year) if birth_year else None
            
            timeline.append({
                'year': y,
                'age': age,
                'year_pillar': self.get_year_ganzhi(y),
                'stem': self.get_year_stem(y),
                'branch': self.get_year_branch(y),
                'luck_pillar': current_luck,
                'is_handover': is_handover,
                'old_luck': old_luck,
                'new_luck': new_luck
            })
        return timeline

    def get_dynamic_luck_pillar(self, luck_cycles: List[Dict], year: int) -> Optional[str]:
        """
        获取指定年份的动态大运干支
        代理方法，用于 QuantumEngine 调用
        :param luck_cycles: 大运列表
        :param year: 目标年份
        :return: 大运干支 或 None
        """
        return self.get_luck_pillar_at_year(luck_cycles, year)
