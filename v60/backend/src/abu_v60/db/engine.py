from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from abu_v60.settings import settings

engine: Engine = create_engine(settings.database_url, pool_pre_ping=True)


def database_health(*, expected_foundation_version: str | None = None) -> dict[str, object]:
    try:
        with engine.connect() as connection:
            version = connection.execute(
                text(
                    "SELECT foundation_version FROM platform.schema_manifest WHERE singleton_id = 1"
                )
            ).scalar_one()
        if expected_foundation_version is not None and version != expected_foundation_version:
            return {
                "status": "incompatible",
                "foundation_version": version,
                "expected_foundation_version": expected_foundation_version,
            }
        return {
            "status": "ready",
            "foundation_version": version,
            "expected_foundation_version": expected_foundation_version,
        }
    except SQLAlchemyError as exc:
        return {"status": "unavailable", "reason": type(exc).__name__}
