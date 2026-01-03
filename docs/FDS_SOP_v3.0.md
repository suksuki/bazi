🏛️ QGA 正向拟合与建模标准操作程序 (FDS-SOP-V3.0)
—— 六步拟合工作流与操作协议规范 ——

**版本**: V3.0 (Precision Physics & Statistical Manifolds)
**修订**: Genesis Protocol, Safety Protocols Injection & Metadata Enforcement
**生效日期**: 2025-12-31
**状态**: ENFORCED (强制执行)
**性质**: 标准操作程序 (Standard Operating Procedure)

> **关联文档**: 本SOP规范必须与 `FDS_ARCHITECTURE_v3.0.md` (架构规范) 配合使用。
> 架构规范定义"是什么"和"为什么"，本SOP规范定义"怎么做"。

---

## 核心依赖声明 (Core Dependencies)

**重要**: 本SOP是通用执行框架，不包含任何具体格局的硬编码逻辑。

在启动任何拟合任务前，必须提供符合 `Schema-V3.0` 定义的 **格局配置文件 (Pattern Manifest)**，通常命名为 `pattern_manifest.json`。

**配置文件必须包含以下两个标准数据块**:

1. **`classical_logic_rules`** (古典逻辑规则):
   - 描述古典格局成格条件的标准化逻辑表达式
   - 用于 Step 2.1 L1 逻辑普查阶段的样本过滤
   - 格式: 布尔表达式树 (Boolean Expression Tree)，支持 AND, OR, GT, LT, EQ 等操作符
   - 示例格式: `(Var_A > Threshold) AND (Var_B < Var_C * Coeff)`

2. **`tensor_mapping_matrix`** (张量映射矩阵):
   - 描述十神到五维张量 ($T_{fate} = [E, O, M, S, R]$) 的初始映射权重表
   - 用于 Step 1 物理原型定义的矩阵初始化
   - 格式: 权重矩阵，行=十神，列=EOMSR五维
   - 必须标记 `strong_correlation` (强相关) 权重项，这些项在拟合过程中将被锁定

**SOP约束**:
- **严禁硬编码**: 所有格局相关的逻辑和权重必须从配置文件读取
- **配置验证**: 缺少上述配置时，SOP流程必须在 Step 0（预处理阶段）终止并报错
- **配置Schema**: 详细的配置文件格式定义见 `FDS_ARCHITECTURE_v3.0.md` 第六章（格局配置文件 Schema）

---

## 一、 六步拟合标准化工作流

### Step 0: 格局配置注入 (Pattern Manifest Injection) [CRITICAL]

**定义**:
这是启动拟合流水线的**强制前置步骤**。此步骤负责将"法理（KMS）"固化为"法律（Manifest）"，并注入到 SOP 执行环境中。**SOP 严禁在未完成此步骤的情况下直接进入 Step 1。**

**操作输入**:

- **来源 A (本地生成)**: FDS-KMS 系统输出的 JSON 文件。
- **来源 B (云端立法)**: 经由架构师确认的、由通用 LLM 依据标准 Schema 生成的 JSON 代码。

**操作协议 (Protocol)**:

1. **获取 (Acquisition)**:
   - 依据 `FDS_ARCHITECTURE_v3.0` 的 Schema 定义，获取目标格局的配置内容。
   - **必查项**: 必须包含 `classical_logic_rules`（逻辑树）和 `tensor_mapping_matrix`（权重表）。

2. **校验 (Verification)**:
   - **Schema 校验**: 检查十神代码是否为标准代码 (`ZS`, `PC` 等)，严禁使用过时代码 (`EG`, `IR`)。
   - **物理校验**: 检查 `strong_correlation`（强相关）字段是否已定义物理锁定项（如：食神格必须锁定 ZS-O 正相关）。

3. **固化 (Solidification)**:
   - 将校验通过的 JSON 内容保存为标准文件。
   - **标准路径**: `./config/patterns/pattern_manifest_{PATTERN_ID}.json`
   - **示例**: `./config/patterns/pattern_manifest_B-01.json`

