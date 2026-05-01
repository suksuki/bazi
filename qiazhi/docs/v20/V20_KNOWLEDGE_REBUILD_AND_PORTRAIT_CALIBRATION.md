# V20 Knowledge Rebuild And Portrait Calibration

V20 uses the feature spine to rebuild the knowledge and portrait systems that
became too entangled in V19.

## Knowledge Rebuild

Knowledge is now split into four auditable surfaces:

- `KnowledgeUnit`: reviewed evidence unit used by runtime retrieval.
- `KnowledgeSource`: traceability handle for the document or implementation
  note behind a unit.
- `KnowledgeCoverageReport`: domain, source, and question-hook gap check.
- `KnowledgeReleaseManifest`: release-review bundle for future Postgres seed or
  artifact promotion.

Endpoints:

- `GET /api/v20/knowledge/catalog`
- `GET /api/v20/knowledge/source-catalog`
- `GET /api/v20/knowledge/coverage-report`
- `GET /api/v20/knowledge/release-manifest`
- `GET /api/v20/knowledge/v19-migration-audit`
- `GET /api/v20/knowledge/draft-import-preview`

These endpoints do not activate rules, write database rows, or treat knowledge
as truth. They make missing sources, duplicate ids, unreviewed sources, and
coverage gaps visible before a release.

The V19 migration audit scans `docs/bazi_knowledge` and classifies legacy files
into review lanes such as reviewed-unit seed, draft-unit review, archive-only
reference, and rule-conversion candidate. No legacy document can enter runtime
directly.

The draft import preview parses legacy `knowledge_drafts` JSON seed packs into
V20 draft candidates. Each candidate remains `draft_review_required` until
source refs, evidence templates, boundaries, feature hooks, question hooks, and
synthetic validation are reviewed.

## Portrait Calibration

The portrait system remains a projection over compiled `BaziFeature[]`.

It can now emit calibration signals:

- `confirm`
- `reject`
- `needs_review`
- `evidence_gap`

Endpoints:

- `POST /api/v20/portrait/calibration/analyze`
- `POST /api/v20/portrait/calibration/record`

Recorded calibration is append-only and redacted. It can feed later learning,
ranking, confidence, or coverage review proposals, but it cannot mutate chart
facts, rules, recommended questions, or answer conclusions.
