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
    它没有出生日期，只有硬编码的四柱文本。
    实现了 BaziProfile 的鸭子类型接口。
    """
    def __init__(self, pillars: Dict[str, str], static_luck: str = "未知", day_master: str = None, gender: int = 1):
        self._pillars = pillars
        self._static_luck = static_luck
        self._day_master = day_master
        self.gender = gender # 默认男，旧用例通常不敏感

    @property
    def pillars(self) -> Dict[str, str]:
        return self._pillars

    @property
    def day_master(self) -> str:
        # 如果初始化时未指定，尝试从 pillars['day'] 解析
        if self._day_master:
            return self._day_master
        if 'day' in self._pillars and len(self._pillars['day']) > 0:
            return self._pillars['day'][0]
        return "甲" # Fallback

    def get_luck_pillar_at(self, year: int) -> str:
        """
        虚拟大运计算 - 基于年份模拟大运变化
        每5年换一个大运（简化版，便于在12年视图中看到换运）
        """
        # 每5年换运（模拟），根据性别顺推或逆推
        base_year = 2024
        cycles = (year - base_year) // 5
        
        # 简化：使用天干地支推算
        gan_list = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        zhi_list = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        
        # 从月柱推算大运
        if 'month' in self._pillars and len(self._pillars['month']) >= 2:
            month_gan = self._pillars['month'][0]
            month_zhi = self._pillars['month'][1]
            
            try:
                gan_idx = gan_list.index(month_gan)
                zhi_idx = zhi_list.index(month_zhi)
                
                # 性别决定顺逆
                direction = 1 if self.gender == 1 else -1
                
                new_gan_idx = (gan_idx + cycles * direction) % 10
                new_zhi_idx = (zhi_idx + cycles * direction) % 12
                
                return gan_list[new_gan_idx] + zhi_list[new_zhi_idx]
            except:
                pass
        
        return self._static_luck if self._static_luck != "未知" else "未知大运"

    # 兼容性接口
    def get_year_pillar(self, year: int) -> str:
        # 如果 QuantumEngine 还需要调用 profile.get_year_pillar
        # 这里返回 Unknown 让 Engine 去处理（Engine 有自己的 get_year_pillar）
        return "Unknown"
