from __future__ import annotations

import json
from pathlib import Path

from scripts.v50_build_knowledge_graph_seed import build_knowledge_graph


V50_ROOT = Path(__file__).resolve().parents[1]
CANON_DIR = V50_ROOT / "data" / "knowledge" / "canon"


def test_v50_knowledge_graph_seed_indexes_cards_topics_and_runtime_status() -> None:
    cards_path = CANON_DIR / "knowledge_cards_v1.jsonl"
    cards = [json.loads(line) for line in cards_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    graph = build_knowledge_graph(cards_path)
    node_ids = {node["id"] for node in graph["nodes"]}
    edge_types = set(graph["edge_types"])

    assert graph["boundary"] == "knowledge_graph_seed_is_index_only_not_runtime_judgment"
    assert {card["id"] for card in cards}.issubset(node_ids)
    assert {"maps_to_topic", "related_to", "runtime_candidate_for", "has_runtime_status"}.issubset(edge_types)
    assert "topic.wealth" in node_ids
    assert "runtime_priority.P0" in node_ids
