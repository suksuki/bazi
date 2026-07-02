# V40 Phase 62: Reading History And Conversation Layering

Date: 2026-07-02

## Source

This phase follows the product decision that history belongs in the left rail and conversation should behave like a true question chain:

```text
历史报告放到左边栏，点击可以查阅。
进入智能对话后，问题以 item 形式显示在主页面。
倒序排列，最后的问题在最上面。
当前问题展开，其余问题折叠。
```

## Product Rule

The left rail is no longer only an input area. It carries lightweight product memory:

```text
测算入口
当前命盘
历史报告
```

The main page is still report-first:

```text
setup -> running -> report -> conversation
```

After the user starts conversation, the full report folds away. The page keeps only the compact core judgment and the conversation chain.

## History Scope

Phase 62 intentionally uses current browser / current account local history first.

Reason:

```text
v40_runtime_records currently stores runtime by reading_id but does not yet carry a user ownership contract.
```

Therefore V40 must not expose a global backend reading history list to ordinary users. Cross-device persistent history is queued for the Reading Revision / ownership contract phase.

## Conversation Chain

Conversation turns are rendered as reverse chronological items:

```text
latest question    expanded
older question     folded
oldest question    folded
```

Rules:

1. A new question is inserted at the top.
2. The current question opens immediately.
3. Older questions fold into compact rows.
4. Clicking a folded question opens it and folds the others.
5. Pending LLM answers stay visible as a pending item; no local fallback answer is generated.
6. The conversation does not rerun the reading and does not mutate chart facts.

## UI Boundary

The user page may show:

- report title and core judgment;
- history report list;
- question item chain;
- pending LLM answer state;
- next question chips;
- lightweight Probe when useful.

The user page must not show:

- provider/model names;
- prompt/debug fields;
- policy keys;
- training internals;
- global runtime records across users.

## Done Criteria

- The left rail shows recent history after at least one report.
- Clicking a history item restores the report without calling LLM again.
- Conversation turns are newest-first.
- Only the current/opened turn is expanded.
- Pending turns are visible while waiting for Gemma.
- Full report does not dominate the conversation state.
