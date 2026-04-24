"use client";

import { useState } from "react";
import { motion } from "framer-motion";

import { mergeV17LlmMetaForUi } from "@/hooks/useV17WebStream";
import { t, type AppLanguage } from "@/lib/i18n";

type EvolutionFrame = {
  timestamp?: string;
  layer?: string;
  payload?: {
    snapshot_kind?: string;
    render_text?: string;
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
      source?: string;
      mode?: string;
      display_mode?: string;
      label_of_use?: string;
      label_of_taboo?: string;
      confidence?: number;
      core_path_count?: number;
      dual_role_candidates?: Array<Record<string, unknown>>;
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
  lang = "zh",
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
  lang?: AppLanguage;
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

  const tension = Number(physicsSnapshot?.payload?.physics_tension || 0);
  const willFlash = Boolean(latestNarrator?.payload?.will_flash);
  const lastFlashAt = [...ordered].reverse().find((f) => String(f?.layer || "").toUpperCase() === "WILL_FLASH")?.timestamp || "";
  const lm = mergeV17LlmMetaForUi(narratorForAudit, latestNarrator, llmAuditSnap);
  const rawFpt = lm.full_prompt_trace;
  const fullPromptTrace: MergedFullPromptTrace | undefined =
    rawFpt && typeof rawFpt === "object" ? (rawFpt as MergedFullPromptTrace) : undefined;
  const reconnecting = String(lm.engine_state || "") === "reconnecting";
  const errId = String(lm.error_id || "").trim();
  const modelLabel = String(lm.model || "").trim() || t(lang, "verdict.model");
  const waitingPhase =
    llmLifecyclePhase === "connecting" || llmLifecyclePhase === "awaiting_first_token";
  const streamingPhase = llmLifecyclePhase === "streaming";
  const [reasonOpen, setReasonOpen] = useState(false);
  const reasonFacts = (physicsSnapshot?.payload?.debug_trace?.facts || []).filter(
    (x) => String(x || "").trim().length > 0,
  );

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
      <div className="relative z-10 mb-3 flex flex-wrap items-center justify-between gap-2 text-[11px] text-zinc-400">
        <span className="rounded-full border border-violet-500/25 bg-violet-950/20 px-2 py-1 text-violet-200">
          {t(lang, "verdict.title")}
        </span>
        <span className="rounded-full border border-zinc-700/80 bg-zinc-900/80 px-2 py-1 text-zinc-300">
          {modelLabel}
        </span>
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
            <p className="mb-2 text-[11px] text-amber-300">
              {t(lang, "verdict.reconnecting")}
              {errId ? ` ${errId}` : ""}
            </p>
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
              <p>{t(lang, "verdict.status", { value: llmStatusText })}</p>
              <p className="font-mono text-violet-300/90">
                {t(lang, "verdict.elapsed", { model: modelLabel, ms: connectTickMs })}
              </p>
            </>
          ) : streamingPhase ? (
            <>
              <p>{t(lang, "verdict.status", { value: llmStatusText })}</p>
              <p className="font-mono text-violet-300/90">{t(lang, "verdict.link", { value: llmStatusDetail })}</p>
            </>
          ) : (
            <>
              <p>{t(lang, "verdict.status", { value: llmStatusText })}</p>
              <p className="font-mono text-violet-300/90">{t(lang, "verdict.link", { value: llmStatusDetail })}</p>
            </>
          )}
        </div>
      ) : null}
      <div className="absolute bottom-2 right-2 z-20 flex items-center gap-1">
        <button
          type="button"
          onClick={() => setReasonOpen((v) => !v)}
          className="rounded-full border border-violet-400/40 bg-violet-900/40 px-2 py-0.5 text-xs text-violet-200 hover:bg-violet-800/50"
          title={t(lang, "verdict.reason.button.title")}
        >
          {t(lang, "verdict.reason.button")}
        </button>
        <button
          type="button"
          onClick={() => onToggleTrace?.()}
          className="rounded-full border border-cyan-500/35 bg-zinc-900/60 px-2 py-0.5 text-[10px] text-cyan-200/90 hover:bg-zinc-800/70"
          title={t(lang, "verdict.trace.button.title")}
        >
          {t(lang, "verdict.trace.button")}
        </button>
      </div>
      {reasonOpen ? (
        <div className="relative z-20 mt-3 max-h-48 overflow-auto rounded-lg border border-violet-500/30 bg-zinc-950/90 p-2 text-left">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-violet-300/90">
            {t(lang, "verdict.reason.title")}
          </p>
          {llmAuditSnap ? (
            <p className="mb-2 text-[11px] text-emerald-200/90">{t(lang, "verdict.reason.audit")}</p>
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
            <p className="text-[11px] text-zinc-500">{t(lang, "verdict.reason.empty")}</p>
          )}
          {typeof lm.elapsed_ms === "number" ||
          lm.prompt_dead_audit_unlock === true ||
          lm.audit_preview === true ||
          lm.llm_audit_preview === true ||
          Boolean(llmAuditSnap) ||
          String(lm.llm_system_prompt || lm.llm_user_prompt || "").trim() ? (
            <div className="mt-3 space-y-2 border-t border-violet-500/25 pt-2">
              {lm.llm_audit_preview === true || Boolean(llmAuditSnap) ? (
                <p className="mb-1 text-[10px] text-emerald-300/90">{t(lang, "verdict.audit.snapshot")}</p>
              ) : lm.audit_preview ? (
                <p className="mb-1 text-[10px] text-emerald-300/90">{t(lang, "verdict.audit.preview")}</p>
              ) : null}
              {fullPromptTrace ? (
                <p className="text-[10px] text-amber-200/90">
                  {t(lang, "verdict.audit.anchor", {
                    value: fullPromptTrace.decision_anchor_literal_in_system_role
                      ? t(lang, "common.yes")
                      : t(lang, "common.no"),
                  })}
                  {typeof fullPromptTrace.decision_anchor_len === "number"
                    ? t(lang, "verdict.audit.anchor_len", { value: fullPromptTrace.decision_anchor_len })
                    : ""}
                </p>
              ) : null}
              <details className="rounded border border-violet-600/30 bg-black/40 px-2 py-1 text-[11px] text-zinc-300">
                <summary className="cursor-pointer select-none text-violet-200/95">{t(lang, "verdict.prompt.view")}</summary>
                <p className="mt-1 text-[10px] uppercase tracking-wide text-violet-400/80">{t(lang, "verdict.prompt.system")}</p>
                <pre className="mt-0.5 max-h-36 overflow-auto whitespace-pre-wrap break-words font-mono text-[10px] text-zinc-200">
                  {String(fullPromptTrace?.system_role ?? lm.llm_system_prompt ?? t(lang, "verdict.prompt.empty"))}
                </pre>
                <p className="mt-2 text-[10px] uppercase tracking-wide text-violet-400/80">{t(lang, "verdict.prompt.user")}</p>
                <pre className="mt-0.5 max-h-36 overflow-auto whitespace-pre-wrap break-words font-mono text-[10px] text-zinc-200">
                  {String(fullPromptTrace?.user_role ?? lm.llm_user_prompt ?? t(lang, "verdict.prompt.empty"))}
                </pre>
              </details>
              <details className="rounded border border-violet-600/30 bg-black/40 px-2 py-1 text-[11px] text-zinc-300">
                <summary className="cursor-pointer select-none text-violet-200/95">{t(lang, "verdict.raw.view")}</summary>
                <p className="mt-1 text-[10px] text-zinc-500">{t(lang, "verdict.raw.reply")}</p>
                <pre className="mt-0.5 max-h-32 overflow-auto whitespace-pre-wrap break-words font-mono text-[10px] text-zinc-200">
                  {String(lm.llm_reply || "").trim() || t(lang, "verdict.raw.empty")}
                </pre>
                <p className="mt-2 text-[10px] text-zinc-500">{t(lang, "verdict.raw.payload")}</p>
                <pre className="mt-0.5 max-h-32 overflow-auto whitespace-pre-wrap break-words font-mono text-[9px] text-zinc-400">
                  {String(lm.llm_raw_response_json || "").trim() || t(lang, "verdict.raw.payload_empty")}
                </pre>
              </details>
            </div>
          ) : null}
        </div>
      ) : null}
    </motion.div>
  );
}
