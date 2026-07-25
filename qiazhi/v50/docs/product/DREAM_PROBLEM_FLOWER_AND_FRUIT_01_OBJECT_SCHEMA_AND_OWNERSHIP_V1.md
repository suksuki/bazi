# DREAM-PROBLEM-FLOWER-AND-FRUIT-01 Object Schema And Ownership v1

```yaml
status: FROZEN_DESIGN_CONTRACT
implementation: NOT_AUTHORIZED
schema_kind: LOGICAL_PRODUCT_SCHEMA
runtime_schema_change: NONE
database_migration: NONE
```

## Purpose

This document defines the logical objects, unique owners, immutability rules, and
data-plane boundaries for the first Problem Flower and Fruit game. It is an
implementation contract, not a runtime schema or migration.

The governing rule is:

> One object has one authoritative owner; a projection may disclose it, but may not
> recreate, reinterpret, or promote it.

## Owner Map

| Object | Unique owner | Mutable after commit | Forbidden owners |
| --- | --- | --- | --- |
| `ProblemQuestionRecord` | Blind Round Service | No; supersede by version | Dream UI, OneCanvas, LLM |
| `BlindRoundDefinition` | Blind Round Service | No; withdraw or supersede | Client, Outcome UI |
| `PreOutcomeInputManifest` | Blind Round Publication Service | No | Client, model runtime |
| `PreOutcomeDreamProjection` | Dream Projection Compiler | No; expires | Browser, tree renderer |
| `DivinationRecord` | Liuyao Command Service | No | Flower UI, client clock |
| `JudgmentSubmission` | Judgment Service | No after user seal | Client storage, LLM |
| `UserPathHypothesis` | Judgment Service | No after user seal | LifeCase, Path Engine |
| `UserJudgmentSeal` | Seal Vault | No | Browser, evaluation code |
| `SystemJudgmentSeal` | Seal Vault | No | Player session, reveal UI |
| `OutcomeEvidence` | Outcome Evidence Service | Append verification records only | Blind Round Service, Dream client |
| `OutcomeBindingRecord` | Outcome Evidence Service | No; withdraw/supersede | Pre-outcome projection |
| `OutcomeRevealRecord` | Reveal Service | No | Client, evaluation UI |
| `EvaluationRecord` | Evaluation Service | No; new policy creates new record | LLM narration, client |
| `KnowledgeSeed` | Viewer Knowledge Ledger | User may append a new revision; history retained | LifeCase, NPC Mind, V50 assertions |
| `PathAdmissionReview` | V50 formal review owner | Append-only lifecycle | Game, Dream UI |
| formal `PathAssertion` | existing LifeCase relation/path owner | Existing CAG-04 lifecycle | Game, player submission |

No new Dream-owned Case, relation graph, path model, evidence ledger, Liuyao engine,
or outcome truth store is permitted.

## Identity, Versioning, And Hashing

All committed objects require:

```yaml
id: opaque_service_owned_identifier
schema_version: explicit
object_version: monotonic_within_identity
created_at: authoritative_server_time
created_by: service_or_actor_ref
payload_hash: sha256_of_canonical_payload
status: object_specific_lifecycle
```

Canonical hashing rules are implementation-independent:

- UTF-8 encoding;
- Unicode normalization fixed by policy;
- object keys sorted;
- timestamps normalized to UTC integer ticks;
- no floating-point confidence values in the signed payload; use an integer basis
  such as `confidence_basis_points`;
- absent and null are distinct and defined per schema;
- server-generated IDs, mutable display copy, and transport envelopes are excluded
  unless explicitly part of the commitment;
- arrays whose order is semantic retain order; sets are normalized before hashing.

Seal hashes are domain-separated. A user seal cannot be replayed as a system seal,
and a simulation seal cannot be replayed as a real-evidence seal.

## Core Objects

### ProblemQuestionRecord

The question is a formal, versioned game object. The flower is only its authorized
projection.

```yaml
ProblemQuestionRecord:
  question_id: opaque
  question_version: integer
  resident_lifecase_ref: versioned_ref
  neutral_question_text: string
  knowledge_cutoff: authoritative_timestamp
  outcome_options:
    - option_id
    - fixed_label
  target_variable: typed_descriptor
  authorized_known_context_ref: content_addressed_pre_cutoff_ref
  outcome_window:
    starts_at: timestamp_or_world_time
    ends_at: timestamp_or_world_time
  resolution_criteria: fixed_structured_rules
  disconfirmation_definition: fixed_text_or_rules
  liuyao_policy:
    permitted: boolean
    mode: RETROSPECTIVE_BLIND | PROSPECTIVE
  evaluation_policy_version: ref
  outcome_resolver_version: ref
  source_authorization_ref: opaque
  payload_hash: sha256
```