4. **加载 (Loading)**:
   - SOP 启动脚本 (`fds_sop_runner.py`) 必须通过命令行参数 `--manifest` 显式读取此文件。
   - **系统行为**: 若文件不存在或 Schema 校验失败，系统必须抛出 `ManifestError` 并立即终止进程，**严禁使用默认参数继续运行**。

**输出产物**:

- 已固化的本地文件: `pattern_manifest_{PATTERN_ID}.json`
- 校验通过日志: `manifest_validation.log`

---

### Step 1: 物理原型定义

**目标**: 根据外部配置构建初始转换矩阵，锁定物理路径的正负倾向。

**操作输入**:
- 读取格局配置文件字段: `tensor_mapping_matrix` (张量映射矩阵)
- 读取格局配置文件字段: `strong_correlation` (强相关权重标记)

**操作内容**:

1. **矩阵构建**:
   - 初始化一个 $N_{ten\_gods} \times 5$ 的权重矩阵 $W$
   - 行维度: 十神类型（如正官、偏财、食神等）
   - 列维度: 五维命运张量 $T_{fate} = [E, O, M, S, R]$

2. **权重注入**:
   - 从配置文件的 `tensor_mapping_matrix` 字段读取权重值
   - 将权重值填入矩阵 $W$ 的对应位置
   - **SOP规范**: 对于配置中未定义的映射关系，默认初始化为 `0.0` 或高斯噪声（从 `@config.physics.init_noise_std` 读取）

3. **强相关权重锁定**:
   - 读取配置文件中的 `strong_correlation` 标记
   - 标记为强相关的权重项将被锁定（Freeze），在后续拟合过程中不可修改
   - **SOP约束**: 必须保留古典命理的骨架结构，不允许完全自由拟合

4. **公理校验**:
   - 检查导入的权重矩阵是否违背"符号守恒公理"（检查符号方向是否符合物理常识）
   - 检查是否违背"正交解耦公理"（检查是否存在单一十神同时极强地正向映射到互斥的两个维度，如M和O）
   - 校验失败时，终止流程并报告配置错误

**输出产物**:
- 初始转换矩阵 $W$（包含锁定标记）
- 公理校验报告
- 强相关权重锁定清单

---

### Step 2: 样本分层与海选 (Census & Stratification)

**目标**: 从518,400样本库中筛选、分层并提纯格局种子样本。

#### 2.1 L1 逻辑普查 (Classical Census) [强制执行]

**操作输入**:
- 读取格局配置文件字段: `classical_logic_rules` (古典逻辑规则)
- 样本数据库: `holographic_universe_518k.jsonl` (518,400个样本)

**操作步骤**:

1. **加载逻辑规则**:
   - 从配置文件的 `classical_logic_rules` 字段读取布尔表达式树
   - **SOP规范**: 表达式格式必须支持标准操作符: `AND`, `OR`, `NOT`, `GT` (大于), `LT` (小于), `GTE` (大于等于), `LTE` (小于等于), `EQ` (等于)
   - 表达式变量必须引用样本的特征字段（如十神数量、通根状态等）

2. **动态执行过滤**:
   - 针对518,400个样本，逐行解析并执行逻辑表达式
   - **SOP约束**: 严禁在代码中硬编码 `if ten_gods['EG'] > 10` 这样的具体逻辑
   - 所有逻辑必须从JSON配置文件的 `classical_logic_rules` 中动态解析
   - 系统必须实现一个通用的表达式解析引擎（如JSONLogic或自定义DSL解析器）

3. **统计命中样本**:
   - 记录符合逻辑表达式的样本数量 $N_{hit}$
   - 记录每个命中样本的唯一标识符 `Case_ID`
   - 生成命中样本列表

4. **计算基础丰度**:
   - **算法**: 古典海选丰度 (Classical Abundance)
   
$$
\text{Abundance}_{base} = \frac{N_{hit}}{518,400} \times 100\%
$$

