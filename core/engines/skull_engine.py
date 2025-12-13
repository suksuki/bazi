"""
core/engines/skull_engine.py
----------------------------
[V6.0 Sub-Engine] 骷髅协议引擎 (Skull Protocol)
负责处理：三刑检测、刑冲害组合、极凶判定
基于 V5.3 Skull Protocol 文档实现
"""
from typing import Dict, List, Tuple, Optional, Set


class SkullEngine:
    """
    [V6.0 Sub-Engine] 骷髅协议引擎
    专门处理三刑检测与极端负面事件
    """
    
    # 三刑组合定义 (丑未戌三刑 / 寅巳申三刑 / 子卯刑)
    THREE_PUNISHMENTS = {
        'chou_wei_xu': {'丑', '未', '戌'},  # 恃势之刑 (最凶)
        'yin_si_shen': {'寅', '巳', '申'},  # 无恩之刑
        'zi_mao': {'子', '卯'},              # 无礼之刑 (二刑)
    }
    
    # 自刑定义
    SELF_PUNISHMENTS = {'辰', '午', '酉', '亥'}
    
    # 六冲定义
    CLASHES = {
        '子': '午', '午': '子',
        '丑': '未', '未': '丑',
        '寅': '申', '申': '寅',
        '卯': '酉', '酉': '卯',
        '辰': '戌', '戌': '辰',
        '巳': '亥', '亥': '巳',
    }
    
    # 六害定义
    HARMS = {
        '子': '未', '未': '子',
        '丑': '午', '午': '丑',
        '寅': '巳', '巳': '寅',
        '卯': '辰', '辰': '卯',
        '申': '亥', '亥': '申',
        '酉': '戌', '戌': '酉',
    }

    def __init__(self):
        pass

    def detect_three_punishments(self, chart: Dict, year_branch: str) -> bool:
        """
        兼容 QuantumEngine 的调用接口
        检测丑未戌三刑是否齐见
        :param chart: 包含 year_pillar, month_pillar, day_pillar, hour_pillar 的字典
        :param year_branch: 流年地支
        :return: 是否触发三刑
        """
        # 提取四柱地支
        branches = []
        for key in ['year_pillar', 'month_pillar', 'day_pillar', 'hour_pillar']:
            pillar = chart.get(key, '')
            if len(pillar) > 1:
                branches.append(pillar[1])  # 地支是第二个字符
        
        # 加入流年地支
        if year_branch:
            branches.append(year_branch)
        
        # 检测丑未戌三刑
        branch_set = set(branches)
        return self.THREE_PUNISHMENTS['chou_wei_xu'].issubset(branch_set)

    def detect_three_punishment(self, branches: List[str]) -> Tuple[bool, str, float]:
        """
        检测三刑是否齐见
        :param branches: 所有地支列表 (四柱 + 大运 + 流年)
        :return: (is_triggered, punishment_type, penalty_score)
        """
        branch_set = set(branches)
        
        # 检测 丑未戌三刑 (最凶，骷髅协议核心)
        if self.THREE_PUNISHMENTS['chou_wei_xu'].issubset(branch_set):
            return True, "丑未戌三刑", -50.0
        
        # 检测 寅巳申三刑
        if self.THREE_PUNISHMENTS['yin_si_shen'].issubset(branch_set):
            return True, "寅巳申三刑", -40.0
        
        # 检测 子卯刑 (二刑，较轻)
        if self.THREE_PUNISHMENTS['zi_mao'].issubset(branch_set):
            return True, "子卯刑", -25.0
        
        return False, "", 0.0

    def detect_self_punishment(self, branches: List[str]) -> Tuple[bool, List[str], float]:
        """
        检测自刑
        :param branches: 所有地支列表
        :return: (is_triggered, self_punish_branches, penalty_score)
        """
        found = []
        for b in branches:
            if b in self.SELF_PUNISHMENTS:
                # 需要出现两次才算自刑触发
                if branches.count(b) >= 2:
                    found.append(b)
        
        if found:
            return True, found, -15.0 * len(found)
        return False, [], 0.0

    def detect_clash(self, branches: List[str]) -> List[Tuple[str, str]]:
        """
        检测六冲
        :param branches: 所有地支列表
        :return: 冲突对列表
        """
        clashes_found = []
        seen = set()
        
        for b in branches:
            clash_pair = self.CLASHES.get(b)
            if clash_pair and clash_pair in branches:
                pair = tuple(sorted([b, clash_pair]))
                if pair not in seen:
                    seen.add(pair)
                    clashes_found.append((b, clash_pair))
        
        return clashes_found

    def detect_harm(self, branches: List[str]) -> List[Tuple[str, str]]:
        """
        检测六害
        :param branches: 所有地支列表
        :return: 害的组合列表
        """
        harms_found = []
        seen = set()
        
        for b in branches:
            harm_pair = self.HARMS.get(b)
            if harm_pair and harm_pair in branches:
                pair = tuple(sorted([b, harm_pair]))
                if pair not in seen:
                    seen.add(pair)
                    harms_found.append((b, harm_pair))
        
        return harms_found

    def evaluate(self, branches: List[str]) -> Dict:
        """
        综合评估刑冲害
        :param branches: 所有地支列表 (四柱 + 大运 + 流年)
        :return: 评估结果字典
        """
        result = {
            'score': 0.0,
            'icon': None,
            'tags': [],
            'details': {}
        }
        
        # 1. 三刑检测 (最高优先级)
        is_3p, p_type, p_score = self.detect_three_punishment(branches)
        if is_3p:
            result['score'] += p_score
            result['icon'] = '💀'
            result['tags'].append('三刑齐见')
            result['tags'].append(p_type)
            result['details']['three_punishment'] = p_type
        
        # 2. 自刑检测
        is_sp, sp_branches, sp_score = self.detect_self_punishment(branches)
        if is_sp:
            result['score'] += sp_score
            result['tags'].append('自刑')
            result['details']['self_punishment'] = sp_branches
        
        # 3. 六冲检测
        clashes = self.detect_clash(branches)
        if clashes:
            # 每组冲 -8 分
            clash_penalty = -8.0 * len(clashes)
            result['score'] += clash_penalty
            result['tags'].append(f'六冲x{len(clashes)}')
            result['details']['clashes'] = clashes
        
        # 4. 六害检测
        harms = self.detect_harm(branches)
        if harms:
            # 每组害 -5 分
            harm_penalty = -5.0 * len(harms)
            result['score'] += harm_penalty
            result['tags'].append(f'六害x{len(harms)}')
            result['details']['harms'] = harms
        
        # 5. 设置图标 (如果没有三刑但有其他负面)
        if not result['icon'] and result['score'] < -20:
            result['icon'] = '⚠️'
        elif not result['icon'] and result['score'] < 0:
            result['icon'] = '🔻'
        
        return result
