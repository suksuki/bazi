🏛️ QGA 正向拟合与建模架构规范 (FDS-ARCHITECTURE-V3.0)
—— 理论框架、物理公理与数据格式规范 ——

**版本**: V3.0 (Precision Physics & Statistical Manifolds)
**修订**: Genesis Protocol, Safety Protocols Injection & Metadata Enforcement
**生效日期**: 2025-12-31
**状态**: ENFORCED (强制执行)
**性质**: 架构与理论规范 (Architecture & Theory Specification)

> **关联文档**: 本架构规范必须与 `FDS_SOP_v3.0.md` (标准操作程序) 配合使用。
> 本规范定义"是什么"和"为什么"，SOP规范定义"怎么做"。

---

## 一、 建模核心哲学 (The Soul)

### 1.1 物理本质

八字格局不是高维空间中的一个"点"，而是一个具有特定形状和概率分布的 **"统计流形" (Statistical Manifold)**。

**物理意义**:
- 每个格局在5D命运张量空间中占据一个概率分布区域
- 格局的边界由协方差矩阵 $\Sigma$ 定义
- 格局的中心由均值向量 $\mu$ 定义

**数学模型**:
- 格局 $P$ 在5D空间中的分布: $P \sim \mathcal{N}(\mu, \Sigma)$
- $\mu \in \mathbb{R}^5$: 均值向量（格局中心）
- $\Sigma \in \mathbb{R}^{5 \times 5}$: 协方差矩阵（格局形状）

### 1.2 识别标准

采用矢量场 (Vector Field) + 概率云 (Probability Cloud) 的双重验证模型，通过方向、位置、能量三重门控判定入格程度。

**三重门控机制**:
1. **方向门控**: 通过矢量场验证样本的运动方向是否符合格局特征
2. **位置门控**: 通过概率云验证样本在5D空间中的位置是否在格局流形内
3. **能量门控**: 通过能量阈值验证样本的能量强度是否符合格局要求

#### 1.2.1 物理判定公理化 (Physics Recognition Axiom)

**识别判定必须从基于圆球的欧氏距离进化为基于概率包络的马氏距离 (Mahalanobis Distance)**。

**判定标准定义**:

样本被判定为"入格"，当且仅当其5D张量 $T_{fate}$ 到格局中心 $\mu$ 的马氏距离 $D_M$ 小于阈值 $\theta$：

$$
D_M = \sqrt{(T_{fate} - \mu)^T \Sigma^{-1} (T_{fate} - \mu)} < \theta
$$

其中：
- $T_{fate} \in \mathbb{R}^5$: 样本的5D张量
- $\mu \in \mathbb{R}^5$: 格局的均值向量（流形中心）
- $\Sigma \in \mathbb{R}^{5 \times 5}$: 格局的协方差矩阵（流形形状）

**物理意义**:
- 马氏距离考虑了维度间的相关性（协方差），比欧氏距离更精确
- 协方差矩阵 $\Sigma$ 定义了格局在5D空间中的"椭球形状"，而非简单的"圆球"
- 阈值 $\theta$ 通常从配置读取（`@config.physics.thresholds.mahalanobis`），标准值约为3.0（对应5维正态分布的95%置信水平）

#### 1.2.2 双轨识别公理 (Dual-Track Recognition Axiom)

**公理定义**: 格局的成立由"逻辑硬门槛"与"物理软流形"共同定义，形成双轨识别体系。

**真理源优先级**:
- **第一优先级**: 以 **"物理张量 $T_{fate}$ 在流形中心 $\mu$ 的投影距离"** 作为主要判定依据
- **第二优先级**: 古典逻辑规则（`classical_logic_rules`）作为辅助验证

**双轨关系**:
- **逻辑硬门槛**: 基于Boolean表达式的确定性判定，边界清晰但可能过于刚性
- **物理软流形**: 基于统计分布的 probabilistic 判定，边界柔和但可能包含扩展区域
- **空间分歧**: 两种方法在样本空间中的判定区域存在显著差异是正常的，反映了观察命运真理的两个不同坐标系

