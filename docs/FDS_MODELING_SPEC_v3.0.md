# 🏛️ QGA 正向拟合与建模规范 (FDS-V3.0 精密物理架构版)
—— 全格局通用统计力学仿真标准 ——

**版本**: V3.0 (Precision Physics & Statistical Manifolds)
**修订**: Genesis Protocol, Safety Protocols Injection & Metadata Enforcement (元数据强制)
**生效日期**: 2025-12-31
**适用范围**: Antigravity Engine 全量格局 (A-Z Series)
**依赖**: `ALGORITHM_CONSTITUTION_v3.0.md`
**状态**: ENFORCED (强制执行)

---

## 一、 建模核心哲学 (The Soul)

### 物理本质
八字格局不是高维空间中的一个“点”，而是一个具有特定形状和概率分布的**“统计流形” (Statistical Manifold)**。

### 概率云 (Probability Cloud)
一个标准的“正财格”或“羊刃架杀”，在 5D 空间中表现为一个协方差椭球。不仅要看中心在哪，还要看它“胖瘦”如何（方差）以及各维度是否“联动”（协方差）。

### 精密识别
摒弃简单的“余弦相似度”。识别一个格局，等同于计算该样本落入目标概率势阱 (Potential Well) 的深度。必须引入能量门控，剔除“有形无气”的伪格局。

---

## 二、 五维命运张量定义 ($T_{fate}$)

所有格局的输出，最终都必须坍缩为以下 5 个维度的无量纲投影值 (0.0 - 1.0)。

| 维度轴 | 物理定义 (Physics) | 通用命理意象 (Metaphysics) |
| :--- | :--- | :--- |
| **E (Energy)** | **能级/振幅** | 生命力、抗压阈值、根基深浅、行动底气 |
| **O (Order)** | **熵减/有序度** | 权力、社会阶层、自律、管理能力、贵气 |
| **M (Material)** | **物质/做功** | 财富总量、资产控制力、现实资源、执行成果 |
| **S (Stress)** | **应力/剪切力** | 风险、灾难、内耗、突发意外、结构断裂 |
| **R (Relation)** | **纠缠/相干性** | 情感连接、人际网络、六亲缘分、社交耦合 |

---

## 三、 三大物理公理 (The Three Axioms)

为防止 AI 拟合出违反物理常识的矩阵，所有模型必须锁死以下公理。

### 公理 1：符号守恒 (Conservation of Sign)
微观粒子对宏观维度的**贡献方向（+/-）**通常由物理常识锁定。
* **示例**: 冲/刑 默认增加 S (Stress)；合 默认增加 R (Relation)。
* **约束**: 拟合器必须对权重矩阵实施 Projected Gradient Descent (投影梯度下降)，确保符号不反转。

### 公理 2：拓扑特异性 (Topological Override)
格局即法律。特定格局有权重定义粒子的物理属性。
* **规则**: 核心反应堆粒子（如杀格之杀）对 E/O/M 的贡献权重必须显著高于背景噪声。允许特定条件下（如相变）发生符号翻转。

### 公理 3：正交解耦 (Orthogonality)
五维轴线必须在语义上互斥。高 M (财) 不代表高 O (贵)；高 E (寿) 不代表低 S (灾)。描述必须解耦。

---

## 四、 六步拟合标准化工作流 (The Standard Workflow)

此流程适用于任何新格局的开发。FDS-V3.0 重点升级了 Step 2、Step 5 和 Step 6。

### Step 1: 物理原型定义 (Prototype Definition)
* **输入**: 古籍定义。
* **输出**: 初始 转换矩阵结构 ($\mathcal{T}_{init}$) 与 公理掩码 (Axiom Mask)。
* **动作**: 确定物理路径的强弱与正负。

### Step 2: 样本分层与海选 (Data Stratification)
* **输入源 (Input Source)**: 全息宇宙静态切片 (Holographic Universe Snapshot)
* **物理路径**: `core/data/holographic_universe_518k.jsonl`
* **数据量级**: 518,400 例 (不可变样本)。
* **创世纪协议 (Genesis Protocol)**:
    * **禁止**: 使用随机数生成器 (random.uniform) 实时生成样本。
    * **强制**: 必须以 Read-Only (只读) 模式加载宇宙文件。所有格局 (A-Z) 必须在同一个物理宇宙中进行筛选，保证统计基准的一致性。
