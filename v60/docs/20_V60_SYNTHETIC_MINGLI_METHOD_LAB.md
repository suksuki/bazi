# V60 合成命局方法 Lab

状态：`IMPLEMENTED / DEV_EVIDENCE_ONLY / PRODUCT_PUBLICATION_BLOCKED`

日期：2026-08-03

最后同步：2026-08-15

## 2026-08-15 Qwen3.8 官方调用校准与产品分层路径

从发现部署、服务端核验、官方模板、双 Runtime 重构、本地规则蒸馏到命理师视角评分的
完整过程，统一记录在
[`23_V60_QWEN38_MINGLI_INTEGRATION_AND_PRACTITIONER_REVIEW.md`](23_V60_QWEN38_MINGLI_INTEGRATION_AND_PRACTITIONER_REVIEW.md)。

官方 `Qwen/Qwen3.8-27B` 模型卡确认模型默认进入 thinking；非思考模式推荐
`temperature=0.7`、`top_p=0.8`、`top_k=20`、`min_p=0`、
`presence_penalty=1.5`、`repetition_penalty=1.0`。官方 tokenizer template 在
`enable_thinking=false` 时以空的 `<think>\n\n</think>\n\n` 开始 assistant
generation。当前 Ollama 模型自带模板只有 `{{ .Prompt }}`，因此 Focused Runtime
使用 `raw=true` 明确渲染同一 ChatML non-thinking 模板；这不是通过自然语言假装关闭
thinking。参考：[Qwen3.8-27B model card](https://huggingface.co/Qwen/Qwen3.8-27B)、
[Ollama generate API](https://docs.ollama.com/api/generate)。

产品路径不再复用严格整盘 JSON Agent 的 24K 上下文与 6K 输出预算。Focused Profile
`.005` 固定 `num_ctx=4096`、`num_predict=320`、`seed=42`、`keep_alive=30m`，
每次只问一个主题；总纲是其他四问唯一依赖。每个回答作为
`v60.mingli-focused-pass-record.001` 追加保存，Summary `.008` 可以表达
`NOT_GENERATED / PARTIAL / READY`，页面会立即进入“正在判断”状态并在用户切换层次时
按需继续。五问批量入口只保留为 DEV 教师批处理，不是产品点击路径。

同一合成命盘的真实 Ollama `qwen3.8:27b` Q4_K_M 测量如下：

| 调用 | 输入 token | 输出 token | 墙钟时间 |
| --- | ---: | ---: | ---: |
| 原局总纲 | 826 | 191 | 14.8s |
| 生命意象／性情 | 556 | 102 | 8.0s |
| 事业／财富 | 627 | 160 | 13.0s |
| 关系／家庭 | 649 | 128 | 10.7s |
| 大运／流年 | 668 | 220 | 16.2s |
| 同一专问缓存重放 | — | — | 9ms |

此前五问串行原型约 `109.6s`，严格整盘资格 Agent 约 `190.9s`。本轮优化没有证明
模型已达到高级命理师：总纲仍把月干甲木写成“月令七杀”，并越界谈岁运；关系层从
无印直接推断原生家庭；时间层把已准入的午子六冲成员关系扩大为确定的财星动荡。
这些差异已蒸馏进本地 Normalizer `.003`，形成月令坐标、判型、范围、传记推断、
五行因果、藏干坐标、心理／灾祸和未准入关系效果等 review code。系统保留原文供
DEV 教师审读，不静默改成“正确答案”，也不允许其写入 canonical facts。

按当前有限样本的高级命理师审稿口径，Qwen3.8 相比 Gemma4 约提升一档：文字与取象提升
明显，结构判断有可信但有限的改善；主次决胜、反证与岁运边界仍未跨过独立执业门槛。
这不是资格结论，完整证据和评分边界见上述整合文档。

## 2026-08-15 Qwen3.8 DEV 对照首轮

本日首轮对照时，`qwen3.8:27b` 先以 DEV comparison candidate 接入 V60 命理
Agent Runner，Gemma4 默认 Profile 与历史封存保持不变。完成同尺审读及后续 Owner
授权后，Qwen 才在同日后续阶段成为当前首选；本段记录的是切换之前的实验时点。两者
使用同一 Suite Definition、Evaluator `.008`、DEV Gold `.005` 和结构化盲断合同。

```text
Qwen3.8 Suite: v60-mingli-synthetic-suite-run-150c896e9c1fe901408e
Gemma4  Suite: v60-mingli-synthetic-suite-run-ea54d9e849a422f02ea3
```

| Candidate | Hold | Changed | Outcome | Model independence | Avg reading time |
| --- | ---: | ---: | --- | --- | ---: |
| `qwen3.8:27b` | 6/6 | 41 | `PRODUCT_SAFE_MODEL_FAIL` | `FAIL` | 191.6s |
| `gemma4:latest` | 6/6 | 37 | `PRODUCT_SAFE_MODEL_FAIL` | `FAIL` | 88.3s |

Qwen3.8 在本轮没有出现 Gemma4 的 `DAY_MASTER_REGIME` 或
`WORK_PATH_FORM` 服务端修复，说明它在根气／判型入口和主路径格式上出现了真实
改善；但四个变体仍出现 `HYPOTHESIS_H1/H2` 或 `HYPOTHESIS_DECISION` 修复，且
反证条件与主次翻转仍未达到模型独立通过。第二个实验还保留隐藏位阶表达范围和
可执行反证失败。因此本轮结论是：Qwen3.8 值得作为本地 Owner Review 首选和教师
差异来源，但不能宣称高级命理师资格通过，也不能进入公开发布。

## 2026-08-15 Qwen3.8 首选与低延迟配置（上一阶段）

本地 Runtime 已将 Qwen3.8 设为命理整盘首选；Gemma4 只有在显式选择
`--mingli-candidate gemma4` 时使用，不做静默混用。Qwen Profile 保持 `think=false`
和严格 JSON Schema，采用 `num_ctx=24576`、`num_predict=5200`、`top_k=20`。
当前四次完整 Reading 的最大输入为 `11219` tokens、最大输出为 `4488` tokens，
因此该上下文和输出预算仍保留安全余量，同时避免为未使用的 32K/8K 上限支付缓存和
生成成本。优化后的 Suite `v60-mingli-synthetic-suite-run-19db9c11b6bbf85c90bc`
仍为 `22/19 changed`、`6/6 hold`、`PRODUCT_SAFE_MODEL_FAIL`，平均 Reading
耗时 `190.9s`；相对原始 `191.6s` 基本没有变化。提示词主合同暂不删减，以免速度
优化破坏事实、方法卡和反证门禁。当前主要瓶颈确认是 27B Q4_K_M 的 token 解码，
不是上下文窗口或异常输出上限。

## 2026-08-15 Qwen3.8 `.032` typed counterfactual calibration

为推进“高级命理师断命”训练，方法卡已经从说明性文本推进为可执行的
counterfactual decision row。每个 method card 会编译出
`CHECK_CODE:TRIGGER_AXIS` 目录；Qwen 只负责选择合法的 `trigger_axis` 和
`RECLASSIFY` action，服务端根据当前 ruling 派生稳定的 `row_ref`、目标
状态和反证转移。这避免模型自由改写当前／目标裁决，同时保留模型对实际触发
轴的判断责任。

跨方法卡翻转也绑定了稳定的
`REVERSAL:PRIMARY>ALTERNATIVE:MAINTAIN_PRIMARY>FLIP_TO_ALTERNATIVE`
receipt，并要求输出两个候选路径的完整假设名称。实现已进入
`agent_counterfactuals.py`、Agent Schema/Prompt、输出清洗、完整性评估和
回归测试；历史没有这些字段的 Reading 仍按兼容规则保留为历史证据。

当前本地首选是 `qwen3.8:27b`，Serving Profile 为
`v60.model-serving.qwen38-27b-mingli-agent.002`，Agent Profile 为
`v60.mingli-agent.whole-chart-cognition.033`；保持 `think=false`、
`temperature=0`、`top_p=0.95`、`top_k=20`、`num_ctx=24576`，输出预算提高到
`num_predict=6000`，以容纳新增 typed receipt，避免 5200 导致 JSON 尾部截断。

最新 Suite 为 `v60-mingli-synthetic-suite-run-92d81fd67b5c94bf89f2`：
`runner_errors=0`、两项实验均 sealed；两个实验的 changed/hold 分别为
`27/30 + 3/30 hold`、`26/30 + 3/30 hold`。本轮重要进展是四个成员的
`RAW_DECISION_ROWS_BOUND` 和 `RAW_REVERSAL_ACTIONABLE` 均通过，说明模型已
能按结构合同选择反事实轴并输出具名翻转信号。仍失败的是
`PRODUCT_SAFE_MODEL` 与 model-independence：H1/H2 方法裁决、work-path
范围、隐藏位阶 prose 和部分可执行反证仍需继续校准。因此 Qwen 已用于系统的
私有 Owner Review/DEV Lab 链路，但没有写入 canonical facts，也没有开启公开
断命或“高级命理师”资格。

随后加入的 `0047_mingli_resolution_guard` 没有改写这份 append-only sealed
Suite；只对四份已保存 raw output 做了只读 replay。结果显示原先由“未形成更强竞争”、
“竞争路径弱／不改变主轴”等中文弱化语义引起的 H1/H2 服务端误修复已消失；剩余
`WORK_PATH` 时序越界、个别反证当前裁决标签不一致和隐藏位阶 prose 失败仍然保留，
所以本次是裁决器真实性修复，不是把模型成绩静默改成通过。

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

## 第六组合成实验：整盘判型与主路径泛化

为避免继续围绕 Owner、阿布、多多或旧甲乙丙命盘调参，本轮加入从未进入目录的戊土
对照。两份命盘只改变合法出生时刻，历法引擎锁定为：

```text
A：1994-01-02 18:00 Asia/Shanghai
   癸酉 / 甲子 / 戊子 / 辛酉
   无戊土根、无明干比劫、无印
   effective root = ABSENT
   regime = FOLLOW_TREND / UNRESOLVED

B：1994-01-02 20:00 Asia/Shanghai
   癸酉 / 甲子 / 戊子 / 壬戌
   hour支藏戊 = EXACT_DAY_MASTER / PRIMARY_QI
   minimum anti-follow gate = PRESENT
   同时新增丁正印，但印不得冒充根
   effective root = PRESENT
   regime = ORDINARY_WEAK / UNRESOLVED
```

完整时柱同时改变时干、全部藏干、候选结构及起运边界，所以本组只能检验整盘响应与
决策自洽，不能把变化单独归因于根位。Gold 固定候选集合：

```text
A：output-to-wealth / output-to-pressure / wealth-to-pressure
B：wealth-to-pressure / pressure-resource-self
```

Gold 不指定哪张机制卡必须胜出，也不裁用神、应事、概率或吉凶。Reading `.006` 要求
模型提交唯一 PRIMARY，`work_path.selected_hypothesis_id` 与
`work_path.method_card_ref` 必须绑定它；服务端只有在原 PRIMARY 已明确 `BROKEN` 时才
安全换位，不能再按支持项数量静默改写模型主线。

Evaluator `.007` 直接读取 normalization receipt 中的 raw output，逐个检查：

- H1/H2 是否按固定槽完整执行方法卡；
- 是否只有一个 PRIMARY，且胜负回执与它一致；
- 前两解释与 excluded ledger 是否恰好覆盖全部候选；
- 主路径是否绑定 PRIMARY/方法卡，动作是否合法且无重复；
- 日主状态与 weak-versus-follow regime 是否属于合法组合；
- 每次服务端修复是否留下对应训练回执。

这意味着服务端补齐后的“完整 Reading”不再被算作模型学会。非弱命局新增
`NON_WEAK_OUTSIDE_SCOPE`，只表示退出身弱／从势子审计，不扩大成用神、做功或吉凶。

真实运行身份：

```text
suite run   v60-mingli-synthetic-suite-run-eeb96631646c98137cd9
experiment  v60-mingli-synthetic-run-3d96c4be35affd574214
candidate   Gemma4 / Profile .027 / Prompt .024 / Reading .006
evaluator   .007
Gold        .005
result      PRODUCT_SAFE_MODEL_FAIL
checks      3/3 holds + 16 method responses passed
```

本轮控制变量有效、runner error 为 0，产品经规则校正后安全，但模型没有独立通过：

- A 在根、明干同类与印星均缺席时，仍提交 `WEAK + ORDINARY_WEAK`，服务端退回
  `UNRESOLVED`；
- A/B 都把已经入选前二的卡再次放入 excluded ledger；
- B 为 winner 与 loser 重复提交同一条 reversal signal，主次回执被重建；
- A/B 的四张方法卡都把 `condition_or_falsifier` 写成重复断言，而不是“若／如果／当”
  开头的可翻转条件，因此留下 H1/H2 方法卡修复回执；
- A/B 的原始 PRIMARY、decision winner 与 work-path binding 均一致，路径动作合法且无
  重复。这部分第一次在陌生整盘上独立通过，不应被失败簇掩盖。

因此下一轮不再泛泛要求“写得更像命理师”，而是针对三个可验证缺口回炉：无支持盘的
判型出口、候选 ledger 集合运算、方法卡反证条件语法。只有新版本在另一组陌生盘上重跑
并减少这些 raw failure，才算方法提升。

## 第七组合成实验：候选闭合、反证与跨日主迁移

为避免继续在戊土盘上追逐输出，本轮追加从未进入目录的庚金合法时柱对照：

```text
A：1995-06-18 12:00 Asia/Shanghai
   乙亥 / 壬午 / 庚辰 / 壬午
   无庚金根、无明干比劫；三处藏印只能进入竞争，不能冒充根

B：1995-06-18 16:00 Asia/Shanghai
   乙亥 / 壬午 / 庚辰 / 甲申
   hour支藏庚 = EXACT_DAY_MASTER / PRIMARY_QI
   minimum anti-follow gate = PRESENT
```

A 的午午同支成员在 B 消失；时干由壬食神改为甲偏财，完整时支藏干、印与输出载体、
关系成员及起运边界也同时改变。因此 Gold 仍不做“申中庚导致全部变化”的单因果断言。
两盘冻结同一组三张候选：

```text
output-to-wealth
output-to-pressure
wealth-to-pressure
```

Gold 只要求模型选两张不同卡、精确排除剩余一张，并保持胜者未知。Method `.006` 同时
补齐 `wealth-to-pressure` 与 `pressure-resource-self` 的精确十神路径和逐项检查；Prompt
View 为三张以上候选列出完整合法 partition。零／一张候选时，fallback 不再混入真实候选
universe，两个固定槽与真实候选账本分别闭合。

Evaluator `.008` 把上一版只写在提示里的要求变成可执行考试：

- raw 判型必须直接绑定 packet 的无根／最低有效根、明干同类与藏印竞争；服务端补根不算
  模型学会；
- 每条 `condition_or_falsifier` 必须同时包含可观察或未决条件，以及“由当前判断改判为另一
  判断”的后件；重复当前断言不通过；
- reversal 必须分别具名主解释和替代解释，一条明确维持，一条明确翻转；同一信号写两遍
  或两条都支持同一方不通过；
- 任何修复仍须留下 H1／H2、主次、候选覆盖、根气或路径回执，产品安全与模型能力继续
  分轨。

本轮连续封存了三代候选的戊土回归与庚金迁移结果。Evaluator `.007` 与 `.008` 增加的
检查项不同，绝对通过数不能横向冒充提升；同一版本内比较错误簇才有效。

| 候选 | 戊土 Suite / Experiment | 庚金 Suite / Experiment | 真实结果 |
| --- | --- | --- | --- |
| Profile `.028` / Prompt `.025` / Eval `.007` | `793f2a...` / `3b68e3...`，3 hold + 15 response | `cf70a7...` / `0240d1...`，4 + 15 | 两盘仍有判型、候选覆盖或方法卡缺口 |
| Profile `.029` / Prompt `.026` / Eval `.007` | `396e61...` / `d1211d...`，3 + 17 | `b1d8e2...` / `a0b7d0...`，4 + 14 | B 的方法卡闭合改善；A 判型与两盘候选账本仍不稳 |
| Profile `.030` / Prompt `.027` / Eval `.008` | `fc1446...` / `78c5bd...`，3 + 21 | `edd6aa...` / `634f46...`，4 + 18 | 庚金 A/B 原生 packet-bound 判型通过；反证与主次翻转仍双盘失败 |

所有六次运行均为 `PRODUCT_SAFE_MODEL_FAIL`，runner error 为 0。最新庚金运行中不再出现
`DAY_MASTER_REGIME` 或 raw packet-fact failure，说明枚举判型出口对同一 Gemma 有真实帮助；
但 A 的候选覆盖仍失败、B 的第二张方法卡仍不完整，A/B 的 raw falsifier 与 reversal 全部
失败。最新戊土回归中，无根 A 仍需一次判型修复。这证明系统尚未达到高级命理师：它开始
稳定掌握部分整盘入口，却还不能独立完成“为什么此路胜出、什么事实会推翻它”的专业比较。

下一刀不再增加自由散文。系统应把每张方法卡编译成可选择的反事实决策行：当前 ruling、
仍未裁定的阻断／承载／可达轴、允许的相反目标和改判动作都先类型化；模型在一次整盘调用
里选择并结合本盘事实落地。跨卡 reversal 同样绑定两张卡的专属决胜项和相反动作。这样仍是
一次 LLM 裁决，但把稳定集合运算与合法状态交给系统，把真正需要命理比较的取舍留给模型。

## 第八组合成实验：月令坐标、根气与原始判断一致性

第五个 DEV Suite 换成从未进入目录的壬水对照，专门检验模型是否把月支月令与月干十神
分开，并在完整时柱变化后重编译判型、候选集合和主路径：

```text
experiment  v60-mingli-synthetic-experiment-4355419cf3ec29abc246
suite       v60-mingli-synthetic-suite-f1d255f320067d119d27

A：1990-03-18 12:00 Asia/Shanghai
   庚午 / 己卯 / 壬午 / 丙午
   月令 = 卯；月干己 = 正官；卯藏乙 = 伤官
   无根、无明干比劫；year干庚偏印只作资源竞争
   regime = FALSE_FOLLOW_COMPETITION / UNRESOLVED

B：1990-03-18 22:00 Asia/Shanghai
   庚午 / 己卯 / 壬午 / 辛亥
   月令与月干坐标不变
   hour支藏壬 = EXACT_DAY_MASTER / PRIMARY_QI
   year干庚偏印、hour干辛正印仍不得冒充根
   regime = ORDINARY_WEAK / UNRESOLVED / NON_WEAK_OUTSIDE_SCOPE
```

完整时柱还同时改变财、印、藏干、同支关系与起运边界，所以 Gold 不把任何结果单独归因于
亥中壬根，也不预选机制赢家。A 的合法候选是 `pressure-resource-self`、
`wealth-to-pressure`、`resource-to-self`；B 重新编译为 `resource-to-self`、
`pressure-resource-self`。新增本地坐标纪律同时检查 raw 与 normalized prose：
“月令正官己土”属于坐标混淆；“月令卯木，月干己土正官”属于合法分离表达。

真实 `qwen3.8:27b` 严格整盘运行共两次调用：

| 变体 | 输入 token | 输出 token | 墙钟时间 |
| --- | ---: | ---: | ---: |
| A | 12,013 | 4,643 | 187.812s |
| B | 10,883 | 4,788 | 202.063s |
| 合计 | 22,896 | 9,431 | 389.875s |

Qwen 原文正确写成“壬水生于卯月”，没有把己正官冒充月令；A 原生识别无根与
`UNRESOLVED`，B 原生识别 `hour支藏壬` 有效根与 `ORDINARY_WEAK`。两盘的候选全集、
唯一主次、排除项、可执行反证、翻转信号和 PRIMARY-bound work path 也全部通过。

但首轮 Evaluator `.009` 把
`v60-mingli-synthetic-run-adad4f4f971bd6cdcb2d` 记成 `PASS` 后，教师逐项复核发现一个
裁判盲点：A/B 的 H1/H2 都把 raw `judgment` 写成 `SUPPORTED`，而各自方法裁决汇总与 raw
`adjudication` 实际都是 `CONDITIONAL`。服务端已把它们安全降为 A 的
`WORKS_IF / PARTIAL` 和 B 的 `PARTIAL / WORKS_IF`，但旧尺子没有要求这种原始修复留下回执。

Evaluator `.010` 因此新增 raw judgment coherence 与 repair receipt 检查。它只读重放同一
sealed raw output，约 `0.25s` 完成，没有再次调用 Qwen，也没有改 Prompt。修正后的证据为：

```text
experiment run  v60-mingli-synthetic-run-5eb1438b1dee74c3395e
run hash        5eb1438b1dee74c3395eabcf2e43ee0ac05dcd00f3cf80a07d2cbd2d28277d6f
suite run       v60-mingli-synthetic-suite-run-0ca2f52f7628e6987f7f
suite hash      0ca2f52f7628e6987f7f4d62b6d94ddb4924d95c6d7a3d33fa5c616ec505cfd2
changed / hold  27 / 3
outcome         PRODUCT_SAFE_MODEL_FAIL
independence    FAIL
runner errors   0
```

失败项只保留在 A/B 的 `RAW_HYPOTHESIS_JUDGMENT_COHERENT` 与
`RAW_REPAIRS_RECEIPTED`；月令坐标、月干十神、根与资源分离、关系 collateral、最低根门、
候选重编译、typed regime 与主路径绑定全部通过。这说明 Qwen 已经能完成这组陌生盘的主要
命理结构工作，但尚不能稳定控制结论强度。产品结果经本地裁判可保持安全，模型独立资格仍
失败；`QUALIFICATION / HOLDOUT` 不解锁。

## V131 Lab 体验接线

V131 commit `ea2db274ba55b8f9d323881c096d3a3a1ceba66c` 的水庭总览和合成验证目录
已经进入真实 V60。进入 Lab 先看到三个研究入口，而不是个人命盘或常驻 WebGL：

```text
六柱关系观察     -> canonical 四／六柱 Scene Player
八字合成验证     -> 8 个真实课题、append-only 封存运行、真实 Suite／训练任务状态
阿布说           -> 同一个六柱 Scene Player 与服务端锁定声画链
```

总览为只读 GET；目录只增加一个服务端绑定任务入口，仍为零 Canvas。只有进入六柱、
阿布说或具体封存现场后才懒加载唯一 Scene Player。最新卯月 DEV Suite 如实显示
`1/1` 封存、`1` 项待复核和修正后的模型独立失败；跨日主与位阶 Suite 历史继续保留；
`QUALIFICATION / HOLDOUT` 继续显示 `Owner Gate 后开放`。当前页面是“已揭晓封存
复盘”，不是盲审；原型的 `localStorage` 裁决、假 Run 身份和写死统计均未进入系统。

六柱入口只说明当前已准入的六冲／六合成员事实。关系作用、来源可用性、旺衰、有效
做功或吉凶仍必须由整盘方法和专业裁决支持，不能从原型演示文案反推。

## 三段式 DEV 蒸馏：先分题，再由本地系统收口

第八组严格整盘运行证明 Qwen 已能处理主要结构，但两次调用合计仍需 `389.875s`，而且
Evaluator `.010` 发现模型会把自身 `CONDITIONAL` 方法证据抬高成 `SUPPORTED`。因此下一步
不再要求它一口气完成整盘、候选、人生领域与文字成品，而是实现独立的 DEV 蒸馏探针：

```text
canonical synthetic packet
  -> REGIME                 只判身弱／从势出口
  -> CANDIDATE_COMPARISON   只比较两张方法卡的逐项检查
  -> local assembly         重算主次、排除集合与 aggregate adjudication
  -> CERTAINTY              只映射 judgment 与 work-path closure
  -> local evaluator        Gold 后置评分、坐标检查与确定性上限
  -> append-only run
```

三段都使用 `think=false`、`temperature=0`、`top_p=0.95`、`top_k=20`、固定 seed `42` 和
`num_ctx=8192`。输出预算分别为 `500 / 1800 / 320`；候选段只要求最短必要解释，避免重复
复述命盘。Gold、另一变体、人生领域与 Timing 都不进入模型上下文。严格整盘 Agent 没有被
删除或替换，它仍是最终同尺资格考试。

首轮 B 的候选 JSON 在 1400-token 上限处被截断，没有形成 Run。保持字段契约不变后，仅将
候选说明压短并把安全上限调到 1800；随后同一 Prompt Hash 的真实 A/B 结果为：

| 变体 | 判型 | 候选比较 | 确定性 | 总 token | 总时长 | 合同结果 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| A | 11.898s | 52.473s | 5.313s | 7,676 | 69.684s | `DEV_PASS` |
| B | 15.897s | 51.202s | 5.211s | 6,242 | 72.310s | `DEV_PASS` |
| 合计 | 27.795s | 103.675s | 10.524s | 13,918 | 141.994s | DEV-only |

与严格整盘 A/B 相比，总时长下降约 `63.6%`，总 token 下降约 `57.0%`；六个小调用仍为
串行，候选比较占总模型时长约 `73.0%`，所以它是下一轮真正要蒸馏的热点。缓存重放不调用
模型，A/B 分别约 `54ms / 42ms`。

```text
prompt hash  bd5dfb9618cc7bc1d7ddec1d53ea6ebc1509cf5b1ce9c669bde44321a36d79ca
A run        v60-mingli-distillation-run-544e86ed8e20b6fd7aa1
B run        v60-mingli-distillation-run-fc8da8a2364ea2a6c2ee
```

两个 `DEV_PASS` 的精确含义是：模型没有依赖服务端改写就完成三段 Schema；判型符合当前
packet 与 DEV Gold；候选全集、检查顺序、证据范围、排除集合、aggregate 和最终强度映射
闭合。它不等于候选裁决已获专业 Gold。压缩前 A 曾给出 `SUPPORTED/BROKEN`，当前 A 给出
`BROKEN/BROKEN`；B 当前为 `SUPPORTED/BROKEN`。提示词变化即可改变 A 的方法强度，教师
复核因此把它记录为“候选专业稳定性待审”，不裁定哪个版本已成为 canonical 命理结论。

本探针没有产品 API 或浏览器入口，不影响当前按主题读取的 Focused Reading；也不解锁
`QUALIFICATION / HOLDOUT`、publication 或 canonical fact write。

## 当前版本

```text
Foundation                 v60.foundation.044
Mingli Engine              v60.mingli-cognitive-engine.051
Runtime Architecture       v60.runtime-architecture.080
Agent Runtime              v60.mingli-agent-runtime.035
Agent Profile              v60.mingli-agent.whole-chart-cognition.033
Agent Prompt               v60.prompt.mingli-agent-whole-chart.029
Provider Profile           v60.model-serving.qwen38-27b-mingli-agent.002
Agent Prompt View          v60.mingli-agent-prompt-view.019
Agent Reading              v60.mingli-agent-reading.006
Normalization Receipt      v60.mingli-agent-normalization-receipt.001
Agent Adjudication         v60.mingli-agent-adjudication.013
Agent Output Repair        v60.mingli-agent-output-repair.004
Method Distillation        v60.mingli-agent-method-distillation.006
Effective-root Method      v60.mingli-effective-root-method.001
Regime Decision            v60.mingli-agent-regime-decision.002
Stage Projection           v60.mingli-stage-projection.004
Synthetic Catalog          v60.mingli-synthetic-experiment-catalog.007
Synthetic Evaluator        v60.mingli-synthetic-experiment-evaluator.010
Synthetic DEV Gold         v60.mingli-synthetic-experiment-dev-gold.006
Synthetic Run              v60.mingli-synthetic-experiment-run.001
Synthetic Snapshot         v60.mingli-synthetic-experiment-snapshot.004
Suite Catalog              v60.mingli-synthetic-suite-catalog.005
Suite Definition           v60.mingli-synthetic-suite-definition.001
Suite Runner               v60.mingli-synthetic-suite-runner.002
Suite Run                  v60.mingli-synthetic-suite-run.002
Training Request           v60.mingli-synthetic-suite-run-request.001
Training Status            v60.mingli-synthetic-training-status.001
Focused Runtime            v60.mingli-focused-runtime.001
Focused Provider Profile   v60.model-serving.mingli-focused-text.008
Focused Pass               v60.mingli-focused-pass.001
Focused Normalizer         v60.mingli-focused-normalizer.006
Distillation Runtime       v60.mingli-synthetic-distillation-runtime.001
Distillation Prompt        v60.prompt.mingli-synthetic-distillation.001
Distillation Pass          v60.mingli-synthetic-distillation-pass.001
Distillation Evaluator     v60.mingli-synthetic-distillation-evaluator.001
Distillation Run           v60.mingli-synthetic-distillation-run.001
Reading Summary            v60.mingli-reading-summary.008
Unit Mingli                v60.unit-mingli.038
Unit Lab                   v60.unit-lab.036
Migration                  0052_mingli_distillation_runs
```

Migration 0043/0044 追加判型出口、候选 partition、Method `.006` 与合法决策行；0045
再追加 packet-bound 根气考试和可执行反证／翻转语义；0046 将 typed decision row
的 Agent Runtime/Prompt/Adjudication 版本绑定到数据库 manifest；0047 修正
中文否定／弱化竞争语义的 resolution guard。它们均只更新 manifest，不改写任何
sealed run。历史 Gemma4 Suite 仍按 Profile/Prompt `.030/.027`、Reading `.006`、
Evaluator `.008` 与 Gold `.005` 的明确版本语义重放，不能被“当前版本”常量静默改义。
当前 typed-row sealed Suite 绑定
`qwen3.8:27b`、Profile/Prompt `.032/.029`、Serving Profile `.002`；新 Runtime
Profile `.033` 仅用于后续生成与 replay，不回写历史结果；
Reading `.006`、Evaluator `.008` 与 Gold `.005`。

Migration 0048 新增五问 DEV envelope；0049 新增产品逐主题 append-only pass，并将
Foundation 推进到 `.041`、Reading Summary 推进到 `.008`。这两次迁移不回写严格 Agent
或 Synthetic Suite 的历史记录。

Migration 0050 新增第八个陌生盘实验、月令／月干 prose 坐标纪律及第五个 DEV Suite；
0051 将教师复核发现的 raw judgment coherence 缺口固化为 Evaluator `.010`。两次迁移只
推进 manifest 和评尺，不改写旧 sealed run；`.009` 的乐观结果保留为历史证据，当前能力
判断以 `.010` 对同一 raw output 的 append-only replay 为准。

Migration 0052 新增独立的 `mingli.synthetic_distillation_runs` 只追加账本，绑定三段 Prompt、
模型 digest、Provider Profile、packet、逐段 token／时长、原始输出、本地 assembly 与评估。
UPDATE／DELETE 由数据库触发器拒绝；该表只保存 DEV 训练证据，不进入产品 Reading 或正式
命理事实。

## 验证

```text
Backend tests              475 PASS
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

真实 Desktop Chrome 已验证 V131 总庭、七课题目录、新庚金实验、当时最新 Suite 优先、
A／B 切换与精确 B 深链接刷新；页面无控制台 error。Evaluator `.008` 的最终运行通过
服务端契约、前端合成 Lab 契约与生产构建验证，未把它伪称为一次新的 Chrome 模型运行。
既有完整
六柱、阿布说 PREPARING、浏览器前进／后退与两种桌面宽度证据继续成立。总览／目录无 Canvas，深场
始终只有一个 Scene Player。
