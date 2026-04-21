"use client";

import type { Decision } from "@/hooks/useOracleSession";
import type { DecisionBatch } from "@/components/decisionInboxUtils";

type BucketKind = "manual" | "auto" | "system" | "llm";
type StatusBadge = { label: string; className: string };
type ConfidenceChip = { label: string; className: string } | null;
type BiasSummary = { useText: string; tabooText: string } | null;

type AutoInboxEntry = {
  key: string;
  decision: Decision;
  channel: "auto" | "system" | "llm" | "context";
};

type Props = {
  passiveLlmContextCount: number;
  passiveLlmContextRows: Decision[];
  autoDecisionBatches: DecisionBatch[];
  autoInboxRows: AutoInboxEntry[];
  focusedDecisionId?: string;
  statusBadge: (kind: BucketKind, decision: Decision) => StatusBadge;
  bucketAccessLabel: (kind: BucketKind) => string;
  bucketReason: (kind: BucketKind, decision: Decision) => string;
  impactText: (decision: Decision) => string;
  patternProfileSummary: (decision: Decision) => string;
  patternConfidenceChip: (decision: Decision) => ConfidenceChip;
  routingRationale: (kind: BucketKind, decision: Decision) => string[];
  fluxRationale: (decision: Decision) => string[];
  groupFluxRationale: (decisions: Decision[]) => string[];
  compactRoutingLines: (lines: string[]) => string;
  arbitrationTrace: (kind: BucketKind, decision: Decision) => string;
  decisionFocusPreview: (decision: Decision) => string;
  decisionReasonTags: (kind: BucketKind, decision: Decision) => string[];
  llmPolicyLabel: (policy: string | undefined) => string;
  llmStateLabel: (state: string | undefined) => string;
  promptPreview: (decision: Decision) => string;
  godRingBiasSummary: (decision: Decision) => BiasSummary;
  groupGodRingBiasSummary: (decisions: Decision[]) => BiasSummary;
};

