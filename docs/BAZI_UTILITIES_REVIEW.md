# 八字工具类代码审查报告

## 📋 概述

本文档整理项目中所有八字相关的工具类和函数，包括：
- 八字排盘工具
- 反推出生年月日时工具
- 大运计算工具
- 流年计算工具

---

## 🔧 核心工具类

### 1. BaziCalculator (`core/calculator.py`)

**功能**: 从出生日期计算八字排盘

**主要方法**:
- `__init__(year, month, day, hour, minute=0, longitude=None, tz_offset=8)`
  - 支持真太阳时修正（longitude 参数）
  - 自动计算时差修正和均时差（EOT）
  
- `get_chart()` → Dict
  - 返回完整的八字排盘信息
  - 包含年、月、日、时四柱的干支和藏干
  - 包含真太阳时修正信息
  
- `get_luck_cycles(gender_idx)` → List[Dict]
  - 计算大运周期
  - `gender_idx`: 1=男, 0=女
  - 返回大运列表，包含起始年份、结束年份、起始年龄、干支

**使用示例**:
```python
from core.calculator import BaziCalculator
from datetime import datetime

# 创建计算器（支持真太阳时）
calc = BaziCalculator(1990, 5, 15, 12, 0, longitude=116.4, tz_offset=8)

# 获取八字排盘
chart = calc.get_chart()
print(chart['year']['stem'])  # 年干
print(chart['month']['branch'])  # 月支

# 获取大运周期
luck_cycles = calc.get_luck_cycles(gender_idx=1)  # 男性
for cycle in luck_cycles:
    print(f"{cycle['start_year']}-{cycle['end_year']}: {cycle['gan_zhi']}")
```

---

### 2. BaziProfile (`core/bazi_profile.py`)

**功能**: 八字档案对象，封装排盘和大运计算逻辑

**主要属性**:
- `pillars`: Dict[str, str] - 四柱干支
- `day_master`: str - 日主天干
- `birth_date`: datetime - 出生日期

**主要方法**:
- `get_luck_pillar_at(year: int)` → str
  - O(1) 复杂度查询指定年份的大运
  - 使用预构建的时间线查找表
  
- `get_year_pillar(year: int)` → str
  - 获取指定流年的干支
  
- `_build_luck_timeline()`
  - 构建未来 100 年的大运查找表
  - 解决动态计算开销问题

**使用示例**:
```python
from core.bazi_profile import BaziProfile
from datetime import datetime

# 创建八字档案
birth_date = datetime(1990, 5, 15, 12, 0)
profile = BaziProfile(birth_date, gender=1)  # 1=男

# 获取四柱
pillars = profile.pillars
print(f"年柱: {pillars['year']}")
print(f"日主: {profile.day_master}")

# 查询大运
luck_2024 = profile.get_luck_pillar_at(2024)
print(f"2024年大运: {luck_2024}")

# 查询流年
year_2024 = profile.get_year_pillar(2024)
print(f"2024年流年: {year_2024}")
```

---

### 3. VirtualBaziProfile (`core/bazi_profile.py`)

**功能**: 虚拟八字档案，从四柱反推出生日期

**主要功能**:
- 从八字四柱反推出生年月日时
- 自动创建真正的 BaziProfile 用于大运计算
- 适配旧测试用例（Legacy Cases）

**主要方法**:
- `__init__(pillars: Dict[str, str], static_luck: str, day_master: str, gender: int)`
  - `pillars`: 四柱字典 `{'year': '甲子', 'month': '丙寅', ...}`
  - 自动反推出生日期并创建 BaziProfile
  
- `_create_real_profile()` → Optional[BaziProfile]
  - 从四柱反推出生日期
  - 年柱反推年份（1920-2020 范围）
  - 月柱反推月份（地支对应月份）
  - 时柱反推时辰（地支对应小时）

**反推逻辑**:
```python
# 年柱反推年份（60甲子循环）
for base_year in range(1920, 2020):
    if (base_year - 4) % 10 == gan_idx and (base_year - 4) % 12 == zhi_idx:
        birth_year = base_year
        break

# 月柱反推月份
ZHI_TO_MONTH = {
    '寅': 1, '卯': 2, '辰': 3, '巳': 4, '午': 5, '未': 6,
    '申': 7, '酉': 8, '戌': 9, '亥': 10, '子': 11, '丑': 12
}

# 时柱反推时辰
ZHI_TO_HOUR = {
    '子': 0, '丑': 2, '寅': 4, '卯': 6, '辰': 8, '巳': 10,
    '午': 12, '未': 14, '申': 16, '酉': 18, '戌': 20, '亥': 22
}
```

