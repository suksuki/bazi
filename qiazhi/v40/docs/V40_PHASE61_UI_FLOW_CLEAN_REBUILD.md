# V40 Phase 61: UI Flow Clean Rebuild

Date: 2026-07-02

## Source

This phase adopts the latest UI / flow review:

```text
Stop feature stacking.
Keep V40 backend, runtime, API, training, LLM, DecisionEngine and Admin control plane.
Clean rebuild the /v40/ui product shell.
```

## Position

This is not a V40 rewrite.

```text
Keep:
  /api/v40
  runtime response
  report API
  conversation API
  training label API
  practitioner calibration API
  LLM / acceptance
  independent admin console

Clean rebuild:
  /v40/ui information architecture
  page state machine
  component hierarchy
  role visibility
  visual rhythm
  copywriting
```

## Product State Machine

`/v40/ui` must be organized by explicit state:

```text
setup / running / report / conversation / practitioner
```

```text
setup        before reading
running      reading generation in progress
report       report generated
conversation user explicitly starts follow-up
practitioner practitioner Lens open
```

Each state displays only what is needed.

## Component Tree

The user-side shell should behave like:

```text
V40UserApp
├── AppHeader
│   ├── Brand
│   ├── MyProfilesButton
│   └── RoleBadge
│
├── MainLayout
│   ├── SetupPanel
│   │   ├── TopicSelector
│   │   ├── CurrentChartCard
│   │   ├── ChartInputDrawer
│   │   ├── QuestionBox
│   │   └── StartReadingButton
│   │
│   └── ReadingColumn
│       ├── ProcessTicker
│       ├── ReadingResult
│       │   ├── VerdictHero
│       │   ├── FocusSummary
│       │   ├── AdviceBlock
│       │   ├── RiskBoundary
│       │   └── ProcessDrawerTrigger
│       ├── CalibrationSurface
│       │   └── ProbeCard
│       ├── FollowUpHub
│       │   └── FollowUpChips
│       ├── ConversationSurface
│       └── FeedbackLayer
│
└── PractitionerLensDrawer
```

## Cleanup Rules

1. Ordinary user flow is only:

```text
输入命盘 -> 开始测算 -> 核心报告 -> 继续追问 -> 必要时校准 -> 反馈
```

2. Account and profile management stay inside `我的命盘`.
3. Chart input is full before reading and collapsed after report.
4. Setup state hides the ReadingColumn; it does not render a placeholder section.
5. Process ticker appears during `running`; after report it is folded as `查看推演过程`.
6. Report structure is fixed:

```text
核心判断
行动建议
风险边界
推荐追问
```

7. Probe is a lightweight one-question card:

```text
一个问题，让判断更准
```

8. Follow-up uses chips, not thick cards.
9. Conversation appears only after user click/type.
10. Practitioner Lens is same-page drawer only for practitioner role.
11. Ordinary user must never see provider/model/acceptance/policy/debug/training internals.

## Visual Direction

```text
暖白背景
墨色文字
低饱和朱砂主色
竹青辅助
少边框
大留白
主报告更稳
Probe 更轻
Lens 抽屉化
```

## Done Criteria

- First screen no longer feels like account/profile admin.
- User can understand the core judgment within 5 seconds after report generation.
- Report, Probe, conversation and Practitioner Lens are layered clearly.
- Conversation does not auto-start and does not overwrite the report.
- Probe asks one concrete question and folds after answer.
- Practitioner Lens does not expose raw keys, policy fields or trainable refs.
- Mobile layout stays single-column and readable.
