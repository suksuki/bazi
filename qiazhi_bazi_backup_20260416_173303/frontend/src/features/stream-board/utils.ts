import { mapConflictDetail } from "@/constants/termMap";
import { STATIC_I18N } from "@/features/stream-board/constants";
import type { BaziMetadata, Lang } from "@/types/bazi";
import type { FinalVerdictResult } from "./models";

export function calculateFireEnergyAfterConflicts(
  pillars: NonNullable<BaziMetadata["pillars"]> | null | undefined,
  conflicts: string[],
) {
  if (!pillars) return 100;
  const hasZiWu = conflicts.some((item) => item.includes("子午冲"));
  if (!hasZiWu) return 100;
  const monthBranch = pillars.month.branch;
  if (monthBranch === "子") return 40;
  if (monthBranch === "午") return 70;
  return 55;
}

export function cacheKey(lang: Lang, text: string) {
  return `${lang}::${text}`;
}

export function isAlreadyTargetLanguage(text: string, target: Lang) {
  if (!text) return false;
  if (target === "KO") return /[\uac00-\ud7a3]/.test(text);
  if (target === "EN") return /^[\x00-\x7F\s.,!?;:'"()[\]{}\-_/]+$/.test(text);
  return /[\u4e00-\u9fff]/.test(text);
}

export function resolveLocalTermTranslation(text: string, lang: Lang): string | null {
  const byStatic = STATIC_I18N[lang]?.[text];
  if (byStatic) return byStatic;
  const byTermMap = mapConflictDetail(text, lang);
  if (byTermMap !== text) return byTermMap;
  return null;
}

export function buildFallbackVerdict(conflicts: string[]): FinalVerdictResult {
  return {
    llmRequestMessages: [],
    llmRawResponse: "",
    llmMeta: { source: "fallback" },
    body: [
      "[SYSTEM_FALLBACK] 物理层输出正常，但语义层请求超时/异常，当前显示为保底断言。",
      "### 核心气象",
      `四柱主轴受 ${conflicts.join("、") || "既定校准项"} 牵动，结构进入高张力区。`,
      "### 裁决共识",
      "已依据本轮确认项完成参数校准并重算，当前断言以更新后物理真值为准。",
      "### 行为指引",
      "执行节奏应先稳后进：先修结构短板，再借顺势年份做放大决策。",
    ].join("\n"),
    changeLog: { text_diff_hint: "Fallback：终判服务异常，已使用保底全量断言。" },
    logicalEvidence: [],
    versionId: "",
    auditLog: {},
  };
}
