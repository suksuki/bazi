# V20 Service Runtime

V20 now exposes a minimal FastAPI runtime over the deterministic measurement core.

## Endpoints

- `GET /health`
- `GET /api/v20/ops/config`
- `GET /api/v20/ops/profile/{profile_name}`
- `GET /api/v20/testing/tiers`
- `GET /api/v20/storage/schema`
- `POST /api/v20/measure`
- `POST /api/v20/runtime/measure`

The health and ops endpoints do not connect to Postgres or Redis. They only report the configured contracts, active profile, and validation status.

The storage schema endpoint returns the reviewed Postgres migration contract. It does not apply migrations.

## Local macOS

```bash
./v20/scripts/start_macos.sh
```

Defaults:

- `V20_ENV=local_macos`
- `V20_HOST=127.0.0.1`
- `V20_PORT=9020`

## Linux 0.13

```bash
V20_ENV=linux_0_13 ./v20/scripts/start_linux.sh
```

Defaults:

- `V20_ENV=linux_0_13`
- `V20_HOST=0.0.0.0`
- `V20_PORT=9020`

## Measurement Request

```json
{
  "year": "甲子",
  "month": "戊辰",
  "day": "甲午",
  "hour": "辛酉",
  "input_id": "demo",
  "question_key": "",
  "locale": "zh"
}
```

The response is the same deterministic runtime envelope produced by `v20.api.runtime.run_runtime_from_pillars`.

## Guardrails

- Service entry is V20-only and imports no V19 runtime modules.
- Measurement is read-only and has `runtime_mutation=false`.
- Health checks do not depend on Redis or Postgres availability.
- Secrets are never rendered by ops config responses.
