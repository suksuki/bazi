# 🏛️ QGA 正向拟合与建模规范 (FDS-V1.4 最终完整版)
—— 从微观粒子到宏观流形的全息映射体系 ——

**版本**: V1.4 (The Matrix & Phase Transition)  
**生效日期**: 2025-12-29  
**状态**: ENFORCED (强制执行)

---

## 一、 建模核心哲学 (The Soul)

1.  **物理本质**：格局不是僵化的文字标签，而是八字微观场（干支粒子振动）在高维空间投射出的宏观吸引子（Attractor）。
2.  **局域规范变换 (Local Gauge Transformation)**：不存在通用的吉凶公式。每一个格局（Pattern）都是一个独特的光学棱镜（转换矩阵）。同样的十神粒子（如七杀），射入不同的棱镜（格局），折射出的五维光谱（命运）截然不同。
3.  **主导权声明**：
    *   **AI 首席分析师 (Gemini)**：负责定义物理意象、初始转换矩阵与物理公理。
    *   **Cursor (Core Engine)**：负责基于此框架进行数据海选与参数拟合。

---

## 二、 五维命运张量定义 ($\mathcal{T}_{fate}$)

所有拟合与输出必须坍缩为以下 5 个维度的投影值 (0.0 - 1.0)。SAI (系统对齐指数) 为总模长。

| 维度轴 (Axis) | 符号 | 物理定义 (Physics) | 命理意象 (Metaphysics) |
| :--- | :---: | :--- | :--- |
| **能级轴** | $\mathbf{E}$ | 系统总振幅/储能 | 寿夭、根基、抗压底气、生命长度 |
| **秩序轴** | $\mathbf{O}$ | 能量的收束与聚焦 | 权力、名誉、社会地位、贵气 |
| **物质轴** | $\mathbf{M}$ | 能量的实体转化率 | 财富、资产、执行力、现实资源 |
| **应力轴** | $\mathbf{S}$ | 内部剪切力/摩擦 | 疾厄、意外、情绪内耗、结构断裂风险 |
| **关联轴** | $\mathbf{R}$ | 场能相干性 | 六亲、情感、人际网络耦合度 |

---

## 三、 三大物理公理 (The Three Axioms)

为防止算法拟合出现虚假相关性（Overfitting），所有转换矩阵的构建必须锁死以下公理。

### 公理 1：能量守恒与转化方向 (Conservation of Sign)
微观粒子对宏观维度的贡献**方向（正负号）由物理常识锁定，仅效率（数值）**可由数据拟合调整。
*   **E (能级)**：比劫、印枭 $\rightarrow$ 必须为正贡献 (+)。
*   **M (物质)**：财星、食伤 $\rightarrow$ 必须为正贡献 (+)。
*   **S (应力)**：冲、刑、七杀 $\rightarrow$ 默认正贡献 (+)。

### 公理 2：格局特异性修正 (Pattern Override)
特定格局拥有改写物理常数的最高权限。
*   **A-03 (羊刃架杀) 修正案**：
    *   **七杀 (Power)**：从主要贡献 S (灾) 强制扭转为主要贡献 O (秩序/权)。
    *   **比劫 (Parallel)**：从负贡献 M (破财) 强制修正为正贡献 E (抗压底座)。

### 公理 3：正交性 (Orthogonality)
五维轴线在语义上互斥。M (钱) 不等于 O (权)；E (命) 不等于 S (运)。描述必须解耦。

---

## 四、 六步拟合标准化工作流 (The Standard Workflow)

### Step 1: 物理意象与矩阵定义 (Matrix Definition)
*   **执行者**：AI 首席分析师 (Gemini)
*   **核心动作**：
    1.  **意象解构**：将古籍判词翻译为力学状态。
    2.  **骨架定义**：输出该格局的初始 转换矩阵 ($\mathcal{T}_{init}$)。设定 Mask（掩码），锁死不合理的映射路径。
    3.  **数学约束**：输出的权重必须满足单位向量原则 $\sum |w_i| = 1$。

