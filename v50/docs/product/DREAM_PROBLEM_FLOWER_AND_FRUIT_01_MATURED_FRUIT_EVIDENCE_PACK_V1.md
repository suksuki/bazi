# DREAM-PROBLEM-FLOWER-AND-FRUIT-01 Matured Fruit Evidence Pack v1

```yaml
status: FROZEN_TEMPLATE
implementation: NOT_AUTHORIZED
first_release_requirement: 3
currently_qualified_by_this_document: 0
content_gate: CLOSED
```

## Purpose

This document defines the intake template and qualification gate for the first three
real matured fruits. It contains no participant data, outcome, birth information,
or implied consent.

A matured fruit is eligible only when a real or reliable historical question can be
reconstructed at a defensible pre-outcome cutoff and its later outcome can be
verified through an auditable evidence chain.

The game must not fill missing fields with model output, operator memory, current
Case state, simulated history, or a plausible story.

## Current Content Gate

| Slot | Required source | Current status | Qualification |
| --- | --- | --- | --- |
| `MATURED-FRUIT-01` | Distinct authorized real or verified historical subject | Empty | `NOT_STARTED` |
| `MATURED-FRUIT-02` | Distinct authorized real or verified historical subject | Empty | `NOT_STARTED` |
| `MATURED-FRUIT-03` | Distinct authorized real or verified historical subject | Empty | `NOT_STARTED` |

Current known exclusions:

- Wulan and Yanzhou are Canonical NPCs but do not have verified real outcome packs.
  Their simulated or canonical-world events cannot enter these three slots.
- Existing Dream display authorization for a human tree does not imply consent to
  use a question, judgment, or outcome in a blind game.
- The old 44 Cases, test fixtures, synthetic residents, and generated examples are
  not eligible merely because they can be rendered by V50.
- A real birth record without an original timed question and verified result is not
  a matured fruit pack.

The first cohort uses three distinct subjects or source histories to avoid presenting
multiple events from one source as independent breadth. Any future relaxation
requires an explicit owner revision.

## Evidence Pack Object

```yaml
MaturedFruitEvidencePack:
  pack_id: private_opaque
  pack_version: integer
  intake_status: DRAFT | QUARANTINED | QUALIFIED | REJECTED | WITHDRAWN

  subject:
    private_subject_ref: private_opaque
    resident_projection_ref: optional_authorized_ref
    subject_kind: AUTHORIZED_HUMAN | VERIFIED_HISTORICAL_RECORD
    canonical_resident_identity_claim: explicit_or_none

  consent:
    consent_record_ref: private_ref
    consent_scope_version: ref
    permitted_uses:
      - blind_round_pre_outcome_projection
      - outcome_reveal_to_authorized_players
      - evaluation
    prohibited_uses:
      - model_training_without_separate_consent
      - public_identity_disclosure
      - npc_memory
      - advertising
    withdrawal_process_ref: ref
    consent_verified_at: timestamp

  deidentification:
    policy_version: ref
    public_alias: neutral_alias
    removed_identifiers_manifest_hash: sha256
    reidentification_risk_review_ref: private_ref
    residual_risk: LOW | UNACCEPTABLE

  original_question:
    source_record_ref: private_ref
    source_type: timestamped_document | message | case_note | other_qualified_record
    source_timestamp: authoritative_or_verified_timestamp
    exact_original_text_private: private_content_ref
    neutral_game_question_ref: versioned_ref
    question_subject_ref: private_ref
    original_context_manifest_hash: sha256
    provenance_review_ref: private_ref

  knowledge_cutoff:
    cutoff_timestamp: timestamp
    cutoff_reason: fixed_text
    pre_cutoff_source_manifest_hash: sha256
    excluded_post_cutoff_manifest_hash: sha256

  pre_outcome_materials:
    birth_facts_ref: exact_version
    lifecase_ref: exact_version
    canonical_scene_ref: exact_version
    timing_refs: [exact_version]
    relation_assertion_refs: [exact_version]
    path_assertion_refs: [exact_version]
    available_question_context_refs: [content_hash_ref]
    knowledge_material_refs: [content_hash_ref]
    missing_materials: [fixed_code]

  outcome_window:
    starts_at: timestamp
    ends_at: timestamp
    target_variable: typed_descriptor
    allowed_outcome_options: [fixed_option]
    resolution_criteria: structured_rules
    ambiguity_policy_version: ref

  outcome_evidence:
    private_evidence_set_ref: private_ref
    evidence_origin: REALITY_FEEDBACK | HISTORICAL_RECORD
    evidence_items: [private_source_ref]
    source_timestamp_range: interval
    chain_of_custody_manifest_hash: sha256
    verifier_refs: [private_authorized_ref]
    verification_status: UNVERIFIED | VERIFIED | DISPUTED | WITHDRAWN
    verification_record_ref: private_ref
    resolved_option_id: fixed_option_ref
    redacted_reveal_projection_ref: content_addressed_ref

  blind_integrity:
    hidden_information_manifest_hash: sha256
    pre_outcome_bundle_hash: sha256
    reveal_bundle_hash: sha256
    causal_firewall_policy_version: ref
    independent_leak_review_ref: private_ref

  policies:
    outcome_resolver_version: ref
    evaluation_policy_version: ref
    reveal_policy_version: ref
    retention_policy_version: ref

  audit:
    curator_ref: private_authorized_ref
    outcome_verifier_ref: private_authorized_ref
    release_approver_ref: private_authorized_ref
    qualified_at: optional_timestamp
    pack_payload_hash: sha256
```

