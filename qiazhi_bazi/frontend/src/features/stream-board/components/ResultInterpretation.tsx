"use client";

import type { ReactNode } from "react";
import { useCallback, useState } from "react";
import { useBlindSkillHighlight } from "@/features/stream-board/context/BlindSkillHighlightContext";
import { skillFeedbackPostUrl } from "@/features/stream-board/lib/feedbackApiUrl";

/**
 * 从断言行文本推断应对应高亮的盲派 Skill 徽章 id（与 blindSkillRuntime / skill_manifest 一致）。
 */
export function inferSkillHintFromAssertionLine(line: string): string | null {
  const t = String(line || "");
  if (t.includes("穿") || /子未|丑午|寅巳|卯辰|申亥|酉戌/.test(t)) return "mp_pierce_01";
  if (t.includes("墓库") || t.includes("闭库")) return "mp_tomb_01";
  if (t.includes("宾主") || (t.includes("财官") && (t.includes("日时") || t.includes("红利")))) return "mp_host_guest_01";
  if (t.includes("MANGPAI_CHIP") && t.includes("穿局")) return "mp_pierce_01";
  if (t.includes("MANGPAI_CHIP") && t.includes("墓库")) return "mp_tomb_01";
  if (t.includes("MANGPAI_CHIP") && t.includes("宾主")) return "mp_host_guest_01";
  return null;
}

function IconLogicAnchor({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.65" aria-hidden>
      <circle cx="12" cy="12" r="3.25" />
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.93 4.93l2.12 2.12M16.95 16.95l2.12 2.12M4.93 19.07l2.12-2.12M16.95 7.05l2.12-2.12" strokeLinecap="round" />
    </svg>
  );
}

type SemanticAnchorProps = {
  skillId: string;
  lineIndex: number;
  linePreview: string;
  sessionHint: string;
  disabled?: boolean;
};

function SemanticFeedbackAnchor({ skillId, lineIndex, linePreview, sessionHint, disabled }: SemanticAnchorProps) {
  const [local, setLocal] = useState<"idle" | "precise" | "drift">("idle");
  const [busy, setBusy] = useState(false);

  const send = useCallback(
    async (rating: "precise" | "drift") => {
      if (disabled || busy) return;
      setBusy(true);
      try {
        const url = skillFeedbackPostUrl();
        await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            skill_id: skillId,
            line_index: lineIndex,
            rating,
            line_preview: linePreview.slice(0, 400),
            session_hint: sessionHint.slice(0, 200),
          }),
        });
        setLocal(rating);
      } catch {
        setLocal("idle");
      } finally {
        setBusy(false);
      }
    },
    [busy, disabled, lineIndex, linePreview, sessionHint, skillId],
  );

  return (
    <span className="ml-1 inline-flex shrink-0 items-center gap-0.5 align-top" title="逻辑锚点：关联 Skill 的语义反馈">
      <span className="text-zinc-600" aria-hidden>
        <IconLogicAnchor className="h-3.5 w-3.5" />
      </span>
      <span className="flex flex-col gap-px">
        <button
          type="button"
          disabled={disabled || busy}
          title="精准"
          onClick={() => send("precise")}
          className={`rounded px-1 py-0 text-[8px] font-medium leading-none ${
            local === "precise" ? "bg-emerald-500/25 text-emerald-200" : "bg-zinc-800/90 text-zinc-500 hover:text-zinc-300"
          }`}
        >
          准
        </button>
        <button
          type="button"
          disabled={disabled || busy}
          title="偏移"
          onClick={() => send("drift")}
          className={`rounded px-1 py-0 text-[8px] font-medium leading-none ${
            local === "drift" ? "bg-amber-500/25 text-amber-200" : "bg-zinc-800/90 text-zinc-500 hover:text-zinc-300"
          }`}
        >
          偏
        </button>
      </span>
    </span>
  );
}

type SkillLinkedLineProps = {
  line: string;
  className: string;
  children: ReactNode;
  /** 断言行在 verdict 中的下标，供后端适应度关联 */
  assertionIndex?: number;
  /** 显式 Skill id；不传则用 inferSkillHintFromAssertionLine(line) */
  skillId?: string | null;
  sessionHint?: string;
  /** 终审冻结时禁用反馈提交 */
  interactionLocked?: boolean;
  /** 为 false 时不展示语义锚点（例如非盲派关联行） */
  enableSemanticFeedback?: boolean;
};

/**
 * 悬停带 Skill 语义的断言行时，驱动顶部对应徽章缩放（需外层 BlindSkillHighlightProvider）。
 */
export function SkillLinkedAssertionLine({
  line,
  className,
  children,
  assertionIndex,
  skillId: skillIdProp,
  sessionHint = "",
  interactionLocked,
  enableSemanticFeedback = true,
}: SkillLinkedLineProps) {
  const { setHighlightedBadgeId } = useBlindSkillHighlight();
  const trimmedProp = skillIdProp && String(skillIdProp).trim() ? String(skillIdProp).trim() : null;
  const hint = trimmedProp || inferSkillHintFromAssertionLine(line);
  const showAnchor = enableSemanticFeedback && hint && typeof assertionIndex === "number" && assertionIndex >= 0;

  return (
    <p
      className={`flex gap-1 ${className}${hint ? " cursor-default rounded-md px-0.5 transition-colors hover:bg-violet-500/12" : ""}`}
      onMouseEnter={() => {
        if (hint) setHighlightedBadgeId(hint);
      }}
      onMouseLeave={() => setHighlightedBadgeId(null)}
    >
      <span className="min-w-0 flex-1">{children}</span>
      {showAnchor ? (
        <SemanticFeedbackAnchor
          skillId={hint}
          lineIndex={assertionIndex}
          linePreview={line}
          sessionHint={sessionHint}
          disabled={Boolean(interactionLocked)}
        />
      ) : null}
    </p>
  );
}
