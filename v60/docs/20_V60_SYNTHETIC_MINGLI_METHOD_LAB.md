# V60 合成命局方法 Lab

状态：`IMPLEMENTED / DEV_EVIDENCE_ONLY / PRODUCT_PUBLICATION_BLOCKED`

日期：2026-08-02

## 目标

合成命盘从本轮开始是命理 Agent 的主要研发与资格验证场，而不是附属演示。
Owner 真实命盘只保留为回归样本，不能继续承担方法发现、阈值拟合和能力宣称。

正式闭环为：

```text
合法出生输入 A / B
→ 独立历法解析与真实四柱
→ 各自 canonical Case / Chart / Reading / Packet
→ 本地产品模型分别盲断
→ 服务端类型化裁决
→ flip / hold / drift 对照
→ append-only 封存运行
→ Lab 只读复盘
→ 方法、Prompt、Schema 与反例继续升级
```

Gold 不进入 Agent Packet。浏览器不能创建实验、提交 Prompt 或调用模型，只读取
离线封存的结果。

## 第一组合成实验

实验：`v60-mingli-synthetic-experiment-999b1a4568cb0bf3c399`

```text
A：2006-10-12 09:00 Asia/Shanghai
   丙戌 / 戊戌 / 甲戌 / 己巳

B：2006-10-12 03:00 Asia/Shanghai
   丙戌 / 戊戌 / 甲戌 / 丙寅
```

这是两个都能由历法引擎独立解析的合法出生时刻。前三柱、日主、月令、明干同类、
印星生扶、候选机制集合和固定分析日的岁运坐标必须保持；时柱必须完整改变。

它不是严格的“只加一个根”因果实验。完整时柱变化同时包含：

- 时干由己正财变为丙食神；
- 时支藏干由巳中丙戊庚变为寅中甲丙戊；
- 新增甲比肩根候选，同时移除庚七杀成员。

因此本轮只能验证系统是否对这组完整时柱证据作出应有响应，不能把全部变化单独
归因于根气。

## 第一条窄专业方法：最低阻从有效根

旧系统已经能找到 `hour支藏甲`，但只把它列为“根候选”，没有回答它是否足以改变
身弱／从势判断。本轮加入：

```text
v60.mingli-effective-root-method.001
```

最低阻从规则为：

```text
与日主同字
+ 位于该支第一藏干
+ 该支没有已准入的原局六冲／六合成员关系竞争
→ 在“排除直接从势”这一窄范围内判为 PRESENT
```

这条规则只允许推出：

```text
存在最低有效根
→ 不能直接判从
→ 转入普通身弱或其他整盘竞争判断
```

它不允许推出身强、可用根、用神、关系作用成立、有效做功或吉凶。若存在候选但未
满足最低规则，且没有明确的失效证据，状态必须保持 `UNRESOLVED`，不得被模型无证据
抹成 `ABSENT`。
若最低阻从根已经成立，但 Agent 对全盘强弱的原始判断仍是 `UNCERTAIN`，系统只能保留
`UNRESOLVED / UNCERTAIN`；根的存在本身不能把强弱未定静默改写为身弱。

完整的从势准入顺序是：

```text
任一候选已证明阻从
→ 不得判从

没有候选阻从，但仍有任一候选未决
→ 不得判从，继续未决

全部候选均有明确“不阻从”证据
+ 异类主导链 CLOSED
+ 无浮比、藏印和组合竞争
→ 才允许进入 FOLLOW_TREND 工作判断
```

藏干位阶同时进入 Prompt 与服务端事实修复。第一藏干必须表达为主气／第一藏干，
不得误写成余气。

## 当前封存运行

历史运行不覆盖、不回写；三个运行都能由当前 Snapshot 服务重放：

| 运行 | Profile / Prompt | 保持项 | 响应项 | 结果 |
| --- | --- | ---: | ---: | --- |
| `v60-mingli-synthetic-run-4470e707b662c6dd1b30` | `.017 / .016` | 6/6 | 1/3 | `PRODUCT_SAFE_MODEL_FAIL` |
| `v60-mingli-synthetic-run-9895e2ae3f16dab4d8b7` | `.018 / .017` | 6/6 | 3/3 | `PRODUCT_SAFE_MODEL_FAIL` |
| `v60-mingli-synthetic-run-a7600d249c620dd5b3b6` | `.019 / .018` | 6/6 | 3/3 | `PRODUCT_SAFE_MODEL_FAIL` |

当前运行中：

```text
A：effective_root = ABSENT
   regime = UNRESOLVED
   day_master_state = WEAK

B：effective_root = PRESENT [hour支藏甲]
   regime = ORDINARY_WEAK
   day_master_state = WEAK
```

B 的当前说明为：

