# V20 UI Alignment

The V20 UI is served from `v20/frontend` through the V20 FastAPI runtime:

- `GET /v20/ui/`
- `GET /v20/ui/app.js`
- `GET /v20/ui/styles.css`

The first screen is the actual Bazi measurement workspace. It renders:

- four-pillar input and natural-language `user_text`
- selected feature-backed question
- `BaziFeature` chips
- `measurement_report` topics
- recommended questions
- portrait projection as calibration-only axes
- deterministic answer text with LLM assist status
- corpus, synthetic validation, and learning evolution status

The UI does not import V19, does not call portrait bias, and does not create
fortune conclusions on the client. It is a runtime viewer and operator surface
for V20 contracts.
