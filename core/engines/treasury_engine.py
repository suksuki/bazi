"""
core/engines/treasury_engine.py
-------------------------------
[V6.0 Sub-Engine] 财库与墓库引擎
负责处理：墓库定义、开库检测、财库识别、爆发系数计算

[V6.0+ Parameterization] 所有评分常量从 config_rules 模块读取
"""
from typing import Dict, List, Tuple, Optional

# === Import Configuration Constants ===
from core.config_rules import (
    SCORE_TREASURY_BONUS,
    SCORE_TREASURY_PENALTY,
    SCORE_GENERAL_OPEN,
    WEALTH_MAP,
    TOMB_ELEMENTS,
)


class TreasuryEngine:
    """
    [V6.0 Sub-Engine] 财库与墓库引擎
    负责处理：墓库定义、开库检测、财库识别、爆发系数计算
    """
    
    # 定义五行生克中 "我克者" (财)
    WEALTH_MAP = {
        'Wood': 'Earth',
        'Fire': 'Metal',
        'Earth': 'Water',
        'Metal': 'Wood',
        'Water': 'Fire'
    }

    # 定义墓库的主气属性 (Tomb Element)
    TOMB_ELEMENTS = {
        '辰': 'Water',  # 水库
        '戌': 'Fire',   # 火库
        '丑': 'Metal',  # 金库
        '未': 'Wood'    # 木库
    }

    # V3.0 完整墓库配置 (兼容 QuantumEngine.VAULT_MAPPING)
    VAULT_MAPPING = {
        '辰': {
            'name_cn': 'Dragon',
            'type': 'water_tomb',
            'element': 'water',
            'stems': {
                'main': '戊',
                'residual': '乙',
                'tomb': '癸'
            }
        },
        '戌': {
            'name_cn': 'Dog',
            'type': 'fire_tomb',
            'element': 'fire',
            'stems': {
                'main': '戊',
                'residual': '辛',
                'tomb': '丁'
            }
        },
        '丑': {
            'name_cn': 'Ox',
            'type': 'metal_tomb',
            'element': 'metal',
            'stems': {
                'main': '己',
                'residual': '癸',
                'tomb': '辛'
            }
        },
        '未': {
            'name_cn': 'Sheep',
            'type': 'wood_tomb',
            'element': 'wood',
            'stems': {
                'main': '己',
                'residual': '丁',
                'tomb': '乙'
            }
        }
    }

    def __init__(self, config: dict = None):
        """初始化，支持外部配置覆盖默认值"""
        self.config = config or {}
        # 从配置获取评分参数，优先使用外部传入值
        self.treasury_bonus = self.config.get('score_treasury_bonus', SCORE_TREASURY_BONUS)
        self.treasury_penalty = self.config.get('score_treasury_penalty', SCORE_TREASURY_PENALTY)
        self.general_open_score = self.config.get('score_general_open', SCORE_GENERAL_OPEN)
        
        # 六冲定义
        self.CLASHES = {
            '子': '午', '午': '子',
            '丑': '未', '未': '丑',
            '寅': '申', '申': '寅',
            '卯': '酉', '酉': '卯',
            '辰': '戌', '戌': '辰',
            '巳': '亥', '亥': '巳',
        }

    def check_clash(self, year_branch: str, chart_branches: list) -> bool:
        """
        检测流年地支是否与四柱中的库位发生冲击（开库条件）
        :param year_branch: 流年地支
        :param chart_branches: 四柱地支列表
        :return: 是否有开库的冲击
        """
        if year_branch not in self.VAULT_MAPPING:
            # 流年不是库，检查是否冲开命局中的库
            clash_target = self.CLASHES.get(year_branch)
            if clash_target and clash_target in chart_branches:
                return clash_target in self.VAULT_MAPPING
        else:
            # 流年本身是库，检查是否被命局冲开
            clash_target = self.CLASHES.get(year_branch)
            return clash_target in chart_branches
        return False

    def process_treasury_scoring(self, birth_chart: dict, year_branch: str, 
                                  base_score: float, dm_strength: str,
                                  dm_element: str) -> tuple:
        """
        综合处理财库评分
        :param birth_chart: 包含四柱信息的字典
        :param year_branch: 流年地支
        :param base_score: 基础分数
        :param dm_strength: 日主强弱 ('Strong', 'Medium', 'Weak')
        :param dm_element: 日主五行
        :return: (final_score, details, icon, risk_level)
        """
        details = []
        icon = None
        risk_level = 'none'
        final_score = base_score
        
        # 提取四柱地支
        chart_branches = []
        for key in ['year', 'month', 'day', 'hour']:
            pillar = birth_chart.get(key, '')
            if len(pillar) > 1:
                chart_branches.append(pillar[1])
        
        # 检测开库
        is_open = self.check_clash(year_branch, chart_branches)
        
        if is_open:
            # 确定是否为财库
            is_wealth = self.is_wealth_treasury(dm_element, year_branch)
            
            # 计算加成
            bonus, t_icon, tags = self.calculate_bonus(is_open, is_wealth, dm_strength)
            
            final_score += bonus
            details.extend(tags)
            icon = t_icon
            
            if bonus > 0:
                risk_level = 'opportunity'
            else:
                risk_level = 'warning'
        
        return final_score, details, icon, risk_level


    def is_wealth_treasury(self, day_master_element: str, branch: str) -> bool:
        """
        判断某个地支是否为命主的财库
        :param day_master_element: 日主五行 (e.g., 'Wood')
        :param branch: 地支字符 (e.g., '戌')
        """
        # 1. 获取命主的财星五行
        wealth_element = self.WEALTH_MAP.get(day_master_element)
        if not wealth_element:
            return False
            
        # 2. 获取该地支藏的五行 (主气)
        tomb_content = self.TOMB_ELEMENTS.get(branch)
        if not tomb_content:
            return False  # 不是四库
            
        # 3. 特殊逻辑：土日主的财库
        if day_master_element == 'Wood' and branch in self.TOMB_ELEMENTS:
            return True
             
        return wealth_element == tomb_content

    def calculate_bonus(self, is_open: bool, is_wealth: bool, dm_strength: str) -> Tuple[float, Optional[str], List[str]]:
        """
        计算财库开启后的加成 (V3.5 伦理安全阀逻辑)
        使用 config_rules 中的配置参数
        """
        score = 0.0
        icon = None
        tags = []
        
        if not is_open:
            return 0.0, None, []

        if is_wealth:
            if dm_strength == 'Strong':
                # 身强胜财 - 使用配置中的 SCORE_TREASURY_BONUS
                score = self.treasury_bonus
                icon = "🏆"
                tags = ["身强胜财", "财库爆发", "暴富契机"]
            else:
                # 身弱不胜财 - 使用配置中的 SCORE_TREASURY_PENALTY
                score = self.treasury_penalty
                icon = "⚠️"
                tags = ["身弱不胜财", "财多压身", "风险警示"]
        else:
            # 普通杂气库开启 - 使用配置中的 SCORE_GENERAL_OPEN
            score = self.general_open_score
            icon = "🗝️"
            tags = ["库门开启", "潜能释放"]
            
        return score, icon, tags

    def process_quantum_tunneling(self, branch: str, element_map: Dict) -> Tuple[float, Dict]:
        """
        V3.0 量子隧穿处理 (开库/破墓)
        :param branch: 被冲的地支 (四库之一)
        :param element_map: 五行能量映射
        :return: (bonus_score, event_dict)
        """
        vault_config = self.VAULT_MAPPING.get(branch)
        if not vault_config:
            return 0.0, {
                'card_type': 'unknown',
                'title': 'Unknown Branch',
                'desc': '',
                'score_delta': '0'
            }
        
        tomb_element = vault_config['element']
        tomb_energy = element_map.get(tomb_element, 0.0)
        
        # V3.0 逻辑：根据墓库内能量判断是开库还是破墓
        # 高能量 = 开库得财 / 低能量 = 破墓受损
        if tomb_energy > 3.0:
            # 开库 (Vault Open)
            bonus = 8.0 + (tomb_energy * 0.5)
            event = {
                'card_type': 'vault_open',
                'level': 'legendary',
                'title': f'{branch}库开启',
                'desc': f'{tomb_element.capitalize()} energy released (+{round(bonus, 1)})',
                'score_delta': f'+{round(bonus, 1)}',
                'animation_trigger': 'vault_unlock'
            }
        else:
            # 破墓 (Tomb Break)
            penalty = -5.0
            event = {
                'card_type': 'tomb_break',
                'level': 'danger',
                'title': f'{branch}墓被冲',
                'desc': f'{tomb_element.capitalize()} vault damaged',
                'score_delta': f'{penalty}',
                'animation_trigger': 'tomb_crack'
            }
            bonus = penalty
        
        return bonus, event

