# V20 Mainline Training Findings

Date: 2026-05-02

## Completed Runs

- Full deterministic corpus precompute completed for `518400` cases.
- Artifact build completed for run `v20_full_518k_mainline_20260502`.
- Training iteration completed with dynamic decision training, practitioner calibration training, synthetic rule training, rule subcondition split, decision registry review, rule/portrait batch, corpus preview, and decision training plan.

## Findings

The full run was useful because it exposed two modeling errors that were hard to see from a few hand-picked charts:

- Wealth material was effectively present in every case when hidden stems were treated the same as visible stems. This made wealth portraits and wealth questions over-dominant.
- Useful-god candidate count was measured by counting `useful_god` feature rows, so it was almost always `2` instead of the real number of candidate paths.
- Corpus artifacts did not record `mainline_keys` and `mainline_domains`, so the training reports could not directly show whether the runtime mainline was drifting toward one domain.

## Correction

Runtime now separates wealth into three levels:

- `visible`: visible wealth stem exists and may enter wealth mainline review.
- `hidden_only`: wealth exists only in hidden stems and remains a boundary or latent material until there is activation,透出, or chain evidence.
- `not_visible`: no direct wealth material is present.

The 518K label snapshot now records:

- `wealth_material_level`
- `wealth_feature_present` only for visible wealth material
- real `useful_god_candidate_count`
- `mainline_keys`
- `mainline_domains`
- `mainline_count`

The corpus artifact cluster key now includes wealth material level and mainline domains, so future corpus summaries can reveal mainline bias instead of hiding it inside broad feature domains.

## Guardrail

The 518K corpus remains a prior, coverage, retrieval, clustering, and calibration artifact. It is not a destiny truth set and must not directly promote rules or conclusions.

## Next Work

1. Rebuild a small corpus artifact sample and verify mainline distributions.
2. Re-run the full 518K precompute with the current runtime when full mainline distributions are needed, then rebuild artifacts with `--no-sqlite` unless a disposable local similarity cache is explicitly required.
3. Continue tightening domain gates for career, relationship, health, pattern, and useful-god paths in the same style: visible evidence, hidden material, chain evidence, and practitioner review must be separated.

## Verification Update

Local sample run `v20_mainline_sample_20260502` rebuilt `240` current-runtime snapshots and artifacts after the correction:

- `wealth_material_level`: `visible=128`, `hidden_only=97`, `not_visible=15`.
- `wealth_feature_present`: `true=128`, `false=112`, so hidden-only wealth no longer counts as visible wealth material.
- `useful_god_candidate_count`: `2=87`, `3=153`, so candidate count is no longer a fixed feature-row count.
- `mainline_domains` and `mainline_keys` are present in coverage summary, cluster keys, flat labels, and similarity metadata.

The existing full run `v20_full_518k_mainline_20260502` completed successfully, but its snapshots and artifacts were built before this correction and still show the old fixed wealth/useful-god distributions. Treat that full run as stale for mainline distribution analysis until the 518K snapshots are regenerated with the current runtime and artifacts are rebuilt from those current snapshots.
