"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";

type Decision = {
  id?: string;
  title?: string;
  label?: string;
  source?: string;
  source_label?: string;
  priority?: number;
  target_god?: string;
  arbitration_trace?: string;
  llm_resolution_policy?: string;
  llm_resolution_result?: string;
  resolved_from_llm?: boolean;
  llm_resolution_state?: string;
  llm_terminal_state?: string;
  physical_impact?: {
    target_god?: string;
    impact_ratio?: number;
    significance_level?: string;
    significance_weight?: number;
    intensity_level?: number;
    resistance_mod?: Record<string, unknown>;
  };
};

type BucketKind = "manual" | "system" | "llm";

type Frame = {
  layer?: string;
  payload?: {
    manual_decisions?: Decision[];
    auto_resolutions?: Decision[];
    llm_arbitration_context?: Decision[];
    pending_decisions?: Decision[];
  };
};

function impactText(decision: Decision): string {
  const impact = decision.physical_impact || {};
  const ratio = typeof impact.impact_ratio === "number" ? Math.abs(impact.impact_ratio) : 0;
  const level = Number(impact.intensity_level || 0);
  if (ratio > 0) return `位移 ${(ratio * 100).toFixed(0)}% · L${level || "?"}`;
  if (level > 0) return `烈度 L${level}`;
  return "等待仲裁";
}

function bucketReason(kind: BucketKind, decision: Decision): string {
  const target = String(decision.target_god || decision.physical_impact?.target_god || "").trim();
  if (kind === "manual") {
    return target ? `已有明确目标神 ${target}，适合由你手动裁定。` : "保留给你手动定夺。";
  }
  if (kind === "system") {
    return target ? `目标神 ${target} 已明确，满足自动处理条件。` : "系统将继续观察并尝试自动收敛。";
  }
  return target ? `可为模型提供 ${target} 方向的叙事参考，但不建议直接点按。` : "更适合作为叙事上下文，而不是直接动作。";
}

function statusBadge(kind: BucketKind, decision: Decision): { label: string; className: string } {
  const impact = decision.physical_impact || {};
  const ratio = Math.abs(Number(impact.impact_ratio || 0));
  const level = Number(impact.intensity_level || 0);
  if (kind === "manual") {
    if (level >= 3 || ratio >= 0.1) {
      return {
        label: "需立即裁定",
        className: "border-rose-500/30 bg-rose-950/40 text-rose-100",
      };
    }
    return {
      label: "等待你确认",
      className: "border-violet-500/25 bg-violet-950/35 text-violet-100",
    };
  }
  if (kind === "system") {
    if (level >= 3) {
      return {
        label: "拟自动收敛",
        className: "border-amber-500/30 bg-amber-950/40 text-amber-100",
      };
    }
    return {
      label: "系统观察中",
      className: "border-zinc-500/20 bg-zinc-900/70 text-zinc-300",
    };
  }
  return {
    label: "将注入 Prompt",
    className: "border-cyan-500/30 bg-cyan-950/35 text-cyan-100",
  };
}

function promptPreview(decision: Decision): string {
  const target = String(decision.target_god || decision.physical_impact?.target_god || "未定目标").trim();
  const source = String(decision.source || "unknown").trim();
  const ratio = Math.abs(Number(decision.physical_impact?.impact_ratio || 0));
  const preview = ratio > 0
    ? `${target} 发生 ${(ratio * 100).toFixed(1)}% 相对位移`
    : `${target} 被纳入叙事仲裁参考`;
  return `Prompt 将引用：${preview}，来源 ${source}。`;
}

function llmPolicyLabel(policy: string | undefined): string {
  if (policy === "auto_apply") return "可自动裁决";
  if (policy === "suggest_only") return "仅给建议";
  return "仅作上下文";
}

function llmResultLabel(result: string | undefined): string {
  if (result === "collapse_system") return "将下沉到 SYSTEM";
  if (result === "promote_manual") return "将升格到 MANUAL";
  if (result === "consume_context") return "将被 LLM 消化";
  return "继续等待";
}

