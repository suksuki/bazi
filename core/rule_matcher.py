"""
八字规则匹配服务 (Bazi Rule Matcher)
=====================================

基于已验证规则列表，检测八字命盘中触发的规则。
所有规则均使用 ProbValue 概率波函数和非线性激活函数。

[V13.0] 规则分类：
- A类: 基础物理规则 (月令、宫位、通根)
- B类: 几何交互规则 (天干五合、地支合冲刑)
- C类: 能量流转规则 (生克泄耗)
- D类: 墓库规则
- E类: 判定阈值规则
"""

from typing import List, Dict, Set, Any, Optional
from dataclasses import dataclass, field
from core.kernel import Kernel
from core.interactions import (
    STEM_COMBINATIONS, BRANCH_SIX_COMBINES, BRANCH_CLASHES, 
    BRANCH_PUNISHMENTS, BRANCH_HARMS
)
from core.engine_graph.constants import TWELVE_LIFE_STAGES, LIFE_STAGE_COEFFICIENTS


@dataclass
class MatchedRule:
    """匹配的规则数据结构"""
    rule_id: str
    name_cn: str
    name_en: str
    category: str  # A/B/C/D/E
    description: str
    participants: List[str] = field(default_factory=list)  # 参与的干支
    effect: str = ""  # 效果描述
    is_active: bool = True  # 是否已激活


# 已验证规则定义
VERIFIED_RULES = {
    # A类: 基础物理规则
    "A1": {"name_cn": "月令统管", "name_en": "Month Commander", "category": "A",
           "desc": "当令者能量显著提升", "always_active": True},
    "A2": {"name_cn": "宫位引力", "name_en": "Pillar Gravity", "category": "A",
           "desc": "日月柱权重高于年时柱", "always_active": True},
    "A3": {"name_cn": "藏干壳核", "name_en": "Hidden Stem Shell", "category": "A",
           "desc": "地支藏干按主60/中30/余10分配", "always_active": True},
    "A4": {"name_cn": "十二长生", "name_en": "Twelve Life Stages", "category": "A",
           "desc": "天干在地支的生旺死绝状态", "always_active": True},
    "A5": {"name_cn": "通根扎根", "name_en": "Rooting", "category": "A",
           "desc": "天干在地支藏干中有根", "trigger": "rooting"},
    "A6": {"name_cn": "自坐强根", "name_en": "Self-Sitting Root", "category": "A",
           "desc": "同柱干支相生加成", "trigger": "same_pillar"},
    
    # B类: 几何交互规则
    "B1": {"name_cn": "天干五合", "name_en": "Stem Five Combinations", "category": "B",
           "desc": "甲己/乙庚/丙辛/丁壬/戊癸合化", "trigger": "stem_combine"},
    "B2": {"name_cn": "六冲", "name_en": "Six Clashes", "category": "B",
           "desc": "子午/丑未/寅申/卯酉/辰戌/巳亥冲", "trigger": "branch_clash"},
    "B3": {"name_cn": "恃势之刑", "name_en": "Bullying Punishment", "category": "B",
           "desc": "寅巳申三刑，能量损耗", "trigger": "punishment_yinsishen"},
    "B4": {"name_cn": "土刑激旺", "name_en": "Earth Punishment Boost", "category": "B",
           "desc": "丑未戌三刑，土能量激旺", "trigger": "punishment_earth"},
    "B5": {"name_cn": "六合", "name_en": "Six Combinations", "category": "B",
           "desc": "子丑/寅亥/卯戌/辰酉/巳申/午未合", "trigger": "branch_combine"},
    "B6": {"name_cn": "三合局", "name_en": "Three Harmony", "category": "B",
           "desc": "申子辰水/亥卯未木/寅午戌火/巳酉丑金", "trigger": "three_harmony"},
    "B7": {"name_cn": "半三合", "name_en": "Half Harmony", "category": "B",
           "desc": "三合中的两支拱向第三支", "trigger": "half_harmony"},
    "B8": {"name_cn": "三会局", "name_en": "Three Meetings", "category": "B",
           "desc": "寅卯辰木/巳午未火/申酉戌金/亥子丑水", "trigger": "three_meeting"},
    
    # C类: 能量流转规则
    "C1": {"name_cn": "生的效率", "name_en": "Generation Efficiency", "category": "C",
           "desc": "五行相生，传递损耗30%", "always_active": True},
    "C2": {"name_cn": "克的破坏", "name_en": "Control Impact", "category": "C",
           "desc": "五行相克，被克方能量减半", "trigger": "control"},
    "C3": {"name_cn": "空间衰减", "name_en": "Spatial Decay", "category": "C",
           "desc": "距离越远作用越弱", "always_active": True},
    "C4": {"name_cn": "系统阻尼", "name_en": "System Damping", "category": "C",
           "desc": "能量传递自然损耗10%", "always_active": True},
    
    # D类: 墓库规则
    "D1": {"name_cn": "墓库判定", "name_en": "Vault Detection", "category": "D",
           "desc": "辰戌丑未为四库", "trigger": "vault"},
    "D2": {"name_cn": "冲开库", "name_en": "Clash Opens Vault", "category": "D",
           "desc": "冲可开库释放能量", "trigger": "vault_open"},
    "D3": {"name_cn": "闭库折损", "name_en": "Sealed Vault Damping", "category": "D",
           "desc": "未开库时能量封存", "trigger": "vault_sealed"},
    
    # E类: 判定阈值规则
    "E1": {"name_cn": "旺衰能量中心", "name_en": "Strength Energy Center", "category": "E",
           "desc": "使用softplus平滑阈值", "always_active": True},
    "E2": {"name_cn": "强弱分数阈值", "name_en": "Strong/Weak Threshold", "category": "E",
           "desc": "使用sigmoid非线性判定", "always_active": True},
    "E3": {"name_cn": "从格阈值", "name_en": "Follower Threshold", "category": "E",
           "desc": "极弱时触发从格判定", "trigger": "follower"},
}


