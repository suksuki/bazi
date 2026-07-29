from __future__ import annotations

import json

import pytest
from abu_v60.decision import (
    BoundedReasonerContext,
    BoundedReasonerRuntime,
    CognitiveDecisionCoordinator,
    DecisionCandidate,
    DecisionKind,
    DecisionRequest,
    GateDisposition,
    OllamaGenerateReasonerProvider,
    OpenAIResponsesReasonerProvider,
    ReasonerCandidateContext,
    ReasonerContextError,
    ReasonerEvidenceContext,
    ReasonerGateRejected,
    ReasonerModelOutput,
    ReasonerProviderResult,
    ReasonerRuntimeStatus,
    ReasonerRuntimeUnavailable,
    reasoner_runtime_manifest,
    reasoner_runtime_status,
)
from abu_v60.provenance import content_hash
from abu_v60.settings import Settings


class _ScalarResult:
    def __init__(self, value: str | None) -> None:
        self._value = value

    def scalar_one_or_none(self) -> str | None:
        return self._value


class _MappingResult:
    def __init__(self, value: dict[str, object] | None) -> None:
        self._value = value

    def mappings(self) -> _MappingResult:
        return self

    def one_or_none(self) -> dict[str, object] | None:
        return self._value


class _MemoryConnection:
    def __init__(self) -> None:
        self.records: dict[str, dict[str, object]] = {}

    def execute(
        self,
        statement: object,
        parameters: dict[str, object],
    ) -> _ScalarResult | _MappingResult:
        sql = str(statement)
        decision_id = str(parameters["decision_id"])
        if "INSERT INTO cognition.decision_records" in sql:
            if decision_id in self.records:
                return _ScalarResult(None)
            self.records[decision_id] = {
                "record_json": json.loads(str(parameters["record_json"])),
                "record_hash": str(parameters["record_hash"]),
            }
            return _ScalarResult(decision_id)
        if "SELECT record_json, record_hash" in sql:
            return _MappingResult(self.records.get(decision_id))
        if "SELECT record_hash" in sql:
            record = self.records.get(decision_id)
            return _ScalarResult(
                str(record["record_hash"]) if record is not None else None
            )
        raise AssertionError(f"unexpected_sql:{sql}")


class _FakeProvider:
    provider_id = "fake-provider"
    model_ref = "fake-model:v1"
    model_profile_ref = "fake-profile:v1"
    model_profile_hash = "f" * 64

    def __init__(self, output: ReasonerModelOutput | None = None) -> None:
        self.calls = 0
        self.output = output or ReasonerModelOutput(
            selected_candidate_ref="candidate:a",
            reviewed_candidate_refs=("candidate:a", "candidate:b"),
            evidence_refs_used=("evidence:a",),
            counter_evidence_refs=("evidence:counter",),
            confidence=0.62,
            rationale_summary="A uses the admitted evidence more completely.",
        )

    def compare(
        self,
        *,
        request: DecisionRequest,
        context: BoundedReasonerContext,
    ) -> ReasonerProviderResult:
        self.calls += 1
        return ReasonerProviderResult(
            provider_response_ref="fake-response:1",
            output=self.output,
            input_tokens=80,
            output_tokens=24,
            total_tokens=104,
            duration_ms=7,
        )


def _request() -> DecisionRequest:
    return DecisionRequest(
        request_id="interpretation:1",
        decision_kind=DecisionKind.INTERPRETATION,
        subject_ref="case:1",
        evidence_refs=("evidence:a", "evidence:b", "evidence:counter"),
        candidates=(
            DecisionCandidate(
                candidate_ref="candidate:a",
                evidence_refs=("evidence:a",),
            ),
            DecisionCandidate(
                candidate_ref="candidate:b",
                evidence_refs=("evidence:b",),
            ),
        ),
        llm_allowed=True,
        correlation_id="correlation:1",
        causation_id="cause:1",
    )


def _evidence(
    evidence_ref: str,
    statement: str,
) -> ReasonerEvidenceContext:
    source_payload = {
        "evidence_ref": evidence_ref,
        "statement": statement,
    }
    return ReasonerEvidenceContext(
        evidence_ref=evidence_ref,
        statement=statement,
        source_ref=f"source:{evidence_ref}",
        source_version="v1",
        source_hash=content_hash(source_payload),
    )


