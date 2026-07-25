from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from threading import Barrier

import pytest
from fastapi.testclient import TestClient

from experience.dream_navigation import DreamControlCredential
from experience.dream_game import BlindRoundDefinition
from product.agent_case_store import MemoryAgentCaseStore
from product.app import create_product_app
from product.dream_feature import DreamFeaturePolicy
from product.dream_game_content import compile_simulated_round, load_content_pack
from product.dream_game_service import DreamGameError, DreamGameService
from product.dream_pilot import DreamCanonicalNpcBootstrapService
from product.dream_service import DreamJourneyService
from product.dream_store_memory import MemoryDreamStore
from product.product_api import PRODUCT_SESSION_COOKIE
from product.product_store import MemoryProductStore
from test_v50_dream_bridge_01 import (
    _activate_dream_control,
    _case_payload,
    _enter_three_tree_visit,
)
from test_v50_dream_problem_flower_fruit_01 import (
    _advance_to_draft,
    _seal_payload,
)


def _multi_user_app():
    product_store = MemoryProductStore()
    accounts = [
        product_store.register_account(
            email=f"dream-multi-{index}@example.com",
            password=f"dream-multi-pass-{index}",
            display_name=f"Dream Visitor {index}",
            role="member",
        )
        for index in (1, 2)
    ]
    user_ids = [str(item["user_id"]) for item in accounts]
    home_case_ids = ["case-dream-multi-1", "case-dream-multi-2"]
    case_store = MemoryAgentCaseStore()
    for index, (user_id, case_id) in enumerate(zip(user_ids, home_case_ids), start=1):
        case_store.save(
            case_id=case_id,
            user_id=user_id,
            profile_id=f"profile-dream-multi-{index}",
            payload=_case_payload(case_id),
        )
    dream_store = MemoryDreamStore()
    DreamCanonicalNpcBootstrapService(
        case_store=case_store,
        dream_store=dream_store,
    ).ensure()
    policy = DreamFeaturePolicy(
        enabled=True,
        allowed_user_ids=frozenset(user_ids),
    )
    app = create_product_app(
        product_store=product_store,
        agent_case_store=case_store,
        dream_store=dream_store,
        dream_feature_policy=policy,
    )
    clients = [TestClient(app), TestClient(app)]
    for client, user_id, case_id in zip(clients, user_ids, home_case_ids):
        client.cookies.set(
            PRODUCT_SESSION_COOKIE,
            product_store.create_session(user_id=user_id),
        )
        granted = client.post("/api/v50/dream/consent", json={
            "case_id": case_id,
            "accepted": True,
            "consent_version": "deepbazi.dream_pilot_consent.v1",
        })
        assert granted.status_code == 200, granted.text
    return clients, dream_store, case_store, policy, user_ids, home_case_ids


def _credential(client: TestClient) -> DreamControlCredential:
    return DreamControlCredential(
        client_instance_id=str(client.headers["x-dream-client-instance"]),
        lease_id=str(client.headers["x-dream-lease-id"]),
        lease_epoch=int(client.headers["x-dream-lease-epoch"]),
        fence_token=int(client.headers["x-dream-fence-token"]),
    )


def _shared_npc_rounds():
    clients, store, case_store, policy, user_ids, case_ids = _multi_user_app()
    visits: list[str] = []
    cards: list[list[dict[str, object]]] = []
    for client, case_id in zip(clients, case_ids):
        visit_id, _ = _enter_three_tree_visit(client, case_id)
        visits.append(visit_id)
        response = client.get(f"/api/v50/dream/visits/{visit_id}/game/rounds")
        assert response.status_code == 200, response.text
        cards.append(response.json())
    by_scene = [
        {str(item["resident_scene_ref"]): item for item in card_set}
        for card_set in cards
    ]
    shared_scene_refs = sorted(set(by_scene[0]) & set(by_scene[1]))
    npc_scene_ref = next(
        scene_ref
        for scene_ref in shared_scene_refs
        if store.get_grant(public_scene_ref=scene_ref).subject_kind == "canonical_npc"
    )
    first = by_scene[0][npc_scene_ref]
    second = by_scene[1][npc_scene_ref]
    assert first["round_id"] == second["round_id"]
    return (
        clients,
        store,
        case_store,
        policy,
        user_ids,
        visits,
        first,
    )


