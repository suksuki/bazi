from __future__ import annotations

from product.agent_case_store import AgentCaseStore
from product.canonical_scene import CanonicalSceneOwner
from experience.contracts import MingliExperienceEnvelope


class ProductExperienceEnvelopePort:
    """Compatibility adapter from Canonical Scene to the Theater envelope.

    Callers: theater_api and experience_api. Retire when both consume the
    canonical projection envelope directly, no later than Workspace canonical
    projection migration.
    """

    def __init__(
        self,
        *,
        case_store: AgentCaseStore | None = None,
        scene_owner: CanonicalSceneOwner | None = None,
    ) -> None:
        if scene_owner is not None:
            self._scene_owner = scene_owner
        elif case_store is not None:
            self._scene_owner = CanonicalSceneOwner(case_store=case_store)
        else:
            raise ValueError("canonical_scene_owner_or_case_store_required")

    def issue_envelope(
        self,
        *,
        participant_id: str,
        topic_id: str,
        topic_version: str,
        disclosure_level: str,
        case_id: str | None = None,
        permitted_capabilities: list[str] | None = None,
        account_role: str = "member",
    ) -> MingliExperienceEnvelope:
        return self._scene_owner.issue_experience_envelope(
            participant_id=participant_id,
            topic_id=topic_id,
            topic_version=topic_version,
            disclosure_level=disclosure_level,
            case_id=case_id,
            permitted_capabilities=permitted_capabilities,
            account_role=account_role,
        )
