# V20 Policy Review Gate

V20 can now review draft learning policies without activating them.

## Endpoints

- `GET /api/v20/learning/policy-review`
- `POST /api/v20/learning/policy-review`

Supported policy types:

- `question_ranking`
- `knowledge_retrieval`
- `confidence_calibration`

## Flow

Policy review creates a draft `LearningProposal`, an `ArtifactRecord`, a
synthetic validation summary, and a `active_iteration_policy` result. Artifacts are not
production eligible by default. A decision record and rollback plan are required
before any scoped runtime use.