**物理溢出合法性**:
- 当物理模型识别出古典逻辑"不认"但在5D空间中物理特征完全符合格局的样本时，这些样本被定义为 **"流形扩展区 (Manifold Extension)"**
- 物理扩展区样本具有极高的实战挖掘价值，是FDS系统对传统命理的重要补盲
- **IoU指标**: 通过IoU（交集率）衡量两种方法的空间重合度，IoU < 30% 是正常现象，反映了Boolean逻辑与Statistical流形的本质区别

---

## 二、 五维命运张量定义 ($T_{fate}$)

### 2.1 张量结构

五维命运张量 $T_{fate} \in \mathbb{R}^5$ 是格局在物理空间中的完整描述：

$$
T_{fate} = [E, O, M, S, R]
$$

### 2.2 维度定义表

| 维度轴 | 物理定义 (Physics) | 通用命理意象 (Metaphysics) | 数值范围 |
| :--- | :--- | :--- | :--- |
| **E (Energy)** | **能级/振幅** | 生命力、抗压阈值、根基深浅、行动底气 | [0, 1] |
| **O (Order)** | **熵减/有序度** | 权力、社会阶层、自律、管理能力、贵气 | [0, 1] |
| **M (Material)** | **物质/做功** | 财富总量、资产控制力、现实资源、执行成果 | [0, 1] |
| **S (Stress)** | **应力/剪切力** | 风险、灾难、内耗、突发意外、结构断裂 | [0, 1] |
| **R (Relation)** | **纠缠/相干性** | 情感连接、人际网络、六亲缘分、社交耦合 | [0, 1] |

### 2.3 维度语义

**E (Energy - 能量)**:
- 物理意义: 系统的基础能量水平，决定系统的稳定性和抗干扰能力
- 命理意义: 日主（命主）的能量强弱，决定能否承受格局的负载
- 计算依据: 通根、得令、得地等因素的综合评估

**O (Order - 有序度)**:
- 物理意义: 系统的有序程度，熵减的度量
- 命理意义: 社会地位、权力结构、组织管理能力
- 计算依据: 官杀、印绶等因素的配置

**M (Material - 物质)**:
- 物理意义: 系统对外做功的能力，物质转换效率
- 命理意义: 财富获取能力、资源控制力、现实成就
- 计算依据: 财星、食伤等因素的配置

**S (Stress - 应力)**:
- 物理意义: 系统承受的剪切力和结构应力
- 命理意义: 风险、灾难、内耗、突发意外
- 计算依据: 冲、克、刑、害等因素的配置

**R (Relation - 关系)**:
- 物理意义: 系统的量子纠缠和相干性
- 命理意义: 人际关系、六亲缘分、社交网络
- 计算依据: 合、会、拱等因素的配置

---

## 三、 三大物理公理 (Axioms)

### 3.1 符号守恒公理 (Conservation of Sign)

**公理陈述**: 拟合器必须对权重实施投影梯度下降，确保贡献方向（如"冲"增加 S）符合物理常识。

**物理意义**:
- 五行生克关系在物理上具有方向性
- "冲"操作必须增加应力维度 (S)，不能减少
- "生"操作必须增加能量维度 (E)，不能减少
- 权重优化过程中，必须保持这种方向性的一致性

**数学表达**:
对于权重矩阵 $W$ 的每个元素 $w_{ij}$，如果 $w_{ij}$ 对应的是"冲"操作对 S 维度的贡献，则：
- $w_{ij} \ge 0$（符号必须为正）
- 优化过程中必须约束 $w_{ij}$ 的符号不变

**实现要求**:
- 使用投影梯度下降（Projected Gradient Descent）
- 在优化过程中实施符号约束
- 损失函数必须包含符号惩罚项

### 3.2 拓扑特异性公理 (Topological Override)