* **挖掘漏斗 (Mining Funnel)**:
    * **L1 结构过滤**: 遍历静态文件，提取符合该格局物理特征的样本。
    * **L2 交叉验证**: 匹配样本的 y_true (预设的人生轨迹真值)。
    * **L3 提纯 (Tier A)**: 最终锁定 500+ 例 黄金样本（种子）。
* **输出 (Output)**:
    * **Tier A (Seeds)**: 500 个标准种子样本。
    * **Tier X (Singularity Candidates)**: 待后续协议处理的奇点候选。

### Step 3: 矩阵拟合 (Matrix Fitting)
* **工具**: `HolographicMatrixFitter`
* **动作**: 优化矩阵权重，最小化 $Loss = || T \cdot V_{in} - y_{true} ||^2 + \lambda_{physics}$。
* **注意**: 此步骤产出的是**“转换透镜” (Matrix)**，用于将 10 神转化为 5D 张量。

### Step 4: 动态演化机制 (Dynamic Mechanics)
* **输入**: 流年/大运介入。
* **定义状态机**:
    * **破格**: 触发 `collapse_rules`。
    * **激活/相变 (Activated)**: 触发 `exceptions` (基于 Schema V3.0)，允许调用物理算子（如 `analyze_clash_dynamics`）进行状态重映射。

### Step 5: 全息封卷与协议植入 (Assembly & Protocols) [CRITICAL UPDATE]
**核心定义**: 此步骤不仅是“打包”，更是“安检”与“归档”。禁止在未植入物理安全阀或元数据缺失的情况下生成注册表。

* **动作**:
    1.  **流形计算**: 将 500 个 Tier A 样本通过拟合好的矩阵投影到 5D 空间，计算均值向量 ($\mu$) 和 协方差矩阵 ($\Sigma$)。
    2.  **安全门控植入 (Safety Gate Injection)**: [强制执行] 在构建 `matching_router` 时，必须**硬编码引用**以下物理死线 (使用 `@config` 引用，严禁写死数字)：
        * **E-Gating (身旺门控)**: 对于所有财富(D)、权力(O)、高压(S)类格局，必须强制植入 `E > @config.gating.weak_self`。防止身弱者被误判为入格（如“富屋贫人”）。
        * **R-Gating (排他门控)**: 对于私有制格局 (如 D-01 正财)，必须强制植入 `R < @config.gating.max_relation`。
    3.  **元数据标准化 (Metadata Normalization)**: [新增] 为确保前端 UI (Project SUNRISE) 能正确渲染，生成的注册表必须包含完整的 `meta_info` 字段，严禁缺失或格式混用。
        * `category`: 必须枚举为 `WEALTH` (财), `POWER` (权/贵), `TALENT` (才/艺), 或 `SELF` (身/寿)。严禁使用 N/A。
        * `chinese_name`: 必须为纯中文名称（如“偏财格”），用于前端标题显示。
        * `display_name`: 必须为纯英文名称（如 "Indirect Wealth"），用于代码索引或副标题。
    4.  **容器封装**: 将标准流形与奇点流形封装进 Schema V3.0 容器 (`sub_patterns_registry`)。

* **输出**: 生成带有物理防盗门且元数据规范的 `registry.json`，不再存储原始样本。

### Step 6: 精密模式识别与负载验收 (Recognition & Load Test)
* **运行时逻辑**:
    1.  **门控裁决 (The Gate)**: 优先检查 `matching_router` 中的硬性规则 (E/R Gating)。若未通过，直接返回 `MISMATCH`，不再进行距离计算。
    2.  **流形路由 (The Router)**: 优先匹配奇点子格局，最后兜底标准格局。
    3.  **马氏距离**: 计算 $D_M = \sqrt{(x - \mu)^T \Sigma^{-1} (x - \mu)}$。
    4.  **概率评分**: $Score = G_{sai} \times \exp(-k \cdot D_M)$。
* **验收测试**: 必须运行 Load Testing 脚本，验证 **Case Z** (如身弱杀重、身弱财重) 是否被 Step 5 植入的门控拦截。若拦截失败，回滚至 Step 5，严禁使用“Step 7 补丁”。

---

## 五、 奇点与子格局发现协议 (Singularity & Sub-Pattern Protocol)

此章节定义了如何处理那些物理上成立、但形态上偏离标准种子的极端样本。

