# DREAM-PROBLEM-FLOWER-AND-FRUIT-01 Canonical Game Contract v1

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

## Purpose

`Abu Asks the Fruit: Three-Tree Round` is the first repeatable core game in the
Dream world. It lets a viewer inspect a real, evidence-qualified life question,
make a prediction before seeing the outcome, and compare that prediction with an
independently sealed system judgment and verified evidence.

The product loop is:

```text
three eligible resident trees
-> pre-outcome tree observation
-> pre-outcome OneCanvas observation
-> one problem flower
-> optional explicit Liuyao divination
-> immutable user judgment and hypothesis
-> independently pre-sealed system judgment
-> verified outcome reveal
-> evaluation
-> personal knowledge seed
```

This is a blind judgment game, not a report-reading page, a quiz with a hidden
answer in the client, or a route for promoting player opinions into formal V50
facts.

## Frozen Product Invariants

1. The outcome cannot be available to the pre-outcome browser, Dream renderer,
   OneCanvas renderer, accessibility tree, model context, logs, or caches.
2. The system judgment is generated and sealed when the round is published,
   before any player sees or answers the question.
3. The user and system judgments are independent immutable seals. Neither may
   contain or depend on the other.
4. A player judgment creates a `JudgmentSubmission` and optional
   `UserPathHypothesis`. It never creates or modifies a formal `PathAssertion`.
5. A later V50 review may create a new formal assertion only through the normal
   provenance and qualification process. It must reference, but cannot rewrite,
   the original game submission.
6. Opening a problem flower never casts Liuyao. Divination requires a separate,
   explicit user action and creates an immutable `DivinationRecord`.
7. A simulated result is never presented, scored, trained, or promoted as a
   verified real fruit.
8. Abu may guide attention and ask for a possible falsifier. He cannot hint at
   the answer, make the decision, or explain away a failed system judgment.
9. No points, levels, streaks, random rewards, attendance pressure, or tree growth
   may be driven by visits or answer frequency.
10. A `KnowledgeSeed` is a private learning record, not currency, a reward, a
    LifeCase fact, or evidence that a Mingli rule is true.

## Scope

This design defines:

- one complete matured-fruit blind round;
- the product and causal order of observation, judgment, sealing, reveal, and
  evaluation;
- the desktop and 390px first-round experience;
- the game state machine and fail-closed behavior;
- the boundary among Bazi observation, optional Liuyao, user hypotheses, formal
  assertions, and verified outcome evidence;
- the content gate for the first three real matured fruits.

This design does not authorize:

- runtime code, database migrations, UI implementation, deployment, or remote
  synchronization;
- live fruit waiting, notifications, social competition, ranking, or rewards;
- NPC Mind Wake, free conversation, autonomous NPC judgment, or system training;
- new Bazi, relation, path, Liuyao, scoring, or outcome-resolution algorithms;
- use of Wulan, Yanzhou, the old 44 Cases, fixtures, or generated stories as if
  they were verified real matured fruits.

Companion contracts:

- `DREAM_PROBLEM_FLOWER_AND_FRUIT_01_OBJECT_SCHEMA_AND_OWNERSHIP_V1.md`
- `DREAM_PROBLEM_FLOWER_AND_FRUIT_01_MATURED_FRUIT_EVIDENCE_PACK_V1.md`
- `DREAM_PROBLEM_FLOWER_AND_FRUIT_01_THREAT_MODEL_AND_ACCEPTANCE_V1.md`

## Authority And Evidence Boundary

```text
Canonical LifeCase / Canonical Scene
-> supplies versioned pre-cutoff facts

DreamProjection
-> discloses only viewer-authorized pre-outcome content

OneCanvas
-> renders the same authorized pre-outcome facts

BlindRound Service
-> owns question, cutoff, windows, policies, and seal references

Judgment Service
-> owns immutable user and system seals

Outcome Evidence Service
-> owns isolated real-world outcome evidence and reveal eligibility

Evaluation Service
-> compares immutable seals with revealed evidence under a frozen policy

Knowledge Ledger
-> stores the viewer's private learning seed
```

Projection layers never own LifeCase facts, the outcome, the player's judgment,
or formal path truth. The client never owns an authoritative timestamp, cutoff,
seal, outcome status, or evaluation.

### Evidence Classes

| Class | Meaning | Permitted product use |
| --- | --- | --- |
| `VERIFIED_REAL` | Outcome supported by qualified real or reliable historical evidence | Eligible for the first matured-fruit mode |
| `REALITY_FEEDBACK_UNVERIFIED` | Real-world claim lacking the required verification | Research quarantine only |
| `HISTORICAL_VERIFIED` | Reliable historical record with auditable provenance | Eligible only when the same content gate is met |
| `SIMULATION_ONLY` | Generated by a canonical or branch simulation | Lab training and mechanism comparison only |
| `SYNTHETIC_FIXTURE` | Purpose-built test or regression material | Automated testing only |