The private subject and evidence fields do not enter the product projection. Public
aliases must not encode profession, location, employer, family structure, or outcome.

## Qualification Checklist

Every item is mandatory unless explicitly marked not applicable by the policy and
reviewed as such.

### A. Consent And Subject Rights

- [ ] The subject or lawful data authority explicitly permits this blind-round use.
- [ ] Dream display consent, ordinary Case use, and blind-game evidence use are
      recorded as separate scopes.
- [ ] Reveal scope and expected viewer audience are understandable to the subject.
- [ ] Withdrawal and deletion behavior are documented.
- [ ] Model training is excluded unless separately and explicitly authorized.
- [ ] The public alias and reveal materials pass reidentification-risk review.
- [ ] Consent is valid at qualification and will be rechecked at publication and
      reveal.

### B. Original Question

- [ ] An original question record exists; it is not reconstructed from memory alone.
- [ ] Its timestamp and custody are verifiable.
- [ ] The subject and target variable are unambiguous.
- [ ] A neutral game rendering preserves meaning without leaking the result.
- [ ] The original question predates the outcome window or is explicitly classified
      under an approved retrospective-unknown protocol.
- [ ] The question was not selected solely because the answer produced an impressive
      story without a documented sampling rule.

### C. Pre-Outcome Knowledge Cutoff

- [ ] `knowledge_cutoff` is explicit and precedes all excluded result knowledge.
- [ ] Birth facts, LifeCase, Canonical Scene, timing, relations, paths, and knowledge
      materials are frozen to exact versions available at cutoff.
- [ ] No `latest`, current tree state, current OneCanvas state, or post-outcome
      corrected record is referenced.
- [ ] Missing pre-outcome materials are disclosed rather than backfilled.
- [ ] The complete pre-outcome bundle can be rebuilt from its manifest and hashes.

### D. Outcome Window And Resolver

- [ ] The window has fixed start and end boundaries.
- [ ] Outcome options are mutually understandable and cover the approved question.
- [ ] The resolver can determine an option without post-hoc semantic expansion.
- [ ] Ambiguous, partial, delayed, or canceled outcomes have frozen handling rules.
- [ ] The evaluation policy was frozen before round publication.
- [ ] Health, death, vague improvement, and unbounded subjective outcomes are absent
      from the first cohort.

### E. Outcome Evidence

- [ ] Evidence is original or traceable to a reliable source.
- [ ] Evidence timestamps fit the declared outcome window and resolution criteria.
- [ ] The chain of custody is documented.
- [ ] At least one authorized verifier confirms the resolved option and limitations.
- [ ] Conflicts, missing periods, or contrary evidence are preserved and reviewed.
- [ ] Verification status is `VERIFIED`, not merely plausible or operator-approved.
- [ ] The redacted reveal projection proves only what the evidence supports.

### F. Blind Isolation

- [ ] Pre-outcome and reveal bundles are separately stored and authorized.
- [ ] Pre-outcome APIs, client assets, DOM, Canvas, ARIA, caches, logs, analytics, and
      model context contain no outcome value or reveal side channel.
- [ ] File names, sizes, resource counts, ordering, colors, aliases, and timings do not
      encode the answer.
- [ ] The system judgment uses only the pre-outcome manifest.
- [ ] An independent leak review attempts to infer the answer from the full blind
      client and fails.
- [ ] The system seal exists before publication.

### G. Evidence Classification

- [ ] `evidence_class` is `VERIFIED_REAL` or `HISTORICAL_VERIFIED`.
- [ ] `judgment_temporality` is explicitly `RETROSPECTIVE_BLIND` for matured fruit.
- [ ] The pack is not a simulation, canonical-world event, synthetic fixture, or
      model-generated biography.
