from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy import text

from abu_v60.provenance import canonical_json, content_hash, stable_ref

DREAM_GROVE_VERSION = "v60.dream-grove.004"
THREE_LIFE_POOL_REF = "v60.dream-grove.three-life-qualification.001"


class DreamGroveError(ValueError):
    pass


class GroveCandidateDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    candidate_ref: str = Field(min_length=1)
    pool_ref: str = Field(min_length=1)
    question_ref: str = Field(min_length=1)
    actor_ref: str = Field(min_length=1)
    tree_ref: str = Field(min_length=1)
    domain: Literal["career", "wealth", "relationship"]
    public_alias: str = Field(min_length=1)
    premise: str = Field(min_length=1)
    display_order: int = Field(ge=1)
    runtime_status: Literal["ACTIVE", "RETIRED"] = "ACTIVE"
    candidate_hash: str = Field(min_length=64, max_length=64)

    @model_validator(mode="after")
    def identity_is_valid(self) -> GroveCandidateDefinition:
        identity = self.model_dump(
            mode="json",
            exclude={"candidate_ref", "candidate_hash"},
        )
        if self.candidate_ref != stable_ref("v60-dream-grove-candidate", identity):
            raise ValueError("dream_grove_candidate_ref_mismatch")
        if self.candidate_hash != content_hash(identity):
            raise ValueError("dream_grove_candidate_hash_mismatch")
        return self

    @classmethod
    def issue(cls, **values: Any) -> GroveCandidateDefinition:
        identity = {
            "pool_ref": values["pool_ref"],
            "question_ref": values["question_ref"],
            "actor_ref": values["actor_ref"],
            "tree_ref": values["tree_ref"],
            "domain": values["domain"],
            "public_alias": values["public_alias"],
            "premise": values["premise"],
            "display_order": values["display_order"],
            "runtime_status": values.get("runtime_status", "ACTIVE"),
        }
        return cls(
            candidate_ref=stable_ref("v60-dream-grove-candidate", identity),
            candidate_hash=content_hash(identity),
            **identity,
        )


class DreamGroveAdmissionService:
    def admit(self, connection: Any, *, definition: GroveCandidateDefinition) -> None:
        payload = definition.model_dump(
            mode="json",
            exclude={"candidate_hash"},
        )
        connection.execute(
            text(
                """
                INSERT INTO dream.grove_candidates
                    (candidate_ref, pool_ref, question_ref, actor_ref, tree_ref,
                     domain, public_alias, premise, display_order,
                     runtime_status, candidate_json, candidate_hash)
                VALUES
                    (:candidate_ref, :pool_ref, :question_ref, :actor_ref,
                     :tree_ref, :domain, :public_alias, :premise,
                     :display_order, :runtime_status,
                     CAST(:candidate_json AS jsonb), :candidate_hash)
                ON CONFLICT (candidate_ref) DO NOTHING
                """
            ),
            {
                **definition.model_dump(
                    mode="python",
                    exclude={"candidate_hash"},
                ),
                "candidate_json": canonical_json(payload),
                "candidate_hash": definition.candidate_hash,
            },
        )
        persisted = (
            connection.execute(
                text(
                    """
                    SELECT candidate_json, candidate_hash
                    FROM dream.grove_candidates
                    WHERE candidate_ref = :candidate_ref
                    """
                ),
                {"candidate_ref": definition.candidate_ref},
            )
            .mappings()
            .one()
        )
        if (
            persisted["candidate_json"] != payload
            or persisted["candidate_hash"] != definition.candidate_hash
        ):
            raise DreamGroveError("dream_grove_candidate_identity_conflict")


