# DREAM-PROBLEM-FLOWER-AND-FRUIT-01 Threat Model And Acceptance v1

```yaml
status: FROZEN_DESIGN_ASSURANCE
implementation: NOT_AUTHORIZED
threat_model_scope: FIRST_MATURED_FRUIT_MODE
design_self_audit: PASS
content_gate: CLOSED
```

## Assurance Goal

The game is valid only when a player and the system can make independent blind
judgments from a reproducible pre-outcome world, then compare immutable claims with
qualified evidence that neither side could access beforehand.

The primary failure is not merely an incorrect answer. It is any path by which the
answer, later state, player judgment, simulated evidence, or post-hoc explanation
crosses the wrong trust boundary.

## Trust Boundaries

```text
PUBLIC CLIENT
  untrusted for timestamps, IDs, selection authority, sealing, and reveal

PRE-OUTCOME APPLICATION DOMAIN
  trusted only for frozen round metadata and authorized blind projections

SEALED JUDGMENT DOMAIN
  trusted for immutable user/system commitments; cannot read reveal evidence

REVEAL DOMAIN
  trusted for qualified outcome evidence; inaccessible before reveal authorization

FORMAL V50 DOMAIN
  owns LifeCase, Scene, RelationAssertion, PathAssertion, and admission review

PERSONAL KNOWLEDGE DOMAIN
  owns private KnowledgeSeed; cannot promote formal truth
```

An operator account, an LLM, a browser extension, and a service process are not
implicitly trusted merely because they run inside the product environment. Access is
least-privilege and recorded.

## Threat Register

