from lunar_python import Lunar, EightChar
from typing import Dict, Optional, List, Tuple

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
        
        result = self._luck_timeline.get(year, "未知大运")
        
        # [V56.3 修复] 确保返回值是字符串格式
        if isinstance(result, str):
            return result
        elif isinstance(result, int):
            # 如果是整数，转换为字符串（可能是索引）
            return "未知大运"
        else:
            # 其他类型，转换为字符串
            return str(result) if result else "未知大运"

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
            
            # [V56.3 修复] 确保 ganzhi 是字符串格式
            if not isinstance(ganzhi, str):
                # 如果是整数或其他类型，转换为字符串
                ganzhi = str(ganzhi) if ganzhi else "未知大运"
            
            # 填充时间轴
            for y in range(start, end + 1):
                self._luck_timeline[y] = ganzhi


class VirtualBaziProfile:
    """
    [V6.0 Adapter] 虚拟八字档案 (The Mask)
    专门用于 QuantumLab 的旧测试用例 (Legacy Cases)。
    从四柱反推出生日期，然后委托给真正的 BaziProfile 计算大运。
    
    [V9.3 Optimization] 使用 BaziReverseCalculator 进行反推，支持自定义年份范围和精度
    """
    
    def __init__(
        self,
        pillars: Dict[str, str],
        static_luck: str = "未知",
        day_master: str = None,
        gender: int = 1,
        year_range: Tuple[int, int] = (1900, 2100),
        precision: str = "medium",
        consider_lichun: bool = True
    ):
        """
        初始化虚拟八字档案
        
        Args:
            pillars: 四柱字典
            static_luck: 静态大运（如果反推失败）
            day_master: 日主天干
            gender: 性别（1=男, 0=女）
            year_range: 年份搜索范围 (start_year, end_year)
            precision: 精度模式 ('high', 'medium', 'low')
            consider_lichun: 是否考虑立春边界
        """
        self._pillars = pillars
        self._static_luck = static_luck
        self._day_master = day_master
        self.gender = gender
        self.year_range = year_range
        self.precision = precision
        self.consider_lichun = consider_lichun
        
        # 使用 BaziReverseCalculator 反推出生日期
        self._reverse_calculator = None
        self._real_profile = self._create_real_profile()
    
    def _create_real_profile(self) -> Optional['BaziProfile']:
        """从四柱反推出生日期，创建真正的 BaziProfile"""
        try:
            from datetime import datetime
            
            # 使用 BaziReverseCalculator 进行反推
            if self._reverse_calculator is None:
                from core.bazi_reverse_calculator import BaziReverseCalculator
                self._reverse_calculator = BaziReverseCalculator(year_range=self.year_range)
            
            result = self._reverse_calculator.reverse_calculate(
                self._pillars,
                precision=self.precision,
                consider_lichun=self.consider_lichun
            )
            
            if result and result.get('birth_date'):
                birth_date = result['birth_date']
                if isinstance(birth_date, datetime):
                    return BaziProfile(birth_date, self.gender)
            
            # 如果反推失败，尝试旧方法（向后兼容）
            return self._create_real_profile_legacy()
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"反推出生日期失败: {e}")
            return None
    
    def _create_real_profile_legacy(self) -> Optional['BaziProfile']:
        """
        旧版反推方法（向后兼容）
        
        使用 BaziReverseCalculator 的低精度模式作为后备方案
        """
        try:
            from datetime import datetime
            
            # 使用 BaziReverseCalculator 的低精度模式
            if self._reverse_calculator is None:
                from core.bazi_reverse_calculator import BaziReverseCalculator
                self._reverse_calculator = BaziReverseCalculator(year_range=self.year_range)
            
            result = self._reverse_calculator.reverse_calculate(
                self._pillars,
                precision='low',
                consider_lichun=False
            )
            
            if result and result.get('birth_date'):
                birth_date = result['birth_date']
                if isinstance(birth_date, datetime):
                    return BaziProfile(birth_date, self.gender)
            
            return None
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"旧版反推方法失败: {e}")
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
