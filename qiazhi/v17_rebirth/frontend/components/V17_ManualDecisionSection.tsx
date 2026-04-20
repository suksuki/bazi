"use client";

import { Check } from "lucide-react";

import type { Decision } from "@/hooks/useOracleSession";
import type { DecisionBatch, DecisionBatchGroup, DecisionWithId } from "@/components/decisionInboxUtils";

type BucketKind = "manual" | "auto" | "system" | "llm";

type StatusBadge = { label: string; className: string };
type ConfidenceChip = { label: string; className: string } | null;

type Props = {
  decisionsLength: number;
  groupedManualDecisionBatches: DecisionBatch[];
  singleManualDecisionBatches: DecisionBatch[];
  manualGroups: DecisionBatchGroup[];
  locked: boolean;
  busyId: string;
  onVote: (decision: DecisionWithId, status: "APPROVED" | "REJECTED") => Promise<void>;
  onBatchVote: (
    group: { decisions: DecisionWithId[]; batch_ids?: string[]; batch_id?: string },
    status: "APPROVED" | "REJECTED",
  ) => Promise<void>;
  statusBadge: (kind: BucketKind, decision: Decision) => StatusBadge;
  singleDecisionButtonLabel: (decision: Decision) => string;
  impactText: (decision: Decision) => string;
  patternProfileSummary: (decision: Decision) => string;
  decisionFocusPreview: (decision: Decision) => string;
  bucketReason: (kind: BucketKind, decision: Decision) => string;
  routingRationale: (kind: BucketKind, decision: Decision) => string[];
  compactRoutingLines: (lines: string[]) => string;
  patternConfidenceChip: (decision: Decision) => ConfidenceChip;
  decisionReasonTags: (kind: BucketKind, decision: Decision) => string[];
  directionGroupLabel: (ratio: number, rawLabel?: string) => string;
};