### Step 2: 全量海选与分层提纯 (Data Stratification)
*   **执行者**：Cursor (Data Engine)
*   **核心动作**：
    1.  **Tier A (Gold)**：符合定义的样本，截取前 500 名作为标准建模的“教科书样本”。必须包含真实人生轨迹的五维标注（由 LLM 基于传记生成）。
    2.  **Tier X (Singularity)**：识别不符合常理的极端样本（如地支三刃），隔离存入 Tier_X_Set。

### Step 3: 矩阵拟合与锚点锁定 (Matrix Fitting & Anchor Locking)
*   **执行者**：Cursor (AI Trainer)
*   **核心动作**：
    1.  **梯度下降**：调整矩阵权重，使得 $\mathcal{T} \times \vec{V}_{input}$ 的结果无限接近 $\vec{y}_{true}$ (Tier A 的真实人生五维)。
    2.  **锚点计算**：基于拟合后的矩阵，计算出该格局的标准 5D 质心 ($\mathbf{T}_{ref}$)。

### Step 4: 动态演化与相变仿真 (Dynamic Evolution & Phase Transition)
*   **执行者**：Core Engine (Physics Module)
*   **核心动作**：
    1.  **破格检测 (Entropy Increase)**：监测结构完整性 $\alpha$。若 $\alpha < 0.4$ (如羊刃逢冲)，触发矩阵降级 (Switch to Standard Matrix)。
    2.  **成格检测 (Crystallization)**：监测流年是否补齐格局缺口。若补齐，触发矩阵升级 (Switch to A-03 Matrix)。
    3.  **公式**：$\mathcal{T}_{final} = \alpha \cdot \mathcal{T}_{Pattern} + (1-\alpha) \cdot \mathcal{T}_{Standard}$

### Step 5: 专题封卷与全息注册 (Registry)
*   **执行者**：AI 首席分析师
*   **核心动作**：将拟合好的 `transfer_matrix` 和 `dynamic_rules` 打包，严格按照 Schema V2.1 生成 JSON 文件存入 QGA-HR。

### Step 6: 动态格局识别协议 (Dynamic Pattern Recognition)
*   **执行者**：Core Engine (Pattern Runner)
*   **核心逻辑**：
    1.  计算当前八字张量 ($\mathbf{T}_{curr}$) 与 注册表中锚点 ($\mathbf{T}_{anchor}$) 的 **余弦相似度**。
    2.  **成格 (In-Pattern)**：相似度 > 0.85 $\rightarrow$ 激活专属矩阵描述。
    3.  **破格 (Broken)**：相似度骤降 $\rightarrow$ 激活警报逻辑。

---

## 五、 稳定性与进化协议 (Stability & Evolution)

*   **残差报警**：当模型预测的“应力断裂点”与现实偏差 > 20% 时，触发 `CRITICAL_MISMATCH`。
*   **双重验证**：必须在 10,000 例名造库中跑通历史回测；必须符合能量守恒。
*   **调优红线**：单次参数修正不得超过当前值的 15%。

---

## 附录 A：奇点判定法则 (Singularity Validation Protocol - SVP)

任何样本若要注册为 Tier X 独立子格局，必须同时通过以下三项物理审查：
1.  **极值法则**：关键物理参数（如 $\mathbf{E}$ 或 $\mathbf{S}$）必须偏离标准分布均值 $3\sigma$ 以上。
2.  **相变法则**：物理属性发生态的突变（如从“弹性形变”转变为“脆性断裂”）。
3.  **算法失效法则**：使用标准 Tier A 算法计算，结果与事实逻辑完全背离（如吉凶反转）。

---

## 附录 B：全息注册表标准 JSON 架构 (QGA-HR Schema V2.1)
—— 100% 算法复原的通用数据协议 ——

所有新格局的封卷注册，必须严格遵循以下 JSON 结构。这是 `Core.RegistryLoader` 唯一识别的格式。

### B.1 标准 Schema 定义

