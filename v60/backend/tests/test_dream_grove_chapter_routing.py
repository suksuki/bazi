from __future__ import annotations

from dataclasses import dataclass

import pytest
from abu_v60.dream.catalog import ActiveEpisodeCatalog
from abu_v60.dream.errors import DreamStateError
from abu_v60.dream.first_slice import first_episode_contract
from abu_v60.dream.grove import GroveCandidateDefinition
from abu_v60.dream.grove_chapter_routing import DreamGroveChapterRouter
from abu_v60.dream.return_slice import return_episode_contract
from abu_v60.game import DreamEpisodeContract
from abu_v60.provenance import content_hash
from abu_v60.story import EpisodeTransitionContract, episode_transition


@dataclass(frozen=True, slots=True)
class _SyntheticChain:
    root: DreamEpisodeContract
    continuation: DreamEpisodeContract
    transition: EpisodeTransitionContract


class _HistoryResult:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self._rows = rows

    def mappings(self) -> _HistoryResult:
        return self

    def all(self) -> list[dict[str, object]]:
        return self._rows


class _HistoryConnection:
    """Minimal completed-history adapter preserving the router's SQL filters."""

    def __init__(self, rows: list[dict[str, object]]) -> None:
        self._rows = rows
        self.filters: list[tuple[str, str, str]] = []

    def execute(
        self,
        statement: object,
        parameters: dict[str, object],
    ) -> _HistoryResult:
        assert "FROM dream.encounters" in str(statement)
        filter_key = (
            str(parameters["account_ref"]),
            str(parameters["actor_ref"]),
            str(parameters["tree_ref"]),
        )
        self.filters.append(filter_key)
        selected = [
            {key: value for key, value in row.items() if not key.startswith("_")}
            for row in self._rows
            if (
                row["_account_ref"],
                row["_actor_ref"],
                row["_tree_ref"],
            )
            == filter_key
        ]
        return _HistoryResult(selected)


def _synthetic_chain(
    *,
    key: str,
    actor_ref: str,
    tree_ref: str,
) -> _SyntheticChain:
    root_question_ref = f"v60-question-router-{key}-root"
    continuation_question_ref = f"v60-question-router-{key}-continuation"
    root_world_event_ref = f"v60-world-event-router-{key}-root"
    continuation_baseline_ref = f"v60-world-event-router-{key}-continuation-baseline"

    root_payload = first_episode_contract().model_dump(mode="json")
    root_payload.update(
        {
            "episode_ref": f"v60-episode-router-{key}-root",
            "content_key": f"dream.router.{key}.root",
            "actor_ref": actor_ref,
            "tree_ref": tree_ref,
            "question_ref": root_question_ref,
            "baseline_event_ref": f"v60-world-event-router-{key}-baseline",
            "world_event_ref": root_world_event_ref,
            "continuation_question_ref": continuation_question_ref,
        }
    )
    root_payload["runtime_metadata"]["baseline_event_ref"] = root_payload["baseline_event_ref"]
    root = DreamEpisodeContract.model_validate(root_payload)

    continuation_payload = return_episode_contract().model_dump(mode="json")
    continuation_payload.update(
        {
            "episode_ref": f"v60-episode-router-{key}-continuation",
            "content_key": f"dream.router.{key}.continuation",
            "actor_ref": actor_ref,
            "tree_ref": tree_ref,
            "question_ref": continuation_question_ref,
            "baseline_event_ref": continuation_baseline_ref,
            "world_event_ref": (f"v60-world-event-router-{key}-continuation-outcome"),
            "continuation_question_ref": None,
            "continuation_label": None,
        }
    )
    continuation_payload["runtime_metadata"]["baseline_event_ref"] = continuation_baseline_ref
    continuation_payload["entry_world_event"].update(
        {
            "event_ref": continuation_baseline_ref,
            "caused_by_event_ref": root_world_event_ref,
        }
    )
    continuation = DreamEpisodeContract.model_validate(continuation_payload)
    transition = episode_transition(
        from_question_ref=root.question_ref,
        to_question_ref=continuation.question_ref,
        label=f"{key} 的下一章",
    )
    return _SyntheticChain(
        root=root,
        continuation=continuation,
        transition=transition,
    )


