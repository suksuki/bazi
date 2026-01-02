# 🏛️ QGA 正向拟合与建模规范 (FDS-V3.0 精密物理架构版)
—— 全格局通用统计力学仿真标准 ——

**版本**: V3.0 (Precision Physics & Statistical Manifolds)
**修订**: Genesis Protocol, Safety Protocols Injection & Metadata Enforcement
**生效日期**: 2025-12-31
**状态**: ENFORCED (强制执行)

---

## 一、 建模核心哲学 (The Soul)

### 物理本质
八字格局不是高维空间中的一个“点”，而是一个具有特定形状和概率分布的 **“统计流形” (Statistical Manifold)**。

### 识别标准
采用矢量场 (Vector Field) + 概率云 (Probability Cloud) 的双重验证模型，通过方向、位置、能量三重门控判定入格程度。

---

## 二、 五维命运张量定义 ($T_{fate}$)

| 维度轴 | 物理定义 (Physics) | 通用命理意象 (Metaphysics) |
| :--- | :--- | :--- |
| **E (Energy)** | **能级/振幅** | 生命力、抗压阈值、根基深浅、行动底气 |
| **O (Order)** | **熵减/有序度** | 权力、社会阶层、自律、管理能力、贵气 |
| **M (Material)** | **物质/做功** | 财富总量、资产控制力、现实资源、执行成果 |
| **S (Stress)** | **应力/剪切力** | 风险、灾难、内耗、突发意外、结构断裂 |
| **R (Relation)** | **纠缠/相干性** | 情感连接、人际网络、六亲缘分、社交耦合 |

---

## 三、 三大物理公理 (Axioms)

1. **符号守恒 (Conservation of Sign)**: 拟合器必须对权重实施投影梯度下降，确保贡献方向（如“冲”增加 S）符合物理常识。
2. **拓扑特异性 (Topological Override)**: 核心反应堆粒子权重必须显著高于背景噪声，作为该格局的物理法律。
3. **正交解耦 (Orthogonality)**: 五维轴线在语义上互斥，高财富 (M) 与高权力 (O) 必须实现物理脱钩。

---

## 四、 六步拟合标准化工作流

### Step 1: 物理原型定义
* 确定初始转换矩阵结构与公理掩码，锁定物理路径的正负倾向。

### Step 2: 样本分层与海选 (Census & Stratification)

1. **L1 逻辑普查 (Classical Census)**：[强制执行]
   - **记录**：记录格局在 518,400 样本库中的绝对命中数 $N_{hit}$。
   - **算法**：古典海选丰度 (Classical Abundance)
   
$$
\text{Abundance}_{base} = \frac{N_{hit}}{518,400} \times 100\%
$$

   - **归档**：此丰度值存入元数据，作为 Step 6 调校的 **法定参考值 (Ground Truth)**。

2. **L2 交叉验证**：匹配样本的人生轨迹真值 $y_{true}$。
3. **L3 提纯 (Tier A)**：锁定 500+ 例黄金种子样本。

### Step 3: 矩阵拟合
* 优化权重，最小化物理损失函数，产出格局专属的“转换透镜”矩阵。

### Step 4: 动态演化机制
* 定义状态机：包含“破格”与“激活/相变”逻辑，支持流年大运介入时的状态重映射。

### Step 5: 全息封卷与协议植入 (Assembly & Protocols) [CRITICAL]

1. **安全门控植入 (Safety Gate Injection)**：[强制执行]
   - **身旺门控 (E-Gating)**：强制植入 `@config.gating.weak_self_limit`。
   - **排他门控 (R-Gating)**：强制植入 `@config.gating.max_relation`。

2. **元数据标准化 (Metadata)**：
   - `category`：必须枚举为 `WEALTH`, `POWER`, `TALENT`, `SELF`。
   - `display_name`：英文索引名 (e.g., `Indirect Wealth`)。
   - `chinese_name`：中文展示名 (e.g., `偏财格`)。

3. **容器封装**：将均值向量 ($\mu$) 和协方差矩阵 ($\Sigma$) 封装进子格局注册表。

