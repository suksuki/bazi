# V40 Phase 53: User Consent Review UI

## Objective

Phase 53 wires the Phase 51/52 consent and practitioner review queue into the user-facing product surface.

The user app remains report-first:

1. Generate the reading report.
2. Show verdict, advice, boundaries, optional probe and follow-up conversation.
3. Only after the report exists, offer a lightweight action to send a desensitized summary to a practitioner.
4. Persist the user grant and review request into V40-owned tables.

This keeps practitioner review as a deliberate user action, not an automatic hidden workflow.

## Scope

Phase 53 includes:

- A small user-side review panel in `/v40/ui` after the report surface.
- A single user action: `授权复核`.
- Two API calls from the user app:
  - `POST /api/v40/consent/grants`
  - `POST /api/v40/practitioner/review-requests`
- Clear visible states:
  - ready to authorize;
  - submitting;
  - submitted;
  - temporarily unavailable.
- Project status updated to Phase 53.
- Focused regression tests proving the UI is wired without leaking internal engineering or Admin concepts.

Phase 53 does not include:

- A practitioner workbench redesign.
- Admin control-plane changes.
- Direct mutation of verdicts, chart facts, runtime weights, V30 state or production weights.
- Silent fallback when the V40 repository is unavailable.

## Product Boundary

The user sees:

```text
命理师复核
如果你想让命理师再看一眼，可以授权发送脱敏摘要。
授权复核
```

The user does not see:

```text
ConsentGrant
AnonymizedCaseView
PractitionerReviewRequest
TrainingLabelEvent
provider / model / prompt / debug / telemetry
Admin control-plane links
```

## Runtime Flow

```text
RuntimeResult
  -> ProductProjectionBundle
  -> /v40/ui report
  -> user clicks 授权复核
  -> create user grant
  -> create practitioner review request from current runtime
  -> persist queue item in qiazhi_v40
  -> practitioner review later produces local training feedback
```

## Safety Boundary

The review UI is only a routing action. It never edits the chart, verdict, advice, signal registry, global weights or V30 data.

If the repository is not available, the UI reports that review queue submission is temporarily unavailable. It must not pretend that a review request has been saved.

## Acceptance

- `/v40/ui` includes the review panel and the two queue endpoints.
- The review panel is hidden before a report and shown after `paintReading`.
- Source and visible copy do not expose internal contract class names or Admin links.
- Project status reports Phase 53 as active.
- Focused tests, visual QA and the full V40 test suite pass.