def _catalog(*chains: _SyntheticChain) -> ActiveEpisodeCatalog:
    episodes = tuple(episode for chain in chains for episode in (chain.root, chain.continuation))
    transitions = tuple(chain.transition for chain in chains)
    return ActiveEpisodeCatalog(
        episodes=episodes,
        transitions=transitions,
        active_episode_refs=tuple(episode.episode_ref for episode in episodes),
        entry_episode_ref=chains[0].root.episode_ref,
        entry_episode_refs=tuple(chain.root.episode_ref for chain in chains),
        question_sequence_indexes=tuple(
            (episode.question_ref, index)
            for chain in chains
            for index, episode in enumerate((chain.root, chain.continuation))
        ),
        graph_hash=content_hash(
            {
                "episodes": [episode.model_dump(mode="json") for episode in episodes],
                "transitions": [transition.model_dump(mode="json") for transition in transitions],
            }
        ),
    )


def _candidate(
    chain: _SyntheticChain,
    *,
    domain: str,
    display_order: int,
) -> GroveCandidateDefinition:
    return GroveCandidateDefinition.issue(
        pool_ref="v60.dream-grove.router-regression.001",
        question_ref=chain.root.question_ref,
        actor_ref=chain.root.actor_ref,
        tree_ref=chain.root.tree_ref,
        domain=domain,
        public_alias=f"{chain.root.actor_ref} 的树",
        premise="只由这棵树自己的 canonical 历史推进。",
        display_order=display_order,
    )


def _completed_history(
    *,
    account_ref: str,
    candidate: GroveCandidateDefinition,
    episode: DreamEpisodeContract,
    outcome_world_event_ref: str,
    incoming_transition: EpisodeTransitionContract | None = None,
) -> dict[str, object]:
    return {
        "_account_ref": account_ref,
        "_actor_ref": candidate.actor_ref,
        "_tree_ref": candidate.tree_ref,
        "encounter_ref": (f"v60-encounter-router-{account_ref}-{episode.episode_ref}"),
        "outcome_world_event_ref": outcome_world_event_ref,
        "source_question_ref": episode.question_ref,
        "source_candidate_ref": candidate.candidate_ref,
        "event_json": {
            "source_question_ref": episode.question_ref,
            "source_candidate_ref": candidate.candidate_ref,
            "source_candidate_hash": candidate.candidate_hash,
            "source_episode_ref": episode.episode_ref,
            "source_episode_version": episode.episode_version,
            "source_episode_contract_hash": content_hash(episode.model_dump(mode="json")),
            "source_transition_ref": (
                incoming_transition.transition_ref if incoming_transition is not None else None
            ),
            "source_transition_hash": (
                content_hash(incoming_transition.model_dump(mode="json"))
                if incoming_transition is not None
                else None
            ),
        },
    }


