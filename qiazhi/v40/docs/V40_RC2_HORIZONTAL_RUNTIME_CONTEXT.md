# V40-RC2 Horizontal Runtime Context

Date: 2026-07-01

## 核心定位

V40 必须保留并升格四个横向能力：

```text
Locale
Role
Client
Engine Capability
```

它们不是 UI 层后补，而是 V40 runtime 的系统维度。

完整表述：

```text
V40 是一个多语言、多角色、多终端、多引擎的可训练命理运行时。
```

## RuntimeContext

V40 runtime 统一上下文：

```text
RuntimeContext =
  LocaleContext
  + RoleContext
  + ClientContext
  + EngineContext
  + TrainingContext
```

它贯穿：

```text
RuntimeRequest
→ EnginePlan
→ SignalRegistry
→ DecisionEngine
→ ProductProjection
→ LLMExpression
→ SurfaceBundle
→ TrainingLabelEvent
→ EvaluationCase
```

## LocaleContext

支持：

```text
zh-CN
en-US
ko-KR
```

多语言不是前端翻译，而是：

```text
canonical claim keys
→ MingliTermDictionary
→ LocaleProjection
→ LLMExpression
→ locale-specific acceptance
```

内部仍使用稳定 key，例如：

```text
food_output_to_wealth
bijie_competition
wealth_manifestation_mode
career_authority_pressure
```

## RoleContext

角色：

```text
guest
user
practitioner
admin
```

Admin 已经独立为新的前台服务和端口，主系统不再塞 Admin 页面。V40 contract 保留 `admin` 只是为了控制台、审计、评测和 projection 测试。

不同角色由 RoleProjection 控制，不靠 UI 按钮隐藏：

| Role | 可见内容 |
| --- | --- |
| guest | 核心结论、少量建议、有限追问、轻量反馈 |
| user | 完整报告、建议、推荐追问、Probe、反馈、历史记录 |
| practitioner | 证据摘要、分支卡、反证、Probe 候选、校准动作 |
| admin | 独立控制台、审计、训练、发布、回滚 |

普通用户不能看到：

```text
raw signal
claim_key
policy_key
engine debug
acceptance status
training weights
practitioner calibration controls
```

## ClientContext

终端不能改变命理结论，只能改变信息密度和布局。

支持：

```text
desktop
tablet
mobile
```

移动端不是桌面端缩放，而是：

```text
core verdict
advice
topic cards
recommended probes
conversation
feedback
```

桌面端可以展示：

```text
report
side panel
evidence drawer
practitioner lens
conversation
```

`SurfaceSection` 用 `priority / default_collapsed / mobile_collapsed / role_visibility` 控制密度。

## EngineContext And EngineCapability

引擎不是 adapter 堆叠，而是能力声明和调度。

第一批：

```text
Bazi
Ziwei
RealityProbe
Conversation
```

边界：

```text
EngineCapability.can_directly_generate_verdict = false
```

所有最终 Verdict 只能由 DecisionEngine 生成。

策略：

| Engine | 策略 |
| --- | --- |
| Bazi | 默认必跑，主引擎，weight=1.0 |
| Ziwei | 有完整出生信息才跑，V40-RC2 仍是 Domain Lens，weight=0 |
| RealityProbe | mixed / conflict / advice gap / mismatch 时触发 |
| Conversation | 报告后用户主动追问才启动 |

## Training And Evaluation

训练必须记录：

```text
locale
role
client
engine_source
```

评测必须能拆分：

```text
zh-CN / en-US / ko-KR overclaim rate
terminology consistency
role leakage rate
mobile report readability
mobile probe completion
desktop practitioner calibration success
engine-aware attribution coverage
```

## Read Model

新增只读接口：

```text
GET /api/v40/project/horizontal-runtime-context
```

Admin 独立控制台新增：

```text
Runtime Context
```

## 硬原则

1. 多语言不是前端翻译，而是 LocaleContext 驱动的 ProductProjection + LLMExpression。
2. 多角色不是按钮隐藏，而是 RoleProjection + 权限 + 训练权重。
3. 多终端不是 CSS 缩放，而是 ClientContext 驱动的 Surface 密度和布局。
4. 多引擎不是模块堆叠，而是 EngineCapability + EnginePlan + SignalRegistry。
5. 所有横向能力都必须进入 Evaluation / Training / Release Gate。
6. Admin 保持独立控制台，不回到主系统。