5. **归档丰度值**:
   - 将 $\text{Abundance}_{base}$ 存入元数据
   - 作为 Step 6 调校的 **法定参考值 (Ground Truth)**
   - **重要**: 此值不可随意修改，必须作为验收基准

**输出产物**:
- $N_{hit}$ (绝对命中数)
- $\text{Abundance}_{base}$ (基础丰度值)
- 样本标识列表（`Case_ID`数组）
- 逻辑表达式执行报告

#### 2.2 L2 交叉验证

**操作步骤**:
- 匹配样本的人生轨迹真值 $y_{true}$
- 验证样本与格局定义的逻辑一致性
- 排除异常样本

**输出产物**:
- 验证后的样本集
- 异常样本清单

#### 2.3 L3 提纯 (Tier A)

**操作步骤**:
- 锁定 500+ 例黄金种子样本
- 确保样本质量符合统计流形建模要求

**输出产物**:
- Tier A 种子样本集（≥500例）

---

### Step 3: 矩阵拟合

**目标**: 优化权重，最小化物理损失函数，产出格局专属的"转换透镜"矩阵。

**操作输入**:
- Step 1 输出的初始转换矩阵 $W$（包含锁定标记）
- Step 2 输出的Tier A种子样本集

**操作步骤**:

1. **权重锁定设置**:
   - 读取Step 1中标记的 `strong_correlation` 权重项
   - **SOP约束**: 必须锁定（Freeze）这些权重项，仅允许微调其他参数
   - 锁定机制确保保留古典命理的骨架结构，避免过度拟合破坏物理逻辑

2. **构建物理损失函数**:
   - 基于种子样本的5D特征张量 $T_{fate}$ 构建损失函数
   - 损失函数必须包含符号守恒惩罚项（确保权重符号符合物理常识）
   - 损失函数必须包含拓扑特异性惩罚项（确保核心权重显著高于背景噪声）

3. **实施投影梯度下降优化**:
   - 使用投影梯度下降（Projected Gradient Descent）方法
   - **确保符号守恒**: 对于标记为强相关的权重项，在优化过程中保持符号不变
   - 仅对未锁定的权重项进行梯度更新

4. **迭代优化权重矩阵**:
   - 迭代优化过程，最小化损失函数
   - 监控损失函数收敛情况
   - 设置最大迭代次数和收敛阈值（从 `@config.optimization.max_iterations` 和 `@config.optimization.convergence_threshold` 读取）

5. **物理公理验证**:
   - 验证权重符合**拓扑特异性公理**（核心反应堆粒子权重显著高于背景噪声）
   - 验证权重符合**正交解耦公理**（五维轴线语义互斥）
   - 验证**符号守恒公理**（权重符号方向符合物理常识）
   - 验证失败时，调整优化参数或重新检查配置文件

**输出产物**:
- 优化后的转换矩阵 $W_{optimized}$（权重矩阵）
- 损失函数收敛曲线
- 物理验证报告
- 权重锁定状态报告（哪些权重被锁定，哪些被优化）

---

### Step 4: 动态演化机制

**目标**: 定义状态机，包含"破格"与"激活/相变"逻辑，支持流年大运介入时的状态重映射。

**操作步骤**:
1. 设计状态机状态定义（标准态、激活态、破格态等）
2. 定义状态转换条件
3. 实现流年大运介入逻辑
4. 实现状态重映射机制

**输出产物**:
- 状态机定义文档
- 状态转换规则表
- 动态演化算法实现

---

### Step 5: 全息封卷与协议植入 (Assembly & Protocols) [CRITICAL]

**目标**: 完成格局的完整封装，植入安全门控，标准化元数据，处理奇点样本。

#### 5.1 安全门控植入 (Safety Gate Injection) [强制执行]

**操作步骤**:

1. **身旺门控 (E-Gating)**:
   - 强制植入 `@config.gating.weak_self_limit`
   - 确保能量维度 (E) 的门控规则生效

2. **排他门控 (R-Gating)**:
   - 强制植入 `@config.gating.max_relation`
   - 确保关系维度 (R) 的门控规则生效

