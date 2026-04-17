"""V7.1：pattern_manifest.json 磁盘加载时的 SHA256 签名校验（非 DEBUG / 非 pytest 时）。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.logic.patterns import engine as engine_mod
from app.logic.patterns.engine import load_pattern_manifest


def test_load_default_manifest_ok_under_pytest():
    m = load_pattern_manifest()
    assert isinstance(m.get("ENGINE"), dict)


def test_signature_mismatch_returns_payload_when_enforced(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    bad = tmp_path / "pattern_manifest.json"
    bad.write_text(json.dumps({"ENGINE": {}, "AXIS_REGISTRY": {}, "STANDARD_OCTAD": {}, "SPECIAL_PATTERNS": {}}), encoding="utf-8")
    sig = bad.with_suffix(".sha256")
    sig.write_text("0" * 64 + "\n", encoding="utf-8")
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("DEBUG", "0")
    monkeypatch.setenv("QIAZHI_PATTERN_MANIFEST_PATH", str(bad))
    monkeypatch.setattr(engine_mod, "_pytest_active", lambda: False)
    monkeypatch.setattr(engine_mod, "_debug_mode", lambda: False)
    out = load_pattern_manifest()
    assert out.get("status") == "SIGNATURE_ERROR"
    assert out.get("code") == "SHA256_MISMATCH"


def test_signature_skipped_in_debug_invalid_json_returns_payload(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    bad = tmp_path / "pattern_manifest.json"
    bad.write_text("not even json", encoding="utf-8")
    monkeypatch.setenv("QIAZHI_PATTERN_MANIFEST_PATH", str(bad))
    monkeypatch.setenv("DEBUG", "1")
    # 签名在 DEBUG 下跳过；无效 JSON 不抛异常，返回 SIGNATURE_ERROR 形状载荷（V7.3 防进程炸裂）
    out = load_pattern_manifest()
    assert out.get("status") == "SIGNATURE_ERROR"
    assert out.get("code") == "JSON_DECODE"
