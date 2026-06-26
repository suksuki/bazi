# V30 Deployment

Updated: 2026-05-20

## Purpose

V30 deployment must stay independent from V20 while allowing both versions to coexist during migration.

## Current Local Service

V30 smoke service:

```text
host: 0.0.0.0
port: 9030
app: v30.api.app:app
```

Health:

```text
/api/v30/health
```

UI:

```text
/v30/ui/
```

## Required Isolation

V30 deployment must use:

```text
V30_DATABASE_URL
V30_REDIS_URL
V30_REDIS_PREFIX=v30
V30_RUNTIME_DIR=/home/hlsystem/bazi/qiazhi/v30/.runtime
V30_HOST
V30_PORT
V30_REPOSITORY=memory
```

Real environment should use:

```text
V30_REPOSITORY=postgres
V30_DATABASE_URL=postgresql://qiazhi_v30_app:...@127.0.0.1:5432/qiazhi_v30?sslmode=prefer
V30_REDIS_URL=redis://127.0.0.1:6379/0
V30_REDIS_PREFIX=v30
```

V30 deployment must not use:

```text
V20_DATABASE_URL
V20_REDIS_URL
v20 runtime dirs
v20 systemd service names
v20 nginx locations for V30 routes
```

## Database Isolation

V30 must use an independent Postgres database or an equally strict schema boundary. The preferred production choice is a separate database.

Recommended database name:

```text
qiazhi_v30
```

Required environment:

```text
V30_DATABASE_URL=postgresql://.../qiazhi_v30
```

Allowed V30 tables:

```text
v30_readings
v30_runtime_traces
v30_feedback_events
v30_validation_cases
v30_policy_pointers
v30_artifacts
```

Forbidden:

```text
V30_DATABASE_URL pointing to a database name containing v20
V30 code reading V20_DATABASE_URL
V30 migrations creating v20_* tables
V30 queries touching v20_* tables
```

Current status:

- Live Postgres connection is not enabled yet.
- V30 adapter SQL is `v30_*` only.
- A config guard rejects obvious V20 database URLs.
- Live Postgres integration tests must be explicit and must use `V30_DATABASE_URL`.

## Nginx Routing

V30 routes:

```text
https://dblife.com/v30/
https://dblife.com/api/v30/
```

Backend:

```text
http://127.0.0.1:9030/v30/
http://127.0.0.1:9030/api/v30/
```

Important:

`/v30/` must be defined before catch-all `location /`, otherwise it can fall through to V20.

## Service Management

Initial development can use:

```bash
V30_HOST=0.0.0.0 ./scripts/start_v30.sh
```

Production should use a separate service name:

```text
qiazhi-v30.service
```

Suggested service properties:

```text
WorkingDirectory=/home/hlsystem/bazi/qiazhi/v30
Environment=V30_HOST=127.0.0.1
Environment=V30_PORT=9030
Environment=V30_REDIS_PREFIX=v30
Environment=V30_RUNTIME_DIR=/home/hlsystem/bazi/qiazhi/v30/.runtime
ExecStart=/usr/bin/python3 -m uvicorn v30.api.app:app --host ${V30_HOST} --port ${V30_PORT}
Restart=always
```

## Deployment Checks

After deploy:

```bash
curl -fsS http://127.0.0.1:9030/api/v30/health
curl -k -I https://dblife.com/v30/ui/
curl -k https://dblife.com/api/v30/health
```

Expected:

- V30 health returns `package: v30`.
- `/v30/ui/` returns 200.
- No redirect to `/v20/ui/`.

## Release Gate

Before V30 release:

- Fast tests pass.
- Runtime smoke passes.
- Synthetic smoke passes.
- Pointer state is V30-only.
- Nginx route does not fall through to V20.
- Deployment docs are updated.

## Storage Adapter Status

Current V30 storage status:

- Postgres schema and SQL use `v30_*` tables only.
- Postgres adapter can prepare reading and trace records.
- Redis keyspace and cache use `v30:{env}:...` keys only.
- Tests use fake Redis and do not require live Postgres or Redis.
- API uses a runtime repository factory.
- Default repository is `memory`.
- Optional local persistence is `V30_REPOSITORY=local_json`, writing readings under `V30_RUNTIME_DIR/readings/`.
- Runtime traces are persisted through the repository boundary and local JSON writes under `V30_RUNTIME_DIR/traces/`.
- Optional Postgres persistence is `V30_REPOSITORY=postgres` with `V30_DATABASE_URL` pointing to a V30 database.
- Postgres repository writes readings to `v30_readings` and traces to `v30_runtime_traces`.
- API writes through Redis cache when `V30_REDIS_URL` is configured.
- Redis cache stores readings and traces under `v30:{env}:reading:*` and `v30:{env}:trace:*`.

Real environment scripts:

```bash
V30_DB_PASSWORD='<strong-password>' ./scripts/bootstrap_postgres_v30_sudo.sh
V30_DB_PASSWORD='<strong-password>' ./scripts/bootstrap_postgres_v30_docker.sh
cp .env.v30.real.example .env.v30.real
python3 scripts/apply_postgres_schema.py
python3 scripts/real_env_smoke.py
./scripts/start_v30_real.sh
```

Current host status:

- Redis is reachable and V30 API is using it when started with `V30_REDIS_URL=redis://127.0.0.1:6379/0`.
- Postgres is running in Docker container `rag-postgres`, image `pgvector/pgvector:pg16`, mapped to `127.0.0.1:5432`.
- Docker Postgres admin user is `rag`; it has superuser/create role/create DB permissions.
- Use `scripts/bootstrap_postgres_v30_docker.sh` for this host instead of the sudo bootstrap script.
- `qiazhi_v30` and `qiazhi_v30_app` are created for V30.
- Real environment smoke passed against Docker Postgres and Redis.
- Current V30 service is running with `repository=postgres` and `redis_cache=true`.

Pending before production persistence:

- Run the sudo bootstrap once on the host to create the V30 database/user.
- Fill `.env.v30.real` with the real V30 database password.
- Add marked integration tests for Postgres.
- Add marked integration tests for Redis.
- Keep live DB/Redis tests outside default `pytest`.

## Acceptance

- V20 and V30 can run at the same time.
- V30 service can restart independently.
- Nginx routes V30 independently.
- V30 runtime writes only V30 runtime paths.
- V30 uses only V30 env names.
