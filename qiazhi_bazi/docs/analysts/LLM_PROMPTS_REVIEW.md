# Qiazhi-Bazi LLM 提示词体系 — 综述与审查说明

**文档性质**：供产品/数据/命理业务分析师阅读的技术综述（非实现规范）。  
**范围**：`qiazhi_bazi/backend` 内与「调用大模型」直接相关的 system/user 文案与拼装逻辑。  
**版本说明**：基于当前仓库结构整理；具体字符串以代码为准。

---

## 1. 执行综述（给分析师的三句话）

1. **提示词分散在多条业务链上**：首轮观察、物理审计、终极判词、通用聊天、翻译、管理端压缩/改写等各自维护一套话术，**没有统一的「提示词注册表」或单一事实来源**。  
2. **终极判词（Final Verdict）单条 system 提示极长**：在同一字符串内叠合角色定义、输出 JSON 形态、物理约束、盲派/旺衰语气、证据模式、多语言提示等，**可读性与可实验性较差**，小模型更容易漏约束或输出畸形 JSON。  
3. **语言策略不统一**：有的链路「推理中文、输出英文」，有的「全程中文」，有的韩语要求固定前缀；分析师做**跨语言对比实验**时需按链路分别记录，不能假设全局一致。

---

## 2. 职责矩阵：谁在什么场景说话

| 场景 | 主要入口（代码锚点） | 角色设定摘要 | 输出形态 |
|------|----------------------|--------------|----------|
| 首轮观察（排盘后「只观察」） | `app/llm/client.py`：`FIRST_OBSERVATION_SYSTEM_PROMPT` + `build_first_observation_messages` | 子平/干支观察员；禁止西洋占星等；两段、约 260 字 | 自然语言两段 |
| 物理 + LLM 审计（结构化） | `app/api/router_helpers.py`：`build_physics_audit_prompt`；`app/services/audit_service.py` 组装 | 「物理命理审计助手」或「首席审计官」；compact/standard 两档 | **严格 JSON**（与 `AuditLlmStructuredResponse` 对齐） |
| 审计失败重试 | `app/services/audit_service.py` 内联 retry | 英文一句：仅 JSON | JSON |
| 终极判词 | `app/skills/final_verdict_parts/prompt_builder.py`：`build_final_verdict_messages` | `FinalVerdictSkill`；大量物理/结构/插件约束 | **要求 JSON**（内含 `verdict_body` markdown、change_log、assertions）；user 末段又要求「三段 markdown 小节」标题 — **与 JSON 内 markdown 并存** |
| 通用聊天 | `app/services/llm_service.py`：`SYSTEM_PROMPT` + `build_chat_messages` | 「严谨命理分析助手」+ 用户消息 + `lang_output_instruction` | 自由文本 |
| 动态文本翻译 | `app/services/helpers/analysis_helpers.py`：`build_translation_messages` | 翻译引擎；仅 JSON `items` | JSON |
| 管理端结论改写/压缩 | `app/api/admin.py`：`_rewrite_final_only`、`_compress_final_only` | 结果整理器 / 结论压缩器 | 短文本 |
| 管理端 LLM 探测 | `app/api/contracts.py`：`ChatRequest.system_prompt` 默认值等 | 可配置 | 依请求 |

---

## 3. 架构层面的「乱」体现在哪里

### 3.1 维护面分散

- **静态常量**（如 `FIRST_OBSERVATION_SYSTEM_PROMPT`、`SYSTEM_PROMPT`）与**动态拼装**（终判 `system` 大段字符串 + `user` 多节区）并存。  
- **同一业务**（终判）在 `prompt_builder` 里重复计算与 `FinalVerdictSkill.generate` 前类似的结构（盲派 work、structure、school_audit 等），**分析「提示词改了什么」时要对两处逻辑对齐**，否则容易误判因果。

### 3.2 单条终判 system 信息密度过高

`build_final_verdict_messages` 的 `system` 在单次调用中同时承担：

- 身份与任务（`FinalVerdictSkill`、高推理模式分支）；  
- 输出契约（JSON 键名、assertions、evidence_refs）；  
- 多条**条件约束**（`[PHYSICS_CONSTRAINT]`、`[BLIND_WORK_CONSTRAINT]`、`[BODY_DAMAGE_CONSTRAINT]` 等）；  
- 插件权重与语气（盲派 vs 旺衰比例）；  
- L1 伤官见官门控、三合证据、证据切片模式（全量 vs 碎片）；  
- 语言 hint。  

**分析师视角**：难以做 A/B（例如只改「语气」不改「JSON 契约」），因为全部耦在同一 blob 中。

### 3.3 输出规格存在「双重叙事」风险

- System 要求顶层为 **JSON**（含 `verdict_body` 为 markdown 字符串等）。  
- User 尾部要求输出 **三段 markdown 小节**（`### 核心气象` 等）。  

