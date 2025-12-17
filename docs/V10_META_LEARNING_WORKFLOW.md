# V10.0 元学习调优工作流 (Meta-Learning Workflow)

**版本**: V10.0  
**发布日期**: 2025-12-17  
**状态**: ✅ 正式发布

---

## 🎯 快速开始

### 针对 Jason D 1999 年误差修正

```bash
# 运行贝叶斯超参数优化
python3 scripts/bayesian_hyperparameter_tuning_jason_d_1999.py \
    --iterations 50 \
    --sensitivity \
    --output reports/jason_d_1999_optimization.json
```

### 完整元学习工作流

```python
# 1. 识别高不确定性、高误差的年份
from core.bayesian_inference import BayesianInference

uncertainty = BayesianInference.estimate_uncertainty_factors(...)
high_uncertainty_years = [year for year, u in uncertainty.items() if u > threshold]

# 2. 超参数敏感度分析
from core.bayesian_optimization import HyperparameterSensitivityAnalyzer

analyzer = HyperparameterSensitivityAnalyzer(base_params)
results = analyzer.analyze_all(objective_func, parameter_ranges)

# 3. 贝叶斯优化
from core.bayesian_optimization import BayesianOptimizer

optimizer = BayesianOptimizer(parameter_bounds)
optimal_params = optimizer.optimize(objective_func, n_iterations=50)

# 4. 对比学习 RLHF
from core.contrastive_rlhf import ContrastiveRLHFTrainer

trainer = ContrastiveRLHFTrainer(reward_model)
pairs = trainer.generate_contrastive_pairs(case_data, engine_a, engine_b, years)
reward_model.train(pairs, n_epochs=100)

# 5. Transformer 位置编码调优
from core.transformer_position_tuning import PositionalEncodingTuner

tuner = PositionalEncodingTuner()
optimal_params = tuner.tune_for_long_range_dependency(timeline_data, objective)

# 6. GAT 路径过滤
from core.gat_path_filter import GATPathFilter

filter = GATPathFilter(threshold=0.1)
filtered_weights = filter.filter_paths(attention_weights, energy_paths)
```

---

## 📊 工作流图示

```
输入: 案例数据 + 真实事件
    ↓
[步骤1] 识别高不确定性年份
    ↓
[步骤2] 超参数敏感度分析
    ↓
[步骤3] 贝叶斯优化
    ↓
[步骤4] 对比学习 RLHF
    ↓
[步骤5] Transformer 位置编码调优
    ↓
[步骤6] GAT 路径过滤
    ↓
输出: 优化后的参数配置
```

---

## 🔧 配置参数

### 贝叶斯优化配置

```json
{
  "bayesian_optimization": {
    "n_initial_samples": 10,
    "n_iterations": 50,
    "acquisition_func": "ei",
    "kernel": "rbf",
    "length_scale": 1.0,
    "noise_level": 0.1
  }
}
```

### 对比学习 RLHF 配置

```json
{
  "contrastive_rlhf": {
    "hidden_dim": 64,
    "learning_rate": 0.001,
    "n_epochs": 100,
    "batch_size": 32
  }
}
```

### Transformer 位置编码配置

```json
{
  "transformer_tuning": {
    "position_scale_range": [1000, 100000],
    "decay_factor_range": [0.5, 1.5],
    "scale_weights": {
      "short_term": [0.1, 0.5],
      "medium_term": [0.2, 0.6],
      "long_term": [0.1, 0.5]
    }
  }
}
```

### GAT 路径过滤配置

```json
{
  "gat_filtering": {
    "threshold_range": [0.01, 0.5],
    "max_entropy": 2.0,
    "base_entropy": 0.1
  }
}
```

---

## 📝 使用示例

### 示例 1: Jason D 1999 年误差修正

```python
from scripts.bayesian_hyperparameter_tuning_jason_d_1999 import JasonD1999Optimizer

# 创建优化器
optimizer = JasonD1999Optimizer()

# 执行优化
optimal_params = optimizer.optimize(n_iterations=50)

# 敏感度分析
sensitivity_results = optimizer.sensitivity_analysis()

# 验证结果
final_error = abs(optimizer._get_prediction(optimal_params) - 50.0)
print(f"最终误差: {final_error:.2f}")
```

### 示例 2: 完整元学习工作流

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

## 🎓 关键概念

### 期望改进 (Expected Improvement)

期望改进是贝叶斯优化中的核心概念，用于选择下一个采样点：

```
EI(x) = σ(x) [z Φ(z) + φ(z)]
```

其中：
- `z = (f_min - μ(x)) / σ(x)`
- `f_min`: 当前最优值
- `μ(x)`: 预测均值
- `σ(x)`: 预测标准差

### 对比学习 (Contrastive Learning)

对比学习通过比较两条路径来学习偏好：

```
P(A > B) = exp(r_A) / (exp(r_A) + exp(r_B))
```

其中：
- `r_A, r_B`: 路径 A 和 B 的奖励值

### 路径熵 (Path Entropy)

路径熵用于衡量注意力路径的分散程度：

```
H = -Σ α_ij log(α_ij)
```

其中：
- `α_ij`: 路径 (i→j) 的注意力权重

---

## 📚 参考文档

- [V10.0 元学习调优体系](./V10_META_LEARNING_OPTIMIZATION.md)
- [V10.0 算法总纲](./V10_ALGORITHM_CONSTITUTION.md)
- [V10.0 完整技术规范](./V10_COMPLETE_TECHNICAL_SPEC.md)

---

**文档维护**: Bazi Predict Team  
**最后更新**: 2025-12-17  
**状态**: ✅ 正式发布

