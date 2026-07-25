from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from core.contracts import BirthInputCanonical
from core.life_case import (
    build_baseline_insight,
    commit_baseline_life_case,
    validate_formal_insight,
)
from core.mingli_agent import MingliAgent
from core.mingli_agent.contracts import ChartWorldInstance
from core.mingli_agent.professional_review import (
    professional_projection_payload,
    review_professional_payload,
    review_professional_record,
)
from product.agent_case_store import MemoryAgentCaseStore
from product.agent_command_service import BaselineCaseCommand, BaselineCaseCommandService
from scripts.v50_build_professional_failure_corpus_v1 import build_corpus
from scripts.v50_run_local_gate_04a import run_gate
from tests.test_v50_mingli_agent_refoundation import FakeCognitiveModel, _birth_payload
from tests.test_v50_mingli_reliability_gate import HardFactBaselineModel, _world


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "reports/local-gate-03/20260722-local-gate-03-v1"
CORPUS_PATH = ROOT / "data/validation/fixtures/professional_failure_corpus_v1.json"


class CountingHardFactBaselineModel(HardFactBaselineModel):
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, **kwargs):
        self.calls += 1
        return super().generate(**kwargs)


def _case_source(case: dict[str, object]) -> tuple[dict, ChartWorldInstance]:
    directory = RUN_DIR / str(case["source_directory"])
    payload = json.loads((directory / "raw_model_output.json").read_text(encoding="utf-8"))
    row = json.loads((directory / "stored_case.json").read_text(encoding="utf-8"))
    return payload, ChartWorldInstance.model_validate(row["world"])


def _review_text(text: str, *, world: ChartWorldInstance | None = None):
    return review_professional_payload(
        payload={"first_look": text, "evidence_refs": []},
        world=world or _world("local-gate-04a-text"),
        cognitive_record_ref=f"fixture:{hashlib.sha256(text.encode()).hexdigest()[:12]}",
        created_at="2026-07-22T00:00:00+00:00",
        raw_source_kind="fixture_raw_payload",
    )


def test_failure_corpus_is_reproducible_and_exactly_bound() -> None:
    frozen = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    rebuilt = build_corpus(run_dir=RUN_DIR)

    assert rebuilt == frozen
    assert frozen["case_count"] == 5
    assert frozen["machine_committed_count"] == 5
    assert frozen["human_safe_count"] == 0
    assert frozen["raw_outputs_embedded"] is False
    for case in frozen["cases"]:
        payload, _world_value = _case_source(case)
        for issue in case["issues"]:
            value = payload
            for token in issue["field_path"].split("."):
                value = value[int(token)] if token.isdigit() else value[token]
            assert value[issue["start"]:issue["end"]] == issue["source_text"]
            assert issue["binding_status"] == "exact"


def test_five_false_releases_are_blocked_and_known_issues_are_caught() -> None:
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    for case in corpus["cases"]:
        payload, world = _case_source(case)
        before = hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        bundle = review_professional_payload(
            payload=payload,
            world=world,
            cognitive_record_ref=str(case["case_id"]),
            created_at="2026-07-22T00:00:00+00:00",
            raw_source_kind="fixture_raw_payload",
        )
        after = hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        detected = {item.issue_class for item in bundle.overlay.issues}

        assert bundle.overlay.persistence_status == "persisted"
        assert bundle.overlay.professional_release_status == "blocked"
        assert bundle.overlay.downstream_domains_blocked is True
        assert before == after
        assert bundle.overlay.raw_output_modified is False
        assert bundle.overlay.raw_source_kind == "fixture_raw_payload"
        for expected in case["issues"]:
            assert expected["issue_class"] in detected


@pytest.mark.parametrize(
    ("text", "issue_class"),
    [
        ("辛金生助丁火。", "five_element_relation_error"),
        ("酉午半合火局已经成立。", "invalid_branch_relation"),
        ("原局构成双财生杀（食伤）之局。", "ontology_mechanism_role_conflict"),
    ],
)
def test_known_hard_errors_fail_closed(text: str, issue_class: str) -> None:
    bundle = _review_text(text)

    assert bundle.overlay.professional_release_status == "blocked"
    issue = next(item for item in bundle.overlay.issues if item.issue_class == issue_class)
    assert issue.severity == "hard"
    assert issue.disposition == "hard_block"


@pytest.mark.parametrize(
    "text",
    [
        "乙木生丁火，丁火克辛金。",
        "酉丑半合金局作为结构候选存在。",
        "寅午半合火局作为结构候选存在。",
        "丑中辛金七杀参与，丁火制杀。",
    ],
)
def test_correct_near_neighbors_do_not_hard_fail(text: str) -> None:
    bundle = _review_text(text)

    assert not [item for item in bundle.overlay.issues if item.severity == "hard"]


@pytest.mark.parametrize(
    "text",
    [
        "有人说：“辛金生助丁火。”",
        "辛金是否生助丁火？",
        "如果辛金生助丁火，另一条路径会怎样？",
        "辛金并非生助丁火。",
    ],
)
def test_non_assertive_modalities_are_not_promoted_to_natal_facts(text: str) -> None:
    bundle = _review_text(text)

    assert bundle.overlay.professional_release_status == "passed"
    assert not bundle.overlay.issues