| ID | Threat or failure | Required design control | Required implementation evidence |
| --- | --- | --- | --- |
| `LEAK-01` | Current LifeCase, timing, tree, or OneCanvas state overwrites the historical blind view | Exact version refs and `knowledge_cutoff`; no `latest` aliases | Mutate current Case after publication and prove projection hash/content remain unchanged |
| `LEAK-02` | Outcome fields are sent but hidden by UI | Pre-outcome transport omits outcome and binding fields entirely | API schema and captured network response contain no forbidden key/value |
| `LEAK-03` | Service worker, prefetch, preload, route loader, or static bundle fetches reveal data | Reveal domain inaccessible to blind client; no prefetch links | Cold-load browser trace shows zero reveal-domain requests before valid seals |
| `LEAK-04` | Hidden DOM, Canvas metadata, tooltip, title, data attribute, or ARIA text contains the result | One sanitized projection feeds visual and accessibility renderers | DOM, accessibility tree, canvas command audit, and snapshots contain no answer |
| `LEAK-05` | Logs, analytics, exception text, tracing tags, or source maps disclose outcome | Outcome values prohibited in pre-outcome telemetry and client errors | Forced failures and telemetry export reveal only opaque IDs and fixed codes |
| `LEAK-06` | Answer can be inferred from resource name, size, count, ordering, color, latency, or alias | Neutralized resource layout and fixed ordering independent of result | Differential side-channel test across all outcome options stays below defined threshold |
| `LEAK-07` | RAG, model prompt, tool context, or memory includes post-cutoff knowledge | Content-addressed input manifest and causal firewall | Full system-run dependency manifest contains only pre-cutoff refs |
| `LEAK-08` | Original evidence is embedded in a generated explanation or tree asset | Pre-outcome assets built only from blind bundle; asset hashes audited | Binary/text scan and asset provenance review pass |
| `SEAL-01` | System judgment is generated after seeing player input | System seal required before publication and first access | Timestamps and server sequence prove seal precedes publication and access |
| `SEAL-02` | Player telemetry or draft hash enters system input indirectly | Separate execution identity and dependency manifest; no session dependency | Canary player values never appear in system inputs or outputs |
| `SEAL-03` | Operator, retry, or reveal flow edits an existing seal | Append-only immutable seal store; domain-separated commitment | Mutation attempts fail; identical retry returns same ID/hash |
| `SEAL-04` | Player changes choice after seal through back navigation or offline replay | Server seal state is authoritative; drafts cannot replace it | Multi-tab, Back, offline, and changed-payload retries preserve original seal |
| `SEAL-05` | User and system seals refer to different projections | Reveal requires equal round and projection/input manifest binding | Mismatched projection hash fails closed |
| `SEAL-06` | The system silently regenerates a failed judgment | One publication seal only; missing/invalid seal withdraws round | Generation counter stays one; no fallback seal appears |
| `CAST-01` | Flower touch, proximity, page entry, or default state creates Liuyao | Explicit command plus confirmation is the sole trigger | Event instrumentation proves all non-command interactions create zero records |
| `CAST-02` | Client clock or outcome-aware server time is used as cast time | Authoritative server timestamp at confirmed command | Tampered client time does not affect record |
| `CAST-03` | Cast is regenerated until it fits the result | Immutable idempotent DivinationRecord bound to exact question | Repeat and altered requests return original or reject |
| `CAST-04` | Retrospective blind cast is reported as prospective prediction | Mandatory temporality label and separate evaluation cohort | UI, export, and metrics retain `RETROSPECTIVE_BLIND` |
| `REVEAL-01` | Client guesses or enumerates an evidence/ref URL | Opaque capability plus viewer/round/seal authorization | Direct, altered, expired, and cross-viewer requests fail |
| `REVEAL-02` | Blind service can read evidence because both tables share broad credentials | Separate repository/service authorization boundary | Pre-outcome service identity is denied evidence read access |
| `REVEAL-03` | Reveal occurs with one missing, late, or mismatched seal | Atomic dual-seal validation | Matrix of missing/invalid/mismatched seals never returns evidence |
| `REVEAL-04` | Evidence is disputed, insufficient, or withdrawn but still scored as verified | Qualification recheck at reveal; status is append-only | Status change before reveal yields fail-closed or explicit unscorable result |
| `REVEAL-05` | Cached reveal remains available after withdrawal | Capability revocation, cache purge policy, no-store for private evidence | Open tab, history, reload, and offline cache cannot reopen content |
| `REVEAL-06` | Another viewer or Case namespace receives a prior reveal | Viewer/round/case binding and isolated caches | Cross-account and shared-device tests fail closed |
| `REVEAL-07` | Browser error or service log includes private source filename or identity | Fixed public error codes and private-domain logging policy | Failure injection exposes no private metadata |
| `EVAL-01` | LLM rewrites a wrong prediction after outcome | Deterministic frozen evaluator; sealed text shown verbatim | Wrong fixture remains wrong; no post-reveal generation request occurs |
| `EVAL-02` | Evaluation policy is changed in place to improve score | Versioned immutable EvaluationRecord | New policy creates a new record linked to the old one |
| `EVAL-03` | Correct option is treated as proof of the proposed path | Separate outcome match and formal mechanism review | Path review state remains `NOT_FORMALLY_REVIEWED` after scoring |
| `PATH-01` | Player path is rendered or stored as formal `PathAssertion` | Distinct `UserPathHypothesis` object and visual grammar | LifeCase/path stores receive zero writes from game submission |
| `PATH-02` | A later review overwrites the original hypothesis | New PathAdmissionReview and new assertion identity | Original submission hash remains unchanged and provenance is complete |
| `SIM-01` | Simulated NPC outcome is relabeled as real | Orthogonal evidence origin/class and namespace separation | Type validation rejects simulation evidence from real-round publication |
| `SIM-02` | Canonical Dream history is mistaken for reality evidence | `canonical_world` never implies `VERIFIED_REAL` | Publication gate requires independent real/historical verification |
| `LEARN-01` | KnowledgeSeed modifies Case, tree, path, NPC memory, or shared knowledge | Private ledger owner and no automatic promotion route | Write-set audit shows only personal knowledge domain changes |
| `LEARN-02` | KnowledgeSeed is silently used for model training | Separate later consent and data-governance gate | Training export excludes seed by default |
| `PRIV-01` | Dream display consent is reused as evidence/reveal consent | Separate scoped consent records | Missing game/evidence scope blocks qualification |
| `PRIV-02` | Public alias or evidence details reidentify a subject | Deidentification and residual-risk review | Human review and automated identifier scan pass |
| `PRIV-03` | Withdrawal leaves summaries, emotional residue, or hidden memory | Default content deletion/deidentification; integrity proof only | Data lineage audit finds no derivative personal content in active systems |
| `OPS-01` | Privileged operator previews outcome while generating system seal | Separation of duties, access logs, isolated execution identity | Audit proves judgment job identity lacked reveal permission |
| `OPS-02` | A round is cherry-picked after outcome because it makes the system look good | Sampling and inclusion rationale recorded; cohort limitations disclosed | Qualification record includes selection policy and excluded candidates |
| `RACE-01` | Two tabs create two casts, seals, or reveals | Idempotency keys and unique viewer-round constraints | Concurrent tests produce one canonical record per object type |
| `RACE-02` | Authorization is revoked between seal validation and evidence read | Reveal authorization and evidence read occur under one consistent command boundary | Revocation race never returns evidence after revocation commits |
| `STATE-01` | Browser Back submits, casts, reveals, or discards a seal | Navigation actions separate from semantic commands | Back-state matrix produces no unintended writes |
| `STATE-02` | Reload mixes pre-outcome and revealed projections | Server round-view state decides projection; caches are partitioned | Reload before/after reveal returns only the authorized phase |

