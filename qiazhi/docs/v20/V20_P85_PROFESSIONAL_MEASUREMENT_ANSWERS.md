# V20 P85 Professional Measurement Answers

P85 deepens the V20 answer mainline without changing chart facts, feature truth,
or rule activation.

The user-facing answer path is now:

```text
QuestionCandidate
-> DomainReadingSection[]
-> KnowledgeEvidenceSupport
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
