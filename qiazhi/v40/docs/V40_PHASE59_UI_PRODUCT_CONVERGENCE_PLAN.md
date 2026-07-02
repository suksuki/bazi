# V40 Phase 59: UI Product Convergence Plan

Date: 2026-07-02

## Source

This plan adopts the external UI review returned from the V40 UI flow brief:

```text
V40 should move from engineering workbench to mingli reading product.
少一点系统能力展示，多一点测算仪式感。
少一点后台感，多一点清晰结论。
```

## Product Position

V40 user app is:

```text
一份安静、清晰、可追问的现代命理测算。
```

It is not:

```text
debug dashboard
admin console
V30 multi-step worksheet
generic chatbot
traditional long report only
```

## Adopted Information Architecture

The user app must progressively disclose capability in four layers:

```text
Layer 1: Reading Setup
  topic selection
  current chart/profile card
  chart input drawer
  start reading

Layer 2: Reading Result
  core verdict
  current focus
  action advice
  risk boundary
  collapsed process summary

Layer 3: Follow-up And Conversation
  recommended follow-up
  free question
  one-question-one-answer chain

Layer 4: Calibration And Practitioner Lens
  one Probe card only when useful
  lightweight feedback
  practitioner drawer only for practitioner/admin role
```

The report is always the spine:

```text
setup -> process -> report -> follow-up -> conversation -> optional calibration
```

Conversation never replaces the report and never appears as a fake step page.

## P0: De-Engineering

Remove or hide from ordinary user surface:

```text
provider/model/local/gemma switch
acceptance status
raw thinking trace
prompt/debug text
SignalRegistry / DecisionEngine / policy key / trainable_refs
常驻 accountPanel
常驻 profilePanel
常驻 review consent surface
```

User-facing names:

```text
Follow-up seeds -> 你可以继续追问
Thinking -> 查看推演过程
Probe -> 一个问题，让判断更准
Training feedback -> 这个判断像你吗？
Practitioner Lens -> 专业视角
```

## P1: Reading Setup First Screen

The first screen should contain only:

```text
brand and identity
topic selector
current chart card
start reading button
short line explaining follow-up/calibration after report
```

Account/profile management becomes:

```text
top-right user menu
or 我的命盘 drawer
```

Current chart card format:

```text
当前命盘
乾造 / 坤造
甲子年 丙寅月 庚午日 丁亥时
大运：庚午
流年：丙午

更换命盘 / 编辑四柱 / 高级设置
```

Four-pillar inputs stay available, but default to a collapsed edit area.

## P2: Report-First Layout

Reading result order:

```text
1. 核心判断
2. 当前重点
3. 行动建议
4. 风险边界
5. 你可以继续追问
```

Core judgment should be concise:

```text
3-5 lines
not a dashboard table
not exhaustive modules
not generic template language
```

Topic focus should show only 2-3 relevant domains. Other domains collapse behind:

```text
展开更多领域
```

Action advice format:

```text
适合做
暂时避免
需要确认
```

Risk boundary should be human-language and confidence-building:

```text
这里不能简单断成“一定好/一定坏”；更准确的是机会与风险并存，关键看承接方式。
```

## P3: Follow-Up And Conversation Layering

Follow-up hub belongs after the report, not as a sticky side panel:

```text
你可以继续追问
[今年财运机会在哪里？]
[适合创业还是稳定发展？]
[合作会带财还是耗财？]
```

Conversation rules:

```text
one turn answers one question
do not auto-answer a question the user did not click/type
do not refresh the report
append turns below report
generate next suggestions after each answer
```

## P4: Probe Card

Probe appears only as a special card:

```text
一个问题，让判断更准
```

It may appear:

```text
below "需要确认" in the report
after a conversation answer when calibration is necessary
```

It must:

```text
ask one concrete question
offer simple options
allow skip
show what changed after answer
convert answer into training material
```

## P5: Practitioner Lens Drawer

Only practitioner/admin role sees:

```text
专业视角
```

Phase 59 locks the product rule:

```text
Practitioner is a role-based lens, not a separate product surface.
命理师是同一测算结果上的专业视角，不是另一个测算流程。
```

The same user app must serve:

```text
same Reading
same Report
same Conversation
same Probe
different RoleProjection
```

There must not be a separate practitioner reading page. Future review queue items may open a case list, but the case detail returns to this same Reading UI with practitioner RoleProjection.

The drawer is contextual:

```text
click 财富卡 -> focus wealth evidence, branches, probes and actions
click 关系卡 -> focus relationship evidence, branches, probes and actions
click 专业视角 -> open the current report focus
```

It is collapsed by default, so the normal report remains the spine even for practitioners.

Drawer content:

```text
当前判断
主分支
备选分支
证据
反证
建议追问
备注
```

Actions use human professional language:

```text
更像这个表现
作为辅助参考
暂不采用
需要追问确认
用户反馈不符合
添加备注
```

No internal words:

```text
adopt / downweight / policy key / VOI / trainable_refs
```

## P6: Mobile Flow

Mobile is not compressed desktop. It becomes a single-column staged flow:

```text
测算主题
当前命盘
开始测算
测算过程
核心判断
建议
风险边界
推荐追问
对话
反馈
```

Hide by default:

```text
Profile management details
advanced settings
practitioner lens
detailed process trace
complex evidence
```

Use drawers for hidden areas.

## P7: Visual Direction

Adopt:

```text
warm paper background
ink text
low-saturation cinnabar accent
bamboo green support color
fewer borders
more whitespace
strong headings
subtle motion
quiet professional metaphysics
```

Suggested palette:

```text
background: #F8F5EE
text: #242424
muted: #6F6A60
border: #E6DDCE
accent: #9A3B2F
support: #6E8B7E
```

Avoid:

```text
pure black control-console feel
big bagua/copper coin/talisman/temple imagery
red-black high contrast
too many bordered cards
fake long thinking text
```

## Implementation Plan

### Phase 59A

```text
P0 de-engineering audit
collapse account/profile into user/profile drawer
rename Practitioner Lens -> 专业视角
hide consent review until user explicitly requests practitioner review
```

### Phase 59B

```text
rebuild Reading Setup around topic selector + current chart card
move four-pillar editor into details/drawer
make start reading the dominant action
```

### Phase 59C

```text
restructure report into VerdictHero / FocusSummary / AdviceBlock / RiskBoundary / Follow-upHub
limit visible topic cards to relevant 2-3 domains
collapse process ticker after completion into 查看推演过程
```

### Phase 59D

```text
conversation append-only below report
next question suggestions after each answer
Probe as a single calibration card
mobile single-column staged flow
```

## Runtime Progress

2026-07-02 已完成第一轮 runtime 收敛：

```text
top user/profile drawer
Reading Setup first screen
CurrentChartCard
collapsed four-pillar editor
completed process ticker collapse
report topic focus limited to 3 visible domains
Probe renamed to 一个问题，让判断更准
review consent hidden until explicit request
Practitioner Lens renamed to 专业视角
```

2026-07-02 第二轮 runtime 收敛目标：

```text
same Reading + RoleProjection principle documented
professional Lens is collapsed by default
report cards can focus Lens by topic
Lens actions use human language and backend-safe action keys
practitioner note is captured as local training material
mobile practitioner view behaves as a lightweight drawer
```

Next runtime work:

```text
contextual practitioner Lens QA
conversation next-suggestion refresh after each answer
live LLM acceptance with admin profiles
online cutover decision with user acceptance evidence
```

## Acceptance Checklist

- First screen no longer feels like account/profile admin.
- User can start a reading with topic + current chart + one primary button.
- Report is readable before follow-up appears.
- Conversation never refreshes or blocks the report.
- Probe asks one question and explains the payoff.
- Practitioner Lens is hidden for ordinary users, collapsed by default for practitioners, and focused by current report topic.
- Mobile reads as a staged product flow, not compressed desktop.
- No engineering/provider/model/policy language leaks into user app.