def _context() -> BoundedReasonerContext:
    return BoundedReasonerContext(
        candidates=(
            ReasonerCandidateContext(
                candidate_ref="candidate:a",
                statement="The first interpretation.",
            ),
            ReasonerCandidateContext(
                candidate_ref="candidate:b",
                statement="The competing interpretation.",
            ),
        ),
        evidence=(
            _evidence("evidence:a", "Evidence supporting A."),
            _evidence("evidence:b", "Evidence supporting B."),
            _evidence("evidence:counter", "Counter-evidence to compare."),
        ),
    )


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "database_url": "postgresql+psycopg:///test",
        "environment": "test",
        "world_runtime_enabled": False,
        "world_runtime_poll_seconds": 1.0,
        "reasoner_enabled": False,
        "reasoner_provider": None,
        "reasoner_model": None,
        "reasoner_api_key": None,
        "reasoner_base_url": "https://api.openai.com/v1",
        "reasoner_timeout_seconds": 30.0,
        "reasoner_profile_ref": "v60.model-serving.gemma4-structured-decision.001",
        "reasoner_think": False,
        "reasoner_temperature": 0.0,
        "reasoner_top_p": 0.95,
        "reasoner_top_k": 64,
        "reasoner_num_ctx": 32768,
        "reasoner_num_predict": 1200,
        "reasoner_keep_alive": "30m",
    }
    values.update(overrides)
    return Settings(**values)


def test_reasoner_runtime_admits_and_records_one_bounded_proposal() -> None:
    provider = _FakeProvider()
    runtime = BoundedReasonerRuntime(provider=provider, enabled=True)
    coordinator = CognitiveDecisionCoordinator(reasoner=runtime)
    connection = _MemoryConnection()

    result = coordinator.decide_and_record(
        connection=connection,
        request=_request(),
        reasoner_context=_context(),
    )
    replay = coordinator.decide_and_record(
        connection=connection,
        request=_request(),
        reasoner_context=_context(),
    )

    assert result.reasoner_execution is not None
    assert result.reasoner_execution.gate_receipt.disposition is GateDisposition.ADMITTED
    assert result.reasoner_execution.gate_receipt.canonical_domain_write_allowed is False
    assert result.ledger_result.route.selected_candidate_ref == "candidate:a"
    assert result.ledger_result.record_hash == replay.ledger_result.record_hash
    assert replay.ledger_result.already_recorded is True
    assert replay.reasoner_execution is None
    assert provider.calls == 1


def test_reasoner_context_must_exactly_match_qualified_refs() -> None:
    provider = _FakeProvider()
    runtime = BoundedReasonerRuntime(provider=provider, enabled=True)
    context = _context().model_copy(
        update={
            "evidence": (
                _evidence("evidence:a", "Evidence supporting A."),
                _evidence("evidence:b", "Evidence supporting B."),
            )
        }
    )

    with pytest.raises(
        ReasonerContextError,
        match="reasoner_evidence_context_mismatch",
    ):
        runtime.run(request=_request(), context=context)
    assert provider.calls == 0


def test_reasoner_output_with_unbound_evidence_is_rejected_by_gate() -> None:
    provider = _FakeProvider(
        ReasonerModelOutput(
            selected_candidate_ref="candidate:a",
            reviewed_candidate_refs=("candidate:a", "candidate:b"),
            evidence_refs_used=("evidence:invented",),
            counter_evidence_refs=(),
            confidence=0.5,
            rationale_summary="Invented evidence must fail.",
        )
    )
    runtime = BoundedReasonerRuntime(provider=provider, enabled=True)

    with pytest.raises(
        ReasonerGateRejected,
        match="proposal_uses_unbound_evidence",
    ):
        runtime.run(request=_request(), context=_context())


def test_disabled_or_missing_provider_fails_before_network() -> None:
    provider = _FakeProvider()
    runtime = BoundedReasonerRuntime(provider=provider, enabled=False)

    with pytest.raises(
        ReasonerRuntimeUnavailable,
        match="bounded_reasoner_not_ready",
    ):
        runtime.run(request=_request(), context=_context())
    assert provider.calls == 0


def test_openai_adapter_uses_strict_schema_and_never_sends_secret_in_payload() -> None:
    captured: dict[str, object] = {}

    def transport(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        result = {
            "selected_candidate_ref": "candidate:a",
            "reviewed_candidate_refs": ["candidate:a", "candidate:b"],
            "evidence_refs_used": ["evidence:a"],
            "counter_evidence_refs": ["evidence:counter"],
            "confidence": 0.61,
            "rationale_summary": "A is better supported.",
        }
        return {
            "id": "resp_reasoner_1",
            "status": "completed",
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": json.dumps(result),
                        }
                    ],
                }
            ],
            "usage": {
                "input_tokens": 100,
                "output_tokens": 20,
                "total_tokens": 120,
            },
        }

    provider = OpenAIResponsesReasonerProvider(
        api_key="secret-test-key",
        model_ref="configured-model",
        base_url="https://api.openai.com/v1",
        timeout_seconds=15,
        transport=transport,
    )
    result = provider.compare(request=_request(), context=_context())
    payload = captured["payload"]
    assert isinstance(payload, dict)

    assert captured["url"] == "https://api.openai.com/v1/responses"
    assert payload["store"] is False
    assert payload["text"]["format"]["strict"] is True
    assert "secret-test-key" not in canonical_json_for_test(payload)
    assert result.provider_response_ref == "resp_reasoner_1"
    assert result.total_tokens == 120


