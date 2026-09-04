from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import date, datetime
from itertools import combinations
from typing import Any
from zoneinfo import ZoneInfo

from lunar_python import LunarYear
from sqlalchemy import text
from sqlalchemy.engine import Engine

from abu_v60.knowledge import KnowledgeAuthority
from abu_v60.mingli.calendar import BirthInput
from abu_v60.mingli.narration_catalog import voice_profile
from abu_v60.mingli.reading_store import MingliReadingStore
from abu_v60.mingli.service import CaseNotFoundError, MingliCaseService
from abu_v60.mingli.showcases import (
    SHOWCASE_ACCOUNT_REF,
    SHOWCASE_BY_SUBJECT,
)
from abu_v60.mingli.stage_contracts import (
    MingliStageBody,
    MingliStageColumn,
    MingliStageMode,
    MingliStageProjection,
    MingliStageRelationMembership,
)
from abu_v60.mingli.synthetic_experiment_catalog import MingliResearchStageBinding
from abu_v60.mingli.timing import MingliTimingEvidenceCompiler
from abu_v60.mingli.timing_contracts import (
    DAYUN_CALCULATION_POLICY,
)
from abu_v60.provenance import stable_ref
from abu_v60.settings import Settings, settings

NATAL_SLOTS = ("year", "month", "day", "hour")
NATAL_COLUMN_SLOTS = ("NATAL_YEAR", "NATAL_MONTH", "NATAL_DAY", "NATAL_HOUR")
NATAL_LABELS = ("年柱", "月柱", "日柱", "时柱")
NATAL_FACT_SLOT_BY_COLUMN = dict(zip(NATAL_COLUMN_SLOTS, NATAL_SLOTS, strict=True))
PRIVATE_CASE_SUBJECT_PREFIX = "case:"


class MingliStageError(ValueError):
    pass


