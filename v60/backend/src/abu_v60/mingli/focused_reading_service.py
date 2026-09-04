from __future__ import annotations

from threading import Lock

from sqlalchemy.engine import Engine

from abu_v60.mingli.agent_service import MingliAgentService, MingliAgentServiceError
from abu_v60.mingli.focused_reading_contracts import MingliFocusedReadingEnvelope
from abu_v60.mingli.focused_reading_runtime import (
    MINGLI_FOCUSED_PROMPT_HASH,
    MingliFocusedRuntime,
    MingliFocusedRuntimeError,
    configured_mingli_focused_runtime,
)
from abu_v60.mingli.focused_reading_store import MingliFocusedReadingStore
from abu_v60.provenance import content_hash

MINGLI_FOCUSED_REQUEST_VERSION = "v60.mingli-focused-request.001"


class MingliFocusedReadingServiceError(ValueError):
    pass


class MingliFocusedReadingService:
    """Generate several narrow prose readings from one immutable fact packet."""

    def __init__(
        self,
        engine: Engine,
        *,
        runtime: MingliFocusedRuntime | None = None,
        store: MingliFocusedReadingStore | None = None,
        packet_service: MingliAgentService | None = None,
    ) -> None:
        self._runtime = runtime or configured_mingli_focused_runtime()
        self._store = store or MingliFocusedReadingStore(engine)
        self._packets = packet_service or MingliAgentService(engine)
        self._generation_lock = Lock()

    def generate(
        self,
        *,
        requester_account_ref: str,
        case_ref: str,
        expected_reading_ref: str,
        expected_reading_hash: str,
    ) -> MingliFocusedReadingEnvelope:
        try:
            packet = self._packets.compile_packet(
                requester_account_ref=requester_account_ref,
                case_ref=case_ref,
                expected_reading_ref=expected_reading_ref,
                expected_reading_hash=expected_reading_hash,
            )
        except MingliAgentServiceError as exc:
            raise MingliFocusedReadingServiceError(str(exc)) from exc
        try:
            provider = self._runtime.required_provider()
        except MingliFocusedRuntimeError as exc:
            raise MingliFocusedReadingServiceError(str(exc)) from exc
        generation_key = content_hash(
            {
                "requester_account_ref": requester_account_ref,
                "reading_ref": packet.reading_ref,
                "reading_hash": packet.reading_hash,
                "packet_ref": packet.packet_ref,
                "packet_hash": packet.packet_hash,
                "provider_profile_ref": provider.provider_profile_ref,
                "provider_profile_hash": provider.provider_profile_hash,
                "prompt_hash": MINGLI_FOCUSED_PROMPT_HASH,
            }
        )
        cached = self._store.find_generation(
            requester_account_ref=requester_account_ref,
            generation_key=generation_key,
        )
        if cached is not None:
            return cached
        with self._generation_lock:
            cached = self._store.find_generation(
                requester_account_ref=requester_account_ref,
                generation_key=generation_key,
            )
            if cached is not None:
                return cached
            try:
                passes = provider.generate(packet=packet)
            except MingliFocusedRuntimeError as exc:
                raise MingliFocusedReadingServiceError(str(exc)) from exc
            reading = MingliFocusedReadingEnvelope.issue(
                generation_key=generation_key,
                requester_account_ref=requester_account_ref,
                case_ref=packet.case_ref,
                chart_version_ref=packet.chart_version_ref,
                life_case_revision_ref=packet.life_case_revision_ref,
                reading_ref=packet.reading_ref,
                reading_hash=packet.reading_hash,
                packet_ref=packet.packet_ref,
                packet_hash=packet.packet_hash,
                provider_id=provider.provider_id,
                model_ref=provider.model_ref,
                model_digest=provider.model_digest,
                provider_profile_ref=provider.provider_profile_ref,
                provider_profile_hash=provider.provider_profile_hash,
                prompt_hash=MINGLI_FOCUSED_PROMPT_HASH,
                passes=passes,
            )
            return self._store.ensure(reading)
