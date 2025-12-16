# V21.0 任务 56：能量流与耦合效应（核心算法二级补充）

## 📋 任务概述

**目标：** 在模型第一层（十神波函数计算）中，实现四柱间的能量传递与抵消机制。

**状态：** 📝 文档设计阶段（待实现）

---

## 1. 问题定义

### 1.1 核心问题

**四柱间的能量传递与抵消机制（Spatial Coupling）**

在传统八字理论中，四柱（年、月、日、时）之间的天干存在生克关系，这些关系会产生：

1. **顺生链放大（Sequential Amplification）**：年干生月干，月干生日干，形成连续的能量传递链
2. **合力共振（Coherent Resonance）**：多个同方向的力量作用于同一目标（如年干、月干都生日干）
3. **多重力量抵消（Multi-Force Cancellation）**：同时存在相反的作用（生/克），产生净能量抵消

### 1.2 问题举例

| 您的举例 | 机制定义 | 修正目标 |
| --- | --- | --- |
| **年干生月干，月干生日干** | **顺生链放大 (Sequential Amplification)** | 增强能量的顺畅性和力量 |
| **年干、月干都生日干** | **合力共振 (Coherent Resonance)** | 增强能量的集中性和稳定性 |
| **月干克日干，时干生日干** | **多重力量抵消 (Multi-Force Cancellation)** | 模拟命局中的内在矛盾和平衡 |

---

## 2. 算法设计

### 2.1 顺生链放大（Sequential Amplification）

#### 定义

如果能量沿相同方向连续流动（年→月→日→时），每增加一环，最终受益者的能量放大。

#### 算法逻辑

```
对于日主（Day Master）：
  检测从年柱到日主的顺生链：
    如果 年干生月干 且 月干生日干：
      顺生链长度 = 2
      日主能量 *= (Sequential_Gain_Factor ^ 顺生链长度)
      默认 Sequential_Gain_Factor = 1.20
```

#### 计算示例

**案例：** 年干（木）生月干（火），月干（火）生日干（土）

- 顺生链长度 = 2
- 日主（土）能量 *= 1.20^2 = 1.44
- **效果：** 日主能量放大 44%

#### 扩展规则

- **三环顺生：** 年→月→日→时，顺生链长度 = 3，放大 = 1.20^3 = 1.728
- **部分顺生：** 如果只有年→月或月→日，顺生链长度 = 1，放大 = 1.20

---

### 2.2 合力共振（Coherent Resonance）

#### 定义

多个同方向的力量作用于同一目标，对目标进行加成。

#### 算法逻辑

```
对于日主（Day Master）：
  统计所有生日干的天干数量：N
  如果 N >= 2：
    日主能量 *= (1 + (N - 1) * Coherence_Boost_Factor)
    默认 Coherence_Boost_Factor = 0.15
```

#### 计算示例

**案例：** 年干（木）生日干（火），月干（木）也生日干（火）

- N = 2（两个天干都生日主）
- 日主（火）能量 *= (1 + (2-1) * 0.15) = 1.15
- **效果：** 日主能量放大 15%

#### 扩展规则

- **三个支持：** N = 3，放大 = 1 + (3-1) * 0.15 = 1.30（30%）
- **四个支持：** N = 4，放大 = 1 + (4-1) * 0.15 = 1.45（45%）
- **单个支持：** N = 1，不触发合力共振（需要至少 2 个）

---

### 2.3 多重力量抵消（Multi-Force Cancellation）

#### 定义

如果力量同时存在相反的作用（生/克），则作用于日主的净能量按比例抵消。

#### 算法逻辑

```
对于日主（Day Master）：
  统计生日干的天干数量：N_support
  统计克日干的天干数量：N_control
  
  如果 N_support > 0 且 N_control > 0：
    净能量系数 = (N_support - N_control * Cancellation_Factor) / (N_support + N_control)
    默认 Cancellation_Factor = 0.60
    
    如果净能量系数 > 0：
      日主能量 *= 净能量系数
    否则：
      日主能量 *= 0.1（最小保留值，防止完全归零）
```

