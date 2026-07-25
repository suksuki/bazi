#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from product.dream_game_content import (
    SIMULATED_PACK_PATH,
    audit_content_pack,
    load_content_pack,
)
from product.dream_store import build_dream_store


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and govern Dream matured-fruit packs.")
    parser.add_argument("command", choices=("validate", "import", "gate", "revoke"))
    parser.add_argument("--path", type=Path, default=SIMULATED_PACK_PATH)
    parser.add_argument("--pack-id", default="")
    args = parser.parse_args()

    if args.command == "validate":
        pack = load_content_pack(args.path)
        audit = audit_content_pack(pack)
        print(json.dumps({
            "pack": pack.model_dump(mode="json"),
            "audit": audit.model_dump(mode="json"),
            "verified_real_content_gate": "0/3" if pack.evidence_class == "SIMULATED" else "pending_store_audit",
        }, ensure_ascii=False, indent=2))
        return 0 if audit.passed else 1

    store = build_dream_store()
    if args.command == "import":
        pack = load_content_pack(args.path)
        audit = audit_content_pack(pack)
        if not audit.passed:
            print(json.dumps(audit.model_dump(mode="json"), ensure_ascii=False, indent=2))
            return 1
        saved = store.save_game_content_pack(pack)
        print(json.dumps({
            "status": "IMPORTED",
            "pack_id": saved.pack_id,
            "content_state": saved.content_state,
            "evidence_class": saved.evidence_class,
            "verified_real_gate_contribution": saved.verified_real_gate_contribution,
            "storage": store.storage_name,
        }, ensure_ascii=False, indent=2))
        return 0

    if args.command == "gate":
        count = store.verified_real_game_content_count()
        print(json.dumps({
            "verified_real_content_count": count,
            "required": 3,
            "gate": f"{count}/3",
            "launch": "LOCKED" if count < 3 else "ELIGIBLE_FOR_REVIEW",
        }, ensure_ascii=False, indent=2))
        return 0

    if not args.pack_id:
        parser.error("revoke requires --pack-id")
    revoked = store.revoke_game_content_pack(
        pack_id=args.pack_id,
        revoked_at=datetime.now(timezone.utc),
    )
    print(json.dumps({
        "status": "REVOKED",
        "pack_id": revoked.pack_id,
        "revoked_at": revoked.revoked_at,
        "verified_real_gate_contribution": 0,
    }, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