对强模型通常能合并为「JSON 里的 markdown 遵守三级标题」；对**小模型**易出现：只吐 markdown、JSON 断裂、或两段要求互相打架。**这是当前最值得单独做实验与收敛的设计点**。

### 3.4 语言指令重复与口径差异

- `prompt_builder`：`lang_hint`（请仅使用中文 / EN / KO）。  
- `router_helpers.lang_output_instruction`：EN/KO 另有「基于中文命理逻辑推演」等表述。  
- `build_first_observation_messages`：`output_hint` + 中文额外 `zh_guard`。  

分析师记录「模型输出语言」时需注明**调用的是哪条 API / 哪组 messages**。

### 3.5 User 消息「区段标签」堆叠

终判 user 内容由多个方括号标题拼接，例如 `[八字元数据快照]`、`[Physical Evidence]`、`[Evidence Slices…]`、`[盲派硬核证据]`、`[Structure Candidates V0]`、`[User Consensus]`、`[Selected Decisions]`、`[PatternRouter]`、`Previous_Verdict=` 等。  

**优点**：便于人类在 `llm_request_messages` 里审计上下文。  
**缺点**：区段顺序与命名若无文档，业务方难建立心智模型；**证据与共识在多处出现**（如 `get_logical_evidence` 多次调用），分析师需理解每段数据源，否则易误判「重复投喂」。

---

## 4. 与「小模型表现差」相关的提示词因素（非唯一因素）

以下仅列**与提示词设计相关**的风险点，不排除模型能力、温度、max_tokens、解析器、前端二次请求等其它因素。

1. **终判 system 过长**：弱模型对尾部约束服从度下降。  
2. **JSON + 章节标题双重要求**：增加格式错误概率。  
3. **Evidence 模式切换**（`runtime_config.llm.is_high_reasoning_mode`）：高推理模式要求更细的字段级溯源，token 与难度同时上升。  
4. **审计链路** compact 已含 `blind_skill_system_suffix`，终判再拼接 `blind_skill_block`，**盲派相关说明可能重复出现**（需结合当次 `physics_tensor` 判断是否两次注入）。

---

## 5. 建议路线图（供评审会讨论，非已排期承诺）

| 阶段 | 目标 | 说明 |
|------|------|------|
| **短期** | 文档化 + 分区冻结 | 将终判 `system` 拆成「不可变契约 / 可变策略 / 语言」三段文档与代码注释边界；在审计日志中固定 `prompt_hash` 便于对比实验。 |
| **中期** | 模板化与配置化 | 用结构化对象（或 YAML）维护各约束块，由代码拼接；便于分析师只改「语气块」或「证据说明块」。 |
| **长期** | 单一注册表 | 全仓 LLM 角色与输出 schema 登记；与前端展示、后端解析器版本对齐，减少「JSON 里 markdown」与纯 markdown 混用。 |

---

## 6. 附录：代码路径速查

| 模块 | 路径 |
|------|------|
| 首轮观察 system + user | `backend/app/llm/client.py` |
| 物理审计 prompt（compact/standard） | `backend/app/api/router_helpers.py` |
| 审计服务 + JSON 重试 | `backend/app/services/audit_service.py` |
| 终判 messages 构建 | `backend/app/skills/final_verdict_parts/prompt_builder.py` |
| 终判技能总控（调用上述 builder、解析、审计） | `backend/app/skills/final_verdict.py` |
| 盲派 skill 注入片段 | `backend/app/plugins/blind_school/skill_prompt.py` |
| 通用聊天 | `backend/app/services/llm_service.py` |
| 翻译 JSON | `backend/app/services/helpers/analysis_helpers.py` |
| 管理端压缩/改写 | `backend/app/api/admin.py` |
| 合同默认 system_prompt | `backend/app/api/contracts.py` |

---

## 7. 单测与回归（工程侧提示）

- `backend/tests/unit/test_first_observation_messages.py`：首轮观察禁占星等。  
- `backend/tests/unit/test_audit_service.py`、`test_llm_service.py`：审计 / 聊天消息结构。  
- 终判 prompt 若有大规模重构，建议补充「消息角色顺序、必含区段标题、JSON 示例一致性」类快照或属性测试。

---

**文档维护**：若终判 `prompt_builder` 或审计 `router_helpers` 有重大变更，请同步更新本文件 §2–§3 与附录。

---

## 8. 架构升级（v1）— 见工程规格

已实现 **单一 Registry + LanguageEngine + 终判契约模块化**，详见：

`../architecture/PROMPTS_ARCHITECTURE_v1.md`

**封卷态（生产）**：`PROMPTS_ARCHITECTURE_v1_LOCKED` — 同上文档 §7；强模型日切环境变量 **`QIAZHI_LLM_HIGH_REASONING`** 见 `backend/.env.example` 与 `runtime_config.py`。
