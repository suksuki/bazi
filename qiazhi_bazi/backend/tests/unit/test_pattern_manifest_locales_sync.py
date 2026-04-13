"""V6.7：pattern_manifest 中格局 id / i18n_key 与前端 locales 键对齐（防 UI 漏键）。"""
from __future__ import annotations

import json
import re
from pathlib import Path


def _collect_manifest_keys(manifest: dict) -> set[str]:
    keys: set[str] = set()
    for section in ("STANDARD_OCTAD", "SPECIAL_PATTERNS"):
        block = manifest.get(section)
        if not isinstance(block, dict):
            continue
        for _k, spec in block.items():
            if not isinstance(spec, dict):
                continue
            pid = str(spec.get("id") or "").strip()
            if pid:
                keys.add(f"pattern.{pid}")
            i18n = str(spec.get("i18n_key") or "").strip()
            if i18n:
                keys.add(i18n)
    return keys


def _zh_locale_string_keys(locales_ts: str) -> set[str]:
    """粗解析 `STATIC_I18N` 的 ZH 块中带引号的键名。"""
    m = re.search(r"ZH:\s*\{", locales_ts)
    if not m:
        return set()
    start = m.end() - 1
    depth = 0
    end = None
    for i in range(start, len(locales_ts)):
        c = locales_ts[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end is None:
        return set()
    block = locales_ts[start : end + 1]
    return set(re.findall(r'"((?:pattern|shadowPreview)[^"]+)"\s*:', block))


def test_manifest_pattern_ids_and_i18n_exist_in_locales_zh() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest_path = root / "app" / "logic" / "patterns" / "pattern_manifest.json"
    locales_path = root.parent / "frontend" / "src" / "constants" / "locales.ts"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    locales_ts = locales_path.read_text(encoding="utf-8")
    required = _collect_manifest_keys(manifest)
    zh_keys = _zh_locale_string_keys(locales_ts)
    missing = sorted(required - zh_keys)
    assert not missing, f"locales ZH 缺少键: {missing[:20]}{'…' if len(missing) > 20 else ''}"


def test_manifest_pattern_ids_exist_in_locales_en_ko() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest_path = root / "app" / "logic" / "patterns" / "pattern_manifest.json"
    locales_path = root.parent / "frontend" / "src" / "constants" / "locales.ts"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    locales_ts = locales_path.read_text(encoding="utf-8")
    required = _collect_manifest_keys(manifest)

    def block_keys(lang: str) -> set[str]:
        m = re.search(rf"{lang}:\s*\{{", locales_ts)
        if not m:
            return set()
        start = m.end() - 1
        depth = 0
        end = None
        for i in range(start, len(locales_ts)):
            if locales_ts[i] == "{":
                depth += 1
            elif locales_ts[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end is None:
            return set()
        block = locales_ts[start : end + 1]
        return set(re.findall(r'"((?:pattern|shadowPreview)[^"]+)"\s*:', block))

    for lang in ("EN", "KO"):
        missing = sorted(required - block_keys(lang))
        assert not missing, f"locales {lang} 缺少键: {missing[:12]}"
