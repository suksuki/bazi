# V20 Test System

V20 uses bounded test tiers so the default developer loop stays fast as the system grows.

## Principle

V19 eventually made full test runs too expensive for every small edit. V20 keeps Markdown documentation, but the executable source of truth is `v20.testing.tiers.TEST_TIERS`.

Tests are split by risk and runtime:

| Tier | Script | Budget | Default Use |
| --- | --- | ---: | --- |
| `smoke` | `v20/scripts/test_smoke.sh` | 8s | tiny edits, first sanity check |
| `fast` | `v20/scripts/test_fast.sh` | 20s | normal local loop |
| `targeted` | `v20/scripts/test_targeted.sh` | 45s | module or bug-specific selectors |
| `full` | `v20/scripts/test_full.sh` | 90s | phase closeout before commit |
| `services` | `v20/scripts/test_services.sh` | 180s | Postgres, Redis, server, sync checks |
| `corpus` | `v20/scripts/test_corpus.sh` | 3600s | synthetic corpus and 518K coverage jobs |

## Guardrails

- `fast` must remain local, deterministic, and service-free.
- Postgres and Redis tests require `RUN_V20_SERVICE_TESTS=1`.
- 518K corpus or learning jobs require `RUN_V20_CORPUS_TESTS=1`.
- Redis is never treated as an authoritative test fixture.
- Long jobs must write run-ledger artifacts in later phases.
- No secret values may appear in test output.

## Recommended Loop

Small Python edit:

```bash
./v20/scripts/test_smoke.sh
```

Normal V20 work:

```bash
./v20/scripts/test_fast.sh
```

Focused check:

```bash
./v20/scripts/test_targeted.sh "knowledge or llm"
```

Before a phase commit:

```bash
./v20/scripts/test_full.sh
```

Coverage matrix:

```text
GET /api/v20/testing/matrix
```

The matrix records which fast-tier files cover runtime feature spine, explicit
time layer, knowledge/LLM/i18n, access roles, ops/storage/Redis,
corpus/learning/feedback/validation, and UI shell contracts.

Service opt-in:

```bash
RUN_V20_SERVICE_TESTS=1 ./v20/scripts/test_services.sh
```

Corpus opt-in:

```bash
RUN_V20_CORPUS_TESTS=1 ./v20/scripts/test_corpus.sh
```

## Future Additions

- Pytest markers can be added once there are enough tests to justify marker-level scheduling.
- JSONL eval exports can mirror synthetic validation without replacing local pytest.
- CI can run `fast` on each push, `full` on mainline PRs, and service/corpus tiers on scheduled jobs.
