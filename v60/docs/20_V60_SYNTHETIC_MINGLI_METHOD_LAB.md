# V60 合成命局方法 Lab

状态：`IMPLEMENTED / DEV_EVIDENCE_ONLY / PRODUCT_PUBLICATION_BLOCKED`

日期：2026-08-03

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

Gold 不进入 Agent Packet。浏览器不能创建实验、提交命盘／模型／Prompt／Gold 或直接
调用模型；它现在只允许创建绑定 Suite Definition Hash、当前候选与执行指纹的服务端
任务，并读取持久化进度与封存结果。

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

它不允许推出身强、可用根、用神、关系作用成立、有效做功或吉凶。若存在候选但最低门
返回 `NOT_DETERMINED`，它必须交给整盘继续裁决：明确整盘依据可形成 `PRESENT`，依据
不闭合时保持 `UNRESOLVED`，只有明确失效证据才能写 `ABSENT`。最低门本身绝不能把它
无证据抹成 `ABSENT`，也不能把实验的预期答案硬编码进全局裁决。
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

历史运行不覆盖、不回写；四个运行都能由当前 Snapshot 服务重放：

| 运行 | Profile / Prompt | 保持项 | 响应项 | 原断凭证 | 结果 |
| --- | --- | ---: | ---: | --- | --- |
| `v60-mingli-synthetic-run-4470e707b662c6dd1b30` | `.017 / .016` | 6/6 | 1/3 | 历史未封存 | `PRODUCT_SAFE_MODEL_FAIL` |
| `v60-mingli-synthetic-run-9895e2ae3f16dab4d8b7` | `.018 / .017` | 6/6 | 3/3 | 历史未封存 | `PRODUCT_SAFE_MODEL_FAIL` |
| `v60-mingli-synthetic-run-a7600d249c620dd5b3b6` | `.019 / .018` | 6/6 | 3/3 | 历史未封存 | `PRODUCT_SAFE_MODEL_FAIL` |
| `v60-mingli-synthetic-run-b11507e53a8bd05faf9b` | `.021 / .018` | 6/6 | 3/3 | A／B 字段级 | `PRODUCT_SAFE_MODEL_FAIL` |

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

### 最新一轮真正发现的模型错误

以前只保存归一化后的 Reading 和泛化修正码，能知道“模型未通过”，却不知道模型究竟
错在哪个字段。最新运行新增 append-only Normalization Receipt，绑定 Packet、Profile、
Provider、Prompt、原始结构化回答 Hash、归一化结果 Hash 与逐阶段字段差异。它只保存
`think=false` 的结构化回答，不请求、不保存隐藏思维链；普通 Reading API 不返回该私有
凭证，只有有审阅权限的合成 Lab 得到经过裁剪的关键差异。

这次终于看见了可训练的问题：

```text
A
模型把 E003 填入根坐标，但该命盘没有准入的同类根；系统移除。
模型没有提供 typed regime_decision；系统补为 UNRESOLVED / ABSENT。

B
模型在正文里看见“寅中甲”，却把它放进 peer support，root_status 仍写 NONE；
系统移除错误 peer 坐标，并把最低阻从范围内的有效根修正为 PRESENT。
模型同样没有提供 typed regime_decision；系统补为 ORDINARY_WEAK / PRESENT。
```

因此这一轮不是继续“拟合 Owner 一盘”，而是第一次得到能直接反馈给 Prompt、规则和
后续模型的错误类型：事实归槽错误、根状态与文字自相矛盾、typed 判型对象缺失。

## 第二组合成实验：同元素候选不等于日主同字门

实验：`v60-mingli-synthetic-experiment-a44f56c301a35d48ff0f`

```text
A：1989-06-03 06:00 Asia/Shanghai
   己巳 / 己巳 / 甲午 / 丁卯

B：1989-06-03 04:00 Asia/Shanghai
   己巳 / 己巳 / 甲午 / 丙寅
```

原设计的 `05:00 / 03:00` 都落在时辰边界，而且 1989-06-03 上海处于历史夏令时区间。
正式 Case 改为 `06:00 / 04:00`：V60 当前历法仍得到相同卯／寅时柱；即使以后明确采用
减一小时的 DST 处理，两者也仍留在各自时辰内。这个调整是历法稳健化，不是为了改变 Gold。

两盘都只有一个木根候选，且都位于第一藏干：

```text
A：hour支藏乙
   SAME_ELEMENT_DIFFERENT_STEM
   minimum_anti_follow_gate = NOT_DETERMINED

B：hour支藏甲
   EXACT_DAY_MASTER
   minimum_anti_follow_gate = PRESENT
```

