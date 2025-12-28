"""
[QGA V24.7] 枭神夺食专项审计测试（修复后）
验证三项修复是否生效：
1. 水元素增强逻辑修复
2. Prompt因果链强化
3. 格局名称匹配优化
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
print("QGA V24.7 枭神夺食专项审计（修复后验证）")
print("=" * 80)

# 1. 生成虚拟档案
virtual_profile = generate_synthetic_bazi("XIAO_SHEN_DUO_SHI", use_hardcoded=True)
hardcoded_pillars = virtual_profile.get('_hardcoded_pillars', {})
day_master = virtual_profile.get('_day_master', '')

print(f"\n✅ 虚拟档案: {virtual_profile['name']}")
print(f"   硬编码干支: {hardcoded_pillars}")

# 2. 测试修复1：水元素增强逻辑
print(f"\n📋 修复1验证: 水元素增强逻辑")
print("-" * 80)

pillars_dict = {
    'year': hardcoded_pillars['year'],
    'month': hardcoded_pillars['month'],
    'day': hardcoded_pillars['day'],
    'hour': hardcoded_pillars['hour']
}

chart = [
    (pillars_dict['year'][0], pillars_dict['year'][1]),
    (pillars_dict['month'][0], pillars_dict['month'][1]),
    (pillars_dict['day'][0], pillars_dict['day'][1]),
    (pillars_dict['hour'][0], pillars_dict['hour'][1])
]

registry = get_pattern_registry()
xiaoshen_engine = registry.get_by_id("XIAO_SHEN_DUO_SHI")

if not xiaoshen_engine:
    print("❌ 未找到枭神夺食引擎")
    exit(1)

match_result = xiaoshen_engine.matching_logic(
    chart=chart,
    day_master=day_master,
    luck_pillar=None,
    year_pillar=None
)

if not match_result.matched:
    print("❌ 格局引擎未匹配")
    exit(1)

# 测试北方/近水环境
geo_context = "北方/北京"  # 北方+近水
bias = xiaoshen_engine.vector_bias(match_result, geo_context)
bias_dict = bias.to_dict()

print(f"   地理环境: {geo_context}")
print(f"   VectorBias:")
element_map = {'metal': '金', 'wood': '木', 'water': '水', 'fire': '火', 'earth': '土'}
for en_name, cn_name in element_map.items():
    val = bias_dict.get(en_name, 0.0)
    if abs(val) > 0.1:
        sign = "+" if val >= 0 else ""
        print(f"     {cn_name}: {sign}{val:.2f}")

# 验证修复
water_bias = bias_dict.get('water', 0)
fire_bias = bias_dict.get('fire', 0)

print(f"\n   ✅ 修复验证:")
if water_bias > 5.0:
    print(f"     ✅ 修复1成功: 水元素增强={water_bias:.2f} (预期 > 5.0，拦截能量注入)")
else:
    print(f"     ❌ 修复1失败: 水元素增强={water_bias:.2f} (预期 > 5.0)")

if fire_bias < -10.0:
    print(f"     ✅ 火元素扣减符合预期: {fire_bias:.2f}")
else:
    print(f"     ⚠️ 火元素扣减不足: {fire_bias:.2f}")

# 3. 测试修复2：格局名称匹配优化
print(f"\n📋 修复2验证: 格局名称匹配优化")
print("-" * 80)

# 模拟PFA检测到的格局名称（带emoji和修饰词）
test_pattern_names = [
    "枭神夺食 ✨",
    "枭神夺食能量拦截",
    "枭神夺食相位干涉",
    "枭神夺食生物能截断",
    "食神制杀能级拦截 ✨"  # 不应该匹配
]

print(f"   测试格局名称匹配:")
for test_name in test_pattern_names:
    # 使用与controller相同的匹配逻辑
    engine = registry.get_by_name(test_name)
    if not engine:
        clean_name = test_name.replace('✨', '').replace(' ', '').strip()
        for engine_candidate in registry.get_all_engines():
            candidate_name = engine_candidate.pattern_name
            if candidate_name in clean_name or clean_name in candidate_name:
                engine = engine_candidate
                break
    
    if not engine:
        key_patterns = {
            '从儿格': '从儿格',
            '枭神夺食': '枭神夺食',
            '枭神': '枭神夺食',
            '夺食': '枭神夺食',
            '伤官见官': '伤官见官',
        }
        clean_name = test_name.replace('✨', '').replace(' ', '').strip()
        for key, pattern_name_cn in key_patterns.items():
            if key in clean_name:
                engine = registry.get_by_name(pattern_name_cn)
                break
    
    if engine and engine.pattern_id == "XIAO_SHEN_DUO_SHI":
        print(f"     ✅ '{test_name}' -> 匹配成功 ({engine.pattern_name})")
    elif engine:
        print(f"     ⚠️ '{test_name}' -> 匹配到其他引擎 ({engine.pattern_name})")
    else:
        print(f"     ❌ '{test_name}' -> 未匹配")

# 4. 测试修复3：Prompt因果链（需要检查LLM实际输出，这里只验证逻辑存在）
print(f"\n📋 修复3验证: Prompt因果链强化")
print("-" * 80)

# 测试semantic_definition
semantic_def = xiaoshen_engine.semantic_definition(match_result, geo_context)
print(f"   语义定义 (geo_context={geo_context}):")
print(f"   {semantic_def}")

if "水" in semantic_def or "寒性" in semantic_def or "增强" in semantic_def or "加剧" in semantic_def:
    print(f"\n   ✅ 语义定义包含环境相关的物理过程描述")
else:
    print(f"\n   ⚠️ 语义定义可能缺少环境相关的物理过程描述")

# 5. 计算BaseVectorBias
print(f"\n📋 完整BaseVectorBias计算")
print("-" * 80)

patterns = [{
    'name': '枭神夺食',
    'Strength': match_result.confidence,
    'PriorityRank': xiaoshen_engine.get_priority_rank(),
    'sai': match_result.sai,
    'stress': match_result.stress
}]

weighted_patterns = WeightCollapseAlgorithm.collapse_pattern_weights(patterns)
pattern_engines_dict = {'枭神夺食': xiaoshen_engine}

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

# 最终验证
water_final = base_vector_bias.get('water', 0)
fire_final = base_vector_bias.get('fire', 0)

print(f"\n   ✅ 最终验证:")
if water_final > 5.0:
    print(f"     ✅ 水元素增强: {water_final:.2f} (修复生效)")
else:
    print(f"     ❌ 水元素增强不足: {water_final:.2f} (修复未生效)")

if fire_final < -10.0:
    print(f"     ✅ 火元素扣减: {fire_final:.2f} (符合预期)")
else:
    print(f"     ⚠️ 火元素扣减不足: {fire_final:.2f}")

print("\n" + "=" * 80)
print("✅ 修复验证完成!")
print("=" * 80)