**公理陈述**: 核心反应堆粒子权重必须显著高于背景噪声，作为该格局的物理法律。

**物理意义**:
- 每个格局都有其核心特征（如"偏财格"的核心是偏财星）
- 核心特征的权重必须显著高于其他特征
- 背景噪声（无关特征）的权重应该接近零

**数学表达**:
对于格局 $P$，设其核心特征权重为 $w_{core}$，背景特征权重为 $w_{bg}$，则：
- $w_{core} \gg w_{bg}$
- 通常要求: $w_{core} / w_{bg} \ge \text{threshold}$（阈值从配置读取，如 10:1）

**实现要求**:
- 在损失函数中添加拓扑特异性惩罚项
- 确保核心特征权重显著高于阈值
- 通过正则化抑制背景噪声

### 3.3 正交解耦公理 (Orthogonality)

**公理陈述**: 五维轴线在语义上互斥，高财富 (M) 与高权力 (O) 必须实现物理脱钩。

**物理意义**:
- 五个维度在语义上应该是独立的
- 高财富不代表高权力，高权力不代表高财富
- 维度之间不应该有强相关性（除非有物理原因）

**数学表达**:
对于协方差矩阵 $\Sigma$，非对角元素（维度间的协方差）应该尽可能小：
- $\Sigma_{ij} \approx 0$（当 $i \ne j$ 时）
- 或者通过主成分分析（PCA）实现维度解耦

**实现要求**:
- 在矩阵拟合过程中添加正交性约束
- 通过正则化减少维度间的相关性
- 验证协方差矩阵的非对角元素是否足够小

---

## 四、 全息注册表通用 Schema (QGA-HR V3.0)

### 4.1 Schema 版本说明

- **Schema 版本**: `3.0`
- **标准名称**: QGA-HR (Quantum General Architecture - Holographic Registry)
- **对齐目标**: `QGA_HR_REGISTRY_SPEC_v3.0.md`

**重要说明**: 所有注册表文件必须包裹在 **QGA 标准信封 (Envelope)** 中，强制指定 `topic` 为 `holographic_pattern`，以确保与量子通用架构系统的兼容性。

---

### 4.2 标准格局 Schema (QGA 信封封装版)

**结构定义**:
所有注册表文件必须包裹在 **QGA 标准信封** 中，强制指定 `topic` 为 `holographic_pattern`。

**信封结构**:

```json
{
  "topic": "holographic_pattern",    // [CRITICAL] 必须指定主题
  "schema_version": "3.0",
  "data": {                          // [CRITICAL] 实际数据载荷
    "pattern_id": "B-01",
    "meta_info": {
      "display_name": "Eating God",
      "chinese_name": "食神格",
      "category": "TALENT",
      "version": "3.0"
    },
  "matching_router": {
    "strategies": [
      {
        "priority": 1,
        "logic": { 
          "rules": [
            { 
              "axis": "E", 
              "operator": "gt", 
              "param_ref": "@config.gating.weak_self_limit" 
            }
          ] 
        }
      }
    ]
  },
    "feature_anchors": {
      "standard_manifold": {
        "mean_vector": [E_mean, O_mean, M_mean, S_mean, R_mean],
        "covariance_matrix": [
          [σ_EE, σ_EO, σ_EM, σ_ES, σ_ER],
          [σ_OE, σ_OO, σ_OM, σ_OS, σ_OR],
          [σ_ME, σ_MO, σ_MM, σ_MS, σ_MR],
          [σ_SE, σ_SO, σ_SM, σ_SS, σ_SR],
          [σ_RE, σ_RO, σ_RM, σ_RS, σ_RR]
        ]
      }
    },
    "population_stats": {            // [NEW] 必须包含统计信息
      "base_abundance": 21.79,
      "sample_size": 518400,
      "sub_patterns": {}
    }
  }
}
```

**信封字段说明**:

