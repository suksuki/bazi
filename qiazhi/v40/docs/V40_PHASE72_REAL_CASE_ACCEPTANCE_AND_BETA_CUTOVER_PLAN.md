# V40 Phase 72: Real Case Acceptance And Beta Cutover Plan

## System Review

V40 has reached the product-acceptance stage.

The runtime spine is now in place:

- isolated V40 directory, API prefix, storage prefix and tests;
- Bazi as primary engine;
- Ziwei as sidecar Domain Lens;
- DecisionEngine as the only verdict authority;
- LLM as required product expression layer, not verdict authority;
- training applies immediately after validated batch training, with rollback evidence;
- real case bank, acceptance window, real case expansion evidence, direct training activation evidence and online cutover decision pack.

The remaining bottleneck is no longer framework shape. It is real acceptance evidence.

## Completion Snapshot

```text
Architecture spine: 99%
User beta surface: 99%
Training / validation loop: 98%
V30 replacement readiness: 99%
Current overall: 99%
```

The last 1% is intentionally not automatic. It needs real cases, owner signoff and a beta cutover window.

## Mainline Decision

Phase 71 completed the online cutover decision pack. The next mainline is:

```text
USER-18: real case quality signoff and beta cutover window
QA-19: live LLM report/conversation acceptance on selected real cases
OPS-20: rollback rehearsal and beta traffic smoke
```

## Phase 72 Goal

Create the acceptance path that turns V40 from "architecturally ready" into "product ready for beta."

Phase 72 should answer four concrete questions:

1. Do real cases produce useful verdicts and advice?
2. Does LLM expression make the result clearer without polluting facts?
3. Do training updates explain their impact and remain rollbackable?
4. Is the beta cutover window safe enough for owner approval?

## Task Plan

### P72-1 Real Case Acceptance Pack

Build a read-only pack that merges:

- selected real cases;
- latest Acceptance Window;
- Real Case Expansion Evidence;
- Online Cutover Decision Pack;
- failed reason counts;
- domain coverage;
- trainable attribution hints.

Output:

```text
ready_for_owner_review
needs_more_cases
needs_replay
blocked_by_quality
```

Boundary:

```text
No traffic switch.
No V30 writes.
No chart fact mutation.
No production policy write.
```

### P72-2 LLM Real Reading QA

Run real-case report and conversation acceptance with the actual LLM path.

Checks:

- no silent fallback;
- clear conclusion and advice;
- no engineering-language leakage;
- no overclaim;
- conversation remains one-question-one-answer;
- Probe appears only when it adds information value.

### P72-3 Training Impact Review

For accepted real-case feedback, compile:

- which trainable units changed;
- before/after policy values;
- affected verdicts, advice, probes and expression rules;
- rollback registry;
- next replay action.

Training remains high-iteration: validated training applies immediately, and rollback is the rescue path.

### P72-4 Beta Cutover Window

Prepare the owner-facing beta cutover window:

- selected beta profile set;
- active policy version;
- rollback pointer;
- LLM provider/model check;
- smoke URL and status;
- final owner signoff fields.

The system may recommend a window, but it must not switch traffic automatically.

## UI Direction

User-facing UI should stay report-first:

```text
命盘 / 报告 / 当前对话
```

During beta acceptance:

- left sidebar shows current chart, report history and acceptance status;
- main surface shows either report or current conversation, not both at full weight;
- practitioner lens shows only useful branch choices and calibration notes;
- admin/control plane owns training, evidence, readiness and rollback views.

## Acceptance Criteria

Phase 72 is complete when:

1. selected real cases can be bundled into a single acceptance pack;
2. pack identifies blockers and next actions without manual spreadsheet work;
3. LLM real reading QA is explicit and cannot silently fallback;
4. training impact and rollback path are visible;
5. beta cutover recommendation still requires owner signoff;
6. V40 full test suite passes.

## Boundary

Phase 72 plans and prepares acceptance. It does not replace the final owner decision.
