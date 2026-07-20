# RA0-518K Audit Evidence

Status: `PASS_WITH_BOUNDARY_FINDING`

This directory retains the small, reviewable evidence from the deterministic
RA0 audit. The full 518,400-row classification remains a reproducible local
runtime artifact to avoid adding generated bulk data to the source baseline.

## Full Classification

- Path: `.runtime/validation/ra0-518k-realizability-v1-final/ra0_518k_classification_v1.jsonl.gz`
- Rows: `518400`
- Size: `9236174` bytes
- SHA-256: `f8cd60c4a8a1ff8fa56726a4166af6bfcddc08bb7bb4e6a7336a942402ec3c9e`
- Uncompressed format: deterministic JSON Lines

The full file can be regenerated with the command recorded in
`ra0_518k_run_manifest_v1.json`. A second independent run produced identical
hashes for the classification, semantic summary, boundary evidence, and
structural anomaly outputs.

## Audit Boundary

- No LLM was called.
- No formal calendar or Bazi algorithm was modified.
- No database migration was performed.
- No historical 518K artifact was deleted or overwritten.
- R1 V6 remained `20/20` hash-valid.
- The Product Kernel Constitution retained SHA-256
  `4908c2865e98ba9e35f12358329fffd0b503ce9edc33cac3cf9d736e2e3caeff`.

The boundary finding is the existing late-Zi inconsistency between the formal
Sect 2 day pillar and the hour stem returned by the calendar dependency at
`23:xx`. RA0 preserves the raw rejection as evidence and uses the existing
formal Five Rats rule only as an audit-side normalization. It does not repair
or silently change the production calendar service.
