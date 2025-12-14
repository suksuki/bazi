from lunar_python import Lunar, EightChar
from typing import Dict, Optional, List

class BaziProfile:
    """
    [V6.0 Core] 八字档案对象 (The Oracle)
    封装所有基于出生信息的计算逻辑（排盘、大运、流年映射）。
    作为 Single Source of Truth，替代散乱的字典传递。
    """
    
    def __init__(self, birth_date, gender: int):
        """
        :param birth_date: datetime 对象
        :param gender: 1男 0女
        """
        self.birth_date = birth_date
        self.gender = gender
        
        # 1. 初始化 Lunar 对象 (最重的计算)
        self.lunar = Lunar.fromDate(birth_date)
        self.chart = self.lunar.getEightChar()
        
        # 2. 缓存字段 (Lazy Loading)
        self._luck_timeline: Optional[Dict[int, str]] = None 
        self._day_master: Optional[str] = None

    # --- 基础属性访问 ---
    
    @property
    def pillars(self) -> Dict[str, str]:
        """返回四柱干支"""
        return {
            'year': self.chart.getYear(),
            'month': self.chart.getMonth(),
            'day': self.chart.getDay(),
            'hour': self.chart.getTime()
        }

    @property
    def day_master(self) -> str:
        """获取日主 (Day Master)"""
        if not self._day_master:
            self._day_master = self.chart.getDayGan()
        return self._day_master

    # --- 核心逻辑：时间线查询 ---

    def get_luck_pillar_at(self, year: int) -> str:
        """
        [V6.0 新特性] O(1) 复杂度查询指定年份的大运
        """
        if self._luck_timeline is None:
            self._build_luck_timeline()
        
        return self._luck_timeline.get(year, "未知大运")

    def get_year_pillar(self, year: int) -> str:
        """
        获取指定流年的干支 (无需 engine 再去算)
        """
        # 简单推算：这里可以使用 lunar_python 的流年对象，
        # 或者为了性能，直接用干支算法。这里演示用 Lunar 准确获取。
        # 注意：为了性能，实际工程中通常用数学公式推算流年干支，
        # 但这里为了准确性（立春界限），我们构建临时的 Lunar 对象。
        # *优化*: 仅计算该年的立春后干支
        
        # 简易版 (仅用于 Demo，后续可优化为查表法)
        from lunar_python import GanZhi
        # 这里的计算略复杂，暂时返回占位，稍后我们在 Engine 里迁移逻辑
        # 或者简单地：
        offset = year - 1984
        return GanZhi.getGanZhi(offset) # 这是一个近似值，V6.1再精细化

    # --- 内部逻辑 ---

    def _build_luck_timeline(self):
        """
        构建未来 100 年的大运查找表 (Timeline)
        解决 V5.4 中的动态计算开销问题
        """
        self._luck_timeline = {}
        yun = self.chart.getYun(self.gender)
        dayun_list = yun.getDaYun()
        
        # 预计算缓存
        for dy in dayun_list:
            start = dy.getStartYear()
            end = dy.getEndYear()
            ganzhi = dy.getGanZhi()
            
            # 填充时间轴
            for y in range(start, end + 1):
                self._luck_timeline[y] = ganzhi


class VirtualBaziProfile:
    """
    [V6.0 Adapter] 虚拟八字档案 (The Mask)
    专门用于 QuantumLab 的旧测试用例 (Legacy Cases)。
    从四柱反推出生日期，然后委托给真正的 BaziProfile 计算大运。
    """
    
    # 天干地支表
    GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    
    # 地支对应的月份 (寅月=1月立春后)
    ZHI_TO_MONTH = {"寅": 1, "卯": 2, "辰": 3, "巳": 4, "午": 5, "未": 6,
                    "申": 7, "酉": 8, "戌": 9, "亥": 10, "子": 11, "丑": 12}
    
    # 地支对应的时辰 (子时=23-1点)
    ZHI_TO_HOUR = {"子": 0, "丑": 2, "寅": 4, "卯": 6, "辰": 8, "巳": 10,
                   "午": 12, "未": 14, "申": 16, "酉": 18, "戌": 20, "亥": 22}
    
    def __init__(self, pillars: Dict[str, str], static_luck: str = "未知", day_master: str = None, gender: int = 1):
        self._pillars = pillars
        self._static_luck = static_luck
        self._day_master = day_master
        self.gender = gender
        
        # 反推出生日期并创建真正的 BaziProfile
        self._real_profile = self._create_real_profile()
    
    def _create_real_profile(self) -> Optional['BaziProfile']:
        """从四柱反推出生日期，创建真正的 BaziProfile"""
        try:
            from datetime import datetime
            from lunar_python import Lunar, Solar
            
            year_pillar = self._pillars.get('year', '')
            month_pillar = self._pillars.get('month', '')
            day_pillar = self._pillars.get('day', '')
            hour_pillar = self._pillars.get('hour', '')
            
            if len(year_pillar) < 2 or len(month_pillar) < 2:
                return None
            
            # 年柱反推年份 (假设是1920-2020之间)
            year_gan = year_pillar[0]
            year_zhi = year_pillar[1]
            gan_idx = self.GAN.index(year_gan)
            zhi_idx = self.ZHI.index(year_zhi)
            
            # 60 甲子循环
            for base_year in range(1920, 2020):
                if (base_year - 4) % 10 == gan_idx and (base_year - 4) % 12 == zhi_idx:
                    birth_year = base_year
                    break
            else:
                return None
            
            # 月柱反推月份
            month_zhi = month_pillar[1]
            birth_month = self.ZHI_TO_MONTH.get(month_zhi, 6)
            # 调整为公历月份 (农历寅月约公历2-3月)
            birth_month_solar = birth_month + 1 if birth_month <= 10 else birth_month - 10
            
            # 假设日期为15日 (月中)
            birth_day = 15
            
            # 时柱反推时辰
            hour_zhi = hour_pillar[1] if len(hour_pillar) > 1 else '午'
            birth_hour = self.ZHI_TO_HOUR.get(hour_zhi, 12)
            
            # 创建真正的 BaziProfile
            birth_date = datetime(birth_year, birth_month_solar, birth_day, birth_hour, 0)
            return BaziProfile(birth_date, self.gender)
            
        except Exception as e:
            return None

    @property
    def pillars(self) -> Dict[str, str]:
        return self._pillars

    @property
    def day_master(self) -> str:
        if self._day_master:
            return self._day_master
        if 'day' in self._pillars and len(self._pillars['day']) > 0:
            return self._pillars['day'][0]
        return "甲"
    
    @property
    def birth_date(self):
        """返回反推的出生日期"""
        return self._real_profile.birth_date if self._real_profile else None

    def get_luck_pillar_at(self, year: int) -> str:
        """使用真正的 BaziProfile 计算大运"""
        if self._real_profile:
            return self._real_profile.get_luck_pillar_at(year)
        return self._static_luck

    def get_year_pillar(self, year: int) -> str:
        if self._real_profile:
            return self._real_profile.get_year_pillar(year)
        return "Unknown"
