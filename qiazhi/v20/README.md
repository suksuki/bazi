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
-> Bazi measurement QuestionCandidate[]
-> EvidencePack
-> AnswerPlan
-> bounded LLM assist contracts
-> ops profile and store contracts
-> deterministic answer
```

V20 does not import V19 runtime modules. V19 remains a reference archive,
regression source, and knowledge/documentation source.

Initial boundaries:

- Core facts are deterministic and typed.
- Feature Spine is the central runtime contract.
- Macro features give UI and LLM compact context while subfeatures remain the source of truth.
- Knowledge is reviewed evidence context, not rule truth.
- Portraits, recommended questions, and answers are Bazi measurement projections over features.
- Domain projections are the anti-corruption layer between features and applied topics.
- LLM outputs are hard-enforced by deterministic text guards before user-facing use.
- Learning, LLM, corpus, and ranking systems are assistive and governed.
- Postgres is the persistent authority; Redis is ephemeral cache/queue/lock state.
- macOS and Linux `0.13` runtime profiles are explicit and host-local runtime files are not synced by default.
- No model may create chart facts, mutate rule truth, or bypass evidence gates.

Primary V20 modules:

- `core`: typed chart facts, ten-god metadata, relations, and strength evidence.
- `features`: the common feature spine used by questions, knowledge, answers, validation, and learning.
- `knowledge`: reviewed units, feature-aligned retrieval, audit, and coverage checks.
- `graph`: chart graph and rule-path candidates.
- `interaction`: Bazi measurement question ranking, portrait projection, and feedback capture.
- `llm`: bounded contracts plus hard text enforcement for intent routing, question suggestion, feature-candidate proposals, answer-plan assistance, multilingual rendering, feedback summaries, and safety review.
- `validation`: synthetic and golden-case gates.
- `corpus`: dry-run full-corpus precompute scaffolding.
- `learning`: proposal ledgers and promotion gates.
- `ops`: macOS/Linux profiles, Postgres/Redis contracts, and sync guardrails.
- `testing`: bounded test tiers, executable test manifest, and fast local scripts.

Storage boundary:

- Postgres is the authoritative store for V20 corpus snapshots, registries, feedback, decisions, rule proposals, and LLM artifacts.
- SQLite is allowed only as a disposable local cache/index for offline similarity probes and fast rebuilds. It is not synced between macOS and Linux, and it must be rebuildable from `v20_corpus_snapshots` or versioned corpus artifacts.
- The 518K structural corpus can be imported into `v20_corpus_snapshots`; query indexes cover case lookup, day-master filters, cluster search, wealth filters, and JSONB containment over feature/portrait tags.

Default local validation:

```bash
./v20/scripts/test_fast.sh
```

Run the local V20 service:

```bash
./v20/scripts/start_macos.sh
```

The first service surface exposes `/health`, `/api/v20/measure`, ops config, and test-tier metadata. Health and ops endpoints are read-only and do not connect to Redis or Postgres.
