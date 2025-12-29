"""
QGA 物理内核引擎 (Physics Engine)
封装所有物理计算函数，包括能量计算和交互阻尼

基于FDS-V1.1规范，从Step 3和Step 4验证成功的代码中提取
"""

from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core.trinity.core.nexus.definitions import BaziParticleNexus
from core.trinity.core.intelligence.symbolic_stars import SymbolicStarsEngine


# 冲合关系定义
CLASH_PAIRS = [
    ('子', '午'), ('丑', '未'), ('寅', '申'), ('卯', '酉'), 
    ('辰', '戌'), ('巳', '亥')
]

COMBINATION_PAIRS = [
    ('子', '丑'), ('寅', '亥'), ('卯', '戌'), ('辰', '酉'),
    ('巳', '申'), ('午', '未')
]


def compute_energy_flux(
    chart: List[str],
    day_master: str,
    ten_god_type: str,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    计算十神能量流（参数化版本）
    
    将Step 3中的"羊刃=1.0, 七杀=0.8"等逻辑参数化，支持任意十神类型
    
    Args:
        chart: 四柱八字 ['年柱', '月柱', '日柱', '时柱']
        day_master: 日主
        ten_god_type: 十神类型（如'七杀', '羊刃', '正印', '偏印'）
        weights: 能量权重字典（可选，默认使用框架标准权重）
            - base: 基础能量（默认1.0）
            - month_resonance: 月令共振权重（默认1.42）
            - rooting: 通根权重（默认3.0）
            - generation: 得生权重（默认1.0）
        
    Returns:
        十神能量值
        
    Example:
        >>> chart = ['丙寅', '甲午', '戊午', '戊午']
        >>> compute_energy_flux(chart, '戊', '七杀')
        0.8  # 七杀透干通根
        >>> compute_energy_flux(chart, '戊', '羊刃')
        3.0  # 地支三午（羊刃）
    """
    if weights is None:
        weights = {
            'base': 1.0,
            'month_resonance': 1.42,  # 从config_schema.py获取
            'rooting': 3.0,
            'generation': 1.0
        }
    
    stems = [p[0] for p in chart]
    branches = [p[1] for p in chart]
    month_branch = branches[1]  # 月支
    
    energy = 0.0
    
    # 特殊处理：羊刃（通过地支计算）
    if ten_god_type == '羊刃':
        yang_ren_map = SymbolicStarsEngine.YANG_REN_MAP
        yang_ren_branch = yang_ren_map.get(day_master)
        if yang_ren_branch:
            blade_count = branches.count(yang_ren_branch)
            energy = weights['base'] * blade_count
            # 月令共振加成
            if month_branch == yang_ren_branch:
                energy *= weights['month_resonance']
        return energy
    
    # 其他十神：通过天干计算
    ten_god_stems = []
    for i, stem in enumerate(stems):
        if i == 2:  # 跳过日主
            continue
        ten_god = BaziParticleNexus.get_shi_shen(stem, day_master)
        if ten_god == ten_god_type:
            ten_god_stems.append((i, stem))
    
    # 检查是否有根（通根权重）
    for _, ten_god_stem in ten_god_stems:
        has_root = False
        
        # 检查自坐
        pillar_idx = ten_god_stems[0][0]
        if pillar_idx < len(branches):
            branch = branches[pillar_idx]
            hidden_stems = BaziParticleNexus.get_branch_weights(branch)
            for hidden_stem, weight in hidden_stems:
                if hidden_stem == ten_god_stem and weight >= 5:  # 主气或中气
                    has_root = True
                    break
        
        # 检查其他地支
        if not has_root:
            for branch in branches:
                hidden_stems = BaziParticleNexus.get_branch_weights(branch)
                for hidden_stem, weight in hidden_stems:
                    if hidden_stem == ten_god_stem and weight >= 5:
                        has_root = True
                        break
                if has_root:
                    break
        
        # 计算能量
        if has_root:
            base_energy = weights['base']
            # 月令共振加成
            if pillar_idx == 1:  # 月干
                base_energy *= weights['month_resonance']
            # 通根加成
            base_energy *= weights['rooting']
            energy += base_energy
        else:
            # 无根：只有基础能量（虚浮）
            energy += weights['base'] * 0.5
    
    return energy


def check_clash(branch1: str, branch2: str) -> bool:
    """检查两个地支是否对冲"""
    return (branch1, branch2) in CLASH_PAIRS or (branch2, branch1) in CLASH_PAIRS


def check_combination(branch1: str, branch2: str) -> bool:
    """检查两个地支是否相合"""
    return (branch1, branch2) in COMBINATION_PAIRS or (branch2, branch1) in COMBINATION_PAIRS


def get_clash_branch(branch: str) -> Optional[str]:
    """获取与指定地支对冲的地支"""
    for b1, b2 in CLASH_PAIRS:
        if branch == b1:
            return b2
        if branch == b2:
            return b1
    return None


def check_has_combination_rescue(chart: List[str], clash_branch: str) -> bool:
    """
    检查原局是否有合来解救冲
    
    Args:
        chart: 四柱八字
        clash_branch: 流年冲刃的地支
        
    Returns:
        是否有合解救
    """
    branches = [p[1] for p in chart]
    
    # 检查原局是否有与冲刃地支相合的地支
    for branch in branches:
        if check_combination(branch, clash_branch):
            return True
    
    return False


def check_has_existing_clash(chart: List[str], month_branch: str) -> bool:
    """
    检查原局是否已有冲（如子午冲）
    
    Args:
        chart: 四柱八字
        month_branch: 月令地支（羊刃）
        
    Returns:
        是否已有冲
    """
    branches = [p[1] for p in chart]
    clash_branch = get_clash_branch(month_branch)
    
    if not clash_branch:
        return False
    
    # 检查原局是否有与月令对冲的地支
    for branch in branches:
        if branch == clash_branch:
            return True
    
    return False


def calculate_interaction_damping(
    chart: List[str],
    month_branch: str,
    clash_branch: str,
    lambda_coefficients: Optional[Dict[str, float]] = None
) -> float:
    """
    计算交互阻尼系数（λ）
    
    将Step 4中的"贪合忘冲"、"冲上加冲"逻辑封装成通用函数
    
    Args:
        chart: 四柱八字
        month_branch: 月令地支（羊刃）
        clash_branch: 流年冲刃的地支
        lambda_coefficients: Lambda系数字典（可选，默认使用A-03的值）
            - resonance: 共振态（原局已有冲，默认2.5）
            - hard_landing: 硬着陆（无解救，默认1.8）
            - damping: 阻尼态（有合缓冲，默认1.2）
        
    Returns:
        激增系数 λ
        
    Example:
        >>> chart = ['丙寅', '甲午', '戊午', '戊午']
        >>> calculate_interaction_damping(chart, '午', '子')
        1.2  # 如果有合解救
        1.8  # 如果无解救
        2.5  # 如果原局已有冲（共振破碎）
    """
    if lambda_coefficients is None:
        lambda_coefficients = {
            'resonance': 2.5,    # 共振态：双冲共振，系统必然崩溃
            'hard_landing': 1.8, # 硬着陆：无缓冲，中等风险
            'damping': 1.2       # 阻尼态：有合缓冲，降低冲击
        }
    
    # 检查是否有合解救（贪合忘冲）
    if check_has_combination_rescue(chart, clash_branch):
        return lambda_coefficients['damping']
    
    # 检查是否已有冲（共振破碎）
    if check_has_existing_clash(chart, month_branch):
        return lambda_coefficients['resonance']
    
    # 无解救（硬着陆）
    return lambda_coefficients['hard_landing']


def calculate_clash_count(chart: List[str]) -> int:
    """
    计算刑冲数量
    
    Args:
        chart: 四柱八字
        
    Returns:
        刑冲总数
    """
    branches = [p[1] for p in chart]
    
    harm_pairs = [
        ('子', '未'), ('丑', '午'), ('寅', '巳'), ('卯', '辰'),
        ('申', '亥'), ('酉', '戌')
    ]
    
    clash_count = 0
    for i, b1 in enumerate(branches):
        for j, b2 in enumerate(branches[i+1:], i+1):
            if check_clash(b1, b2):
                clash_count += 1
            if (b1, b2) in harm_pairs or (b2, b1) in harm_pairs:
                clash_count += 1
    
    return clash_count

