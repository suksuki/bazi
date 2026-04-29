# V19 八字数据库优先知识系统计划

日期：2026-04-29

状态：执行稿

定位：V19 不再沿用 V17/V18 的插件优先模式，而是先建立八字资料数据库与知识治理系统，再逐步生成规则提案和推理能力。

## 1. 方向修正

V17/V18 的模式可以概括为：

```text
知识 / 规则 / 专题能力
→ 插件承载
→ 插件内聚合推理与展示
```

V19 的新模式必须改为：

```text
资料来源库
→ 知识摘录库
→ 知识单元库
→ 规则提案账本
→ 校验 / 审核 / 版本记录
→ 未来 active rule
```

也就是：

```text
先做八字数据库系统
再做相应规则
最后才考虑推理引擎激活
```

## 2. 为什么不能继续插件优先

旧插件模式的问题：

```text
1. 知识来源、规则、展示、推理容易混在一起。
2. 插件容易绕过统一审核流程。
3. 不同插件之间的规则冲突难以治理。
4. 传统断语、象义、经验规则容易直接污染推理层。
5. 后期很难追溯某个结论来自哪条知识、哪本书、哪个版本。
```

V19 的数据库优先模式要解决：

```text
1. 先记录来源。
2. 再摘录知识。
3. 再结构化成知识单元。
4. 再进入规则提案。
5. 再通过校验与审核。
6. 最后才允许进入推理层。
```

## 3. V19 八字数据库分层

### Layer 0：Source Archive（资料来源库）

记录资料来源，不做规则判断。

包括：

```text
古籍
现代整理本
旧系统知识文件
命理师笔记
网络文章
百科资料
PDF / 图书馆条目
```

输出：

```text
source_id
source_type
title
author_or_compiler
period
url_or_path
reliability
license_note
allowed_usage
forbidden_usage
```

### Layer 1：Excerpt Archive（知识摘录库）

从来源中摘出具体知识片段。

注意：

```text
只能短摘录或摘要。
不能大量复制现代版权文本。
古籍公开文本也要保留来源定位。
```

输出：

```text
excerpt_id
source_id
locator
original_excerpt_short
normalized_summary
keywords
risk_level
```

### Layer 2：Knowledge Unit Draft（知识单元草稿）

将摘录转成结构化知识。

输出：

```text
knowledge_id
domain
category
statement
structured_facts
conditions
allowed_usage
forbidden_usage
source_refs
confidence_prior
status=draft
```

### Layer 3：Rule Knowledge Proposal（规则知识提案）

只有通过分析师整理后，才进入规则提案。

输出：

```text
proposal_id
source_knowledge_ids
rule_domain
rule_type
inputs
outputs
reasoning_path
runtime_scope
validation
review
status
```

### Layer 4：Validated Rule Record（已校验规则记录）

通过 schema validation 和人工审核后，进入版本记录。

注意：

```text
这仍然不等于 active inference。
```

### Layer 5：Active Inference Rule（未来激活规则）

只有在单独版本计划中才允许激活。

当前禁止：

```text
古籍摘录直接激活
网络文章直接激活
盲派断语直接激活
流年大运直接影响 income_stability
```

## 4. 首批资料来源分类

### 4.1 古籍主来源

首批收录：

```text
三命通会
渊海子平
滴天髓
滴天髓阐微
穷通宝鉴
子平真诠
神峰通考
命理约言
```

用途：

```text
建立 source archive
建立知识主题索引
提取结构知识与规则候选
保留传统断语但不直接推理
```

### 4.2 旧系统来源

首批收录：

```text
V18_2_KNOWLEDGE_CORPUS_TO_RULE_KERNEL_2026-04-27.md
bazi_knowledge_units.json
bazi_feature_definitions.json
v18_1_wealth_domain_bundles.json
bazi_symbolic_primitives.v1.json
wealth_code_knowledge.v1.json
```

用途：

```text
迁移线索
feature schema 参考
规则提案来源
污染风险审计
```

