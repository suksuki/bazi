# Qiazhi-Bazi LLM 提示词体系 — 宪法索引（v2.1）

**文档性质**：产品与工程共用的**架构索引**（为何这样设计、改哪里、如何回归）。  
**范围**：`qiazhi_bazi/backend` 内与「调用大模型」直接相关的 system/user 文案、拼装与发送前清洗。  
**版本**：**v2.2**（2026-04-12）— 在 v2.1 上增加 **§7 四块模型（Cursor 重写协议）**；具体字符串以代码为准。

---

## 0. 为什么要在 2026 年的这个深夜干掉浮点数（写给未来的自己）

终审判词（第三阶段）的定位是 **Synthesis Narrator**：把引擎与插件已经算好的结论，用**有逻辑、有气势的中文**缝合成裁决文本。若 User 上下文里仍出现 `risk=0.4079`、十神 `Abs=12.34` 这类浮点字面量，模型会同时收到两类矛盾信号——System 说「不要现场重算能量」，Body 里却塞满可抄的小数——**认知失调**下输出必然碎、偏、或偷偷当计算器用。

**v2.1 的宪法级决定**：

1. **计算在 Python / 物理张量**：强弱、档位、结构闸口由引擎与插件预先判定；LLM 不承接「再算一遍 Abs」的任务。  
2. **叙事只消费文本标签**：终判 User 以 **`[Verified Facts]`（VF01… 编号）** 与 **`[User Decisions]`**（用户勾选与归档判词）为主；证据引用用短锚（`VF03`、`year.stem`、`plugin.*`、`conflict_matrix.*` 等）。  
3. **语义防火墙**：在发起终判请求前，对 **完整 `user` + `system`（含盲派动态后缀）** 及强制终审块，用后端过滤器 **剔除浮点字面量**（如 `0.4079`、`3.14e-2`），避免第三阶段被小数绑架。整数与干支等非浮点 token 保留。实现见 `prompt_builder._semantic_firewall_strip_float_literals`。

这不是「讨厌数字」，而是**任务解耦**：小数留在审计 JSON 与 `physics_tensor` 里给程序与质检员用；终审只吃**档位句与引擎脱水行**。

---

## 1. 三阶段角色（v2.1 定型）

| 阶段 | 角色名 | 职责 | 输出形态 | 代码锚点 |
|------|--------|------|----------|----------|
| **Step 1** | **Structural Observer**（原子观测） | 只做「翻译官」：按固定句式列出 `[位置] A 与 B 存在 [关系名称]`；不延伸吉凶、建议、第二段提问 | Markdown 列表 | `app/prompts/first_observation.py`；`app/llm/client.py`：`build_first_observation_messages` |
| **Step 2** | **Diagnostic Auditor**（逻辑质检） | 对比物理数据与共识库；**除 JSON 字段值外不写自然语言段落**；`diagnosis` 工程师短句；补丁意图进 `logic_proposal` / `sql_patch` | **严格 JSON**（`AuditLlmStructuredResponse`） | `app/prompts/physics_audit.py`；`router_helpers` / `audit_service` |
| **Step 3** | **Synthesis Narrator / Final Narrator**（终审整合） | **唯一**叙事润色出口；缝合 VF 与用户意志标签；输出顶层 JSON + `verdict_body`（三段 `###`） | JSON（内含 markdown 字符串） | `app/prompts/final_verdict_contracts.py`；`app/skills/final_verdict_parts/prompt_builder.py` |

其它链路（通用聊天、翻译、管理端改写）仍各自维护话术，但**不与终审判「宪法」混写**；跨语言口径见 `LanguageEngine`。

---

## 2. 终判上下文长什么样（已实现）

- **System**：短契约（角色、JSON 壳、`assertions` 与 VF 对齐、`EVOLUTION_LEARNING_CONTEXT_RULE`、语言）；盲派 skill 片段仍可由 `format_blind_skill_registry_for_prompt` 追加，**整块再过浮点防火墙**。  
- **User**：**`[Verified Facts]`**（多源脱水行编号 VF01…，含插件切片、结构行、神煞、因果流通等经清洗与编号）、**`[User Decisions]`**、`[L1·结构闸口]`、`[叙述权重]`、格局路由、可选 `Auxiliary·溯源`（高推理）、`Previous_Verdict`、可选 `MANDATORY_FINAL_SYNTHESIS`。  
- **弱模式断言守卫**：`evidence_refs` 至少命中 VF / 柱位 / 矩阵 / `plugin.*` 等短锚之一（见 `narrative_guard.weak_mode_requires_physics_fallback`）。

与旧版「`[Physical Evidence]` 长卷 + 盲派数字行 + 重复 JSON」相比，**Token 与冲突显著下降**。

