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

---

## 六、 附录：全息注册表通用 Schema (QGA-HR V3.0)

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
  }
}
```