def test_ollama_adapter_uses_frozen_gemma4_structured_profile() -> None:
    captured: dict[str, object] = {}

    def transport(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        result = {
            "selected_candidate_ref": "candidate:b",
            "reviewed_candidate_refs": ["candidate:a", "candidate:b"],
            "evidence_refs_used": ["evidence:b"],
            "counter_evidence_refs": ["evidence:counter"],
            "confidence": 0.57,
            "rationale_summary": "B has the clearer admitted support.",
        }
        return {
            "model": "gemma4:latest",
            "created_at": "2026-07-29T01:00:00Z",
            "response": json.dumps(result),
            "done": True,
            "prompt_eval_count": 130,
            "eval_count": 26,
        }

    provider = OllamaGenerateReasonerProvider(
        model_ref="gemma4:latest",
        model_profile_ref="v60.model-serving.gemma4-structured-decision.001",
        base_url="http://dblife.com:11888",
        timeout_seconds=180,
        transport=transport,
    )
    result = provider.compare(request=_request(), context=_context())
    payload = captured["payload"]
    assert isinstance(payload, dict)

    assert captured["url"] == "http://dblife.com:11888/api/generate"
    assert payload["stream"] is False
    assert payload["think"] is False
    assert payload["format"]["additionalProperties"] is False
    assert payload["options"]["temperature"] == 0
    assert payload["options"]["top_p"] == 0.95
    assert payload["options"]["top_k"] == 64
    assert payload["options"]["num_ctx"] == 32768
    assert payload["options"]["num_predict"] == 1200
    assert "repeat_penalty" not in payload["options"]
    assert payload["keep_alive"] == "30m"
    assert provider.model_profile_hash == content_hash(provider.model_profile)
    assert result.output.selected_candidate_ref == "candidate:b"
    assert result.total_tokens == 156
    assert result.provider_response_ref.startswith("v60-ollama-response-")


def test_ollama_adapter_accepts_structured_json_from_thinking_channel() -> None:
    result = {
        "selected_candidate_ref": "candidate:a",
        "reviewed_candidate_refs": ["candidate:a", "candidate:b"],
        "evidence_refs_used": ["evidence:a"],
        "counter_evidence_refs": [],
        "confidence": 0.54,
        "rationale_summary": "A has bounded support.",
    }

    def transport(**_: object) -> dict[str, object]:
        return {
            "model": "gemma4:latest",
            "created_at": "2026-07-29T01:01:00Z",
            "response": "",
            "thinking": json.dumps(result),
            "done": True,
            "prompt_eval_count": 100,
            "eval_count": 20,
        }

    provider = OllamaGenerateReasonerProvider(
        model_ref="gemma4:latest",
        model_profile_ref="v60.model-serving.gemma4-structured-decision.001",
        base_url="http://dblife.com:11888",
        timeout_seconds=180,
        transport=transport,
    )

    output = provider.compare(request=_request(), context=_context())

    assert output.output.selected_candidate_ref == "candidate:a"
    assert output.total_tokens == 120


@pytest.mark.parametrize(
    ("configuration", "expected"),
    (
        ({}, ReasonerRuntimeStatus.NOT_CONFIGURED),
        (
            {
                "reasoner_provider": "openai-responses",
                "reasoner_model": "configured-model",
                "reasoner_api_key": "secret",
            },
            ReasonerRuntimeStatus.DISABLED,
        ),
        (
            {
                "reasoner_enabled": True,
                "reasoner_provider": "unsupported",
                "reasoner_model": "configured-model",
                "reasoner_api_key": "secret",
            },
            ReasonerRuntimeStatus.MISCONFIGURED,
        ),
        (
            {
                "reasoner_enabled": True,
                "reasoner_provider": "openai-responses",
                "reasoner_model": "configured-model",
                "reasoner_api_key": "secret",
            },
            ReasonerRuntimeStatus.READY,
        ),
        (
            {
                "reasoner_enabled": True,
                "reasoner_provider": "ollama-generate",
                "reasoner_model": "gemma4:latest",
            },
            ReasonerRuntimeStatus.READY,
        ),
    ),
)
def test_reasoner_status_is_explicit_and_never_exposes_secret(
    configuration: dict[str, object],
    expected: ReasonerRuntimeStatus,
) -> None:
    current_settings = _settings(**configuration)

    assert reasoner_runtime_status(current_settings) is expected
    manifest = reasoner_runtime_manifest(current_settings)
    assert manifest["status"] == expected.value
    assert "secret" not in json.dumps(manifest)


def canonical_json_for_test(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)
