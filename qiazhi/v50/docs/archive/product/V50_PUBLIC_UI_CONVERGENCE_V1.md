# V50 Public UI Convergence v1

Status: implemented product baseline

## Goal

公开界面必须像一个由 Abu 引导的智能命理系统，而不是四份并列报告、工程控制台或功能目录。此次清理只调整信息架构与显示层，不修改命理事实、LLM 推理、角色权限或案例数据。

## Public Surface

```text
Welcome / Birth Intake
→ Current Mingli Journey
   01 看见命局
   02 现在处于哪里
   03 继续探索
→ On-demand Task View
→ Return to Current Mingli Journey
```

游客与普通用户没有常驻的“综合 / 八字 / 紫微 / 人生地图”标签。以下内容只在用户或 Abu 需要时出现：

- 八字长期结构；
- 紫微人生舞台；
- 人生主题选择；
- 单个专题推演。

## Specialized Task Views

八字详情固定为：

```text
长期结构 → 命盘底图 → 现实表现
```

紫微详情固定为：

```text
人生舞台 → 当前阶段
```

单个专题固定为：

```text
核心判断 → 何时成立、何时受阻 → 现实方向与下一问
```

系统不得把任意后端字段自动包装成新的可见页面或章节。

## Role Boundary

- Guest / Member：单一命理旅程与按需任务视图。
- Practitioner / Research：保留综合、八字、紫微和专题的专业工作视图。
- Admin：可以切换披露模式测试，但不重算命盘。

## Content Ownership

- Task Canvas：稳定结论、阶段状态、专题因果、行动与当前 Probe。
- Abu：一句解释、一个问题、导航和受控操作。
- Header / Archive：当前命盘、账户、档案和继续入口。
- Hidden：模型、Schema、审查、存储、调试与工程信息。

## Removed From Public Navigation

- 四个并列报告标签；
- 自动把每个返回字段变成折叠章节的逻辑；
- 重复的页面标题与报告标题；
- 专题结果中的分散“机会 / 风险 / 时机 / 行动 / Probe / 边界”页面层级；
- 普通用户页面上的专业研判工作台。

## Invariants

1. 首屏永远最多三个命理阶段。
2. 当前只展开一个阶段。
3. 专题结果最多三个阶段。
4. 一个任务只有一个主要动作。
5. Abu 与页面使用同一个动作，不复制 CTA。
6. 返回动作不触发 LLM，也不重新计算命盘。
7. 角色切换只改变披露，不改变 Life Case。
