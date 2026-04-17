"use client";

import { motion } from "framer-motion";

type EvolutionFrame = {
  timestamp?: string;
  layer?: string;
  payload?: {
    render_text?: string;
    deity_scores?: Record<string, number>;
    physics_tension?: number;
    will_flash?: boolean;
    llm_meta?: {
      engine_state?: string;
      error_id?: string;
    };
    god_rings?: {
      god_of_use?: string[];
      god_of_taboo?: string[];
    };
  };
};

export function V17_PurpleVerdictCard({
  frames,
  onToggleTrace,
}: {
  frames: EvolutionFrame[];
  onToggleTrace?: () => void;
}) {
  const ordered = [...(frames || [])];
  const latestSnapshot = [...ordered].reverse().find((f) => String(f?.layer || "").toUpperCase() === "SNAPSHOT");
  const latestNarrator = [...ordered].reverse().find((f) => String(f?.payload?.render_text || "").trim().length > 0);
  const renderText = String(latestNarrator?.payload?.render_text || "").trim();
  const snapshotUse = latestSnapshot?.payload?.god_rings?.god_of_use || [];
  const snapshotTaboo = latestSnapshot?.payload?.god_rings?.god_of_taboo || [];
  const scoreMap = latestSnapshot?.payload?.deity_scores || {};
  const scoreRank = Object.entries(scoreMap || {})
    .map(([k, v]) => ({ k: String(k).trim(), v: Number(v || 0) }))
    .filter((x) => x.k && Number.isFinite(x.v))
    .sort((a, b) => b.v - a.v);
  const godUse = snapshotUse.length ? snapshotUse : scoreRank.slice(0, 2).map((x) => x.k);
  const godTaboo = snapshotTaboo.length ? snapshotTaboo : scoreRank.slice(-2).map((x) => x.k);
  const ringsLit = godUse.length > 0 || godTaboo.length > 0;

  const tension = Number(latestSnapshot?.payload?.physics_tension || 0);
  const willFlash = Boolean(latestNarrator?.payload?.will_flash);
  const lastFlashAt = [...ordered].reverse().find((f) => String(f?.layer || "").toUpperCase() === "WILL_FLASH")?.timestamp || "";
  const reconnecting = String(latestNarrator?.payload?.llm_meta?.engine_state || "") === "reconnecting";
  const errId = String(latestNarrator?.payload?.llm_meta?.error_id || "").trim();

  return (
    <motion.div 
      className="rounded-xl border border-violet-700/60 bg-black p-4 relative overflow-hidden"
      animate={{ 
        boxShadow: tension > 25 ? ["0 0 10px #7c3aed44", "0 0 25px #7c3aed66", "0 0 10px #7c3aed44"] : "none",
        y: tension > 40 ? [-1, 1, -1] : 0 
      }}
      transition={{ duration: tension > 40 ? 0.3 : 1.5, repeat: Infinity }}
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
      <button
        type="button"
        onClick={() => onToggleTrace?.()}
        className="absolute bottom-2 right-2 z-20 rounded-full border border-violet-400/40 bg-violet-900/40 px-2 py-0.5 text-xs text-violet-200 hover:bg-violet-800/50"
      >
        理
      </button>
    </motion.div>
  );
}