def _start_shared_rounds():
    clients, store, case_store, policy, user_ids, visits, card = _shared_npc_rounds()
    attempts: list[dict[str, object]] = []
    bases: list[str] = []
    for client, visit_id in zip(clients, visits):
        base = f"/api/v50/dream/visits/{visit_id}/game"
        response = client.post(f"{base}/rounds/{card['round_id']}/start")
        assert response.status_code == 200, response.text
        bases.append(base)
        attempts.append(response.json())
    return clients, store, case_store, policy, user_ids, visits, bases, attempts


def test_two_visitors_share_one_flower_but_never_receive_each_others_answers() -> None:
    clients, store, _, _, user_ids, _, bases, attempts = _start_shared_rounds()
    sealed_attempts = []
    for index, (client, base, attempt) in enumerate(
        zip(clients, bases, attempts),
        start=1,
    ):
        draft = _advance_to_draft(client, store, base, attempt)
        response = client.post(
            f"{base}/attempts/{draft['attempt_id']}/judgment/seal",
            json=_seal_payload(draft, key=f"multi-answer-{index}"),
        )
        assert response.status_code == 200, response.text
        sealed = response.json()
        sealed_attempts.append(sealed)
        assert sealed["state"] == "USER_JUDGMENT_SEALED"
        assert sealed["flower"]["state"] == "OPEN"
        assert sealed["flower"]["own_answer_sealed"] is True
        assert sealed["flower"]["shared_fruit_visible"] is False
        assert sealed["flower"]["answer_count_visible"] is False
        assert sealed["flower"]["answer_count"] is None
        assert "outcome_evidence" not in response.text
        assert "system_seal" not in response.text

    round_id = str(sealed_attempts[0]["round_id"])
    answer_seals = store.list_game_answer_seals(round_id=round_id)
    assert len(answer_seals) == 2
    assert {item.viewer_id for item in answer_seals} == set(user_ids)
    assert store.get_game_flower(round_id=round_id).state == "OPEN"