---

## 3. 仍须注意的工程边界（非回归项清单）

1. **JSON 内 markdown**：终判仍要求「顶层 JSON + `verdict_body` 内三个 H3」；弱模型需靠短 System 与干净 User 降低畸形率。  
2. **引擎约束标签**：`[PHYSICS_CONSTRAINT]` 等若仍以长句出现在 VF 中，属于**数据面**文案；进一步「全部改为插件预生成正向标签句」见路线图。  
3. **审计 User**：Step 2 仍接收数值 JSON（十神分值等）— **正确**，质检员需要数；与 Step 3 脱钩不矛盾。

---

## 4. 与 ILD、意志补丁的关系

**ILD（Intelligence-Led Decision）** 将用户勾选与归档视为意志层；终判叙事以 **`persistence_layer` 与用户确认卡片** 为「意志补丁」输入之一（在 User 中体现为 `[User Decisions]`）。详见：

`../architecture/INTELLIGENCE_LED_DECISION_FRAMEWORK_v2.md`

总览索引中的 ILD 一句话表述见 **`../architecture/OVERVIEW.md`**（与 v2.1 同步）。

---

## 5. 代码路径速查

| 模块 | 路径 |
|------|------|
| 首轮观察 system + user | `backend/app/prompts/first_observation.py`、`backend/app/llm/client.py` |
| 物理审计 | `backend/app/prompts/physics_audit.py`；组装入口见 `router_helpers` / `audit_service` |
| 终判契约（system 短文） | `backend/app/prompts/final_verdict_contracts.py` |
| 终判 User 拼装 + 语义防火墙 | `backend/app/skills/final_verdict_parts/prompt_builder.py` |
| 弱模式证据锚、十神 Abs 行过滤 | `backend/app/skills/final_verdict_parts/narrative_guard.py` |
| 终判解析与 VF 启发式 | `backend/app/skills/final_verdict_parts/verdict_parse.py` |
| 进化学习片段（短） | `backend/app/prompts/evolution_contracts.py` |
| 通用聊天 | `backend/app/services/llm_service.py` |
| 翻译 JSON | `backend/app/services/helpers/analysis_helpers.py` |
| 管理端压缩/改写 | `backend/app/api/admin.py` |

---

## 6. 单测与回归

- `tests/unit/test_first_observation_messages.py`：Structural Observer 契约。  
- `tests/unit/test_prompts_registry.py`：注册表与终判 system 关键子串。  
- `tests/unit/test_narrative_guard.py`：弱模式锚、Abs 行过滤。  
- `tests/unit/test_verdict_prompt_hardening.py`：元数据清洗、语义防火墙、physics fallback。  
- `tests/unit/test_final_verdict_skill_protocol.py`：终判协议。

**维护约定**：若 `prompt_builder`、`final_verdict_contracts`、`first_observation`、`physics_audit` 或防火墙规则有重大变更，**必须**同步修订本文件 §1–§2、§5 与 §7 对照表。

---

## 7. 四块模型：给 Cursor 的重写协议（为何「不蠢」、如何改代码）

本节是**提示词拼装的心智模板**：以后无论是人还是 Cursor 改 `first_observation` / `physics_audit` / `final_verdict`，都应先问「四块是否各居其位」，避免把 500 行 JSON 或浮点表塞进叙事模型。

### 7.1 四块定义（认知顺序 = 拼装顺序）

| 块 | 名称 | 作用 | 对模型的含义 |
|----|------|------|----------------|
| **一** | **角色契约 (Identity Contract)** | 定边界：你是谁、本回合**唯一**任务、禁止越权 | 缩小解空间；禁止「又算物理又写判词」 |
| **二** | **环境快照 (Environment Snapshot)** | 只放**大脑已算完、不可置疑**的脱水事实 | 注意力只在 VF 标签与柱位短锚，不解析整包 `physics_tensor` |
| **三** | **意志导向 (Will Direction)** | 用户勾选、归档判词、叙事重心（止损/获利等） | 界面变动只改这一块即可**实时共振**下一轮流式/再终判 |
| **四** | **输出协议 (Output Protocol)** | 形态：仅 JSON、字段名、`verdict_body` 小节标题、禁浮点等 | 与「叙事内容」分离，减少畸形输出 |

### 7.2 可复制模板（终判 / 类终判叙事链）

**块一 · 角色契约（通常放在 System 首段或紧随 STRICT 头之后）**

```text
你是 Qiazhi-Bazi 的 [Structural Observer | Diagnostic Auditor | Final Narrator] 代理。
你本回合的单一任务是：[仅列出冲突关系 / 仅输出审计 JSON / 仅将 VF 与意志缝合成顶层 JSON 判词]。
严禁执行超出本阶段的任务（例如在本阶段重算能量、编造未出现在上下文中的数值）。
```

