# V52.0 任务 C：合力结算 (Net Force Settlement) 实现报告

**执行时间**: 2025-12-16  
**执行人**: Cursor AI (按架构师指令)  
**状态**: ✅ 已完成

---

## 📋 任务概述

实现显式的"净作用力计算"（Net Force Calculation），解决 Balanced 案例的误判问题。

**核心问题**: 图网络容易陷入"大锅炖"，把所有能量混在一起迭代，无法准确识别"受力平衡态"。

**解决方案**: 在 Phase 3 传播结束后，显式计算日主受到的净作用力，如果推力与拉力差值小于阈值，强制判定为 Balanced。

---

## ✅ 实现内容

### 1. 新增方法：`_calculate_net_force()`

**位置**: `core/engine_graph.py`

**功能**:
- 显式计算日主受到的 **Total_Push (推力)** 和 **Total_Pull (拉力)**
- 计算平衡比例：`balance_ratio = (total_push - total_pull) / total_force`
- 如果 `abs(balance_ratio) < 0.15`（15%容差），判定为"受力平衡态"

**推力 (Total_Push)**:
- 印星（生我）：Resource element
- 比劫（同我）：Self element

**拉力 (Total_Pull)**:
- 官杀（克我）：Officer element
- 食伤（我生）：Output element（泄气）
- 财星（我克）：Wealth element（耗气）

### 2. 修改方法：`calculate_strength_score()`

**新增逻辑**:
```python
# [V52.0] 任务 C：显式计算净作用力
net_force_result = self._calculate_net_force(dm_element, resource_element)
total_push = net_force_result['total_push']
total_pull = net_force_result['total_pull']
net_force_balance = net_force_result['balance_ratio']

# 净作用力平衡检测：如果推力与拉力差值小于15%，强制判定为 Balanced
net_force_threshold = 0.15  # 15% 容差
if abs(net_force_balance) < net_force_threshold:
    strength_label = "Balanced"
    net_force_override = True
```

### 3. 返回值扩展

`calculate_strength_score()` 现在返回额外的 `net_force` 信息：
```python
{
    'strength_score': float,
    'strength_label': str,
    'net_force': {
        'total_push': float,      # 推力（印+比）
        'total_pull': float,       # 拉力（官杀+食伤+财）
        'balance_ratio': float,    # 平衡比例 (-1.0 到 1.0)
        'override': bool           # 是否被净作用力覆盖判定
    }
}
```

---

## 🎯 物理原理

### 受力平衡态 (Force Equilibrium State)

**传统判定**: 基于占比分数（Self_Team / Total_Energy）

**问题**: 
- 占比分数可能显示 Strong（比如 65%），但实际上推力与拉力接近平衡
- 图网络迭代后，能量"大锅炖"，无法区分"真强"和"假强"

**新判定**:
- 显式计算净作用力：`F_net = F_push - F_pull`
- 如果 `|F_net| / (F_push + F_pull) < 15%`，判定为 **Balanced**
- 这是物理学上的"受力平衡态"，即使占比分数可能显示 Strong 或 Weak

### 作用力分类

| 十神 | 元素关系 | 作用力类型 | 物理意义 |
|------|---------|-----------|---------|
| **印星** | 生我 | 推力 (Push) | 能量输入，增强日主 |
| **比劫** | 同我 | 推力 (Push) | 共振加强，增强日主 |
| **官杀** | 克我 | 拉力 (Pull) | 能量对抗，削弱日主 |
| **食伤** | 我生 | 拉力 (Pull) | 能量输出，泄气 |
| **财星** | 我克 | 拉力 (Pull) | 能量消耗，耗气 |

---

## 📊 计算示例

### 案例：月干生、时干克的平衡态

**八字**: 年柱(木) 月柱(火) 日柱(土) 时柱(木)

**计算过程**:
1. **推力 (Total_Push)**:
   - 月干（火）生日主（土）：`force = 10.0 × 0.3 = 3.0`
   - 年干（木）生月干（火），间接支持：`force = 8.0 × 0.2 = 1.6`
   - `Total_Push = 3.0 + 1.6 = 4.6`

2. **拉力 (Total_Pull)**:
   - 时干（木）克日主（土）：`force = 8.0 × 0.7 = 5.6`
   - `Total_Pull = 5.6`

3. **平衡比例**:
   - `total_force = 4.6 + 5.6 = 10.2`
   - `balance_ratio = (4.6 - 5.6) / 10.2 = -0.098` (约 -10%)

4. **判定**:
   - `abs(-0.098) = 0.098 < 0.15` ✅
   - **强制判定为 Balanced**（即使占比分数可能显示 Strong）

---

## 🔧 参数配置

**平衡阈值**: `net_force_threshold = 0.15` (15% 容差)

**未来可参数化**:
```json
{
  "strength_judge": {
    "net_force_threshold": 0.15,  // 平衡判定阈值
    "push_coefficients": {
      "resource": 1.0,   // 印星推力系数
      "self": 1.0        // 比劫推力系数
    },
    "pull_coefficients": {
      "officer": 1.0,    // 官杀拉力系数
      "output": 0.8,     // 食伤拉力系数（泄气）
      "wealth": 0.6      // 财星拉力系数（耗气）
    }
  }
}
```

---

## 📈 预期效果

### 解决的问题

1. **假 Strong 误判**:
   - 之前：占比分数 65%，判定为 Strong
   - 现在：净作用力平衡，判定为 Balanced ✅

2. **假 Weak 误判**:
   - 之前：占比分数 35%，判定为 Weak
   - 现在：净作用力平衡，判定为 Balanced ✅

3. **Balanced 准确率提升**:
   - 预期：从 65% 提升到 **75%+**
   - 原因：正确识别"受力平衡态"

### 验证方法

运行 `batch_verify.py`，重点关注：
- **Balanced 准确率**: 应该显著提升
- **Strong/Weak 准确率**: 应该保持或略有提升（因为减少了误判）

---

## 🔄 与现有逻辑的关系

### 优先级

1. **特殊格局检测** (最高优先级)
   - 如果检测到专旺/从旺格，覆盖为 "Special_Strong"

2. **净作用力平衡检测** (次优先级)
   - 如果 `abs(balance_ratio) < 0.15`，强制判定为 "Balanced"

3. **占比分数判定** (默认)
   - 基于 `strength_score` 和阈值判定

### 兼容性

- ✅ 与现有占比分数判定兼容
- ✅ 与特殊格局检测兼容
- ✅ 不影响 Strong/Weak 的正常判定（只在平衡时覆盖）

---

## 📝 下一步

### 任务 A：通关导管 (Mediation Conduit)

**待实现**: 升级 `enable_mediation` 逻辑，计算通关神的容量。

**公式**: `Effective_Flow = Min(Source_Energy, Mediator_Energy)`

### 任务 B：十二长生系数 (12 Phases Coefficient)

**待实现**: 引入 `Energy_Phase_Table`，根据长生状态调整通根权重。

**系数表**:
- 长生/帝旺/临官: `rootingWeight × 1.5`
- 衰/病/死: `rootingWeight × 0.5`
- 墓/绝: `rootingWeight × 0.3`

---

**批准人**: Architect & Antigravity  
**执行代码库**: V52.0 Net Force Settlement

