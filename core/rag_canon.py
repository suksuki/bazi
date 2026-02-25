"""
第 045 号：FDS 古典原典 RAG — 判词须含古典原话引证
从 config/rag/fds_classical_canon.json 灌入 ChromaDB，按格局召回，注入 ai_engine 判词链路。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
CANON_CONFIG = ROOT / "config" / "rag" / "fds_classical_canon.json"
# 与 VaultManager 同路径，共用 ChromaDB
VAULT_PATH = ROOT / "knowledge_vault"
COLLECTION_CITATIONS = "fds_classical_citations"


def _get_client_and_embedding():
    """ChromaDB 客户端 + Ollama Embedding（与 VaultManager 一致）。"""
    try:
        import chromadb
        from chromadb.config import Settings
    except ImportError:
        return None, None
    try:
        from core.vault_manager import VaultManager
        vm = VaultManager()
        client = vm.client
        def embed(texts):
            if isinstance(texts, str):
                texts = [texts]
            return [vm.get_embedding(t) for t in texts]
        return client, embed
    except Exception as e:
        logger.debug("RAG canonical embedding 不可用: %s", e)
    return None, None


def ingest_canon_from_config(config_path: Optional[Path] = None) -> int:
    """从 JSON 配置灌入古典原话与判例到 ChromaDB。返回入库条数。"""
    path = config_path or CANON_CONFIG
    if not path.exists():
        logger.warning("古典原典配置不存在: %s", path)
        return 0
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    client, embed_fn = _get_client_and_embedding()
    if not client or not embed_fn:
        logger.warning("ChromaDB 或 Embedding 不可用，跳过 RAG 灌入")
        return 0
    VAULT_PATH.mkdir(parents=True, exist_ok=True)
    coll = client.get_or_create_collection(
        name=COLLECTION_CITATIONS,
        metadata={"description": "FDS 古典原话与判例，判词须含引证"},
    )
    count = 0
    for item in data.get("classical_quotes", []) + data.get("verdict_precedents", []):
        doc_id = item.get("id", f"doc_{count}")
        text = item.get("text", "")
        if not text:
            continue
        pattern_id = (item.get("pattern_id") or "").strip().upper()
        source = item.get("source_book") or item.get("title") or "古典"
        doc_type = "precedent" if "precedent" in str(item.get("id", "")) or item.get("title") else "canon"
        try:
            vec = embed_fn(text)[0] if isinstance(embed_fn(text), list) else embed_fn(text)
        except Exception as e:
            logger.debug("embedding 失败 %s: %s", doc_id, e)
            continue
        meta = {"pattern_id": pattern_id, "source": source, "type": doc_type}
        try:
            coll.upsert(ids=[doc_id], embeddings=[vec], documents=[text], metadatas=[meta])
            count += 1
        except Exception as e:
            logger.debug("upsert 失败 %s: %s", doc_id, e)
    logger.info("RAG 古典灌入完成: %d 条", count)
    return count


def query_citations(
    pattern_id: str,
    query_text: Optional[str] = None,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """
    按格局召回古典原话/判例，供判词注入。
    若提供 query_text 则语义检索，否则按 pattern_id 过滤后取前 top_k。
    返回 [{"text": "...", "source": "子平真诠", "pattern_id": "A-07"}, ...]
    """
    client, embed_fn = _get_client_and_embedding()
    if not client:
        return []
    try:
        coll = client.get_collection(name=COLLECTION_CITATIONS)
    except Exception:
        return []
    pid = pattern_id.strip().upper()
    try:
        if query_text and embed_fn:
            vec = embed_fn(query_text)[0] if isinstance(embed_fn(query_text), list) else embed_fn(query_text)
            res = coll.query(
                query_embeddings=[vec],
                n_results=top_k,
                where={"pattern_id": pid},
            )
        else:
            # 无 query_text 时按 metadata 过滤：ChromaDB 需 where，再取前 top_k
            res = coll.get(where={"pattern_id": pid}, limit=top_k)
            if not res or not res.get("ids"):
                return []
            # get 返回的是 id/document/metadata，无 distance；格式化为统一结构
            out = []
            for i, doc_id in enumerate(res["ids"]):
                doc = (res.get("documents") or [[""]])[i] if i < len(res.get("documents") or []) else ""
                meta = (res.get("metadatas") or [{}])[i] if i < len(res.get("metadatas") or []) else {}
                out.append({"text": doc, "source": meta.get("source", ""), "pattern_id": meta.get("pattern_id", pid)})
            return out
        if not res or not res.get("ids") or not res["ids"][0]:
            return []
        out = []
        for i, doc_id in enumerate(res["ids"][0][:top_k]):
            doc = res["documents"][0][i] if res.get("documents") and res["documents"][0] else ""
            meta = res["metadatas"][0][i] if res.get("metadatas") and res["metadatas"][0] else {}
            out.append({"text": doc, "source": meta.get("source", ""), "pattern_id": meta.get("pattern_id", pid)})
        return out
    except Exception as e:
        logger.debug("RAG query_citations 失败: %s", e)
        return []


def _get_meta_instruction(config_path: Optional[Path] = None) -> str:
    """读取 meta_instruction，防 RAG 复读机化：先引古文后化白话。"""
    path = config_path or CANON_CONFIG
    if not path.exists():
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return (data.get("meta_instruction") or "").strip()
    except Exception:
        return ""


def format_citations_for_prompt(citations: List[Dict[str, Any]], config_path: Optional[Path] = None) -> str:
    """将召回的条目格式化为「判词须含古典引证」的 Prompt 片段；注入 meta_instruction，要求先引古文后化白话。"""
    if not citations:
        return ""
    lines = ["", "## 判词须含古典原话引证（至少引用一条）"]
    meta = _get_meta_instruction(config_path)
    if meta:
        lines.append(f"**判词风格**：{meta}")
    for c in citations[:3]:
        src = c.get("source", "古典")
        text = c.get("text", "")
        if text:
            lines.append(f"- 《{src}》云：{text}")
    return "\n".join(lines)
