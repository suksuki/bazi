from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json

from test_v50_dream_bridge_01 import (
    _activate_dream_control,
    _dream_app,
    _enter_three_tree_visit,
    _visit_request,
)

from product.dream_game_content import audit_content_pack, load_content_pack


def _start_round():
    client, other, store, case_store, user_id, home_case_id = _dream_app()
    visit_id, _ = _enter_three_tree_visit(client, home_case_id)
    base = f"/api/v50/dream/visits/{visit_id}/game"
    rounds = client.get(f"{base}/rounds")
    assert rounds.status_code == 200, rounds.text
    started = client.post(f"{base}/rounds/{rounds.json()[0]['round_id']}/start")
    assert started.status_code == 200, started.text
    return (
        client,
        other,
        store,
        case_store,
        user_id,
        home_case_id,
        visit_id,
        base,
        started.json(),
    )


def _answer_learning_questions(client, store, base: str, attempt: dict[str, object]):
    attempt_id = attempt["attempt_id"]
    round_definition = store.get_game_round(round_id=attempt["round_id"])
    assert round_definition is not None
    assert round_definition.question_set is not None
    current = attempt
    for index, question in enumerate(round_definition.question_set.questions):
        answered = client.post(
            f"{base}/attempts/{attempt_id}/learning/{question.question_id}/answer",
            json={
                "option_id": question.correct_option_id,
                "idempotency_key": f"learning-answer-{index:02d}",
            },
        )
        assert answered.status_code == 200, answered.text
        current = answered.json()
    assert current["question_progress"]["flower_unlocked"] is True
    return current


def _advance_to_draft(client, store, base: str, attempt: dict[str, object]):
    attempt_id = attempt["attempt_id"]
    observed = client.post(f"{base}/attempts/{attempt_id}/lenses/overview")
    assert observed.status_code == 200, observed.text
    _answer_learning_questions(client, store, base, attempt)
    flower = client.post(f"{base}/attempts/{attempt_id}/question/open")
    assert flower.status_code == 200, flower.text
    draft = client.post(f"{base}/attempts/{attempt_id}/judgment/start")
    assert draft.status_code == 200, draft.text
    return draft.json()


def _seal_payload(attempt: dict[str, object], *, key: str = "seal-idempotency-001"):
    projection = attempt["projection"]
    nodes = [item["node_ref"] for item in projection["allowed_nodes"][:2]]
    relations = [item["relation_ref"] for item in projection["allowed_relations"][:1]]
    return {
        "selected_outcome_option_id": "yes",
        "confidence_basis_points": 6400,
        "node_refs": nodes,
        "relation_refs": relations,
        "interpretation": "这是玩家提出的候选解释，不是正式做功路径。",
        "evidence_refs": [*nodes, *relations],
        "strongest_alternative": "事件可能只停留在准备阶段。",
        "disconfirmation_condition": "结果窗口内没有正式完成证据。",
        "idempotency_key": key,
        "confirmed": True,
    }


def test_simulated_pack_is_publishable_but_can_never_count_as_verified_real() -> None:
    pack = load_content_pack()
    audit = audit_content_pack(pack)

    assert audit.passed is True
    assert audit.resulting_state == "PUBLISHABLE"
    assert pack.evidence_class == "SIMULATED"
    assert pack.development_only is True
    assert pack.release_eligible is False
    assert pack.verified_real_gate_contribution == 0
    assert len(pack.slots) == 3


def test_content_gate_uses_three_v50_snapshots_but_real_launch_stays_zero_of_three() -> None:
    client, _, _, _, _, home_case_id = _dream_app()
    visit_id, _ = _enter_three_tree_visit(client, home_case_id)
    base = f"/api/v50/dream/visits/{visit_id}/game"

    gate = client.get(f"{base}/content-gate")
    rounds = client.get(f"{base}/rounds")

    assert gate.status_code == 200
    assert gate.json()["verified_real_content_gate"] == "0/3"
    assert gate.json()["verified_real_launch"] == "LOCKED"
    assert gate.json()["development_content"] == "V50_CANONICAL_ONLY"
    assert gate.json()["simulated_round_count"] == 0
    assert gate.json()["v50_canonical_round_count"] == 3
    assert len(rounds.json()) == 3
    assert all(item["evidence_class"] == "V50_CANONICAL" for item in rounds.json())
    assert all(item["development_only"] is False for item in rounds.json())
    assert all(
        item["banner"] == "V50结构验证场｜正式命盘快照｜不计入真人果实"
        for item in rounds.json()
    )