class DreamGroveRepository:
    @staticmethod
    def active_candidates(
        connection: Any,
        *,
        pool_ref: str = THREE_LIFE_POOL_REF,
    ) -> list[dict[str, Any]]:
        rows = (
            connection.execute(
                text(
                    """
                    SELECT candidate.candidate_ref, candidate.pool_ref,
                           candidate.question_ref, candidate.actor_ref,
                           candidate.tree_ref, candidate.domain,
                           candidate.public_alias, candidate.premise,
                           candidate.display_order, candidate.runtime_status,
                           candidate.candidate_json, candidate.candidate_hash,
                           scene.scene_json, scene.scene_hash,
                           tree.state AS tree_state,
                           tree.tree_version AS tree_version
                    FROM dream.grove_candidates AS candidate
                    JOIN dream.life_trees AS tree
                      ON tree.tree_ref = candidate.tree_ref
                    JOIN mingli.canonical_scenes AS scene
                      ON scene.scene_ref = tree.scene_ref
                    JOIN story.question_instances AS question
                      ON question.question_ref = candidate.question_ref
                    WHERE candidate.pool_ref = :pool_ref
                      AND candidate.runtime_status = 'ACTIVE'
                      AND question.episode_contract_json
                          ->> 'runtime_status' = 'ACTIVE'
                    ORDER BY candidate.display_order
                    """
                ),
                {"pool_ref": pool_ref},
            )
            .mappings()
            .all()
        )
        candidates: list[dict[str, Any]] = []
        for row in rows:
            payload = row["candidate_json"]
            if (
                content_hash(
                    {
                        key: payload[key]
                        for key in (
                            "pool_ref",
                            "question_ref",
                            "actor_ref",
                            "tree_ref",
                            "domain",
                            "public_alias",
                            "premise",
                            "display_order",
                            "runtime_status",
                        )
                    }
                )
                != row["candidate_hash"]
            ):
                raise DreamGroveError("dream_grove_candidate_hash_mismatch")
            candidates.append(
                {
                    "candidate_ref": row["candidate_ref"],
                    "candidate_hash": row["candidate_hash"],
                    "tree_ref": row["tree_ref"],
                    "domain": row["domain"],
                    "public_alias": row["public_alias"],
                    "premise": row["premise"],
                    "display_order": row["display_order"],
                    "tree": {
                        "state": row["tree_state"],
                        "version": row["tree_version"],
                        "phenotype": row["scene_json"]["tree_phenotype"],
                        "scene_hash": row["scene_hash"],
                    },
                }
            )
        return candidates

    @staticmethod
    def candidate(
        connection: Any,
        *,
        candidate_ref: str,
        pool_ref: str = THREE_LIFE_POOL_REF,
    ) -> dict[str, Any] | None:
        definition = DreamGroveRepository.candidate_definition(
            connection,
            candidate_ref=candidate_ref,
            pool_ref=pool_ref,
            for_update=True,
        )
        if definition is None:
            return None
        return definition.model_dump(
            mode="python",
            include={
                "candidate_ref",
                "question_ref",
                "actor_ref",
                "tree_ref",
                "candidate_hash",
            },
        )

    @staticmethod
    def candidate_definition(
        connection: Any,
        *,
        candidate_ref: str,
        pool_ref: str = THREE_LIFE_POOL_REF,
        for_update: bool,
    ) -> GroveCandidateDefinition | None:
        lock_clause = "FOR UPDATE" if for_update else ""
        row = (
            connection.execute(
                text(
                    f"""
                    SELECT candidate_ref, question_ref, actor_ref, tree_ref,
                           candidate_json, candidate_hash
                    FROM dream.grove_candidates
                    WHERE candidate_ref = :candidate_ref
                      AND pool_ref = :pool_ref
                      AND runtime_status = 'ACTIVE'
                    {lock_clause}
                    """
                ),
                {"candidate_ref": candidate_ref, "pool_ref": pool_ref},
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        try:
            definition = GroveCandidateDefinition.model_validate(
                {
                    **row["candidate_json"],
                    "candidate_hash": row["candidate_hash"],
                }
            )
        except (ValidationError, ValueError) as exc:
            raise DreamGroveError("dream_grove_candidate_invalid") from exc
        if (
            definition.candidate_ref != row["candidate_ref"]
            or definition.question_ref != row["question_ref"]
            or definition.actor_ref != row["actor_ref"]
            or definition.tree_ref != row["tree_ref"]
        ):
            raise DreamGroveError(
                "dream_grove_candidate_column_mismatch"
            )
        return definition
