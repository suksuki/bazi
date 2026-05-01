# V20

V20 is a clean, independent Bazi system.

The first implementation goal is a small deterministic mainline:

```text
ChartInput
-> ChartFacts
-> CoreInference
-> RulePath candidates
-> BaziFeature[]
-> KnowledgeRef[] and knowledge alignment
-> KnowledgeSemanticModel
-> FeatureDiscovery report and 518K corpus training priors
-> Chart-specific salience features and rule collision summaries
-> PortraitIntelligence
-> Bazi measurement QuestionCandidate[]
-> Professional domain reading path
-> Reviewed knowledge evidence support
-> Shadow rule candidate support
-> Synthetic rule collision validation/training gate
-> Rule/portrait/question batch generation and validation
-> Rule candidate validation and bounded question reranking
-> Bazi-domain alignment gate for rules, portraits, and questions
-> EvidencePack
-> AnswerPlan
-> bounded LLM assist contracts
-> evidence-bounded LLM practitioner answer when explicitly requested
-> ops profile and store contracts
-> deterministic answer
```

V20 does not import V19 runtime modules. V19 remains a reference archive,
regression source, and knowledge/documentation source.

Initial boundaries:

- Core facts are deterministic and typed.
- Feature Spine is the central runtime contract.
- Macro features give UI and LLM compact context while subfeatures remain the source of truth.
- Chart-specific salience features make different charts surface different ten-god, element, branch, and time-trigger material.
- Knowledge is reviewed evidence context, not rule truth.
- Feature Discovery is the central runtime intelligence router: it fuses compiled features, reviewed knowledge, portrait axes, shadow rule candidates, user interaction, bounded LLM assist, and 518K corpus training artifacts into ranked features and domain hypotheses.
- Knowledge Semantic Model turns reviewed knowledge into feature hooks, question hooks, portrait label candidates, interaction keywords, and rule-atom signals.
- Portrait Intelligence turns raw portrait axes into knowledge-backed sub-axis candidates and calibration prompts.
- Portraits, recommended questions, and answers are Bazi measurement projections over features.
- Rules, portrait axes, and recommended questions must pass Bazi-domain alignment before ranking or display.
- Domain projections are the anti-corruption layer between features and applied topics.
- Professional answer paths explain wealth, career, relationship, health, time, ten-god, and useful-god questions from compiled feature evidence, reviewed knowledge boundaries, and shadow-only rule candidates.
- Shadow rule candidates report current-chart feature collisions, but still cannot activate as rule truth without validation and promotion.
- Rule learning is synthetic-case driven. The 518K corpus supplies coverage and ranking priors, not rule truth.
- Rule and portrait batches can be generated and validated by script before any promotion discussion.
- LLM outputs are hard-enforced by deterministic text guards before user-facing use.
- LLM can act as a practitioner-style answer composer only after FeatureDiscovery, KnowledgeSemanticModel, PortraitIntelligence, and AnswerPlan have prepared verified context.
- Rule candidates may reorder existing questions only through a capped shadow signal and synthetic validation.
- Learning, LLM, corpus, and ranking systems are assistive and governed.
- Postgres is the persistent authority; Redis is ephemeral cache/queue/lock state.
- macOS and Linux `0.13` runtime profiles are explicit and host-local runtime files are not synced by default.
- No model may create chart facts, mutate rule truth, or bypass evidence gates.

Primary V20 modules:

- `core`: typed chart facts, ten-god metadata, relations, and strength evidence.
- `features`: the common feature spine used by questions, knowledge, answers, validation, and learning.
- `intelligence`: feature discovery fusion, training-signal ingestion, and intelligence generation manifests.
- `knowledge`: reviewed units, feature-aligned retrieval, audit, and coverage checks.
- `graph`: chart graph and rule-path candidates.
- `interaction`: Bazi measurement question ranking, portrait projection, and feedback capture.
- `measurement`: runtime topic reports and the Bazi-domain alignment contract.
- `answer`: evidence-backed answer planning, professional domain reading paths, and bounded answer composition.
- `llm`: bounded contracts plus hard text enforcement for intent routing, question suggestion, feature-candidate proposals, answer-plan assistance, multilingual rendering, feedback summaries, and safety review.
- `validation`: synthetic and golden-case gates.
- `corpus`: dry-run full-corpus precompute scaffolding.
- `learning`: proposal ledgers and promotion gates.
- `ops`: macOS/Linux profiles, Postgres/Redis contracts, and sync guardrails.
- `testing`: bounded test tiers, executable test manifest, and fast local scripts.
- `profiles`: V19 profile migration preview/import and V20 user profile storage.

Storage boundary:

- Postgres is the authoritative store for V20 corpus snapshots, registries, feedback, decisions, rule proposals, and LLM artifacts.
- SQLite is allowed only as a disposable local cache/index for offline similarity probes and fast rebuilds. It is not synced between macOS and Linux, and it must be rebuildable from `v20_corpus_snapshots` or versioned corpus artifacts.
- The 518K structural corpus can be imported into `v20_corpus_snapshots`; query indexes cover case lookup, day-master filters, cluster search, wealth filters, and JSONB containment over feature/portrait tags.
- V19 user profile data migrates into `v20_user_profiles`; location metadata is preserved as user context and does not alter chart facts unless a future deterministic calendar layer explicitly supports it.

UI boundary:

- `/v20/ui/` is the multi-role, multi-language entry/login surface for guest, practitioner, and admin access.
- `/v20/ui/workbench.html` is the measurement workspace for Bazi feature, portrait, question, and answer projections.
- `/v20/ui/admin.html` is intentionally limited to DB and LLM status so operations stay readable.

Default local validation:

```bash
./v20/scripts/test_fast.sh
```

Run the local V20 service:

```bash
./v20/scripts/start_macos.sh
```

Run the local V20 service in the background:

```bash
./v20/scripts/service_macos.sh start
./v20/scripts/service_macos.sh status
./v20/scripts/service_macos.sh logs
```

The first service surface exposes `/health`, `/api/v20/measure`, ops config, and test-tier metadata. Health and ops endpoints are read-only and do not connect to Redis or Postgres.
