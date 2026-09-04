# V60 Server 13 deployment

This directory contains the checked-in production service contracts for Server 13.
Secrets and database dumps belong under `/home/hlsystem/abu-v60/shared` and are never
committed.

## Runtime layout

```text
/home/hlsystem/abu-v60/
  current -> releases/<git-sha>
  releases/<git-sha>/
  shared/postgres.env
  shared/v60.production.env
  backups/
```

PostgreSQL runs as the `qiazhi-v60-postgres` Docker container, binds only to
`127.0.0.1:5432`, and stores data in the dedicated `qiazhi_v60_pgdata` volume. The
application runs as `qiazhi-v60.service` on `127.0.0.1:9050`; the existing nginx
virtual host owns TLS and the public reverse proxy.

The historical `/home/hlsystem/bazi` checkout and `rag_pgdata` Docker volume are not
deployment targets and must not be reset, overwritten, or reused for V60.

## Database recovery

Use a PostgreSQL custom-format dump created with `--no-owner --no-acl`. Before any
replacement restore, save a fresh dump of the current production database. Restore
inside the container with the checked-in application stopped, then verify:

- `public.alembic_version` is the repository migration head;
- `platform.schema_manifest.foundation_version` matches the runtime manifest;
- only `cognition`, `identity`, `media`, `mingli`, `platform`, and `public` remain;
- private Profile and Case counts match the source snapshot;
- `/api/v60/health`, `/api/v60/system/manifest`, `/`, and `/experience` succeed.

Never restore the retired Dream, Story, or World schemas into V60.

The first Owner-authorized Server 13 deployment and its verified hashes are recorded
in [`../docs/26_V60_SERVER13_DEPLOYMENT_RECEIPT.md`](../docs/26_V60_SERVER13_DEPLOYMENT_RECEIPT.md).
