"""
八字反推计算器 (Bazi Reverse Calculator)
V9.3 Optimization: 统一反推接口，支持高精度和性能优化
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from lunar_python import Solar
import logging

logger = logging.getLogger(__name__)


class BaziReverseCalculator:
    """
    统一的八字反推计算器
    
    功能:
    1. 从四柱反推出生日期（支持立春边界）
    2. 支持自定义年份范围
    3. 性能优化（索引和缓存）
    4. 多种精度模式
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
    
    def __init__(self, year_range: Tuple[int, int] = (1900, 2100)):
        """
        初始化反推计算器
        
        Args:
            year_range: 年份搜索范围 (start_year, end_year)
        """
        self.year_range = year_range
        self._cache = {}  # 缓存查询结果
        self._year_index = {}  # 年份索引（年柱 -> 年份列表）
        self._build_year_index()
    
    def _build_year_index(self):
        """构建年份索引，加速年柱匹配"""
        start_year, end_year = self.year_range
        self._year_index = {}
        
        for year in range(start_year, end_year + 1):
            # 使用年中点（6月15日）计算年柱（近似值）
            try:
                solar = Solar.fromYmd(year, 6, 15)
                lunar = solar.getLunar()
                year_ganzhi = lunar.getYearInGanZhi()
                
                if year_ganzhi not in self._year_index:
                    self._year_index[year_ganzhi] = []
                self._year_index[year_ganzhi].append(year)
            except Exception as e:
                logger.debug(f"构建年份索引失败 {year}: {e}")
    
    def reverse_calculate(
        self,
        pillars: Dict[str, str],
        precision: str = "high",
        consider_lichun: bool = True
    ) -> Optional[Dict]:
        """
        从四柱反推出生日期
        
        Args:
            pillars: 四柱字典 {'year': '甲子', 'month': '丙寅', 'day': '庚辰', 'hour': '戊午'}
            precision: 精度模式
                - 'high': 高精度，考虑立春边界，精确匹配
                - 'medium': 中等精度，考虑立春边界，近似匹配
                - 'low': 低精度，快速近似
            consider_lichun: 是否考虑立春边界
        
        Returns:
            Dict 包含:
                - 'birth_date': datetime 对象
                - 'confidence': 置信度 (0-1)
                - 'matches': 匹配的日期列表（高精度模式可能有多个）
        """
        cache_key = f"{pillars}_{precision}_{consider_lichun}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        year_pillar = pillars.get('year', '')
        month_pillar = pillars.get('month', '')
        day_pillar = pillars.get('day', '')
        hour_pillar = pillars.get('hour', '')
        
        if len(year_pillar) < 2 or len(month_pillar) < 2:
            return None
        
        if precision == 'high':
            result = self._reverse_high_precision(year_pillar, month_pillar, day_pillar, hour_pillar, consider_lichun)
        elif precision == 'medium':
            result = self._reverse_medium_precision(year_pillar, month_pillar, day_pillar, hour_pillar, consider_lichun)
        else:
            result = self._reverse_low_precision(year_pillar, month_pillar, day_pillar, hour_pillar)
        
        if result:
            self._cache[cache_key] = result
        
        return result
    
    def _reverse_high_precision(
        self,
        year_pillar: str,
        month_pillar: str,
        day_pillar: str,
        hour_pillar: str,
        consider_lichun: bool
    ) -> Optional[Dict]:
        """
        高精度反推：精确匹配，考虑立春边界
        """
        matches = []
        start_year, end_year = self.year_range
        
        # 使用索引快速找到可能的年份
        candidate_years = self._year_index.get(year_pillar, [])
        
        # 如果没有索引，回退到全范围搜索
        if not candidate_years:
            candidate_years = list(range(start_year, end_year + 1))
        
        for year in candidate_years:
            # 搜索该年及前后一年（考虑立春边界）
            search_years = [year - 1, year, year + 1] if consider_lichun else [year]
            
            for search_year in search_years:
                if search_year < start_year or search_year > end_year:
                    continue
                
                # 搜索该年的日期范围（考虑立春边界）
                start_date = datetime(search_year, 1, 15) if not consider_lichun else datetime(search_year, 1, 1)
                end_date = datetime(search_year + 1, 2, 15) if consider_lichun else datetime(search_year, 12, 31)
                
                current = start_date
                while current <= end_date:
                    try:
                        solar = Solar.fromYmd(current.year, current.month, current.day)
                        lunar = solar.getLunar()
                        
                        # 精确匹配年柱（考虑立春）
                        if consider_lichun:
                            year_gz = lunar.getYearInGanZhiExact()
                        else:
                            year_gz = lunar.getYearInGanZhi()
                        
                        if year_gz != year_pillar:
                            current += timedelta(days=1)
                            continue
                        
                        # 精确匹配月柱（考虑立春）
                        if consider_lichun:
                            month_gz = lunar.getMonthInGanZhiExact()
                        else:
                            month_gz = lunar.getMonthInGanZhi()
                        
                        if month_gz != month_pillar:
                            current += timedelta(days=1)
                            continue
                        
                        # 精确匹配日柱
                        day_gz = lunar.getDayInGanZhiExact()
                        if day_gz != day_pillar:
                            current += timedelta(days=1)
                            continue
                        
                        # 精确匹配时柱
                        for hour in range(0, 24, 2):
                            try:
                                hour_solar = Solar.fromYmdHms(current.year, current.month, current.day, hour, 0, 0)
                                hour_lunar = hour_solar.getLunar()
                                hour_gz = hour_lunar.getTimeInGanZhi()
                                
                                if hour_gz == hour_pillar:
                                    match_date = datetime(current.year, current.month, current.day, hour, 0, 0)
                                    matches.append(match_date)
                                    break
                            except Exception:
                                continue
                        
                        current += timedelta(days=1)
                    except Exception as e:
                        logger.debug(f"高精度反推错误 {current}: {e}")
                        current += timedelta(days=1)
        
        if matches:
            # 返回第一个匹配结果，但包含所有匹配
            return {
                'birth_date': matches[0],
                'confidence': 1.0 if len(matches) == 1 else 0.8,
                'matches': matches,
                'match_count': len(matches)
            }
        
        return None
    
    def _reverse_medium_precision(
        self,
        year_pillar: str,
        month_pillar: str,
        day_pillar: str,
        hour_pillar: str,
        consider_lichun: bool
    ) -> Optional[Dict]:
        """
        中等精度反推：考虑立春边界，但使用近似日期
        """
        # 年柱反推年份
        year_gan = year_pillar[0]
        year_zhi = year_pillar[1]
        
        if year_gan not in self.GAN or year_zhi not in self.ZHI:
            return None
        
        gan_idx = self.GAN.index(year_gan)
        zhi_idx = self.ZHI.index(year_zhi)
        
        # 使用索引快速查找
        candidate_years = self._year_index.get(year_pillar, [])
        
        if not candidate_years:
            # 回退到循环查找
            start_year, end_year = self.year_range
            for year in range(start_year, end_year + 1):
                if (year - 4) % 10 == gan_idx and (year - 4) % 12 == zhi_idx:
                    candidate_years.append(year)
        
        if not candidate_years:
            return None
        
        # 使用第一个候选年份
        birth_year = candidate_years[0]
        
        # 月柱反推月份
        month_zhi = month_pillar[1]
        birth_month = self.ZHI_TO_MONTH.get(month_zhi, 6)
        # 调整为公历月份（农历寅月约公历2-3月）
        birth_month_solar = birth_month + 1 if birth_month <= 10 else birth_month - 10
        
        # 使用月中（15日）作为近似日期
        birth_day = 15
        
        # 时柱反推时辰
        hour_zhi = hour_pillar[1] if len(hour_pillar) > 1 else '午'
        birth_hour = self.ZHI_TO_HOUR.get(hour_zhi, 12)
        
        birth_date = datetime(birth_year, birth_month_solar, birth_day, birth_hour, 0)
        
        # 验证匹配度
        try:
            solar = Solar.fromYmd(birth_year, birth_month_solar, birth_day)
            lunar = solar.getLunar()
            
            if consider_lichun:
                year_match = lunar.getYearInGanZhiExact() == year_pillar
                month_match = lunar.getMonthInGanZhiExact() == month_pillar
            else:
                year_match = lunar.getYearInGanZhi() == year_pillar
                month_match = lunar.getMonthInGanZhi() == month_pillar
            
            confidence = 0.7 if (year_match and month_match) else 0.5
        except Exception:
            confidence = 0.5
        
        return {
            'birth_date': birth_date,
            'confidence': confidence,
            'matches': [birth_date],
            'match_count': 1
        }
    
    def _reverse_low_precision(
        self,
        year_pillar: str,
        month_pillar: str,
        day_pillar: str,
        hour_pillar: str
    ) -> Optional[Dict]:
        """
        低精度反推：快速近似，不考虑立春边界
        """
        # 年柱反推年份
        year_gan = year_pillar[0]
        year_zhi = year_pillar[1]
        
        if year_gan not in self.GAN or year_zhi not in self.ZHI:
            return None
        
        gan_idx = self.GAN.index(year_gan)
        zhi_idx = self.ZHI.index(year_zhi)
        
        # 使用索引快速查找
        candidate_years = self._year_index.get(year_pillar, [])
        
        if not candidate_years:
            # 回退到循环查找
            start_year, end_year = self.year_range
            for year in range(start_year, end_year + 1):
                if (year - 4) % 10 == gan_idx and (year - 4) % 12 == zhi_idx:
                    candidate_years.append(year)
                    break
        
        if not candidate_years:
            return None
        
        birth_year = candidate_years[0]
        
        # 月柱反推月份
        month_zhi = month_pillar[1]
        birth_month = self.ZHI_TO_MONTH.get(month_zhi, 6)
        birth_month_solar = birth_month + 1 if birth_month <= 10 else birth_month - 10
        
        birth_day = 15
        hour_zhi = hour_pillar[1] if len(hour_pillar) > 1 else '午'
        birth_hour = self.ZHI_TO_HOUR.get(hour_zhi, 12)
        
        birth_date = datetime(birth_year, birth_month_solar, birth_day, birth_hour, 0)
        
        return {
            'birth_date': birth_date,
            'confidence': 0.5,
            'matches': [birth_date],
            'match_count': 1
        }
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        return {
            'cache_size': len(self._cache),
            'index_size': sum(len(years) for years in self._year_index.values()),
            'year_range': self.year_range
        }

