from __future__ import annotations

import hashlib
from typing import Any

from core.engines import BirthCalendarResolutionError, resolve_birth_input_pillars
from core.mingli_agent import ChartWorldInstance, compile_chart_world
from experience.product_projection import (
    ExperienceCaseSummary,
    ExperienceWorkspaceBootstrapResponse,
    WorkspaceAccountSummary,
    WorkspaceCognitionState,
)
from experience.workspace import (
    CaseWorkspaceState,
    build_case_workspace_state,
    compile_case_workspace,
)
from product.agent_case_store import AgentCaseStore
from product.canonical_scene import CanonicalSceneOwner, CanonicalSceneUnavailable
from product.product_store import ProductStore, birth_input_from_profile
from product.theater_envelope import ProductExperienceEnvelopePort


class WorkspaceBootstrapError(ValueError):
    pass


class WorkspaceBootstrapService:
    """Compose one product entry response without invoking cognition or TTS."""

    def __init__(self, *, product_store: ProductStore, case_store: AgentCaseStore) -> None:
        self.product_store = product_store
        self.case_store = case_store
        self.scene_owner = CanonicalSceneOwner(case_store=case_store)
        self.envelope_port = ProductExperienceEnvelopePort(scene_owner=self.scene_owner)

    def issue(
        self,
        *,
        account: dict[str, object],
        requested_profile_id: str = "",
        requested_case_id: str = "",
    ) -> ExperienceWorkspaceBootstrapResponse:
        user_id = str(account["user_id"])
        role = str(account.get("account_role") or account.get("role") or "member")
        profiles = self.product_store.list_profiles(user_id=user_id)
        rows = self.case_store.list_for_user(user_id=user_id)
        rows_by_profile = self._current_rows_by_profile(rows=rows, profiles=profiles)

        if not profiles:
            return ExperienceWorkspaceBootstrapResponse(
                status="workspace_profile_required",
                account=WorkspaceAccountSummary(
                    display_name=str(account.get("display_name") or ""),
                    role=role,
                ),
                cases=[],
                cognition=WorkspaceCognitionState(
                    status="chart_ready",
                    message="先建立一份出生档案，四柱确认后会直接进入命局。",
                    cache_hit=False,
                    background_start_allowed=False,
                ),
            )

        selected_profile = self._select_profile(
            user_id=user_id,
            profiles=profiles,
            rows=rows,
            requested_profile_id=requested_profile_id,
            requested_case_id=requested_case_id,
        )
        profile_id = str(selected_profile["profile_id"])
        selected_row = self._select_row(
            rows=rows_by_profile.get(profile_id, []),
            requested_case_id=requested_case_id,
        )
        if selected_row is None:
            selected_row = self._create_chart_case(
                user_id=user_id,
                profile=selected_profile,
                role=role,
            )
            rows_by_profile.setdefault(profile_id, []).insert(0, selected_row)

        case_id = str(selected_row["case_id"])
        cases = [
            self._case_summary(
                profile=profile,
                row=self._preferred_row(rows_by_profile.get(str(profile["profile_id"]), [])),
                user_id=user_id,
            )
            for profile in profiles
        ]
        cognition = self._cognition_state(selected_row)
        envelope = self.envelope_port.issue_envelope(
            participant_id=user_id,
            topic_id="whole-chart-baseline",
            topic_version="workspace-bootstrap-v1",
            disclosure_level="approved_insights",
            case_id=case_id,
            permitted_capabilities=[
                "narrated_workspace",
                "four_pillar_stage",
                "reasoning_path_stage",
            ],
            account_role=role,
        )
        workspace = self._workspace(
            row=selected_row,
            case_id=case_id,
            participant_id=user_id,
            role=role,
        )
        return ExperienceWorkspaceBootstrapResponse(
            status="workspace_bootstrap_ready",
            account=WorkspaceAccountSummary(
                display_name=str(account.get("display_name") or ""),
                role=role,
            ),
            cases=cases,
            selected_case_id=case_id,
            selected_profile_id=profile_id,
            envelope=envelope,
            workspace=workspace,
            cognition=cognition,
        )

    def _create_chart_case(
        self,
        *,
        user_id: str,
        profile: dict[str, object],
        role: str,
    ) -> dict[str, Any]:
        profile_id = str(profile["profile_id"])
        case_id = _workspace_case_id(user_id=user_id, profile=profile)
        existing = self.case_store.get(case_id=case_id, user_id=user_id)
        if existing is not None:
            return existing
        birth_input = birth_input_from_profile(profile)
        try:
            birth_input = resolve_birth_input_pillars(birth_input)
        except BirthCalendarResolutionError as exc:
            raise WorkspaceBootstrapError(str(exc)) from exc
        if not all((
            birth_input.year_pillar,
            birth_input.month_pillar,
            birth_input.day_pillar,
            birth_input.hour_pillar,
        )):
            raise WorkspaceBootstrapError("four_pillars_resolution_failed")
        reading_id = f"workspace-reading-{case_id.rsplit('-', 1)[-1]}"
        world = compile_chart_world(reading_id=reading_id, birth_input=birth_input)
        row: dict[str, Any] = {
            "case_id": case_id,
            "profile_id": profile_id,
            "profile_fingerprint": str(profile.get("profile_fingerprint") or ""),
            "birth_input": birth_input.model_dump(mode="json"),
            "world": world.model_dump(mode="json"),
            "workspace_state": build_case_workspace_state(
                case_id=case_id,
                active_mode=_workspace_role(role),
            ).model_dump(mode="json"),
            "life_case": None,
            "background_cognition": {
                "status": "not_started",
                "attempt_count": 0,
                "job_id": "",
                "reason": "valid_baseline_missing",
            },
            "status": "chart_ready",
            "entry_protocol": "flow_slim_workspace_bootstrap_v1",
        }
        self.case_store.save(
            case_id=case_id,
            user_id=user_id,
            profile_id=profile_id,
            payload=row,
        )
        return row

    def _workspace(
        self,
        *,
        row: dict[str, Any],
        case_id: str,
        participant_id: str,
        role: str,
    ):
        if not _active_life_case(row):
            return None
        try:
            projection = self.scene_owner.issue_projection(
                case_id=case_id,
                participant_id=participant_id,
                account_role=role,
                projection_kind="workspace",
            )
            raw_state = row.get("workspace_state")
            state = (
                CaseWorkspaceState.model_validate(raw_state)
                if isinstance(raw_state, dict)
                else build_case_workspace_state(case_id=case_id, active_mode=_workspace_role(role))
            )
            return compile_case_workspace(state=state, projection=projection)
        except (CanonicalSceneUnavailable, ValueError):
            return None

    def _select_profile(
        self,
        *,
        user_id: str,
        profiles: list[dict[str, object]],
        rows: list[dict[str, Any]],
        requested_profile_id: str,
        requested_case_id: str,
    ) -> dict[str, object]:
        if requested_case_id:
            row = next(
                (item for item in rows if str(item.get("case_id") or "") == requested_case_id),
                None,
            )
            if row is not None:
                requested_profile_id = str(row.get("profile_id") or "")
            else:
                profile = next(
                    (
                        item
                        for item in profiles
                        if _workspace_case_id(user_id=user_id, profile=item)
                        == requested_case_id
                    ),
                    None,
                )
                if profile is None:
                    raise WorkspaceBootstrapError("workspace_case_not_found")
                return profile
        if requested_profile_id:
            profile = next(
                (item for item in profiles if str(item.get("profile_id") or "") == requested_profile_id),
                None,
            )
            if profile is None:
                raise WorkspaceBootstrapError("workspace_profile_not_found")
            return profile
        return profiles[0]

    def _select_row(
        self,
        *,
        rows: list[dict[str, Any]],
        requested_case_id: str,
    ) -> dict[str, Any] | None:
        if requested_case_id:
            return next(
                (item for item in rows if str(item.get("case_id") or "") == requested_case_id),
                None,
            )
        return self._preferred_row(rows)

    @staticmethod
    def _preferred_row(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not rows:
            return None
        committed = next((item for item in rows if _active_life_case(item)), None)
        if committed is not None:
            return committed
        preparing = next(
            (
                item
                for item in rows
                if str((item.get("background_cognition") or {}).get("status") or "")
                in {"queued", "running"}
            ),
            None,
        )
        return preparing or rows[0]

    def _current_rows_by_profile(
        self,
        *,
        rows: list[dict[str, Any]],
        profiles: list[dict[str, object]],
    ) -> dict[str, list[dict[str, Any]]]:
        profiles_by_id = {str(item["profile_id"]): item for item in profiles}
        output: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            profile_id = str(row.get("profile_id") or "")
            profile = profiles_by_id.get(profile_id)
            if profile is None or not _row_is_current(row):
                continue
            if not _row_matches_profile(row=row, profile=profile):
                continue
            output.setdefault(profile_id, []).append(row)
        return output

    def _case_summary(
        self,
        *,
        profile: dict[str, object],
        row: dict[str, Any] | None,
        user_id: str,
    ) -> ExperienceCaseSummary:
        case_id = str(row.get("case_id") or "") if row else _workspace_case_id(
            user_id=user_id,
            profile=profile,
        )
        cognition = self._cognition_state(row) if row else WorkspaceCognitionState(
            status="chart_ready",
            message="四柱可以立即打开；整盘主线尚未生成。",
            cache_hit=False,
            background_start_allowed=True,
        )
        life_case = row.get("life_case") if isinstance(row, dict) else None
        return ExperienceCaseSummary(
            case_id=case_id,
            profile_id=str(profile["profile_id"]),
            display_name=str(profile.get("display_name") or "当前命盘"),
            case_version=(
                str(life_case.get("case_version") or "")
                if isinstance(life_case, dict)
                else ""
            ),
            status=cognition.status,
            baseline_available=cognition.status == "ready",
            chart_ready=bool(profile.get("pillars")),
            cognition_status=cognition.status,
            experience_url=f"/experience?profile={profile['profile_id']}",
        )

    @staticmethod
    def _cognition_state(row: dict[str, Any] | None) -> WorkspaceCognitionState:
        if row is None:
            return WorkspaceCognitionState(
                status="chart_ready",
                message="四柱可以立即打开；整盘主线尚未生成。",
                cache_hit=False,
                background_start_allowed=True,
            )
        if _active_life_case(row):
            return WorkspaceCognitionState(
                status="ready",
                message="已复用这份档案的正式整盘认知。",
                cache_hit=True,
                background_start_allowed=False,
            )
        background = row.get("background_cognition")
        background = background if isinstance(background, dict) else {}
        status = str(background.get("status") or "")
        job_id = str(background.get("job_id") or "")
        if status in {"queued", "running"}:
            return WorkspaceCognitionState(
                status="preparing",
                message="四柱已经就绪，阿布正在梳理整盘主线。",
                cache_hit=False,
                background_start_allowed=False,
                background_job_id=job_id,
            )
        if row.get("record") or status in {"completed_partial", "failed"}:
            return WorkspaceCognitionState(
                status="partial",
                message="命盘已经就绪；阿布只保留依据充分的部分。",
                cache_hit=False,
                background_start_allowed=False,
                background_job_id=job_id,
            )
        return WorkspaceCognitionState(
            status="chart_ready",
            message="四柱已经就绪，阿布会继续梳理整盘主线。",
            cache_hit=False,
            background_start_allowed=int(background.get("attempt_count") or 0) == 0,
            background_job_id=job_id,
        )


def _workspace_case_id(*, user_id: str, profile: dict[str, object]) -> str:
    fingerprint = str(profile.get("profile_fingerprint") or profile.get("profile_id") or "")
    digest = hashlib.sha256(
        f"flow-slim-v1|{user_id}|{profile['profile_id']}|{fingerprint}".encode("utf-8")
    ).hexdigest()[:20]
    return f"mingli-case-{digest}"


def _workspace_role(value: str) -> str:
    return {
        "admin": "research",
        "research_master": "research",
        "research": "research",
        "practitioner": "practitioner",
    }.get(str(value).strip().lower(), "member")


def _row_is_current(row: dict[str, Any]) -> bool:
    if str(row.get("status") or "") in {"superseded", "archived"}:
        return False
    life_case = row.get("life_case")
    if not isinstance(life_case, dict):
        return True
    chart_version = life_case.get("chart_version")
    return bool(
        life_case.get("status") == "active"
        and isinstance(chart_version, dict)
        and chart_version.get("active") is True
    )


def _active_life_case(row: dict[str, Any]) -> bool:
    life_case = row.get("life_case")
    if not isinstance(life_case, dict):
        return False
    baseline = life_case.get("baseline_insight")
    chart_version = life_case.get("chart_version")
    return bool(
        life_case.get("status") == "active"
        and isinstance(chart_version, dict)
        and chart_version.get("active") is True
        and isinstance(baseline, dict)
        and baseline.get("status") == "committed"
    )


def _row_matches_profile(*, row: dict[str, Any], profile: dict[str, object]) -> bool:
    stored_fingerprint = str(row.get("profile_fingerprint") or "")
    profile_fingerprint = str(profile.get("profile_fingerprint") or "")
    if stored_fingerprint:
        return stored_fingerprint == profile_fingerprint
    birth = row.get("birth_input")
    if not isinstance(birth, dict):
        return False
    return all(
        str(birth.get(key) or "") == str(profile.get(key) or "")
        for key in ("birth_date", "birth_time", "timezone", "calendar_type", "gender")
    )


__all__ = ["WorkspaceBootstrapError", "WorkspaceBootstrapService"]
