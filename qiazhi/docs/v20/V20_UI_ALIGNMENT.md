# V20 UI Alignment

The V20 UI is served from `v20/frontend` through the V20 FastAPI runtime.
The default view is the user role projection, so the browser does not fetch
internal feature evidence, knowledge refs, rule paths, or chart graphs unless a
non-user role is selected.

- `GET /v20/ui/`
- `GET /v20/ui/app.js`
- `GET /v20/ui/styles.css`

The first screen is the actual Bazi measurement workspace. It renders:

- four-pillar input and natural-language `user_text`
- optional explicit time pillars for flow year, luck pillar, and flow month
- role-projected runtime views for user, analyst, lab, and admin
- selected feature-backed question
- `BaziFeature` chips
- `measurement_report` topics
- recommended questions
- portrait projection as calibration-only axes
- deterministic answer text with LLM assist status
- corpus, synthetic validation, and learning evolution status
- dependency, policy review, testing matrix, and feedback-learning status
- append-only feedback record submission through the local JSONL ledger

The UI does not import V19, does not call portrait bias, and does not create
fortune conclusions on the client. It is a runtime viewer and operator surface
for V20 contracts.