The question text cannot contain the answer, post-outcome wording, evaluative tone,
or hints derived from the evidence.

### BlindRoundDefinition

```yaml
BlindRoundDefinition:
  round_id: opaque
  round_version: integer
  mode: MATURED_FRUIT_IMMEDIATE_REVEAL | LIVE_FRUIT_REAL_WAITING
  evidence_class: VERIFIED_REAL | HISTORICAL_VERIFIED
  judgment_temporality: RETROSPECTIVE_BLIND | PROSPECTIVE_PREOUTCOME
  resident_ref: canonical_resident_ref
  question_ref: versioned_ref
  knowledge_cutoff: authoritative_timestamp
  pre_outcome_input_manifest_hash: sha256
  pre_outcome_projection_policy_version: ref
  system_judgment_seal_ref: sealed_opaque_ref
  system_judgment_commitment_hash: sha256
  system_sealed_at: authoritative_timestamp
  publication_state: DRAFT | QUALIFIED | PUBLISHED | WITHDRAWN
  published_at: authoritative_timestamp
  viewer_eligibility_policy_version: ref
  reveal_policy_version: ref
  payload_hash: sha256
```

The round object contains no outcome value, evidence document identifier, outcome
summary, post-outcome Case reference, or reveal decryption material. The reveal
domain stores the private binding separately.

Publication must reject a round when:

- `system_sealed_at >= published_at`;
- a system seal was generated after any player's first access;
- the pre-outcome input manifest cannot be reproduced;
- evidence qualification or consent is missing;
- the evidence class is simulated, synthetic, unverified, disputed, or withdrawn.

### PreOutcomeInputManifest

```yaml
PreOutcomeInputManifest:
  manifest_id: opaque
  round_id: opaque
  knowledge_cutoff: timestamp
  lifecase_ref: versioned_ref
  birth_facts_ref: versioned_ref
  canonical_scene_ref: versioned_ref
  dream_projection_source_ref: versioned_ref
  onecanvas_coordinate_version: ref
  timing_refs: [versioned_ref]
  relation_assertion_refs: [versioned_ref]
  path_assertion_refs: [versioned_ref]
  knowledge_material_refs: [content_hash_ref]
  model_version: ref_or_none
  prompt_version: ref_or_none
  rule_versions: [ref]
  hidden_information_manifest_hash: sha256
  causal_firewall_policy_version: ref
  causal_dependency_manifest_hash: sha256
  payload_hash: sha256
```

Every referenced object must have an effective time at or before `knowledge_cutoff`.
The manifest cannot reference a current-state alias such as `latest`.

`hidden_information_manifest_hash` proves which information was isolated; it does
not disclose the information itself.

### PreOutcomeDreamProjection

```yaml
PreOutcomeDreamProjection:
  projection_ref: opaque_short_lived_capability
  round_id: opaque
  viewer_ref: scoped_ref
  case_namespace: opaque_scoped_namespace
  resident_ref: canonical_resident_ref
  authorization_version: ref
  knowledge_cutoff: timestamp
  source_manifest_hash: sha256
  tree_projection_ref: content_addressed_ref
  onecanvas_view_ref: opaque
  problem_flower_projection_ref: opaque
  allowed_lenses: subset_of_existing_six
  expires_at: timestamp
  projection_hash: sha256
```

The transport representation must omit, rather than null out:

- outcome fields and options marked as correct;
- evidence identifiers, filenames, URLs, sizes, and timestamps after cutoff;
- evaluation results;
- reveal tokens or storage keys;
- post-cutoff Case, timing, relation, path, tree, or narrative data;
- system judgment payload, confidence, or explanation;
- hidden accessibility labels, tooltips, source maps, debug data, or analytics fields
  that imply the outcome.

The browser cannot derive another projection by modifying IDs or query parameters.

### DivinationRecord

```yaml
DivinationRecord:
  divination_id: opaque
  round_id: opaque
  question_ref: exact_version
  exact_question: immutable_text
  subject_ref: scoped_ref
  viewer_ref: scoped_ref
  explicit_user_intent: true
  trigger_mode: EXPLICIT_USER_ACTION
  divination_temporality: RETROSPECTIVE_BLIND | PROSPECTIVE
  cast_at_server_time: timestamp
  timezone_policy_version: ref
  casting_method_version: ref
  casting_method_parameters: typed_payload
  casting_entropy_commitment: sha256
  canonical_hexagram_payload: typed_liuyao_payload
  authorization_ref: exact_version
  outcome_access_state_at_cast: UNREVEALED
  idempotency_key_hash: sha256
  payload_hash: sha256
```

