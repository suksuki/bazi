"""
FDS Embedding 统一入口
======================
与对话模型一致：使用同一 Ollama 服务 URL，仅模型名不同。
从 config 读取 ollama_host 与 embedding_engine.model，调用 Ollama Embeddings API。
零硬编码：URL 与模型名均来自配置。
"""

from __future__ import annotations

import logging
from typing import List

from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


def _get_ollama_client():
    """与 ai_engine 一致：从配置读取 ollama_host。"""
    try:
        import ollama
    except ImportError:
        return None
    cm = ConfigManager()
    host = cm.get("ollama_host") or "http://localhost:11434"
    if host and host != "http://localhost:11434":
        return ollama.Client(host=host)
    return ollama.Client()


def get_embedding(text: str) -> List[float]:
    """
    使用当前配置的 Ollama 服务（与对话模型同 URL）及 embedding_engine.model 生成向量。
    """
    client = _get_ollama_client()
    if not client:
        raise ImportError("请安装 ollama: pip install ollama")
    cm = ConfigManager()
    cfg = cm.get("embedding_engine")
    model = "nomic-embed-text"
    if isinstance(cfg, dict) and cfg.get("model"):
        model = str(cfg["model"]).strip()
    try:
        response = client.embeddings(model=model, prompt=text)
        if isinstance(response, dict) and "embedding" in response:
            return response["embedding"]
        if hasattr(response, "embedding"):
            return response.embedding
        raise ValueError(f"Unexpected embedding response: {type(response)}")
    except Exception as e:
        logger.exception("Embedding 调用失败")
        raise


def get_embedding_provider_name() -> str:
    """返回当前配置的向量模型名，供 UI 显示。"""
    cm = ConfigManager()
    cfg = cm.get("embedding_engine")
    if isinstance(cfg, dict) and cfg.get("model"):
        return str(cfg["model"]).strip()
    return "nomic-embed-text"
