# V19 当前八字知识库完成记录

日期：2026-04-29

状态：当前阶段完成

范围：对齐 V17/V18 知识系统文档与 V19 数据库优先新框架，完成当前应纳入的八字知识库草稿层。

## 1. 总结

当前 V19 已经不再采用 V17/V18 的插件优先模式，而是完成了数据库优先的知识链路第一版：

```text
Source Archive
→ Excerpt Archive
→ Knowledge Unit Draft
→ Rule Knowledge Proposal Ledger
→ Validation / Approval / Version Record
```

本次新增了当前八字知识库草稿种子文件，并接入 Admin 一键导入。

新增：

```text
docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json
```

Admin 可通过：

```text
八字资料来源库 → Knowledge Unit Draft → 导入当前知识库
```

将当前知识库导入草稿层。

## 2. 已完成的知识范围

### 2.1 基础符号与结构

已覆盖：

```text
十天干
十二地支
天干五行阴阳
地支藏干
五行生克
```

对应知识草稿：

```text
core.heavenly_stems.v1
core.earthly_branches.v1
core.stem_attributes.v1
core.branch_attributes_hidden_stems.v1
core.five_element_relations.v1
```

### 2.2 十神体系

已覆盖：

```text
十神基础映射
十神作为关系元数据的边界
```

对应知识草稿：

```text
core.ten_god_mapping.v1
```

边界：

```text
十神标签不是预测结论。
不能单独生成吉凶或 fortune。
```

### 2.3 地支关系

已覆盖：

```text
六合
六冲
三合
三会
刑害破索引
```

对应知识草稿：

```text
core.branch_relations.six_combination.v1
core.branch_relations.six_clash.v1
core.branch_relations.three_harmony.v1
core.branch_relations.three_meeting.v1
core.branch_relations.penalty_harm_break.v1
```

边界：

```text
当前只做结构关系检测。
不直接输出好坏、机会、风险或流年预测。
```

### 2.4 天干关系

已覆盖：

```text
天干五合
```

对应知识草稿：

```text
core.stem_combination.v1
```

### 2.5 墓库结构

已覆盖：

```text
辰戌丑未四墓库
墓库作为结构候选
财库相关未来提案来源
```

对应知识草稿：

```text
core.vault_structure.v1
```

边界：

```text
不直接判断发财、破财、开库发财等传统断语。
```

### 2.6 日主强弱证据模型

已覆盖：

```text
月令
根气
同党
异党
生助
克泄耗
```

对应知识草稿：

```text
strength.day_master_evidence_model.v1
```

边界：

```text
当前只定义 evidence schema。
不替换现有 income_stability 推理。
```

### 2.7 财富结构知识

已覆盖：

```text
财星强弱
食伤生财机制候选
比劫与财结构关系候选
```

对应知识草稿：

```text
wealth.wealth_strength.v1
wealth.output_generate_wealth.v1
wealth.peer_competition.v1
```

边界：

```text
只作为 feature / mechanism candidate。
不直接输出财富预测。
不直接改变 ResultCard。
```

### 2.8 时间结构边界

已覆盖：

```text
大运 / 流年只作为 Time Context
不直接影响 income_stability
```

对应知识草稿：

```text
time.time_context_boundary.v1
```

### 2.9 格局索引

已覆盖：

```text
正官格
七杀格
正财格
偏财格
食神格
伤官格
印绶格
建禄格
羊刃格
从格
化气格
专旺格
杂气格
```

对应知识草稿：

```text
pattern.structure_index.v1
```

边界：

```text
格局目前只是结构索引。
不输出命好、命差、富贵贫贱。
```

### 2.10 盲派、象法、神煞边界

已覆盖：

```text
盲派象法归档边界
神煞归档边界
```

对应知识草稿：

```text
symbolic.blind_school_boundary.v1
symbolic.shensha_boundary.v1
```

边界：

```text
只作为 source archive / analyst reference。
不进入 active inference。
```

## 3. 系统接入

### 3.1 后端

更新：

```text
v19/bazi_source_archive.py
```

新增能力：

```text
seed_current_knowledge_drafts
```

### 3.2 API

新增：

```text
POST /api/admin/bazi-source-archive/knowledge-drafts/seed-current
```

权限：

```text
admin only
```

### 3.3 Admin UI

更新：

```text
v19/frontend/admin.html
v19/frontend/assets/admin.js
```

新增按钮：

```text
导入当前知识库
```

位置：

```text
八字资料来源库 → Knowledge Unit Draft
```

## 4. 与旧 V17/V18 的对齐

当前知识库草稿对齐了旧系统中的：

```text
V18.2 Knowledge Corpus → Rule Kernel 分层
V18 runtime bazi_knowledge_units.json
V18 bazi_feature_definitions.json
V18 wealth domain bundles
V19 core_units_v1.md
V19 wealth_units_v1.md
```

