# V40-RC2 Module Status And Migration Map

Date: 2026-07-01

## 核心结论

V40 当前不是缺整体框架，而是缺命理纵深迁移。

```text
V40 architecture: mostly ready
V40 mingli depth: still needs RC2 migration and acceptance
Direct V30 runtime reuse: 0
Reusable V30 asset groups: 10+
New RC2 module groups: 5
```

V30 可以复用的是命理资产、算法口径和测试样本，不是 runtime、UI、Admin 或旧流程。

## Read Model

新增只读接口：

```text
GET /api/v40/project/module-migration-status
```

它回答三件事：

1. 当前 V40 哪些模块已经是原生骨架；
2. V30 哪些模块可以通过 DTO / adapter 萃取进来；
3. RC2 还必须新增哪些命理纵深模块。

该接口不读取 V30 runtime，不写 V30，不写 V40 production。

## Module Map

| Module | Current State | V30 Policy | RC2 Action |
| --- | --- | --- | --- |
| Contracts / protocols | V40 native ready | 不迁移 V30 | 稳定扩展新合约 |
| Runtime repository | V40 native ready | 不共表、不共 Redis | 继续保持 V40 隔离 |
| API / user surface | V40 native ready | 只参考体验 | 接入命理纵深输出 |
| Admin control plane | V40 native ready | 不迁移主系统 admin | 保持独立控制面 |
| Training spine | V40 native ready, needs cases | 参考 V30 training | 接真实案例和 diff |
| Evaluation / release gate | V40 native ready, needs window | 参考 V30 evaluator | 建 Acceptance Window |
| Native Bazi runtime | V40 minimal, needs depth | 重构 V30 算法 | 升级 Fact Engine Pro |
| Bazi Fact Engine Pro | New required | 参考 V30 core/calendar | 新建事实引擎 |
| Signal Registry | V40 ready, needs assets | V30 rules/evidence -> RuntimeSignal | 建资产迁移 adapter |
| Decision Engine | V40 ready, needs domain depth | 不复用 V30 verdict | 接 domain hints |
| Domain adapters | New required | 萃取 V30 path/rule/knowledge | 新建领域 adapter |
| LLM expression | V40 ready | 参考表达策略 | 只负责语言，不裁决 |
| Conversation / probe | V40 ready, needs depth | V30 question assets -> ProbeTemplate | 升级为持续 probe chain |
| Hidden Factor Probe | New required | 萃取 V30 hidden_factor | 新建 hidden attribute update |
| Knowledge cards | Migration required | V30 knowledge -> ExplanationBasis | 只解释，不裁决 |
| Portrait signals | Migration required | V30 portrait -> low-weight signal | 不直接强断语 |
| Rule/path assets | Migration required | V30 rules/path -> signal/path/conflict | 不直接 verdict |
| Ziwei sidecar | V40 sidecar ready, needs assets | V30 ziwei -> sidecar lens | 辅助证据，不与八字平权 |
| Asset Migration Gate | New required | 所有 V30 asset 必经 gate | 实现 sidecar/evaluating/enabled |
| Real Case Bank | New required | 参考 V30 case_bank | 收 100-200 个高质量案例 |
| Legacy V30 UI/Admin | No reuse | 不迁移 | 只保留产品经验 |

## Need More Modules?

需要，但不是继续堆命理模块，而是补齐 5 个 RC2 产品级模块：

1. `Bazi Fact Engine Pro`
2. `Asset Migration Gate + V30 Mingli Asset Pipeline`
3. `Domain Verdict Adapters`
4. `Hidden Factor Probe Engine`
5. `Real Case Bank / Acceptance Window`

这五个模块完成后，V40 才能从“架构完成”进入“命理可验收”。

## Reuse Rules

| V30 Source | V40 Reuse Form |
| --- | --- |
| `core`, `pillars`, `time_context`, `luck_flow`, `ten_gods` | 重构为 V40 Fact Engine，配回归测试 |
| `rules`, `diagnosis/rule_matcher`, `feature_engine` | RuntimeSignal / CandidateSeed |
| `path_engine`, `graph` | PathSignal / ConflictSignal |
| `portrait`, `portrait_engine` | Low-weight PortraitSignal |
| `knowledge`, `docs/bazi_knowledge` | KnowledgeCard / ExplanationBasis |
| `questions`, `dialogue_chain` | ProbeTemplate / ConversationSeed |
| `hidden_factor` | HiddenAttribute / Probe strategy |
| `ziwei` | Sidecar Domain Lens |
| `evaluation`, `case_bank` | Acceptance Window seed |
| `frontend`, `admin`, old mixed flows | 不迁移 |

## Acceptance Rule

每个模块必须回答：

```text
我产出什么？
谁消费我？
我影响用户结果的哪一部分？
我是否能被训练和验证？
我是否能通过 before/after diff？
```

不能回答这五个问题的模块，不进入 V40 主线。
