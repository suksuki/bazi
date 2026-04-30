# V19 P50 Guided Answer Evidence Pack

P50 creates a unified evidence pack before guided answers are rendered.

## Goal

Before P50, answer generation read several separate contexts:

- retrieved facts
- applied knowledge
- route-aware knowledge scores
- answer-level rule graph context
- runtime rule graph route pack

P50 combines these into one auditable `evidence_pack`.

## Runtime Output

`guided_question_answer.evidence_pack` includes:

- question and intent metadata
- fact evidence summary
- applied knowledge evidence
- rule graph evidence
- unified evidence bindings
- audit status
- guardrails

`retrieved_facts.evidence_pack` carries a compact summary for UI and audit surfaces.

## Prompt Use

The LLM rewrite path receives a compact evidence pack via `evidence_pack_to_prompt_context`.

The LLM still cannot:

- add new facts
- mutate conclusions
- activate rules
- output prediction text
- expose internal IDs unless explicitly asked for audit

## Boundaries

P50 is context only:

- no inference mutation
- no answer mutation
- no runtime rule activation
- no automatic learning

It makes the answer pipeline easier to audit and prepares the system for later UI review and intelligent approval flows.
