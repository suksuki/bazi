"""V12 BrainHub：反应式调度枢纽（PSV + 语义监军 + 自动重试）。"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Sequence, Set, Tuple

from pydantic import BaseModel, Field

_LOG = logging.getLogger(__name__)


class BrainHubPulseState(str, Enum):
    """E2E 演示与编排用脉冲状态（与物理子系统解耦，仅用于可观测迁移日志）。"""

    HUB_IDLE = "HUB_IDLE"
    PROBE_OFFERED = "PROBE_OFFERED"
    BIAS_ACK_INGESTED = "BIAS_ACK_INGESTED"
    LOCAL_RECOMPUTE_REQUESTED = "LOCAL_RECOMPUTE_REQUESTED"
    AUDIT_GATE = "AUDIT_GATE"
    ASSERTION_TREE_MATERIALIZED = "ASSERTION_TREE_MATERIALIZED"

from app.logic.brain.psv_engine import PSVEngine, PSVSymbol
from app.logic.brain.semantic_auditor import AuditResult, DissentBlock, SemanticAuditor
from app.logic.brain.seeds import KNOWLEDGE_SEEDS, SOVEREIGNTY_WEIGHTS, seed_short_code
from app.logic.brain.htn_domain import evaluate_htn_tasks, plan_htn_route
from app.schemas.tri_layer_v12 import TriLayerMetadata
from app.services.helpers.metadata_projector_v12 import MetadataProjectorV12


class BrainHubContext(BaseModel):
    """Hub 上下文：三色投影 + PSV 视图。"""

    model_config = {"extra": "forbid"}

    tri: TriLayerMetadata
    psv_list: List[PSVSymbol] = Field(default_factory=list)


class BrainHubRun(BaseModel):
    """Hub 一次执行的结果摘要。"""

    model_config = {"extra": "forbid"}

    audit: AuditResult
    retry_count: int = 0
    auto_retry_prompt: str = ""
    dissent_block: DissentBlock | None = None


class BrainHubOrchestration(BaseModel):
    model_config = {"extra": "forbid"}

    flow_state: str = "ready"
    target_node_id: str = "node:unknown"
    llm_user_message: str = ""
    seed_key: str = ""
    seed_short: str = ""
    probe_query: str = ""
    why_probe: str = ""
    vf_tags: List[str] = Field(default_factory=list)
    introspection_path: List[str] = Field(default_factory=list)
    htn_tasks: List[str] = Field(default_factory=list)
    htn_plan: Dict[str, Any] = Field(default_factory=dict)
    interrupt_request: Dict[str, Any] = Field(
        default_factory=dict,
        description="V12.93：与 flow_state 原子绑定；PROBE_WAITING 时必须非空且含 probe_query",
    )
    finality_hammer_applied: bool = Field(
        default=False,
        description="V13.02：同一 Session resume 反馈超过 3 条时强制收敛，已压低张力并推进 SYNTHESIS。",
    )


class BrainHub:
    """反应式调度器：project -> psv -> audit -> retry/dissent。"""

    def __init__(
        self,
        *,
        projector: MetadataProjectorV12 | None = None,
        auditor: SemanticAuditor | None = None,
        max_auto_retry: int = 2,
    ) -> None:
        self._projector = projector or MetadataProjectorV12()
        self._auditor = auditor or SemanticAuditor()
        self._max_auto_retry = max(0, int(max_auto_retry))

    @property
    def max_auto_retry(self) -> int:
        return self._max_auto_retry

    def build_context(
        self,
        *,
        metadata: Dict[str, Any],
        physics_tensor: Dict[str, Any],
        user_intention: str = "",
    ) -> BrainHubContext:
        bundle = {
            "metadata": metadata or {},
            "physics_tensor": physics_tensor or {},
            "user_intention": str(user_intention or "").strip(),
        }
        tri = self._projector.project(bundle)
        psv_list = PSVEngine.from_tri(tri).build(tri)
        return BrainHubContext(tri=tri, psv_list=psv_list)

    @staticmethod
    def llm_decision_allowed(node_state: str) -> bool:
        state = str(node_state or "").strip().upper()
        return state in {"AMBIGUOUS", "CONFLICT_UNRESOLVED"}

    @staticmethod
    def build_local_fact_block(metadata: Dict[str, Any], *, fallback: str = "FACT_NODE:局部冲突待复核") -> str:
        md = metadata if isinstance(metadata, dict) else {}
        lines = md.get("node_context_lines")
        if isinstance(lines, list):
            first = next((str(x).strip() for x in lines if str(x).strip()), "")
            if first:
                return first[:220]
        points = ((md.get("conflict_matrix") or {}).get("points") or []) if isinstance(md.get("conflict_matrix"), dict) else []
        if isinstance(points, list):
            for p in points:
                if not isinstance(p, dict):
                    continue
                detail = str(p.get("detail") or p.get("kind") or "").strip()
                if detail:
                    return f"FACT_NODE:{detail[:200]}"
        return fallback[:220]

    @staticmethod
    def enforce_prompt_boundary(
        *,
        local_fact_block: str,
        target_node_id: str,
        vf_tags: List[str],
    ) -> List[Dict[str, str]]:
        nid = str(target_node_id or "node:unknown").strip()
        vf_top = [str(x).strip() for x in (vf_tags or []) if str(x).strip()][:3]
        payload = (
            f"Target_Node_ID={nid}; "
            f"Local_Fact={str(local_fact_block or '').strip()[:180]}; "
            f"VF_TOP3={','.join(vf_top)}"
        )[:300]
        return [
            {"role": "system", "content": "仅基于局部事实块输出；禁止访问或猜测底层物理数据。"},
            {"role": "user", "content": payload},
        ]

    @staticmethod
    def extract_candidate_evidence_refs(candidate_obj: Dict[str, Any]) -> List[str]:
        refs: List[str] = []
        obj = candidate_obj if isinstance(candidate_obj, dict) else {}
        rows = obj.get("assertions")
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                raw = row.get("evidence_refs") or row.get("refs") or []
                if isinstance(raw, list):
                    refs.extend([str(x).strip() for x in raw if str(x).strip()])
        return sorted(set(refs))

    @staticmethod
    def build_blackboard_refs(*, local_fact_block: str, psv_list: Sequence[PSVSymbol], logical_evidence: List[str]) -> Set[str]:
        refs: Set[str] = set()
        if str(local_fact_block or "").strip():
            refs.add(str(local_fact_block).strip())
        for s in psv_list:
            refs.add(f"{s.axis}:{s.polarity}")
            refs.update([str(x).strip() for x in (s.evidence or []) if str(x).strip()])
        refs.update([str(x).strip() for x in (logical_evidence or []) if str(x).strip()])
        return refs

    @staticmethod
    def verify_evidence_chain(*, candidate_refs: List[str], blackboard_refs: Set[str]) -> Tuple[bool, List[str]]:
        if not candidate_refs:
            return False, ["MISSING_EVIDENCE_CHAIN"]
        missing: List[str] = []
        for ref in candidate_refs:
            token = str(ref).strip()
            if not token:
                continue
            if token not in blackboard_refs:
                missing.append(token)
        return len(missing) == 0, missing[:8]

    @staticmethod
    def export_lineage(*, seed_short: str, htn_plan: Dict[str, Any]) -> Dict[str, Any]:
        seed = str(seed_short or "").strip()
        hp = dict(htn_plan or {}) if isinstance(htn_plan, dict) else {}
        if not isinstance(hp.get("plan"), list) or len(hp.get("plan") or []) == 0:
            hp = {
                "lineage": "HTN_DRIVEN",
                "goal": "终局裁决 v2.0",
                "plan": ["OBSERVE", "AUDIT", "PROBE", "SYNTHESIS"],
                "status": "fallback_htn_plan_applied",
            }
        return {
            "lineage": "HTN_DRIVEN",
            "seeds_matched": [seed] if seed else [],
            "htn_plan": hp,
        }

    @staticmethod
    def _build_atomic_interrupt_request(
        *,
        seed_key: str,
        seed_short: str,
        probe_query: str,
        target_node_id: str,
        why_probe: str,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        pq = str(probe_query or "").strip()
        if not pq:
            seed_payload = KNOWLEDGE_SEEDS.get(str(seed_key or "").strip(), {}) if seed_key else {}
            pq = str(seed_payload.get("probe_query") or "").strip()
        if not pq:
            pq = str(why_probe or "").strip()
        if not pq:
            pq = "系统检测到逻辑断点，请确认后再继续终判。"
            _LOG.error(
                "FATAL_LOGIC_SKEW code=HUB_PROBE_QUERY_EMPTY seed_key=%s seed_short=%s",
                seed_key,
                seed_short,
            )
        rc = str(seed_short or seed_key or "PROBE_PENDING").strip() or "PROBE_PENDING"
        return {
            "interrupt_id": f"hub-{uuid.uuid4().hex[:16]}",
            "source": "brain_hub_orchestrate",
            "reason_code": rc,
            "severity": "blocking",
            "state": "pending",
            "created_at": now,
            "probe_query": pq[:520],
            "target_node_id": str(target_node_id or "node:unknown").strip() or "node:unknown",
            "required_actions": ["confirm_conflict_branch", "choose_conflict_resolution_mode"],
            "evidence_refs": [
                f"hub.seed_key={seed_key}",
                f"hub.seed_short={seed_short}",
            ],
        }

    @staticmethod
    def _apply_finality_hammer_v1302(
        *,
        base: "BrainHubOrchestration",
        conflict_points: List[Dict[str, Any]],
        verified_facts: List[str],
        physics_tensor: Dict[str, Any] | None,
    ) -> "BrainHubOrchestration":
        """resume_feedback_history 超过 3 条时：压低全局张力并强制 READY / SYNTHESIS，终止无限追问。"""
        if not isinstance(physics_tensor, dict):
            return base
        meta = physics_tensor.setdefault("meta", {})
        if not isinstance(meta, dict):
            return base
        meta["global_conflict_tension"] = 0.05
        meta["v1302_finality_hammer"] = True
        vf_top = [str(x).strip() for x in (verified_facts or []) if str(x).strip()][:3]
        htn_tasks = evaluate_htn_tasks(
            {
                "has_raw_data": True,
                "has_clash_matrix": bool(conflict_points),
                "logic_gap_detected": False,
                "introspection_clear": True,
                "will_assimilated": True,
            }
        )
        htn_plan = plan_htn_route(
            {
                "has_raw_data": True,
                "has_clash_matrix": bool(conflict_points),
                "logic_gap_detected": False,
                "introspection_clear": True,
                "will_assimilated": True,
                "seeds_matched": [base.seed_short] if base.seed_short else [],
            }
        )
        user_msg = BrainHub.build_micro_user_message(
            target_node_id=str(base.target_node_id or "node:unknown"),
            key_pairs={
                "seed": base.seed_key or "none",
                "seed_short": base.seed_short or "none",
                "vf_top3": ",".join(vf_top),
                "note": "FINALITY_HAMMER_V1302",
            },
        )
        return BrainHubOrchestration(
            flow_state="READY",
            target_node_id=str(base.target_node_id or "node:unknown"),
            llm_user_message=user_msg[:800],
            seed_key=base.seed_key,
            seed_short=base.seed_short,
            probe_query="",
            why_probe="",
            vf_tags=vf_top,
            introspection_path=list(base.introspection_path or [])
            + ["FINALITY_HAMMER_V1302", "强制 SYNTHESIS 收敛"],
            htn_tasks=htn_tasks,
            htn_plan=htn_plan,
            interrupt_request={},
            finality_hammer_applied=True,
        )

    def orchestrate(
        self,
        *,
        conflict_points: List[Dict[str, Any]],
        verified_facts: List[str],
        user_confirmed: bool,
        self_abs: float = 0.0,
        output_vector_present: bool = True,
        resume_feedback_history: List[Any] | None = None,
        physics_tensor: Dict[str, Any] | None = None,
    ) -> BrainHubOrchestration:
        seed_key = ""
        seed_payload: Dict[str, Any] = {}
        target_node_id = "node:unknown"
        for i, cp in enumerate(conflict_points or []):
            detail = str((cp or {}).get("detail") or "")
            kind = str((cp or {}).get("kind") or "").lower()
            if "寅巳" in detail and ("害" in detail or "穿" in detail):
                seed_key = "harm:寅巳"
                seed_payload = KNOWLEDGE_SEEDS[seed_key]
                target_node_id = f"fact-{i}"
                break
            if "子午" in detail or (kind == "clash" and "子" in detail and "午" in detail):
                seed_key = "clash:子午"
                seed_payload = KNOWLEDGE_SEEDS[seed_key]
                target_node_id = f"fact-{i}"
                break
        if not seed_key and float(self_abs or 0.0) > 0.8 and not bool(output_vector_present):
            seed_key = "stagnation:high_lock_no_output"
            seed_payload = KNOWLEDGE_SEEDS[seed_key]
            target_node_id = "fact-stagnation"
        vf_top = [str(x).strip() for x in (verified_facts or []) if str(x).strip()][:3]
        aspect = str(seed_payload.get("aspect") or "GENERAL")
        probe_query = str(seed_payload.get("probe_query") or "").strip()
        why_probe = ""
        if seed_key == "harm:寅巳":
            why_probe = "命中寅巳穿害高权重结构，婚姻稳定轴存在现实映射风险。"
        elif seed_key == "clash:子午":
            why_probe = "命中子午对冲，系统张力与执行负载存在失衡风险。"
        elif seed_key == "stagnation:high_lock_no_output":
            why_probe = "自我能量高聚且食伤泄路缺失，疑似高能闭锁。"
        seed_short = seed_short_code(seed_key) if seed_key else ""
        flow_state = "PROBE_WAITING" if (seed_key and not user_confirmed) else "READY"
        hub_interrupt: Dict[str, Any] = {}
        if flow_state == "PROBE_WAITING":
            hub_interrupt = BrainHub._build_atomic_interrupt_request(
                seed_key=seed_key,
                seed_short=seed_short,
                probe_query=probe_query,
                target_node_id=target_node_id,
                why_probe=why_probe,
            )
            user_msg = self.build_micro_user_message(
                target_node_id=target_node_id,
                key_pairs={
                    "seed": seed_key,
                    "seed_short": seed_short,
                    "aspect": aspect,
                    "probe_query": probe_query,
                    "vf_top3": ",".join(vf_top),
                },
            )
        else:
            user_msg = self.build_micro_user_message(
                target_node_id=target_node_id,
                key_pairs={
                    "seed": seed_key or "none",
                    "seed_short": seed_short or "none",
                    "aspect": aspect,
                    "vf_top3": ",".join(vf_top),
                },
            )
        path = [
            "发现冲突点",
            "检索种子库",
            "判定信息真空" if flow_state == "PROBE_WAITING" else "信息充分",
            "执行主动追问" if flow_state == "PROBE_WAITING" else "继续窄带推理",
        ]
        htn_tasks = evaluate_htn_tasks(
            {
                "has_raw_data": True,
                "has_clash_matrix": bool(conflict_points),
                "logic_gap_detected": flow_state == "PROBE_WAITING",
                "introspection_clear": flow_state != "PROBE_WAITING",
            }
        )
        htn_plan = plan_htn_route(
            {
                "has_raw_data": True,
                "has_clash_matrix": bool(conflict_points),
                "logic_gap_detected": flow_state == "PROBE_WAITING",
                "introspection_clear": flow_state != "PROBE_WAITING",
                "will_assimilated": False,
                "seeds_matched": [seed_short] if seed_short else [],
            }
        )
        out = BrainHubOrchestration(
            flow_state=flow_state,
            target_node_id=target_node_id,
            llm_user_message=user_msg[:300],
            seed_key=seed_key,
            seed_short=seed_short,
            probe_query=probe_query,
            why_probe=why_probe,
            vf_tags=vf_top,
            introspection_path=path,
            htn_tasks=htn_tasks,
            htn_plan=htn_plan,
            interrupt_request=hub_interrupt,
            finality_hammer_applied=False,
        )
        hist = resume_feedback_history if isinstance(resume_feedback_history, list) else []
        if len(hist) > 3:
            _LOG.info(
                "v1302_finality_hammer: resume_feedback_history len=%s > 3, forcing synthesis convergence",
                len(hist),
            )
            out = BrainHub._apply_finality_hammer_v1302(
                base=out,
                conflict_points=conflict_points,
                verified_facts=verified_facts,
                physics_tensor=physics_tensor,
            )
        if out.flow_state == "PROBE_WAITING":
            pq_chk = str((out.interrupt_request or {}).get("probe_query") or "").strip()
            if not pq_chk:
                _LOG.error("FATAL_LOGIC_SKEW code=ORCH_PROBE_WAITING_NO_PAYLOAD seed_key=%s", out.seed_key)
        return out

    @staticmethod
    def assimilate_feedback(feedback: Dict[str, Any]) -> Dict[str, Any]:
        fb = feedback if isinstance(feedback, dict) else {}
        text = " ".join(
            [
                str(fb.get("text") or ""),
                str(fb.get("notes") or ""),
                str(fb.get("comment") or ""),
                str(fb.get("user_reply") or ""),
                str(fb.get("message") or ""),
            ]
        ).strip()
        yes_hits = ("是的", "很准", "准确", "确实", "对的")
        confirmed = any(x in text for x in yes_hits)
        item = {
            "kind": "CONFIRMED_FACT",
            "text": "用户确认：推断与现实一致",
            "source": "resume_feedback",
            "raw_feedback": text[:220],
            "weight": float(SOVEREIGNTY_WEIGHTS.get("confirmed_fact", 1.0)),
        }
        return {"confirmed": bool(confirmed), "fact": item if confirmed else {}}

    def audit(self, narrative: str, psv_list: Sequence[PSVSymbol]) -> AuditResult:
        return self._auditor.audit(narrative, list(psv_list))

    def build_auto_retry_prompt(self, narrative: str, psv_list: Sequence[PSVSymbol], audit: AuditResult) -> str:
        return self._auditor.build_auto_retry_prompt(narrative, list(psv_list), audit)

    @staticmethod
    def build_micro_user_message(*, target_node_id: str, key_pairs: Dict[str, Any]) -> str:
        """V12.2：构造节点级窄带 user_message（<=300 字）。"""
        nid = str(target_node_id or "").strip() or "UNKNOWN_NODE"
        items: List[str] = []
        for k, v in (key_pairs or {}).items():
            key = str(k or "").strip()
            if not key:
                continue
            val = str(v if v is not None else "").strip()
            if not val:
                continue
            items.append(f"{key}={val}")
        body = "；".join(items)
        raw = f"Target_Node_ID={nid} | {body}".strip()
        return raw[:300]

    @staticmethod
    def append_auto_retry_prompt(
        messages: Sequence[Dict[str, str]],
        auto_retry_prompt: str,
        *,
        target_node_id: str,
    ) -> List[Dict[str, str]]:
        nid = str(target_node_id or "").strip() or "UNKNOWN_NODE"
        base = [{"role": str(m.get("role") or ""), "content": str(m.get("content") or "")} for m in messages]
        if not base:
            return [{"role": "system", "content": f"[Target_Node_ID:{nid}] {str(auto_retry_prompt or '')[:300]}"}]
        out = list(base)
        out.append({"role": "system", "content": f"[Target_Node_ID:{nid}] {str(auto_retry_prompt or '')[:300]}"})
        return out

    def conclude(self, *, audit: AuditResult, retry_count: int, auto_retry_prompt: str) -> BrainHubRun:
        if audit.audit_state != "REJECT":
            return BrainHubRun(audit=audit, retry_count=retry_count, auto_retry_prompt=auto_retry_prompt)
        exhausted = retry_count >= self._max_auto_retry
        if exhausted:
            return BrainHubRun(
                audit=AuditResult(
                    is_passed=False,
                    reason_code="LIG_RETRY_EXHAUSTED",
                    feedback_for_llm=audit.feedback_for_llm,
                    audit_state="REJECT",
                    matched_rules=list(audit.matched_rules),
                    conflict_excerpt=audit.conflict_excerpt,
                ),
                retry_count=retry_count,
                auto_retry_prompt=auto_retry_prompt,
                dissent_block=DissentBlock(
                    reason_code="LIG_RETRY_EXHAUSTED",
                    summary=f"自动重试耗尽，最后一次拒稿={audit.reason_code}",
                ),
            )
        return BrainHubRun(audit=audit, retry_count=retry_count, auto_retry_prompt=auto_retry_prompt)


__all__ = ["BrainHub", "BrainHubContext", "BrainHubRun", "BrainHubPulseState", "BrainHubOrchestration"]
