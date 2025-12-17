# Model Context Protocol (MCP) 改进方案 V9.3

## 📋 概述

将 MCP 从架构概念转化为用户可感知、且对财富预测更具影响力的实时机制。

## 🎯 改进目标

1. **增强地理/环境上下文** (K_geo Activation)
2. **引入动态实时上下文** (流时修正)
3. **强化交互上下文** (案例学习与自我校准)

---

## 1. 🌍 增强地理/环境上下文 (K_geo Activation)

### 1.1 强制地理输入

**问题**: 当前地理输入是可选的，导致地域修正模块未被激活。

**解决方案**:
- 在输入面板中强制要求用户输入城市或经纬度
- 如果未输入，显示警告并阻止预测生成
- 提供城市自动补全功能

**实施位置**:
- `ui/components/unified_input_panel.py` - 添加强制验证
- `ui/pages/prediction_dashboard.py` - 添加地理输入提示

### 1.2 寒暖燥湿可视化

**功能**: 在财富全息图中显示环境修正偏向

**实施位置**:
- `ui/pages/prediction_dashboard.py` - 添加环境修正面板
- `core/processors/geo.py` - 扩展返回环境描述

**显示内容**:
- 温度系数（寒暖）
- 湿度系数（燥湿）
- 对五行能量的修正影响

---

## 2. ⏳ 引入动态实时上下文 (流时修正)

### 2.1 流时修正模块

**功能**: 计算当前小时的干支（流时）与日主之间的作用力

**实施位置**:
- `core/processors/hourly_context.py` - 新建流时处理器
- `core/engine_graph.py` - 集成流时修正

**计算逻辑**:
- 根据当前时间计算流时干支
- 分析流时与日主的生克关系
- 计算短期决策的最佳时间点

### 2.2 宏观场实时更新

**功能**: 在 UI 中动态显示九紫离火运的参数

**实施位置**:
- `ui/pages/prediction_dashboard.py` - 添加宏观场显示
- `core/processors/era.py` - 扩展时代修正信息

**显示内容**:
- 当前时代（如：九紫离火运）
- 时代红利/折损系数
- 对财富预测的影响

---

## 3. 💾 强化交互上下文 (案例学习与自我校准)

### 3.1 事件锚点用户输入

**功能**: 允许用户在财富全息图上点击年份，输入实际财富事件

**实施位置**:
- `ui/pages/wealth_verification.py` - 添加事件输入功能
- `core/models/wealth_case_model.py` - 扩展案例模型
- `controllers/wealth_verification_controller.py` - 处理用户反馈

**数据流**:
1. 用户在图表上点击年份
2. 弹出输入框，输入实际事件和财富值
3. 保存为 Tier B 案例
4. 用于回归调优

### 3.2 模型不确定性提示

**功能**: 针对极弱格局或多冲格局，显示概率分布警告

**实施位置**:
- `core/engine_graph.py` - 计算格局不确定性
- `ui/pages/prediction_dashboard.py` - 显示不确定性警告

**显示内容**:
- 格局类型（极弱、多冲等）
- 转化为从格的概率
- 预测结果的波动范围

---

## 📊 实施优先级

### 高优先级 (P0)
1. ✅ 强制地理输入验证
2. ✅ 寒暖燥湿可视化
3. ✅ 流时修正模块

### 中优先级 (P1)
4. ⏳ 宏观场实时更新
5. ⏳ 事件锚点用户输入

### 低优先级 (P2)
6. ⏳ 模型不确定性提示

---

## 🔧 技术实现细节

### 地理输入验证

```python
def validate_geo_input(city: str, latitude: float, longitude: float) -> bool:
    """验证地理输入是否完整"""
    if city and city != "Unknown":
        return True
    if latitude is not None and longitude is not None:
        return True
    return False
```

### 流时计算

```python
def calculate_hourly_pillar(current_time: datetime) -> str:
    """计算当前小时的干支"""
    # 根据日干和时支计算时干
    # 返回流时干支（如：甲子）
    pass
```

### 用户反馈处理

```python
def save_user_feedback(case_id: str, year: int, real_value: float, description: str):
    """保存用户反馈为新的案例数据"""
    # 保存到 wealth_cases.json
    # 触发回归调优
    pass
```

---

## 📈 预期效果

1. **地理修正激活率**: 从 < 30% 提升到 > 90%
2. **预测准确率**: 提升 5-10%（通过地理修正）
3. **用户参与度**: 通过交互反馈提升 20%
4. **模型自学习**: 通过用户反馈持续优化

---

## 🚀 下一步行动

1. 实现强制地理输入验证
2. 创建流时修正模块
3. 添加寒暖燥湿可视化
4. 实现事件锚点输入功能
5. 添加模型不确定性提示

