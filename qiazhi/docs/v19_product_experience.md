# V19 Product Experience

V19 Product Experience is a clean restart.

It does not inherit the V18 UI structure.

It does not use `/demo` as the product center.

It does not make wealth the system center.

## 1. Product Positioning

V19 is a Bazi prediction system.

It is not a wealth demo.

It is not an open-ended AI fortune-telling chat.

The product promise is:

```text
chart structure understanding -> verifiable prediction
```

The engine first understands the chart:

```text
Core Feature
Strength
Structure
Inference
Mapping
Contract-backed result
```

The first product phase should focus on:

```text
basic chart structure
one controlled prediction theme
```

The controlled theme may be used to prove the experience loop, but it must not redefine the system as a wealth product.

## 2. Product Principles

```text
1. Bazi first, not theme first.
2. Mobile first, not desktop compressed.
3. Structure before prediction.
4. Evidence before explanation.
5. Contract before narrative.
6. Feedback becomes learning signal, not direct rule change.
7. Replay is part of trust, not an afterthought.
8. Unsupported questions fail closed.
9. LLM expresses verified outputs only.
10. zh / en / ko are first-class expression systems.
```

## 3. Information Architecture

V19 product surfaces:

```text
/
/oracle
/replay
/practitioner
/admin
```

### Visitor surface

Primary route:

```text
/
```

Purpose:

```text
explain the system
show capability boundary
let visitor understand why V19 is verifiable
lead visitor into oracle flow
```

Visitor must see:

```text
what the system can do
what the system cannot do
how verification works
how replay works
why feedback matters
```

Visitor must not be pushed into a wealth-only demo.

### User surface

Primary route:

```text
/oracle
```

Purpose:

```text
birth input
basic chart structure
question guidance
controlled prediction theme
contract-backed result
feedback
history
replay
```

User experience should feel like:

```text
I provide birth info.
The system understands my chart.
I ask a supported question.
The system gives a verified result with evidence.
I can give feedback.
I can replay what happened.
```

### Practitioner surface

Primary route:

```text
/practitioner
```

Purpose:

```text
knowledge review
inference signal review
mapping review
synthetic validation review
rule candidate proposal
case commentary
```

Practitioner experience should feel like:

```text
I can inspect the system's Bazi reasoning language.
I can mark signals and mappings as correct, questionable, or wrong.
I can propose corrections.
I cannot activate production rules directly.
```

### Admin surface

Primary route:

```text
/admin
```

Purpose:

```text
rule activation governance
mapping governance
knowledge governance
user and role management
system health
audit trail
PostgreSQL / Redis runtime visibility
```

Admin experience should feel like:

```text
I govern what reaches production.
I can see review status, validation results, and audit trails.
I approve activation only after review and validation.
```

## 4. Role Experience

### Visitor

Visitor can:

```text
read product explanation
see capability boundary
view public replay
start oracle onboarding
```

Visitor cannot:

```text
write feedback
access private history
create Knowledge Unit
submit rule candidate
activate rule
```

### User

User can:

```text
enter birth information
generate basic chart structure
ask supported prediction questions
view Contract-backed result
submit feedback
view own history
share replay
```

User cannot:

```text
change rules
review Knowledge Units
approve mappings
activate production rules
```

### Practitioner

Practitioner can:

```text
review Knowledge Unit
comment on Core / Inference signals
mark Domain Mapping as correct, questionable, or wrong
propose corrections
submit rule candidates
review synthetic validation results
```

Practitioner cannot:

```text
activate rule
modify active production rule directly
skip audit trail
override admin governance
```

### Admin

Admin can:

```text
approve reviewed Knowledge Unit
activate rule
review mapping registry status
inspect synthetic validation reports
manage roles
inspect audit trail
monitor runtime stability
```

Admin should act through governed workflows, not direct hidden mutation.

## 5. Core Page Drafts

## `/`

Goal:

```text
position V19 as a verifiable Bazi prediction system
```

Sections:

```text
hero
what V19 does
what V19 does not do
Core -> Inference -> Contract explanation
trust model
role entry points
language switch
start oracle CTA
```

Mobile layout:

```text
single column
short cards
no technical tables
one primary CTA
capability boundary visible before CTA
```

Desktop layout:

```text
hero with trust diagram
two-column explanation
role cards
verification flow
```

## `/oracle`

Goal:

```text
main user product flow
```

Sections:

