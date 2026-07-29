from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine


class CaseNotFoundError(ValueError):
    pass


class MingliCaseService:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_cases(self, *, account_ref: str) -> list[dict[str, Any]]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        """
                    SELECT c.case_ref, c.subject_kind, c.status, c.case_version,
                           p.profile_ref, p.display_name,
                           cv.chart_version_ref, cv.pillars_json,
                           lc.life_case_revision_ref,
                           cs.scene_ref, cs.scene_json
                    FROM mingli.cases AS c
                    JOIN identity.profiles AS p ON p.profile_ref = c.profile_ref
                    JOIN LATERAL (
                        SELECT chart_version_ref, pillars_json
                        FROM mingli.chart_versions
                        WHERE case_ref = c.case_ref
                        ORDER BY version DESC
                        LIMIT 1
                    ) AS cv ON true
                    JOIN LATERAL (
                        SELECT life_case_revision_ref
                        FROM mingli.life_case_revisions
                        WHERE case_ref = c.case_ref
                        ORDER BY revision DESC
                        LIMIT 1
                    ) AS lc ON true
                    JOIN LATERAL (
                        SELECT scene_ref, scene_json
                        FROM mingli.canonical_scenes
                        WHERE case_ref = c.case_ref
                        ORDER BY scene_version DESC
                        LIMIT 1
                    ) AS cs ON true
                    WHERE c.owner_account_ref = :account_ref
                    ORDER BY c.created_at, c.case_ref
                    """
                    ),
                    {"account_ref": account_ref},
                )
                .mappings()
                .all()
            )
        return [dict(row) for row in rows]

    def workspace(self, *, account_ref: str, case_ref: str) -> dict[str, Any]:
        with self._engine.connect() as connection:
            root = (
                connection.execute(
                    text(
                        """
                    SELECT c.case_ref, c.subject_kind, c.status, c.case_version,
                           p.profile_ref, p.display_name, p.gender, p.calendar_type,
                           p.birth_date, p.birth_time, p.birth_location, p.timezone,
                           p.input_json,
                           cv.chart_version_ref, cv.version AS chart_version,
                           cv.pillars_json, cv.algorithm_version, cv.chart_hash,
                           lc.life_case_revision_ref, lc.revision AS life_case_revision,
                           lc.status AS life_case_status, lc.payload_json,
                           lc.evidence_manifest_json, lc.revision_hash,
                           cs.scene_ref, cs.scene_version, cs.scene_json, cs.scene_hash
                    FROM mingli.cases AS c
                    JOIN identity.profiles AS p ON p.profile_ref = c.profile_ref
                    JOIN LATERAL (
                        SELECT *
                        FROM mingli.chart_versions
                        WHERE case_ref = c.case_ref
                        ORDER BY version DESC
                        LIMIT 1
                    ) AS cv ON true
                    JOIN LATERAL (
                        SELECT *
                        FROM mingli.life_case_revisions
                        WHERE case_ref = c.case_ref
                        ORDER BY revision DESC
                        LIMIT 1
                    ) AS lc ON true
                    JOIN LATERAL (
                        SELECT *
                        FROM mingli.canonical_scenes
                        WHERE case_ref = c.case_ref
                        ORDER BY scene_version DESC
                        LIMIT 1
                    ) AS cs ON true
                    WHERE c.case_ref = :case_ref
                      AND c.owner_account_ref = :account_ref
                    """
                    ),
                    {"case_ref": case_ref, "account_ref": account_ref},
                )
                .mappings()
                .one_or_none()
            )
            if root is None:
                raise CaseNotFoundError("case_not_found")
            facts = (
                connection.execute(
                    text(
                        """
                    SELECT fact_ref, fact_type, subject_ref, object_ref, authority,
                           fact_json, source_ref, fact_hash
                    FROM mingli.facts
                    WHERE case_ref = :case_ref
                      AND chart_version_ref = :chart_version_ref
                    ORDER BY fact_type, fact_ref
                    """
                    ),
                    {
                        "case_ref": case_ref,
                        "chart_version_ref": root["chart_version_ref"],
                    },
                )
                .mappings()
                .all()
            )
        return {
            "case": {
                "case_ref": root["case_ref"],
                "subject_kind": root["subject_kind"],
                "status": root["status"],
                "case_version": root["case_version"],
            },
            "profile": {
                "profile_ref": root["profile_ref"],
                "display_name": root["display_name"],
                "gender": root["gender"],
                "calendar_type": root["calendar_type"],
                "birth_date": root["birth_date"].isoformat(),
                "birth_time": root["birth_time"].isoformat(timespec="minutes"),
                "birth_location": root["birth_location"],
                "timezone": root["timezone"],
                "birth_input": {
                    "calendar_type": root["calendar_type"],
                    "birth_date": root["birth_date"].isoformat(),
                    "birth_time": root["birth_time"].isoformat(),
                    "timezone": root["timezone"],
                    "lunar_leap_month": bool(
                        root["input_json"].get("lunar_leap_month", False)
                    ),
                    "true_solar_time_policy": root["input_json"].get(
                        "true_solar_time_policy",
                        "not_applied",
                    ),
                },
            },
            "chart": {
                "chart_version_ref": root["chart_version_ref"],
                "version": root["chart_version"],
                "pillars": root["pillars_json"],
                "algorithm_version": root["algorithm_version"],
                "chart_hash": root["chart_hash"],
            },
            "life_case": {
                "life_case_revision_ref": root["life_case_revision_ref"],
                "revision": root["life_case_revision"],
                "status": root["life_case_status"],
                "payload": root["payload_json"],
                "evidence_manifest": root["evidence_manifest_json"],
                "revision_hash": root["revision_hash"],
            },
            "scene": {
                "scene_ref": root["scene_ref"],
                "version": root["scene_version"],
                "payload": root["scene_json"],
                "scene_hash": root["scene_hash"],
            },
            "facts": [dict(fact) for fact in facts],
        }
