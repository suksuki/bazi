from __future__ import annotations

import io
import wave
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from product.agent_case_store import MemoryAgentCaseStore
from product.app import create_product_app
from product.product_store import MemoryProductStore
from product.theater_performance import (
    PerformancePackageRepository,
    SynthesizedSpeech,
    TheaterPerformanceService,
)
from experience import compile_topic, load_topic_package
from experience.contracts import (
    AllowedChartFact,
    ApprovedClaim,
    ApprovedReasoningStep,
    EnvelopeFallback,
    EnvelopeSource,
    EnvelopeUncertainty,
    MingliExperienceEnvelope,
    ParticipantScope,
    TopicPackage,
    TopicScope,
)
from experience.runtime import TheaterRuntime, TheaterRuntimeError
from experience.store import MemoryTheaterStore


ROOT = Path(__file__).resolve().parents[1]
TOPICS = ROOT / "packages" / "experience" / "topics"


class _FakeTheaterTTS:
    voice_id = "Eric"
    voice_version = "fake-qwen-eric.v1"

    def __init__(self) -> None:
        self.calls = 0

    def synthesize(self, text: str) -> SynthesizedSpeech:
        self.calls += 1
        target = io.BytesIO()
        with wave.open(target, "wb") as writer:
            writer.setnchannels(1)
            writer.setsampwidth(2)
            writer.setframerate(24_000)
            frames = bytearray()
            for index in range(24_000 * 2):
                value = 0 if index < 1_200 else (4_000 if (index // 1_200) % 2 else 500)
                frames.extend(int(value).to_bytes(2, "little", signed=True))
            writer.writeframes(bytes(frames))
        return SynthesizedSpeech(wav_bytes=target.getvalue(), generation_seconds=0.01)


class _OverwriteTheaterStore(MemoryTheaterStore):
    """Matches stores that do not silently repair stale aggregate snapshots."""

    def save_session(self, session) -> None:
        with self._lock:
            self._sessions[session.session_id] = session


def _compiled(name: str):
    return compile_topic(load_topic_package(TOPICS / name))


def _envelope(topic, participant: str, mode: str = "personal_ready") -> MingliExperienceEnvelope:
    now = datetime.now(timezone.utc)
    facts = [
        AllowedChartFact(
            fact_ref="chart.pillars",
            fact_type="four_pillars",
            display_value="甲子 · 乙丑 · 丙寅 · 丁卯",
            visual_anchor="four-pillars",
        )
    ]
    claims = [
        ApprovedClaim(
            claim_ref="baseline-claim-1",
            category="baseline",
            approved_meaning="你更擅长把复杂经验整理成可以传递的方法。",
            certainty="medium",
            conditions=["现实中持续输出并获得反馈"],
            counter_signals=["长期没有任何表达或转化行为"],
            evidence_refs=["chart.fact.1"],
        )
    ]
    if mode == "observer":
        facts = []
        claims = []
        disclosure = "observer"
        life_case_version = None
    elif mode == "chart_facts_only":
        claims = []
        disclosure = "chart_facts"
        life_case_version = None
    else:
        disclosure = "approved_insights"
        life_case_version = "life-case-v3"
    return MingliExperienceEnvelope(
        envelope_id=f"envelope-{participant}",
        mode=mode,
        participant_scope=ParticipantScope(
            participant_ref=participant,
            privacy_level="account",
            disclosure_level=disclosure,
        ),
        source=EnvelopeSource(
            chart_version="chart-v2",
            life_case_version=life_case_version,
            generated_at=now,
            expires_at=now + timedelta(hours=2),
            source_hash=(participant.encode().hex() + "a" * 64)[:64],
        ),
        topic_scope=TopicScope(topic_id=topic.topic.topic_id, topic_version=topic.topic.version),
        allowed_chart_facts=facts,
        approved_claims=claims,
        uncertainty=EnvelopeUncertainty(level="medium", reasons=["需要现实反馈继续区分"]),
        must_not_say=["命中注定"],
        fallback=EnvelopeFallback(mode="chart_facts_only" if facts else "observer"),
    )


def _runtime(*topic_names: str):
    store = MemoryTheaterStore()
    topics = [_compiled(name) for name in topic_names]
    return TheaterRuntime(store=store, topics=topics), store, topics


def test_topic00_and_topic01_compile_as_immutable_generic_topics() -> None:
    topic00 = _compiled("topic00_living_theater.json")
    topic01 = _compiled("topic01_contract_fixture.json")

    assert len(topic00.scene_nodes) == 10
    assert len(topic01.scene_nodes) == 4
    assert set(topic00.topic.supported_modes) == {"live", "time_shift", "solo", "replay"}
    assert topic00.content_hash != topic01.content_hash
    with pytest.raises(Exception):
        topic00.scene_nodes["opening"] = topic00.scene_nodes["closing"]

    runtime_source = (ROOT / "packages" / "experience" / "runtime.py").read_text(encoding="utf-8")
    frontend_source = (ROOT / "apps" / "product" / "static" / "l5" / "theater.js").read_text(encoding="utf-8")
    assert 'topic_id == "topic-00' not in runtime_source
    assert 'topic_id == "topic-01' not in runtime_source
    assert "topic-01-irreplaceable-node" not in frontend_source


def test_compiler_rejects_public_envelope_access() -> None:
    package = load_topic_package(TOPICS / "topic01_contract_fixture.json")
    rows = [item.model_dump(mode="json") for item in package.scene_nodes]
    rows[0]["data_bindings"] = ["envelope.approved_claims"]
    invalid = TopicPackage.model_validate({**package.model_dump(mode="json"), "scene_nodes": rows})

    with pytest.raises(ValueError, match="public_node_reads_envelope"):
        compile_topic(invalid)


def test_private_cues_are_isolated_from_public_stream_and_other_participants() -> None:
    runtime, store, (topic,) = _runtime("topic00_living_theater.json")
    session = runtime.create_session(topic_id=topic.topic.topic_id, topic_version=topic.topic.version, mode="live")
    run_a = runtime.join(session_id=session.session_id, envelope=_envelope(topic, "participant-a"))
    run_b = runtime.join(session_id=session.session_id, envelope=_envelope(topic, "participant-b"))

    runtime.advance(session_id=session.session_id)
    runtime.complete_private(
        session_id=session.session_id,
        participant_run_id=run_a.participant_run_id,
        response="我正在坚持的事",
    )

    public = runtime.snapshot(session_id=session.session_id)
    private_a = runtime.snapshot(session_id=session.session_id, participant_run_id=run_a.participant_run_id)
    private_b = runtime.snapshot(session_id=session.session_id, participant_run_id=run_b.participant_run_id)
    public_blob = str(public)

    assert "我正在坚持的事" not in public_blob
    assert "baseline-claim-1" not in public_blob
    assert all(event["scope"] == "public" for event in public["events"])
    assert "我正在坚持的事" in str(private_a)
    private_b_answers = [
        event["payload"].get("response")
        for event in private_b["events"]
        if event["event_type"] == "private_interaction_completed"
    ]
    assert "我正在坚持的事" not in private_b_answers
    assert store.get_envelope(run_a.envelope_id) is not None


def test_live_barrier_group_reveal_and_rejoin_use_anonymous_aggregation() -> None:
    runtime, _, (topic,) = _runtime("topic00_living_theater.json")
    session = runtime.create_session(topic_id=topic.topic.topic_id, topic_version=topic.topic.version, mode="live")
    runs = [runtime.join(session_id=session.session_id, envelope=_envelope(topic, f"participant-{i}")) for i in range(3)]
    runtime.advance(session_id=session.session_id)
    answers = ["我正在坚持的事", "我正在坚持的事", "我反复卡住的地方"]
    for run, answer in zip(runs, answers, strict=True):
        runtime.complete_private(
            session_id=session.session_id,
            participant_run_id=run.participant_run_id,
            response=answer,
        )
    reveal = runtime.reveal_group_trace(session_id=session.session_id)
    session = runtime.rejoin(session_id=session.session_id)

    assert reveal.payload["choice_counts"] == {"我正在坚持的事": 2, "我反复卡住的地方": 1}
    assert "participant-" not in str(reveal.model_dump(mode="json"))
    assert session.current_public_node_id == "group_reveal"
    assert session.active_private_node_id is None


def test_frozen_cues_are_identical_in_live_snapshot_and_replay() -> None:
    runtime, store, (topic,) = _runtime("topic00_living_theater.json")
    session = runtime.create_session(topic_id=topic.topic.topic_id, topic_version=topic.topic.version, mode="solo")
    run = runtime.join(session_id=session.session_id, envelope=_envelope(topic, "participant-replay"))
    runtime.advance(session_id=session.session_id)
    runtime.complete_private(
        session_id=session.session_id,
        participant_run_id=run.participant_run_id,
        response="我尚未说出口的变化",
    )
    before = {item.cue_instance_id: item.cue_hash for item in store.list_cues(session.session_id)}
    replay = runtime.replay(session_id=session.session_id, participant_run_id=run.participant_run_id)
    after = {item.cue_instance_id: item.cue_hash for item in store.list_cues(session.session_id)}

    assert before == after
    assert {item["cue_instance_id"]: item["cue_hash"] for item in replay["cues"]} == before
    assert replay["regeneration_performed"] is False
    assert replay["llm_used"] is False
    assert replay["reasoner_used"] is False
    assert replay["tts_regenerated"] is False


def test_private_cue_repairs_duplicate_punctuation_without_changing_claim_reference() -> None:
    runtime, store, (topic,) = _runtime("topic00_living_theater.json")
    envelope = _envelope(topic, "participant-typography")
    claim = envelope.approved_claims[0].model_copy(
        update={
            "approved_meaning": "这是一条已经批准的案例认知。",
            "conditions": ["条件甲；", "条件乙。"],
        }
    )
    envelope = envelope.model_copy(update={"approved_claims": [claim]})
    session = runtime.create_session(topic_id=topic.topic.topic_id, topic_version=topic.topic.version, mode="solo")
    run = runtime.join(session_id=session.session_id, envelope=envelope)
    runtime.advance(session_id=session.session_id)
    runtime.complete_private(
        session_id=session.session_id,
        participant_run_id=run.participant_run_id,
        response="我正在坚持的事",
    )
    runtime.advance(session_id=session.session_id)

    private_cues = [cue for cue in store.list_cues(session.session_id) if cue.participant_run_id == run.participant_run_id]
    personal = private_cues[-1]
    assert "。。" not in personal.final_dialogue
    assert "；；" not in personal.final_dialogue
    assert personal.claim_refs == [claim.claim_ref]


def test_disconnect_recovery_only_returns_events_after_cursor() -> None:
    runtime, _, (topic,) = _runtime("topic00_living_theater.json")
    session = runtime.create_session(topic_id=topic.topic.topic_id, topic_version=topic.topic.version, mode="solo")
    run = runtime.join(session_id=session.session_id, envelope=_envelope(topic, "participant-recover"))
    cursor = runtime.snapshot(session_id=session.session_id, participant_run_id=run.participant_run_id)["session"]["sequence"]
    runtime.advance(session_id=session.session_id)
    delta = runtime.snapshot(
        session_id=session.session_id,
        participant_run_id=run.participant_run_id,
        after_sequence=cursor,
    )

    assert delta["recovered"] is True
    assert delta["events"]
    assert all(item["sequence"] > cursor for item in delta["events"])


def test_solo_rejoin_never_overwrites_the_latest_event_sequence() -> None:
    topic = _compiled("topic00_living_theater.json")
    store = _OverwriteTheaterStore()
    runtime = TheaterRuntime(store=store, topics=[topic])
    session = runtime.create_session(topic_id=topic.topic.topic_id, topic_version=topic.topic.version, mode="solo")
    run = runtime.join(session_id=session.session_id, envelope=_envelope(topic, "participant-sequence"))

    runtime.advance(session_id=session.session_id)
    runtime.complete_private(
        session_id=session.session_id,
        participant_run_id=run.participant_run_id,
        response="我正在坚持的事",
    )

    current = store.get_session(session.session_id)
    events = store.list_events(session.session_id)
    participant = store.get_participant(run.participant_run_id)
    assert current is not None
    assert participant is not None
    assert current.sequence == max(item.sequence for item in events)
    assert current.current_public_node_id == "group_reveal"
    assert participant.status == "joined"


@pytest.mark.parametrize("mode", ["solo", "time_shift"])
def test_topic00_runs_private_scene_in_independent_modes(mode: str) -> None:
    runtime, _, (topic,) = _runtime("topic00_living_theater.json")
    session = runtime.create_session(topic_id=topic.topic.topic_id, topic_version=topic.topic.version, mode=mode)
    run = runtime.join(session_id=session.session_id, envelope=_envelope(topic, f"participant-{mode}"))
    runtime.advance(session_id=session.session_id)
    runtime.complete_private(
        session_id=session.session_id,
        participant_run_id=run.participant_run_id,
        response="我反复卡住的地方",
    )
    snapshot = runtime.snapshot(session_id=session.session_id, participant_run_id=run.participant_run_id)
    assert snapshot["session"]["current_public_node_id"] == "group_reveal"
    assert snapshot["participant"]["status"] == "joined"


def test_topic01_fixture_runs_without_topic_specific_runtime_branch() -> None:
    runtime, _, (_, topic01) = _runtime("topic00_living_theater.json", "topic01_contract_fixture.json")
    session = runtime.create_session(topic_id=topic01.topic.topic_id, topic_version=topic01.topic.version, mode="solo")
    run = runtime.join(session_id=session.session_id, envelope=_envelope(topic01, "fixture-user", "observer"))
    runtime.advance(session_id=session.session_id)
    runtime.complete_private(
        session_id=session.session_id,
        participant_run_id=run.participant_run_id,
        response="左",
    )
    runtime.advance(session_id=session.session_id)
    snapshot = runtime.snapshot(session_id=session.session_id, participant_run_id=run.participant_run_id)

    assert snapshot["session"]["current_public_node_id"] == "fixture_close"
    assert snapshot["session"]["status"] == "completed"
    assert snapshot["topic"]["topic_id"] == topic01.topic.topic_id
    assert snapshot["topic"]["required_experience_capabilities"] == ["private_scene", "barrier"]


def test_public_payload_redline_is_enforced() -> None:
    runtime, _, (topic,) = _runtime("topic00_living_theater.json")
    session = runtime.create_session(topic_id=topic.topic.topic_id, topic_version=topic.topic.version, mode="solo")
    with pytest.raises(TheaterRuntimeError, match="public_event_sensitive_key"):
        runtime._append_event(  # noqa: SLF001 - explicit redline fault injection
            session,
            event_type="fault_injection",
            scope="public",
            payload={"approved_claims": ["private"]},
        )


def test_product_api_supports_observer_join_and_rejects_wrong_private_token(monkeypatch) -> None:
    monkeypatch.delenv("V50_DATABASE_URL", raising=False)
    app = create_product_app(
        product_store=MemoryProductStore(),
        agent_case_store=MemoryAgentCaseStore(),
    )
    client = TestClient(app)
    created = client.post(f"/api/v50/theater/sessions", json={"mode": "solo"})
    session_id = created.json()["session"]["session_id"]
    joined = client.post(
        f"/api/v50/theater/sessions/{session_id}/join",
        json={"disclosure_level": "observer"},
    )
    body = joined.json()
    run_id = body["participant_run"]["participant_run_id"]

    denied = client.get(
        f"/api/v50/theater/sessions/{session_id}",
        params={"participant_run_id": run_id, "access_token": "wrong-token-that-is-long-enough"},
    )
    allowed = client.get(
        f"/api/v50/theater/sessions/{session_id}",
        params={"participant_run_id": run_id, "access_token": body["access_token"]},
    )

    assert joined.status_code == 200
    assert body["envelope_mode"] == "observer"
    assert denied.status_code == 403
    assert allowed.status_code == 200
    assert "access_token_hash" not in str(allowed.json())


def test_experience_package_has_no_life_case_repository_dependency() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "packages" / "experience").glob("*.py")
    )
    assert "from core.life_case" not in text
    assert "import core.life_case" not in text
    assert "AgentCaseStore" not in text
    assert "RealityEvidence" not in text


