# V30 Review Improvements

Updated: 2026-06-26

## Purpose

This document records the main improvement items found during the V30 review after syncing local, GitHub, and the 13 server.

Review focus:

- Production safety
- V30/V20 isolation
- Runtime configuration behavior
- Test reliability
- Storage scalability
- Admin and product authorization boundaries

## Current Verified State

- Local, GitHub, and 13 server code are aligned at `19a9283a`.
- Local V30 runs at `http://127.0.0.1:9030`.
- Local V30 health reports `repository=postgres` and `redis_cache=true`.
- Local database was restored back to the 13 server snapshot after review testing.
- Snapshot counts after restore:

```text
v30_artifacts=28
v30_readings=167
v30_runtime_traces=169
```

## P1: Protect Admin APIs Before External Use

### Finding

V30 exposes many `/api/v30/admin/...` routes without authentication, role checks, admin token checks, or network restrictions.

High-risk routes include:

- `GET /api/v30/admin/runtime/config`
- `POST /api/v30/admin/runtime/db/config`
- `POST /api/v30/admin/runtime/db/apply-schema`
- `POST /api/v30/admin/runtime/redis/config`
- `POST /api/v30/admin/runtime/llm/config`
- `POST /api/v30/admin/training/run`
- `POST /api/v30/admin/training/m3-background/run`

### Impact

If `/api/v30/` is public through nginx, an external caller could potentially:

- Change runtime database, Redis, or LLM configuration.
- Write `.runtime/admin_config.json`.
- Trigger schema creation.
- Start training or validation jobs.
- Read operational status that should be internal.

### Recommended Fix

Add a shared admin authorization dependency for every `/api/v30/admin/...` route.

Minimum acceptable boundary:

- Require an admin bearer token or signed admin session.
- Reject missing/invalid credentials with `401`.
- Reject non-admin roles with `403`.
- Keep `/api/v30/health` public.
- Consider nginx-level restriction for `/api/v30/admin/` as an immediate defense-in-depth layer.

Suggested implementation direction:

- Add `V30_ADMIN_TOKEN` or equivalent secret.
- Add a FastAPI dependency such as `require_admin_access`.
- Apply it to an admin router or every admin route.
- Add tests proving admin routes reject unauthenticated requests.

### Verification

Expected tests:

```bash
pytest -q tests/test_v30_scaffold.py::test_admin_routes_require_auth
pytest -q tests/unit/test_admin_authorization.py
```

Expected manual checks:

```bash
curl -i http://127.0.0.1:9030/api/v30/admin/runtime/config
curl -i -H "Authorization: Bearer $V30_ADMIN_TOKEN" http://127.0.0.1:9030/api/v30/admin/runtime/config
```

## P1: Make Tests Hermetic From Saved Admin Config

### Finding

`load_settings()` applies saved admin config on every call, and saved admin config writes back into `os.environ`.

This makes tests order-dependent:

- One test can call the admin runtime config endpoint.
- That endpoint can write `V30_REPOSITORY=postgres` and `V30_DATABASE_URL` into an admin config file.
- Later tests that expect `local_json` or memory can silently pick up the saved Postgres configuration.

During review, full pytest produced:

```text
681 passed, 7 failed, 1 skipped
```

After removing the temporary saved admin config, the same failed tests passed individually. The failures were caused by configuration pollution, not by deterministic module logic.

### Impact

Risks:

- Tests may fail or pass depending on run order.
- Default pytest can accidentally write to a real local database.
- Local development can diverge from CI behavior.
- Release confidence is reduced because environment state affects test outcome.

### Recommended Fix

Separate runtime config loading from test config loading.

Preferred direction:

- Make `create_app()` accept an optional explicit settings object.
- Make tests pass explicit settings or disable saved admin overrides by default.
- Add a test-only env switch such as `V30_DISABLE_SAVED_ADMIN_OVERRIDES=1`.
- Ensure `pytest` sets a temporary `V30_ADMIN_CONFIG_PATH` per test or globally through `conftest.py`.
- Avoid mutating process-global `os.environ` in helper functions except at process startup or explicit admin-save boundaries.

### Verification

Expected behavior:

- Full pytest passes from a clean shell.
- Full pytest passes after local real environment has been configured.
- Full pytest does not modify the real local database unless explicit live integration flags are enabled.

Suggested commands:

```bash
V30_DISABLE_SAVED_ADMIN_OVERRIDES=1 pytest -q
V30_ADMIN_CONFIG_PATH="$(mktemp)" pytest -q
```

