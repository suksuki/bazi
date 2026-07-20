# RA0-518K Chart Realizability Audit v1

> Read-only deterministic audit. No LLM, database migration, formal algorithm change, or source-corpus deletion.

## Executive Finding

The historical V30 `518K` implementation is a validation target contract, not an entity corpus of 518,400 four-pillar charts. Its generated rows rotate day masters and do not contain four pillars. RA0 therefore rebuilt the requested structural universe from the current formal V50 Jiazi, Five Tigers, and Five Rats rules, as explicitly authorized when no entity corpus exists.

## Source Discovery

- Entity 518K corpus found: `False`
- Actual entity rows found: `0`
- Legacy claimed target count: `518400`
- Legacy validation runs: `608`
- Legacy artifact files: `1217`
- Legacy four-pillar schema present: `False`
- Legacy Five Tigers / Five Rats applied: `False / False`

## Structural Reconciliation

- Formula: `60*12*60*12` = `518400`
- Unique ChartKeys: `518400`
- Duplicates: `0`
- Structurally valid: `518400`
- Structurally invalid: `0`
- Universe content SHA-256: `05c97a1518ff840ef3d4955f92dd0a22de9c4729ef7ff2ec8601efbcb14a454c`

## Calendar Realizability

| Range | Realizable | Unseen in range | Boundary-sensitive charts |
|---|---:|---:|---:|
| 1984 LiChun to 2044 LiChun | 264355 | 254045 | 23978 |
| Current product full supported civil-date range | 515576 | 2824 | 47579 |
| Four Jiazi cycles: 1804 LiChun to 2044 LiChun | 518400 | 0 | 48478 |

- Calendar days scanned: `108443`
- Canonical resolver calls: `176040`
- Actual timestamp structural failures: `0`
- Canonical raw late-Zi rejections retained as boundary evidence: `4019`
- Jie boundaries audited: `3563`

`BOUNDARY_AMBIGUOUS` is recorded orthogonally in `boundary_status`; it never turns a structurally valid chart into `STRUCTURALLY_INVALID`.

## Temporal Policy

- Policy hash: `3d7af5b188bd444649ff0f2d693d498162ca4e331407554d16a6906326365215`
- Calendar profile: `lunar_python.sect2.v1`
- Formal day rollover: `midnight_lunar_python_sect_2`
- Sensitivity policy: `late_zi_lunar_python_sect_1_read_only_comparison`
- Timezone: `Asia/Shanghai`
- True solar time: `not_applied`
- Historical DST: `not_normalized_by_birth_pillar_engine_local_civil_input_used_as_supplied`

## Performance

- Pure compute: `96.988686` seconds
- Total elapsed: `101.903206` seconds
- Peak RSS: `68485120` bytes
- Deterministic rerun: `PASS`

## Classification Decision

1. Structural impossibility is determined only by Jiazi, Five Tigers, and Five Rats failures, not by finite-range nonappearance.
2. `UNSEEN_IN_RANGE` remains a range-scoped observation and is not deleted.
3. Structurally invalid counterexamples and boundary-policy divergences remain Negative Fixtures.
4. Structurally valid unseen rows remain theoretical synthetic candidates until stronger evidence exists.

## Reproduce

```bash
PYTHONPATH=packages:apps .runtime/venv/bin/python scripts/v50_run_ra0_518k_realizability_audit.py --output-root .runtime/validation/ra0-518k-realizability-v1
```
