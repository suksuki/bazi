# V20 P86 Feature Discovery Intelligence

P86 moves V20 from "feature spine exists" to "runtime intelligence routes by discovered features".

## Core Position

`FeatureDiscovery` is the V20 runtime intelligence layer. It does not replace chart facts, feature compilation, knowledge review, or validation. It fuses their outputs into ranked feature and domain hypotheses that can drive:

- recommended question order
- portrait emphasis
- answer planning context
- analyst review
- shadow learning and training loops

It is intentionally bounded: it reorders and explains; it does not create chart facts, activate rule truth, or output unsupported fortune verdicts.

## Signal Sources

- `BaziFeature[]`: deterministic feature spine from the compiler.
- `KnowledgeRef[]`: reviewed knowledge boundaries and evidence context.
- `PortraitProjection`: feature-backed portrait axes and calibration surface.
- `ShadowRuleCandidates`: knowledge-to-rule proposals and bounded ranking signals.
- `Interaction`: user text, selected question, and bounded LLM routing assist.
- `518K Corpus Training`: portrait-axis priors, rule-proposal selectivity, and similarity-index readiness.

## Runtime Flow

```text
ChartFacts
-> CoreInference
-> RulePath candidates
-> BaziFeature[]
-> preliminary KnowledgeRef[] + PortraitProjection
-> ShadowRuleCandidateRanking
-> FeatureDiscoveryReport
-> FeatureDiscoveryQuestionPolicy
-> QuestionCandidate[]
-> selected question / bounded LLM assist
-> final KnowledgeRef[] + PortraitProjection
-> final FeatureDiscoveryReport + validation
-> AnswerPlan
```

## Training Boundary

The 518K corpus is now read as a shadow training prior during runtime. It can influence small, capped ranking weights and analyst-visible discovery explanations. It cannot:

- generate destiny labels
- mutate core rules
- promote rule candidates
- override deterministic chart facts
- create user-visible conclusions without evidence gates

## Why This Matters

The knowledge base, portrait system, interaction system, and question ranking now coordinate around one shared intelligence artifact. This is the main V20 path toward a system that can intelligently find the important Bazi features first, then ask and answer from that structure.
