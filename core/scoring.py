"""
Scoring Logic
=============
V56.0 ported logic for Lucky Score calculation.
"""

def calculate_lucky_score(result: dict, useful_god: list, taboo_god: list, 
                          year_pillar: str = None, day_master: str = None) -> float:
    """
    [V56.0 改进版] 计算吉凶分（Lucky Score）
    从 verify_timeline.py 移植
    """
    dynamic_score = result.get('dynamic_score', 0.0)
    trigger_events = result.get('trigger_events', [])
    strength_score = result.get('strength_score', 50.0)
    strength_label = result.get('strength_label', 'Balanced')
    
    # 基础分数：动态评分
    base_score = dynamic_score
    
    # 检查触发事件
    penalty = 0.0
    bonus = 0.0
    
    # [V56.0 新增] 检测七杀攻身
    has_seven_kill = False
    has_officer_attack = False
    
    # 从流年天干判断七杀攻身
    if year_pillar and day_master and len(year_pillar) >= 2:
        year_stem = year_pillar[0]
        seven_kill_map = {
            '甲': '庚', '乙': '辛', '丙': '壬', '丁': '癸', '戊': '甲',
            '己': '乙', '庚': '丙', '辛': '丁', '壬': '戊', '癸': '己'
        }
        if seven_kill_map.get(day_master) == year_stem:
            has_seven_kill = True
            if strength_label == 'Weak' or strength_score < 40:
                has_officer_attack = True
                penalty += 35.0
            else:
                penalty += 20.0
    
    for event in trigger_events:
        if '冲提纲' in event:
            penalty += 40.0
        if '强根' in event or '帝旺' in event or '临官' in event:
            if '帝旺' in event:
                bonus += 20.0
            elif '临官' in event:
                bonus += 15.0
            elif '强根' in event:
                bonus += 10.0
        elif '冲开' in event and '库' in event:
            bonus += 20.0
        elif '冲' in event and '提纲' not in event:
            penalty += 5.0
    
    # 最终分数
    lucky_score = base_score - penalty + bonus
    
    # [V56.0 改进] 强根加分需要根据身强身弱调整
    has_strong_root = any('强根' in e or '帝旺' in e or '临官' in e for e in trigger_events)
    if has_strong_root and penalty < 5:
        if strength_label == 'Weak' or strength_score < 40:
            if any('帝旺' in e for e in trigger_events):
                lucky_score += 12.0
            elif any('临官' in e for e in trigger_events):
                lucky_score += 10.0
            else:
                lucky_score += 8.0
        else:
            if any('帝旺' in e for e in trigger_events):
                lucky_score += 8.0
            elif any('临官' in e for e in trigger_events):
                lucky_score += 6.0
            else:
                lucky_score += 5.0
    
    # 根据喜用神调整
    if dynamic_score > 50 and penalty < 10:
        lucky_score += 10.0
    
    # [V56.0 改进] 七杀攻身时，即使有官印相生也要扣分
    has_officer_resource = any('官印相生' in e for e in trigger_events)
    if has_officer_resource:
        if has_officer_attack:
            lucky_score += 0.0
        else:
            lucky_score += 30.0
    
    # 如果有冲提纲，大幅扣分
    has_month_clash = any('冲提纲' in e for e in trigger_events)
    if has_month_clash:
        lucky_score -= 30.0
    
    # 如果有库开，加分
    has_storehouse_open = any('冲开' in e and '库' in e for e in trigger_events)
    if has_storehouse_open:
        lucky_score += 25.0
    
    # [V56.0 新增] 如果七杀攻身且身弱，额外扣分
    if has_seven_kill and (strength_label == 'Weak' or strength_score < 40):
        has_passage = any('通关' in e for e in trigger_events)
        if not has_passage:
            lucky_score -= 15.0
        else:
            lucky_score -= 8.0
    
    return max(0.0, min(100.0, lucky_score))