**验证要求**:
- 所有门控参数必须从配置文件读取，严禁硬编码
- 门控逻辑必须通过单元测试验证

#### 5.2 元数据标准化 (Metadata) [强制执行]

**操作步骤**:

必须为每个格局设置以下元数据字段:

1. **category** (格局类别):
   - 必须枚举为以下值之一: `WEALTH`, `POWER`, `TALENT`, `SELF`
   - 不可使用其他值

2. **display_name** (英文索引名):
   - 格式: 英文名称，采用PascalCase或Title Case
   - 示例: `Indirect Wealth`, `Eating God`, `Direct Officer`

3. **chinese_name** (中文展示名):
   - 格式: 简体中文名称
   - 示例: `偏财格`, `食神格`, `正官格`

4. **version** (版本号):
   - 必须设置为 `"3.0"`

**输出产物**:
- 完整的元数据字典
- 元数据验证报告

#### 5.3 量子架构注册 (QGA Topic Registration) [CRITICAL]

**目标**: 将封卷后的数据封装为 QGA 标准消息，并注册到主题频道。

**操作协议**:

1. **构建 Topic 信封**:
   - 根节点必须包含 `topic`: 固定值为字符串 `"holographic_pattern"`
   - 根节点必须包含 `schema_version`: 固定值为 `"3.0"`

2. **组装 Data 载荷**:
   - 将 `meta_info`, `feature_anchors` (流形参数), `population_stats` (丰度统计), `benchmarks` (奇点) 全部放入 `data` 字段
   - **数据脱钩检查**: 再次确认 `data` 中不包含任何原始八字字符串（Privacy Check）

3. **物理落盘**:
   - **路径规范**: `./registry/holographic_pattern/{PATTERN_ID}.json`
   - **示例**: `./registry/holographic_pattern/A-01.json`
   - **系统行为**: 写入成功后，应触发（或模拟触发）消息队列的 `PUB` 事件

**输出产物**:
- 符合 QGA 规范的 JSON 文件
- 文件路径: `./registry/holographic_pattern/{PATTERN_ID}.json`

#### 5.4 奇点样本存证 (Singularity Benchmarking) [强制执行]

**物理逻辑**:
- 对于判定的奇点样本（Singularity），系统**不再进行流形平均化**（即不计算 $\mu$ 和 $\Sigma$），而是采用**全息存证**模式。
- 奇点判定标准：样本到种子流形的马氏距离 $D_M \gg \text{threshold}$，且样本数量 $N < \text{min\_samples}$（无法形成统计流形）。

**操作步骤**:

1. **奇点判定**:
   - 计算每个样本到种子流形的马氏距离 $D_M$
   - 若 $D_M > \text{threshold}$ 且 $N < \text{min\_samples}$，判定为奇点

2. **存证内容准备**:
   - 保存 5D 特征张量 $T_{fate} = [E, O, M, S, R]$
   - 保存样本唯一标识符 `Case_ID`（作为指针，不保存原始八字字符串）
   - 计算 `distance_to_manifold`（到标准流形的马氏距离）
   - 计算 `abundance`（该奇点在总样本中的占比）

3. **存储格式**:
   ```json
   {
     "benchmarks": [
       {
         "t": [E, O, M, S, R],  // 5D特征张量
         "ref": "Case_ID",        // 指向原始数据的索引
         "distance_to_manifold": 3.45,
         "abundance": 0.00543
       }
     ]
   }
   ```

4. **索引关联**:
   - `Case_ID` 作为**指针**，指向 `holographic_universe_518k.jsonl` 或数据库中的完整原始数据
   - 完整数据包括：原始八字、大运、人生轨迹真值 $y_{true}$

