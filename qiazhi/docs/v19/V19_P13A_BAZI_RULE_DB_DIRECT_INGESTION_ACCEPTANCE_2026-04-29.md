# V19 P13-A Bazi Rule DB 直接入库验收记录

日期：2026-04-29

状态：完成第一版

## 1. 本阶段目标

根据新的产品方向，V19 不再把每条知识草稿都卡在人工审核之后才入库。当前阶段改为：

```text
Knowledge Draft
→ Bazi Rule DB
→ Future Engine Adapter
```

其中 R4 高风险知识仍然保持归档，不进入规则库。

## 2. 已完成能力

### 2.1 新增 Bazi Rule DB 模块

新增：

```text
v19/bazi_rule_db.py
```

能力：

```text
- 从 v19/.runtime/bazi_source_archive.json 读取 knowledge_drafts
- 将 R0-R3 知识草稿直接转为 rule records
- 阻断 R4 archive-only 知识
- 生成 input_contract / condition / output_contract / reasoning_path / evidence
- 保留 source_draft_id / source_refs / risk_level / forbidden_usage
```

### 2.2 新增 Admin API

```text
GET  /api/admin/bazi-rule-db/status
GET  /api/admin/bazi-rule-db/rules
POST /api/admin/bazi-rule-db/ingest-current
```

### 2.3 新增 Admin UI

新增区域：

```text
Bazi Rule DB
```

支持：

```text
当前知识直接入库
刷新 Rule DB
按 domain / risk / keyword 筛选
```

## 3. 当前入库结果

本地 runtime 已执行入库。

结果：

```text
knowledge_drafts: 21
rule_db_records: 19
blocked: 2
```

被阻断的 2 条为 R4：

```text
symbolic.blind_school_boundary.v1
symbolic.shensha_boundary.v1
```

这些仍然保持：

```text
archive-only
analyst reference only
not active rule
```

## 4. Rule DB 覆盖范围

当前 Rule DB 已覆盖：

```text
基础符号规则
干支属性规则
藏干规则
五行生克规则
十神映射规则
六合 / 六冲 / 三合 / 三会
刑害破索引
天干五合
墓库结构
日主强弱证据模型
财富结构候选
时间结构边界
格局索引
```

## 5. 与旧插件模式的区别

旧模式：

```text
插件内部承载知识与规则
```

当前模式：

```text
Knowledge Draft
→ Bazi Rule DB
→ Engine Adapter
```

规则记录是可查询、可追溯、可治理的，不再是插件黑盒。

## 6. 当前边界

Rule DB 已经是规则数据库，但还不是最终预测输出。

当前允许：

```text
规则入库
规则查询
规则作为 Engine Adapter 输入
结构信号输出准备
```

当前仍禁止：

```text
R4 断语/盲派/神煞直接入规则库
LLM 自动生成规则权威
插件黑盒规则
无 attribution 的预测结论
```

## 7. 下一阶段

下一步进入：

```text
P13-B：Bazi Rule Engine Adapter
```

目标：

```text
读取 Bazi Rule DB
基于 chart / time_context 输出 structural_rule_signals
为未来智能八字预测系统提供规则信号层
```
