#!/usr/bin/env python3
"""
第 045 号指令：将 config/rag/fds_classical_canon.json 灌入 ChromaDB（fds_classical_citations）。
供判词链路 RAG 召回，判词须含古典原话引证。
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.rag_canon import ingest_canon_from_config, CANON_CONFIG


def main():
    print("第 045 号：古典原典 + 判例 → ChromaDB（RAG 判词引证）")
    print(f"  配置: {CANON_CONFIG}")
    n = ingest_canon_from_config()
    print(f"  灌入 {n} 条")
    sys.exit(0 if n >= 0 else 1)


if __name__ == "__main__":
    main()
