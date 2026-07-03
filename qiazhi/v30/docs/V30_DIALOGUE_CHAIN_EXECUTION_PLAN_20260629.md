# V30 Dialogue Chain Execution Plan

更新时间：2026-06-29

## 主线任务

本轮执行 `Dialogue-Centered Layer over Decision-Centered Architecture` 的最小完整闭环。

目标不是继续把问题塞进 7 阶段页面，而是新增独立八字对话链：

```text
DialogueSeed
-> DialogueSession
-> DialogueTurn
-> DialogueOrchestrator
-> API
-> UI 问八字面板
-> Training / Validation hooks
```

## 执行范围

### DLG-1 Schema And Store

- 新增 `BaziDialogueSeed`、`BaziDialogueSession`、`BaziDialogueTurn` 等模型。
- 新增 JSON/Postgres 兼容前的本地 store 接口，当前先保存到 runtime `.runtime/dialogues`。
- Store 是对话状态，不修改 runtime chart facts。

### DLG-2 Seed Router

- 支持系统种子与用户自然语言种子。
- 覆盖财富、事业、感情、健康、亲情、时运、决策、总览。
- 必须识别典型问题：`我今年财运如何？`。

### DLG-3 Dialogue Orchestrator

- 读取 runtime、Decision Workbench、Final Synthesis、Domain Cards、Current Dialogue Turn。
- 采用 answer-first 策略：用户明确问结论时先回答，再追问。
- 输出下一轮主问题和 2-3 个快捷方向。

### DLG-4 API

新增：

```text
POST /api/v30/readings/{reading_id}/dialogues
GET  /api/v30/readings/{reading_id}/dialogues
GET  /api/v30/readings/{reading_id}/dialogues/{dialogue_id}
POST /api/v30/readings/{reading_id}/dialogues/{dialogue_id}/turns
GET  /api/v30/readings/{reading_id}/dialogue-seeds
```

### DLG-5 UI

- 新增独立 `问八字` 面板。
- 支持自由输入种子问题。
- 支持点击快捷追问继续对话。
- 阶段页追问仍保留，但完整对话链进入新面板。

### DLG-6 Validation

- 新增专项测试覆盖：
  - Seed router 能识别 `我今年财运如何？`
  - Dialogue session 能 answer-first 并生成下一问
  - API 能创建会话并追加 turn
  - 对话不会修改 chart facts

## 边界

- LLM 只做表达，不改命理事实。
- Dialogue store 不写 runtime chart fields。
- 用户对话可持续，不进入第 8 步导航。
- 训练信号只面向 dialogue policy、seed routing、expression quality。

## 完成标准

- 文档更新。
- API + UI 可用。
- 专项测试通过。
- 后台重启后 smoke：创建 reading，发起 `我今年财运如何？`，得到回答与下一问。

## 执行结果

状态：已完成最小闭环。

落地内容：

- 新增 `v30.dialogue_chain` 模块：
  - `contracts.py`：`BaziDialogueSeed / BaziDialogueSession / BaziDialogueTurn / DialogueQuestionCandidate / BaziDialogueAnswer`
  - `seed_router.py`：用户自然语言种子识别，已覆盖 `我今年财运如何？ -> wealth + current_year + answer_first`
  - `orchestrator.py`：answer-first 对话编排，本轮回答后生成下一问和快捷选项
  - `store.py`：本地 JSON DialogueStore，当前存入 `.runtime/dialogues`
- 新增独立 API：
  - `GET /api/v30/readings/{reading_id}/dialogue-seeds`
  - `POST /api/v30/readings/{reading_id}/dialogues`
  - `GET /api/v30/readings/{reading_id}/dialogues`
  - `GET /api/v30/readings/{reading_id}/dialogues/{dialogue_id}`
  - `POST /api/v30/readings/{reading_id}/dialogues/{dialogue_id}/turns`
- 前端新增独立 `问八字` 面板：
  - 用户可点击种子问题启动对话
  - 用户可自由输入问题启动或继续对话
  - 点击下一问选项只追加 DialogueTurn，不切换测算步骤
  - 结论按 `断 / 策 / 歧` 展示，避免长段 debug 文案
- 验证：
  - `../.venv312/bin/python -m pytest tests/unit/test_dialogue_chain_mainline.py -q`
  - 结果：`3 passed`

## 当前边界

- 新对话链暂不复用旧 `/questions/{question_id}/answer` 接口。
- 新对话链不自动调用阶段页 LLM summary，避免页面导航被 LLM latency 卡住。
- LLM 表达增强已预留在 `answer.llm_metadata`，后续应作为 DialogueTurn expression 层接入，不允许改 Verdict 或 chart facts。
- 当前 store 先用 runtime JSON；Postgres 表结构与 Admin 对话回放可作为下一阶段。
