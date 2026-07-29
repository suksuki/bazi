from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.identity import (
    AccountAdmissionDefinition,
    IdentityAdmissionDefinition,
    IdentityAdmissionError,
    IdentityAdmissionService,
    ProfileAdmissionDefinition,
)
from abu_v60.identity.security import PBKDF2_SHA256_310K
from abu_v60.migration.admission import (
    MigrationBatchAdmissionError,
    MigrationBatchAdmissionService,
    MigrationBatchDefinition,
)
from abu_v60.mingli import (
    MingliCaseAdmissionDefinition,
    MingliCaseAdmissionError,
    MingliCaseAdmissionService,
)
from abu_v60.mingli.calendar import CALENDAR_ENGINE_VERSION, BirthInput, resolve_four_pillars
from abu_v60.mingli.compiler import CompiledCase, compile_case
from abu_v60.provenance import content_hash, stable_ref


class MigrationBoundaryError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class MigrationResult:
    batch_ref: str
    account_ref: str
    profile_ref: str
    case_ref: str
    chart_version_ref: str
    life_case_revision_ref: str
    scene_ref: str
    pillars: tuple[str, str, str, str]
    fact_count: int
    subject_kind: str


@dataclass(frozen=True, slots=True)
class AccountCorpusImportResult:
    account_ref: str
    owner_profile_id: str
    profile_count: int
    imports: tuple[MigrationResult, ...]


