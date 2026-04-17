"""L0 原子层：干支元数据、藏干表、通根系数 — 优先 DB，回退 physics_rules 常量。"""
from __future__ import annotations

from threading import Lock
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from sqlmodel import select

from app.db.models import L0BranchHiddenSchema, L0ElementRegistry, L0ResonanceRules
from app.db.session import session_scope

# 支 → 主气五行（与地支本气传统归类一致，供 l0_element_registry 种子）
BRANCH_PRIMARY_ELEMENT: Dict[str, str] = {
    "子": "water",
    "丑": "earth",
    "寅": "wood",
    "卯": "wood",
    "辰": "earth",
    "巳": "fire",
    "午": "fire",
    "未": "earth",
    "申": "metal",
    "酉": "metal",
    "戌": "earth",
    "亥": "water",
}

_DEFAULT_RESONANCE: Dict[str, float] = {
    "ROOT_TIER_MAIN": 1.0,
    "ROOT_TIER_MIDDLE": 0.55,
    "ROOT_TIER_RESIDUAL": 0.25,
}


def _tier_for_stem(branch: str, stem: str, ratios: Dict[str, float]) -> str:
    if stem not in ratios:
        return "MAIN"
    ordered = sorted(ratios.items(), key=lambda x: -float(x[1]))
    for i, (s, _) in enumerate(ordered):
        if s == stem:
            return ("MAIN", "MIDDLE", "RESIDUAL")[min(i, 2)]
    return "MAIN"


class L0PluginManager:
    """单例：缓存从 DB 解析的藏干表与共振系数；无表或异常时回退代码常量。"""

    _instance: Optional["L0PluginManager"] = None
    _singleton_lock = Lock()

    def __init__(self) -> None:
        self._lock = Lock()
        self._valid = False
        self._hidden: Dict[str, Dict[str, float]] = {}
        self._resonance: Dict[str, float] = dict(_DEFAULT_RESONANCE)
        self._main_stem: Dict[str, str] = {}

    @classmethod
    def instance(cls) -> "L0PluginManager":
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def reset_instance_for_tests(cls) -> None:
        with cls._singleton_lock:
            cls._instance = None

    def bump_cache(self) -> None:
        with self._lock:
            self._valid = False

    def ensure_loaded(self) -> None:
        with self._lock:
            if self._valid:
                return
            self._reload_unlocked()
            self._valid = True

    def _reload_unlocked(self) -> None:
        from app.skills.physics_rules import BRANCH_HIDDEN_STEMS, STEM_TO_ELEMENT, STEM_YIN_YANG

        hidden: Dict[str, Dict[str, float]] = {}
        resonance = dict(_DEFAULT_RESONANCE)
        try:
            with session_scope() as s:
                rows = s.exec(select(L0BranchHiddenSchema)).all()
                if rows:
                    for r in rows:
                        br = str(r.branch)
                        hidden.setdefault(br, {})[str(r.hidden_stem)] = float(r.ratio_pct)
                rrows = s.exec(select(L0ResonanceRules)).all()
                if rrows:
                    resonance = {str(x.rule_key): float(x.coefficient) for x in rrows}
        except Exception:
            hidden = {}
            resonance = dict(_DEFAULT_RESONANCE)

        if not hidden:
            hidden = {k: dict(v) for k, v in BRANCH_HIDDEN_STEMS.items()}
        self._hidden = hidden
        self._resonance = {**_DEFAULT_RESONANCE, **resonance}
        self._main_stem = {}
        for br, stems in self._hidden.items():
            if stems:
                main = max(stems.items(), key=lambda x: float(x[1]))[0]
                self._main_stem[str(br)] = str(main)

    def get_branch_hidden_stems(self) -> Dict[str, Dict[str, float]]:
        self.ensure_loaded()
        return {k: dict(v) for k, v in self._hidden.items()}

    def get_branch_main_stem(self) -> Dict[str, str]:
        self.ensure_loaded()
        return dict(self._main_stem)

    def get_resonance_coeffs(self) -> Dict[str, float]:
        self.ensure_loaded()
        return dict(self._resonance)

    def hidden_tier(self, branch: str, stem: str) -> str:
        row = self._hidden.get(str(branch), {})
        return _tier_for_stem(str(branch), str(stem), row)


def sync_l0_from_defaults() -> Tuple[int, int, int]:
    """将 `physics_rules` 中常量 Upsert 至 L0 三表；返回 (element_rows, hidden_rows, rule_rows) 写入计数近似。"""
    from app.skills.physics_rules import BRANCH_HIDDEN_STEMS, STEM_TO_ELEMENT, STEM_YIN_YANG

    ne, nh, nr = 0, 0, 0
    with session_scope() as s:
        for stem, el in STEM_TO_ELEMENT.items():
            pol = STEM_YIN_YANG.get(stem)
            row = s.get(L0ElementRegistry, stem)
            if row is None:
                s.add(L0ElementRegistry(glyph=stem, kind="stem", element=el, polarity=pol))
                ne += 1
            else:
                row.element = el
                row.kind = "stem"
                row.polarity = pol
                s.add(row)
        for br, el in BRANCH_PRIMARY_ELEMENT.items():
            row = s.get(L0ElementRegistry, br)
            if row is None:
                s.add(L0ElementRegistry(glyph=br, kind="branch", element=el, polarity=None))
                ne += 1
            else:
                row.element = el
                row.kind = "branch"
                row.polarity = None
                s.add(row)

        for br, stems in BRANCH_HIDDEN_STEMS.items():
            for hid, ratio in stems.items():
                tier = _tier_for_stem(str(br), str(hid), dict(stems))
                tier_l = tier.lower()
                row = s.exec(
                    select(L0BranchHiddenSchema).where(
                        L0BranchHiddenSchema.branch == str(br),
                        L0BranchHiddenSchema.hidden_stem == str(hid),
                    )
                ).first()
                if row is None:
                    s.add(
                        L0BranchHiddenSchema(
                            branch=str(br),
                            hidden_stem=str(hid),
                            ratio_pct=float(ratio),
                            tier=tier_l,
                        )
                    )
                    nh += 1
                else:
                    row.ratio_pct = float(ratio)
                    row.tier = tier_l
                    s.add(row)

        for k, v in _DEFAULT_RESONANCE.items():
            row = s.get(L0ResonanceRules, k)
            if row is None:
                s.add(L0ResonanceRules(rule_key=k, coefficient=float(v), description="L0 通根分层默认系数"))
                nr += 1
            else:
                row.coefficient = float(v)
                s.add(row)
    L0PluginManager.instance().bump_cache()
    return ne, nh, nr
