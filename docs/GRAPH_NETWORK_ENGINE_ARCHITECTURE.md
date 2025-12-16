# 图网络引擎架构文档 (Graph Network Engine Architecture)

## 概述

`core/engine_graph.py` 实现了基于图神经网络（GNN）的八字算法引擎，严格遵循"物理初始化图网络"模型。

**核心思想**：将所有物理规则嵌入到图网络的初始化阶段，然后通过矩阵传播模拟能量流动。

---

## 架构设计

### 三阶段模型

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Node Initialization (节点初始化)               │
│ 应用所有基础物理规则，计算初始能量向量 H^(0)            │
│ - 月令权重 (pg_month)                                   │
│ - 通根加成 (root_w)                                     │
│ - 地理修正 (K_geo)                                      │
│ - 壳核模型 (Hidden Stems 60/30/10)                      │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Phase 2: Adjacency Matrix Construction (邻接矩阵构建)   │
│ 将生克制化转化为矩阵权重 A                              │
│ - 生 (Generation): 正权重 (0.6)                        │
│ - 克 (Control): 负权重 (-0.3)                          │
│ - 合 (Combination): 强正权重 (1.5)                     │
│ - 冲 (Clash): 强负权重 (-0.8)                          │
│ - 距离衰减 (Spatial Decay)                              │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Phase 3: Propagation (传播迭代)                         │
│ 模拟动态做功：H^(t+1) = damping * A * H^(t) + ...      │
│ - 能量从 Source 流向 Sink                               │
│ - Flow（流通）和 Blockage（阻滞）                       │
│ - 全局熵增（能量损耗）                                  │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 1: 节点初始化

### 节点结构

每个节点代表一个八字粒子（天干或地支），包含：

- **节点属性**：
  - `node_id`: 唯一标识（0-11）
  - `char`: 天干或地支字符
  - `node_type`: 'stem' 或 'branch'
  - `element`: 五行元素
  - `pillar_idx`: 所属柱的索引
  
- **能量属性**：
  - `initial_energy`: 初始能量（Phase 1 计算）
  - `current_energy`: 当前能量（Phase 3 传播后）

### 物理规则应用

#### 1. 月令权重 (Seasonality)

```python
if node.pillar_name == 'month':
    energy *= pillar_weights['month']  # 默认 1.2-1.8
```

**意义**：月令是热力学基准，对能量计算有决定性影响。

#### 2. 通根加成 (Rooting)

```python
if node.has_root:
    if node.is_same_pillar:
        energy *= same_pillar_bonus  # 自坐强根（默认 1.2）
    else:
        energy *= (1.0 + (root_weight - 1.0) * 0.5)  # 普通通根
```

**意义**：天干在地支藏干中出现时，能量增强。

#### 3. 地理修正 (Geography)

```python
if geo_modifiers and node.element in geo_modifiers:
    energy *= geo_modifiers[node.element]
```

**意义**：出生地影响五行能量基线。

#### 4. 壳核模型 (Shell-Core)

```python
# 地支的能量来自藏干的加权和
if node.node_type == 'branch':
    energy = BASE_SCORE * pillar_weight * sum(hidden_stems_energy.values())
```

**意义**：地支是"壳"，藏干是"核"，能量由主/中/余气按 60/30/10 比率加权。

---

## Phase 2: 邻接矩阵构建

### 矩阵定义

邻接矩阵 `A[i][j]` 表示节点 `j` 对节点 `i` 的影响：

- **正数**：增强影响（生、合）
- **负数**：削弱影响（克、冲）
- **零**：无直接关系

### 权重计算规则

#### 1. 五行生克

```python
# 生（Generation）
if GENERATION[source_element] == target_element:
    A[i][j] = 0.6 * generation_efficiency  # 正权重

# 克（Control）
if CONTROL[source_element] == target_element:
    A[i][j] = -0.3 * control_impact  # 负权重
```

#### 2. 天干五合

```python
if (stem1, stem2) in STEM_COMBINATIONS:
    A[i][j] = 1.5 * bonus  # 强正连接
```

#### 3. 地支合局

- **六合**：`A[i][j] = six_harmony / 10.0`
- **三合**：`A[i][j] = trine_bonus / 10.0`

#### 4. 冲（Clash）

```python
if (branch1, branch2) in BRANCH_CLASHES:
    A[i][j] = clash_score / 10.0 * clash_damping  # 强负权重
```

#### 5. 距离衰减

```python
distance = abs(pillar_i - pillar_j)
if distance == 1:
    A[i][j] *= spatial_decay['gap1']  # 0.6
elif distance >= 2:
    A[i][j] *= spatial_decay['gap2']  # 0.3
```

**意义**：距离越远，影响越弱（符合物理直觉）。

---

## Phase 3: 传播迭代

### 迭代公式

```
H^(t+1) = damping * A * H^(t) + (1-damping) * H^(0)
```

### 参数说明

- **damping** (0.9)：阻尼系数，防止发散
- **A**：邻接矩阵
- **H^(0)**：初始能量向量（保持作为基础）

### 能量损耗（熵增）

```python
H *= (1.0 - global_entropy)  # 默认 0.05 (5%损耗)
```

**意义**：每轮迭代都有能量损耗，模拟系统的不可逆性。

### 物理约束

```python
H = np.maximum(H, 0.0)  # 确保能量非负
```

**意义**：能量不能为负（物理约束）。

---

## 关键优势

### 1. 物理规则完整保留

所有基础算法（月令、通根、壳核等）都在 Phase 1 初始化时应用，**不会丢失**。

### 2. 动态做功模拟

Phase 3 的传播迭代模拟了能量的**动态流动和相互作用**，这是传统算法难以实现的。

### 3. 可扩展性

矩阵模型可以轻松添加新的交互规则，只需修改邻接矩阵的构建逻辑。

### 4. 数学严谨性

使用矩阵运算，确保了计算的**数学严谨性**和**可优化性**。

---

## 使用示例

```python
from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS

# 初始化引擎
engine = GraphNetworkEngine(config=DEFAULT_FULL_ALGO_PARAMS)

# 执行分析
result = engine.analyze(
    bazi=['甲子', '丙午', '辛卯', '壬辰'],
    day_master='辛',
    luck_pillar='癸卯',
    year_pillar='甲辰',
    geo_modifiers={'wood': 1.1, 'fire': 1.05}  # 地理修正
)

# 获取结果
print(f"初始能量: {result['initial_energy']}")
print(f"最终能量: {result['final_energy']}")
print(f"宏观得分: {result['domain_scores']}")
```

---

## 与现有引擎的关系

### 兼容性

- **向后兼容**：可以作为 `EngineV91` 的替代品
- **参数兼容**：使用相同的 `DEFAULT_FULL_ALGO_PARAMS` 配置结构
- **接口兼容**：提供相同的 `analyze()` 接口

### 性能考虑

- **计算复杂度**：O(N² × iterations)，其中 N=12（节点数），iterations=10
- **内存占用**：需要存储 12×12 的邻接矩阵，内存占用较小

---

## 未来改进方向

1. **三合局完整检测**：当前实现简化了三合检测，需要完整的三节点组合逻辑
2. **高级交互规则**：刑、害、墓库等复杂交互的矩阵表示
3. **自适应迭代**：根据收敛情况自动调整迭代次数
4. **GPU 加速**：利用 GPU 加速矩阵运算

---

**文档版本**: V1.0  
**最后更新**: 2025-01-16

