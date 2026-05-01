# V20 Service Runtime

V20 now exposes a minimal FastAPI runtime over the deterministic measurement core.

## Endpoints

- `GET /health`
- `GET /api/v20/ops/config`
- `GET /api/v20/ops/profile/{profile_name}`
- `GET /api/v20/ops/sync-readiness`
- `GET /api/v20/system/status`
- `GET /api/v20/testing/tiers`
- `GET /api/v20/storage/schema`
- `GET /api/v20/redis/contract`
- `POST /api/v20/measure`
- `POST /api/v20/runtime/measure`

The health and ops endpoints do not connect to Postgres or Redis. They only report the configured contracts, active profile, and validation status.

The storage schema endpoint returns the reviewed Postgres migration contract. It does not apply migrations.

The Redis contract endpoint returns keyspace, TTL, and ownership rules. It does not connect to Redis.

The sync-readiness endpoint reports the macOS <-> Linux 0.13 directions,
preflight checks, Postgres promotion boundary, and Redis rebuild policy. It
does not run git, rsync, database exports, or remote commands.

`GET /api/v20/system/status` aggregates ops validation, dependency readiness,
storage/Redis contracts, access roles, policy surfaces, learning dry-run state,
and test matrix coverage. It is read-only and safe for monitoring.

## Local macOS

Recommended Python setup:

```bash
python3.12 -m venv .venv312
.venv312/bin/python -m pip install -r v20/requirements.txt
```

```bash
./v20/scripts/start_macos.sh
```

Background service control:

```bash
./v20/scripts/service_macos.sh start
./v20/scripts/service_macos.sh status
./v20/scripts/service_macos.sh logs
./v20/scripts/service_macos.sh stop
```

The macOS background script loads `v20/.runtime/local/service.env` when present.
Keep local Postgres, Redis, and LLM connection settings there instead of typing
them before every restart.

Generate a launchd plist for review without installing it:

```bash
./v20/scripts/service_macos.sh launchd-plist
```

Defaults:

- `V20_ENV=local_macos`
- `V20_HOST=127.0.0.1`
- `V20_PORT=9020`
- `PYTHON_BIN=python3.12` unless explicitly overridden with another Python 3.12 executable

## Linux 0.13

```bash
V20_ENV=linux_0_13 ./v20/scripts/start_linux.sh
```

Background service control:

```bash
./v20/scripts/service_linux.sh start
./v20/scripts/service_linux.sh status
./v20/scripts/service_linux.sh logs
./v20/scripts/service_linux.sh stop
```

The Linux background script loads `v20/.runtime/linux_0_13/service.env` when
present. These env files are runtime-local and ignored by git.

Generate a systemd unit for review without installing it:

```bash
./v20/scripts/service_linux.sh systemd-unit
```

Defaults:

- `V20_ENV=linux_0_13`
- `V20_HOST=0.0.0.0`
- `V20_PORT=9020`
- `PYTHON_BIN=python3.12` unless explicitly overridden with another Python 3.12 executable

## Service Unit Manifest

```text
GET /api/v20/ops/service-unit/local_macos
GET /api/v20/ops/service-unit/linux_0_13
```

These endpoints return reviewed launchd plist or systemd unit text, service
script commands, health check URLs, and UI URLs. They do not start processes,
install OS services, or render secret values. Remote install still requires
human review on the target host.

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
