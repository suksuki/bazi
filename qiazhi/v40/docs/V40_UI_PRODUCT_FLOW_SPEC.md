# V40 UI Product Flow Spec

Date: 2026-07-01

## Positioning

V40 user surface is not a debug console, not a generic chat product, and not a traditional long report product.

The product shape is:

```text
Input
→ Report-first reading
→ Follow-up conversation
→ Probe calibration when useful
→ Feedback to training
→ Practitioner Lens when role allows
```

The long-term product identity is:

```text
AI initial reading
+ user reality feedback
+ practitioner professional calibration
+ trainable and verifiable policy loop
```

## Product Principles

1. First screen after reading must show conclusion and advice.
2. Conversation never interrupts reading.
3. Probe appears only when information gain is worth user cost.
4. Practitioner Lens is professional calibration, not Admin.
5. Admin remains an independent control plane and never appears in the user app.
6. Ordinary users never see provider, model, prompt, acceptance, policy key, trace, VOI, or training target.
7. LLM expresses and explains; it does not own verdict authority.
8. Every meaningful user or practitioner interaction must become structured training material.
9. Training policy is high-iteration: training can take effect immediately, with rollback and repair records.
10. UI should feel modern, quiet, professional, and lightly inspired by mingli, not old-fashioned fortune-telling.

## Top-Level Information Architecture

```text
User App
  Input Workspace
  Reading Surface
  Follow-up Hub
  Conversation Surface
  Probe Calibration Surface
  Feedback Layer
  Practitioner Lens

Admin App
  Evaluation
  Training
  Active Policy Registry
  Release / Cutover / Smoke
```

Admin is not part of the user app.

## User Flow

### Ordinary User

```text
choose topic
→ enter chart
→ generate report
→ read core verdict and advice
→ click suggested question or type follow-up
→ answer optional probe
→ give lightweight feedback
```

The ordinary user sees:

- Core judgment.
- This reading's focus.
- Action advice.
- Risk boundary.
- Suggested follow-up questions.
- Optional feedback controls.

The ordinary user does not see:

- Provider/model/base URL.
- Local/Gemma/Ollama switch.
- Acceptance status.
- Raw thinking.
- Policy registry.
- Training labels.
- Practitioner calibration internals.

### Deep Calibration User

```text
report
→ mixed branch or insufficient context detected
→ probe card appears
→ user selects simple option or enters short fact
→ refined advice appears
→ feedback is converted into training labels
```

Probe must be skippable, short, and explained in user language:

```text
这个问题会让财富判断更准。
当前更像哪一种赚钱方式？
固定工资 / 项目客户 / 合伙团队 / 投资资产 / 暂不确定
```

### Practitioner

```text
open Practitioner Lens
→ inspect main verdict, alternative branches, evidence and counter-evidence
→ choose professional action
→ add optional note
→ action becomes local overlay and training label
```

Practitioner actions are human-language choices:

- 更像这个表现
- 作为辅助参考
- 暂不采用
- 需要追问确认
- 用户反馈不符合
- 添加备注

Internal mapping may become:

```text
support
auxiliary
downweight
ask_more
mismatch
note
```

Practitioners cannot:

- Edit chart facts.
- Edit global weights directly.
- Publish policy.
- View Admin debug by default.

## Future Human Review Flow

Human practitioner review is optional and consent-bound.

```text
user requests practitioner review
→ user selects share scope
→ ConsentGrant is created
→ anonymized case enters review queue
→ practitioner reviews structured branches and advice
→ review result returns to user
→ user optionally allows anonymized training use
```

Required future contracts:

```text
ConsentGrant
AnonymizedCaseView
PractitionerReviewRequest
PractitionerReviewResult
CaseAssignment
PractitionerReliabilityScore
```

ConsentGrant must include:

```text
consent_id
user_id
reading_id
share_scope
allowed_recipients
allowed_usage
allow_training
anonymized
expires_at
revoked_at
```

No user chart, conversation, or personal context may be distributed to practitioners without explicit consent.

## Desktop Layout

Target desktop layout:

```text
┌──────────────────┬──────────────────────────────┬──────────────────┐
│ Input Workspace  │ Reading / Conversation        │ Practitioner Lens │
│                  │                              │ optional drawer   │
│ topic            │ VerdictHero                   │ branches          │
│ chart            │ TopicInsightCards             │ evidence          │
│ question         │ AdviceCards                   │ counter-evidence  │
│ submit           │ RiskBoundary                  │ calibration       │
│                  │ Follow-up Hub                 │ notes             │
│                  │ Conversation Surface          │                  │
└──────────────────┴──────────────────────────────┴──────────────────┘
```

Default user mode shows only left and center.

Practitioner Lens is a right drawer, not a section inside the report.

## Mobile Layout

Mobile is a single column:

```text
brand / topic
input
start reading
core verdict
advice
topic cards
follow-up hub
conversation
feedback
```

Mobile practitioner mode only exposes lightweight actions:

- 查看证据
- 需要追问
- 添加备注

Complex calibration is desktop-first.

## Visual Direction

Target tone:

- Modern.
- Calm.
- Professional.
- Slight mingli atmosphere.
- No cheap old-style fortune-telling.

Suggested palette:

```text
background: #F8F5EE
text:       #252525
muted:      #6F6A60
line:       #E5DCCB
accent:     #9A3B2F
support:    #6E8B7E
```

Use:

- Fine lines.
- Light paper texture.
- Stem/branch micro labels.
- Quiet time-cycle marks.
- Small icon accents.

Avoid:

- Large gold.
- Red/black hard contrast.
- Bagua/copper coin overuse.
- Temple, deity, dragon/phoenix imagery.
- Heavy gradients.
- Calligraphy body text.