这组只验证最低阻从门是否区分“同元素异字”与“日主同字”。A 的 `NOT_DETERMINED`
不是“无根”：它必须回到月令、藏干位置、生扶泄耗和组合竞争中作整盘工作裁决；Agent
若有明确整盘依据可以写 `PRESENT`，依据不闭合则写 `UNRESOLVED`，只有明确失效证据
才能写 `ABSENT`。B 的 `PRESENT` 也只排除直接从势，不证明身强、可用根、用神或吉凶。

完整时柱仍同时改变丁伤官／丙食神与卯中乙／寅中甲丙戊。两盘当前均无准入的原局
六冲／六合竞争，但未来关系库可能讨论卯午破、寅巳刑害或寅午半合，所以不得宣称
“没有任何关系”。出生时刻还会让 canonical 起运日期相差十天；Timing 被完整保存，
但不参加本组评分。

### 当前干净封存运行

```text
run_ref: v60-mingli-synthetic-run-f90c01fefacdc663a5ea
profile / prompt: .022 / .019
provider profile: v60.model-serving.gemma4-mingli-agent.003
evaluator / Gold: .003 / .003
holds: 4 / 4
expected responses: 3 / 3
outcome: PRODUCT_SAFE_MODEL_FAIL
```

当前产品结果为：

```text
A：effective_root = UNRESOLVED
   regime = UNRESOLVED

B：effective_root = PRESENT [hour支藏甲]
   regime = ORDINARY_WEAK
```

真实 Gemma4 原断暴露出两类稳定错误：

- A 把 `hour支藏乙` 填进印星资源，称为“余气”，并漏掉 typed `regime_decision`；
- B 正确识别 `hour支藏甲` 与 `ORDINARY_WEAK`，却同时把同一坐标写进印星资源，
  又虚构 `HIDDEN_RESOURCE` 竞争与未决的有根明透支持。

服务端修正后，A 没被写成无根，B 的最低同字门成立，三条预期响应全部通过；但 A／B
仍都有 `DAY_MASTER_REGIME`，所以本地模型没有独立通过。系统现在会这条窄判断，Gemma
尚未稳定学会事实归槽与 typed 判型；这两件事必须分开陈述。

此前的 `v60-mingli-synthetic-run-ec587bce4fe1e0e09856` 保持 append-only，但只作为
`SUPERSEDED` DEV 预检记录：它复用了旧 Profile Ref 的不同 Hash，并把 A 的最终
`UNRESOLVED` 错当成 Gold 必答。当前目录会明确标成“旧口径”，不得参与方法或模型资格。

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
- 浏览器只有一个受控任务 POST；请求体只含 Suite、Definition Hash、Execution
  Fingerprint 与 Idempotency Key。命盘、模型、Prompt、Gold 和运行身份仍由服务端锁定；
- 首屏明确分开“实验有效性／模型独立能力／产品结果”三条轨道；
- 两个实验及各自封存历史都可发现；目录明确区分当前／旧审阅口径；
- 跨实验或 Run 的 URL 先关闭旧 Snapshot，绝不在新标题下短暂显示旧命盘；
- 返回任一 Snapshot 前同时验证 A／B 两侧 Case、Reading、Stage 与实验成员绑定；
- 最新运行可展开“模型原断 → 系统校正”，旧运行诚实显示原断未封存；
- 合成 Lab 只允许 `admin / local_qa_owner` 审阅角色读取，普通会员不能读取 DEV Gold；
- Desktop Chrome 1440×900 与 1280×800 均无舞台／Inspector 重叠或横向溢出。

原有 Chrome 证据在 `.artifacts/mingli-synthetic-lab/`，三轨与字段差异证据在
`.artifacts/mingli-synthetic-model-trace/`，第二组证据在
`.artifacts/mingli-synthetic-root-identity/`。macOS 125% 缩放下，物理
1440×900／1280×800 分别对应 CSS 1152×720／1024×640；证据 JSON 明确记录两种尺寸。
第二组最终运行另在 Desktop Chrome CSS 1512×861、DPR 2 下验证 A／B、刷新、前进后退、
两实验历史、未知实验不回退、无横向溢出与舞台／Inspector 不重叠；同目录
`browser-audit.json` 记录断言。

## 当前能力与下一组矩阵

本轮完成的是“系统能用候选绑定的批次脚本顺序运行多组合法成对命盘、聚合专业错误、
用同一把评尺复跑并显示紧邻训练变化”，不是完整断命资格。第一／第二／第三藏干位阶
矩阵已经完成三轮 `.006` DEV 复跑；当前最大问题不再是位阶事实缺失或正文直接把第二／
第三藏干说成无力，而是模型能否稳定选择整盘主路径，并让 typed 派生投影与自己的有效根
裁决一致。

当前可直接比较的紧邻两轮为：

