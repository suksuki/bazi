# V10.0 MCP 上下文注入指南

**版本**: V10.0  
**日期**: 2025-01-17  
**用途**: 指导如何在量子验证页面使用MCP上下文注入

---

## 📋 概述

根据V10.0架构，**大运、流年、GEO、ERA等上下文信息通过MCP协议注入**，不再需要在UI中手动调节。

---

## 🎯 上下文注入范围

### 1. 地理信息 (GEO)

**数据来源**: 案例数据中的 `geo_city`, `geo_latitude`, `geo_longitude`

**注入方式**:
```python
# 案例数据格式
case = {
    "geo_city": "Beijing",
    "geo_longitude": 116.407,
    "geo_latitude": 39.904
}

# MCP注入
context = inject_context(case)
# context['geo_city'] = "Beijing"
# context['geo_latitude'] = 39.904
# context['geo_longitude'] = 116.407
```

**UI变更**: 删除 `Panel 5` 中的城市选择器和地理修正参数

### 2. 时代背景 (ERA)

**数据来源**: 案例数据中的 `birth_date`，自动计算元运

**注入方式**:
```python
# 案例数据格式
case = {
    "birth_date": "1961-10-10"
}

# MCP自动计算ERA
from datetime import datetime
birth_year = datetime.strptime(case['birth_date'], "%Y-%m-%d").year

# 元运计算规则
if birth_year < 1984:
    era = "Period 8 (Earth)"
elif birth_year < 2024:
    era = "Period 9 (Fire)"
else:
    era = "Period 1 (Water)"

context['era_element'] = era.split()[1].strip('()')  # "Earth", "Fire", "Water"
```

**UI变更**: 删除 `Panel 5` 中的ERA Factor滑块

### 3. 大运 (Luck Pillar)

**数据来源**: 
- 案例的 `timeline` 数据中的 `dayun` 字段
- 或根据 `birth_date` 和 `gender` 自动计算

**注入方式**:
```python
# 方式1: 从timeline获取
if case.get('timeline'):
    context['luck_pillar'] = case['timeline'][0]['dayun']

# 方式2: 自动计算（如果timeline中没有）
else:
    context['luck_pillar'] = calculate_luck_pillar(
        birth_date=case['birth_date'],
        gender=case['gender']
    )
```

**UI变更**: 删除 `Panel 5` 中的"大运权重"滑块（权重通过配置文件设置，不需要UI调节）

### 4. 流年 (Year Pillar)

**数据来源**: 
- 用户选择的年份（在UI中选择）
- 或从 `timeline` 数据中获取

**注入方式**:
```python
# 用户选择年份
selected_year = 2014  # 从UI获取

# 计算流年干支
context['year_pillar'] = calculate_year_pillar(selected_year)
# 例如：2014 -> "甲午"
```

**UI变更**: 保留年份选择器（在主界面），但不需要权重调节

---

## 🔧 实施步骤

### 步骤1: 修改案例加载逻辑

```python
# ui/pages/quantum_lab.py

def load_case_with_mcp_context(case_id: str) -> Dict[str, Any]:
    """加载案例并注入MCP上下文"""
    # 1. 加载案例数据
    case = load_case(case_id)
    
    # 2. 注入MCP上下文
    context = inject_context(case)
    
    # 3. 返回合并后的数据
    return {**case, **context}
```

### 步骤2: 修改引擎调用

```python
# ui/pages/quantum_lab.py

# 旧代码（需要手动传递GEO、ERA）
result = engine.analyze(
    bazi=case['bazi'],
    day_master=case['day_master'],
    city=st.sidebar.selectbox("城市", ...),  # ❌ 删除
    latitude=...,
    longitude=...,
    era_element=st.sidebar.selectbox("元运", ...)  # ❌ 删除
)

# 新代码（使用MCP上下文）
case_with_context = load_case_with_mcp_context(case_id)
result = engine.analyze(
    bazi=case_with_context['bazi'],
    day_master=case_with_context['day_master'],
    city=case_with_context['geo_city'],  # ✅ 从上下文获取
    latitude=case_with_context['geo_latitude'],
    longitude=case_with_context['geo_longitude'],
    era_element=case_with_context['era_element'],  # ✅ 自动计算
    luck_pillar=case_with_context['luck_pillar'],  # ✅ 从上下文获取
    year_pillar=case_with_context['year_pillar']   # ✅ 从用户选择计算
)
```

### 步骤3: 删除UI参数

```python
# ui/pages/quantum_lab.py

# ❌ 删除整个 Panel 5: 时空修正 (Spacetime)
# with st.sidebar.expander("⏳ 时空修正 (Spacetime)", expanded=False):
#     lp_w = st.slider("大运权重 (Luck Pillar)", ...)  # ❌ 删除
#     era_txt = st.selectbox("当前元运 (Era)", ...)    # ❌ 删除
#     geo_cities_list = load_geo_cities_for_sidebar()  # ❌ 删除
#     p2_city_input = st.selectbox("🌍 出生城市", ...) # ❌ 删除
```

---

## 📝 MCP上下文数据结构

```python
{
    # 基本信息（从案例数据）
    "bazi": ["年柱", "月柱", "日柱", "时柱"],
    "day_master": "日主",
    "gender": "性别",
    "birth_date": "YYYY-MM-DD",
    
    # GEO信息（从案例数据）
    "geo_city": "城市名称",
    "geo_longitude": 经度,
    "geo_latitude": 纬度,
    
    # ERA信息（自动计算）
    "era_element": "Fire|Earth|Water",
    "era_bonus": 0.2,  # 从配置文件读取
    "era_penalty": 0.1,  # 从配置文件读取
    
    # 大运信息（从timeline或计算）
    "luck_pillar": "大运干支",
    "luck_pillar_weight": 0.5,  # 从配置文件读取
    
    # 流年信息（用户选择或计算）
    "year_pillar": "流年干支",
    "selected_year": 2014,
    
    # 其他上下文
    "use_solar_time": True,  # 从案例数据或配置
    "invert_seasons": False  # 从案例数据或配置
}
```

---

## ✅ 实施检查清单

- [ ] 修改案例加载函数，支持MCP上下文注入
- [ ] 修改引擎调用，使用上下文数据而非UI参数
- [ ] 删除Panel 5时空修正面板的所有UI代码
- [ ] 删除城市选择器相关代码
- [ ] 删除ERA Factor滑块
- [ ] 删除大运权重滑块（权重通过配置文件设置）
- [ ] 测试MCP上下文注入是否正确工作
- [ ] 验证删除UI参数后，功能仍然正常

---

## 🔗 相关文档

- [V10.0 MCP 协议文档](./V10_MCP_PROTOCOL.md)
- [V10.0 量子验证页面 UI Review](./V10_QUANTUM_LAB_UI_REVIEW.md)

