# V40 Phase 54: User Account And Profile Flow

## Objective

Phase 54 turns `/v40/ui` from a single reading workbench into the first complete user product flow:

```text
register/login
  -> choose or create a bazi profile
  -> run dual-engine report
  -> answer necessary probe
  -> continue concise one-question-one-answer dialogue
```

This phase exists because UI flow is part of product architecture. It cannot be postponed until all engines are "done".

## Product Decisions

### 1. V30 multi-step reading pages are not kept as the V40 user flow

V30's multi-step pages are useful as an internal thinking and practitioner evidence model, but they are too heavy for V40's ordinary user surface.

V40 keeps the staged material internally:

- Bazi facts;
- ten-god structure;
- useful-god candidates;
- rule/path/domain signals;
- Ziwei sidecar signals;
- probe candidates;
- decision output;
- LLM expression;
- training labels.

But the ordinary user sees:

```text
profile -> report -> necessary calibration -> dialogue
```

Practitioners may see more evidence through the lens and future review workbench.

### 2. Dual engine is runtime-first, not UI-step-first

The user does not need a separate "Bazi page" and "Ziwei page".

The report request should send:

- `chart_facts` to the native Bazi engine;
- `ziwei_chart_facts` as a sidecar Domain Lens when a profile/report can provide it.

Ziwei remains:

- sidecar;
- zero decision weight;
- useful for probe triggers, practitioner lens, hidden-attribute calibration and expression context.

### 3. Probe is a required product surface, not chat

Probe answers are reality calibration. They must not become generic conversation.

The report can show one necessary probe after the main report:

- if runtime produced an `ask_now` probe, use it;
- otherwise show a hidden-attribute calibration probe;
- record the answer as current-reading calibration and training material;
- keep verdict and chart facts immutable.

### 4. Dialogue is one question, one answer

The dialogue mode starts after report/probe and is intentionally simple:

- show seed questions;
- user clicks one seed or types one question;
- answer one round;
- generate the next seed questions;
- do not rerun the reading;
- do not auto-start conversation.

## Scope

Phase 54 includes:

- user registration and login for `user` and `practitioner`;
- admin cannot register in the user app;
- multi-user session cookies;
- per-user Bazi profile CRUD;
- profile selection that fills the reading form;
- report request includes Bazi plus Ziwei sidecar facts;
- the user UI separates account, profile, report, probe and dialogue;
- project status moves to Phase 54.

Phase 54 does not include:

- Admin Control Plane changes;
- production-grade password reset or OAuth;
- public billing;
- final practitioner workbench;
- V30 UI copy/paste.

## Data Boundary

New user-facing data is V40-only:

```text
v40_user_accounts
v40_user_sessions
v40_bazi_profiles
```

These tables must not read or write V30 users, profiles or runtime state.

## Acceptance

- `/v40/ui` exposes a clear auth/profile/report/probe/dialogue flow.
- Registration rejects `admin` as a user-app role.
- Login creates a multi-user session and sets user-app cookies.
- Profiles are scoped by user session.
- Native report receives `ziwei_chart_facts` from the selected profile or generated sidecar.
- Probe can record hidden-attribute calibration before or alongside dialogue.
- Conversation remains one-turn-at-a-time and report-grounded.
- Focused tests, visual QA and full V40 tests pass.