但没有直接导入：

```text
旧插件 active rules
旧评分权重
旧传统断语
旧 narrative prompt
旧 plugin match ratio
```

## 5. 当前仍然不是 active inference

必须明确：

```text
当前完成的是八字知识库草稿层。
不是 active rule database。
不是 prediction engine。
```

当前所有知识草稿都带有护栏：

```text
DRAFT_ONLY
NO_ACTIVE_RULE_CREATION
NO_RUNTIME_INFERENCE_CHANGE
NO_DIRECT_PLUGIN_RULE_REUSE
REQUIRES_RULE_PROPOSAL_BEFORE_RUNTIME
```

## 6. 下一步

下一步应该进入：

```text
P12-F：Knowledge Draft → Rule Proposal 手动转化入口
```

目标：

```text
从知识草稿选择一条
生成 Rule Knowledge Proposal
自动带入 source_refs / risk_level / forbidden_usage
仍需 validation / approval / version record
不自动激活
```

## 7. 结论

当前 V19 已完成“目前所有应纳入的八字知识库”的数据库草稿层：

```text
基础知识 ✔
十神 ✔
地支关系 ✔
墓库 ✔
日主强弱证据 ✔
财富结构候选 ✔
时间边界 ✔
格局索引 ✔
盲派/神煞边界 ✔
旧系统对齐 ✔
```

系统方向保持：

```text
资料数据库先行
知识草稿其次
规则提案第三
推理激活最后
```

## 8. Knowledge Draft Review Queue

已新增知识草稿审核队列能力。

后端：

```text
update_knowledge_draft_review
```

API：

```text
POST /api/admin/bazi-source-archive/knowledge-drafts/{draft_id}/review
```

Admin UI：

```text
Review Draft ID / Knowledge ID
Review Status
Review Note
更新 Draft 审核
```

审核状态：

```text
pending
reviewed
needs_revision
proposal_ready
rejected
deprecated
```

边界：

```text
审核状态只影响知识草稿治理。
不生成规则。
不改变推理。
不改变 /oracle。
```

## 9. Knowledge Draft → Rule Proposal 桥接

已新增从知识草稿生成规则提案的手动桥接流程。

API：

```text
POST /api/admin/bazi-source-archive/knowledge-drafts/{draft_id}/create-rule-proposal
```

硬约束：

```text
1. Knowledge Draft 必须 review_status = proposal_ready
2. R4 archive-only 知识不能生成规则提案
3. 生成后仍然只是 Rule Proposal
4. 必须继续经过 validation / approval / version record
5. 不改变 runtime inference
```

Admin UI 已支持：

```text
从 Draft 创建 Rule Proposal
Use for Proposal
```

当前完整链路：

```text
Source Archive
→ Excerpt Archive
→ Knowledge Unit Draft
→ Draft Review Queue
→ Rule Knowledge Proposal Ledger
→ Validation / Approval / Version
```

## 10. 八字知识库治理总览

已新增治理总览：

```text
GET /api/admin/bazi-source-archive/governance-overview
```

Admin UI：

```text
加载治理总览
```

当前本地状态：

```text
knowledge_drafts: 21
proposal_ready: 0
r4_blocked: 2
needs_revision: 0
pending: 21
```

解释：

```text
所有当前知识都在草稿层。
尚未有草稿通过人工审核进入 proposal_ready。
R4 盲派/神煞边界类知识被阻断，不能转规则提案。
```

## 11. Bazi Rule DB 直接入库

已新增规则数据库层：

```text
v19/bazi_rule_db.py
```

已新增 API：

```text
GET  /api/admin/bazi-rule-db/status
GET  /api/admin/bazi-rule-db/rules
POST /api/admin/bazi-rule-db/ingest-current
```

Admin UI 新增：

```text
Bazi Rule DB
当前知识直接入库
```

当前入库结果：

```text
knowledge_drafts: 21
rule_db_records: 19
blocked_R4: 2
```

R4 阻断：

```text
symbolic.blind_school_boundary.v1
symbolic.shensha_boundary.v1
```

当前规则数据库已覆盖 R0-R3 的基础八字知识和结构候选规则，为下一步 Engine Adapter 做准备。

## 12. Rule DB 驱动的动态引导提问

已新增：

```text
v19/bazi_guided_questions.py
```

接入：

```text
/api/agent/structure
/api/agent/turn
```

新增返回：

```text
guided_question_context
```

前端 Question Builder 已支持：

```text
静态问题库 + 动态规则问题合并
动态问题三语 label
动态问题点击后进入 message
动态问题反馈进入原有 feedback ledger
```

当前支持触发：

```text
墓库结构
地支冲合关系
十神元数据
财富结构候选
时间结构边界
格局索引边界
```

边界：

```text
Rule DB 只用于生成引导问题。
不改变 income_stability。
不改变 ResultCard。
不生成 fortune。
```
