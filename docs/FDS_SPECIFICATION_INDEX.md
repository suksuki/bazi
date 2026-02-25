# FDS 规范文档索引 (FDS Specification Index)

**最后更新**: 2026-02  
**版本**: V5.5 智能数仓驱动  
**状态**: ✅ 核心规范就绪；SOP 执行以 **V5.5** 为准（以库治律、一键注库、OLAP 压力审计、流形健康度监测）；V5.1 已由 V5.5 继承

---

## 📚 核心规范文档 (Core Specifications)

### 🏛️ 三大核心支柱

| 层级 | 文档 | 版本 | 状态 | 职责 |
| :--- | :--- | :--- | :--- | :--- |
| **L1 物理架构** | `FDS_ARCHITECTURE_v3.0.md` | V3.0 | ✅ Ready | 定义数据结构、物理公理、Schema (What) |
| **L2 执行流程** | `sop/FDS_SOP_v5.5.md` | V5.5 | ✅ ENFORCED | 智能数仓驱动、一键注库、OLAP 压力审计、流形健康度 (How) |
| **L2 执行流程（参考）** | `sop/FDS_SOP_v5.1.md` | V5.1 | 📖 参考 | 元驱动架构，已由 V5.5 继承 |
| **L2 执行流程（参考）** | `sop/FDS_SOP_v5.0.md` | V5.0 | 📖 参考 | 已由 V5.1 继承 |
| **L2 法理原文** | `FDS_SOP_v3.0.md` | V3.0 | 📖 参考 | 物理公式与协议原文，已由 V5.0 继承 |
| **L3 法理逻辑** | `FDS_KMS_SPEC_v1.0-BETA.md` | V1.0-BETA | ✅ Ready | 定义逻辑生成、权重溯源 (Why) |

---

## 📋 文档详细列表

### 核心规范文档

1. **FDS_ARCHITECTURE_v3.0.md** (565行)
   - **性质**: 架构与理论规范
   - **内容**: 
     - 建模核心哲学（统计流形理论）
     - 五维命运张量定义
     - 三大物理公理
     - 全息注册表Schema
     - 格局配置文件Schema
     - 配置参数规范
   - **关联**: 与SOP和KMS规范配套使用

2. **sop/FDS_SOP_v5.0.md** (FDS SOP V5.0，正式执行版)
   - **性质**: 标准操作程序（物理流形、统计宪法与 AI 语义挂载统一协议）
   - **内容**: 核心依赖声明（含 semantic_core_dimensions）；八步拟合（Step 0–8）；奇点与子格局发现协议；强制性检查清单；注意事项与最佳实践
   - **关联**: 依赖 Architecture、KMS；继承 V3.0 法理与公式，收口 V4.x 的 HKB、QGA、流形修复、矩阵回溯
   - **执行**: 全量格局适用，以本版为准

3. **FDS_SOP_v3.0.md** (法理原文 / 参考)
   - **性质**: V5.0 的物理与协议原文参考
   - **内容**: 六步拟合工作流、马氏距离/IoU/丰度对撞等公式、奇点晋升三要素
   - **关联**: 执行流程以 `sop/FDS_SOP_v5.0.md` 为准

4. **FDS_KMS_SPEC_v1.0-BETA.md** (239行)
   - **性质**: 知识库与计算语文学规范
   - **内容**:
     - 系统核心哲学
     - 知识库架构分层
     - 核心数据模式（classical_codex.jsonl）
     - 自动化配置生成协议
     - 接口协议定义
     - 验证规则
     - 奇点判例索引接口
   - **关联**: 生成SOP所需的pattern_manifest.json

### 补充规范文档

5. **ALGORITHM_SUPPLEMENT_L3_PATTERNS.md** (1.5KB)
   - **性质**: 代码接口规范 (Implementation Interface Spec)
   - **内容**:
     - IPatternPhysics接口定义
     - 能量门控协议（Gating）
     - 拓扑分型标准（Topology）
     - 安全阀机制（Safety Valve）
   - **定位**: L3级代码接口规范，定义格局模块的代码实现标准
   - **受众**: 后端开发工程师（Antigravity Engine开发者）
   - **关联**: 连接架构文档（Schema）和代码实现（Interface）

---

## 三、 文档拓扑结构