def test_performance_proof_compiles_a_frozen_audio_clock_package(tmp_path: Path) -> None:
    runtime, store, (topic,) = _runtime("topic00_performance_proof01.json")
    envelope = _envelope(topic, "performance-user")
    step = ApprovedReasoningStep(
        step_ref="baseline-claim-1.reasoning.0",
        premise="月令与透干共同指向持续输出",
        conclusion="表达和转化是当前获批主线",
        source_refs=["chart.fact.1"],
        visual_anchor="reasoning-step-0",
    )
    claim = envelope.approved_claims[0].model_copy(
        update={
            "spoken_summary": envelope.approved_claims[0].approved_meaning,
            "subtitle_summary": "复杂经验可以转化为可传递的方法",
            "visual_anchors": [step.visual_anchor],
        }
    )
    envelope = envelope.model_copy(
        update={"approved_claims": [claim], "approved_reasoning_steps": [step]}
    )
    session = runtime.create_session(
        topic_id=topic.topic.topic_id,
        topic_version=topic.topic.version,
        mode="solo",
    )
    run = runtime.join(session_id=session.session_id, envelope=envelope)
    runtime.advance(session_id=session.session_id)
    cue = [
        item
        for item in store.list_cues(session.session_id)
        if item.participant_run_id == run.participant_run_id
    ][0]
    tts = _FakeTheaterTTS()
    service = TheaterPerformanceService(
        repository=PerformancePackageRepository(tmp_path),
        tts=tts,
    )

    package = service.prepare(cue=cue, envelope=envelope)
    replay_package = service.prepare(cue=cue, envelope=envelope)

    assert package == replay_package
    assert tts.calls == 1
    assert package.audio.voice_id == "Eric"
    assert package.audio.sha256 == replay_package.audio.sha256
    assert package.subtitle_track
    assert package.viseme_track
    assert len(package.stage_snapshot.chart_facts) == 1
    assert package.stage_snapshot.reasoning_steps == [step]
    assert any(item.action == "highlight_approved_path" for item in package.stage_track)
    assert any(item.action == "listen" for item in package.actor_track)
    assert service.repository.audio_path(package.package_id).read_bytes().startswith(b"RIFF")


