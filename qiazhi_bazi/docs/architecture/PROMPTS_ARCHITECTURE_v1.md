# 提示词架构升级说明（v1）— 技术规格

**状态：PROMPTS_ARCHITECTURE_v1_LOCKED（生产封卷）** — 见 §7。

本文描述 `qiazhi_bazi/backend/app/prompts/` 引入后的**单一事实来源（SSoT）**、终判 **System/User 解耦**、**语言指令收敛**、以及 **强弱推理模式** 下的契约策略。

---

## 1. 目录结构

```
backend/app/prompts/
├── __init__.py                 # 对外导出常量 + LanguageEngine + get_prompt
├── registry.py                 # 静态片段 ID → 字符串（审计/检索）
├── language.py                 # LanguageEngine：全仓自然语言输出指令入口
├── chat.py                     # 通用聊天默认 system
├── first_observation.py        # 首轮观察 system
├── audit.py                    # 物理审计 JSON 修复轮 system
├── physics_audit.py            # 物理审计主链路 compact/standard（system+user 拼装）
├── admin_surface.py            # Admin 结论改写/压缩固定 system
├── translation.py              # 翻译链路 system
└── final_verdict_contracts.py # 终判 system 契约（含 JSON+verdict_body 内三节 Markdown 规则）
```

**未迁入 registry 的内容**：`final_verdict_contracts` 由代码拼装，属于「契约模板」而非静态常量；若需版本指纹，可对 `build_final_verdict_system_message(..., high_reasoning=...)` 的产物做 hash。

---

## 2. Registry 与引用约定

| `prompt_id` | 用途 |
|-------------|------|
| `chat.default_system` | `/chat` 类通用对话 |
| `first_observation.system` | analyze-seed 首轮观察 |
| `audit.json_repair_system` | 审计 LLM JSON 解析失败时的重试 system |
| `translation.system` | 动态文案翻译 |
| `physics_audit.schema_line` | 物理审计 JSON 单行 schema 样例（与 `AuditLlmStructuredResponse` 对齐） |
| `admin.conclusion_rewriter_system` | Admin 结论改写（80 字内） |
| `admin.conclusion_compressor_system` | Admin 结论压缩（120 字内） |

**规则**：新增静态 system 文案必须注册 `prompt_id`，禁止在业务文件内再写长字符串常量（短句 user 拼接除外）。

**拼装型提示词（不进入单条 registry 字符串，但代码须在 `app/prompts/`）**：`physics_audit.build_physics_audit_messages`（完整审计消息）、`final_verdict_contracts.build_final_verdict_system_message`（终判 system）。

---

## 3. LanguageEngine（语言指令收敛）

`app/prompts/language.py` 中 `LanguageEngine` 提供两类 API：

1. **`output_directive_for_structured_flow(lang)`**  
   与历史 `router_helpers.lang_output_instruction` 语义一致：  
   「推理语境为中文命理逻辑，终稿语言为 ZH/EN/KO」。  
   `router_helpers.lang_output_instruction` 现**委托**至此，旧调用方无需修改。

2. **`strict_assistant_output_language(lang)`**  
   仅约束助手输出语种（无「推理用中文」子句）。  
   **终判 system** 使用此项，避免与 JSON 契约重复堆叠「推演语言 vs 输出语言」。

3. **`first_observation_output_hint(lang)`**  
   首轮观察 user 尾部 hint（含 EN 的拼音说明），与历史 `build_first_observation_messages` 对齐。

---

## 4. Final Verdict：System-User 解耦与 JSON/Markdown 单一指令

### 4.1 问题（旧态）

- System 要求 JSON，**User 末尾又要求**「输出三段 `###` Markdown」，形成**双重输出指令**，小模型易在 JSON 外再吐一篇 Markdown 或截断 JSON。  
- User 中 `[Physical Evidence]` 与 `[User Consensus]` / `[Selected Decisions]` 对 `get_logical_evidence` **分次调用**，导致 **共识行 / 裁决项行重复**。

### 4.2 新态

