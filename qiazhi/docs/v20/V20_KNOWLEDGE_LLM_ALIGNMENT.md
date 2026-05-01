# V20 Knowledge And LLM Alignment

V20 starts as a clean directory and treats the knowledge base and LLM as governed subsystems instead of late-stage answer helpers.

## Knowledge System

Knowledge is a reviewed evidence layer. It can support feature explanation, question routing, and answer context, but it cannot activate rules or create conclusions.

Current V20 knowledge contracts:

- `KnowledgeUnit`: reviewed source unit with domain, source refs, feature hooks, question hooks, evidence template, and boundary.
- `KnowledgeRef`: runtime-safe citation object selected from reviewed units.
- `KnowledgeRetrievalReport`: feature-spine retrieval result with guardrails.
- `KnowledgeCatalog`: read-only catalog of domains, feature hooks, question
  hooks, retrieval tags, duplicate ids, and audit status.
- `knowledge_feature_alignment`: audit that every runtime feature domain has reviewed knowledge coverage.
- `audit_default_knowledge_units`: baseline check for review status, evidence templates, and forbidden direct-rule usage.

The current covered domains are:

- `strength`
- `useful_god`
- `ten_god`
- `element`
- `branch`
- `time`
- `wealth`
- `career`
- `relationship`
- `health`
- `pattern`

Later V20 phases can add embedding retrieval and multilingual terminology maps, but every retrieved unit must remain reviewed and evidence-only.

`GET /api/v20/knowledge/catalog` exposes this coverage without activating
rules or connecting to an external vector store.

## LLM System

LLM is a controlled collaborator. It can improve interaction, routing, clarity, multilingual rendering, feedback summaries, and safety review, but it cannot own Bazi facts or mutate rule truth.

Current V20 LLM contracts:

- `intent_parse`: turns user text into routing hints and candidate domains.
- `question_suggestion`: suggests from existing feature-backed question candidates.
- `feature_candidate_proposal`: proposes domains for review without writing runtime features.
- `answer_plan_assist`: helps organize verified answer-plan material.
- `answer_plan_rewrite`: rewrites only verified answer plans.
- `multilingual_render`: renders verified answers across locales without adding claims.
- `feedback_summary`: summarizes feedback for later validation.
- `safety_review`: performs advisory safety review while deterministic validators keep final authority.

LLM output is always checked for forbidden claims and internal identifier leaks before it can be user-facing. Failed output falls back to deterministic V20 text.

## Runtime LLM Assist

`llm_assist` is now part of the V20 runtime response:

- `user_text` is parsed as a routing hint, not as evidence.
- LLM question suggestions can route to an existing feature-backed
  `QuestionCandidate`, but cannot create unsupported questions.
- LLM feature candidates remain `proposal_only`; the compiler owns runtime
  `BaziFeature` creation.
- `llm_assist.context_pack` now packages bounded prompt inputs for intent
  parsing, question suggestion, feature candidate proposal, answer-plan
  rewriting, and safety review. It is internal assistive context, not
  publishable output.
- Answer text receives deterministic safety review before publication.
- English and Korean answer rendering use deterministic V20 terminology maps
  before any future LLM rewrite is allowed.

When `user_text` is absent, `llm_assist.status` stays `idle`; the runtime still
attaches an answer safety review so UI and server layers can rely on the same
guardrail surface.

## Core Boundary

The V20 mainline remains deterministic:

```text
ChartFacts
-> CoreInference
-> RulePath candidates
-> BaziFeature[]
-> KnowledgeRef[]
-> QuestionCandidate[]
-> EvidencePack
-> AnswerPlan
-> deterministic answer or validated LLM rewrite
```

This preserves the P84 feature spine while making knowledge and LLM stronger, cleaner, and easier to validate.
