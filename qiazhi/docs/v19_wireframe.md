# V19 Page-level UX Wireframe v1

This document turns V19 Product Experience into page-level wireframes.

It is not UI code.

It is not a visual design file.

It defines page structure, user cognition, and interaction order.

## Global Rules

All pages are mobile-first.

Mobile layout:

```text
single column
no horizontal scrolling
large tap targets
collapsed technical detail
2 to 3 evidence items by default
sticky or repeated primary action when useful
```

Desktop layout:

```text
use columns only to clarify the workflow
do not hide the primary action
keep result, evidence, and trust anchors connected
```

Multilingual rule:

```text
All labels must reserve zh / en / ko.
Do not assume fixed label width.
Korean and English must wrap safely.
```

## Shared Label Contract

Any user-facing component must use label objects:

```json
{
  "label": {
    "zh": "...",
    "en": "...",
    "ko": "..."
  }
}
```

## Inference Summary Display Rule

Inference Summary is structural signal display.

It is not Bazi explanation.

Allowed:

```text
Day master state: leaning_strong
Structural stability: unstable
Main conflict: peer_vs_wealth
Energy flow: output -> wealth, weak
Uncertainty: weak_signal
```

Forbidden:

```text
free-form destiny explanation
wealth conclusion
career conclusion
relationship conclusion
health conclusion
useful-god final judgment
```

Inference Summary should display:

```text
signal key
bounded value
source indicator
confidence when available
```

## Result Display Contract

Every prediction result area must include:

```text
summary
confidence
evidence preview
risk
uncertainty
feedback
replay
```

Evidence preview:

```text
show 2 to 3 items by default
expand on demand
never use dense tables on mobile
```

## `/` Visitor Home

Goal:

```text
Help visitors understand that V19 is a verifiable Bazi prediction system.
```

### Mobile Wireframe

[Header]

- title: product name
- content: language switch
- actions: sign in, start oracle

[Hero]

- title: verifiable Bazi prediction system
- content: chart understanding -> verifiable prediction
- actions: start with birth info

[Capability Boundary]

- title: what the system can answer now
- content: supported and unsupported scopes
- actions: start supported flow

[How It Works]

- title: from chart to verified result
- content:
  - birth info
  - Core Bazi Engine
  - Inference signals
  - Contract-backed result
  - Feedback and replay
- actions: none

[Trust Model]

- title: why this is not open-ended AI fortune telling
- content:
  - evidence binding
  - verifier
  - ledger
  - replay
- actions: view sample replay

[Role Entry]

- title: choose your role
- content:
  - visitor
  - user
  - practitioner
  - admin
- actions:
  - enter oracle
  - practitioner login
  - admin login

### Desktop Wireframe

[Top Nav]

- left: brand
- center: product principles
- right: language, login, oracle CTA

[Hero + Trust Diagram]

- left: positioning and CTA
- right: Core -> Inference -> Contract diagram

[Capability + Roles]

- left: supported scope
- right: role cards

[Verification Flow]

- full-width flow:
  - input
  - inference
  - mapping
  - contract
  - verifier
  - replay

## `/oracle`

Goal:

```text
Main user product surface.
```

The page must start with chart structure, not wealth.

## Oracle First Screen Contract

The first screen must answer:

```text
1. What is this system?
2. What can I ask now?
3. What should I do next?
```

### First Screen Required Content

[System Identity]

- title: this is a verifiable Bazi prediction system
- content: the system first understands chart structure, then provides verifiable predictions
- actions: none

[Current Scope]

- title: current supported scope
- content:
  - supported: controlled prediction theme
  - unsupported: full chart general reading, relationship, health
- actions: view supported questions

[Primary CTA]

- title: next step
- content: enter birth information or use sample chart
- actions:
  - enter birth information
  - use sample chart

### Mobile Wireframe

[First Screen]

- section: System Identity
- section: Current Scope
- section: Primary CTA

[Birth Input]

- title: birth information
- content:
  - date
  - time
  - location or timezone if required
  - gender if required by product policy
- actions:
  - generate chart structure
  - save profile if logged in

[Chart Structure Summary]

- title: basic chart structure
- content:
  - four pillars
  - day master
  - visible ten gods summary
  - completeness state
- actions:
  - edit birth info

[Inference Summary]

- title: structure signals
- content:
  - day_master_state
  - ten_god_structure top signals
  - structural_stability
  - internal_conflicts
  - energy_flow
  - uncertainty_sources
- actions:
  - expand signal sources

[Theme Selection]

- title: choose a supported question area
- content:
  - controlled theme card
  - unsupported theme cards disabled
- actions:
  - select supported theme

[Question Guidance]