## P2: Stop GET Read Endpoints From Creating Runtime Records

### Finding

Some GET endpoints create and persist smoke runtime records when a requested reading does not exist.

Observed behavior:

- `GET /api/v30/readings/{reading_id}` creates a smoke runtime when missing.
- `GET /api/v30/readings/{reading_id}/view` also creates a smoke runtime when missing.
- Admin trace lookup has similar smoke fallback behavior.

### Impact

Risks:

- Crawlers, mistyped IDs, probes, or UI retries can create database rows.
- Production data becomes polluted with smoke records.
- Read endpoints are no longer safe/idempotent from a storage perspective.
- Operational metrics become harder to trust.

### Recommended Fix

Change production GET behavior to return `404` for missing readings.

Keep smoke generation only behind an explicit development or smoke-test path, for example:

- `POST /api/v30/dev/smoke-reading`
- `V30_ENV=dev`
- `V30_ALLOW_SMOKE_FALLBACK=1`

### Verification

Expected tests:

```bash
pytest -q tests/unit/test_read_endpoints_are_read_only.py
```

Expected manual check:

```bash
curl -i http://127.0.0.1:9030/api/v30/readings/does-not-exist
```

Expected result:

```text
HTTP 404
```

## P2: Move Reading History Filtering Into Postgres

### Finding

Postgres reading history currently selects all payloads from `v30_readings` and filters in Python.

Current risk pattern:

```text
SELECT payload FROM v30_readings;
```

Then Python filters by actor/session and sorts by payload timestamps.

### Impact

This is acceptable for small data, but it will not scale with real user history.

Risks:

- Slow history API as rows grow.
- Excess memory use.
- Higher database and app latency.
- Inefficient filtering because actor/session/created time are buried in JSON payload.

### Recommended Fix

Add queryable columns and indexes:

- `actor_id`
- `session_id`
- `created_at`
- possibly `locale`, `status`, or `profile_id` later

Update writes to populate those columns, then change history reads to filter and paginate in SQL.

Example index direction:

```sql
CREATE INDEX IF NOT EXISTS idx_v30_readings_actor_session_created
ON v30_readings (actor_id, session_id, created_at DESC);
```

### Verification

Expected tests:

```bash
pytest -q tests/unit/test_runtime_repository.py
pytest -q tests/unit/test_reading_history_postgres_filters.py
```

Expected checks:

- SQL query contains owner filters.
- History endpoint does not load all rows.
- Result ordering remains newest first.

## P2: Harden Product Auth Before Real Users

### Finding

Product auth currently uses a local JSON store under runtime storage.

Current limitations:

- Sessions do not expire.
- Sessions are bearer tokens without rotation or revocation policy beyond logout.
- Admin registration is controlled by "first admin wins".
- Product auth roles are not connected to admin API authorization.
- JSON file persistence is not safe for concurrent multi-process writes.

### Impact

This is enough for a productization MVP, but not for real production access control.

Risks:

- Long-lived leaked session tokens remain valid.
- Concurrent requests may overwrite auth/profile state.
- Admin role in product auth does not actually protect admin runtime operations.
- File-based auth does not align with the Postgres runtime direction.

### Recommended Fix

Move product auth/session storage to Postgres before opening to real users.

Add:

- Session expiry.
- Token rotation or explicit session revocation.
- Password hash upgrade path.
- Admin authorization bridge for `/api/v30/admin/...`.
- Concurrent write safety.

### Verification

Expected tests:

```bash
pytest -q tests/unit/test_product_auth.py
pytest -q tests/unit/test_admin_authorization.py
```

Expected behavior:

- Expired session rejects.
- Non-admin session rejects admin route.
- Admin session or admin token allows admin route.
- Concurrent profile saves do not corrupt store.

## Suggested Execution Order

1. Add nginx restriction for `/api/v30/admin/` immediately.
2. Add FastAPI admin authorization dependency.
3. Make tests hermetic from saved admin config.
4. Change missing GET reading/view behavior to `404`.
5. Add Postgres columns/indexes for history filtering.
6. Move product auth/session storage out of local JSON.

## Review Notes

The strongest part of V30 is that it has extensive modular docs and broad test coverage. The main issue is not lack of code or tests; it is that operational boundaries are still MVP-shaped in several places:

- Admin endpoints are present before admin authorization.
- Runtime config can leak into tests.
- Read endpoints still carry smoke/development behavior.
- Storage works but needs production query shape.

These are fixable without reopening the core Bazi modeling work.
