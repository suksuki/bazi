from datetime import datetime
from lunar_python import Lunar, EightChar
from typing import Dict, Optional, List, Tuple, Any, Union

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
        # 使用 lunar_python 的 Solar 对象计算流年干支
        # 注意：为了准确性（立春界限），使用年中点（6月15日）计算
        try:
            from lunar_python import Solar
            solar = Solar.fromYmd(year, 6, 15)
            lunar = solar.getLunar()
            year_ganzhi = lunar.getYearInGanZhi()
            return str(year_ganzhi) if year_ganzhi else "未知"
        except Exception as e:
            # 如果计算失败，使用简化算法（基于1984年甲子年）
            # 1984年是甲子年，以此为基准推算
            offset = year - 1984
            gan_list = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
            zhi_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
            gan_idx = offset % 10
            zhi_idx = offset % 12
            return gan_list[gan_idx] + zhi_list[zhi_idx]

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

    @staticmethod
    def get_void_branches(pillar: str) -> List[str]:
        """
        [V6.1] Calculate Void Branches (空亡) for a given pillar.
        Logic: Find the 'Xun' (10-day cycle start) and the remaining 2 branches after 10 days.
        """
        if not pillar or len(pillar) < 2: return []
        
        gan_list = "甲乙丙丁戊己庚辛壬癸"
        zhi_list = "子丑寅卯辰巳午未申酉戌亥"
        
        try:
            g_idx = gan_list.index(pillar[0])
            z_idx = zhi_list.index(pillar[1])
            
            # The 'Xun' start is at z_idx - g_idx
            xun_start_idx = (z_idx - g_idx) % 12
            # The two void branches are the 11th and 12th in the 12-branch sequence starting from xun_start
            void1 = zhi_list[(xun_start_idx + 10) % 12]
            void2 = zhi_list[(xun_start_idx + 11) % 12]
            return [void1, void2]
        except:
            return []

    def get_chart_voids(self) -> List[str]:
        """Returns the void branches based on the Day Pillar."""
        day_p = self.chart.getDay()
        return self.get_void_branches(day_p)

    def get_luck_cycles(self) -> List[Dict]:
        """返回所有大运周期的列表"""
        yun = self.chart.getYun(self.gender)
        da_yun_arr = yun.getDaYun()
        cycles = []
        for i, dy in enumerate(da_yun_arr):
            gan_zhi = dy.getGanZhi()
            if not gan_zhi:
                continue
            cycles.append({
                "start_year": dy.getStartYear(),
                "end_year": dy.getEndYear(),
                "gan_zhi": gan_zhi
            })
        return cycles


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
        consider_lichun: bool = True,
        birth_date: Optional[datetime] = None
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
        self._provided_birth_date = birth_date
        
        # 使用 BaziReverseCalculator 反推出生日期
        self._reverse_calculator = None
        self._real_profile = self._create_real_profile()
    
    def _create_real_profile(self) -> Optional['BaziProfile']:
        """如果有提供出生日期，直接使用；否则从四柱反推"""
        try:
            
            # 如果提供了出生日期，直接返回 BaziProfile
            if self._provided_birth_date:
                return BaziProfile(self._provided_birth_date, self.gender)
            
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
                    # Phase 28: Modern Era Shift Logic (Jiazi Cycles)
                    # If birth year is too early (e.g. early 1900s), shift it forward by 60 years
                    # to make luck cycles start after 1950 (Master Jin's requirement)
                    while birth_date.year < 1940:
                        try:
                            birth_date = birth_date.replace(year=birth_date.year + 60)
                        except ValueError: # Leap year Feb 29 issue
                            birth_date = birth_date.replace(year=birth_date.year + 60, day=28)
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

    def get_luck_cycles(self) -> List[Dict]:
        """使用真正的 BaziProfile 获取大运周期列表"""
        if self._real_profile:
            return self._real_profile.get_luck_cycles()
        return []