**识别逻辑（运行时）**:
- 在测试真实八字时，若判定为非主流形（$D_M > \text{threshold}$），则激活 **最近邻检索 (Nearest Neighbor Search)**
- 通过计算输入张量 $T_{input}$ 与 `benchmarks` 中所有奇点张量的**欧氏距离**或**余弦相似度**，锁定最接近的 1-3 个奇点样本
- **判定基准**：若最小距离 $d_{min} < \epsilon$（$\epsilon$ 为相似度阈值），则判定命中该子专题

**应用场景**:
- 当输入八字偏离标准流形时，系统返回：
  > "检测到该八字偏离标准流形，高度匹配奇点样本 **#CASE-9527**。该样本在 5D 空间中的表现为：高能量、极高剪切力。历史记录显示该类命造多发于...（调用 $y_{true}$）。"
- 这种基于**真实坐标点**的对比，比基于"模糊公式"的对比要准确得多。

**输出产物**:
- `benchmarks` 数组（包含所有奇点样本的5D张量和索引）
- 奇点判定报告

---

### Step 6: 精密模式识别与负载验收 (Recognition)

**目标**: 实现精密评分算法，并进行验收测试，确保识别率符合预期。

#### 6.1 精密评分算法 (Enhanced Precision Score)

**计算公式**:

$$
\text{Score} = (W_{sim} \cdot \text{CosSim} + W_{dist} \cdot e^{-D_M^2 / 2\sigma^2}) \cdot G_{sai}
$$

**参数说明**:
- $W_{sim}$: 相似度权重（从 `@config.physics.precision_weights.similarity` 读取）
- $W_{dist}$: 距离权重（从 `@config.physics.precision_weights.distance` 读取）
- $\text{CosSim}$: 余弦相似度
- $D_M$: 马氏距离
- $\sigma$: 高斯衰减参数（从配置读取）
- $G_{sai}$: 安全门控因子（Safety Gate Factor）

**操作要求**:
- **严禁硬编码**: 所有参数必须从配置中心读取
- 参数路径示例: `@config.physics.precision_weights.similarity`

#### 6.2 负载验收与丰度对撞 (Load Acceptance & Abundance Collision)

**目标**: 使用物理引擎（马氏距离判定）对全量样本进行识别率计算，与逻辑规则（基准丰度）进行对撞验证。

**操作步骤**:

1. **特征捕获 (Feature Extraction)**:
   - SOP必须从所有符合 `classical_logic_rules` 的样本中提取统计特征
   - 计算均值向量 $\mu$ 和协方差矩阵 $\Sigma$
   - 将 $\mu$ 和 $\Sigma$ 存入registry的 `feature_anchors.standard_manifold` 字段

2. **物理判别 (Physics Recognition)**:
   - 执行全量518,400样本扫描时，**严禁使用**布尔逻辑过滤（`classical_logic_rules`）
   - 必须仅使用马氏距离判定：
     - 对每个样本计算5D张量 $T_{fate}$
     - 计算马氏距离: $D_M = \sqrt{(T_{fate} - \mu)^T \Sigma^{-1} (T_{fate} - \mu)}$
     - 判定准则: 若 $D_M < \theta$（阈值从 `@config.physics.thresholds.mahalanobis` 读取），则计为命中
   - 统计识别率: $\text{RecognitionRate}_{actual} = \frac{\text{命中样本数}}{\text{总样本数}} \times 100\%$

3. **对撞验收 (Collision Acceptance)**:
   - 获取基准丰度: $\text{Abundance}_{base}$（从registry的 `population_stats.base_abundance` 读取）
   - 计算偏差: $\Delta = |\text{RecognitionRate}_{actual} - \text{Abundance}_{base}|$
   - **纠偏逻辑**: 若 $\Delta > \text{tolerance}$（从 `@config.recognition.tolerance` 读取，标准值0.02），强制进入纠偏周期
     - 调整马氏距离阈值 $\theta$
     - 重新执行物理判别，直到偏差在可接受范围内

4. **验收标准**:
   - $\Delta \le \text{tolerance}$（容差值从配置读取，标准值2.0%）
   - 所有物理公理验证通过
   - 所有安全门控生效

