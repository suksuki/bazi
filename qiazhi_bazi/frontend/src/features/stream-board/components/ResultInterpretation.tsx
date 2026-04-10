"use client";

import type { ReactNode } from "react";
import { useBlindSkillHighlight } from "@/features/stream-board/context/BlindSkillHighlightContext";

/**
 * 从断言行文本推断应对应高亮的盲派 Skill 徽章 id（与 blindSkillRuntime / skill_manifest 一致）。
 */
function inferSkillHintFromAssertionLine(line: string): string | null {
  const t = String(line || "");
  if (t.includes("穿") || /子未|丑午|寅巳|卯辰|申亥|酉戌/.test(t)) return "mp_pierce_01";
  if (t.includes("墓库") || t.includes("闭库")) return "mp_tomb_01";
  if (t.includes("宾主") || (t.includes("财官") && (t.includes("日时") || t.includes("红利")))) return "mp_host_guest_01";
  if (t.includes("MANGPAI_CHIP") && t.includes("穿局")) return "mp_pierce_01";
  if (t.includes("MANGPAI_CHIP") && t.includes("墓库")) return "mp_tomb_01";
  if (t.includes("MANGPAI_CHIP") && t.includes("宾主")) return "mp_host_guest_01";
  return null;
}

type SkillLinkedLineProps = {
  line: string;
  className: string;
  children: ReactNode;
};

/**
 * 悬停带 Skill 语义的断言行时，驱动顶部对应徽章缩放（需外层 BlindSkillHighlightProvider）。
 */
export function SkillLinkedAssertionLine({ line, className, children }: SkillLinkedLineProps) {
  const { setHighlightedBadgeId } = useBlindSkillHighlight();
  const hint = inferSkillHintFromAssertionLine(line);
  return (
    <p
      className={`${className}${hint ? " cursor-default rounded-md px-0.5 transition-colors hover:bg-violet-500/12" : ""}`}
      onMouseEnter={() => {
        if (hint) setHighlightedBadgeId(hint);
      }}
      onMouseLeave={() => setHighlightedBadgeId(null)}
    >
      {children}
    </p>
  );
}