4. **奇点样本存证 (Singularity Benchmarking)**：[强制执行]
   
   **物理逻辑**：
   - 对于判定的奇点样本（Singularity），系统**不再进行流形平均化**（即不计算 $\mu$ 和 $\Sigma$），而是采用**全息存证**模式。
   - 奇点判定标准：样本到种子流形的马氏距离 $D_M \gg \text{threshold}$，且样本数量 $N < \text{min\_samples}$（无法形成统计流形）。
   
   **存证内容**：
   - 每一个奇点必须保存其 **5D 特征张量** ($T_{fate} = [E, O, M, S, R]$) 以及 **样本唯一标识符** (`Case_ID`)。
   - **不直接保存原始八字字符串**：保持物理脱钩原则，`registry.json` 保持轻量级。
   - `Case_ID` 作为**指针**，指向 `holographic_universe_518k.jsonl` 或数据库中的完整原始数据（包括原始八字、大运、人生轨迹真值 $y_{true}$）。
   
   **存储规格**：
   ```json
   {
     "id": "SUB_ID",
     "benchmarks": [
       {
         "t": [E, O, M, S, R],  // 5D特征张量
         "ref": "Case_ID"        // 指向原始数据的索引
       }
     ]
   }
   ```
   
   **识别逻辑**：
   - 在测试真实八字时，若判定为非主流形（$D_M > \text{threshold}$），则激活 **最近邻检索 (Nearest Neighbor Search)**。
   - 通过计算输入张量 $T_{input}$ 与 `benchmarks` 中所有奇点张量的**欧氏距离**或**余弦相似度**，锁定最接近的 1-3 个奇点样本。
   - **判定基准**：若最小距离 $d_{min} < \epsilon$（$\epsilon$ 为相似度阈值），则判定命中该子专题。
   
   **应用场景**：
   - 当输入八字偏离标准流形时，系统返回：
     > "检测到该八字偏离标准流形，高度匹配奇点样本 **#CASE-9527**。该样本在 5D 空间中的表现为：高能量、极高剪切力。历史记录显示该类命造多发于...（调用 $y_{true}$）。"
   - 这种基于**真实坐标点**的对比，比基于"模糊公式"的对比要准确得多。

---

### Step 6: 精密模式识别与负载验收 (Recognition)

* **精密评分 (Enhanced Precision Score)**：

$$
\text{Score} = (W_{sim} \cdot \text{CosSim} + W_{dist} \cdot e^{-D_M^2 / 2\sigma^2}) \cdot G_{sai}
$$

* **物理参数配置**：
  - 参数必须从配置中心读取（如 `@config.physics.precision_weights.similarity`）。
  - **纠偏逻辑**：最终识别率必须对比 Step 2 的 $\text{Abundance}_{base}$。若偏差过大，必须回退调整马氏距离阈值。

---

## 五、 奇点与子格局发现协议

1. **奇点判定**：计算样本到种子流形的距离，大幅偏离者（$D_M \gg \text{threshold}$）判定为奇点。
2. **子格局晋升**：奇点样本聚类数满足 $N \ge \text{min\_samples}$ 且轨迹一致时，正式晋升为子格局。
3. **奇点存证**：对于无法形成统计流形的奇点样本（$N < \text{min\_samples}$），采用全息存证模式（见 Step 5.4），通过 **KNN (K-Nearest Neighbors)** 算法实现精准物理溯源。

---

## 六、 附录：全息注册表通用 Schema (QGA-HR V3.0)

### 标准格局 Schema（含统计流形）

```json
{
  "meta_info": {
    "pattern_id": "B-01",
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
                 { "axis": "E", "operator": "gt", "param_ref": "@config.gating.weak_self_limit" }
             ] 
         }
       }
    ]
  },
  "feature_anchors": {
    "standard_manifold": {
      "mean_vector": [E_mean, O_mean, M_mean, S_mean, R_mean],
      "covariance_matrix": [[...], [...], [...], [...], [...]]
    }
  }
}
```

### 奇点存证 Schema（含 benchmarks）

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
      "t": [0.72, 0.18, 0.05, 0.85, 0.12],
      "ref": "CASE-9527",
      "distance_to_manifold": 3.45,
      "abundance": 0.00543
    },
    {
      "t": [0.68, 0.22, 0.08, 0.78, 0.15],
      "ref": "CASE-12834",
      "distance_to_manifold": 3.12,
      "abundance": 0.00421
    }
  ]
}
```

**说明**：
- `benchmarks` 字段仅在奇点存证模式下存在（$N < \text{min\_samples}$）。
- `t`：5D特征张量 `[E, O, M, S, R]`。
- `ref`：Case_ID，指向 `holographic_universe_518k.jsonl` 中的完整原始数据。
- `distance_to_manifold`：该奇点到标准流形的马氏距离。
- `abundance`：该奇点在总样本中的占比（如 0.543%）。
