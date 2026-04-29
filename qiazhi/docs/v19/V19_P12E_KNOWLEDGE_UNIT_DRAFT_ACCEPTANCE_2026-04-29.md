# V19 P12-E Knowledge Unit Draft 验收记录

日期：2026-04-29

状态：完成第一版

## 1. 本阶段目标

P12-E 在 Source Archive 和 Excerpt Archive 之上增加知识单元草稿层。

它的作用是让八字资料开始变成结构化知识对象，但仍然不进入 active knowledge，不进入推理引擎。

合法链路：

```text
Source Record
→ Excerpt Record
→ Knowledge Unit Draft
→ Rule Knowledge Proposal
→ Validation
→ Review / Version
→ Future Engine Adapter
```

## 2. 已完成能力

### 2.1 后端能力

在 `v19/bazi_source_archive.py` 中新增：

```text
list_knowledge_drafts
create_knowledge_draft
```

支持字段：

```text
draft_id
knowledge_id
domain
category
title
statement
structured_facts
conditions
source_excerpt_ids
source_refs
risk_level
confidence_prior
status
allowed_usage
forbidden_usage
history
guardrails
```

### 2.2 Admin API

新增管理员接口：

```text
GET  /api/admin/bazi-source-archive/knowledge-drafts
POST /api/admin/bazi-source-archive/knowledge-drafts
```

权限：

```text
admin only
```

### 2.3 Admin UI

Admin 中文治理台新增：

```text
Knowledge Unit Draft
```

能力：

```text
- 输入 knowledge_id
- 输入 domain
- 输入 category
- 选择 risk_level
- 关联 source_excerpt_ids
- 输入 statement
- 输入 structured_facts JSON
- 创建 knowledge draft
- 刷新 draft 列表
```

## 3. 护栏

Knowledge Draft 明确是：

```text
DRAFT_ONLY
NO_ACTIVE_RULE_CREATION
NO_RUNTIME_INFERENCE_CHANGE
REQUIRES_RULE_PROPOSAL_BEFORE_RUNTIME
```

## 4. 明确未做

本阶段没有做：

```text
- 不进入 v19/.runtime/knowledge_units.json
- 不进入 Knowledge Evidence Store
- 不进入 income_stability
- 不进入 ResultCard
- 不生成 Rule Proposal
- 不自动校验为 active rule
```

## 5. 当前 V19 数据库优先链路状态

现在已经具备：

```text
Source Archive ✔
Excerpt Archive ✔
Knowledge Unit Draft ✔
Rule Knowledge Proposal Ledger ✔
Validation / Approval / Version Record ✔
```

仍然保持：

```text
active inference unchanged
/oracle unchanged
LLM not authority
```

## 6. 下一阶段建议

下一步可以进入：

```text
P12-F：Knowledge Draft → Rule Proposal 手动转化入口
```

范围：

```text
- 从 draft 创建 bazi rule proposal
- 自动带入 source refs / excerpt ids
- 仍需 validation / approval
- 不自动激活
```
