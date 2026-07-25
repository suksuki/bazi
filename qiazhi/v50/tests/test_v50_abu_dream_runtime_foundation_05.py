from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "apps/product/experience_shell/src"
STATIC = ROOT / "apps/product/static/l5"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_story_runtime_separates_business_state_from_presentation_state() -> None:
    contracts = _read(SHELL / "dream_story_contracts.ts")
    reducer = _read(SHELL / "dream_story_reducer.ts")
    director = _read(SHELL / "dream_scene_director.ts")

    for state in (
        "HOME_AWAKE",
        "DREAM_AVAILABLE",
        "DREAM_PORTAL_READY",
        "ENTERING_DREAM",
        "THREE_TREE_SELECTION",
        "ENCOUNTER_COMMITTED",
        "FIXED_TREE_EXPLORATION",
        "FOUNDATION_COMPLETE",
        "BLIND_ROUND_OPEN",
        "JUDGMENT_SUBMITTED",
        "DOUBLE_SEALED",
        "REVEALABLE",
        "REVEAL_COMPLETE",
        "RETURNED_WITH_SEED",
    ):
        assert state in contracts
    assert "DreamPresentationState" in contracts
    assert "animation callback" not in reducer.lower()
    assert "allowedCommands" in director
    assert "assetDependencies" in director


def test_runtime_asset_manifest_is_traceable_to_all_three_library_masters() -> None:
    manifest_path = (
        STATIC / "assets/dream/runtime-foundation-v1/manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["asset_set_id"] == "ABU_DREAM_RUNTIME_FOUNDATION_05"
    assert len(manifest["prototype_masters"]) == 3
    for master in manifest["prototype_masters"]:
        source = ROOT / master["archived_path"]
        assert source.is_file()
        assert _sha256(source) == master["sha256"]
    for asset in manifest["registered_runtime_assets"]:
        if "path" not in asset:
            continue
        delivery = ROOT / asset["path"]
        assert delivery.is_file(), asset["asset_id"]
        assert _sha256(delivery) == asset["sha256"]
    assert manifest["runtime_boundaries"]["pre_seal_fruit_visual"] == "FORBIDDEN"
    assert manifest["runtime_boundaries"]["frontend_selects_mingli_fact"] is False


def test_home_entry_is_the_sleeping_abu_at_the_life_tree_root() -> None:
    home = _read(SHELL / "dream_home_portal.ts")
    components = _read(SHELL / "components.ts")

    assert 'data-command="enter-dream"' in home
    assert "dream-home-abu-portal" in home
    assert 'aria-label="你的生命树"' in home
    assert "renderDreamHomeLifeTree" in components
    assert "dream-entry-card" not in home


def test_three_tree_selection_uses_one_center_commit_and_two_ghost_echoes() -> None:
    tree_world = _read(SHELL / "dream_tree_world.ts")
    runtime = _read(SHELL / "dream_runtime.ts")

    assert "rounds.slice(0, 3)" in tree_world
    assert "is-dream-heart" in tree_world
    assert "is-ghost" in tree_world
    assert "dream-ghost-orbit-veil" in tree_world
    assert "进入这棵树" not in tree_world
    assert "commitFocusedTree" in runtime
    assert "if (next === this.porchIndex)" in runtime
    assert 'type: "FOCUS_CANDIDATE"' in runtime


def test_round_cards_expose_only_anonymous_selection_language() -> None:
    service = _read(ROOT / "apps/product/dream_game_service.py")
    contract = _read(ROOT / "packages/experience/dream_game.py")

    assert "anonymous_label" in contract
    assert "selection_whisper" in contract
    assert 'anonymous_label=f"梦树{index + 1}"' in service
    assert "_selection_whisper(item.event_family)" in service
    assert "outcome_summary" not in service.split(
        "def round_cards",
        1,
    )[1].split(
        "def start_round",
        1,
    )[0]