def test_performance_api_authorizes_private_frozen_audio(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("V50_DATABASE_URL", raising=False)
    tts = _FakeTheaterTTS()
    service = TheaterPerformanceService(
        repository=PerformancePackageRepository(tmp_path),
        tts=tts,
    )
    app = create_product_app(
        product_store=MemoryProductStore(),
        agent_case_store=MemoryAgentCaseStore(),
        theater_performance_service=service,
    )
    client = TestClient(app)
    created = client.post(
        "/api/v50/theater/sessions",
        json={"topic_id": "topic-00-performance-proof-01", "topic_version": "1.0.0", "mode": "solo"},
    ).json()
    session_id = created["session"]["session_id"]
    joined = client.post(
        f"/api/v50/theater/sessions/{session_id}/join",
        json={"disclosure_level": "observer"},
    ).json()
    run_id = joined["participant_run"]["participant_run_id"]
    token = joined["access_token"]
    client.post(
        f"/api/v50/theater/sessions/{session_id}/participant/advance",
        json={"participant_run_id": run_id, "access_token": token, "event": "next"},
    )
    snapshot = client.get(
        f"/api/v50/theater/sessions/{session_id}",
        params={"participant_run_id": run_id, "access_token": token},
    ).json()
    cue_id = snapshot["cues"][-1]["cue_instance_id"]
    prepared = client.post(
        f"/api/v50/theater/sessions/{session_id}/cues/{cue_id}/performance",
        json={"participant_run_id": run_id, "access_token": token},
    )
    package = prepared.json()["package"]
    allowed_audio = client.get(
        f"/api/v50/theater/sessions/{session_id}/performance/{package['package_id']}/audio",
        params={"participant_run_id": run_id, "access_token": token},
    )
    denied_audio = client.get(
        f"/api/v50/theater/sessions/{session_id}/performance/{package['package_id']}/audio",
        params={"participant_run_id": run_id, "access_token": "wrong-token-that-is-long-enough"},
    )

    assert prepared.status_code == 200
    assert prepared.json()["llm_used"] is False
    assert prepared.json()["reasoner_used"] is False
    assert allowed_audio.status_code == 200
    assert allowed_audio.content.startswith(b"RIFF")
    assert denied_audio.status_code == 403
    assert tts.calls == 1