**输出产物**:
- 识别准确率报告（物理判定结果）
- 偏差分析报告（物理 vs 逻辑）
- 验收测试报告（PASS/FAIL判定）
- 最终参数配置（如果进行了纠偏）

#### 6.3 全息重合度审计 (IoU Audit) [CRITICAL]

**目标**: 通过IoU（交集率）指标深度审计物理模型与古典逻辑的空间分歧，揭示物理发现的真实价值。

**核心指标**:
- 不再以 $\Delta$（偏差）作为唯一通过标准
- **强制要求**: 必须输出 **IoU (Intersection over Union)**

**操作步骤**:

1. **集合统计**:
   - 逻辑匹配集合 $L$: 所有通过 `classical_logic_rules` 判定的样本
   - 物理匹配集合 $P$: 所有通过马氏距离判定的样本
   - 交集 $I = L \cap P$: 同时被两种方法判定的样本
   - 并集 $U = L \cup P$: 至少被一种方法判定的样本

2. **IoU计算**:
   $$
   \text{IoU} = \frac{|I|}{|U|} = \frac{\text{交集样本数}}{\text{并集样本数}}
   $$

3. **物理溢出分析**:
   - **物理扩展区**: $P \setminus L$（仅物理匹配，逻辑不匹配）
   - **逻辑独有区**: $L \setminus P$（仅逻辑匹配，物理不匹配）
   - 统计物理扩展区样本的特征，分析其共性

4. **阈值哲学判定**:
   - 若 IoU < 30%，必须撰写《物理溢出特征分析报告》
   - 说明物理模型为何发现了古典逻辑之外的样本
   - 将这些样本判定为 **"物理真理扩展 (Manifold Extension)"**
   - **合法性判定**: 物理扩展区样本具有极高的实战挖掘价值，是FDS系统对传统命理的重要补盲

**输出产物**:
- IoU审计报告
- 象限分析报告（逻辑独有区、物理扩展区、交集区）
- 物理溢出特征分析报告（如果IoU < 30%）
- 最终校准指标（deviation, iou, mef）

**验收标准**:
- $\Delta \le \text{tolerance}$（容差标准，默认10%）
- IoU值作为物理发现价值的衡量指标（而非失败标准）
- 物理扩展区样本特征分析完成

---

## 二、 奇点与子格局发现协议 (Discovery Protocol) [RESTORED]

**目标**: 规范系统如何从海量样本中发现"离群点"（奇点），并判断其是否具备晋升为"独立子格局"的资格（成格条件）。

### 2.1 奇点判定协议 (Singularity Detection)

**操作步骤**:

1. **距离计算**:
   - 计算每个样本到标准流形（均值向量 $\mu$）的马氏距离 $D_M$

2. **阈值判定**:
   - 若 $D_M > \text{threshold}$（通常取 $\text{threshold} = 3.0$ 或配置值），判定为**奇点候选**

3. **初步分流**:
   - 将所有奇点候选样本移入 `Singularity Pool`（奇点池）

**输出产物**:
- 奇点池（`Singularity Pool`）
- 奇点候选清单

### 2.2 子格局晋升协议 (Sub-Pattern Promotion) [核心成格条件]

**定义**: 这里定义了"一个新的子格局"是如何诞生的。

**晋升条件 (成格三要素)**:

1. **数量阈值 (Critical Mass)**:
   - 对奇点池进行聚类分析（如 DBSCAN 或 K-Means）
   - 若某聚类簇的样本数量 $N \ge \text{min\_samples}$（从配置读取，如 50 例），则满足数量条件

2. **轨迹一致性 (Trajectory Consistency)**:
   - 检查该聚类内样本的人生轨迹真值 $y_{true}$ 是否呈现**低方差**（即命运表现高度一致）
   - 若一致性分数 $C_{consistency} > \text{threshold}$（从配置读取），则满足轨迹条件

3. **物理可解释性 (Physics Explainability)**:
   - AI 尝试提取该聚类的共有特征（如"都有伤官且都有印"）
   - 若能生成符合 JSONLogic 语法的逻辑描述，则满足解释性条件