```
🏛️ FDS 规范体系 (三层架构)

┌─────────────────────────────────────────────────────────────┐
│  Layer 1: 核心规范 (Core Specifications)                    │
│  ─────────────────────────────────────────────────────────  │
│  • FDS_ARCHITECTURE_v3.0.md      (物理架构与理论框架)       │
│  • sop/FDS_SOP_v5.5.md            (标准操作程序 · 执行以本版为准) │
│  • FDS_SOP_v3.0.md                (法理原文参考)             │
│  • FDS_KMS_SPEC_v1.0-BETA.md     (知识管理系统规范)         │
│  • ALGORITHM_SUPPLEMENT_L3_PATTERNS.md (L3格局接口规范)     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: 实现接口 (Implementation Interfaces)              │
│  ─────────────────────────────────────────────────────────  │
│  • ALGORITHM_SUPPLEMENT_L3_PATTERNS.md (格局拓扑协议)       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: 文档索引 (Documentation Index)                    │
│  ─────────────────────────────────────────────────────────  │
│  • FDS_SPECIFICATION_INDEX.md (本文档)                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、 文档状态说明

| 文档 | 状态 | 说明 |
|------|------|------|
| FDS_ARCHITECTURE_v3.0.md | ✅ ACTIVE | 核心架构规范，强制执行 |
| **sop/FDS_SOP_v5.5.md** | ✅ ENFORCED | **标准操作程序（执行以本版为准）** |
| FDS_SOP_v3.0.md | 📖 参考 | 法理与公式原文，已由 V5.0 继承 |
| FDS_KMS_SPEC_v1.0-BETA.md | ✅ ACTIVE | 知识管理系统规范（立法层） |
| ALGORITHM_SUPPLEMENT_L3_PATTERNS.md | ✅ ACTIVE | L3格局接口规范（实现层） |
| FDS_SOP_v4.0_AI.md | ❌ ARCHIVED | 已归档至 docs/archive/，由 V5.0 替代 |
| FDS_SOP_V4.1_Amendment.md | ❌ ARCHIVED | 已归档至 docs/archive/，已纳入 V5.0 |
| FDS_MODELING_SPEC_v3.0.md | ❌ ARCHIVED | 已归档，内容已拆分到其他规范 |
| PATTERN_SPECIFICATION_REVIEW.md | 📦 ARCHIVED | 已归档，历史审阅记录 |

**归档目录**: `docs/archive/` (历史文档和审阅记录)

### 格局立法状态 (Pattern Legislation Status)

| 格局 ID | 名称   | 状态       | 说明 |
|---------|--------|------------|------|
| A-01    | 正官格 | ✅ ACTIVE  | 已有封卷与索引 |
| A-02    | 七杀格 | ✅ ENFORCED| SOP V5.0 标杆，HKB/QGA 就绪 |
| A-03    | 偏财格 | ✅ ENFORCED| SOP V5.0 标杆，语义降维就绪 |
| A-04    | 正财格 | ✅ ENFORCED | 2026-02-24 封卷；518k 索引就绪；IoU 34.2%，财印两旺验收通过 |
| A-05    | 枭神格 | ✅ ENFORCED | 第 044 号纠偏：古典正名枭神格（原偏印格），判词须体现枭神夺食之危机感 |
| A-06    | 食神格 | ✅ ENFORCED | 2026-02-24 第 043 号封卷；518k 索引就绪；三专项验收清单见下 |
| A-07    | 伤官格 | ✅ ENFORCED | 2026-02-24 第 043 号封卷；伤官见官物理坍缩审计已归档 `audit_logs/` |
| A-08    | 正印格 | ✅ ENFORCED | 2026-02-24 第 043 号封卷；印星制伤语义验收见三专项清单 |
| A-09    | 建禄格 | ✅ ENFORCED | 第 044 号纠偏：古典正名建禄格（禄劫用财官），禁止称「比肩格」 |
| A-10    | 阳刃格 | ✅ ENFORCED | 第 044 号纠偏：古典正名阳刃格（极端应力、羊刃架杀），禁止称「劫财格」；IoU 关注 S 轴极值 |
| A-11    | 从财格 | 📋 046 立法 | 第 046 号审计师签发：弃命从财，TMM M 极值 E/O 坍缩；L1 锁定 E&lt;-0.8；仅镜像入库 |
| A-12    | 从杀格 | 📋 046 立法 | 第 046 号审计师签发：从杀，TMM S 峰值 E 消失；L1 锁定 E&lt;-0.8；仅镜像入库 |
| A-13    | 专旺格 | 📋 046 立法 | 第 046 号审计师签发：一气专旺，TMM E 爆表；L1 锁定 E&gt;1.8 且主气纯度；仅镜像入库 |

**第 046 号立法令**：A-11～A-13 古典定义与 TMM 由审计师签发；Cursor 只读式注库（Manifest、SQLite、RAG、HKB）。SOP V5.5 修正补丁：真值锁定协议 (V5.5-A)、立法流程强制化（审计师签发→指挥官审批→Cursor 镜像入库）。

**Step 6 物理生产（深水区海选）**：① A-11 日主坍缩度审计 `scripts/audit/audit_a11_e_collapse.py`；② A-13 流形纯度审计 `scripts/audit/audit_a13_purity.py`；③ A-11/A-12/A-13 518k 海选并迁入 DuckDB `scripts/run_a11_a12_a13_scan_and_migrate.py`；④ 法理一致性终审 `scripts/audit/v5_5_extreme_patterns_alignment.py` → `audit_logs/v5_5_extreme_patterns_alignment.json`；⑤ A-12 RAG 判词抽检验收要点见 `docs/audit/A12_RAG_VERDICT_CHECKLIST.md`。

封卷流程见 `docs/engineering/EDR_042_A04_A05_Manifest.md` 之「Step 6 终极封卷令」。  
**第 043 号终极封卷**：物理溢出报告已归档至 `audit_logs/audit_043_shangguan_jian_guan_report.json`。三专项语义验收脚本：`scripts/seal_043_final_verification.py`。**UI 降噪**：默认以白话版呈现判词，学术模式可折叠。  
**第 044 号纠偏（回归正八格法典）**：A-05→枭神格、A-09→建禄格、A-10→阳刃格；禁止十神名当格局名。**TMM 审计师签发**：四格局五维张量已按审计师真值覆盖（W_A05～W_A10）；L1 古典过滤器：阳刃=帝旺月令、建禄=临官月令（当前以十神强度为代理），枭神夺食预警已入 A-05。

#### V5.1 法理对齐校验位 (Classical Naming Seal)

以下格局名已完成古典正名，判词/HKB/Manifest 均以本表为准，禁止使用十神俗称替代。

| 格局 ID | 古典正名 | 备注 |
|---------|----------|------|
| A-01 | 正官格 | 王道之法 |
| A-02 | 七杀格 | 有制则发 |
| A-03 | 偏财格 | 众人之财 |
| A-04 | 正财格 | 己身之财 |
| A-05 | 枭神格 | 偏印夺食预警 |
| A-06 | 食神格 | 福寿发秀 |
| A-07 | 伤官格 | 伤官见官须缓冲 |
| A-08 | 正印格 | 印能化杀 |
| A-09 | 建禄格 | 月令临官（V5.2 收紧 pipeline） |
| A-10 | 阳刃格 | 月令帝旺，S 轴极值观测红线 |
| A-11 | 从财格 | 弃命从财，E&lt;-0.8（第046号） |
| A-12 | 从杀格 | 从杀，E&lt;-0.8（第046号） |
| A-13 | 专旺格 | 一气专旺，E&gt;1.8 主气纯度（第046号） |

**校验结论**：A-01～A-10 十神格局版图已完成法理化正名；古典真意语义块已注入 `config/hkb/hkb_params.json` → `pattern_classical_verdict`。

**A-10 阳刃格物理溢出观测红线**（第 044 号终审）：重跑 A-10 海选后，《物理溢出报告》须满足：**A-10 的 S 轴（应力）均值显著高于 A-01（正官格）**；若 A-10 应力表现平平，须通过 L1 强制锁定「月令帝旺」提纯样本。当前基线：`python3 scripts/fds_pattern_scanner.py --target A-10 --census` 已产出 `data_local/a10_full_points.npz`（约 38.8 万匹配）；同批 TMM 下 A-10 五维均值 (E,O,M,S,R) 中 S 轴已显著抬升，流形呈「刀尖」极值态。

#### 第 045 号 FDS 双核 2.0（RAG + SQL 数仓）— ✅ ENFORCED（并网验收通过）

| 组件 | 路径/说明 |
|------|-----------|
| **元数据层 SQLite** | `core/database/fds_registry.db`：`pattern_definitions`（A-01～A-10 古典正名 + TMM）、`audit_logs`（物理溢出/IoU/纠偏） |
| **特征层 DuckDB** | `core/database/fds_physics.duckdb`：`pattern_points`（518k 样本 5D 张量）；迁移脚本 `scripts/migrate_npz_to_duckdb.py`，物理等效性 max_diff &lt; 1e-7 |
| **PatternCollider** | 质心优先从 DuckDB 向量化取；无 DuckDB 数据时回退 NPZ/registry |
| **RAG 古典引证** | `config/rag/fds_classical_canon.json`（含 `meta_instruction`：先引古文后化白话，防复读机）→ ChromaDB `fds_classical_citations`；灌入 `python3 scripts/ingest_rag_classical_canon.py` |
| **判词链路** | 格局对撞 → DB TMM 定性 → RAG 召回古典判例 → LLM 生成判词；判词须含「古典原话引证」（见 `core/ai_engine.py` + `core/rag_canon.py`） |

**零风险自检**：① 物理等效性：DuckDB 与 NPZ 均值误差 &lt; 1e-7（迁移脚本已校验）。② 法典一致性：TMM 来自 manifest，由 `scripts/seed_registry_from_manifests.py` 灌入 SQLite。③ 判词深度：RAG 召回 + meta_instruction 注入，要求「至少引用一条」且「先引古文以定性，后化白话以指引」。

**并网后合拢**：DuckDB 秒级审计 SQL 示例见 `docs/audit/FDS_045_DuckDB_OLAP_Examples.md`（含 A-04 身强财弱坍缩查询）；2.0 全量物理基线 `python3 scripts/audit_v2_physics_baseline.py` → `audit_logs/v2_0_physics_baseline.json`。

**第 045 号正式封卷**（审计师签收）：RAG 书卷气抽检（A-02+A-10 羊刃架杀）合格；DuckDB A-04 坍缩异类抓取合格；判词质量与物理异类标记已纳入 2.0 治理。

**FDS 2.0 全息治理—后续建议（待排期）**  
- **判词质量监控看板**：DuckDB 随机抽各格局典型对撞（伤官见官、枭神夺食等），批量 RAG 判词，由 LLM 评价「古典引用契合度」与「白话指引实用度」。  
- **物理流形实时归位**：格局 TMM 微调时，用 DuckDB 一键对比调整前后样本丰度，避免法理修改导致大规模物理漂移。

#### 第 043 号三专项验收红线（A-06～A-10 封卷依据）

| 专项 | 观测 | 红线 |
|------|------|------|
| **伤官见官 (A-07 vs A-01)** | 抽 10 例 D_M>2.5 判词 | 须明确「财星/商业成果作缓冲带」；仅「口舌是非」不合格 |
| **羊刃架杀 (A-02 vs A-10)** | S 轴≥1.5 时 BalanceAuditor | 用神须指向印星(R 轴)/以柔克刚；判词须体现「英雄主义代价」「权力边缘冒险」 |
| **印星制伤 (A-07 vs A-08)** | 判词语义 | 须出现「才华合法化包装」或「学术沉淀化解批判锋芒」等表述 |

---

## 五、 历史记录文档（已归档）

**说明**: 以下文档记录了规范文档的演进历史，已移至 `docs/archive/` 目录。当前版本规范以核心规范文档为准。

- `FDS_SOP_v4.0_AI.md` - 已废弃，由 sop/FDS_SOP_v5.0.md 替代（2026-02-24）
- `FDS_SOP_V4.1_Amendment.md` - 已废弃，HKB/QGA 已纳入 V5.0（2026-02-24）
- `FDS_KMS_SPEC_v1.0_FINAL_ACCEPTANCE.md` - KMS规范的最终验收报告
- `FDS_SEPARATION_SUMMARY.md` - 规范分离总结报告（记录MODELING_SPEC分离过程）
- `FDS_ABSTRACTION_UPDATE.md` - 抽象化修正报告（记录SOP和Architecture抽象化过程）
- `PATTERN_SPECIFICATION_REVIEW.md` - 格局规范审阅报告
- `FDS_MODELING_SPEC_v3.0.md` - 已废弃的原始建模规范（内容已分离升级）

---

## 🔗 文档关联关系

### 数据流层（核心三支柱）

```
古籍文本
    ↓ 语义蒸馏