`canonical_world` is internal Dream chronology. It does not upgrade evidence to
`VERIFIED_REAL`.

## Blind Round Definition

Each published round binds exactly one resident, one question, one outcome window,
and one immutable knowledge boundary. Publication is valid only after all required
pre-outcome artifacts and the system judgment seal exist.

```text
prepare eligible evidence pack
-> freeze knowledge_cutoff
-> build pre-outcome manifests and projections
-> generate system judgment from pre-outcome inputs only
-> seal system judgment
-> verify outcome evidence remains in the isolated reveal domain
-> publish BlindRoundDefinition
```

`knowledge_cutoff` is not a display filter applied at the end. It is the latest
allowed time for every input used by the pre-outcome experience, including:

- LifeCase and birth-fact version;
- Canonical Scene, timing, relation, and path versions;
- tree state and DreamProjection;
- OneCanvas verification data;
- question context and available options;
- retrieved knowledge, model, Prompt, and policy inputs;
- system judgment and explanation.

Later Case revisions, later timing interpretations, current tree state, outcome
facts, reveal summaries, and post-outcome knowledge cannot enter the blind phase.

## First Mode

```yaml
mode: MATURED_FRUIT_IMMEDIATE_REVEAL
resident_pool: THREE_VERIFIED_CANONICAL_RESIDENTS
outcome_already_occurred: true
outcome_hidden_until_user_seal: true
reveal_after_valid_user_seal: immediate
round_duration_target: 6_TO_10_MINUTES
```

The first mode uses outcomes that have already happened so the player can finish a
round immediately. The outcome is still blind because it is isolated until a valid
user seal has been committed.

Preferred first-round questions are objectively resolvable events, for example:

- whether a documented job change completed by a fixed date;
- whether a named contract was signed within a fixed window;
- whether a documented relocation or journey occurred within a fixed window.

Health, death, vague improvement, subjective happiness, and questions with movable
time windows are ineligible for this first mode.

## First-Round Experience

### Stage 1: Three-Tree Entry

The viewer enters the existing living grove and sees three evidence-qualified
resident trees. The scene remains spatial and continuous. It is not converted into
three cards, a carousel, or a leaderboard.

- Resident source is disclosed truthfully.
- Outcome, question answer, and post-cutoff state are absent.
- A tree may indicate that a problem flower is available, but not whether the
  eventual outcome is favorable.
- Choosing a tree selects a round; it does not create a relationship or a Mingli
  fact.

### Stage 2: Pre-Outcome Observation

The player may observe only the frozen pre-outcome tree projection. The tree cannot
quietly use its current state or the known outcome.

The root mirror opens the same pre-outcome OneCanvas under the round's fixed
`knowledge_cutoff`. Existing six Lens semantics are reused:

```text
overview | five-elements | combinations-conflicts | roots-transparency
| timing | work-path
```

The player may inspect only content authorized for this round. Potential relations,
Lab diagnostics, outcome-linked annotations, later Case revisions, and post-cutoff
facts remain unavailable.

### Stage 3: Problem Flower

The problem flower reveals a frozen question package:

- neutral question text;
- the subject and authorized context known at `knowledge_cutoff`;
- fixed outcome options;
- target variable;
- result window;
- evaluation rule summary;
- what counts as disconfirming evidence;
- whether optional Liuyao is permitted.

Opening the flower has no canonical Mingli effect and does not cast Liuyao.

### Stage 4: Optional Liuyao

When permitted, the player may select the explicit command `起一卦再判断`.

Before casting, the product must state that:

- this is a new divination about the displayed question;
- the cast time is server time at the confirmed user action;
- the resulting record is immutable;
- Bazi observation and Liuyao divination are separate evidence channels;
- the round can be completed without casting.

The cast cannot be triggered by opening the flower, touching the tree, entering
OneCanvas, inactivity, or a default selection.

### Stage 5: User Judgment

The player submits:

1. one fixed outcome choice;
2. a confidence value;
3. an optional `UserPathHypothesis` assembled only from server-authorized pre-cutoff
   references;
4. the strongest competing explanation;
5. one explicit disconfirmation condition.

Abu may ask only the approved prompt:

> If your judgment is wrong, which evidence is most likely to overturn it?

The submission screen identifies the judgment as immutable after confirmation. A
second confirmation commits the seal. No LLM rewrites the player's text.