#### 计算示例

**案例：** 年干（木）生日干（火），月干（水）克日干（火）

- N_support = 1（年干生）
- N_control = 1（月干克）
- 净能量系数 = (1 - 1 * 0.60) / (1 + 1) = 0.20
- 日主（火）能量 *= 0.20
- **效果：** 日主能量被大幅削弱，仅保留 20%

#### 扩展规则

**案例 1：** 2 生 1 克
- N_support = 2, N_control = 1
- 净能量系数 = (2 - 1 * 0.60) / (2 + 1) = 0.467
- 日主能量 *= 0.467（保留 46.7%）

**案例 2：** 1 生 2 克
- N_support = 1, N_control = 2
- 净能量系数 = (1 - 2 * 0.60) / (1 + 2) = -0.067（负数）
- 日主能量 *= 0.1（最小保留值 10%）

---

## 3. 参数定义

### 3.1 配置位置

在 `config/parameters.json` 的 `flow` 模块中新增：

```json
{
  "flow": {
    "outputViscosity": {
      "maxDrainRate": 0.35,
      "drainFriction": 0.3,
      "viscosity": 0.95
    },
    "resourceImpedance": {
      "base": 0.75,
      "weaknessPenalty": 0.75
    },
    "couplingEffects": {
      "Sequential_Gain_Factor": 1.20,
      "Coherence_Boost_Factor": 0.15,
      "Cancellation_Factor": 0.60
    }
  }
}
```

### 3.2 参数说明

| 参数名 | 默认值 | 范围建议 | 说明 |
|--------|--------|----------|------|
| **Sequential_Gain_Factor** | 1.20 | 1.10 ~ 1.30 | 顺生链每环的放大倍率 |
| **Coherence_Boost_Factor** | 0.15 | 0.10 ~ 0.25 | 合力共振每增加一个支持者的加成率 |
| **Cancellation_Factor** | 0.60 | 0.40 ~ 0.80 | 克的力量相对于生的力量的抵消系数 |

---

## 4. 实现设计

### 4.1 实现位置

**在 `PhysicsProcessor.process()` 中：**

1. **执行时机：** 在计算完基础能量、通根加成、时代修正之后
2. **执行位置：** 在返回 `raw_energy` 之前
3. **修正目标：** 直接修正 `raw_energy` 字典中的五行能量，特别关注日主对应的元素能量

### 4.2 算法优先级

**应用顺序：**

```
1. 基础能量计算（天干+地支藏干）
2. 通根加成
3. 时代修正
4. 【V21.0 新增】能量流耦合修正 ← 在这里应用
5. 返回 raw_energy 给 DomainProcessor
```

### 4.3 实现逻辑流程

```
1. 从 context 中获取 flow_config
2. 提取 couplingEffects 参数（带默认值）
3. 从 bazi 中提取四柱天干和元素
4. 识别日主（Day Master，位于日柱）
5. 应用三个耦合效应：
   a. 检测顺生链（年→月→日）
   b. 统计合力共振（多个生）
   c. 计算多重抵消（生 vs 克）
6. 修正 raw_energy[dm_element]
7. 返回修正后的 energy
```

### 4.4 代码结构（伪代码）