#### Liuyao Boundary

For `MATURED_FRUIT_IMMEDIATE_REVEAL`, the event has already occurred but remains
unknown to the player and isolated from the cast. The record is therefore
`RETROSPECTIVE_BLIND`. It may inform the player's blind inference, but it must not be
reported as a prospective forecast made before the event.

For future `LIVE_FRUIT_REAL_WAITING`, a cast made before the frozen outcome window
closes may be `PROSPECTIVE`.

The same accuracy dashboard, evidence label, or training cohort must never combine
these temporalities without explicit stratification.

Opening the flower, reading the question, touching a tree, entering OneCanvas,
waiting, scrolling, or confirming a Bazi judgment cannot create a DivinationRecord.
The server owns the cast timestamp and immutable payload. A duplicate identical
request returns the same record; a changed question binding is rejected.

Liuyao does not modify Bazi facts, RelationAssertions, PathAssertions, the resident's
tree, or the outcome. It is a separately labeled observation channel in the user's
seal.

### UserPathHypothesis

```yaml
UserPathHypothesis:
  hypothesis_id: opaque
  ordered_segments:
    - source_node_ref
    - target_node_ref
    - relation_key_or_assertion_ref
    - player_interpretation
  competing_hypothesis_text: string
  disconfirmation_condition: string
  source_projection_hash: sha256
  formal_status: USER_HYPOTHESIS_ONLY
```

References must belong to the round's authorized pre-outcome manifest. The client
cannot invent NodeRefs or RelationKeys. A missing or invalid segment is rejected or
removed before the user confirms; it is never repaired by guessing.

The object cannot use lifecycle terms such as `candidate`, `committed`, or
`effective` in a way that suggests formal V50 status.

### JudgmentSubmission

```yaml
JudgmentSubmission:
  submission_id: opaque
  round_id: opaque
  viewer_ref: scoped_ref
  selected_outcome_option_id: fixed_option_ref
  confidence_basis_points: integer_0_to_10000
  evidence_refs: [pre_outcome_authorized_ref]
  user_path_hypothesis_ref: optional_ref
  strongest_alternative: string
  disconfirmation_condition: string
  divination_ref: optional_ref
  pre_outcome_projection_hash: sha256
  pre_outcome_input_manifest_hash: sha256
  client_draft_started_at: audit_only_timestamp
  committed_at: authoritative_server_time
  payload_hash: sha256
```

Drafts are local convenience state and have no evidentiary authority. The committed
submission is immutable.

### UserJudgmentSeal

```yaml
UserJudgmentSeal:
  seal_id: opaque
  seal_type: USER_JUDGMENT
  round_id: opaque
  submission_ref: immutable_ref
  submission_payload_hash: sha256
  pre_outcome_projection_hash: sha256
  evidence_refs_hash: sha256
  commitment_hash: domain_separated_sha256
  created_at: authoritative_server_time
  sealed_at: authoritative_server_time
  first_access_sequence: server_sequence
  seal_state: SEALED | REVEALED | WITHDRAWN_CONTENT_PROOF_RETAINED
```

An identical idempotent retry returns this seal. Any changed payload after commit is
rejected. Withdrawal may remove personal content according to privacy policy while
retaining only the permitted integrity proof; it cannot rewrite history into a
different judgment.

The committed seal payload includes the round and projection hash, selected result,
confidence, complete `UserPathHypothesis` or its immutable hash, authorized
`evidence_refs`, disconfirmation condition, and authoritative creation time. The
`submission_ref` is an envelope boundary, not permission to omit these values from
the commitment.

### SystemJudgmentSeal

```yaml
SystemJudgmentSeal:
  seal_id: opaque
  seal_type: SYSTEM_JUDGMENT
  round_id: opaque
  selected_outcome_option_id: fixed_option_ref
  confidence_basis_points: integer_0_to_10000
  formal_path_assertion_refs: [exact_pre_cutoff_ref]
  candidate_path_refs: [exact_pre_cutoff_ref]
  system_path_hypothesis: optional_nonformal_hypothesis
  strongest_alternative: string
  disconfirmation_condition: string
  input_manifest_hash: sha256
  pre_outcome_projection_hash: sha256
  model_version: ref_or_none
  prompt_version: ref_or_none
  reasoner_version: ref_or_none
  knowledge_versions: [ref]
  producer_version: ref
  generation_started_at: authoritative_timestamp
  generated_at: authoritative_timestamp
  sealed_at: authoritative_timestamp
  commitment_hash: domain_separated_sha256
  seal_state: SEALED | REVEALED | WITHDRAWN
```

