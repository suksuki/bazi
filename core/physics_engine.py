"""
QGA 物理内核引擎 (Physics Engine)
封装所有物理计算函数，包括能量计算和交互阻尼

基于FDS-V1.1规范，从Step 3和Step 4验证成功的代码中提取
"""

from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import sys
from functools import lru_cache

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



@lru_cache(maxsize=1)
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



@lru_cache(maxsize=1)
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
    FDS-V1.4 Compliant Energy Calculation
    Implements Vector Flux with Hidden Stem Ratios & Seasonal Damping.
    
    Args:
        chart: 四柱八字 ['年柱', '月柱', '日柱', '时柱']
        day_master: 日主
        ten_god_type: 十神类型（如'七杀', '羊刃'）
        weights: (Deprecated) Compatibility argument, ignored in V1.4 logic.
        
    Returns:
        Energy flux value (float)
    """
    # [FDS-V1.5 FIX] 羊刃特殊处理
    # "羊刃" 不是标准十神，而是 "劫财" 在帝旺位置的特殊名称
    # 壬日主 -> 羊刃在子 (子中藏癸, 癸是壬的劫财)
    # 甲日主 -> 羊刃在卯 (卯中藏乙, 乙是甲的劫财)
    # 丙日主 -> 羊刃在午 (午中藏丁, 丁是丙的劫财)
    # etc.
    BLADE_BRANCH_MAP = {
        '甲': '卯', '乙': '寅', '丙': '午', '丁': '巳',
        '戊': '午', '己': '巳', '庚': '酉', '辛': '申',
        '壬': '子', '癸': '亥'
    }
    
    is_blade_search = ten_god_type == '羊刃'
    if is_blade_search:
        # 转换为劫财搜索，但需要验证地支是否为帝旺位置
        ten_god_type = '劫财'
        blade_branch = BLADE_BRANCH_MAP.get(day_master)
    
    # 1. Load Physics Constants from Schema
    from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
    from core.trinity.core.nexus.definitions import PhysicsConstants, BaziParticleNexus
    
    physics_cfg = DEFAULT_FULL_ALGO_PARAMS['physics']
    season_weights = physics_cfg.get('seasonWeights', {})       # {wang: 1.2, xiang: 1.0, ...}
    hidden_ratios = physics_cfg.get('hiddenStemRatios', {})     # {main: 0.6, middle: 0.3, remnant: 0.1}
    pillar_weights = physics_cfg.get('pillarWeights', {})       # {year: 0.8, month: 1.2, ...}
    structure_params = DEFAULT_FULL_ALGO_PARAMS.get('structure', {})
    interactions_cfg = DEFAULT_FULL_ALGO_PARAMS.get('interactions', {})
    vault_cfg = interactions_cfg.get('vault', {})
    
    total_energy = 0.0
    
    # Helper to determine Phase (Wang/Xiang/Xiu/Qiu/Si)
    def _get_phase(stem_elem: str, season_elem: str) -> str:
        if stem_elem == season_elem:
            return 'wang'
        if PhysicsConstants.GENERATION.get(season_elem) == stem_elem: # Season generates Stem
            return 'xiang'
        if PhysicsConstants.GENERATION.get(stem_elem) == season_elem: # Stem generates Season
            return 'xiu'
        if PhysicsConstants.CONTROL.get(stem_elem) == season_elem: # Stem controls Season
            return 'qiu'
        if PhysicsConstants.CONTROL.get(season_elem) == stem_elem: # Season controls Stem
            return 'si'
        return 'si' # Default low

    # Helper to check if a branch is clashed by any other branch in the chart
    def _check_clash_exists_in_chart(target_branch: str, all_branches: List[str]) -> bool:
        for b in all_branches:
            if check_clash(target_branch, b):
                return True
        return False

    # Safe extraction of Month Branch (Season Ruler)
    context_month_branch = chart[1][1] if len(chart) > 1 and len(chart[1]) > 1 else (chart[0][1] if chart else "")
    month_element = BaziParticleNexus.get_branch_main_element(context_month_branch)
    
    pillars_names = ['year', 'month', 'day', 'hour']
    chart_branches = [p[1] for p in chart if len(p) > 1]
    
    # === Main Loop: Iterate Pillars ===
    for idx, pillar_str in enumerate(chart):
        if idx >= len(pillars_names): 
            break
        
        stem_char = pillar_str[0]
        branch_char = pillar_str[1]
        pillar_key = pillars_names[idx]
        pillar_w = pillar_weights.get(pillar_key, 1.0)
        
        # --- Part A: Hidden Stems (Ground Field / Rooting) ---
        raw_hidden = BaziParticleNexus.get_branch_weights(branch_char)
        
        for h_idx, (hidden_stem, _) in enumerate(raw_hidden):
            # Determine Ratio Type
            ratio_type = 'remnant'
            if h_idx == 0: ratio_type = 'main'
            elif h_idx == 1: ratio_type = 'middle'
            
            # Check ID
            current_ten_god = BaziParticleNexus.get_shi_shen(hidden_stem, day_master)
            
            if current_ten_god == ten_god_type:
                # [FDS-V1.5] 羊刃位置验证
                # 如果正在搜索羊刃（已转换为劫财），必须验证地支是否为帝旺位置
                if is_blade_search and branch_char != blade_branch:
                    continue  # 跳过非帝旺位置的劫财
                
                # Term 1: Mass
                mass = hidden_ratios.get(ratio_type, 0.1)
                
                # Term 2: Seasonality
                h_elem = BaziParticleNexus.get_element(hidden_stem)
                phase = _get_phase(h_elem, month_element)
                season_mod = season_weights.get(phase, 0.45) # Default to 'si'
                
                # Term 3: Structure Bonus (Same Pillar)
                # If checking YangRen (Blade), and it's Day Pillar, it's the "Day Blade" (Extreme)
                structure_mod = 1.0
                if pillar_key == 'day' and is_blade_search:
                    structure_mod = structure_params.get('samePillarBonus', 1.5)
                
                # Calculate Base Term Energy
                term_energy = mass * season_mod * pillar_w * structure_mod
                
                # [V3.0] Vault Topology (Tomb Logic)
                # Check if this branch is a Tomb (Chen/Xu/Chou/Wei)
                if branch_char in ['辰', '戌', '丑', '未']:
                    is_open = _check_clash_exists_in_chart(branch_char, chart_branches)
                    if is_open:
                        term_energy *= vault_cfg.get('openBonus', 1.8)
                    else:
                        term_energy *= vault_cfg.get('sealedDamping', 0.4)
                
                total_energy += term_energy

        # --- Part B: Exposed Stems (Sky Field) ---
        # Ten Gods like Seven Killings often float in Stems.
        # Note: Yang Ren is strictly a Branch phenomenon (Emperor Prosperous), 
        # but sometimes Stem Rob Wealth is counted as assistance. 
        # Here we only count if ten_god_type matches Stem.
        stem_ten_god = BaziParticleNexus.get_shi_shen(stem_char, day_master)
        if stem_ten_god == ten_god_type:
            # Stem Mass is defined as Base (1.0) * ExposedBonus
            stem_mass = 1.0 * structure_params.get('exposedBoost', 1.5)
            
            # Seasonality for Stem
            s_elem = BaziParticleNexus.get_element(stem_char)
            s_phase = _get_phase(s_elem, month_element)
            s_season_mod = season_weights.get(s_phase, 0.45)
            
            # Add to total
            total_energy += (stem_mass * s_season_mod * pillar_w)

    return round(total_energy, 4)


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


def analyze_clash_dynamics(target_branch: str, trigger_branch: str) -> Dict[str, Any]:
    """
    [V2.3] 判断冲的物理性质：是 'OPENER' (开库) 还是 'BREAKER' (破坏)
    
    核心逻辑：
    - 四墓库（辰戌丑未）相冲，且为库位对冲（辰戌、丑未）时，视为开库。
    - 开库释放库中藏干，增加系统的能量多样性和做功潜力（Entropy Delta > 0）。
    - 破坏性相冲（如子午、卯酉）损耗根基权重（Breaker）。
    
    Returns:
        Dict: {
            "type": "OPENER" | "BREAKER",
            "entropy_delta": float,  # 能量释放/损耗系数
            "structure_risk": float # 结构性风险系数
        }
    """
    vaults = ['辰', '戌', '丑', '未']
    is_clash = check_clash(target_branch, trigger_branch)
    
    if not is_clash:
        return {"type": "NONE", "entropy_delta": 0.0, "structure_risk": 0.0}
    
    # 墓库对冲判定
    if target_branch in vaults and trigger_branch in vaults:
        # 辰戌冲 / 丑未冲
        return {
            "type": "OPENER",
            "entropy_delta": 0.45,  # 正值：释放库中藏干能量
            "structure_risk": 0.2   # 低风险：受控的能量释放
        }
    
    # 破坏性相冲
    return {
        "type": "BREAKER",
        "entropy_delta": -0.6,    # 负值：主根损耗
        "structure_risk": 0.8     # 高风险：结构可能崩塌
    }


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
    
    elif rule_name == "Kill_Blade_Resonance":
        # 刃杀共振：两者能量都在高位且接近平衡
        e_blade = energy_flux.get("E_blade", 0.0)
        e_kill = energy_flux.get("E_kill", 0.0)
        
        if e_blade > 0.6 and e_kill > 0.5:
            # [V1.5.2 Wide Window] 聚变响应区间扩展至 0.5 - 2.0
            balance = e_blade / e_kill if e_kill > 0 else 0
            return 0.5 <= balance <= 2.0
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


def analyze_clash_dynamics(target_branch: str, trigger_branch: str) -> Dict[str, Any]:
    """
    [V2.3] 判断冲的物理性质：是 'OPENER' (开库) 还是 'BREAKER' (破坏)
    
    核心逻辑：
    - 四墓库（辰戌丑未）相冲，且为库位对冲（辰戌、丑未）时，视为开库。
    - 开库释放库中藏干，增加系统的能量多样性和做功潜力（Entropy Delta > 0）。
    - 破坏性相冲（如子午、卯酉）损耗根基权重（Breaker）。
    
    Returns:
        Dict: {
            "type": "OPENER" | "BREAKER",
            "entropy_delta": float,  # 能量释放/损耗系数
            "structure_risk": float # 结构性风险系数
        }
    """
    vaults = ['辰', '戌', '丑', '未']
    is_clash = check_clash(target_branch, trigger_branch)
    
    if not is_clash:
        return {"type": "NONE", "entropy_delta": 0.0, "structure_risk": 0.0}
    
    # 墓库对冲判定
    if target_branch in vaults and trigger_branch in vaults:
        # 辰戌冲 / 丑未冲
        return {
            "type": "OPENER",
            "entropy_delta": 0.45,  # 正值：释放库中藏干能量
            "structure_risk": 0.2   # 低风险：受控的能量释放
        }
    
    # 破坏性相冲
    return {
        "type": "BREAKER",
        "entropy_delta": -0.6,    # 负值：主根损耗
        "structure_risk": 0.8     # 高风险：结构可能崩塌
    }