export function V17_ManualDecisionSection({
  decisionsLength,
  groupedManualDecisionBatches,
  singleManualDecisionBatches,
  manualGroups,
  locked,
  busyId,
  onVote,
  onBatchVote,
  statusBadge,
  singleDecisionButtonLabel,
  impactText,
  patternProfileSummary,
  decisionFocusPreview,
  bucketReason,
  routingRationale,
  compactRoutingLines,
  patternConfidenceChip,
  decisionReasonTags,
  directionGroupLabel,
}: Props) {
  return (
    <div className="rounded-xl border border-violet-500/20 bg-zinc-950/55 p-3">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-[11px] tracking-[0.22em] text-violet-200">MANUAL</p>
        <span className="text-[10px] text-zinc-500">可点击执行</span>
      </div>
      {decisionsLength ? (
        <div className="space-y-2">
          {groupedManualDecisionBatches.length ? (
            <>
              <p className="text-[10px] tracking-[0.15em] text-violet-300/70">自动整组入口（按批决策）</p>
              {groupedManualDecisionBatches.map((group) => {
                const badge = statusBadge("manual", group.decisions[0]);
                const sourceText =
                  group.source_families && group.source_families.length
                    ? group.source_families.join(" / ")
                    : group.source_anchor || "自动归并";
                const ratio = Number(group.net_impact_ratio || 0);
                const groupLabel = directionGroupLabel(ratio, group.direction_label);
                return (
                  <div
                    key={group.batch_id}
                    className="rounded-2xl border border-violet-500/35 bg-[linear-gradient(180deg,rgba(76,29,149,0.24),rgba(46,16,101,0.16))] p-3"
                  >
                    <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="text-xs font-medium text-violet-50">{group.target} · {groupLabel}</p>
                        <p className="text-[10px] text-violet-300/80">
                          来源 {sourceText} · 批次 {group.decision_count} 条 · 位移 {Math.abs(ratio) * 100 > 1000 ? ">=1000" : `${(Math.abs(ratio) * 100).toFixed(1)}%`}
                        </p>
                      </div>
                      <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${badge.className}`}>{badge.label}</span>
                    </div>

                    <p className="text-[10px] leading-relaxed text-zinc-400">{group.prompt_line}</p>

                    {group.labels.length ? (
                      <div className="mt-2 flex flex-wrap gap-1 opacity-80">
                        {group.labels.map((label) => (
                          <span
                            key={`${group.batch_id}:${label}`}
                            className="rounded-full border border-violet-500/25 bg-zinc-950/60 px-1.5 py-0.5 text-[8px] text-violet-100"
                          >
                            {label}
                          </span>
                        ))}
                      </div>
                    ) : null}

                    <div className="mt-3 flex items-center gap-2 border-t border-violet-500/20 pt-2">
                      <button
                        type="button"
                        onClick={() => onBatchVote(group, "APPROVED")}
                        disabled={locked || busyId !== ""}
                        className="flex h-8 w-full items-center justify-center gap-1 rounded-lg border border-emerald-500/20 bg-emerald-950/20 text-[10px] text-emerald-400 transition hover:bg-emerald-500/40 hover:text-emerald-100 disabled:opacity-30 shadow-[0_4px_12px_rgba(16,185,129,0.15)]"
                      >
                        <Check className="h-3 w-3" /> 批量处理本组 ({group.decisions.length})
                      </button>
                    </div>
                  </div>
                );
              })}
            </>
          ) : null}

          {singleManualDecisionBatches.length ? (
            singleManualDecisionBatches.map((group) => {
              const d = group.decisions[0];
              if (!d) return null;
              const badge = statusBadge("manual", d);
              return (
                <div
                  key={`single_batch_${group.batch_id}`}
                  className="rounded-2xl border border-violet-500/35 bg-[linear-gradient(180deg,rgba(76,29,149,0.24),rgba(46,16,101,0.16))] p-3"
                >
                  <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="text-xs font-medium text-violet-50">
                        {String(d.label || d.title || "行动建议").trim()}
                      </p>
                      <p className="text-[10px] text-violet-300/80">
                        目标 {String(d.target_god || d.physical_impact?.target_god || "未定目标").trim()} · 来源 {String(d.source || d.plugin_id || "manual").trim()} · {impactText(d)}
                      </p>
                    </div>
                    <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${badge.className}`}>{badge.label}</span>
                  </div>
                  <p className="text-[10px] leading-relaxed text-zinc-400">{group.prompt_line}</p>
                  {patternProfileSummary(d) ? (
                    <p className="mt-1 break-words text-[10px] text-cyan-100/90">{patternProfileSummary(d)}</p>
                  ) : null}
                  {decisionFocusPreview(d) ? (
                    <p className="mt-1 text-[10px] text-fuchsia-200/90">{decisionFocusPreview(d)}</p>
                  ) : null}
                  <div className="mt-3 flex items-center gap-2 border-t border-violet-500/20 pt-2">
                    <button
                      type="button"
                      onClick={() => onVote(d, "APPROVED")}
                      disabled={locked || busyId !== ""}
                      className="flex h-8 w-full items-center justify-center gap-1 rounded-lg border border-emerald-500/20 bg-emerald-950/20 text-[10px] text-emerald-400 transition hover:bg-emerald-500/40 hover:text-emerald-100 disabled:opacity-30 shadow-[0_4px_12px_rgba(16,185,129,0.15)]"
                    >
                      <Check className="h-3 w-3" /> 处理这条决策
                    </button>
                  </div>
                </div>
              );
            })
          ) : null}

          {manualGroups.length && !groupedManualDecisionBatches.length && !singleManualDecisionBatches.length ? (
            manualGroups.map((group) => {
              const sampleDecision = group.decisions[0];
              const badge = statusBadge("manual", sampleDecision);
              const sampleConfidence = patternConfidenceChip(sampleDecision);
              const sampleRationale = routingRationale("manual", sampleDecision);
              return (
                <div
                  key={group.key}
                  className="rounded-2xl border border-violet-500/35 bg-[linear-gradient(180deg,rgba(76,29,149,0.24),rgba(46,16,101,0.16))] p-3"
                >
                  <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="text-xs font-medium text-violet-50">目标 {group.target}</p>
                      <p className="text-[10px] text-violet-300/80">来源 {group.source} · 冲突域 {group.exclusivityKey} · {group.decisions.length} 条</p>
                    </div>
                    <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${badge.className}`}>{badge.label}</span>
                  </div>

                  <div className="mb-2 flex flex-wrap gap-1">
                    {group.decisions.map((d) => (
                      <span key={d._ui_id} className="rounded-full border border-violet-500/25 bg-zinc-950/60 px-1.5 py-0.5 text-[8px] text-violet-100">
                        {String(d.source || d.target_god || d.label || "待定").trim()}
                      </span>
                    ))}
                  </div>

                  <p className="text-[10px] leading-relaxed break-words text-zinc-500">{bucketReason("manual", sampleDecision)}</p>
                  {patternProfileSummary(sampleDecision) ? (
                    <p className="mt-1 break-words text-[10px] text-cyan-100/90">{patternProfileSummary(sampleDecision)}</p>
                  ) : null}
                  {sampleRationale.length ? (
                    <p className="mt-1 break-words text-[9px] text-zinc-500">{compactRoutingLines(sampleRationale)}</p>
                  ) : null}

                  <div className="mt-2 flex flex-wrap gap-1 opacity-80">
                    {sampleConfidence ? (
                      <span className={`rounded-full border px-1.5 py-0.5 text-[8px] ${sampleConfidence.className}`}>
                        {sampleConfidence.label}
                      </span>
                    ) : null}
                    {decisionReasonTags("manual", sampleDecision).map((tag) => (
                      <span key={tag} className="rounded-full border border-violet-500/20 bg-zinc-950/60 px-1.5 py-0.5 text-[8px] text-zinc-400">
                        {tag}
                      </span>
                    ))}
                  </div>
                  {decisionFocusPreview(sampleDecision) ? (
                    <p className="mt-2 text-[10px] text-fuchsia-200/90">{decisionFocusPreview(sampleDecision)}</p>
                  ) : null}

                  {group.decisions.length > 1 ? (
                    <div className="mt-3 flex items-center gap-2 border-t border-violet-500/20 pt-2">
                      <button
                        type="button"
                        onClick={() => onBatchVote(group, "APPROVED")}
                        disabled={locked || busyId !== ""}
                        className="flex h-8 w-full items-center justify-center gap-1 rounded-lg border border-emerald-500/20 bg-emerald-950/20 text-[10px] text-emerald-400 transition hover:bg-emerald-500/40 hover:text-emerald-100 disabled:opacity-30 shadow-[0_4px_12px_rgba(16,185,129,0.15)]"
                      >
                        <Check className="h-3 w-3" /> 批量处理本组 ({group.decisions.length})
                      </button>
                    </div>
                  ) : null}

                  <div className="mt-2 space-y-1">
                    {group.decisions.map((d) => {
                      const decisionConfidence = patternConfidenceChip(d);
                      return (
                        <div key={d._ui_id} className="rounded-lg border border-violet-500/25 bg-zinc-950/45 px-2 py-1.5">
                          <div className="flex items-center justify-between gap-2">
                            <p className="break-words text-[10px] text-violet-100">{(d.label || d.title || "行动建议").trim()}</p>
                            <span className="text-[9px] text-zinc-500">{impactText(d)}</span>
                          </div>
                          <div className="mt-1 flex items-center justify-between gap-2">
                            <span className="break-words text-[9px] text-zinc-500">{String(d.source || "manual")}</span>
                            <div className="flex items-center gap-1">
                              <button
                                type="button"
                                onClick={() => onVote(d, "APPROVED")}
                                disabled={locked || busyId !== ""}
                                className="rounded border border-emerald-500/20 bg-emerald-950/20 px-2 py-1 text-[9px] text-emerald-300 disabled:opacity-30"
                              >
                                {singleDecisionButtonLabel(d)}
                              </button>
                            </div>
                          </div>
                          {patternProfileSummary(d) ? (
                            <p className="mt-1 break-words text-[9px] text-cyan-100/85">{patternProfileSummary(d)}</p>
                          ) : null}
                          {decisionConfidence ? (
                            <div className="mt-1">
                              <span className={`rounded-full border px-1.5 py-0.5 text-[8px] ${decisionConfidence.className}`}>
                                {decisionConfidence.label}
                              </span>
                            </div>
                          ) : null}
                          {decisionFocusPreview(d) ? (
                            <p className="mt-1 break-words text-[9px] text-fuchsia-200/80">{decisionFocusPreview(d)}</p>
                          ) : null}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })
          ) : !groupedManualDecisionBatches.length && !singleManualDecisionBatches.length ? (
            <p className="text-[11px] text-zinc-500">当前没有可批量归类的手动裁决。</p>
          ) : null}
        </div>
      ) : (
        <p className="text-[11px] text-zinc-500">当前没有需要你手动点按的裁决项。</p>
      )}
    </div>
  );
}