function llmStateLabel(state: string | undefined): string {
  if (state === "collapsed_to_system") return "已转入 SYSTEM";
  if (state === "promoted_to_manual") return "已转入 MANUAL";
  if (state === "pending_context") return "等待模型消化";
  return "处理中";
}

function arbitrationRule(kind: BucketKind): { title: string; detail: string; accent: string } {
  if (kind === "manual") {
    return {
      title: "进入条件",
      detail: "存在明确目标神，且属于可执行动作，不是诊断态或纯说明态。",
      accent: "text-violet-100 border-violet-500/20 bg-violet-950/20",
    };
  }
  if (kind === "system") {
    return {
      title: "进入条件",
      detail: "烈度较高，且满足自动处理阈值，系统可先行收敛。",
      accent: "text-amber-100 border-amber-500/20 bg-amber-950/20",
    };
  }
  return {
    title: "进入条件",
    detail: "更适合作为叙事依据、诊断上下文或提示词引用，而非直接动作。",
    accent: "text-cyan-100 border-cyan-500/20 bg-cyan-950/20",
  };
}

function decisionReasonTags(kind: BucketKind, decision: Decision): string[] {
  const impact = decision.physical_impact || {};
  const ratio = Math.abs(Number(impact.impact_ratio || 0));
  const level = Number(impact.intensity_level || 0);
  const target = String(decision.target_god || impact.target_god || "").trim();
  const tags: string[] = [];
  if (target) tags.push(`目标神:${target}`);
  if (level > 0) tags.push(`烈度:L${level}`);
  if (ratio > 0) tags.push(`位移:${(ratio * 100).toFixed(0)}%`);
  if (kind === "manual") tags.push("人工裁决");
  if (kind === "system") tags.push("自动收敛");
  if (kind === "llm") tags.push("叙事引用");
  return tags.slice(0, 4);
}

function sourceLabel(decision: Decision): string {
  const raw = String(decision.source || "unknown").trim();
  if (!raw) return "未知规则";
  if (raw.includes("liuchong")) return "六冲";
  if (raw.includes("liuhe")) return "六合";
  if (raw.includes("liupo")) return "六破";
  if (raw.includes("sanxing")) return "三刑";
  if (raw.includes("banhe")) return "半合";
  if (raw.includes("three_harmony")) return "三合";
  if (raw.includes("muku")) return "墓库";
  if (raw.includes("stem_fusion")) return "天干五合";
  if (raw.includes("chang_sheng")) return "长生状态";
  if (raw.includes("geometry")) return "几何关系";
  if (raw.includes("manifest")) return "插件命中";
  if (raw.startsWith("l2.")) return raw.replace(/^l2\./, "L2:");
  return raw;
}

function arbitrationModeLabel(kind: BucketKind): string {
  if (kind === "manual") return "手动";
  if (kind === "system") return "自动";
  return "LLM";
}

function arbitrationTrace(kind: BucketKind, decision: Decision): string {
  if (String(decision.arbitration_trace || "").trim()) {
    return String(decision.arbitration_trace || "").trim();
  }
  const impact = decision.physical_impact || {};
  const level = Number(impact.intensity_level || 0);
  const source = String(decision.source_label || "").trim() || sourceLabel(decision);
  const levelText = level > 0 ? `L${level}` : "L?";
  return `${source} -> ${levelText} -> ${arbitrationModeLabel(kind)}`;
}

