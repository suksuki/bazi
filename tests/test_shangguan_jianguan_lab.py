"""
[QGA V24.7] 伤官见官虚拟靶机完整测试
测试目标：验证"强官vs强伤"的对撞态在南方火地环境下的物理逻辑
"""

import sys
sys.path.insert(0, '.')

import logging
from tests.pattern_lab import generate_synthetic_bazi
from core.bazi_profile import VirtualBaziProfile
from core.models.pattern_engine import get_pattern_registry, PatternMatchResult
from core.models.weight_collapse import WeightCollapseAlgorithm, VectorFieldCalibration

logging.basicConfig(level=logging.ERROR)

print("=" * 80)
print("QGA V24.7 伤官见官虚拟靶机完整测试")
print("=" * 80)

# 1. 生成虚拟档案
virtual_profile = generate_synthetic_bazi("SHANG_GUAN_JIAN_GUAN", use_hardcoded=True)
hardcoded_pillars = virtual_profile.get('_hardcoded_pillars', {})
day_master = virtual_profile.get('_day_master', '')

print(f"\n✅ 虚拟档案: {virtual_profile['name']}")
print(f"   硬编码干支: {hardcoded_pillars}")
print(f"   日主: {day_master}")
print(f"   描述: {virtual_profile.get('_description', '')}")

# 2. 创建VirtualBaziProfile
pillars_dict = {
    'year': hardcoded_pillars['year'],
    'month': hardcoded_pillars['month'],
    'day': hardcoded_pillars['day'],
    'hour': hardcoded_pillars['hour']
}

virtual_bazi = VirtualBaziProfile(
    pillars=pillars_dict,
    day_master=day_master,
    gender=1
)

chart = [
    (pillars_dict['year'][0], pillars_dict['year'][1]),
    (pillars_dict['month'][0], pillars_dict['month'][1]),
    (pillars_dict['day'][0], pillars_dict['day'][1]),
    (pillars_dict['hour'][0], pillars_dict['hour'][1])
]

print(f"\n✅ 四柱: {pillars_dict['year']} {pillars_dict['month']} {pillars_dict['day']} {pillars_dict['hour']}")

# 3. 测试格局引擎匹配
registry = get_pattern_registry()
shangguan_engine = registry.get_by_id("SHANG_GUAN_JIAN_GUAN")

if not shangguan_engine:
    print("\n❌ 未找到伤官见官引擎")
    exit(1)

match_result = shangguan_engine.matching_logic(
    chart=chart,
    day_master=day_master,
    luck_pillar=None,
    year_pillar=None
)

if not match_result.matched:
    print("\n❌ 格局引擎未匹配")
    exit(1)

print(f"\n✅ 格局引擎匹配成功:")
print(f"   置信度: {match_result.confidence:.2f}")
print(f"   SAI: {match_result.sai:.2f}")
print(f"   匹配数据: {match_result.match_data}")

# 4. 测试VectorBias（南方/火地环境）
print(f"\n📋 测试VectorBias（南方/火地环境）")
print("-" * 80)

geo_context = "南方/火地"  # 火旺之地，增强伤官能级
bias = shangguan_engine.vector_bias(match_result, geo_context)
bias_dict = bias.to_dict()

print(f"   地理环境: {geo_context}")
print(f"   VectorBias:")
element_map = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}
for en_name, cn_name in element_map.items():
    val = bias_dict.get(en_name, 0.0)
    if abs(val) > 0.1:
        sign = "+" if val >= 0 else ""
        print(f"     {cn_name}: {sign}{val:.2f}")

# 验证预期（关键指标）
metal_bias = bias_dict.get('metal', 0)
fire_bias = bias_dict.get('fire', 0)
earth_bias = bias_dict.get('earth', 0)

print(f"\n   ✅ 关键指标验证:")
print(f"     应力断裂点（金元素）: {metal_bias:.2f} (预期 < -15.0，火地导致官星断裂)")
print(f"     伤官能级过载（火元素）: {fire_bias:.2f} (预期 > 0，伤官增强)")
print(f"     财星通关（土元素）: {earth_bias:.2f} (预期 > 5.0，火生土，土生金)")

if metal_bias < -15.0:
    print(f"     ✅ 应力断裂点验证通过: 金元素扣减={metal_bias:.2f}")
else:
    print(f"     ⚠️ 应力断裂点验证未通过: 金元素扣减={metal_bias:.2f} (预期 < -15.0)")

if fire_bias > 0:
    print(f"     ✅ 伤官能级过载验证通过: 火元素增强={fire_bias:.2f}")
else:
    print(f"     ⚠️ 伤官能级过载验证未通过: 火元素={fire_bias:.2f}")

if earth_bias > 5.0:
    print(f"     ✅ 财星通关验证通过: 土元素增强={earth_bias:.2f}")
else:
    print(f"     ⚠️ 财星通关验证未通过: 土元素={earth_bias:.2f}")

# 5. 计算BaseVectorBias
print(f"\n📋 计算BaseVectorBias（权重坍缩后）")
print("-" * 80)

patterns = [{
    'name': '伤官见官',
    'Strength': match_result.confidence,
    'PriorityRank': shangguan_engine.get_priority_rank(),
    'sai': match_result.sai,
    'stress': match_result.stress
}]

weighted_patterns = WeightCollapseAlgorithm.collapse_pattern_weights(patterns)
pattern_engines_dict = {'伤官见官': shangguan_engine}

base_vector_bias = VectorFieldCalibration.calculate_weighted_bias(
    patterns_with_weights=weighted_patterns,
    pattern_engines=pattern_engines_dict,
    geo_context=geo_context
)

print(f"   BaseVectorBias (geo_context={geo_context}):")
for en_name, cn_name in element_map.items():
    val = base_vector_bias.get(en_name, 0.0)
    if abs(val) > 0.1:
        sign = "+" if val >= 0 else ""
        print(f"     {cn_name}: {sign}{val:.2f}")

print("\n" + "=" * 80)
print("✅ 伤官见官虚拟靶机测试完成!")
print("=" * 80)