## Component Spec

### Input Workspace

Fields:

- Topic selector.
- Role is derived from login, not a casual user dropdown.
- Chart mode:
  - 我知道出生时间
  - 我知道四柱
- Four pillars as stem/branch selectors.
- Current luck and year under advanced settings.
- User question.

Remove from ordinary user surface:

- execution_mode.
- provider/model.
- raw LLM status.

### Reading Surface

Main components:

```text
VerdictHero
TopicInsightCard
AdviceCard
RiskBoundaryCard
ThinkingSummaryDisclosure
```

VerdictHero includes:

- One-sentence core judgment.
- Strength label: 较有依据 / 需要校准 / 倾向参考.
- This reading's focus.

AdviceCard groups:

- 适合做.
- 暂时避免.
- 需要确认.

RiskBoundaryCard explains what cannot be said too absolutely.

### Follow-Up Hub

Appears only after accepted report.

It contains 3 to 5 suggested questions from `ConversationSeed`.

It also allows a free user question.

Clicking a seed starts `ConversationTurn`; it does not rerun the reading and does not refresh the report.

### Conversation Surface

Each turn displays:

- User question.
- Answer grounded in current report.
- Related basis in user language.
- Next suggested questions.
- Feedback buttons.

The answer is report-grounded conversation, not generic chat.

### Probe Calibration Card

Probe is separate from conversation.

It appears when:

- Verdict is mixed.
- Advice needs reality context.
- Bazi and Ziwei signals disagree.
- User says "not like me".
- User explicitly chooses deep calibration.

Probe output should create:

```text
AnswerSignal
HiddenAttributeUpdate
TrainingLabelEvent
LocalOverlay
```

### Feedback Layer

Report feedback:

```text
这个判断像你吗？
很像 / 部分像 / 不太像
```

Conversation feedback:

```text
这个回答有帮助吗？
有帮助 / 一般 / 不准确
```

Mismatch should trigger a recovery probe instead of only recording a negative label.

### Practitioner Lens

Practitioner Lens shows:

- Main verdict.
- Alternative branches.
- Evidence.
- Counter-evidence.
- Probe candidates.
- User feedback.
- Notes.
- Human-language calibration actions.

It must not show:

- claim_key.
- policy_key.
- VOI threshold.
- weight_delta.
- conflict_group_id.
- training_target.

## Data And API Mapping

Current V40 runtime assets:

```text
RuntimeResult
SurfaceBundle
ProductProjectionBundle
ConversationSeed
ConversationTurn
TrainingLabelEvent
LocalOverlay
PractitionerLensAction
TrainablePolicyRegistry
```

Current API mapping:

```text
POST /api/v40/readings/native-report
POST /api/v40/conversation/turn
POST /api/v40/training/labels
POST /api/v40/calibration/practitioner-lens-action
GET  /api/v40/surface/beta-readiness
GET  /api/v40/training/policy-registries/active
```

Future API mapping:

```text
POST /api/v40/probes/answer
POST /api/v40/consent/grants
POST /api/v40/practitioner/review-requests
GET  /api/v40/practitioner/review-queue
POST /api/v40/practitioner/review-results
```

## Current V40 UI Audit

Current `/v40/ui` already has:

- Report-first generation.
- Conversation after report.
- Feedback buttons mapped to training labels.
- Practitioner calibration panel.
- Admin separated on `/admin/v40`.
- No silent local fallback when LLM is required.

Current gaps:

- UI still exposes `execution_mode` to ordinary users.
- Role can be selected casually instead of being login-derived.
- Practitioner panel is embedded inside result flow instead of a right drawer.
- Visual direction is dark control-plane style, not final user product style.
- Probe is not yet a first-class calibration card.
- Four pillars are free text inputs instead of stem/branch selectors.
- Thinking is not formalized as a clean disclosure component.
- Human review and ConsentGrant are not yet modeled.

## Mainline Tasks

### UI-1 Product Shell

Create the final user app shell:

- Warm light visual system.
- Left input, center report/conversation, right practitioner drawer.
- Mobile single-column layout.
- Remove ordinary user engineering fields.

### UI-2 Reading Components

Implement:

- VerdictHero.
- TopicInsightCard.
- AdviceCard.
- RiskBoundaryCard.
- ThinkingSummaryDisclosure.

### UI-3 Conversation Surface

Refine report-grounded conversation:

- Keep report stable.
- Render basis and next seeds.
- Persist feedback as training labels.
- Never auto-start conversation.

### UI-4 Probe Calibration

Make Probe a first-class surface:

- Probe card.
- Simple choices.
- Skip action.
- Immediate refined advice.
- AnswerSignal / HiddenAttributeUpdate / LocalOverlay / TrainingLabelEvent.

### UI-5 Practitioner Lens

Move Practitioner Lens to drawer:

- Professional language.
- Branch and evidence cards.
- Human-readable calibration actions.
- Notes.
- Training event bridge.

### UI-6 Consent And Review Queue

Prepare future human review:

- ConsentGrant.
- AnonymizedCaseView.
- PractitionerReviewRequest.
- PractitionerReviewResult.
- CaseAssignment.
- PractitionerReliabilityScore.

## Acceptance Gates

User surface is acceptable when:

1. Ordinary user sees core verdict and advice before any conversation.
2. Conversation never refreshes or reruns the report.
3. Probe appears only with explanation and can be skipped.
4. Practitioner controls are hidden unless role allows.
5. No provider/model/prompt/acceptance/policy/debug terms leak to ordinary users.
6. Mobile view is usable without side panels.
7. Feedback creates structured training material.
8. Practitioner action creates structured calibration material.
9. Admin remains independent.
10. Active policy version used by runtime remains traceable.
