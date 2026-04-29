# V19 P12 Controlled Promotion Pipeline

## Goal

P12 connects synthetic-collision failures to a controlled promotion pipeline. It does not add automatic learning. The system can prepare proposals, but every promotion still requires analyst/admin review and synthetic regression before any active record is written.

## Pipeline

```text
P11 synthetic failure
-> draft suggestion
-> synthetic promotion candidate
-> analyst/admin review decision
-> downstream proposal ledger
-> proposal validation
-> proposal approval
-> P11 regression gate
-> active/version record only
```

## Review Decisions

Supported decisions:

- `approve`
- `reject`
- `needs_knowledge`
- `needs_rule`
- `needs_expression`

Decision mapping:

- `needs_knowledge` creates a Knowledge Draft.
- `needs_expression` creates an `answer_expression` Knowledge Draft.
- `needs_rule` creates a Bazi Rule Proposal.
- `approve` maps according to the draft type:
  - `knowledge_seed` -> Knowledge Draft
  - `answer_expression` -> Knowledge Draft
  - `rule_draft` -> Bazi Rule Proposal
  - `question_recommendation_draft` -> Guided Question Proposal

All downstream objects remain proposal/draft records. They do not mutate runtime behavior.

## Regression Gate

Active/version record paths now enforce P11 synthetic regression:

- Guided Question Library version record
- Bazi Rule Knowledge version record
- Active Rule Revision record

If the P11 matrix fails, the record call returns `P12_SYNTHETIC_REGRESSION_FAILED`.

Current gate result:

- matrix: `P11_SYNTHETIC_EXPANSION`
- total: 20
- failed: 0
- status: pass

## UI

Admin now includes a Controlled Promotion Queue under the synthetic review area.

The UI supports:

- creating a promotion candidate from a synthetic draft suggestion;
- choosing a review decision;
- submitting the decision;
- showing the downstream proposal/draft created by the decision;
- keeping the P11 regression requirement visible before active/version record.

## Guardrails

- No auto learning
- No auto rule promotion
- No runtime mutation
- Analyst/admin decision required
- P11 regression required before active/version record
