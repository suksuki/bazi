"use client";

import { useState } from "react";
import { motion } from "framer-motion";

import { mergeV17LlmMetaForUi } from "@/hooks/useV17WebStream";

type EvolutionFrame = {
  timestamp?: string;
  layer?: string;
  payload?: {
    snapshot_kind?: string;
    render_text?: string;
    pattern?: string;
    ten_gods_base_l0?: Record<string, number>;
    ten_gods_runtime?: Record<string, number>;
    ten_gods_narrative?: Record<string, number>;
    deity_scores?: Record<string, number>;
    ten_gods_absolute_intensity?: Record<string, number>;
    total_energy_index?: number;
    physics_tension?: number;
    will_flash?: boolean;
    debug_trace?: {
      hits?: string[];
      facts?: string[];
    };
      llm_meta?: {
      engine_state?: string;
      error_id?: string;
      prompt_dead_audit_unlock?: boolean;
      fuse_hard_circuit_sec?: number;
      audit_preview?: boolean;
      llm_audit_preview?: boolean;
      stream_partial?: boolean;
      elapsed_ms?: number;
      ok?: boolean;
      model?: string;
      llm_system_prompt?: string;
      llm_user_prompt?: string;
      llm_reply?: string;
      llm_raw_response_json?: string;
      full_prompt_trace?: {
        system_role?: string;
        user_role?: string;
        decision_anchor_literal_in_system_role?: boolean;
        decision_anchor_len?: number;
      };
    };
    god_rings?: {
      god_of_use?: string[];
      god_of_taboo?: string[];
    };
  };
};

type MergedFullPromptTrace = {
  system_role?: string;
  user_role?: string;
  decision_anchor_literal_in_system_role?: boolean;
  decision_anchor_len?: number;
};

