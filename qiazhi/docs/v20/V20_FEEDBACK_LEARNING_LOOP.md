# V20 Feedback Learning Loop

V20 now accepts feedback as a governed learning signal, not as runtime truth.

## Endpoints

- `GET /api/v20/learning/registries`
- `POST /api/v20/feedback/analyze`

## Flow

Feedback analysis produces:

- anonymized `source_hash`
- redacted summary
- LLM-assisted domain summary using bounded contracts
- `FeatureCalibrationSignal[]`
- draft `LearningProposal`
- append-only `LedgerEntry`

Raw feedback is not retained by the runtime response. Calibration signals must
pass validation, registry review, and decision records before any scoped runtime
use. Feedback can improve ranking, retrieval, calibration, and coverage review;
it cannot mutate core rules, chart facts, feature compiler output, or final
Bazi conclusions.