export function V17_AutoDecisionSection({
  passiveLlmContextCount,
  passiveLlmContextRows,
  autoDecisionBatches,
  autoInboxRows,
  focusedDecisionId,
  statusBadge,
  bucketAccessLabel,
  bucketReason,
  impactText,
  patternProfileSummary,
  patternConfidenceChip,
  routingRationale,
  fluxRationale,
  groupFluxRationale,
  compactRoutingLines,
  arbitrationTrace,
  decisionFocusPreview,
  decisionReasonTags,
  llmPolicyLabel,
  llmStateLabel,
  promptPreview,
  godRingBiasSummary,
  groupGodRingBiasSummary,
}: Props) {
  return (
    <div className="rounded-xl border border-amber-500/15 bg-zinc-950/55 p-3">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-[11px] tracking-[0.22em] text-amber-200">AUTO</p>
        <span className="text-[10px] text-zinc-500">系统已处理结果、叙事建议与上下文素材</span>
      </div>
      {passiveLlmContextCount > 0 ? (
        <div className="mb-2 rounded-xl border border-amber-500/10 bg-amber-950/10 px-2.5 py-2">
          <p className="text-[10px] text-amber-100">
            已自动收纳 {passiveLlmContextCount} 条“仅作上下文”的素材，它们不会阻塞 Inbox，也不需要手动处理。
          </p>
          {passiveLlmContextRows.length ? (
            <div className="mt-1 flex flex-wrap gap-1">
              {passiveLlmContextRows.map((row, idx) => (
                <span
                  key={`passive_llm_${String(row.id || row.label || idx)}`}
                  className="rounded-full border border-amber-500/20 bg-zinc-950/60 px-1.5 py-0.5 text-[9px] text-zinc-300"
                >
                  {String(row.label || row.title || row.source || "上下文素材").trim()}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="space-y-2">
        {autoDecisionBatches.length ? (
          <>
            {autoDecisionBatches.map((group) => {
              const badge = statusBadge(group.bucket, group.decisions[0]);
              const sourceText =
                group.source_families && group.source_families.length
                  ? group.source_families.join(" / ")
                  : group.source_anchor || "自动归并";
              const ratio = Number(group.net_impact_ratio || 0);
              const channelLabel = group.bucket === "llm" ? "叙事建议" : "系统自动处理";
              const groupRationale = routingRationale(group.bucket, group.decisions[0]);
              const groupBias = groupGodRingBiasSummary(group.decisions);
              const groupFlux = groupFluxRationale(group.decisions);
              return (
                <div
                  key={`auto_batch_${group.batch_id}`}
                  className={`rounded-xl border bg-amber-950/15 px-2.5 py-2 ${
                    group.decisions.some((item) => String(item.id || item._ui_id || "").trim() === focusedDecisionId)
                      ? "border-emerald-500/35 shadow-[0_0_0_1px_rgba(16,185,129,0.22)]"
                      : "border-amber-500/10"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-[11px] text-amber-100">自动批次 · {channelLabel}</p>
                    <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${badge.className}`}>{badge.label}</span>
                  </div>
                  <p className="mt-1 break-words text-[10px] text-zinc-500">访问方式：{bucketAccessLabel(group.bucket)}</p>
                  <p className="mt-1 break-words text-[10px] text-zinc-500">
                    目标 {group.target} · 来源 {sourceText} · 批次 {group.decision_count}
                    {group.net_impact_ratio ? ` · 位移 ${Math.abs(ratio) * 100 > 1000 ? ">=1000" : `${(Math.abs(ratio) * 100).toFixed(1)}%`}` : ""}
                  </p>
                  <p className="mt-1 break-words text-[10px] leading-relaxed text-zinc-500">
                    {bucketReason(group.bucket, group.decisions[0])}
                  </p>
                  {patternProfileSummary(group.decisions[0]) ? (
                    <p className="mt-1 break-words text-[10px] text-cyan-100/85">{patternProfileSummary(group.decisions[0])}</p>
                  ) : null}
                  {groupBias ? (
                    <div className="mt-1 space-y-0.5 text-[10px]">
                      {groupBias.useText ? <p className="text-emerald-200/90">用侧推动：{groupBias.useText}</p> : null}
                      {groupBias.tabooText ? <p className="text-rose-200/90">忌侧推动：{groupBias.tabooText}</p> : null}
                    </div>
                  ) : null}
                  {groupFlux.length ? (
                    <div className="mt-1 space-y-0.5 text-[10px]">
                      {groupFlux.map((line) => (
                        <p key={`${group.batch_id}_${line}`} className="break-words text-sky-200/85">
                          {line}
                        </p>
                      ))}
                    </div>
                  ) : null}
                  {groupRationale.length ? (
                    <p className="mt-1 break-words text-[9px] text-zinc-500">{compactRoutingLines(groupRationale)}</p>
                  ) : null}
                  {group.labels.length ? (
                    <div className="mt-2 flex flex-wrap gap-1 opacity-80">
                      {group.labels.map((label) => (
                        <span
                          key={`${group.batch_id}:${label}`}
                          className="rounded-full border border-amber-500/20 bg-zinc-950/60 px-1.5 py-0.5 text-[8px] text-zinc-300"
                        >
                          {label}
                        </span>
                      ))}
                    </div>
                  ) : null}
                  <div className="mt-2 space-y-1">
                    {group.decisions.map((decision) => {
                      const confidence = patternConfidenceChip(decision);
                      const bias = godRingBiasSummary(decision);
                      const fluxLines = fluxRationale(decision);
                      return (
                        <div
                          key={`batch_${group.batch_id}_${decision._ui_id}`}
                          className={`rounded-lg border bg-zinc-950/45 px-2 py-1.5 ${
                            String(decision.id || decision._ui_id || "").trim() === focusedDecisionId
                              ? "border-emerald-500/35 shadow-[0_0_0_1px_rgba(16,185,129,0.22)]"
                              : "border-amber-500/20"
                          }`}
                        >
                          <p className="break-words text-[10px] text-zinc-100">{String(decision.label || decision.title || "自动处理项").trim()}</p>
                          <p className="mt-0.5 break-words text-[9px] text-zinc-400">{impactText(decision)}</p>
                          {patternProfileSummary(decision) ? (
                            <p className="mt-0.5 break-words text-[9px] text-cyan-100/85">{patternProfileSummary(decision)}</p>
                          ) : null}
                          {bias ? (
                            <div className="mt-1 space-y-0.5 text-[9px]">
                              {bias.useText ? <p className="text-emerald-200/90">用侧推动：{bias.useText}</p> : null}
                              {bias.tabooText ? <p className="text-rose-200/90">忌侧推动：{bias.tabooText}</p> : null}
                            </div>
                          ) : null}
                          {fluxLines.length ? (
                            <div className="mt-1 space-y-0.5 text-[9px]">
                              {fluxLines.map((line) => (
                                <p key={`${decision._ui_id}_${line}`} className="break-words text-sky-200/85">
                                  {line}
                                </p>
                              ))}
                            </div>
                          ) : null}
                          {confidence ? (
                            <div className="mt-1">
                              <span className={`rounded-full border px-1.5 py-0.5 text-[8px] ${confidence.className}`}>
                                {confidence.label}
                              </span>
                            </div>
                          ) : null}
                          <p className="mt-0.5 text-[9px] text-amber-200/80">{arbitrationTrace(group.bucket, decision)}</p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </>
        ) : null}

        {autoInboxRows.length ? (
          autoInboxRows.map((entry) => {
            const row = entry.decision;
            const badge = statusBadge("auto", row);
            const channelLabel =
              entry.channel === "system" ? "自动结算" : entry.channel === "llm" ? "叙事建议" : "上下文素材";
            const entryKind = entry.channel === "llm" || entry.channel === "system" ? (entry.channel as BucketKind) : "auto";
            const rationale = routingRationale(entryKind, row);
            const confidence = patternConfidenceChip(row);
            const bias = godRingBiasSummary(row);
            const fluxLines = fluxRationale(row);
            return (
              <div
                key={entry.key}
                className={`rounded-xl border bg-amber-950/15 px-2.5 py-2 ${
                  String(row.id || "").trim() === focusedDecisionId
                    ? "border-emerald-500/35 shadow-[0_0_0_1px_rgba(16,185,129,0.22)]"
                    : "border-amber-500/10"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-[11px] text-amber-100">{String(row.label || row.title || "自动处理项").trim()}</p>
                  <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${badge.className}`}>{badge.label}</span>
                </div>
                <p className="mt-1 break-words text-[10px] text-zinc-500">访问方式：{bucketAccessLabel(entryKind)}</p>
                <p className="mt-1 break-words text-[10px] text-zinc-500">
                  {channelLabel} · {String(row.source || row.source_label || "auto_context")} · {String(row.target_god || row.physical_impact?.target_god || "未定目标")}
                </p>
                <p className="mt-1 break-words text-[10px] text-zinc-400">{impactText(row)}</p>
                <p className="mt-1 font-mono text-[10px] text-amber-200/80">{arbitrationTrace("auto", row)}</p>
                <p className="mt-1 break-words text-[10px] leading-relaxed text-zinc-500">{bucketReason("auto", row)}</p>
                {patternProfileSummary(row) ? (
                  <p className="mt-1 break-words text-[10px] text-cyan-100/85">{patternProfileSummary(row)}</p>
                ) : null}
                {bias ? (
                  <div className="mt-1 space-y-0.5 text-[10px]">
                    {bias.useText ? <p className="text-emerald-200/90">用侧推动：{bias.useText}</p> : null}
                    {bias.tabooText ? <p className="text-rose-200/90">忌侧推动：{bias.tabooText}</p> : null}
                  </div>
                ) : null}
                {fluxLines.length ? (
                  <div className="mt-1 space-y-0.5 text-[10px]">
                    {fluxLines.map((line) => (
                      <p key={`${entry.key}_${line}`} className="break-words text-sky-200/85">
                        {line}
                      </p>
                    ))}
                  </div>
                ) : null}
                {rationale.length ? (
                  <p className="mt-1 break-words text-[9px] text-zinc-500">{compactRoutingLines(rationale)}</p>
                ) : null}
                {decisionFocusPreview(row) ? (
                  <p className="mt-1 break-words text-[10px] text-fuchsia-200/90">{decisionFocusPreview(row)}</p>
                ) : null}
                <div className="mt-1 flex flex-wrap gap-1">
                  {confidence ? (
                    <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${confidence.className}`}>
                      {confidence.label}
                    </span>
                  ) : null}
                  {decisionReasonTags("auto", row).map((tag) => (
                    <span key={`${entry.key}:${tag}`} className="rounded-full border border-amber-500/20 bg-zinc-950/60 px-1.5 py-0.5 text-[9px] text-zinc-300">
                      {tag}
                    </span>
                  ))}
                  {row.llm_resolution_policy ? (
                    <span className="rounded-full border border-cyan-500/20 bg-zinc-950/60 px-1.5 py-0.5 text-[9px] text-cyan-100">
                      {llmPolicyLabel(row.llm_resolution_policy)}
                    </span>
                  ) : null}
                  {row.llm_resolution_state ? (
                    <span className="rounded-full border border-cyan-500/20 bg-zinc-950/60 px-1.5 py-0.5 text-[9px] text-zinc-300">
                      {llmStateLabel(row.llm_resolution_state)}
                    </span>
                  ) : null}
                </div>
                {row.llm_terminal_state ? (
                  <p className="mt-1 text-[10px] leading-relaxed text-zinc-500">终态：{String(row.llm_terminal_state)}</p>
                ) : null}
                <p className="mt-1 break-words text-[10px] leading-relaxed text-amber-100/80">{promptPreview(row)}</p>
              </div>
            );
          })
        ) : null}

        {autoDecisionBatches.length || autoInboxRows.length ? null : <p className="text-[11px] text-zinc-500">暂无自动处理回执。</p>}
      </div>
    </div>
  );
}
