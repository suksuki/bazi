# V19 P28E 十神组合类知识 Review

状态：已入库为知识草案与 Rule DB 候选

日期：2026-04-30

## 目标

把“伤官见官、枭神夺食”这一类知识正式归入知识库，而不是散落在单个十神、财富或格局目录里。

本阶段只做低风险结构化：

- 组合是否存在。
- 涉及哪些十神。
- 作用机制需要哪些上下文。
- 哪些传统断语不能直接输出。

## 已完成

新增知识包：

```text
docs/bazi_knowledge/packs/p28e_ten_god_interaction_knowledge_draft_seeds_v1.json
```

覆盖 12 个组合，每个组合 2 条知识：

| 组合 | R1 | R2 |
|---|---|---|
| 伤官见官 | 组合存在 | 机制边界 |
| 枭神夺食 | 组合存在 | 机制边界 |
| 食神制杀 | 组合存在 | 机制边界 |
| 杀印相生 | 组合存在 | 机制边界 |
| 伤官配印 | 组合存在 | 机制边界 |
| 官印相生 | 组合存在 | 机制边界 |
| 财生官 | 组合存在 | 机制边界 |
| 食伤生财 | 组合存在 | 机制边界 |
| 比劫夺财 | 组合存在 | 机制边界 |
| 财破印 | 组合存在 | 机制边界 |
| 官杀混杂 | 组合存在 | 机制边界 |
| 羊刃驾杀 | 组合存在 | 机制边界 |

总计：24 条。

## 系统对齐

- `interaction` 领域映射到 `ten_god_relation`。
- Rule DB adapter 增加十神组合类回答范围：`explain_ten_god_interaction_without_verdict`。
- 推荐问题锚点增加：十神元数据、组合信号、非断语阅读。
- 中文审阅目录更新到 143 条结构化知识。
- 总目录 L3 已把首批 12 个组合标为“部分”。

## 当前边界

P28E 进入 Rule DB 候选层，但不启用 engine adapter。

这些知识不能直接输出：

- 官非、灾祸、疾病、破财、升职、婚姻、贵贱等传统断语。
- 具体年份或应期。
- 命好命坏、财富好坏等结果判断。

## 验证

已通过：

```text
python3 -m py_compile v19/bazi_rule_db.py v19/bazi_source_archive.py v19/lab_interfaces.py v19/server.py
node --check v19/frontend/assets/admin.js
python3 -m pytest -q v19/tests
git diff --check -- ':!v19/.runtime/*'
```

运行时同步结果：

```text
knowledge_drafts: 143
rule_db.rules: 141
p28.interaction drafts: 24
p28.interaction rules: 24
p28.interaction engine_enabled: 0
```

## P28F 调整

“伤官见官”不再作为单点专题单独推进，已经合并进“十神冲突 / 牵制 / 混杂专题”：

```text
docs/bazi_knowledge/interaction/ten_god_conflict_constraint_mixed_topic_v1.md
```

P28F 一次性补入同类对象：伤官制杀、官杀攻身、印制食伤、比劫分财、财多坏印、财滋杀、食伤混杂、印枭混杂、合杀留官、合官留杀。

## 下一步

进入 P28G：为“十神冲突 / 牵制 / 混杂专题”做合成盘碰撞矩阵和规则启用边界。

重点不是增加断语，而是补齐：

- 透干 vs 藏干。
- 本命 vs 大运流年。
- 有印救应 vs 无救应。
- 伤官、官星强弱和来源层。
- 与格局、宫位、财富/事业领域的连接边界。