| 字段 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `topic` | String | 是 | 主题标识符，必须为 `"holographic_pattern"` |
| `schema_version` | String | 是 | Schema 版本，当前版本为 `"3.0"` |
| `data` | Object | 是 | 实际数据载荷，包含格局的所有信息 |

**数据载荷 (data) 字段说明**:

#### 4.2.1 meta_info 字段说明

| 字段 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `pattern_id` | String | 是 | 格局唯一标识符，格式: `[类别]-[序号]`，如 `B-01`, `A-03` |
| `display_name` | String | 是 | 英文索引名，采用PascalCase或Title Case，如 `Eating God`, `Indirect Wealth` |
| `chinese_name` | String | 是 | 中文展示名，简体中文，如 `食神格`, `偏财格` |
| `category` | Enum | 是 | 格局类别，必须为: `WEALTH`, `POWER`, `TALENT`, `SELF` 之一 |
| `version` | String | 是 | 版本号，当前版本必须为 `"3.0"` |

#### 4.2.2 matching_router 字段说明

| 字段 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `strategies` | Array | 是 | 匹配策略数组，按优先级排序 |
| `strategies[].priority` | Integer | 是 | 优先级，数字越小优先级越高 |
| `strategies[].logic.rules` | Array | 是 | 匹配规则数组 |
| `strategies[].logic.rules[].axis` | String | 是 | 维度轴，必须为: `E`, `O`, `M`, `S`, `R` 之一 |
| `strategies[].logic.rules[].operator` | String | 是 | 操作符，如: `gt` (大于), `lt` (小于), `eq` (等于), `gte` (大于等于), `lte` (小于等于) |
| `strategies[].logic.rules[].param_ref` | String | 是 | 参数引用，格式: `@config.路径`，如 `@config.gating.weak_self_limit` |

**注意**: 
- 所有参数必须通过 `param_ref` 引用配置文件，严禁硬编码数值
- `param_ref` 格式: `@config.层级路径`，使用点号分隔

#### 4.2.3 feature_anchors 字段说明

| 字段 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `standard_manifold` | Object | 是 | 标准统计流形定义 |
| `standard_manifold.mean_vector` | Array[Float] | 是 | 均值向量 $\mu \in \mathbb{R}^5$，5个浮点数，范围 [0, 1] |
| `standard_manifold.covariance_matrix` | Array[Array[Float]] | 是 | 协方差矩阵 $\Sigma \in \mathbb{R}^{5 \times 5}$，5x5的浮点数矩阵 |

**数学要求**:
- `mean_vector` 的长度必须为 5
- `covariance_matrix` 必须是 5x5 的对称正定矩阵
- 所有数值必须在合理的物理范围内（通常 [0, 1] 或归一化后的范围）

### 4.3 奇点存证 Schema（含 benchmarks）

适用于有奇点样本但无法形成统计流形的格局（或标准格局的补充）。

```json
{
  "meta_info": {
    "pattern_id": "A-03",
    "display_name": "Direct Officer",
    "chinese_name": "正官格",
    "category": "POWER",
    "version": "3.0"
  },
  "matching_router": {
    "strategies": [...]
  },
  "feature_anchors": {
    "standard_manifold": {
      "mean_vector": [0.45, 0.65, 0.30, 0.25, 0.40],
      "covariance_matrix": [[...], [...], [...], [...], [...]]
    }
  },
  "benchmarks": [
    {
      "t": [0.72, 0.18, 0.05, 0.85, 0.12],  // 5D 特征张量
      "ref": "CASE-9527",                   // 指向原始数据的指针
      "distance_to_manifold": 3.45,         // 偏离度
      "cluster_id": "C-05"                  // 所属聚类ID (若有)
    },
    {
      "t": [0.68, 0.22, 0.08, 0.78, 0.15],
      "ref": "CASE-12834",
      "distance_to_manifold": 3.12,
      "cluster_id": null                    // 孤立奇点（无聚类）
    }
  ]
}
```