**使用示例**:
```python
from core.bazi_profile import VirtualBaziProfile

# 从四柱创建虚拟档案
pillars = {
    'year': '甲子',
    'month': '丙寅',
    'day': '庚辰',
    'hour': '戊午'
}
profile = VirtualBaziProfile(pillars, day_master='庚', gender=1)

# 获取反推的出生日期
birth_date = profile.birth_date
print(f"反推的出生日期: {birth_date}")

# 使用反推的profile计算大运
luck_2024 = profile.get_luck_pillar_at(2024)
print(f"2024年大运: {luck_2024}")
```

---

### 4. LuckEngine (`core/engines/luck_engine.py`)

**功能**: 大运计算引擎

**主要方法**:
- `calculate_luck_start_age(birth_month, birth_day, gender)`
  - 计算大运起始年龄
  
- `get_luck_pillar_at_age(luck_cycles, age)`
  - 根据年龄查询大运
  
- `get_luck_pillar_at_year(luck_cycles, year)`
  - 根据年份查询大运
  
- `is_handover_year(luck_cycles, year)`
  - 判断是否为换运年份
  
- `get_luck_timeline(luck_cycles, start_year, duration)`
  - 获取大运时间线
  
- `get_dynamic_luck_pillar(luck_cycles, year)`
  - 动态获取指定年份的大运

---

## 🔄 反推工具函数

### 1. `reverse_lookup_bazi()` (`ui/pages/zeitgeist.py`)

**功能**: 暴力搜索反推八字对应的出生日期

**参数**:
- `target_bazi`: List[str] - 目标八字 `[年柱, 月柱, 日柱, 时柱]`
- `start_year`: int - 搜索起始年份（默认 1950）
- `end_year`: int - 搜索结束年份（默认 2030）

**返回**: `str` - 找到的日期时间字符串，格式 `"YYYY-MM-DD HH:00"`

**算法**:
1. 遍历年份范围
2. 检查年中点（6月15日）的年柱是否匹配
3. 如果匹配，扫描该年（考虑立春边界）
4. 精确匹配月柱、日柱、时柱

**使用示例**:
```python
from ui.pages.zeitgeist import reverse_lookup_bazi

target_bazi = ['甲子', '丙寅', '庚辰', '戊午']
birth_date = reverse_lookup_bazi(target_bazi, start_year=1950, end_year=2030)
print(f"找到的出生日期: {birth_date}")
```

---

### 2. `_reverse_calculate_date()` (`ui/modules/profile_section.py`)

**功能**: 简化版反推出生日期（近似值）

**参数**:
- `year_pz`: str - 年柱
- `month_pz`: str - 月柱
- `day_pz`: str - 日柱
- `hour_pz`: str - 时柱

**返回**: `Dict` - `{'date': datetime, 'hour': int}`

**特点**:
- 使用 60 甲子循环查找年份（1924-2043）
- 使用月中（15日）作为近似日期
- 使用地支对应月份和时辰

**使用示例**:
```python
from ui.modules.profile_section import _reverse_calculate_date

result = _reverse_calculate_date('甲子', '丙寅', '庚辰', '戊午')
print(f"近似出生日期: {result['date']}, 时辰: {result['hour']}")
```

---

### 3. `calculate_dayun_from_bazi()` (`scripts/clean_and_reimport_cases.py`)

**功能**: 从八字反推出生日期并计算大运

**参数**:
- `bazi`: List[str] - 八字列表 `['年柱', '月柱', '日柱', '时柱']`
- `gender`: int - 性别（1=男, 0=女）
- `year`: int - 查询年份

**返回**: `str` - 大运干支

**实现**:
```python
def calculate_dayun_from_bazi(bazi, gender, year):
    # 使用 VirtualBaziProfile 反推出生日期
    pillars = {
        'year': bazi[0],
        'month': bazi[1],
        'day': bazi[2],
        'hour': bazi[3]
    }
    day_master = bazi[2][0]  # 日主是天干
    
    # 创建 VirtualBaziProfile，自动反推出生日期
    profile = VirtualBaziProfile(pillars, day_master=day_master, gender=gender)
    
    # 使用反推的 profile 计算大运
    dayun = profile.get_luck_pillar_at(year)
    return dayun
```

---

## 📊 工具类对比

| 工具类/函数 | 位置 | 主要功能 | 精度 | 适用场景 |
|------------|------|---------|------|---------|
| **BaziCalculator** | `core/calculator.py` | 从日期计算八字 | 高（支持真太阳时） | 正常排盘 |
| **BaziProfile** | `core/bazi_profile.py` | 八字档案，大运查询 | 高 | 正常排盘，大运查询 |
| **VirtualBaziProfile** | `core/bazi_profile.py` | 从四柱反推日期 | 中（近似值） | 测试用例，已知八字 |
| **reverse_lookup_bazi** | `ui/pages/zeitgeist.py` | 精确反推日期 | 高（暴力搜索） | UI 反推功能 |
| **_reverse_calculate_date** | `ui/modules/profile_section.py` | 简化反推日期 | 低（近似值） | UI 快速预览 |
| **calculate_dayun_from_bazi** | `scripts/...` | 从八字计算大运 | 中 | 脚本工具 |