def test_natural_close_forms_exactly_one_shared_fruit_for_all_answers() -> None:
    (
        clients,
        store,
        case_store,
        policy,
        user_ids,
        visits,
        bases,
        attempts,
    ) = _start_shared_rounds()
    sealed_attempts = []
    for index, (client, base, attempt) in enumerate(
        zip(clients, bases, attempts),
        start=1,
    ):
        draft = _advance_to_draft(client, store, base, attempt)
        response = client.post(
            f"{base}/attempts/{draft['attempt_id']}/judgment/seal",
            json=_seal_payload(draft, key=f"shared-fruit-{index}"),
        )
        assert response.status_code == 200, response.text
        sealed_attempts.append(response.json())

    round_definition = store.get_game_round(round_id=sealed_attempts[0]["round_id"])
    assert round_definition is not None
    assert round_definition.answer_close_at is not None
    assert round_definition.outcome_due_at is not None
    close_clock = round_definition.answer_close_at + timedelta(seconds=1)
    closer = DreamGameService(
        journey=object(),
        store=store,
        clock=lambda: close_clock,
    )
    first_closed = closer._close_flower(
        round_definition=round_definition,
        reason="NATURAL_WITHER",
        trigger_kind="SYSTEM",
        trigger_ref="test-scheduler",
        idempotency_key="natural-close-shared-flower",
    )
    repeated_closed = closer._close_flower(
        round_definition=round_definition,
        reason="NATURAL_WITHER",
        trigger_kind="SYSTEM",
        trigger_ref="test-scheduler",
        idempotency_key="natural-close-shared-flower",
    )
    assert first_closed == repeated_closed
    assert first_closed.state == "SHARED_FRUIT_FORMED"
    assert first_closed.answer_count == 2
    assert first_closed.shared_fruit_ref

    shared_fruit = store.get_game_record(record_id=first_closed.shared_fruit_ref)
    assert shared_fruit is not None
    assert shared_fruit.payload["answer_count"] == 2
    assert shared_fruit.payload["visual_state"] == "MIST_WHITE"
    assert len([
        item
        for item in store._game_records.values()
        if item.record_kind == "shared_fruit"
        and item.round_id == round_definition.round_id
    ]) == 1

    journey = DreamJourneyService(
        case_store=case_store,
        dream_store=store,
        feature_policy=policy,
    )
    reveal_clock = round_definition.outcome_due_at + timedelta(seconds=1)
    revealer = DreamGameService(
        journey=journey,
        store=store,
        clock=lambda: reveal_clock,
    )
    fruit_ids = set()
    for index, (client, user_id, visit_id, sealed) in enumerate(
        zip(clients, user_ids, visits, sealed_attempts),
        start=1,
    ):
        result = revealer.reveal(
            user_id=user_id,
            visit_id=visit_id,
            attempt_id=str(sealed["attempt_id"]),
            idempotency_key=f"shared-reveal-{index}",
            credential=_credential(client),
        )
        assert result.shared_fruit is not None
        fruit_ids.add(result.shared_fruit.fruit_id)
        assert result.shared_fruit.answer_count == 2
        assert result.submission.viewer_id == user_id
    assert fruit_ids == {first_closed.shared_fruit_ref}


def test_owner_close_is_blind_idempotent_and_zero_answers_never_form_a_fruit() -> None:
    clients, store, _, _, user_ids, case_ids = _multi_user_app()
    client = clients[0]
    user_id = user_ids[0]
    visit_id, _ = _enter_three_tree_visit(client, case_ids[0])
    base = f"/api/v50/dream/visits/{visit_id}/game"
    rounds = client.get(f"{base}/rounds").json()
    owner_round = next(
        item
        for item in rounds
        if store.get_game_round(round_id=item["round_id"]).flower_owner_ref == user_id
    )
    started = client.post(
        f"{base}/rounds/{owner_round['round_id']}/start"
    ).json()
    payload = {
        "idempotency_key": "owner-close-empty-flower",
        "confirmed": True,
    }
    closed = client.post(
        f"{base}/attempts/{started['attempt_id']}/flower/close",
        json=payload,
    )
    repeated = client.post(
        f"{base}/attempts/{started['attempt_id']}/flower/close",
        json=payload,
    )
    assert closed.status_code == 200, closed.text
    assert repeated.json() == closed.json()
    flower = closed.json()["flower"]
    assert flower["state"] == "CLOSED_NO_RESPONSE"
    assert flower["answer_count_visible"] is True
    assert flower["answer_count"] == 0
    assert flower["shared_fruit_visible"] is False
    assert "submission" not in closed.text
    assert "selected_outcome_option_id" not in closed.text
    stored = store.get_game_flower(round_id=owner_round["round_id"])
    assert stored is not None
    assert stored.shared_fruit_ref == ""


