# V17 Prompt Engine 重构方案（2026-04-20）

## 一、目标

当前系统的核心问题不在于“调用模型太少或太多”，而在于“模型输入上下文不统一、缺乏可审计约束”。  
目标是把提示词从“临时字符串”升级为“可版本化协议（Prompt Contract）”：

1. 同一条决策链路只允许同一类语义模型触发一次聚合决策，不做逐条散乱调用。  
2. 决策提示词中明确任务边界（只允许输出字段化结果）。  
3. 每类仲裁（决策/冲突）都能回放、追溯、单测验证。  

## 二、先回答你的关键问题

### 1）是否每个 decision 都要调 LLM 生成断言？

**不建议。**  
应当“按批次”调用，不按单条。已支持的机制：

- `decision_baches` 已将同类决策聚合；
- `PLAN_SUBMIT` 会产生 plan 级上下文给 LLM；
- 系统路由策略（system/llm/user）决定是否进入 LLM 层；
- 只有 `routing="llm"` 的批次才需要 LLM 仲裁。  

### 2）哪些场景应交给 LLM、哪些应交给用户/系统？

| 场景 | 建议路由 |
| --- | --- |
| 低风险、低冲突、低净变动 | system 自动 |
| 中风险、无强冲突 | llm 校验 |
| 高风险、同目标冲突、依赖/互斥歧义 | user 优先（或 llm 先给建议再给用户） |

## 三、Prompt Contract 设计

### A. 决策批次 Prompt（`PLAN`）

结构化字段：
- `task_type = decision_batch_arbitration`
- `policy_version = v17.plan.arbitration.v1.0`
- `summary`（decision_count / truncated / total_abs_ratio / net_ratio）
- `decision_rows`（统一标准化候选行）
- `output_contract`（输出字段与枚举）

输出要求：  
- 只返回 JSON；  
- 每条建议必须含 `decision_id / action / reason`；  
- `action ∈ {KEEP, DROP, ESCALATE}`。  

### B. 冲突包 Prompt（`CONFLICT`）

结构化字段：
- `task_type = conflict_bundle_arbitration`
- `policy_version = v17.conflict.arbitration.v1.0`
- `conflicts`（可多冲突）  
- `claims`
- `output_contract`（`resolution_type` / `preferred_arbiter` / `winner_claim_ids` / `dropped_claim_ids` / `reason` / `confidence`）

输出要求：  
- 多冲突时返回 `results_by_conflict`；
- 单冲突时返回单对象。

## 四、是否每个 Decision 都调用 LLM？——结论

结论：**不该每条都调用。**

推荐规则如下：
- `PLAN` 级别统一调用：同一批次一条 prompt，多条决策一次处理；
- 低风险批次（`routing=system`）不调 LLM，直接落地；
- 中风险批次（`routing=llm`）由 LLM 做结构化裁决；
- 高风险冲突批次（`routing=user`）直接交给用户，仅在 `llm_suggest` 模式提供“候选建议”。

这样做的收益：
- 降低延迟与 token 消耗；
- 减少上下文漂移，避免“同一主题多轮互斥改写”；
- 让 LLM 在关键决策点发力，而不是做机械重复。

## 五、给八字系统的提示词设计建议（可直接落地）

### 1. 领域语义层：先“命理语义”后“规则语义”
每个 prompt 入口统一加入：
- 命局上下文（`anchor`、`流派版本`、`冲突强度`）；
- 五行/十神目标对象；
- 物理约束边界（本次批次最大偏移、保底阈值）；
- 冲突原因与证据（为什么这个决策可疑/需核验）。

### 2. 输出约束层：JSON + Schema + 置信度
强制输出 schema 字段，包含：
- 决策类：`decision_id/action/reason`；
- 冲突类：`resolution_type/preferred_arbiter/winner_claim_ids/dropped_claim_ids/confidence`；
- 明确不允许文本回复、不得新增条目、不得引用外部信息。

### 3. 可解释层：每次输出带简短 rationale 但不冗长
保留 `reason` 字段（≤120 字）用于事后审计，不用在 prompt 内要求长叙述，避免模型“跑偏”。

### 4. 成本与质量层：缓存 + 版本化
- 对同一 `prompt_signature`（anchor+routing+decision_id集合）加缓存；
- 写入 `prompt_contract_version`、`policy_version`，便于回滚；
- 对 parse 失败按保守策略回退为 `context_only`，避免系统失控。

### 5. 学习层：反馈闭环
- 挂接用户采纳/驳回率到路由阈值；
- `llm_conflict` 与 `llm_plan` 的误判率用于动态调权：提高 `system` 自动通过率/提高 `user` escalate 阈值；
- 每周产出冲突样本报告，做 prompt 版本AB实验（`v1.1`,`v1.2`）。

## 六、下一步（推荐执行顺序）

1. 保持 `plan`、`conflict` 两类 contract 稳定并上版本；
2. 完成 `llm_review_prompt_signature`（批次去重）；
3. 对 admin 前端加“LLM建议摘要”展示与“采纳原因”字段；
4. 在 `conflict_prompt`/`plan_prompt` 中加入统一知识快照（历史 arbitrate 统计）；
5. 加入每日离线回放任务：同一历史样本比对不同版本输出变化率。

## 四、当前落地状态（已实现）

- `v17_rebirth/backend/services/llm_prompt_contracts.py`
  - 统一生成决策/冲突 prompt 文本
  - 写明输出 contract、枚举、版本与 fallback
- `v17_rebirth/backend/api/stream_v17.py`
  - `_build_llm_plan_prompt` 改为调用统一 contract 生成器
- `v17_rebirth/backend/services/llm_conflict_arbiter.py`
  - `build_llm_conflict_prompt` 改为统一冲突合同生成

## 五、下一步建议（高优先）

1. 给冲突路由添加 `plan_cache_key`，同一批次重复提交不重复调用模型。  
2. 在 admin 冲突裁决入口返回 `llm_request_id` + `prompt_contract_version`，便于问题回放。  
3. 增加 parser 容错：支持模型返回 `output_version`、`results_by_conflict`、`decisions` 三种结构。  
4. 将“LLM 返回结果置信度”与 `llm_feedback` 一起喂给 `arbiter_router`，闭环自适应路由阈值。  
