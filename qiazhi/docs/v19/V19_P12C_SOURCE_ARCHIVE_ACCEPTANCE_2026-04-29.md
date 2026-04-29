# V19 P12-C Source Archive 验收记录

日期：2026-04-29

状态：完成第一版

## 1. 本阶段目标

P12-C 的目标是将八字知识建设从文档阶段推进到系统第一层：资料来源库。

本阶段不是规则扩展，也不是推理增强。

```text
目标：Source Archive 可管理
非目标：active rule / inference mutation
```

## 2. 已完成能力

### 2.1 Source Archive 后端模块

新增：

```text
v19/bazi_source_archive.py
```

能力：

```text
- 读取 docs/bazi_knowledge/source_archive/source_catalog_v1.json
- 建立 runtime source archive fallback
- 支持 seed 到 v19/.runtime/bazi_source_archive.json
- 支持 source 列表查询
- 支持 source_type / risk_level / ingestion_status / q 过滤
- 支持手动创建 source record
- 支持更新 ingestion_status
```

### 2.2 Admin API

新增管理员接口：

```text
GET  /api/admin/bazi-source-archive/status
GET  /api/admin/bazi-source-archive/sources
POST /api/admin/bazi-source-archive/seed
POST /api/admin/bazi-source-archive/sources
POST /api/admin/bazi-source-archive/sources/{source_id}/status
```

权限：

```text
admin only
```

### 2.3 Admin 中文治理台

Admin 页面新增：

```text
八字资料来源库
```

功能：

```text
- 初始化来源目录
- 刷新来源
- 按风险等级过滤
- 按来源类型过滤
- 按关键词搜索
- 显示 allowed_usage / forbidden_usage
- 显示 no runtime inference change 护栏
```

### 2.4 首批 Source Catalog

首批已 catalog 的来源包括：

```text
三命通会
渊海子平
滴天髓
滴天髓阐微
穷通宝鉴
神峰通考
子平真诠参考条目
V18.2 知识分层报告
V18 runtime bazi_knowledge_units.json
```

## 3. 治理边界

所有 Source Archive API 均返回或展示以下边界：

```text
SOURCE_ARCHIVE_ONLY
NO_ACTIVE_RULE_CREATION
NO_RUNTIME_INFERENCE_CHANGE
NO_DIRECT_PLUGIN_RULE_REUSE
ANALYST_REVIEW_REQUIRED_BEFORE_RULE_PROPOSAL
```

## 4. 明确未做

本阶段没有做：

```text
- 不抓取全文入库
- 不生成 Knowledge Unit Draft
- 不生成 active rule
- 不修改 income_stability
- 不接入 time-aware inference
- 不改变 /oracle 问题推荐
- 不让 LLM 处理资料来源
```

## 5. 与 V19 新框架对齐

P12-C 接入的位置是：

```text
Source Archive
```

尚未进入：

```text
Knowledge Unit
Rule Proposal
Validation
Inference
Renderer
```

合法链路保持为：

```text
Source Archive
→ Excerpt Archive
→ Knowledge Unit Draft
→ Rule Knowledge Proposal
→ Validation
→ Review / Version
→ Future Engine Adapter
```

## 6. 下一阶段建议

下一步建议进入：

```text
P12-D：Excerpt Archive Schema + 首批短摘录规范
```

范围：

```text
- 定义 excerpt_id / source_id / locator / short_excerpt / normalized_summary
- 只允许短摘录与摘要
- 不复制现代版权全文
- 不生成规则
```
