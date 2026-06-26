#!/usr/bin/env bash
set -euo pipefail

CONTAINER="${V30_POSTGRES_CONTAINER:-rag-postgres}"
ADMIN_USER="${V30_POSTGRES_ADMIN_USER:-rag}"
ADMIN_DB="${V30_POSTGRES_ADMIN_DB:-postgres}"
DB_NAME="${V30_DB_NAME:-qiazhi_v30}"
DB_USER="${V30_DB_USER:-qiazhi_v30_app}"
DB_PASSWORD="${V30_DB_PASSWORD:?set V30_DB_PASSWORD before running this script}"

docker exec -i "${CONTAINER}" psql -U "${ADMIN_USER}" -d "${ADMIN_DB}" -v ON_ERROR_STOP=1 <<SQL
DO \$\$
DECLARE
  role_name text := '${DB_USER}';
  role_password text := '${DB_PASSWORD}';
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = role_name) THEN
    EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', role_name, role_password);
  ELSE
    EXECUTE format('ALTER ROLE %I WITH LOGIN PASSWORD %L', role_name, role_password);
  END IF;
END
\$\$;

SELECT format('CREATE DATABASE %I OWNER %I', '${DB_NAME}', '${DB_USER}')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME}')\gexec

GRANT ALL PRIVILEGES ON DATABASE "${DB_NAME}" TO "${DB_USER}";
SQL

docker exec -i "${CONTAINER}" psql -U "${ADMIN_USER}" -d "${DB_NAME}" -v ON_ERROR_STOP=1 <<SQL
GRANT ALL ON SCHEMA public TO "${DB_USER}";
ALTER SCHEMA public OWNER TO "${DB_USER}";
SQL
