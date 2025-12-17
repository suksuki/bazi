# V10.0 旺衰判定改进文档

**版本**: V10.0  
**发布日期**: 2025-12-17  
**状态**: ✅ 正式发布

---

## 📋 概述

在 V9.3 之前的系统中，旺衰判定是**硬性的、阶梯式的逻辑**，导致"打地鼠"困境（Fix one, break another）。V10.0 通过三个维度的改进，实现了"降维打击"式的调优。

---

## 🎯 核心问题

### "打地鼠"困境

在传统系统中：
- 旺衰判定是二元的（0 或 1）
- 在临界点附近（如能量值 2.9 vs 3.1）预测结果会发生剧烈震荡
- 调优基础参数会影响全局所有案例
- 修复一个案例可能破坏另一个案例

---

## 🚀 三大改进维度

### 1. 废除"二元论"，引入"旺衰概率波" (Probability Wave)

#### 问题

以前系统判定"身弱"就给 0，判定"身强"就给 1。这种硬切分导致在临界点附近预测结果发生剧烈震荡。

#### 解决方案

使用 **Soft-thresholding (非线性软阈值)**，将旺衰从二元转换为连续概率分布。

#### 数学原理

**Sigmoid 函数**:
```
P(strong) = 1 / (1 + exp(-k * (energy - threshold)))
```

其中：
- `energy`: 能量总和
- `threshold`: 激活函数中心点（中性点）
- `k`: 相变宽度参数（控制过渡的陡峭程度）

#### 实现

```python
from core.strength_probability_wave import StrengthProbabilityWave

# 计算旺衰概率（连续值 [0, 1]）
strength_prob, details = StrengthProbabilityWave.calculate_strength_probability(
    energy_sum=3.5,
    threshold_center=3.0,
    phase_transition_width=10.0
)

# strength_prob: 0.8808 (身强概率)
# details['strength_label']: 'strong'
```

#### 优势

- ✅ 平滑过渡，避免剧烈震荡
- ✅ 可以通过调优 `slope`（斜率）参数控制过渡速度
- ✅ 解决了"打地鼠"问题

---

### 2. 基础参数的"解耦"调优 (GAT 动态注意力)

#### 问题

以前调优基础参数（比如水克火的权重），会影响全局所有案例。

#### 解决方案

利用 **GAT (图注意力网络)**，针对不同命局结构学习专门的旺衰评估权重。

#### 实现

```python
from core.gat_strength_attention import GATStrengthAttention

# 创建 GAT 注意力
gat_attention = GATStrengthAttention(
    n_heads=4,
    hidden_dim=64,
    dropout=0.1  # 注意力稀疏度
)

# 识别命局类型
pattern_type = gat_attention.identify_pattern_type(
    bazi=['辛丑', '丁酉', '庚辰', '丙戌'],
    day_master='庚'
)
# pattern_type: 'wealth_vault' (财库多)

# 计算动态权重
bazi_features = {
    'has_vault': True,
    'clash_count': 1
}
weights = gat_attention.calculate_dynamic_strength_weights(
    bazi_features=bazi_features,
    pattern_type=pattern_type
)
# weights: {'water_fire_weight': 0.4, 'earth_water_weight': 0.7, ...}
```

#### 优势

- ✅ 针对"财库多"的命局，系统自动学习专门的权重
- ✅ 不会干扰到"官印相生"的命局
- ✅ 实现了参数的"局部隔离"

---

### 3. 旺衰判定的"贝叶斯自校准" (Bayesian Self-Calibration)

#### 问题

以前旺衰判错了，只能手动改代码。

#### 解决方案

利用 **贝叶斯推理与 RLHF 闭环**，如果第二阶段的"财富预测"与实际值偏差巨大，自动反向推导第一阶段的旺衰判定是否错误。

#### 实现