### 4.3 网络资料来源

用途：

```text
只做线索
不做权威
不直接进入 active rule
```

## 5. 知识分类体系

V19 八字数据库按以下类别归档：

```text
core_symbol：天干、地支、五行、阴阳
stem_branch_attribute：干支属性
hidden_stem：藏干
five_element_relation：五行生克
ten_god：十神
branch_relation：六合、三合、三会、冲、刑、害、破
stem_relation：天干合化
strength_model：旺衰、得令、得地、得势
vault：墓库、财库、开库、闭库
pattern_structure：格局、结构模式
timing_context：大运、流年、岁运关系
blind_symbolic：盲派象法
shensha：神煞
classical_saying：古籍断语 / 口诀
case_record：命例 / 案例
```

## 6. 风险等级

### R0：基础事实

例：

```text
天干列表
地支列表
五行生克
六合表
六冲表
```

允许：

```text
可以进入 core knowledge。
可以用于结构检测。
```

### R1：结构关系

例：

```text
十神映射
藏干
墓库关系
三合三会
```

允许：

```text
可以进入 knowledge unit。
可作为 future rule proposal。
```

### R2：机制解释

例：

```text
食伤生财
比劫夺财
财库开合
印制食伤
```

允许：

```text
只能进入 rule proposal。
需要 evidence、confidence、review。
```

### R3：格局与用神判断

例：

```text
正官格
七杀格
食神格
伤官格
从格
调候用神
```

允许：

```text
只能做 proposal draft。
不得直接影响当前 ResultCard。
```

### R4：象义 / 盲派 / 神煞 / 断语

例：

```text
盲派口诀
宫位象
职业象
婚恋断语
应期断语
```

允许：

```text
只进入 source archive 或 analyst reference。
不进入 active inference。
```

## 7. 当前第一阶段执行范围

第一阶段只做：

```text
1. 建立 source archive schema
2. 建立首批 source catalog
3. 建立 collection backlog
4. 建立知识分类与风险分级
5. 标注哪些来源可用于未来规则提案
```

第一阶段不做：

```text
不抓取全文入库
不大规模复制古籍原文
不生成 active rules
不改变 inference
不让时间背景影响 income_stability
```

## 8. 下一步工程任务

接下来按顺序执行：

```text
P12-C：Source Archive + Source Catalog
P12-D：Excerpt Archive Schema
P12-E：Knowledge Unit Draft Schema 扩展
P12-F：Legacy Knowledge Import Mapping
P13：基础规则提案 seeds
```

## 9. 当前交付物

本阶段已经建立：

```text
docs/bazi_knowledge/source_archive/source_archive_schema_v1.md
docs/bazi_knowledge/source_archive/source_catalog_v1.json
docs/bazi_knowledge/source_archive/collection_backlog_v1.md
```

## 10. 最终判断

V19 的正确知识建设路径是：

```text
资料数据库先行
知识结构化其次
规则提案第三
推理激活最后
```

这样可以吸收 V17/V18 插件时代积累的知识，同时避免插件时代最大的问题：规则、来源、叙事和推理混在一起。

## 11. 与 V19 新框架 / 新引擎的对齐原则

V19 八字数据库系统必须对齐当前新框架，而不是回到 V17/V18 插件模式。

### 11.1 引擎分层

V19 新框架按以下层次工作：

```text
Source Archive（资料来源）
→ Knowledge Unit（知识单元）
→ Rule Proposal（规则提案）
→ Validation（校验）
→ Review / Version（审核与版本）
→ Engine Adapter（引擎适配）
→ Inference（推理）
→ Renderer（确定性展示）
→ Optional LLM Explanation（可选解释）
```

任何知识都不能跳过中间层直接进入推理。

### 11.2 数据库优先，不是插件优先

旧系统：

```text
插件承载知识 + 插件执行逻辑 + 插件展示结果
```

V19：

