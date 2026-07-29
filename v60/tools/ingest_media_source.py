from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from abu_v60.media import PROJECT_ROOT
from abu_v60.media.registry import sha256_file
from abu_v60.provenance import canonical_json

IDENTIFIER_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]*$")
REVISION_PATTERN = re.compile(r"^v[1-9][0-9]*$")


def probe(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Archive an immutable, owner-authorized generated media source. "
            "This command never publishes the source to Runtime."
        )
    )
    parser.add_argument("--media-id", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--kind", required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--generator", required=True)
    parser.add_argument("--prompt-ref", required=True)
    parser.add_argument("--authorization", required=True)
    args = parser.parse_args()

    if not IDENTIFIER_PATTERN.fullmatch(args.media_id):
        raise SystemExit("media-id must use uppercase letters, numbers, underscore or hyphen")
    if not REVISION_PATTERN.fullmatch(args.revision):
        raise SystemExit("revision must be v1, v2, ...")
    source = args.source.expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"source does not exist: {source}")
    if "OWNER_APPROVED" not in args.authorization:
        raise SystemExit("source ingest requires explicit OWNER_APPROVED authorization")

    destination_directory = (
        PROJECT_ROOT / "media" / "sources" / args.media_id / args.revision
    )
    destination_directory.mkdir(parents=True, exist_ok=True)
    destination = destination_directory / f"source{source.suffix.lower()}"
    source_hash = sha256_file(source)
    if destination.exists():
        if sha256_file(destination) != source_hash:
            raise SystemExit(
                "immutable source revision already exists with a different hash; "
                "create a new revision"
            )
    else:
        shutil.copy2(source, destination)

    receipt = {
        "schema_version": "v60.media-ingest-receipt.001",
        "media_id": args.media_id,
        "revision": args.revision,
        "kind": args.kind,
        "source_path": str(destination.relative_to(PROJECT_ROOT)),
        "original_filename": source.name,
        "source_sha256": source_hash,
        "source_bytes": destination.stat().st_size,
        "generator": args.generator,
        "prompt_ref": args.prompt_ref,
        "authorization": args.authorization,
        "probe": probe(destination),
        "ingested_at": datetime.now(UTC).isoformat(),
        "publication_status": "NOT_PUBLISHED",
    }
    receipt_path = destination_directory / "ingest-receipt.json"
    if receipt_path.exists():
        previous = json.loads(receipt_path.read_text(encoding="utf-8"))
        if previous["source_sha256"] != source_hash:
            raise SystemExit("existing ingest receipt belongs to a different source")
        receipt["ingested_at"] = previous["ingested_at"]
    receipt_path.write_text(f"{canonical_json(receipt)}\n", encoding="utf-8")
    print(canonical_json(receipt))


if __name__ == "__main__":
    main()
