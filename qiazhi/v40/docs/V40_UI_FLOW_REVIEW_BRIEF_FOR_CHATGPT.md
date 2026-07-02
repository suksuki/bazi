# V40 UI Flow Review Brief For ChatGPT

Date: 2026-07-02

## Copy This To ChatGPT / Product Analyst

请你审核下面这套 V40 用户侧 UI 流程，重点不是重新设计命理算法，而是帮助我们优化产品体验、信息层级、页面节奏和视觉表达。

## Product Context

产品名：

```text
掐指一算 V40
```

当前定位：

```text
report-first intelligent mingli reading
+ one-question-one-answer conversation chain
+ lightweight Probe calibration
+ practitioner professional lens
+ training and validation loop
```

V40 不是传统长报告，也不是纯聊天产品。我们希望用户先看到清晰结论和建议，再自然进入连续追问；必要时系统只问一个低成本校准问题；命理师角色可以在专业 Lens 中做选择和校准，反馈会进入训练。

## Hard System Principles

1. 没有 LLM，产品运行时直接失败，不允许本地模板静默 fallback。
2. LLM 负责表达、对话和 Thinking 展示，不负责改命盘事实和最终裁决。
3. 八字是主引擎，紫微是 Domain Lens / sidecar，不替代八字主线。
4. 训练和验证通过后直接调参并立即生效，保留 rollback 和补救，不设置人工审核门。
5. Admin 是独立控制台，不出现在用户 app。主系统里 admin 只作为特殊命理师账号使用。
6. 用户 app 不能出现 provider、model、prompt、debug、SignalRegistry、DecisionEngine、policy key 等工程语言。

## Current Entry Points

Local user app:

```text
http://127.0.0.1:9040/v40/ui
```

Runtime API:

```text
/api/v40
```

Admin console is separate:

```text
/admin/v40
```

Current status:

```text
Phase 58: Hard LLM And Direct Training Principles
overall completion: 99%
```

## Current UI Structure

The user app currently contains:

```text
Header / identity
Account panel
Profile panel
Chart input form
Live three-line process ticker
Report hero
Report surface
Probe surface
Consent review surface
Follow-up hub
Conversation surface
Practitioner Lens drawer
Feedback layer
```

The core HTML sections are:

```text
accountPanel
profilePanel
readingForm
verdictHero
reportSurface
processTicker
probeSurface
reviewSurface
followupHub
conversationSurface
lensDrawer
```

## Intended User Flow

### Guest / Ordinary User

```text
open app
→ enter or select chart
→ choose topic
→ click 开始测算
→ see live three-line process ticker while Gemma is thinking
→ read report-first verdict/advice/risk
→ answer optional one-question Probe if useful
→ click a suggested follow-up or type a question
→ receive one answer
→ continue one-question-one-answer chain
→ give lightweight feedback
```

### Registered User

```text
login/register
→ manage own Bazi profiles
→ select one profile
→ run report
→ save reading context
→ continue conversation
→ feedback becomes training material
```

### Practitioner

```text
login as practitioner/admin
→ select profile
→ run report
→ inspect practitioner Lens
→ choose professional action:
   采为主断 / 作为辅助 / 暂不采用 / 需要追问
→ optional note
→ action becomes local overlay and training label
```

## Current Report Flow

After clicking `开始测算`, the app should show only compact process feedback:

```text
定盘
取象
合参
```

It cycles through real work-like stages:

```text
四柱 / 月令 / 大运 / 流年
十神 / 用神候选 / 规则 / 画像 / 路径
八字主引擎 / 紫微旁路 / 分支反证 / 智能表达
```

The user should not click through V30-style multi-step pages. The process is for confidence and rhythm, not interaction.

When the report returns, the page should prioritize:

```text
1. 核心判断
2. 当前重点
3. 可执行建议
4. 风险边界
5. 可以继续问什么
```

## Current Conversation Flow

Conversation should be independent from the reading process:

```text
reading/report is stable
conversation can appear after report
conversation can continue indefinitely
each turn handles one question
new suggested questions can be generated after each answer
```

Important boundary:

```text
Do not mix a fake step page with conversation.
Do not auto-answer a question the user did not click or type.
Do not block page navigation because a conversation answer is pending.
```

## What We Need You To Review

Please review the UI/flow from a product and interaction-design perspective.

Focus questions:

1. Is the first screen too busy because account, profile, chart input and report all live together?
2. Should login/register/profile management be visually separated from the reading workspace?
3. What is the best report-first layout for conclusion, advice, risk, and follow-up?
4. Is the three-line process ticker enough, too subtle, or too artificial?
5. Where should the follow-up hub appear after report: below report, sticky side panel, or conversation-first transition?
6. How should Probe appear without feeling like interruption?
7. How should Practitioner Lens be discoverable but not clutter ordinary user UI?
8. How should mobile handle profile selection, chart input, and long conversation?
9. Which current sections should be collapsed, deferred, or merged?
10. What visual language best matches “modern, quiet, professional metaphysics” without becoming antique/fortune-telling style?

## Desired Output From You

Please return:

```text
1. UI flow critique
2. Recommended page information architecture
3. A simplified user flow
4. Desktop layout recommendation
5. Mobile layout recommendation
6. Component hierarchy
7. Copywriting improvements
8. Animation/motion suggestions
9. What to remove or hide
10. A prioritized implementation checklist
```

## Design Direction

We prefer:

```text
high-trust
minimal
quiet luxury
data-backed but not dashboard-like
professional metaphysics
subtle motion
clear reading order
large enough whitespace
few visible borders
strong typography
warm dark theme or restrained light/dark hybrid
```

Avoid:

```text
old temple / antique fortune-telling style
debug dashboard feeling
engineering terms
too many cards with borders
V30-style 13-step clickable flow
model/provider/prompt text
fake overexplained thinking
conversation appearing before user intent
```

## Current Known Tensions

1. Profile management is necessary, but it can make the first screen feel administrative.
2. Chart input is powerful but visually heavy.
3. Process ticker creates trust, but must not become fake “thinking text”.
4. Report-first flow is correct, but report/advice/risk/follow-up can still compete visually.
5. Conversation is core, but it should not swallow the report.
6. Practitioner Lens is a product differentiator, but ordinary users should not see professional calibration complexity.
7. Training feedback is central to the system, but users should only experience it as simple feedback.

## Current Implementation Constraints

- V40 user app is a single HTML runtime surface at `/v40/ui`.
- Admin console is separate.
- Product requests use Ollama/Gemma4.
- Tests enforce no silent local fallback.
- Training policy can activate immediately after validation.
- V40 must remain isolated from V30 runtime.

