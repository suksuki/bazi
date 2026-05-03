# V20 Question Agent Model

## Goal

Recommended questions are no longer a static template list.

They are a session-aware agent queue:

```text
ChartFacts
-> RuleDecision
-> BaziFeatureContext
-> TopicProjection
-> PortraitAxis
-> QuestionCandidate
-> QuestionAgentState
-> refreshed next-question queue
```

## Inputs

The question agent consumes:

```text
decision_report
runtime_decision_fusion
portrait_projection
feature_contexts
question_intent_model
answered_question_ids
answered_question_keys
selected_question
```

## Output

The agent returns:

```text
questions[]                 next visible queue
selected_question           the question being answered now
question_agent_state        memory, suppression and follow-up report
```

## Behavior

After a user clicks and answers a recommended question:

```text
1. The selected question is still answered.
2. The selected question id is added to answered memory.
3. The next question list suppresses the answered question.
4. The queue is refreshed with same-domain follow-ups.
5. Remaining questions are re-ranked by decision strength and context.
```

This creates the expected agent loop:

```text
recommend -> answer -> remember -> suppress -> generate follow-up -> recommend next
```

## Human Language Rule

Question titles must be readable user questions, not internal debug text.

Allowed:

```text
这盘的财运，是机会更强，还是承接压力更关键？
事业主线里，规则压力、个人表达和平台资源谁更主导？
当前大运流年先牵动的是事业、财运，还是关系？
```

Blocked:

```text
RuleSpec 裁决主线
条件成立 3/3
evidence.l3...
feature.debug title
```

## Learning Plan

The trainable target is not “generate any question with LLM”.

The trainable targets are:

```text
question priority
follow-up strategy
domain transition
question diversity
answered-question suppression
click-through / continue-depth outcome
practitioner correction outcome
synthetic chart coverage
```

First phase:

```text
deterministic templates
+ answered memory
+ feature-context hooks
+ shadow ranking policy
```

Second phase:

```text
offline LTR / bandit report
+ 518K corpus replay
+ synthetic chart validation
+ promotion gate
```

Runtime learning guardrail:

```text
Learning can reorder and select question candidates.
Learning cannot mutate ChartFacts, rule truth, or answer conclusions.
```