def test_release_status_is_independent_from_persistence_and_commit() -> None:
    world = _world("local-gate-04a-safe")
    record = MingliAgent(FakeCognitiveModel()).first_baseline_reading(
        case_id="local-gate-04a-safe",
        world=world,
    )
    review = review_professional_record(
        record=record,
        world=world,
        persistence_status="persisted",
        created_at="2026-07-22T00:00:00+00:00",
    )
    insight = build_baseline_insight(
        record=record,
        world=world,
        professional_review=review,
    )
    life_case, validation = commit_baseline_life_case(
        insight=insight,
        world=world,
        profile_id=None,
    )

    assert review.overlay.professional_release_status == "passed"
    assert review.overlay.raw_source_kind == "assertion_gate_original_chunks"
    assert insight.persistence_status == "persisted"
    assert insight.status == "draft"
    assert validation.passed is True
    assert life_case.baseline_insight.status == "committed"
    assert life_case.baseline_insight.professional_release_status == "passed"


def test_legacy_committed_without_overlay_is_not_formally_eligible() -> None:
    world = _world("local-gate-04a-legacy")
    record = MingliAgent(FakeCognitiveModel()).first_baseline_reading(
        case_id="local-gate-04a-legacy",
        world=world,
    )
    insight = build_baseline_insight(record=record, world=world).model_copy(update={
        "status": "committed",
        "professional_release_status": "unreviewed",
        "professional_review_overlay": None,
    })
    validation = validate_formal_insight(insight=insight, world=world)

    assert validation.passed is False
    assert "professional_release_not_committable:unreviewed" in validation.errors
    assert "professional_review_overlay_missing" in validation.errors


def test_individual_error_is_suppressed_without_rewriting_valid_assertions() -> None:
    payload = {
        "selected_hypothesis_id": "h1",
        "hypotheses": [
            {
                "hypothesis_id": "h1",
                "status": "primary",
                "confidence": "medium",
                "thesis": "乙木生丁火，丁火克辛金。",
                "success_conditions": ["乙木与丁火均参与结构。"],
                "failure_conditions": [],
                "evidence_refs": [],
            },
            {
                "hypothesis_id": "h2",
                "status": "alternative",
                "confidence": "low",
                "thesis": "辛金生助丁火。",
                "success_conditions": [],
                "failure_conditions": [],
                "evidence_refs": [],
            },
        ],
    }
    original = json.loads(json.dumps(payload, ensure_ascii=False))
    bundle = review_professional_payload(
        payload=payload,
        world=_world("local-gate-04a-partial"),
        cognitive_record_ref="fixture:partial-projection",
        created_at="2026-07-22T00:00:00+00:00",
        raw_source_kind="fixture_raw_payload",
    )
    projection = professional_projection_payload(payload=payload, bundle=bundle)

    assert bundle.overlay.professional_release_status == "partially_blocked"
    assert bundle.overlay.downstream_domains_blocked is False
    assert payload == original
    assert [item["hypothesis_id"] for item in projection["hypotheses"]] == ["h1"]
    assert projection["hypotheses"][0]["thesis"] == original["hypotheses"][0]["thesis"]


def test_domain_error_blocks_only_its_domain() -> None:
    payload = {"career": {"claim": "辛金生助丁火。"}}
    bundle = review_professional_payload(
        payload=payload,
        world=_world("local-gate-04a-domain"),
        cognitive_record_ref="fixture:domain-block",
        created_at="2026-07-22T00:00:00+00:00",
        raw_source_kind="fixture_raw_payload",
    )

    assert bundle.overlay.professional_release_status == "partially_blocked"
    assert bundle.overlay.downstream_domains_blocked is False
    assert [(item.scope, item.scope_ref) for item in bundle.overlay.scope_blocks] == [
        ("domain", "career")
    ]


def test_professionally_blocked_baseline_is_cached_without_model_retry() -> None:
    model = CountingHardFactBaselineModel()
    service = BaselineCaseCommandService(
        agent=MingliAgent(model),
        case_store=MemoryAgentCaseStore(),
    )
    command = BaselineCaseCommand(
        case_id="case.local-gate-04a-cache",
        reading_id="reading.local-gate-04a-cache",
        birth_input=BirthInputCanonical.model_validate(_birth_payload()),
        profile_id=None,
        user_id=None,
        active_mode="member",
    )

    first = service.execute(command)
    second = service.execute(command)

    assert first.committed is False
    assert first.professional_review.overlay.professional_release_status == "blocked"
    assert second.committed is False
    assert second.professional_review.overlay.professional_release_status == "blocked"
    assert second.metrics["cache_hit"] is True
    assert second.metrics["model_calls"] == 0
    assert model.calls == 1


def test_local_gate_04a_replay_is_deterministic(tmp_path: Path) -> None:
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    first = run_gate(output_dir=first_dir)
    second = run_gate(output_dir=second_dir)

    assert first == second
    assert first["status"] == "PASS"
    for filename in (
        "local_gate_04a_summary.json",
        "LOCAL_GATE_04A_ASSERTION_INTEGRITY.md",
        "manifest.sha256.json",
    ):
        assert (first_dir / filename).read_bytes() == (second_dir / filename).read_bytes()
