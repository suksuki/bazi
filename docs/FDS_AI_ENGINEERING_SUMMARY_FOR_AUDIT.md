# FDS AI 算力挂载与界面升级 — 工程汇报摘要

**汇报对象**：Gemini 3 审计师  
**周期**：第 023、025 号工程指令及后续优化  
**执行**：Cursor（Composer）+ 本地 GB10 服务器（Qwen 32B/14B、Ollama）

---

## 一、总体目标与成果

将 FDS 排盘系统从「查表程序」升级为**全息智慧引擎**：在保留 5D 物理归位与质心锚点的前提下，接入本地大模型实现**流形语义生成（Manifold-to-Text）**与**古籍语义向量检索**，并在 UI 上完成「物理定位 + AI 实时解读 + 古籍印证」的一体化展示。当前在 GB10 上 14B/32B 速度表现均良好。

---

## 二、已完成工作清单

### 1. 第 023 号工程指令：AI 算力挂载与向量化预热

| 项 | 内容 |
|----|------|
| **core/ai_engine.py** | 对接本地 Ollama；实现针对「5D 坐标 + 偏移向量」的 System Prompt；`generate_manifold_interpretation()` 产出物理逻辑一致的判词。 |
| **data/vector_db/** | 古籍向量库原型：`classical_db.py` 使用与对话模型**同一 Ollama 服务**的向量模型；`find_classical_match(coordinates)` 根据归位结果检索语义最匹配古籍；`ingest_file()` 支持按段落切片入库；附示例文本与 README。 |
| **prediction_dashboard** | 在 A-01 流形归位区块下新增 **[AI 深度透视]**、**[古籍印证]** 模块。 |

### 2. 第 025 号工程指令：向量模型统一与配置页增强

| 项 | 内容 |
|----|------|
| **向量模型策略** | 与审计师确认：**无本地独立向量模型**，向量与对话使用同一 Ollama URL，仅在配置页选择「对话模型」与「向量模型」两个模型名。 |
| **config** | `embedding_engine.model`、`ai_engine.chat_model`；向量调用统一经 `core/embedding_provider.py` 走 Ollama。 |
| **A-01 古典语义立法** | 审计师提供的三维度（秩序的刚性 / 能量的载体 / 财富的源头）写入 `config/hkb/hkb_params.json` 的 `a01_semantic_core`；`ai_engine` 在生成判词时将该立法注入 System Prompt。 |
| **prediction_dashboard** | **[AI 深度透视]** 提升为第一优先级；全息报告样式（推理依据 + 渐变框 + 判词正文）。 |
| **ui/pages/system_config.py** | 对话模型与向量模型**同服选择**；Ollama 与古籍向量库**连接状态检测**；**古籍 TXT 上传**并触发向量化入库。 |

### 3. 界面与体验优化（后续迭代）

| 项 | 内容 |
|----|------|
| **A-01 立法可见性** | 在智能预测页 A-01 区块下增加可折叠「📜 A-01 古典语义立法（本页依据）」，从 `hkb_params.json` 读取并展示三维度定义与物理映射。 |
| **打字机式判词** | 新增 `stream_manifold_interpretation()`，Ollama `stream=True`；仪表盘用 `st.empty()` 占位符按 chunk 更新，实现逐字/逐句展示，避免长时间「正在生成…」无反馈。 |
| **实时切换 14B/32B** | AI 判词缓存键包含**当前对话模型名**；在系统配置页切换模型并保存后，再进入智能预测页即用新模型重新流式生成，便于对比 14B 与 32B 速度；页面展示「当前判词模型：xxx」。 |

---

## 三、关键文件与配置

| 类型 | 路径 / 说明 |
|------|--------------|
| AI 判词引擎 | `core/ai_engine.py`（含流式 `stream_manifold_interpretation`） |
| 向量统一入口 | `core/embedding_provider.py`（同 URL、选模型） |
| 古籍向量库 | `data/vector_db/classical_db.py`、`find_classical_match`、`ingest_file` |
| 语义立法配置 | `config/hkb/hkb_params.json` → `hkb.a01_semantic_core` |
| 运行配置 | `config/tuning_params.json` → `ollama_host`、`ai_engine.chat_model`、`embedding_engine.model` |
| 智能预测页 | `ui/pages/prediction_dashboard.py`（归位 → 立法折叠 → AI 深度透视 → 古籍印证） |
| 系统配置页 | `ui/pages/system_config.py`（模型切换、状态检测、古籍上传入库） |

---

## 四、合规性简要说明

- **公理一（零硬编码）**：模型名、URL、向量模型均从 config 或 `ConfigManager` 读取。  
- **公理二（MVC/结构）**：UI 仅调用 Controller/引擎与 `ai_engine`、`find_classical_match`，无在 UI 内写死五行/强弱逻辑。  
- **公理三（概率输出）**：AI 判词为自然段解读，带推理依据与模型标识，非二元结论。  
- **古典立法**：A-01 三维度由审计师（Gemini）立法并写入 hkb，Cursor 仅做配置与 Prompt 注入实现。

---

## 五、当前使用流程（供审计师验证）

1. **系统配置页**：填写 Ollama URL → 测试连接并刷新模型列表 → 选择「对话模型」（如 32B/14B）与「向量模型」（如 nomic-embed-text）→ 可选：上传古籍 TXT 并执行入库。  
2. **智能预测页**：输入八字并启卦排盘 → 若触发 A-01，则依次展示：流形归位、可折叠 A-01 立法、**AI 深度透视**（打字机式流式输出）、**古籍印证**（若有入库）。  
3. **切换模型比较**：在配置页改选 14B 或 32B 并保存 → 返回同一命例，判词会按新模型重新流式生成，可直观比较速度与风格。

---

## 六、后续可扩展方向（建议）

- 更多格局（如 A-03）的古典语义立法写入 hkb，并在对应页面注入 Prompt。  
- 审计师整理《渊海子平》《三命通会》正官篇等原文后，经系统配置页「古籍入库」批量导入，进一步验证「物理坐标 + 古籍语义」匹配质量。  
- 可选：在 AI 深度透视区块记录首 token 延迟与总耗时，便于量化 14B/32B 性能对比。

---

## 七、第 026 号工程指令：全息动态演化（已落地）

| 项 | 内容 |
|----|------|
| **core/dynamic_engine.py** | 大运/流年干支 → 五行 → 5D 增量（`pillar_to_5d_delta`、`get_time_delta`）；地理方位 → 5D 修正（`get_geo_factor`）；`calculate_dynamic_state(base_point, time_delta, geo_factor)` 合成动态点；参数来自 `config/dynamic_evolution.json`。 |
| **config/dynamic_evolution.json** | 时间权重（weight_luck/weight_year）、五行→5D 增量、方位→5D 修正，零硬编码。 |
| **core/ai_engine.py** | System Prompt 增加「动态演化」段；用户 Prompt 支持可选 `dynamic_context`；流式/非流式判词均可传入大运+流年+地理后的动态坐标，AI 输出原局解读 + 动态趋势与风险提示。 |
| **prediction_dashboard** | 运势推演区增加**地理方位**选择（东/南/西/北/中）；A-01 雷达图增加**动态点**轨迹（大运+流年+地理合成），与原局 P、S1/S2 质心同图；AI 判词缓存键含大运/流年/方位，切换即重新生成含动态趋势的判词。 |

---

*本摘要由 Cursor 根据第 023、025、026 号工程指令及后续迭代整理，供 Gemini 3 审计师审阅与归档。*