class V50OwnerImporter:
    def __init__(self, *, source_engine: Engine, target_engine: Engine) -> None:
        self._source = source_engine
        self._target = target_engine

    def import_selected_profile(
        self,
        *,
        email: str,
        profile_id: str,
        subject_kind: str = "HUMAN_OWNER",
    ) -> MigrationResult:
        if subject_kind not in {"HUMAN_OWNER", "HUMAN_REFERENCE"}:
            raise MigrationBoundaryError("unsupported_v50_subject_kind")
        account, profile = self._read_source(email=email, profile_id=profile_id)
        birth_input = BirthInput(
            calendar_type=profile["calendar_type"],
            birth_date=date.fromisoformat(profile["birth_date"]),
            birth_time=time.fromisoformat(profile["birth_time"]),
            timezone=profile["timezone"],
            lunar_leap_month=bool(profile["profile_json"].get("lunar_leap_month", False)),
            true_solar_time_policy=profile["profile_json"].get(
                "true_solar_time_policy", "not_applied"
            ),
        )
        chart = resolve_four_pillars(birth_input)
        stored_pillars = tuple(profile["pillars"])
        if tuple(chart.ordered()) != stored_pillars:
            raise MigrationBoundaryError(
                f"recomputed_pillars_mismatch:stored={stored_pillars}:computed={chart.ordered()}"
            )

        source_account_hash = content_hash(_account_source_material(account))
        source_profile_hash = content_hash(_profile_source_material(profile))
        account_ref = stable_ref("v60-account", {"v50_user_id": account["user_id"]})
        profile_ref = stable_ref("v60-profile", {"v50_profile_id": profile["profile_id"]})
        case_ref = stable_ref(
            "v60-case",
            {"profile_ref": profile_ref, "purpose": "owner-real-case"},
        )
        compiled = compile_case(case_ref=case_ref, birth_input=birth_input, chart=chart)
        existing = self._reuse_existing_import(
            account_ref=account_ref,
            profile_ref=profile_ref,
            case_ref=case_ref,
            source_profile_ref=f"v50.profile:{profile['profile_id']}",
            source_profile_hash=source_profile_hash,
            subject_kind=subject_kind,
            birth_input=birth_input,
            compiled=compiled,
        )
        if existing is not None:
            return existing
        manifest = {
            "policy": "v60.v50-whitelist-owner-import.v2",
            "source_account_ref": f"v50.account:{account['user_id']}",
            "source_account_hash": source_account_hash,
            "source_profile_ref": f"v50.profile:{profile['profile_id']}",
            "source_profile_hash": source_profile_hash,
            "admitted": ["credential_verifier", "birth_input"],
            "recomputed": ["four_pillars", "bounded_chart_facts", "life_case_baseline"],
            "rejected": [
                "v50_life_case",
                "professional_conclusions",
                "dream_state",
                "fixtures",
            ],
            "pillar_parity": True,
            "calendar_engine": CALENDAR_ENGINE_VERSION,
            "subject_kind": subject_kind,
        }
        manifest_hash = content_hash(manifest)
        batch_ref = stable_ref("v60-migration", manifest_hash)
        self._write_target(
            account=account,
            profile=profile,
            birth_input=birth_input,
            account_ref=account_ref,
            profile_ref=profile_ref,
            case_ref=case_ref,
            source_account_hash=source_account_hash,
            source_profile_hash=source_profile_hash,
            batch_ref=batch_ref,
            manifest=manifest,
            compiled=compiled,
            subject_kind=subject_kind,
        )
        return MigrationResult(
            batch_ref=batch_ref,
            account_ref=account_ref,
            profile_ref=profile_ref,
            case_ref=case_ref,
            chart_version_ref=compiled.chart_version_ref,
            life_case_revision_ref=compiled.life_case_revision_ref,
            scene_ref=compiled.scene_ref,
            pillars=tuple(chart.ordered()),
            fact_count=len(compiled.facts),
            subject_kind=subject_kind,
        )

    def import_account_corpus(
        self,
        *,
        email: str,
        owner_profile_id: str,
    ) -> AccountCorpusImportResult:
        profile_ids = self._source_profile_ids(email=email)
        if owner_profile_id not in profile_ids:
            raise MigrationBoundaryError("owner_profile_not_found_in_source_account")
        ordered_ids = (owner_profile_id, *sorted(set(profile_ids) - {owner_profile_id}))
        imports = tuple(
            self.import_selected_profile(
                email=email,
                profile_id=profile_id,
                subject_kind=(
                    "HUMAN_OWNER"
                    if profile_id == owner_profile_id
                    else "HUMAN_REFERENCE"
                ),
            )
            for profile_id in ordered_ids
        )
        return AccountCorpusImportResult(
            account_ref=imports[0].account_ref,
            owner_profile_id=owner_profile_id,
            profile_count=len(imports),
            imports=imports,
        )

    def _source_profile_ids(self, *, email: str) -> tuple[str, ...]:
        with self._source.connect() as connection:
            account_ref = connection.execute(
                text(
                    """
                    SELECT user_id
                    FROM v50_user_accounts
                    WHERE lower(email) = lower(:email)
                      AND active = true
                    """
                ),
                {"email": email},
            ).scalar_one_or_none()
            if account_ref is None:
                raise MigrationBoundaryError("source_account_not_found")
            rows = connection.execute(
                text(
                    """
                    SELECT profile_id
                    FROM v50_bazi_profiles
                    WHERE user_id = :user_id
                      AND deleted = false
                    ORDER BY created_at, profile_id
                    """
                ),
                {"user_id": account_ref},
            ).scalars()
        return tuple(str(profile_id) for profile_id in rows)

    def _reuse_existing_import(
        self,
        *,
        account_ref: str,
        profile_ref: str,
        case_ref: str,
        source_profile_ref: str,
        source_profile_hash: str,
        subject_kind: str,
        birth_input: BirthInput,
        compiled: CompiledCase,
    ) -> MigrationResult | None:
        with self._target.connect() as connection:
            profile_exists = connection.execute(
                text(
                    """
                    SELECT 1
                    FROM identity.profiles
                    WHERE profile_ref = :profile_ref
                    """
                ),
                {"profile_ref": profile_ref},
            ).scalar_one_or_none()
            if profile_exists is None:
                return None
            row = (
                connection.execute(
                    text(
                        """
                        SELECT a.source_batch_ref, p.account_ref, p.source_ref,
                               p.source_hash, c.owner_account_ref, c.subject_kind,
                               c.status AS case_status, c.case_version,
                               cv.birth_input_hash, cv.pillars_json,
                               cv.algorithm_version, cv.chart_hash,
                               lc.revision_hash AS life_case_hash,
                               cs.scene_hash,
                               (
                                   SELECT count(*)
                                   FROM mingli.facts AS f
                                   WHERE f.case_ref = c.case_ref
                                     AND f.chart_version_ref = cv.chart_version_ref
                               ) AS fact_count
                        FROM identity.profiles AS p
                        JOIN identity.accounts AS a
                          ON a.account_ref = p.account_ref
                        JOIN mingli.cases AS c
                          ON c.profile_ref = p.profile_ref
                         AND c.case_ref = :case_ref
                        JOIN mingli.chart_versions AS cv
                          ON cv.chart_version_ref = :chart_version_ref
                         AND cv.case_ref = c.case_ref
                        JOIN mingli.life_case_revisions AS lc
                          ON lc.life_case_revision_ref = :life_case_revision_ref
                         AND lc.case_ref = c.case_ref
                        JOIN mingli.canonical_scenes AS cs
                          ON cs.scene_ref = :scene_ref
                         AND cs.case_ref = c.case_ref
                        WHERE p.profile_ref = :profile_ref
                        """
                    ),
                    {
                        "case_ref": case_ref,
                        "chart_version_ref": compiled.chart_version_ref,
                        "life_case_revision_ref": compiled.life_case_revision_ref,
                        "scene_ref": compiled.scene_ref,
                        "profile_ref": profile_ref,
                    },
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            raise MigrationBoundaryError("existing_v60_profile_lineage_conflict")
        expected = {
            "account_ref": account_ref,
            "source_ref": source_profile_ref,
            "source_hash": source_profile_hash,
            "owner_account_ref": account_ref,
            "subject_kind": subject_kind,
            "case_status": "ACTIVE",
            "case_version": 1,
            "birth_input_hash": birth_input.input_hash,
            "pillars_json": compiled.pillars,
            "algorithm_version": CALENDAR_ENGINE_VERSION,
            "chart_hash": compiled.chart_hash,
            "life_case_hash": compiled.life_case_hash,
            "scene_hash": compiled.scene_hash,
            "fact_count": len(compiled.facts),
        }
        actual = {key: row[key] for key in expected}
        if actual != expected:
            raise MigrationBoundaryError("existing_v60_profile_lineage_conflict")
        return MigrationResult(
            batch_ref=str(row["source_batch_ref"]),
            account_ref=account_ref,
            profile_ref=profile_ref,
            case_ref=case_ref,
            chart_version_ref=compiled.chart_version_ref,
            life_case_revision_ref=compiled.life_case_revision_ref,
            scene_ref=compiled.scene_ref,
            pillars=tuple(compiled.pillars[slot] for slot in ("year", "month", "day", "hour")),
            fact_count=len(compiled.facts),
            subject_kind=subject_kind,
        )

    def _read_source(self, *, email: str, profile_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        with self._source.connect() as connection:
            account_row = (
                connection.execute(
                    text(
                        """
                    SELECT user_id, email, display_name, account_role, active,
                           password_hash, password_salt, account_json
                    FROM v50_user_accounts
                    WHERE lower(email) = lower(:email)
                    """
                    ),
                    {"email": email},
                )
                .mappings()
                .one_or_none()
            )
            if account_row is None:
                raise MigrationBoundaryError("source_account_not_found")
            profile_row = (
                connection.execute(
                    text(
                        """
                    SELECT profile_id, user_id, display_name, gender, calendar_type,
                           birth_date, birth_time, birth_location, timezone, pillars,
                           profile_json
                    FROM v50_bazi_profiles
                    WHERE profile_id = :profile_id
                      AND user_id = :user_id
                      AND deleted = false
                    """
                    ),
                    {"profile_id": profile_id, "user_id": account_row["user_id"]},
                )
                .mappings()
                .one_or_none()
            )
            if profile_row is None:
                raise MigrationBoundaryError("source_profile_not_found_or_not_owned")
        account = dict(account_row)
        profile = dict(profile_row)
        if not account["active"]:
            raise MigrationBoundaryError("source_account_inactive")
        if profile["calendar_type"] not in {"solar", "lunar"}:
            raise MigrationBoundaryError("unsupported_source_calendar_type")
        if not profile["pillars"] or len(profile["pillars"]) != 4:
            raise MigrationBoundaryError("source_pillars_incomplete")
        return account, profile

    def _write_target(
        self,
        *,
        account: dict[str, Any],
        profile: dict[str, Any],
        birth_input: BirthInput,
        account_ref: str,
        profile_ref: str,
        case_ref: str,
        source_account_hash: str,
        source_profile_hash: str,
        batch_ref: str,
        manifest: dict[str, Any],
        compiled: CompiledCase,
        subject_kind: str,
    ) -> None:
        with self._target.begin() as connection:
            try:
                existing_account_batch_ref = connection.execute(
                    text(
                        """
                        SELECT source_batch_ref
                        FROM identity.accounts
                        WHERE account_ref = :account_ref
                        """
                    ),
                    {"account_ref": account_ref},
                ).scalar_one_or_none()
                MigrationBatchAdmissionService().admit(
                    connection,
                    definition=MigrationBatchDefinition(
                        batch_ref=batch_ref,
                        source_system="V50",
                        source_database="qiazhi_v50",
                        status="COMPLETED",
                        manifest=manifest,
                    ),
                )
                IdentityAdmissionService().admit(
                    connection,
                    definition=IdentityAdmissionDefinition(
                        account=AccountAdmissionDefinition(
                            account_ref=account_ref,
                            email=account["email"].lower(),
                            display_name=account["display_name"],
                            account_role=account["account_role"],
                            active=True,
                            password_scheme=PBKDF2_SHA256_310K,
                            password_hash=account["password_hash"],
                            password_salt=account["password_salt"],
                            source_ref=f"v50.account:{account['user_id']}",
                            source_hash=source_account_hash,
                            source_batch_ref=(
                                str(existing_account_batch_ref)
                                if existing_account_batch_ref is not None
                                else batch_ref
                            ),
                        ),
                        profile=ProfileAdmissionDefinition(
                            profile_ref=profile_ref,
                            account_ref=account_ref,
                            display_name=profile["display_name"],
                            gender=profile["gender"],
                            calendar_type=profile["calendar_type"],
                            birth_date=birth_input.birth_date,
                            birth_time=birth_input.birth_time,
                            birth_location=profile["birth_location"],
                            timezone=profile["timezone"],
                            source_ref=f"v50.profile:{profile['profile_id']}",
                            source_hash=source_profile_hash,
                            input_payload=birth_input.model_dump(mode="json"),
                        ),
                    ),
                )
                MingliCaseAdmissionService().admit(
                    connection,
                    definition=MingliCaseAdmissionDefinition.from_compiled(
                        compiled=compiled,
                        case_ref=case_ref,
                        owner_account_ref=account_ref,
                        profile_ref=profile_ref,
                        subject_kind=subject_kind,
                        birth_input_hash=birth_input.input_hash,
                        algorithm_version=CALENDAR_ENGINE_VERSION,
                        source_manifest={
                            "migration_batch_ref": batch_ref,
                            "source_profile_ref": f"v50.profile:{profile['profile_id']}",
                            "source_profile_hash": source_profile_hash,
                            "pillar_parity": True,
                        },
                    ),
                )
            except (
                IdentityAdmissionError,
                MigrationBatchAdmissionError,
                MingliCaseAdmissionError,
            ) as exc:
                raise MigrationBoundaryError(str(exc)) from exc


def _account_source_material(account: dict[str, Any]) -> dict[str, Any]:
    return {
        "user_id": account["user_id"],
        "email": account["email"],
        "display_name": account["display_name"],
        "account_role": account["account_role"],
        "active": account["active"],
        "password_hash": account["password_hash"],
        "password_salt": account["password_salt"],
    }


def _profile_source_material(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "profile_id": profile["profile_id"],
        "user_id": profile["user_id"],
        "display_name": profile["display_name"],
        "gender": profile["gender"],
        "calendar_type": profile["calendar_type"],
        "birth_date": profile["birth_date"],
        "birth_time": profile["birth_time"],
        "birth_location": profile["birth_location"],
        "timezone": profile["timezone"],
        "pillars": profile["pillars"],
        "profile_json": profile["profile_json"],
    }