While drafting, a `UserPathHypothesis` may be drawn only as a clearly labeled,
visually distinct candidate overlay. It cannot replace the committed work-path layer,
and it disappears outside the judgment/reconciliation context. Existing formal paths
remain unchanged.

### Stage 6: Dual Seal Check

After the user seal commits, the server proves that:

- the system seal existed before round publication;
- the system seal predates the user's first round access;
- user and system input manifests are distinct and valid;
- neither seal has been superseded or opened;
- the outcome remains unrevealed to this viewer.

The player cannot proceed to reveal when these checks fail.

### Stage 7: Immediate Reveal

The fruit opens only through an authorized server reveal command. The result view
shows, without post-hoc rewriting:

- the original user judgment and confidence;
- the original user path hypothesis and falsifier;
- the original system judgment and confidence;
- the verified outcome and evidence scope;
- the frozen evaluation policy and its result;
- disputed, withdrawn, or unavailable evidence status when applicable.

The system must display its own error plainly. It cannot generate a new explanation
that changes the sealed claim after seeing the outcome.

### Stage 8: Knowledge Seed

After evaluation, the system issues one private seed containing:

- what they observed correctly;
- which node, relation, timing fact, or alternative they missed;
- what the outcome did and did not establish;
- where the lesson should not be generalized;
- references to the immutable submission, evaluation, and evidence version.

The seed uses frozen evaluation fields and approved copy, not a post-reveal LLM
rationalization. The viewer may later append a private reflection without modifying
the issued seed. This record is personal learning material only. It cannot alter the
resident's tree, LifeCase, formal relations, formal paths, NPC memory, or V50 rules.

## Desktop Composition

The desktop experience remains one full-bleed grove.

- Three residents occupy the scene at real depth rather than equal-width choices.
- The selected resident and flower remain in the grove while observation is active.
- OneCanvas continues to appear in the physical root mirror.
- The judgment surface is an unframed writing layer anchored to the flower/root area,
  not a dashboard or a nested card stack.
- Outcome choices use a compact option control; confidence uses a clearly labeled
  slider or stepper; hypothesis references use explicit nodes and segments.
- The sealed comparison uses two parallel, equally weighted records. The system is
  not visually privileged as the correct answer.
- Reveal evidence is visually distinct from both predictions and appears only after
  authorization.

## 390px Mobile Composition

Mobile preserves the same causal sequence and world, with these constraints:

- The grove stays full-bleed; resident selection uses direct scene movement and
  touch, not a substitute list of cards.
- OneCanvas keeps its canonical six-pillar coordinate space and uses the existing
  mobile pan/zoom behavior. It is not reflowed into a different chart.
- The problem flower remains a scene object. Its question opens into one stable,
  scrollable reading surface that never covers the active confirmation control.
- Outcome choices, confidence, alternative, and falsifier are completed in clear
  steps with persistent progress inside the current draft only.
- Casting Liuyao requires a separate full-width command and confirmation; it is not
  adjacent to the final judgment confirmation in a way that invites accidental use.
- The seal confirmation remains reachable above browser controls and safe areas.
- The result comparison uses a vertical sequence: user seal, system seal, verified
  outcome, evaluation, then seed. It never squeezes two columns into 390px.
- Browser Back closes the current reading surface or root mirror before leaving the
  round. It never submits, casts, reveals, or discards an immutable seal.
- Screen-reader order follows the same causal order and contains no hidden outcome
  text before reveal.

## State Machine