The system input context cannot contain:

- player identity beyond the minimum round-scoped capability;
- player observation telemetry, navigation, draft, choice, confidence, hypothesis,
  alternative, falsifier, or Liuyao result;
- outcome evidence, outcome value, post-cutoff source, reveal summary, or evaluation;
- another system run generated after player access.

The system seal must exist before publication. It cannot be generated on first play,
after the user's seal, or after a reveal failure. The first mode therefore measures
retrospective blind inference, not a prospective forecast made before the event.

### OutcomeBindingRecord

The reveal domain privately binds a round to qualified evidence:

```yaml
OutcomeBindingRecord:
  binding_id: private_opaque
  round_id: opaque
  evidence_pack_ref: private_versioned_ref
  evidence_commitment_hash: sha256
  evidence_class: VERIFIED_REAL | HISTORICAL_VERIFIED
  verification_status: VERIFIED | DISPUTED | WITHDRAWN
  qualification_record_ref: private_ref
  reveal_policy_version: ref
  created_at: timestamp
  payload_hash: sha256
```

This object is never serialized into a pre-outcome response. The Blind Round Service
may ask only whether a round is reveal-eligible; it cannot read evidence content.

### OutcomeEvidence

```yaml
OutcomeEvidence:
  evidence_id: private_opaque
  evidence_version: integer
  evidence_origin: REALITY_FEEDBACK | HISTORICAL_RECORD
  verification_status: UNVERIFIED | VERIFIED | DISPUTED | WITHDRAWN
  target_variable: typed_descriptor
  resolved_option_id: fixed_option_ref
  outcome_window: frozen_window
  occurred_at_or_interval: timestamp_or_interval
  evidence_items: [private_source_record]
  custodian_ref: private_ref
  verification_record_refs: [private_ref]
  consent_and_disclosure_ref: private_ref
  redacted_reveal_projection_ref: content_addressed_ref
  payload_hash: sha256
```

Evidence content remains in the reveal domain. The game receives a redacted,
viewer-authorized reveal projection only after authorization.

### OutcomeRevealRecord

```yaml
OutcomeRevealRecord:
  reveal_id: opaque
  round_id: opaque
  viewer_ref: scoped_ref
  user_seal_ref: immutable_ref
  system_seal_ref: immutable_ref
  evidence_version: exact_version
  redacted_evidence_projection_hash: sha256
  reveal_authorization_version: ref
  revealed_at: authoritative_server_time
  idempotency_key_hash: sha256
  payload_hash: sha256
```

Reveal requires both valid seals, current evidence qualification, current disclosure
authorization, and an unopened viewer-round pair. An identical retry returns the
same record.

### EvaluationRecord

```yaml
EvaluationRecord:
  evaluation_id: opaque
  round_id: opaque
  user_seal_ref: immutable_ref
  system_seal_ref: immutable_ref
  reveal_ref: immutable_ref
  outcome_resolver_version: exact_ref
  evaluation_policy_version: exact_ref
  user_result:
    option_match: true | false | unscorable
    confidence_bucket: fixed_bucket
    hypothesis_review_state: NOT_FORMALLY_REVIEWED
    formal_evidence_support: SUPPORTED | UNSUPPORTED | PARTIAL | NOT_REVIEWED
    decisive_node_omissions: [authorized_node_ref]
    disconfirmation_condition_quality: VALID | INVALID | UNREVIEWED
  system_result:
    option_match: true | false | unscorable
    confidence_bucket: fixed_bucket
    hypothesis_review_state: NOT_FORMALLY_REVIEWED
    formal_evidence_support: SUPPORTED | UNSUPPORTED | PARTIAL | NOT_REVIEWED
    decisive_node_omissions: [authorized_node_ref]
    disconfirmation_condition_quality: VALID | INVALID | UNREVIEWED
  divergence:
    outcome_choice_differs: boolean
    confidence_gap_basis_points: integer
    path_reference_overlap: fixed_metric_or_unreviewed
    strongest_disagreement_codes: [fixed_code]
  evidence_scope_statement: fixed_copy_ref
  limitations: [fixed_code]
  evaluated_at: authoritative_server_time
  payload_hash: sha256
```

