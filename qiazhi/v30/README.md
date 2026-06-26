# Qiazhi V30

V30 is an independent runtime scaffold. It must not import `v20.*` at runtime, read V20 runtime files, use V20 Redis keys, or touch V20 database tables.

Required service boundaries:

- Python package: `v30`
- API prefix: `/api/v30`
- UI prefix: `/v30/ui`
- Runtime directory: `v30/.runtime` by default
- Postgres tables: `v30_*`
- Redis keys: `v30:*`

Start the smoke service:

```bash
V30_PORT=9030 ./scripts/start_v30.sh
```

Run tests:

```bash
pytest
```