def test_pre_outcome_api_never_contains_outcome_or_system_seal_material() -> None:
    client, _, _, _, _, _, _, base, started = _start_round()
    attempt_id = started["attempt_id"]
    payloads = [
        started,
        client.get(f"{base}/attempts/{attempt_id}").json(),
        client.post(f"{base}/attempts/{attempt_id}/lenses/overview").json(),
    ]
    serialized = json.dumps(payloads, ensure_ascii=False)

    for forbidden in (
        "correct_option_id",
        "answer_commitment_hash",
        "snapshot_payload",
        "simulated_outcome_summary",
        "outcome_evidence",
        "system_judgment_seal",
        "正式到岗确认",
        "岗位调动记录",
    ):
        assert forbidden not in serialized
    assert all(item["flower_question"] is None for item in payloads)

    before = client.get(f"{base}/attempts/{attempt_id}/result")
    assert before.status_code == 422
    assert before.json()["detail"] == "dream_game_outcome_not_revealed"


def test_real_dream_flower_is_one_click_sealed_and_restored_from_topic_exploration() -> None:
    (
        client,
        _,
        _,
        _,
        _,
        _,
        visit_id,
        base,
        started,
    ) = _start_round()
    round_id = started["round_id"]
    url = f"{base}/rounds/{round_id}/reality-question"

    initial = client.get(url)
    assert initial.status_code == 200, initial.text
    payload = initial.json()
    assert payload["available"] is True
    assert payload["sealed"] is False
    assert payload["fruit_state"] == "FLOWER_OPEN"
    assert payload["question"]["blueprint_id"] == "LQ-REAL-OUTPUT-DESTINATION-01"
    assert payload["question"]["prompt"] == "这份成果最先带来的现实反馈会是什么？"
    assert payload["write_owner"] == "TopicExploration"
    assert payload["writes_life_case"] is False
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    for forbidden in (
        "correct_answer",
        "answer_key",
        "outcome_evidence",
        "future_evidence",
        "evidence_criteria",
    ):
        assert forbidden not in serialized

    option = payload["question"]["options"][0]
    request = {
        "question_instance_id": payload["question"]["question_instance_id"],
        "option_id": option["option_id"],
        "idempotency_key": "dream-real-one-click-001",
    }
    sealed = client.post(f"{url}/answer", json=request)
    assert sealed.status_code == 200, sealed.text
    assert sealed.json()["sealed"] is True
    assert sealed.json()["selected_option_id"] == option["option_id"]
    assert sealed.json()["reveal_status"] == "WAITING_REALITY_EVIDENCE"
    assert sealed.json()["fruit_state"] == "PENDING_REALITY_EVIDENCE"

    repeated = client.post(f"{url}/answer", json=request)
    assert repeated.status_code == 200
    assert repeated.json() == sealed.json()
    restored = client.get(url)
    assert restored.status_code == 200
    assert restored.json() == sealed.json()

    conflict = client.post(
        f"{url}/answer",
        json={
            **request,
            "option_id": payload["question"]["options"][1]["option_id"],
            "idempotency_key": "dream-real-one-click-conflict",
        },
    )
    assert conflict.status_code == 409
    assert client.get(
        f"/api/v50/dream/visits/{visit_id}/game/rounds"
    ).status_code == 200