def test_outcome_cutoff_closes_before_a_late_answer_can_commit() -> None:
    (
        clients,
        store,
        case_store,
        policy,
        user_ids,
        visits,
        bases,
        attempts,
    ) = _start_shared_rounds()
    drafts = [
        _advance_to_draft(client, store, base, attempt)
        for client, base, attempt in zip(clients, bases, attempts)
    ]
    first = clients[0].post(
        f"{bases[0]}/attempts/{drafts[0]['attempt_id']}/judgment/seal",
        json=_seal_payload(drafts[0], key="before-outcome-cutoff"),
    )
    assert first.status_code == 200, first.text
    round_definition = store.get_game_round(round_id=drafts[0]["round_id"])
    assert round_definition is not None and round_definition.outcome_due_at is not None
    journey = DreamJourneyService(
        case_store=case_store,
        dream_store=store,
        feature_policy=policy,
    )
    late_service = DreamGameService(
        journey=journey,
        store=store,
        clock=lambda: round_definition.outcome_due_at + timedelta(seconds=1),
    )
    late_payload = _seal_payload(drafts[1], key="late-after-outcome-cutoff")
    with pytest.raises(DreamGameError, match="dream_game_answer_collection_closed"):
        late_service.seal_judgment(
            user_id=user_ids[1],
            visit_id=visits[1],
            attempt_id=str(drafts[1]["attempt_id"]),
            selected_outcome_option_id=late_payload["selected_outcome_option_id"],
            confidence_basis_points=late_payload["confidence_basis_points"],
            node_refs=late_payload["node_refs"],
            relation_refs=late_payload["relation_refs"],
            interpretation=late_payload["interpretation"],
            strongest_alternative=late_payload["strongest_alternative"],
            disconfirmation_condition=late_payload["disconfirmation_condition"],
            evidence_refs=late_payload["evidence_refs"],
            idempotency_key=late_payload["idempotency_key"],
            confirmed=True,
            credential=_credential(clients[1]),
        )
    flower = store.get_game_flower(round_id=round_definition.round_id)
    assert flower is not None
    assert flower.state == "SHARED_FRUIT_FORMED"
    assert flower.answer_count == 1
    closure = store.get_game_record(record_id=flower.closure_ref)
    assert closure is not None
    assert closure.payload["close_reason"] == "OUTCOME_CUTOFF"


def test_answer_and_close_race_has_one_atomic_authoritative_outcome() -> None:
    (
        clients,
        store,
        case_store,
        policy,
        user_ids,
        visits,
        bases,
        attempts,
    ) = _start_shared_rounds()
    draft = _advance_to_draft(clients[0], store, bases[0], attempts[0])
    round_definition = store.get_game_round(round_id=draft["round_id"])
    assert round_definition is not None
    now = round_definition.published_at + timedelta(seconds=1)
    journey = DreamJourneyService(
        case_store=case_store,
        dream_store=store,
        feature_policy=policy,
    )
    submitter = DreamGameService(journey=journey, store=store, clock=lambda: now)
    closer = DreamGameService(journey=journey, store=store, clock=lambda: now)
    barrier = Barrier(2)
    seal_payload = _seal_payload(draft, key="answer-close-race")

    def submit_answer() -> str:
        barrier.wait()
        try:
            submitter.seal_judgment(
                user_id=user_ids[0],
                visit_id=visits[0],
                attempt_id=str(draft["attempt_id"]),
                selected_outcome_option_id=seal_payload[
                    "selected_outcome_option_id"
                ],
                confidence_basis_points=seal_payload[
                    "confidence_basis_points"
                ],
                node_refs=seal_payload["node_refs"],
                relation_refs=seal_payload["relation_refs"],
                interpretation=seal_payload["interpretation"],
                strongest_alternative=seal_payload["strongest_alternative"],
                disconfirmation_condition=seal_payload[
                    "disconfirmation_condition"
                ],
                evidence_refs=seal_payload["evidence_refs"],
                idempotency_key=seal_payload["idempotency_key"],
                confirmed=True,
                credential=_credential(clients[0]),
            )
        except DreamGameError as exc:
            return str(exc)
        return "sealed"

    def close_answer_collection() -> str:
        barrier.wait()
        return closer._close_flower(
            round_definition=round_definition,
            reason="OWNER_CLOSED",
            trigger_kind="SYSTEM",
            trigger_ref="atomic-race-test",
            idempotency_key="answer-close-race",
        ).state

    with ThreadPoolExecutor(max_workers=2) as executor:
        submit_future = executor.submit(submit_answer)
        close_future = executor.submit(close_answer_collection)
        submit_result = submit_future.result()
        close_state = close_future.result()

    flower = store.get_game_flower(round_id=round_definition.round_id)
    assert flower is not None
    answer_seals = store.list_game_answer_seals(
        round_id=round_definition.round_id
    )
    closure = store.get_game_record(record_id=flower.closure_ref)
    assert closure is not None
    assert closure.payload["answer_seal_refs"] == [
        item.seal_id for item in answer_seals
    ]
    assert closure.payload["answer_count"] == len(answer_seals)
    assert close_state == flower.state
    if submit_result == "sealed":
        assert len(answer_seals) == 1
        assert flower.state == "SHARED_FRUIT_FORMED"
        assert flower.shared_fruit_ref
    else:
        assert submit_result == "dream_game_answer_collection_closed"
        assert answer_seals == []
        assert flower.state == "CLOSED_NO_RESPONSE"
        assert flower.shared_fruit_ref == ""
    shared_fruits = [
        item
        for item in store._game_records.values()
        if item.record_kind == "shared_fruit"
        and item.round_id == round_definition.round_id
    ]
    assert len(shared_fruits) == len(answer_seals)


