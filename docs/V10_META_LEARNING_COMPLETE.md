# V10.0 元学习调优体系完整文档

**版本**: V10.0  
**发布日期**: 2025-12-17  
**状态**: ✅ 正式发布

---

## 📋 概述

V10.0 引入了**元学习 (Meta-Learning)** 调优体系，从传统的线性调优（梯度下降）进化为智能参数优化系统，能够处理高维、非凸的能量场变化。

### 核心突破

1. **贝叶斯优化**: 使用高斯过程代理模型和期望改进来寻找全局最优解
2. **超参数敏感度分析**: 分析激活函数参数对预测结果的影响
3. **对比学习 RLHF**: 提供"路径 A vs 路径 B"的对比，而非单一反馈
4. **Transformer 位置编码调优**: 平衡"远期积压能量"与"近期突发能量"
5. **GAT 路径过滤**: 过滤无效注意力路径，聚焦核心路径

---

## 🎯 五大调优策略详解

### 1. 贝叶斯优化 (Bayesian Optimization)

#### 问题背景

在 V10.0 非线性架构下，损失函数极其复杂（非凸、高维），传统的梯度下降无法有效优化。

#### 解决方案

使用**高斯过程（Gaussian Process）**作为代理模型，通过**期望改进（Expected Improvement）**来智能选择下一个采样点。

#### 数学原理

**高斯过程**:
```
f(x) ~ GP(μ(x), k(x, x'))
```

**期望改进**:
```
EI(x) = σ(x) [z Φ(z) + φ(z)]
z = (f_min - μ(x)) / σ(x)
```

#### 实现

```python
from core.bayesian_optimization import BayesianOptimizer

# 定义参数边界
parameter_bounds = {
    'strength_beta': (5.0, 15.0),      # Softplus 的 β 参数
    'clash_k': (3.0, 7.0),            # Sigmoid 的 k 参数
    'trine_boost': (0.1, 0.5),        # 三刑增强系数
    'tunneling_factor': (0.05, 0.2)   # 隧穿概率系数
}

# 创建优化器
optimizer = BayesianOptimizer(
    parameter_bounds=parameter_bounds,
    acquisition_func='ei',  # 期望改进
    n_initial_samples=10
)

# 执行优化
optimal_params = optimizer.optimize(objective_func, n_iterations=50)
```

---

### 2. 超参数敏感度分析

#### 问题背景

非线性模型（如 Sigmoid 和 Softplus）对初始参数极度敏感。需要识别哪些参数对预测结果影响最大。

#### 解决方案

固定其他参数，只改变目标参数，计算损失函数的变化率（敏感度）。

#### 数学原理

**敏感度定义**:
```
S_i = ∂L/∂θ_i ≈ (L(θ_i + ε) - L(θ_i - ε)) / (2ε)
```

#### 实现

```python
from core.bayesian_optimization import HyperparameterSensitivityAnalyzer

# 创建分析器
analyzer = HyperparameterSensitivityAnalyzer(base_params)

# 分析所有参数
parameter_ranges = {
    'strength_beta': np.linspace(5.0, 15.0, 20),
    'clash_k': np.linspace(3.0, 7.0, 20),
    'trine_boost': np.linspace(0.1, 0.5, 20),
    'tunneling_factor': np.linspace(0.05, 0.2, 20)
}

results = analyzer.analyze_all(objective_func, parameter_ranges)

# 获取最优值
for param_name, result in results.items():
    print(f"{param_name}: 最优值 = {result['optimal_value']:.4f}")
```

---

### 3. 对比学习 RLHF

#### 问题背景

传统的 RLHF 只告诉系统"预测错了"，无法学习复杂的能量传播模式。

#### 解决方案

提供"路径 A vs 路径 B"的对比，使用 **Bradley-Terry 模型**学习偏好。

#### 数学原理

**Bradley-Terry 模型**:
```
P(A > B) = exp(r_A) / (exp(r_A) + exp(r_B))
```

**对比学习损失**:
```
L = -log(P(preferred_path))
```

#### 实现

```python
from core.contrastive_rlhf import ContrastiveRLHFTrainer, ContrastiveRewardModel

# 创建奖励模型
reward_model = ContrastiveRewardModel()

# 创建训练器
trainer = ContrastiveRLHFTrainer(reward_model)

# 生成对比学习对
pairs = trainer.generate_contrastive_pairs(
    case_data=case_data,
    engine_a=engine_a,  # 不同参数配置
    engine_b=engine_b,
    target_years=[1999, 2015, 2021]
)

# 训练奖励模型
reward_model.train(pairs, n_epochs=100)
```

---

### 4. Transformer 位置编码调优

#### 问题背景

系统现在具备捕捉 54 年长程依赖的能力，需要平衡"远期积压能量"与"近期突发能量"的权重。

#### 解决方案

调整 Transformer 的位置编码参数（`position_scale` 和 `decay_factor`），优化多尺度时序融合权重。

#### 数学原理

**位置编码**:
```
PE(pos, 2i) = sin(pos × decay_factor / (10000^(2i/d_model)))
```

**多尺度时序融合**:
```
fused = w_short × f_short + w_medium × f_medium + w_long × f_long
```

