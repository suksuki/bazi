# Qiazhi-Inference-v1（V12.6）架构方案

## 1. 目标

- 物理优先：Python 推理机先定义边界，LLM 只做受限语言变换。
- 纳米带宽：单轮只处理一个冲突点；`Target_Node_ID` 强制存在；`payload <= 300`。
- 状态挂起：命中逻辑真空即切入 `PROBE_WAITING`，先问后算。

## 2. 黑板架构

### 2.1 专家种子库（Knowledge Seed Bank）

- 路径：`backend/app/logic/brain/seeds.py`
- 常量：`KNOWLEDGE_SEEDS`
  - `harm:寅巳` → `MARRIAGE_STABILITY`
  - `clash:子午` → `SYSTEM_STRESS`

### 2.2 推理路由器（Reasoning Router）

- 路径：`backend/app/logic/brain/hub.py`
- 新增：`BrainHub.orchestrate(...)`
  - 扫描 `conflict_matrix.points`
  - 命中种子库后输出：
    - `target_node_id`
    - `flow_state`（`PROBE_WAITING` 或 `READY`）
    - `probe_query`
    - `vf_tags`（最多 3 条）
    - `llm_user_message`（300 字封顶）
  - 禁止发送全量 Verified Facts。

### 2.3 决策闸门（Decision Gate）

- 路径：`backend/app/services/analysis_service.py`
- 行为：
  - `analyze_clash_flow` 接入 `orchestrate`，并把 `logic_introspection` 写入快照。
  - 若 `flow_state=PROBE_WAITING`，在返回中附带主动追问字段并保持挂起。
  - `generate_final_verdict` 在 `flow_state=probe_waiting` 时硬阻断（抛协议错误）。

## 3. 展示层收敛（Debug）

- 路径：`frontend/src/components/views/DebugView.tsx`
  - 新增紫色 `Logic_Introspection` 脉冲点。
  - 点击可看到路径：发现冲突点 → 检索种子库 → 判定信息真空 → 执行主动追问。
  - `Payload_Size_Monitor` 阈值收紧为 300；超限打红色闪烁并标记 `EXPERT_SYSTEM_LOCK`。

- 路径：`frontend/src/features/stream-board/components/PulseReplayOverlay.tsx`
  - 超限时拒绝渲染完整 JSON，仅展示：
    - `Target_Node_ID`
    - 前 150 字预览
    - `[EXPERT_SYSTEM_LOCK][ARCH_VIOLATION]` 告警

## 4. 验收口径

- 主动性：寅巳穿害命例触发具体追问，不允许泛问。
- 纯净度：LLM 上下文不超过 3 条 VF 标签（远低于 5 条上限）。
- 确定性：Debug 可追踪自省脉冲与闸门触发原因。
