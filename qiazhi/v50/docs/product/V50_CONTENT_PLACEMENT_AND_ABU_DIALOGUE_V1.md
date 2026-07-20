# V50 Content Placement and Abu Dialogue v1

Status: current product contract

## Purpose

DeepBazi is an Abu-led Mingli cognition product, not an engineering dashboard and not an unbounded chat window. Every visible item has one owner.

## Task Canvas

The canvas owns durable content the user may compare, revisit or act on:

- whole-chart pattern and personal portrait;
- Bazi long-term structure and Ziwei life-stage lens;
- one selected life-domain causal reading;
- supporting conditions, failure conditions and uncertainty;
- the active Probe and the resulting case revision;
- professional hypotheses, evidence and deliberation only for authorized roles.

The canvas never shows model parameters, storage state, internal identifiers, raw prompts, contract names, debug traces or validation scores.

## Abu Dialogue

Abu owns short-lived guidance and one-step interaction:

- welcome and birth-information intake;
- explain what the current canvas means;
- state what is missing and ask one high-value question;
- introduce a Probe and explain why it matters;
- acknowledge a case-level revision;
- explain a capability or safety boundary;
- navigate to an action already authorized by the product runtime.

Abu may converse through the LLM, but it cannot invent a capability, alter chart facts, bypass Epistemic Review, or create a second competing page action.

## Chart Context

The header capsule and archive sheet own identity and continuity:

- selected profile and four pillars;
- signed-in account and active role;
- saved profiles and restorable cases.

They do not carry the main judgment, Probe or next action.

## Hidden System Data

The following remain hidden from Guest and Member surfaces:

- Graph/Path internals and raw Mechanism representations;
- raw competing-hypothesis and evidence ledgers;
- review diagnostics, prompt payloads and model telemetry;
- storage keys, cache state and version diagnostics;
- raw birth data in analytics and UX reports.

Practitioner and Research modes may expose reviewed professional structures, never infrastructure diagnostics or secrets.

## Placement Rule

```text
Must compare, revisit or act on it? -> Task Canvas
Temporary explanation or one question? -> Abu Dialogue
Identifies chart, account or continuity? -> Chart Context
Only useful for implementation or audit? -> Hidden
```

No field may appear on two surfaces unless accessibility requires a second representation.

## Progressive Rhythm

```text
Birth intake and confirmation
-> Whole-chart cognition
-> Bazi / Ziwei lenses
-> One life-domain question
-> One discriminating Probe
-> Case-level revision
-> Continue or close
```

The product does not render all domains, all evidence and all professional detail at once.

## Acceptance

- A user can state the current task without knowing system terminology.
- One primary action is visible for the current step.
- Abu explains or navigates without duplicating that action.
- Guest and Member pages contain no professional audit language.
- Probe feedback changes only allowed case beliefs.
- Login, profiles and cases remain durable through PostgreSQL.

