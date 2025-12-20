#!/usr/bin/env python3
"""
V55.0 Step 3: Timeline Backtester
回测马斯克的人生事件，验证大运流年算法
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

# 结果映射
RESULT_SCORE_MAP = {
    "TERRIBLE": 0,
    "BAD": 25,
    "GOOD": 75,
    "GREAT": 100
}

RESULT_LABEL_MAP = {
    "TERRIBLE": "极凶",
    "BAD": "凶",
    "GOOD": "吉",
    "GREAT": "大吉"
}

def calculate_lucky_score(result: dict, useful_god: list, taboo_god: list, 
                          year_pillar: str = None, day_master: str = None) -> float:
    """
    [V56.0 改进版] 计算吉凶分（Lucky Score）
    
    改进点：
    1. 增加七杀攻身识别（即使有通关也要扣分）
    2. 限制强根加分，避免过度加分
    3. 考虑身强身弱对强根效果的影响
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
        # 判断流年天干是否为日主的七杀
        # 七杀关系：甲见庚、乙见辛、丙见壬、丁见癸、戊见甲、己见乙、庚见丙、辛见丁、壬见戊、癸见己
        seven_kill_map = {
            '甲': '庚', '乙': '辛', '丙': '壬', '丁': '癸', '戊': '甲',
            '己': '乙', '庚': '丙', '辛': '丁', '壬': '戊', '癸': '己'
        }
        if seven_kill_map.get(day_master) == year_stem:
            has_seven_kill = True
            # 如果身弱，七杀攻身更严重
            if strength_label == 'Weak' or strength_score < 40:
                has_officer_attack = True
                penalty += 35.0  # 七杀攻身严重扣分
            else:
                penalty += 20.0  # 身强时七杀也有压力
    
    for event in trigger_events:
        # 冲提纲（月支被冲）极其严重扣分
        if '冲提纲' in event:
            penalty += 40.0  # 冲提纲极其严重
        
        # 流年为日主强根：加分（但需要限制）
        if '强根' in event or '帝旺' in event or '临官' in event:
            # [V56.0 改进] 限制强根加分，避免过度
            # 长生强根加分较少，帝旺/临官加分较多
            if '帝旺' in event:
                bonus += 20.0  # 帝旺强根（从30降到20）
            elif '临官' in event:
                bonus += 15.0  # 临官强根（从30降到15）
            elif '强根' in event:
                bonus += 10.0  # 其他强根如长生（从30降到10）
        
        # 库被冲开：能量释放，加分
        elif '冲开' in event and '库' in event:
            bonus += 20.0  # 库开能量释放
        
        # 普通冲：中等扣分
        elif '冲' in event and '提纲' not in event:
            penalty += 5.0
    
    # 最终分数
    lucky_score = base_score - penalty + bonus
    
    # [V56.0 改进] 强根加分需要根据身强身弱调整
    # 身弱得强根效果更明显，身强得强根效果有限
    has_strong_root = any('强根' in e or '帝旺' in e or '临官' in e for e in trigger_events)
    if has_strong_root and penalty < 5:
        # 身弱时强根效果更明显
        if strength_label == 'Weak' or strength_score < 40:
            if any('帝旺' in e for e in trigger_events):
                lucky_score += 12.0  # 身弱得帝旺强根（从15降到12）
            elif any('临官' in e for e in trigger_events):
                lucky_score += 10.0  # 身弱得临官强根（从12降到10）
            else:
                lucky_score += 8.0  # 身弱得其他强根（从10降到8）
        else:
            # 身强时强根效果有限
            if any('帝旺' in e for e in trigger_events):
                lucky_score += 8.0  # 身强得帝旺强根
            elif any('临官' in e for e in trigger_events):
                lucky_score += 6.0  # 身强得临官强根
            else:
                lucky_score += 5.0  # 身强得其他强根
    
    # 根据喜用神调整（简化处理）
    # 如果动态评分高且没有严重冲克，说明喜用神到位
    if dynamic_score > 50 and penalty < 10:
        lucky_score += 10.0
    
    # [V56.0 改进] 七杀攻身时，即使有官印相生也要扣分
    # 因为七杀攻身是直接攻击，官印相生只是缓解，不能完全抵消
    has_officer_resource = any('官印相生' in e for e in trigger_events)
    if has_officer_resource:
        if has_officer_attack:
            # 七杀攻身时，官印相生只能缓解，不能加分
            lucky_score += 0.0  # 不加分，因为已经被七杀攻身扣分了
        else:
            lucky_score += 30.0  # 正常情况下的官印相生加分
    
    # 2. 如果有冲提纲，大幅扣分（根基动摇）
    has_month_clash = any('冲提纲' in e for e in trigger_events)
    if has_month_clash:
        lucky_score -= 30.0  # 冲提纲大幅扣分
    
    # 3. 如果有库开，加分（能量释放）
    has_storehouse_open = any('冲开' in e and '库' in e for e in trigger_events)
    if has_storehouse_open:
        lucky_score += 25.0  # 库开大幅加分
    
    # [V56.0 新增] 如果七杀攻身且身弱，额外扣分
    if has_seven_kill and (strength_label == 'Weak' or strength_score < 40):
        # 即使有通关，七杀攻身对身弱的人来说仍然很危险
        # 检查是否有通关来缓解
        has_passage = any('通关' in e for e in trigger_events)
        if not has_passage:
            lucky_score -= 15.0  # 无通关时额外扣分
        else:
            # 有通关时扣分减少，但不能完全抵消
            lucky_score -= 8.0  # 有通关时仍要扣分
    
    return max(0.0, min(100.0, lucky_score))

