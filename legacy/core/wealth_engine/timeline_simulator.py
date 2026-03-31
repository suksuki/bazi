"""
V12.0 时间序列模拟器 (Timeline Simulator)

实现0-100岁完整时间序列模拟，生成完整人生财富曲线

性能优化：
- 预计算所有年份的大运和流年（避免重复计算）
- 使用缓存减少重复的引擎初始化
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from functools import lru_cache

from core.engine_graph import GraphNetworkEngine
from core.bazi_profile import VirtualBaziProfile
from .vectors import (
    calculate_flow_vector,
    calculate_capacity_vector,
    calculate_volatility_sigma
)

logger = logging.getLogger(__name__)


def calculate_wealth_potential(
    engine: GraphNetworkEngine,
    bazi: List[str],
    day_master: str,
    gender: str,
    year_pillar: str,
    luck_pillar: Optional[str] = None,
    strength_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    计算单年的财富势能 W(t) = F × C × (1 + σ)
    
    Args:
        engine: GraphNetworkEngine 实例（已初始化）
        bazi: 八字列表
        day_master: 日主天干
        gender: 性别
        year_pillar: 流年干支
        luck_pillar: 大运干支（可选）
        strength_type: 身强类型（如果已知，可传入以提高性能）
    
    Returns:
        dict: {
            'wealth_potential': float,  # W(t) = F × C × (1 + σ)
            'flow_vector': float,  # F
            'capacity_vector': float,  # C
            'volatility_sigma': float,  # σ
            'year_pillar': str,
            'luck_pillar': str
        }
    """
    try:
        # 确保引擎已初始化
        if not hasattr(engine, 'nodes') or not engine.nodes:
            engine.initialize_nodes(bazi, day_master, luck_pillar=luck_pillar, year_pillar=year_pillar)
            engine.build_adjacency_matrix()
            engine.propagate(max_iterations=10)
        
        # 如果未提供strength_type，计算它
        if strength_type is None:
            strength_result = engine.calculate_strength_score(day_master)
            strength_type = strength_result.get('strength_label', 'Balanced')
        
        # 计算三大向量
        F = calculate_flow_vector(engine, bazi, day_master, year_pillar, luck_pillar)
        C = calculate_capacity_vector(engine, bazi, day_master, strength_type, year_pillar, luck_pillar)
        sigma = calculate_volatility_sigma(engine, bazi, day_master, year_pillar, luck_pillar)
        
        # 计算财富势能：W = F × C × (1 + σ)
        wealth_potential = F * C * (1 + sigma) * 100  # 放大到0-200范围
        
        return {
            'wealth_potential': wealth_potential,
            'flow_vector': F,
            'capacity_vector': C,
            'volatility_sigma': sigma,
            'year_pillar': year_pillar,
            'luck_pillar': luck_pillar or '未知',
            'strength_type': strength_type
        }
        
    except Exception as e:
        logger.error(f"计算财富势能失败: {e}")
        return {
            'wealth_potential': 0.0,
            'flow_vector': 0.5,
            'capacity_vector': 0.5,
            'volatility_sigma': 0.0,
            'year_pillar': year_pillar,
            'luck_pillar': luck_pillar or '未知',
            'strength_type': strength_type or 'Unknown'
        }


