from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIRECTOR_ROOT = (
    ROOT
    / "apps/product/static/l5/assets/dream/encounter-01-v1/director-v2"
)


def test_director_assets_match_the_registered_runtime_manifest() -> None:
    manifest = json.loads(
        (DIRECTOR_ROOT / "manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["asset_set_id"] == (
        "DREAM_ENCOUNTER_VISUAL_QA_REBUILD_02_DIRECTOR_V2"
    )
    assert manifest["security_boundaries"]["pre_seal_fruit_visual"] == "FORBIDDEN"
    assert manifest["security_boundaries"]["pre_seal_outcome_data"] == "FORBIDDEN"

    for item in manifest["assets"]:
        path = DIRECTOR_ROOT / item["file"]
        assert path.is_file(), item["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]


def test_fixed_tree_question_map_replaces_the_long_page_journey() -> None:
    tree_world = (
        ROOT / "apps/product/experience_shell/src/dream_tree_world.ts"
    ).read_text(encoding="utf-8")
    asset_registry = (
        ROOT / "apps/product/experience_shell/src/dream_asset_registry.ts"
    ).read_text(encoding="utf-8")
    runtime = (
        ROOT / "apps/product/experience_shell/src/dream_runtime.ts"
    ).read_text(encoding="utf-8")
    styles = (
        ROOT / "apps/product/static/experience/styles.css"
    ).read_text(encoding="utf-8")

    assert "renderDreamTreeQuestionMap" in tree_world
    assert "data-tree-world-mode=\"question-map\"" in tree_world
    assert "data-dream-tree-world-scroll" not in tree_world
    assert "renderDreamTreeJourney" not in runtime
    assert "handleTreeWorldScroll" not in runtime
    assert "height: 100dvh;" in styles
    assert ".dream-question-band" in styles
    assert "max-height: 29%;" in styles
    assert "overflow: hidden;" in styles


def test_fixed_tree_uses_the_approved_scene_and_server_question_map() -> None:
    tree_world = (
        ROOT / "apps/product/experience_shell/src/dream_tree_world.ts"
    ).read_text(encoding="utf-8")
    runtime = (
        ROOT / "apps/product/experience_shell/src/dream_runtime.ts"
    ).read_text(encoding="utf-8")
    styles = (
        ROOT / "apps/product/static/experience/styles.css"
    ).read_text(encoding="utf-8")

    renderer = tree_world.split(
        "export function renderDreamTreeQuestionMap",
        1,
    )[1].split(
        "export function buildDreamTreeQuestions",
        1,
    )[0]

    assert 'data-tree-world-mode="question-map"' in renderer
    assert "dream-question-tree-node" in renderer
    assert "SEMANTIC_TREE_SCENE_BUNDLE" in renderer
    assert 'data-semantic-tree-bundle="${bundle.bundleId}"' in renderer
    assert "renderFlowerOrFruit(view)" in renderer
    assert "renderDreamFixedTreeIdle" not in runtime
    assert "ENABLE_PHASE_B_TREE_QUESTIONS" not in runtime
    deferred = runtime.split(
        "private renderDeferredQuestionLayer",
        1,
    )[1].split("private renderGameStage", 1)[0]
    assert "DREAM_RUNTIME_ASSETS.fixedTreeBud.source" not in deferred
    assert "DREAM_RUNTIME_ASSETS.fixedTreeFlower.source" not in deferred
    assert "DREAM_RUNTIME_ASSETS.porchBlue.source" not in runtime.split(
        "private renderDeferredQuestionLayer",
        1,
    )[1].split("private renderGameStage", 1)[0]
    assert ".dream-question-tree-master" in styles


def test_tree_questions_only_use_the_frozen_pre_outcome_projection() -> None:
    tree_world = (
        ROOT / "apps/product/experience_shell/src/dream_tree_world.ts"
    ).read_text(encoding="utf-8")

    question_builder = tree_world.split(
        "export function buildDreamTreeQuestions",
        1,
    )[1].split(
        "export function treeQuestionForNode",
        1,
    )[0]

    assert "attempt.question_set.questions" in question_builder
    assert "question.options.map" in question_builder
    assert "correctOptionId" not in tree_world
    assert "correct_option_id" not in tree_world
    assert "answer_commitment_hash" not in tree_world
    assert "outcome_evidence" not in question_builder
    assert "system_seal" not in question_builder


def test_question_progress_and_draft_restore_share_the_attempt_namespace() -> None:
    runtime = (
        ROOT / "apps/product/experience_shell/src/dream_runtime.ts"
    ).read_text(encoding="utf-8")

    assert 'TREE_QUESTION_STATE_KEY = "deepbazi.dream.tree-question-map.v1"' in runtime
    assert "treeQuestionStorageKey(attemptId" in runtime
    assert "restoreTreeQuestionState()" in runtime
    assert "persistTreeQuestionState()" in runtime
    assert "judgmentStep" in runtime
    local_state = runtime.split(
        "interface DreamTreeQuestionState",
        1,
    )[1].split("interface DreamGameDraft", 1)[0]
    assert "passedNodes" not in local_state
    assert "answers:" not in local_state
    assert "question_progress.flower_unlocked" in runtime
    assert "answerDreamLearningQuestion(" in runtime
    assert "activeNode" in runtime
    assert '"tree-question"' in runtime
    assert "routeNodeUnlocked" in runtime
    assert 'url.hash.startsWith("#tree-question=")' in runtime
    close_question = runtime.split(
        "private closeTreeQuestion",
        1,
    )[1].split(
        "private stepJudgmentBack",
        1,
    )[0]
    assert close_question.index("this.renderGameLayer();") < close_question.index(
        "history.back();"
    )


def test_fruit_is_created_only_after_the_dual_seal_state() -> None:
    runtime = (
        ROOT / "apps/product/experience_shell/src/dream_runtime.ts"
    ).read_text(encoding="utf-8")
    tree_world = (
        ROOT / "apps/product/experience_shell/src/dream_tree_world.ts"
    ).read_text(encoding="utf-8")
    asset_registry = (
        ROOT / "apps/product/experience_shell/src/dream_asset_registry.ts"
    ).read_text(encoding="utf-8")

    observing = runtime.split(
        'if (attempt.state === "ROUND_OBSERVING") {',
        1,
    )[1].split(
        'if (["QUESTION_FLOWER_OPEN", "OPTIONAL_DIVINATION"].includes(attempt.state)) {',
        1,
    )[0]
    assert "dream-question-tree-fruit" not in observing
    assert 'attempt.state === "OUTCOME_REVEALABLE"' in runtime
    assert 'data-semantic-organ="FRUIT_RESULT"' in tree_world
    assert "bundle.assets.fruitWhite" in tree_world
    assert "DREAM_RUNTIME_ASSETS.fruitForm.source" not in tree_world
    assert "fruit-reveal-reference-clean.mp4" in asset_registry
    assert 'is-${cue.replaceAll("_", "-")}' in tree_world