#### 4.3.1 benchmarks 字段说明

| 字段 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `benchmarks` | Array | 否 | 奇点样本数组，仅在存在奇点样本时出现 |
| `benchmarks[].t` | Array[Float] | 是 | 5D特征张量 $T_{fate} = [E, O, M, S, R]$，5个浮点数 |
| `benchmarks[].ref` | String | 是 | Case_ID，指向 `holographic_universe_518k.jsonl` 或数据库中的完整原始数据 |
| `benchmarks[].distance_to_manifold` | Float | 是 | 该奇点到标准流形的马氏距离 $D_M$（偏离度） |
| `benchmarks[].cluster_id` | String | 否 | 所属聚类ID（若有聚类分析，如 "C-05"） |
| `benchmarks[].abundance` | Float | 否 | 该奇点在总样本中的占比（如 0.00543 表示 0.543%） |

**物理逻辑**:
- `benchmarks` 字段仅在奇点存证模式下存在（$N < \text{min\_samples}$，无法形成统计流形）
- `t` 存储5D特征张量，不存储原始八字字符串（保持物理脱钩原则）
- `ref` 作为指针，指向完整原始数据（包括原始八字、大运、人生轨迹真值 $y_{true}$）

**识别逻辑**:
- 在测试真实八字时，若判定为非主流形（$D_M > \text{threshold}$），则激活最近邻检索 (Nearest Neighbor Search)
- 通过计算输入张量 $T_{input}$ 与 `benchmarks` 中所有奇点张量的欧氏距离或余弦相似度，锁定最接近的 1-3 个奇点样本
- 判定基准：若最小距离 $d_{min} < \epsilon$（$\epsilon$ 为相似度阈值），则判定命中该子专题

---

## 五、 数据关联与索引规范

### 5.1 全息宇宙数据文件

**文件名**: `holographic_universe_518k.jsonl`

**格式**: JSON Lines (每行一个JSON对象)

**内容结构**:
```json
{
  "Case_ID": "CASE-9527",
  "bazi": {
    "year": {"gan": "甲", "zhi": "子"},
    "month": {"gan": "乙", "zhi": "丑"},
    "day": {"gan": "丙", "zhi": "寅"},
    "hour": {"gan": "丁", "zhi": "卯"}
  },
  "dashun": [...],
  "y_true": {
    "wealth": 0.65,
    "power": 0.32,
    "talent": 0.78,
    "stress": 0.45,
    "relation": 0.58
  },
  "metadata": {...}
}
```

### 5.2 Case_ID 索引规范

- **格式**: `CASE-XXXX` 或 `CASE-XXXXX`（数字部分为唯一标识符）
- **唯一性**: 每个样本的 Case_ID 必须在518,400样本库中唯一
- **关联**: `benchmarks[].ref` 字段通过 Case_ID 关联到完整原始数据

### 5.3 数据脱钩原则

- **注册表轻量化**: `registry.json` 中不直接保存原始八字字符串
- **指针引用**: 通过 `Case_ID` 作为指针，指向完整数据源
- **物理分离**: 格局定义（流形、参数）与原始数据（八字、大运）在存储上分离

---

## 六、 格局配置文件 Schema (Pattern Manifest Schema)

### 6.1 配置文件概述

**文件名**: `pattern_manifest.json`  
**用途**: 定义具体格局的古典逻辑规则和初始权重映射，作为SOP工作流的输入配置  
**性质**: 每个格局需要独立的配置文件，SOP规范不包含任何具体格局的硬编码逻辑

### 6.2 配置文件结构