The authoritative server lifecycle is:

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
-> ROUND_COMPLETE
```

The client may use animation substates such as `ROUND_SELECTED`,
`LIUYAO_CONFIRMING`, `JUDGMENT_CONFIRMING`, and `REVEAL_AUTHORIZING`, but they do
not own authority and cannot bypass a server state.

### Transition Contract

| From | Command | Server-owned precondition | To |
| --- | --- | --- | --- |
| `ROUND_ELIGIBILITY_CHECK` | select eligible tree | round qualified and published; viewer authorized | `PROJECTION_ISSUING` |
| `PROJECTION_ISSUING` | issue blind capability | exact cutoff manifest and authorization valid | `ROUND_OBSERVING` |
| `ROUND_OBSERVING` | open flower | question projection belongs to selected round | `QUESTION_FLOWER_OPEN` |
| `QUESTION_FLOWER_OPEN` | confirm Liuyao request | Liuyao allowed; no prior cast; explicit confirmation completed | `OPTIONAL_DIVINATION` |
| `OPTIONAL_DIVINATION` | cast succeeds | active control; server cast timestamp; idempotency key valid | `JUDGMENT_DRAFTING` |
| `QUESTION_FLOWER_OPEN` | continue without Liuyao | no outcome access; valid input manifest | `JUDGMENT_DRAFTING` |
| `JUDGMENT_DRAFTING` | commit judgment | required fields valid; immutable payload confirmed; no prior user seal | `USER_JUDGMENT_SEALED` |
| `USER_JUDGMENT_SEALED` | validate pre-existing system seal | system seal predates publication and player access; independence proven | `BOTH_JUDGMENTS_SEALED` |
| `BOTH_JUDGMENTS_SEALED` | check evidence | both seals bind the same projection; evidence verified; authorization current | `OUTCOME_REVEALABLE` |
| `OUTCOME_REVEALABLE` | reveal | one idempotent authorized reveal record committed | `OUTCOME_REVEALED` |
| `OUTCOME_REVEALED` | evaluate | frozen resolver and evaluation policy available | `EVALUATED` |
| `EVALUATED` | issue seed | seed binds exact evaluation and evidence versions | `KNOWLEDGE_SEED_ISSUED` |
| `KNOWLEDGE_SEED_ISSUED` | finish | private seed persisted; no formal-domain write | `ROUND_COMPLETE` |

Draft data may be edited before the user seal. Once sealed, no state transition can
return to drafting.

## Failure States

| State | Trigger | Product behavior |
| --- | --- | --- |
| `CONTENT_GATE_BLOCKED` | Fewer than three qualified packs exist, or selected pack is ineligible | Omit the round; show no partial question or substitute tree |
| `AUTHORIZATION_REVOKED` | Viewer, subject, disclosure, or evidence authorization is withdrawn | Clear sensitive content, revoke capabilities, and leave without substitution |
| `PROJECTION_INVALID` | Cutoff, source version, authorization, expiry, or projection hash fails | Rebuild only from exact frozen sources when permitted; never use current state |
| `SEAL_CONFLICT` | A seal is missing, late, contaminated, mismatched, duplicated with changed content, or mutable | Preserve any valid original seal, reject replacement, and block reveal |
| `EVIDENCE_INSUFFICIENT` | Evidence is unverified, disputed, incomplete, withdrawn, or no longer resolvable | Do not reveal or score as verified; withdraw or quarantine the round |
| `FAIL_CLOSED` | Leak suspicion, reveal-domain failure, impossible state, or authorization race | Mask private content, emit a fixed non-sensitive reason, and quarantine as required |

Detailed internal reason codes may include `OUTCOME_LEAK_SUSPECTED`,
`SYSTEM_SEAL_INVALID`, `USER_SEAL_CONFLICT`, `LIUYAO_CAST_CONFLICT`,
`EVIDENCE_DISPUTED`, `EVIDENCE_WITHDRAWN`, and `REVEAL_UNAVAILABLE`. They do not
create additional product-authority states. If evaluation alone is temporarily
unavailable after a legitimate reveal, the immutable seals and verified evidence
remain visible with `evaluation pending`; the client still cannot infer a score.

No failure permits the client to synthesize an outcome, use current Case data,
regenerate a system judgment, edit a seal, or replace the resident.

## Path And Assertion Boundary

The player may use the visual language of a path to express a hypothesis, but the
object remains explicitly non-formal:

```text
UserPathHypothesis
  references authorized NodeRef / RelationKey / existing assertion refs
  records player ordering and interpretation
  remains bound to the user seal
  is not rendered as a committed main path outside the game review
```

After reveal, a practitioner or formal V50 process may open a separate review:

```text
immutable game evidence
-> formal Path Review
-> deterministic reference validation
-> professional qualification
-> new PathAssertion candidate
-> normal commit process
```

The new assertion, if any, receives its own identity, producer, version, evidence,
and provenance. It never adopts the player's seal timestamp as its own creation time
and never retroactively marks the player as having submitted formal truth.

## Content Gate

The game design can remain frozen while content is unavailable. Runtime release
cannot begin until exactly three initial packs independently pass the matured-fruit
qualification checklist.

Current gate:

```yaml
required_verified_matured_fruit_packs: 3
qualified_packs_asserted_by_this_design: 0
wulan_eligible: false
yanzhou_eligible: false
mock_or_fixture_substitution: forbidden
implementation_authorized: false
release_authorized: false
```

The absence of three packs is a content gate, not permission to fabricate Cases,
outcomes, consent, timestamps, or evidence.

## Design Exit Decision

The product semantics, causal order, first mode, evidence classes, interaction
sequence, and failure behavior are internally resolved. The design is frozen.

Implementation remains unauthorized until the owner separately authorizes it, and
the first playable content remains closed until three verified matured-fruit packs
pass the evidence gate.
