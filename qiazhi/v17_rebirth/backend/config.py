from __future__ import annotations

import os
from urllib.parse import urlparse


PREDICTIVE_DATABASE_URL = (
    os.getenv("PREDICTIVE_DATABASE_URL")
    or os.getenv("DATABASE_URL")
    or os.getenv("POSTGRES_DSN")
    or ""
).strip()

PREDICTIVE_STORAGE_BACKEND = (
    os.getenv("PREDICTIVE_STORAGE_BACKEND")
    or os.getenv("V18_1_STORAGE_BACKEND")
    or "json"
).strip().lower() or "json"

PREDICTIVE_AUTO_MIGRATE_JSON_TO_POSTGRES = (
    os.getenv("PREDICTIVE_AUTO_MIGRATE_JSON_TO_POSTGRES", "1").strip().lower()
    in {"1", "true", "yes", "on"}
)


def predictive_database_url_status() -> dict:
    parsed = urlparse(PREDICTIVE_DATABASE_URL) if PREDICTIVE_DATABASE_URL else None
    valid_scheme = bool(parsed and parsed.scheme in {"postgres", "postgresql"})
    valid_location = bool(parsed and (parsed.netloc or parsed.path))
    return {
        "configured": bool(PREDICTIVE_DATABASE_URL),
        "valid": bool(valid_scheme and valid_location),
        "scheme": parsed.scheme if parsed else "",
        "storage_backend": PREDICTIVE_STORAGE_BACKEND,
        "auto_migrate_json_to_postgres": PREDICTIVE_AUTO_MIGRATE_JSON_TO_POSTGRES,
    }


def should_auto_migrate_predictive_json_to_postgres() -> bool:
    status = predictive_database_url_status()
    return bool(
        status["configured"]
        and status["valid"]
        and PREDICTIVE_AUTO_MIGRATE_JSON_TO_POSTGRES
    )
