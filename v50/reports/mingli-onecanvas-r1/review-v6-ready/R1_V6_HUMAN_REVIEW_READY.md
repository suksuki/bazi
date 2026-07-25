# R1 v6 Human Review Build Ready

```yaml
date: 2026-07-20
status: READY_FOR_UNGUIDED_HUMAN_REVIEW
machine_prerequisite: PASS
review_build_hash_locked: true
human_sessions_started: false
production_deployed: false
```

## What Changed

The v5 preparation dry run correctly blocked recruitment because the active
surface reduced the canonical Solver's `0 / 1 / many` contract to a single
happy path. This build closes only that projection gap.

```text
TargetDraft
→ server-owned Chart Constraint Solver
→ no_solution | single_solution | multiple_solutions
→ faithful R1 product state
```

- `multiple_solutions` displays complete legal variants and requires an
  explicit choice;
- the first candidate is never selected automatically;
- order is disclosed as presentation order, not professional ranking;
- `no_solution` displays the server conflict and only server-provided
  releasable constraints;
- releasing a constraint recompiles on the server;
- cancel leaves the current chart and formal authority unchanged.

No calendar, Jiazi, DaYun, Relation, Path, Reasoner or LifeCase algorithm was
added or changed for this slice.

## Review Routes

The normal review surface is:

```text
/experience-static/active/onecanvas-r1/index.html
```

The two anonymous deterministic preparation tasks are:

```text
/experience-static/active/onecanvas-r1/index.html?r1ReviewTask=4
/experience-static/active/onecanvas-r1/index.html?r1ReviewTask=5
```

Task 4 produces six legal complete variants. Task 5 produces a server-owned
year/month conflict; releasing the month constraint produces twelve legal
variants without selecting one.

## Machine Verification

```text
focused projection and R1 authority tests: 30 passed
full Python regression:                     438 passed
Experience TypeScript typecheck:            PASS
JavaScript syntax checks:                   PASS
```

`npm test` is not defined in this repository; it was not treated as a failed
verification command.

## Browser Verification

Desktop and 390 x 844 were exercised against a fresh local server.

Verified behavior:

- six candidates are all visible and none is preselected;
- explicit selection applies the chosen complete chart and enters Sandbox;
- the no-solution state identifies the conflict;
- only `month.pillar` and `year.pillar` are offered as releasable constraints;
- releasing `month.pillar` recompiles to twelve candidates;
- cancel restores the untouched formal chart;
- no horizontal overflow at 390px;
- no browser console errors.

Evidence:

```text
evidence/r1-task4-desktop.png
evidence/r1-task5-desktop.png
evidence/r1-task4-mobile-390.png
evidence/r1-task5-mobile-390.png
```

## Gate State

```yaml
L2_authority_consolidation: CLOSED_PASS
R1_machine_gate: PASS
R1_preparation_gate: PASS
R1_human_product_gate: READY_PENDING_EXECUTION
architecture_consolidation_gate: NOT_PASSED
RA1: BLOCKED
full_C2: BLOCKED
professional_blind_gate: PENDING
production_release: BLOCKED
```

The next and only authorized product action is the protocolled review with two
professional analysts and five first-time users. This report is not a human
product `PASS`.
