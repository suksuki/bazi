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


def _get_clash_pairs_from_module() -> List[Tuple[str, str]]:
    """从BAZI_FUNDAMENTAL的MOD_03_TRANSFORM模块获取冲合关系"""
    try:
        from core.logic_registry import LogicRegistry
        
        registry = LogicRegistry()
        modules = registry.get_active_modules(theme_id="BAZI_FUNDAMENTAL")
        
        # 查找MOD_03_TRANSFORM模块
        mod_03 = None
        for module in modules:
            if module.get('id') == 'MOD_03_TRANSFORM':
                mod_03 = module
                break
        
        if mod_03 and 'pattern_data' in mod_03:
            pattern_data = mod_03['pattern_data']
            physics_kernel = pattern_data.get('physics_kernel', {})
            
            # 尝试从physics_kernel中读取冲合关系
            clash_rules = physics_kernel.get('clash_rules', [])
            if clash_rules:
                pairs = []
                for rule in clash_rules:
                    if isinstance(rule, dict) and 'branch1' in rule and 'branch2' in rule:
                        pairs.append((rule['branch1'], rule['branch2']))
                if pairs:
                    return pairs
        
        # 如果模块未定义，回退到硬编码
        return CLASH_PAIRS
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"无法从模块读取冲合关系，使用默认值: {e}")
        return CLASH_PAIRS


def _get_combination_pairs_from_module() -> List[Tuple[str, str]]:
    """从BAZI_FUNDAMENTAL的MOD_03_TRANSFORM模块获取合化关系"""
    try:
        from core.logic_registry import LogicRegistry
        
        registry = LogicRegistry()
        modules = registry.get_active_modules(theme_id="BAZI_FUNDAMENTAL")
        
        # 查找MOD_03_TRANSFORM模块
        mod_03 = None
        for module in modules:
            if module.get('id') == 'MOD_03_TRANSFORM':
                mod_03 = module
                break
        
        if mod_03 and 'pattern_data' in mod_03:
            pattern_data = mod_03['pattern_data']
            physics_kernel = pattern_data.get('physics_kernel', {})
            
            # 尝试从physics_kernel中读取合化关系
            combination_rules = physics_kernel.get('combination_rules', [])
            if combination_rules:
                pairs = []
                for rule in combination_rules:
                    if isinstance(rule, dict) and 'branch1' in rule and 'branch2' in rule:
                        pairs.append((rule['branch1'], rule['branch2']))
                if pairs:
                    return pairs
        
        # 如果模块未定义，回退到硬编码
        return COMBINATION_PAIRS
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"无法从模块读取合化关系，使用默认值: {e}")
        return COMBINATION_PAIRS


