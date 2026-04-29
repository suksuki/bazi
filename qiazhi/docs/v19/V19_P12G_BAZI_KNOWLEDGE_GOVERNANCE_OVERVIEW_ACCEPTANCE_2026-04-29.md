# V19 P12-G 八字知识库治理总览验收记录

日期：2026-04-29

状态：完成第一版

## 1. 本阶段目标

P12-G 不是新增规则能力，而是为 Admin 增加八字知识库治理状态总览。

目标：

```text
让管理员 / 分析师快速看到：
- 当前有多少资料来源
- 当前有多少短摘录
- 当前有多少知识草稿
- 哪些草稿已经 proposal_ready
- 哪些 R4 草稿被阻断
- 哪些草稿需要修改
- 哪些草稿仍待审核
```

## 2. 已完成能力

### 2.1 后端总览

新增：

```text
source_governance_overview
```

位置：

```text
v19/bazi_source_archive.py
```

返回内容：

```text
counts
proposal_ready_items
r4_blocked_items
needs_revision_items
pending_items
guardrails
```

### 2.2 API

新增：

```text
GET /api/admin/bazi-source-archive/governance-overview
```

权限：

```text
admin only
```

### 2.3 Admin UI

新增按钮：

```text
加载治理总览
```

显示：

```text
Draft 总数
Proposal Ready 数量
R4 Blocked 数量
Pending 数量
Needs Revision 数量
按 review_status 汇总
按 risk_level 汇总
```

## 3. 当前本地状态

当前 runtime 读数：

```text
knowledge_drafts: 21
proposal_ready: 0
r4_blocked: 2
needs_revision: 0
pending: 21
```

这符合预期：

```text
当前知识库已导入草稿层，但尚未经过人工审核。
没有任何草稿可以直接生成规则提案。
R4 盲派/神煞边界类知识被明确阻断。
```

## 4. 边界

P12-G 只做治理总览。

不做：

```text
不创建规则
不修改规则
不自动审核
不自动 proposal_ready
不改变 /oracle
不改变 inference
```

## 5. 当前完整链路

```text
Source Archive
→ Excerpt Archive
→ Knowledge Unit Draft
→ Draft Review Queue
→ Governance Overview
→ Rule Knowledge Proposal Ledger
→ Validation / Approval / Version
```