## Outcome Leak Detection Strategy

Future implementation must produce a machine-readable forbidden-data policy. The
policy covers values and derivatives, not just field names.

Before any playable release, the following audits are mandatory:

1. Capture all network requests and responses from round list through user seal.
2. Snapshot DOM, accessibility tree, browser storage, service-worker cache, Canvas
   commands, client logs, source maps, and analytics payloads.
3. Inspect model prompts, retrieval results, tool inputs, and dependency manifests.
4. Compare equivalent rounds with different outcomes for file size, resource count,
   ordering, latency, color, and alias side channels.
5. Attempt direct reveal endpoint access with no seal, one seal, wrong viewer, wrong
   round, expired capability, disputed evidence, and revoked consent.
6. Seed outcome canaries in the reveal domain and prove they never appear in blind
   artifacts.
7. Rebuild the historical projection after current Case changes and verify the exact
   content hash is unchanged.

Any canary or outcome-derived difference before reveal quarantines the entire round,
not just the affected UI element.

## Acceptance Matrix

| ID | Contract to prove | Future automated evidence | Future Chrome/manual evidence | Pass condition |
| --- | --- | --- | --- | --- |
| `ACC-01` | Player submission never creates formal PathAssertion | Store write-set and event audit | Candidate path is visibly distinct in review | Zero formal path writes; status stays user hypothesis |
| `ACC-02` | System seal cannot read player submission | Dependency-manifest and canary test | System result is already sealed before entry | No player/session dependency; seal timestamp predates publication |
| `ACC-03` | Current state cannot leak into historical projection | Version mutation/rebuild test | Old round remains visually unchanged after current Case changes | Exact projection hash stable |
| `ACC-04` | Client cannot obtain OutcomeEvidence before reveal | Network/storage/DOM/ARIA/cache scan and endpoint-denial tests | DevTools inspection finds no outcome | Zero outcome or derivative access before valid dual seal |
| `ACC-05` | Flower interaction does not cast Liuyao | Event-to-write instrumentation | Open, close, approach, and inspect flower | Zero DivinationRecord writes |
| `ACC-06` | Only explicit confirmed cast creates server timestamp | Command/idempotency test | User sees separate action and confirmation | Exactly one immutable record with server time |
| `ACC-07` | Revoked or insufficient evidence cannot reveal | Status/race matrix | Round closes or shows unavailable without answer | No evidence payload or score |
| `ACC-08` | Seals remain immutable after reveal | Mutation, retry, and policy-version tests | Original player/system wording remains visible | Original hashes unchanged forever |
| `ACC-09` | Simulation cannot masquerade as verified real | Type/publication gate tests | Source and evidence class remain explicit | Simulation publication to first mode is rejected |
| `ACC-10` | KnowledgeSeed cannot become formal knowledge/history | Domain write-set and export tests | Saving a seed changes no tree or formal chart | Only personal ledger write occurs |
| `ACC-11` | Both seals reference the same frozen projection | Mismatch tests | Reveal unavailable on mismatch | Equal round, projection, and manifest binding required |
| `ACC-12` | Wrong system judgment is shown without rescue | Deliberately wrong fixture under frozen evaluator | Result comparison displays the error plainly | No LLM call or text mutation after reveal |
| `ACC-13` | Matured fruit is labeled retrospective blind | Metrics/export schema tests | Label visible in evidence explanation | Never counted as prospective forecast |
| `ACC-14` | Desktop first round follows causal sequence | State-machine integration test | Full Chrome round from grove to seed | No hidden step, accidental write, or page-product split |
| `ACC-15` | 390px flow remains usable and semantically identical | Responsive interaction suite | Touch, scroll, cast, seal, reveal, Back, safe-area audit | No overlap, clipped controls, or semantic shortcut |
| `ACC-16` | Accessibility contains no hidden result | Accessibility snapshot diff | Screen-reader traversal before and after reveal | Result absent before reveal, ordered after reveal |
| `ACC-17` | Three qualified packs are truly independent and authorized | Qualification-record validation | Human evidence review | 3/3 complete; no Wulan/Yanzhou/mock substitution |
| `ACC-18` | Formal path admission remains a later V50 process | API capability and ownership test | Game has no promotion control | Only separate review can create a new assertion |
| `ACC-19` | Disclosure withdrawal clears active content | Revocation/cache/race suite | Open tabs veil and cannot reopen evidence | Sensitive content inaccessible after committed withdrawal |
| `ACC-20` | Evaluation separates option accuracy from mechanism support | Evaluation fixture suite | Result view presents distinct fields | Correct option does not mark path as reviewed |