def simulate_life_wealth(
    bazi: List[str],
    day_master: str,
    gender: str,
    birth_year: int,
    lifespan: int = 100,
    config: Optional[Dict] = None
) -> List[Dict[str, Any]]:
    """
    模拟0-100岁完整人生财富曲线
    
    步骤：
    1. 排盘：计算出命主 0-100 岁每一年对应的大运和流年干支
    2. 循环：对每一年调用向量计算 F, C, S
    3. 合成：wealth_score = (F * C * (1 + S)) * 100
    4. 平滑：对结果进行简单的滑动平均（Window=3），模拟运势的惯性
    5. 输出：返回包含 {age, year, score, events_desc} 的列表
    
    Args:
        bazi: 八字列表
        day_master: 日主天干
        gender: 性别
        birth_year: 出生年份
        lifespan: 寿命（默认100岁）
        config: 引擎配置（可选）
    
    Returns:
        List[Dict]: 每年财富数据列表
    """
    try:
        from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
        
        # 初始化引擎
        engine_config = config or DEFAULT_FULL_ALGO_PARAMS
        engine = GraphNetworkEngine(config=engine_config)
        
        # 创建VirtualBaziProfile用于排盘
        pillars = {
            'year': bazi[0] if len(bazi) > 0 else '',
            'month': bazi[1] if len(bazi) > 1 else '',
            'day': bazi[2] if len(bazi) > 2 else '',
            'hour': bazi[3] if len(bazi) > 3 else ''
        }
        
        gender_code = 1 if gender == '男' else 0
        profile = VirtualBaziProfile(
            pillars=pillars,
            static_luck=None,  # 动态计算
            day_master=day_master,
            gender=gender_code
        )
        
        # 计算基础身强类型（只需计算一次）
        engine.initialize_nodes(bazi, day_master)
        engine.build_adjacency_matrix()
        engine.propagate(max_iterations=10)
        strength_result = engine.calculate_strength_score(day_master)
        strength_type = strength_result.get('strength_label', 'Balanced')
        
        # [V12.0 性能优化] 预计算所有年份的大运和流年（避免重复计算）
        year_pillars = {}
        luck_pillars = {}
        
        for age in range(lifespan + 1):
            year = birth_year + age
            try:
                luck_pillar = profile.get_luck_pillar_at(year)
                year_pillar = profile.get_year_pillar(year)
                if year_pillar and year_pillar != "未知":
                    year_pillars[year] = year_pillar
                    luck_pillars[year] = luck_pillar if luck_pillar and luck_pillar != "未知大运" else None
            except:
                pass
        
        logger.info(f"预计算完成：{len(year_pillars)} 个有效年份")
        
        # 模拟每一年
        timeline = []
        raw_scores = []
        
        for age in range(lifespan + 1):
            year = birth_year + age
            
            # 从预计算结果获取
            year_pillar = year_pillars.get(year)
            luck_pillar = luck_pillars.get(year)
            
            if not year_pillar:
                # 如果无法计算流年，跳过
                continue
            
            # 重新初始化引擎（因为流年变化）
            engine.initialize_nodes(bazi, day_master, luck_pillar=luck_pillar, year_pillar=year_pillar)
            engine.build_adjacency_matrix()
            engine.propagate(max_iterations=10)
            
            # 计算财富势能
            wealth_data = calculate_wealth_potential(
                engine, bazi, day_master, gender, year_pillar, luck_pillar, strength_type
            )
            
            raw_scores.append(wealth_data['wealth_potential'])
            
            timeline.append({
                'age': age,
                'year': year,
                'score': wealth_data['wealth_potential'],
                'flow_vector': wealth_data['flow_vector'],
                'capacity_vector': wealth_data['capacity_vector'],
                'volatility_sigma': wealth_data['volatility_sigma'],
                'year_pillar': year_pillar,
                'luck_pillar': luck_pillar or '未知',
                'strength_type': strength_type,
                'events_desc': []  # 可以后续添加事件描述
            })
        
        # 滑动平均平滑（Window=3）
        if len(raw_scores) >= 3:
            smoothed_scores = []
            for i in range(len(raw_scores)):
                if i == 0:
                    smoothed = (raw_scores[0] + raw_scores[1]) / 2
                elif i == len(raw_scores) - 1:
                    smoothed = (raw_scores[-2] + raw_scores[-1]) / 2
                else:
                    smoothed = (raw_scores[i-1] + raw_scores[i] + raw_scores[i+1]) / 3
                smoothed_scores.append(smoothed)
            
            # 更新平滑后的分数
            for i, item in enumerate(timeline):
                item['score'] = smoothed_scores[i]
                item['score_raw'] = raw_scores[i]  # 保留原始分数
        
        logger.info(f"✅ 完成0-{lifespan}岁财富曲线模拟，共{len(timeline)}个数据点")
        
        return timeline
        
    except Exception as e:
        logger.error(f"模拟人生财富曲线失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