def test_learning_answers_are_server_authoritative_idempotent_and_restorable() -> None:
    client, _, store, _, _, _, _, base, started = _start_round()
    attempt_id = started["attempt_id"]
    round_definition = store.get_game_round(round_id=started["round_id"])
    assert round_definition is not None and round_definition.question_set is not None
    first, second, trunk = round_definition.question_set.questions
    wrong_option = next(
        item.option_id for item in first.options
        if item.option_id != first.correct_option_id
    )

    wrong = client.post(
        f"{base}/attempts/{attempt_id}/learning/{first.question_id}/answer",
        json={"option_id": wrong_option, "idempotency_key": "learning-wrong-001"},
    )
    repeated_wrong = client.post(
        f"{base}/attempts/{attempt_id}/learning/{first.question_id}/answer",
        json={"option_id": wrong_option, "idempotency_key": "learning-wrong-001"},
    )
    assert wrong.status_code == 200, wrong.text
    assert repeated_wrong.json() == wrong.json()
    first_progress = wrong.json()["question_progress"]["items"][0]
    assert first_progress["status"] == "RETRY_REQUIRED"
    assert first_progress["attempts"] == 1
    assert first_progress["resolved_answer_ref"] == ""
    assert first_progress["resolved_evidence_refs"] == []

    for index, question in enumerate((first, second)):
        answered = client.post(
            f"{base}/attempts/{attempt_id}/learning/{question.question_id}/answer",
            json={
                "option_id": question.correct_option_id,
                "idempotency_key": f"learning-correct-{index:02d}",
            },
        )
        assert answered.status_code == 200, answered.text
    restored = client.get(f"{base}/attempts/{attempt_id}")
    assert restored.status_code == 200, restored.text
    assert [item["status"] for item in restored.json()["question_progress"]["items"]] == [
        "COMPLETED",
        "COMPLETED",
        "NOT_STARTED",
    ]
    assert restored.json()["question_set"]["questions"][2]["available"] is True
    assert restored.json()["question_progress"]["flower_unlocked"] is False

    completed = client.post(
        f"{base}/attempts/{attempt_id}/learning/{trunk.question_id}/answer",
        json={
            "option_id": trunk.correct_option_id,
            "idempotency_key": "learning-correct-trunk",
        },
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["question_progress"]["flower_unlocked"] is True
    refreshed = client.get(f"{base}/attempts/{attempt_id}")
    assert refreshed.json()["question_progress"] == completed.json()["question_progress"]


def test_cutoff_snapshot_is_immutable_and_later_case_write_fails_closed() -> None:
    client, _, store, case_store, _, _, _, base, started = _start_round()
    round_before = store.get_game_round(round_id=started["round_id"])
    assert round_before is not None
    assert round_before.source_snapshot is not None
    assert round_before.question_set is not None
    assert (
        round_before.source_snapshot.cutoff_verification_status
        == "VERIFIED_AS_OF_SOURCE_VERSION"
    )
    snapshot_hash = round_before.source_snapshot.snapshot_hash
    question_hash = round_before.question_set.immutable_hash
    grant = store.get_grant(
        public_scene_ref=round_before.resident_scene_ref,
    )
    assert grant is not None
    changed = deepcopy(case_store.get(case_id=grant.case_id, user_id=None))
    assert changed is not None
    changed["world"]["timing_context"]["analysis_year"] = 2025
    changed["world"]["timing_context"]["annual_pillar"] = "乙巳"
    case_store.save(
        case_id=grant.case_id,
        user_id=None,
        profile_id=None,
        payload=changed,
    )

    rejected = client.get(f"{base}/attempts/{started['attempt_id']}")
    assert rejected.status_code == 422
    assert rejected.json()["detail"] == "dream_scene_source_version_changed"
    round_after = store.get_game_round(round_id=started["round_id"])
    assert round_after is not None
    assert round_after.source_snapshot is not None
    assert round_after.question_set is not None
    assert round_after.source_snapshot.snapshot_hash == snapshot_hash
    assert round_after.question_set.immutable_hash == question_hash


def test_expired_projection_envelope_is_safely_reissued_without_changing_frozen_content() -> None:
    client, _, store, _, user_id, _, _, base, started = _start_round()
    attempt_id = started["attempt_id"]
    current = store.get_game_attempt(attempt_id=attempt_id, viewer_id=user_id)
    assert current is not None
    original_projection_ref = current.projection.projection_ref
    original_viewer_hash = current.projection.viewer_projection_hash
    expired = current.model_copy(update={
        "projection": current.projection.model_copy(update={
            "expires_at": datetime.now(timezone.utc) - timedelta(seconds=1),
        }),
        "updated_at": datetime.now(timezone.utc),
        "row_version": current.row_version + 1,
    })
    store.update_game_attempt(expired, expected_row_version=current.row_version)

    resumed = client.get(f"{base}/attempts/{attempt_id}")
    observed = client.post(f"{base}/attempts/{attempt_id}/lenses/overview")

    assert resumed.status_code == 200, resumed.text
    assert observed.status_code == 200, observed.text
    renewed_projection = resumed.json()["projection"]
    assert renewed_projection["projection_ref"] != original_projection_ref
    assert renewed_projection["viewer_projection_hash"] == original_viewer_hash
    assert datetime.fromisoformat(
        renewed_projection["expires_at"].replace("Z", "+00:00")
    ) > datetime.now(timezone.utc)


def test_problem_flower_requires_server_progress_and_v50_round_does_not_fake_liuyao() -> None:
    client, _, store, _, _, _, _, base, started = _start_round()
    attempt_id = started["attempt_id"]
    client.post(f"{base}/attempts/{attempt_id}/lenses/overview")
    early = client.post(f"{base}/attempts/{attempt_id}/question/open")
    assert early.status_code == 422
    assert early.json()["detail"] == "dream_game_flower_prerequisites_incomplete"
    _answer_learning_questions(client, store, base, started)
    opened = client.post(f"{base}/attempts/{attempt_id}/question/open")

    assert opened.status_code == 200
    assert opened.json()["divination"] is None
    assert opened.json()["flower_question"]["liuyao_permitted"] is False
    denied = client.post(
        f"{base}/attempts/{attempt_id}/divination",
        json={"explicit_user_intent": False, "idempotency_key": "cast-denied-001"},
    )
    assert denied.status_code == 422
    cast = client.post(
        f"{base}/attempts/{attempt_id}/divination",
        json={"explicit_user_intent": True, "idempotency_key": "cast-allowed-001"},
    )
    assert cast.status_code == 422
    assert cast.json()["detail"] == "dream_game_divination_not_permitted"


def test_first_answer_stays_in_the_open_flower_and_keeps_authority_neutral() -> None:
    client, _, store, case_store, user_id, home_case_id, _, base, started = _start_round()
    before_case = deepcopy(case_store.get(case_id=home_case_id, user_id=user_id))
    draft = _advance_to_draft(client, store, base, started)
    attempt_id = draft["attempt_id"]
    payload = _seal_payload(draft)

    sealed = client.post(f"{base}/attempts/{attempt_id}/judgment/seal", json=payload)
    repeated = client.post(f"{base}/attempts/{attempt_id}/judgment/seal", json=payload)
    assert sealed.status_code == 200, sealed.text
    assert sealed.json()["state"] == "USER_JUDGMENT_SEALED"
    assert repeated.json() == sealed.json()
    assert sealed.json()["flower"]["state"] == "OPEN"
    assert sealed.json()["flower"]["shared_fruit_visible"] is False
    assert sealed.json()["revealable"] is False

    early_reveal = client.post(
        f"{base}/attempts/{attempt_id}/reveal",
        json={"idempotency_key": "reveal-idempotency-001"},
    )
    assert early_reveal.status_code == 409
    assert early_reveal.json()["detail"] == "dream_game_outcome_not_revealable"
    submission = store.find_game_record(
        round_id=draft["round_id"],
        viewer_id=user_id,
        record_kind="judgment_submission",
    )
    assert submission is not None
    assert (
        submission.payload["user_path_hypothesis"]["formal_status"]
        == "USER_HYPOTHESIS_ONLY"
    )
    assert case_store.get(case_id=home_case_id, user_id=user_id) == before_case


def test_revoked_pack_fails_closed_without_exposing_outcome() -> None:
    client, _, store, _, _, _, _, base, started = _start_round()
    draft = _advance_to_draft(client, store, base, started)
    attempt_id = draft["attempt_id"]
    sealed = client.post(
        f"{base}/attempts/{attempt_id}/judgment/seal",
        json=_seal_payload(draft),
    )
    assert sealed.status_code == 200
    round_definition = store.get_game_round(round_id=draft["round_id"])
    assert round_definition is not None
    from datetime import datetime, timezone
    store.revoke_game_content_pack(
        pack_id=round_definition.pack_id,
        revoked_at=datetime.now(timezone.utc),
    )

    revealed = client.post(
        f"{base}/attempts/{attempt_id}/reveal",
        json={"idempotency_key": "reveal-after-revoke"},
    )
    assert revealed.status_code == 409
    assert revealed.json()["detail"] == "dream_game_content_revoked"
    assert "outcome" not in revealed.text.lower()


def test_stale_control_lease_cannot_write_game_state() -> None:
    client, _, _, _, _, home_case_id = _dream_app()
    visit_id, _ = _enter_three_tree_visit(client, home_case_id)
    stale_headers = dict(client.headers)
    takeover = client.post(
        f"/api/v50/dream/visits/{visit_id}/control/takeover",
        json={"client_instance_id": "dream-second-tab-client"},
    )
    assert takeover.status_code == 200
    _activate_dream_control(client, takeover.json())

    stale = client.get(
        f"/api/v50/dream/visits/{visit_id}/game/rounds",
        headers=stale_headers,
    )
    assert stale.status_code == 409
    assert stale.json()["detail"] == "dream_control_lease_superseded"


def test_schema_contains_isolated_dream_game_authority_tables() -> None:
    from product.database_schema import EXPECTED_SCHEMA_VERSION, SCHEMA_PATH

    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    assert EXPECTED_SCHEMA_VERSION == "v50.consolidated.006"
    assert "CREATE TABLE IF NOT EXISTS v50_dream_game_content_packs" in schema
    assert "CREATE TABLE IF NOT EXISTS v50_dream_game_rounds" in schema
    assert "CREATE TABLE IF NOT EXISTS v50_dream_game_system_seals" in schema
    assert "CREATE TABLE IF NOT EXISTS v50_dream_game_outcome_evidence" in schema
    assert "CREATE TABLE IF NOT EXISTS v50_dream_game_attempts" in schema
    assert "CREATE TABLE IF NOT EXISTS v50_dream_game_flowers" in schema
    assert "CREATE TABLE IF NOT EXISTS v50_dream_game_records" in schema
    assert "CREATE TABLE IF NOT EXISTS v50_dream_game_answers" in schema


def test_problem_flower_pointer_is_not_claimed_by_forest_movement() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    source = (
        root / "apps/product/experience_shell/src/dream_runtime.ts"
    ).read_text(encoding="utf-8")

    pointer_guard = (
        '"button, a, input, textarea, select, [role=\'button\'], '
        '[data-dream-game-round], [data-dream-game-command], [data-dream-a11y]"'
    )
    handler = source.split("private handlePointerDown", 1)[1].split(
        "private handlePointerMove", 1
    )[0]
    assert pointer_guard in handler
    assert handler.index(pointer_guard) < handler.index('if (this.phase === "fog_wait")')


def test_return_visit_resumes_pending_idempotent_game_action_before_exit() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "apps/product/experience_shell/src/dream_runtime.ts"
    ).read_text(encoding="utf-8")
    return_branch = source.split(
        'if (this.visit.is_return_visit || this.visit.runtime_state === "LOCAL_MIST_REENTRY") {',
        1,
    )[1].split("return;", 1)[0]

    assert "await this.resumeGameFromRoute();" in return_branch
    assert "await this.resumePendingGameAction();" in return_branch


