# V60 Cognitive Decision Kernel

Status: `EXECUTABLE_V4`

## Constitutional answer

The V60 central brain is the `CognitiveDecisionKernel`.

The kernel governs how a decision is resolved. It does not pretend that one
method can answer every class of question.

```text
DecisionRequest
-> evidence assembly
-> deterministic resolution when possible
-> rule-constrained candidate resolution
-> bounded LLM comparison when authorized
-> human decision when required
-> Epistemic Gate
-> immutable DecisionRecord
```

## Authorities

| Decision class | Primary authority | LLM role |
| --- | --- | --- |
| Calendar, chart and typed facts | Deterministic system | None |
| Permission and disclosure | Policy system | None |
| World transitions and outcomes | World resolver | None |
| Legal relations and candidates | Rule/graph system | Challenge only |
| Whole-chart interpretation | LLM Reasoner | Comparative authority |
| Presentation and wording | Story/Abu projection | Bounded generation |
| Consent and subjective choice | Human | Clarification only |
| Global knowledge promotion | Owner/professional review | Candidate authoring only |

## Resolution hierarchy

```text
system_can_prove
-> SYSTEM

rules_leave_one_qualified_candidate
-> RULE_ENGINE

multiple_qualified_interpretations && llm_allowed
-> LLM_REASONER

human_consent_or_irreversible_choice
-> HUMAN

insufficient_evidence
-> UNRESOLVED
```

LLM output is always a `DecisionProposal`. `EpistemicGate` verifies that the
proposal:

- belongs to the routed request;
- compares the complete set of qualified candidates;
- selects only a qualified candidate;
- cites only request-bound evidence and the selected candidate's evidence;
- carries provider, model and prompt identity.

An admitted Gate receipt may authorize an immutable DecisionRecord. It always
keeps `canonical_domain_write_allowed=false`: a proposal cannot directly write
LifeCase, WorldEvent, ActorState, AnswerSeal, Reveal or global knowledge.
Rejected, pending and unresolved routes cannot be recorded as final decisions.

## Executable decision ledger

`CognitiveDecisionLedger` is the only writer to
`cognition.decision_records`. Version
`v60.cognitive-decision-kernel.004` is active in deterministic canonical paths
and owns the bounded comparison coordinator:

```text
due WorldEvent
-> deterministic WORLD_OUTCOME decision
-> atomic world settlement

settled WorldEvent + sealed Answer
-> atom reconciliation
-> deterministic DOMAIN_INFERENCE decision
-> Reveal
```

Both records are written inside the caller's database transaction. A stable
decision identity may be replayed only with the exact canonical request and
route Hash. Exact replay returns the existing record; changed content fails
closed with `decision_record_conflict`.

No browser, product unit, Story projection or LLM writes this ledger.

`CognitiveDecisionCoordinator` is the single executable entry for deterministic
and LLM-authorized decisions. The bounded Host:

- requires an exact projection of every qualified candidate and every
  request-bound, decision-visible evidence item;
- sends no hidden outcome, domain tool or canonical write capability;
- uses strict structured output and stamps provider, model, prompt, response
  and context Hash itself;
- replays an existing immutable DecisionRecord before any second provider call;
- passes every output through `EpistemicGate` before Ledger admission.

The OpenAI Responses adapter remains available for an explicitly configured
deployment. The managed local Runtime currently uses the dblife-hosted Ollama
endpoint with `gemma4:latest` and the hash-locked profile
`v60.model-serving.gemma4-structured-decision.001`:

```yaml
think: false
temperature: 0
top_p: 0.95
top_k: 64
num_ctx: 32768
num_predict: 1200
keep_alive: 30m
timeout_seconds: 180
```

The public manifest exposes this profile and its SHA-256, but not credentials.
The application intentionally overrides the model's general-purpose
temperature with `0` for deterministic JSON-Schema comparison. An unavailable
or partially configured provider leaves interpretation unresolved instead of
silently falling back to generated prose. Historical Qwen records remain
append-only research/trial evidence; Qwen is not the active V60 product model.

## Required decision record contract

Every committed decision preserves:

```yaml
decision_id:
decision_type:
subject_ref:
authority:
method:
input_version_refs: []
evidence_refs: []
candidate_refs: []
selected_candidate_ref:
rejected_candidate_refs: []
uncertainty:
counter_evidence_refs: []
gate_receipt:
commit_target:
correlation_id:
causation_id:
created_at:
```

The current database record stores the complete immutable `DecisionRequest`
and `DecisionRoute` inside `record_json`, with authority, method, status,
correlation and causation duplicated into indexed columns. Candidate rejection,
uncertainty and gate-receipt fields remain required before those decision
classes are enabled; they are not fabricated for deterministic outcomes.

## Learning boundary

Runtime evidence may enter an evaluation dataset only after authorization and
de-identification. Training, model evaluation and rule promotion are offline
processes. No runtime interaction may silently update model weights, prompts,
rule profiles or knowledge authority.
