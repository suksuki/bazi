# V20 Service Runtime

V20 now exposes a minimal FastAPI runtime over the deterministic measurement core.

## Endpoints

- `GET /health`
- `GET /api/v20/ops/config`
- `GET /api/v20/ops/profile/{profile_name}`
- `GET /api/v20/system/status`
- `GET /api/v20/testing/tiers`
- `GET /api/v20/storage/schema`
- `GET /api/v20/redis/contract`
- `POST /api/v20/measure`
- `POST /api/v20/runtime/measure`

The health and ops endpoints do not connect to Postgres or Redis. They only report the configured contracts, active profile, and validation status.

The storage schema endpoint returns the reviewed Postgres migration contract. It does not apply migrations.

The Redis contract endpoint returns keyspace, TTL, and ownership rules. It does not connect to Redis.

`GET /api/v20/system/status` aggregates ops validation, dependency readiness,
storage/Redis contracts, access roles, policy surfaces, learning dry-run state,
and test matrix coverage. It is read-only and safe for monitoring.

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

## Service Unit Manifest

```text
GET /api/v20/ops/service-unit/local_macos
GET /api/v20/ops/service-unit/linux_0_13
```

These endpoints return reviewed launch commands or systemd unit text, health
check URLs, and UI URLs. They do not start processes or render secret values.
Remote install still requires human review on the target host.

## Measurement Request

```json
{
  "year": "甲子",
  "month": "戊辰",
  "day": "甲午",
  "hour": "辛酉",
  "flow_year_pillar": "庚子",
  "luck_pillar": "",
  "flow_month_pillar": "",
  "user_text": "我想看流年触发",
  "input_id": "demo",
  "question_key": "",
  "locale": "zh"
}
```

The response is the same deterministic runtime envelope produced by `v20.api.runtime.run_runtime_from_pillars`.
Time fields are optional and must be explicit two-character pillars. They create
a `time_context` and `feature.time.explicit_context`; they do not create fixed
event predictions or calendar-derived timing facts.

## Guardrails

- Service entry is V20-only and imports no V19 runtime modules.
- Measurement is read-only and has `runtime_mutation=false`.
- Health checks do not depend on Redis or Postgres availability.
- Secrets are never rendered by ops config responses.