def test_reentering_a_completed_tree_restores_the_reveal_instead_of_reobserving() -> None:
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "apps/product/experience_shell/src/dream_runtime.ts"
    ).read_text(encoding="utf-8")
    open_round = source.split(
        "private async openProblemRound",
        1,
    )[1].split(
        "private async resumeGameFromRoute",
        1,
    )[0]

    assert '["KNOWLEDGE_SEED_ISSUED", "ROUND_COMPLETE"]' in open_round
    assert "loadDreamGameResult(" in open_round
    assert 'this.gameAttempt.state === "ROUND_OBSERVING"' in open_round
    assert "!this.gameAttempt.observed_lenses.includes(this.gameLens)" in open_round
    assert "this.restoreTreeQuestionState();" in open_round


def test_tree_world_shell_uses_three_rounds_and_one_fixed_question_tree() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    tree_world = (
        root / "apps/product/experience_shell/src/dream_tree_world.ts"
    ).read_text(encoding="utf-8")
    asset_registry = (
        root / "apps/product/experience_shell/src/dream_asset_registry.ts"
    ).read_text(encoding="utf-8")
    runtime = (
        root / "apps/product/experience_shell/src/dream_runtime.ts"
    ).read_text(encoding="utf-8")

    assert "rounds.slice(0, 3)" in tree_world
    assert "is-own-tree" not in tree_world
    for node_id in (
        "leaf_structure",
        "leaf_support",
        "branch_path",
        "problem_flower",
    ):
        assert f'"{node_id}"' in tree_world
    for lens in (
        "overview",
        "five_element",
        "combination_conflict",
        "roots_reveal",
        "timing",
        "work_path",
    ):
        assert f"{lens}:" in tree_world
    assert "DREAM_RUNTIME_ASSETS" in tree_world
    for director_asset in (
        "abu_03_dream_entry_transition_v1_runtime_1080p.mp4",
        "tree-enter-clean.mp4",
        "fruit-reveal-reference-clean.mp4",
        "grove-clean-approved-v5-e97ec6b5.png",
        "tree-blue-actor-v5-08170159.png",
        "tree-jade-actor-v5-9541d056.png",
        "tree-amber-actor-v5-1f98142a.png",
        "tree-question-map-full-preseal.png",
        "tree-flower-open-preseal.png",
    ):
        assert director_asset in asset_registry
    assert "abu_01_seated_idle_loop_v3.webm" in asset_registry
    assert "abu_01_seated_idle_loop_v3.png" in asset_registry
    assert "data-dream-tree-world-scroll" not in tree_world
    assert "data-tree-journey-anchor" not in tree_world
    assert "renderDreamTreeQuestionMap" in tree_world
    assert "buildDreamTreeQuestions" in tree_world
    assert "renderDreamTreePorch" in runtime
    assert "renderDreamRealityTree" in runtime
    assert "renderDreamTreeQuestionMap" not in runtime
    assert "renderDreamTreeJourney" not in runtime
    assert "handleTreeWorldScroll" not in runtime
    assert 'main.classList.toggle("is-tree-world-active", this.gameShellOpen)' in runtime
    assert 'commandTarget?.closest<HTMLElement>(".dream-tree-porch-tree")' in runtime
    assert "suppressNextPorchSelection" in runtime
    assert "treeIndex: porchTree?.dataset.porchIndex" in runtime
    assert "this.focusPorchIndex(pointer.treeIndex);" in runtime
    assert 'source_kind !== "authorized_human"' not in runtime
    assert "return `匿名梦境居民" in runtime
    assert "${round.resident_label}的问题花" not in runtime


