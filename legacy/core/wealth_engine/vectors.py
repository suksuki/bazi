"""
V12.0 财富向量计算引擎 (Wealth Vectors Engine)

实现 F, C, σ 三维向量计算：
- F (Flow Vector): 通关流量 - 能量流向财星的顺畅度
- C (Capacity Vector): 掌控系数 - 日主获取并留存能量的能力
- σ (Volatility Sigma): 波动/爆发系数 - 系统的震荡幅度
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
import numpy as np

from core.engine_graph import GraphNetworkEngine
from core.processors.physics import GENERATION, CONTROL

logger = logging.getLogger(__name__)


def calculate_flow_vector(
    engine: GraphNetworkEngine,
    bazi: List[str],
    day_master: str,
    year_pillar: str,
    luck_pillar: Optional[str] = None
) -> float:
    """
    计算通关流量向量 F(t)
    
    物理定义：能量流向财星的顺畅度
    古诀映射：食伤生财、官印相生（对于护财）
    
    计算逻辑：
    1. 检测能量瓶颈：如果原局有财无食伤（堵塞），流年补了食伤 -> F 飙升
    2. 检测喜用神到位：流年五行是否为系统急需的五行？
    
    Args:
        engine: GraphNetworkEngine 实例（已初始化）
        bazi: 八字列表
        day_master: 日主天干
        year_pillar: 流年干支
        luck_pillar: 大运干支（可选）
    
    Returns:
        float: 流量系数 0.0-1.0
    """
    try:
        # 获取日主元素
        dm_element = engine.STEM_ELEMENTS.get(day_master, 'earth')
        
        # 确定财星元素
        wealth_element = CONTROL.get(dm_element)  # 我克的
        output_element = GENERATION.get(dm_element)  # 我生的（食伤）
        
        # 提取流年天干地支
        if not year_pillar or len(year_pillar) < 2:
            return 0.5  # 默认中等流量
        
        year_stem = year_pillar[0]
        year_branch = year_pillar[1]
        year_stem_element = engine.STEM_ELEMENTS.get(year_stem, 'earth')
        year_branch_element = engine.BRANCH_ELEMENTS.get(year_branch, 'earth')
        
        # 1. 检测原局是否有财星
        has_wealth_in_chart = False
        has_output_in_chart = False
        
        for pillar in bazi:
            if len(pillar) >= 2:
                stem = pillar[0]
                branch = pillar[1]
                stem_element = engine.STEM_ELEMENTS.get(stem, 'earth')
                branch_element = engine.BRANCH_ELEMENTS.get(branch, 'earth')
                
                if stem_element == wealth_element or branch_element == wealth_element:
                    has_wealth_in_chart = True
                if stem_element == output_element or branch_element == output_element:
                    has_output_in_chart = True
        
        # 2. 检测流年是否疏通瓶颈
        flow_score = 0.5  # 基础流量
        
        # 如果原局有财但无食伤（堵塞），流年补了食伤 -> F 飙升
        if has_wealth_in_chart and not has_output_in_chart:
            if year_stem_element == output_element or year_branch_element == output_element:
                flow_score = 0.9  # 疏通瓶颈，流量大增
                logger.debug(f"   🔓 疏通瓶颈：原局有财无食伤，流年补食伤 -> F={flow_score:.2f}")
        
        # 如果原局有食伤，流年再补食伤 -> 流量增强
        elif has_output_in_chart:
            if year_stem_element == output_element or year_branch_element == output_element:
                flow_score = 0.8  # 食伤生财，流量增强
        
        # 3. 检测喜用神到位（简化版：基于身强身弱）
        # 这里可以调用engine的strength分析，但为了性能，先简化处理
        # 如果流年五行生助日主（对于身弱），或流年五行是财官（对于身强），流量提升
        
        # 4. 检测财星到位
        if year_stem_element == wealth_element or year_branch_element == wealth_element:
            flow_score = min(1.0, flow_score + 0.2)  # 财星到位，流量提升
        
        return max(0.0, min(1.0, flow_score))
        
    except Exception as e:
        logger.error(f"计算Flow Vector失败: {e}")
        return 0.5  # 默认值


def calculate_capacity_vector(
    engine: GraphNetworkEngine,
    bazi: List[str],
    day_master: str,
    strength_type: str,
    year_pillar: str,
    luck_pillar: Optional[str] = None
) -> float:
    """
    计算掌控系数向量 C(t)
    
    物理定义：日主获取并留存能量的能力
    古诀映射：身强担财、身弱得助、从格顺势
    
    计算逻辑：
    - 身弱模型：C ∝ E_self (流年帮身，掌控力提升)
    - 身强模型：C ∝ 1 / E_self (流年泄身，去臃肿，掌控力提升)
    - 特殊模型：如果是专旺/从格，顺势即为高掌控
    
    Args:
        engine: GraphNetworkEngine 实例（已初始化）
        bazi: 八字列表
        day_master: 日主天干
        strength_type: 身强类型 ('Strong', 'Weak', 'Special_Strong', 'Follower', 'Balanced')
        year_pillar: 流年干支
        luck_pillar: 大运干支（可选）
    
    Returns:
        float: 掌控系数 0.0-1.0
    """
    try:
        # 获取日主元素
        dm_element = engine.STEM_ELEMENTS.get(day_master, 'earth')
        
        # 确定帮身元素（印、比）和泄身元素（食伤、财、官）
        resource_element = None  # 印星（生我的）
        for attacker, defender in CONTROL.items():
            if defender == dm_element:
                resource_element = attacker  # 印星
                break
        
        output_element = GENERATION.get(dm_element)  # 食伤（我生的）
        wealth_element = CONTROL.get(dm_element)  # 财星（我克的）
        
        # 提取流年天干地支
        if not year_pillar or len(year_pillar) < 2:
            return 0.5  # 默认中等掌控
        
        year_stem = year_pillar[0]
        year_branch = year_pillar[1]
        year_stem_element = engine.STEM_ELEMENTS.get(year_stem, 'earth')
        year_branch_element = engine.BRANCH_ELEMENTS.get(year_branch, 'earth')
        
        capacity_score = 0.5  # 基础掌控
        
        # 根据身强类型计算
        if strength_type in ['Weak', 'Extreme_Weak']:
            # 身弱模型：流年帮身（印、比）-> 掌控力提升
            if (year_stem_element == resource_element or year_branch_element == resource_element or
                year_stem_element == dm_element or year_branch_element == dm_element):
                capacity_score = 0.8  # 身弱得助，掌控力提升
                logger.debug(f"   💪 身弱得助：流年帮身 -> C={capacity_score:.2f}")
            else:
                capacity_score = 0.3  # 身弱无助，掌控力低
        
        elif strength_type in ['Strong', 'Special_Strong']:
            # 身强模型：流年泄身（食伤、财、官）-> 去臃肿，掌控力提升
            if (year_stem_element == output_element or year_branch_element == output_element or
                year_stem_element == wealth_element or year_branch_element == wealth_element):
                capacity_score = 0.8  # 身强泄身，掌控力提升
                logger.debug(f"   🎯 身强泄身：流年去臃肿 -> C={capacity_score:.2f}")
            else:
                capacity_score = 0.6  # 身强但无泄，掌控力中等
        
        elif strength_type == 'Follower':
            # 从格模型：顺势即为高掌控
            # 检测流年是否顺势（与从的五行一致）
            # 简化处理：从格通常从财或从官，流年财官到位 -> 高掌控
            if (year_stem_element == wealth_element or year_branch_element == wealth_element):
                capacity_score = 0.9  # 从格顺势，高掌控
            else:
                capacity_score = 0.4  # 从格逆势，掌控力低
        
        else:  # Balanced
            # 中和模型：平衡状态，掌控力中等
            capacity_score = 0.5
        
        return max(0.0, min(1.0, capacity_score))
        
    except Exception as e:
        logger.error(f"计算Capacity Vector失败: {e}")
        return 0.5  # 默认值


def calculate_volatility_sigma(
    engine: GraphNetworkEngine,
    bazi: List[str],
    day_master: str,
    year_pillar: str,
    luck_pillar: Optional[str] = None
) -> float:
    """
    计算波动/爆发系数 σ(t)
    
    物理定义：系统的震荡幅度（不稳定性）
    古诀映射：辰戌冲（开库）、羊刃倒戈、三合局
    
    临界值逻辑：
    - 冲库 (Tomb Clash)：计算冲量 I vs 阻力 R
    - 若 0.8 < I/R < 1.5 -> 开库 (Boom)
    - 若 I/R > 1.5 -> 崩塌 (Crash)
    
    Args:
        engine: GraphNetworkEngine 实例（已初始化）
        bazi: 八字列表
        day_master: 日主天干
        year_pillar: 流年干支
        luck_pillar: 大运干支（可选）
    
    Returns:
        float: 波动系数 0.0-2.0（0.0=平静，2.0=剧烈震荡）
    """
    try:
        from .tomb_physics import check_tomb_opening, calculate_tomb_clash_intensity
        
        if not year_pillar or len(year_pillar) < 2:
            return 0.0  # 无流年，无波动
        
        year_branch = year_pillar[1]
        
        # 1. 检测地支刑冲合害
        volatility = 0.0
        
        # 提取所有地支
        branches = [p[1] for p in bazi if len(p) >= 2]
        if luck_pillar and len(luck_pillar) >= 2:
            branches.append(luck_pillar[1])
        branches.append(year_branch)
        
        # 检测冲
        from core.interactions import BRANCH_CLASHES
        clash_count = 0
        for i, b1 in enumerate(branches):
            for j, b2 in enumerate(branches):
                if i != j and BRANCH_CLASHES.get(b1) == b2:
                    clash_count += 1
        
        # 每个冲增加波动
        volatility += clash_count * 0.3
        
        # 2. 检测墓库冲开（重点逻辑）
        tomb_branches = ['辰', '戌', '丑', '未']
        has_tomb_in_chart = any(b in branches[:-1] for b in tomb_branches)  # 原局或大运有库
        year_is_tomb = year_branch in tomb_branches
        
        if has_tomb_in_chart and year_is_tomb:
            # 检测是否冲库
            tomb_result = check_tomb_opening(
                engine, bazi, day_master, year_pillar, luck_pillar
            )
            
            if tomb_result.get('tomb_opened'):
                # 开库：剧烈波动（爆发）
                volatility = 1.5  # 高波动，可能爆发
                logger.debug(f"   🏆 墓库冲开：剧烈波动 -> σ={volatility:.2f}")
            elif tomb_result.get('tomb_collapsed'):
                # 坍塌：极端波动（灾难）
                volatility = 2.0  # 极端波动，可能灾难
                logger.debug(f"   💀 墓库坍塌：极端波动 -> σ={volatility:.2f}")
            else:
                # 库未动：中等波动
                volatility = 0.5
        
        # 3. 检测三合局（简化版）
        # 如果流年与两个地支形成三合局，增加波动
        # 这里简化处理，实际应该检测完整的三合局
        
        # 4. 检测羊刃倒戈（简化版）
        # 如果流年冲日支（羊刃位），增加波动
        if len(bazi) >= 3:
            day_branch = bazi[2][1] if len(bazi[2]) >= 2 else None
            if day_branch and BRANCH_CLASHES.get(day_branch) == year_branch:
                volatility += 0.5  # 冲日支，增加波动
        
        return max(0.0, min(2.0, volatility))
        
    except Exception as e:
        logger.error(f"计算Volatility Sigma失败: {e}")
        return 0.0  # 默认无波动

