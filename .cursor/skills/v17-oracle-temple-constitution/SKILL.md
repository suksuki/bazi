---
name: v17-oracle-temple-constitution
description: >-
  Encodes the V17 Oracle Temple architecture constitution (data sovereignty SSOT,
  deterministic step-async LLM protocol, WEAVER vs JUDGE roles, Chinese-only narrative
  purity). Use when editing qiazhi/v17_rebirth backend narrative/LLM/stream paths,
  PhysicsService, VerdictOrchestrator, llm_micro_client, semantic_fusion, sanitizer,
  or V17 Oracle frontend stream subscription behavior.
---

# V17 Oracle 圣殿架构宪法

## 1. 元数据主权 (Data Sovereignty — SSOT)

- **真源**：后端 Model 层（`PhysicsService` 绑定之 `physics_tensor` 缓存）为因果事实唯一真源。
- **禁止**：从 `Request Body`、Query 或前端任意字段**提取/解析**物理元数据（六柱、神煞、烈度、插件数值等）用于 LLM 提示词或门控逻辑。UI 仅传 **`session_id`** 与 **`action_intent`**（如 `user_message`、裁决 `decisions` 等意图），不得回灌柱位覆盖服务端（参见 `stream_v17` 之 `_PHYS_SSOT_KEYS`）。
- **强制**：LLM System/User 中与物理锚定相关的内容，须通过 **`PhysicsService.get_metadata(session_id)`**（或同语义之 `get_current_pillars`）读取；组装入口见 `llm_micro_client.build_v17_system_prompt`、`physics_canonical`、管道 `physics_tensor` 参数链。
- **违规**：若出现「`const pillars = req.body.pillars`」或后端等效逻辑，须立即重构并改抛 **`DataSovereigntyError`** 门闸。

## 2. 确定性步进异步协议 (Deterministic Step-Async)

- **四阶语义**（与实现对齐时的名称映射）：
  1. **dispatched**：提示词已组装并外发；编排层对应 **AUDIT_PREVIEW** SNAPSHOT（`LlmStreamStep` / `status_callback`）。
  2. **connected**：上游握手成功（HTTP 建立、耗时 ms）。
  3. **weaving**：叙事/判定坍缩中（流式 token 或块式回放）。
  4. **completed**：逻辑归档（`complete`/`error` 步进帧 + 最终 `llm_meta`）。
- **实现注**：`fuse` 异步生成器对外步进名为 `dispatching` / `handshake` / `weaving` / `complete|error`，经 `_emit_fuse_step_legacy` 映射为上述 `status` 语义。
- **心跳**：`stream_v17` 之 `_narrator_with_heartbeat` 须在约 **2s** 无帧时下发 **`HEARTBEAT`**（含 `step_position`）。

## 3. 多态角色 (WEAVER / JUDGE)

- **WEAVER（织造官）**：主页 Oracle 判词；**仅**对插件已给出之 Fact 做文学性缝合与润色；**禁止**令模型做未被事实支撑的链式推演（见 `semantic_fusion._weaver_system_core`）。
- **JUDGE（判定师）**：Decision 路径；宗师式断言，宜输出带决策权重之 **宜/忌/断** 等指令式中文（见 `_judge_system_core`）。角色常量：`V17_ROLE_WEAVER` / `V17_ROLE_JUDGE`（`llm_bridge`）。

## 4. 中文魂锁与叙事降噪 (Linguistic Purity)

- **System 首行**：`CHINESE_SOUL_LOCK` 必须以 **「STRICT CHINESE ONLY」** 起首，并禁止 `Thinking Process` / `Analysis` 及英文化推理备注（`semantic_fusion.py`）。
- **工程噪声**：`NarrativeSanitizer` 剔除 `VF.`、`Abs`、`Fact_ID`、`node_id`、`seed` 等；并剔除虚浮词如 **赛博、极客、激光** 等（可扩展 `_replacements`）。
- **文风**：古法命理之魂 × 冷峻科技之壳；**开口即判词**，禁废话与无事实铺陈。

## 5. 关键路径速查

| 关切 | 文件 |
|------|------|
| 会话张量绑定 / `get_metadata` | `qiazhi/v17_rebirth/backend/services/physics_service.py` |
| 六柱门闸 / `DataSovereigntyError` / `is_stable` | `verdict_orchestrator.py`、`physics_canonical.py` |
| NDJSON 流、SSOT 合并键 | `backend/api/stream_v17.py` |
| fuse 步进、System 锚定 | `infrastructure/llm_micro_client.py` |
| 角色 System、魂锁 | `backend/narrative/semantic_fusion.py` |
| 事实行清洗 | `backend/narrative/sanitizer.py` |
| UI 仅订阅流、不本地推柱 | `frontend/hooks/useV17WebStream.ts`、`V17_SixPillarsPanel.tsx` |
