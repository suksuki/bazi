#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
练剑脚本：直接调用 Ollama 流式 generate，打印 qwen3.5:35b 的原始 chunk 结构。
用于确认 FDS 判词解析应如何兼容 Qwen3.5（含 thinking 等字段）。
运行：在项目根执行 python scripts/test_ollama_qwen35_stream.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main():
    from core.config_manager import ConfigManager
    cm = ConfigManager()
    host = cm.get("ollama_host") or "http://localhost:11434"
    model = cm.get("selected_model_name") or (cm.get("ai_engine") or {}).get("chat_model") or "qwen3.5:35b"

    try:
        import ollama
    except ImportError:
        print("未安装 ollama 包，请 pip install ollama")
        return

    if host and host != "http://localhost:11434":
        client = ollama.Client(host=host)
    else:
        client = ollama.Client()

    prompt = "用一句话说：今天天气很好。"
    print(f"Host: {host}\nModel: {model}\nPrompt: {prompt}\n")

    def extract_text(chunk):
        """从单 chunk 提取本次增量文本（兼容 generate 与 chat/thinking 模型）。"""
        text = ""
        if isinstance(chunk, dict):
            msg = chunk.get("message") or {}
            if isinstance(msg, dict):
                text += msg.get("content", "") or ""
            text += chunk.get("response", "") or chunk.get("text", "") or ""
        else:
            if hasattr(chunk, "message"):
                m = chunk.message
                if hasattr(m, "content"):
                    text += m.content or ""
                elif isinstance(m, dict):
                    text += m.get("content", "") or ""
            if hasattr(chunk, "response"):
                text += chunk.response or ""
        return text

    # ---------- 1. 流式 generate() ----------
    print("--- 流式 generate() 原始 chunk（前 5 个）---")
    try:
        stream = client.generate(model=model, prompt=prompt, stream=True, options={"num_predict": 80})
        full_gen = ""
        for i, chunk in enumerate(stream):
            if i < 5:
                print(f"\n[Chunk {i}] type={type(chunk).__name__}")
                if isinstance(chunk, dict):
                    print(f"  keys: {list(chunk.keys())}")
                    if "message" in chunk:
                        print(f"  message: {chunk['message']}")
                    if "response" in chunk:
                        print(f"  response: {chunk['response']!r}")
                else:
                    print(f"  has message: {hasattr(chunk,'message')}, has response: {hasattr(chunk,'response')}")
                    if hasattr(chunk, "message") and chunk.message:
                        print(f"  message: {chunk.message}")
                    if hasattr(chunk, "response"):
                        print(f"  response: {chunk.response!r}")
            full_gen += extract_text(chunk)
        print(f"\n[generate] 拼接全文长度: {len(full_gen)}, 内容: {full_gen[:200]!r}...")
    except Exception as e:
        print(f"generate 抛错: {e}")

    # ---------- 2. 流式 chat()（Qwen3.5 等 thinking 模型常用） ----------
    print("\n--- 流式 chat() 原始 chunk（前 5 个）---")
    try:
        chat_stream = client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            options={"num_predict": 80},
        )
        full_chat = ""
        for i, chunk in enumerate(chat_stream):
            if i < 5:
                print(f"\n[Chat Chunk {i}] type={type(chunk).__name__}")
                if isinstance(chunk, dict):
                    print(f"  keys: {list(chunk.keys())}")
                    if "message" in chunk:
                        print(f"  message: {chunk['message']}")
                else:
                    print(f"  has message: {hasattr(chunk,'message')}")
                    if hasattr(chunk, "message") and chunk.message:
                        m = chunk.message
                        print(f"  message.content: {getattr(m,'content','')!r}")
                        print(f"  message.thinking: {getattr(m,'thinking','')!r}")
            full_chat += extract_text(chunk)
        print(f"\n[chat] 拼接全文长度: {len(full_chat)}, 内容: {full_chat[:200]!r}...")
    except Exception as e:
        print(f"chat 抛错: {e}")


if __name__ == "__main__":
    main()
