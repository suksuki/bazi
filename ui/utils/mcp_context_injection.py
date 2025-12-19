"""
MCP上下文注入工具 (MCP Context Injection Utilities)
====================================================

用于在量子验证页面中自动注入GEO、ERA、大运、流年等上下文信息。

作者: Antigravity Team
版本: V10.0
日期: 2025-01-17
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def inject_mcp_context(case_data: Dict[str, Any], selected_year: Optional[int] = None) -> Dict[str, Any]:
    """
    注入MCP上下文信息（GEO、ERA、大运、流年等）
    
    Args:
        case_data: 案例数据字典，应包含以下字段：
            - birth_date: 出生日期 (YYYY-MM-DD)
            - geo_city: 出生城市
            - geo_longitude: 经度
            - geo_latitude: 纬度
            - gender: 性别
            - timeline: 时间线（可选，用于获取大运）
        selected_year: 用户选择的年份（用于计算流年）
    
    Returns:
        包含MCP上下文的字典，添加了以下字段：
            - geo_city: 城市名称
            - geo_longitude: 经度
            - geo_latitude: 纬度
            - era_element: 元运元素 (Fire/Earth/Water)
            - era_period: 元运周期 (Period 8/9/1)
            - luck_pillar: 大运干支（如果有timeline，从timeline获取；否则计算）
            - year_pillar: 流年干支（如果提供了selected_year）
    """
    context = case_data.copy()
    
    # 1. GEO信息（直接从案例数据获取）
    geo_city = case_data.get('geo_city', 'Unknown')
    geo_longitude = case_data.get('geo_longitude', 0.0)
    geo_latitude = case_data.get('geo_latitude', 0.0)
    
    context['geo_city'] = geo_city
    context['geo_longitude'] = geo_longitude
    context['geo_latitude'] = geo_latitude
    
    logger.debug(f"📍 GEO上下文: {geo_city} ({geo_latitude}, {geo_longitude})")
    
    # 2. ERA信息（从birth_date计算元运）
    birth_date_str = case_data.get('birth_date')
    if birth_date_str:
        try:
            # 解析日期
            if isinstance(birth_date_str, str):
                birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
            else:
                birth_date = birth_date_str
            
            birth_year = birth_date.year
            
            # 元运计算规则
            if birth_year < 1984:
                era_period = "Period 8 (Earth)"
                era_element = "Earth"
            elif birth_year < 2024:
                era_period = "Period 9 (Fire)"
                era_element = "Fire"
            else:
                era_period = "Period 1 (Water)"
                era_element = "Water"
            
            context['era_period'] = era_period
            context['era_element'] = era_element
            
            logger.debug(f"⏳ ERA上下文: {era_period} ({era_element})")
            
        except Exception as e:
            logger.warning(f"⚠️ 无法计算ERA信息: {e}")
            context['era_period'] = "Period 9 (Fire)"
            context['era_element'] = "Fire"
    else:
        # 默认值
        context['era_period'] = "Period 9 (Fire)"
        context['era_element'] = "Fire"
    
    # 3. 大运信息（从timeline获取或计算）
    timeline = case_data.get('timeline', [])
    luck_pillar = None
    
    if timeline and len(timeline) > 0:
        # 从timeline的第一个事件获取大运
        first_event = timeline[0]
        luck_pillar = first_event.get('dayun')
        logger.debug(f"🔄 大运（从timeline）: {luck_pillar}")
    else:
        # 如果没有timeline，尝试根据birth_date和gender计算
        # 这里暂时返回None，由调用方处理
        logger.debug("⚠️ 未找到timeline，无法自动计算大运")
    
    context['luck_pillar'] = luck_pillar
    
    # 4. 流年信息（如果提供了selected_year）
    if selected_year is not None:
        year_pillar = calculate_year_pillar(selected_year)
        context['year_pillar'] = year_pillar
        context['selected_year'] = selected_year
        logger.debug(f"📅 流年上下文: {selected_year} -> {year_pillar}")
    
    return context


def calculate_year_pillar(year: int) -> str:
    """
    计算流年干支
    
    Args:
        year: 年份（如 2014）
    
    Returns:
        流年干支（如 "甲午"）
    """
    # 天干：甲=4, 乙=5, 丙=6, 丁=7, 戊=8, 己=9, 庚=0, 辛=1, 壬=2, 癸=3
    # 地支：子=4, 丑=5, 寅=6, 卯=7, 辰=8, 巳=9, 午=10, 未=11, 申=0, 酉=1, 戌=2, 亥=3
    
    gan_chars = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    zhi_chars = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    
    # 基准年：1924年是甲子年
    # 天干：甲=0, 乙=1, 丙=2, 丁=3, 戊=4, 己=5, 庚=6, 辛=7, 壬=8, 癸=9
    # 地支：子=0, 丑=1, 寅=2, 卯=3, 辰=4, 巳=5, 午=6, 未=7, 申=8, 酉=9, 戌=10, 亥=11
    
    base_year = 1924
    offset = year - base_year
    
    # 1924年是甲子（天干索引0，地支索引0）
    gan_idx = offset % 10
    zhi_idx = offset % 12
    
    return f"{gan_chars[gan_idx]}{zhi_chars[zhi_idx]}"


def calculate_luck_pillar_from_birth_date(birth_date: str, gender: str) -> Optional[str]:
    """
    根据出生日期和性别计算大运（简化版，实际应该使用BaziProfile）
    
    注意：这个方法只是占位符，实际应该使用BaziProfile或类似工具计算
    
    Args:
        birth_date: 出生日期 (YYYY-MM-DD)
        gender: 性别 ("男" 或 "女")
    
    Returns:
        大运干支，如果无法计算则返回None
    """
    # TODO: 实现完整的大运计算逻辑
    # 这需要：
    # 1. 解析出生日期
    # 2. 根据性别确定大运方向（男顺女逆或男逆女顺）
    # 3. 从月柱开始计算大运
    # 4. 根据当前年份确定当前大运
    
    logger.warning("⚠️ calculate_luck_pillar_from_birth_date 未完全实现，返回None")
    return None