def test_tree_world_keeps_fruit_and_reveal_behind_the_dual_seal_state() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    runtime = (
        root / "apps/product/experience_shell/src/dream_runtime.ts"
    ).read_text(encoding="utf-8")
    tree_world = (
        root / "apps/product/experience_shell/src/dream_tree_world.ts"
    ).read_text(encoding="utf-8")

    observing = runtime.split(
        'if (attempt.state === "ROUND_OBSERVING") {',
        1,
    )[1].split(
        'if (["QUESTION_FLOWER_OPEN", "OPTIONAL_DIVINATION"].includes(attempt.state)) {',
        1,
    )[0]
    revealable = runtime.split(
        "if (flower.revealable && attempt.sealed) {",
        1,
    )[1].split(
        'if (attempt.state === "OUTCOME_REVEALABLE") {',
        1,
    )[0]

    assert "dream-game-fruit" not in observing
    assert "雾白果实可以打开" in revealable
    assert "你的判断已经封入花心" in runtime
    assert "flower.neutral_message" in runtime
    assert 'if (flowerChanged) {' in runtime
    assert 'this.gameStatusMessage = next.flower?.neutral_message || "";' in runtime
    assert "this.gameReality = await answerDreamRealityQuestion(" in runtime
    assert 'this.gameStatusMessage = "已封存，待现实证据出现后揭晓。";' in runtime
    assert "const organ = sealed" in tree_world
    assert "? bundle.assets.fruitWhite" in tree_world
    assert "data-fruit-state=" in tree_world
    assert "if (view.fruitVisible)" in tree_world
    assert 'data-semantic-organ="FRUIT_RESULT"' in tree_world
    assert "bundle.assets.fruitWhite" in tree_world
    assert "outcome_evidence" not in tree_world
    assert 'gameRevealAct: DreamTreeRevealAct = "user"' in runtime
    assert '["user", "system", "evidence", "seed"]' in runtime