#### 实现

```python
from core.transformer_position_tuning import PositionalEncodingTuner, MultiScaleTemporalFusion

# 位置编码调优
tuner = PositionalEncodingTuner(d_model=128, max_length=100)
optimal_params = tuner.tune_for_long_range_dependency(timeline_data, objective)

# 多尺度时序融合
fusion = MultiScaleTemporalFusion()
optimal_weights = fusion.optimize_scale_weights(
    timeline_data=timeline_data,
    ground_truth=ground_truth,
    objective_func=objective
)
```

---

### 5. GAT 路径过滤

#### 问题背景

GAT 动态注意力机制有时会捕捉到太多微弱的能量干扰（熵），需要聚焦核心路径。

#### 解决方案

通过调整路径过滤阈值和系统熵参数，过滤无效注意力路径。

#### 数学原理

**路径强度**:
```
strength(path_i→j) = attention_weight(i, j) × energy_flow(i, j)
```

**路径过滤**:
```
filtered_paths = {path | strength(path) >= threshold}
```

**系统熵控制**:
```
H = -Σ α_ij log(α_ij)
```

#### 实现

```python
from core.gat_path_filter import GATPathFilter, SystemEntropyController

# 路径过滤
filter = GATPathFilter(threshold=0.1)
filtered_weights = filter.filter_paths(attention_weights, energy_paths)

# 优化阈值
optimal_threshold = filter.optimize_threshold(
    attention_weights=attention_weights,
    energy_paths=energy_paths,
    objective_func=objective
)

# 系统熵控制
entropy_controller = SystemEntropyController(base_entropy=0.1)
filtered_by_entropy = entropy_controller.filter_by_entropy(
    attention_weights=attention_weights,
    max_entropy=2.0
)
```

---

## 🔄 完整元学习工作流

### 工作流步骤

```
1. 识别高不确定性、高误差的年份
   ↓
2. 超参数敏感度分析
   ↓
3. 贝叶斯优化
   ↓
4. 对比学习 RLHF
   ↓
5. Transformer 位置编码调优
   ↓
6. GAT 路径过滤
   ↓
7. 验证与迭代
```

### 实现示例

```python
# 完整的元学习调优流程
from core.bayesian_optimization import BayesianOptimizer, HyperparameterSensitivityAnalyzer
from core.contrastive_rlhf import ContrastiveRLHFTrainer
from core.transformer_position_tuning import PositionalEncodingTuner
from core.gat_path_filter import GATPathFilter

# 1. 贝叶斯优化
optimizer = BayesianOptimizer(parameter_bounds)
optimal_params = optimizer.optimize(objective_func, n_iterations=50)

# 2. 敏感度分析
analyzer = HyperparameterSensitivityAnalyzer(optimal_params)
sensitivity_results = analyzer.analyze_all(objective_func, parameter_ranges)

# 3. 对比学习 RLHF
trainer = ContrastiveRLHFTrainer(reward_model)
pairs = trainer.generate_contrastive_pairs(case_data, engine_a, engine_b, years)
reward_model.train(pairs, n_epochs=100)

# 4. Transformer 位置编码调优
tuner = PositionalEncodingTuner()
position_params = tuner.tune_for_long_range_dependency(timeline_data, objective)

# 5. GAT 路径过滤
filter = GATPathFilter()
optimal_threshold = filter.optimize_threshold(attention_weights, energy_paths, objective)

# 6. 综合结果
final_params = {
    **optimal_params,
    **position_params,
    'gat_threshold': optimal_threshold
}
```

---

## 📊 案例：Jason D 1999年误差修正

### 问题描述

- **真实值**: 50.0
- **预测值**: -30.0
- **误差**: 80.0
- **目标**: 通过贝叶斯优化调整非线性参数，使预测更准确

### 优化脚本

```bash
# 运行贝叶斯优化
python3 scripts/bayesian_hyperparameter_tuning_jason_d_1999.py \
    --iterations 50 \
    --sensitivity \
    --output reports/jason_d_1999_optimization.json
```

### 优化参数

```json
{
  "parameter_bounds": {
    "strength_beta": [5.0, 15.0],
    "clash_k": [3.0, 7.0],
    "trine_boost": [0.1, 0.5],
    "tunneling_factor": [0.05, 0.2]
  }
}
```

### 参数映射

- `strength_beta` → `nonlinear.scale` (Softplus 的缩放因子)
- `clash_k` → `nonlinear.steepness` (Sigmoid 的陡峭度)
- `trine_boost` → `nonlinear.trine_boost` (三刑增强系数)
- `tunneling_factor` → `nonlinear.tunneling_factor` (隧穿概率系数)

---

## 📚 参考文档

- [V10.0 元学习调优体系](./V10_META_LEARNING_OPTIMIZATION.md)
- [V10.0 元学习工作流](./V10_META_LEARNING_WORKFLOW.md)
- [V10.0 算法总纲](./V10_ALGORITHM_CONSTITUTION.md)
- [V10.0 完整技术规范](./V10_COMPLETE_TECHNICAL_SPEC.md)

---

**文档维护**: Bazi Predict Team  
**最后更新**: 2025-12-17  
**状态**: ✅ 正式发布

