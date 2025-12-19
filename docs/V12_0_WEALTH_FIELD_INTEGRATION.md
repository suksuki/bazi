# V12.0 "量子财富引力场" 整合方案

## 📋 现状分析

### 现有系统（已实现）

1. **财富验证页面** (`ui/pages/wealth_verification.py`)
   - ✅ 案例管理（导入、选择）
   - ✅ 时间轴验证（单点验证）
   - ✅ 可视化（折线图、置信区间）
   - ✅ 用户反馈功能
   - ✅ 概率分布验证

2. **财富计算引擎** (`core/engine_graph.py::calculate_wealth_index`)
   - ✅ 基于物理模型的财富计算
   - ✅ 财库冲开/坍塌检测
   - ✅ 强根检测
   - ✅ 机会能量计算

3. **数据模型** (`core/models/wealth_case_model.py`)
   - ✅ WealthCase 数据类
   - ✅ WealthEvent 时间轴事件
   - ✅ 案例持久化

### V12.0 新设计核心

1. **F, C, σ 三维向量模型**
   - F: 通关流量 (Flow Vector)
   - C: 掌控系数 (Capacity Vector)
   - σ: 波动/爆发系数 (Volatility Sigma)
   - 公式：W = F × C × (1 + σ)

2. **0-100岁完整时间序列模拟**
   - 自动排盘（大运、流年）
   - 滑动平均平滑
   - 完整人生曲线

3. **名人回测靶场**
   - 高净值名人案例库
   - Ground Truth 对比
   - 拟合度评估

## 🔄 整合策略

### 原则
1. **保留现有功能**：不破坏现有MVC架构
2. **增强而非重写**：在现有基础上扩展
3. **向后兼容**：新功能作为可选增强

### 实施计划

#### Phase 1: 数据基建（名人案例库）
- 创建 `data/celebrity_wealth.json`
- 整合现有名人数据（如Musk）
- 统一数据格式

#### Phase 2: 向量计算引擎（新增模块）
- 创建 `core/wealth_engine/` 目录
- 实现 `vectors.py`（F, C, σ计算）
- 实现 `tomb_physics.py`（墓库物理）
- 与现有 `calculate_wealth_index` 集成

#### Phase 3: 时间序列模拟器
- 创建 `timeline_simulator.py`
- 实现0-100岁完整模拟
- 集成到现有 `simulate_timeline` 方法

#### Phase 4: UI增强
- 在现有 `wealth_verification.py` 中添加新Tab
- 添加"V12.0 量子财富场"视图
- 保留原有功能不变

## 📐 技术架构

```
现有架构：
ui/pages/wealth_verification.py
  └─> controllers/wealth_verification_controller.py
      └─> core/engine_graph.py::calculate_wealth_index

增强架构（V12.0）：
ui/pages/wealth_verification.py (新增Tab)
  └─> controllers/wealth_verification_controller.py (新增方法)
      └─> core/wealth_engine/timeline_simulator.py (新增)
          └─> core/wealth_engine/vectors.py (新增)
              └─> core/engine_graph.py (复用现有)
```

## 🎯 实施优先级

1. **高优先级**：向量计算引擎（核心算法）
2. **中优先级**：时间序列模拟器（完整曲线）
3. **低优先级**：UI增强（可视化优化）

