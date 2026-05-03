# V20 I18N Product Completion Plan

## Goal

V20 must become a fully multilingual Bazi reading product for normal users and
practitioners, while keeping admin-only operation screens in Chinese.

The current multilingual work is incomplete: some UI labels are translated, but
many buttons, panels, profile screens, recommended questions, answer sections,
and runtime messages still mix Chinese, English, Korean, and internal debug
phrasing. The final product rule is:

```text
User-facing V20 = zh / en / ko complete localization
Admin-only V20 = Chinese only
Runtime debug / developer traces = admin observation only
```

## Non-Negotiable Principles

1. Locale is selected once at entry and carried through the whole session.
2. Every normal-user and practitioner-facing label must come from an i18n table
   or localized backend payload.
3. Recommended questions must be localized and read like real human questions.
4. Q&A is the highest priority: answer text, follow-up questions, boundaries,
   and evidence summaries must use the selected locale.
5. Admin-exclusive pages and admin observation panels stay Chinese only.
6. Internal rule ids, feature ids, debug states, and raw decision traces must not
   leak into non-admin UI in any locale.
7. Fallback is allowed internally, but user-facing fallback must be readable in
   the selected locale.

## Scope Boundary

### Must Be Multilingual

```text
Entry page
Login / registration / logout messages
Profiles page for ordinary users and practitioners
Workbench page
Chart input labels and placeholders
Measure / generate / send buttons
Smart question buttons
Question list refresh states
Answer panel
Recommended questions
Follow-up questions after each answer
Portrait summaries shown to users
Boundary notes shown to users
Validation and form errors
Loading / empty / failure states
```

### Chinese Only

```text
Admin page
Admin navigation
Observation page
Decision Hits
Latent Factors admin view
Topic Projection admin debug view
Rule hit list
Knowledge/rule import status
Training script status
Artifact registry
Raw JSON/debug panels
System health/admin ops labels
```

Admin-only content can still contain English technical terms when they are code
or model names, for example `FeatureContext`, `DecisionRegistry`, `LTR`, or
`gemma4:latest`.

## Locale Contract

Supported locales:

```text
zh = 中文
en = English
ko = 한국어
```

Resolution order:

```text
URL locale
-> authenticated session locale
-> localStorage v20_locale
-> zh
```

The chosen locale must be sent to every runtime call:

```text
/api/v20/measure
/api/v20/auth/guest
/api/v20/auth/login
/api/v20/auth/register
/api/v20/profiles
/api/v20/learning/*
```

Admin pages ignore locale for display copy and render Chinese.

## Architecture

### 1. Frontend Label Registry

Frontend must not keep scattered per-page dictionaries such as one-off
`ENTRY_TEXT` objects as the long-term source of truth.

Target:

```text
v20/i18n/ui_labels.py
-> /api/v20/i18n/ui-labels?locale=xx&surface=workbench
-> frontend i18n helper
-> page rendering
```

Surfaces:

```text
entry
profiles
workbench
answer
question
portrait
auth
admin_chinese_only
```

### 2. Backend Payload Localization

Backend objects that reach non-admin UI must carry localized display fields:

```text
title
subtitle
label
summary
question_text
boundary_text
empty_text
error_text
```

They may also carry raw ids for tracing, but frontend must hide raw ids outside
admin surfaces.

### 3. Question Localization

Recommended questions must be generated from:

```text
BaziFeatureContext
-> TopicProjection
-> UserIntentTemplate
-> localized QuestionCandidate
```

Forbidden for user-facing questions:

```text
rule title -> question title
feature debug summary -> question title
raw decision_state -> question title
internal id -> question title
```

Each `QuestionCandidate` should contain:

```text
question_key
domain
intent_type
source_feature_ids
answered_state
rank_score
localized_text.zh
localized_text.en
localized_text.ko
localized_reason.zh
localized_reason.en
localized_reason.ko
```

Question wording requirements:

```text
zh: 白话、像命理师在引导，不堆术语
en: natural reading language, not literal Chinese translation
ko: 자연스러운 사주 상담 문장
```

### 4. Answer Localization

Answer generation path:

```text
EvidencePack
-> AnswerPlan
-> deterministic localized answer
-> optional LLM practitioner rewrite in selected locale
-> verifier
-> user output
```

LLM role:

```text
zh: 中文命理师，白话
en: English Bazi practitioner, plain language
ko: Korean Saju/Bazi practitioner, plain language
```

LLM must not translate admin/debug traces. It only rewrites verified answer
context and selected-locale question text.

### 5. Admin Chinese-Only Gate

Admin pages must explicitly force:

```text
display_locale = zh
admin_copy_policy = chinese_only
```

Admin-only panels:

```text
图谱画像总览
主题投射画像
Latent Factors / 命主校准
Decision Hits / 规则命中
Practitioner / 命理师校准
训练与学习状态
规则/知识入库状态
```

These remain Chinese because they are operational tools, not user product copy.

## Implementation Phases

### P0: Inventory And Leak Audit

Scan frontend and backend for hardcoded visible copy:

```text
frontend/*.html
frontend/*.js
answer/*
interaction/*
profiles/*
llm/*
i18n/*
server.py
```

Classify every string:

```text
user_visible_multilingual
admin_chinese_only
internal_debug_hidden
```

Output:

```text
v20/.runtime/i18n/i18n_audit_report.json
```

### P1: Centralize UI Labels

Move all normal-user/practitioner UI copy into the i18n registry:

```text
entry labels
profile labels
workbench labels
answer labels
question labels
auth states
empty/error/loading states
```

Admin labels are kept in Chinese constants.

### P2: Localize Recommended Questions

Refactor question generation so each candidate is localized before reaching the
frontend.

Acceptance:

```text
Same chart + zh -> Chinese human questions
Same chart + en -> English human questions
Same chart + ko -> Korean human questions
Answered questions are removed from the active list in every locale
Follow-up questions refresh after each answer
```

### P3: Localize Answer And Follow-Up Q&A

Ensure `/api/v20/measure` respects locale for:

```text
answer_text
questions[]
llm_assist.practitioner_answer.text
llm_assist.practitioner_answer.next_questions
boundary notes
empty/fallback answer
```

Acceptance:

```text
No Chinese leakage in en/ko answer mode except fixed Bazi technical terms when intentionally preserved.
No English internal ids in zh/ko answer mode.
No raw decision debug text in normal user UI.
```

### P4: Admin Isolation

Admin-only routes and panels should stay Chinese and can show raw traces.

Acceptance:

```text
role=user cannot see admin observation panels
role=practitioner cannot see admin observation panels unless explicitly allowed
role=admin sees Chinese-only admin ops surfaces
```

### P5: Regression Tests

Add locale smoke tests:

```text
zh measure returns Chinese answer and Chinese questions
en measure returns English answer and English questions
ko measure returns Korean answer and Korean questions
admin page remains Chinese
questions refresh and answered question is excluded
```

## Acceptance Checklist

- [x] Entry page has no mixed-language labels.
- [x] Registration uses only user/practitioner roles in selected locale.
- [x] Login has no role selector and messages are localized.
- [x] Workbench buttons, tabs, placeholders, empty states are localized.
- [x] Profile list and profile actions are localized for non-admin users.
- [x] Smart questions are localized and natural.
- [x] Answer text uses selected locale.
- [x] LLM practitioner rewrite uses selected locale.
- [x] Admin observation page is Chinese only.
- [x] Raw rule/feature/decision ids are hidden from non-admin UI.
- [x] Answered questions do not reappear in the active question list.
- [x] Locale persists across page navigation.
- [ ] Server 0.13 and macOS produce consistent locale output for the same input.

## 2026-05-03 Implementation Pass

This pass completes the product-facing i18n loop on macOS and prepares the same
code path for Linux 0.13 deployment.

Completed:

```text
Backend:
- QuestionCandidate is localized before leaving /api/v20/measure.
- selected_question is localized by exact question_id, without resurrecting answered questions.
- en/ko answer sections no longer reuse Chinese section bodies.
- Korean answer copy uses natural "사주 분석 / 프로필 요약 / 주요 판단" wording.

Frontend:
- Workbench chart labels, question controls, buttons, placeholders, profile strip,
  metrics, practitioner collapse controls, empty states, and question cards use
  selected-locale text.
- Profile page navigation, form options, status copy, delete/save messages, and
  role labels use selected-locale text.
- Admin observation and admin-only operation surfaces remain Chinese.

Tests:
- v20/tests/test_v20_i18n_runtime.py verifies en/ko questions and answer text.
- question ranking tests verify answered questions are suppressed and follow-ups
  refresh after each answer.
```

Linux 0.13 acceptance remains open until the pushed commit is pulled and the
systemd V20 service is restarted on `dblife.com`.

## Product Standard

The user should feel:

```text
中文：像中文命理师在直接讲盘。
English: like a clear English-speaking Bazi practitioner, not a translated debug tool.
한국어: 한국어 상담 문장처럼 자연스럽게 읽힌다.
```

The admin should feel:

```text
中文运维和命理调参后台，能清楚看到规则、画像、裁决、学习状态。
```

This is the final i18n direction for V20.
