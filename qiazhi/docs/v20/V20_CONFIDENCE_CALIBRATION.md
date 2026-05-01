# V20 Confidence Calibration

V20 confidence calibration is numeric and bounded.

## Contract

A `ConfidenceCalibrationPolicy` can apply domain or readiness offsets to
existing `BaziFeature.confidence` values. It cannot:

- create new features
- rewrite evidence refs
- change question hooks
- mutate rule truth
- create answer conclusions

## Endpoint

```text
GET /api/v20/features/confidence-calibration
```

Future Bayesian calibration can propose offsets from synthetic validation,
coverage gaps, anonymized feedback, and shadow-run deltas. Promotion still
requires artifact, evaluation, and decision records.
