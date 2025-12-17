# MCP V9.3 API 文档

## 概述

Model Context Protocol (MCP) V9.3 提供了动态上下文驱动的预测功能。本文档说明所有 MCP 相关的 API 接口。

---

## 🌍 地理修正 API

### GeoProcessor

**位置**: `core.processors.geo.GeoProcessor`

#### `process(input_location: Any) -> Dict[str, float]`

计算地理修正系数。

**参数**:
- `input_location`: 城市名称 (str) 或纬度 (float)

**返回**:
```python
{
    'wood': 1.05,              # 木能量修正系数
    'fire': 1.15,              # 火能量修正系数
    'earth': 0.95,             # 土能量修正系数
    'metal': 1.0,              # 金能量修正系数
    'water': 0.9,              # 水能量修正系数
    'desc': 'City: Beijing',   # 描述
    'temperature_factor': 1.0, # 温度系数（寒暖）
    'humidity_factor': 1.0,    # 湿度系数（燥湿）
    'environment_bias': '环境修正偏向：火能量增强(1.15x)'  # 环境修正偏向
}
```

**示例**:
```python
from core.processors.geo import GeoProcessor

geo = GeoProcessor()
result = geo.process("Beijing")
print(result['environment_bias'])
```

---

## ⏳ 流时修正 API

### HourlyContextProcessor

**位置**: `core.processors.hourly_context.HourlyContextProcessor`

#### `process(context: Dict[str, Any]) -> Dict[str, Any]`

计算流时修正。

**参数**:
```python
{
    'day_master': '甲',                    # 日主天干
    'current_time': datetime.now(),        # 当前时间（可选）
    'bazi': ['甲子', '乙丑', '丙寅', '丁卯']  # 八字列表（可选）
}
```

**返回**:
```python
{
    'hourly_pillar': '甲子',      # 流时干支
    'hourly_stem': '甲',          # 时干
    'hourly_branch': '子',        # 时支
    'interaction': {
        'type': '生',              # 作用类型（生、克、比、泄、耗）
        'strength': 0.8,           # 作用强度
        'description': '...',     # 描述
        'favorable': True         # 是否有利
    },
    'energy_boost': 0.16,         # 能量加成（-0.2 到 0.2）
    'recommendation': '...',      # 决策建议
    'current_hour': 14            # 当前小时
}
```

**示例**:
```python
from core.processors.hourly_context import HourlyContextProcessor
from datetime import datetime

hourly = HourlyContextProcessor()
result = hourly.process({
    'day_master': '甲',
    'current_time': datetime.now(),
    'bazi': ['甲子', '乙丑', '丙寅', '丁卯']
})
print(result['recommendation'])
```

---

## 🌐 宏观场 API

### EraProcessor

**位置**: `core.processors.era.EraProcessor`

#### `process(year: int) -> Dict[str, Any]`

获取时代修正信息。

**参数**:
- `year`: 年份（如 2024）

**返回**:
```python
{
    'era_element': 'fire',         # 时代元素
    'period': 9,                   # 周期编号
    'desc': '离火运',              # 描述
    'modifiers': {
        'fire': 1.2,               # 时代元素增强
        'metal': 0.9                # 被克元素减弱
    },
    'era_bonus': 0.2,              # 时代红利系数
    'era_penalty': -0.1,           # 时代折损系数
    'impact_description': '火能量增强 20%；金能量减弱 10%',
    'start_year': 2024,
    'end_year': 2043
}
```

### BaziController.get_current_era_info()

**位置**: `controllers.bazi_controller.BaziController`

获取当前时代的详细信息。

**返回**: 同 `EraProcessor.process()`

**示例**:
```python
from controllers.bazi_controller import BaziController

controller = BaziController()
era_info = controller.get_current_era_info()
print(era_info['desc'])
```

---

## 💾 交互上下文 API

### WealthVerificationController.add_user_feedback()

