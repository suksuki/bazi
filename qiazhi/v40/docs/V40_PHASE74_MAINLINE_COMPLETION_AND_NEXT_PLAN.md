# V40 Phase 74: Mainline Completion Audit And Next Plan

## 当前判断

V40 已经从“能跑的隔离骨架”进入“真实命理产品验收”阶段。

当前主线完成度可以这样理解：

```text
架构骨架、用户流程、Admin 控制面、LLM 表达、训练闭环、回滚证据：基本完成
真实命例规模、真实 LLM 报告质量、训练后效果归因、上线前回归：仍需持续跑数
```

所以 V40 不应该再追逐更多分散功能，而应该进入主线收口：

```text
真实命例 -> 原生 runtime -> Decision -> LLM 表达 -> Probe / 对话 -> 反馈训练 -> 直接生效 -> 回滚补救 -> owner 验收
```

## 已完成的产品主线

| 主线 | 状态 | 说明 |
| --- | --- | --- |
| V30/V40 隔离 | 完成 | 独立目录、独立服务、独立端口、独立 runtime 边界 |
| 用户侧流程 | 完成 | 登录/注册、档案、报告优先、追问后置、历史侧栏、一问一答 |
| admin 特例 | 完成 | `admin` 作为唯一内置账号，在主系统中只是特殊命理师 |
| V30 admin 档案同步 | 完成 | 本地无仓储时可从 V30 product store bootstrap 到 V40 admin 账号 |
| 八字主引擎 | 完成骨架 | 原生 runtime / signal / decision / report 已贯通，命理纵深继续用真实案例推进 |
| 紫微 sidecar | 完成 V1 | 作为 Domain Lens / sidecar，不与八字平权，不直接下 verdict |
| LLM 表达 | 完成原则和运行时 | 没有 LLM 就失败，不走 fallback；LLM 组织语言，不做最终命理裁决 |
| 训练闭环 | 完成骨架 | 训练后直接成为 active policy，保留 previous registry 和 impact diff 用于补救 |
| Probe / 对话 | 完成 V1 | 报告后进入持续一问一答，回答可转训练标签 |
| Admin 控制面 | 完成拆分 | 独立前台服务和端口，主系统不再混入 admin UI |

## 仍未真正完成的 1%

这 1% 不是小修小补，而是真实系统能否成立的核心质量闭环。

| 缺口 | 为什么重要 | 下一步 |
| --- | --- | --- |
| 真实命例不足 | 没有真实命例，训练和验证都是空转 | 建立 100-200 个高质量案例，先覆盖事业、财运、关系、健康、时运、用神、隐藏线索 |
| LLM 表达质量未充分验收 | LLM 是用户可读表达入口，不能变成工程语言 | 对 selected real cases 跑 live LLM report/conversation acceptance |
| 训练后直生效证据不足 | 系统核心特点是高迭代，必须能看到效果和补救路径 | 每次训练输出 before/after diff、active policy、previous registry 和 rollback pointer |
| V30 shadow compare 数据不足 | V40 要替代 V30，不能只靠主观感觉 | 对 admin 档案和真实命例跑 V30/V40 对照，不追求字面一致，追求 verdict/advice 不退化 |
| 本地开发仓储仍可缺省 | memory bootstrap 适合开发，不适合长期运行证据 | 配好 V40 Postgres dev/prod 仓储，把账号、档案、报告、对话、训练、验收全部落库 |
| owner 真实验收未完成 | 命理质量最后必须由 owner 判断 | 用 Phase 73 pack 输出 owner review 包，然后逐案签核 |

## Phase 74 主线任务

Project status keeps these three owner-facing tasks as the active next-mainline anchors:

```text
QA-19: live LLM report/conversation acceptance on selected real cases
OPS-20: rollback rehearsal and beta traffic smoke
USER-21: owner approval for beta cutover window
DATA-22: V40 persistent runtime evidence
DEPTH-23: mingli depth regression
```

### QA-19: 真实 LLM 报告与对话验收

目标：

```text
用 selected real cases 跑完整链路：
档案 -> 报告 -> Probe -> 一问一答 -> 用户反馈 -> 训练标签
```

验收标准：

- LLM 必须真的被调用；
- LLM 失败时直接暴露模型不可用，不生成备用报告；
- 用户看到的是命理语言，不是 policy、runtime、debug、candidate 等工程语言；
- 报告只展示核心判断、建议、风险和下一问；
- 对话进入后，主页面聚焦问题链，报告归入历史侧栏。

### OPS-20: 回滚演练与 beta smoke

目标：

```text
验证训练后直接生效，同时证明可以补救。
```

验收标准：

- BatchTrainerV1 产出 active policy；
- Admin 能看到本次训练改变了哪些权重、阈值、排序或 prompt policy；
- previous registry 可定位；
- rollback / corrective training 有清晰补救路径；
- beta smoke 不写 V30 state。

### USER-21: owner 真实命例验收

目标：

```text
把真实命例验收从系统指标变成 owner 可以逐案判断的产品包。
```

验收标准：

- 每个 case 有命盘事实、核心 verdict、advice、LLM 文案、probe 价值、训练归因；
- blocked / review / passed 原因清楚；
- 过度断言必须降权或阻断；
- owner 可以判断“这个结果有没有命理价值”。

### DATA-22: V40 持久化运行证据

目标：

```text
把当前 memory/bootstrap 形态推进到可持续运行。
```

验收标准：

- user account / profile / reading / conversation / review / training / acceptance evidence 都进入 V40 仓储；
- 本地开发与生产部署各有清晰连接方式；
- 不和 V30 共表、共 Redis 前缀或共 runtime 目录；
- admin 的 V30 档案迁移可以重复跑、可审计、不会污染 V30。

### DEPTH-23: 命理纵深回归

目标：

```text
继续把 V30 命理资产萃取成 V40 原生 RuntimeSignal / Domain Adapter / Probe / Evaluation。
```

优先级：

1. 用神 / 忌神 / 喜神候选与反证；
2. 十神到事业、财运、关系、健康、亲情的领域映射；
3. 做功路径和冲突分支；
4. Hidden Factor Probe；
5. 紫微 sidecar 与八字主判断的一致/冲突提示。

## 下一轮执行顺序

```text
P74-1: 固化 Phase 74 状态、文档和测试
P74-2: 运行 admin 账号真实命盘 smoke，确认 LLM/report/conversation 可用
P74-3: 建立最小真实命例验收批次
P74-4: 把训练后 direct activation 的 diff/rollback 放入 Admin 可读面
P74-5: 配置并验证 V40 持久化仓储
P74-6: 开始命理纵深回归，不再新增散乱 UI
```

## 不做的事

- 不回到 V30 旧的 13 步页面。
- 不把智能对话塞回测算步骤中。
- 不把 LLM 当最终命理裁决者。
- 不为缺少 LLM 做 fallback。
- 不把 admin 重新塞回主系统。
- 不让训练变成“审批后才生效”的工程系统。

## 当前完成度表达

V40 可以对外描述为：

```text
V40 architecture and user runtime: 99%
V40 product-quality acceptance: entering owner review and real-case evidence phase
V40 stable cutover: pending real-case acceptance, persistence evidence and beta smoke
```

## Boundary

Phase 74 是主线计划和验收锚点。它不会：

- 切换线上流量；
- 写 V30 state；
- 改命盘事实；
- 自动批准 beta；
- 把 owner 真实命例判断替换成系统分数。
