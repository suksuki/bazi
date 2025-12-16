# V25.0 任务 68：AI 精确计算路径披露与对齐分析报告

## 🚨 关键发现：多处未对齐问题

基于详细诊断脚本的输出，我发现了 **多个严重的对齐问题**，这些问题导致了 C07 事业相 MAE 无法收敛。

---

## 📊 诊断结果总览

### C07 事业相计算路径

| 步骤 | 理论预期 | 实际结果 | 对齐状态 |
|------|----------|----------|----------|
| **Step A: 原始能量** | Earth ≈ 29.7 | Earth = 29.7 | ✅ 对齐 |
| **Step B: 复杂交互后** | Earth ≈ 26.7 (29.7 - 3.0) | Earth = 4.64 | ❌ **严重未对齐** |
| **Step C: 十神波函数** | Resource ≈ 26.7 | Resource = 4.64 | ❌ 未对齐 |
| **Step D: 基础得分** | S0_Base ≈ 14.79 | S0_Base = 0.00 | ❌ **严重未对齐** |
| **Step E: 最终得分** | Final ≈ 75.0 | Final = 16.27 | ❌ 未对齐 |

---

## 🔍 问题 1：复杂交互后能量过度衰减（严重）

### 现象

**Earth 能量：**
- 交互前：29.7
- 交互后：4.64
- 下降：84.4%

**Wood 能量：**
- 交互前：42.6
- 交互后：17.04
- 下降：60.0%

### 诊断

**代码检查：**
- ✅ 六冲使用减法惩罚：`energy[e1] = max(0, energy.get(e1, 0) + clash_score)`
- ✅ 相刑使用减法惩罚：`energy[e1] = max(0, energy.get(e1, 0) + punishment_penalty)`
- ✅ 相害使用减法惩罚：`energy[e1] = max(0, energy.get(e1, 0) + harm_penalty)`

**但发现：**
1. **六合使用乘法：** `energy[transform_to] = base_energy * 1.2` (第368行)
2. **三合使用乘法：** `energy[elem_lower] = base_energy * trine_bonus` (第314行)
3. **三会使用乘法：** `energy[elem_lower] = base_energy * dir_bonus` (第323行)
4. **天干五合（合绊）使用乘法：** `energy[e1] *= penalty` (第286-287行)

**问题根源：**
- C07 的八字：辛丑、乙未、庚午、甲申
- **未-丑相冲：** 导致 Earth 能量被减法惩罚 -3.0
- **但可能还有其他交互：** 午-未相合（六合），导致 Wood 能量被乘法修正
- **多重交互叠加：** 可能同时触发了多个交互，导致能量被多次修正

**计算验证：**
- 如果只有未-丑相冲：Earth = 29.7 - 3.0 = 26.7 ✅
- 但实际结果：Earth = 4.64 ❌
- **差值：** 26.7 - 4.64 = 22.06

**可能原因：**
1. **午-未相合：** 如果触发了六合，可能影响 Earth 能量
2. **多重惩罚叠加：** 可能同时触发了相冲、相刑、相害
3. **天干五合（合绊）：** 如果触发了合绊，会使用乘法惩罚（0.4倍）

---

## 🔍 问题 2：S0_Base = 0.00（严重）

### 现象

**Career Base Score：**
- 理论预期：≈ 14.79 (officer + resource*0.3 = 13.40 + 4.64*0.3)
- 实际结果：0.00
- **差值：** 14.79

### 诊断

**代码检查：**
- `_calc_career` 方法中，`base_energy_before_amplifier = final_score` (第497行)
- `s0_base = base_energy_before_amplifier` (第540行)
- 但诊断脚本显示 `s0_base = 0.00`

**可能原因：**
1. **`_calc_career` 返回的字典中没有 `s0_base` 键：**
   - 检查返回语句：`return {'score': max(0.0, final_score), 'reason': reason}`
   - **问题：** 返回字典中没有 `s0_base` 或 `base_score` 键！
   - 诊断脚本使用 `career_result.get('s0_base', career_result.get('base_score', 0))`，但都返回默认值 0

