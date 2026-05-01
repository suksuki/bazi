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
- `GET /api/v20/knowledge/rule-extraction`
- `GET /api/v20/knowledge/rule-extraction/{domain}`
- `GET /api/v20/knowledge/rule-extraction-validation`
- `GET /api/v20/knowledge/rule-extraction-validation/{domain}`
- `GET /api/v20/knowledge/llm-rule-extraction`
- `GET /api/v20/knowledge/llm-rule-extraction/{domain}`
- `GET /api/v20/knowledge/llm-rule-extraction-validation`
- `GET /api/v20/knowledge/llm-rule-extraction-validation/{domain}`

These endpoints do not activate rules, write database rows, or treat knowledge
as truth. They make missing sources, duplicate ids, unreviewed sources, and
coverage gaps visible before a release.

Current completeness status is `phase1_seed_coverage_ready_depth_incomplete`.
That means the reviewed seed units cover the main V20 domains, but this is not
yet a full Bazi canon. Classical source coverage, school variants, combination
exceptions, time-layer details, and applied-domain rules still need deeper
import, review, and extraction.

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

Rule extraction is knowledge-first. The source of a rule candidate is the
reviewed Bazi knowledge base: `KnowledgeUnit.summary`, `evidence_template`,
`boundary`, `feature_hooks`, `question_hooks`, and source refs. The extractor
turns those fields into `ExtractedRuleAtom[]`, `ExtractedRuleCandidate[]`, and
projection-only candidate rule paths.

The 518K corpus does not author rules. It only attaches validation signals:
coverage, support quality, overly broad conditions, sparse hooks, and
subcondition hints for shadow review. LLM can draft missing atoms from reviewed
knowledge text, but deterministic validation remains authoritative and no LLM
draft can activate runtime rules.

LLM extraction is now executable behind explicit provider flags. With
`V20_LLM_ENABLED=1` and `V20_LLM_EXECUTE=1`, V20 sends a structured
`rule_extraction_draft` prompt to the configured OpenAI-compatible provider.
When the provider is disabled or validation fails, V20 returns deterministic
fallback atoms and records the fallback reason. No LLM output can enter runtime
without the same review and promotion gates as deterministic extraction.

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