def get_score_label(score: float) -> str:
    """根据分数获取标签"""
    if score >= 80:
        return "High"
    elif score >= 60:
        return "Medium"
    elif score >= 40:
        return "Low"
    else:
        return "Very Low"

def main():
    # 加载时间线数据
    timeline_path = project_root / "data" / "golden_timeline.json"
    if not timeline_path.exists():
        print(f"❌ 时间线数据文件不存在: {timeline_path}")
        print("   请先运行: python3 scripts/create_timeline_data.py")
        return
    
    with open(timeline_path, 'r', encoding='utf-8') as f:
        timeline_data = json.load(f)
    
    # 初始化引擎
    engine = GraphNetworkEngine(config=DEFAULT_FULL_ALGO_PARAMS)
    
    print("=" * 80)
    print("📊 V55.0 时间线回测：埃隆·马斯克")
    print("=" * 80)
    print()
    
    # 遍历每个案例
    for case in timeline_data:
        name = case.get('name', 'Unknown')
        bazi = case['bazi']
        day_master = case['day_master']
        useful_god = case.get('useful_god', [])
        taboo_god = case.get('taboo_god', [])
        timeline = case.get('timeline', [])
        
        print(f"👤 案例: {name}")
        print(f"   八字: {' '.join(bazi)}")
        print(f"   日主: {day_master}")
        print(f"   喜用神: {', '.join(useful_god)}")
        print(f"   忌神: {', '.join(taboo_god)}")
        print()
        print("📅 事件回测:")
        print("-" * 80)
        
        matches = 0
        total = len(timeline)
        
        for event in timeline:
            year = event['year']
            ganzhi = event['ganzhi']
            dayun = event.get('dayun', '')
            event_type = event['event_type']
            real_result = event['result']
            desc = event.get('desc', '')
            
            # 解析大运和流年
            dayun_pillar = dayun if dayun else None
            year_pillar = ganzhi if len(ganzhi) == 2 else None
            
            # 分析该年运势
            try:
                result = engine.analyze(
                    bazi=bazi,
                    day_master=day_master,
                    luck_pillar=dayun_pillar,
                    year_pillar=year_pillar
                )
                
                # 计算吉凶分（传入流年和日主信息用于七杀识别）
                lucky_score = calculate_lucky_score(result, useful_god, taboo_god, 
                                                    year_pillar=year_pillar, day_master=day_master)
                score_label = get_score_label(lucky_score)
                
                # 预期结果分数
                expected_score = RESULT_SCORE_MAP.get(real_result, 50)
                expected_label = RESULT_LABEL_MAP.get(real_result, "未知")
                
                # 判断是否匹配（允许 ±20 分的误差）
                is_match = abs(lucky_score - expected_score) <= 20
                if is_match:
                    matches += 1
                
                match_symbol = "✅" if is_match else "❌"
                
                # 打印结果
                print(f"{year}年 | 流年: {ganzhi} | 大运: {dayun}")
                print(f"  真实: {expected_label:6s} ({expected_score:3.0f}分) | "
                      f"AI: {score_label:8s} ({lucky_score:5.1f}分) | "
                      f"匹配: {match_symbol}")
                print(f"  事件: {event_type}")
                print(f"  说明: {desc}")
                
                # 显示触发事件
                trigger_events = result.get('trigger_events', [])
                if trigger_events:
                    print(f"  触发: {', '.join(trigger_events)}")
                
                print()
                
            except Exception as e:
                print(f"{year}年 | ❌ 分析失败: {e}")
                print()
        
        # 统计结果
        accuracy = (matches / total * 100) if total > 0 else 0.0
        print("-" * 80)
        print(f"📊 回测结果: {matches}/{total} 匹配 ({accuracy:.1f}%)")
        print()
    
    print("=" * 80)
    print("✅ 回测完成")
    print("=" * 80)

if __name__ == "__main__":
    main()

