"use client";

import { Check } from "lucide-react";

import type { Decision } from "@/hooks/useOracleSession";
import type { DecisionBatch, DecisionBatchGroup, DecisionWithId } from "@/components/decisionInboxUtils";
import { t, translateTerm, type AppLanguage } from "@/lib/i18n";

type BucketKind = "manual" | "auto" | "system" | "llm";

type StatusBadge = { label: string; className: string };
type ConfidenceChip = { label: string; className: string } | null;
type BiasSummary = { useText: string; tabooText: string } | null;
type ActionMeta = { label: string; hint?: string };

type Props = {
  decisionsLength: number;
  groupedManualDecisionBatches: DecisionBatch[];
  singleManualDecisionBatches: DecisionBatch[];
  manualGroups: DecisionBatchGroup[];
  focusedDecisionId?: string;
  locked: boolean;
  busyId: string;
  onVote: (decision: DecisionWithId, status: "APPROVED" | "REJECTED") => Promise<void>;
  onBatchVote: (
    group: { decisions: DecisionWithId[]; batch_ids?: string[]; batch_id?: string },
    status: "APPROVED" | "REJECTED",
  ) => Promise<void>;
  statusBadge: (kind: BucketKind, decision: Decision) => StatusBadge;
  singleDecisionButtonLabel: (decision: Decision) => string;
  singleDecisionActionMeta: (decision: Decision) => ActionMeta;
  groupDecisionActionMeta: (decisions: Decision[]) => ActionMeta;
  impactText: (decision: Decision) => string;
  patternProfileSummary: (decision: Decision) => string;
  decisionFocusPreview: (decision: Decision) => string;
  bucketReason: (kind: BucketKind, decision: Decision) => string;
  routingRationale: (kind: BucketKind, decision: Decision) => string[];
  fluxRationale: (decision: Decision) => string[];
  groupFluxRationale: (decisions: Decision[]) => string[];
  compactRoutingLines: (lines: string[]) => string;
  patternConfidenceChip: (decision: Decision) => ConfidenceChip;
  decisionReasonTags: (kind: BucketKind, decision: Decision) => string[];
  directionGroupLabel: (ratio: number, rawLabel?: string) => string;
  godRingBiasSummary: (decision: Decision) => BiasSummary;
  groupGodRingBiasSummary: (decisions: Decision[]) => BiasSummary;
  lang?: AppLanguage;
};