```text
birth input
chart completeness state
basic chart structure summary
Core / Inference summary
prediction theme selection
question guidance
Contract-backed result
evidence summary
uncertainty
feedback
history
```

Mobile flow:

```text
1. Birth info
2. Basic chart structure
3. Supported question
4. Result summary
5. Evidence preview
6. Uncertainty
7. Feedback
8. Replay
```

Desktop flow:

```text
left: input and history
center: chart structure and prediction result
right: evidence, verifier, replay
```

The page must not start from wealth.

It starts from chart structure.

## `/replay`

Goal:

```text
public-safe verification surface
```

Replay shows:

```text
result summary
confidence
verifier status
evidence summary
uncertainty
feedback summary
redaction notice
prediction_id
contract hash
```

Replay hides:

```text
private birth details unless owner is authenticated
full ledger internals
admin-only debug data
raw prompts
raw LLM output
```

Mobile layout:

```text
result first
trust state second
evidence summary third
technical ids collapsed
```

## `/practitioner`

Goal:

```text
professional review workspace
```

Sections:

```text
review queue
Knowledge Unit review
Inference signal review
Mapping review
Synthetic Validation report
rule candidate submission
case comments
```

Primary actions:

```text
mark correct
mark questionable
mark wrong
propose correction
submit candidate
request more validation
```

The practitioner workspace must show reasoning artifacts, not product marketing copy.

## `/admin`

Goal:

```text
governance and operations
```

Sections:

```text
rule lifecycle
mapping registry
knowledge lifecycle
synthetic validation runs
self-learning signals
practitioner feedback
PostgreSQL source-of-truth status
Redis runtime layer status
audit trail
role management
```

Primary actions:

```text
approve reviewed item
reject item
request revision
activate rule
deprecate rule
inspect drift
inspect audit trail
```

Admin UI must emphasize risk and traceability over convenience.

## 6. Mobile-First Design

V19 must be designed first for:

```text
phone Chrome
```

Then adapted to:

```text
desktop Chrome
```

Target viewports:

```text
iPhone SE
iPhone 14 / 15
common Android widths
desktop 1440px
```

Mobile rules:

```text
single column by default
no horizontal scrolling
large tap targets
short result cards
evidence collapsed by default
technical data collapsed by default
sticky or easy-to-reach primary action
long prediction_id and hashes must wrap
chips may horizontally scroll only when intentional
```

Desktop rules:

```text
use side panels only when they clarify the flow
do not turn evidence into dense tables
keep result and evidence visually connected
```

Multilingual rules:

```text
zh / en / ko must be designed together
Korean length must be tested
English wrapping must be tested
labels must not assume fixed width
buttons must support longer translations
```

V19 must not rely on V18 components.

## 7. Main Interaction Flow

```text
1. User opens /oracle.
2. User enters birth information.
3. System generates basic chart structure.
4. System displays Core / Inference summary.
5. User selects a supported prediction theme.
6. System guides the question.
7. System produces a Contract-backed result.
8. System displays result, evidence, risk, and uncertainty.
9. User submits feedback.
10. System records feedback as learning signal.
11. User can replay the result.
```

The product should teach the user:

```text
chart structure first
prediction second
explanation third
feedback and replay always available
```

## 8. Result Presentation Model

A V19 result should display:

```text
summary
confidence
evidence preview
risk
uncertainty
verifier status
feedback action
replay action
```

It should not display:

```text
raw rule internals by default
raw LLM text
uncited claims
unsupported theme expansion
```

Mobile result order:

```text
1. Core result summary
2. Why this result exists
3. Evidence preview
4. Risk and uncertainty
5. Feedback
6. Replay
7. Technical details collapsed
```

## 9. Explicit Deprecations

The following are deprecated for V19 Experience:

```text
/demo as product center
V18 LandingDemoExperience
V18 Oracle UI
V18 Replay Share UI
V18 frontend experience structure
wealth-first product framing
demo-first product framing
```

The following may be retained as reference only:

```text
V18 backend APIs
V18 Contract / Verifier / Ledger ideas
V18 Replay concept
V18 Trust Metrics concept
V18 Feedback concept
```

V18 UI should not be patched into V19 UI.

V19 Experience should be designed from zero.

## 10. Current Boundary

This document is product design only.

It does not implement UI code.

It does not connect APIs.

It does not change backend behavior.

It does not change V19 Core, Inference, Mapping Registry, or Synthetic Validation.

The next step after this document is:

```text
V19 page-level UX wireframe
```

Only after wireframe approval should component implementation begin.