export function V17_DecisionInbox({
  frames,
  adoptedIds,
  sessionId,
  locked = false,
  lockMessage = "",
  onAdopted,
}: {
  frames: Frame[];
  adoptedIds: string[];
  sessionId: string;
  locked?: boolean;
  lockMessage?: string;
  onAdopted?: (decision: Decision) => void | Promise<void>;
}) {
  const [busyId, setBusyId] = useState<string>("");
  const latestSnapshot = useMemo(
    () =>
      [...(frames || [])].reverse().find((f) => {
        if (String(f?.layer || "").toUpperCase() !== "SNAPSHOT") return false;
        const sk = String((f?.payload as { snapshot_kind?: string })?.snapshot_kind || "").trim();
        return sk === "physics" || sk === "physical_void" || sk === "system_init_failure";
      }),
    [frames],
  );
  const { visible: decisions, hiddenCount } = useMemo(() => {
    const source = latestSnapshot?.payload?.manual_decisions || latestSnapshot?.payload?.pending_decisions || [];
    const raw = source.filter((d, idx) => {
      const id = String(d?.id || idx);
      return !adoptedIds.includes(id);
    });
    const sorted = [...raw].sort((a, b) => (Number(b.priority) || 0) - (Number(a.priority) || 0));
    const DISPLAY_CAP = 14;
    const cap = Math.min(sorted.length, DISPLAY_CAP);
    return { visible: sorted.slice(0, cap), hiddenCount: Math.max(0, sorted.length - cap) };
  }, [latestSnapshot?.payload?.manual_decisions, latestSnapshot?.payload?.pending_decisions, adoptedIds]);
  const autoResolutions = useMemo(
    () => (latestSnapshot?.payload?.auto_resolutions || []).slice(0, 6),
    [latestSnapshot?.payload?.auto_resolutions],
  );
  const llmArbitration = useMemo(
    () => (latestSnapshot?.payload?.llm_arbitration_context || []).slice(0, 6),
    [latestSnapshot?.payload?.llm_arbitration_context],
  );

  async function onPick(decision: Decision) {
    if (locked || busyId) return;
    const id = String(decision.id || decision.title || "pick");
    setBusyId(id);
    try {
      await onAdopted?.(decision);
    } finally {
      setBusyId("");
    }
  }

  if (!decisions.length && !autoResolutions.length && !llmArbitration.length) return null;

  return (
    <section className="rounded-2xl border border-violet-700/40 bg-[linear-gradient(180deg,rgba(8,4,20,0.92),rgba(10,10,16,0.82))] p-3 shadow-[0_16px_50px_rgba(76,29,149,0.18)]">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs tracking-[0.24em] text-violet-200/85">DECISION CONSOLE</p>
          <p className="mt-1 text-[11px] text-zinc-500">手动裁决 / 系统建议 / LLM 仲裁参考</p>
        </div>
        <div className="flex items-center gap-2 text-[10px]">
          <span className="rounded-full border border-violet-500/25 bg-violet-900/20 px-2 py-1 text-violet-100">
            手动 {decisions.length}
          </span>
          <span className="rounded-full border border-amber-500/20 bg-amber-950/30 px-2 py-1 text-amber-100">
            系统 {autoResolutions.length}
          </span>
          <span className="rounded-full border border-cyan-500/20 bg-cyan-950/25 px-2 py-1 text-cyan-100">
            LLM {llmArbitration.length}
          </span>
        </div>
      </div>

      <div className="mb-3 grid gap-2 lg:grid-cols-3">
        {(["manual", "system", "llm"] as BucketKind[]).map((kind) => {
          const rule = arbitrationRule(kind);
          return (
            <div key={kind} className={`rounded-xl border px-3 py-2 text-[10px] leading-relaxed ${rule.accent}`}>
              <p className="tracking-[0.2em]">{kind.toUpperCase()}</p>
              <p className="mt-1 text-zinc-300">{rule.title}</p>
              <p className="mt-1 text-zinc-400">{rule.detail}</p>
            </div>
          );
        })}
      </div>

      <div className="grid gap-3 lg:grid-cols-[1.3fr_0.9fr_0.9fr]">
        <div className="rounded-xl border border-violet-500/20 bg-zinc-950/55 p-3">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-[11px] tracking-[0.22em] text-violet-200">MANUAL</p>
            <span className="text-[10px] text-zinc-500">可点击执行</span>
          </div>
          {decisions.length ? (
            <div className="flex flex-wrap gap-2">
              {decisions.map((d, idx) => {
                const id = String(d.id || idx);
                const target = String(d.target_god || d.physical_impact?.target_god || "").trim();
                const badge = statusBadge("manual", d);
                return (
                  <motion.button
                    key={id}
                    type="button"
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => onPick(d)}
                    disabled={locked || busyId !== ""}
                    className="group min-w-[8rem] rounded-2xl border border-violet-500/35 bg-[linear-gradient(180deg,rgba(76,29,149,0.24),rgba(46,16,101,0.16))] px-3 py-2 text-left transition hover:border-violet-300/50 hover:bg-violet-700/20 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    <p className="text-xs text-violet-50">{(d.label || d.title || "行动建议").trim()}</p>
                    <div className="mt-1 flex items-center gap-1 text-[10px] text-violet-200/75">
                      <span>{String(d.source || "manual")}</span>
                      {target ? <span className="rounded-full border border-violet-400/25 px-1.5 py-0.5 text-[9px] text-violet-100">{target}</span> : null}
                      <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${badge.className}`}>{badge.label}</span>
                    </div>
                    <p className="mt-1 text-[10px] text-zinc-400">{impactText(d)}</p>
                    <p className="mt-1 font-mono text-[10px] text-violet-200/80">{arbitrationTrace("manual", d)}</p>
                    <p className="mt-1 text-[10px] leading-relaxed text-zinc-500">{bucketReason("manual", d)}</p>
                    {d.resolved_from_llm ? (
                      <div className="mt-1 flex flex-wrap gap-1">
                        <span className="rounded-full border border-cyan-500/20 bg-cyan-950/25 px-1.5 py-0.5 text-[9px] text-cyan-100">
                          来自 LLM 仲裁
                        </span>
                        <span className="rounded-full border border-violet-500/20 bg-zinc-950/60 px-1.5 py-0.5 text-[9px] text-zinc-300">
                          {String(d.llm_resolution_state || "promoted_to_manual")}
                        </span>
                      </div>
                    ) : null}
                    <div className="mt-1 flex flex-wrap gap-1">
                      {decisionReasonTags("manual", d).map((tag) => (
                        <span key={tag} className="rounded-full border border-violet-500/20 bg-zinc-950/60 px-1.5 py-0.5 text-[9px] text-zinc-300">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </motion.button>
                );
              })}
            </div>
          ) : (
            <p className="text-[11px] text-zinc-500">当前没有需要你手动点按的裁决项。</p>
          )}
        </div>

        <div className="rounded-xl border border-amber-500/15 bg-zinc-950/55 p-3">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-[11px] tracking-[0.22em] text-amber-200">SYSTEM</p>
            <span className="text-[10px] text-zinc-500">自动裁决候选</span>
          </div>
          <div className="space-y-2">
            {autoResolutions.length ? autoResolutions.map((row, idx) => {
              const badge = statusBadge("system", row);
              return (
              <div key={`auto_${idx}`} className="rounded-xl border border-amber-500/10 bg-amber-950/20 px-2.5 py-2">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-[11px] text-amber-100">{String(row.label || row.title || "系统动作").trim()}</p>
                  <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${badge.className}`}>{badge.label}</span>
                </div>
                <p className="mt-1 text-[10px] text-zinc-500">
                  {String(row.source || "system")} · {String(row.target_god || row.physical_impact?.target_god || "自动求解")}
                </p>
                <p className="mt-1 text-[10px] text-zinc-400">{impactText(row)}</p>
                <p className="mt-1 font-mono text-[10px] text-amber-200/80">{arbitrationTrace("system", row)}</p>
                <p className="mt-1 text-[10px] leading-relaxed text-zinc-500">{bucketReason("system", row)}</p>
                {row.resolved_from_llm ? (
                  <div className="mt-1 flex flex-wrap gap-1">
                    <span className="rounded-full border border-cyan-500/20 bg-cyan-950/25 px-1.5 py-0.5 text-[9px] text-cyan-100">
                      来自 LLM 仲裁
                    </span>
                    <span className="rounded-full border border-amber-500/20 bg-zinc-950/60 px-1.5 py-0.5 text-[9px] text-zinc-300">
                      {String(row.llm_resolution_state || "collapsed_to_system")}
                    </span>
                  </div>
                ) : null}
                <div className="mt-1 flex flex-wrap gap-1">
                  {decisionReasonTags("system", row).map((tag) => (
                    <span key={tag} className="rounded-full border border-amber-500/20 bg-zinc-950/60 px-1.5 py-0.5 text-[9px] text-zinc-300">
                      {tag}
                    </span>
                  ))}
                </div>
                <p className="mt-1 text-[10px] leading-relaxed text-amber-100/80">{promptPreview(row)}</p>
              </div>
            );}) : <p className="text-[11px] text-zinc-500">暂无系统自动裁决项。</p>}
          </div>
        </div>

        <div className="rounded-xl border border-cyan-500/15 bg-zinc-950/55 p-3">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-[11px] tracking-[0.22em] text-cyan-200">LLM</p>
            <span className="text-[10px] text-zinc-500">叙事仲裁参考</span>
          </div>
          <div className="space-y-2">
            {llmArbitration.length ? llmArbitration.map((row, idx) => {
              const badge = statusBadge("llm", row);
              return (
              <div key={`llm_${idx}`} className="rounded-xl border border-cyan-500/10 bg-cyan-950/15 px-2.5 py-2">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-[11px] text-cyan-100">{String(row.label || row.title || "LLM 参考").trim()}</p>
                  <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${badge.className}`}>{badge.label}</span>
                </div>
                <p className="mt-1 text-[10px] text-zinc-500">{String(row.source || "llm_context")}</p>
                <p className="mt-1 text-[10px] text-zinc-400">{impactText(row)}</p>
                <p className="mt-1 font-mono text-[10px] text-cyan-200/80">{arbitrationTrace("llm", row)}</p>
                <p className="mt-1 text-[10px] leading-relaxed text-zinc-500">{bucketReason("llm", row)}</p>
                <div className="mt-1 flex flex-wrap gap-1">
                  <span className="rounded-full border border-cyan-500/20 bg-zinc-950/60 px-1.5 py-0.5 text-[9px] text-cyan-100">
                    {llmPolicyLabel(row.llm_resolution_policy)}
                  </span>
                  <span className="rounded-full border border-cyan-500/20 bg-zinc-950/60 px-1.5 py-0.5 text-[9px] text-zinc-300">
                    {llmStateLabel(row.llm_resolution_state)}
                  </span>
                  <span className="rounded-full border border-cyan-500/20 bg-zinc-950/60 px-1.5 py-0.5 text-[9px] text-zinc-300">
                    {llmResultLabel(row.llm_resolution_result)}
                  </span>
                </div>
                {row.llm_terminal_state ? (
                  <p className="mt-1 text-[10px] leading-relaxed text-zinc-500">
                    终态：{String(row.llm_terminal_state)}
                  </p>
                ) : null}
                <div className="mt-1 flex flex-wrap gap-1">
                  {decisionReasonTags("llm", row).map((tag) => (
                    <span key={tag} className="rounded-full border border-cyan-500/20 bg-zinc-950/60 px-1.5 py-0.5 text-[9px] text-zinc-300">
                      {tag}
                    </span>
                  ))}
                </div>
                <p className="mt-1 text-[10px] leading-relaxed text-cyan-100/80">{promptPreview(row)}</p>
              </div>
            );}) : <p className="text-[11px] text-zinc-500">暂无需要交给 LLM 仲裁的参考项。</p>}
          </div>
        </div>
      </div>
      {locked && lockMessage ? <p className="mt-2 text-[11px] text-amber-200/85">{lockMessage}</p> : null}
      {hiddenCount > 0 ? (
        <p className="mt-2 text-[11px] text-zinc-500">另有 {hiddenCount} 条手动决策已接收但未展开，可拉高 SNAPSHOT 中 manual_decisions 上限或调低已采纳项。</p>
      ) : null}
    </section>
  );
}