```json
{
  "pattern_id": "B-01",
  "version": "3.0",
  "classical_logic_rules": {
    "format": "jsonlogic",
    "expression": {
      "and": [
        { ">": [{ "var": "ten_gods.EG" }, 0] },
        { "<": [{ "var": "ten_gods.SG" }, { "var": "ten_gods.EG" }] },
        { ">=": [{ "var": "self_energy" }, { "var": "@config.gating.weak_self_limit" }] }
      ]
    }
  },
  "tensor_mapping_matrix": {
    "ten_gods": ["ZG", "PG", "ZR", "PR", "ZS", "PS", "ZC", "PC", "ZB", "PB"],
    "dimensions": ["E", "O", "M", "S", "R"],
    "weights": {
      "ZG": [0.1, 0.8, 0.2, 0.1, 0.3],
      "PG": [0.1, 0.7, 0.3, 0.2, 0.4],
      "ZR": [0.2, 0.1, 0.9, 0.1, 0.2],
      "PR": [0.2, 0.1, 0.85, 0.15, 0.25],
      "ZS": [0.6, 0.1, 0.2, 0.1, 0.3],
      "PS": [0.55, 0.1, 0.25, 0.15, 0.35],
      "ZC": [0.3, 0.2, 0.1, 0.8, 0.1],
      "PC": [0.3, 0.25, 0.15, 0.75, 0.15],
      "ZB": [0.4, 0.1, 0.1, 0.1, 0.8],
      "PB": [0.35, 0.15, 0.15, 0.15, 0.75]
    },
    "strong_correlation": [
      { "ten_god": "ZR", "dimension": "M", "reason": "正财是财富核心" },
      { "ten_god": "PG", "dimension": "O", "reason": "偏官是权力核心" }
    ]
  }
}
```

### 6.3 字段详细说明

#### 6.3.1 pattern_id

| 字段 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `pattern_id` | String | 是 | 格局唯一标识符，格式: `[类别]-[序号]`，如 `B-01`, `A-03` |

#### 6.3.2 classical_logic_rules (古典逻辑规则)

**用途**: 定义格局的成格条件，用于L1逻辑普查阶段的样本过滤

| 字段 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `format` | String | 是 | 表达式格式，推荐: `"jsonlogic"` (JSONLogic格式) 或 `"dsl"` (自定义DSL) |
| `expression` | Object | 是 | 布尔表达式树，支持标准逻辑操作符 |

**支持的逻辑操作符**:
- `and`: 逻辑与
- `or`: 逻辑或
- `not`: 逻辑非
- `>`: 大于
- `<`: 小于
- `>=`: 大于等于
- `<=`: 小于等于
- `==` 或 `eq`: 等于
- `!=` 或 `ne`: 不等于

**变量引用格式**:
- `{ "var": "ten_gods.EG" }`: 引用十神变量（如食神数量）
- `{ "var": "self_energy" }`: 引用日主能量
- `{ "var": "@config.gating.weak_self_limit" }`: 引用系统配置参数

**示例表达式** (JSONLogic格式):
```json
{
  "and": [
    { ">": [{ "var": "ten_gods.EG" }, 0] },
    { "<": [{ "var": "ten_gods.SG" }, { "var": "ten_gods.EG" }] }
  ]
}
```

**约束**:
- 表达式必须能够被通用的表达式解析引擎执行
- 严禁在SOP代码中硬编码具体格局的逻辑判断
- 所有逻辑必须从配置文件动态解析

#### 6.3.3 tensor_mapping_matrix (张量映射矩阵)

**用途**: 定义十神到五维张量的初始映射权重，用于Step 1矩阵初始化

| 字段 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `ten_gods` | Array[String] | 是 | 十神类型列表，如: `["ZG", "PG", "ZR", "PR", ...]` |
| `dimensions` | Array[String] | 是 | 五维张量维度列表: `["E", "O", "M", "S", "R"]` |
| `weights` | Object | 是 | 权重映射表，key为十神代码，value为5维权重数组 |
| `strong_correlation` | Array[Object] | 否 | 强相关权重标记列表，这些权重在拟合过程中将被锁定 |

**weights字段格式**:
```json
{
  "ZR": [0.1, 0.8, 0.2, 0.1, 0.3]  // [E, O, M, S, R] 五个维度的权重
}
```

