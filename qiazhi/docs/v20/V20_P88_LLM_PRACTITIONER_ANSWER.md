# V20 P88 LLM Practitioner Answer

P88 upgrades the LLM from a simple rewrite helper into an evidence-bounded Bazi practitioner answer engine.

## Core Idea

The system still owns facts and structure:

```text
ChartFacts
-> FeatureLayer
-> KnowledgeSemanticModel
-> FeatureDiscovery
-> PortraitIntelligence
-> RuleCandidateSupport
-> AnswerPlan
```

After that, LLM may act as a practitioner-style answer composer. It receives only verified context and must return structured JSON:

- `text`
- `mainline`
- `question_answer`
- `evidence_notes`
- `next_questions`
- `boundary_notes`

## Runtime Mode

Use `llm_mode="practitioner"` to request the new lane.

If the provider is disabled, unavailable, times out, or fails validation, V20 uses the deterministic answer.

## Boundaries

LLM may:

- organize the answer like a practitioner
- emphasize the discovered feature mainline
- explain the selected question in natural language
- suggest follow-up questions from the supplied context
- state uncertainty and evidence boundaries

LLM may not:

- create chart facts
- invent stems, branches, ten-gods, or time layers
- activate rule candidates
- output fixed good/bad conclusions
- generate unsupported events, private facts, or guaranteed outcomes
- leak internal ids

## Why This Matters

This keeps V20's deterministic spine and evidence gates intact while letting LLM provide the thing it is good at: professional synthesis, conversational flow, and readable practitioner-style explanation.