2. **`final_score` 在某个地方被设为 0：**
   - 检查代码：`final_score = max(final_score, 0.1)` (第491行)
   - 但可能在后续处理中被设为 0

**修复方案：**
- 需要在 `_calc_career` 的返回字典中添加 `s0_base` 键
- 确保 `s0_base` 在返回前被正确设置

---

## 🔍 问题 3：Pillar Weights 未正确应用

### 现象

**诊断脚本输出：**
- Pillar Weights: `{'year': 0.8, 'month': 1.2, 'day': 1.0, 'hour': 0.9}`
- **V24.0 预期：** `{'year': 1.0, 'month': 1.8, 'day': 1.5, 'hour': 1.2}`

### 诊断

**代码检查：**
- `PhysicsProcessor` 的 `PILLAR_WEIGHTS` 默认值是 V24.0 的值
- 但 `process` 方法中会从 `context.get('pillar_weights', {})` 读取配置
- 如果配置为空，会使用默认值，但默认值可能不是最新的

**问题根源：**
- `EngineV88` 和 `EngineV91` 传递 `pillar_weights` 时，可能传递的是旧值
- 或者 `PhysicsProcessor` 的默认值没有被正确更新

**修复方案：**
- 确保 `EngineV88` 和 `EngineV91` 从配置中读取最新的 `pillarWeights`
- 确保 `PhysicsProcessor` 的默认值与配置一致

---

## 🔍 问题 4：Particle Weights 未应用

### 现象

**诊断脚本输出：**
- Particle Weights: 全部为 1.0
- **预期：** 应该从 `config/parameters.json` 的 `particleWeights` 读取

### 诊断

**代码检查：**
- `DomainProcessor._calculate_ten_gods` 方法中，`particle_weights` 参数来自 `context.get('particle_weights', {})`
- 如果 `particle_weights` 为空，会使用默认值 1.0

**问题根源：**
- `EngineV88` 和 `EngineV91` 可能没有正确传递 `particle_weights` 到 `DomainProcessor`

**修复方案：**
- 确保 `EngineV88` 和 `EngineV91` 从配置中读取 `particleWeights` 并传递给 `DomainProcessor`

---

## 💡 修复方案

### 修复 1：修复 S0_Base 返回问题

**位置：** `core/processors/domains.py` 的 `_calc_career` 方法

**修复内容：**
- 在返回字典中添加 `s0_base` 键
- 确保 `s0_base` 在返回前被正确设置

### 修复 2：修复 Pillar Weights 传递问题

**位置：** `core/engine_v88.py` 和 `core/engine_v91.py`

**修复内容：**
- 确保从配置中读取最新的 `pillarWeights`
- 确保正确传递给 `PhysicsProcessor`

### 修复 3：修复 Particle Weights 传递问题

**位置：** `core/engine_v88.py` 和 `core/engine_v91.py`

**修复内容：**
- 确保从配置中读取 `particleWeights`
- 确保正确传递给 `DomainProcessor`

### 修复 4：检查复杂交互的叠加问题

**位置：** `core/processors/physics.py` 的 `_apply_complex_interactions` 方法

**修复内容：**
- 检查是否有多个交互同时作用导致能量被多次修正
- 考虑添加交互优先级，避免同一元素被多次修正

---

## 📝 下一步行动

### 选项 A：立即修复所有对齐问题

1. 修复 S0_Base 返回问题
2. 修复 Pillar Weights 传递问题
3. 修复 Particle Weights 传递问题
4. 检查复杂交互的叠加问题
5. 重新运行批量校准验证

### 选项 B：分阶段修复

1. **第一阶段：** 修复 S0_Base 返回问题
2. **第二阶段：** 修复参数传递问题
3. **第三阶段：** 检查复杂交互问题

---

**报告生成时间：** V25.0 Task 68 (Alignment Analysis)
**验证状态：** ❌ 发现4个严重对齐问题，需要立即修复