```python
def _apply_coupling_effects(self, energy, bazi, dm_element, context):
    """
    V21.0: Apply Energy Flow Coupling Effects
    """
    # 1. 获取参数
    flow_config = context.get('flow_config', {})
    coupling = flow_config.get('couplingEffects', {})
    seq_gain = coupling.get('Sequential_Gain_Factor', 1.20)
    coherence_boost = coupling.get('Coherence_Boost_Factor', 0.15)
    cancel_factor = coupling.get('Cancellation_Factor', 0.60)
    
    # 2. 提取四柱天干元素
    stems = [提取年、月、日、时天干]
    stem_elements = [转换为五行元素]
    
    # 3. 顺生链放大
    if 检测到顺生链:
        计算链长度
        日主能量 *= seq_gain ^ 链长度
    
    # 4. 合力共振
    support_count = 统计生日主的天干数量
    if support_count >= 2:
        日主能量 *= (1 + (support_count - 1) * coherence_boost)
    
    # 5. 多重抵消
    support_count = 统计生日主的天干数量
    control_count = 统计克日主的天干数量
    if support_count > 0 and control_count > 0:
        净能量系数 = (support_count - control_count * cancel_factor) / (support_count + control_count)
        日主能量 *= max(净能量系数, 0.1)  # 最小保留 10%
    
    return energy
```

---

## 5. 影响分析

### 5.1 对模型的影响

**预期效果：**
- ✅ 更准确地反映四柱间的能量传递关系
- ✅ 增强顺生链的能量放大效应
- ✅ 体现多力合一的共振效果
- ✅ 模拟生克并存的平衡状态

**潜在风险：**
- ⚠️ 可能过度放大某些案例的能量
- ⚠️ 需要重新校准第二层参数（BiasFactor、CorrectorFactor）

### 5.2 验证计划

**V21.0 Task 56 验证步骤：**

1. **实现代码**（待 Master 批准）
2. **运行批量校准脚本**
3. **对比 MAE 变化：**
   - 记录所有 8 个案例的 MAE
   - 分析哪些案例改善，哪些案例恶化
   - 识别需要重新调优的参数
4. **参数微调：**
   - 如果整体 MAE 上升，调整 `couplingEffects` 参数
   - 如果部分案例恶化，调整第二层参数（BiasFactor、CorrectorFactor）

---

## 6. 理论依据

### 6.1 传统命理依据

**《三命通会》** 中提到：
- "年干生月干，月干生日干，谓之顺生，主贵"
- "多干生一干，谓之合力，主强"
- "生克并存，谓之制化，主平衡"

### 6.2 量子力学类比

- **顺生链放大：** 类似量子纠缠的能量传递
- **合力共振：** 类似波函数的相干叠加
- **多重抵消：** 类似量子态的干涉相消

---

## 7. 待讨论问题

### 7.1 算法细节

1. **顺生链是否包含时柱？**
   - 选项 A：只考虑年→月→日
   - 选项 B：考虑年→月→日→时（四环）

2. **合力共振是否考虑地支？**
   - 当前设计：只考虑天干
   - 扩展可能：考虑地支藏干

3. **多重抵消的最小保留值？**
   - 当前设计：10%
   - 是否需要根据身强身弱调整？

### 7.2 参数调优

1. **默认参数是否合理？**
   - Sequential_Gain_Factor = 1.20（每环 20%）
   - Coherence_Boost_Factor = 0.15（每增加一个支持者 15%）
   - Cancellation_Factor = 0.60（克的力量是生的 60%）

2. **是否需要案例特定参数？**
   - 类似 `CaseSpecificCorrectorFactor`
   - 是否需要 `CaseSpecificCouplingFactor`？

---

## 8. 下一步行动

### 8.1 待 Master 批准

- [ ] 算法设计是否合理？
- [ ] 参数默认值是否合适？
- [ ] 实现位置是否正确？
- [ ] 是否需要调整算法细节？

### 8.2 实现计划（待批准后）

1. **代码实现：**
   - 在 `PhysicsProcessor` 中添加 `_apply_coupling_effects()` 方法
   - 在 `EngineV88` 和 `EngineV91` 中传递 `flow_config`
   - 更新 `config/parameters.json`

2. **验证测试：**
   - 运行批量校准脚本
   - 分析 MAE 变化
   - 生成验证报告

3. **参数调优：**
   - 根据验证结果调整参数
   - 必要时重新调优第二层参数

---

**文档生成时间：** V21.0 Task 56 (Energy Flow Coupling Design)
**文档状态：** 📝 设计阶段（待 Master 批准后实现）