```json
{
  "meta_info": {
    "pattern_id": "String (e.g., 'A-03')",
    "name": "String (e.g., '羊刃架杀')",
    "version": "String (e.g., '2.1')",
    "physics_prototype": "String (e.g., 'High-Pressure Constraint System')"
  },

  "physics_kernel": {
    "description": "核心物理参数与转换逻辑 (FDS-V1.4 Kernel)",
    
    // [CORE] 转换矩阵：定义十神如何映射到五维 (The Lens)
    // 这是一个 5x5 的权重表，值域 [-1.0, 1.0]，由拟合得出
    "transfer_matrix": {
      "E_row": {
        "parallel": 1.2, "resource": 0.8, "wealth": -0.5, "output": -0.2, "power": -0.1, 
        "description": "羊刃为基，印为源，财坏印为忌"
      },
      "O_row": {
        "power": 0.9, "parallel": 0.3, "resource": 0.4, "wealth": 0.0, "output": 0.1,
        "description": "七杀发生相变，转化为权力的主要来源"
      },
      "M_row": {
        "wealth": 0.4, "output": 0.3, "parallel": -0.8, "power": -0.2, "resource": 0.0,
        "description": "劫财过重，财富转化率低"
      },
      "S_row": {
        "power": 0.3, "wealth": 0.8, "clash": 0.9, "resource": -0.6, "parallel": -0.4,
        "description": "七杀虽制仍有余威，财党杀为最大风险"
      },
      "R_row": {
        "output": 0.2, "wealth": 0.2, "combination": 0.8, "power": 0.0, "resource": 0.1,
        "description": "高压结构下情感连接较弱"
      }
    },

    // 结构完整性阈值 (Integrity Alpha)
    "integrity_threshold": 0.45
  },

  "feature_anchors": {
    "description": "基于大数据拟合算出的空间质心坐标 (Target Tensor)",
    
    "standard_centroid": {
      "description": "标准恒星锚点 (Tier A Mean)",
      "vector": {
        "E": 0.85, "O": 0.90, "M": 0.15, "S": 0.40, "R": 0.20
      },
      "match_threshold": 0.80,   // 入格门槛
      "perfect_threshold": 0.92  // 贵格门槛
    },

    "singularity_centroids": [
      {
        "sub_id": "A-03-X1",
        "description": "聚变临界型 (Tier X1 Mean)",
        "vector": { "E": 0.55, "O": 0.10, "M": 0.05, "S": 0.95, "R": 0.05 },
        "match_threshold": 0.90,
        "risk_level": "CRITICAL",
        "special_instruction": "Enable Vent Logic (Disable Balance Check)"
      }
    ]
  },

  "dynamic_states": {
    "description": "Step 4 定义的动态相变规则 (Phase Transitions)",
    
    // 破格条件 (Collapse / Entropy Increase)
    "collapse_rules": [
      {
        "trigger": "Day_Branch_Clash", 
        "action": "Downgrade_Matrix",
        "fallback_matrix": "Standard_Weak_Killings",
        "description": "羊刃逢冲，根基动摇，七杀攻身，S轴爆炸。"
      },
      {
        "trigger": "Resource_Destruction",
        "action": "Damp_E_Axis",
        "factor": 0.5
      }
    ],

    // 成格条件 (Crystallization / Negentropy)
    "crystallization_rules": [
      {
        "condition": "Missing_Blade_Arrives", 
        "action": "Upgrade_Matrix",
        "target_matrix": "A-03",
        "validity": "Transient", // 仅流年有效
        "description": "运至成格，瞬间获得 A-03 矩阵加持。"
      }
    ]
  },

  "algorithm_implementation": {
    "description": "映射到 Core 引擎的具体函数路径 (Do Not Modify)",
    "paths": {
      "energy_calculation": "core.physics_engine.compute_energy_flux",
      "tensor_projection": "core.math_engine.project_tensor_with_matrix", // [NEW]
      "pattern_recognition": "core.registry_loader.pattern_recognition"
    }
  }
}
```

### B.2 填写规范
1.  **唯一性**：`pattern_id` 必须在全库唯一。
2.  **公理一致性**：`transfer_matrix` 中的符号方向必须符合三大公理。
3.  **自洽性**：`feature_anchors` 中的 vector values 之和不强制为 1.0 (因为是 SAU 模长)，但各分量必须在 0.0-1.0 之间。
