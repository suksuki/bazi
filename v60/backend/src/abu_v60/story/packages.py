from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from abu_v60.game import DreamEpisodeDefinition
from abu_v60.provenance import content_hash
from abu_v60.story.contracts import EpisodeTransitionContract

EPISODE_SOURCE_PACKAGE_VERSION = "v60.episode-source-package.002"
EPISODE_SOURCE_REGISTRY_VERSION = "v60.episode-source-registry.002"
EPISODE_SOURCE_REGISTRY_HASH = "863708cccfe500d40a58f4ebe460e6e542e8ee1001fb896c1bc54b60fbbc2cba"
QUALIFICATION_EPISODE_SOURCE_REGISTRY_HASH = (
    "9c42166f63d97fb6608656f71077cc91283ef266b811e83b861f60b3cf7dacd8"
)


class EpisodeSourcePackageError(ValueError):
    pass


def _binding_markers(value: Any) -> tuple[str, ...]:
    markers: list[str] = []

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            if "$binding" in item:
                if set(item) != {"$binding"} or not isinstance(item["$binding"], str):
                    raise ValueError("episode_source_binding_marker_must_be_exact")
                markers.append(item["$binding"])
                return
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)

    visit(value)
    return tuple(markers)


def _bind_template(value: Any, bindings: dict[str, str]) -> Any:
    if isinstance(value, dict):
        if "$binding" in value:
            if set(value) != {"$binding"}:
                raise EpisodeSourcePackageError("episode_source_binding_marker_must_be_exact")
            key = value["$binding"]
            if key not in bindings:
                raise EpisodeSourcePackageError(f"episode_source_binding_missing:{key}")
            return bindings[key]
        return {key: _bind_template(item, bindings) for key, item in value.items()}
    if isinstance(value, list):
        return [_bind_template(item, bindings) for item in value]
    return value