- **唯一叙事结构说明**：三个小节（`### 核心气象` / `### 裁决共识` / `### 行为指引`）及首段 Self_Abs/Tomb_State 要求，**全部写入** `final_verdict_contracts._verdict_json_envelope_and_verdict_body_rules()`，明确 **仅出现在 JSON 字段 `verdict_body` 内**，且 **禁止在 JSON 外再输出 Markdown 文档**。  
- **User 尾部**删除「请输出三段 markdown…」行。  
- **EvidenceDedup**：仅保留一次 `get_logical_evidence(metadata, physics_tensor, selected_cards, consensus_history)` 结果进入 `[Physical Evidence]`；删除重复的 `[User Consensus]` / `[Selected Decisions]` 列表，改为 `[EvidenceDedup]` 一行说明。  
- **System 强弱模式**：`is_high_reasoning_mode` 为真时，`build_final_verdict_system_message` 使用高推理身份后缀 + `evidence_mode_clause(high=True)`；否则使用碎片模式文案（仍由 `prompt_builder` 侧 `format_plugin_evidence_chunks` 的 `high_reasoning` 控制切片形态，与 system 叙述一致）。

### 4.3 循环依赖处理

`prompt_builder` 对 `merge_interpretation_metadata_for_llm` 改为 **函数内延迟 import**，避免 `import app.services` 包初始化与 `final_verdict` → `prompt_builder` 的环。

---

## 5. 兼容与迁移

| 旧符号 | 新位置 |
|--------|--------|
| `FIRST_OBSERVATION_SYSTEM_PROMPT` in `llm/client.py` | `app.prompts.first_observation`（`client` 仍 re-export） |
| `SYSTEM_PROMPT` in `llm_service.py` | `CHAT_DEFAULT_SYSTEM_PROMPT`；`SYSTEM_PROMPT` 为别名 |
| `lang_output_instruction` 实现 | `LanguageEngine.output_directive_for_structured_flow` |

---

## 6. 后续可选工作

- 为 `build_final_verdict_system_message` 增加 golden-file 或 hash 快照测试（防契约漂移）。  
- 前端/解析器：确认 `verdict_parse` 对「仅 JSON、verdict_body 内含 ###」的样本覆盖。

---

## 7. 生产封卷（PROMPTS_ARCHITECTURE_v1_LOCKED）

### 7.1 Registry 完整性（裁决判定）

| 场景 | 落点 | 残留硬编码 |
|------|------|------------|
| 通用聊天 system | `prompts/chat.py` + registry | 无 |
| 首轮观察 system | `prompts/first_observation.py` + registry | 无 |
| 物理审计主链路 | `prompts/physics_audit.py`（`router_helpers.build_physics_audit_prompt` 仅委托） | 无 |
| 审计 JSON 重试 | `prompts/audit.py` + registry | 无 |
| 翻译 | `prompts/translation.py` + registry | 无 |
| Admin 改写/压缩 | `prompts/admin_surface.py` + registry | 无 |
| 终判 system 契约 | `prompts/final_verdict_contracts.py` | 契约字符串仅此处与 `prompt_builder` 数据拼装 |
| Admin LLM 探测 / 用户自定义 | `admin_service` 使用请求体 `system_prompt` | **有意保留**（联调可变） |

### 7.2 JSON 契约（裁决判定）

- 终判：**仅**通过 JSON 输出；`### 核心气象` / `### 裁决共识` / `### 行为指引` **仅**允许出现在 **`verdict_body` 字符串内**；User 消息**不得**再含「请输出三段 markdown」类第二套指令。  
- 实现与回归：`prompt_builder.py` + `tests/unit/test_prompts_registry.py` + 全量 `pytest tests/unit/`。

### 7.3 强模型环境变量（机房预置）

- **变量名**：`QIAZHI_LLM_HIGH_REASONING`（取值 `1` / `true` / `yes` 区分大小写不敏感，见 `runtime_config._default_llm`）。  
- **语义**：为真时 `llm.is_high_reasoning_mode=true`，终判走全量插件 evidence 与高推理 system 后缀。  
- **覆盖规则**：若 `runtime_config.json` 的 `llm` 对象中**显式写入** `is_high_reasoning_mode`，则合并时**文件值覆盖**环境变量缺省；若文件**省略**该键，则以环境变量为准。  
- **示例**：`backend/.env.example` 已收录 `QIAZHI_LLM_HIGH_REASONING=0`。

---

**文档版本**：v1 LOCKED。变更须走评审并同步 Registry / 本节封卷说明。
