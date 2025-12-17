#!/usr/bin/env python3
"""
调试 Musk 2021 年官印相生机制
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.processors.physics import GENERATION, CONTROL
import copy

# Musk 2021: 流年辛丑，大运亥，日主甲木
bazi = ["辛亥", "甲午", "甲申", "甲子"]
day_master = "甲"
gender = "男"
luck_pillar = "己亥"  # 根据描述，大运应该是亥
year_pillar = "辛丑"

# 初始化引擎
config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
engine = GraphNetworkEngine(config=config)

# 计算财富指数
result = engine.calculate_wealth_index(
    bazi=bazi,
    day_master=day_master,
    gender=gender,
    luck_pillar=luck_pillar,
    year_pillar=year_pillar
)

print("=" * 80)
print("Musk 2021 年财富预测调试")
print("=" * 80)
print(f"八字: {' '.join(bazi)}")
print(f"日主: {day_master}")
print(f"大运: {luck_pillar}")
print(f"流年: {year_pillar}")
print()
print(f"财富指数: {result['wealth_index']:.1f}")
print()
print("详情:")
for detail in result['details']:
    print(f"  - {detail}")
print()

# 手动检查官印相生逻辑
dm_element = engine.STEM_ELEMENTS.get(day_master, 'wood')
print(f"日主元素: {dm_element}")

# 确定官杀元素和印星元素
officer_element = None
for attacker, defender in CONTROL.items():
    if defender == dm_element:
        officer_element = attacker
        break

resource_element = None
for source, target in GENERATION.items():
    if target == dm_element:
        resource_element = source
        break

print(f"官杀元素: {officer_element}")
print(f"印星元素: {resource_element}")
print()

# 流年辛丑
year_stem = year_pillar[0]
year_branch = year_pillar[1]
stem_elem = engine._get_element_str(year_stem)
branch_elem = engine._get_element_str(year_branch)

print(f"流年天干: {year_stem} ({stem_elem})")
print(f"流年地支: {year_branch} ({branch_elem})")

# 检查流年天干是否是官杀
year_is_officer = (stem_elem == officer_element)
print(f"流年天干是官杀: {year_is_officer}")

# 检查流年地支是否是官杀库
vaults = {'辰', '戌', '丑', '未'}
vault_elements = {'辰': 'water', '戌': 'fire', '丑': 'metal', '未': 'wood'}

year_branch_is_officer_vault = False
if year_branch in vaults:
    vault_element = vault_elements.get(year_branch)
    print(f"流年地支库元素: {vault_element}")
    if vault_element and vault_element == officer_element:
        year_branch_is_officer_vault = True
        print(f"流年地支是官杀库: {year_branch_is_officer_vault}")
    else:
        print(f"流年地支不是官杀库 (vault_element={vault_element}, officer_element={officer_element})")

print()

# 大运己亥
luck_stem = luck_pillar[0]
luck_branch = luck_pillar[1]
luck_stem_elem = engine._get_element_str(luck_stem)
luck_branch_elem = engine._get_element_str(luck_branch)

print(f"大运天干: {luck_stem} ({luck_stem_elem})")
print(f"大运地支: {luck_branch} ({luck_branch_elem})")

# 检查大运是否是印星
luck_is_resource = (luck_stem_elem == resource_element or luck_branch_elem == resource_element)
print(f"大运是印星: {luck_is_resource}")

print()
print("=" * 80)
print("官印相生判断:")
print("=" * 80)
should_trigger = (year_is_officer or year_branch_is_officer_vault) and luck_is_resource
print(f"应该触发官印相生: {should_trigger}")
if should_trigger:
    print("✅ 逻辑正确，应该触发官印相生")
else:
    print("❌ 逻辑错误，没有触发官印相生")
    print(f"  - year_is_officer: {year_is_officer}")
    print(f"  - year_branch_is_officer_vault: {year_branch_is_officer_vault}")
    print(f"  - luck_is_resource: {luck_is_resource}")

