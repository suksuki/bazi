# 语义快照 + 强制叙事（中控终判）— 开发规约 v1.0

**状态**：规约 + 初版实现（`active_verdict_skeleton` 字段、`[MANDATORY_NARRATION]` 终判 System 段、断言区展示）。  
**命名说明**：本规约**不**沿用「V4 实时流式断言」代号（该方向已废弃），以免与仓库历史混淆。对外可称 **「中控终判 v1」** 或 **「语义快照规约」**。

---

## 1. 目标（分析师意图落地）

| 维度 | 要求 |
|------|------|
| **确定性 (Certainty)** | 因果与结构断言由 Python / 物理张量与插件产出；LLM 温度不改变已固定的骨架逻辑。 |
| **即时性 (Immediacy)** | 物理参数或盘面一变，`active_verdict_skeleton` 即更新；断言区可先渲染骨架，再等待终判润色。 |
| **专业性 (Professionalism)** | 命理逻辑在代码与 VF 标签中；LLM 只做「命题作文」式中文润色与三节排版。 |

---

## 2. 数据契约：`BaziMetadata.active_verdict_skeleton`

协议：`active_verdict_skeleton.v1`（由子对象字段 `protocol` 标识）。

| 字段 | 类型 | 说明 |
|------|------|------|
| `protocol` | string | 固定 `active_verdict_skeleton.v1`。 |
| `engine_bullets` | string[] | **引擎骨架**：由后端从 conflict_matrix、四柱摘要、semantic_label_bundle 的 VF 脱水行等拼装；**无浮点**。 |
| `user_will_lines` | string[] | **意志硬编码**：Decision Inbox 勾选（及终判请求中的 `selected_cards`）由后端合并进骨架；LLM 须在润色时显著呈现。 |
| `updated_at` | string | ISO8601 UTC；物理重算或合并意志时刷新。 |

**刷新时机（初版）**：

- **analyze-seed / analyze-clash 成功后**：仅填充 `engine_bullets`（及空 `user_will_lines`），保证前端在首观 LLM 返回前即可展示「系统在算」。  
- **终判请求拼装时**：在 `build_final_verdict_messages` 内用当前 `metadata` + `physics_tensor` + `selected_cards` **再算一遍**完整骨架，供 `[MANDATORY_NARRATION]` 使用（避免仅依赖客户端缓存的 metadata）。

---

## 3. LLM 契约：`[MANDATORY_NARRATION]`（终判 System）

- **废弃**「请模型自主分析全盘」类表述作为**主任务**；终判 **Final Narrator** 的主任务改为：**在骨架与 VF 边界内润色**。  
- System 中在既有 `STRICT_JSON_ONLY`、JSON 壳、`###` 规则之后，追加格式化骨架摘要（见 `final_verdict_contracts._mandatory_narration_clause`）。  
- **禁止**：模型增删已列骨架中的因果链；可在三节中用不同措辞复述，但不得引入骨架未给出的新结构结论。  
- **用户意志**：若骨架含 `【用户意志·须显著呈现】` 下列条目，润色后正文须在相应小节**最显著句位**体现（规约建议：首段首句或「裁决共识」段首）。

---

## 4. 前端：断言区「先骨架、后 LLM」

- 消费 `metadata.active_verdict_skeleton.engine_bullets`（及有则 `user_will_lines`），在 **MultiSourceAssertionsPanel**（或后续专用条）中展示。  
- 与 `verdict_anchor_layer.final_verdict` 区分：骨架是**中控即时态**；终判正文仍为签发后的主展示。

---

## 5. 代码锚点（维护时同步）

| 能力 | 路径 |
|------|------|
| 骨架拼装 | `backend/app/services/helpers/active_verdict_skeleton.py` |
| Schema | `backend/app/schemas/bazi_metadata.py`（`ActiveVerdictSkeleton`、`BaziMetadata.active_verdict_skeleton`） |
| analyze 挂载 | `backend/app/services/analysis_service.py`（`analyze_clash_flow` 返回前 `model_copy`） |
| 终判 System + 意志合并 | `backend/app/prompts/final_verdict_contracts.py`、`backend/app/skills/final_verdict_parts/prompt_builder.py` |
| 前端类型 + 断言区 | `frontend/src/types/bazi.ts`、`MultiSourceAssertionsPanel.tsx` |
| 提示词体系索引 | `docs/analysts/LLM_PROMPTS_REVIEW.md` |

---

## 6. 回归与后续增强

- **单测**：`tests/unit/test_active_verdict_skeleton.py`（骨架字段与无浮点/意志合并）。  
- **后续**：骨架可与 `prompt_builder._pack_verified_facts` 更强对齐（减少重复脱水）、静默重算路径统一刷新、`memory_schema_version` 是否 bump 由数据迁移策略决定。

---

**裁决**：本规约即「系统预判骨架 + LLM 语义渲染」的 **v1.0 开发规约**；若需对外 PR 标题，建议使用 **「中控终判 / 语义快照 v1」**，避免使用 **V4.0** 字样。
