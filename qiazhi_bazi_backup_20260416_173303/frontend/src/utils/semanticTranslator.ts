import { mapConflictDetail } from "@/constants/termMap";
import type { Lang } from "@/types/bazi";

const SKELETON_H3: Record<Lang, Record<string, string>> = {
  ZH: {},
  EN: {
    "### 核心气象 (物理预判)": "### Core climate (physics preview)",
    "### 风险预警 (意志对垒)": "### Risk alert (will vs engine)",
    "### 裁决共识": "### Verdict consensus",
    "### 行为指引": "### Behavioral guidance",
    "### 核心气象": "### Core climate",
  },
  KO: {
    "### 核心气象 (物理预判)": "### 핵심 기상(물리 예견)",
    "### 风险预警 (意志对垒)": "### 위험 경고(의지 대 엔진)",
    "### 裁决共识": "### 판정 합의",
    "### 行为指引": "### 행동 지침",
    "### 核心气象": "### 핵심 기상",
  },
};

const SKELETON_INLINE: Record<Lang, Record<string, string>> = {
  ZH: {},
  EN: {
    "**结构：**": "**Structure:**",
    "**状态：**": "**State:**",
    "**意志：**": "**Will:**",
    "**张力：**": "**Tension:**",
    "**时序：**": "**Timing:**",
  },
  KO: {
    "**结构：**": "**구조:**",
    "**状态：**": "**상태:**",
    "**意志：**": "**의지:**",
    "**张力：**": "**장력:**",
    "**时序：**": "**시점:**",
  },
};

/**
 * 主界面「物理骨架 / verdict_skeleton」展示用本地化（不改变原始数据；Debug 仍读中文原串）。
 * VF01 等锚点前缀保持；干支关系与十神走 termMap。
 */
export function translateVerdictSkeletonLine(line: string, lang: Lang): string {
  if (!line || lang === "ZH") return line;
  let s = line;
  const h3 = SKELETON_H3[lang];
  for (const [zh, loc] of Object.entries(h3)) {
    if (s.includes(zh)) s = s.split(zh).join(loc);
  }
  const inline = SKELETON_INLINE[lang];
  for (const [zh, loc] of Object.entries(inline)) {
    if (s.includes(zh)) s = s.split(zh).join(loc);
  }
  const vf = /^(\s*VF\d{2}:\s*)(.*)$/i.exec(s);
  if (vf) {
    const prefix = vf[1];
    const body = vf[2];
    return prefix + mapConflictDetail(body, lang);
  }
  return mapConflictDetail(s, lang);
}