class RuleMatcher:
    """
    规则匹配器
    
    检测八字命盘中触发的规则，返回匹配列表。
    """
    
    # 三合局定义
    THREE_HARMONY = {
        frozenset({'申', '子', '辰'}): 'Water',
        frozenset({'亥', '卯', '未'}): 'Wood',
        frozenset({'寅', '午', '戌'}): 'Fire',
        frozenset({'巳', '酉', '丑'}): 'Metal',
    }
    
    # 三会局定义
    THREE_MEETING = {
        frozenset({'寅', '卯', '辰'}): 'Wood',
        frozenset({'巳', '午', '未'}): 'Fire',
        frozenset({'申', '酉', '戌'}): 'Metal',
        frozenset({'亥', '子', '丑'}): 'Water',
    }
    
    # 四墓库
    VAULT_BRANCHES = {'辰', '戌', '丑', '未'}
    VAULT_ELEMENTS = {'辰': 'Water', '戌': 'Fire', '丑': 'Metal', '未': 'Wood'}
    
    def __init__(self):
        self.rules = VERIFIED_RULES
    
    def match(self, bazi: List[str], day_master: str, 
              engine_result: Optional[Dict] = None) -> List[MatchedRule]:
        """
        匹配八字中触发的规则
        
        Args:
            bazi: 八字列表 ["甲子", "乙丑", "丙寅", "丁卯"]
            day_master: 日主天干
            engine_result: GraphNetworkEngine 计算结果（可选，用于能量判定）
            
        Returns:
            匹配的规则列表
        """
        matched = []
        
        # 解析干支
        stems = []
        branches = []
        for pillar in bazi:
            if len(pillar) >= 2:
                stems.append(pillar[0])
                branches.append(pillar[1])
        
        branch_set = set(branches)
        stem_set = set(stems)
        
        # === A类: 基础物理规则 (总是激活) ===
        for rule_id in ['A1', 'A2', 'A3', 'A4']:
            rule = self.rules[rule_id]
            matched.append(MatchedRule(
                rule_id=rule_id,
                name_cn=rule['name_cn'],
                name_en=rule['name_en'],
                category=rule['category'],
                description=rule['desc'],
                effect="始终应用"
            ))
        
        # A5: 通根检测
        rooting_info = self._detect_rooting(stems, branches, day_master)
        if rooting_info:
            matched.append(MatchedRule(
                rule_id="A5",
                name_cn=self.rules['A5']['name_cn'],
                name_en=self.rules['A5']['name_en'],
                category="A",
                description=self.rules['A5']['desc'],
                participants=rooting_info['participants'],
                effect=f"通根于: {', '.join(rooting_info['roots'])}"
            ))
        
        # A6: 自坐检测
        same_pillar = self._detect_same_pillar_bonus(bazi)
        if same_pillar:
            matched.append(MatchedRule(
                rule_id="A6",
                name_cn=self.rules['A6']['name_cn'],
                name_en=self.rules['A6']['name_en'],
                category="A",
                description=self.rules['A6']['desc'],
                participants=same_pillar,
                effect="同柱相生加成"
            ))
        
        # === B类: 几何交互规则 ===
        
        # B1: 天干五合
        stem_combines = self._detect_stem_combinations(stems)
        for combo in stem_combines:
            matched.append(MatchedRule(
                rule_id="B1",
                name_cn=self.rules['B1']['name_cn'],
                name_en=self.rules['B1']['name_en'],
                category="B",
                description=self.rules['B1']['desc'],
                participants=list(combo['stems']),
                effect=f"合化{combo['element']}"
            ))
        
        # B2: 六冲
        clashes = self._detect_branch_clashes(branches)
        for clash in clashes:
            matched.append(MatchedRule(
                rule_id="B2",
                name_cn=self.rules['B2']['name_cn'],
                name_en=self.rules['B2']['name_en'],
                category="B",
                description=self.rules['B2']['desc'],
                participants=list(clash),
                effect="双方能量×0.4"
            ))
        
        # B3/B4: 刑
        punishments = self._detect_punishments(branches)
        for pun in punishments:
            if pun['type'] == 'earth':
                matched.append(MatchedRule(
                    rule_id="B4",
                    name_cn=self.rules['B4']['name_cn'],
                    name_en=self.rules['B4']['name_en'],
                    category="B",
                    description=self.rules['B4']['desc'],
                    participants=pun['branches'],
                    effect="土能量×1.3激旺"
                ))
            else:
                matched.append(MatchedRule(
                    rule_id="B3",
                    name_cn=self.rules['B3']['name_cn'],
                    name_en=self.rules['B3']['name_en'],
                    category="B",
                    description=self.rules['B3']['desc'],
                    participants=pun['branches'],
                    effect="能量损耗"
                ))
        
        # B5: 六合
        six_combines = self._detect_six_combinations(branches)
        for combo in six_combines:
            matched.append(MatchedRule(
                rule_id="B5",
                name_cn=self.rules['B5']['name_cn'],
                name_en=self.rules['B5']['name_en'],
                category="B",
                description=self.rules['B5']['desc'],
                participants=list(combo),
                effect="能量×1.15"
            ))
        
        # B6: 三合局
        three_harmony = self._detect_three_harmony(branch_set)
        if three_harmony:
            matched.append(MatchedRule(
                rule_id="B6",
                name_cn=self.rules['B6']['name_cn'],
                name_en=self.rules['B6']['name_en'],
                category="B",
                description=self.rules['B6']['desc'],
                participants=list(three_harmony['branches']),
                effect=f"化{three_harmony['element']}局，能量×2.5"
            ))
        
        # B7: 半三合
        half_harmony = self._detect_half_harmony(branch_set)
        for hh in half_harmony:
            matched.append(MatchedRule(
                rule_id="B7",
                name_cn=self.rules['B7']['name_cn'],
                name_en=self.rules['B7']['name_en'],
                category="B",
                description=self.rules['B7']['desc'],
                participants=list(hh['branches']),
                effect=f"拱{hh['element']}气，能量×1.5"
            ))
        
        # B8: 三会局
        three_meeting = self._detect_three_meeting(branch_set)
        if three_meeting:
            matched.append(MatchedRule(
                rule_id="B8",
                name_cn=self.rules['B8']['name_cn'],
                name_en=self.rules['B8']['name_en'],
                category="B",
                description=self.rules['B8']['desc'],
                participants=list(three_meeting['branches']),
                effect=f"会{three_meeting['element']}局，能量×3.0"
            ))
        
        # === C类: 能量流转规则 (总是激活) ===
        for rule_id in ['C1', 'C3', 'C4']:
            rule = self.rules[rule_id]
            matched.append(MatchedRule(
                rule_id=rule_id,
                name_cn=rule['name_cn'],
                name_en=rule['name_en'],
                category=rule['category'],
                description=rule['desc'],
                effect="始终应用"
            ))
        
        # C2: 克制检测
        controls = self._detect_control_relations(stems, day_master)
        if controls:
            matched.append(MatchedRule(
                rule_id="C2",
                name_cn=self.rules['C2']['name_cn'],
                name_en=self.rules['C2']['name_en'],
                category="C",
                description=self.rules['C2']['desc'],
                participants=controls['participants'],
                effect=controls['effect']
            ))
        
        # === D类: 墓库规则 ===
        vaults = self._detect_vaults(branch_set, clashes)
        for vault in vaults:
            if vault['opened']:
                matched.append(MatchedRule(
                    rule_id="D2",
                    name_cn=self.rules['D2']['name_cn'],
                    name_en=self.rules['D2']['name_en'],
                    category="D",
                    description=self.rules['D2']['desc'],
                    participants=[vault['branch']],
                    effect=f"{vault['element']}库已开，能量×1.8"
                ))
            else:
                matched.append(MatchedRule(
                    rule_id="D3",
                    name_cn=self.rules['D3']['name_cn'],
                    name_en=self.rules['D3']['name_en'],
                    category="D",
                    description=self.rules['D3']['desc'],
                    participants=[vault['branch']],
                    effect=f"{vault['element']}库封存，能量×0.4"
                ))
        
        # === E类: 判定阈值规则 (总是激活) ===
        for rule_id in ['E1', 'E2']:
            rule = self.rules[rule_id]
            matched.append(MatchedRule(
                rule_id=rule_id,
                name_cn=rule['name_cn'],
                name_en=rule['name_en'],
                category=rule['category'],
                description=rule['desc'],
                effect="始终应用"
            ))
        
        return matched
    
    def _detect_rooting(self, stems: List[str], branches: List[str], 
                        day_master: str) -> Optional[Dict]:
        """检测通根"""
        dm_idx = stems.index(day_master) if day_master in stems else -1
        if dm_idx == -1:
            return None
        
        dm_props = Kernel.STEM_PROPERTIES.get(day_master, {})
        dm_element = dm_props.get('element')
        if not dm_element:
            return None
        
        roots = []
        for b in branches:
            hidden = Kernel.HIDDEN_STEMS.get(b, {})
            for h_stem, ratio in hidden.items():
                h_elem = Kernel.STEM_PROPERTIES.get(h_stem, {}).get('element')
                if h_elem == dm_element and ratio >= 0.3:
                    roots.append(b)
                    break
        
        if roots:
            return {
                'participants': [day_master] + roots,
                'roots': roots
            }
        return None
    
    def _detect_same_pillar_bonus(self, bazi: List[str]) -> List[str]:
        """检测自坐强根"""
        result = []
        for pillar in bazi:
            if len(pillar) >= 2:
                stem, branch = pillar[0], pillar[1]
                # 检查天干是否通根于座下
                hidden = Kernel.HIDDEN_STEMS.get(branch, {})
                stem_elem = Kernel.STEM_PROPERTIES.get(stem, {}).get('element')
                for h_stem in hidden:
                    if Kernel.STEM_PROPERTIES.get(h_stem, {}).get('element') == stem_elem:
                        result.append(pillar)
                        break
        return result
    
    def _detect_stem_combinations(self, stems: List[str]) -> List[Dict]:
        """检测天干五合"""
        combos = []
        stem_set = set(stems)
        
        combine_map = {
            frozenset({'甲', '己'}): 'Earth',
            frozenset({'乙', '庚'}): 'Metal',
            frozenset({'丙', '辛'}): 'Water',
            frozenset({'丁', '壬'}): 'Wood',
            frozenset({'戊', '癸'}): 'Fire',
        }
        
        for pair, element in combine_map.items():
            if pair.issubset(stem_set):
                combos.append({'stems': pair, 'element': element})
        
        return combos
    
    def _detect_branch_clashes(self, branches: List[str]) -> List[Set[str]]:
        """检测六冲"""
        clashes = []
        branch_list = list(branches)
        
        for i in range(len(branch_list)):
            for j in range(i + 1, len(branch_list)):
                b1, b2 = branch_list[i], branch_list[j]
                if BRANCH_CLASHES.get(b1) == b2:
                    clashes.append({b1, b2})
        
        return clashes
    
    def _detect_punishments(self, branches: List[str]) -> List[Dict]:
        """检测刑"""
        punishments = []
        branch_set = set(branches)
        
        # 丑未戌三刑（土刑激旺）
        earth_punishment = {'丑', '未', '戌'}
        earth_found = branch_set & earth_punishment
        if len(earth_found) >= 2:
            punishments.append({
                'type': 'earth',
                'branches': list(earth_found)
            })
        
        # 寅巳申三刑（恃势之刑）
        power_punishment = {'寅', '巳', '申'}
        power_found = branch_set & power_punishment
        if len(power_found) >= 2:
            punishments.append({
                'type': 'power',
                'branches': list(power_found)
            })
        
        return punishments
    
    def _detect_six_combinations(self, branches: List[str]) -> List[Set[str]]:
        """检测六合"""
        combos = []
        branch_list = list(branches)
        
        for i in range(len(branch_list)):
            for j in range(i + 1, len(branch_list)):
                b1, b2 = branch_list[i], branch_list[j]
                if BRANCH_SIX_COMBINES.get(b1) == b2:
                    combos.append({b1, b2})
        
        return combos
    
    def _detect_three_harmony(self, branch_set: Set[str]) -> Optional[Dict]:
        """检测三合局"""
        for trio, element in self.THREE_HARMONY.items():
            if trio.issubset(branch_set):
                return {'branches': trio, 'element': element}
        return None
    
    def _detect_half_harmony(self, branch_set: Set[str]) -> List[Dict]:
        """检测半三合"""
        results = []
        for trio, element in self.THREE_HARMONY.items():
            common = branch_set & trio
            if len(common) == 2:
                results.append({'branches': common, 'element': element})
        return results
    
    def _detect_three_meeting(self, branch_set: Set[str]) -> Optional[Dict]:
        """检测三会局"""
        for trio, element in self.THREE_MEETING.items():
            if trio.issubset(branch_set):
                return {'branches': trio, 'element': element}
        return None
    
    def _detect_control_relations(self, stems: List[str], 
                                   day_master: str) -> Optional[Dict]:
        """检测克制关系"""
        dm_elem = Kernel.STEM_PROPERTIES.get(day_master, {}).get('element')
        if not dm_elem:
            return None
        
        # 五行相克
        control_map = {
            'Wood': 'Earth', 'Earth': 'Water', 'Water': 'Fire',
            'Fire': 'Metal', 'Metal': 'Wood'
        }
        
        controlled_elem = control_map.get(dm_elem)
        controller_elem = None
        for k, v in control_map.items():
            if v == dm_elem:
                controller_elem = k
                break
        
        controlled_by = []
        controlling = []
        
        for s in stems:
            if s == day_master:
                continue
            s_elem = Kernel.STEM_PROPERTIES.get(s, {}).get('element')
            if s_elem == controller_elem:
                controlled_by.append(s)
            elif s_elem == controlled_elem:
                controlling.append(s)
        
        if controlled_by or controlling:
            effects = []
            if controlled_by:
                effects.append(f"被{','.join(controlled_by)}克")
            if controlling:
                effects.append(f"克{','.join(controlling)}")
            
            return {
                'participants': [day_master] + controlled_by + controlling,
                'effect': '，'.join(effects)
            }
        return None
    
    def _detect_vaults(self, branch_set: Set[str], 
                       clashes: List[Set[str]]) -> List[Dict]:
        """检测墓库"""
        vaults = []
        clash_branches = set()
        for clash in clashes:
            clash_branches.update(clash)
        
        for v in self.VAULT_BRANCHES & branch_set:
            opened = v in clash_branches
            vaults.append({
                'branch': v,
                'element': self.VAULT_ELEMENTS[v],
                'opened': opened
            })
        
        return vaults
    
    def get_rule_summary(self, matched: List[MatchedRule]) -> Dict[str, Any]:
        """
        获取规则匹配摘要
        
        Returns:
            {
                'total': 总规则数,
                'by_category': {'A': 3, 'B': 5, ...},
                'active_effects': [效果列表]
            }
        """
        by_cat = {}
        effects = []
        
        for rule in matched:
            cat = rule.category
            by_cat[cat] = by_cat.get(cat, 0) + 1
            if rule.effect and rule.effect != "始终应用":
                effects.append(f"{rule.name_cn}: {rule.effect}")
        
        return {
            'total': len(matched),
            'by_category': by_cat,
            'active_effects': effects
        }