**执行动作**:

- **晋升 (Promote)**: 若满足上述三要素，系统自动为该聚类分配新的 `sub_pattern_id`（如 `A-01-S3`）
- **建模**: 对该新子格局执行 Step 0-6 完整拟合，生成独立的 $\mu$ 和 $\Sigma$
- **注册**: 将新子格局写入 Registry

**输出产物**:
- 子格局定义文档
- 子格局注册表条目（包含独立的 `pattern_id`）
- 子格局独立模型（$\mu$, $\Sigma$）

### 2.3 奇点存证协议 (Singularity Archiving)

**适用对象**: 无法晋升为子格局的"孤立奇点" ($N < \text{min\_samples}$)

**操作步骤**:

- 采用 **全息存证 (Holographic Benchmarking)** 模式
- 仅保存 5D 特征张量 $T_{fate} = [E, O, M, S, R]$ 和原始索引 `ref`
- 写入 `registry.json` 的 `benchmarks` 数组中，作为"判例"存在，用于 KNN 检索

**详细操作**: 见 **Step 5.4 奇点样本存证**

**输出产物**:
- `benchmarks` 数组（包含奇点样本的5D张量和索引）

---

## 三、 操作检查清单 (Checklist)

### 3.1 Step 0-6 完成度检查

- [ ] Step 0: 格局配置注入完成，Manifest 文件已校验并加载
- [ ] Step 1: 物理原型定义完成
- [ ] Step 2: L1逻辑普查完成，$\text{Abundance}_{base}$ 已归档
- [ ] Step 2: L2交叉验证完成
- [ ] Step 2: L3提纯完成（≥500例种子样本）
- [ ] Step 3: 矩阵拟合完成，物理公理验证通过
- [ ] Step 4: 动态演化机制定义完成
- [ ] Step 5.1: 安全门控植入完成（E-Gating, R-Gating）
- [ ] Step 5.2: 元数据标准化完成（category, display_name, chinese_name, version）
- [ ] Step 5.3: 量子架构注册完成（QGA Topic Registration，路径规范正确）
- [ ] Step 5.4: 奇点存证完成（如有奇点）
- [ ] Step 6: 精密评分算法实现完成
- [ ] Step 6: 验收测试通过（$\Delta \le \text{tolerance}$）

### 3.2 质量控制检查

- [ ] 所有参数从配置文件读取，无硬编码
- [ ] 所有物理公理验证通过（符号守恒、拓扑特异性、正交解耦）
- [ ] 所有安全门控生效
- [ ] 元数据格式符合规范
- [ ] 识别率偏差在可接受范围内

### 3.3 文档完整性检查

- [ ] 所有输出产物已生成
- [ ] 所有报告已归档
- [ ] 配置参数已记录
- [ ] 异常情况已记录

---

## 四、 注意事项与最佳实践

### 4.1 参数配置原则

- **零硬编码**: 所有数值参数必须从配置中心读取
- **单一真理源**: 任何算法调整，必须通过修改配置文件实现
- **版本控制**: 配置文件变更必须记录版本号和变更原因

### 4.2 物理公理遵守

在执行任何步骤时，必须严格遵守三大物理公理：
1. **符号守恒**: 权重优化必须符合物理常识的方向性
2. **拓扑特异性**: 核心粒子权重必须显著高于背景噪声
3. **正交解耦**: 五维轴线语义互斥，不得混淆

### 4.3 验收标准

- 识别率必须接近 $\text{Abundance}_{base}$（Step 2 归档的基准值）
- 偏差超过容差时必须回退调整
- 所有强制执行项（[强制执行]标记）必须完成

### 4.4 异常处理

- 样本数量不足时，必须记录原因并评估是否可继续
- 奇点样本必须妥善存证，不可丢弃
- 验收测试失败时，必须回退到上一步重新执行

---

**文档维护**: 本SOP规范与 `FDS_ARCHITECTURE_v3.0.md` 配套使用，任何架构变更必须同步更新本SOP。