FDS_KMS_SPEC_v1.0-BETA.md (法理逻辑层/生成规范)
    ↓ 生成
pattern_manifest.json (格局配置文件)
    ↑ 定义Schema
FDS_ARCHITECTURE_v3.0.md (物理架构层/Schema定义)
    ↓ 理论支撑
sop/FDS_SOP_v5.0.md (执行流程层/使用规范)
    ↓ 执行工作流
格局拟合结果
```

### 代码实现层

```
ALGORITHM_SUPPLEMENT_L3_PATTERNS.md (代码接口层)
    ↓ 实现接口 (IPatternPhysics)
Antigravity Engine (格局模块实现)
    ↑ 注入配置
pattern_manifest.json
```

---

## 📖 使用指南

### 对于架构师
- 主要参考: `FDS_ARCHITECTURE_v3.0.md`
- 理解: 理论框架、物理公理、数据结构

### 对于开发人员
- 主要参考: `sop/FDS_SOP_v5.5.md`（执行以 V5.5 为准）
- 理解: 八步拟合与觉醒、HKB/QGA 注册、操作步骤、验收标准

### 对于知识库工程师
- 主要参考: `FDS_KMS_SPEC_v1.0-BETA.md`
- 理解: 逻辑提取、权重聚合、配置生成

### 对于后端开发工程师（引擎实现）
- 主要参考: `ALGORITHM_SUPPLEMENT_L3_PATTERNS.md`
- 理解: 代码接口、实现标准、安全机制

### 对于新成员
- 建议阅读顺序:
  1. `FDS_ARCHITECTURE_v3.0.md` - 理解理论框架
  2. `sop/FDS_SOP_v5.0.md` - 学习操作流程（执行标准）
  3. `FDS_KMS_SPEC_v1.0-BETA.md` - 了解知识库系统

### 测试与回归
- **测试说明与回归清单**: 见仓库根目录 `tests/README.md`
- 覆盖：FDS 推理引擎、TMM、全息控制器 FDS 分支（A-01/A-02/A-03）、AI 判词/格局解读、全量索引、V5.0 检查清单
- 运行: `pip install -r requirements-test.txt` 后执行 `python -m pytest tests/ -v` 或 `python tests/integration/test_fds_sop_v4_regression.py`

---

## ✅ 规范完整性检查

### 核心规范状态

- ✅ **物理架构规范**: 完成 (V3.0)
- ✅ **执行流程规范**: 完成 (V5.5)，以 sop/FDS_SOP_v5.5.md 为准
- ✅ **法理逻辑规范**: 完成 (V1.0-BETA)
- ✅ **代码接口规范**: 完成 (L3 Supplement)

### 规范质量

- ✅ **完整性**: 所有核心章节完整
- ✅ **一致性**: 文档间相互兼容，术语统一
- ✅ **可执行性**: 算法和公式明确，可直接实现
- ✅ **可维护性**: 文档结构清晰，易于更新

---

## 🎯 下一步行动

### 工程实施阶段

1. **Step 0: Manifest Generation**
   - 基于 `FDS_KMS_SPEC_v1.0-BETA.md` 实现聚合算法
   - 开发 `kms_aggregator.py` 原型

2. **Step 0-8: Pattern Fitting & 觉醒**
   - 基于 `sop/FDS_SOP_v5.0.md` 实现八步拟合与 HKB/QGA 注册
   - 使用生成的 `pattern_manifest.json`（含 semantic_core_dimensions）进行格局拟合

3. **Step 7: Integration**
   - 整合KMS、SOP和Architecture
   - 进行端到端测试

---

## 📝 版本历史

- **2026-02**: SOP 升级至 V5.5 智能数仓驱动版；以库治律、一键注库（upsert_pattern_meta.py）、OLAP 压力审计（DuckDB 极值 Top100 + 判词回测）、流形健康度监测；审计脚本库 `scripts/audit/`；执行以 V5.5 为准
- **2026-02-24**: 第 044 号纠偏：回归正八格法典。A-05→枭神格、A-09→建禄格、A-10→阳刃格；manifest/判词模板/索引统一古典正名，禁止「比肩格」「劫财格」
- **2026-02-24**: A-06～A-10 终极封卷完成；物理溢出报告归档 `audit_logs/`；格局状态切换为 ENFORCED；三专项验收红线入表
- **2026-02-24**: A-07 伤官格、A-08 正印格、A-09 比肩格、A-10 劫财格 Manifest 批量签发并 QGA 注册；判词模板注入「伤官见官」手术刀式识别；十格局全量对撞/判词/喜忌神零代码可用，待 518k 批量扫描后 Step 6 封卷
- **2026-02-24**: SOP 升级至 V5.1 元驱动架构；废除硬编码模板、Manifest 唯一真理源、喜忌神归一化；A-06 食神格接入实验（仅 Manifest + QGA 注册，零 AI 代码修改）通过
- **2026-02-24**: A-04 正财格、A-05 偏印格 Step 6 终极封卷完成，状态置为 ENFORCED；518k 索引、IoU 审计、财印两旺语义验收就绪
- **2026-02-24**: FDS_SOP_v5.0 正式落盘；V4.0/V4.1 归档；索引更新为以 V5.0 为执行标准
- **2026-01-03**: FDS_KMS_SPEC_v1.0-BETA 通过最终验收
- **2026-01-03**: FDS规范体系完成，三大核心支柱全部就绪
- **2025-12-31**: FDS_ARCHITECTURE_v3.0 和 FDS_SOP_v3.0 完成分离和抽象化

---

**文档维护**: 本索引文档应随规范文档的更新而同步更新。