- title: ask a supported question
- content:
  - recommended question chips
  - capability boundary hint
  - free input field
- actions:
  - submit question

[Contract-backed Result]

- title: result
- content:
  - summary
  - confidence
  - verifier state
- actions:
  - view evidence
  - give feedback
  - replay

[Evidence Preview]

- title: why this result exists
- content:
  - evidence item 1
  - evidence item 2
  - optional evidence item 3
- actions:
  - expand evidence

[Risk and Uncertainty]

- title: risk and uncertainty
- content:
  - risk signals
  - uncertainty signals
  - unsupported scope reminder
- actions: none

[Feedback]

- title: was this useful or accurate?
- content:
  - hit
  - partial
  - miss
  - unclear
- actions:
  - submit feedback

[Replay]

- title: replay this result
- content:
  - replay link
  - prediction_id short form
- actions:
  - copy replay link

### Desktop Wireframe

[Three-column Workspace]

- left: birth input, profile, history
- center: chart structure, inference summary, result
- right: evidence, verifier, replay, feedback

[Sticky State]

- keep current chart status visible
- keep primary action visible

## `/replay`

Goal:

```text
Public-safe trust and verification surface.
```

Replay must feel like a verification document, not a screenshot.

## Replay Trust Anchors

Replay must include:

```text
prediction_id
contract hash
verifier status
evidence summary
redaction status
engine and schema source
```

Source anchors:

```text
Core Bazi Engine version
Inference Schema version
Mapping Registry version
Contract version
Verifier version
```

### Mobile Wireframe

[Replay Header]

- title: verifiable replay
- content:
  - redaction notice
  - public-safe mode
- actions:
  - copy link

[Result Summary]

- title: result
- content:
  - summary
  - confidence
  - verifier status
- actions: none

[Trust Anchors]

- title: what this result is based on
- content:
  - Core Bazi Engine version
  - Inference Schema version
  - Mapping Registry version
  - Contract hash
- actions:
  - expand technical details

[Evidence Summary]

- title: evidence
- content:
  - 2 to 3 evidence items
- actions:
  - expand evidence

[Feedback Summary]

- title: feedback signal
- content:
  - public aggregate only
  - no private user details
- actions:
  - try your own reading

### Desktop Wireframe

[Replay Document]

- left: result and evidence
- right: trust anchors and technical detail

## `/practitioner`

Goal:

```text
Professional review workspace.
```

### Mobile Wireframe

[Practitioner Header]

- title: review workspace
- content:
  - role
  - pending count
- actions:
  - open queue

[Review Queue]

- title: pending reviews
- content:
  - Knowledge Unit
  - Inference signal
  - Mapping Unit
  - Synthetic Validation result
- actions:
  - review item

[Review Detail]

- title: selected item
- content:
  - source
  - expected behavior
  - observed behavior
  - audit trail
- actions:
  - mark correct
  - mark questionable
  - mark wrong
  - propose correction

[Synthetic Validation Review]

- title: validation reports
- content:
  - pass
  - fail
  - warning
  - drift report
  - regression report
- actions:
  - request more cases
  - submit candidate

### Desktop Wireframe

[Review Console]

- left: queue filters
- center: selected review artifact
- right: comments, decision actions, audit trail

## `/admin`

Goal:

```text
Governance and system control.
```

### Mobile Wireframe

[Admin Header]

- title: governance console
- content:
  - system health
  - pending approvals
- actions:
  - view critical queue

[Critical Queue]

- title: items requiring admin decision
- content:
  - rule activation
  - mapping review
  - knowledge lifecycle
  - validation failure
- actions:
  - inspect item

[Lifecycle Panel]

- title: governed lifecycle
- content:
  - Knowledge
  - Candidate
  - Test
  - PR
  - Activate
- actions:
  - approve
  - reject
  - request revision

[Runtime Status]

- title: runtime
- content:
  - PostgreSQL source of truth
  - Redis runtime acceleration
  - audit status
- actions:
  - inspect logs

### Desktop Wireframe

[Governance Dashboard]

- left: lifecycle navigation
- center: active item detail
- right: audit trail, validation status, activation controls

Admin activation must show:

```text
review status
synthetic validation status
practitioner feedback
audit trail
risk warning
```

## Deprecated UI Contract

The following must not be used as the basis for V19 UI:

```text
/demo
V18 LandingDemoExperience
V18 Oracle UI
V18 Replay Share UI
wealth-first result flow
demo-first product framing
```

V18 backend may be used as API reference only.

V19 UI must be designed from the V19 product language.

## Next Step

After this wireframe is accepted:

```text
V19 visual system direction
```

Then:

```text
V19 component architecture
```

Only after both are accepted should UI implementation begin.
