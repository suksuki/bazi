from __future__ import annotations

import json
from pathlib import Path

from experience.contracts import (
    CompiledTopic,
    CueTemplate,
    MingliExperienceEnvelope,
    PerformanceCueInstance,
    TheaterEvent,
    TopicPackage,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "product" / "contracts" / "abu-living-theater-v1"
CONTRACTS = {
    "mingli_experience_envelope_v1.schema.json": MingliExperienceEnvelope,
    "topic_package_v1.schema.json": TopicPackage,
    "compiled_topic_v1.schema.json": CompiledTopic,
    "cue_template_v1.schema.json": CueTemplate,
    "performance_cue_instance_v1.schema.json": PerformanceCueInstance,
    "theater_event_v1.schema.json": TheaterEvent,
}


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for filename, contract in CONTRACTS.items():
        path = OUTPUT / filename
        path.write_text(
            json.dumps(contract.model_json_schema(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"exported={len(CONTRACTS)} output={OUTPUT}")


if __name__ == "__main__":
    main()