**位置**: `controllers.wealth_verification_controller.WealthVerificationController`

添加用户反馈事件。

**参数**:
- `case_id`: 案例ID
- `year`: 年份
- `real_magnitude`: 实际财富值（-100 到 100）
- `description`: 事件描述
- `ganzhi`: 流年干支（可选）
- `dayun`: 大运干支（可选）

**返回**: `(success: bool, message: str)`

**示例**:
```python
from controllers.wealth_verification_controller import WealthVerificationController

controller = WealthVerificationController()
success, message = controller.add_user_feedback(
    case_id="CASE_001",
    year=2025,
    real_magnitude=50.0,
    description="投资成功",
    ganzhi="乙巳",
    dayun="甲子"
)
```

---

## ⚠️ 模型不确定性 API

### GraphNetworkEngine._calculate_pattern_uncertainty()

**位置**: `core.engine_graph.GraphNetworkEngine`

计算格局不确定性。

**参数**:
- `strength_score`: 身强分数 (0-100)
- `strength_label`: 身强标签
- `bazi`: 八字列表
- `dm_element`: 日主元素
- `special_pattern`: 特殊格局（可选）

**返回**:
```python
{
    'has_uncertainty': True,           # 是否有不确定性
    'pattern_type': 'Extreme_Weak',    # 格局类型
    'follower_probability': 0.3,      # 从格转化概率 (0-1)
    'volatility_range': 40.0,         # 预测波动范围
    'warning_message': '⚠️ **极弱格局警告**: ...'
}
```

**示例**:
```python
from core.engine_graph import GraphNetworkEngine

engine = GraphNetworkEngine()
result = engine.analyze(['甲子', '丙午', '辛卯', '壬辰'], '辛', '男')
uncertainty = result.get('uncertainty', {})
if uncertainty.get('has_uncertainty'):
    print(uncertainty['warning_message'])
```

---

## 🔧 Controller API

### BaziController.get_geo_modifiers()

获取地理修正系数。

**参数**:
- `city`: 城市名称

**返回**: 地理修正系数字典（同 `GeoProcessor.process()`）

### BaziController.get_current_era_info()

获取当前时代信息。

**返回**: 时代信息字典（同 `EraProcessor.process()`）

---

## 📊 使用示例

### 完整 MCP 流程

```python
from controllers.bazi_controller import BaziController
from core.processors.hourly_context import HourlyContextProcessor
from datetime import datetime

# 1. 初始化 Controller
controller = BaziController()

# 2. 获取地理修正
geo_mods = controller.get_geo_modifiers("Beijing")
print(f"地理修正: {geo_mods.get('environment_bias')}")

# 3. 获取时代信息
era_info = controller.get_current_era_info()
print(f"当前时代: {era_info.get('desc')}")

# 4. 计算流时修正
hourly = HourlyContextProcessor()
hourly_result = hourly.process({
    'day_master': '甲',
    'current_time': datetime.now(),
    'bazi': ['甲子', '乙丑', '丙寅', '丁卯']
})
print(f"流时建议: {hourly_result.get('recommendation')}")

# 5. 分析格局不确定性
from core.engine_graph import GraphNetworkEngine
engine = GraphNetworkEngine()
result = engine.analyze(['甲子', '丙午', '辛卯', '壬辰'], '辛', '男')
uncertainty = result.get('uncertainty', {})
if uncertainty.get('has_uncertainty'):
    print(f"不确定性警告: {uncertainty.get('warning_message')}")
```

---

## 📝 注意事项

1. **地理修正**: 必须提供城市名称或经纬度，否则返回默认值
2. **流时修正**: 需要提供日主和当前时间
3. **时代信息**: 自动根据当前年份计算
4. **不确定性**: 仅在极弱格局或多冲格局时返回
5. **用户反馈**: 需要先有案例数据才能添加反馈

---

**最后更新**: 2025-01-XX  
**版本**: V9.3 MCP API