**strong_correlation字段格式**:
```json
[
  {
    "ten_god": "ZR",      // 十神代码
    "dimension": "M",     // 维度 (E/O/M/S/R)
    "reason": "正财是财富核心"  // 标记原因（可选，用于文档化）
  }
]
```

**约束**:
- 权重值范围: 建议 [0, 1]，但可根据实际情况调整
- 强相关权重在Step 3矩阵拟合过程中将被锁定（Freeze），不允许修改
- 未定义的映射关系，SOP执行时默认初始化为 `0.0` 或高斯噪声

### 6.4 配置文件验证规则

在SOP执行前，必须验证配置文件：

1. **必需字段检查**:
   - `pattern_id` 必须存在且格式正确
   - `classical_logic_rules` 必须存在且格式有效
   - `tensor_mapping_matrix` 必须存在且格式有效

2. **逻辑表达式验证**:
   - 表达式必须能被解析引擎成功解析
   - 所有变量引用必须有效（不存在未定义的变量）

3. **权重矩阵验证**:
   - 权重数组长度必须为5（对应EOMSR五个维度）
   - 强相关标记的 `ten_god` 和 `dimension` 必须在矩阵中存在

4. **公理一致性验证**:
   - 检查权重矩阵是否符合符号守恒公理
   - 检查是否存在违背正交解耦公理的映射（如单一十神同时极强映射到互斥维度）

### 6.5 配置文件与注册表的关系

- **配置文件 (`pattern_manifest.json`)**: 定义格局的**输入规范**（如何识别、如何初始化）
- **注册表 (`registry.json`)**: 定义格局的**输出结果**（拟合后的流形参数、元数据）

配置文件用于SOP工作流的执行，注册表用于运行时的格局识别。

---

## 七、 配置参数规范

### 6.1 参数引用格式

所有参数必须通过 `@config.路径` 格式引用，严禁硬编码。

**示例**:
- `@config.gating.weak_self_limit` - 身弱门控阈值
- `@config.gating.max_relation` - 关系维度最大值
- `@config.physics.precision_weights.similarity` - 相似度权重
- `@config.physics.precision_weights.distance` - 距离权重

### 6.2 参数层级结构

```
config/
  gating/
    weak_self_limit: Float
    max_relation: Float
  physics/
    precision_weights/
      similarity: Float
      distance: Float
    thresholds/
      mahalanobis: Float
      similarity: Float
  recognition/
    min_samples: Integer
    tolerance: Float
```

### 6.3 参数配置原则

- **零硬编码**: 所有数值参数必须从配置文件读取
- **单一真理源**: 参数修改只能通过配置文件进行
- **版本控制**: 配置文件变更必须记录版本号和变更原因

---

## 八、 术语表 (Glossary)

| 术语 | 英文 | 定义 |
| :--- | :--- | :--- |
| 统计流形 | Statistical Manifold | 在5D空间中具有特定形状和概率分布的格局区域 |
| 均值向量 | Mean Vector ($\mu$) | 格局在5D空间中的中心点 |
| 协方差矩阵 | Covariance Matrix ($\Sigma$) | 描述格局形状和分布的5x5矩阵 |
| 马氏距离 | Mahalanobis Distance ($D_M$) | 考虑协方差的距离度量，用于判断样本是否属于格局 |
| 奇点 | Singularity | 偏离标准流形的特殊样本，无法形成统计流形 |
| 全息存证 | Holographic Benchmarking | 对奇点样本保存完整5D张量而非流形参数的存证模式 |
| 门控 | Gating | 安全阈值机制，用于过滤不符合条件的样本 |
| 基准丰度 | Abundance (Base) | 格局在518,400样本库中的基础命中率 |
| Case_ID | Case Identifier | 样本的唯一标识符，用于关联完整原始数据 |

---

**文档维护**: 本架构规范与 `FDS_SOP_v3.0.md` 配套使用，任何架构变更必须同步更新SOP。