## Required Failure-State Coverage

The implemented state machine must expose fixed, non-sensitive states for:

```text
CONTENT_GATE_BLOCKED
AUTHORIZATION_REVOKED
PROJECTION_INVALID
SEAL_CONFLICT
EVIDENCE_INSUFFICIENT
FAIL_CLOSED
```

Each state must satisfy:

- no outcome, source identity, system judgment, or private evidence in user-visible
  text, accessibility output, logs, or telemetry;
- no client-selected fallback Case, projection, outcome, or evidence;
- no automatic regeneration of system judgment or Liuyao;
- no mutation of an existing seal;
- a recoverable action only when the authoritative server state supports it.

## State-Machine Acceptance

The canonical lifecycle names are:

```text
ROUND_ELIGIBILITY_CHECK
-> PROJECTION_ISSUING
-> ROUND_OBSERVING
-> QUESTION_FLOWER_OPEN
-> optional OPTIONAL_DIVINATION
-> JUDGMENT_DRAFTING
-> USER_JUDGMENT_SEALED
-> BOTH_JUDGMENTS_SEALED
-> OUTCOME_REVEALABLE
-> OUTCOME_REVEALED
-> EVALUATED
-> KNOWLEDGE_SEED_ISSUED
```

UI animation substates may exist, but they cannot replace or bypass these server
states. The implementation must prove every state-changing command is server-owned,
idempotent where retryable, and guarded by exact round and projection versions.

## Internal Consistency Audit

| Audit question | Result | Evidence |
| --- | --- | --- |
| Does player judgment create a formal path? | PASS | It creates only immutable `UserPathHypothesis`; later review is separate |
| Is system judgment causally prior to player input? | PASS | Seal is mandatory before publication and first access |
| Can current world state replace the historical blind world? | PASS | Exact pre-cutoff refs and content-addressed projection are mandatory |
| Is outcome isolation server-enforced? | PASS | Separate reveal domain and no pre-outcome read capability |
| Are user and system seals independent and immutable? | PASS | Separate stores/records, manifests, commitments, and timestamps |
| Does a flower click cast Liuyao? | PASS | Only explicit confirmed command can create DivinationRecord |
| Is matured-fruit Liuyao temporality honest? | PASS | It is labeled `RETROSPECTIVE_BLIND`, never prospective |
| Can simulated evidence enter the first mode? | PASS | Publication type gate forbids it |
| Can a correct result promote a mechanism automatically? | PASS | Formal V50 PathAdmissionReview remains mandatory |
| Can KnowledgeSeed change world or formal truth? | PASS | It belongs only to the private viewer ledger |
| Are withdrawal and evidence dispute fail-closed? | PASS | They revoke reveal/scoring and preserve only permitted integrity proof |
| Are desktop and 390px flows semantically identical? | PASS | Same states, commands, projections, and seals; composition alone differs |
| Are any product semantics unresolved? | PASS | None within the authorized design scope |

## Final Design Assurance State

```yaml
DREAM_PROBLEM_FLOWER_AND_FRUIT_01:
  product_direction: ACCEPTED
  design: FROZEN
  implementation: NOT_AUTHORIZED
  first_mode: MATURED_FRUIT_IMMEDIATE_REVEAL
  player_submission: IMMUTABLE_USER_HYPOTHESIS
  formal_path_assertion: V50_REVIEW_REQUIRED
  projection_policy: PRE_OUTCOME_KNOWLEDGE_CUTOFF
  judgment_sealing: INDEPENDENT_DUAL_SEAL
  liuyao_trigger: EXPLICIT_USER_ACTION_ONLY
  content_gate: THREE_VERIFIED_MATURED_FRUITS_REQUIRED
  simulated_fruit_as_real: FORBIDDEN
  unresolved_product_semantics: NONE
```

The design assurance review passes. Implementation and release remain closed because
no three qualified matured-fruit packs have been supplied or verified.
