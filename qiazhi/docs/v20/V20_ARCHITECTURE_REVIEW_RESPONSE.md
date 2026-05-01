# V20 Architecture Review Response

This note records the first implementation response to the V20 architecture review.

## Feature Explosion

Risk: a flat `BaziFeature[]` can grow too large for UI and LLM context.

Response:

- Added `MacroFeature` to the feature schema.
- Added `v20.features.hierarchy.cluster_features`.
- `FeatureLayer` now exposes both `macro_features` and full `features`.
- UI and LLM can use macro features by default and expand subfeatures only when the user drills in.

Rule: macro features are aggregates. Subfeatures remain the source of truth.

## Hard LLM Enforcement

Risk: contract declarations alone do not stop a model from smuggling a claim into natural language.

Response:

- Added `v20.llm.enforcement.hard_enforce_text`.
- Validators now run deterministic literal and regex scans over public text.
- Hidden phrasing such as “你会在未来发大财” triggers fallback even if the JSON shape is valid.

Rule: deterministic hard enforcement has final authority. LLM safety review is advisory.

## Domain Projection Anti-Corruption Layer

Risk: wealth, career, relationship, health, and other applied topics can leak from feature evidence into unbounded domain claims.

Response:

- Added `v20.answer.domain_projection`.
- `AnswerPlan` now includes `domain_projection`.
- Domain projection defines source features, allowed claim types, blocked claim types, and boundary text.

Rule: applied Bazi topics are projections from compiled features. Domain questions cannot directly create verdicts.

## Dataclass vs Pydantic V2

Decision for current phase:

- Keep frozen dataclasses inside the core engine because they are small, dependency-light, immutable, and easy to inspect.
- Reserve Pydantic V2 for public API schemas, storage boundaries, service requests, and migration-heavy integration surfaces.

Migration trigger:

- introduce FastAPI V20 endpoints,
- expose OpenAPI contracts,
- accept external client payloads,
- add Postgres-backed schema migrations,
- or maintain more than one serializer for the same runtime object.

This keeps the V20 core simple now while leaving a clear path to Pydantic V2 at the API boundary.
