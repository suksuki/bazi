# V19 P7 Rule Revision Proposal Workflow

Date: 2026-04-29
System: V19 Standalone Agent Lab
Status: implemented as governance workflow skeleton

## Purpose

P7 turns rule impact mapping into a governed revision proposal workflow.

The goal is not to add prediction capability. The goal is to make feedback traceable into a proposed rule revision that can be validated and reviewed before any future rule activation work.

```text
Agent output
-> signal_evidence
-> user / analyst feedback
-> rule impact mapping
-> revision proposal
-> synthetic validation
-> analyst/admin approval
-> active revision record
```

## Scope Lock

P7 is proposal workflow only.

Allowed:

```text
feedback -> proposal
proposal -> synthetic validation
proposal -> analyst/admin approval
approval -> active revision record
```

Forbidden:

```text
feedback -> automatic rule mutation
proposal -> runtime inference mutation
validation -> automatic activation
approval -> hidden code change
LLM -> rule editing
```

## State Machine

```text
draft
-> validation_passed | validation_failed
-> approved
-> active_revision_record
```

`active_revision_record` is a governance record only. It does not modify active runtime rules.

## API Surface

```text
POST /api/lab/revisions
GET /api/lab/revisions
POST /api/lab/revisions/{revision_id}/validate
POST /api/lab/revisions/{revision_id}/approve
POST /api/lab/revisions/{revision_id}/activate
GET /api/lab/active-revisions
```

## Data Contract

Revision proposal fields:

```ts
type RuleRevisionProposal = {
  revision_id: string
  status: 'draft' | 'validation_passed' | 'validation_failed' | 'approved' | 'active_revision_record'
  source_rule_impact_ids: string[]
  target_rule_id: string
  target_signal: string
  current_version: number
  proposed_version: number
  proposal: string
  rationale: string
  proposed_by_role: string
  validation_run_id?: string
  validation_summary?: {
    passed: number
    failed: number
    case_count: number
  }
  approved_by_role?: string
  approval_note?: string
}
```

Active revision record fields:

```ts
type ActiveRevisionRecord = {
  revision_id: string
  target_rule_id: string
  target_signal: string
  proposed_version: number
  activated_by_role: 'analyst' | 'admin'
  activation_note: string
  runtime_mutation: false
}
```

## Guardrails

Feedback cannot automatically change rules.

Only `analyst` and `admin` roles can approve or record active revisions.

A proposal must pass synthetic validation before approval.

A proposal must be approved before it can be recorded as active.

Recording an active revision does not mutate runtime inference code or active rule behavior.

## UI

Admin page adds:

```text
Rule Revision Proposal Workflow
```

It supports:

```text
create proposal
validate proposal
approve proposal
record active revision
view active revision records
```

The UI explicitly labels the workflow as:

```text
proposal only
validation required
no runtime mutation
```

## Current Readiness

This completes the governance skeleton needed for a future self-evolving Bazi agent system.

It does not make V19 a public prediction product.

Current status remains:

```text
analyst review lab
not production fortune prediction
```