- [ ] This pack will not be merged into prospective-forecast accuracy statistics.

### H. Publication Readiness

- [ ] All exact object versions and hashes are recorded.
- [ ] No production projection contains private source references.
- [ ] Required disclosure copy is approved.
- [ ] Withdrawal has been tested as a fail-closed operation.
- [ ] Round publication can be reversed without editing sealed judgments.
- [ ] Curator, verifier, and release approver have signed the qualification record.

Any unchecked item keeps the pack in `DRAFT`, `QUARANTINED`, or `REJECTED`. There is
no partial qualification.

## Three Required Pack Templates

The following slots are intentionally empty. They are not examples and must not be
populated in this document with personal information.

### MATURED-FRUIT-01

```yaml
slot_id: MATURED-FRUIT-01
status: NOT_STARTED
preferred_event_family: JOB_CHANGE
subject_ref: null
question_record_ref: null
knowledge_cutoff: null
pre_outcome_bundle_hash: null
outcome_window: null
verified_evidence_ref: null
qualification_record_ref: null
round_id: null
```

### MATURED-FRUIT-02

```yaml
slot_id: MATURED-FRUIT-02
status: NOT_STARTED
preferred_event_family: CONTRACT_SIGNING
subject_ref: null
question_record_ref: null
knowledge_cutoff: null
pre_outcome_bundle_hash: null
outcome_window: null
verified_evidence_ref: null
qualification_record_ref: null
round_id: null
```

### MATURED-FRUIT-03

```yaml
slot_id: MATURED-FRUIT-03
status: NOT_STARTED
preferred_event_family: RELOCATION_OR_TRAVEL
subject_ref: null
question_record_ref: null
knowledge_cutoff: null
pre_outcome_bundle_hash: null
outcome_window: null
verified_evidence_ref: null
qualification_record_ref: null
round_id: null
```

The preferred event family is a content-balancing target, not permission to force an
available record into that category. If a slot lacks a qualified source, it remains
empty.

## Pack Construction Workflow

```text
private intake
-> consent and identity authority check
-> original question provenance check
-> freeze target variable, window, resolver, and knowledge_cutoff
-> inventory exact pre-cutoff materials
-> isolate all outcome and post-cutoff materials
-> build content-addressed pre-outcome bundle
-> build separately protected reveal bundle
-> generate and seal system judgment from blind bundle
-> independent client and model-context leak review
-> verify evidence and redacted reveal projection
-> approve pack
-> publish round
```

The outcome curator and pre-outcome/system-judgment operator should be separated in
access wherever practical. At minimum, the system-judgment execution identity must
have no read capability for the reveal bundle.

## Pre-Outcome Bundle

The bundle may contain only:

- the neutral question and fixed options;
- source facts and context demonstrably available by cutoff;
- exact pre-cutoff LifeCase and Canonical Scene references;
- authorized Dream tree and OneCanvas projection inputs;
- allowed NodeRefs, RelationKeys, and existing assertion references;
- knowledge and model manifests used by the system judgment;
- policies required to understand the task.

It must not contain redacted placeholders whose count, length, path, or key reveals
the answer.

## Reveal Bundle

The bundle remains inaccessible before valid dual sealing. It contains:

- private source evidence under custodian access;
- the frozen resolved option;
- verification and chain-of-custody records;
- contrary or limiting evidence;
- a separately generated redacted reveal projection;
- consent, withdrawal, resolver, and evaluation policy references.

The client receives only the authorized redacted projection after a reveal record is
created. It never receives the private evidence bundle.

## Withdrawal And Deletion

Withdrawal must:

1. change evidence and publication status through an append-only record;
2. revoke all active projection and reveal capabilities;
3. remove the round from selection immediately;
4. prevent cached evidence from reopening;
5. delete, de-identify, or seal personal content according to policy;
6. retain only a content-free integrity proof when permitted;
7. preserve the fact that prior seals existed without retaining withdrawn personal
   content beyond authorization.

The system does not preserve emotional residue, relationship weight, NPC memory, or
a hidden summary of the withdrawn content by default.

## Qualification Decision

The template and gate are complete. No real pack is asserted or implied.

```yaml
MATURED_FRUIT_CONTENT_GATE:
  required: 3
  qualified: 0
  blocked_reason: NO_THREE_VERIFIED_AUTHORIZED_PACKS
  design_freeze_impact: NONE
  implementation_and_release_impact: BLOCKING
```