```python
from core.bayesian_strength_calibration import BayesianStrengthCalibration

# 计算旺衰置信度
confidence = BayesianStrengthCalibration.calculate_strength_confidence(
    strength_probability=0.6,
    energy_sum=3.2,
    threshold_center=3.0
)
# confidence: 0.75 (75% 置信度)

# 反向推断旺衰判定错误
is_error, suggested_prob = BayesianStrengthCalibration.reverse_infer_strength_error(
    predicted_wealth=30.0,
    real_wealth=50.0,
    strength_probability=0.4,
    wealth_error_threshold=50.0
)
# is_error: True
# suggested_prob: 0.6 (建议增加旺衰概率)

# 自动调整阈值中心点
case_results = [
    {'predicted_wealth': 30.0, 'real_wealth': 50.0, 
     'strength_probability': 0.4, 'energy_sum': 2.8},
    {'predicted_wealth': 80.0, 'real_wealth': 100.0,
     'strength_probability': 0.7, 'energy_sum': 3.5}
]
new_threshold = BayesianStrengthCalibration.auto_adjust_threshold_center(
    case_results=case_results,
    current_threshold=3.0,
    learning_rate=0.01
)
# new_threshold: 2.95 (自动降低阈值)
```

#### 优势

- ✅ 自动反向推导旺衰判定错误
- ✅ 自动调整全局基准
- ✅ 系统通过海量案例自动寻找平衡点

---

## 📊 三个元参数

### 1. 激活函数中心点 (energy_threshold_center)

**作用**: 决定旺衰判定的中性点

**调优方法**: 通过贝叶斯优化，寻找大多数财富爆发案例的能量中枢

**默认值**: 3.0

**调优范围**: [1.0, 5.0]

### 2. 相变宽度 (phase_transition_width / strength_beta)

**作用**: 控制从"极弱"到"中和"转化的敏感速度

**调优方法**: 调整 Softplus 函数的 β 参数

**默认值**: 10.0

**调优范围**: [1.0, 20.0]

### 3. 注意力稀疏度 (attention_dropout)

**作用**: 防止系统过度关注某些细微的生克路径，导致旺衰判定被杂气干扰

**调优方法**: 调整 GAT 注意力网络的 dropout 参数

**默认值**: 0.1

**调优范围**: [0.0, 0.5]

---

## 🔧 参数敏感度分析

### 运行分析脚本

```bash
python3 scripts/strength_parameter_sensitivity_analysis.py --output reports/
```

### 分析报告

脚本会生成：
1. **JSON 报告**: `reports/strength_parameter_sensitivity_report.json`
2. **可视化图表**: `reports/strength_parameter_sensitivity_curves.png`

### 报告内容

- 每个参数的敏感度曲线
- 最优参数值
- 敏感度范围
- 调优建议

---

## 📈 使用示例

### 完整工作流

```python
from core.strength_probability_wave import StrengthProbabilityWave
from core.gat_strength_attention import GATStrengthAttention
from core.bayesian_strength_calibration import BayesianStrengthCalibration

# 1. 计算旺衰概率（使用概率波）
strength_prob, details = StrengthProbabilityWave.calculate_strength_probability(
    energy_sum=3.5,
    threshold_center=3.0,
    phase_transition_width=10.0
)

# 2. 计算动态权重（使用 GAT 注意力）
gat_attention = GATStrengthAttention(dropout=0.1)
pattern_type = gat_attention.identify_pattern_type(bazi, day_master)
weights = gat_attention.calculate_dynamic_strength_weights(
    bazi_features={'has_vault': True},
    pattern_type=pattern_type
)

# 3. 计算置信度（使用贝叶斯校准）
confidence = BayesianStrengthCalibration.calculate_strength_confidence(
    strength_probability=strength_prob,
    energy_sum=3.5,
    threshold_center=3.0
)

# 4. 如果置信度低，自动调整阈值
if confidence < 0.7:
    new_threshold = BayesianStrengthCalibration.auto_adjust_threshold_center(
        case_results=[...],
        current_threshold=3.0
    )
```

---

## 🎨 总结

**V10.0 已经把"地鼠机"变成了一个"调音台"。**

- ❌ 不再需要暴力修改"水克火 = 0.5"
- ✅ 而是调整"在身弱背景下，水对火的抑制斜率"
- ✅ 这种**非线性的、带上下文的**调优，能让你在不破坏 A 案例的前提下，精准修复 B 案例

---

## 📚 参考文档

- [V10.0 算法总纲](./V10_ALGORITHM_CONSTITUTION.md)
- [V10.0 元学习调优体系](./V10_META_LEARNING_OPTIMIZATION.md)
- [V10.0 完整技术规范](./V10_COMPLETE_TECHNICAL_SPEC.md)

---

**文档维护**: Bazi Predict Team  
**最后更新**: 2025-12-17  
**状态**: ✅ 正式发布

