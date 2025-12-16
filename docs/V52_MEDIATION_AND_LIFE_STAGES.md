# V52.0 算法补全：通关导管与十二长生系数

## 概述

V52.0 版本实现了两个关键的"中间件"算法，用于提升八字能量传导的精确度：

1. **任务 A：通关导管 (Mediation Conduit)**
2. **任务 B：十二长生系数 (12 Life Stages Coefficient)**

---

## 任务 A：通关导管 (Mediation Conduit)

### 问题描述

原有的 `enable_mediation` 参数只是一个简单的 `True/False` 开关，过于粗糙。物理上，"通关"不是一个开关，而是一个**"能量导管" (Conduit)**，需要计算**"导管容量" (Conduit Capacity)**。

**例子**：金克木，有水通关。
- **原有逻辑**：如果开关开了，金就不克木了？
- **缺失逻辑**：**"导管容量"**。如果水（通关神）太弱，它根本承载不了金的巨大能量，会被"冲爆"，通关失败，金依然会去克木。

### 实现方案

在 `core/engine_graph.py` 的 `_get_control_weight()` 方法中实现：

```python
def _get_control_weight(self, source_element: str, target_element: str,
                        flow_config: Dict, source_char: str = None,
                        target_char: str = None) -> float:
    """
    [V52.0] 任务 A：通关导管逻辑
    - 如果存在通关神（中间元素），计算导管容量
    - 只有当通关神足够强时，才能转化掉克制力
    """
    # 1. 查找通关神（中间元素）
    mediator_element = self._find_mediator_element(source_element, target_element)
    
    # 2. 计算导管容量 = Min(源能量, 通关神能量)
    conduit_capacity = min(abs(source_energy), mediator_energy)
    
    # 3. 根据通关神强度，决定转化程度：
    #    - 通关神能量 >= 源能量 * 80%：完全转化（克制力 → 生成力）
    #    - 通关神能量 >= 源能量 * 50%：部分转化（减少 50% 克制力）
    #    - 通关神能量 >= 源能量 * 30%：弱转化（减少 30% 克制力）
    #    - 否则：通关失败，保持原克制力
```

### 通关类型

1. **食伤通关 (Output Mediation)**
   - 场景：劫财克财，有食伤通关
   - 规则：金克木，有水（金生水，水生木）

2. **官杀护财 (Officer Shield)**
   - 场景：比肩劫财克财，有官杀护财
   - 规则：比肩克财，有官杀克比肩

### 配置参数

- `flow.enable_mediation`: 是否启用通关机制（默认：`True`）
- `flow.generationEfficiency`: 生成效率（用于完全通关时的转化）

---

## 任务 B：十二长生系数 (12 Life Stages Coefficient)

### 问题描述

原有的 `rootingWeight` 是一个通用的系数（比如 3.0），这把所有的"根"都同质化了。

**例子**：
- 甲木见亥水是"长生"（活力极强）
- 甲木见未土是"墓库"（有根但被困）

在现有系统中，它们可能都被算作"有根"，给一样的分。

**影响**：这会导致对"身强"的误判。长生之根应该比墓库之根强得多。

### 实现方案

在 `core/engine_graph.py` 中实现：

1. **定义十二长生表** (`TWELVE_LIFE_STAGES`)
   - 记录每个天干在各地支的长生状态
   - 例如：`('甲', '亥'): '长生'`, `('甲', '未'): '墓'`

2. **定义长生系数表** (`LIFE_STAGE_COEFFICIENTS`)
   ```python
   {
       '长生': 1.5,   # 活力极强
       '帝旺': 1.5,   # 能量巅峰
       '临官': 1.5,   # 建禄，强根
       '冠带': 1.2,   # 成长中
       '沐浴': 1.0,   # 基础值
       '胎': 0.8,     # 萌芽
       '养': 0.8,     # 孕育
       '衰': 0.5,     # 衰退
       '病': 0.5,     # 虚弱
       '死': 0.5,     # 无活力
       '墓': 0.3,     # 被困
       '绝': 0.3,     # 极弱
   }
   ```

3. **在通根计算时应用系数**
   ```python
   # 在 _calculate_node_initial_energy() 中
   if node.node_type == 'stem' and node.has_root:
       root_weight = structure_config.get('rootingWeight', 1.0)
       
       # [V52.0] 任务 B：应用十二长生系数
       life_stage = TWELVE_LIFE_STAGES.get((node.char, node.root_branch), None)
       if life_stage:
           life_stage_coefficient = LIFE_STAGE_COEFFICIENTS.get(life_stage, 1.0)
           energy *= life_stage_coefficient
   ```

### 效果

- **长生/帝旺/临官**：通根能量 × 1.5（强根）
- **衰/病/死**：通根能量 × 0.5（弱根）
- **墓/绝**：通根能量 × 0.3（极弱根）

---

## 代码位置

- **通关导管逻辑**：`core/engine_graph.py` → `_get_control_weight()`, `_find_mediator_element()`, `_calculate_mediator_energy()`
- **十二长生系数**：`core/engine_graph.py` → `_calculate_node_initial_energy()` (通根计算部分)
- **十二长生表定义**：`core/engine_graph.py` → `TWELVE_LIFE_STAGES`, `LIFE_STAGE_COEFFICIENTS`

---

## 预期改进

1. **通关导管**：
   - 解决"假中和"或"假身旺"的案例
   - 正确识别通关失败的情况（通关神太弱）

2. **十二长生系数**：
   - 提升"身强"判断的精确度
   - 区分不同强度的通根（长生 vs 墓库）

---

## 版本信息

- **版本**：V52.0
- **日期**：2025-01-16
- **作者**：Antigravity Team
- **相关文档**：
  - `docs/ALGORITHM_SUPPLEMENT_L2_ENERGY_CONDUCTION.md` (能量传导补充文档)
  - `docs/V52_NET_FORCE_SETTLEMENT.md` (任务 C：净作用力结算)

