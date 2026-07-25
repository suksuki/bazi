# Mingli Interactive Canvas C0 Audit v1

Status: **PASSED**  
C0 Gate: **PASS**

## Observed Data

```json
{
  "baseline_spec_id": "canvas-spec-9bd3bfa29386e8e51b4d0a59",
  "luck_spec_id": "canvas-spec-c786ac667dbcf637d7fa7192",
  "year_spec_id": "canvas-spec-f4207dd2e137810591a8c72b",
  "hypothetical_spec_id": "canvas-spec-ab366a311c5c2b811a0e7ac5",
  "formal_to_hypothetical_diff_id": "canvas-diff-290fbc711f2fdae4023b1b94",
  "semantic_diff_counts": {
    "introduced": 1,
    "removed": 1,
    "activated": 1,
    "reinforced": 1,
    "weakened": 1,
    "blocked": 1,
    "reopened": 1,
    "unchanged": 1
  },
  "trace_count": 34,
  "source_mode_counts": {
    "canonical": 10,
    "committed": 1,
    "derived": 17,
    "hypothetical": 6
  },
  "epistemic_status_counts": {
    "blocked": 2,
    "candidate": 5,
    "committed": 1,
    "derived": 7,
    "fact": 13,
    "hypothetical": 6
  },
  "role_disclosure": {
    "member": {
      "committed_paths": [
        "path-committed-output-pressure"
      ],
      "candidate_paths": [],
      "blocked_paths": [],
      "disclosed_object_count": 22
    },
    "practitioner": {
      "committed_paths": [
        "path-committed-output-pressure"
      ],
      "candidate_paths": [
        "path-candidate-direct-earth"
      ],
      "blocked_paths": [],
      "disclosed_object_count": 25
    },
    "research": {
      "committed_paths": [
        "path-committed-output-pressure"
      ],
      "candidate_paths": [
        "path-candidate-direct-earth"
      ],
      "blocked_paths": [
        "path-blocked-template-reading"
      ],
      "disclosed_object_count": 26
    }
  }
}
```

## Contract Checks

- PASS `same_input_same_spec`
- PASS `same_sandbox_replay_same_spec`
- PASS `restore_returns_formal_spec`
- PASS `every_trace_has_source`
- PASS `all_eight_diff_semantics_present`
- PASS `natal_slots_remain_immutable`
- PASS `sandbox_does_not_write_chart`
- PASS `sandbox_does_not_write_life_case`
- PASS `member_cannot_see_candidate`
- PASS `member_cannot_see_research_block`
- PASS `practitioner_sees_candidate_not_research_block`
- PASS `research_sees_blocked_path`
- PASS `official_diffs_are_independent`

## Interpretation

C0 proves deterministic, traceable Spec/Diff/Context compilation without a renderer.

## Recommendation

`authorize C1 read-only six-pillar canvas`

## Boundary Status

- `runtime_modified`: `false`
- `reasoner_modified`: `false`
- `life_case_modified`: `false`
- `ui_modified`: `false`
- `mingli_algorithm_modified`: `false`
- `llm_used`: `false`
- `sandbox_writes_formal_state`: `false`

## Reproduce

```bash
PYTHONPATH=packages:apps ../.venv/bin/python scripts/v50_audit_mingli_canvas_c0.py
```
