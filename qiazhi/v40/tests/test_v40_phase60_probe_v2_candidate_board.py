from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import create_app
from v40.contracts.base import SurfaceKey, Topic
from v40.engines import build_native_bazi_runtime
from v40.synthetic import load_synthetic_seeds


def _seed():
    return load_synthetic_seeds("qiazhi/v40/data/synthetic/native_bazi_seeds.json")[0]


def test_phase60_probe_v2_and_candidate_board_are_projected_for_practitioner() -> None:
    seed = _seed()
    runtime = build_native_bazi_runtime(
        request_id="request.phase60.practitioner.001",
        reading_id="reading.phase60.practitioner.001",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.CAREER,
        role_key="practitioner",
    )

    assert any(probe.probe_type == "manifestation" and probe.options for probe in runtime.probes)
    assert any(
        probe.probe_type == "timeline" and probe.target_years and probe.impact_preview
        for probe in runtime.probes
    )

    lens = runtime.surface_bundle.surfaces[SurfaceKey.CALIBRATION]["practitioner_lens"]
    board = lens["candidate_board"]
    candidates = [
        candidate
        for group in board["groups"]
        for candidate in group["candidates"]
    ]

    assert board["version"] == "v40.mingli_candidate_board.v1"
    assert any(group["title"] == "事业断项" for group in board["groups"])
    assert any(candidate["candidate_type"] == "career_branch" for candidate in candidates)
    assert any(candidate["candidate_type"] == "timeline_probe" for candidate in candidates)
    assert all(candidate["impact_preview"] for candidate in candidates)
    assert any(action["label"] == "采为主断" for action in board["actions"])
    assert lens["summary"]["candidate_count"] == len(candidates)


def test_phase60_user_ui_exposes_candidate_board_probe_v2_hooks() -> None:
    html = TestClient(create_app()).get("/v40/ui").text

    for text in [
        "断项池、影响预览和校准动作",
        "采为主断",
        "作为辅助",
        "需要追问",
        "candidate_board",
        "data-probe-options",
        "data-probe-impact",
        "命理师选择需要追问",
    ]:
        assert text in html


def test_phase60_mainline_documentation_is_registered() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE60_PROBE_V2_AND_CANDIDATE_BOARD.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    ui_spec = Path("qiazhi/v40/docs/V40_UI_PRODUCT_FLOW_SPEC.md").read_text(encoding="utf-8")

    assert "Probe V2" in doc
    assert "Mingli Candidate Board" in doc
    assert "SystemAssertionCandidate" in doc
    assert "docs/V40_PHASE60_PROBE_V2_AND_CANDIDATE_BOARD.md" in readme
    assert "SystemAssertionCandidate" in spec
    assert "断项池" in ui_spec
