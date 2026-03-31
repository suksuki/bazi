"""
V12.0 墓库物理引擎 (Tomb Physics Engine)

专门计算"墓库冲开"的临界概率和物理机制
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from core.engine_graph import GraphNetworkEngine
from core.interactions import BRANCH_CLASHES

logger = logging.getLogger(__name__)


def calculate_tomb_clash_intensity(
    engine: GraphNetworkEngine,
    bazi: List[str],
    day_master: str,
    year_pillar: str,
    luck_pillar: Optional[str] = None
) -> Dict[str, float]:
    """
    计算墓库冲的强度（冲量 I vs 阻力 R）
    
    Args:
        engine: GraphNetworkEngine 实例
        bazi: 八字列表
        day_master: 日主天干
        year_pillar: 流年干支
        luck_pillar: 大运干支（可选）
    
    Returns:
        dict: {
            'intensity': float,  # 冲量 I
            'resistance': float,  # 阻力 R
            'ratio': float,  # I/R 比值
            'tomb_branches': List[str]  # 涉及的墓库地支
        }
    """
    try:
        # 墓库地支
        tomb_branches = ['辰', '戌', '丑', '未']
        
        # 提取所有地支
        branches = [p[1] for p in bazi if len(p) >= 2]
        if luck_pillar and len(luck_pillar) >= 2:
            branches.append(luck_pillar[1])
        
        if not year_pillar or len(year_pillar) < 2:
            return {
                'intensity': 0.0,
                'resistance': 1.0,
                'ratio': 0.0,
                'tomb_branches': []
            }
        
        year_branch = year_pillar[1]
        
        # 检测原局中的墓库
        chart_tombs = [b for b in branches if b in tomb_branches]
        
        # 检测流年是否冲库
        intensity = 0.0
        resistance = 1.0
        involved_tombs = []
        
        for tomb in chart_tombs:
            # 检测是否被冲
            clash_target = BRANCH_CLASHES.get(tomb)
            if clash_target == year_branch:
                # 流年冲库
                intensity += 1.0
                involved_tombs.append(tomb)
                
                # 计算阻力（基于身强身弱）
                # 简化处理：身强阻力大，身弱阻力小
                try:
                    result = engine.analyze(bazi, day_master, luck_pillar=luck_pillar, year_pillar=year_pillar)
                    strength_score = result.get('strength_score', 50.0)
                    strength_normalized = strength_score / 100.0
                    
                    # 身强时阻力大（1.5），身弱时阻力小（0.5）
                    resistance = 0.5 + strength_normalized  # 0.5-1.5
                except:
                    resistance = 1.0  # 默认中等阻力
        
        ratio = intensity / resistance if resistance > 0 else 0.0
        
        return {
            'intensity': intensity,
            'resistance': resistance,
            'ratio': ratio,
            'tomb_branches': involved_tombs
        }
        
    except Exception as e:
        logger.error(f"计算墓库冲强度失败: {e}")
        return {
            'intensity': 0.0,
            'resistance': 1.0,
            'ratio': 0.0,
            'tomb_branches': []
        }


def check_tomb_opening(
    engine: GraphNetworkEngine,
    bazi: List[str],
    day_master: str,
    year_pillar: str,
    luck_pillar: Optional[str] = None
) -> Dict[str, Any]:
    """
    检查墓库是否被冲开（临界判定）
    
    临界值逻辑：
    - 若 0.8 < I/R < 1.5 -> 开库 (Boom)
    - 若 I/R > 1.5 -> 崩塌 (Crash)
    - 若 I/R < 0.8 -> 未动
    
    Args:
        engine: GraphNetworkEngine 实例
        bazi: 八字列表
        day_master: 日主天干
        year_pillar: 流年干支
        luck_pillar: 大运干支（可选）
    
    Returns:
        dict: {
            'tomb_opened': bool,  # 是否开库
            'tomb_collapsed': bool,  # 是否坍塌
            'intensity_ratio': float,  # I/R 比值
            'details': List[str]  # 详细信息
        }
    """
    try:
        clash_result = calculate_tomb_clash_intensity(
            engine, bazi, day_master, year_pillar, luck_pillar
        )
        
        ratio = clash_result['ratio']
        involved_tombs = clash_result['tomb_branches']
        
        tomb_opened = False
        tomb_collapsed = False
        details = []
        
        if ratio > 0:
            if 0.8 < ratio < 1.5:
                # 开库：理想状态，财富爆发
                tomb_opened = True
                details.append(f"🏆 墓库冲开：I/R={ratio:.2f}，财富爆发")
            elif ratio >= 1.5:
                # 坍塌：过度冲击，灾难
                tomb_collapsed = True
                details.append(f"💀 墓库坍塌：I/R={ratio:.2f}，过度冲击")
            else:
                # 未动：冲击不足
                details.append(f"🔒 墓库未动：I/R={ratio:.2f}，冲击不足")
        
        if involved_tombs:
            details.append(f"涉及墓库：{', '.join(involved_tombs)}")
        
        return {
            'tomb_opened': tomb_opened,
            'tomb_collapsed': tomb_collapsed,
            'intensity_ratio': ratio,
            'details': details,
            'involved_tombs': involved_tombs
        }
        
    except Exception as e:
        logger.error(f"检查墓库状态失败: {e}")
        return {
            'tomb_opened': False,
            'tomb_collapsed': False,
            'intensity_ratio': 0.0,
            'details': [f"检查失败: {str(e)}"],
            'involved_tombs': []
        }

