#!/usr/bin/env python3
"""
调试 Musk 2021 年的财富计算
检查官印相生和大运强根是否触发
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from controllers.wealth_verification_controller import WealthVerificationController
from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
import copy
import json

def debug_musk_2021():
    """调试 Musk 2021 年的财富计算"""
    print("=" * 80)
    print("🔍 调试 Musk 2021 年财富计算")
    print("=" * 80)
    print()
    
    # 初始化控制器
    controller = WealthVerificationController()
    
    # 获取 Musk 案例
    all_cases = controller.get_all_cases()
    musk_case = next((c for c in all_cases if c.id == "TIMELINE_MUSK_WEALTH"), None)
    
    if not musk_case:
        print("❌ 未找到 Musk 案例")
        return
    
    print(f"📋 案例: {musk_case.name} ({musk_case.id})")
    print(f"   八字: {' '.join(musk_case.bazi)}")
    print(f"   日主: {musk_case.day_master}")
    print()
    
    # 找到 2021 年的事件
    event_2021 = None
    for event in musk_case.timeline:
        if event.year == 2021:
            event_2021 = event
            break
    
    if not event_2021:
        print("❌ 未找到 2021 年事件")
        return
    
    print(f"📅 2021 年事件:")
    print(f"   流年: {event_2021.ganzhi}")
    print(f"   大运: {event_2021.dayun}")
    print(f"   真实值: {event_2021.real_magnitude}")
    print()
    
    # 直接调用引擎计算
    engine = controller.engine
    
    print("🔧 调用 calculate_wealth_index...")
    print(f"   luck_pillar = {event_2021.dayun} (type: {type(event_2021.dayun)})")
    print(f"   year_pillar = {event_2021.ganzhi} (type: {type(event_2021.ganzhi)})")
    print()
    
    result = engine.calculate_wealth_index(
        bazi=musk_case.bazi,
        day_master=musk_case.day_master,
        gender=musk_case.gender,
        luck_pillar=event_2021.dayun,
        year_pillar=event_2021.ganzhi
    )
    
    print("📊 计算结果:")
    print(f"   预测值: {result.get('wealth_index', 0.0):.1f}")
    print(f"   真实值: {event_2021.real_magnitude:.1f}")
    print(f"   误差: {abs(result.get('wealth_index', 0.0) - event_2021.real_magnitude):.1f}")
    print()
    
    print("📋 详情:")
    details = result.get('details', [])
    for i, detail in enumerate(details, 1):
        print(f"   {i}. {detail}")
    print()
    
    # 检查关键机制
    has_officer_resource = any('官印相生' in d for d in details)
    has_luck_strong_root = any('大运' in d and ('长生' in d or '临官' in d or '帝旺' in d) for d in details)
    has_help = any('帮身' in d or '强根' in d for d in details)
    
    print("🔍 关键机制检查:")
    print(f"   🌟 官印相生: {'✅' if has_officer_resource else '❌'}")
    print(f"   💪 大运强根: {'✅' if has_luck_strong_root else '❌'}")
    print(f"   🤝 帮身: {'✅' if has_help else '❌'}")
    print()
    
    # 手动检查官印相生条件
    print("🔬 手动检查官印相生条件:")
    from core.processors.physics import GENERATION, CONTROL
    
    # 日主元素
    dm_element = engine.STEM_ELEMENTS.get(musk_case.day_master, 'wood')
    print(f"   日主元素: {dm_element}")
    
    # 官杀元素
    officer_element = None
    for attacker, defender in CONTROL.items():
        if defender == dm_element:
            officer_element = attacker
            break
    print(f"   官杀元素: {officer_element}")
    
    # 印星元素
    resource_element = None
    for source, target in GENERATION.items():
        if target == dm_element:
            resource_element = source
            break
    print(f"   印星元素: {resource_element}")
    
    # 流年
    year_stem = event_2021.ganzhi[0]
    year_branch = event_2021.ganzhi[1]
    year_stem_elem = engine._get_element_str(year_stem)
    year_branch_elem = engine._get_element_str(year_branch)
    print(f"   流年天干: {year_stem} ({year_stem_elem})")
    print(f"   流年地支: {year_branch} ({year_branch_elem})")
    
    # 检查流年是否是官杀
    year_is_officer = (year_stem_elem == officer_element)
    print(f"   流年天干是官杀: {year_is_officer}")
    
    # 检查流年地支是否是官杀库
    vaults = {'辰', '戌', '丑', '未'}
    vault_elements = {'辰': 'water', '戌': 'fire', '丑': 'metal', '未': 'wood'}
    year_branch_is_officer_vault = False
    if year_branch in vaults:
        vault_element = vault_elements.get(year_branch)
        print(f"   流年地支是库: {year_branch} (库中元素: {vault_element})")
        if vault_element and vault_element == officer_element:
            year_branch_is_officer_vault = True
            print(f"   流年地支是官杀库: ✅")
        else:
            print(f"   流年地支是官杀库: ❌ (库中元素 {vault_element} != 官杀元素 {officer_element})")
    else:
        print(f"   流年地支不是库: {year_branch}")
    
    # 大运
    if event_2021.dayun and len(event_2021.dayun) >= 2:
        luck_stem = event_2021.dayun[0]
        luck_branch = event_2021.dayun[1]
        luck_stem_elem = engine._get_element_str(luck_stem)
        luck_branch_elem = engine._get_element_str(luck_branch)
        print(f"   大运天干: {luck_stem} ({luck_stem_elem})")
        print(f"   大运地支: {luck_branch} ({luck_branch_elem})")
        
        # 检查大运是否是印星
        luck_is_resource = (luck_stem_elem == resource_element or luck_branch_elem == resource_element)
        print(f"   大运是印星: {luck_is_resource}")
        
        # 检查大运地支是否是强根
        from core.engine_graph import TWELVE_LIFE_STAGES
        luck_life_stage = TWELVE_LIFE_STAGES.get((musk_case.day_master, luck_branch))
        print(f"   大运地支强根: {luck_life_stage} ({'✅' if luck_life_stage in ['帝旺', '临官', '长生'] else '❌'})")
        
        # 检查官印相生条件
        print()
        print("🎯 官印相生条件检查:")
        print(f"   (year_is_officer or year_branch_is_officer_vault) = {year_is_officer or year_branch_is_officer_vault}")
        print(f"   luck_is_resource = {luck_is_resource}")
        print(f"   应该触发: {'✅' if (year_is_officer or year_branch_is_officer_vault) and luck_is_resource else '❌'}")
    else:
        print(f"   ❌ 大运无效: {event_2021.dayun}")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    debug_musk_2021()