```text
previous  v60-mingli-synthetic-suite-run-7107e2e6ac01162f6064
current   v60-mingli-synthetic-suite-run-63da38288080c7fa5c3a
尺子      Evaluator .006 / DEV Gold .004 / 同一 Suite Definition

模型独立课题          0/2 -> 0/2
需校正课题            2   -> 2
DAY_MASTER_REGIME      4   -> 2
HIDDEN_RANK_PROSE      1   -> 0
DAY_MASTER_CAPACITY_H1 1   -> 0
WORK_PATH              2   -> 2
```

最早批次 `a72328...` 使用 Evaluator `.005`，它漏过“微弱比肩”等隐式位阶偷换，因此只
作为历史证据，不能拿来宣称当前候选提升。Lab 只有在 Suite、每个实验 Definition、
Evaluator、Gold Version 与 Gold Hash 全部相同时才显示箭头；评尺不同只能并列查看。
当前候选身份同时显示 Model Digest、Agent Profile、Provider Profile、Prompt 与各自短
Hash，避免 Ref 未变但实际内容已变。

最新两次 `DAY_MASTER_REGIME` 都来自同一张 08:00 桥接盘。模型的有效根状态已经正确且
稳定为 `UNRESOLVED`，服务端只把不一致的 `ORDINARY_WEAK` classification 收回
`UNRESOLVED`。两个 `WORK_PATH` 分别暴露原局主线混入时序证据与 raw/final PRIMARY
翻转。它们都继续令模型独立失败，不能因产品结果经修正后安全就省略。

下一批按方法矩阵推进，不继续人工围绕某一真人命盘扩写：

1. 停止对当前四盘做第四次提示词追逐；扩大陌生合法合成盘，验证主路径选择与派生
   classification 的跨盘一致性；
2. 有六冲／六合成员关系但作用未决的保留未决组；
3. 具备明确失效证据后才允许 `DOES_NOT_BLOCK / ABSENT` 的反例组；
4. 多个根候选的合并与竞争组；
5. 只改变大运／流年的原局保持组，禁止岁运回写原局；
6. 根气判型稳定后，再进入食伤生财／制杀、财星通关、调候与人生应事方法矩阵。

后续实验拆为 `DEV / QUALIFICATION / HOLDOUT`。DEV 用于发现与修正方法；只有冻结
方法后运行的陌生 QUALIFICATION／HOLDOUT 结果，才有资格参与模型能力声明。

## 第五组合成实验：跨日主泛化与产品内训练任务

为避免继续围绕乙木、卯辰未旧盘调 Prompt，本轮增加一组从未进入既有目录的丙火命盘：

```text
A：2000-03-19 10:00 Asia/Shanghai
   庚辰 / 己卯 / 丙子 / 癸巳
   hour支藏丙 = PRIMARY_QI / minimum gate PRESENT

B：2000-03-19 04:00 Asia/Shanghai
   庚辰 / 己卯 / 丙子 / 庚寅
   hour支藏丙 = SECONDARY_QI / minimum gate NOT_DETERMINED
```

前三柱没有其他丙火根候选或明干火同类；当前准入关系库也没有给两个时支返回六冲／
六合竞争。完整时柱仍同时改变时干十神与所有藏干，所以 Gold 只检查已经准入的同字、
藏干位阶和最低阻从门，不把整盘强弱、用神、机制、应事或吉凶写成固定答案。

产品内的真实运行链已经闭合：

```text
V131 合成验证目录
→ 浏览器读取服务端锁定的候选与可运行 Suite
→ POST Hash／Fingerprint／Idempotency 绑定请求
→ 服务端顺序运行 A／B，持久化 START／SEALED／SEALING／终态
→ 刷新或重进继续读取同一个 Request
→ append-only Experiment Run + Suite Run
→ 服务端派生 DEV Review Disposition 与错误簇
→ 回到同一个四柱 Scene Player 复盘 A／B
```

真实运行身份：

```text
request     v60-mingli-synthetic-suite-run-request-684b2d6203b0eaa4ff71
suite run   v60-mingli-synthetic-suite-run-c84fd3d22f1406423361
experiment  v60-mingli-synthetic-run-41f70f6dfdeb3a83ee0d
candidate   Gemma4 / Profile .026 / Prompt .023
result      PRODUCT_SAFE_MODEL_FAIL
disposition CANDIDATE_REVISION_REQUIRED
checks      3/3 holds + 4/4 method responses
clusters    DAY_MASTER_REGIME ×1 / WORK_PATH ×2
```

两次真实模型调用分别耗时约 `118.1s / 109.5s`，总 Token 为 `17,158 / 16,424`。A 能识别
第一藏干同字根为 `PRESENT`，却把整盘直接写成 `ORDINARY_WEAK`，系统只能退回
`UNRESOLVED`；A／B 的主路径还各有一次服务端归槽。因此这次验证回答了一个比“页面能
不能运行”更重要的问题：当前模型已能读取局部位阶事实，但尚不能稳定地把局部事实、
整盘判型和主路径排序连成同一套独立裁决。

