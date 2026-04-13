"""
V6.3 全知推荐：能量补丁 + L1 结构（三合局）预览、LRU 缓存、因果理由合成。
"""
from __future__ import annotations

import copy
import hashlib
import json
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from app.logic.causal_scoring import calculate_decision_score
from app.logic.pattern_physics import calculate_pattern_proximity
from app.logic.reasoning_synthesizer import synthesize_recommendation_reason
from app.logic.structural_override import apply_structural_override
from app.services.helpers.structural_preview_semantics import normalize_structural_preview_hint
from app.services.plugin_service import PluginService

_OPTIONAL_PLUGIN_IDS: Tuple[str, ...] = (
    "classical.blind_school.v1",
    "classical.wangshuai.v1",
    "modern.wealth_risk.v1",
)

_PLUGIN_REASON_TEMPLATES: Dict[str, str] = {
    "classical.blind_school.v1": "启用盲派因果审计，重算做工矢量与门控证据；主推格局「{structure}」达成度约 {progress}%。",
    "classical.wangshuai.v1": "启用旺衰压力审计，柔化身强/身弱误判对格局水位的拉扯；主推「{structure}」约 {progress}%。",
    "modern.wealth_risk.v1": "启用现代财位风险审计，压低极端财杀张力；格局「{structure}」约 {progress}%。",
}

_BUILTIN_PATCH_CANDIDATES: Tuple[Dict[str, Any], ...] = (
    {
        "id": "patch:follower_wealth_bias",
        "deity_scores_delta": {
            "偏财": 0.09,
            "正财": 0.07,
            "比肩": -0.06,
            "劫财": -0.06,
        },
        "reason_template": "柔化比劫夺财张力并抬高财星占比，抬升从财格达成度（配置补丁预览）。",
    },
)

# (candidate_id, enabled_plugins, deity_delta|None, structural_hint|None)
RecoJob = Tuple[str, List[str], Optional[Dict[str, float]], Optional[Dict[str, Any]]]

_CACHE_LOCK = threading.Lock()
_CACHE: "OrderedDict[str, Tuple[float, Dict[str, Any]]]" = OrderedDict()
_CACHE_TTL_SEC = 60.0
_CACHE_MAX = 48


