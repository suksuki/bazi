# V10.0 算法总纲 (Algorithm Constitution V10.0)

**版本**: V10.0  
**发布日期**: 2025-12-17  
**状态**: ✅ 正式发布

---

## 📋 目录

1. [概述](#概述)
2. [核心架构](#核心架构)
3. [五大核心模块](#五大核心模块)
4. [数学基础](#数学基础)
5. [MCP 协议](#mcp-协议)
6. [实现细节](#实现细节)
7. [性能优化](#性能优化)
8. [验证与测试](#验证与测试)

---

## 概述

**Antigravity V10.0** 是八字预测系统的重大算法飞跃，从简单的逻辑推导完全进化为基于**非线性动力学**、**图神经网络**和**量子概率**的高维物理仿真系统。

### 核心突破

1. **从线性到非线性**: 使用 Soft-thresholding 替代硬编码 `if/else`
2. **从静态到动态**: GAT 网络提供动态注意力权重
3. **从确定到概率**: 贝叶斯推理提供不确定性量化
4. **从短期到长期**: Transformer 捕捉长程依赖
5. **从固定到自适应**: RLHF 实现参数自动调优

### 设计原则

- **物理建模**: 遵循矢量场、波动力学、流体力学原理
- **可配置性**: 所有参数通过配置文件管理
- **可验证性**: 提供回归验证接口
- **可扩展性**: 模块化设计，易于扩展

---

## 核心架构

### 三阶段架构 (Three-Phase Architecture)

V10.0 保持了 GraphNetworkEngine 的三阶段架构，但每个阶段都得到了增强：

```
Phase 1: 节点初始化 (Node Initialization)
  ↓
Phase 2: 邻接矩阵构建 (Adjacency Matrix Construction)
  ↓
Phase 3: 能量传播 (Energy Propagation)
```

#### Phase 1: 节点初始化

**传统方式**:
```python
H^(0) = [节点基础能量]
```

**V10.0 增强**:
```python
H^(0) = [节点基础能量] × [GAT 注意力权重] × [时空修正]
```

#### Phase 2: 邻接矩阵构建

**传统方式**:
```python
A = [固定关系矩阵]
```

**V10.0 增强**:
```python
A = GAT_Attention(H^(0))  # 动态注意力矩阵
```

#### Phase 3: 能量传播

**传统方式**:
```python
H^(t+1) = A × H^(t)
```

**V10.0 增强**:
```python
H^(t+1) = Transformer_Encode(A × H^(t), temporal_context)
```

---

## 五大核心模块

### 1. GAT (Graph Attention Networks) - 动态注意力机制

#### 核心思想

使用**多头注意力机制**替代固定的邻接矩阵，让网络自动学习节点间的关系强度。

#### 数学公式

**注意力权重计算**:
```
α_ij = softmax(LeakyReLU(a^T [W h_i || W h_j]))
```

其中：
- `h_i, h_j`: 节点 i 和 j 的特征向量
- `W`: 可学习的权重矩阵
- `a`: 注意力向量
- `||`: 向量拼接

**多头注意力**:
```
h'_i = ||_k=1^K σ(Σ_j∈N_i α_ij^k W^k h_j)
```

其中：
- `K`: 注意力头数（默认 4）
- `σ`: 激活函数（ELU）

#### 实现细节

```python
class GATAdjacencyBuilder:
    def build_adjacency(self, nodes, num_heads=4):
        # 计算注意力权重
        attention_weights = self.multi_head_attention(nodes, num_heads)
        # 构建动态邻接矩阵
        adjacency = self.apply_attention(attention_weights)
        return adjacency
```

#### 优势

- ✅ 自动识别关键节点（如财库节点）
- ✅ 动态调整关系强度
- ✅ 捕捉复杂的节点交互模式

---

### 2. 非线性激活 (Non-linear Soft-thresholding) - 相变仿真

#### 核心思想

使用**Softplus** 和 **Sigmoid** 函数替代硬编码的 `if/else` 判断，模拟能量在临界点处的"相变"过程。

#### 数学公式

**Softplus 函数**:
```
softplus(x, β) = log(1 + exp(βx))
```

**Sigmoid 函数**:
```
sigmoid(x, k) = 1 / (1 + exp(-kx))
```

**财库开启能量计算**:
```
# 1. 身强激活因子
strength_activation = softplus(strength_normalized - threshold, β=10.0)

# 2. 冲的强度因子
clash_factor = sigmoid(clash_intensity, k=5.0)

# 3. 三刑效应因子
trine_factor = 1 + trine_effect × trine_boost

# 4. 相变能量
phase_transition_energy = base_bonus × strength_activation × clash_factor × trine_factor

# 5. 量子隧穿概率
tunneling_probability = sigmoid((strength_normalized - threshold) × β/2, k=1.0) × tunneling_factor

# 6. 最终能量
if strength_normalized > threshold:
    final_energy = phase_transition_energy + base_bonus × tunneling_probability
else:
    if tunneling_probability > 0.01:
        final_energy = base_bonus × tunneling_probability × clash_factor × trine_factor
    else:
        final_energy = base_penalty × (1 - strength_normalized) × clash_factor × trine_factor
```

#### 参数说明

- `strength_threshold`: 身强阈值（默认 0.5）
- `strength_beta`: Softplus 的陡峭度（默认 10.0）
- `clash_k`: Sigmoid 的陡峭度（默认 5.0）
- `trine_boost`: 三刑增强系数（默认 0.3）
- `tunneling_factor`: 隧穿概率系数（默认 0.1）

#### 优势

- ✅ 平滑的能量过渡（无硬截断）
- ✅ 模拟量子隧穿效应
- ✅ 可微分的激活函数（支持梯度下降）

---

### 3. Transformer 时序建模 - 长程依赖捕捉

#### 核心思想

使用 **Transformer 架构**捕捉时间序列中的长程依赖，理解能量在时间维度上的积累和释放。

#### 数学公式

**位置编码**:
```
PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
```

**多头自注意力**:
```
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) W^O
head_i = Attention(QW_i^Q, KW_i^K, VW_i^V)
```

**前馈网络**:
```
FFN(x) = max(0, xW_1 + b_1)W_2 + b_2
```

#### 实现细节

```python
class TransformerTemporal:
    def encode_temporal_features(self, timeline_data, max_length=100):
        # 位置编码
        pos_encoding = self.positional_encoding(max_length)
        # 多头自注意力
        attention_output = self.multi_head_attention(timeline_data, pos_encoding)
        # 前馈网络
        output = self.feed_forward(attention_output)
        return output
```

#### 优势

- ✅ 捕捉长程依赖（54年能量积累）
- ✅ 并行计算（比 RNN 更快）
- ✅ 位置信息编码（理解时间顺序）

---

### 4. 贝叶斯推理 (Bayesian Inference) - 概率分布生成

#### 核心思想

使用**贝叶斯推理**和**蒙特卡洛模拟**生成概率分布，而非单一确定值。

#### 数学公式

**贝叶斯定理**:
```
P(θ|D) = P(D|θ) × P(θ) / P(D)
```

**置信区间计算**:
```
CI = [μ - z_α/2 × σ, μ + z_α/2 × σ]
```

其中：
- `μ`: 均值
- `σ`: 标准差
- `z_α/2`: 标准正态分布的分位数

**蒙特卡洛模拟**:
```
for i in range(n_samples):
    θ_i ~ P(θ|D)
    y_i = f(θ_i)
    
mean = Σ y_i / n_samples
std = sqrt(Σ (y_i - mean)^2 / (n_samples - 1))
```

#### 不确定性因子

```python
uncertainty_factors = {
    'strength_uncertainty': 基于身强分数的方差,
    'clash_uncertainty': 基于冲的强度的方差,
    'trine_uncertainty': 基于三刑效应的方差,
    'mediation_uncertainty': 基于调和的方差,
    'help_uncertainty': 基于帮扶的方差,
    'base_uncertainty': 基础不确定性
}
```

#### 实现细节

```python
class BayesianInference:
    @staticmethod
    def monte_carlo_simulation(base_estimate, parameter_ranges, n_samples=1000):
        samples = []
        for _ in range(n_samples):
            # 采样参数
            params = sample_from_ranges(parameter_ranges)
            # 计算预测值
            prediction = calculate_prediction(base_estimate, params)
            samples.append(prediction)
        
        # 计算统计量
        mean = np.mean(samples)
        std = np.std(samples)
        percentiles = np.percentile(samples, [5, 25, 50, 75, 95])
        
        return {
            'mean': mean,
            'std': std,
            'percentiles': {
                'p5': percentiles[0],
                'p25': percentiles[1],
                'p50': percentiles[2],
                'p75': percentiles[3],
                'p95': percentiles[4]
            }
        }
```

#### 优势

- ✅ 量化不确定性
- ✅ 提供置信区间
- ✅ 支持风险分析

---

### 5. RLHF (Reinforcement Learning from Human Feedback) - 自适应调优

#### 核心思想

使用**强化学习**根据真实反馈自动调优参数，实现系统的持续进化。

#### 数学公式

**奖励函数**:
```
R(θ) = -Σ |predicted_i - real_i| / n
```

**策略梯度**:
```
∇_θ J(θ) = E[∇_θ log π_θ(a|s) × R(θ)]
```

**参数更新**:
```
θ_new = θ_old + α × ∇_θ J(θ)
```

#### 实现细节

```python
class RLHFTrainer:
    def train(self, feedback_data, current_params):
        # 计算奖励
        reward = self.calculate_reward(feedback_data, current_params)
        
        # 计算梯度
        gradient = self.compute_gradient(reward, current_params)
        
        # 更新参数
        new_params = current_params + self.learning_rate * gradient
        
        return new_params
```

#### 优势

- ✅ 自动参数调优
- ✅ 持续学习改进
- ✅ 适应新案例

---

## 数学基础

### 矢量场模型

八字中的五行能量被建模为**矢量场**：

```
E(x, y, z, t) = Σ_i E_i × exp(-|r - r_i|^2 / σ^2)
```

其中：
- `E_i`: 节点 i 的能量
- `r_i`: 节点 i 的位置
- `σ`: 能量衰减系数

### 波动力学模型

天干被建模为**波形态**：

```
ψ(t) = A × exp(i(kx - ωt + φ))
```

其中：
- `A`: 振幅（能量强度）
- `k`: 波数（频率）
- `ω`: 角频率
- `φ`: 相位

### 流体力学模型

地支被建模为**场域环境**：

```
∇·v = 0  (连续性方程)
ρ(∂v/∂t + v·∇v) = -∇p + μ∇²v  (Navier-Stokes 方程)
```

---

## MCP 协议

### Model Context Protocol (MCP) 概述

**MCP** 是 V10.0 引入的上下文管理协议，用于在推演过程中注入"地面真值"上下文，实现更精准的预测。

### MCP 核心组件

#### 1. Context Injection (上下文注入)

**目的**: 在推演开始前注入案例的真实背景信息。

**数据结构**:
```json
{
  "case_id": "JASON_D_T1961_1010",
  "ground_truth": {
    "strength": "Special_Strong",
    "wealth_vaults": ["丑", "辰", "戌"],
    "historical_events": [...]
  },
  "context_features": {
    "vault_count": 3,
    "vault_density": 0.75,
    "attention_weights": {...}
  }
}
```

#### 2. Temporal Context (时空上下文)

**目的**: 捕捉时间序列中的长程依赖。

**数据结构**:
```json
{
  "timeline": [
    {"year": 1961, "energy": 50, "state": "accumulation"},
    {"year": 1971, "energy": 55, "state": "accumulation"},
    ...
    {"year": 2015, "energy": 130, "state": "critical"}
  ],
  "temporal_features": {
    "accumulation_period": 54,
    "pressure_gradient": 0.8,
    "critical_point": 2015
  }
}
```

#### 3. Probabilistic Context (概率上下文)

**目的**: 提供不确定性量化信息。

**数据结构**:
```json
{
  "distribution": {
    "mean": 100.0,
    "std": 10.2,
    "percentiles": {
      "p25": 92.7,
      "p50": 99.7,
      "p75": 106.9
    }
  },
  "uncertainty_factors": {
    "strength_uncertainty": 5.0,
    "clash_uncertainty": 0.0,
    "trine_uncertainty": 0.0
  }
}
```

#### 4. Feedback Context (反馈上下文)

**目的**: 存储真实事件反馈，用于 RLHF 调优。

**数据结构**:
```json
{
  "feedback_events": [
    {
      "year": 2015,
      "real_value": 100.0,
      "predicted_value": 100.0,
      "error": 0.0,
      "is_correct": true
    }
  ],
  "recommendations": [
    "建议调整 breakPenalty 参数",
    "优化 controlImpact 参数"
  ]
}
```

### MCP 工作流程

```
1. Context Injection
   ↓
2. Temporal Context Encoding
   ↓
3. Probabilistic Context Generation
   ↓
4. Feedback Context Collection
   ↓
5. RLHF Parameter Tuning
```

---

## 实现细节

### 配置文件结构

```json
{
  "use_gat": true,
  "use_transformer": true,
  "use_rlhf": true,
  "probabilistic_energy": {
    "use_probabilistic_energy": true,
    "n_samples": 1000,
    "confidence_level": 0.95
  },
  "nonlinear": {
    "strength_threshold": 0.5,
    "strength_beta": 10.0,
    "clash_k": 5.0,
    "trine_boost": 0.3,
    "tunneling_factor": 0.1
  },
  "gat": {
    "num_heads": 4,
    "hidden_dim": 64,
    "dropout": 0.1
  },
  "transformer": {
    "d_model": 128,
    "n_heads": 8,
    "n_layers": 6,
    "dropout": 0.1
  },
  "rlhf": {
    "learning_rate": 0.001,
    "reward_scale": 1.0,
    "update_frequency": 10
  }
}
```

### 核心类结构

```python
class GraphNetworkEngine:
    def __init__(self, config):
        self.config = config
        self.gat_builder = GATAdjacencyBuilder() if config['use_gat'] else None
        self.transformer = TransformerTemporal() if config['use_transformer'] else None
        self.bayesian = BayesianInference()
        self.rlhf_trainer = RLHFTrainer() if config['use_rlhf'] else None
    
    def analyze(self, bazi, day_master, ...):
        # Phase 1: 节点初始化
        nodes = self.initialize_nodes(bazi, day_master, ...)
        
        # Phase 2: 邻接矩阵构建（GAT）
        if self.gat_builder:
            adjacency = self.gat_builder.build_adjacency(nodes)
        else:
            adjacency = self.build_fixed_adjacency(nodes)
        
        # Phase 3: 能量传播
        energy = self.propagate_energy(nodes, adjacency)
        
        return energy
    
    def calculate_wealth_index(self, ...):
        # 计算基础财富指数
        base_index = self._calculate_base_wealth(...)
        
        # 非线性激活
        if self.config['nonlinear']:
            index = self._apply_nonlinear_activation(base_index, ...)
        
        # 贝叶斯推理
        if self.config['probabilistic_energy']['use_probabilistic_energy']:
            distribution = self.bayesian.monte_carlo_simulation(...)
            return {
                'wealth_index': distribution['mean'],
                'wealth_distribution': distribution
            }
        
        return base_index
```

---

## 性能优化

### 1. 缓存机制

- 节点初始化结果缓存
- 邻接矩阵缓存
- 概率分布结果缓存

### 2. 并行计算

- GAT 多头注意力并行计算
- Transformer 自注意力并行计算
- 蒙特卡洛模拟并行采样

### 3. 延迟初始化

- 引擎懒加载
- 模块按需初始化
- 配置延迟加载

---

## 验证与测试

### 回归测试

```python
def test_v10_regression():
    # 加载历史案例
    cases = load_calibration_cases()
    
    # 推演所有案例
    results = []
    for case in cases:
        result = engine.run_full_inference(case.id)
        results.append(result)
    
    # 计算命中率
    hit_rate = calculate_hit_rate(results)
    
    # 验证阈值
    assert hit_rate >= 0.5, f"命中率 {hit_rate} 低于阈值 0.5"
```

### 单元测试

- GAT 注意力权重计算
- 非线性激活函数
- Transformer 编码
- 贝叶斯推理
- RLHF 参数更新

---

## 版本历史

### V10.0 (2025-12-17)

- ✅ 引入 GAT 动态注意力机制
- ✅ 实现非线性 Soft-thresholding
- ✅ 集成 Transformer 时序建模
- ✅ 添加贝叶斯概率分布
- ✅ 实现 RLHF 自适应调优
- ✅ 建立 MCP 协议

### V9.3 (之前版本)

- GraphNetworkEngine 基础架构
- 固定邻接矩阵
- 硬编码判断逻辑
- 单一确定值输出

---

## 参考文档

- [核心算法内核 V9](./CORE_ALGORITHM_KERNEL_V9.md)
- [算法总纲 V2.5](./ALGORITHM_CONSTITUTION_v2.5.md)
- [V10.0 Jason D 推演报告](./V10_JASON_D_2015_ENERGY_BURST_ANALYSIS.md)
- [V10.0 优化建议](./BAZI_PREDICTION_SYSTEM_COMPLETE_REVIEW.md)

---

**文档维护**: Bazi Predict Team  
**最后更新**: 2025-12-17  
**状态**: ✅ 正式发布