export function V17_PurpleVerdictCard({
  frames,
  onToggleTrace,
  connectTickMs = 0,
  running = false,
  llmStatusText,
  llmStatusDetail,
  llmLifecyclePhase,
}: {
  frames: EvolutionFrame[];
  onToggleTrace?: () => void;
  /** 测算开始后前端计时（ms），用于连接态跳动 */
  connectTickMs?: number;
  running?: boolean;
  llmStatusText: string;
  llmStatusDetail: string;
  llmLifecyclePhase:
    | "idle"
    | "connecting"
    | "awaiting_first_token"
    | "streaming"
    | "completed"
    | "failed"
    | "closed_without_output";
}) {
  const ordered = [...(frames || [])];
  const llmAuditSnap = [...ordered].reverse().find(
    (f) =>
      String(f?.layer || "").toUpperCase() === "SNAPSHOT" &&
      String(f?.payload?.snapshot_kind || "") === "llm_audit_preview",
  );
  const physicsSnapshot = [...ordered].reverse().find((f) => {
    if (String(f?.layer || "").toUpperCase() !== "SNAPSHOT") return false;
    const sk = String(f?.payload?.snapshot_kind || "").trim();
    return sk === "physics" || sk === "physical_void" || sk === "system_init_failure";
  });
  const latestNarrator = [...ordered].reverse().find(
    (f) =>
      String(f?.layer || "").toUpperCase() === "NARRATOR" &&
      String(f?.payload?.render_text || "").trim().length > 0,
  );
  const narratorForAudit =
    [...ordered].reverse().find((f) => {
      if (String(f?.layer || "").toUpperCase() !== "NARRATOR") return false;
      const p = f?.payload;
      if (!p) return false;
      const rt = String(p.render_text || "").trim();
      const m = p.llm_meta || {};
      const sp = String(
        (m as { llm_system_prompt?: string; full_prompt_trace?: { system_role?: string } }).llm_system_prompt ||
          (m as { full_prompt_trace?: { system_role?: string } }).full_prompt_trace?.system_role ||
          "",
      ).trim();
      const unlock = (m as { prompt_dead_audit_unlock?: boolean }).prompt_dead_audit_unlock === true;
      return rt.length > 0 || sp.length > 0 || unlock;
    }) ||
    [...ordered].reverse().find(
      (f) =>
        String(f?.layer || "").toUpperCase() === "SNAPSHOT" &&
        String(f?.payload?.snapshot_kind || "") === "llm_audit_preview",
    );
  const renderText = String(
    latestNarrator?.payload?.render_text || physicsSnapshot?.payload?.render_text || "",
  ).trim();
  const snapshotUse = physicsSnapshot?.payload?.god_rings?.god_of_use || [];
  const snapshotTaboo = physicsSnapshot?.payload?.god_rings?.god_of_taboo || [];
  const scoreMap =
    latestNarrator?.payload?.ten_gods_narrative ||
    physicsSnapshot?.payload?.ten_gods_narrative ||
    physicsSnapshot?.payload?.ten_gods_runtime ||
    physicsSnapshot?.payload?.ten_gods_absolute_intensity ||
    physicsSnapshot?.payload?.deity_scores ||
    {};
  const scoreRank = Object.entries(scoreMap || {})
    .map(([k, v]) => ({ k: String(k).trim(), v: Number(v || 0) }))
    .filter((x) => x.k && Number.isFinite(x.v))
    .sort((a, b) => b.v - a.v);
  const godUse = snapshotUse.length ? snapshotUse : scoreRank.slice(0, 2).map((x) => x.k);
  const godTaboo = snapshotTaboo.length ? snapshotTaboo : scoreRank.slice(-2).map((x) => x.k);
  const ringsLit = godUse.length > 0 || godTaboo.length > 0;

  const tension = Number(physicsSnapshot?.payload?.physics_tension || 0);
  const willFlash = Boolean(latestNarrator?.payload?.will_flash);
  const lastFlashAt = [...ordered].reverse().find((f) => String(f?.layer || "").toUpperCase() === "WILL_FLASH")?.timestamp || "";
  const lm = mergeV17LlmMetaForUi(narratorForAudit, latestNarrator, llmAuditSnap);
  const rawFpt = lm.full_prompt_trace;
  const fullPromptTrace: MergedFullPromptTrace | undefined =
    rawFpt && typeof rawFpt === "object" ? (rawFpt as MergedFullPromptTrace) : undefined;
  const reconnecting = String(lm.engine_state || "") === "reconnecting";
  const errId = String(lm.error_id || "").trim();
  const modelLabel = String(lm.model || "").trim() || "叙事引擎";
  const waitingPhase =
    llmLifecyclePhase === "connecting" || llmLifecyclePhase === "awaiting_first_token";
  const streamingPhase = llmLifecyclePhase === "streaming";
  const [reasonOpen, setReasonOpen] = useState(false);
  const reasonFacts = (physicsSnapshot?.payload?.debug_trace?.facts || []).filter(
    (x) => String(x || "").trim().length > 0,
  );
  const snapPattern = String(physicsSnapshot?.payload?.pattern || "").trim();

  return (
    <motion.div 
      className="rounded-xl border border-violet-700/60 bg-black p-4 relative overflow-hidden"
      animate={{ 
        boxShadow: tension > 25 ? ["0 0 10px #7c3aed44", "0 0 25px #7c3aed66", "0 0 10px #7c3aed44"] : "none",
      }}
      transition={{ duration: 1.5, repeat: Infinity }}
    >
      <motion.div 
        className="absolute inset-0 z-0 pointer-events-none opacity-20 bg-gradient-to-tr from-violet-900/50 to-transparent"
        animate={{
          opacity: willFlash ? [0.1, 0.9, 0.25] : [0.1, 0.1 + (tension / 100), 0.1],
          scale: willFlash ? [1, 1.03, 1] : 1,
        }}
        transition={{ duration: willFlash ? 0.45 : Math.max(0.2, 2.0 - tension / 30), repeat: willFlash ? 0 : Infinity }}
      />
      <div className="relative z-10 mb-3 flex items-center justify-between text-xs">
        <motion.div
          initial={{ opacity: 0.45 }}
          animate={{ opacity: ringsLit ? 1 : [0.45, 0.8, 0.45] }}
          transition={{ duration: ringsLit ? 0.12 : 1.1, repeat: ringsLit ? 0 : Infinity }}
          className="text-emerald-300 font-mono tracking-wider"
        >
          [USE] {godUse.join("/") || "—"}
        </motion.div>
        <motion.div
          initial={{ opacity: 0.45 }}
          animate={{ opacity: ringsLit ? 1 : [0.45, 0.8, 0.45] }}
          transition={{ duration: ringsLit ? 0.12 : 1.1, repeat: ringsLit ? 0 : Infinity }}
          className="text-rose-300 font-mono tracking-wider"
        >
          [TABOO] {godTaboo.join("/") || "—"}
        </motion.div>
      </div>

      <motion.div
        className="relative z-10"
        key={String(lastFlashAt || "steady")}
        initial={lastFlashAt ? { filter: "blur(5px)", opacity: 0.65 } : undefined}
        animate={{ filter: "blur(0px)", opacity: 1 }}
        transition={{ duration: lastFlashAt ? 0.22 : 0.12, ease: "easeOut" }}
      >
      {renderText ? (
        <>
          {reconnecting ? (
            <p className="mb-2 text-[11px] text-amber-300">[叙事引擎重连中]{errId ? ` ${errId}` : ""}</p>
          ) : null}
          <motion.p
            key={renderText}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: willFlash ? 0.12 : 0.25, ease: "easeOut" }}
            className="text-sm leading-loose text-zinc-100 font-medium tracking-wide"
          >
            {renderText}
          </motion.p>
        </>
      ) : (
        <motion.div
          className="h-12 rounded-md bg-violet-500/10"
          animate={{ opacity: [0.3, 0.65, 0.3] }}
          transition={{ duration: 1.2, repeat: Infinity }}
        />
      )}
      </motion.div>
      {(waitingPhase || streamingPhase || llmLifecyclePhase === "closed_without_output") && running ? (
        <div className="relative z-10 mt-2 text-[10px] leading-relaxed text-violet-200/85">
          {waitingPhase ? (
            <>
              <p>状态：{llmStatusText}</p>
              <p className="font-mono text-violet-300/90">
                耗时：{modelLabel} · {connectTickMs} ms
              </p>
            </>
          ) : streamingPhase ? (
            <>
              <p>状态：{llmStatusText}</p>
              <p className="font-mono text-violet-300/90">链路：{llmStatusDetail}</p>
            </>
          ) : (
            <>
              <p>状态：{llmStatusText}</p>
              <p className="font-mono text-violet-300/90">链路：{llmStatusDetail}</p>
            </>
          )}
        </div>
      ) : null}
      <div className="absolute bottom-2 right-2 z-20 flex items-center gap-1">
        <button
          type="button"
          onClick={() => setReasonOpen((v) => !v)}
          className="rounded-full border border-violet-400/40 bg-violet-900/40 px-2 py-0.5 text-xs text-violet-200 hover:bg-violet-800/50"
          title="理：格局与插件事实碎屑（SNAPSHOT）"
        >
          理
        </button>
        <button
          type="button"
          onClick={() => onToggleTrace?.()}
          className="rounded-full border border-cyan-500/35 bg-zinc-900/60 px-2 py-0.5 text-[10px] text-cyan-200/90 hover:bg-zinc-800/70"
          title="因果链路面板"
        >
          溯
        </button>
      </div>
      {reasonOpen ? (
        <div className="relative z-20 mt-3 max-h-48 overflow-auto rounded-lg border border-violet-500/30 bg-zinc-950/90 p-2 text-left">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-violet-300/90">理 · 格局与因果碎屑</p>
          {llmAuditSnap ? (
            <p className="mb-2 text-[11px] text-emerald-200/90">引擎正在思考以下事实…（Prompt 已由 SNAPSHOT 审计帧解锁）</p>
          ) : null}
          {snapPattern ? (
            <p className="mb-2 text-[11px] text-zinc-300">
              格局：<span className="text-amber-200/90">{snapPattern}</span>
            </p>
          ) : null}
          {reasonFacts.length ? (
            <ul className="space-y-1 text-[11px] leading-snug text-zinc-200">
              {reasonFacts.map((line, i) => (
                <li key={`${i}_${line.slice(0, 24)}`} className="border-l border-violet-600/40 pl-2">
                  {line}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-[11px] text-zinc-500">尚无插件事实（等待 SNAPSHOT 一帧）。</p>
          )}
          {typeof lm.elapsed_ms === "number" ||
          lm.prompt_dead_audit_unlock === true ||
          lm.audit_preview === true ||
          lm.llm_audit_preview === true ||
          Boolean(llmAuditSnap) ||
          String(lm.llm_system_prompt || lm.llm_user_prompt || "").trim() ? (
            <div className="mt-3 space-y-2 border-t border-violet-500/25 pt-2">
              {lm.llm_audit_preview === true || Boolean(llmAuditSnap) ? (
                <p className="mb-1 text-[10px] text-emerald-300/90">首帧审计（SNAPSHOT / llm_audit_preview）：LLM 调用前已下发 System/User。</p>
              ) : lm.audit_preview ? (
                <p className="mb-1 text-[10px] text-emerald-300/90">首帧审计（AUDIT_PREVIEW）：LLM 调用前已下发 System/User。</p>
              ) : null}
              {fullPromptTrace ? (
                <p className="text-[10px] text-amber-200/90">
                  decision_anchor 已进入 System：{fullPromptTrace.decision_anchor_literal_in_system_role ? "是" : "否"}
                  {typeof fullPromptTrace.decision_anchor_len === "number"
                    ? `（锚点长度 ${fullPromptTrace.decision_anchor_len}）`
                    : ""}
                </p>
              ) : null}
              <details className="rounded border border-violet-600/30 bg-black/40 px-2 py-1 text-[11px] text-zinc-300">
                <summary className="cursor-pointer select-none text-violet-200/95">[查看完整提示词 (Prompt)]</summary>
                <p className="mt-1 text-[10px] uppercase tracking-wide text-violet-400/80">System</p>
                <pre className="mt-0.5 max-h-36 overflow-auto whitespace-pre-wrap break-words font-mono text-[10px] text-zinc-200">
                  {String(fullPromptTrace?.system_role ?? lm.llm_system_prompt ?? "（未携带）")}
                </pre>
                <p className="mt-2 text-[10px] uppercase tracking-wide text-violet-400/80">User</p>
                <pre className="mt-0.5 max-h-36 overflow-auto whitespace-pre-wrap break-words font-mono text-[10px] text-zinc-200">
                  {String(fullPromptTrace?.user_role ?? lm.llm_user_prompt ?? "（未携带）")}
                </pre>
              </details>
              <details className="rounded border border-violet-600/30 bg-black/40 px-2 py-1 text-[11px] text-zinc-300">
                <summary className="cursor-pointer select-none text-violet-200/95">[查看原始回复 (Raw)]</summary>
                <p className="mt-1 text-[10px] text-zinc-500">模型正文（未经叙事 Sanitizer）</p>
                <pre className="mt-0.5 max-h-32 overflow-auto whitespace-pre-wrap break-words font-mono text-[10px] text-zinc-200">
                  {String(lm.llm_reply || "").trim() || "（空）"}
                </pre>
                <p className="mt-2 text-[10px] text-zinc-500">上游 JSON / SSE 原始帧（截断存储）</p>
                <pre className="mt-0.5 max-h-32 overflow-auto whitespace-pre-wrap break-words font-mono text-[9px] text-zinc-400">
                  {String(lm.llm_raw_response_json || "").trim() || "（无或未启用流式捕获）"}
                </pre>
              </details>
            </div>
          ) : null}
        </div>
      ) : null}
    </motion.div>
  );
}