def test_tree_world_keeps_onecanvas_and_departure_on_existing_owners() -> None:
    from pathlib import Path

    runtime = (
        Path(__file__).resolve().parents[1]
        / "apps/product/experience_shell/src/dream_runtime.ts"
    ).read_text(encoding="utf-8")

    assert "renderDreamGameCanvas(" not in runtime
    assert "renderDreamVerificationCanvas(" in runtime
    assert "observeDreamGameLens(" in runtime
    assert 'await this.departDream("SEMANTIC_EXIT")' in runtime
    assert "commitDreamDeparture(" in runtime
    assert runtime.count("class DreamFirstVisitRuntime") == 1
    assert "gameEvidenceDisplayLabel" in runtime
    assert "knowledge_seed.observation_kept.map((item) => `<span>${escapeHtml(item)" not in runtime
    return_to_porch = runtime.split(
        "private async returnToTreePorch",
        1,
    )[1].split(
        "private async closeGameLayer",
        1,
    )[0]
    close_game = runtime.split(
        "private async closeGameLayer",
        1,
    )[1].split(
        "private openGameHistory",
        1,
    )[0]
    assert "history.back()" not in return_to_porch
    assert "history.back()" not in close_game
    assert 'url.searchParams.delete("dreamGameAttempt")' in return_to_porch
    assert 'url.searchParams.delete("dreamGameAttempt")' in close_game


