-- Qiazhi V40 isolated Postgres bootstrap.
-- Run with a Postgres admin role, then put the final password in .env.v40.local.
--
-- V40 must not share V30 tables, schemas, runtime rows, or migration history.

CREATE DATABASE qiazhi_v40;

CREATE USER qiazhi_v40_app WITH PASSWORD 'CHANGE_ME_V40_LOCAL_PASSWORD';

GRANT ALL PRIVILEGES ON DATABASE qiazhi_v40 TO qiazhi_v40_app;

\connect qiazhi_v40

CREATE SCHEMA IF NOT EXISTS public AUTHORIZATION qiazhi_v40_app;

GRANT ALL ON SCHEMA public TO qiazhi_v40_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO qiazhi_v40_app;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO qiazhi_v40_app;
