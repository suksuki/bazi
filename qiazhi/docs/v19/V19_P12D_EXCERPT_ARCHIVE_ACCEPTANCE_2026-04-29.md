# V19 P12-D Excerpt Archive 验收记录

日期：2026-04-29

状态：完成第一版

## 1. 本阶段目标

P12-D 在 P12-C Source Archive 之上增加短摘录 / 摘要层。

目标不是抓取全文，也不是生成规则，而是建立从资料来源到知识单元草稿之间的中间层。

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

### 2.1 Excerpt Record 后端能力

在 `v19/bazi_source_archive.py` 中新增：

```text
list_excerpt_records
create_excerpt_record
```

支持字段：

```text
excerpt_id
source_id
locator
original_excerpt_short
normalized_summary
keywords
risk_level
language
status
allowed_usage
forbidden_usage
history
guardrails
```

### 2.2 短摘录长度限制

已设置：

```text
MAX_SHORT_EXCERPT_CHARS = 600
```

目的：

```text
避免把现代版权资料或古籍全文直接搬进系统。
鼓励摘要化、结构化、可审查。
```

### 2.3 Admin API

新增管理员接口：

```text
GET  /api/admin/bazi-source-archive/excerpts
POST /api/admin/bazi-source-archive/excerpts
```

权限：

```text
admin only
```

### 2.4 Admin UI

Admin 中文治理台新增：

```text
Excerpt Archive
```

能力：

```text
- 输入 Source ID
- 输入 locator
- 输入 risk level
- 输入 keywords
- 输入 short excerpt
- 输入 normalized summary
- 创建 excerpt
- 刷新 excerpt 列表
```

## 3. 护栏

Excerpt Archive 明确返回和展示：

```text
SHORT_EXCERPT_ONLY
NO_BULK_COPY
SOURCE_ARCHIVE_ONLY
NO_ACTIVE_RULE_CREATION
NO_RUNTIME_INFERENCE_CHANGE
```

## 4. 明确未做

本阶段没有做：

```text
- 不自动抓取网页内容
- 不自动 OCR PDF
- 不自动总结古籍
- 不自动生成 Knowledge Unit
- 不自动生成 Rule Proposal
- 不改变 /oracle
- 不改变 income_stability
```

## 5. 下一阶段建议

下一步进入：

```text
P12-E：Knowledge Unit Draft 生成与审核入口
```

范围：

```text
- 从 excerpt 手动创建 knowledge draft
- 要求 allowed_usage / forbidden_usage
- 要求 source_refs
- 要求 risk_level
- 不进入 active inference
```