def test_two_candidate_roots_route_and_finish_independently() -> None:
    chain_a = _synthetic_chain(
        key="a",
        actor_ref="v60-actor-router-a",
        tree_ref="v60-tree-router-a",
    )
    chain_b = _synthetic_chain(
        key="b",
        actor_ref="v60-actor-router-b",
        tree_ref="v60-tree-router-b",
    )
    catalog = _catalog(chain_a, chain_b)
    candidate_a = _candidate(
        chain_a,
        domain="career",
        display_order=1,
    )
    candidate_b = _candidate(
        chain_b,
        domain="wealth",
        display_order=2,
    )
    owner_ref = "v60-account-router-owner"
    other_ref = "v60-account-router-other"
    connection = _HistoryConnection(
        [
            _completed_history(
                account_ref=owner_ref,
                candidate=candidate_a,
                episode=chain_a.root,
                outcome_world_event_ref="v60-event-owner-a-root",
            ),
            _completed_history(
                account_ref=owner_ref,
                candidate=candidate_b,
                episode=chain_b.root,
                outcome_world_event_ref="v60-event-owner-b-root",
            ),
            _completed_history(
                account_ref=owner_ref,
                candidate=candidate_b,
                episode=chain_b.continuation,
                outcome_world_event_ref="v60-event-owner-b-continuation",
                incoming_transition=chain_b.transition,
            ),
            _completed_history(
                account_ref=other_ref,
                candidate=candidate_a,
                episode=chain_a.root,
                outcome_world_event_ref="v60-event-other-a-root",
            ),
            _completed_history(
                account_ref=other_ref,
                candidate=candidate_a,
                episode=chain_a.continuation,
                outcome_world_event_ref="v60-event-other-a-continuation",
                incoming_transition=chain_a.transition,
            ),
        ]
    )
    router = DreamGroveChapterRouter()

    owner_a = router.resolve(
        connection,
        account_ref=owner_ref,
        candidate=candidate_a,
        catalog=catalog,
    )
    owner_b = router.resolve(
        connection,
        account_ref=owner_ref,
        candidate=candidate_b,
        catalog=catalog,
    )
    other_a = router.resolve(
        connection,
        account_ref=other_ref,
        candidate=candidate_a,
        catalog=catalog,
    )

    assert owner_a.route.status == "AVAILABLE"
    assert owner_a.route.basis == "CANONICAL_TRANSITION"
    assert owner_a.route.target_source_question_ref == (chain_a.continuation.question_ref)
    assert owner_a.route.transition_ref == chain_a.transition.transition_ref
    assert owner_a.preceding_world_event_ref == "v60-event-owner-a-root"

    assert owner_b.route.status == "STORY_CURRENTLY_COMPLETE"
    assert owner_b.route.basis == "TERMINAL_CHAPTER"
    assert owner_b.route.target_source_question_ref == (chain_b.continuation.question_ref)
    assert owner_b.route.transition_ref is None
    assert owner_b.preceding_world_event_ref == ("v60-event-owner-b-continuation")

    assert other_a.route.status == "STORY_CURRENTLY_COMPLETE"
    assert other_a.route.target_source_question_ref == (chain_a.continuation.question_ref)
    assert other_a.preceding_world_event_ref == ("v60-event-other-a-continuation")
    assert owner_a.route.candidate_ref == candidate_a.candidate_ref
    assert owner_b.route.candidate_ref == candidate_b.candidate_ref
    assert owner_a.route.tree_ref != owner_b.route.tree_ref
    assert connection.filters == [
        (owner_ref, candidate_a.actor_ref, candidate_a.tree_ref),
        (owner_ref, candidate_b.actor_ref, candidate_b.tree_ref),
        (other_ref, candidate_a.actor_ref, candidate_a.tree_ref),
    ]


def test_same_actor_and_tree_history_cannot_cross_candidate_identity() -> None:
    chain = _synthetic_chain(
        key="candidate-boundary",
        actor_ref="v60-actor-router-candidate-boundary",
        tree_ref="v60-tree-router-candidate-boundary",
    )
    catalog = _catalog(chain)
    original = _candidate(
        chain,
        domain="relationship",
        display_order=1,
    )
    alternate = GroveCandidateDefinition.issue(
        **{
            **original.model_dump(
                mode="python",
                exclude={"candidate_ref", "candidate_hash"},
            ),
            "premise": "相同 actor/tree 也不能借用另一候选的完成历史。",
            "display_order": 2,
        }
    )
    connection = _HistoryConnection(
        [
            _completed_history(
                account_ref="v60-account-router-candidate-boundary",
                candidate=original,
                episode=chain.root,
                outcome_world_event_ref=("v60-event-router-candidate-boundary-root"),
            )
        ]
    )

    with pytest.raises(
        DreamStateError,
        match="dream_grove_chapter_history_candidate_mismatch",
    ):
        DreamGroveChapterRouter().resolve(
            connection,
            account_ref="v60-account-router-candidate-boundary",
            candidate=alternate,
            catalog=catalog,
        )
