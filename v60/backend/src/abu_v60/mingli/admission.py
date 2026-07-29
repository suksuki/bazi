from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import text

from abu_v60.mingli.compiler import CompiledCase
from abu_v60.provenance import canonical_json, content_hash


class MingliCaseAdmissionError(ValueError):
    pass


class MingliFactAdmissionDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    fact_ref: str = Field(min_length=1)
    fact_type: str = Field(min_length=1)
    subject_ref: str = Field(min_length=1)
    object_ref: str | None = None
    authority: str = Field(min_length=1)
    fact_payload: dict[str, Any]
    source_ref: str = Field(min_length=1)
    fact_hash: str = Field(min_length=64, max_length=64)


class MingliCaseAdmissionDefinition(BaseModel):
    """Typed immutable port from a deterministic compiler into Mingli storage."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    case_ref: str = Field(min_length=1)
    owner_account_ref: str = Field(min_length=1)
    profile_ref: str = Field(min_length=1)
    subject_kind: str = Field(min_length=1)
    case_status: str = Field(min_length=1)
    case_version: int = Field(ge=1)

    chart_version_ref: str = Field(min_length=1)
    chart_version: int = Field(ge=1)
    birth_input_hash: str = Field(min_length=64, max_length=64)
    pillars: dict[str, str]
    algorithm_version: str = Field(min_length=1)
    source_manifest: dict[str, Any]
    chart_hash: str = Field(min_length=64, max_length=64)
    facts: tuple[MingliFactAdmissionDefinition, ...]

    life_case_revision_ref: str = Field(min_length=1)
    life_case_revision: int = Field(ge=1)
    life_case_status: str = Field(min_length=1)
    life_case_payload: dict[str, Any]
    evidence_manifest: dict[str, Any]
    life_case_hash: str = Field(min_length=64, max_length=64)

    scene_ref: str = Field(min_length=1)
    scene_version: int = Field(ge=1)
    scene_payload: dict[str, Any]
    scene_hash: str = Field(min_length=64, max_length=64)

    @classmethod
    def from_compiled(
        cls,
        *,
        compiled: CompiledCase,
        case_ref: str,
        owner_account_ref: str,
        profile_ref: str,
        subject_kind: str,
        birth_input_hash: str,
        algorithm_version: str,
        source_manifest: dict[str, Any],
        case_status: str = "ACTIVE",
    ) -> Self:
        return cls(
            case_ref=case_ref,
            owner_account_ref=owner_account_ref,
            profile_ref=profile_ref,
            subject_kind=subject_kind,
            case_status=case_status,
            case_version=1,
            chart_version_ref=compiled.chart_version_ref,
            chart_version=1,
            birth_input_hash=birth_input_hash,
            pillars=compiled.pillars,
            algorithm_version=algorithm_version,
            source_manifest=source_manifest,
            chart_hash=compiled.chart_hash,
            facts=tuple(
                MingliFactAdmissionDefinition(
                    fact_ref=fact["fact_ref"],
                    fact_type=fact["fact_type"],
                    subject_ref=fact["subject_ref"],
                    object_ref=fact["object_ref"],
                    authority=fact["authority"],
                    fact_payload=fact["fact_json"],
                    source_ref=fact["source_ref"],
                    fact_hash=fact["fact_hash"],
                )
                for fact in compiled.facts
            ),
            life_case_revision_ref=compiled.life_case_revision_ref,
            life_case_revision=1,
            life_case_status=str(compiled.life_case_payload["status"]),
            life_case_payload=compiled.life_case_payload,
            evidence_manifest=compiled.evidence_manifest,
            life_case_hash=compiled.life_case_hash,
            scene_ref=compiled.scene_ref,
            scene_version=1,
            scene_payload=compiled.scene_payload,
            scene_hash=compiled.scene_hash,
        )

    @model_validator(mode="after")
    def immutable_hashes_and_lineage_match(self) -> MingliCaseAdmissionDefinition:
        chart_payload = {
            "case_ref": self.case_ref,
            "version": self.chart_version,
            "birth_input_hash": self.birth_input_hash,
            "pillars": self.pillars,
            "algorithm_version": self.algorithm_version,
        }
        if content_hash(chart_payload) != self.chart_hash:
            raise ValueError("mingli_chart_hash_mismatch")

        fact_refs: list[str] = []
        for fact in self.facts:
            identity = {
                "case_ref": self.case_ref,
                "chart_version_ref": self.chart_version_ref,
                "fact_type": fact.fact_type,
                "subject_ref": fact.subject_ref,
                "object_ref": fact.object_ref,
                "payload": fact.fact_payload,
                "source_ref": fact.source_ref,
            }
            if content_hash(identity) != fact.fact_hash:
                raise ValueError("mingli_fact_hash_mismatch")
            fact_refs.append(fact.fact_ref)

        if (
            self.life_case_payload.get("case_ref") != self.case_ref
            or self.life_case_payload.get("chart_version_ref") != self.chart_version_ref
            or self.life_case_payload.get("fact_refs") != fact_refs
            or self.life_case_payload.get("status") != self.life_case_status
        ):
            raise ValueError("mingli_life_case_lineage_mismatch")
        if (
            content_hash(
                {
                    "payload": self.life_case_payload,
                    "evidence_manifest": self.evidence_manifest,
                }
            )
            != self.life_case_hash
        ):
            raise ValueError("mingli_life_case_hash_mismatch")
        if (
            self.scene_payload.get("case_ref") != self.case_ref
            or self.scene_payload.get("life_case_revision_ref") != self.life_case_revision_ref
        ):
            raise ValueError("mingli_scene_lineage_mismatch")
        if content_hash(self.scene_payload) != self.scene_hash:
            raise ValueError("mingli_scene_hash_mismatch")
        return self


class MingliCaseAdmissionService:
    """Mingli-owned idempotent write path for one compiled Case lineage."""

    def activate_owner_case(
        self,
        connection: Any,
        *,
        account_ref: str,
        case_ref: str,
        require_existing: bool = True,
    ) -> bool:
        connection.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:account_ref))"),
            {"account_ref": account_ref},
        )
        target_exists = connection.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM mingli.cases
                    WHERE case_ref = :case_ref
                      AND owner_account_ref = :account_ref
                      AND subject_kind = 'HUMAN_OWNER'
                )
                """
            ),
            {"case_ref": case_ref, "account_ref": account_ref},
        ).scalar_one()
        if require_existing and not target_exists:
            raise MingliCaseAdmissionError("owner_case_not_found")

        connection.execute(
            text(
                """
                UPDATE mingli.cases
                SET status = 'INACTIVE'
                WHERE owner_account_ref = :account_ref
                  AND subject_kind = 'HUMAN_OWNER'
                  AND status = 'ACTIVE'
                  AND case_ref <> :case_ref
                """
            ),
            {"account_ref": account_ref, "case_ref": case_ref},
        )
        if target_exists:
            connection.execute(
                text(
                    """
                    UPDATE mingli.cases
                    SET status = 'ACTIVE'
                    WHERE case_ref = :case_ref
                    """
                ),
                {"case_ref": case_ref},
            )
        return bool(target_exists)

    def admit(
        self,
        connection: Any,
        *,
        definition: MingliCaseAdmissionDefinition,
    ) -> None:
        connection.execute(
            text(
                """
                INSERT INTO mingli.cases
                    (case_ref, owner_account_ref, profile_ref,
                     subject_kind, status, case_version)
                VALUES
                    (:case_ref, :owner_account_ref, :profile_ref,
                     :subject_kind, :case_status, :case_version)
                ON CONFLICT (case_ref) DO NOTHING
                """
            ),
            definition.model_dump(
                mode="python",
                include={
                    "case_ref",
                    "owner_account_ref",
                    "profile_ref",
                    "subject_kind",
                    "case_status",
                    "case_version",
                },
            ),
        )
        connection.execute(
            text(
                """
                INSERT INTO mingli.chart_versions
                    (chart_version_ref, case_ref, version, birth_input_hash,
                     pillars_json, algorithm_version, source_manifest_json, chart_hash)
                VALUES
                    (:chart_version_ref, :case_ref, :chart_version, :birth_input_hash,
                     CAST(:pillars AS jsonb), :algorithm_version,
                     CAST(:source_manifest AS jsonb), :chart_hash)
                ON CONFLICT (chart_version_ref) DO NOTHING
                """
            ),
            {
                "chart_version_ref": definition.chart_version_ref,
                "case_ref": definition.case_ref,
                "chart_version": definition.chart_version,
                "birth_input_hash": definition.birth_input_hash,
                "pillars": canonical_json(definition.pillars),
                "algorithm_version": definition.algorithm_version,
                "source_manifest": canonical_json(definition.source_manifest),
                "chart_hash": definition.chart_hash,
            },
        )
        for fact in definition.facts:
            connection.execute(
                text(
                    """
                    INSERT INTO mingli.facts
                        (fact_ref, case_ref, chart_version_ref, fact_type,
                         subject_ref, object_ref, authority, fact_json,
                         source_ref, fact_hash)
                    VALUES
                        (:fact_ref, :case_ref, :chart_version_ref, :fact_type,
                         :subject_ref, :object_ref, :authority,
                         CAST(:fact_payload AS jsonb), :source_ref, :fact_hash)
                    ON CONFLICT (fact_ref) DO NOTHING
                    """
                ),
                {
                    **fact.model_dump(mode="python", exclude={"fact_payload"}),
                    "case_ref": definition.case_ref,
                    "chart_version_ref": definition.chart_version_ref,
                    "fact_payload": canonical_json(fact.fact_payload),
                },
            )
        connection.execute(
            text(
                """
                INSERT INTO mingli.life_case_revisions
                    (life_case_revision_ref, case_ref, chart_version_ref, revision,
                     status, payload_json, evidence_manifest_json, revision_hash)
                VALUES
                    (:life_case_revision_ref, :case_ref, :chart_version_ref,
                     :life_case_revision, :life_case_status,
                     CAST(:life_case_payload AS jsonb),
                     CAST(:evidence_manifest AS jsonb), :life_case_hash)
                ON CONFLICT (life_case_revision_ref) DO NOTHING
                """
            ),
            {
                "life_case_revision_ref": definition.life_case_revision_ref,
                "case_ref": definition.case_ref,
                "chart_version_ref": definition.chart_version_ref,
                "life_case_revision": definition.life_case_revision,
                "life_case_status": definition.life_case_status,
                "life_case_payload": canonical_json(definition.life_case_payload),
                "evidence_manifest": canonical_json(definition.evidence_manifest),
                "life_case_hash": definition.life_case_hash,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO mingli.canonical_scenes
                    (scene_ref, case_ref, life_case_revision_ref,
                     scene_version, scene_json, scene_hash)
                VALUES
                    (:scene_ref, :case_ref, :life_case_revision_ref,
                     :scene_version, CAST(:scene_payload AS jsonb), :scene_hash)
                ON CONFLICT (scene_ref) DO NOTHING
                """
            ),
            {
                "scene_ref": definition.scene_ref,
                "case_ref": definition.case_ref,
                "life_case_revision_ref": definition.life_case_revision_ref,
                "scene_version": definition.scene_version,
                "scene_payload": canonical_json(definition.scene_payload),
                "scene_hash": definition.scene_hash,
            },
        )
        self._verify(connection, definition=definition)

    @staticmethod
    def _verify(
        connection: Any,
        *,
        definition: MingliCaseAdmissionDefinition,
    ) -> None:
        root = (
            connection.execute(
                text(
                    """
                    SELECT c.owner_account_ref, c.profile_ref, c.subject_kind,
                           c.status AS case_status, c.case_version,
                           cv.case_ref AS chart_case_ref, cv.version AS chart_version,
                           cv.birth_input_hash, cv.pillars_json, cv.algorithm_version,
                           cv.source_manifest_json, cv.chart_hash,
                           lc.case_ref AS life_case_ref_case,
                           lc.chart_version_ref AS life_case_chart_ref,
                           lc.revision AS life_case_revision,
                           lc.status AS life_case_status, lc.payload_json,
                           lc.evidence_manifest_json, lc.revision_hash,
                           cs.case_ref AS scene_case_ref,
                           cs.life_case_revision_ref AS scene_life_case_ref,
                           cs.scene_version, cs.scene_json, cs.scene_hash
                    FROM mingli.cases AS c
                    JOIN mingli.chart_versions AS cv
                      ON cv.chart_version_ref = :chart_version_ref
                    JOIN mingli.life_case_revisions AS lc
                      ON lc.life_case_revision_ref = :life_case_revision_ref
                    JOIN mingli.canonical_scenes AS cs
                      ON cs.scene_ref = :scene_ref
                    WHERE c.case_ref = :case_ref
                    """
                ),
                {
                    "case_ref": definition.case_ref,
                    "chart_version_ref": definition.chart_version_ref,
                    "life_case_revision_ref": definition.life_case_revision_ref,
                    "scene_ref": definition.scene_ref,
                },
            )
            .mappings()
            .one()
        )
        expected_root = {
            "owner_account_ref": definition.owner_account_ref,
            "profile_ref": definition.profile_ref,
            "subject_kind": definition.subject_kind,
            "case_status": definition.case_status,
            "case_version": definition.case_version,
            "chart_case_ref": definition.case_ref,
            "chart_version": definition.chart_version,
            "birth_input_hash": definition.birth_input_hash,
            "pillars_json": definition.pillars,
            "algorithm_version": definition.algorithm_version,
            "source_manifest_json": definition.source_manifest,
            "chart_hash": definition.chart_hash,
            "life_case_ref_case": definition.case_ref,
            "life_case_chart_ref": definition.chart_version_ref,
            "life_case_revision": definition.life_case_revision,
            "life_case_status": definition.life_case_status,
            "payload_json": definition.life_case_payload,
            "evidence_manifest_json": definition.evidence_manifest,
            "revision_hash": definition.life_case_hash,
            "scene_case_ref": definition.case_ref,
            "scene_life_case_ref": definition.life_case_revision_ref,
            "scene_version": definition.scene_version,
            "scene_json": definition.scene_payload,
            "scene_hash": definition.scene_hash,
        }
        fact_rows = (
            connection.execute(
                text(
                    """
                    SELECT fact_ref, fact_type, subject_ref, object_ref, authority,
                           fact_json, source_ref, fact_hash
                    FROM mingli.facts
                    WHERE case_ref = :case_ref
                      AND chart_version_ref = :chart_version_ref
                    ORDER BY fact_ref
                    """
                ),
                {
                    "case_ref": definition.case_ref,
                    "chart_version_ref": definition.chart_version_ref,
                },
            )
            .mappings()
            .all()
        )
        expected_facts = sorted(
            (
                {
                    "fact_ref": fact.fact_ref,
                    "fact_type": fact.fact_type,
                    "subject_ref": fact.subject_ref,
                    "object_ref": fact.object_ref,
                    "authority": fact.authority,
                    "fact_json": fact.fact_payload,
                    "source_ref": fact.source_ref,
                    "fact_hash": fact.fact_hash,
                }
                for fact in definition.facts
            ),
            key=lambda fact: fact["fact_ref"],
        )
        if dict(root) != expected_root or [dict(row) for row in fact_rows] != expected_facts:
            raise MingliCaseAdmissionError("mingli_case_admission_conflict")
