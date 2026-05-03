# V20 Ops Sync And Database Config

V20 has two expected runtime profiles:

- `local_macos`: local developer workstation.
- `linux_0_13`: Linux server on `0.13`.

The profiles are defined in `v20.ops` and can be overridden with environment variables. Real secrets must stay outside Git.

## Store Responsibilities

Postgres is the persistent authority:

- reviewed knowledge units
- artifact registry
- run registry
- decision registry
- feedback ledger
- corpus snapshots
- validated migration state

Redis is ephemeral:

- request cache
- rate limit counters
- background job queues
- distributed locks
- short TTL runtime state

Redis must not be synced between macOS and Linux. If Redis is lost or flushed, V20 should rebuild cache and queues from Postgres or deterministic runtime state.

## Sync Policy

Code sync:

- macOS to Linux: push/pull or rsync after tests.
- Linux to macOS: pull code only, no runtime overwrite.

Postgres sync:

- schema changes move through reviewed migrations.
- reviewed knowledge seeds and approved artifacts may be promoted.
- raw user sessions and identifiable feedback are protected.
- Linux to macOS exports must be anonymized and backed up first.

Runtime files:

- `.runtime` directories are host-local.
- backup/restore is explicit.
- no default overwrite across hosts.

Secrets:

- never sync through Git.
- never render secret values in config reports.
- use env vars such as `V20_DATABASE_URL`, `V20_REDIS_URL`, `V20_POSTGRES_PASSWORD`.

## First V20 Defaults

Local macOS:

- API port: `9020`
- Postgres database: `qiazhi_v20_local`
- Redis DB: `20`
- runtime dir: `v20/.runtime/local`

Linux `0.13`:

- API port: `9020`
- service name: `qiazhi-v20`
- Postgres database: `qiazhi_v20`
- Redis DB: `20`
- runtime dir: `v20/.runtime/linux_0_13`

These defaults are config contracts only; the V20 server process and database migrations will be added in later implementation phases.

## Initial Schema Contract

The first Postgres schema contract is exposed at:

```text
GET /api/v20/storage/schema
```

It defines reviewed authoritative tables but does not apply migrations automatically:

- `v20_knowledge_units`
- `v20_artifact_registry`
- `v20_run_registry`
- `v20_decision_registry`
- `v20_feedback_ledger`
- `v20_corpus_snapshots`

Applying migrations uses an explicit dry-run/apply command and still requires a backup policy before remote apply:

```bash
python3.12 v20/scripts/apply_postgres_schema.py --env-file v20/.runtime/linux_0_13/service.env
python3.12 v20/scripts/apply_postgres_schema.py --env-file v20/.runtime/linux_0_13/service.env --apply
```

## Redis Keyspace Contract

The Redis contract is exposed at:

```text
GET /api/v20/redis/contract
```

Initial keyspaces:

- `v20:cache:request:` for short-lived deterministic response fragments.
- `v20:rate:` for rate counters.
- `v20:queue:job:` for eval/corpus/learning worker dispatch handles.
- `v20:lock:` for short TTL distributed locks.
- `v20:runtime:short:` for temporary interaction state.

Every Redis keyspace must have a TTL and must be reconstructable from Postgres or deterministic runtime state. Redis remains non-authoritative.

## Dependency Readiness

The dependency readiness report is exposed at:

```text
GET /api/v20/runtime/dependencies
```

It checks whether the active profile has enough environment configuration to
connect to Postgres or Redis without opening a network connection and without
rendering secret values.

- Postgres readiness checks `V20_DATABASE_URL` or user/password env presence.
- Redis readiness checks `V20_REDIS_URL` or configured host metadata.
- The report is read-only and keeps Redis explicitly ephemeral.