class EpisodeSourcePackage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    package_version: Literal["v60.episode-source-package.002"]
    package_ref: str = Field(min_length=1)
    binding_keys: tuple[str, ...] = Field(min_length=1)
    definition_template: dict[str, Any]
    world_event_definitions: tuple[dict[str, Any], ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_bindings(self) -> EpisodeSourcePackage:
        if len(self.binding_keys) != len(set(self.binding_keys)):
            raise ValueError("episode_source_binding_keys_must_be_unique")
        if any(not key or key.startswith("$") for key in self.binding_keys):
            raise ValueError("episode_source_binding_key_invalid")
        markers = _binding_markers(self.definition_template)
        if set(markers) != set(self.binding_keys):
            raise ValueError("episode_source_binding_manifest_mismatch")
        event_refs = [
            definition.get("world_event_ref") for definition in self.world_event_definitions
        ]
        if any(not isinstance(event_ref, str) or not event_ref for event_ref in event_refs) or len(
            event_refs
        ) != len(set(event_refs)):
            raise ValueError("episode_source_world_event_refs_must_be_unique")
        return self


class EpisodeSourceRegistryRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    package_ref: str = Field(min_length=1)
    path: str = Field(min_length=1)
    package_hash: str = Field(min_length=64, max_length=64)


class EpisodeSourceTransition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    from_package_ref: str = Field(min_length=1)
    to_package_ref: str = Field(min_length=1)
    definition: EpisodeTransitionContract

    @model_validator(mode="after")
    def validate_distinct_packages(self) -> EpisodeSourceTransition:
        if self.from_package_ref == self.to_package_ref:
            raise ValueError("episode_source_transition_cannot_target_same_package")
        return self


class EpisodeSourceRegistryDocument(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    registry_version: Literal["v60.episode-source-registry.002"]
    packages: tuple[EpisodeSourceRegistryRow, ...] = Field(min_length=1)
    transitions: tuple[EpisodeSourceTransition, ...] = ()

    @model_validator(mode="after")
    def validate_rows(self) -> EpisodeSourceRegistryDocument:
        package_refs = [row.package_ref for row in self.packages]
        paths = [row.path for row in self.packages]
        if len(package_refs) != len(set(package_refs)):
            raise ValueError("episode_source_package_refs_must_be_unique")
        if len(paths) != len(set(paths)):
            raise ValueError("episode_source_package_paths_must_be_unique")
        package_ref_set = set(package_refs)
        for transition in self.transitions:
            if (
                transition.from_package_ref not in package_ref_set
                or transition.to_package_ref not in package_ref_set
            ):
                raise ValueError("episode_source_transition_package_unknown")
        return self


class EpisodeSourceCompilation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    package_ref: str = Field(min_length=1)
    package_hash: str = Field(min_length=64, max_length=64)
    definition: DreamEpisodeDefinition
    world_event_definitions: tuple[Any, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_event_bindings(self) -> EpisodeSourceCompilation:
        episode = self.definition.runtime
        events = {
            definition.world_event_ref: definition for definition in self.world_event_definitions
        }
        future_event = events.get(episode.world_event_ref)
        if future_event is None:
            raise ValueError("episode_source_future_world_event_missing")
        if (
            future_event.actor_ref != episode.actor_ref
            or future_event.event_type != self.definition.world_event_type
            or future_event.due_tick != episode.due_tick
            or future_event.event_payload.get("summary") != self.definition.world_event_summary
            or future_event.sealed_outcome != self.definition.sealed_outcome.model_dump(mode="json")
        ):
            raise ValueError("episode_source_future_world_event_mismatch")
        if episode.entrypoint:
            baseline_event = events.get(episode.baseline_event_ref)
            if (
                baseline_event is None
                or baseline_event.actor_ref != episode.actor_ref
                or baseline_event.due_tick != episode.cutoff_tick
            ):
                raise ValueError("episode_source_entry_baseline_event_missing")
        elif episode.baseline_event_ref in events:
            raise ValueError("episode_source_continuation_baseline_is_runtime_committed")
        return self


class EpisodeSourceRegistry:
    """Hash-locked authoring packages used only before Story admission."""

    def __init__(
        self,
        *,
        root: Path,
        expected_registry_hash: str,
    ) -> None:
        self._root = root.resolve()
        registry_payload = self._read_json(self._root / "registry.json")
        registry_hash = content_hash(registry_payload)
        if registry_hash != expected_registry_hash:
            raise EpisodeSourcePackageError("episode_source_registry_hash_mismatch")
        try:
            document = EpisodeSourceRegistryDocument.model_validate(registry_payload)
        except ValueError as exc:
            raise EpisodeSourcePackageError(str(exc)) from exc

        packages: dict[str, tuple[EpisodeSourcePackage, str]] = {}
        for row in document.packages:
            package_path = self._package_path(row.path)
            package_payload = self._read_json(package_path)
            if content_hash(package_payload) != row.package_hash:
                raise EpisodeSourcePackageError(
                    f"episode_source_package_hash_mismatch:{row.package_ref}"
                )
            try:
                package = EpisodeSourcePackage.model_validate(package_payload)
            except ValueError as exc:
                raise EpisodeSourcePackageError(str(exc)) from exc
            if package.package_ref != row.package_ref:
                raise EpisodeSourcePackageError(
                    f"episode_source_package_ref_mismatch:{row.package_ref}"
                )
            packages[row.package_ref] = (package, row.package_hash)

        self._document = document
        self._registry_hash = registry_hash
        self._packages = packages
        self._validate_transitions()

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise EpisodeSourcePackageError(f"episode_source_file_unreadable:{path.name}") from exc
        if not isinstance(payload, dict):
            raise EpisodeSourcePackageError(f"episode_source_file_must_be_object:{path.name}")
        return payload

    def _package_path(self, relative_path: str) -> Path:
        pure_path = PurePosixPath(relative_path)
        if (
            pure_path.is_absolute()
            or len(pure_path.parts) != 1
            or pure_path.suffix != ".json"
            or pure_path.name == "registry.json"
        ):
            raise EpisodeSourcePackageError(f"episode_source_package_path_invalid:{relative_path}")
        package_path = (self._root / relative_path).resolve()
        if package_path.parent != self._root:
            raise EpisodeSourcePackageError(f"episode_source_package_path_escape:{relative_path}")
        return package_path

    def _validate_transitions(self) -> None:
        for transition in self._document.transitions:
            source = self._packages[transition.from_package_ref][0]
            target = self._packages[transition.to_package_ref][0]
            source_runtime = source.definition_template.get("runtime", {})
            target_runtime = target.definition_template.get("runtime", {})
            definition = transition.definition
            authored_next = source_runtime.get("continuation_question_ref")
            authored_label = source_runtime.get("continuation_label")
            if (
                definition.from_question_ref != source_runtime.get("question_ref")
                or definition.to_question_ref != target_runtime.get("question_ref")
                or (authored_next is not None and authored_next != definition.to_question_ref)
                or (authored_label is not None and authored_label != definition.label)
                or target_runtime.get("entrypoint") is not False
            ):
                raise EpisodeSourcePackageError(
                    f"episode_source_transition_binding_mismatch:{definition.transition_ref}"
                )

    def compile_package(
        self,
        package_ref: str,
        *,
        bindings: dict[str, str],
    ) -> EpisodeSourceCompilation:
        try:
            package, expected_hash = self._packages[package_ref]
        except KeyError as exc:
            raise EpisodeSourcePackageError(
                f"episode_source_package_unknown:{package_ref}"
            ) from exc
        if content_hash(package.model_dump(mode="json")) != expected_hash:
            raise EpisodeSourcePackageError(f"episode_source_package_mutated:{package_ref}")

        expected_keys = set(package.binding_keys)
        supplied_keys = set(bindings)
        if supplied_keys != expected_keys:
            missing = ",".join(sorted(expected_keys - supplied_keys))
            extra = ",".join(sorted(supplied_keys - expected_keys))
            raise EpisodeSourcePackageError(
                f"episode_source_bindings_invalid:missing={missing}:extra={extra}"
            )
        if any(not isinstance(value, str) or not value for value in bindings.values()):
            raise EpisodeSourcePackageError("episode_source_binding_value_invalid")

        compiled_payload = _bind_template(package.definition_template, bindings)
        if _binding_markers(compiled_payload):
            raise EpisodeSourcePackageError("episode_source_binding_unresolved")
        try:
            definition = DreamEpisodeDefinition.model_validate(compiled_payload)
        except ValueError as exc:
            raise EpisodeSourcePackageError(str(exc)) from exc
        from abu_v60.world.admission import WorldEventDefinition

        try:
            world_event_definitions = tuple(
                WorldEventDefinition.model_validate(payload)
                for payload in package.world_event_definitions
            )
        except ValueError as exc:
            raise EpisodeSourcePackageError(str(exc)) from exc
        try:
            return EpisodeSourceCompilation(
                package_ref=package.package_ref,
                package_hash=expected_hash,
                definition=definition,
                world_event_definitions=world_event_definitions,
            )
        except ValueError as exc:
            raise EpisodeSourcePackageError(str(exc)) from exc

    def compile_definition(
        self,
        package_ref: str,
        *,
        bindings: dict[str, str],
    ) -> DreamEpisodeDefinition:
        return self.compile_package(
            package_ref,
            bindings=bindings,
        ).definition

    def compile_all(
        self,
        *,
        bindings: dict[str, str],
    ) -> tuple[EpisodeSourceCompilation, ...]:
        return tuple(
            self.compile_package(
                row.package_ref,
                bindings={
                    key: bindings[key]
                    for key in self._packages[row.package_ref][0].binding_keys
                    if key in bindings
                },
            )
            for row in self._document.packages
        )

    def transitions(self) -> tuple[EpisodeTransitionContract, ...]:
        return tuple(transition.definition for transition in self._document.transitions)

    def public_manifest(self) -> dict[str, Any]:
        return {
            "registry_version": self._document.registry_version,
            "registry_hash": self._registry_hash,
            "runtime_access": "ADMISSION_ONLY",
            "packages": [
                {
                    "package_ref": row.package_ref,
                    "package_hash": row.package_hash,
                    "binding_keys": list(self._packages[row.package_ref][0].binding_keys),
                }
                for row in self._document.packages
            ],
            "transitions": [
                {
                    "transition_ref": transition.definition.transition_ref,
                    "transition_hash": content_hash(transition.definition.model_dump(mode="json")),
                    "from_package_ref": transition.from_package_ref,
                    "to_package_ref": transition.to_package_ref,
                }
                for transition in self._document.transitions
            ],
        }


@lru_cache(maxsize=1)
def default_episode_source_registry() -> EpisodeSourceRegistry:
    root = Path(__file__).resolve().parents[4] / "content" / "dream" / "episodes"
    return EpisodeSourceRegistry(
        root=root,
        expected_registry_hash=EPISODE_SOURCE_REGISTRY_HASH,
    )


@lru_cache(maxsize=1)
def qualification_episode_source_registry() -> EpisodeSourceRegistry:
    root = Path(__file__).resolve().parents[4] / "content" / "dream" / "qualification"
    return EpisodeSourceRegistry(
        root=root,
        expected_registry_hash=QUALIFICATION_EPISODE_SOURCE_REGISTRY_HASH,
    )