export function V17_ManualDecisionSection({
  decisionsLength,
  groupedManualDecisionBatches,
  singleManualDecisionBatches,
  manualGroups,
  focusedDecisionId,
  locked,
  busyId,
  onVote,
  onBatchVote,
  statusBadge,
  singleDecisionButtonLabel,
  singleDecisionActionMeta,
  groupDecisionActionMeta,
  impactText,
  patternProfileSummary,
  decisionFocusPreview,
  bucketReason,
  routingRationale,
  fluxRationale,
  groupFluxRationale,
  compactRoutingLines,
  patternConfidenceChip,
  decisionReasonTags,
  directionGroupLabel,
  godRingBiasSummary,
  groupGodRingBiasSummary,
  lang = "zh",
}: Props) {
  const ui = (zh: string, en: string, ko: string) => (lang === "en" ? en : lang === "ko" ? ko : zh);
  const term = (value: string) => translateTerm(lang, value);
  const approveLabel = (meta: ActionMeta, count = 1) => {
    if (lang === "zh") return meta.label;
    return count > 1 ? t(lang, "decision.manual.group_button") : t(lang, "decision.manual.button");
  };
  const statusText = (label: string) => {
    if (label === "需立即裁定") return ui("需立即裁定", "Needs decision", "즉시 판정 필요");
    if (label === "等待你确认") return ui("等待你确认", "Waiting for you", "확인 대기");
    if (label === "已自动承接") return ui("已自动承接", "Auto accepted", "자동 인수됨");
    if (label === "后台静默处理") return ui("后台静默处理", "Silent backend handling", "백엔드 조용 처리");
    if (label === "拟自动收敛") return ui("拟自动收敛", "Auto convergence planned", "자동 수렴 예정");
    if (label === "系统观察中") return ui("系统观察中", "System observing", "시스템 관측 중");
    if (label === "将注入 Prompt") return ui("将注入 Prompt", "Will enter prompt", "프롬프트 주입 예정");
    return term(label);
  };
  return (
    <div className="rounded-xl border border-violet-500/20 bg-zinc-950/55 p-3">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-[11px] tracking-[0.22em] text-violet-200">MANUAL</p>
        <span className="text-[10px] text-zinc-500">{ui("可点击执行", "Ready to process", "처리 가능")}</span>
      </div>
      {decisionsLength ? (
        <div className="space-y-2">
          {groupedManualDecisionBatches.length ? (
            <>
              <p className="text-[10px] tracking-[0.15em] text-violet-300/70">
                {ui("自动整组入口（按批决策）", "Grouped entry by decision batch", "결정 묶음별 그룹 처리")}
              </p>
              {groupedManualDecisionBatches.map((group) => {
                const badge = statusBadge("manual", group.decisions[0]);
                const sourceText =
                  group.source_families && group.source_families.length
                    ? group.source_families.join(" / ")
                    : group.source_anchor || ui("自动归并", "Auto grouped", "자동 그룹");
                const ratio = Number(group.net_impact_ratio || 0);
                const groupLabel = directionGroupLabel(ratio, group.direction_label);
                const groupBias = groupGodRingBiasSummary(group.decisions);
                const groupFlux = groupFluxRationale(group.decisions);
                const actionMeta = groupDecisionActionMeta(group.decisions);
                return (
                  <div
                    key={group.batch_id}
                    className={`rounded-2xl border bg-[linear-gradient(180deg,rgba(76,29,149,0.24),rgba(46,16,101,0.16))] p-3 ${
                      group.decisions.some((item) => String(item.id || item._ui_id || "").trim() === focusedDecisionId)
                        ? "border-emerald-500/45 shadow-[0_0_0_1px_rgba(16,185,129,0.25)]"
                        : "border-violet-500/35"
                    }`}
                  >
                    <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="text-xs font-medium text-violet-50">{term(group.target)} · {term(groupLabel)}</p>
                        <p className="text-[10px] text-violet-300/80">
                          {ui("来源", "Source", "출처")} {sourceText} · {ui("批次", "Batch", "묶음")} {group.decision_count} {ui("条", "items", "건")} · {ui("位移", "Shift", "변위")} {Math.abs(ratio) * 100 > 1000 ? ">=1000" : `${(Math.abs(ratio) * 100).toFixed(1)}%`}
                        </p>
                      </div>
                      <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${badge.className}`}>{statusText(badge.label)}</span>
                    </div>

                    <p className="text-[10px] leading-relaxed text-zinc-400">{group.prompt_line}</p>
                    {groupBias ? (
                      <div className="mt-2 space-y-1 text-[10px]">
                        {groupBias.useText ? <p className="text-emerald-200/90">{ui("用侧推动", "Use-side push", "용측 추진")}：{groupBias.useText}</p> : null}
                        {groupBias.tabooText ? <p className="text-rose-200/90">{ui("忌侧推动", "Taboo-side push", "기측 추진")}：{groupBias.tabooText}</p> : null}
                      </div>
                    ) : null}
                    {groupFlux.length ? (
                      <div className="mt-2 space-y-0.5 text-[10px]">
                        {groupFlux.map((line) => (
                          <p key={`${group.batch_id}_${line}`} className="break-words text-sky-200/85">
                            {line}
                          </p>
                        ))}
                      </div>
                    ) : null}
                    {actionMeta.hint ? (
                      <p className="mt-2 break-words text-[10px] text-violet-200/85">
                        {ui("动作建议", "Action hint", "행동 제안")}：{actionMeta.hint}
                      </p>
                    ) : null}

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
                        <Check className="h-3 w-3" /> {approveLabel(actionMeta, group.decisions.length)}
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
              const bias = godRingBiasSummary(d);
              const fluxLines = fluxRationale(d);
              const actionMeta = singleDecisionActionMeta(d);
              return (
                <div
                  key={`single_batch_${group.batch_id}`}
                  className={`rounded-2xl border bg-[linear-gradient(180deg,rgba(76,29,149,0.24),rgba(46,16,101,0.16))] p-3 ${
                    String(d.id || d._ui_id || "").trim() === focusedDecisionId
                      ? "border-emerald-500/45 shadow-[0_0_0_1px_rgba(16,185,129,0.25)]"
                      : "border-violet-500/35"
                  }`}
                >
                  <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="text-xs font-medium text-violet-50">
                        {String(d.label || d.title || ui("行动建议", "Action hint", "행동 제안")).trim()}
                      </p>
                      <p className="text-[10px] text-violet-300/80">
                        {ui("目标", "Target", "대상")} {term(String(d.target_god || d.physical_impact?.target_god || "未定目标").trim())} · {ui("来源", "Source", "출처")} {String(d.source || d.plugin_id || "manual").trim()} · {impactText(d)}
                      </p>
                    </div>
                    <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${badge.className}`}>{statusText(badge.label)}</span>
                  </div>
                  <p className="text-[10px] leading-relaxed text-zinc-400">{group.prompt_line}</p>
                  {patternProfileSummary(d) ? (
                    <p className="mt-1 break-words text-[10px] text-cyan-100/90">{patternProfileSummary(d)}</p>
                  ) : null}
                  {bias ? (
                    <div className="mt-1 space-y-0.5 text-[10px]">
                      {bias.useText ? <p className="text-emerald-200/90">{ui("用侧推动", "Use-side push", "용측 추진")}：{bias.useText}</p> : null}
                      {bias.tabooText ? <p className="text-rose-200/90">{ui("忌侧推动", "Taboo-side push", "기측 추진")}：{bias.tabooText}</p> : null}
                    </div>
                  ) : null}
                  {fluxLines.length ? (
                    <div className="mt-1 space-y-0.5 text-[10px]">
                      {fluxLines.map((line) => (
                        <p key={`${group.batch_id}_${line}`} className="break-words text-sky-200/85">
                          {line}
                        </p>
                      ))}
                    </div>
                  ) : null}
                  {actionMeta.hint ? (
                    <p className="mt-1 break-words text-[10px] text-violet-200/85">
                      {ui("动作建议", "Action hint", "행동 제안")}：{actionMeta.hint}
                    </p>
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
                        <Check className="h-3 w-3" /> {approveLabel(actionMeta)}
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
              const groupBias = groupGodRingBiasSummary(group.decisions);
              const groupFlux = groupFluxRationale(group.decisions);
              const actionMeta = groupDecisionActionMeta(group.decisions);
              return (
                <div
                  key={group.key}
                  className={`rounded-2xl border bg-[linear-gradient(180deg,rgba(76,29,149,0.24),rgba(46,16,101,0.16))] p-3 ${
                    group.decisions.some((item) => String(item.id || item._ui_id || "").trim() === focusedDecisionId)
                      ? "border-emerald-500/45 shadow-[0_0_0_1px_rgba(16,185,129,0.25)]"
                      : "border-violet-500/35"
                  }`}
                >
                  <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="text-xs font-medium text-violet-50">{ui("目标", "Target", "대상")} {term(group.target)}</p>
                      <p className="text-[10px] text-violet-300/80">
                        {ui("来源", "Source", "출처")} {group.source} · {ui("冲突域", "Conflict domain", "충돌 영역")} {group.exclusivityKey} · {group.decisions.length} {ui("条", "items", "건")}
                      </p>
                    </div>
                    <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${badge.className}`}>{statusText(badge.label)}</span>
                  </div>

                  <div className="mb-2 flex flex-wrap gap-1">
                    {group.decisions.map((d) => (
                      <span key={d._ui_id} className="rounded-full border border-violet-500/25 bg-zinc-950/60 px-1.5 py-0.5 text-[8px] text-violet-100">
                        {term(String(d.source || d.target_god || d.label || "待定").trim())}
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
                  {groupBias ? (
                    <div className="mt-1 space-y-0.5 text-[10px]">
                      {groupBias.useText ? <p className="text-emerald-200/90">{ui("用侧推动", "Use-side push", "용측 추진")}：{groupBias.useText}</p> : null}
                      {groupBias.tabooText ? <p className="text-rose-200/90">{ui("忌侧推动", "Taboo-side push", "기측 추진")}：{groupBias.tabooText}</p> : null}
                    </div>
                  ) : null}
                  {groupFlux.length ? (
                    <div className="mt-1 space-y-0.5 text-[10px]">
                      {groupFlux.map((line) => (
                        <p key={`${group.key}_${line}`} className="break-words text-sky-200/85">
                          {line}
                        </p>
                      ))}
                    </div>
                  ) : null}
                  {actionMeta.hint ? (
                    <p className="mt-1 break-words text-[10px] text-violet-200/85">
                      {ui("动作建议", "Action hint", "행동 제안")}：{actionMeta.hint}
                    </p>
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
                        <Check className="h-3 w-3" /> {approveLabel(actionMeta, group.decisions.length)}
                      </button>
                    </div>
                  ) : null}

                  <div className="mt-2 space-y-1">
                    {group.decisions.map((d) => {
                      const decisionConfidence = patternConfidenceChip(d);
                      const bias = godRingBiasSummary(d);
                      const fluxLines = fluxRationale(d);
                      const actionMeta = singleDecisionActionMeta(d);
                      return (
                        <div
                          key={d._ui_id}
                          className={`rounded-lg border bg-zinc-950/45 px-2 py-1.5 ${
                            String(d.id || d._ui_id || "").trim() === focusedDecisionId
                              ? "border-emerald-500/45 shadow-[0_0_0_1px_rgba(16,185,129,0.25)]"
                              : "border-violet-500/25"
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <p className="break-words text-[10px] text-violet-100">
                              {(d.label || d.title || ui("行动建议", "Action hint", "행동 제안")).trim()}
                            </p>
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
                                {lang === "zh" ? singleDecisionButtonLabel(d) : t(lang, "decision.manual.button")}
                              </button>
                            </div>
                          </div>
                          {patternProfileSummary(d) ? (
                            <p className="mt-1 break-words text-[9px] text-cyan-100/85">{patternProfileSummary(d)}</p>
                          ) : null}
                          {bias ? (
                            <div className="mt-1 space-y-0.5 text-[9px]">
                              {bias.useText ? <p className="text-emerald-200/90">{ui("用侧推动", "Use-side push", "용측 추진")}：{bias.useText}</p> : null}
                              {bias.tabooText ? <p className="text-rose-200/90">{ui("忌侧推动", "Taboo-side push", "기측 추진")}：{bias.tabooText}</p> : null}
                            </div>
                          ) : null}
                          {fluxLines.length ? (
                            <div className="mt-1 space-y-0.5 text-[9px]">
                              {fluxLines.map((line) => (
                                <p key={`${d._ui_id}_${line}`} className="break-words text-sky-200/85">
                                  {line}
                                </p>
                              ))}
                            </div>
                          ) : null}
                          {actionMeta.hint ? (
                            <p className="mt-1 break-words text-[9px] text-violet-200/85">
                              {ui("动作建议", "Action hint", "행동 제안")}：{actionMeta.hint}
                            </p>
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
            <p className="text-[11px] text-zinc-500">
              {ui(
                "当前没有可批量归类的手动裁决。",
                "No manually grouped decisions are available right now.",
                "현재 묶음으로 처리할 수 있는 수동 결정이 없습니다.",
              )}
            </p>
          ) : null}
        </div>
      ) : (
        <p className="text-[11px] text-zinc-500">
          {ui(
            "当前没有需要你手动点按的裁决项。",
            "There are no manual decisions for you to process right now.",
            "지금 직접 처리해야 할 결정 항목은 없습니다.",
          )}
        </p>
      )}
    </div>
  );
}
