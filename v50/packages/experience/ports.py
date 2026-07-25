from __future__ import annotations

from typing import Protocol

from experience.contracts import MingliExperienceEnvelope


class MingliExperienceEnvelopePort(Protocol):
    """The only cognitive input accepted by the Experience Runtime."""

    def issue_envelope(
        self,
        *,
        participant_id: str,
        topic_id: str,
        topic_version: str,
        disclosure_level: str,
        case_id: str | None = None,
    ) -> MingliExperienceEnvelope: ...
