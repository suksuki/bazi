# V20 P89 Chart-Specific Features And Rule Collision

P89 addresses the mainline gap where many charts produced similar question
sets because the feature spine was still too coarse.

## Problem

Before P89, V20 could reliably produce broad features:

- strength
- useful-god candidate gate
- ten-god visible/hidden material
- element balance
- branch relation availability
- time context
- wealth material

Those were safe, but too generic. Question ranking could only reorder broad
topics, so different charts often surfaced similar questions.

## Runtime Upgrade

The feature compiler now adds chart-specific salience features:

- ten-god focus features, such as a repeated or visible `正财`, `偏印`, `七杀`
- element emphasis features, such as `木偏显` or `金偏弱`
- branch relation-type focus features, such as visible `冲`, `合`, `破`
- time-layer relation focus features when luck/flow pillars are supplied
- time-layer ten-god focus features

Feature Discovery gives those features an explicit `chart_specific_salience`
source and a bounded specificity weight. This remains ranking-only; it does not
create facts, activate rules, or produce conclusions.

## Question Upgrade

Recommended questions keep the same feature-backed question keys, but their
titles now include chart-specific material. Examples:

- `正财（明透）、偏财（藏干）...，财运结构边界是什么？`
- `年柱子与日柱午冲...，地支互动怎么分层？`
- `时间干支：甲申、丙午...，时间层触发什么？`

This keeps compatibility with tests, UI routing, corpus labels, and stored
question-key analytics while making the user-facing questions feel like they
come from the current chart.

## Rule Collision Upgrade

Rule candidates are still shadow-only, but they now report the current chart
features they match:

```text
KnowledgeRuleProposal
-> feature_hook_prefix_match
-> matched_feature_ids / matched_feature_labels
-> answer-visible shadow collision summary
```

This makes the rule layer less weak without promoting it to runtime authority.
The user can see that a rule candidate has collided with current chart
features, while V20 still requires synthetic validation and decision approval
before any rule can become user-visible rule truth.

## Next Step

The next useful intelligence step is not a black-box neural model yet. It is a
trained or semi-trained ranker over these richer feature signatures:

```text
chart-specific features
+ knowledge semantic hooks
+ rule collision counts
+ portrait axes
+ 518K cluster priors
+ user question/feedback behavior
-> question ranking and answer emphasis
```

Once this target is stable, neural retrieval, graph embeddings, or learning-to-
rank models have meaningful inputs to learn from.
