from __future__ import annotations

from threading import Lock

from sqlalchemy.engine import Engine

from abu_v60.mingli.agent_contracts import MingliAgentReadingEnvelope
from abu_v60.mingli.agent_packet import MingliAgentCasePacketCompiler
from abu_v60.mingli.agent_runtime import (
    MingliAgentRuntime,
    MingliAgentRuntimeError,
    configured_mingli_agent_runtime,
)
from abu_v60.mingli.agent_store import MingliAgentReadingStore
from abu_v60.mingli.mechanism_store import MingliMechanismVectorStore
from abu_v60.mingli.quant_store import MingliQuantVectorStore
from abu_v60.mingli.reading_store import (
    MingliReadingNotFoundError,
    MingliReadingStore,
)
from abu_v60.mingli.service import CaseNotFoundError, MingliCaseService
from abu_v60.mingli.showcases import SHOWCASE_ACCOUNT_REF, SHOWCASE_BY_SUBJECT
from abu_v60.mingli.timing_store import MingliTimingVectorStore

MINGLI_AGENT_REQUEST_VERSION = "v60.mingli-agent-request.001"
SUPPORTED_SUBJECT_KINDS = frozenset(
    {"HUMAN_OWNER", "HUMAN_REFERENCE", "CANONICAL_SYNTHETIC"}
)
SHOWCASE_CASE_REFS = frozenset(item.case_ref for item in SHOWCASE_BY_SUBJECT.values())


class MingliAgentServiceError(ValueError):
    pass


class MingliAgentService:
    """Explicit one-call whole-chart interpretation with exact lineage replay."""

    def __init__(
        self,
        engine: Engine,
        *,
        runtime: MingliAgentRuntime | None = None,
        store: MingliAgentReadingStore | None = None,
        cases: MingliCaseService | None = None,
        packet_compiler: MingliAgentCasePacketCompiler | None = None,
    ) -> None:
        self._cases = cases or MingliCaseService(engine)
        self._readings = MingliReadingStore(engine)
        self._quant = MingliQuantVectorStore(engine)
        self._mechanism = MingliMechanismVectorStore(engine)
        self._timing = MingliTimingVectorStore(engine)
        self._runtime = runtime or configured_mingli_agent_runtime()
        self._store = store or MingliAgentReadingStore(engine)
        self._packet_compiler = packet_compiler or MingliAgentCasePacketCompiler()
        # The private model serves one expensive whole-chart call at a time. This
        # also makes a double-click idempotent inside the API process.
        self._generation_lock = Lock()

    def generate(
        self,
        *,
        requester_account_ref: str,
        case_ref: str,
        expected_reading_ref: str,
        expected_reading_hash: str,
    ) -> MingliAgentReadingEnvelope:
        workspace = self._authorized_workspace(
            requester_account_ref=requester_account_ref,
            case_ref=case_ref,
        )
        try:
            reading = self._readings.get(reading_ref=expected_reading_ref)
        except MingliReadingNotFoundError as exc:
            raise MingliAgentServiceError("mingli_agent_base_reading_not_found") from exc
        lineage = (
            str(workspace["case"]["case_ref"]),
            str(workspace["chart"]["chart_version_ref"]),
            str(workspace["life_case"]["life_case_revision_ref"]),
        )
        if (
            reading.case_ref,
            reading.chart_version_ref,
            reading.life_case_revision_ref,
        ) != lineage:
            raise MingliAgentServiceError("mingli_agent_base_reading_lineage_conflict")
        if reading.reading_hash != expected_reading_hash:
            raise MingliAgentServiceError("mingli_agent_base_reading_hash_conflict")
        if (
            reading.quant_vector_ref is None
            or reading.mechanism_vector_ref is None
            or reading.timing_vector_ref is None
        ):
            raise MingliAgentServiceError("mingli_agent_base_reading_incomplete")

        quant = self._quant.get(vector_ref=reading.quant_vector_ref)
        mechanism = self._mechanism.get(vector_ref=reading.mechanism_vector_ref)
        timing = self._timing.get(vector_ref=reading.timing_vector_ref)
        try:
            packet = self._packet_compiler.compile(
                workspace=workspace,
                reading=reading,
                quant_vector=quant,
                mechanism_vector=mechanism,
                timing_vector=timing,
            )
        except ValueError as exc:
            raise MingliAgentServiceError(f"mingli_agent_packet_invalid:{exc}") from exc

        try:
            generation_key = self._runtime.generation_key(
                requester_account_ref=requester_account_ref,
                packet=packet,
            )
        except MingliAgentRuntimeError as exc:
            raise MingliAgentServiceError(str(exc)) from exc
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
                generated = self._runtime.run(
                    requester_account_ref=requester_account_ref,
                    packet=packet,
                )
            except MingliAgentRuntimeError as exc:
                raise MingliAgentServiceError(str(exc)) from exc
            return self._store.ensure(generated)

    def _authorized_workspace(
        self,
        *,
        requester_account_ref: str,
        case_ref: str,
    ) -> dict[str, object]:
        workspace_account_ref = (
            SHOWCASE_ACCOUNT_REF if case_ref in SHOWCASE_CASE_REFS else requester_account_ref
        )
        try:
            workspace = self._cases.workspace(
                account_ref=workspace_account_ref,
                case_ref=case_ref,
            )
        except CaseNotFoundError as exc:
            raise MingliAgentServiceError("mingli_agent_case_not_found") from exc
        if str(workspace["case"]["subject_kind"]) not in SUPPORTED_SUBJECT_KINDS:
            raise MingliAgentServiceError("mingli_agent_subject_kind_unsupported")
        return workspace