> 日主甲生于戌月；时支寅的第一藏干甲与日主同字，在最低阻从范围内构成有效根。
> 因此退出直接从势，按普通身弱继续比较全盘泄耗、生扶、财与官杀压力。

三个预期响应和六个保持检查全部通过，仍不能写成模型资格 `PASS`。A、B 都带有
`DAY_MASTER_REGIME` 服务端归一化记录，说明 Gemma4 尚未独立给出完全符合合同的原始
判断；系统只是把产品结果收敛在已准入的窄规则内。因此真实结论是：

```text
产品结果安全且对照响应成立
≠ 本地模型已经学会该方法
≠ 高级命理师资格通过
```

## 可见 Lab 闭环

入口：

```text
命理 Lab
→ 合成验证
→ 选择 A / B
→ 同一个 Mingli Scene Player 切换 Projection
→ 查看保持项、响应项、方法结论与运行身份
```

已实现：

- A／B 使用同一个四柱 3D 舞台实例，切换不会创建第二个 Canvas；
- URL 固定 experiment、run 和 variant，刷新可恢复同一封存结果；
- 浏览器后退恢复前一变体，再返回普通 Lab 时清除全部合成参数；
- `research:*` Case 不进入普通档案选择器；
- 切换失败时继续显示已提交的旧变体，并明确说明目标变体读取失败；
- 失效的 pinned run 可以改读 catalog 中最新封存运行；
- 浏览器只有两个 GET 读取入口，没有模型 POST；
- Desktop Chrome 1440×900 与 1280×800 均无舞台／Inspector 重叠或横向溢出。

真实 Chrome 证据在 `.artifacts/mingli-synthetic-lab/`。macOS 125% 缩放下，物理
1440×900／1280×800 分别对应 CSS 1152×720／1024×640；证据 JSON 明确记录两种尺寸。

## 当前能力与下一组矩阵

本轮完成的是“系统第一次能用合法成对命盘发现方法缺口、写入窄规则、重跑并封存
差异”，不是完整断命资格。当前最大问题已经从“只测 Owner 一盘”收窄为：样本仍只有
一组完整时柱对照，且模型原始结果仍需服务端修正。

下一批按方法矩阵推进，不继续人工围绕某一真人命盘扩写：

1. 第一藏干同字、第二藏干同字、第三藏干同字三组位阶对照；
2. 同元素不同字与日主同字对照；
3. 有六冲／六合成员关系但作用未决的保留未决组；
4. 具备明确失效证据后才允许 `DOES_NOT_BLOCK` 的反例组；
5. 多个根候选的合并与竞争组；
6. 只改变大运／流年的原局保持组，禁止岁运回写原局；
7. 根气判型稳定后，再进入食伤生财／制杀、财星通关、调候与人生应事方法矩阵。

后续实验拆为 `DEV / QUALIFICATION / HOLDOUT`。DEV 用于发现与修正方法；只有冻结
方法后运行的陌生 QUALIFICATION／HOLDOUT 结果，才有资格参与模型能力声明。

## 当前版本

```text
Foundation                 v60.foundation.027
Mingli Engine              v60.mingli-cognitive-engine.038
Runtime Architecture       v60.runtime-architecture.065
Agent Runtime              v60.mingli-agent-runtime.021
Agent Profile              v60.mingli-agent.whole-chart-cognition.020
Agent Prompt               v60.prompt.mingli-agent-whole-chart.018
Agent Prompt View          v60.mingli-agent-prompt-view.011
Agent Adjudication         v60.mingli-agent-adjudication.009
Method Distillation        v60.mingli-agent-method-distillation.003
Effective-root Method      v60.mingli-effective-root-method.001
Regime Decision            v60.mingli-agent-regime-decision.001
Stage Projection           v60.mingli-stage-projection.004
Synthetic Catalog          v60.mingli-synthetic-experiment-catalog.001
Synthetic Evaluator        v60.mingli-synthetic-experiment-evaluator.001
Synthetic Run              v60.mingli-synthetic-experiment-run.001
Synthetic Snapshot         v60.mingli-synthetic-experiment-snapshot.001
Migration                  0035_mingli_uncertain_root_guard
```

Migration 0035 did not call the model or rewrite a sealed run. The current
`a7600d...` evidence therefore remains bound to Profile/Prompt `.019/.018`;
future generation uses Profile `.020`, so it cannot silently reuse the older
normalization behavior.

## 验证

```text
Backend tests              396 PASS
Ruff                       PASS
TypeScript / Vite build    PASS
Runtime Architecture       PASS
Source maintainability     PASS
Shared Scene contract      PASS
Synthetic Lab contract     PASS
Real Desktop Chrome        PASS
```

Vite 仍报告两个大于 500 kB 的既有异步图形 chunk；这是已记录性能债，不改变本轮方法
Lab 的功能结论。