任务表是可恢复的研发运行状态，不伪装成 append-only 专业证据；最终 Experiment／Suite
Run 仍是 append-only。当前恢复合同覆盖浏览器刷新与重进，不宣称进程崩溃后自动续跑。
短暂读取失败后轮询会继续；任务完成后，界面先展示与 Suite／执行指纹精确绑定的本轮
结果，再允许进入下一组验证。待复核入口只选择真正标记 `review_required` 的封存课题；
相同候选与同一执行指纹不会重复冒充新训练。

## V131 Lab 体验接线

V131 commit `ea2db274ba55b8f9d323881c096d3a3a1ceba66c` 的水庭总览和合成验证目录
已经进入真实 V60。进入 Lab 先看到三个研究入口，而不是个人命盘或常驻 WebGL：

```text
六柱关系观察     -> canonical 四／六柱 Scene Player
八字合成验证     -> 5 个真实课题、17 次封存运行、真实 Suite／训练任务状态
阿布说           -> 同一个六柱 Scene Player 与服务端锁定声画链
```

总览为只读 GET；目录只增加一个服务端绑定任务入口，仍为零 Canvas。只有进入六柱、
阿布说或具体封存现场后才懒加载唯一 Scene Player。最新跨日主 DEV Suite 如实显示
`1/1` 封存、`1` 项待复核和 `2` 个错误簇；上一组位阶 Suite 的 `2/2` 历史继续保留；
`QUALIFICATION / HOLDOUT` 继续显示 `Owner Gate 后开放`。当前页面是“已揭晓封存
复盘”，不是盲审；原型的 `localStorage` 裁决、假 Run 身份和写死统计均未进入系统。

六柱入口只说明当前已准入的六冲／六合成员事实。关系作用、来源可用性、旺衰、有效
做功或吉凶仍必须由整盘方法和专业裁决支持，不能从原型演示文案反推。

## 当前版本

```text
Foundation                 v60.foundation.033
Mingli Engine              v60.mingli-cognitive-engine.044
Runtime Architecture       v60.runtime-architecture.073
Agent Runtime              v60.mingli-agent-runtime.028
Agent Profile              v60.mingli-agent.whole-chart-cognition.026
Agent Prompt               v60.prompt.mingli-agent-whole-chart.023
Provider Profile           v60.model-serving.gemma4-mingli-agent.003
Agent Prompt View          v60.mingli-agent-prompt-view.014
Agent Reading              v60.mingli-agent-reading.005
Normalization Receipt      v60.mingli-agent-normalization-receipt.001
Agent Adjudication         v60.mingli-agent-adjudication.009
Method Distillation        v60.mingli-agent-method-distillation.004
Effective-root Method      v60.mingli-effective-root-method.001
Regime Decision            v60.mingli-agent-regime-decision.001
Stage Projection           v60.mingli-stage-projection.004
Synthetic Catalog          v60.mingli-synthetic-experiment-catalog.004
Synthetic Evaluator        v60.mingli-synthetic-experiment-evaluator.006
Synthetic Run              v60.mingli-synthetic-experiment-run.001
Synthetic Snapshot         v60.mingli-synthetic-experiment-snapshot.004
Suite Catalog              v60.mingli-synthetic-suite-catalog.002
Suite Definition           v60.mingli-synthetic-suite-definition.001
Suite Runner               v60.mingli-synthetic-suite-runner.002
Suite Run                  v60.mingli-synthetic-suite-run.002
Training Request           v60.mingli-synthetic-suite-run-request.001
Training Status            v60.mingli-synthetic-training-status.001
Unit Mingli                v60.unit-mingli.034
Unit Lab                   v60.unit-lab.030
Migration                  0041_mingli_training_requests
```

Migration 0041 增加候选绑定、幂等且可恢复的训练任务表；0040 继续绑定非空 typed
regime、Prompt View `.014`、Method Distillation `.004` 与 Evaluator `.006`。两次迁移
都不改写任何 sealed run。最新 Suite `c84fd3...` 绑定本地 Gemma4、
Profile/Prompt `.026/.023` 与 Reading `.005`；历史 Reading、Evaluator、Gold 与 Suite
仍按各自明确版本语义重放，不能被“当前版本”常量静默改义。

## 验证

```text
Backend tests              437 PASS
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

真实 Desktop Chrome 已验证 V131 总庭、五课题目录、服务端任务启动、运行中刷新恢复、
真实封存、A／B 切换与精确深链接刷新；页面无控制台错误。既有完整六柱、阿布说
PREPARING、浏览器前进／后退与两种桌面宽度证据继续成立。总览／目录无 Canvas，深场
始终只有一个 Scene Player。