### 1. 奇点判定：基于种子的偏离度 (Deviation from Seeds)
我们不预设奇点名字（如“古墓”），只通过数学距离发现它。
* **基准锚点**: Step 2 中提纯的 500 个标准种子 (Standard Seeds)。
* **算法**: 计算样本到标准种子流形的马氏距离 $D_{std}$。
* **裁决逻辑**:
    * **情形 A (平庸)**: $D_{std} < @config.singularity.threshold$。判定：标准格局的变体。
    * **情形 B (奇点)**: $D_{std} \gg @config.singularity.threshold$。判定：奇点 (Singularity)。结构差异极大，但物理成立。

### 2. 子格局晋升机制 (Sub-Pattern Promotion)
并非所有奇点都能独立。必须经过“成团验证”。
* **聚类审计**: 对所有确认为“奇点”的样本进行 DBSCAN 聚类。
* **晋升条件**:
    * **成团性**: 聚类样本数 $N \ge @config.clustering.min_samples$ (e.g. 30)。
    * **一致性**: 簇内样本的人生真值 ($y_{true}$) 高度一致。
* **动作**: 满足条件的簇，正式注册为 **子格局 (Sub-Pattern)**，并拟合其专属的协方差流形。

### 3. 运行时路由 (Runtime Routing)
当输入为“八字 + 注入因子”时：
1.  **状态融合**。
2.  **门控预检 (E-Gate Check)**。
3.  **奇点优先**: 优先计算到各奇点子格局的距离。若落入某奇点流形，则锁定为该奇点。
4.  **标准兜底**: 若未命中奇点，再计算到标准格局的距离。

---

## 六、 附录：全息注册表通用 Schema (QGA-HR V3.0)
*(Updated for Safety Protocol Injection & Metadata Enforcement)*

JSON 结构升级为容器模式，以支持多子格局共存、强制安全门控及标准化元数据。**所有逻辑阈值均已升级为 Config 引用。**

```json
{
  "meta_info": {
    "pattern_id": "D-02",
    "name": "Indirect Wealth (The Venture)", // display_name 的副本或全称
    "display_name": "Indirect Wealth",       // [NEW] 纯英文，代码索引
    "chinese_name": "偏财格",               // [NEW] 纯中文，UI 标题
    "category": "WEALTH",                    // [NEW] 必须枚举 (WEALTH/POWER/TALENT/SELF)
    "version": "3.0",
    "compliance": "FDS-V3.0"
  },

  "physics_kernel": {
    "description": "通用物理参数 (Fallback)",
    "transfer_matrix": { 
        "E_row": { "Day_Master": 0.8, "Resource": 0.5 }, 
        "M_row": { "Wealth": 0.9, "Clash": -0.3 }
    },
    "tensor_dynamics": { 
        "activation_function": "sigmoid_variant",
        "k_factor_ref": "@config.physics.k_factor"
    }
  },

  // 子格局容器
  "sub_patterns_registry": [
    {
      "id": "SP_D02_SYNDICATE",
      "type": "SINGULARITY",
      "name": "财团/众筹态",
      "matrix_override": { 
          "transfer_matrix": {
              "M_row": { "Rob_Wealth": 0.8 }, // 翻转：劫财为用
              "R_row": { "Rob_Wealth": 0.6 }
          }
      },
      "manifold_data": { 
          "mean_vector": { "E": 0.6, "M": 0.7, ... },
          "covariance_matrix": [ ... ]
      }
    }
  ],

  // 运行时路由协议 (含安全门控 - V3.0引用版)
  "matching_router": {
    "strategy_version": "3.0",
    "strategies": [
       {
         "priority": 1,
         "target": "SP_D02_SYNDICATE",
         "logic": { 
             "condition": "AND", 
             "rules": [
                 // [SAFETY GATE] 必须前置，引用配置
                 { "axis": "E", "operator": "gt", "param_ref": "@config.gating.weak_self_limit", "description": "Safety: Anti-Puppet" },
                 // 业务逻辑
                 { "axis": "R", "operator": "gt", "param_ref": "@config.patterns.d02.syndicate_r_limit" },
                 { "axis": "M", "operator": "gt", "param_ref": "@config.patterns.d02.syndicate_m_limit" }
             ] 
         }
       }
    ]
  },

  "dynamic_states": { "description": "Phase Change Definitions..." },
  "algorithm_implementation": { "class_path": "core.patterns.pattern_d02.PatternD02" }
}
