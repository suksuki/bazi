from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


V50_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANON = V50_ROOT / "data" / "knowledge" / "canon" / "knowledge_cards_v1.jsonl"
DEFAULT_OUTPUT = V50_ROOT / "data" / "knowledge" / "canon" / "knowledge_graph_seed_v1.json"


def build_knowledge_graph(cards_path: Path) -> dict[str, Any]:
    cards = _load_cards(cards_path)
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []

    for card in cards:
        card_id = card["id"]
        nodes[card_id] = {
            "id": card_id,
            "node_type": "knowledge_card",
            "label": card["name_zh"],
            "domain": card["domain"],
            "category": card["category"],
            "runtime_status": card["runtime_status"],
            "runtime_priority": card["recommended_runtime_priority"],
            "consensus_level": card.get("consensus_level", "unknown"),
        }

        for topic in card.get("topic_mapping", []):
            topic_id = f"topic.{topic}"
            nodes.setdefault(topic_id, {"id": topic_id, "node_type": "topic", "label": topic})
            edges.append(_edge(card_id, topic_id, "maps_to_topic"))

        for school in card.get("schools", []):
            school_id = f"school.{_stable_key(school)}"
            nodes.setdefault(school_id, {"id": school_id, "node_type": "school", "label": school})
            edges.append(_edge(card_id, school_id, "same_school_as"))

        for concept in card.get("related_concepts", []):
            concept_id = f"concept.{_stable_key(concept)}"
            nodes.setdefault(concept_id, {"id": concept_id, "node_type": "concept", "label": concept})
            edges.append(_edge(card_id, concept_id, "related_to"))

        runtime_id = f"runtime_status.{card['runtime_status']}"
        nodes.setdefault(runtime_id, {"id": runtime_id, "node_type": "runtime_status", "label": card["runtime_status"]})
        edges.append(_edge(card_id, runtime_id, "has_runtime_status"))

        priority_id = f"runtime_priority.{card['recommended_runtime_priority']}"
        nodes.setdefault(
            priority_id,
            {"id": priority_id, "node_type": "runtime_priority", "label": card["recommended_runtime_priority"]},
        )
        edges.append(_edge(card_id, priority_id, "runtime_candidate_for"))

    edge_types = sorted({edge["edge_type"] for edge in edges})
    return {
        "version": "v50.knowledge_graph_seed.v1",
        "source": str(cards_path.relative_to(V50_ROOT)),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "edge_types": edge_types,
        "nodes": sorted(nodes.values(), key=lambda row: row["id"]),
        "edges": sorted(edges, key=lambda row: (row["source"], row["edge_type"], row["target"])),
        "boundary": "knowledge_graph_seed_is_index_only_not_runtime_judgment",
    }


def write_graph(cards_path: Path = DEFAULT_CANON, output_path: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    graph = build_knowledge_graph(cards_path)
    output_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return graph


def _load_cards(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _stable_key(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]


def _edge(source: str, target: str, edge_type: str) -> dict[str, str]:
    return {"source": source, "target": target, "edge_type": edge_type}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build V50 Knowledge Graph seed from Knowledge Cards.")
    parser.add_argument("--cards", type=Path, default=DEFAULT_CANON)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    graph = write_graph(args.cards, args.output)
    print(
        f"{graph['version']}: nodes={graph['node_count']} "
        f"edges={graph['edge_count']} output={args.output}"
    )


if __name__ == "__main__":
    main()