Evaluation is deterministic under a frozen policy. It cannot use an LLM to rescue,
reinterpret, or rescore an answer after reveal. A new policy creates a new record
that references the prior one; it does not overwrite it.

### KnowledgeSeed

```yaml
KnowledgeSeed:
  seed_id: opaque
  viewer_ref: private_ref
  round_id: opaque
  evaluation_ref: immutable_ref
  issued_calibration_summary: approved_fixed_copy_and_refs
  observation_kept: fixed_refs
  missed_or_overweighted: fixed_refs
  applicable_boundary: approved_fixed_copy
  viewer_reflection_revision_ref: optional_private_ref
  seed_status: PRIVATE_LEARNING_RECORD
  created_at: timestamp
  payload_hash: sha256
```

It is excluded from:

- LifeCase and Canonical Scene;
- resident or Abu canonical memory;
- formal RelationAssertion and PathAssertion;
- world settlement and tree growth;
- rewards, ranks, matchmaking, and evidence counts;
- model training unless a later, separate consent and data-governance process
  explicitly qualifies it.

### PathAdmissionReview

```yaml
PathAdmissionReview:
  review_id: opaque
  source_user_hypothesis_ref: immutable_ref
  source_system_hypothesis_ref: optional_immutable_ref
  source_evaluation_ref: immutable_ref
  formal_scene_ref: exact_version
  review_policy_version: ref
  reviewer_or_process_ref: authorized_ref
  deterministic_reference_validation: PASS | FAIL
  professional_qualification: PENDING | PASS | FAIL
  decision: REJECTED | RESEARCH_ONLY | PATH_ASSERTION_CANDIDATE
  resulting_path_assertion_ref: optional_new_ref
  created_at: timestamp
  payload_hash: sha256
```

Only a separate V50 review may create a new formal assertion. The game cannot call
this process automatically, and a correct outcome choice does not prove that the
player's proposed mechanism was correct.

Any resulting new `PathAssertion` must carry `source_submission_ref`,
`review_record_ref`, reviewer or authorized process identity, review policy and
producer versions, and its own creation timestamp. A rejected, competing, or
insufficiently supported hypothesis remains in the non-formal hypothesis/review
record and is never upgraded in place.

## Independent Dual-Seal Protocol

### Publication Side

```text
freeze pre-outcome input manifest
-> run system judgment in isolated context
-> seal system payload
-> register commitment hash
-> qualify evidence in separate reveal domain
-> publish round
```

### Player Side

```text
load pre-outcome projection
-> optional explicit Liuyao cast
-> draft player judgment locally
-> commit immutable submission
-> seal user payload
-> validate pre-existing system seal and independence
-> request reveal
```

### Required Independence Proofs

- The system seal timestamp predates publication and all player access.
- The system input manifest hash equals the publication manifest hash.
- The user input projection hash equals the published pre-outcome projection hash.
- The system causal dependency manifest contains no player-session dependency.
- The system and user seal services write separate immutable records.
- The reveal domain cannot alter either payload.
- An operator correction creates a withdrawal/supersession record; it cannot edit a
  commitment.

## Data-Plane Separation

At minimum, the design requires three access domains:

```text
PRE_OUTCOME DOMAIN
  round metadata, cutoff manifests, authorized Dream/OneCanvas projection

SEALED JUDGMENT DOMAIN
  encrypted or access-controlled immutable user and system seals

REVEAL DOMAIN
  outcome binding, source evidence, qualification, redacted reveal projection
```

Separation must be enforced by server authorization and repository/service access,
not by hiding fields with CSS or delaying rendering in JavaScript.

Before reveal, the client bundle and API graph must be able to function without any
read permission to the reveal domain. Service workers, prefetchers, analytics, error
reporting, and model calls inherit the same restriction.

## Withdrawal And Dispute

- A resident or evidence subject may withdraw disclosure according to the governing
  consent policy.
- Withdrawal revokes future projections and reveal access immediately.
- Personal content is deleted, de-identified, or sealed as required; only an
  approved content-free integrity proof may remain.
- Existing viewers cannot reopen cached evidence after withdrawal.
- A disputed outcome cannot be scored as verified.
- A later verification creates a new evidence version and evaluation record. It does
  not alter the original seals or conceal the dispute interval.

## Design Completion

The logical objects, owners, immutability, dual sealing, projection separation,
Liuyao boundary, evaluation, learning, and formal-path admission boundary are fully
defined for design purposes.

No runtime type, API, persistence model, migration, or UI implementation is
authorized by this document.
