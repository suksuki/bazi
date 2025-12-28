"""
[QGA V24.7] Pattern Lab 硬编码模式测试
验证硬编码干支是否正确生成，并测试格局引擎匹配
"""

import sys
sys.path.insert(0, '.')

from tests.pattern_lab import generate_synthetic_bazi, verify_pattern_purity
from core.bazi_profile import VirtualBaziProfile
from core.models.pattern_engine import get_pattern_registry

print("=" * 80)
print("QGA V24.7 Pattern Lab 硬编码模式测试")
print("=" * 80)

# 测试从儿格虚拟档案
print("\n📋 测试1: 生成从儿格虚拟档案（硬编码模式）")
print("-" * 80)

try:
    virtual_profile = generate_synthetic_bazi("CONG_ER_GE", use_hardcoded=True)
    
    print(f"✅ 虚拟档案生成成功:")
    print(f"   名称: {virtual_profile['name']}")
    print(f"   格局ID: {virtual_profile.get('_pattern_id', '未知')}")
    
    hardcoded_pillars = virtual_profile.get('_hardcoded_pillars', {})
    print(f"\n   硬编码干支:")
    print(f"     年柱: {hardcoded_pillars.get('year', '')}")
    print(f"     月柱: {hardcoded_pillars.get('month', '')}")
    print(f"     日柱: {hardcoded_pillars.get('day', '')}")
    print(f"     时柱: {hardcoded_pillars.get('hour', '')}")
    print(f"   日主: {virtual_profile.get('_day_master', '未知')}")
    
    # 测试创建VirtualBaziProfile
    print(f"\n📋 测试2: 创建VirtualBaziProfile")
    print("-" * 80)
    
    pillars_dict = {
        'year': hardcoded_pillars['year'],
        'month': hardcoded_pillars['month'],
        'day': hardcoded_pillars['day'],
        'hour': hardcoded_pillars['hour']
    }
    
    day_master = virtual_profile.get('_day_master', '')
    gender = 1 if virtual_profile.get('gender') == '男' else 0
    
    virtual_bazi = VirtualBaziProfile(
        pillars=pillars_dict,
        day_master=day_master,
        gender=gender
    )
    
    print(f"✅ VirtualBaziProfile创建成功")
    print(f"   四柱: {virtual_bazi.pillars}")
    print(f"   日主: {virtual_bazi.day_master}")
    
    # 测试格局引擎匹配
    print(f"\n📋 测试3: 测试格局引擎匹配")
    print("-" * 80)
    
    registry = get_pattern_registry()
    cong_er_ge_engine = registry.get_by_id("CONG_ER_GE")
    
    if cong_er_ge_engine:
        # 转换为chart格式
        chart = [
            (pillars_dict['year'][0], pillars_dict['year'][1]),
            (pillars_dict['month'][0], pillars_dict['month'][1]),
            (pillars_dict['day'][0], pillars_dict['day'][1]),
            (pillars_dict['hour'][0], pillars_dict['hour'][1])
        ]
        
        match_result = cong_er_ge_engine.matching_logic(
            chart=chart,
            day_master=day_master,
            luck_pillar=None,
            year_pillar=None
        )
        
        print(f"   格局引擎: {cong_er_ge_engine.pattern_name}")
        print(f"   匹配结果: {'✅ 匹配' if match_result.matched else '❌ 未匹配'}")
        if match_result.matched:
            print(f"   置信度: {match_result.confidence:.2f}")
            print(f"   SAI: {match_result.sai:.2f}")
        else:
            print(f"   ⚠️ 从儿格引擎未匹配，需要检查格局判定逻辑")
    else:
        print(f"   ⚠️ 未找到从儿格引擎")
    
    # 执行纯度校验
    print(f"\n📋 测试4: 执行格局纯度校验")
    print("-" * 80)
    
    if verify_pattern_purity(virtual_profile):
        print(f"   ✅ 格局纯度校验通过")
    else:
        print(f"   ⚠️ 格局纯度校验未通过")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("✅ 硬编码模式测试完成!")
print("=" * 80)