class MingliStageService:
    def __init__(
        self,
        engine: Engine,
        *,
        cases: MingliCaseService | None = None,
        authority: KnowledgeAuthority | None = None,
        timing: MingliTimingEvidenceCompiler | None = None,
        readings: MingliReadingStore | None = None,
        current_date_provider: Callable[[str], date] | None = None,
        runtime_settings: Settings | None = None,
        research_subject_resolver: Callable[[str], MingliResearchStageBinding | None] | None = None,
    ) -> None:
        self._engine = engine
        self._cases = cases or MingliCaseService(engine)
        self._authority = authority or KnowledgeAuthority()
        self._timing = timing or MingliTimingEvidenceCompiler(self._authority)
        self._readings = readings or MingliReadingStore(engine)
        self._settings = runtime_settings or settings
        self._current_date_provider = current_date_provider or (
            lambda timezone: datetime.now(ZoneInfo(timezone)).date()
        )
        self._research_subject_resolver = research_subject_resolver

    def subjects(self, *, account_ref: str) -> list[dict[str, object]]:
        current = self._owner_workspace(account_ref=account_ref)
        subjects: list[dict[str, object]] = [
            {
                "subject_id": "current",
                "display_name": current["profile"]["display_name"],
                "subject_kind": "HUMAN_OWNER",
                "identity_badge": "私密真实档案",
                "default_narrator_actor_id": "ABU_NARRATOR_V1",
            }
        ]
        current_case_ref = str(current["case"]["case_ref"])
        subjects.extend(
            {
                "subject_id": f"{PRIVATE_CASE_SUBJECT_PREFIX}{item['case_ref']}",
                "display_name": item["display_name"],
                "subject_kind": item["subject_kind"],
                "identity_badge": (
                    "私密真实档案" if item["subject_kind"] == "HUMAN_OWNER" else "真实参考档案"
                ),
                "default_narrator_actor_id": "ABU_NARRATOR_V1",
            }
            for item in self._cases.list_cases(account_ref=account_ref)
            if item["subject_kind"] in {"HUMAN_OWNER", "HUMAN_REFERENCE"}
            and str(item["case_ref"]) != current_case_ref
        )
        subjects.extend(
            {
                "subject_id": item.subject_id,
                "display_name": item.display_name,
                "subject_kind": "CANONICAL_SYNTHETIC",
                "identity_badge": "角色合成设定",
                "default_narrator_actor_id": item.narrator_actor_id,
            }
            for item in SHOWCASE_BY_SUBJECT.values()
        )
        return subjects

    def project(
        self,
        *,
        account_ref: str,
        subject_id: str,
        stage_mode: MingliStageMode,
        selected_year: int | None = None,
        pinned_reading_ref: str | None = None,
        pinned_reading_hash: str | None = None,
    ) -> MingliStageProjection:
        workspace, narrator_actor_id, identity_badge, privacy_scope = self._workspace(
            account_ref=account_ref,
            subject_id=subject_id,
        )
        birth_input = BirthInput.model_validate(workspace["profile"]["birth_input"])
        current_date = self._current_date_provider(birth_input.timezone)
        current_timing = self._compile_timing(
            workspace=workspace,
            birth_input=birth_input,
            analysis_date=current_date,
        )
        current_dayun = current_timing.coordinates[0]
        if (
            current_dayun.start_year is None
            or current_dayun.end_year is None
            or current_dayun.start_date is None
            or current_dayun.end_date is None
        ):
            raise MingliStageError("mingli_stage_current_dayun_bounds_missing")
        available_years = tuple(
            range(current_dayun.start_date.year, current_dayun.end_date.year + 1)
        )

        if stage_mode == MingliStageMode.NATAL_4:
            if selected_year is not None:
                raise MingliStageError("mingli_stage_four_does_not_accept_year")
            annual_pillar = None
        else:
            selected_year = selected_year or current_date.year
            if selected_year not in available_years:
                raise MingliStageError("mingli_stage_year_outside_current_dayun")
            annual_pillar = LunarYear.fromYear(selected_year).getGanZhi()

        columns = self._columns(
            workspace=workspace,
            stage_mode=stage_mode,
            current_dayun=current_dayun,
            selected_year=selected_year,
            annual_pillar=annual_pillar,
        )
        bodies = self._bodies(columns=columns)
        foundation = self._authority.active_foundation_profile()
        relations = self._relations(
            columns=columns,
            facts=workspace["facts"],
            relation_definitions=foundation.relations,
            rule_ref=foundation.source_ref,
            rule_hash=foundation.profile_hash,
        )
        subject_kind = str(workspace["case"]["subject_kind"])
        reading_binding = self._reading_binding(
            case_ref=str(workspace["case"]["case_ref"]),
            chart_version_ref=str(workspace["chart"]["chart_version_ref"]),
            life_case_revision_ref=str(workspace["life_case"]["life_case_revision_ref"]),
            pinned_reading_ref=pinned_reading_ref,
            pinned_reading_hash=pinned_reading_hash,
        )
        timing_profile = self._authority.active_timing_evidence_profile()
        source_refs = {
            foundation.source_ref,
            timing_profile.source_ref,
            str(workspace["chart"]["chart_version_ref"]),
            str(workspace["life_case"]["life_case_revision_ref"]),
            *(relation.rule_ref for relation in relations),
        }
        if reading_binding is not None:
            source_refs.add(str(reading_binding["reading_ref"]))
        configured_speaker = (
            self._settings.tts_duoduo_voice
            if narrator_actor_id == "DUODUO_NARRATOR_V1"
            else self._settings.tts_abu_voice
        )
        narration_voice = voice_profile(
            narrator_actor_id,
            speaker=configured_speaker,
            model=self._settings.tts_model,
        )
        return MingliStageProjection.issue(
            subject_id=subject_id,
            case_ref=str(workspace["case"]["case_ref"]),
            chart_version_ref=str(workspace["chart"]["chart_version_ref"]),
            life_case_revision_ref=str(workspace["life_case"]["life_case_revision_ref"]),
            reading_ref=(
                str(reading_binding["reading_ref"]) if reading_binding is not None else None
            ),
            reading_hash=(
                str(reading_binding["reading_hash"]) if reading_binding is not None else None
            ),
            display_name=str(workspace["profile"]["display_name"]),
            subject_kind=subject_kind,
            identity_badge=identity_badge,
            privacy_scope=privacy_scope,
            stage_mode=stage_mode,
            selected_year=selected_year,
            available_years=available_years,
            current_dayun_label=current_dayun.pillar,
            current_dayun_start_year=current_dayun.start_year,
            current_dayun_end_year=current_dayun.end_year,
            current_dayun_start_date=current_dayun.start_date,
            current_dayun_end_date=current_dayun.end_date,
            dayun_boundary_precision=current_timing.dayun_boundary_precision,
            dayun_calculation_policy=current_timing.dayun_calculation_policy,
            dayun_resolution_status=current_timing.dayun_resolution_status,
            annual_label_semantics="SELECTED_SOLAR_YEAR_GANZHI",
            foundation_profile_ref=foundation.source_ref,
            foundation_profile_hash=foundation.profile_hash,
            timing_profile_ref=timing_profile.source_ref,
            timing_profile_hash=timing_profile.profile_hash,
            columns=columns,
            bodies=bodies,
            relations=relations,
            narrator_actor_id=narrator_actor_id,
            narration_voice_status=narration_voice.status,
            stage_semantics="COORDINATES_AND_MEMBERSHIP_ONLY",
            relation_effect_status="UNRESOLVED",
            usable_source_status="UNRESOLVED",
            professional_verdict_allowed=False,
            forbidden_conclusions=(
                "strength",
                "usable_root",
                "relation_effect",
                "time_activation",
                "probability",
                "auspiciousness",
                "effective_work",
            ),
            source_refs=tuple(sorted(source_refs)),
        )

    def can_access_case(self, *, account_ref: str, case_ref: str) -> bool:
        if any(item.case_ref == case_ref for item in SHOWCASE_BY_SUBJECT.values()):
            return True
        with self._engine.connect() as connection:
            return bool(
                connection.execute(
                    text(
                        """
                        SELECT EXISTS (
                            SELECT 1 FROM mingli.cases
                            WHERE case_ref = :case_ref
                              AND owner_account_ref = :account_ref
                              AND subject_kind IN ('HUMAN_OWNER', 'HUMAN_REFERENCE')
                        )
                        """
                    ),
                    {"case_ref": case_ref, "account_ref": account_ref},
                ).scalar_one()
            )

    def _workspace(
        self,
        *,
        account_ref: str,
        subject_id: str,
    ) -> tuple[dict[str, Any], str, str, str]:
        if subject_id == "current":
            return (
                self._owner_workspace(account_ref=account_ref),
                "ABU_NARRATOR_V1",
                "私密真实档案",
                "PRIVATE_OWNER",
            )
        if subject_id.startswith(PRIVATE_CASE_SUBJECT_PREFIX):
            case_ref = subject_id.removeprefix(PRIVATE_CASE_SUBJECT_PREFIX)
            if not case_ref:
                raise MingliStageError("mingli_stage_subject_not_found")
            try:
                workspace = self._cases.workspace(
                    account_ref=account_ref,
                    case_ref=case_ref,
                )
            except CaseNotFoundError as exc:
                raise MingliStageError("mingli_stage_subject_not_found") from exc
            if workspace["case"]["subject_kind"] not in {
                "HUMAN_OWNER",
                "HUMAN_REFERENCE",
            }:
                raise MingliStageError("mingli_stage_private_case_kind_mismatch")
            subject_kind = str(workspace["case"]["subject_kind"])
            return (
                workspace,
                "ABU_NARRATOR_V1",
                "私密真实档案" if subject_kind == "HUMAN_OWNER" else "真实参考档案",
                "PRIVATE_OWNER" if subject_kind == "HUMAN_OWNER" else "PRIVATE_REFERENCE",
            )
        research_binding = (
            self._research_subject_resolver(subject_id)
            if self._research_subject_resolver is not None
            else None
        )
        if research_binding is not None:
            try:
                workspace = self._cases.workspace(
                    account_ref=research_binding.account_ref,
                    case_ref=research_binding.case_ref,
                )
            except CaseNotFoundError as exc:
                raise MingliStageError("mingli_stage_research_case_not_seeded") from exc
            if workspace["case"]["subject_kind"] != "CANONICAL_SYNTHETIC":
                raise MingliStageError("mingli_stage_research_case_kind_mismatch")
            return (
                workspace,
                research_binding.narrator_actor_id,
                research_binding.identity_badge,
                research_binding.privacy_scope,
            )
        definition = SHOWCASE_BY_SUBJECT.get(subject_id)
        if definition is None:
            raise MingliStageError("mingli_stage_subject_not_found")
        try:
            workspace = self._cases.workspace(
                account_ref=SHOWCASE_ACCOUNT_REF,
                case_ref=definition.case_ref,
            )
        except CaseNotFoundError as exc:
            raise MingliStageError("mingli_stage_showcase_not_seeded") from exc
        if workspace["case"]["subject_kind"] != "CANONICAL_SYNTHETIC":
            raise MingliStageError("mingli_stage_showcase_kind_mismatch")
        return (
            workspace,
            definition.narrator_actor_id,
            "角色合成设定",
            "PUBLIC_SYNTHETIC_SHOWCASE",
        )

    def _owner_workspace(self, *, account_ref: str) -> dict[str, Any]:
        cases = [
            item
            for item in self._cases.list_cases(account_ref=account_ref)
            if item["subject_kind"] == "HUMAN_OWNER" and item["status"] == "ACTIVE"
        ]
        if len(cases) != 1:
            raise MingliStageError("mingli_stage_owner_case_selection_required")
        return self._cases.workspace(
            account_ref=account_ref,
            case_ref=str(cases[0]["case_ref"]),
        )

    def _compile_timing(
        self,
        *,
        workspace: Mapping[str, Any],
        birth_input: BirthInput,
        analysis_date: date,
    ) -> Any:
        try:
            return self._timing.compile(
                case_ref=str(workspace["case"]["case_ref"]),
                chart_version_ref=str(workspace["chart"]["chart_version_ref"]),
                life_case_revision_ref=str(workspace["life_case"]["life_case_revision_ref"]),
                birth_input=birth_input,
                gender=str(workspace["profile"]["gender"]),
                pillars=workspace["chart"]["pillars"],
                facts=workspace["facts"],
                analysis_date=analysis_date,
            )
        except ValueError as exc:
            if str(exc) == "timing_vector_dayun_boundary_unresolved":
                raise MingliStageError("mingli_stage_dayun_boundary_unresolved") from exc
            raise

    @staticmethod
    def _columns(
        *,
        workspace: Mapping[str, Any],
        stage_mode: MingliStageMode,
        current_dayun: Any,
        selected_year: int | None,
        annual_pillar: str | None,
    ) -> tuple[MingliStageColumn, ...]:
        columns: list[MingliStageColumn] = []
        chart_ref = str(workspace["chart"]["chart_version_ref"])
        pillars = workspace["chart"]["pillars"]
        for slot, column_slot, label in zip(
            NATAL_SLOTS,
            NATAL_COLUMN_SLOTS,
            NATAL_LABELS,
            strict=True,
        ):
            pillar = str(pillars[slot])
            coordinate_ref = stable_ref(
                "v60-mingli-natal-coordinate",
                {"chart_version_ref": chart_ref, "slot": slot, "pillar": pillar},
            )
            columns.append(
                MingliStageColumn(
                    column_ref=stable_ref(
                        "v60-mingli-stage-column",
                        {"coordinate_ref": coordinate_ref, "slot": column_slot},
                    ),
                    slot=column_slot,
                    label=label,
                    source_layer="NATAL",
                    pillar=pillar,
                    stem=pillar[0],
                    branch=pillar[1],
                    coordinate_ref=coordinate_ref,
                    calculation_status="DETERMINISTIC_COORDINATE",
                )
            )
        if stage_mode == MingliStageMode.NATAL_DAYUN_YEAR_6:
            if selected_year is None or annual_pillar is None:
                raise MingliStageError("mingli_stage_six_timing_missing")
            temporal_coordinates = (
                (
                    "DAYUN",
                    "大运",
                    current_dayun.pillar,
                    current_dayun.start_year,
                    current_dayun.end_year,
                    current_dayun.start_date,
                    current_dayun.end_date,
                    stable_ref(
                        "v60-mingli-stage-dayun-coordinate",
                        {
                            "case_ref": workspace["case"]["case_ref"],
                            "chart_version_ref": chart_ref,
                            "pillar": current_dayun.pillar,
                            "start_year": current_dayun.start_year,
                            "end_year": current_dayun.end_year,
                            "start_date": current_dayun.start_date.isoformat(),
                            "end_date": current_dayun.end_date.isoformat(),
                            "policy": DAYUN_CALCULATION_POLICY,
                        },
                    ),
                ),
                (
                    "ANNUAL",
                    "流年",
                    annual_pillar,
                    None,
                    None,
                    None,
                    None,
                    stable_ref(
                        "v60-mingli-stage-annual-coordinate",
                        {
                            "selected_year": selected_year,
                            "pillar": annual_pillar,
                            "semantics": "SELECTED_SOLAR_YEAR_GANZHI",
                        },
                    ),
                ),
            )
            for (
                column_slot,
                label,
                pillar,
                start_year,
                end_year,
                start_date,
                end_date,
                coordinate_ref,
            ) in temporal_coordinates:
                columns.append(
                    MingliStageColumn(
                        column_ref=stable_ref(
                            "v60-mingli-stage-column",
                            {
                                "coordinate_ref": coordinate_ref,
                                "slot": column_slot,
                            },
                        ),
                        slot=column_slot,
                        label=label,
                        source_layer=column_slot,
                        pillar=pillar,
                        stem=pillar[0],
                        branch=pillar[1],
                        coordinate_ref=coordinate_ref,
                        start_year=start_year,
                        end_year=end_year,
                        start_date=start_date,
                        end_date=end_date,
                        calculation_status="DETERMINISTIC_COORDINATE",
                    )
                )
        return tuple(columns)

    @staticmethod
    def _bodies(*, columns: Sequence[MingliStageColumn]) -> tuple[MingliStageBody, ...]:
        bodies: list[MingliStageBody] = []
        for column_index, column in enumerate(columns):
            for role_index, (role, glyph) in enumerate(
                (("STEM", column.stem), ("BRANCH", column.branch))
            ):
                order = column_index * 2 + role_index
                bodies.append(
                    MingliStageBody(
                        body_ref=stable_ref(
                            "v60-mingli-stage-body",
                            {
                                "column_ref": column.column_ref,
                                "role": role,
                                "glyph": glyph,
                            },
                        ),
                        column_ref=column.column_ref,
                        role=role,
                        glyph=glyph,
                        order=order,
                    )
                )
        return tuple(bodies)

    @staticmethod
    def _relations(
        *,
        columns: Sequence[MingliStageColumn],
        facts: Sequence[Mapping[str, Any]],
        relation_definitions: Sequence[Any],
        rule_ref: str,
        rule_hash: str,
    ) -> tuple[MingliStageRelationMembership, ...]:
        relation_lookup = {
            frozenset((item.left_branch, item.right_branch)): item.relation_type
            for item in relation_definitions
        }
        results: list[MingliStageRelationMembership] = []
        for left, right in combinations(columns, 2):
            relation_type = relation_lookup.get(frozenset((left.branch, right.branch)))
            if relation_type is None:
                continue
            matching_fact_refs = MingliStageService._matching_natal_fact_refs(
                left=left,
                right=right,
                facts=facts,
                relation_type=relation_type,
            )
            evidence_refs = tuple(
                dict.fromkeys(
                    (
                        left.coordinate_ref,
                        right.coordinate_ref,
                        *matching_fact_refs,
                    )
                )
            )
            identity = {
                "left_column_ref": left.column_ref,
                "right_column_ref": right.column_ref,
                "left_branch": left.branch,
                "right_branch": right.branch,
                "relation_type": relation_type,
                "rule_ref": rule_ref,
                "evidence_refs": evidence_refs,
            }
            results.append(
                MingliStageRelationMembership(
                    relation_ref=stable_ref("v60-mingli-stage-relation", identity),
                    relation_type=relation_type,
                    label="六冲成员关系"
                    if relation_type == "six_clash_membership"
                    else "六合成员关系",
                    left_column_ref=left.column_ref,
                    right_column_ref=right.column_ref,
                    left_branch=left.branch,
                    right_branch=right.branch,
                    evidence_refs=evidence_refs,
                    rule_ref=rule_ref,
                    rule_hash=rule_hash,
                    relation_status="MEMBERSHIP_PRESENT",
                    effect_status="UNRESOLVED",
                    usable_source_status="UNRESOLVED",
                )
            )
        return tuple(results)

    @staticmethod
    def _matching_natal_fact_refs(
        *,
        left: MingliStageColumn,
        right: MingliStageColumn,
        facts: Sequence[Mapping[str, Any]],
        relation_type: str,
    ) -> tuple[str, ...]:
        """Bind compiled natal facts only to their exact two source columns."""

        if left.source_layer != "NATAL" or right.source_layer != "NATAL":
            return ()
        left_slot = NATAL_FACT_SLOT_BY_COLUMN.get(left.slot)
        right_slot = NATAL_FACT_SLOT_BY_COLUMN.get(right.slot)
        if left_slot is None or right_slot is None:
            return ()

        matching_refs: set[str] = set()
        for fact in facts:
            if fact.get("fact_type") != relation_type:
                continue
            payload = fact.get("fact_json")
            if not isinstance(payload, Mapping):
                continue
            direct_match = (
                payload.get("left_slot") == left_slot
                and payload.get("left_branch") == left.branch
                and payload.get("right_slot") == right_slot
                and payload.get("right_branch") == right.branch
            )
            reverse_match = (
                payload.get("left_slot") == right_slot
                and payload.get("left_branch") == right.branch
                and payload.get("right_slot") == left_slot
                and payload.get("right_branch") == left.branch
            )
            fact_ref = fact.get("fact_ref")
            if (direct_match or reverse_match) and isinstance(fact_ref, str) and fact_ref:
                matching_refs.add(fact_ref)
        return tuple(sorted(matching_refs))

    def _reading_binding(
        self,
        *,
        case_ref: str,
        chart_version_ref: str,
        life_case_revision_ref: str,
        pinned_reading_ref: str | None,
        pinned_reading_hash: str | None,
    ) -> Mapping[str, Any] | None:
        if (pinned_reading_ref is None) != (pinned_reading_hash is None):
            raise MingliStageError("mingli_stage_pinned_reading_binding_incomplete")
        if pinned_reading_ref is not None:
            reading = self._readings.get(reading_ref=pinned_reading_ref)
            if (
                reading.case_ref != case_ref
                or reading.chart_version_ref != chart_version_ref
                or reading.life_case_revision_ref != life_case_revision_ref
                or reading.reading_hash != pinned_reading_hash
            ):
                raise MingliStageError("mingli_stage_pinned_reading_lineage_conflict")
            return {
                "reading_ref": reading.reading_ref,
                "reading_hash": reading.reading_hash,
            }
        with self._engine.connect() as connection:
            reading_ref = connection.execute(
                text(
                    """
                    SELECT reading_ref
                    FROM mingli.readings
                    WHERE case_ref = :case_ref
                      AND chart_version_ref = :chart_version_ref
                      AND life_case_revision_ref = :life_case_revision_ref
                    ORDER BY created_at DESC, reading_ref DESC
                    LIMIT 1
                    """
                ),
                {
                    "case_ref": case_ref,
                    "chart_version_ref": chart_version_ref,
                    "life_case_revision_ref": life_case_revision_ref,
                },
            ).scalar_one_or_none()
        if reading_ref is None:
            return None
        reading = self._readings.get(reading_ref=str(reading_ref))
        return {
            "reading_ref": reading.reading_ref,
            "reading_hash": reading.reading_hash,
        }