def _pattern_threshold_rows_index(tensor: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    meta = tensor.get("meta") if isinstance(tensor.get("meta"), dict) else {}
    rows = meta.get("pattern_thresholds")
    if not isinstance(rows, list):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        if isinstance(r, dict):
            pid = str(r.get("pattern_id") or "").strip()
            if pid:
                out[pid] = r
    return out


def _trace_logic_excerpt(row: Mapping[str, Any], *, max_lines: int = 4) -> str:
    tl = row.get("trace_logic") if isinstance(row.get("trace_logic"), list) else []
    lines = [str(x).strip() for x in tl if str(x).strip()]
    return "；".join(lines[:max_lines])


def _hydrate_manifest_pattern_rows_if_missing(tensor: Dict[str, Any], md: Dict[str, Any]) -> None:
    """推荐对比前补算 manifest 行（不写入 pattern_thresholds_engine，避免干扰 SSE 分支）。"""
    if not isinstance(tensor, dict):
        return
    meta = tensor.setdefault("meta", {})
    if not isinstance(meta, dict):
        return
    rows = meta.get("pattern_thresholds")
    if isinstance(rows, list) and len(rows) > 0:
        return
    from app.logic.patterns.engine import UniversalPatternEngine

    meta["pattern_thresholds"] = UniversalPatternEngine().evaluate(tensor, md if isinstance(md, dict) else {})


def synthesize_manifest_trace_reason(
    tensor_before: Mapping[str, Any],
    tensor_after: Mapping[str, Any],
) -> str:
    """
    从 meta.pattern_thresholds 的 trace_logic / trace_display_zh 提炼推荐旁白，
    用于「压制忌神、避开红线条款」等可审计语义。
    """
    b = _pattern_threshold_rows_index(tensor_before)
    a = _pattern_threshold_rows_index(tensor_after)
    if not a:
        return ""
    parts: List[str] = []
    for pid, ra in a.items():
        rb = b.get(pid)
        name = str(ra.get("name") or pid).strip()
        zh_a = ra.get("trace_display_zh") if isinstance(ra.get("trace_display_zh"), list) else []
        zh_lines = [str(x).strip() for x in zh_a if str(x).strip()]
        rb_ex = bool(rb and rb.get("exclusion_hit"))
        ra_ex = bool(ra.get("exclusion_hit"))
        stab_b = float(rb.get("stability", 0.0) or 0.0) if isinstance(rb, dict) else 0.0
        stab_a = float(ra.get("stability", 0.0) or 0.0)

        if rb_ex and not ra_ex:
            detail = "；".join(zh_lines[:2]) if zh_lines else _trace_logic_excerpt(ra, max_lines=2)
            parts.append(
                f"裁决者，此意志成功压制忌神轴，避开了「{name}」的逻辑坍塌"
                + (f"；{detail}" if detail else "")
                + "，使稳定性回升。"
            )
        elif isinstance(rb, dict) and (not ra_ex) and stab_a > stab_b + 0.035:
            ex = _trace_logic_excerpt(ra, max_lines=3)
            if ex:
                parts.append(
                    f"裁决者，「{name}」稳定性由约 {stab_b:.0%} 抬升至 {stab_a:.0%}；依据 trace：{ex}。"
                )
    return "\n".join(parts[:2]).strip()


def _cache_prune_unlocked(now: float) -> None:
    dead = [k for k, (exp, _) in _CACHE.items() if exp <= now]
    for k in dead:
        _CACHE.pop(k, None)
    while len(_CACHE) > _CACHE_MAX:
        _CACHE.popitem(last=False)


def invalidate_recommendation_cache() -> None:
    """法典落盘或回滚后清空推荐 LRU，避免 Decision Inbox 命中旧 manifest 语义。"""
    with _CACHE_LOCK:
        _CACHE.clear()


def _pattern_manifest_cache_fingerprint() -> str:
    try:
        from app.logic.patterns.engine import get_pattern_manifest_path

        p = get_pattern_manifest_path()
        if p.is_file():
            st = p.stat()
            return f"{int(st.st_mtime_ns)}:{int(st.st_size)}"
    except OSError:
        pass
    return "0:0"


def _is_physics_param_energy_card(c: Mapping[str, Any]) -> bool:
    ct = str(c.get("cardType") or c.get("card_type") or "").strip()
    prop = c.get("proposal") if isinstance(c.get("proposal"), dict) else {}
    adj = str(prop.get("adjustment_type") or "").strip().upper()
    if ct == "energy-patch":
        return True
    if ct in ("PHYSICS_PARAM", "physics-param"):
        return True
    if ct == "auditor-proposal" and adj == "ENERGY_PATCH":
        return True
    if adj == "UPDATE_PHYSICS_PARAM":
        return True
    return False


def _is_l1_structure_card(c: Mapping[str, Any]) -> bool:
    ct = str(c.get("cardType") or c.get("card_type") or "").strip()
    if ct == "L1_STRUCTURE":
        return True
    cid = str(c.get("id") or "")
    return cid.startswith("inbox-sanhe-")


def _structural_hint_from_card(c: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    raw = c.get("structural_preview_hint") or c.get("structuralPreviewHint")
    if isinstance(raw, dict) and normalize_structural_preview_hint(raw):
        return dict(raw)
    if not _is_l1_structure_card(c):
        return None
    label = str(c.get("displayText") or c.get("title") or "").strip()
    if not label:
        label = str(c.get("title") or "").strip()
    if not label:
        return None
    hint: Dict[str, Any] = {
        "kind": "L1_STRUCTURE",
        "card_id": str(c.get("id") or ""),
        "label": label,
        "plugin_id": "",
        "override_key": "",
    }
    bk = str(c.get("baseline_pattern_kind") or "").strip()
    bn = str(c.get("baseline_pattern_name_zh") or "").strip()
    if bk:
        hint["baseline_pattern_kind"] = bk
    if bn:
        hint["baseline_pattern_name_zh"] = bn
    return hint if normalize_structural_preview_hint(hint) else None


def _recommendation_cache_key(
    *,
    physics_tensor: Dict[str, Any],
    metadata: Dict[str, Any],
    blind_school_features: Dict[str, Any],
    enabled_plugins: List[str],
    inbox_cards: List[Dict[str, Any]],
    top_n: int,
) -> str:
    inbox_sig: List[Any] = []
    for c in sorted(inbox_cards or [], key=lambda x: str((x or {}).get("id") or "")):
        if not isinstance(c, dict):
            continue
        if _is_physics_param_energy_card(c):
            prop = c.get("proposal") if isinstance(c.get("proposal"), dict) else {}
            d = prop.get("energy_deltas")
            if not isinstance(d, dict) or not d:
                continue
            pairs = sorted(
                (str(k).strip(), round(float(v), 6))
                for k, v in d.items()
                if str(k).strip() and isinstance(v, (int, float)) and not isinstance(v, bool)
            )
            inbox_sig.append(
                ["energy", str(c.get("id") or "").strip(), str(c.get("title") or "").strip(), pairs]
            )
        elif _is_l1_structure_card(c):
            h = _structural_hint_from_card(c)
            inbox_sig.append(
                [
                    "l1",
                    str(c.get("id") or "").strip(),
                    str(c.get("title") or "").strip(),
                    json.dumps(h, sort_keys=True, ensure_ascii=False, default=str) if h else "",
                ]
            )
    payload = {
        "tensor": physics_tensor,
        "metadata": metadata,
        "blind": blind_school_features,
        "plugins": list(enabled_plugins),
        "inbox": inbox_sig,
        "top_n": int(top_n),
        "pattern_manifest_fp": _pattern_manifest_cache_fingerprint(),
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _normalize_enabled(raw: Sequence[str] | None) -> List[str]:
    out: List[str] = []
    seen: Set[str] = set()
    for x in raw or []:
        s = str(x).strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _coerce_energy_deltas(raw: Any) -> Dict[str, float]:
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, float] = {}
    for k, v in raw.items():
        ks = str(k).strip()
        if not ks:
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if fv == fv:
            out[ks] = fv
    return out


def _apply_deity_delta(tensor: Dict[str, Any], delta: Mapping[str, float]) -> None:
    ds = tensor.setdefault("deity_scores", {})
    if not isinstance(ds, dict):
        tensor["deity_scores"] = {}
        ds = tensor["deity_scores"]
    for k, v in delta.items():
        ks = str(k).strip()
        if not ks:
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        base = float(ds.get(ks) or 0.0) if isinstance(ds.get(ks), (int, float)) else 0.0
        ds[ks] = max(0.0, base + fv)


def _preview_run(
    svc: PluginService,
    *,
    enabled_plugins: List[str],
    physics_tensor: Dict[str, Any],
    metadata: Dict[str, Any],
    blind_school_features: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    pt = copy.deepcopy(physics_tensor)
    md = copy.deepcopy(metadata)
    bf = copy.deepcopy(blind_school_features) if isinstance(blind_school_features, dict) else blind_school_features
    outputs = svc.run_on_physics_complete(
        enabled_plugins=list(enabled_plugins or []),
        physics_tensor=pt,
        metadata=md,
        blind_school_features=bf if isinstance(bf, dict) else {},
        is_preview=True,
        dry_run=True,
    )
    return outputs, pt


def _dominant_structure_label(tensor: Mapping[str, Any], metadata: Optional[Mapping[str, Any]]) -> Tuple[str, int]:
    rows = calculate_pattern_proximity(tensor, metadata)
    if not rows:
        return "未定", 0
    top = rows[0]
    name = str(top.get("name") or "格局")
    pct = int(round(float(top.get("progress") or 0.0) * 100.0))
    return name, pct


def _fill_reason_templates(
    templates: List[str],
    *,
    tensor_after: Mapping[str, Any],
    metadata: Mapping[str, Any],
) -> str:
    structure, progress = _dominant_structure_label(tensor_after, metadata)
    filled_parts: List[str] = []
    for tpl in templates:
        s = str(tpl or "").strip()
        if not s:
            continue
        try:
            filled_parts.append(
                s.format(structure=structure, progress=progress, name=structure, pct=progress)
            )
        except (KeyError, ValueError):
            filled_parts.append(s.replace("{structure}", structure).replace("{progress}", str(progress)))
    return " ".join(filled_parts).strip()


def _quant_suffix(score_detail: Mapping[str, Any]) -> str:
    raw = score_detail.get("raw") if isinstance(score_detail.get("raw"), dict) else {}
    dp = float(raw.get("follower_progress_after") or 0.0) - float(raw.get("follower_progress_before") or 0.0)
    ds = float(raw.get("follower_stability_after") or 0.0) - float(raw.get("follower_stability_before") or 0.0)
    parts: List[str] = []
    if abs(dp) >= 0.002:
        parts.append(f"达成度{dp * 100:+.1f}%")
    if abs(ds) >= 0.002:
        parts.append(f"稳定性{ds * 100:+.1f}%")
    if not parts:
        return ""
    return " " + " · ".join(parts)


def _collect_reason_templates_for_delta(
    baseline: Set[str], proposed: Sequence[str]
) -> List[str]:
    out: List[str] = []
    prop_set = set(proposed)
    added = sorted(prop_set - baseline)
    for pid in added:
        t = _PLUGIN_REASON_TEMPLATES.get(pid)
        if t:
            out.append(t)
    return out


def _inbox_energy_patch_candidates(
    cards: Optional[List[Dict[str, Any]]], baseline: List[str]
) -> List[RecoJob]:
    out: List[RecoJob] = []
    for c in cards or []:
        if not isinstance(c, dict) or not _is_physics_param_energy_card(c):
            continue
        cid = str(c.get("id") or "").strip()
        if not cid:
            continue
        prop = c.get("proposal") if isinstance(c.get("proposal"), dict) else {}
        deltas = _coerce_energy_deltas(prop.get("energy_deltas"))
        if not deltas:
            continue
        out.append((f"card:{cid}", list(baseline), deltas, None))
    return out


def _l1_structure_candidates(cards: Optional[List[Dict[str, Any]]], baseline: List[str]) -> List[RecoJob]:
    out: List[RecoJob] = []
    for c in cards or []:
        if not isinstance(c, dict):
            continue
        hint = _structural_hint_from_card(c)
        if not hint:
            continue
        cid = str(c.get("id") or "").strip()
        if not cid:
            continue
        out.append((f"l1struct:{cid}", list(baseline), None, hint))
    return out


def _build_card_reason_templates(cards: List[Dict[str, Any]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for c in cards:
        if not isinstance(c, dict) or not _is_physics_param_energy_card(c):
            continue
        cid = str(c.get("id") or "").strip()
        if not cid:
            continue
        prop = c.get("proposal") if isinstance(c.get("proposal"), dict) else {}
        if not _coerce_energy_deltas(prop.get("energy_deltas")):
            continue
        title = str(c.get("title") or "意志能量补丁").strip()
        out[cid] = f"「{title}」十神能量偏移预览：格局「{{structure}}」约 {{progress}}%。"
    return out


def _build_l1_card_reason_templates(cards: List[Dict[str, Any]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for c in cards:
        if not isinstance(c, dict) or not _is_l1_structure_card(c):
            continue
        cid = str(c.get("id") or "").strip()
        if not cid:
            continue
        title = str(c.get("title") or "结构意志").strip()
        out[cid] = f"「{title}」结构预览：{{structure}} 水位约 {{progress}}%。"
    return out


def _enumerate_plugin_candidates(baseline: List[str]) -> List[RecoJob]:
    base = _normalize_enabled(baseline)
    base_set = set(base)
    out: List[RecoJob] = []

    for opt in _OPTIONAL_PLUGIN_IDS:
        if opt not in base_set:
            out.append((f"enable:{opt}", sorted(base_set | {opt}), None, None))
        else:
            nb = [x for x in base if x != opt]
            out.append((f"disable:{opt}", _normalize_enabled(nb), None, None))

    for patch in _BUILTIN_PATCH_CANDIDATES:
        pid = str(patch.get("id") or "patch:unknown")
        delta = patch.get("deity_scores_delta")
        if isinstance(delta, dict) and delta:
            out.append((pid, list(base), dict(delta), None))
    return out


def _patch_reason_template(patch_id: str) -> str:
    for p in _BUILTIN_PATCH_CANDIDATES:
        if str(p.get("id")) == patch_id:
            return str(p.get("reason_template") or "")
    return ""


def _job_sig(job: RecoJob) -> Tuple[Any, ...]:
    cid, plugs, d, sh = job
    dk = frozenset(sorted((str(k), float(v)) for k, v in (d or {}).items()))
    sh_blob = json.dumps(sh, sort_keys=True, ensure_ascii=False, default=str) if sh else ""
    return (cid, tuple(sorted(plugs)), dk, sh_blob)


def _enumerate_all_candidates(baseline: List[str], cards: Optional[List[Dict[str, Any]]]) -> List[RecoJob]:
    seen: Set[Tuple[Any, ...]] = set()
    merged: List[RecoJob] = []
    for job in (
        _enumerate_plugin_candidates(baseline)
        + _inbox_energy_patch_candidates(cards, baseline)
        + _l1_structure_candidates(cards, baseline)
    ):
        s = _job_sig(job)
        if s in seen:
            continue
        seen.add(s)
        merged.append(job)
    return merged


def _action_phrase(candidate_id: str, cards: List[Dict[str, Any]]) -> str:
    if candidate_id.startswith("l1struct:"):
        tail = candidate_id[9:].strip()
        for c in cards:
            if str(c.get("id") or "") == tail:
                return f"通过「{str(c.get('title') or '地支结构锁定')}」预演合局场强"
        return "通过「L1 结构意志」预演合局场强"
    if candidate_id.startswith("card:"):
        tail = candidate_id[5:].strip()
        for c in cards:
            if str(c.get("id") or "") == tail:
                return f"通过「{str(c.get('title') or '意志能量补丁')}」修补十神断裂点"
        return "通过「意志能量补丁」修补十神断裂点"
    if candidate_id.startswith("patch:"):
        return "通过「配置补丁预览」柔化格局张力"
    if candidate_id.startswith("enable:") or candidate_id.startswith("disable:"):
        return f"通过插件开关「{candidate_id}」再校准物理子域"
    return "通过当前候选意志路径"


def get_top_recommendations(
    *,
    physics_tensor: Dict[str, Any],
    metadata: Dict[str, Any],
    blind_school_features: Dict[str, Any],
    enabled_plugins: Sequence[str] | None = None,
    inbox_cards: Optional[List[Dict[str, Any]]] = None,
    plugin_service: Optional[PluginService] = None,
    top_n: int = 3,
    max_workers: int = 8,
) -> Dict[str, Any]:
    svc = plugin_service or PluginService()
    base_list = _normalize_enabled(list(enabled_plugins or []))
    baseline_set = set(base_list)
    cards_list = [c for c in (inbox_cards or []) if isinstance(c, dict)]
    card_reason_templates = _build_card_reason_templates(cards_list)
    l1_reason_templates = _build_l1_card_reason_templates(cards_list)

    cache_key = _recommendation_cache_key(
        physics_tensor=physics_tensor if isinstance(physics_tensor, dict) else {},
        metadata=metadata if isinstance(metadata, dict) else {},
        blind_school_features=blind_school_features if isinstance(blind_school_features, dict) else {},
        enabled_plugins=base_list,
        inbox_cards=cards_list,
        top_n=top_n,
    )
    now = time.time()
    with _CACHE_LOCK:
        _cache_prune_unlocked(now)
        hit = _CACHE.get(cache_key)
        if hit and hit[0] > now:
            _CACHE.move_to_end(cache_key)
            return copy.deepcopy(hit[1])

    tensor_before = copy.deepcopy(physics_tensor) if isinstance(physics_tensor, dict) else {}
    md_before = copy.deepcopy(metadata) if isinstance(metadata, dict) else {}
    bf = blind_school_features if isinstance(blind_school_features, dict) else {}
    _hydrate_manifest_pattern_rows_if_missing(tensor_before, md_before)

    candidates = _enumerate_all_candidates(base_list, cards_list)

    def _one(
        job: RecoJob,
        *,
        _energy_tpl: Dict[str, str] = card_reason_templates,
        _l1_tpl: Dict[str, str] = l1_reason_templates,
    ) -> Dict[str, Any]:
        cid, plugs, delta, struct_hint = job
        seed = copy.deepcopy(tensor_before)
        if struct_hint:
            apply_structural_override(hint=struct_hint, physics_tensor=seed, unused_metadata=md_before)
        if delta:
            _apply_deity_delta(seed, delta)
        _outputs, pt_after = _preview_run(
            svc,
            enabled_plugins=plugs,
            physics_tensor=seed,
            metadata=md_before,
            blind_school_features=bf,
        )
        _hydrate_manifest_pattern_rows_if_missing(pt_after, md_before)
        score_bundle = calculate_decision_score(
            tensor_before,
            pt_after,
            metadata_before=md_before,
            metadata_after=None,
        )
        templates = _collect_reason_templates_for_delta(baseline_set, plugs)
        if delta and cid.startswith("patch:"):
            ptpl = _patch_reason_template(cid)
            if ptpl:
                templates.insert(0, ptpl)
        if cid.startswith("card:"):
            tail = cid[5:].strip()
            ctpl = _energy_tpl.get(tail)
            if ctpl:
                templates.insert(0, ctpl)
        if cid.startswith("l1struct:"):
            tail = cid[9:].strip()
            ltpl = _l1_tpl.get(tail)
            if ltpl:
                templates.insert(0, ltpl)
        if not templates:
            templates = ["因果评分优先：格局「{structure}」约 {progress}%。"]
        filled = _fill_reason_templates(templates, tensor_after=pt_after, metadata=md_before)
        filled = (filled + _quant_suffix(score_bundle)).strip()
        syn = synthesize_recommendation_reason(
            action_phrase=_action_phrase(cid, cards_list),
            score_detail=score_bundle,
            tensor_before=tensor_before,
            tensor_after=pt_after,
        )
        trace_voice = synthesize_manifest_trace_reason(tensor_before, pt_after)
        if trace_voice:
            syn = f"{trace_voice}\n{syn}".strip()
        filled = f"{syn}\n{filled}".strip()
        return {
            "candidate_id": cid,
            "total_score": float(score_bundle["total_score"]),
            "score_detail": score_bundle,
            "enabled_plugins": list(plugs),
            "reason_templates": templates,
            "filled_reason": filled,
            "plugin_outputs": _outputs,
        }

    rows: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(2, min(max_workers, len(candidates) or 1))) as ex:
        futs = [ex.submit(_one, c) for c in candidates]
        for fut in as_completed(futs):
            try:
                rows.append(fut.result())
            except Exception as exc:  # noqa: BLE001
                rows.append(
                    {
                        "candidate_id": "error",
                        "total_score": -1.0,
                        "score_detail": {"error": str(exc)},
                        "enabled_plugins": [],
                        "reason_templates": [],
                        "filled_reason": "",
                        "plugin_outputs": {},
                    }
                )

    def _reco_sort_key(r: Mapping[str, Any]) -> Tuple[float, int, str]:
        """同分稳定序：补丁/结构卡优先于纯插件开关，避免并行评分全零时顺序抖动。"""
        cid = str(r.get("candidate_id") or "")
        if cid.startswith("patch:"):
            tier = 0
        elif cid.startswith("card:") or cid.startswith("l1struct:"):
            tier = 1
        elif cid.startswith("enable:"):
            tier = 2
        elif cid.startswith("disable:"):
            tier = 3
        else:
            tier = 9
        return (-float(r.get("total_score") or 0.0), tier, cid)

    rows.sort(key=lambda r: _reco_sort_key(r))
    top = rows[: max(1, top_n)]

    for item in top:
        matched: List[str] = []
        cand = str(item.get("candidate_id") or "")
        if cand.startswith("card:"):
            tail = cand[5:].strip()
            if tail:
                matched.append(tail)
        if cand.startswith("l1struct:"):
            tail = cand[9:].strip()
            if tail:
                matched.append(tail)
        added = set(item.get("enabled_plugins") or []) - baseline_set
        removed = baseline_set - set(item.get("enabled_plugins") or [])
        delta_plugins = sorted(added | removed)
        for c in cards_list:
            cid = str(c.get("id") or "").strip()
            anchor = str(c.get("pluginAuditAnchorId") or c.get("plugin_audit_anchor_id") or "").strip()
            prop = c.get("proposal") if isinstance(c.get("proposal"), dict) else {}
            plug = str((prop or {}).get("plugin_id") or "").strip()
            if anchor and anchor in added:
                matched.append(cid)
            elif plug and plug in added:
                matched.append(cid)
            elif delta_plugins:
                title = str(c.get("title") or "")
                if plug in delta_plugins or any(p in title for p in delta_plugins):
                    matched.append(cid)
        dedup: List[str] = []
        seen_m: Set[str] = set()
        for m in matched:
            if m and m not in seen_m:
                seen_m.add(m)
                dedup.append(m)
        item["matched_card_ids"] = dedup

    result: Dict[str, Any] = {
        "baseline_enabled_plugins": base_list,
        "candidates_evaluated": len(candidates),
        "top": top,
        "cache_key": cache_key,
        "cache_hit": False,
    }
    with _CACHE_LOCK:
        _cache_prune_unlocked(time.time())
        _CACHE[cache_key] = (time.time() + _CACHE_TTL_SEC, copy.deepcopy(result))
        _CACHE.move_to_end(cache_key)
        while len(_CACHE) > _CACHE_MAX:
            _CACHE.popitem(last=False)

    return result
