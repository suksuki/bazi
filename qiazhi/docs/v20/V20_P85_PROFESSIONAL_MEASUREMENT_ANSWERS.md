# V20 P85 Professional Measurement Answers

P85 deepens the V20 answer mainline without changing chart facts, feature truth,
or rule activation.

The user-facing answer path is now:

```text
QuestionCandidate
-> DomainReadingSection[]
-> KnowledgeEvidenceSupport
-> RuleCandidateSupport
-> Feature-backed AnswerSection[]
-> EvidencePack
-> deterministic answer
-> bounded LLM rewrite
```

## Goal

V20 must feel like a Bazi measurement system, not a generic safety template.
The answer layer now adds a professional reading path before listing individual
features. This path explains how a domain should be measured from compiled
features:

- wealth: wealth material, day-master capacity, structure channel, timing context
- career: ten-god role material, capacity, branch interaction, pattern review
- relationship: ten-god relationship material, branch interaction, capacity
- health boundary: five-element balance and structural pressure only
- time: explicit time pillars, ten-gods, and natal-time branch relations
- useful-god: candidate paths plus evidence gaps
- ten-god: visible and hidden source layers

## Boundaries

- Domain sections are projections over `BaziFeature[]`; they never create facts.
- LLM may rewrite only the verified answer text.
- Wealth, career, relationship, health, and timing sections do not produce fixed
  events, fixed fortune verdicts, medical claims, or unsupported timing.
- `q_income_stability` is now a stable applied-domain question, so wealth reading
  is not lost when the recommendation list is crowded.

## Tests

P85 adds runtime tests for:

- applied-domain wealth answers using the professional reading path
- time answers preserving explicit trigger material
- reviewed knowledge evidence support inside answer plans
- shadow-only rule candidates inside answer plans
- no internal feature IDs leaking into user-facing answers

## P85-2 Knowledge Evidence

Professional reading paths now receive `KnowledgeRetrievalReport` from the
runtime. User-facing answers expose only safe Chinese knowledge labels and usage
boundaries, such as:

- 财星材料边界
- 十神解释边界
- 日主强弱证据边界
- 时间层触发边界

The original knowledge IDs, English templates, and rule hooks remain internal.
Knowledge still cannot activate rules or create conclusions; it only supports
the reading path and evidence boundary.

## P85-3 Rule Candidates

Professional reading paths now also receive a compact
`RuleCandidateSupport` report. It is built from reviewed knowledge rule
proposals and stays shadow-only.

User-facing text may show safe labels such as:

- 财星材料规则候选
- 时间层触发规则候选
- 事业投影规则候选

Each candidate exposes only:

- a readable label
- a collision-condition summary
- validation requirements
- shadow status

The condition model, feature hooks, and promotion details remain internal. A
candidate rule cannot create a verdict or mutate runtime behavior until future
synthetic validation, decision registry approval, and promotion gates pass.

## P85-4 Validation And Ranking Loop

Rule candidates now feed two bounded runtime surfaces:

- `rule_candidate_validation`: checks that selected candidates remain
  shadow-only, carry collision-condition summaries, and still require
  validation before promotion.
- `rule_candidate_ranking`: gives existing `QuestionCandidate[]` rows a small
  bounded reorder signal from available shadow rule candidates.

The ranking signal is reorder-only:

- it cannot create new question keys
- it cannot activate a rule
- it cannot override feature-backed candidates
- each domain adjustment is capped at `0.055`

Synthetic runtime evaluation can now assert expected rule-candidate domains,
which lets golden cases check feature coverage, question coverage, answer text,
runtime mutation invariants, and shadow-rule availability together.
