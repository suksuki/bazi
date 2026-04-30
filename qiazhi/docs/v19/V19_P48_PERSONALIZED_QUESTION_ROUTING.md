# V19 P48 Personalized Question Routing

P48 uses the P47 rule graph runtime context to personalize the first guided questions shown for a chart.

## What Changed

The system now builds a `question_personalization_context` inside `guided_question_context`.

It reads:

- selected rule graph routes
- topic lane counts
- domain counts
- selected knowledge IDs
- visible chart facts such as vaults, branch relations, and time relations

It then adjusts question ranking only. It does not change chart inference, income stability, knowledge records, or rule activation state.

## Personalization Logic

Question buckets are ordered from route evidence:

- `branch_time_activation` -> branch relation, time context, vault
- `ten_god_mechanism` -> metadata and income structure
- `wealth_career_bridge` -> income structure
- `core_strength_foundation` -> metadata and structure basis
- `pattern_structure` -> structure basis and boundary
- `blind_lifa_palace` -> vault and branch relation

Visible chart facts can pull key buckets earlier:

- visible branch relation
- visible vault
- visible time relation

Each question receives:

- `personalized_score`
- `personalization.applied`
- `personalization.route_boost`
- `personalization.bucket`
- `personalization.reasons`

## Boundaries

P48 is ranking only:

- no runtime rule activation
- no answer mutation
- no inference mutation
- no prediction text
- no removal of baseline entry questions

This makes the opening question list increasingly chart-specific while preserving stable fallback coverage.