**块二 · 环境快照（User 中独立成段；事实全部用标签，不写散文论证）**

```text
[Verified Facts]（由系统大脑计算完成，不可置疑；引用时用 VF01、VF02…）：

- VF01: …
- VF10: …

[Pillars]: 丁巳 / 乙巳 / 乙丑 / 乙酉
```

说明：生产里四柱可能以「四柱快照=…」等形式并入 VF 行（见 `prompt_builder._pack_verified_facts`）；**重构时建议**显式增加 `[Pillars]:` 一行，与上表模板一致，便于弱模型对齐。

**块三 · 意志导向（与块二分离；勾选变化应只触达本块或本块 + 下游缓存键）**

```text
[Current Will]: 用户当前勾选了 [项 A、项 B]，要求叙事重心向 [止损 | 获利 | 中性稳态] 偏移。
已归档意志（若有）与本轮 Inbox 勾选须同时可见且可区分优先级（与 persistence_layer / ILD 一致）。
```

说明：当前实现将「已归档」放在 `[User Will · persistence_layer · …]`，「本回合勾选」放在 `[User Decisions]`（`prompt_builder._user_will_priority_block` / `_user_decision_lines`）。**语义上二者同属块三**；若重写 prompt，可用 `[Current Will]` 作为总标题，下面再分子列表。

**块四 · 输出协议（通常放在 System 末段或与块一相邻；勿写入长篇 user 故事）**

```text
仅返回合法 JSON（首字符「{」末字符「}」）；不得输出 Markdown 围栏或思考过程。
verdict_body 中必须包含且仅包含三个小节：### 核心气象 / ### 裁决共识 / ### 行为指引。
JSON 任意字段的字符串值中严禁出现浮点数字面量（与语义防火墙一致）。
```

### 7.3 与现有代码的对照（改哪里）

| 块 | 终判 Step 3 现状（v2.2） |
|----|---------------------------|
| 一 + 四 | `app/prompts/final_verdict_contracts.py`：`build_final_verdict_system_message`（含 `STRICT_JSON_ONLY`、Final Narrator 角色、`verdict_body` 三 `###` 等） |
| 二 | `app/skills/final_verdict_parts/prompt_builder.py`：`[Verified Facts]` + `_pack_verified_facts`（VF01…）；`format_core_logic_seed_user_block` 等补充种子块 |
| 三 | 同上：`will_head`（persistence）+ `[User Decisions]` + 叙事权重行；勾选变动经 `mergeLabSnapshot` / 终判请求体更新本块即可驱动「共振」 |
| 防火墙 | `strip_float_literals` 在发送前作用于 system+user（见 §0） |

Step 1 / Step 2：块一、块四各自不同（观察用 Markdown 列表；审计用 JSON schema）；**块二**在观察阶段对应「冲突矩阵脱水」，在审计阶段对应「物理与 metadata 的结构化字段」——仍遵守「大脑算完、本阶段只消费不发明」。

### 7.4 为什么这样组织就不「蠢」

1. **注意力聚焦**：模型读到的是任务书 + 有限条 VF，而不是整仓 JSON。  
2. **逻辑强一致**：叙事必须挂 VF / 短锚，判词不易脱离物理事实。  
3. **实时感知**：产品侧勾选、归档变化优先写入**块三**，再触发重算或再终判，无需重扫全量物理包。

### 7.5 Cursor 重写时的自检清单

- [ ] 块一是否明确**阶段名 + 单一任务 + 禁止越权**？  
- [ ] 块二是否**无用户长文、无浮点**（或已在防火墙剥离）？  
- [ ] 块三是否包含**当前勾选与已归档意志**，且与块二边界清晰？  
- [ ] 块四是否仍在 **System**（或与 System 绑定的不可变头），避免被 user 里的长上下文淹没？  
- [ ] 修改后是否跑 §6 所列单测 + 与 `final_verdict_contracts` 关键子串相关的注册表测试？

---

## 8. 历史与延伸阅读

- **Registry + LanguageEngine + 终判契约模块化（v1）**：`../architecture/PROMPTS_ARCHITECTURE_v1.md`  
- **强推理日切**：`QIAZHI_LLM_HIGH_REASONING` 见 `backend/.env.example` 与 `runtime_config.py`。

---

**v2.2 封卷说明**：**当前生产默认以 v2.1 架构 + §7 四块模型为提示词心智与重构协议为准**。若分析师文档与代码冲突，以代码与单测为准；§7 模板与实现不一致时，以单测与 `prompt_builder` / `final_verdict_contracts` 为准并回写 §7 对照表。