def compute_energy_flux(
    chart: List[str],
    day_master: str,
    ten_god_type: str,
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    计算十神能量流（参数化版本）
    
    将Step 3中的"羊刃=1.0, 七杀=0.8"等逻辑参数化，支持任意十神类型
    参数从config_schema.py的DEFAULT_FULL_ALGO_PARAMS读取
    
    Args:
        chart: 四柱八字 ['年柱', '月柱', '日柱', '时柱']
        day_master: 日主
        ten_god_type: 十神类型（如'七杀', '羊刃', '正印', '偏印'）
        weights: 能量权重字典（可选，默认从配置读取）
            - base: 基础能量（默认1.0）
            - month_resonance: 月令共振权重（从config_schema.py读取）
            - rooting: 通根权重（从config_schema.py读取）
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
        # 从配置读取参数
        try:
            from core.config_manager import ConfigManager
            from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
            
            config = ConfigManager.load_config()
            physics_params = config.get('physics', DEFAULT_FULL_ALGO_PARAMS.get('physics', {}))
            structure_params = config.get('structure', DEFAULT_FULL_ALGO_PARAMS.get('structure', {}))
            
            pillar_weights = physics_params.get('pillarWeights', {})
            month_resonance = pillar_weights.get('month', 1.42)
            rooting_weight = structure_params.get('rootingWeight', 1.0)
            
            # 应用通根饱和函数（如果有定义）
            rooting_saturation_max = structure_params.get('rootingSaturationMax', 2.5)
            rooting_saturation_steepness = structure_params.get('rootingSaturationSteepness', 0.8)
            
            # 使用饱和函数计算实际通根权重
            import math
            # Tanh饱和函数: saturation = max_val * tanh(weight * steepness)
            actual_rooting = rooting_saturation_max * math.tanh(rooting_weight * rooting_saturation_steepness)
            
            weights = {
                'base': 1.0,
                'month_resonance': month_resonance,
                'rooting': actual_rooting,
                'generation': 1.0
            }
        except Exception as e:
            # 如果读取配置失败，使用默认值
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"无法从配置读取参数，使用默认值: {e}")
            weights = {
                'base': 1.0,
                'month_resonance': 1.42,
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
    """
    检查两个地支是否对冲
    
    优先从BAZI_FUNDAMENTAL的MOD_03_TRANSFORM模块读取冲合关系，
    如果模块未定义，则使用默认的CLASH_PAIRS。
    
    Args:
        branch1: 地支1
        branch2: 地支2
        
    Returns:
        是否对冲
    """
    clash_pairs = _get_clash_pairs_from_module()
    return (branch1, branch2) in clash_pairs or (branch2, branch1) in clash_pairs


def check_combination(branch1: str, branch2: str) -> bool:
    """
    检查两个地支是否相合
    
    优先从BAZI_FUNDAMENTAL的MOD_03_TRANSFORM模块读取合化关系，
    如果模块未定义，则使用默认的COMBINATION_PAIRS。
    
    Args:
        branch1: 地支1
        branch2: 地支2
        
    Returns:
        是否相合
    """
    combination_pairs = _get_combination_pairs_from_module()
    return (branch1, branch2) in combination_pairs or (branch2, branch1) in combination_pairs


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


def check_trigger(
    rule_name: str,
    context: Dict[str, Any]
) -> bool:
    """
    检查事件触发条件（FDS-V1.4）
    
    基于InteractionEngine的事件标签匹配，实现事件触发字典
    
    Args:
        rule_name: 规则名称，如 "Day_Branch_Clash", "Missing_Blade_Arrives"
        context: 上下文字典，包含：
            - chart: 四柱八字
            - day_master: 日主
            - day_branch: 日支
            - luck_pillar: 大运（可选）
            - year_pillar: 流年（可选）
            - flux_events: 事件列表（可选）
            - energy_flux: 能量流字典（可选）
    
    Returns:
        是否触发该规则
        
    Example:
        >>> context = {
        ...     "chart": ["丙寅", "甲午", "戊午", "戊午"],
        ...     "day_master": "戊",
        ...     "day_branch": "午",
        ...     "year_pillar": "子",
        ...     "flux_events": []
        ... }
        >>> check_trigger("Day_Branch_Clash", context)
        True  # 子冲午
    """
    chart = context.get("chart", [])
    day_master = context.get("day_master", "")
    day_branch = context.get("day_branch", "")
    luck_pillar = context.get("luck_pillar", "")
    year_pillar = context.get("year_pillar", "")
    flux_events = context.get("flux_events", [])
    energy_flux = context.get("energy_flux", {})
    
    # 获取地支
    branches = [p[1] for p in chart] if chart else []
    year_branch = year_pillar[1] if year_pillar and len(year_pillar) >= 2 else ""
    luck_branch = luck_pillar[1] if luck_pillar and len(luck_pillar) >= 2 else ""
    
    # 规则映射表
    if rule_name == "Day_Branch_Clash":
        # 日支受到强力冲撞
        # 检查流年地支是否冲日支
        if day_branch and year_branch:
            return check_clash(day_branch, year_branch)
        # 检查大运地支是否冲日支
        if day_branch and luck_branch:
            return check_clash(day_branch, luck_branch)
        # 检查原局是否有冲日支
        for branch in branches:
            if branch != day_branch and check_clash(day_branch, branch):
                return True
        return False
    
    elif rule_name == "Missing_Blade_Arrives":
        # 原局缺羊刃，流年补齐
        from core.trinity.core.intelligence.symbolic_stars import SymbolicStarsEngine
        yang_ren_map = SymbolicStarsEngine.YANG_REN_MAP
        expected_blade = yang_ren_map.get(day_master)
        
        if not expected_blade:
            return False
        
        # 检查原局是否有羊刃
        has_blade = expected_blade in branches
        
        # 如果原局没有羊刃，检查流年是否补齐
        if not has_blade and year_branch == expected_blade:
            return True
        
        # 检查大运是否补齐
        if not has_blade and luck_branch == expected_blade:
            return True
        
        return False
    
    elif rule_name == "Resource_Destruction":
        # 强财克印
        # 检查财星能量是否过强，印星能量是否过弱
        wealth_strength = energy_flux.get("wealth", 0.0)
        resource_strength = energy_flux.get("resource", 0.0)
        
        return wealth_strength > 2.0 and resource_strength < 0.5
    
    elif rule_name == "Blade_Combined_Transformation":
        # 羊刃被合
        from core.trinity.core.intelligence.symbolic_stars import SymbolicStarsEngine
        yang_ren_map = SymbolicStarsEngine.YANG_REN_MAP
        expected_blade = yang_ren_map.get(day_master)
        
        if not expected_blade:
            return False
        
        # 检查羊刃是否在原局
        if expected_blade not in branches:
            return False
        
        # 检查羊刃是否被合
        for branch in branches:
            if branch != expected_blade and check_combination(expected_blade, branch):
                return True
        
        # 检查流年是否合羊刃
        if year_branch and check_combination(expected_blade, year_branch):
            return True
        
        # 检查大运是否合羊刃
        if luck_branch and check_combination(expected_blade, luck_branch):
            return True
        
        return False
    
    else:
        # 未知规则，返回False
        return False


def calculate_integrity_alpha(
    natal_chart: List[str],
    day_master: str,
    day_branch: str,
    flux_events: Optional[List[str]] = None,
    luck_pillar: Optional[str] = None,
    year_pillar: Optional[str] = None,
    energy_flux: Optional[Dict[str, float]] = None
) -> float:
    """
    计算结构完整性alpha值（FDS-V1.4）
    
    采用"扣分制"损伤模型 (Damage Model)
    alpha代表结构的物理完整度 (0.0 - 1.0)
    
    公式: alpha = 1.0 - Σ(扣分项)
    
    Args:
        natal_chart: 四柱八字
        day_master: 日主
        day_branch: 日支
        flux_events: 事件列表（可选，如果提供则直接使用）
        luck_pillar: 大运（可选）
        year_pillar: 流年（可选）
        energy_flux: 能量流字典（可选）
    
    Returns:
        alpha值 (0.0 - 1.0)
        
    Example:
        >>> chart = ["丙寅", "甲午", "戊午", "戊午"]
        >>> alpha = calculate_integrity_alpha(chart, "戊", "午", year_pillar="子")
        >>> alpha
        0.4  # 日支逢冲，扣0.6
    """
    if flux_events is None:
        flux_events = []
    
    if energy_flux is None:
        energy_flux = {}
    
    # 初始化alpha为1.0（完美状态）
    alpha = 1.0
    
    # 构建context用于check_trigger
    context = {
        "chart": natal_chart,
        "day_master": day_master,
        "day_branch": day_branch,
        "luck_pillar": luck_pillar,
        "year_pillar": year_pillar,
        "flux_events": flux_events,
        "energy_flux": energy_flux
    }
    
    # 1. 根基崩塌 (羊刃逢冲) - 致命伤，扣0.6
    if check_trigger("Day_Branch_Clash", context):
        alpha -= 0.6  # 直接扣到0.4，触发破格
    
    # 2. 核心被合 (羊刃/七杀被合绊) - 结构失效，扣0.4
    if check_trigger("Blade_Combined_Transformation", context):
        alpha -= 0.4  # 降至0.6，边缘状态
    
    # 3. 资源断裂 (财坏印) - 续航受损，扣0.3
    if check_trigger("Resource_Destruction", context):
        alpha -= 0.3
    
    # 确保alpha在[0.0, 1.0]范围内
    return max(0.0, min(1.0, alpha))

