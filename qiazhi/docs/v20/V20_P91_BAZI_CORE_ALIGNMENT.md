# V20 P91 Bazi Core Alignment Gate

P91 turns "stay focused on Bazi measurement" into a runtime contract.

Rules, portrait axes, and recommended questions now share one alignment policy:

```text
BaziFeature[]
-> Bazi-domain alignment
-> rule candidates / portrait projection / question ranking
```

## Allowed Focus

Core Bazi domains:

- day-master strength
- ten-god structure
- useful-god candidate paths
- five-element distribution
- branch relations
- wealth-star material
- pattern review
- explicit time layers

Applied domains remain supported, but only as projections over core features:

- career -> ten-god, pattern, strength, branch
- relationship -> ten-god, branch, strength
- health -> element, strength, branch, pattern

## Hard Blocks

The alignment gate blocks candidates that:

- use unknown domains
- create unknown question keys
- lack feature evidence
- route applied domains without core feature anchors
- contain off-topic or verdict-style wording

This prevents strange questions, loose portrait labels, and rule candidates that
drift away from the Bazi chart.

## UI Effect

Question titles are now cleaner. Buttons point to the measurement topic, while
detailed values such as support scores and element spreads remain in the answer
and evidence sections.

## API

The active policy is visible at:

```text
GET /api/v20/measurement/bazi-domain-alignment
```
