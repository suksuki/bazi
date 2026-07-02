# V40 Phase 60: Probe V2 And Mingli Candidate Board

Date: 2026-07-02

## Source

This phase adopts the latest product analysis for V40 Practitioner Lens and Probe:

```text
Probe should become Event Probe / Timeline Probe, not only abstract manifestation calibration.
Practitioner Lens should become a system assertion candidate selector, not a passive feedback panel.
```

## Mainline Goal

V40 keeps the report-first product flow, but upgrades the professional layer:

```text
Decision / Projection
  -> SystemAssertionCandidate
  -> Mingli Candidate Board
  -> Practitioner selection
  -> Local overlay + training label
  -> Probe V2 when more reality evidence is needed
```

The ordinary user still sees only:

```text
核心报告
继续追问
必要时一个校准问题
```

The practitioner sees a contextual candidate board on the same reading page.

## Probe V2

Probe is no longer just a broad question. Each Probe must carry an explicit target:

```text
probe_type
target_branch_ids
target_verdict_ids
target_domains
target_years
target_hidden_attribute_ids
options
impact_preview
```

Probe types:

```text
manifestation  - confirm the real-life manifestation pattern
timeline       - confirm which year or period is most obvious
event          - confirm what kind of event happened
luck_transition - confirm how a luck-cycle shift felt
```

V40 Phase 60 starts with:

```text
manifestation probes for every selected product topic
timeline probes for career / wealth / relationship / timing topics
```

## Mingli Candidate Board

The Practitioner Lens exposes a `candidate_board`:

```text
candidate_board
  version: v40.mingli_candidate_board.v1
  groups:
    命局骨架
    财富断项
    事业断项
    感情断项
    时运断项
    健康断项
    隐藏线索
  candidates:
    candidate_id
    candidate_type
    topic
    title
    summary
    current_status
    confidence_label
    target_type
    target_ids
    suggested_probe_question
    impact_preview
    available_actions
```

Candidate actions use product language:

```text
采为主断
作为辅助
暂不采用
需要追问
用户反馈不符
添加备注
```

Internal action keys remain compatible with the existing training loop:

```text
more_like_this
supporting_context
do_not_use_now
ask_to_confirm
user_mismatch
note
```

## Selection Runtime

Practitioner selection does not mutate chart facts.

```text
selection
  -> TrainingLabelEvent
  -> LocalOverlay
  -> optional ProbeCandidate
```

Phase 60 keeps global weight changes out of the user app. The existing direct-training principle still applies after validated training jobs: validated policy updates may activate immediately with rollback and repair records.

## UI Contract

The user app remains:

```text
report-first
conversation after report
one-question-one-answer
Probe only when useful
Practitioner Lens as a drawer on the same report
```

When a practitioner clicks `需要追问`, the UI creates a visible Probe card for the user instead of silently logging a note.

Each Lens candidate displays a short impact preview:

```text
选择这个断项会影响财富结论、建议方向、下一条校准问题。
```

## Tasks

1. Extend `ProbeCandidate` with V2 target and option fields.
2. Generate manifestation and timeline probes in the Decision runtime.
3. Build `SystemAssertionCandidate` and `MingliCandidateBoard` projection contracts.
4. Project branch and probe material into the Practitioner Lens candidate board.
5. Update the UI drawer to show candidate board, impact preview, and product action labels.
6. Make `需要追问` surface a real Probe card.
7. Add focused tests for Probe V2, candidate board projection, and UI strings.

## Done Criteria

- Ordinary users do not see raw ids, policy names, provider/model fields, prompt traces, or candidate-board internals.
- Practitioners can inspect a concise assertion pool and choose an action.
- Probe V2 carries target and option metadata.
- `ask_to_confirm` can turn a Lens candidate into a user-visible Probe.
- The change is covered by focused tests and does not break the existing V40 runtime suite.
