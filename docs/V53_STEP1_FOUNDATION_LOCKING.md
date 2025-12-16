# V53.0 Step 1: Foundation Locking Tuning (分层锁定 - 第一阶段)

## 概述

V53.0 Step 1 采用严格的 **"分层锁定 (Layer-wise Locking)"** 策略，仅优化基础物理层（Group 1: Foundation），锁死其他所有参数。

**执行日期**: 2025-01-16

---

## 策略说明

### 核心思想

**"先锁死上层建筑，专心夯实地基"**

对于拥有 80+ 参数的复杂系统，一次性全调（Global Optimization）容易导致模型"顾头不顾尾"。采用"控制变量法"（Control Variate Method）或"分块坐标下降"（Block Coordinate Descent），先优化最基础的物理层，确保地基稳固。

### 为什么这样做更有效？

1. **排除干扰**：如果 AI 同时调"生克"和"月令"，它可能会偷懒——比如月令没算对，它就通过把"生"调得特别大来凑数。锁死生克后，AI 就**必须**硬着头皮去把月令权重算准。

2. **物理隔离**：这就像盖楼。我们现在只管打地基（Phase 1）。等地基的 Loss 降到最低不动了，我们再盖主体结构（Phase 2: Flow），最后再搞装修（Phase 3: Interactions）。

---

## 优化范围

### ✅ 仅优化 Group 1: Foundation（基础物理层）

以下参数允许优化（基于 V52.0 黄金值进行 ±30% 浮动）：

1. **`structure.rootingWeight` (通根系数)**
   - 搜索范围: `[3.0, 5.5]`
   - 中心值: `4.25`
   - 说明: 这是地支对天干的支撑力，是一切旺衰的根基

2. **`physics.pillarWeights.month` (月令权重)**
   - 搜索范围: `[1.5, 2.2]`
   - 中心值: `1.88`
   - 说明: 提纲挈领，月令必须是绝对统治者

3. **`physics.pillarWeights.day` (日主权重)**
   - 搜索范围: `[1.2, 1.8]`
   - 中心值: `1.62`
   - 说明: 观测者效应，日主权重需独立微调

4. **`physics.pillarWeights.year` (年柱权重)**
   - 搜索范围: `[0.6, 1.0]`
   - 中心值: `0.82`

5. **`physics.pillarWeights.hour` (时柱权重)**
   - 搜索范围: `[0.7, 1.2]`
   - 中心值: `0.95`

### 🔒 锁死 Group 2: Flow/Dynamics（能量流转层）

以下参数**强制使用** `config/parameters.json` 中的固定值，**不允许优化**：

- `flow.controlImpact`: 固定为 `-2.618`
- `flow.outputDrainPenalty`: 固定为 `2.80`
- `flow.generationEfficiency`: 固定为 `0.25`
- `flow.dampingFactor`: 固定为 `0.33`
- `flow.globalEntropy`: 固定为 `0.1`
- 其他所有 Flow 参数

### 🔒 锁死 Group 3: Interactions（交互层）

以下参数**强制使用** `config/parameters.json` 中的固定值，**不允许优化**：

- `flow.earthMetalMoistureBoost`: 固定为当前值
- `interactions.stemFiveCombination.bonus`: 固定为当前值
- `interactions.branchEvents.clashDamping`: 固定为当前值
- 其他所有 Interactions 参数

---

## 执行策略

### 训练配置

- **Epochs**: 200 次试验/循环
- **Cycles**: 5 轮循环
- **Goal**: 在不改变生克逻辑的前提下，找到能够让 Strong/Weak 案例分类最清晰的"地基参数"
- **Output**: 仅更新 Group 1 参数到配置文件，保留其他参数不变

### 实现方式

在 `create_objective_for_group` 函数中：

1. **仅定义 Group 1 的搜索空间**：使用 `trial.suggest_float()` 定义 Group 1 参数的搜索范围

2. **强制读取固定值**：对于 Group 2 和 Group 3 的参数：
   - **严禁**使用 `trial.suggest`
   - **强制读取** `base_config` 中的值（来自 `config/parameters.json`）
   - 这些值在 `copy.deepcopy(base_config)` 时已经包含

3. **逻辑保证**：当 `group_params == GROUP_1_FOUNDATION` 时，Group 2 和 Group 3 的参数不会进入 `if 'flow.xxx' in group_params` 的条件，因此会使用 `base_config` 中的固定值

---

## 预期效果

### 1. 地基参数优化

AI 会专注于找到最佳的：
- 月令权重（确保月令的统治力）
- 通根系数（确保地支对天干的支撑力）
- 日主权重（确保观测点的准确性）

### 2. 物理隔离

- 不会通过调整"生克"来补偿"月令"的错误
- 必须硬着头皮把基础物理参数算准
- 为后续的 Flow 和 Interactions 优化打下坚实基础

### 3. 损失降低

- 在不改变生克逻辑的前提下，通过优化基础参数降低损失
- 为后续阶段提供更好的起点

---

## 代码修改

### 主要变更

1. **修改 `run_cyclic_optimization` 函数**:
   - 添加 `step` 参数（1=Foundation only, 2=Flow only, 3=All）
   - 当 `step=1` 时，只运行 Stage 1 (Foundation)

2. **修改 `create_objective_for_group` 函数**:
   - 添加注释说明：当只优化 Group 1 时，Group 2 和 Group 3 使用固定值

3. **修改 `main` 函数**:
   - 调用 `run_cyclic_optimization` 时传入 `step=1`

---

## 下一步

完成 Step 1 后，可以继续：

- **Step 2: Flow Locking Tuning**：锁死 Foundation 和 Interactions，只优化 Flow/Dynamics
- **Step 3: Interactions Locking Tuning**：锁死 Foundation 和 Flow，只优化 Interactions
- **Step 4: Full Optimization**：所有参数一起优化（使用 Step 1-3 的结果作为起点）

---

## 相关文档

- `docs/V53_CONTROLLED_FLOAT.md` - V53.0 受控浮动策略
- `docs/V52_BASE_PARAMETER_RESET.md` - V52.0 基础参数重置
- `docs/V51_GOLDEN_RATIO_RESET.md` - V51.0 黄金比例重置

---

## 版本信息

- **版本**: V53.0 Step 1
- **日期**: 2025-01-16
- **作者**: Antigravity Team
- **类型**: 分层锁定优化 (Layer-wise Locking Optimization)
- **策略**: 控制变量法 (Control Variate Method)