```text
数据库承载知识来源与知识单元
提案系统承载规则变更
引擎只读取经过批准的稳定输入
```

因此后续新增内容必须进入：

```text
资料来源库
知识单元草稿
规则提案账本
```

不能直接新增：

```text
插件预测逻辑
插件断语模板
插件内部规则权重
```

### 11.3 Engine Adapter 边界

未来如果某条规则要进入推理引擎，必须先通过 Engine Adapter。

Engine Adapter 的责任：

```text
1. 只接收 approved / versioned 的规则输入。
2. 将规则转成结构化 signal。
3. 输出 rule attribution。
4. 保留 source_refs 与 proposal_id。
5. 不生成叙事。
6. 不生成传统断语。
```

禁止：

```text
规则直接调用 LLM
规则直接输出 fortune
规则直接写 ResultCard 文案
规则绕过 validation
```

### 11.4 Time Context 边界

时间结构仍然是 context，不是结论。

当前阶段允许：

```text
流年柱
大运柱
与原局的冲合关系
algorithm_status
provenance
```

当前阶段禁止：

```text
流年直接改变 income_stability
大运直接生成预测结论
输出今年好坏
输出什么时候发财
```

### 11.5 LLM 边界

LLM 在 V19 中只能作为：

```text
解释辅助
提案草稿辅助
管理员治理辅助
```

LLM 不能作为：

```text
规则权威
知识权威
active inference
自动学习器
自动激活器
```

### 11.6 和当前 V19 能力的对应关系

当前已有：

```text
Guided Agent
Pillar-first UI
Knowledge Evidence Store
Feedback Ledger
Guided Question Governance
Rule Attribution
Rule Knowledge Proposal Ledger
Admin Governance Console
```

八字数据库系统要接入的位置：

```text
Source Archive
→ Knowledge Unit Draft
→ Rule Knowledge Proposal Ledger
```

暂时不接入：

```text
active inference
ResultCard 主结论
time-aware inference
LLM 主回答
```

### 11.7 总约束

一句话：

```text
V19 的新引擎只接受被治理过的结构化知识，不接受插件式黑盒知识。
```

## 12. P12-C / P12-D / P12-E 落地状态

当前已从文档路线推进到系统第一版。

### 12.1 已落地层级

```text
Source Archive ✔
Excerpt Archive ✔
Knowledge Unit Draft ✔
Rule Knowledge Proposal Ledger ✔
```

### 12.2 新增后端模块

```text
v19/bazi_source_archive.py
```

职责：

```text
- 管理资料来源
- 管理短摘录 / 摘要
- 管理知识单元草稿
- 保持 no runtime inference change 护栏
```

### 12.3 新增 Admin API

```text
/api/admin/bazi-source-archive/status
/api/admin/bazi-source-archive/sources
/api/admin/bazi-source-archive/seed
/api/admin/bazi-source-archive/excerpts
/api/admin/bazi-source-archive/knowledge-drafts
```

### 12.4 新增 Admin UI

Admin 中文治理台新增：

```text
八字资料来源库
Excerpt Archive
Knowledge Unit Draft
```

### 12.5 仍然不做

```text
不改变 /oracle
不改变 income_stability
不生成 active rule
不让古籍/网络资料直接进入推理
不让 LLM 成为知识权威
```

## 13. 当前八字知识库草稿层完成状态

已新增：

```text
docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json
```

该文件收拢当前阶段所有应进入 V19 数据库系统的八字知识草稿：

```text
基础符号
干支属性
藏干
五行生克
十神
六合 / 六冲 / 三合 / 三会 / 刑害破
天干五合
墓库
日主强弱证据模型
财富结构候选
时间结构边界
格局索引
盲派/神煞归档边界
```

Admin 已支持：

```text
八字资料来源库 → Knowledge Unit Draft → 导入当前知识库
```

该导入仍然只进入：

```text
Knowledge Unit Draft
```

不进入：

```text
active rule
runtime inference
ResultCard
/oracle 主结果
```
