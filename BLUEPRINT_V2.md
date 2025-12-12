# Antigravity App V2.0 - 核心架构与模型蓝图

## 1. 核心哲学：量子态势场 (Quantum Field)
我们将八字（Bazi）视为一个动态的、不确定的“立体网格量子场”，而非静态的干支组合。

- **场体结构**: 立体长方体网格。
  - **Z轴 (势能 $E_{god}$)**: 决定粒子（十神）的能量高低（得令、通根、得生）。
  - **X/Y轴 (耦合 $C_{coupling}$)**: 决定粒子间的作用效率（距离衰减、阴阳自旋）。

## 2. 量化基准 (Quantification Formulas)

### A. 粒子势能 ($E_{god}$) - Z轴高度
势能由三个核心来源加权求和得出：
- **月令 (Time Resonance)**: 权重 `+4.0` (最高，宇宙同频)。
- **通根 (Grounding)**: 权重 `+3.0` (地支藏干共振)。
- **得生 (Catalyst)**: 权重 `+1.0` (能量紧贴传递)。

### B. 耦合强度 ($C_{final}$) - 相互作用
$$ C_{final} = (C_{base} \times F_{yinyang}) \times F_{distance} $$

- **$F_{distance}$ (距离衰减)**:
  $$ F_{distance} = \frac{1}{D_{ij}^\gamma} $$
  *(其中 $D_{ij}$ 为欧几里得距离，$\gamma \approx 1.5$ 待贝叶斯优化)*

### C. 宏观之相 ($W_{career}$)
在冷启动阶段，使用社会学经验权重预设模型参数：
| 十神 (God) | 权重 | 含义 |
| :--- | :--- | :--- |
| 正官 (Official) | 0.30 | 权力、平台 |
| 七杀 (Killer) | 0.25 | 挑战、成就 |
| 正印 (Seal) | 0.15 | 名誉、背景 |
| ... | ... | ... |

## 3. 实现流水线 (Pipeline Implementation)

### 阶段一：数据结构化 (Data Structuring) ✅ [Done]
- **模块**: `learning/theory_miner.py`, `learning/knowledge_processor.py`
- **功能**: 
  - 利用本地 LLM 从古籍/视频中提取结构化 JSON。
  - **关键特性**: 自动提取 `vreal_score` (0-100) 作为 Ground Truth。

### 阶段二：向量生成 (Vector Generation) ✅ [Done]
- **模块**: `core/vectorizer.py`
- **功能**:
  - 输入：八字排盘 JSON。
  - 输出：**93维混合向量** ($X$)。
    - **前5维**: 量子势能场 ($E_{wood}, E_{fire}...$)，基于上述物理公式计算。
    - **后88维**: 原始 One-Hot 拓扑，保留原始信息供模型学习残差。
  - 能够加载数据库案例，生成训练集 $(X, Y)$。

### 阶段三：模型训练 (Model Training) 🔄 [In Progress]
- **模块**: `core/trainer.py`, `train_model.py`
- **算法**: 支持向量机 (SVR) / 岭回归 (Ridge)。
- **状态**: 基础框架已就绪，依赖 `scikit-learn`。
- **冷启动策略**: 若无数据，模型应基于 $W_{career}$ 等先验权重进行初始化（待完善）。

### 阶段四：迭代核心 (Iteration Core) 📅 [Todo]
- **目标**: 贝叶斯迭代校正。
- **逻辑**: 根据 $E_{pred}$ (预测) 与 $V_{real}$ (现实) 的误差，反向修正 $\gamma$ (衰减指数) 和 $W_E$ (基础权重)。

## 4. 任务清单 (To-Do List)

- [x] **Phase 1: Structuring**: 实现 LLM 提取 `vreal_score`。
- [x] **Phase 2: Vectorization**: 实现基于物理公式的 $E$ 和 $C$ 计算逻辑。
- [ ] **Phase 3: Training**: 
  - [x] 创建 `Trainer` 类。
  - [x] 创建 `train_model.py` 入口。
  - [ ] **Critical**: 确保生产环境 `scikit-learn` 安装成功。
  - [ ] **Feat**: 实现“冷启动”逻辑，无数据时直接加载物理规则权重。
- [ ] **Phase 4: Feedback Loop**: 
  - [ ] 实现参数自动调优接口 (`Optimizer`)。

## 5. 当前问题 (Issues)
- `pip install scikit-learn` 在 WSL 环境下可能需要 `--break-system-packages` 或使用 venv (已尝试自动修复)。
- 数据库目前可能缺乏足够的“带评分案例”进行有效训练。需考虑从 Rule 库生成合成数据。
