from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERIENCE = ROOT / "apps" / "product" / "static" / "experience"
SHARED = EXPERIENCE / "shared" / "s0-v12-shared"
THEATER = EXPERIENCE / "internal-tools" / "abu-says-mingli-s0-v12"
XIANGFA = EXPERIENCE / "active" / "xiangfa-generation-v1"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_s0_v11_public_scene_is_anonymous_and_uses_a_versioned_source() -> None:
    source = _load_json(SHARED / "scene-source.json")
    serialized = json.dumps(source, ensure_ascii=False)

    assert source["source_mode"] == "anonymized_public_source_teaching_case"
    assert source["identity_boundary"]["anonymous_in_product"] is True
    assert source["identity_boundary"]["public_figure_name_included"] is False
    assert [slot["pillar"] for slot in source["chart"]["semantic_slots"]] == ["庚辰", "丁亥", "甲戌", "戊辰"]
    assert [stage["pillar"] for stage in source["temporal_stages"]] == ["庚寅", "丙午"]
    for forbidden in ("Bruce", "Lee", "李小龙", "1940", "San Francisco", "旧金山"):
        assert forbidden not in serialized


def test_s0_v11_scene_relations_are_exactly_bound_to_the_visual_experience() -> None:
    source = _load_json(SHARED / "scene-source.json")
    manifest = _load_json(SHARED / "manifest.json")
    expected = {
        "relation-jia-generates-ding",
        "relation-ding-controls-geng",
        "relation-year-chen-clashes-day-xu",
        "relation-hour-chen-clashes-day-xu",
        "relation-luck-geng-controls-jia",
        "relation-luck-yin-roots-jia",
        "relation-year-bing-supports-ding",
    }

    assert source["observed_natal_path"]["path_ref"] == "path-observed-jia-ding-geng"
    assert set(manifest["allowed_relation_refs"]) == expected
    assert set(source["observed_natal_path"]["relation_refs"]) <= expected
    assert {item["relation_ref"] for item in source["structural_tensions"]} <= expected
    assert {ref for stage in source["temporal_stages"] for ref in stage["relation_refs"]} <= expected


def test_s0_v11_theater_is_a_timed_scene_not_a_static_slideshow() -> None:
    html = (THEATER / "index.html").read_text(encoding="utf-8")
    script = (THEATER / "app.js").read_text(encoding="utf-8")
    styles = (THEATER / "styles.css").read_text(encoding="utf-8")

    assert "s0-v11-eric-mix.wav" in html
    assert "data-stage-button=\"original\"" in html
    assert "data-stage-button=\"luck\"" in html
    assert "data-stage-button=\"year\"" in html
    assert "window.setTheaterTime" in script
    assert 'id: "morph"' in script
    assert 'id: "finale"' in script
    assert ".theater.capture .topbar" in styles
    assert "abu_taoist_divination" not in html + script


def test_xiangfa_v1_uses_one_scene_with_three_modes_and_bound_hotspots() -> None:
    html = (XIANGFA / "index.html").read_text(encoding="utf-8")
    script = (XIANGFA / "app.js").read_text(encoding="utf-8")
    styles = (XIANGFA / "styles.css").read_text(encoding="utf-8")

    assert "xiangfa-anonymous-case-wide-v1.png" in html
    assert "xiangfa-anonymous-case-portrait-v1.png" in html
    assert html.count("data-mode-button=") == 3
    assert html.count("data-stage-button=") == 3
    for semantic_ref in (
        "node-stem-day-jia",
        "node-stem-month-ding",
        "node-stem-year-geng",
        "path-observed-jia-ding-geng",
        "current-time-effect",
    ):
        assert f'data-semantic-ref="{semantic_ref}"' in html
        assert semantic_ref in script
    assert 'data-mode="xiangfa"' in html
    assert ".portrait-overlay" in styles
    assert ".inspector.is-closed" in styles
    assert 'pageParams.get("embed") === "theater"' in script
    assert "deepbazi:xiangfa-ready" in script
    assert "deepbazi:xiangfa-engaged" in script
    assert "deepbazi:xiangfa-activity" in script
    assert '"pointermove", "mousemove", "pointerover", "wheel", "touchmove", "pointerdown", "touchstart", "keydown"' in script
    assert 'window.addEventListener("focus", notifyTheaterActivity)' in script
    assert 'app.js?v=20260720-abu-wake1' in html
    assert "deepbazi:xiangfa-state" in script
    assert '.xiangfa[data-embed="theater"] .header' in styles
    assert "abu-says-mingli-s0-v12" in html
    assert 'id="interactionHint"' in html
    assert "轻触光点查看" in html
    assert "hotspotBreathe" in styles
    assert "hintRing" in styles
    assert 'interactionHint.classList.add("is-dismissed")' in script


def test_public_static_tree_does_not_contain_internal_source_provenance() -> None:
    public_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for directory in (SHARED, THEATER, XIANGFA)
        for path in directory.rglob("*")
        if path.is_file() and path.suffix in {".html", ".css", ".js", ".json"}
    )
    assert "INTERNAL_SOURCE_PROVENANCE" not in public_text
    assert "brucelee.com" not in public_text
    assert "astro.com" not in public_text
