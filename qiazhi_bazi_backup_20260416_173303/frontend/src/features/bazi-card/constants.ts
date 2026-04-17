import type { BaziMetadata } from "@/types/bazi";

export const PILLAR_ORDER: Array<keyof NonNullable<BaziMetadata["pillars"]>> = ["year", "month", "day", "hour"];

export const STEM_ELEMENT: Record<string, "wood" | "fire" | "earth" | "metal" | "water"> = {
  甲: "wood", 乙: "wood", 丙: "fire", 丁: "fire", 戊: "earth", 己: "earth", 庚: "metal", 辛: "metal", 壬: "water", 癸: "water",
};

export const STEM_POLARITY: Record<string, "yang" | "yin"> = {
  甲: "yang", 丙: "yang", 戊: "yang", 庚: "yang", 壬: "yang",
  乙: "yin", 丁: "yin", 己: "yin", 辛: "yin", 癸: "yin",
};

export const ELEMENT_GENERATES: Record<string, string> = { wood: "fire", fire: "earth", earth: "metal", metal: "water", water: "wood" };
export const ELEMENT_CONTROLS: Record<string, string> = { wood: "earth", fire: "metal", earth: "water", metal: "wood", water: "fire" };

export const BRANCH_MAIN_STEM: Record<string, string> = {
  子: "癸", 丑: "己", 寅: "甲", 卯: "乙", 辰: "戊", 巳: "丙", 午: "丁", 未: "己", 申: "庚", 酉: "辛", 戌: "戊", 亥: "壬",
};

export const BRANCH_HIDDEN_STEMS: Record<string, string[]> = {
  子: ["癸"], 丑: ["己", "癸", "辛"], 寅: ["甲", "丙", "戊"], 卯: ["乙"], 辰: ["戊", "乙", "癸"], 巳: ["丙", "戊", "庚"],
  午: ["丁", "己"], 未: ["己", "丁", "乙"], 申: ["庚", "壬", "戊"], 酉: ["辛"], 戌: ["戊", "辛", "丁"], 亥: ["壬", "甲"],
};

export const DEITY_ABBR: Record<string, string> = {
  比肩: "比", 劫财: "劫", 食神: "食", 伤官: "伤", 正财: "财", 偏财: "才", 正官: "官", 七杀: "杀", 正印: "印", 偏印: "枭",
};

export const DAY_ROOT_BRANCHES: Record<string, string[]> = {
  甲: ["寅", "卯", "辰", "未", "亥"],
  乙: ["寅", "卯", "辰", "未"],
  丙: ["巳", "午", "寅", "未"],
  丁: ["巳", "午", "未", "戌"],
  戊: ["辰", "戌", "丑", "未", "巳", "午"],
  己: ["辰", "戌", "丑", "未", "午"],
  庚: ["申", "酉", "戌", "丑"],
  辛: ["申", "酉", "戌", "丑"],
  壬: ["亥", "子", "申", "辰"],
  癸: ["亥", "子", "丑", "辰"],
};