def test_legacy_single_answer_round_remains_hash_stable_and_is_not_upgraded() -> None:
    clients, store, case_store, policy, _, case_ids = _multi_user_app()
    _enter_three_tree_visit(clients[0], case_ids[0])
    journey = DreamJourneyService(
        case_store=case_store,
        dream_store=store,
        feature_policy=policy,
    )
    grant = next(
        item for item in store.list_grants()
        if item.subject_kind == "canonical_npc"
    )
    pack = load_content_pack()
    slot = pack.slots[0]
    fixed_now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    first, _, _ = compile_simulated_round(
        pack=pack,
        slot=slot,
        grant=grant,
        resident_label="历史单回答样本",
        canvas=journey.truth.canvas(grant),
        now=fixed_now,
    )
    second, _, _ = compile_simulated_round(
        pack=pack,
        slot=slot,
        grant=grant,
        resident_label="历史单回答样本",
        canvas=journey.truth.canvas(grant),
        now=fixed_now,
    )
    assert first.immutable_hash == second.immutable_hash
    assert first.flower_protocol_version == "single-answer-immediate-fruit.v1"

    legacy_payload = first.model_dump(mode="json")
    for field in (
        "source_snapshot",
        "question_set",
        "flower_owner_ref",
        "answer_close_at",
        "outcome_due_at",
    ):
        legacy_payload.pop(field, None)
    restored = BlindRoundDefinition.model_validate(legacy_payload)
    assert restored.immutable_hash == first.immutable_hash
    assert restored.flower_protocol_version == "single-answer-immediate-fruit.v1"
    assert restored.answer_close_at is None
    assert restored.outcome_due_at is None
    store.save_game_round(restored)
    service = DreamGameService(journey=journey, store=store, clock=lambda: fixed_now)
    assert service._refresh_flower(restored) is None
    assert store.get_game_flower(round_id=restored.round_id) is None


def test_no_leak_question_set_keeps_trunk_training_distinct_from_flower_target() -> None:
    _, store, _, _, _, _, _, attempts = _start_shared_rounds()
    round_definition = store.get_game_round(round_id=attempts[0]["round_id"])
    assert round_definition is not None
    assert round_definition.question_set is not None
    trunk = next(
        item
        for item in round_definition.question_set.questions
        if item.kind == "TRUNK_BACKBONE_01"
    )
    assert trunk.target_lens == "five_element"
    assert trunk.evidence_refs
    assert "PathAssertion" not in trunk.prompt
    assert trunk.correct_option_id not in round_definition.question.outcome_options
    assert round_definition.question.question_id != trunk.question_id
