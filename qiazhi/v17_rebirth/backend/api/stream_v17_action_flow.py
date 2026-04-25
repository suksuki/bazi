from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi.responses import JSONResponse

from v17_rebirth.infrastructure.state_backend import get_state_backend
from v17_rebirth.backend.infrastructure.evolution_db import evolution_storage
from v17_rebirth.backend.services.target_god_resolver import resolve_target_god
from v17_rebirth.backend.logic.L1_atomic_ops.physics_kernel import PhysicsKernel
from v17_rebirth.backend.api import stream_v17_decision_flow as _decision_flow


async def process_plan_signal_action(
    *,
    payload: Dict[str, Any],
    signal: str,
    action: str,
    raw_status: str,
    plan_signal: str,
    session_id: str,
    decision_id: str,
    plan_id: str,
    action_seq: int,
    request_verdict: bool,
    get_state_backend_fn: Optional[Callable[[], Any]] = None,
) -> JSONResponse:
    event: Dict[str, Any] = {
        "signal": signal,
        "plan_signal": plan_signal,
        "action": action,
        "plan_id": plan_id,
        "ts": datetime.now(timezone.utc).isoformat(),
        "seq": action_seq,
        "session_id": session_id,
        "request_verdict": request_verdict,
    }

    kernel_dispatch_ok = True
    kernel_dispatch_detail = ""
    execution_signal: Optional[str] = None
    matched_decisions: List[Dict[str, Any]] = []
    plan = None

    if not plan_signal:
        return JSONResponse({"ok": True, "signal": signal, "plan_signal": plan_signal}, status_code=200)

    try:
        backend_getter = get_state_backend_fn or get_state_backend
        current_physics = await backend_getter().get_physics(session_id)
        if not isinstance(current_physics, dict):
            current_physics = {}
        resolved_plan = _decision_flow.find_plan_by_id(
            current_physics,
            plan_id,
            decision_brain_key="decision_brain_state",
            plan_queue_key="plan_queue",
        ) if plan_id else None
        anchor = str(payload.get("anchor", "")).strip()
        if not anchor:
            anchor = str(resolved_plan.get("anchor") or "") if isinstance(resolved_plan, dict) else ""

        batch_ids = _decision_flow.safe_plan_ids(payload.get("batch_ids") or payload.get("batch_id"))
        decision_ids = _decision_flow.safe_plan_ids(payload.get("decision_ids"))
        if (not batch_ids and not decision_ids) and resolved_plan:
            resolved_plan_rows = _decision_flow.safe_plan_ids(resolved_plan.get("batch_ids"))
            if resolved_plan_rows:
                batch_ids = resolved_plan_rows
            else:
                decision_ids = _decision_flow.safe_plan_ids((resolved_plan.get("meta") or {}).get("decision_ids"))
        if not decision_ids and decision_id:
            decision_ids.append(decision_id)

        matched_decisions = []
        if decision_ids:
            matched_decisions = _decision_flow.collect_matched_decisions(current_physics, decision_ids=decision_ids)
        if not matched_decisions and batch_ids:
            matched_decisions = _decision_flow.resolve_batch_decisions(current_physics, batch_ids)
        if not matched_decisions and not decision_ids:
            matched_decisions = _decision_flow.collect_matched_decisions(
                current_physics,
                decision_labels=[action] if action else [],
            )

        if not action and matched_decisions:
            sample = matched_decisions[0]
            action = str(sample.get("label") or sample.get("title") or "").strip()

        if not action:
            if isinstance(resolved_plan, dict):
                action = str(
                    ((resolved_plan.get("meta") or {}).get("action") or resolved_plan.get("anchor") or "").strip()
                ) or action
            action = action or f"PLAN-{plan_signal}"
            event["action"] = action

        if _decision_flow.are_decisions_settled(matched_decisions) and plan_signal in {"PLAN_APPROVE", "PLAN_SUBMIT"}:
            event["decision_count"] = 0
            event["plan_status"] = (
                str((resolved_plan or {}).get("status") or "APPROVED") if resolved_plan else "APPROVED"
            )
            event["note"] = "decision set already settled; skip duplicate dispatch"
            await backend_getter().set_physics(session_id, current_physics)
            await backend_getter().publish_action(
                session_id,
                _decision_flow.event_for_publish(event, physics_tensor=current_physics),
            )
            return JSONResponse({
                "ok": True,
                "signal": "VOTE_IGNORED",
                "action": action,
                "detail": event["note"],
            })

        if resolved_plan:
            resolved_status = str((resolved_plan or {}).get("status", "")).strip().upper()
            if _decision_flow.is_plan_terminal(resolved_status) and plan_signal in {
                "PLAN_APPROVE",
                "PLAN_REJECT",
                "PLAN_ESCALATE",
                "PLAN_WITHDRAW",
                "PLAN_SUBMIT",
            }:
                event["plan_status"] = resolved_status
                event["note"] = "plan already terminal; duplicate ignored"
                await backend_getter().set_physics(session_id, current_physics)
                await backend_getter().publish_action(
                    session_id,
                    _decision_flow.event_for_publish(event, physics_tensor=current_physics),
                )
                return JSONResponse(
                    {
                        "ok": True,
                        "signal": "VOTE_IGNORED",
                        "action": action,
                        "plan_id": str(plan_id),
                        "detail": event["note"],
                    }
                )

        if not matched_decisions:
            fallback_target = (
                str(payload.get("target_god") or "").strip()
                or str((payload.get("physical_impact") or {}).get("target_god") if isinstance(payload.get("physical_impact"), dict) else "").strip()
            )
            source_hint = str(payload.get("source") or anchor or "").strip()
            matched_decisions = _decision_flow.fallback_match_pending_decisions(
                current_physics,
                action=action,
                fallback_target=fallback_target,
                source_hint=source_hint,
            )

        if not matched_decisions:
            event["error"] = "decision_not_found"
            await backend_getter().set_physics(session_id, current_physics)
            await backend_getter().publish_action(
                session_id,
                _decision_flow.event_for_publish(event, physics_tensor=current_physics),
            )
            return JSONResponse(
                {"ok": True, "signal": "DECISION_NOT_FOUND", "action": action, "detail": event["error"]},
            )

        for each in matched_decisions:
            each.setdefault("id", str(each.get("label") or each.get("title") or action).strip())

        plan = _decision_flow.seed_plan_from_payload(
            payload={**payload, "action": action, "anchor": anchor},
            session_id=session_id,
            rows=matched_decisions,
            signal=plan_signal,
        )

        if plan_signal == "PLAN_SUBMIT" and str(plan.routing or "").strip().lower() == "llm":
            plan.meta["llm_review_prompt"] = _decision_flow.build_llm_plan_prompt(
                rows=matched_decisions,
                action=action,
                anchor=anchor,
                output_language=str(payload.get("ui_lang") or current_physics.get("ui_lang") or "zh"),
            )
            event["llm_review_prompt"] = plan.meta.get("llm_review_prompt")

        execute_as_plan_approve = plan_signal == "PLAN_SUBMIT" and str(plan.routing or "user").strip().lower() == "system"
        execution_signal = "PLAN_APPROVE" if execute_as_plan_approve else plan_signal
        if execute_as_plan_approve:
            event["auto_approved"] = True
            event["routing"] = plan.routing
            event["routing_reason"] = str(plan.meta.get("routing_reason") or "").strip() or None

        decision_status = {
            "PLAN_APPROVE": "APPROVED",
            "PLAN_REJECT": "REJECTED",
            "PLAN_ESCALATE": "AWAIT_REVIEW",
            "PLAN_WITHDRAW": "REJECTED",
            "PLAN_SUBMIT": "AWAIT_REVIEW" if not execute_as_plan_approve else "APPROVED",
        }.get(plan_signal, "DRAFT")

        applied_ids: list[str] = []
        if execution_signal == "PLAN_APPROVE":
            for idx, matched_decision in enumerate(matched_decisions):
                row_payload = dict(payload)
                matched_label = str(matched_decision.get("label", "")).strip()
                matched_title = str(matched_decision.get("title", "")).strip()
                row_payload["action"] = matched_label or matched_title or action
                row_payload.pop("decision_ids", None)
                row_payload["decision_ids"] = [str(matched_decision.get("id", "")).strip()] if str(
                    matched_decision.get("id", "")
                ).strip() else []

                if isinstance(matched_decision.get("physical_impact"), dict):
                    row_payload["physical_impact"] = dict(matched_decision.get("physical_impact"))
                elif isinstance(payload.get("physical_impact"), dict):
                    row_payload["physical_impact"] = dict(payload.get("physical_impact"))
                else:
                    row_payload["physical_impact"] = {}

                final_target = str(row_payload.get("target_god", "")).strip()
                if not final_target and isinstance(row_payload.get("physical_impact"), dict):
                    final_target = str(row_payload["physical_impact"].get("target_god", "")).strip()
                    if final_target:
                        row_payload["target_god"] = final_target
                if not final_target:
                    final_target = resolve_target_god(
                        row_target=row_payload.get("target_god"),
                        impact=row_payload.get("physical_impact") if isinstance(row_payload.get("physical_impact"), dict) else {},
                        title=row_payload.get("title") or row_payload.get("action"),
                        label=matched_label,
                        plugin_id=matched_decision.get("plugin_id") if isinstance(matched_decision, dict) else "",
                        physics_tensor=current_physics if isinstance(current_physics, dict) else {},
                    )
                    if final_target:
                        row_payload["target_god"] = final_target

                if not final_target:
                    matched_decision["status"] = "CONSUMED_CONTEXT"
                    matched_decision["applied"] = False
                    matched_decision["llm_resolution_type"] = "context_only"
                    matched_decision["llm_resolution_state"] = "pending_context"
                    matched_decision["llm_terminal_state"] = "consume_context"
                    continue

                matched_decision["status"] = "APPROVED"
                matched_decision["applied"] = True
                decision_id_val = str(matched_decision.get("id", "")).strip() or f"{action}_{idx}"
                applied_ids.append(decision_id_val)
                row_payload["decision_id"] = decision_id_val
                ok = await PhysicsKernel.dispatch_perturbation(
                    session_id=session_id,
                    source="SRC_MANUAL",
                    payload={**row_payload, "reason": f"手动激活动作: {action}"},
                    causality_id=f"plan_{plan.plan_id}_{action_seq}_{idx}_{decision_id_val}",
                )
                if not ok:
                    kernel_dispatch_ok = False
                    kernel_dispatch_detail = f"physics kernel rejected perturbation at index {idx}"
                    matched_decision["status"] = "FAILED"
                    break
        else:
            for matched_decision in matched_decisions:
                matched_decision["status"] = decision_status

        if execution_signal != "PLAN_APPROVE":
            event["decision_count"] = len(matched_decisions)
            _decision_flow.mark_plan_decisions(
                current_physics,
                matched_decisions,
                status=decision_status,
                plan_id=plan.plan_id,
            )
            if plan_signal == "PLAN_REJECT":
                for matched in matched_decisions:
                    evolution_storage.log_feedback(
                        session_id=session_id,
                        decision_id=str(matched.get("id") or "").strip(),
                        action=action,
                        status="REJECTED",
                        meta={"trigger": "user_manual_reject", "plan_id": plan.plan_id},
                    )
                plan.transition("REJECTED")
                _decision_flow.write_plan_state(
                    current_physics,
                    plan=plan,
                    decision_brain_key="decision_brain_state",
                    plan_queue_key="plan_queue",
                    max_queue=96,
                )
                _decision_flow.emit_decision_batch_cache(current_physics)
                await backend_getter().set_physics(session_id, current_physics)
                await backend_getter().publish_action(
                    session_id,
                    _decision_flow.event_for_publish(event, physics_tensor=current_physics),
                )
                return JSONResponse(
                    {
                        "ok": True,
                        "signal": "VOTE_REJECTED",
                        "action": action,
                        "plan_id": plan.plan_id,
                        "decision_count": len(matched_decisions),
                    }
                )
            if plan_signal == "PLAN_WITHDRAW":
                for matched in matched_decisions:
                    evolution_storage.log_feedback(
                        session_id=session_id,
                        decision_id=str(matched.get("id") or "").strip(),
                        action=action,
                        status="REJECTED",
                        meta={"trigger": "user_plan_withdraw", "plan_id": plan.plan_id},
                    )
                plan.transition("REJECTED")
                _decision_flow.write_plan_state(
                    current_physics,
                    plan=plan,
                    decision_brain_key="decision_brain_state",
                    plan_queue_key="plan_queue",
                    max_queue=96,
                )
                _decision_flow.emit_decision_batch_cache(current_physics)
                await backend_getter().set_physics(session_id, current_physics)
                await backend_getter().publish_action(
                    session_id,
                    _decision_flow.event_for_publish(event, physics_tensor=current_physics),
                )
                return JSONResponse(
                    {
                        "ok": True,
                        "signal": "VOTE_WITHDRAWN",
                        "action": action,
                        "plan_id": plan.plan_id,
                        "decision_count": len(matched_decisions),
                    }
                )
            if plan_signal in {"PLAN_SUBMIT", "PLAN_ESCALATE"}:
                plan.transition("AWAIT_REVIEW")
                if str(plan.routing or "").strip().lower() == "llm":
                    event["llm_review_prompt"] = plan.meta.get("llm_review_prompt")
                _decision_flow.write_plan_state(
                    current_physics,
                    plan=plan,
                    decision_brain_key="decision_brain_state",
                    plan_queue_key="plan_queue",
                    max_queue=96,
                )
                _decision_flow.emit_decision_batch_cache(current_physics)
                await backend_getter().set_physics(session_id, current_physics)
                await backend_getter().publish_action(
                    session_id,
                    _decision_flow.event_for_publish(event, physics_tensor=current_physics),
                )
                return JSONResponse(
                    {
                        "ok": True,
                        "plan_id": plan.plan_id,
                        "signal": signal if signal == "PLAN_SUBMIT" else plan_signal,
                        "action": action,
                        "decision_count": len(matched_decisions),
                        "llm_review_prompt": event.get("llm_review_prompt"),
                    }
                )

        if execution_signal == "PLAN_APPROVE" and not applied_ids:
            no_target_only = all(
                str(item.get("status") or "").strip().upper() == "CONSUMED_CONTEXT"
                for item in matched_decisions
            )
            event["decision_count"] = len(matched_decisions)
            if no_target_only:
                plan.transition("COMMITTED")
                event["signal"] = "CONTEXT_CONSUMED"
            else:
                event["error"] = "no_physics_apply"
                plan.transition("FAILED")
            _decision_flow.write_plan_state(
                current_physics,
                plan=plan,
                decision_brain_key="decision_brain_state",
                plan_queue_key="plan_queue",
                max_queue=96,
            )
            _decision_flow.emit_decision_batch_cache(current_physics)
            await backend_getter().set_physics(session_id, current_physics)
            await backend_getter().publish_action(
                session_id,
                _decision_flow.event_for_publish(event, physics_tensor=current_physics),
            )
            if no_target_only:
                return JSONResponse(
                    {
                        "ok": True,
                        "signal": "CONTEXT_CONSUMED",
                        "action": action,
                        "decision_count": len(matched_decisions),
                    }
                )
            return JSONResponse(
                {
                    "ok": True,
                    "signal": "NARRATIVE_TRIGGER",
                    "action": action,
                    "decision_count": 0,
                }
            )

        if execution_signal == "PLAN_APPROVE":
            latest_physics = await backend_getter().get_physics(session_id)
            if isinstance(latest_physics, dict) and latest_physics:
                current_physics = latest_physics
            _decision_flow.mark_plan_decisions(
                current_physics,
                matched_decisions,
                status="APPROVED" if kernel_dispatch_ok else "FAILED",
                plan_id=plan.plan_id,
            )
            if kernel_dispatch_ok:
                plan.transition("COMMITTED")
                event["decision_count"] = len(applied_ids)
            else:
                plan.transition("FAILED")
                event["error"] = "physics kernel dispatch failed"
                event["detail"] = kernel_dispatch_detail or "physics kernel dispatch failed"
                event["decision_count"] = len(matched_decisions)

            _decision_flow.write_plan_state(
                current_physics,
                plan=plan,
                decision_brain_key="decision_brain_state",
                plan_queue_key="plan_queue",
                max_queue=96,
            )
            _decision_flow.emit_decision_batch_cache(current_physics)
            await backend_getter().set_physics(session_id, current_physics)
            await backend_getter().publish_action(
                session_id,
                _decision_flow.event_for_publish(event, physics_tensor=current_physics),
            )
            if not kernel_dispatch_ok:
                return JSONResponse(
                    {"ok": False, "detail": kernel_dispatch_detail or "physics kernel dispatch failed", "signal": signal},
                    status_code=500,
                )

    except Exception as e:
        kernel_dispatch_ok = False
        kernel_dispatch_detail = str(e)
        return JSONResponse(
            {"ok": False, "detail": kernel_dispatch_detail or "physics action failed", "signal": signal},
            status_code=500,
        )

    if not kernel_dispatch_ok:
        return JSONResponse(
            {
                "ok": False,
                "detail": kernel_dispatch_detail or "physics kernel dispatch failed",
                "signal": signal,
            },
            status_code=500,
        )

    if execution_signal == "PLAN_APPROVE" and kernel_dispatch_ok:
        try:
            residual = float(payload.get("residual", 0.0))
            decision_ids = payload.get("decision_ids")
            id_lookup = {str(dec.get("id", "")).strip(): dec for dec in matched_decisions if isinstance(dec, dict)}
            if isinstance(decision_ids, list) and decision_ids:
                for each_id in decision_ids:
                    each_sid = str(each_id or "").strip()
                    if not each_sid:
                        continue
                    matched = id_lookup.get(each_sid, {})
                    meta = {
                        "impact_ratio": (
                            matched.get("physical_impact", {}).get("impact_ratio")
                            if isinstance(matched.get("physical_impact"), dict)
                            else payload.get("physical_impact", {}).get("impact_ratio") if isinstance(payload.get("physical_impact"), dict) else None
                        ),
                        "target_god": (
                            str(
                                matched.get("target_god", "")
                                or (
                                    matched.get("physical_impact", {}).get("target_god")
                                    if isinstance(matched.get("physical_impact"), dict)
                                    else ""
                                )
                            ).strip()
                            or payload.get("target_god")
                        ),
                    }
                    evolution_storage.log_feedback(
                        session_id=session_id,
                        decision_id=each_sid,
                        action=action,
                        status="APPROVED",
                        residual=residual,
                        meta=meta,
                    )
            else:
                evolution_storage.log_feedback(
                    session_id=session_id,
                    decision_id=decision_id or action,
                    action=action,
                    status="APPROVED",
                    residual=residual,
                    meta={
                        "impact_ratio": payload.get("physical_impact", {}).get("impact_ratio")
                        if isinstance(payload.get("physical_impact"), dict)
                        else None,
                        "target_god": payload.get("target_god"),
                    },
                )
        except Exception:
            pass

    return JSONResponse(
        {
            "ok": True,
            "signal": signal if signal != "PLAN_WITHDRAW" else plan_signal,
            "plan_id": plan.plan_id if plan is not None else None,
            "plan_signal": plan_signal,
            "will_proxy_delta": "aggressive" if any(k in action for k in ["进", "冲", "加码"]) else "stable",
        }
    )
