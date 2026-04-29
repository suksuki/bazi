# V19 P12-F Knowledge Draft → Rule Proposal 验收记录

日期：2026-04-29

状态：完成第一版

## 1. 本阶段目标

P12-F 建立从知识草稿到八字规则提案的手动桥接流程。

合法链路：

```text
Knowledge Unit Draft
→ Draft Review Queue
→ proposal_ready
→ Rule Knowledge Proposal Ledger
→ Validation
→ Approval
→ Version Record
```

## 2. 已完成能力

### 2.1 后端桥接

新增：

```text
build_rule_proposal_from_knowledge_draft
```

位置：

```text
v19/bazi_source_archive.py
```

能力：

```text
- 根据 draft_id 或 knowledge_id 查找知识草稿
- 要求 review_status = proposal_ready
- 禁止 R4 知识进入规则提案
- 自动映射 rule domain
- 自动带入 source_refs / source_excerpt_ids / risk_level / forbidden_usage
- 生成 create_bazi_rule_proposal 所需 payload
```

### 2.2 Admin API

新增：

```text
POST /api/admin/bazi-source-archive/knowledge-drafts/{draft_id}/create-rule-proposal
```

该接口会：

```text
1. 检查知识草稿是否存在
2. 检查是否 proposal_ready
3. 检查是否 R4 archive-only
4. 创建 Bazi Rule Proposal
5. 写入 proposal history
6. 不改变 runtime inference
```

### 2.3 Admin UI

新增入口：

```text
从 Draft 创建 Rule Proposal
```

位置：

```text
八字资料来源库 → Knowledge Unit Draft
```

UI 支持：

```text
- 选择 Draft ID / Knowledge ID
- 自动或手动指定 Proposal Domain
- 输入 Proposal Rationale
- 从 Draft 列表一键填入 Proposal ID
```

## 3. 强制边界

### 3.1 必须 proposal_ready

如果知识草稿仍是：

```text
pending
reviewed
needs_revision
rejected
deprecated
```

则不能创建规则提案。

### 3.2 R4 禁止进入规则提案

R4 包括：

```text
盲派象法
神煞
断语
案例
高风险象义材料
```

这些只能进入：

```text
source archive
analyst reference
case archive
```

不能进入：

```text
Rule Proposal
active inference
ResultCard
```

## 4. Domain 映射

当前自动映射：

```text
ten_god → ten_god_relation
luck_flow / timing_context → time_structure
wealth → income_stability
five_element / strength → day_master_element
core_structure → structural_relation 或 day_master_element
```

如果无法映射，则拒绝创建提案。

## 5. 明确未做

本阶段没有做：

```text
- 不自动 validate
- 不自动 approve
- 不自动 version record
- 不自动 active rule
- 不改变 inference
- 不改变 /oracle
- 不改变 ResultCard
```

## 6. 当前完整治理链路

```text
Source Archive
→ Excerpt Archive
→ Knowledge Unit Draft
→ Draft Review Queue
→ Rule Knowledge Proposal Ledger
→ Schema Validation
→ Analyst/Admin Approval
→ Version Record
→ Future Engine Adapter
```

## 7. 下一步建议

下一步可以做：

```text
P12-G：Rule Proposal Review QA + 批量 proposal readiness view
```

目标：

```text
- 统计 proposal_ready drafts
- 统计 blocked R4 drafts
- 统计已生成 proposal 的 drafts
- 给分析师一个更清楚的治理面板
```
