"""
UniversalPatternEngine：L2 格局判定，阈值/门控/排除/共振全部来自 pattern_manifest.json。
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Tuple

from app.logic.pattern_physics import temporal_volatility_for_pattern
from app.skills.physics_rules import STEM_TO_ELEMENT, deity_element_map

_DEITY_TO_CLIMATE_GROUP: Dict[str, str] = {
    "比肩": "比劫",
    "劫财": "比劫",
    "食神": "食伤",
    "伤官": "食伤",
    "偏财": "财星",
    "正财": "财星",
    "七杀": "官杀",
    "正官": "官杀",
    "偏印": "印星",
    "正印": "印星",
}


def _climate_element_mods_from_meta(meta: Mapping[str, Any]) -> Dict[str, float]:
    raw = meta.get("climate_field_correction_v1") if isinstance(meta, dict) else None
    if not isinstance(raw, dict):
        return {}
    em = raw.get("element_mods")
    if not isinstance(em, dict):
        return {}
    out: Dict[str, float] = {}
    for k in ("wood", "fire", "earth", "metal", "water"):
        v = em.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            out[k] = float(v)
    return out


def _day_master_element_for_climate(meta: Mapping[str, Any], metadata: Optional[Mapping[str, Any]]) -> str:
    dm = ""
    if isinstance(metadata, dict):
        pillars = metadata.get("pillars")
        if isinstance(pillars, dict):
            day = pillars.get("day")
            if isinstance(day, dict):
                dm = str(day.get("stem") or "").strip()
    if not dm and isinstance(meta, dict):
        pillars = meta.get("pillars")
        if isinstance(pillars, dict):
            day = pillars.get("day")
            if isinstance(day, dict):
                dm = str(day.get("stem") or "").strip()
    return str(STEM_TO_ELEMENT.get(dm, "") or "")

_MANIFEST_DIR = Path(__file__).resolve().parent
_DEFAULT_MANIFEST_PATH = _MANIFEST_DIR / "pattern_manifest.json"
_LOG = logging.getLogger(__name__)


def _debug_mode() -> bool:
    """与常见栈对齐：DEBUG / QIAZHI_DEBUG 为真时视为开发态，跳过法典磁盘签名校验。"""
    v = (os.environ.get("DEBUG") or os.environ.get("QIAZHI_DEBUG") or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _pytest_active() -> bool:
    return bool(os.environ.get("PYTEST_CURRENT_TEST"))


def _manifest_signature_enforced() -> bool:
    """
    生产级签名校验：非 DEBUG 且非 pytest 时，对从磁盘加载的 JSON 字节做 SHA256 比对。
    可通过 QIAZHI_PATTERN_MANIFEST_SIGNATURE=0|off|skip 显式关闭（应急运维）。
    期望哈希：环境变量 QIAZHI_PATTERN_MANIFEST_EXPECTED_SHA256（64 hex），
    否则读取与 JSON 同目录、同主文件名的 ``*.sha256``（如 pattern_manifest.sha256）。
    """
    if _debug_mode() or _pytest_active():
        return False
    raw = (os.environ.get("QIAZHI_PATTERN_MANIFEST_SIGNATURE") or "").strip().lower()
    if raw in ("0", "off", "false", "skip", "no"):
        if not _debug_mode() and not _pytest_active():
            _LOG.warning(
                "pattern_manifest disk SHA256 verification is OFF (QIAZHI_PATTERN_MANIFEST_SIGNATURE=%r). "
                "Unset in production unless intentionally bypassing integrity checks.",
                os.environ.get("QIAZHI_PATTERN_MANIFEST_SIGNATURE"),
            )
        return False
    return True


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _expected_manifest_sha256_hex(manifest_path: Path) -> str:
    env = (os.environ.get("QIAZHI_PATTERN_MANIFEST_EXPECTED_SHA256") or "").strip().lower()
    if env:
        if len(env) != 64 or any(c not in "0123456789abcdef" for c in env):
            raise ValueError("QIAZHI_PATTERN_MANIFEST_EXPECTED_SHA256 must be 64 lowercase hex chars")
        return env
    sig_path = manifest_path.with_suffix(".sha256")
    if not sig_path.is_file():
        raise FileNotFoundError(
            f"Missing manifest signature file {sig_path.name} beside {manifest_path.name} "
            f"(or set QIAZHI_PATTERN_MANIFEST_EXPECTED_SHA256). Required when not in DEBUG."
        )
    line = sig_path.read_text(encoding="utf-8").strip().splitlines()[0].strip().split()[0]
    line = line.lower()
    if len(line) != 64 or any(c not in "0123456789abcdef" for c in line):
        raise ValueError(f"Invalid SHA256 in {sig_path}")
    return line


def disk_signature_check_failure(manifest_path: Path, raw_bytes: bytes) -> Optional[Dict[str, Any]]:
    """
    磁盘法典签名校验。通过返回 None；失败返回 ``{"status": "SIGNATURE_ERROR", ...}`` 载荷（已打 error 日志），**不抛异常**。
    """
    if not _manifest_signature_enforced():
        return None
    try:
        expected = _expected_manifest_sha256_hex(manifest_path)
    except FileNotFoundError as e:
        _LOG.error("pattern_manifest signature file missing: %s", e)
        return {"status": "SIGNATURE_ERROR", "detail": str(e), "code": "SIGNATURE_FILE_MISSING", "path": str(manifest_path)}
    except ValueError as e:
        _LOG.error("pattern_manifest signature config invalid: %s", e)
        return {"status": "SIGNATURE_ERROR", "detail": str(e), "code": "SIGNATURE_CONFIG", "path": str(manifest_path)}
    got = _sha256_hex(raw_bytes).lower()
    if got != expected:
        _LOG.error(
            "pattern_manifest SHA256 mismatch path=%s expected_prefix=%s got_prefix=%s",
            manifest_path,
            expected[:16],
            got[:16],
        )
        return {
            "status": "SIGNATURE_ERROR",
            "detail": "SHA256_MISMATCH",
            "code": "SHA256_MISMATCH",
            "expected_prefix": expected[:16],
            "got_prefix": got[:16],
            "path": str(manifest_path),
        }
    return None


def get_pattern_manifest_path() -> Path:
    """默认仓库内 JSON；测试或运维可通过 `QIAZHI_PATTERN_MANIFEST_PATH` 覆盖。"""
    raw = (os.environ.get("QIAZHI_PATTERN_MANIFEST_PATH") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return _DEFAULT_MANIFEST_PATH


def _manifest_codex_fingerprint(manifest: Mapping[str, Any]) -> str:
    """本次 evaluate 所用 manifest 内容指纹（与磁盘 mtime 解耦，热替换 dict 亦可审计）。"""
    blob = json.dumps(dict(manifest), sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:20]


def _manifest_disk_fingerprint_note() -> str:
    try:
        p = get_pattern_manifest_path()
        if p.is_file():
            st = p.stat()
            return f"disk={int(st.st_mtime_ns)}:{int(st.st_size)}"
    except OSError:
        pass
    return "disk=unavailable"


def _as_float(x: Any, default: float = 0.0) -> float:
    if isinstance(x, bool):
        return default
    if isinstance(x, (int, float)):
        v = float(x)
        return v if v == v else default
    return default


def _intention_context_dict(meta_bundle: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if not isinstance(meta_bundle, dict):
        return {}
    raw = meta_bundle.get("intention_context")
    return dict(raw) if isinstance(raw, dict) else {}


def _as_bool(x: Any, default: bool = False) -> bool:
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, float)):
        return bool(x)
    return default


def _float_dict(d: Any) -> Dict[str, float]:
    out: Dict[str, float] = {}
    if not isinstance(d, dict):
        return out
    for k, v in d.items():
        ks = str(k).strip()
        if not ks:
            continue
        fv = _as_float(v, float("nan"))
        if fv == fv and fv >= 0.0:
            out[ks] = fv
    return out


def _deity_scores_norm(tensor: Mapping[str, Any]) -> Dict[str, float]:
    return _float_dict(tensor.get("deity_scores"))


def _deity_fraction_map(tensor: Mapping[str, Any]) -> Dict[str, float]:
    """兼容 physics 引擎（0–100 累加）与单测/草稿张量（0–1 小数）。"""
    raw = _deity_scores_norm(tensor)
    if not raw:
        return {}
    tot = sum(raw.values())
    if tot <= 1.05:
        return {k: max(0.0, min(1.0, float(v))) for k, v in raw.items()}
    return {k: max(0.0, min(1.0, float(v) / 100.0)) for k, v in raw.items()}


def _axis_value_from_axes(
    tensor: Mapping[str, Any],
    deities: List[str],
    mode: str,
) -> float:
    axes = tensor.get("deity_energy_axes")
    if isinstance(axes, dict) and mode == "absolute_energy_sum":
        s = 0.0
        for d in deities:
            b = axes.get(d)
            if isinstance(b, dict):
                s += max(0.0, _as_float(b.get("absolute_energy"), 0.0))
        return float(s)
    frac = _deity_fraction_map(tensor)
    s = sum(frac.get(d, 0.0) for d in deities)
    return float(s)


def _dominant_deity_on_axis(tensor: Mapping[str, Any], deities: List[str]) -> Optional[str]:
    frac = _deity_fraction_map(tensor)
    best: Optional[str] = None
    best_v = -1.0
    for d in deities:
        v = frac.get(d, 0.0)
        if v > best_v:
            best_v = v
            best = d
    return best


def _month_branch(meta: Mapping[str, Any], metadata: Optional[Mapping[str, Any]]) -> str:
    mb = str(meta.get("month_branch") or "").strip()
    if mb:
        return mb
    if isinstance(metadata, dict):
        pillars = metadata.get("pillars")
        if isinstance(pillars, dict):
            month = pillars.get("month")
            if isinstance(month, dict):
                b = str(month.get("branch") or "").strip()
                if b:
                    return b
    return ""


def _active_structure_tags(meta: Mapping[str, Any]) -> List[str]:
    raw = meta.get("active_structures")
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for x in raw:
        s = str(x).strip()
        if s:
            out.append(s)
    return out


def _iter_specs(manifest: Mapping[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    rows: List[Tuple[str, Dict[str, Any]]] = []
    for section in ("STANDARD_OCTAD", "SPECIAL_PATTERNS"):
        block = manifest.get(section)
        if not isinstance(block, dict):
            continue
        for _k, spec in block.items():
            if isinstance(spec, dict) and str(spec.get("id") or "").strip():
                rows.append((str(section), spec))
    return rows


def load_pattern_manifest(
    source: Optional[Mapping[str, Any] | str | Path] = None,
) -> Dict[str, Any]:
    if source is None:
        path = get_pattern_manifest_path()
        try:
            raw = path.read_bytes()
        except OSError as e:
            _LOG.error("pattern_manifest read failed: %s", e)
            return {"status": "SIGNATURE_ERROR", "detail": str(e), "code": "READ_ERROR", "path": str(path)}
        sig_err = disk_signature_check_failure(path, raw)
        if sig_err:
            return sig_err
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as e:
            _LOG.error("pattern_manifest JSON invalid: %s", e)
            return {"status": "SIGNATURE_ERROR", "detail": str(e), "code": "JSON_DECODE", "path": str(path)}
    if isinstance(source, (str, Path)):
        path = Path(source).expanduser().resolve()
        try:
            raw = path.read_bytes()
        except OSError as e:
            _LOG.error("pattern_manifest read failed: %s", e)
            return {"status": "SIGNATURE_ERROR", "detail": str(e), "code": "READ_ERROR", "path": str(path)}
        sig_err = disk_signature_check_failure(path, raw)
        if sig_err:
            return sig_err
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as e:
            _LOG.error("pattern_manifest JSON invalid: %s", e)
            return {"status": "SIGNATURE_ERROR", "detail": str(e), "code": "JSON_DECODE", "path": str(path)}
    if isinstance(source, Mapping):
        return dict(source)
    raise TypeError("source must be None, Path/str, or Mapping")


class UniversalPatternEngine:
    """每次实例化可从磁盘重新读取 manifest（改 JSON 后下一轮请求即生效，无需重启进程）。"""

    _EMPTY_MANIFEST: Dict[str, Any] = {
        "ENGINE": {},
        "ENGINE_CONSTANTS": {},
        "AXIS_REGISTRY": {},
        "TRACE_LABELS": {},
        "MONTH_BRANCH_STRENGTH_BY_DEITY": {},
        "STANDARD_OCTAD": {},
        "SPECIAL_PATTERNS": {},
    }

    def __init__(self, manifest: Optional[Mapping[str, Any] | str | Path] = None) -> None:
        loaded = load_pattern_manifest(manifest)
        if isinstance(loaded, dict) and loaded.get("status") == "SIGNATURE_ERROR":
            self._manifest = dict(self._EMPTY_MANIFEST)
            self._manifest_signature_error: Optional[Dict[str, Any]] = loaded
        else:
            self._manifest = loaded
            self._manifest_signature_error = None

    @property
    def manifest_signature_error(self) -> Optional[Dict[str, Any]]:
        """磁盘签名校验失败时的载荷；正常加载时为 None。"""
        return self._manifest_signature_error

    @property
    def manifest(self) -> Mapping[str, Any]:
        return self._manifest

    def _engine_cfg(self) -> Dict[str, Any]:
        """ENGINE 与 ENGINE_CONSTANTS 合并，后者覆盖前者（分析师可只改 CONSTANTS 段落）。"""
        eng = self._manifest.get("ENGINE")
        ovr = self._manifest.get("ENGINE_CONSTANTS")
        out: Dict[str, Any] = {}
        if isinstance(eng, dict):
            out.update(eng)
        if isinstance(ovr, dict):
            out.update(ovr)
        return out

    def _trace_labels(self) -> Dict[str, str]:
        raw = self._manifest.get("TRACE_LABELS")
        if not isinstance(raw, dict):
            return {}
        return {str(k).strip(): str(v).strip() for k, v in raw.items() if str(k).strip() and str(v).strip()}

    def _axis_registry(self) -> Dict[str, Any]:
        reg = self._manifest.get("AXIS_REGISTRY")
        return reg if isinstance(reg, dict) else {}

    def _month_strength_table(self) -> Dict[str, Any]:
        t = self._manifest.get("MONTH_BRANCH_STRENGTH_BY_DEITY")
        return t if isinstance(t, dict) else {}

    def _axis_deities(self, axis_key: str) -> List[str]:
        reg = self._axis_registry()
        entry = reg.get(axis_key)
        if not isinstance(entry, dict):
            return []
        raw = entry.get("deities")
        if not isinstance(raw, list):
            return []
        return [str(x).strip() for x in raw if str(x).strip()]

    def _climate_axis_multiplier(
        self,
        tensor: Mapping[str, Any],
        axis_key: str,
        meta_bundle: Optional[Mapping[str, Any]],
        metadata: Optional[Mapping[str, Any]],
    ) -> float:
        """V8.0：按调候插件写入的 ``element_mods``，对单轴能量做加权乘子（基于日干十神→五行归属）。"""
        if not isinstance(meta_bundle, dict):
            return 1.0
        mods = _climate_element_mods_from_meta(meta_bundle)
        if not mods:
            return 1.0
        self_el = _day_master_element_for_climate(meta_bundle, metadata)
        if not self_el:
            return 1.0
        cat_map = deity_element_map(self_el)
        deities = self._axis_deities(axis_key)
        if not deities:
            return 1.0
        frac = _deity_fraction_map(tensor)
        den = sum(max(0.0, float(frac.get(d, 0.0))) for d in deities)
        if den <= 1e-12:
            return 1.0
        num = 0.0
        for d in deities:
            g = _DEITY_TO_CLIMATE_GROUP.get(str(d).strip())
            if not g:
                continue
            el = cat_map.get(g)
            if not el:
                continue
            w = max(0.0, float(frac.get(d, 0.0)))
            num += w * float(mods.get(el, 1.0))
        q = num / den
        return max(0.25, min(1.75, float(q)))

    def _axis_energy(
        self,
        tensor: Mapping[str, Any],
        axis_key: str,
        *,
        meta_bundle: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> float:
        mode = str(self._engine_cfg().get("axis_value_mode") or "relative_percentage_sum")
        deities = self._axis_deities(axis_key)
        if not deities:
            return 0.0
        if mode == "absolute_energy_sum":
            base = _axis_value_from_axes(tensor, deities, "absolute_energy_sum")
        else:
            base = _axis_value_from_axes(tensor, deities, "relative_percentage_sum")
        m = self._climate_axis_multiplier(tensor, axis_key, meta_bundle, metadata)
        v = float(base) * float(m)
        # V10.1：求财抬升财星轴「生扶/显化」等效能量（EFF_PROMOTING 语义，读 intention_context 标量）
        icx = _intention_context_dict(meta_bundle)
        if axis_key == "Wealth_Axis":
            scale = _as_float(icx.get("l2_wealth_axis_eff_scale"), float("nan"))
            if scale == scale and scale > 1.0:
                v *= max(0.85, min(1.35, float(scale)))
        return v

    def _month_gate_multiplier(
        self,
        *,
        tensor: Mapping[str, Any],
        meta: Mapping[str, Any],
        metadata: Optional[Mapping[str, Any]],
        primary_axis: str,
        gating: Mapping[str, Any],
    ) -> Tuple[float, List[str]]:
        trace: List[str] = []
        month = _month_branch(meta, metadata)
        mgc = gating.get("month_gate_custom")
        if isinstance(mgc, list) and mgc:
            allowed = [str(x).strip() for x in mgc if str(x).strip()]
            if not month:
                trace.append("month_gate_custom:skip_no_month_branch")
                return 1.0, trace
            if month in allowed:
                trace.append(f"month_gate_custom:pass_branch={month}")
                return 1.0, trace
            w = _as_float(self._engine_cfg().get("month_gate_weight"), 0.3)
            w = max(0.0, min(1.0, w))
            trace.append(f"month_gate_custom:penalize_branch={month}_weight={w}")
            return w, trace

        if not _as_bool(gating.get("month_gate"), False):
            trace.append("month_gate:off")
            return 1.0, trace
        if not month:
            trace.append("month_gate:skip_no_month_branch")
            return 1.0, trace
        deities = self._axis_deities(primary_axis)
        dom = _dominant_deity_on_axis(tensor, deities)
        if not dom:
            trace.append("month_gate:skip_no_dominant_deity")
            return 1.0, trace
        tbl = self._month_strength_table()
        row = tbl.get(dom)
        strong: List[str] = []
        if isinstance(row, dict):
            br = row.get("strong_branches")
            if isinstance(br, list):
                strong = [str(x).strip() for x in br if str(x).strip()]
        if not strong:
            trace.append(f"month_gate:pass_no_table_for_deity={dom}")
            return 1.0, trace
        if month in strong:
            trace.append(f"month_gate:pass_branch={month}_deity={dom}")
            return 1.0, trace
        w = _as_float(self._engine_cfg().get("month_gate_weight"), 0.3)
        w = max(0.0, min(1.0, w))
        trace.append(f"month_gate:penalize_branch={month}_deity={dom}_weight={w}")
        return w, trace

    def _self_gate_multiplier(
        self,
        tensor: Mapping[str, Any],
        gating: Mapping[str, Any],
        *,
        meta_bundle: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Tuple[float, List[str]]:
        trace: List[str] = []
        if "max_self_energy" not in gating:
            return 1.0, trace
        cap = _as_float(gating.get("max_self_energy"), float("nan"))
        if cap != cap:
            return 1.0, trace
        self_e = self._axis_energy(tensor, "Self_Axis", meta_bundle=meta_bundle, metadata=metadata)
        if self_e <= cap + 1e-9:
            trace.append(f"self_gate:pass_self={self_e:.4f}_cap={cap:.4f}")
            return 1.0, trace
        ratio = cap / max(self_e, 1e-9)
        trace.append(f"self_gate:scale_self={self_e:.4f}_cap={cap:.4f}_ratio={ratio:.4f}")
        return max(0.0, min(1.0, ratio)), trace

    def _base_affinity(self, primary_e: float, gating: Mapping[str, Any]) -> Tuple[float, List[str]]:
        trace: List[str] = []
        min_e = _as_float(gating.get("min_energy"), float("nan"))
        if min_e != min_e or min_e <= 0.0:
            trace.append("base:invalid_min_energy")
            return 0.0, trace
        mode = str(self._engine_cfg().get("base_score_mode") or "ratio_to_min_energy")
        if mode == "ratio_to_min_energy":
            raw = primary_e / max(min_e, 1e-9)
            score = max(0.0, min(1.0, raw * 0.92))
            trace.append(f"base:primary={primary_e:.4f}_min={min_e:.4f}_affinity={score:.4f}")
            return score, trace
        dev = abs(primary_e - min_e)
        score = max(0.0, min(1.0, 1.0 - dev / max(min_e, 0.05)))
        trace.append(f"base:deviation_mode_primary={primary_e:.4f}_min={min_e:.4f}_affinity={score:.4f}")
        return score, trace

    @staticmethod
    def _will_adjust_exclusion_threshold(axis_key: str, thr: float, ic: Mapping[str, Any]) -> float:
        """V10.1：意志重塑法典红线阈值（系数由 WILL_PROXY 写入 intention_context）。"""
        if thr != thr or not str(ic.get("active_intention") or "").strip():
            return thr
        if axis_key == "Robber_Axis":
            f = _as_float(ic.get("l2_robber_exclusion_relax_factor"), float("nan"))
            if f == f and f > 1.0:
                return max(0.001, min(0.95, thr * f))
        if axis_key in ("Output_Axis", "Seal_Axis"):
            f = _as_float(ic.get("l2_output_seal_exclusion_tight_factor"), float("nan"))
            if f == f and 0.0 < f < 1.0:
                return max(0.001, min(0.95, thr * f))
        return thr

    def _exclusion_eval(
        self,
        tensor: Mapping[str, Any],
        exclusions: Mapping[str, Any],
        *,
        meta_bundle: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        intention_context: Optional[Mapping[str, Any]] = None,
    ) -> Tuple[bool, List[str], List[str]]:
        """返回 (是否触发红线, 机器 trace, 人读拦截句)。"""

        hits: List[str] = []
        zh: List[str] = []
        labels = self._trace_labels()
        ic = intention_context if isinstance(intention_context, dict) else {}
        if not isinstance(exclusions, dict):
            return False, hits, zh
        for axis_key, thr_any in exclusions.items():
            ax = str(axis_key).strip()
            thr = _as_float(thr_any, float("nan"))
            if ax and thr == thr:
                thr_eff = self._will_adjust_exclusion_threshold(ax, float(thr), ic)
                val = self._axis_energy(tensor, ax, meta_bundle=meta_bundle, metadata=metadata)
                if val > thr_eff + 1e-12:
                    hits.append(f"exclusion:{ax}={val:.4f}>{thr_eff:.4f}")
                    lab = labels.get(ax, ax)
                    zh.append(f"[拦截] {lab} 权重 {val:.2f} > 阈值 {thr_eff:.2f}")
        return bool(hits), hits, zh

    def _exclusion_axis_snapshots(
        self,
        tensor: Mapping[str, Any],
        exclusions: Mapping[str, Any],
        *,
        meta_bundle: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        intention_context: Optional[Mapping[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """各红线轴：当前能量 vs 阈值（供 Admin 可视化）。"""
        labels = self._trace_labels()
        out: List[Dict[str, Any]] = []
        ic = intention_context if isinstance(intention_context, dict) else {}
        if not isinstance(exclusions, dict):
            return out
        for axis_key, thr_any in exclusions.items():
            ax = str(axis_key).strip()
            thr = _as_float(thr_any, float("nan"))
            if not ax or thr != thr:
                continue
            thr_eff = self._will_adjust_exclusion_threshold(ax, float(thr), ic)
            val = self._axis_energy(tensor, ax, meta_bundle=meta_bundle, metadata=metadata)
            lab = labels.get(ax, ax)
            out.append(
                {
                    "axis": ax,
                    "label_zh": lab,
                    "energy": float(val),
                    "threshold": float(thr_eff),
                    "triggered": bool(val > thr_eff + 1e-12),
                }
            )
        return out

    def _resonance_bonus(self, meta: Mapping[str, Any], resonance: Mapping[str, Any]) -> Tuple[float, List[str]]:
        trace: List[str] = []
        if not isinstance(resonance, dict) or not resonance:
            return 0.0, trace
        tags = set(_active_structure_tags(meta))
        cap = _as_float(self._engine_cfg().get("resonance_cap"), 0.25)
        acc = 0.0
        for label_any, w_any in resonance.items():
            lab = str(label_any).strip()
            w = _as_float(w_any, 0.0)
            if lab and lab in tags and w > 0.0:
                acc += w
                trace.append(f"resonance:hit_{lab}+{w:.4f}")
        acc = max(0.0, min(cap, acc))
        if not trace:
            trace.append("resonance:none")
        return acc, trace

    def evaluate(
        self,
        physics_tensor: Mapping[str, Any],
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        tensor = dict(physics_tensor) if not isinstance(physics_tensor, dict) else physics_tensor
        raw_meta = tensor.get("meta")
        # 外置 metadata（冲突矩阵、pillars 等）与 tensor.meta 合并；后者覆盖前者，避免调度层字段被丢弃。
        merged: Dict[str, Any] = {}
        if isinstance(metadata, dict):
            merged.update(metadata)
        if isinstance(raw_meta, dict):
            merged.update(raw_meta)
        meta = merged
        meta_bundle: Mapping[str, Any] = meta

        codex_fp = _manifest_codex_fingerprint(self._manifest)
        disk_note = _manifest_disk_fingerprint_note()
        codex_line = f"[CODEX_LOAD] manifest_sha20={codex_fp} {disk_note} path={get_pattern_manifest_path()}"

        out_rows: List[Dict[str, Any]] = []
        for _section, spec in _iter_specs(self._manifest):
            pid = str(spec.get("id") or "").strip()
            display = str(spec.get("display_name") or pid).strip()
            primary = str(spec.get("primary_axis") or "").strip()
            gating = spec.get("gating") if isinstance(spec.get("gating"), dict) else {}
            exclusions = spec.get("exclusions") if isinstance(spec.get("exclusions"), dict) else {}
            resonance = spec.get("resonance") if isinstance(spec.get("resonance"), dict) else {}
            i18n_key = str(spec.get("i18n_key") or "").strip()
            description = str(spec.get("description") or "").strip() or None

            ic = _intention_context_dict(meta_bundle)
            primary_e = self._axis_energy(tensor, primary, meta_bundle=meta_bundle, metadata=metadata)
            # V7.0 匹配度（manifest-only）：
            # core = 能量基准分(主轴 vs min_energy) × 月令调节系数(月令门×身宫门) + 法典共振加成分；
            # affinity = max(0, core − 红线拦截惩罚)；惩罚量由 ENGINE.exclusion_hit_zero 决定硬归零或软衰减。
            gating_eff: Dict[str, Any] = dict(gating) if isinstance(gating, dict) else {}
            if primary in ("Gov_Axis", "Kill_Axis"):
                me0 = _as_float(gating_eff.get("min_energy"), float("nan"))
                if me0 == me0:
                    sc = _as_float(ic.get("l2_officer_min_energy_scale"), float("nan"))
                    if sc == sc and sc > 1.0:
                        gating_eff["min_energy"] = float(min(0.92, me0 * sc))
            energy_base, t_base = self._base_affinity(primary_e, gating_eff)
            m_mul, t_month = self._month_gate_multiplier(
                tensor=tensor,
                meta=meta_bundle,
                metadata=metadata,
                primary_axis=primary,
                gating=gating,
            )
            s_mul, t_self = self._self_gate_multiplier(tensor, gating, meta_bundle=meta_bundle, metadata=metadata)
            month_modulator = float(m_mul) * float(s_mul)
            r_bonus, t_res = self._resonance_bonus(meta_bundle, resonance)

            core_match = max(0.0, min(1.0, energy_base * month_modulator + r_bonus))
            excl, excl_hits, excl_zh = self._exclusion_eval(
                tensor,
                exclusions,
                meta_bundle=meta_bundle,
                metadata=metadata,
                intention_context=ic,
            )
            excl_snap = self._exclusion_axis_snapshots(
                tensor,
                exclusions,
                meta_bundle=meta_bundle,
                metadata=metadata,
                intention_context=ic,
            )
            hard_zero = _as_bool(self._engine_cfg().get("exclusion_hit_zero"), True)
            if excl and hard_zero:
                redline_penalty = core_match
                affinity = max(0.0, min(1.0, core_match - redline_penalty))
            elif excl:
                redline_penalty = core_match * 0.85
                affinity = max(0.0, min(1.0, core_match - redline_penalty))
            else:
                affinity = core_match

            # 意志后亲和度：Base_Affinity（红线后）× pattern_affinity_multipliers（Will_Multiplier）
            pre_will_proxy = float(affinity)
            aff_mult = 1.0
            if str(ic.get("active_intention") or "").strip():
                pm = ic.get("pattern_affinity_multipliers")
                if isinstance(pm, dict) and pid in pm:
                    try:
                        aff_mult = float(pm.get(pid) or 1.0)
                    except (TypeError, ValueError):
                        aff_mult = 1.0
                aff_mult = max(0.65, min(1.35, aff_mult))
            affinity = max(0.0, min(1.0, pre_will_proxy * aff_mult))
            if aff_mult != 1.0:
                trace_logic_pre_will: List[str] = [
                    f"will_proxy:affinity=Base*{aff_mult:.4f}_base={pre_will_proxy:.4f}_post={affinity:.4f}"
                ]
            else:
                trace_logic_pre_will = []

            min_e_raw = _as_float(gating_eff.get("min_energy"), float("nan"))
            axis_gate_ok = not (min_e_raw == min_e_raw) or (primary_e + 1e-12 >= min_e_raw)
            gate_result = "PASS" if axis_gate_ok else "FAIL"
            if min_e_raw == min_e_raw:
                gating_line = (
                    f"[GATING_CHECK] {pid}: Axis={primary_e:.4f} Req={min_e_raw:.4f} "
                    f"Result={gate_result} MonthMul={m_mul:.4f} SelfMul={s_mul:.4f}"
                )
            else:
                gating_line = (
                    f"[GATING_CHECK] {pid}: Axis={primary_e:.4f} Req=INVALID "
                    f"Result=SKIP MonthMul={m_mul:.4f} SelfMul={s_mul:.4f}"
                )

            excl_check_lines: List[str] = []
            for snap in excl_snap:
                if snap.get("triggered"):
                    excl_check_lines.append(
                        "[EXCLUSION_CHECK] "
                        f"{pid}: axis={snap.get('axis')} "
                        f"energy={float(snap.get('energy', 0.0)):.4f}>thr={float(snap.get('threshold', 0.0)):.4f}"
                    )

            trace_logic: List[str] = [
                codex_line,
                gating_line,
                *excl_check_lines,
                *t_base,
                *t_month,
                *t_self,
                *t_res,
                *trace_logic_pre_will,
            ]
            trace_display_zh: List[str] = []
            if excl:
                trace_logic.extend(excl_hits)
                trace_display_zh.extend(excl_zh)
                trace_logic.append("affinity_forced_zero:exclusions" if hard_zero else "affinity_soft_penalty:exclusions")
            else:
                trace_logic.append(f"core_match={core_match:.4f}_final={affinity:.4f}")

            aff_pre_will_field: Optional[float] = pre_will_proxy if str(ic.get("active_intention") or "").strip() else None

            tv = temporal_volatility_for_pattern(display, meta_bundle if isinstance(meta_bundle, dict) else {})
            base_stab = max(0.0, min(1.0, 1.0 - abs(primary_e - _as_float(gating_eff.get("min_energy"), 0.28)) * 1.2))
            stab = max(0.0, min(1.0, float(base_stab) * (1.0 - 0.62 * float(tv))))

            max_self_raw = _as_float(gating.get("max_self_energy"), float("nan"))
            out_rows.append(
                {
                    "pattern_id": pid,
                    "name": display,
                    "primary_axis": primary or None,
                    "i18n_key": i18n_key or None,
                    "description": description,
                    "progress": float(affinity),
                    "affinity_score": float(affinity),
                    "pre_exclusion_affinity": float(core_match),
                    **({"affinity_pre_will_proxy": float(aff_pre_will_field)} if aff_pre_will_field is not None else {}),
                    "primary_axis_energy": float(primary_e),
                    "gating_min_energy": float(min_e_raw) if min_e_raw == min_e_raw else None,
                    "gating_max_self_energy": float(max_self_raw) if max_self_raw == max_self_raw else None,
                    "exclusion_axis_snapshots": excl_snap,
                    "stability": float(stab),
                    "temporal_volatility": float(tv),
                    "trace_logic": trace_logic,
                    "trace_display_zh": trace_display_zh,
                    "exclusion_hit": bool(excl),
                    "engine_v": "MANIFEST_V5.8_STRICT",
                }
            )

        out_rows.sort(key=lambda r: float(r.get("affinity_score", 0.0)), reverse=True)

        rank_lines: List[str] = []
        for i, r in enumerate(out_rows[:3], start=1):
            rid = str(r.get("pattern_id") or "")
            aff = float(r.get("affinity_score", 0.0) or 0.0)
            ex = bool(r.get("exclusion_hit"))
            rank_lines.append(f"[FINAL_RANKING] #{i} {rid} affinity={aff:.4f} exclusion_hit={ex}")
        if len(out_rows) > 3:
            rank_lines.append(f"[FINAL_RANKING] ... total_patterns={len(out_rows)}")
        elif not out_rows:
            rank_lines.append("[FINAL_RANKING] #empty")

        if rank_lines:
            for r in out_rows:
                tl = list(r.get("trace_logic") or [])
                tl.extend(rank_lines)
                r["trace_logic"] = tl

        return out_rows