def test_reveal_copy_scrolls_without_covering_the_final_actions() -> None:
    from pathlib import Path

    styles = (
        Path(__file__).resolve().parents[1]
        / "apps/product/static/experience/styles.css"
    ).read_text(encoding="utf-8")

    reveal = styles.split(".dream-tree-reveal {", 1)[1].split("}", 1)[0]
    stage = styles.split(".dream-tree-reveal-stage {", 1)[1].split("}", 1)[0]
    act = styles.split(".dream-tree-reveal-act {", 1)[1].split("}", 1)[0]
    actions = styles.split(
        ".dream-tree-reveal > .dream-game-actions {",
        1,
    )[1].split("}", 1)[0]

    assert "display: flex;" in reveal
    assert "flex-direction: column;" in reveal
    assert "overflow: hidden;" in reveal
    assert "flex: 1 1 auto;" in stage
    assert "overflow: hidden;" in stage
    assert "height: 100%;" in act
    assert "overflow: auto;" in act
    assert "position: relative;" in actions
    assert "z-index: 1;" in actions


def test_dream_store_bounds_long_lived_visit_audit_window() -> None:
    from product.dream_store_contracts import normalize_dream_visit

    client, _, store, _, user_id, home_case_id = _dream_app()
    visit_id, _ = _enter_three_tree_visit(client, home_case_id)
    visit = store.get_visit(visit_id=visit_id, owner_user_id=user_id)
    assert visit is not None and visit.audit_events

    overflow = visit.model_copy(update={"audit_events": [visit.audit_events[-1]] * 129})
    normalized = normalize_dream_visit(overflow)

    assert len(normalized.audit_events) == 128
