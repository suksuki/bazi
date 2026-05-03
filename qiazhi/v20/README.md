# V20

V20 is a clean, independent Bazi system.

The current implementation goal is a small dynamic-decision mainline:

```text
ChartInput
-> ChartFacts
-> CoreInference
-> RulePath candidates
-> BaziFeature[]
-> KnowledgeRef[] and knowledge alignment
-> KnowledgeSemanticModel
-> RuleHit[]
-> RuleDecision[]
-> DefeasibleDecisionModel
-> PortraitProjection / TopicProjection
-> FeatureStateModel
-> QuestionIntentModel
-> InteractionSession
-> Bazi measurement QuestionCandidate[] from decision states
-> Professional domain reading path
-> Reviewed knowledge evidence support
-> Synthetic rule collision validation/training gate
-> Rule/portrait/question batch generation and validation
-> Dynamic decision training batch for current-chart portrait/question quality
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
- Feature Spine is an intermediate evidence contract, not the user-facing intelligence layer.
- Runtime user-facing intelligence is the Bazi Feature Graph mainline: RuleHit -> RuleDecision -> DefeasibleDecisionModel -> PortraitProjection -> QuestionIntent -> InteractionSession -> LLM answer.
- Macro features and 518K corpus labels can support offline training, but they must not become runtime portrait truth.
- Knowledge is reviewed evidence context, not rule truth.
- Feature Discovery is no longer the user measurement driver. It may remain as an offline/admin experiment for coverage and training signals.
- Knowledge Semantic Model turns reviewed knowledge into feature hooks, question hooks, portrait label candidates, interaction keywords, and rule-atom signals.
- Portrait Projection turns current-chart decision states into user-facing命理主题画像轴.
- Recommended questions and answers are driven by dynamic rule decisions, with features and knowledge as evidence.
- Rules, portrait axes, and recommended questions must pass Bazi-domain alignment before ranking or display.
- Domain projections are the anti-corruption layer between features and applied topics.
- Professional answer paths explain wealth, career, relationship, health, time, ten-god, and useful-god questions from current-chart rule decisions, compiled evidence, and reviewed knowledge boundaries.
- Old feature-discovery and conservative rule-candidate experiments are removed from the main runtime chain. They must not drive the user measurement page, portrait projection, recommended questions, or LLM practitioner context.
- Rule and decision learning are synthetic-case and practitioner-calibration driven. The 518K corpus supplies coverage, similarity, and offline priors, not runtime portrait truth.
- Rule and portrait batches can be generated and validated by script for active runtime iteration.
- Dynamic decision training batches validate whether a current chart can produce usable rule decisions, portrait projection axes, human-facing recommended questions, and practitioner controls before any parameter reweighting.
- LLM outputs are hard-enforced by deterministic text guards before user-facing use.
- LLM can act as a practitioner-style answer composer only after RuleDecision, PortraitProjection, KnowledgeSemanticModel, and AnswerPlan have prepared verified context.
- Rule and question ranking proposals are trained offline by scripts/admin review, then promoted only through synthetic validation and a decision registry record.
- Learning, LLM, corpus, and ranking systems are assistive and governed.
- Postgres is the persistent authority; Redis is ephemeral cache/queue/lock state.
- macOS and Linux `0.13` runtime profiles are explicit and host-local runtime files are not synced by default.
- No model may create chart facts, mutate rule truth, or bypass evidence gates.

Primary V20 modules:

- `core`: typed chart facts, ten-god metadata, relations, and strength evidence.
- `features`: the common feature spine used by questions, knowledge, answers, validation, and learning.
- `decision`: runtime rule hits, rule decisions, defeasible decision states, practitioner controls, portrait projection, and decision validation.
- `intelligence`: offline/admin feature discovery, training-signal ingestion, and intelligence generation manifests.
- `knowledge`: reviewed units, feature-aligned retrieval, audit, and coverage checks.
- `graph`: chart graph and rule-path candidates.
- `interaction`: Bazi measurement question ranking, portrait projection, and feedback capture.
- `measurement`: runtime topic reports and the Bazi-domain alignment contract.
- `answer`: evidence-backed answer planning, professional domain reading paths, and bounded answer composition.
- `llm`: bounded contracts plus hard text enforcement for intent routing, question suggestion, feature-candidate proposals, answer-plan assistance, multilingual rendering, feedback summaries, and safety review.
- `validation`: synthetic and golden-case gates.
- `corpus`: dry-run full-corpus precompute scaffolding.
- `learning`: proposal ledgers and active iteration records.
- `ops`: macOS/Linux profiles, Postgres/Redis contracts, and sync guardrails.
- `testing`: bounded test tiers, executable test manifest, and fast local scripts.
- `profiles`: V20 user profile storage and native profile management.

Storage boundary:

- Postgres is the authoritative store for V20 corpus snapshots, registries, feedback, decisions, rule proposals, and LLM artifacts.
- SQLite is optional and only allowed as a disposable local cache/index for offline similarity probes and fast rebuilds. Postgres remains the authority; the local SQLite cache is not synced between macOS and Linux, can be skipped with `--no-sqlite`, and must be rebuildable from `v20_corpus_snapshots` or versioned corpus artifacts.
- The 518K structural corpus can be imported into `v20_corpus_snapshots`; query indexes cover case lookup, day-master filters, cluster search, wealth filters, and JSONB containment over feature/portrait tags.
- V20 user profiles are created and managed natively in `v20_user_profiles`; profile metadata remains user context and does not alter chart facts unless a deterministic calendar layer explicitly supports it.

UI boundary:

- `/v20/ui/` is the multi-role, multi-language entry/login surface for guest, practitioner, and admin access.
- `/v20/ui/workbench.html` is the measurement workspace for six-pillar chart context, dynamic decision portrait, recommendation questions, and the practitioner-style dialog.
- `/v20/ui/admin.html` is intentionally limited to DB and LLM status so operations stay readable.
- Training, corpus precompute, rule extraction, portrait batch validation, and decision-parameter learning are script/admin surfaces only. They are not shown in the user measurement workspace.
- `v20/scripts/run_decision_training_plan.py` lists the current offline training targets and the scripts that manage them.
- `v20/scripts/run_dynamic_decision_training.py --progress` is the current background check for dynamic rule decisions, portraits, recommended questions, and decision-parameter training proposals.
- `v20/scripts/run_practitioner_calibration_training.py --progress` aggregates structured practitioner choices into offline decision-parameter proposals without mutating runtime rules.
- `v20/scripts/import_calibration_postgres.py --ledger practitioner_calibration_ledger` dry-runs local calibration ledger import; add `--apply` only after `V20_DATABASE_URL` is configured and backups are ready.
- `v20/scripts/apply_postgres_schema.py --env-file v20/.runtime/linux_0_13/service.env` dry-runs the authoritative Postgres schema; add `--apply` only on the target server after backup.
- `v20/scripts/run_training_iteration.py --write --progress` runs the lightweight script-only iteration loop and writes local artifacts; add `--dynamic-limit 0 --rule-iteration-limit 0 --include-replay-eval --include-rule-batch` for the full long run.
- `v20/scripts/run_main_chain_review.py` reviews the Knowledge -> Rule -> FeatureContext -> Portrait -> Question -> Answer -> Training spine in one read-only command.
- `v20/scripts/run_arbitration_loop.py --progress` turns mixed/countered/requires_review decisions into conflict snapshots for calibration and replay learning.
- `docs/v20/V20_0_13_SERVER_SYNC_RUNBOOK.md` contains the Linux `0.13` / `dblife.com` deployment and sync steps.
- `docs/v20/V20_SCRIPT_RUNBOOK.md` contains a complete step-by-step runbook for dev/test/corpus/self-evolution.
- `docs/v20/V20_INTELLIGENT_MAIN_CHAIN_REVIEW.md` records the cleaned intelligent main-chain boundary and the current cleanup policy.
- `v20/scripts/run_knowledge_rule_library.py --summary` shows the current knowledge-authored active rule definitions, portrait outputs, question outputs, and validation state.
- `v20/scripts/run_knowledge_rule_validation.py --summary` checks those active rules against synthetic coverage and 518K corpus priors, then lists the next review action per rule.
- `v20/scripts/run_rule_activation.py --summary` turns active-rule iteration into review packets so humans review packets, not raw rules.
- Heavy corpus work stays manual: `v20/scripts/run_full_precompute.py --progress --limit N --status-every M`.
- After corpus precompute, `v20/scripts/build_corpus_artifacts.py --run-id RUN --progress --no-sqlite` builds coverage/training artifacts without creating the disposable SQLite cache; omit `--no-sqlite` only when you want a local fallback similarity index before Postgres import.

See also:

- `docs/V20_DYNAMIC_DECISION_SPINE.md`
- `docs/V20_KNOWLEDGE_RULE_COMPLETION_PLAN.md`

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
