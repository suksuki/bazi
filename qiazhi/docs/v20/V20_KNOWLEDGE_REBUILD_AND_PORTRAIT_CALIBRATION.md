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
- `GET /api/v20/knowledge/review-queue`
- `GET /api/v20/knowledge/review-packet/{domain}`
- `GET /api/v20/knowledge/first-wave-review-packets`
- `GET /api/v20/knowledge/approval-preflight/{domain}`
- `GET /api/v20/knowledge/first-wave-approval-preflight`
- `GET /api/v20/knowledge/review-assist/{domain}`
- `GET /api/v20/knowledge/first-wave-review-assist`
- `GET /api/v20/knowledge/rule-proposals/{domain}`
- `GET /api/v20/knowledge/first-wave-rule-proposals`
- `GET /api/v20/knowledge/rule-proposal-preflight/{domain}`
- `GET /api/v20/knowledge/first-wave-rule-proposal-preflight`

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

The review queue groups draft candidates by domain and prioritizes core Bazi
domains first: strength, ten god, useful god, five elements, branches, wealth,
pattern, and time context.

Review packets turn a domain queue into draft `KnowledgeUnit` skeletons with
missing fields, release blockers, review checklist, and validation
requirements. They are not runtime-retrievable until reviewed and released.

Approval preflight checks whether a packet has source refs, evidence templates,
boundaries, feature hooks, question hooks, and decision requirements satisfied.
Current migrated drafts are expected to be blocked until reviewers complete
those fields.

Review assist gives deterministic field suggestions for blocked drafts. The
suggestions help reviewers fill evidence templates, boundaries, and hooks, but
they do not write fields, approve drafts, or make units runtime-retrievable.

Reviewed knowledge units can also produce `KnowledgeRuleProposal` rows. These
are released to shadow training by default so the system can learn from them
early. Static contract failures still block malformed proposals, but synthetic
validation and DecisionRegistry approval are promotion gates for user-visible
runtime, not blockers for shadow learning.

## Portrait Calibration

The portrait system remains a projection over compiled `BaziFeature[]`, but it
now also carries reviewed knowledge provenance.

Portrait data has three sources with separate duties:

- `BaziFeature[]`: decides which portrait axes exist, their confidence, and
  the source feature ids.
- reviewed `KnowledgeUnit`: supplies axis language, evidence boundaries, and
  calibration prompts.
- calibration ledger: records whether a user or analyst confirms, rejects, or
  requests review for a projection.

Knowledge can shape portrait wording and boundaries, but it cannot create
personality verdicts, rank recommended questions, drive answers, or activate
rules. User role projection hides internal feature ids and knowledge links;
analyst and lab views can inspect provenance.

It can now emit calibration signals:

- `confirm`
- `reject`
- `needs_review`
- `evidence_gap`

Endpoints:

- `GET /api/v20/portrait/ontology`
- `POST /api/v20/portrait/calibration/analyze`
- `POST /api/v20/portrait/calibration/record`

Recorded calibration is append-only and redacted. It can feed later learning,
ranking, confidence, or coverage review proposals, but it cannot mutate chart
facts, rules, recommended questions, or answer conclusions.
