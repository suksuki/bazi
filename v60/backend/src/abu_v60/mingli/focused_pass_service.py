from __future__ import annotations

from threading import Lock

from sqlalchemy.engine import Engine

from abu_v60.mingli.agent_service import MingliAgentService, MingliAgentServiceError
from abu_v60.mingli.focused_pass_store import MingliFocusedPassStore
from abu_v60.mingli.focused_reading_contracts import (
    MingliFocus,
    MingliFocusedPassRecord,
)
from abu_v60.mingli.focused_reading_runtime import (
    MINGLI_FOCUSED_PROMPT_HASH,
    MingliFocusedRuntime,
    MingliFocusedRuntimeError,
    configured_mingli_focused_runtime,
)
from abu_v60.provenance import content_hash

MINGLI_FOCUSED_PASS_REQUEST_VERSION = "v60.mingli-focused-pass-request.001"


class MingliFocusedPassServiceError(ValueError):
    pass


class MingliFocusedPassService:
    """Generate only the requested layer; structure is the sole dependency."""

    def __init__(
        self,
        engine: Engine,
        *,
        runtime: MingliFocusedRuntime | None = None,
        store: MingliFocusedPassStore | None = None,
        packet_service: MingliAgentService | None = None,
    ) -> None:
        self._runtime = runtime or configured_mingli_focused_runtime()
        self._store = store or MingliFocusedPassStore(engine)
        self._packets = packet_service or MingliAgentService(engine)
        self._generation_lock = Lock()

    def generate(
        self,
        *,
        requester_account_ref: str,
        case_ref: str,
        expected_reading_ref: str,
        expected_reading_hash: str,
        focus: MingliFocus,
    ) -> MingliFocusedPassRecord:
        try:
            packet = self._packets.compile_packet(
                requester_account_ref=requester_account_ref,
                case_ref=case_ref,
                expected_reading_ref=expected_reading_ref,
                expected_reading_hash=expected_reading_hash,
            )
        except MingliAgentServiceError as exc:
            raise MingliFocusedPassServiceError(str(exc)) from exc
        try:
            provider = self._runtime.required_provider()
        except MingliFocusedRuntimeError as exc:
            raise MingliFocusedPassServiceError(str(exc)) from exc

        structure = None
        if focus != "STRUCTURE":
            structure = self._store.latest(
                requester_account_ref=requester_account_ref,
                case_ref=case_ref,
                reading_ref=packet.reading_ref,
                reading_hash=packet.reading_hash,
                provider_profile_hash=provider.provider_profile_hash,
                prompt_hash=MINGLI_FOCUSED_PROMPT_HASH,
                focus="STRUCTURE",
            )
            if structure is None:
                raise MingliFocusedPassServiceError("mingli_focused_structure_required")
        structure_hash = None if structure is None else structure.pass_result.pass_hash
        generation_key = content_hash(
            {
                "requester_account_ref": requester_account_ref,
                "reading_ref": packet.reading_ref,
                "reading_hash": packet.reading_hash,
                "packet_ref": packet.packet_ref,
                "packet_hash": packet.packet_hash,
                "focus": focus,
                "structure_pass_hash": structure_hash,
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
                result = provider.generate_focus(
                    packet=packet,
                    focus=focus,
                    structure_text=(
                        None if structure is None else structure.pass_result.normalized_text
                    ),
                )
            except MingliFocusedRuntimeError as exc:
                raise MingliFocusedPassServiceError(str(exc)) from exc
            record = MingliFocusedPassRecord.issue(
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
                focus=focus,
                structure_pass_hash=structure_hash,
                pass_result=result,
            )
            return self._store.ensure(record)