---

## 🔍 反推功能详细说明

### 反推出生年月日时的实现方式

#### 方式 1: VirtualBaziProfile（推荐）

**优点**:
- 代码集中，易于维护
- 自动创建 BaziProfile，可计算大运
- 支持完整的八字功能

**缺点**:
- 年份范围有限（1920-2020）
- 日期为近似值（月中15日）

**实现位置**: `core/bazi_profile.py:139-185`

#### 方式 2: reverse_lookup_bazi（精确）

**优点**:
- 精确匹配，考虑立春边界
- 可指定搜索年份范围
- 返回精确的日期时间

**缺点**:
- 性能较低（暴力搜索）
- 只返回第一个匹配结果

**实现位置**: `ui/pages/zeitgeist.py:139-187`

#### 方式 3: _reverse_calculate_date（快速）

**优点**:
- 计算快速
- 适合 UI 预览

**缺点**:
- 精度较低（近似值）
- 不考虑立春边界

**实现位置**: `ui/modules/profile_section.py:253-313`

---

## 🛠️ 大运计算工具

### 1. BaziCalculator.get_luck_cycles()

**功能**: 计算大运周期列表

**返回格式**:
```python
[
    {
        "index": 0,
        "start_year": 1994,
        "end_year": 2003,
        "start_age": 4,
        "gan_zhi": "甲子",
        "gan": "甲",
        "branch": "子"
    },
    ...
]
```

### 2. BaziProfile.get_luck_pillar_at()

**功能**: O(1) 查询指定年份的大运

**实现**: 使用预构建的时间线查找表

### 3. LuckEngine 系列方法

**功能**: 提供更丰富的大运查询功能
- 根据年龄查询
- 根据年份查询
- 判断换运年份
- 获取大运时间线

---

## 📝 使用建议

### 场景 1: 正常排盘（已知出生日期）

```python
from core.calculator import BaziCalculator

calc = BaziCalculator(1990, 5, 15, 12, 0, longitude=116.4)
chart = calc.get_chart()
luck_cycles = calc.get_luck_cycles(gender_idx=1)
```

### 场景 2: 从八字反推日期（已知八字）

```python
from core.bazi_profile import VirtualBaziProfile

pillars = {'year': '甲子', 'month': '丙寅', 'day': '庚辰', 'hour': '戊午'}
profile = VirtualBaziProfile(pillars, day_master='庚', gender=1)
birth_date = profile.birth_date
luck_2024 = profile.get_luck_pillar_at(2024)
```

### 场景 3: 精确反推（需要精确日期）

```python
from ui.pages.zeitgeist import reverse_lookup_bazi

target_bazi = ['甲子', '丙寅', '庚辰', '戊午']
birth_date = reverse_lookup_bazi(target_bazi, start_year=1950, end_year=2030)
```

### 场景 4: 快速预览（UI 场景）

```python
from ui.modules.profile_section import _reverse_calculate_date

result = _reverse_calculate_date('甲子', '丙寅', '庚辰', '戊午')
approx_date = result['date']
```

---

## ⚠️ 注意事项

1. **年份范围限制**
   - `VirtualBaziProfile` 默认搜索 1920-2020
   - 如需其他范围，需要修改代码

2. **日期精度**
   - 反推功能通常使用月中（15日）作为近似值
   - 只有 `reverse_lookup_bazi` 提供精确日期

3. **立春边界**
   - 年柱和月柱的切换点在立春
   - `reverse_lookup_bazi` 考虑了立春边界
   - 其他反推方法可能不准确

4. **真太阳时**
   - `BaziCalculator` 支持真太阳时修正
   - 需要提供 `longitude` 参数
   - 其他工具类不包含真太阳时修正

5. **大运计算**
   - 大运计算需要性别信息（男顺女逆）
   - 大运起始年龄需要出生月份和日期

---

## 🔄 改进建议

1. **统一反推接口**
   - 建议创建一个统一的 `BaziReverseCalculator` 类
   - 整合所有反推功能
   - 提供统一的 API

2. **扩展年份范围**
   - `VirtualBaziProfile` 支持自定义年份范围
   - 或使用更智能的算法

3. **提高精度**
   - 反推功能考虑立春边界
   - 提供精确日期匹配

4. **性能优化**
   - `reverse_lookup_bazi` 使用索引优化
   - 缓存常用查询结果

---

**最后更新**: 2025-01-XX  
**审查人**: AI Assistant  
**版本**: V1.0

