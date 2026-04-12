"""DB-backed 物理参数：启动同步、读取合并、Admin 持久化。"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from sqlmodel import select

from app.core.config.physics_settings import DEFAULT_PHYSICS_SETTINGS
from app.db.models import CausalManifestMeta, CausalSkill, PhysicsSettingsRegistry
from app.db.session import session_scope

_MANIFEST_DIR = Path(__file__).resolve().parents[2] / "plugins" / "base_physics"
_SKILL_JSON = _MANIFEST_DIR / "skill_manifest.json"
_L1_MANIFEST = _MANIFEST_DIR / "manifests" / "l1_physics_manifest.json"

_SETTINGS_CACHE_REV = 0


@lru_cache(maxsize=16)
def _registry_overrides_cached(rev: int) -> Dict[str, float]:
    del rev
    out: Dict[str, float] = {}
    try:
        with session_scope() as s:
            rows = s.exec(select(PhysicsSettingsRegistry)).all()
            for r in rows:
                out[str(r.key)] = float(r.value)
    except Exception:
        return {}
    return out


def bump_physics_settings_cache() -> None:
    global _SETTINGS_CACHE_REV
    _SETTINGS_CACHE_REV += 1
    _registry_overrides_cached.cache_clear()


def apply_db_layer_to_settings(base: Dict[str, float]) -> Dict[str, float]:
    """在硬编码 DEFAULT 之上合并 DB `physics_settings_registry.value`。"""
    merged = dict(base)
    db_layer = _registry_overrides_cached(_SETTINGS_CACHE_REV)
    for k, v in db_layer.items():
        if k in merged:
            merged[k] = float(v)
    return merged


def _build_key_category_and_description() -> Tuple[Dict[str, str], Dict[str, str]]:
    """由 skill_manifest + l1_physics_manifest 推导 physics_setting_key → 插件 ID / 描述。"""
    cat: Dict[str, str] = {}
    desc: Dict[str, str] = {}
    try:
        skill_doc = json.loads(_SKILL_JSON.read_text(encoding="utf-8"))
        for sk in skill_doc.get("skills") or []:
            if not isinstance(sk, dict):
                continue
            pk = sk.get("physics_setting_key")
            if not pk:
                continue
            pk = str(pk).strip()
            sid = str(sk.get("id") or "")
            name = str(sk.get("name") or "")
            if pk not in desc:
                desc[pk] = str(sk.get("description") or name or pk)
    except Exception:
        pass
    try:
        l1 = json.loads(_L1_MANIFEST.read_text(encoding="utf-8"))
        for op in l1.get("operators") or []:
            if not isinstance(op, dict):
                continue
            oid = str(op.get("id") or "").strip()
            keys = op.get("physics_settings_keys") or []
            if not oid or not isinstance(keys, list):
                continue
            for k in keys:
                ks = str(k).strip()
                if ks and ks not in cat:
                    cat[ks] = oid
    except Exception:
        pass
    for pk, cid, text in (
        ("L0_HIDDEN_ENERGY_SCALE", "l0.hidden_schema", "L0 藏干能量整体标度（乘在藏干支分量上）"),
        ("L0_ROOT_BOOST_FACTOR", "l0.root_resonance", "L0 通根反哺强度乘子（见 get_root_resonance）"),
        ("L0_YM_DH_WEIGHT_RATIO", "l0.pillar_time", "L0 年月相对日时柱位权重比（>1 偏强年月）"),
        ("SUB_BRANCH_SANHE_REQ_WANG_ZHI", "base.physics.op_branch_sanhe", "三合中神须见月/日地支（帝旺支）"),
        ("SANHE_ALPHA_LEAKAGE", "base.physics.op_branch_sanhe", "三合 Abs 增益的 α 泄漏（削弱有效 boost）"),
    ):
        cat.setdefault(pk, cid)
        desc.setdefault(pk, text)
    return cat, desc


def sync_physics_registry_from_defaults() -> int:
    """将 `DEFAULT_PHYSICS_SETTINGS` Upsert 到 `physics_settings_registry`（刷新 default_value / 元数据）。"""
    cat_map, desc_map = _build_key_category_and_description()
    n = 0
    with session_scope() as s:
        for key, default_v in DEFAULT_PHYSICS_SETTINGS.items():
            row = s.get(PhysicsSettingsRegistry, key)
            fv = float(default_v)
            category = cat_map.get(key, "base.physics")
            description = desc_map.get(key, key)
            if row is None:
                s.add(
                    PhysicsSettingsRegistry(
                        key=key,
                        value=fv,
                        default_value=fv,
                        category=category,
                        description=description[:4000] if description else "",
                    )
                )
                n += 1
            else:
                row.default_value = fv
                row.category = category
                if not (row.description or "").strip():
                    row.description = description[:4000] if description else ""
                s.add(row)
    bump_physics_settings_cache()
    return n


def persist_physics_registry_updates(updates: Iterable[Tuple[str, float]]) -> List[str]:
    """将 Admin 提交的键值写入 DB 并失效缓存。"""
    changed: List[str] = []
    with session_scope() as s:
        for key, raw in updates:
            k = str(key).strip()
            if not k or k not in DEFAULT_PHYSICS_SETTINGS:
                continue
            try:
                val = float(raw)
            except (TypeError, ValueError):
                continue
            row = s.get(PhysicsSettingsRegistry, k)
            if row is None:
                fv = float(DEFAULT_PHYSICS_SETTINGS[k])
                cat_map, desc_map = _build_key_category_and_description()
                s.add(
                    PhysicsSettingsRegistry(
                        key=k,
                        value=val,
                        default_value=fv,
                        category=cat_map.get(k, "base.physics"),
                        description=(desc_map.get(k, k))[:4000],
                    )
                )
            else:
                row.value = val
                s.add(row)
            changed.append(k)
    bump_physics_settings_cache()
    return changed


def list_physics_registry_rows() -> List[Dict[str, Any]]:
    try:
        with session_scope() as s:
            rows = s.exec(select(PhysicsSettingsRegistry)).all()
            return [
                {
                    "key": r.key,
                    "value": float(r.value),
                    "default_value": float(r.default_value),
                    "category": r.category,
                    "description": r.description,
                }
                for r in rows
            ]
    except Exception:
        return []


def _read_file_skill_manifest() -> Dict[str, Any]:
    raw = _SKILL_JSON.read_text(encoding="utf-8")
    data = json.loads(raw)
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def _file_skill_manifest_cached() -> Dict[str, Any]:
    return _read_file_skill_manifest()


def reload_file_skill_manifest_cache() -> None:
    _file_skill_manifest_cached.cache_clear()


def _load_operator_map_from_db() -> Optional[Dict[str, Any]]:
    try:
        with session_scope() as s:
            row = s.get(CausalManifestMeta, "base_physics_operator_map")
            if row is None or not isinstance(row.payload, dict):
                return None
            m = row.payload.get("operator_to_skill")
            return m if isinstance(m, dict) else None
    except Exception:
        return None


def _load_skills_from_db() -> Optional[List[Dict[str, Any]]]:
    try:
        with session_scope() as s:
            rows = s.exec(select(CausalSkill).where(CausalSkill.scope == "base_physics")).all()
            if not rows:
                return None
            out: List[Dict[str, Any]] = []
            for r in rows:
                tags = r.description_tags if isinstance(r.description_tags, list) else []
                item: Dict[str, Any] = {
                    "id": r.skill_id,
                    "name": r.name,
                    "description": r.description,
                    "impact_factor": r.impact_factor or "",
                    "assertion_template": r.assertion_template or "",
                }
                if r.physics_weight is not None:
                    item["physics_weight"] = float(r.physics_weight)
                if r.physics_setting_key:
                    item["physics_setting_key"] = r.physics_setting_key
                if tags:
                    item["description_tags"] = tags
                out.append(item)
            return out
    except Exception:
        return None


def sync_causal_skills_from_json() -> Tuple[int, bool]:
    """将磁盘 `skill_manifest.json` 全量写入 `causal_skills` 与 operator 映射元表。"""
    data = _read_file_skill_manifest()
    skills = data.get("skills") if isinstance(data.get("skills"), list) else []
    op_map = data.get("operator_to_skill") if isinstance(data.get("operator_to_skill"), dict) else {}
    n = 0
    with session_scope() as s:
        meta = s.get(CausalManifestMeta, "base_physics_operator_map")
        payload = {"operator_to_skill": op_map, "version": str(data.get("version") or "1.0")}
        if meta is None:
            s.add(CausalManifestMeta(scope="base_physics_operator_map", payload=payload))
        else:
            meta.payload = payload
            s.add(meta)
        for sk in skills:
            if not isinstance(sk, dict) or not sk.get("id"):
                continue
            sid = str(sk["id"])
            tags = sk.get("description_tags") if isinstance(sk.get("description_tags"), list) else []
            row = s.get(CausalSkill, sid)
            if row is None:
                s.add(
                    CausalSkill(
                        skill_id=sid,
                        scope="base_physics",
                        name=str(sk.get("name") or ""),
                        description=str(sk.get("description") or ""),
                        impact_factor=str(sk.get("impact_factor") or ""),
                        physics_weight=float(sk["physics_weight"]) if sk.get("physics_weight") is not None else None,
                        physics_setting_key=str(sk["physics_setting_key"]).strip() if sk.get("physics_setting_key") else None,
                        assertion_template=str(sk.get("assertion_template") or ""),
                        description_tags=tags,
                    )
                )
                n += 1
            else:
                row.name = str(sk.get("name") or "")
                row.description = str(sk.get("description") or "")
                row.impact_factor = str(sk.get("impact_factor") or "")
                row.physics_weight = (
                    float(sk["physics_weight"]) if sk.get("physics_weight") is not None else None
                )
                row.physics_setting_key = (
                    str(sk["physics_setting_key"]).strip() if sk.get("physics_setting_key") else None
                )
                row.assertion_template = str(sk.get("assertion_template") or "")
                row.description_tags = tags
                s.add(row)
    reload_file_skill_manifest_cache()
    return n, True


class DynamicSettingsProvider:
    """读取优先级：API overrides（在 `resolve_physics_settings` 内处理）> DB registry > 硬编码 DEFAULT。"""

    @staticmethod
    def apply_db_to(base: Mapping[str, float]) -> Dict[str, float]:
        return apply_db_layer_to_settings(dict(base))

    @staticmethod
    def sync_defaults_on_startup() -> None:
        sync_physics_registry_from_defaults()
        sync_causal_skills_from_json()


def persist_physics_registry_updates_from_body(updates: List[Mapping[str, Any]]) -> List[str]:
    pairs: List[Tuple[str, float]] = []
    for u in updates:
        if not isinstance(u, dict):
            continue
        k = str(u.get("key") or "").strip()
        if not k:
            continue
        try:
            v = float(u.get("value"))
        except (TypeError, ValueError):
            continue
        pairs.append((k, v))
    return persist_physics_registry_updates(pairs)
