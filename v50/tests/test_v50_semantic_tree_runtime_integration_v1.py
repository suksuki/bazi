from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUNDLE_DIR = (
    ROOT
    / "apps/product/static/l5/assets/dream/semantic-tree-visible-v1"
)
REGISTRY = (
    ROOT
    / "apps/product/experience_shell/src/semantic_tree_scene_bundle.ts"
)
TREE_WORLD = ROOT / "apps/product/experience_shell/src/dream_tree_world.ts"
RUNTIME = ROOT / "apps/product/experience_shell/src/dream_runtime.ts"
STYLES = ROOT / "apps/product/static/experience/styles.css"


def test_accepted_bundle_is_present_and_all_25_payload_hashes_match() -> None:
    checksums = _checksum_manifest()

    assert len(checksums) == 25
    for relative_path, expected in checksums.items():
        asset = BUNDLE_DIR / relative_path
        assert asset.is_file(), relative_path
        assert hashlib.sha256(asset.read_bytes()).hexdigest() == expected


def test_runtime_registry_locks_the_owner_accepted_bundle_without_fallback() -> None:
    registry = REGISTRY.read_text(encoding="utf-8")

    assert 'bundleId: "SEMANTIC_TREE_VISIBLE_V1"' in registry
    assert (
        "2bd3f4d277462eec9200622315e2124ddd8e9ed417f12603500dfc9adf777efc"
        in registry
    )
    assert 'publicRoot: ROOT' in registry
    assert 'legacyFallbackAllowed: false' in registry
    assert 'characterPolicy: "PRESERVE_EXISTING_RUNTIME_ABU"' in registry
    for expected in _checksum_manifest().values():
        assert expected in registry


def test_fixed_tree_reads_only_the_semantic_bundle() -> None:
    tree_world = TREE_WORLD.read_text(encoding="utf-8")
    runtime = RUNTIME.read_text(encoding="utf-8")
    renderer = tree_world.split(
        "export function renderDreamTreeQuestionMap",
        1,
    )[1].split(
        "export function buildDreamTreeQuestions",
        1,
    )[0]
    deferred = runtime.split(
        "private renderDeferredQuestionLayer",
        1,
    )[1].split(
        "private renderGameStage",
        1,
    )[0]

    assert "SEMANTIC_TREE_SCENE_BUNDLE" in renderer
    assert "bundle.assets.treeBase.source" in renderer
    assert "bundle.assets.leafBasic01" in tree_world
    assert "bundle.assets.leafBasic02" in tree_world
    assert "bundle.assets.trunkBackbone01" in tree_world
    assert "bundle.assets.flowerBudClosed" in tree_world
    assert "bundle.assets.flowerOpen" in tree_world
    assert "bundle.assets.fruitWhite" in tree_world
    assert "treeSceneSource" not in tree_world
    assert "DREAM_RUNTIME_ASSETS.fixedTreeBud.source" not in deferred
    assert "DREAM_RUNTIME_ASSETS.fixedTreeFlower.source" not in deferred
    assert "DREAM_RUNTIME_ASSETS.fruitForm.source" not in tree_world
    assert "dream-question-tree-root-life" not in renderer
    assert "dream-question-tree-canopy-life" not in renderer
    assert "dream-question-tree-fruit" not in renderer


def test_server_owned_states_drive_flower_energy_and_fruit() -> None:
    tree_world = TREE_WORLD.read_text(encoding="utf-8")
    runtime = RUNTIME.read_text(encoding="utf-8")

    assert "const flowerUnlocked = attempt.question_progress.flower_unlocked;" in runtime
    assert "flowerOpened: flowerUnlocked" in runtime
    assert (
        "fruitVisible: Boolean(attempt.flower?.shared_fruit_visible || this.gameResult)"
        in runtime
    )
    assert "view.flowerUnlocked" in tree_world
    assert "bundle.assets.flowerOpen" in tree_world
    assert "bundle.assets.flowerBudClosed" in tree_world
    assert "if (view.fruitVisible)" in tree_world
    assert 'data-semantic-anchor="FLOWER_BLINDROUND_01"' in tree_world
    assert 'view.flowerUnlocked ? " is-active" : ""' in tree_world
    assert "correct_option_id" not in tree_world
    assert "outcome_evidence" not in tree_world


def test_desktop_and_mobile_share_assets_with_profile_only_anchor_changes() -> None:
    registry = REGISTRY.read_text(encoding="utf-8")
    styles = STYLES.read_text(encoding="utf-8")

    assert "anchorStyle(\"desktop\"" in registry
    assert "anchorStyle(\"mobile\"" in registry
    assert "--semantic-${profile}-left" in registry
    assert "@media (max-width: 720px)" in styles
    assert "top: var(--semantic-mobile-top);" in styles
    assert "left: var(--semantic-mobile-left);" in styles
    assert "object-fit: cover;" in styles
    assert "object-position: center center;" in styles
    assert "animation: none;" in styles


def _checksum_manifest() -> dict[str, str]:
    result: dict[str, str] = {}
    prefix = "SEMANTIC_TREE_VISIBLE_V1/"
    for line in (BUNDLE_DIR / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected, packaged_path = line.split(maxsplit=1)
        assert packaged_path.startswith(prefix)
        result[packaged_path.removeprefix(prefix)] = expected
    return result
