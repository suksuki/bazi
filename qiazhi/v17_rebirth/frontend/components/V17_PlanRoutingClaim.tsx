"use client";

import type { PlanDecisionClaim, PlanDecisionRoutingFeatures } from "@/types/decisionBrain";

type Props = {
  routingLabel?: string;
  routingReason?: string;
  routingPolicy?: string;
  routingFeatures?: PlanDecisionRoutingFeatures;
  claim?: PlanDecisionClaim;
};

function compactRoutingHints(features?: PlanDecisionRoutingFeatures): string {
  if (!features) return "";
  const kv: string[] = [];
  const keys = ["decision_count", "conflict_pairs", "duplicate_events", "max_abs_ratio", "total_abs_ratio", "net_ratio"];
  for (const key of keys) {
    const value = features[key];
    if (value === undefined) continue;
    if (typeof value === "number" && Number.isFinite(value)) {
      kv.push(`${key}=${value}`);
    } else if (typeof value === "boolean") {
      kv.push(`${key}=${value ? "Y" : "N"}`);
    } else if (typeof value === "string" && value.trim()) {
      kv.push(`${key}=${value}`);
    }
  }
  return kv.join(" · ");
}

function compactClaimSignals(claim?: PlanDecisionClaim): string {
  if (!claim?.signals) return "";
  const parts: string[] = [];
  const keys = ["decision_count", "conflict_pairs", "duplicate_events", "max_abs_ratio", "total_abs_ratio"];
  for (const key of keys) {
    const value = claim.signals[key];
    if (value === undefined) continue;
    if (typeof value === "number" && Number.isFinite(value)) {
      parts.push(`${key}=${value}`);
    } else if (typeof value === "boolean") {
      parts.push(`${key}=${value ? "Y" : "N"}`);
    } else if (typeof value === "string" && value.trim()) {
      parts.push(`${key}=${value}`);
    }
  }
  return parts.join(" · ");
}

function claimSeverity(claim?: PlanDecisionClaim): string {
  const severity = String(claim?.severity || "").trim().toUpperCase();
  if (["P1", "P2", "P3"].includes(severity)) return severity;
  return "P3";
}

function planSeverityTone(severity?: string): string {
  const normalized = String(severity || "").trim().toUpperCase();
  if (normalized === "P1") return "border-rose-500/30 bg-rose-950/30 text-rose-100";
  if (normalized === "P2") return "border-amber-500/30 bg-amber-950/30 text-amber-100";
  return "border-violet-500/25 bg-violet-950/30 text-violet-100";
}

function claimConfidencePct(claim?: PlanDecisionClaim): string | null {
  const value = Number(claim?.confidence);
  if (!Number.isFinite(value)) return null;
  return `${Math.round(Math.max(0, Math.min(1, value)) * 100)}%`;
}

export function V17PlanRoutingClaim({
  routingLabel,
  routingReason,
  routingPolicy,
  routingFeatures,
  claim,
}: Props) {
  const labelText = routingLabel ? `策略 ${routingLabel}` : undefined;
  const policyText = routingPolicy ? `策略 ${routingPolicy}` : undefined;
  const routingText = compactRoutingHints(routingFeatures);
  const signalText = compactClaimSignals(claim);
  const severityText = claimSeverity(claim);
  const confidenceText = claimConfidencePct(claim);
  const rationale = String(claim?.rationale || "").trim();

  return (
    <>
      <div className="mt-1 flex flex-wrap items-center gap-2">
        {labelText ? <span className="rounded-full border px-1.5 py-0.5 text-[9px] text-zinc-200">{labelText}</span> : null}
        {policyText ? <span className="rounded-full border border-zinc-500/20 px-1.5 py-0.5 text-[9px] text-zinc-200">{policyText}</span> : null}
        <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${planSeverityTone(severityText)}`}>
          风险 {severityText}
        </span>
        {routingText ? (
          <span className="rounded-full border border-zinc-500/20 px-1.5 py-0.5 text-[8px] leading-tight text-zinc-400">{routingText}</span>
        ) : null}
        {signalText ? (
          <span className="rounded-full border border-zinc-500/20 px-1.5 py-0.5 text-[8px] leading-tight text-zinc-300">{signalText}</span>
        ) : null}
      </div>
      {routingReason ? <p className="mt-1 text-[9px] text-zinc-500">路由说明：{routingReason}</p> : null}
      {rationale ? <p className="mt-1 text-[9px] text-zinc-500">裁决依据：{rationale}</p> : null}
      {confidenceText ? <p className="mt-1 text-[9px] text-zinc-500">裁决置信度：{confidenceText}</p> : null}
    </>
  );
}

export function compactRoutingLabel(planRouting?: string): string {
  const routing = String(planRouting || "system").trim().toLowerCase();
  if (routing === "llm") return "LLM 预审";
  if (routing === "user") return "用户确认";
  return "系统自动";
}

